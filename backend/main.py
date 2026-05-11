from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from graph.neo4j_client import neo4j_client
from routers import pokemon, team_builder, chat, users

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pokemon App Backend",
    description="FastAPI Backend for Pokemon Data & RAG",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(pokemon.router)
app.include_router(team_builder.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Pokemon App API", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
def shutdown_event():
    """
    FastAPI 앱 종료 시 Neo4j driver 연결을 닫습니다.

    목적:
        백엔드 컨테이너가 재시작되거나 종료될 때
        Neo4j 연결 리소스가 남지 않도록 정리합니다.
    """
    neo4j_client.close()
