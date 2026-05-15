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
"""
ingest_embeddings() — flavor_text.embedding 컬럼 채움 (psycopg2 직접)
index_vectorstore() — langchain_pg_embedding 테이블에 PGVector 인덱싱
"""
import json
import os
import psycopg2
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

load_dotenv()

DB_CONN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pokemon_db"
)
if DB_CONN.startswith("postgres://"):
    DB_CONN = DB_CONN.replace("postgres://", "postgresql://", 1)

embeddings = OpenAIEmbeddings()


def init_db_extensions():
    """필요한 DB 확장 모듈(vector, pg_trgm)을 활성화합니다."""
    try:
        conn = psycopg2.connect(DB_CONN)
        conn.autocommit = True
        cur = conn.cursor()
        print("🔧 DB 확장 모듈 활성화 중 (vector, pg_trgm)...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        
        # ↓ 추가
        print("🔧 pg_trgm 인덱스 생성 중...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_flavor_text_trgm
            ON flavor_text USING GIN (content gin_trgm_ops)
        """)
        print("✅ pg_trgm 인덱스 생성 완료")
        # ↑ 추가
        
        cur.close()
        conn.close()
        print("✅ DB 확장 모듈 활성화 완료")
    except Exception as e:
        print(f"⚠️ DB 확장 모듈 활성화 실패: {e}")


def index_vectorstore():
    """JSON 파일을 PGVector(langchain_pg_embedding)에 인덱싱합니다. 1회만 실행하면 됩니다."""
    file_path = os.path.join(
        os.path.dirname(__file__),
        "../../database/common/data/processed/flavor_text.json"
    )
    file_path = os.path.normpath(file_path)

    vectorstore = PGVector(
        connection_string=DB_CONN,
        embedding_function=embeddings,
        collection_name="flavor_text",
    )

    existing = vectorstore.similarity_search("포켓몬", k=1)
    if existing:
        print("⏭ PGVector 컬렉션에 이미 데이터가 있습니다. 인덱싱을 건너뜁니다.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    documents = [
        Document(page_content=f"{row['species_id']}: {row['version_name']} {row['content']}")
        for row in data
    ]
    print(f"PGVector 인덱싱 시작 — {len(documents)}개 문서")
    vectorstore.add_documents(documents)
    print(f"✅ PGVector 인덱싱 완료 — {len(documents)}개")


if __name__ == "__main__":
    init_db_extensions()  # DB 확장 모듈 먼저 활성화
    #ingest_embeddings()
    index_vectorstore()
