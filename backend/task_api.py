"""Persistent task tracking API for Fridey Agent.
Tasks are recorded in SQLite. This first milestone tracks requests; a separate durable
worker/integrations are needed for reliable background execution and monitoring.
"""
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
DB_PATH = os.getenv("FRIDEY_TASK_DB", str(Path(__file__).with_name("fridey_tasks.sqlite3")))
KINDS = Literal["general", "research", "coding", "monitoring", "zip_project"]

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, instructions TEXT NOT NULL,
            kind TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, result TEXT, error TEXT
        )""")
        db.commit()

init_db()

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    instructions: str = Field(min_length=1, max_length=10000)
    kind: KINDS = "general"

def serialize(row):
    return dict(row)

@router.post("", status_code=201)
def create_task(req: TaskCreate):
    task_id = str(uuid.uuid4())
    stamp = now()
    with connect() as db:
        db.execute("INSERT INTO tasks (id,title,instructions,kind,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                   (task_id, req.title.strip(), req.instructions.strip(), req.kind, "pending", stamp, stamp))
        db.commit()
        row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return serialize(row)

@router.get("")
def list_tasks(limit: int = 50):
    if not 1 <= limit <= 100:
        raise HTTPException(400, "limit must be between 1 and 100")
    with connect() as db:
        rows = db.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"tasks": [serialize(row) for row in rows]}

@router.get("/{task_id}")
def get_task(task_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Task not found")
    return serialize(row)

@router.delete("/{task_id}")
def delete_task(task_id: str):
    with connect() as db:
        cur = db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        db.commit()
    if cur.rowcount == 0:
        raise HTTPException(404, "Task not found")
    return {"deleted": True, "id": task_id}
