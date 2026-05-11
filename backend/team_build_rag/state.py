"""
Hybrid RAG state definitions.

목적:
    LangGraph의 각 노드가 주고받는 공통 상태 구조를 정의합니다.
    workflow.py의 모든 단계는 이 상태 딕셔너리에 값을 추가하거나 수정하는 방식으로 동작합니다.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict


# RagRequestType:
# - 현재 하이브리드 RAG가 처리할 수 있는 요청 종류입니다.
# - analysis는 덱 분석, recommendation은 6번째 포켓몬 추천 설명에 사용합니다.
RagRequestType = Literal["analysis", "recommendation"]


class HybridRagState(TypedDict, total=False):
    """
    LangGraph 하이브리드 RAG 워크플로우에서 공유하는 상태입니다.

    Attributes:
        pokemon_ids: 사용자가 선택한 5마리 포켓몬 ID입니다.
        request_type: 분석인지 추천인지 나타내는 요청 타입입니다.
        graph: Neo4j 쿼리를 실행할 클라이언트 객체입니다.
        limit: 추천 후보를 몇 개까지 반환할지 나타내는 값입니다.
        selected_graph_tool: supervisor가 선택한 graph tool 이름입니다.
        graph_result: Neo4j 기반 분석/추천 결과입니다.
        vector_query: Vector DB 검색에 사용할 검색 문장입니다.
        vector_documents: Vector DB에서 검색한 텍스트 근거 목록입니다.
        llm_evaluation: LLM 평가 또는 규칙 기반 평가 결과입니다.
        reranked_result: 추천 후보 재정렬 결과입니다.
        final_answer: 사용자에게 보여줄 최종 자연어 답변입니다.
        errors: 워크플로우 중 발생한 오류 메시지 목록입니다.
    """

    pokemon_ids: List[int]
    request_type: RagRequestType
    graph: Any
    limit: int
    selected_graph_tool: str
    graph_result: Dict[str, Any]
    vector_query: str
    vector_documents: List[Dict[str, Any]]
    llm_evaluation: Dict[str, Any]
    reranked_result: Dict[str, Any]
    final_answer: str
    errors: List[str]


def append_error(state: HybridRagState, message: str) -> HybridRagState:
    """워크플로우 오류 메시지를 상태에 누적하기 위한 헬퍼 함수입니다."""

    # errors:
    # - LangGraph 노드들이 중간에 실패해도 어디서 실패했는지 추적하기 위한 리스트입니다.
    errors = list(state.get("errors", []))
    errors.append(message)
    return {"errors": errors}


def get_request_type(state: HybridRagState) -> RagRequestType:
    """상태에서 요청 타입을 안전하게 꺼내는 함수입니다."""

    # request_type:
    # - 값이 없으면 덱 분석을 기본값으로 사용합니다.
    return state.get("request_type", "analysis")


def get_limit(state: HybridRagState) -> int:
    """추천 후보 개수를 안전하게 꺼내는 함수입니다."""

    # limit:
    # - 추천 워크플로우에서만 의미가 있으며 기본값은 3입니다.
    return int(state.get("limit", 3))


def get_optional_graph_result(state: HybridRagState) -> Optional[Dict[str, Any]]:
    """graph_result가 있는지 확인하고 꺼내는 함수입니다."""

    return state.get("graph_result")
