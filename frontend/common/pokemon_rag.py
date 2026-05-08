"""
포켓몬 챗봇 - LangGraph + Hybrid RAG
실제 DB 구조 (models.py) 기반으로 작성

테이블 구조:
  pokemon → pokemon_stats (1:1)
  pokemon → pokemon_types → types (N:M)
  pokemon → species → flavor_text (비정형, embedding 있음)
  pokemon → pokemon_knowledge (비정형, embedding 있음)
"""

import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()
from typing import TypedDict, List

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_community.tools import TavilySearchResults
from langgraph.graph import StateGraph, START, END


# ══════════════════════════════════════════════════════════
# 설정
# ══════════════════════════════════════════════════════════

DB_CONN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pokemon_db"  # 포트 5433
)
# psycopg2 호환
if DB_CONN.startswith("postgres://"):
    DB_CONN = DB_CONN.replace("postgres://", "postgresql://", 1)

llm        = ChatOpenAI(model="gpt-4o-mini", temperature=0)  #gemma3:4b  ,gpt-4o-mini
embeddings = OpenAIEmbeddings()
search     = TavilySearchResults(max_results=3)


# ══════════════════════════════════════════════════════════
# 실제 DB 스키마 (models.py 기반)
# ══════════════════════════════════════════════════════════

SCHEMA = """
테이블: pokemon
컬럼: id, name, height, weight, base_exp, image_url, cry_url, is_default

테이블: pokemon_stats  (pokemon_id 로 pokemon 과 1:1 조인)
컬럼: pokemon_id(FK), hp, attack, defense, sp_attack, sp_defense, speed

테이블: types
컬럼: id, name

테이블: pokemon_types  (pokemon ↔ types 중간 테이블)
컬럼: pokemon_id(FK), type_id(FK), slot

테이블: species  (pokemon_id 로 pokemon 과 1:1 조인)
컬럼: id, pokemon_id(FK), generation, capture_rate

테이블: flavor_text  (비정형 도감 설명 — embedding 컬럼 있음)
컬럼: id, species_id(FK), version_name, content, embedding

테이블: pokemon_knowledge  (비정형 추가 지식 — embedding 컬럼 있음)
컬럼: pokemon_id(FK), content, embedding

─── 자주 쓰는 조인 패턴 ───────────────────────────────────

-- 타입으로 포켓몬 검색
SELECT p.name FROM pokemon p
JOIN pokemon_types pt ON p.id = pt.pokemon_id
JOIN types t ON pt.type_id = t.id
WHERE t.name = '불꽃';

-- 스탯으로 검색
SELECT p.name, ps.attack FROM pokemon p
JOIN pokemon_stats ps ON p.id = ps.pokemon_id
ORDER BY ps.attack DESC LIMIT 5;

-- 세대/포획률
SELECT p.name, s.generation, s.capture_rate FROM pokemon p
JOIN species s ON p.id = s.pokemon_id
WHERE s.generation = 1;

-- 도감 설명 포함
SELECT p.name, ft.content FROM pokemon p
JOIN species s ON p.id = s.pokemon_id
JOIN flavor_text ft ON s.id = ft.species_id
WHERE p.name ILIKE '%피카츄%'
LIMIT 1;
"""


# ══════════════════════════════════════════════════════════
# GraphState
# ══════════════════════════════════════════════════════════

class GraphState(TypedDict):
    query:       str
    route:       str          # "sql" | "embedding"
    sql:         str
    db_result:   str          # SQL 결과 (정형)
    vector_docs: List[Document]  # 벡터 검색 결과 (비정형)
    web_result:  str          # 웹 검색 결과 (fallback)
    context:     str          # 통합 컨텍스트
    answer:      str


# ══════════════════════════════════════════════════════════
# Ingestion — 최초 1회만 실행
# flavor_text, pokemon_knowledge 의 embedding 컬럼을 채움
# ══════════════════════════════════════════════════════════

def ingest_embeddings():
    """
    DB 의 비정형 텍스트에 embedding 을 생성해서 저장합니다.
    embedding IS NULL 인 행만 처리하므로 여러 번 실행해도 안전합니다.
    """
    conn = psycopg2.connect(DB_CONN)
    cur  = conn.cursor()

    # 1. flavor_text ─────────────────────────────────────
    cur.execute("""
        SELECT ft.id, p.name, ft.version_name, ft.content
        FROM flavor_text ft
        JOIN species s ON ft.species_id = s.id
        JOIN pokemon p ON s.pokemon_id  = p.id
        WHERE ft.embedding IS NULL
          AND ft.content    IS NOT NULL
    """)
    flavor_rows = cur.fetchall()
    print(f"flavor_text 임베딩 대상: {len(flavor_rows)}개")

    for ft_id, name, version, content in flavor_rows:
        text   = f"포켓몬: {name} (버전: {version})\n{content}"
        vector = embeddings.embed_query(text)
        cur.execute(
            "UPDATE flavor_text SET embedding = %s WHERE id = %s",
            (vector, ft_id)
        )

    # 2. pokemon_knowledge ───────────────────────────────
    cur.execute("""
        SELECT pk.pokemon_id, p.name, pk.content
        FROM pokemon_knowledge pk
        JOIN pokemon p ON pk.pokemon_id = p.id
        WHERE pk.embedding IS NULL
          AND pk.content    IS NOT NULL
    """)
    knowledge_rows = cur.fetchall()
    print(f"pokemon_knowledge 임베딩 대상: {len(knowledge_rows)}개")

    for pokemon_id, name, content in knowledge_rows:
        text   = f"포켓몬: {name}\n{content}"
        vector = embeddings.embed_query(text)
        cur.execute(
            "UPDATE pokemon_knowledge SET embedding = %s WHERE pokemon_id = %s",
            (vector, pokemon_id)
        )

    conn.commit()
    conn.close()
    print(f"✅ 임베딩 완료 — flavor_text {len(flavor_rows)}개 / knowledge {len(knowledge_rows)}개")


# ══════════════════════════════════════════════════════════
# 노드 1: query_classifier
# ══════════════════════════════════════════════════════════

classify_prompt = ChatPromptTemplate.from_messages([
    ("system", """포켓몬 질문을 분류하세요.

'sql' 분류 기준 (수치/조건/비교/순위/타입/세대):
  예) "피카츄 공격력은?" / "불꽃타입 중 빠른 포켓몬" / "1세대 포켓몬 목록"
      "hp 가장 높은 포켓몬" / "물 타입이면서 방어력 80 이상"

'embedding' 분류 기준 (느낌/묘사/스토리/성격/배경):
  예) "귀엽고 작은 포켓몬 추천해줘" / "바다 느낌 나는 포켓몬"
      "피카츄는 어떤 성격이야?" / "불꽃에서 살아가는 포켓몬 이야기"

반드시 'sql' 또는 'embedding' 중 하나만 출력하세요."""),
    ("human", "{query}")
])

def query_classifier(state: GraphState) -> GraphState:
    chain  = classify_prompt | llm | StrOutputParser()
    result = chain.invoke({"query": state["query"]}).strip().lower()
    route  = "sql" if "sql" in result else "embedding"
    print(f"🔀 분류: {route}")
    return {"route": route}

def route_by_type(state: GraphState) -> str:
    return state["route"]


# ══════════════════════════════════════════════════════════
# 노드 2a: generate_sql
# ══════════════════════════════════════════════════════════

sql_prompt = ChatPromptTemplate.from_messages([
    ("system", f"""PostgreSQL 전문가입니다. 스키마를 참고해 SQL 만 출력하세요.

{SCHEMA}

규칙:
- SELECT 만 허용 (INSERT/UPDATE/DELETE 금지)
- 설명 없이 SQL 만 출력
- LIMIT 10 이하
- 타입 검색 시 반드시 pokemon_types → types 조인 사용
- 스탯 검색 시 반드시 pokemon_stats 조인 사용"""),
    ("human", "{query}")
])

def generate_sql(state: GraphState) -> GraphState:
    chain = sql_prompt | llm | StrOutputParser()
    sql   = chain.invoke({"query": state["query"]}).strip()
    # 마크다운 코드블록 제거
    sql   = sql.replace("```sql", "").replace("```", "").strip()
    print(f"🗄️  SQL: {sql}")
    return {"sql": sql}


# ══════════════════════════════════════════════════════════
# 노드 2b: execute_sql
# ══════════════════════════════════════════════════════════

def execute_sql(state: GraphState) -> GraphState:
    try:
        conn = psycopg2.connect(DB_CONN)
        cur  = conn.cursor()
        cur.execute(state["sql"])
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        conn.close()

        if not rows:
            print("⚠️  SQL 결과 없음 → fallback")
            return {"db_result": "", "route": "fallback"}

        result = json.dumps(
            [dict(zip(cols, row)) for row in rows],
            ensure_ascii=False,
            default=str  # datetime 등 직렬화
        )
        print(f"✅ SQL 결과: {len(rows)}행")
        return {"db_result": result, "route": "sql_done"}

    except Exception as e:
        print(f"❌ SQL 실패: {e}")
        return {"db_result": "", "route": "fallback"}

def route_after_sql(state: GraphState) -> str:
    return state["route"]


# ══════════════════════════════════════════════════════════
# 노드 3: embedding_search
# pgvector <=> 연산자로 코사인 유사도 검색
# flavor_text + pokemon_knowledge 동시 검색
# ══════════════════════════════════════════════════════════

def embedding_search(state: GraphState) -> GraphState:
    try:
        query_vector = embeddings.embed_query(state["query"])

        conn = psycopg2.connect(DB_CONN)
        cur  = conn.cursor()

        # flavor_text 검색
        cur.execute("""
            SELECT p.name,
                   ft.version_name,
                   ft.content,
                   ft.embedding <=> %s::vector AS distance
            FROM flavor_text ft
            JOIN species s ON ft.species_id = s.id
            JOIN pokemon p ON s.pokemon_id  = p.id
            WHERE ft.embedding IS NOT NULL
            ORDER BY distance
            LIMIT 4
        """, (query_vector,))
        flavor_rows = cur.fetchall()

        # pokemon_knowledge 검색
        cur.execute("""
            SELECT p.name,
                   'knowledge'        AS version_name,
                   pk.content,
                   pk.embedding <=> %s::vector AS distance
            FROM pokemon_knowledge pk
            JOIN pokemon p ON pk.pokemon_id = p.id
            WHERE pk.embedding IS NOT NULL
            ORDER BY distance
            LIMIT 4
        """, (query_vector,))
        knowledge_rows = cur.fetchall()
        conn.close()

        all_rows = flavor_rows + knowledge_rows
        # 거리 기준 재정렬 후 상위 5개만
        all_rows.sort(key=lambda x: x[3])
        all_rows = all_rows[:5]

        if not all_rows:
            print("⚠️  Embedding 결과 없음 → fallback")
            return {"vector_docs": [], "route": "fallback"}

        docs = [
            Document(
                page_content=f"[{name} / {version}]\n{content}",
                metadata={"pokemon_name": name, "source": version, "distance": float(dist)}
            )
            for name, version, content, dist in all_rows
        ]
        print(f"✅ Embedding 검색: {len(docs)}개")
        return {"vector_docs": docs, "route": "embedding_done"}

    except Exception as e:
        print(f"❌ Embedding 실패: {e}")
        return {"vector_docs": [], "route": "fallback"}

def route_after_embedding(state: GraphState) -> str:
    return state["route"]


# ══════════════════════════════════════════════════════════
# 노드 4: web_search (fallback)
# ══════════════════════════════════════════════════════════

def web_search(state: GraphState) -> GraphState:
    print("🌐 fallback → 웹 검색")
    try:
        results  = search.invoke(state["query"] + " 포켓몬")
        web_text = "\n\n".join([r["content"] for r in results])
    except Exception as e:
        web_text = f"웹 검색 실패: {e}"
    return {"web_result": web_text}


# ══════════════════════════════════════════════════════════
# 노드 5: context_merger
# ══════════════════════════════════════════════════════════

def context_merger(state: GraphState) -> GraphState:
    parts = []

    if state.get("db_result"):
        parts.append(f"[DB 정형 데이터]\n{state['db_result']}")

    if state.get("vector_docs"):
        docs_text = "\n\n".join(
            [doc.page_content for doc in state["vector_docs"]]
        )
        parts.append(f"[도감/지식 검색 결과]\n{docs_text}")

    if state.get("web_result"):
        parts.append(f"[웹 검색 결과 (DB 미보유 정보)]\n{state['web_result']}")

    context = "\n\n".join(parts) if parts else "관련 정보를 찾지 못했습니다."
    return {"context": context}


# ══════════════════════════════════════════════════════════
# 노드 6: generator
# ══════════════════════════════════════════════════════════

answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """당신은 친절한 포켓몬 박사입니다.
주어진 컨텍스트를 바탕으로 질문에 정확하고 친절하게 답하세요.
컨텍스트에 없는 내용은 절대 지어내지 마세요.
웹 검색 결과를 사용한 경우 "DB에 없어 웹에서 찾았습니다" 라고 먼저 알려주세요."""),
    ("human", "질문: {query}\n\n컨텍스트:\n{context}")
])

def generator(state: GraphState) -> GraphState:
    chain  = answer_prompt | llm | StrOutputParser()
    answer = chain.invoke({
        "query":   state["query"],
        "context": state["context"]
    })
    return {"answer": answer}


# ══════════════════════════════════════════════════════════
# 그래프 조립
# ══════════════════════════════════════════════════════════

def build_graph():
    workflow = StateGraph(GraphState)

    # 노드 등록
    workflow.add_node("query_classifier",  query_classifier)
    workflow.add_node("generate_sql",      generate_sql)
    workflow.add_node("execute_sql",       execute_sql)
    workflow.add_node("embedding_search",  embedding_search)
    workflow.add_node("web_search",        web_search)
    workflow.add_node("context_merger",    context_merger)
    workflow.add_node("generator",         generator)

    # 시작
    workflow.add_edge(START, "query_classifier")

    # sql / embedding 분기
    workflow.add_conditional_edges(
        "query_classifier",
        route_by_type,
        {
            "sql":       "generate_sql",
            "embedding": "embedding_search",
        }
    )

    # SQL 경로
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_conditional_edges(
        "execute_sql",
        route_after_sql,
        {
            "sql_done": "context_merger",
            "fallback": "web_search",
        }
    )

    # Embedding 경로
    workflow.add_conditional_edges(
        "embedding_search",
        route_after_embedding,
        {
            "embedding_done": "context_merger",
            "fallback":       "web_search",
        }
    )

    # 공통 후반부
    workflow.add_edge("web_search",     "context_merger")
    workflow.add_edge("context_merger", "generator")
    workflow.add_edge("generator",      END)

    return workflow.compile()


app = build_graph()


# ══════════════════════════════════════════════════════════
# 실행 헬퍼
# ══════════════════════════════════════════════════════════

def chat(query: str) -> str:
    result = app.invoke({
        "query":       query,
        "route":       "",
        "sql":         "",
        "db_result":   "",
        "vector_docs": [],
        "web_result":  "",
        "context":     "",
        "answer":      "",
    })
    return result["answer"]


# ══════════════════════════════════════════════════════════
# FastAPI 라우터로 연결하는 예시
# main.py 의 app.include_router() 에 추가 가능
# ══════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    query:  str
    answer: str

@router.post("/", response_model=ChatResponse)
def pokemon_chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="질문을 입력하세요.")
    answer = chat(req.query)
    return ChatResponse(query=req.query, answer=answer)


# ══════════════════════════════════════════════════════════
# 직접 실행 테스트
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 임베딩 최초 실행 시 아래 주석 해제
    # ingest_embeddings()

    tests = [
        "불꽃 타입 중 공격력 가장 높은 포켓몬 3마리는?",   # SQL 경로
        "귀엽고 작은 느낌의 포켓몬 추천해줘",              # Embedding 경로
        "피카츄는 어떤 성격이야?",                         # Embedding 경로
        "1세대 포켓몬 중 hp 가장 높은 건?",               # SQL 경로
    ]

    for q in tests:
        print(f"\n{'='*50}")
        print(f"Q: {q}")
        print(f"A: {chat(q)}")