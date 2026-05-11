"""
임베딩 초기화 스크립트
======================
새 환경(컴퓨터)에서 DB를 처음 구성할 때 1회 실행합니다.

실행 방법 (frontend/ 디렉터리에서):
  python -m common.ingest

수행 작업:
  1. flavor_text, pokemon_knowledge 테이블의 embedding 컬럼 채우기
  2. BM25 전문 검색용 GIN 인덱스 생성

이미 embedding이 있는 행은 건너뜁니다 (WHERE embedding IS NULL).
"""

import os
import psycopg2
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

DB_CONN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pokemon_db"
)
if DB_CONN.startswith("postgres://"):
    DB_CONN = DB_CONN.replace("postgres://", "postgresql://", 1)

embeddings = OpenAIEmbeddings()


def ingest_embeddings():
    conn = psycopg2.connect(DB_CONN)
    cur  = conn.cursor()

    # ── BM25용 GIN 인덱스 (없을 때만 생성) ─────────────────────
    print("BM25 GIN 인덱스 확인/생성 중...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_flavor_text_fts
        ON flavor_text USING GIN (to_tsvector('simple', content));
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_pokemon_knowledge_fts
        ON pokemon_knowledge USING GIN (to_tsvector('simple', content));
    """)
    conn.commit()
    print("✅ GIN 인덱스 준비 완료")

    # ── flavor_text 임베딩 ───────────────────────────────────────
    cur.execute("""
        SELECT ft.id, p.name, ft.version_name, ft.content
        FROM flavor_text ft
        JOIN species s ON ft.species_id = s.id
        JOIN pokemon p ON s.pokemon_id  = p.id
        WHERE ft.embedding IS NULL AND ft.content IS NOT NULL
    """)
    flavor_rows = cur.fetchall()
    print(f"flavor_text 임베딩 대상: {len(flavor_rows)}개")

    for ft_id, name, version, content in flavor_rows:
        text   = f"포켓몬: {name} (버전: {version})\n{content}"
        vector = embeddings.embed_query(text)
        cur.execute("UPDATE flavor_text SET embedding = %s WHERE id = %s", (vector, ft_id))

    # ── pokemon_knowledge 임베딩 ─────────────────────────────────
    # ctid로 행을 개별 식별 — pokemon_id가 PK가 아니라 중복 행이 있을 수 있음
    cur.execute("""
        SELECT pk.ctid, p.name, pk.content
        FROM pokemon_knowledge pk
        JOIN pokemon p ON pk.pokemon_id = p.id
        WHERE pk.embedding IS NULL AND pk.content IS NOT NULL
    """)
    knowledge_rows = cur.fetchall()
    print(f"pokemon_knowledge 임베딩 대상: {len(knowledge_rows)}개")

    for row_ctid, name, content in knowledge_rows:
        text   = f"포켓몬: {name}\n{content}"
        vector = embeddings.embed_query(text)
        cur.execute(
            "UPDATE pokemon_knowledge SET embedding = %s WHERE ctid = %s::tid",
            (vector, row_ctid)
        )

    conn.commit()
    conn.close()
    print(f"✅ 임베딩 완료 — flavor_text {len(flavor_rows)}개 / knowledge {len(knowledge_rows)}개")


if __name__ == "__main__":
    ingest_embeddings()
