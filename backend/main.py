import os
from pathlib import Path
from typing import Literal
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from task_api import router as tasks_router

app = FastAPI(title="My AI Agent API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS","http://localhost:8000").split(","), allow_credentials=False, allow_methods=["GET","POST","DELETE"], allow_headers=["Content-Type","Authorization"])
app.include_router(tasks_router)

@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    page = Path(__file__).resolve().parent.parent / "dashboard.html"
    if not page.is_file():
        raise HTTPException(404, "Dashboard file is missing from the deployment.")
    return FileResponse(page, media_type="text/html")

class Message(BaseModel):
    role: Literal["user","assistant"]
    content: str = Field(min_length=1, max_length=20000)
class ChatRequest(BaseModel):
    provider: Literal["openai","anthropic","gemini"] = "openai"
    model: str = Field(default="gpt-4o-mini", min_length=1, max_length=100)
    messages: list[Message] = Field(min_length=1, max_length=50)

@app.get("/health")
async def health():
    return {"status":"ok","service":"My AI Agent API"}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages=[{"role":m.role,"content":m.content} for m in req.messages]
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0,connect=15.0)) as client:
            if req.provider=="openai":
                key=os.getenv("OPENAI_API_KEY")
                if not key: raise HTTPException(503,"OPENAI_API_KEY is not configured on the backend.")
                r=await client.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {key}"},json={"model":req.model,"messages":messages,"temperature":0.7})
                if r.is_error: raise HTTPException(r.status_code,"OpenAI request failed: "+r.text[:400])
                answer=r.json()["choices"][0]["message"]["content"]
            elif req.provider=="anthropic":
                key=os.getenv("ANTHROPIC_API_KEY")
                if not key: raise HTTPException(503,"ANTHROPIC_API_KEY is not configured on the backend.")
                r=await client.post("https://api.anthropic.com/v1/messages",headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},json={"model":req.model,"max_tokens":2048,"messages":messages})
                if r.is_error: raise HTTPException(r.status_code,"Anthropic request failed: "+r.text[:400])
                answer="".join(p.get("text","") for p in r.json().get("content",[]) if p.get("type")=="text")
            else:
                key=os.getenv("GEMINI_API_KEY")
                if not key: raise HTTPException(503,"GEMINI_API_KEY is not configured on the backend.")
                contents=[{"role":"model" if m["role"]=="assistant" else "user","parts":[{"text":m["content"]}]} for m in messages]
                r=await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{req.model}:generateContent",params={"key":key},json={"contents":contents,"generationConfig":{"temperature":0.7,"maxOutputTokens":2048}})
                if r.is_error: raise HTTPException(r.status_code,"Gemini request failed: "+r.text[:400])
                answer="".join(p.get("text","") for p in r.json().get("candidates",[{}])[0].get("content",{}).get("parts",[]))
        return {"answer":answer,"provider":req.provider,"model":req.model}
    except HTTPException: raise
    except httpx.TimeoutException: raise HTTPException(504,"AI provider timed out. Please try again.")
    except (httpx.HTTPError,KeyError,IndexError,ValueError) as exc: raise HTTPException(502,"AI provider request failed. Check model name and backend logs.") from exc
