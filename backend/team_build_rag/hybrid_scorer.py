"""Hybrid score calculator for Team Build RAG.

목적:
    Graph DB가 만든 정량 점수와 Vector DB 문서 근거 점수를 합쳐 최종 hybrid_score를 만듭니다.
    LangGraph에서는 evaluate_with_llm 다음 단계에서 실행되어, 답변 생성 전에 순위와 근거를 정리합니다.
"""

from typing import Any, Dict, List

from team_build_rag.scoring_policy import (
    GRAPH_SCORE_MAX,
    get_hybrid_weights,
    normalize_graph_score,
)
from team_build_rag.state import HybridRagState, get_request_type
from team_build_rag.vector_scorer import (
    score_analysis_evidence,
    score_recommendation_evidence,
)


def _calculate_candidate_hybrid_score(
    candidate: Dict[str, Any],
    vector_info: Dict[str, Any],
    weights: Dict[str, float],
) -> Dict[str, Any]:
    """추천 후보 1마리의 graph_score, vector_score, hybrid_score를 계산합니다."""

    # graph_score:
    # - 팀 약점 보완, 종족값, 기술 타입 커버리지로 계산된 기존 추천 점수입니다.
    # graph_raw_score는 Graph DB 추천 로직이 만든 원본 점수입니다.
    # 원본 값은 디버깅/설명용으로 남기고, 하이브리드 계산에는 정규화 점수를 사용합니다.
    graph_raw_score = float(candidate.get("graph_score", candidate.get("score", 0)) or 0)

    # graph_score는 vector_score와 같은 0~100 기준으로 맞춘 Graph DB 점수입니다.
    # graph_score:
    # - raw graph_score는 최대 150점으로 설계했습니다.
    # - 후보군 안의 상대 최고점이 아니라, 고정 최대값 150점을 기준으로 0~100으로 환산합니다.
    graph_score = normalize_graph_score(graph_raw_score, GRAPH_SCORE_MAX)

    # vector_score:
    # - 후보 이름/타입/기술과 관련된 Vector DB 문서 근거 점수입니다.
    vector_score = float(vector_info.get("vector_score", 0) or 0)

    # hybrid_score:
    # - 추천 순위에 사용할 최종 점수입니다.
    hybrid_score = round(
        graph_score * weights["graph"] + vector_score * weights["vector"],
        2,
    )

    return {
        **candidate,
        "graph_raw_score": round(graph_raw_score, 2),
        "graph_score": round(graph_score, 2),
        "vector_score": round(vector_score, 2),
        "hybrid_score": hybrid_score,
        "score": hybrid_score,
        "vector_evidence": vector_info.get("vector_evidence", []),
        "matched_terms": vector_info.get("matched_terms", []),
    }


def _score_recommendations(state: HybridRagState) -> Dict[str, Any]:
    """추천 요청에서 후보 1~3순위를 hybrid_score 기준으로 다시 정렬합니다."""

    graph_result = state.get("graph_result", {})
    recommendations = list(graph_result.get("recommendations", []))
    vector_documents = state.get("vector_documents", [])
    weights = get_hybrid_weights("recommendation")

    vector_score_map = score_recommendation_evidence(recommendations, vector_documents)
    # 이번 추천 후보군의 최대 graph raw score를 기준으로 graph_score를 0~100으로 정규화합니다.
    scored_recommendations: List[Dict[str, Any]] = []

    for candidate in recommendations:
        pokemon_id = int(candidate.get("pokemon_id"))
        scored_recommendations.append(
            _calculate_candidate_hybrid_score(
                candidate=candidate,
                vector_info=vector_score_map.get(pokemon_id, {}),
                weights=weights,
            )
        )

    scored_recommendations = sorted(
        scored_recommendations,
        key=lambda item: item.get("hybrid_score", 0),
        reverse=True,
    )

    for rank, item in enumerate(scored_recommendations, start=1):
        item["rank"] = rank

    reranked_result = dict(graph_result)
    reranked_result["recommendations"] = scored_recommendations
    reranked_result["hybrid_policy"] = {
        "request_type": "recommendation",
        "graph_weight": weights["graph"],
        "vector_weight": weights["vector"],
        "graph_score_normalized": True,
        "graph_score_normalization": "fixed_design_max",
        "graph_score_max": GRAPH_SCORE_MAX,
        "score_fields": ["graph_raw_score", "graph_score", "vector_score", "hybrid_score"],
    }

    return {"reranked_result": reranked_result}


def _score_analysis(state: HybridRagState) -> Dict[str, Any]:
    """덱 분석 요청에서 Graph 분석 결과에 Vector 근거 평가 정보를 붙입니다."""

    graph_result = dict(state.get("graph_result", {}))
    vector_documents = state.get("vector_documents", [])
    weights = get_hybrid_weights("analysis")
    vector_info = score_analysis_evidence(graph_result, vector_documents)

    graph_result["hybrid_policy"] = {
        "request_type": "analysis",
        "graph_weight": weights["graph"],
        "vector_weight": weights["vector"],
        "score_fields": ["graph_analysis", "vector_score"],
    }
    graph_result["vector_evaluation"] = vector_info

    return {"reranked_result": graph_result}


def calculate_hybrid_score(state: HybridRagState) -> Dict[str, Any]:
    """요청 종류에 맞게 분석/추천 하이브리드 점수 단계를 실행합니다."""

    request_type = get_request_type(state)
    if request_type == "recommendation":
        return _score_recommendations(state)
    return _score_analysis(state)
