import asyncio
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chatbot.pokemon_agent import chat_with_tools, astream_chat, MODELS, DEFAULT_MODEL
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
    user_id: Optional[str] = None

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
        session_id = create_session(req.query, req.model, user_id=req.user_id)

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


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if req.model not in MODELS:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 모델: {req.model}")

    session_id = req.session_id
    if session_id is None:
        session_id = create_session(req.query, req.model, user_id=req.user_id)

    save_message(session_id, "user", req.query)

    async def event_generator():
        full_answer = ""
        used_tools = []

        # 즉시 keepalive 전송 — Railway 프록시가 첫 바이트 없으면 502 반환하는 문제 방지
        yield ": keepalive\n\n"

        queue: asyncio.Queue = asyncio.Queue()

        async def produce():
            try:
                async for chunk in astream_chat(req.query, req.history, req.model):
                    await queue.put(("chunk", chunk))
            except Exception as e:
                await queue.put(("error", str(e)))
            finally:
                await queue.put(("done", None))

        task = asyncio.create_task(produce())
        try:
            while True:
                try:
                    kind, value = await asyncio.wait_for(queue.get(), timeout=10.0)
                except asyncio.TimeoutError:
                    # 처리 중 keepalive — 30s 프록시 타임아웃 방지
                    yield ": keepalive\n\n"
                    continue

                if kind == "done":
                    break
                elif kind == "error":
                    yield f"data: {json.dumps({'type': 'error', 'content': value})}\n\n"
                    break
                else:
                    chunk = value
                    if chunk.startswith("\n\n[USED_TOOLS]:"):
                        tools_str = chunk.replace("\n\n[USED_TOOLS]:", "")
                        used_tools = tools_str.split(",")
                        yield f"data: {json.dumps({'type': 'tools', 'content': used_tools})}\n\n"
                    else:
                        full_answer += chunk
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        save_message(session_id, "assistant", full_answer, used_tools)
        yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},  # nginx/Railway 프록시 버퍼링 비활성화
    )


@router.get("/sessions")
def get_sessions(user_id: Optional[str] = Query(default=None)):
    return load_sessions(user_id=user_id)


@router.get("/sessions/{session_id}/messages")
def get_messages(session_id: int):
    return load_messages(session_id)


@router.delete("/sessions/{session_id}")
def remove_session(session_id: int):
    delete_session(session_id)
    return {"ok": True}
