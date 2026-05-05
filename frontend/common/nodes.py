# nodes.py
from typing import TypedDict
from database import execute_query, get_schema
from llm import llm_generate

# ── State 정의 ────────────────────────
class PokemonChatState(TypedDict):
    question    : str
    intent      : str
    context     : list
    answer      : str
    retry_count : int
    sql         : str

# ── 라우터 노드 ───────────────────────
def router_node(state: PokemonChatState):
    prompt = f"""
    포켓몬 관련 질문을 분류해줘.

    - sql    : 숫자/통계/집계 질문
               예) "공격력 100 이상 포켓몬은?"
                   "1세대 포켓몬 총 몇마리야?"

    - general: 텍스트/특징/일반 질문
               예) "피카츄 특징이 뭐야?"
                   "불꽃타입 포켓몬 알려줘"

    질문: {state["question"]}
    sql 또는 general 중 하나만 답해:
    """
    intent = llm_generate(prompt).strip().lower()
    print(f"--- [라우터 결과]: {intent} ---") 

    # 혹시 엉뚱한 값 나오면 general로 처리
    if intent not in ["sql", "general"]:
        intent = "general"

    current_retry = state.get("retry_count", 0)

    return {
        "intent"      : intent,
        "retry_count" : current_retry
    }

# ── SQL 노드 ──────────────────────────
def sql_node(state: PokemonChatState):
    schema = get_schema()

    prompt = f"""
    다음은 PostgreSQL 스키마야:
    {schema}

    질문: {state["question"]}

    주의사항:
    - SQL 쿼리만 작성해줘 (설명 없이)
    - 세미콜론(;) 없이
    - PostgreSQL 문법으로
    """
    sql = llm_generate(prompt).strip()
    print(f"--- [생성된 SQL]: {sql} ---")
    # SQL 코드블록 제거
    sql = sql.replace("```sql", "").replace("```", "").strip()

    try:
        result = execute_query(sql)
    except Exception as e:
        result = [{"error": str(e)}]

    return {"context": result, "sql": sql}

# ── 일반 질문 노드 ────────────────────
def general_node(state: PokemonChatState):
    """
    나중에 Elasticsearch, VectorDB 붙으면
    여기에 검색 로직 추가하면 됨
    """
    return {"context": [{"message": "일반 질문 처리"}]}

# ── 품질 체크 ─────────────────────────
def quality_check(state: PokemonChatState) -> str:
    context     = state.get("context", [])
    retry_count = state.get("retry_count", 0)

    # 결과 없고 재시도 2번 미만이면 재시도
    if not context and retry_count < 2:
        return "retry"
    return "answer"

# ── 답변 생성 노드 ────────────────────
def answer_node(state: PokemonChatState):
    prompt = f"""
    너는 포켓몬 전문가야.

    유저 질문: {state["question"]}

    검색된 데이터:
    {state["context"]}

    위 데이터를 바탕으로 친절하게 답변해줘.
    데이터가 없으면 모른다고 솔직하게 말해줘.
    한국어로 답변해줘.
    """
    answer = llm_generate(prompt)
    return {"answer": answer}