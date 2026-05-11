from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from graph.neo4j_client import neo4j_client
from routers import pokemon, team_builder, chat, users

# DB 테이블 생성 및 스키마 업데이트 (간이 마이그레이션)
Base.metadata.create_all(bind=engine)

def update_schema():
    from sqlalchemy import text
    with engine.begin() as conn:  # begin()을 사용하여 자동 커밋/롤백 처리
        try:
            # public_repos 컬럼이 있는지 확인
            conn.execute(text("SELECT public_repos FROM users LIMIT 1"))
        except Exception:
            print("Migrating: Adding GitHub stats columns to users table...")
            # PostgreSQL에서는 IF NOT EXISTS를 지원하므로 안전하게 추가 가능
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS public_repos INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_commits INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_stars INTEGER DEFAULT 0"))
            print("Migration complete.")

try:
    update_schema()
except Exception as e:
    print(f"Migration failed (possibly already applied): {e}")

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
app.include_router(users.router)

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
