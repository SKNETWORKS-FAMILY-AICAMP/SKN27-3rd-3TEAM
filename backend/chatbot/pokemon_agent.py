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
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults
from langchain_community.vectorstores import PGVector
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Neo4j 툴
try:
    from chatbot.pokemon_neo4j import search_evolution_chain, search_type_relations, search_pokemon_weakness
except ImportError:
    from pokemon_neo4j import search_evolution_chain, search_type_relations, search_pokemon_weakness


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

FLAVOR_TOP_N = 5


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
        "k":           20,
        "fetch_k":     50,
        "lambda_mult": 0.7,
    }
)


# ══════════════════════════════════════════════════════════
# Phase 2/4B: Hybrid Search helpers
# ══════════════════════════════════════════════════════════

def _reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    """여러 순위 목록을 RRF로 합산해 단일 순위 반환."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)


# Phase 4-B: BM25 인덱스 (rank_bm25, 모듈 로드 시 1회 빌드)
_bm25_index:   object      = None
_bm25_docs:    list[str]   = []

def _get_bm25():
    """BM25 인덱스 초기화 — '포켓몬명: 도감설명' 형식으로 저장."""
    global _bm25_index, _bm25_docs
    if _bm25_index is None:
        try:
            from rank_bm25 import BM25Okapi
            conn = psycopg2.connect(DB_CONN)
            cur  = conn.cursor()
            cur.execute(
                "SELECT p.name || ': ' || ft.content "
                "FROM flavor_text ft "
                "JOIN species s ON ft.species_id = s.id "
                "JOIN pokemon p ON s.pokemon_id = p.id "
                "WHERE ft.content IS NOT NULL ORDER BY ft.id"
            )
            _bm25_docs  = [row[0] for row in cur.fetchall()]
            conn.close()
            tokenized   = [doc.split() for doc in _bm25_docs]
            _bm25_index = BM25Okapi(tokenized)
        except Exception as e:
            print(f"BM25 인덱스 빌드 실패: {e}")
            _bm25_index = False
    return _bm25_index, _bm25_docs


_rewriter_llm: object = None

def _rewrite_query(query: str) -> str:
    """사용자 질문에서 핵심 검색 키워드를 보존하며 최소한으로 재작성."""
    global _rewriter_llm
    try:
        if _rewriter_llm is None:
            _rewriter_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = (
            "다음 포켓몬 질문의 핵심 의도를 유지하면서 검색 키워드를 명확히 하세요.\n"
            "- 원본 질문의 의도를 절대 바꾸지 마세요\n"
            "- 포켓몬 이름·타입·능력 등 구체적인 키워드를 보존하세요\n"
            "- 불필요한 표현만 제거하고 한 문장으로 답하세요\n\n"
            f"원본: {query}\n재작성 (한 문장, 의도 보존):"
        )
        result = _rewriter_llm.invoke(prompt, config={"tags": ["nosync", "rewriter"]})
        rewritten = result.content.strip()
        return rewritten if rewritten else query
    except Exception:
        return query


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

SYSTEM_PROMPT = f"""당신은 포켓몬 세계의 최고 권위자, 오키드(오박사)입니다! 친근하고 활기찬 성격으로 트레이너(사용자)의 질문에 당당하게 답변합니다.

## 핵심 규칙 (반드시 준수)
- **검색 결과에 없는 내용은 절대 지어내지 마세요.** 툴이 반환한 데이터에만 근거해 답변한단다!
- **모르면 모른다고 솔직하게 말하는 것이 진정한 학자란다.** 검색 결과가 부족하면 "오호라, 그건 내 연구 자료에도 아직 없구나!"라고 답하렴.
- **숫자·이름·진화 조건 등은 툴 결과를 그대로 인용하렴.** 절대 추측으로 채워넣지 마라.
- **내부 평가 지표나 시스템 메타데이터(예: AI Confidence, 팩트체크 등)는 절대 출력하지 마라.** 오직 포켓몬 박사로서 자연스럽게 대화해야 해!

## 툴 선택 기준
1. **항상 툴을 먼저 호출하고 결과를 확인한 뒤 답변하렴.**
2. **복합 질문은 필요한 툴을 순서대로 모두 호출해라 (최대 5회).**
   - 수치/조건/비교/포획률/세대 → `search_pokemon_db` (SELECT SQL 작성)
   - 느낌/묘사/성격/배경/분위기 → `search_flavor_text` (벡터 검색)
   - 진화 경로·조건 → `search_evolution_chain` (Neo4j)
   - 특정 포켓몬의 약점·저항·면역 → `search_pokemon_weakness` (Neo4j, 듀얼타입 정확 반영)
   - 타입 자체의 공격·방어 상성 → `search_type_relations` (Neo4j)
3. **복합 질문은 반드시 분해해라.** "A와 B를 함께 알려줘" → A 툴 호출 → B 툴 호출 → 통합 답변.
4. SQL 오류 발생 시 오류 메시지를 정확히 분석하고 컬럼명·조인 조건을 수정해 즉시 재시도하렴.
5. 검색 결과가 질문과 관련 없거나 비어 있으면 검색어를 바꾸거나 다른 툴로 재시도해라.
6. **최솟값·최댓값 조건**: `ORDER BY ... LIMIT 1` 대신 서브쿼리 `WHERE col = (SELECT MIN/MAX(col) FROM ...)` 를 사용해 동점 결과를 모두 반환하렴.

## 답변 스타일 (매우 중요!)
- **오박사 톤 유지**: 친근하고 열정적으로 대답하렴! ("~단다!", "~란다!", "오호라!", "훌륭한 질문이구나!")
- **시각적 즐거움 (이모지)**: 포켓몬과 어울리는 이모지(🔥, 💧, ⚡, 🍃, 🐾 등)를 적극적으로 사용해서 단조롭지 않게 꾸며라!
- **간결하고 세련된 포맷**: 항목을 나열할 때 번호 매기기로 띄어쓰기를 남발하지 말고, **가독성 좋은 표(Table)나 짧은 글머리 기호(Bullet points)**로 압축해서 보여주렴. 목록이 너무 길어지면 핵심만 요약해서 알려주는 센스를 발휘해라!
- 포켓몬의 특징을 도감 데이터를 바탕으로 생생하고 재밌게 설명해주렴.
- 답변 말미에 불필요한 출처 블록이나 시스템 로그를 직접 작성하지 마라. (출처 렌더링은 시스템이 알아서 처리한단다.)

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
    BM25·pg_trgm 키워드 검색과 벡터 검색을 RRF로 결합해 정확도를 높입니다.
    """
    # 1. Vector search (MMR) → PGVector content는 "species_id: version 설명" 형식
    #    species_id 파싱 후 DB 조회로 포켓몬 이름 부착
    vector_docs     = _vector_retriever.invoke(query)
    vector_contents: list[str] = []
    if vector_docs:
        try:
            parsed: list[tuple[int | None, str]] = []
            for doc in vector_docs[:20]:
                raw_c = doc.page_content
                colon_idx = raw_c.find(': ')
                if colon_idx > 0 and raw_c[:colon_idx].strip().isdigit():
                    sid    = int(raw_c[:colon_idx].strip())
                    rest   = raw_c[colon_idx + 2:]   # "version_name 실제설명"
                    # version_name은 공백 기준 첫 단어; 실제 설명만 전달
                    parts  = rest.split(' ', 1)
                    actual = parts[1] if len(parts) > 1 else rest
                    parsed.append((sid, actual))
                else:
                    parsed.append((None, raw_c))

            valid_sids = list({p[0] for p in parsed if p[0] is not None})
            sid_to_name: dict[int, str] = {}
            if valid_sids:
                conn = psycopg2.connect(DB_CONN)
                cur  = conn.cursor()
                cur.execute(
                    "SELECT s.id, p.name "
                    "FROM species s "
                    "JOIN pokemon p ON s.pokemon_id = p.id "
                    "WHERE s.id = ANY(%s)",
                    (valid_sids,),
                )
                sid_to_name = {row[0]: row[1] for row in cur.fetchall()}
                conn.close()

            vector_contents = [
                f"{sid_to_name[sid]}: {content}" if sid and sid in sid_to_name
                else content
                for sid, content in parsed
            ]
        except Exception:
            vector_contents = [doc.page_content for doc in vector_docs[:20]]

    # 2. BM25 (rank_bm25 — 단어 단위 TF-IDF, 이미 '이름: 내용' 형식)
    bm25_contents: list[str] = []
    try:
        bm25, docs = _get_bm25()
        if bm25 and docs:
            tokens        = query.split()
            scores        = bm25.get_scores(tokens)
            top_idx       = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:20]
            bm25_contents = [docs[i] for i in top_idx if scores[i] > 0]
    except Exception:
        pass

    # 3. pg_trgm 유사도 검색 — '포켓몬명: 내용' 형식으로 반환
    trgm_contents: list[str] = []
    try:
        conn = psycopg2.connect(DB_CONN)
        cur  = conn.cursor()
        cur.execute(
            "SELECT p.name || ': ' || ft.content "
            "FROM flavor_text ft "
            "JOIN species s ON ft.species_id = s.id "
            "JOIN pokemon p ON s.pokemon_id = p.id "
            "WHERE similarity(ft.content, %s) > 0.05 "
            "ORDER BY similarity(ft.content, %s) DESC LIMIT 20",
            (query, query),
        )
        trgm_contents = [row[0] for row in cur.fetchall()]
        conn.close()
    except Exception:
        pass

    # 4. RRF 3-way fusion
    channels = [c for c in [vector_contents, bm25_contents, trgm_contents] if c]
    merged   = _reciprocal_rank_fusion(channels) if len(channels) > 1 else (channels[0] if channels else [])

    if not merged:
        return "검색 결과가 없습니다."

    top = merged[:FLAVOR_TOP_N]
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
              search_evolution_chain, search_type_relations,
              search_pokemon_weakness,]
_tool_node = ToolNode(tools)

MAX_TOOL_CALLS = 5

class AgentState(TypedDict):
    messages:        Annotated[List, operator.add]
    tool_call_count: int


def build_agent(model_name: str):
    llm_with_tools = MODELS[model_name]().bind_tools(tools)

    def agent_node(state: AgentState) -> AgentState:
        messages = list(state["messages"])
        count = state.get("tool_call_count", 0)

        # Phase 2: Query Rewriting — 첫 번째 호출 시에만 마지막 HumanMessage 재작성
        if count == 0:
            for i in range(len(messages) - 1, -1, -1):
                if isinstance(messages[i], HumanMessage):
                    rewritten = _rewrite_query(messages[i].content)
                    if rewritten and rewritten != messages[i].content:
                        messages[i] = HumanMessage(content=rewritten)
                    break

        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

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

    _grader = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def crag_check_node(state: AgentState) -> AgentState:
        """Phase 3 CRAG: 툴 결과 관련성 평가 → 낮으면 재검색 가이드."""
        messages = state["messages"]
        count    = state.get("tool_call_count", 0)

        if count >= MAX_TOOL_CALLS - 1:
            return {"messages": [], "tool_call_count": count}

        original = next(
            (m.content for m in messages if isinstance(m, HumanMessage)), ""
        )
        last_tool = next(
            (m for m in reversed(messages) if isinstance(m, ToolMessage)), None
        )

        if not last_tool or not last_tool.content:
            return {"messages": [], "tool_call_count": count}

        content = last_tool.content
        if content.startswith("오류") or content.startswith("SQL 오류"):
            return {"messages": [], "tool_call_count": count}

        if "검색 결과가 없습니다" in content or "찾을 수 없습니다" in content:
            return {
                "messages": [SystemMessage(content=(
                    "검색 결과가 없었습니다. 검색어를 바꾸거나 다른 툴로 재시도하세요."
                ))],
                "tool_call_count": count,
            }

        # 완화된 판정: 조금이라도 관련 정보 포함 시 통과
        judgment = _grader.invoke(
            f"검색 결과가 질문 답변에 조금이라도 도움이 되는 정보를 포함하면 YES, "
            f"전혀 무관하면 NO로만 답하세요.\n"
            f"질문: {original[:150]}\n"
            f"검색 결과: {content[:400]}"
        ).content.strip().upper()

        if "NO" in judgment and "YES" not in judgment:
            return {
                "messages": [SystemMessage(content=(
                    "⚠️ 직전 검색 결과가 질문과 전혀 관련이 없습니다. "
                    "검색 키워드를 바꾸거나 다른 툴을 사용해 재검색하세요."
                ))],
                "tool_call_count": count,
            }

        return {"messages": [], "tool_call_count": count}

    def should_continue(state: AgentState) -> str:
        last  = state["messages"][-1]
        count = state.get("tool_call_count", 0)
        if hasattr(last, "tool_calls") and last.tool_calls and count < MAX_TOOL_CALLS:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node_wrapper)
    workflow.add_node("crag",  crag_check_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "crag")
    workflow.add_edge("crag",  "agent")
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


async def astream_chat(
    query: str,
    history: list[dict] | None = None,
    model_name: str = DEFAULT_MODEL,
):
    """
    LangGraph 에이전트로부터 응답 토큰을 스트리밍합니다.
    (Used tools 정보는 스트림 마지막이나 중간에 함께 전송 가능)
    """
    messages = []
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=query))

    agent = get_agent(model_name)
    used_tools = []
    full_answer = ""

    # astream_events (v2) 사용
    async for event in agent.astream_events(
        {"messages": messages, "tool_call_count": 0},
        version="v2"
    ):
        kind = event["event"]

        # 1. 어떤 툴이 호출되었는지 추적
        if kind == "on_tool_start":
            tool_name = event["name"]
            if tool_name not in used_tools:
                used_tools.append(tool_name)
                # 툴 호출 시작 시 시각적 피드백을 위해 특수 메타데이터 전송 (선택 사항)
                # yield f"METADATA:TOOL:{tool_name}"

        # 2. 최종 에이전트(agent 노드)가 생성하는 토큰만 스트리밍
        if kind == "on_chat_model_stream":
            tags = event.get("tags", [])
            node_name = event.get("metadata", {}).get("langgraph_node")
            
            # 'agent' 노드에서 나오는 스트림만 전달하되, 내부 재작성기(rewriter)는 제외
            if node_name == "agent" and "rewriter" not in tags:
                content = event["data"]["chunk"].content
                if content:
                    full_answer += content
                    yield content

    # 마지막에 사용된 툴 목록을 특수한 형태로 전달 (프론트엔드 약속)
    if used_tools:
        yield f"\n\n[USED_TOOLS]:{','.join(used_tools)}"


def print_graph_mermaid(model: str = DEFAULT_MODEL) -> None:
    print(get_agent(model).get_graph().draw_mermaid())


if __name__ == "__main__":
    print_graph_mermaid()


