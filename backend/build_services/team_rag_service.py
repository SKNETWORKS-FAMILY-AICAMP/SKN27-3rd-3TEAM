"""
Team RAG service.

목적:
    FastAPI router 또는 다른 service에서 LangGraph 기반 Hybrid RAG 워크플로우를 쉽게 호출할 수 있게 감쌉니다.
    기존 team_analysis_service/team_builder_service는 그대로 두고, RAG 설명이 필요할 때만 이 서비스를 사용합니다.
"""

from typing import Any, Dict, List, Literal

from graph.neo4j_client import Neo4jClient
from team_build_rag.workflow import hybrid_rag_app


TeamRagRequestType = Literal["analysis", "recommendation"]


def run_team_rag(
    pokemon_ids: List[int],
    graph: Neo4jClient,
    request_type: TeamRagRequestType = "analysis",
    limit: int = 3,
) -> Dict[str, Any]:
    """
    팀 분석/추천 Hybrid RAG 워크플로우를 실행하는 함수입니다.

    Args:
        pokemon_ids: 사용자가 선택한 포켓몬 ID 5개입니다.
        graph: Neo4j 쿼리를 실행할 클라이언트입니다.
        request_type: analysis 또는 recommendation입니다.
        limit: 추천 후보를 몇 개까지 사용할지 나타냅니다.

    Returns:
        LangGraph 워크플로우 최종 상태입니다.
        graph_result, vector_documents, llm_evaluation, reranked_result, final_answer를 포함합니다.
    """

    # initial_state:
    # - LangGraph가 첫 노드부터 끝 노드까지 전달받는 시작 상태입니다.
    initial_state = {
        "pokemon_ids": pokemon_ids,
        "graph": graph,
        "request_type": request_type,
        "limit": limit,
        "errors": [],
    }

    # result:
    # - LangGraph는 입력 state를 최종 state에 함께 보존합니다.
    # - graph 클라이언트는 내부 연결 객체라 JSON 응답으로 직렬화할 수 없으므로 제거해야 합니다.
    result = dict(hybrid_rag_app.invoke(initial_state))
    result.pop("graph", None)

    return result
