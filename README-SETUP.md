# My AI Agent — starter setup

This repository now contains a responsive chat UI and a FastAPI backend for OpenAI, Anthropic Claude, and Google Gemini. It is a starter, not yet a native Android APK. Phone usage statistics, notification reading, background wake word, and web search still need separate implementations.

## Run the backend locally
1. Install Python 3.11 or newer.
2. From the repository root run: `python -m venv .venv`
3. Activate the environment and run: `pip install -r backend/requirements.txt`
4. Set API keys as environment variables on the backend host. Never commit real keys.
5. Run: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
6. Serve `index.html` from the same origin as the API, or configure CORS_ORIGINS for the exact frontend origin.

## Model names
Model availability changes. Enter a model name supported by your provider account. API access and billing are separate from ChatGPT/Claude/Gemini consumer subscriptions.

## Security before public deployment
- Keep this repository private while developing.
- Store keys only in backend environment variables / hosting secrets.
- Add authentication and rate limiting before exposing the API publicly.
- Restrict CORS_ORIGINS to the deployed frontend origin.
- Do not use a publicly exposed unauthenticated endpoint for a personal API.

## Current status
The UI has text chat, provider selection, browser speech input (where supported), and speech output. Real AI replies require a deployed backend with configured provider keys. No code has been built into an APK or end-to-end tested in this chat.
