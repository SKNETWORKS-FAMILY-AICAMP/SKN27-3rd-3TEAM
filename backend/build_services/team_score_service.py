"""
Pokemon team score service.

목적:
    Graph DB에서 조회한 팀 분석 원본 데이터에 화면 표시용 점수와 설명을 붙입니다.
    Neo4j 조회 로직과 점수 계산 규칙을 분리해서, 나중에 추천/RAG 설명에도 같은 점수를 재사용하기 위해 작성했습니다.
"""

from typing import Any, Dict, List


def _get_matchup_grade(average_multiplier: float) -> str:
    """평균 피해 배율을 사람이 읽기 쉬운 등급으로 바꿔주는 함수입니다."""

    # average_multiplier:
    # - 1보다 크면 해당 공격 타입에 약하고, 1보다 작으면 잘 버티는 타입입니다.
    if average_multiplier >= 2:
        return "매우 위험"
    if average_multiplier > 1:
        return "주의"
    if average_multiplier == 1:
        return "보통"
    if average_multiplier <= 0.5:
        return "매우 안정"
    return "안정"


def _calculate_matchup_score(average_multiplier: float) -> float:
    """평균 피해 배율을 프론트에서 바로 보여줄 수 있는 점수로 변환하는 함수입니다."""

    # score:
    # - 약점 타입이면 1배를 초과한 만큼 위험 점수로 계산합니다.
    # - 저항 타입이면 1배보다 낮아진 만큼 방어 점수로 계산합니다.
    # - 예: 평균 2.0배는 100점 위험, 평균 0.5배는 50점 안정으로 표시됩니다.
    if average_multiplier > 1:
        return round((average_multiplier - 1) * 100, 1)
    if average_multiplier < 1:
        return round((1 - average_multiplier) * 100, 1)
    return 0.0


def _build_matchup_reason(type_name: str, average_multiplier: float, team_size: int) -> str:
    """타입별 평균 피해 배율을 짧은 설명 문장으로 바꿔주는 함수입니다."""

    # reason:
    # - 현재는 규칙 기반 문장입니다.
    # - 이후 RAG를 붙이면 이 문장을 LLM 설명의 근거 자료로 넘길 수 있습니다.
    if average_multiplier > 1:
        return f"{type_name} 공격을 팀 평균 {average_multiplier:.2f}배로 받아 주의가 필요합니다."
    if average_multiplier < 1:
        return f"{type_name} 공격을 팀 평균 {average_multiplier:.2f}배로 받아 비교적 안정적입니다."
    return f"{type_name} 공격은 팀 평균 1.00배로 특별한 약점이나 저항이 아닙니다."


def build_type_matchup_items(
    matchup_rows: List[Dict[str, Any]],
    team_size: int,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Neo4j 타입 상성 결과를 weak/neutral/resistant 목록으로 나누고 점수를 붙이는 함수입니다.

    Args:
        matchup_rows: TEAM_WEAKNESS_SUMMARY Cypher에서 내려온 타입별 배율 요약입니다.
        team_size: 현재 선택한 포켓몬 수입니다. 보통 5마리입니다.

    Returns:
        weak_types, neutral_types, resistant_types를 담은 딕셔너리입니다.
    """

    weak_types: List[Dict[str, Any]] = []
    neutral_types: List[Dict[str, Any]] = []
    resistant_types: List[Dict[str, Any]] = []

    for row in matchup_rows:
        # average_multiplier:
        # - 팀 전체가 해당 공격 타입을 평균 몇 배로 받는지 나타냅니다.
        average_multiplier = float(row["average_multiplier"])

        # total_multiplier:
        # - 5마리 각각의 피해 배율을 모두 더한 값입니다.
        # - Neo4j 쿼리의 weakness_score와 같은 값이지만, 의미가 더 분명한 이름도 함께 내려줍니다.
        total_multiplier = float(row["weakness_score"])

        # item:
        # - 프론트가 바로 사용할 수 있도록 score, grade, reason을 포함한 표준 응답 형태입니다.
        item = {
            "type_id": row["type_id"],
            "type_name": row["type_name"],
            "weakness_score": total_multiplier,
            "total_multiplier": total_multiplier,
            "average_multiplier": average_multiplier,
            "pokemon_count": team_size,
            "score": _calculate_matchup_score(average_multiplier),
            "grade": _get_matchup_grade(average_multiplier),
            "reason": _build_matchup_reason(row["type_name"], average_multiplier, team_size),
        }

        if average_multiplier > 1:
            weak_types.append(item)
        elif average_multiplier < 1:
            resistant_types.append(item)
        else:
            neutral_types.append(item)

    return {
        "weak_types": weak_types,
        "neutral_types": neutral_types,
        "resistant_types": resistant_types,
    }
