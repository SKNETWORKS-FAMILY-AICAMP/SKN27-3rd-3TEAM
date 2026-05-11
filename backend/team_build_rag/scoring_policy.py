"""Hybrid RAG scoring policy.

목적:
    Graph DB 점수와 Vector DB 근거 점수를 어떤 비율로 합칠지 한 곳에서 관리합니다.
    비율을 코드 곳곳에 흩뿌리지 않고 여기서만 바꾸면 전체 하이브리드 랭킹 정책이 바뀝니다.
"""

from typing import Dict, Literal


RequestType = Literal["analysis", "recommendation"]


# ANALYSIS_WEIGHTS:
# - 덱 분석은 Graph DB가 계산한 타입 상성 결과가 핵심입니다.
# - Vector DB는 포켓몬/기술/특성 설명을 보강하는 근거라서 보조 비중을 둡니다.
ANALYSIS_WEIGHTS = {
    "graph": 0.60,
    "vector": 0.40,
}


# RECOMMENDATION_WEIGHTS:
# - 추천 순위는 실제 타입 보완, 종족값, 기술 커버리지 같은 Graph 계산이 더 중요합니다.
# - 다만 추천 이유를 풍부하게 만들기 위해 Vector 근거도 30% 반영합니다.
RECOMMENDATION_WEIGHTS = {
    "graph": 0.70,
    "vector": 0.30,
}


# ANSWER_GENERATION_WEIGHTS:
# - 추천 순위 계산은 Graph 비중이 더 높지만, AI 해설은 사용자가 납득할 수 있는 설명이 핵심입니다.
# - 그래서 답변 생성 단계에서는 Graph DB 계산 근거와 Vector DB 문서 근거를 같은 비중으로 반영하도록 명시합니다.
ANSWER_GENERATION_WEIGHTS = {
    "graph": 0.50,
    "vector": 0.50,
}


def get_hybrid_weights(request_type: RequestType) -> Dict[str, float]:
    """요청 종류에 맞는 graph/vector 가중치를 반환합니다."""

    if request_type == "recommendation":
        return RECOMMENDATION_WEIGHTS
    return ANALYSIS_WEIGHTS


def get_answer_generation_weights() -> Dict[str, float]:
    """AI 답변 생성 단계에서 사용할 graph/vector 설명 비중을 반환합니다."""

    return ANSWER_GENERATION_WEIGHTS


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
