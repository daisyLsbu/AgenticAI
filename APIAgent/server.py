"""
HTTP wrapper around the local agent — this is what Slack (or anything else)
will talk to in Phase 3. Everything still runs 100% locally through Ollama;
this just puts a small local API in front of agent_core.

Usage:
    uvicorn server:app --host 127.0.0.1 --port 8000

Endpoints:
    GET  /health          -> {"status": "ok"}
    POST /chat            -> body: {"message": "...", "session_id": "...", "model": "..."}
                              returns: {"reply": "...", "session_id": "..."}
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent_core import DEFAULT_MODEL, AgentError, chat_once, load_history, save_history

app = FastAPI(title="Local Ollama Agent")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    model: str = DEFAULT_MODEL


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    history = load_history(req.session_id)
    try:
        reply = chat_once(req.model, history, req.message)
    except AgentError as e:
        raise HTTPException(status_code=502, detail=str(e))

    save_history(req.session_id, history)
    return ChatResponse(reply=reply, session_id=req.session_id)
