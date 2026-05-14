"""Hybrid RAG scoring policy.

목적:
    Graph DB 점수와 Vector DB 근거 점수를 어떤 비율로 합칠지 한 곳에서 관리합니다.
    비율을 코드 곳곳에 흩뿌리지 않고 여기서만 바꾸면 전체 하이브리드 랭킹 정책이 바뀝니다.
"""

from typing import Dict, Literal


RequestType = Literal["analysis", "recommendation"]


# GRAPH_SCORE_MAX:
# - Team Builder 추천 graph_score의 설계상 최대값입니다.
# - defensive_score 125점 + stat_score 5점 + coverage_score 20점 = 150점입니다.
# - duplicate_penalty는 감점 항목이므로 최대점 계산에서는 0점 감점 기준으로 봅니다.
GRAPH_SCORE_MAX = 150.0


# ANALYSIS_WEIGHTS:
# - 덱 분석은 Graph DB가 계산한 타입 상성 결과가 핵심입니다.
# - Vector DB는 포켓몬/기술/특성 설명을 보강하는 근거라서 보조 비중을 둡니다.
ANALYSIS_WEIGHTS = {
    "graph": 0.70,
    "vector": 0.30,
}


# RECOMMENDATION_WEIGHTS:
# - 추천 순위는 실제 타입 보완, 종족값, 기술 커버리지 같은 Graph 계산이 더 중요합니다.
# - 다만 추천 이유를 풍부하게 만들기 위해 Vector 근거도 30% 반영합니다.
RECOMMENDATION_WEIGHTS = {
    "graph": 0.80,
    "vector": 0.20,
}


# ANSWER_GENERATION_WEIGHTS:
# - 추천 순위 계산은 Graph 비중이 더 높지만, AI 해설은 사용자가 납득할 수 있는 설명이 핵심입니다.
# - 그래서 답변 생성 단계에서는 Graph DB 계산 근거와 Vector DB 문서 근거를 같은 비중으로 반영하도록 명시합니다.
ANSWER_GENERATION_WEIGHTS = {
    "graph": 0.60,
    "vector": 0.40,
}


def get_hybrid_weights(request_type: RequestType) -> Dict[str, float]:
    """요청 종류에 맞는 graph/vector 가중치를 반환합니다."""

    if request_type == "recommendation":
        return RECOMMENDATION_WEIGHTS
    return ANALYSIS_WEIGHTS


def get_answer_generation_weights() -> Dict[str, float]:
    """AI 답변 생성 단계에서 사용할 graph/vector 설명 비중을 반환합니다."""

    return ANSWER_GENERATION_WEIGHTS


def normalize_graph_score(raw_score: float, max_score: float = GRAPH_SCORE_MAX) -> float:
    """Graph DB raw score를 후보군 안에서 0~100 점수로 정규화합니다.

    목적:
        추천 후보마다 graph_score의 절대 범위가 달라질 수 있기 때문에,
        vector_score와 합치기 전에 같은 0~100 기준으로 맞춥니다.

    Args:
        raw_score: Graph DB 추천 로직이 계산한 원본 점수입니다.
        max_score: 이번 추천 후보군 안에서 가장 높은 원본 graph_score입니다.
    """

    # max_score가 0이면 비교 기준이 없으므로 안전하게 0점으로 처리합니다.
    if max_score <= 0:
        return 0.0

    # raw_score / max_score 비율을 100점 기준으로 바꿉니다.
    normalized_score = (raw_score / max_score) * 100
    return round(min(max(normalized_score, 0.0), 100.0), 2)


def normalize_vector_score(raw_score: float) -> float:
    """Vector DB 유사도 점수를 Graph 점수와 합치기 쉬운 0~100 점수로 변환합니다."""

    # raw_score:
    # - pgvector 검색 결과는 보통 0~1 사이의 유사도입니다.
    # - 상태 문서처럼 score가 0인 문서는 근거 점수에 거의 영향을 주지 않습니다.
    if raw_score <= 0:
        return 0.0
    if raw_score <= 1:
        return round(raw_score * 100, 2)
    return round(min(raw_score, 100.0), 2)
