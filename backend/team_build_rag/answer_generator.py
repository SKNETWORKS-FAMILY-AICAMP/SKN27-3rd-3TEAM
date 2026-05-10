"""
Answer generator for Team Build Hybrid RAG.

목적:
    Hybrid RAG의 마지막 단계에서 Graph DB 계산 결과와 Vector DB 검색 근거를 LLM 프롬프트로 묶고,
    LLM이 실제 사용자용 자연어 답변을 생성하도록 합니다.

중요:
    generate_answer()가 {"final_answer": "..."} 형태로 반환하는 이유는
    LangGraph 노드가 "상태에 추가할 값"을 dict로 반환해야 하기 때문입니다.
    즉, 이 dict는 사용자에게 보여주는 최종 응답 포맷이 아니라 LangGraph 내부 상태 업데이트 포맷입니다.
"""

import json
import os
from typing import Any, Dict, List, Optional

from team_build_rag.state import HybridRagState, get_request_type

try:
    # ChatOpenAI:
    # - OPENAI_API_KEY가 있을 때 사용할 LLM입니다.
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - 환경에 패키지가 없을 때도 서버가 죽지 않도록 처리합니다.
    ChatOpenAI = None

try:
    # ChatGroq:
    # - GROQ_API_KEY가 있을 때 사용할 LLM입니다.
    from langchain_groq import ChatGroq
except ImportError:  # pragma: no cover
    ChatGroq = None


def _safe_json(data: Any) -> str:
    """프롬프트에 넣을 데이터를 깨지지 않는 JSON 문자열로 바꾸는 함수입니다."""

    # ensure_ascii=False:
    # - 포켓몬 이름과 타입 이름이 한국어이므로 그대로 보이게 하기 위한 옵션입니다.
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _format_type_with_score(items: List[Dict[str, Any]], limit: int = 3) -> str:
    """타입 이름과 평균 배율을 함께 보여주는 fallback용 보조 함수입니다."""

    chunks: List[str] = []
    for item in items[:limit]:
        type_name = item.get("type_name")
        average_multiplier = item.get("average_multiplier")
        if not type_name:
            continue

        if average_multiplier is None:
            chunks.append(str(type_name))
        else:
            chunks.append(f"{type_name} 평균 {float(average_multiplier):.2f}배")

    return ", ".join(chunks) if chunks else "뚜렷하게 확인된 타입 없음"


def _format_defensive_covers(covers: List[Dict[str, Any]], limit: int = 5) -> str:
    """추천 후보가 어떤 약점 타입을 어떻게 받아주는지 fallback 문장으로 정리합니다."""

    if not covers:
        return "직접 보완 관계 정보 부족"

    relation_labels = {
        "IMMUNE_TO": "무효",
        "VERY_RESISTANT_TO": "강한 저항",
        "RESISTANT_TO": "저항",
    }
    chunks = []
    for cover in covers[:limit]:
        relation = relation_labels.get(cover.get("relation"), "저항")
        chunks.append(f"{cover.get('type_name')} {relation}({cover.get('multiplier')}배)")
    return ", ".join(chunks)


def _format_useful_moves(moves: List[Dict[str, Any]], limit: int = 3) -> str:
    """추천 후보의 대표 기술을 fallback 문장으로 정리합니다."""

    if not moves:
        return "대표 기술 정보 부족"

    chunks = []
    for move in moves[:limit]:
        stab_text = "자속 주력기" if move.get("is_stab") else "견제기"
        chunks.append(
            f"{move.get('move_name')}({move.get('type_name')}, 위력 {move.get('power')}, {stab_text})"
        )
    return ", ".join(chunks)


def _get_chat_model() -> Optional[Any]:
    """사용 가능한 LLM 클라이언트를 선택하는 함수입니다."""

    # provider:
    # - 명시적으로 TEAM_BUILD_RAG_LLM_PROVIDER를 주면 해당 provider를 우선합니다.
    # - 없으면 GROQ_API_KEY, OPENAI_API_KEY 순서로 자동 선택합니다.
    provider = os.getenv("TEAM_BUILD_RAG_LLM_PROVIDER", "").lower().strip()

    groq_api_key = os.getenv("GROQ_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if (provider == "groq" or (not provider and groq_api_key)) and ChatGroq and groq_api_key:
        return ChatGroq(
            model=os.getenv("TEAM_BUILD_RAG_GROQ_MODEL", "llama-3.1-8b-instant"),
            temperature=float(os.getenv("TEAM_BUILD_RAG_TEMPERATURE", "0.2")),
        )

    if (provider == "openai" or (not provider and openai_api_key)) and ChatOpenAI and openai_api_key:
        return ChatOpenAI(
            model=os.getenv("TEAM_BUILD_RAG_OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("TEAM_BUILD_RAG_TEMPERATURE", "0.2")),
        )

    return None


def _build_evidence_context(state: HybridRagState) -> str:
    """Vector DB 검색 근거 문서를 LLM 프롬프트용 텍스트로 정리하는 함수입니다."""

    # vector_documents:
    # - vector_search.py에서 Graph 결과 문서와 pgvector 검색 문서를 합쳐 넣어둔 근거 목록입니다.
    documents = state.get("vector_documents", [])
    if not documents:
        return "검색 근거 문서가 없습니다. Graph DB 계산 결과를 중심으로 답변하세요."

    evidence_blocks: List[str] = []
    for index, document in enumerate(documents[:8], start=1):
        evidence_blocks.append(
            "\n".join(
                [
                    f"[근거 {index}]",
                    f"source: {document.get('source', 'unknown')}",
                    f"title: {document.get('title', '제목 없음')}",
                    f"score: {document.get('score', 0)}",
                    f"content: {document.get('content', '')}",
                ]
            )
        )

    return "\n\n".join(evidence_blocks)


def _build_analysis_prompt(state: HybridRagState, graph_result: Dict[str, Any]) -> str:
    """덱 분석 요청용 RAG 프롬프트를 만드는 함수입니다."""

    # compact_graph_result:
    # - LLM이 필요한 핵심 정보만 읽을 수 있도록 Graph 결과를 그대로 넣되, 역할을 명확히 지시합니다.
    compact_graph_result = {
        "selected_pokemon": graph_result.get("selected_pokemon", []),
        "weak_types": graph_result.get("weak_types", []),
        "resistant_types": graph_result.get("resistant_types", []),
        "move_type_coverage": graph_result.get("move_type_coverage", []),
        "insights": graph_result.get("insights", {}),
    }

    return f"""
너는 포켓몬 팀 빌딩을 도와주는 분석가다.
아래 Graph DB 계산 결과와 검색 근거를 사용해서 사용자가 선택한 5마리 덱을 분석해라.

답변 규칙:
- 한국어로 답변한다.
- 단순 나열이 아니라 "왜 그런 판단을 했는지" 설명한다.
- 약점 타입, 안정적인 방어 타입, 기술 타입 커버리지, 6번째 포켓몬 방향을 포함한다.
- 숫자는 Graph DB 결과를 우선 신뢰한다.
- 근거에 없는 내용을 확정적으로 지어내지 않는다.
- 너무 길게 늘어놓지 말고 4~6문단 정도로 정리한다.

[Graph DB 계산 결과]
{_safe_json(compact_graph_result)}

[검색 근거]
{_build_evidence_context(state)}

최종 답변:
""".strip()


def _build_recommendation_prompt(state: HybridRagState, reranked_result: Dict[str, Any]) -> str:
    """추천 요청용 RAG 프롬프트를 만드는 함수입니다."""

    # compact_reranked_result:
    # - 추천 후보, 점수, 이유, 기존 팀 분석 결과를 LLM에게 같이 제공합니다.
    compact_reranked_result = {
        "analysis": reranked_result.get("analysis", {}),
        "recommendations": reranked_result.get("recommendations", []),
    }

    return f"""
너는 포켓몬 팀 빌딩을 도와주는 추천 분석가다.
아래 Graph DB 추천 결과와 검색 근거를 사용해서 6번째 포켓몬 추천 이유를 설명해라.

답변 규칙:
- 한국어로 답변한다.
- 1순위 추천 포켓몬을 가장 먼저 말한다.
- "몇 개 약점 보완"처럼 뭉뚱그리지 말고, 어떤 약점 타입을 어떤 저항/무효 관계로 보완하는지 구체적으로 말한다.
- useful_moves에 있는 기술명을 반드시 활용해서, 어떤 기술이 주력기인지/견제기인지/어떤 상황에서 쓸지 설명한다.
- 추천 점수, 보완하는 약점, 대표 기술, 기대 역할을 설명한다.
- 2~3순위 후보가 있으면 비교 관점으로 짧게 언급한다.
- 숫자와 추천 순위는 Graph DB 결과를 우선 신뢰한다.
- 근거에 없는 내용을 확정적으로 지어내지 않는다.
- 사용자가 바로 선택을 판단할 수 있도록 5~7문단 정도로 정리한다.
- 문장 예시: "디아루가는 바위 공격을 0.5배로 받아 리자몽/피죤투 쪽의 부담을 줄이고, 용성군은 드래곤 상대로 강하게 압박할 때 유용합니다."

[Graph DB 추천 결과]
{_safe_json(compact_reranked_result)}

[검색 근거]
{_build_evidence_context(state)}

최종 답변:
""".strip()


def _call_llm(prompt: str) -> Optional[str]:
    """LLM을 호출해서 RAG 답변을 생성하는 함수입니다."""

    # model:
    # - API 키가 없으면 None이므로 fallback 템플릿 답변을 사용합니다.
    model = _get_chat_model()
    if model is None:
        return None

    try:
        # response.content:
        # - LangChain ChatModel의 표준 응답에서 실제 텍스트만 꺼냅니다.
        response = model.invoke(prompt)
        content = getattr(response, "content", None)
        return str(content).strip() if content else None
    except Exception:
        # LLM API 호출 실패가 전체 팀 분석 API 실패로 이어지면 안 되므로 fallback으로 넘깁니다.
        return None


def _generate_fallback_analysis_answer(graph_result: Dict[str, Any]) -> str:
    """LLM을 사용할 수 없을 때 보여줄 최소 fallback 분석 문장입니다."""

    insights = graph_result.get("insights", {})
    weak_types = graph_result.get("weak_types", [])
    resistant_types = graph_result.get("resistant_types", [])

    return (
        f"{insights.get('summary', '현재 덱의 상성 정보를 기준으로 분석했습니다.')}\n\n"
        f"주의해야 할 공격 타입은 {_format_type_with_score(weak_types)}입니다. "
        f"반대로 비교적 안정적으로 받아낼 수 있는 타입은 {_format_type_with_score(resistant_types)}입니다.\n\n"
        f"추천 방향: {insights.get('recommendation_direction', '6번째 포켓몬은 현재 약점 타입을 줄이는 방향으로 고르는 것이 좋습니다.')}"
    )


def _generate_fallback_recommendation_answer(reranked_result: Dict[str, Any]) -> str:
    """LLM을 사용할 수 없을 때 보여줄 최소 fallback 추천 문장입니다."""

    recommendations = reranked_result.get("recommendations", [])
    analysis = reranked_result.get("analysis", {})
    weak_types = analysis.get("weak_types", [])

    if not recommendations:
        return "추천 후보를 찾지 못했습니다. 선택한 5마리의 조건을 다시 확인해 주세요."

    top = recommendations[0]
    reasons = top.get("reasons") or []
    reason_text = " ".join(reasons) if reasons else "현재 팀의 약점을 보완할 수 있는 후보입니다."
    defensive_text = _format_defensive_covers(top.get("defensive_covers", []))
    move_text = _format_useful_moves(top.get("useful_moves", []))

    return (
        f"현재 팀에서 우선적으로 보완해야 할 타입은 {_format_type_with_score(weak_types)}입니다.\n\n"
        f"가장 추천하는 포켓몬은 {top.get('name')}입니다. "
        f"추천 점수는 {top.get('hybrid_score', top.get('score'))}점입니다.\n\n"
        f"방어적으로는 {defensive_text} 관계로 현재 팀의 약점 부담을 줄입니다. "
        f"즉, 해당 타입 공격을 받는 상황에서 교체 후보로 활용하기 좋습니다.\n\n"
        f"기술 쪽에서는 {move_text}를 우선적으로 볼 수 있습니다. "
        f"이 기술들은 주력 화력이나 견제 폭을 확보하는 데 도움이 됩니다.\n\n"
        f"요약하면, {reason_text}"
    )


def generate_answer(state: HybridRagState) -> Dict[str, str]:
    """LangGraph 워크플로우의 최종 답변을 생성하는 노드 함수입니다."""

    # request_type:
    # - analysis면 덱 분석 RAG 프롬프트, recommendation이면 추천 RAG 프롬프트를 사용합니다.
    request_type = get_request_type(state)

    # result:
    # - recommendation은 reranker를 거친 reranked_result를 우선 사용합니다.
    # - analysis는 graph_result가 그대로 최종 분석 결과입니다.
    result = state.get("reranked_result", state.get("graph_result", {}))

    if request_type == "recommendation":
        prompt = _build_recommendation_prompt(state, result)
        llm_answer = _call_llm(prompt)
        return {"final_answer": llm_answer or _generate_fallback_recommendation_answer(result)}

    prompt = _build_analysis_prompt(state, result)
    llm_answer = _call_llm(prompt)
    return {"final_answer": llm_answer or _generate_fallback_analysis_answer(result)}
