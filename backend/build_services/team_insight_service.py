"""
Pokemon team insight service.

목적:
    팀 분석 결과를 단순 숫자 목록이 아니라 사용자가 이해할 수 있는 해석 문장으로 바꿉니다.
    이 파일은 RAG 이전 단계의 규칙 기반 분석 담당입니다.
    나중에 RAG를 붙이면 여기서 만든 summary, risk_summary, recommendation_direction을 근거 자료로 사용할 수 있습니다.
"""

from collections import Counter
from typing import Any, Dict, List, Optional


def _format_type_names(types: List[Dict[str, Any]]) -> str:
    """포켓몬 타입 목록을 '불꽃/드래곤' 같은 짧은 문자열로 바꿔주는 함수입니다."""

    # type_names:
    # - Neo4j에서 내려온 타입 dict에서 화면에 보여줄 타입 이름만 꺼냅니다.
    type_names = [type_item["type_name"] for type_item in types if type_item.get("type_name")]
    return "/".join(type_names) if type_names else "타입 미확인"


def _get_top_item(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """score가 가장 높은 항목 하나를 안전하게 꺼내기 위한 함수입니다."""

    if not items:
        return None
    return sorted(items, key=lambda item: item.get("score", 0), reverse=True)[0]


def _build_type_counter(selected_pokemon: List[Dict[str, Any]]) -> Counter:
    """선택한 포켓몬 5마리의 타입 중복 정도를 계산하는 함수입니다."""

    # counter:
    # - 예: 드래곤 3마리, 강철 2마리처럼 팀 타입 쏠림을 판단할 때 사용합니다.
    counter: Counter = Counter()
    for pokemon in selected_pokemon:
        for type_item in pokemon.get("types", []):
            type_name = type_item.get("type_name")
            if type_name:
                counter[type_name] += 1
    return counter


def _build_team_identity(
    selected_pokemon: List[Dict[str, Any]],
    type_counter: Counter,
) -> str:
    """팀의 큰 성격을 한 문장 라벨로 정리하는 함수입니다."""

    # average_base_total:
    # - 팀 평균 종족값입니다. 높을수록 전설/준전설 중심의 고스탯 팀으로 볼 수 있습니다.
    base_totals = [pokemon.get("base_total") or 0 for pokemon in selected_pokemon]
    average_base_total = sum(base_totals) / len(base_totals) if base_totals else 0

    # duplicated_types:
    # - 2마리 이상 겹치는 타입입니다. 팀 컨셉 또는 타입 쏠림을 판단하는 데 사용합니다.
    duplicated_types = [type_name for type_name, count in type_counter.items() if count >= 2]

    # core_types:
    # - 3마리 이상 겹칠 때만 "중심 타입"으로 봅니다.
    # - 2마리 겹침까지 중심이라고 부르면 실제 팀 해석보다 과하게 보일 수 있습니다.
    core_types = [type_name for type_name, count in type_counter.items() if count >= 3]

    if average_base_total >= 570 and core_types:
        return f"{'/'.join(core_types[:2])} 중심의 고스탯 압박 팀"
    if average_base_total >= 570 and duplicated_types:
        return f"{'/'.join(duplicated_types[:2])} 타입이 일부 겹친 고스탯 팀"
    if average_base_total >= 570:
        return "고스탯 포켓몬 중심의 공격형 팀"
    if core_types:
        return f"{'/'.join(core_types[:2])} 중심의 테마형 팀"
    if duplicated_types:
        return f"{'/'.join(duplicated_types[:2])} 타입이 일부 겹친 밸런스형 팀"
    return "타입 분산을 노린 밸런스형 팀"

    if average_base_total >= 570 and duplicated_types:
        return f"{'/'.join(duplicated_types[:2])} 중심의 고스탯 압박 팀"
    if average_base_total >= 570:
        return "고스탯 포켓몬 중심의 공격형 팀"
    if duplicated_types:
        return f"{'/'.join(duplicated_types[:2])} 타입 색이 강한 테마형 팀"
    return "타입 분산을 노린 밸런스형 팀"


def _build_role_summary(selected_pokemon: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """선택한 포켓몬별 간단한 역할 설명을 만드는 함수입니다."""

    role_summary: List[Dict[str, Any]] = []
    for pokemon in selected_pokemon:
        # type_text:
        # - 역할 문장에서 포켓몬의 정체성을 빠르게 보여주기 위한 타입 문자열입니다.
        type_text = _format_type_names(pokemon.get("types", []))

        # base_total:
        # - 종족값 합계를 기준으로 주력/보조 표현을 간단히 나눕니다.
        base_total = pokemon.get("base_total") or 0
        role = "주력 전투원" if base_total >= 500 else "보조 전투원"

        role_summary.append(
            {
                "pokemon_id": pokemon["pokemon_id"],
                "name": pokemon["name"],
                "types": pokemon.get("types", []),
                "role": role,
                "detail": f"{type_text} 타입 기반의 {role}입니다. 종족값 합계는 {base_total}입니다.",
            }
        )
    return role_summary


def _build_risk_summary(
    weak_types: List[Dict[str, Any]],
    type_counter: Counter,
) -> List[Dict[str, Any]]:
    """팀의 핵심 위험 요소를 1~3개 요약하는 함수입니다."""

    risk_summary: List[Dict[str, Any]] = []
    top_weaknesses = sorted(weak_types, key=lambda item: item.get("score", 0), reverse=True)[:3]

    for item in top_weaknesses:
        # severity:
        # - 프론트에서 위험 카드 색상이나 강조 정도를 정할 수 있는 값입니다.
        severity = "high" if item.get("average_multiplier", 1) >= 1.5 else "medium"
        risk_summary.append(
            {
                "title": f"{item['type_name']} 타입 공격 주의",
                "severity": severity,
                "detail": item.get("reason")
                or f"{item['type_name']} 타입 공격을 평균 {item.get('average_multiplier')}배로 받습니다.",
            }
        )

    duplicated_types = [
        {"type_name": type_name, "count": count}
        for type_name, count in type_counter.most_common()
        if count >= 3
    ]
    if duplicated_types:
        top_duplicate = duplicated_types[0]
        risk_summary.append(
            {
                "title": f"{top_duplicate['type_name']} 타입 중복",
                "severity": "medium",
                "detail": (
                    f"{top_duplicate['type_name']} 타입이 {top_duplicate['count']}마리라 "
                    "특정 약점 타입에 팀이 함께 흔들릴 수 있습니다."
                ),
            }
        )

    return risk_summary[:4]


def _build_strength_summary(
    resistant_types: List[Dict[str, Any]],
    move_type_coverage: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """팀의 강점과 공격 커버리지 장점을 요약하는 함수입니다."""

    strength_summary: List[Dict[str, Any]] = []
    top_resistances = sorted(
        resistant_types,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )[:3]

    for item in top_resistances:
        strength_summary.append(
            {
                "title": f"{item['type_name']} 타입 방어 안정",
                "detail": item.get("reason")
                or f"{item['type_name']} 타입 공격을 평균 {item.get('average_multiplier')}배로 받습니다.",
            }
        )

    if move_type_coverage:
        top_move_type = move_type_coverage[0]
        strength_summary.append(
            {
                "title": f"{top_move_type['type_name']} 기술 커버리지 우수",
                "detail": (
                    f"팀 전체가 배울 수 있는 {top_move_type['type_name']} 타입 기술이 "
                    f"{top_move_type['move_count']}개로 가장 많습니다."
                ),
            }
        )

    return strength_summary[:4]


def _build_recommendation_direction(
    weak_types: List[Dict[str, Any]],
    resistant_types: List[Dict[str, Any]],
    type_counter: Counter,
) -> str:
    """6번째 포켓몬 추천 방향을 한 문장으로 만드는 함수입니다."""

    top_weak = _get_top_item(weak_types)
    if top_weak:
        # weak_type_name:
        # - 가장 먼저 보완해야 할 공격 타입입니다.
        weak_type_name = top_weak["type_name"]
        duplicated = [type_name for type_name, count in type_counter.items() if count >= 2]
        if duplicated:
            return (
                f"6번째 포켓몬은 {weak_type_name} 타입 공격 부담을 줄이면서 "
                f"{'/'.join(duplicated[:2])} 타입 중복을 완화할 수 있는 포켓몬이 좋습니다."
            )
        return f"6번째 포켓몬은 {weak_type_name} 타입 공격을 반감하거나 무효화할 수 있는 포켓몬이 좋습니다."

    if resistant_types:
        return "뚜렷한 약점은 적으므로, 부족한 공격 타입 커버리지를 늘릴 수 있는 포켓몬이 좋습니다."

    return "현재 분석 정보가 부족하므로, 타입이 겹치지 않는 포켓몬을 우선 고려하는 것이 좋습니다."


def build_team_insights(
    selected_pokemon: List[Dict[str, Any]],
    weak_types: List[Dict[str, Any]],
    resistant_types: List[Dict[str, Any]],
    move_type_coverage: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    팀 분석 원본 결과를 사용자가 이해하기 쉬운 해석 결과로 바꾸는 메인 함수입니다.

    Args:
        selected_pokemon: 사용자가 선택한 5마리 포켓몬 정보입니다.
        weak_types: 팀이 평균 1배 초과로 받는 공격 타입 목록입니다.
        resistant_types: 팀이 평균 1배 미만으로 받는 공격 타입 목록입니다.
        move_type_coverage: 팀 전체가 배울 수 있는 기술 타입 분포입니다.

    Returns:
        summary, risk_summary, strength_summary, role_summary 등을 담은 딕셔너리입니다.
    """

    type_counter = _build_type_counter(selected_pokemon)
    team_identity = _build_team_identity(selected_pokemon, type_counter)
    top_weak = _get_top_item(weak_types)

    # summary:
    # - 덱 분석 화면 최상단에 보여줄 핵심 총평입니다.
    if top_weak:
        summary = (
            f"이 팀은 {team_identity}입니다. "
            f"가장 먼저 확인할 위험은 {top_weak['type_name']} 타입 공격이며, "
            f"팀 평균 {top_weak['average_multiplier']:.2f}배 피해를 받습니다."
        )
    else:
        summary = f"이 팀은 {team_identity}입니다. 뚜렷하게 평균 1배를 넘는 약점 타입은 적은 편입니다."

    return {
        "team_identity": team_identity,
        "summary": summary,
        "risk_summary": _build_risk_summary(weak_types, type_counter),
        "strength_summary": _build_strength_summary(resistant_types, move_type_coverage),
        "role_summary": _build_role_summary(selected_pokemon),
        "type_balance": [
            {"type_name": type_name, "count": count}
            for type_name, count in type_counter.most_common()
        ],
        "recommendation_direction": _build_recommendation_direction(
            weak_types,
            resistant_types,
            type_counter,
        ),
    }
