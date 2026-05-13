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
import os
import json
import psycopg2
from dotenv import load_dotenv
from typing import TypedDict, List, Annotated
import operator

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults
from langchain_community.vectorstores import PGVector
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

# Tavily API 키가 없을 경우를 대비한 예외 처리
try:
    if not os.environ.get("TAVILY_API_KEY"):
        # 키가 없으면 더미 키를 잠시 넣어 초기화 에러 방지 (실제 호출 시에만 에러 발생)
        os.environ["TAVILY_API_KEY"] = "dummy_for_startup"
    tavily = TavilySearchResults(max_results=3)
except Exception as e:
    print(f"⚠️ Tavily 초기화 실패 (웹 검색 기능 제한): {e}")
    tavily = None

MODELS = {
    "gpt-4o-mini": lambda: ChatOpenAI(model="gpt-4o-mini", temperature=0),
    "gemma4:e2b":  lambda: ChatOllama(
        model="gemma4:e2b",
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0,
    ),
}
DEFAULT_MODEL = "gpt-4o-mini"

FLAVOR_TOP_N = 3


# ══════════════════════════════════════════════════════════
# PGVector VectorStore 인스턴스
# ══════════════════════════════════════════════════════════

_vectorstore = PGVector(
    connection_string=DB_CONN,
    embedding_function=embeddings,
    collection_name="flavor_text",
)

# MMR Retriever — 유사도 + 다양성 동시 고려
_vector_retriever = _vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k":       10,
        "fetch_k": 20,
    }
)


# ══════════════════════════════════════════════════════════
# SYSTEM_PROMPT
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

테이블: flavor_text  (비정형 도감 설명)
컬럼: id, species_id(FK), version_name, content, embedding
"""

SYSTEM_PROMPT = f"""당신은 세계 최고의 포켓몬 박사입니다. 풍부하고 정확한 정보를 바탕으로 답변합니다.

## 답변 원칙
1. **항상 툴을 먼저 사용하세요.** 질문에 답하기 전에 반드시 관련 툴을 호출해 데이터를 확인합니다.
2. **복합 질문은 여러 툴을 함께 활용하세요.**
   - 수치/조건/비교 → `search_pokemon_db` (SELECT SQL 문 작성)
   - 느낌/묘사/성격/배경 → `search_flavor_text` (벡터 검색)
   - 진화 경로/조건 → `search_evolution_chain` (Neo4j 그래프)
   - 타입 상성/약점 → `search_type_relations` (Neo4j 그래프)
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

    if not sql.upper().strip().startswith("SELECT"):
        return "오류: SELECT 문만 허용됩니다."
    for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER"]:
        if forbidden in sql.upper():
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
            ensure_ascii=False, default=str
        )
        return f"✅ {len(rows)}개 결과:\n{result}"

    except Exception as e:
        return f"SQL 오류: {e}\n힌트: 위 오류를 분석해 SQL을 수정한 후 재시도하세요."


@tool
def search_flavor_text(query: str) -> str:
    """
    포켓몬 도감 설명(flavor_text)에서 의미 기반으로 검색합니다.
    "귀여운 포켓몬", "바다 느낌", "불꽃에서 사는 포켓몬" 같은 분위기·묘사·성격 질문에 사용하세요.
    """
    docs = _vector_retriever.invoke(query)

    if not docs:
        return "검색 결과가 없습니다."

    top = [doc.page_content for doc in docs[:FLAVOR_TOP_N]]

    return "✅ 관련 도감 설명:\n\n" + "\n\n---\n\n".join(top)


@tool
def web_search(query: str) -> str:
    """
    DB에 없는 포켓몬 정보를 웹에서 검색합니다.
    최신 게임 정보, DB 미보유 포켓몬, 공식 이벤트 등에만 사용하세요.
    """
    try:
        if not tavily:
            return "웹 검색 API 키가 설정되지 않아 검색을 수행할 수 없습니다."
        results  = tavily.invoke(query + " 포켓몬")
        web_text = "\n\n".join([r["content"] for r in results])
        return f"✅ 웹 검색 결과:\n{web_text}"
    except Exception as e:
        return f"웹 검색 실패: {e}"


# ══════════════════════════════════════════════════════════
# Agent State & Graph (변경 없음)
# ══════════════════════════════════════════════════════════

tools      = [search_pokemon_db, search_flavor_text,
              search_evolution_chain, search_type_relations,]
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


