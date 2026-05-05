from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import pokemon

# DB 테이블 생성 (schema.sql로 이미 생성되므로 안전한 no-op)
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

@app.get("/")
def read_root():
    return {"message": "Welcome to Pokemon App API", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
