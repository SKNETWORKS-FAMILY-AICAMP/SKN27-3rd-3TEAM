import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chatbot.pokemon_agent import chat_with_tools, MODELS, DEFAULT_MODEL
from chatbot.chat_history import (
    init_tables, create_session, save_message,
    load_sessions, load_messages, delete_session,
)

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])

try:
    init_tables()
except Exception:
    pass


# ── 스키마 ────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    history: list[dict] = []
    model: str = DEFAULT_MODEL
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    used_tools: list[str]
    session_id: int


# ── 엔드포인트 ────────────────────────────────────────────────

@router.get("/models")
def get_models():
    return {"models": list(MODELS.keys()), "default": DEFAULT_MODEL}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.model not in MODELS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 모델: {req.model}")

    session_id = req.session_id
    if session_id is None:
        session_id = create_session(req.query, req.model)

    save_message(session_id, "user", req.query)

    try:
        answer, used_tools = await asyncio.to_thread(
            chat_with_tools, req.query, req.history, req.model
        )
    except Exception as e:
        answer = f"⚠️ 오류 ({type(e).__name__}): {e}"
        used_tools = []

    save_message(session_id, "assistant", answer, used_tools)

    return ChatResponse(answer=answer, used_tools=used_tools, session_id=session_id)


@router.get("/sessions")
def get_sessions():
    return load_sessions()


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int):
    return load_messages(session_id)


@router.delete("/sessions/{session_id}")
def remove_session(session_id: int):
    delete_session(session_id)
    return {"ok": True}
