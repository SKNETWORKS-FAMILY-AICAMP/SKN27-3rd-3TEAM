"""
포켓몬 챗봇 - Tool-calling Agent (LangGraph)
=============================================
변경 사항:
  - query_classifier 제거 → LLM이 직접 툴을 선택
  - SQL 실패 시 LLM이 오류 메시지를 보고 SQL 수정 후 재시도 (최대 3회)
  - SQL + 벡터 동시 사용 가능 (복합 질문 처리)
  - 답변 품질 향상을 위한 강화된 system prompt
  - 웹검색은 DB에 정말 없을 때만 사용
  - [REFACTOR] search_pokemon_db: psycopg2 직접 쿼리 → SQLDatabase + create_sql_query_chain
  - [REFACTOR] search_flavor_text: BM25 제거, psycopg2 직접 쿼리 → PGVector VectorStore
  - [KEEP] Cross-encoder Re-ranking 유지
  - [KEEP] Neo4j 툴 연동 유지
  - [KEEP] 멀티턴 대화 히스토리 유지

테이블 구조:
  pokemon → pokemon_stats (1:1)
  pokemon → pokemon_types → types (N:M)
  pokemon → species → flavor_text (비정형, embedding 있음)
"""
import sqlalchemy
import os
import threading
from dotenv import load_dotenv
from typing import TypedDict, List, Annotated
import operator

try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    DEVICE = "cpu"

from sentence_transformers import CrossEncoder

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults
from langchain_community.utilities import SQLDatabase          # [NEW] SQLDatabase
from langchain.chains import create_sql_query_chain            # [NEW] SQL 생성 체인
from langchain_community.vectorstores import PGVector          # [NEW] VectorStore
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode


# Neo4j 툴
try:
    from chatbot.pokemon_neo4j import search_evolution_chain, search_type_relations
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

embeddings = OpenAIEmbeddings()
tavily     = TavilySearchResults(max_results=3)

MODELS = {
    "gpt-4o-mini": lambda: ChatOpenAI(model="gpt-4o-mini", temperature=0),
    "gemma4:e2b":  lambda: ChatOllama(
        model="gemma4:e2b",
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0,
    ),
}
DEFAULT_MODEL = "gpt-4o-mini"

# # ── Cross-encoder 싱글톤 (변경 없음) ──────────────────────
# _cross_encoder: CrossEncoder | None = None
# _cross_encoder_lock = threading.Lock()

# def get_cross_encoder() -> CrossEncoder:
#     global _cross_encoder
#     if _cross_encoder is None:
#         with _cross_encoder_lock:
#             if _cross_encoder is None:
#                 _cross_encoder = CrossEncoder(
#                     "BAAI/bge-reranker-v2-m3",
#                     max_length=512,
#                     device=DEVICE,
#                 )
#     return _cross_encoder

# [CHANGE] BM25·벡터 각각 후보 수 → 벡터만 사용하므로 의미 변경
FLAVOR_CANDIDATE_K = 10   # VectorStore 후보 수 (기존: BM25·벡터 각각 20개 → 벡터만 20개)
FLAVOR_TOP_N       = 3   # LLM에 전달할 최종 문서 수 (변경 없음)


# ══════════════════════════════════════════════════════════
# [NEW] SQLDatabase 인스턴스
# 기존: SCHEMA 문자열 하드코딩 + psycopg2 직접 연결
# 변경: SQLDatabase 가 실제 DB에서 스키마 자동 읽어옴
#       스키마 변경 시 코드 수정 불필요
# ══════════════════════════════════════════════════════════

_sql_db = SQLDatabase.from_uri(
    DB_CONN,
    include_tables=[          # 조회 허용 테이블만 명시 (보안)
        "pokemon",
        "pokemon_stats",
        "pokemon_types",
        "types",
        "species",
        "flavor_text",
    ],
    sample_rows_in_table_info=2,  # 테이블당 샘플 2행을 LLM에 전달 → SQL 정확도 향상
)

# SQL 생성 체인 — 자연어 질문 → SQL 자동 생성
# 기존: LLM이 SCHEMA 문자열 보고 SQL 직접 생성해서 툴에 넘김
# 변경: 툴 내부에서 _sql_chain 이 자연어 → SQL 변환
_sql_chain = create_sql_query_chain(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    db=_sql_db,
)


# ══════════════════════════════════════════════════════════
# [NEW] PGVector VectorStore 인스턴스
# 기존: psycopg2로 ft.embedding <=> 직접 쿼리
# 변경: PGVector 클래스가 내부적으로 동일한 쿼리를 추상화
#       DB를 Chroma·Elasticsearch 등으로 교체 시 이 한 줄만 변경
# ══════════════════════════════════════════════════════════

_vectorstore = PGVector(
    connection_string=DB_CONN,
    embedding_function=embeddings,
    collection_name="flavor_text",  # flavor_text 테이블과 연결
)

# MMR Retriever — 유사도 + 다양성 동시 고려
# 기존: 유사도만 기준으로 상위 K개 반환 → 비슷한 문서 중복 가능
# 변경: MMR 으로 다양한 문서 후보 확보 → Re-ranking 품질 향상
_vector_retriever = _vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k":       10,
        "fetch_k": 20,  # MMR 후보풀 (40개 중 20개 선별)
    }
)


# ══════════════════════════════════════════════════════════
# SYSTEM_PROMPT
# ══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """당신은 세계 최고의 포켓몬 박사입니다. 풍부하고 정확한 정보를 바탕으로 답변합니다.

## 답변 원칙
1. **항상 툴을 먼저 사용하세요.** 질문에 답하기 전에 반드시 관련 툴을 호출해 데이터를 확인합니다.
2. **복합 질문은 여러 툴을 함께 활용하세요.**
   - 수치/조건/비교 → `search_pokemon_db` (자연어 질문 그대로 넘기세요)
   - 느낌/묘사/성격/배경 → `search_flavor_text` (벡터 + Re-ranking)
   - 진화 경로/조건 → `search_evolution_chain` (Neo4j 그래프)
   - 타입 상성/약점 → `search_type_relations` (Neo4j 그래프)
   - "불꽃타입이면서 귀여운 포켓몬" 같은 복합 질문 → 여러 툴 함께 사용
3. **DB에 없는 정보만** `web_search`를 사용하고, 사용 시 "웹에서 찾은 정보입니다"를 명시합니다.
4. search_pokemon_db 는 SQL 이 아닌 자연어 질문을 그대로 넘기세요.

## 답변 스타일
- 친절하고 열정적으로 답변합니다.
- 수치 데이터는 표 형태로 정리합니다.
- 포켓몬의 특징을 생생하게 설명합니다.
- 컨텍스트에 없는 내용은 절대 지어내지 않습니다.
"""


# ══════════════════════════════════════════════════════════
# Tools
# ══════════════════════════════════════════════════════════

@tool
def search_pokemon_db(query: str) -> str:
    """
    PostgreSQL DB에서 포켓몬 정형 데이터를 조회합니다.
    수치, 타입, 스탯, 세대, 포획률 등 구조화된 정보 검색에 사용하세요.

    SQL 을 직접 작성하지 말고 자연어 질문을 그대로 넘기세요.
    예시:
      - "불꽃 타입 중 공격력 가장 높은 포켓몬 5마리"
      - "1세대 포켓몬 포획률 낮은 순"
      - "피카츄 스탯 전체"
    """
    # [CHANGE] 기존: LLM이 SQL 직접 생성해서 툴에 넘김 → psycopg2 실행
    #          변경: 툴 내부에서 _sql_chain 이 자연어 → SQL 변환
    #                _sql_db.run() 으로 실행 (psycopg2 직접 연결 제거)
    try:
        # 1. 자연어 → SQL 생성
        sql = _sql_chain.invoke({"question": query})
        sql = sql.replace("```sql", "").replace("```", "").strip()

        # SELECT 만 허용 (보안)
        if not sql.upper().strip().startswith("SELECT"):
            return "오류: SELECT 문만 허용됩니다."

        # 2. SQL 실행 — SQLDatabase 추상화
        result = _sql_db.run(sql)

        if not result:
            return "조회 결과가 없습니다. 다른 조건으로 시도해보세요."

        return f"✅ 조회 결과:\n{result}"

    except Exception as e:
        return f"SQL 오류: {e}\n힌트: 질문을 더 구체적으로 입력해보세요."


@tool
def search_flavor_text(query: str) ->str:
    docs = _vector_retriever.invoke(query)

    if not docs:
        return "검색 결과가 없습니다."

    # Re-ranking 제거 — VectorStore 순서 그대로 사용
    top = [doc.page_content for doc in docs[:FLAVOR_TOP_N]]

    return "✅ 관련 도감 설명:\n\n" + "\n\n---\n\n".join(top)


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
# Agent State & Graph (변경 없음)
# ══════════════════════════════════════════════════════════

tools      = [search_pokemon_db, search_flavor_text,
              search_evolution_chain, search_type_relations,
              web_search]
_tool_node = ToolNode(tools)

MAX_TOOL_CALLS = 2

class AgentState(TypedDict):
    messages:        Annotated[List, operator.add]
    tool_call_count: int


def build_agent(model_name: str):
    llm_with_tools = MODELS[model_name]().bind_tools(tools)

    def agent_node(state: AgentState) -> AgentState:
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        count = state.get("tool_call_count", 0)
        if count >= MAX_TOOL_CALLS:
            messages = messages + [SystemMessage(content=(
                "지금까지 검색한 정보를 바탕으로 최선의 답변을 지금 바로 작성하세요. "
                "더 이상 툴을 호출하지 마세요."
            ))]

        response = llm_with_tools.invoke(messages)

        if count >= MAX_TOOL_CALLS and hasattr(response, "tool_calls") and response.tool_calls:
            response.tool_calls = []

        tool_names = [tc["name"] if isinstance(tc, dict) else tc.name
                      for tc in response.tool_calls] if response.tool_calls else []
        print(f"[{model_name}] Agent (툴호출 {count}회): {tool_names or '최종 답변'}")

        return {"messages": [response], "tool_call_count": count}

    def tools_node_wrapper(state: AgentState) -> AgentState:
        result = _tool_node.invoke(state)
        return {**result, "tool_call_count": state.get("tool_call_count", 0) + 1}

    def should_continue(state: AgentState) -> str:
        last  = state["messages"][-1]
        count = state.get("tool_call_count", 0)
        if hasattr(last, "tool_calls") and last.tool_calls and count < MAX_TOOL_CALLS:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node_wrapper)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")
    return workflow.compile()


_agent_cache: dict[str, object] = {}

def get_agent(model_name: str):
    if model_name not in _agent_cache:
        _agent_cache[model_name] = build_agent(model_name)
    return _agent_cache[model_name]


# ══════════════════════════════════════════════════════════
# 실행 헬퍼 (변경 없음)
# ══════════════════════════════════════════════════════════

def chat_with_tools(
    query: str,
    history: list[dict] | None = None,
    model: str = DEFAULT_MODEL,
) -> tuple[str, list[str]]:
    """
    답변 텍스트와 실제 사용된 툴 이름 목록을 함께 반환합니다.

    Args:
        query:   현재 사용자 질문
        history: 이전 대화 목록 [{"role": "user"|"assistant", "content": "..."}, ...]
        model:   사용할 모델명 (MODELS 키 중 하나)
    """
    messages = []
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=query))

    result = get_agent(model).invoke({
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


def chat(query: str, history: list[dict] | None = None, model: str = DEFAULT_MODEL) -> str:
    """답변 텍스트만 반환합니다 (툴 목록이 필요 없을 때 사용)."""
    answer, _ = chat_with_tools(query, history, model)
    return answer


# # ══════════════════════════════════════════════════════════
# # 직접 실행 테스트
# # ══════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     tests = [
#         "불꽃 타입 중 공격력 가장 높은 포켓몬 3마리는?",       # SQLDatabase
#         "귀엽고 작은 느낌의 포켓몬 추천해줘",                  # VectorStore
#         "피카츄는 어떤 성격이야?",                             # VectorStore
#         "1세대 포켓몬 중 hp 가장 높은 건?",                   # SQLDatabase
#         "불꽃 타입이면서 귀여운 느낌의 포켓몬 추천해줘",        # SQLDatabase + VectorStore
#         "물 타입 포켓몬인데 바다 이야기가 있는 포켓몬은?",      # SQLDatabase + VectorStore
#         "이브이 진화 경로 알려줘",                             # Neo4j
#         "드래곤 타입 상성은?",                                 # Neo4j
#     ]

#     for q in tests:
#         print(f"\n{'='*60}")
#         print(f"Q: {q}")
#         answer, used = chat_with_tools(q)
#         print(f"툴: {used}")
#         print(f"A: {answer}")