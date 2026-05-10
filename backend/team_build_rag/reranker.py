"""
Reranker for Hybrid RAG.

목적:
    추천 후보가 있을 때 Graph 점수와 RAG 근거 점수를 합쳐 최종 순서를 조정합니다.
    현재는 기존 추천 점수를 유지하되, 추후 LLM 평가 점수나 Vector 검색 점수를 더할 수 있게 구조를 분리했습니다.
"""

from typing import Any, Dict, List

from team_build_rag.state import HybridRagState


def rerank_with_score(state: HybridRagState) -> Dict[str, Any]:
    """추천 결과가 있으면 점수 기준으로 재정렬하는 함수입니다."""

    # graph_result:
    # - recommendation 요청이면 recommendations 키를 포함합니다.
    graph_result = state.get("graph_result", {})
    recommendations = list(graph_result.get("recommendations", []))

    if not recommendations:
        return {"reranked_result": graph_result}

    # reranked_recommendations:
    # - 현재는 Graph 기반 추천 점수를 기준으로 정렬합니다.
    # - 나중에는 llm_evaluation, vector_documents의 신뢰도 점수를 더해 hybrid_score를 만들 수 있습니다.
    reranked_recommendations = sorted(
        recommendations,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )

    for index, item in enumerate(reranked_recommendations, start=1):
        item["rank"] = index
        item["hybrid_score"] = item.get("score", 0)

    reranked_result = dict(graph_result)
    reranked_result["recommendations"] = reranked_recommendations
    return {"reranked_result": reranked_result}
