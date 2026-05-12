from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from graph.neo4j_client import neo4j_client
from routers import pokemon, team_builder, chat, users

# DB 테이블 생성 및 스키마 업데이트 (간이 마이그레이션)
Base.metadata.create_all(bind=engine)

def update_schema():
    from sqlalchemy import text
    # Try to add each column one by one in separate transactions
    columns_to_add = [
        ("public_repos", "INTEGER DEFAULT 0"),
        ("total_commits", "INTEGER DEFAULT 0"),
        ("total_stars", "INTEGER DEFAULT 0")
    ]
    
    with engine.connect() as conn:
        # Check if users table exists first
        table_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")).scalar()
        if not table_exists:
            print("Users table does not exist yet. create_all will handle it.")
            return

        for col_name, col_type in columns_to_add:
            try:
                # We use individual begin() blocks for each column to ensure one failure doesn't block others
                with engine.begin() as transaction_conn:
                    # Check if column exists to avoid noisy error logs
                    check_sql = f"SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='{col_name}'"
                    col_exists = transaction_conn.execute(text(check_sql)).fetchone()
                    
                    if not col_exists:
                        print(f"Adding column {col_name} to users table...")
                        transaction_conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            except Exception as e:
                print(f"Skipping {col_name} addition: {e}")

        # Update github_id type to BIGINT
        try:
            with engine.begin() as transaction_conn:
                transaction_conn.execute(text("ALTER TABLE users ALTER COLUMN github_id TYPE BIGINT"))
        except Exception as e:
            print(f"Skipping github_id type update: {e}")

try:
    update_schema()
except Exception as e:
    print(f"Migration failed: {e}")

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
