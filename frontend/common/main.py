# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import app as langgraph_app

api = FastAPI(title="포켓몬 챗봇")

# CORS (프론트엔드 연결용)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer : str
    intent : str

@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = langgraph_app.invoke({
        "question"    : request.question,
        "retry_count" : 0
    })
    return {
        "answer" : result["answer"],
        "intent" : result["intent"],
        "sql"    : result.get("sql","")
    }

@api.get("/health")
def health():
    return {"status": "ok"}