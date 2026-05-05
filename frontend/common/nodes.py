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
    포켓몬 관련 질문을 분류하는 전문가야. 아래 규칙에 따라 딱 한 단어(sql 또는 general)로만 답해.

    - sql    : 특정 포켓몬의 수치(공격력, 방어력, 체력 등), 통계, 순위, 개수 등을 묻는 질문
               예) "피카츄의 공격력은?", "1세대 포켓몬은 몇 마리야?", "가장 무거운 포켓몬은?"

    - general: 포켓몬의 유래, 특징, 설명, 일반적인 대화 등 수치 계산이 필요 없는 질문
               예) "피카츄는 어떻게 생겼어?", "안녕?", "포켓몬스터가 뭐야?"

    질문: {state["question"]}
    분류(sql/general):
    """
    raw_intent = llm_generate(prompt).strip().lower()
    print(f"--- [라우터 원본 결과]: {raw_intent} ---") 

    # 'sql'이라는 글자가 포함되어 있으면 sql로 판정
    if "sql" in raw_intent:
        intent = "sql"
    else:
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
    print(f"--- [생성된 SQL]: {sql} ---")

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