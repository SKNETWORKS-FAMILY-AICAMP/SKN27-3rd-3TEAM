"""
포켓몬 챗봇 - Tool-calling Agent (LangGraph)
=============================================
변경 사항:
  - query_classifier 제거 → LLM이 직접 툴을 선택
  - SQL 실패 시 LLM이 오류 메시지를 보고 SQL 수정 후 재시도 (최대 3회)
  - SQL + 벡터 동시 사용 가능 (복합 질문 처리)
  - 답변 품질 향상을 위한 강화된 system prompt
  - 웹검색은 DB에 정말 없을 때만 사용
  - [NEW] 하이브리드 검색: BM25(키워드) + 벡터 검색 → RRF 융합
  - [NEW] Cross-encoder Re-ranking (BAAI/bge-reranker-v2-m3): 상위 후보를 재정렬해 LLM에 최적 컨텍스트 전달
         (Cohere API 의존성 제거 → 로컬 추론, 무료, 한국어 지원)
  - [NEW] Neo4j 툴 연동: 진화 체인(search_evolution_chain) · 타입 상성(search_type_relations) 그래프 검색
  - [NEW] 멀티턴 대화 히스토리 지원 (chat_with_tools 에 history 파라미터 추가)

테이블 구조:
  pokemon → pokemon_stats (1:1)
  pokemon → pokemon_types → types (N:M)
  pokemon → species → flavor_text (비정형, embedding 있음, tsvector 인덱스 있음)
  pokemon → pokemon_knowledge (비정형, embedding 있음, tsvector 인덱스 있음)
"""

import os
import json
import threading
import psycopg2
from dotenv import load_dotenv
from typing import TypedDict, List, Annotated
import operator

# GPU 자동 감지 — torch 없으면 CPU 폴백
try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    DEVICE = "cpu"

from sentence_transformers import CrossEncoder

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Neo4j 툴 — pokemon_neo4j.py 에서 가져옴
try:
    from common.pokemon_neo4j import search_evolution_chain, search_type_relations
except ImportError:
    from pokemon_neo4j import search_evolution_chain, search_type_relations


# ══════════════════════════════════════════════════════════
# 설정
# ══════════════════════════════════════════════════════════

DB_CONN = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pokemon_db"
)
if DB_CONN.startswith("postgres://"):
    DB_CONN = DB_CONN.replace("postgres://", "postgresql://", 1)

llm        = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings()
tavily     = TavilySearchResults(max_results=3)

# Cross-encoder: 첫 호출 시 모델 자동 다운로드 (~1GB), 이후 로컬 캐시 사용
# BAAI/bge-reranker-v2-m3 — 다국어(한국어 포함) 지원, 무료
_cross_encoder: CrossEncoder | None = None
_cross_encoder_lock = threading.Lock()

def get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        with _cross_encoder_lock:
            if _cross_encoder is None:
                print(f"🔄 Cross-encoder 모델 로딩 중... (device={DEVICE}, 최초 1회만)")
                _cross_encoder = CrossEncoder(
                    "BAAI/bge-reranker-v2-m3",
                    max_length=512,
                    device=DEVICE,
                )
                print("✅ Cross-encoder 로딩 완료")
    return _cross_encoder

# 하이브리드 검색 후보 수 (BM25·벡터 각각) / Re-rank 후 최종 전달 수
HYBRID_CANDIDATE_K  = 10
RERANK_CANDIDATE_N  = HYBRID_CANDIDATE_K * 2   # Cross-encoder 입력 후보 수
RERANK_TOP_N        = 5                         # LLM에 전달할 최종 문서 수


# ══════════════════════════════════════════════════════════
# DB 스키마 (툴 description 에서 LLM이 참조)
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

SYSTEM_PROMPT = f"""당신은 세계 최고의 포켓몬 박사입니다. 풍부하고 정확한 정보를 바탕으로 답변합니다.

## 답변 원칙
1. **항상 툴을 먼저 사용하세요.** 질문에 답하기 전에 반드시 관련 툴을 호출해 데이터를 확인합니다.
2. **복합 질문은 여러 툴을 함께 활용하세요.**
   - 수치/조건/비교 → `search_pokemon_db` (SQL)
   - 느낌/묘사/성격/배경 → `search_pokemon_knowledge` (벡터)
   - 진화 경로/조건 → `search_evolution_chain` (Neo4j 그래프)
   - 타입 상성/약점 → `search_type_relations` (Neo4j 그래프)
   - "불꽃타입이면서 귀여운 포켓몬" 같은 복합 질문 → 여러 툴 함께 사용
3. **DB에 없는 정보만** `web_search`를 사용하고, 사용 시 "웹에서 찾은 정보입니다"를 명시합니다.
4. SQL 오류가 발생하면 오류 메시지를 분석해 SQL을 수정 후 재시도합니다.

## 답변 스타일
- 친절하고 열정적으로 답변합니다.
- 수치 데이터는 표 형태로 정리합니다.
- 포켓몬의 특징을 생생하게 설명합니다.
- 컨텍스트에 없는 내용은 절대 지어내지 않습니다.

## DB 스키마
{SCHEMA}
"""


# ══════════════════════════════════════════════════════════
# Tools
# ══════════════════════════════════════════════════════════

@tool
def search_pokemon_db(sql: str) -> str:
    """
    PostgreSQL DB에서 포켓몬 정형 데이터를 조회합니다.
    수치, 타입, 스탯, 세대, 포획률 등 구조화된 정보 검색에 사용하세요.
    SELECT 문만 허용됩니다. LIMIT 10 이하를 권장합니다.

    예시 쿼리:
      - 공격력 높은 포켓몬: SELECT p.name, ps.attack FROM pokemon p JOIN pokemon_stats ps ON p.id = ps.pokemon_id ORDER BY ps.attack DESC LIMIT 5
      - 불꽃 타입: SELECT p.name FROM pokemon p JOIN pokemon_types pt ON p.id = pt.pokemon_id JOIN types t ON pt.type_id = t.id WHERE t.name = '불꽃'
    """
    sql = sql.replace("```sql", "").replace("```", "").strip()

    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        return "오류: SELECT 문만 허용됩니다."
    for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER"]:
        if forbidden in sql_upper:
            return f"오류: {forbidden} 명령은 허용되지 않습니다."

    try:
        conn = psycopg2.connect(DB_CONN)
        cur  = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        conn.close()

        if not rows:
            return "조회 결과가 없습니다. 다른 조건으로 시도해보세요."

        result = json.dumps(
            [dict(zip(cols, row)) for row in rows],
            ensure_ascii=False,
            default=str
        )
        return f"✅ {len(rows)}개 결과:\n{result}"

    except Exception as e:
        return f"SQL 오류: {e}\n힌트: 위 오류를 분석해 SQL을 수정한 후 재시도하세요."


def _rrf_merge(
    bm25_rows: list,
    vec_rows:  list,
    k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — BM25 순위와 벡터 순위를 합산해 단일 리스트로 융합합니다.
    동일 content가 두 리스트에 모두 있으면 점수가 더 높아져 상위에 오릅니다.
    """
    scores: dict[str, dict] = {}

    for rank, (name, source, content) in enumerate(bm25_rows):
        key = content[:80]
        if key not in scores:
            scores[key] = {"name": name, "source": source, "content": content, "score": 0.0}
        scores[key]["score"] += 1.0 / (k + rank + 1)

    for rank, (name, source, content) in enumerate(vec_rows):
        key = content[:80]
        if key not in scores:
            scores[key] = {"name": name, "source": source, "content": content, "score": 0.0}
        scores[key]["score"] += 1.0 / (k + rank + 1)

    return sorted(scores.values(), key=lambda x: x["score"], reverse=True)


@tool
def search_pokemon_knowledge(query: str) -> str:
    """
    포켓몬의 도감 설명, 성격, 배경, 느낌 등 비정형 정보를 검색합니다.
    "귀여운 포켓몬", "바다 느낌", "불꽃에서 사는 포켓몬 이야기" 같은 의미 기반 검색에 사용하세요.

    내부 동작:
      1. BM25 키워드 검색 (PostgreSQL full-text search) — 고유명사·정확한 단어에 강함
      2. 벡터 유사도 검색 — 의미·분위기 기반 검색에 강함
      3. RRF(Reciprocal Rank Fusion)로 두 결과 융합
      4. Cross-encoder Re-ranking으로 최종 정렬 → 상위 5개만 LLM에 전달
    """
    merged = []
    try:
        conn = psycopg2.connect(DB_CONN)
        cur  = conn.cursor()

        # ── 1. BM25 키워드 검색 ──────────────────────────────────
        ts_query = " | ".join(query.split())

        cur.execute("""
            SELECT p.name, ft.version_name AS source, ft.content
            FROM flavor_text ft
            JOIN species s ON ft.species_id = s.id
            JOIN pokemon p ON s.pokemon_id  = p.id
            WHERE to_tsvector('simple', ft.content) @@ to_tsquery('simple', %s)
            ORDER BY ts_rank(to_tsvector('simple', ft.content), to_tsquery('simple', %s)) DESC
            LIMIT %s
        """, (ts_query, ts_query, HYBRID_CANDIDATE_K))
        bm25_flavor = [(r[0], r[1], r[2]) for r in cur.fetchall()]

        cur.execute("""
            SELECT p.name, 'knowledge' AS source, pk.content
            FROM pokemon_knowledge pk
            JOIN pokemon p ON pk.pokemon_id = p.id
            WHERE to_tsvector('simple', pk.content) @@ to_tsquery('simple', %s)
            ORDER BY ts_rank(to_tsvector('simple', pk.content), to_tsquery('simple', %s)) DESC
            LIMIT %s
        """, (ts_query, ts_query, HYBRID_CANDIDATE_K))
        bm25_knowledge = [(r[0], r[1], r[2]) for r in cur.fetchall()]

        bm25_all = bm25_flavor + bm25_knowledge

        # ── 2. 벡터 유사도 검색 ──────────────────────────────────
        query_vector = embeddings.embed_query(query)

        cur.execute("""
            SELECT p.name, ft.version_name AS source, ft.content
            FROM flavor_text ft
            JOIN species s ON ft.species_id = s.id
            JOIN pokemon p ON s.pokemon_id  = p.id
            WHERE ft.embedding IS NOT NULL
            ORDER BY ft.embedding <=> %s::vector
            LIMIT %s
        """, (query_vector, HYBRID_CANDIDATE_K))
        vec_flavor = [(r[0], r[1], r[2]) for r in cur.fetchall()]

        cur.execute("""
            SELECT p.name, 'knowledge' AS source, pk.content
            FROM pokemon_knowledge pk
            JOIN pokemon p ON pk.pokemon_id = p.id
            WHERE pk.embedding IS NOT NULL
            ORDER BY pk.embedding <=> %s::vector
            LIMIT %s
        """, (query_vector, HYBRID_CANDIDATE_K))
        vec_knowledge = [(r[0], r[1], r[2]) for r in cur.fetchall()]

        vec_all = vec_flavor + vec_knowledge
        conn.close()

        # ── 3. RRF 융합 ──────────────────────────────────────────
        merged = _rrf_merge(bm25_all, vec_all)
        if not merged:
            return "검색 결과가 없습니다. 다른 표현으로 질문해보세요."

        candidates = merged[:RERANK_CANDIDATE_N]

        # ── 4. Cross-encoder Re-ranking ──────────────────────────
        docs_for_rerank = [f"[{c['name']} / {c['source']}]\n{c['content']}" for c in candidates]

        encoder = get_cross_encoder()
        pairs   = [(query, doc) for doc in docs_for_rerank]
        scores  = encoder.predict(pairs)

        ranked   = sorted(zip(scores, docs_for_rerank), key=lambda x: x[0], reverse=True)
        top_docs = [doc for _, doc in ranked[:RERANK_TOP_N]]

        return "✅ 관련 포켓몬 정보 (하이브리드 검색 + Cross-encoder Re-ranking):\n\n" + "\n\n---\n\n".join(top_docs)

    except Exception as e:
        # Cross-encoder 실패 시 RRF 결과로 fallback
        print(f"⚠️  Re-ranking 실패 (fallback to RRF): {e}")
        fallback = merged[:RERANK_TOP_N] if merged else []
        if not fallback:
            return "검색 결과가 없습니다."
        results = [f"[{c['name']} / {c['source']}]\n{c['content']}" for c in fallback]
        return "✅ 관련 포켓몬 정보 (RRF only):\n\n" + "\n\n---\n\n".join(results)


@tool
def web_search(query: str) -> str:
    """
    DB에 없는 포켓몬 정보를 웹에서 검색합니다.
    최신 게임 정보, DB 미보유 포켓몬, 공식 이벤트 등에만 사용하세요.
    """
    try:
        results  = tavily.invoke(query + " 포켓몬")
        web_text = "\n\n".join([r["content"] for r in results])
        return f"✅ 웹 검색 결과:\n{web_text}"
    except Exception as e:
        return f"웹 검색 실패: {e}"


# ══════════════════════════════════════════════════════════
# Agent State & Graph
# ══════════════════════════════════════════════════════════

# Neo4j 툴 포함 — 툴 수가 늘어났으므로 최대 호출 횟수를 8로 상향
tools     = [search_pokemon_db, search_pokemon_knowledge,
             search_evolution_chain, search_type_relations,
             web_search]
llm_agent = llm.bind_tools(tools)

MAX_TOOL_CALLS = 8

class AgentState(TypedDict):
    messages:        Annotated[List, operator.add]
    tool_call_count: int


def agent_node(state: AgentState) -> AgentState:
    """LLM이 툴을 선택하고 답변을 생성하는 핵심 노드"""
    messages = state["messages"]

    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    count = state.get("tool_call_count", 0)
    if count >= MAX_TOOL_CALLS:
        messages = messages + [
            SystemMessage(content=(
                "지금까지 검색한 정보를 바탕으로 최선의 답변을 지금 바로 작성하세요. "
                "더 이상 툴을 호출하지 마세요."
            ))
        ]

    response = llm_agent.invoke(messages)

    if count >= MAX_TOOL_CALLS and hasattr(response, "tool_calls") and response.tool_calls:
        response.tool_calls = []

    tool_names = [tc["name"] if isinstance(tc, dict) else tc.name
                  for tc in response.tool_calls] if response.tool_calls else []
    print(f"🤖 Agent (툴호출 {count}회): {tool_names if tool_names else '최종 답변'}")

    return {"messages": [response], "tool_call_count": count}


_tool_node = ToolNode(tools)

def tools_node_wrapper(state: AgentState) -> AgentState:
    """ToolNode 실행 후 tool_call_count 증가"""
    result = _tool_node.invoke(state)
    new_count = state.get("tool_call_count", 0) + 1
    return {**result, "tool_call_count": new_count}


def should_continue(state: AgentState) -> str:
    last  = state["messages"][-1]
    count = state.get("tool_call_count", 0)

    if hasattr(last, "tool_calls") and last.tool_calls and count < MAX_TOOL_CALLS:
        return "tools"
    return END


# ══════════════════════════════════════════════════════════
# 그래프 조립
# ══════════════════════════════════════════════════════════

def build_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node_wrapper)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    return workflow.compile()


app = build_agent()


# ══════════════════════════════════════════════════════════
# 실행 헬퍼
# ══════════════════════════════════════════════════════════

def chat_with_tools(
    query: str,
    history: list[dict] | None = None
) -> tuple[str, list[str]]:
    """
    답변 텍스트와 실제 사용된 툴 이름 목록을 함께 반환합니다.

    Args:
        query:   현재 사용자 질문
        history: 이전 대화 목록 [{"role": "user"|"assistant", "content": "..."}, ...]
                 Streamlit 의 st.session_state.messages 를 그대로 전달하면 됩니다.
    """
    messages = []

    # 이전 대화를 LangChain 메시지로 변환
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    result = app.invoke({
        "messages":        messages,
        "tool_call_count": 0,
    })

    used_tools: list[str] = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                if name and name not in used_tools:
                    used_tools.append(name)

    answer = result["messages"][-1].content
    return answer, used_tools


def chat(query: str, history: list[dict] | None = None) -> str:
    """답변 텍스트만 반환합니다 (툴 목록이 필요 없을 때 사용)."""
    answer, _ = chat_with_tools(query, history)
    return answer


# ══════════════════════════════════════════════════════════
# 직접 실행 테스트
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 임베딩 초기화는 python -m common.ingest 으로 별도 실행
    tests = [
        "불꽃 타입 중 공격력 가장 높은 포켓몬 3마리는?",       # SQL
        "귀엽고 작은 느낌의 포켓몬 추천해줘",                  # 벡터
        "피카츄는 어떤 성격이야?",                             # 벡터
        "1세대 포켓몬 중 hp 가장 높은 건?",                   # SQL
        "불꽃 타입이면서 귀여운 느낌의 포켓몬 추천해줘",        # SQL + 벡터
        "물 타입 포켓몬인데 바다 이야기가 있는 포켓몬은?",      # SQL + 벡터
        "이브이 진화 경로 알려줘",                             # Neo4j
        "드래곤 타입 상성은?",                                 # Neo4j
    ]

    for q in tests:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        answer, used = chat_with_tools(q)
        print(f"툴: {used}")
        print(f"A: {answer}")
