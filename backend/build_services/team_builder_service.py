"""
Pokemon team builder service.

목적:
    선택한 5마리 팀의 약점을 바탕으로 Graph DB에서 1~3순위 추천 포켓몬을 계산합니다.
    추천 판단은 Graph DB 관계와 간단한 점수 규칙을 사용하고, RAG 설명은 이후 단계에서 붙입니다.
"""

from typing import Any, Dict, List

from graph import queries
from graph.neo4j_client import Neo4jClient
from build_services.team_analysis_service import analyze_team


def _describe_defensive_relation(relation: str, multiplier: float) -> str:
    """Graph DB 방어 관계를 사용자에게 읽기 쉬운 한국어 표현으로 바꾸는 함수입니다."""

    # relation:
    # - Neo4j에는 RESISTANT_TO, VERY_RESISTANT_TO, IMMUNE_TO 같은 관계명으로 저장되어 있습니다.
    relation_labels = {
        "IMMUNE_TO": "무효",
        "VERY_RESISTANT_TO": "강한 저항",
        "RESISTANT_TO": "저항",
    }
    label = relation_labels.get(relation, "저항")
    return f"{label}({multiplier}배)"


def _build_defensive_reason(defensive_covers: List[Dict[str, Any]]) -> str:
    """후보가 어떤 약점 타입을 어떤 방식으로 보완하는지 설명하는 함수입니다."""

    if not defensive_covers:
        return "현재 팀의 주요 약점을 직접 저항/무효로 받는 정보는 부족합니다."

    # cover_texts:
    # - 예: 바위는 저항(0.5배), 전기는 무효(0배)
    cover_texts = [
        f"{cover['type_name']}는 {_describe_defensive_relation(cover.get('relation'), cover.get('multiplier'))}"
        for cover in defensive_covers[:5]
    ]
    return f"{', '.join(cover_texts)}로 받아 현재 팀의 약점 부담을 줄입니다."


def _build_useful_move_notes(
    useful_moves: List[Dict[str, Any]],
    candidate_types: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """추천 후보가 배울 수 있는 기술 중 설명에 쓸 대표 기술을 고르는 함수입니다."""

    # candidate_type_ids:
    # - 후보 자신의 타입과 같은 기술은 STAB 보너스를 기대할 수 있으므로 우선 설명 대상으로 둡니다.
    candidate_type_ids = {type_row["type_id"] for type_row in candidate_types}

    enriched_moves = []
    for move in useful_moves:
        is_stab = move.get("type_id") in candidate_type_ids
        enriched_moves.append(
            {
                **move,
                "is_stab": is_stab,
                "usage_note": (
                    f"{move.get('move_name')}은 {move.get('type_name')} 타입 주력기로 쓰기 좋습니다."
                    if is_stab
                    else f"{move.get('move_name')}은 {move.get('type_name')} 타입 견제 폭을 넓힐 때 유용합니다."
                ),
            }
        )

    # STAB 기술을 먼저, 그다음 위력이 높은 기술을 우선 노출합니다.
    return sorted(
        enriched_moves,
        key=lambda move: (move.get("is_stab", False), move.get("power") or 0),
        reverse=True,
    )[:5]


def _build_move_reason(useful_move_notes: List[Dict[str, Any]]) -> str:
    """추천 이유에 들어갈 대표 기술 설명 문장을 만드는 함수입니다."""

    if not useful_move_notes:
        return "대표 기술 정보가 부족해 기술 기반 추천 이유는 제한적입니다."

    # primary_moves:
    # - 너무 많은 기술을 한 문장에 넣으면 오히려 읽기 어려우므로 상위 3개만 요약합니다.
    primary_moves = [
        f"{move['move_name']}({move['type_name']}, 위력 {move.get('power')})"
        for move in useful_move_notes[:3]
    ]
    return f"대표적으로 {', '.join(primary_moves)}를 활용해 공격 선택지를 넓힐 수 있습니다."


def _build_candidate_score(
    candidate: Dict[str, Any],
    candidate_move_types: List[Dict[str, Any]],
    candidate_types: List[Dict[str, Any]],
    useful_moves: List[Dict[str, Any]],
    team_type_counts: Dict[int, int],
) -> Dict[str, Any]:
    """
    추천 후보 1마리의 점수와 추천 이유를 계산하기 위해 작성한 함수입니다.

    Args:
        candidate: 방어 상성 기준으로 조회된 추천 후보 정보입니다.
        candidate_move_types: 후보가 배울 수 있는 기술 타입 목록입니다.
        candidate_types: 후보 포켓몬 자신의 타입 목록입니다.
        team_type_counts: 현재 팀의 타입별 중복 개수입니다.

    Returns:
        점수와 이유가 추가된 추천 후보 딕셔너리입니다.
    """
    # base_total은 포켓몬의 기본 능력치 합계이며, 추천 후보의 기본 체급을 판단하는 데 사용합니다.
    base_total = candidate.get("base_total") or 0

    # defensive_covers는 현재 팀의 약점 타입을 후보가 얼마나 저항/무효로 받아주는지 의미합니다.
    defensive_covers = candidate.get("defensive_covers", [])

    # move_type_count는 후보가 배울 수 있는 기술 타입의 다양성을 의미합니다.
    move_type_count = len(candidate_move_types)

    # duplicate_type_count는 후보 타입이 현재 팀과 겹치는 "종류" 수를 의미합니다.
    # 팀에 같은 타입이 여러 번 있어도 후보 입장에서는 해당 타입 1종류가 겹친 것으로 봅니다.
    team_type_ids = {type_id for type_id, count in team_type_counts.items() if count > 0}
    duplicate_type_ids = {
        type_row["type_id"]
        for type_row in candidate_types
        if type_row.get("type_id") in team_type_ids
    }
    duplicate_type_count = len(duplicate_type_ids)

    # useful_move_notes는 RAG와 프론트 카드에서 사용할 대표 기술 설명 목록입니다.
    useful_move_notes = _build_useful_move_notes(useful_moves, candidate_types)

    # defensive_score는 약점을 보완하는 정도를 가장 크게 반영합니다.
    defensive_score = len(defensive_covers) * 25

    # stat_score는 기본 능력치를 추천의 보조 기준으로만 반영하기 위해 최대 5점으로 제한합니다.
    stat_score = round(min(base_total / 140, 5), 2)

    # coverage_score는 후보가 다양한 타입 기술을 배울수록 조금 더 높게 줍니다.
    coverage_score = min(move_type_count * 1.5, 20)

    # duplicate_penalty는 6번째 포켓몬의 타입 다양성을 강하게 유도하기 위한 감점입니다.
    # 후보 타입 1종류가 현재 팀과 겹치면 20점, 2종류가 겹치면 최대 40점까지 감점합니다.
    duplicate_penalty = min(duplicate_type_count * 20, 40)

    # total_score는 추천 정렬에 사용할 최종 점수입니다.
    total_score = round(
        defensive_score + stat_score + coverage_score - duplicate_penalty,
        2,
    )

    # reasons는 프론트엔드와 이후 RAG 설명에 전달할 추천 근거 목록입니다.
    reasons = [
        _build_defensive_reason(defensive_covers),
        f"기본 능력치 합계가 {base_total}이며 능력치 보조 점수는 {stat_score}점입니다.",
        _build_move_reason(useful_move_notes),
        f"{move_type_count}개 타입의 기술을 배울 수 있어 기술 선택 폭이 넓습니다.",
    ]

    if duplicate_type_count:
        reasons.append(f"현재 팀과 겹치는 타입 종류가 {duplicate_type_count}개 있어 감점했습니다.")

    return {
        "pokemon_id": candidate["pokemon_id"],
        "name": candidate["name"],
        "image_url": candidate.get("image_url"),
        "base_total": base_total,
        "graph_score": total_score,
        "score": total_score,
        "defensive_covers": defensive_covers,
        "move_types": candidate_move_types,
        "pokemon_types": candidate_types,
        "types": candidate_types,
        "useful_moves": useful_move_notes,
        "reasons": reasons,
    }


def _index_by_pokemon_id(rows: List[Dict[str, Any]], value_key: str) -> Dict[int, List[Dict[str, Any]]]:
    """
    후보별 상세 목록을 pokemon_id 기준 딕셔너리로 바꾸기 위해 작성한 함수입니다.

    Args:
        rows: Neo4j에서 후보별로 조회한 row 목록입니다.
        value_key: row 안에서 리스트 값을 꺼낼 키 이름입니다.
    """
    # indexed는 pokemon_id를 key로, 타입 목록을 value로 갖는 딕셔너리입니다.
    indexed = {}
    for row in rows:
        indexed[row["pokemon_id"]] = row.get(value_key, [])
    return indexed


def recommend_team_member(
    pokemon_ids: List[int],
    graph: Neo4jClient,
    limit: int = 3,
) -> Dict[str, Any]:
    """
    선택한 5마리를 기준으로 추천 포켓몬 1~3순위를 계산하기 위해 작성한 함수입니다.

    Args:
        pokemon_ids: 프론트엔드에서 선택한 포켓몬 ID 5개입니다.
        graph: Neo4j에 Cypher 쿼리를 실행하는 클라이언트입니다.
        limit: 반환할 추천 후보 수입니다.

    Returns:
        팀 분석 결과와 추천 후보 목록을 함께 담은 딕셔너리입니다.
    """
    # analysis는 추천 후보를 찾기 전에 계산한 팀 약점/저항/타입 분포 결과입니다.
    analysis = analyze_team(pokemon_ids, graph)

    # weak_type_ids는 평균 배율이 1보다 큰 팀 약점 타입 ID 목록입니다.
    weak_type_ids = [row["type_id"] for row in analysis["weak_types"]]

    # 약점이 명확하지 않은 경우에도 추천이 비지 않도록 상위 취약 타입 3개를 fallback으로 사용합니다.
    if not weak_type_ids:
        weakness_rows = sorted(
            analysis["neutral_types"] + analysis["resistant_types"],
            key=lambda row: row["weakness_score"],
            reverse=True,
        )
        weak_type_ids = [row["type_id"] for row in weakness_rows[:3]]

    # candidate_limit은 중간 후보를 넉넉히 가져온 뒤 서비스 레이어에서 다시 점수화하기 위한 값입니다.
    candidate_limit = max(limit * 8, 20)

    # candidates는 약점 타입을 저항/무효로 받아주는 추천 후보 목록입니다.
    candidates = graph.run_query(
        queries.DEFENSIVE_CANDIDATES_BY_WEAK_TYPES,
        {
            "selected_pokemon_ids": pokemon_ids,
            "weak_type_ids": weak_type_ids,
            "limit": candidate_limit,
        },
    )

    # candidate_ids는 후보 상세 정보를 추가 조회하기 위한 포켓몬 ID 목록입니다.
    candidate_ids = [candidate["pokemon_id"] for candidate in candidates]

    if not candidate_ids:
        return {
            "analysis": analysis,
            "recommendations": [],
        }

    # move_type_rows는 후보별로 배울 수 있는 기술 타입을 조회한 결과입니다.
    move_type_rows = graph.run_query(
        queries.CANDIDATE_MOVE_TYPES,
        {"candidate_pokemon_ids": candidate_ids},
    )

    # pokemon_type_rows는 후보 자신의 타입을 조회한 결과입니다.
    pokemon_type_rows = graph.run_query(
        queries.CANDIDATE_TYPES,
        {"candidate_pokemon_ids": candidate_ids},
    )

    # useful_move_rows는 후보가 실제로 어떤 기술을 활용할 수 있는지 설명하기 위한 대표 기술 목록입니다.
    useful_move_rows = graph.run_query(
        queries.CANDIDATE_USEFUL_MOVES,
        {"candidate_pokemon_ids": candidate_ids},
    )

    # move_types_by_candidate는 pokemon_id 기준으로 기술 타입 목록을 찾기 위한 딕셔너리입니다.
    move_types_by_candidate = _index_by_pokemon_id(move_type_rows, "move_types")

    # pokemon_types_by_candidate는 pokemon_id 기준으로 후보 타입 목록을 찾기 위한 딕셔너리입니다.
    pokemon_types_by_candidate = _index_by_pokemon_id(pokemon_type_rows, "pokemon_types")

    # useful_moves_by_candidate는 pokemon_id 기준으로 후보 대표 기술 목록을 찾기 위한 딕셔너리입니다.
    useful_moves_by_candidate = _index_by_pokemon_id(useful_move_rows, "useful_moves")

    # team_type_counts는 현재 팀의 타입 중복 정도를 판단하기 위한 딕셔너리입니다.
    team_type_counts = {
        row["type_id"]: row["count"]
        for row in analysis["team_type_distribution"]
    }

    # scored_candidates는 점수와 이유를 추가한 후보 목록입니다.
    scored_candidates = [
        _build_candidate_score(
            candidate,
            move_types_by_candidate.get(candidate["pokemon_id"], []),
            pokemon_types_by_candidate.get(candidate["pokemon_id"], []),
            useful_moves_by_candidate.get(candidate["pokemon_id"], []),
            team_type_counts,
        )
        for candidate in candidates
    ]

    # 점수가 높은 후보부터 정렬하고 요청한 개수만 반환합니다.
    recommendations = sorted(
        scored_candidates,
        key=lambda row: row.get("graph_score", row.get("score", 0)),
        reverse=True,
    )[:limit]

    # rank는 화면에서 1순위, 2순위, 3순위로 보여주기 위한 번호입니다.
    for index, recommendation in enumerate(recommendations, start=1):
        recommendation["rank"] = index

    return {
        "analysis": analysis,
        "recommendations": recommendations,
    }
