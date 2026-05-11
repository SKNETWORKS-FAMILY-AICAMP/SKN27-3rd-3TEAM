"""
채팅 세션 DB 저장/조회 모듈
============================
테이블:
  chat_sessions  — 대화 세션 (제목, 모델, 생성일)
  chat_messages  — 메시지 (role, content, used_tools)
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_CONN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pokemon_db"
)
if DB_CONN.startswith("postgres://"):
    DB_CONN = DB_CONN.replace("postgres://", "postgresql://", 1)


def _connect():
    return psycopg2.connect(DB_CONN)


def init_tables() -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id         SERIAL PRIMARY KEY,
                    title      TEXT        NOT NULL,
                    model      TEXT        NOT NULL,
                    created_at TIMESTAMP   DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id         SERIAL  PRIMARY KEY,
                    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role       TEXT    NOT NULL,
                    content    TEXT    NOT NULL,
                    used_tools TEXT[]  DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()


def create_session(title: str, model: str) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_sessions (title, model) VALUES (%s, %s) RETURNING id",
                (title[:60], model),
            )
            session_id = cur.fetchone()[0]
        conn.commit()
    return session_id


def save_message(session_id: int, role: str, content: str, used_tools: list | None = None) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_messages (session_id, role, content, used_tools) VALUES (%s, %s, %s, %s)",
                (session_id, role, content, used_tools or []),
            )
        conn.commit()


def load_sessions(limit: int = 60) -> list[dict]:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, title, model, created_at
                FROM chat_sessions
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            return [dict(r) for r in cur.fetchall()]


def load_messages(session_id: int) -> list[dict]:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT role, content, used_tools
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY created_at
            """, (session_id,))
            return [dict(r) for r in cur.fetchall()]


def delete_session(session_id: int) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))
        conn.commit()
