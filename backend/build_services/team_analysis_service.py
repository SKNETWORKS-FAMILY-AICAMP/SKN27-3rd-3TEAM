"""
Pokemon team analysis service.

목적:
    선택한 5마리 포켓몬을 Neo4j Graph DB 기준으로 분석합니다.
    프론트엔드 분석 화면에서 사용할 약점, 저항, 타입 분포, 기술 타입 커버리지를 만듭니다.
"""

from typing import Any, Dict, List

from graph import queries
from graph.neo4j_client import Neo4jClient
from build_services.team_insight_service import build_team_insights
from build_services.team_score_service import build_type_matchup_items


# 선택한 포켓몬의 기본 정보와 타입을 조회하기 위한 Cypher 쿼리입니다.
SELECTED_POKEMON_DETAILS = """
MATCH (p:Pokemon)-[:HAS_TYPE]->(type:Type)
WHERE p.pokemon_id IN $selected_pokemon_ids
RETURN p.pokemon_id AS pokemon_id,
       p.name AS name,
       p.image_url AS image_url,
       p.base_total AS base_total,
       collect(DISTINCT {
           type_id: type.type_id,
           type_name: type.name
       }) AS types
ORDER BY p.pokemon_id
"""


# 선택한 팀이 배울 수 있는 기술 타입 분포를 조회하기 위한 Cypher 쿼리입니다.
TEAM_MOVE_TYPE_COVERAGE = """
MATCH (p:Pokemon)-[:CAN_KNOW]->(move:Move)-[:HAS_TYPE]->(moveType:Type)
WHERE p.pokemon_id IN $selected_pokemon_ids
RETURN moveType.type_id AS type_id,
       moveType.name AS type_name,
       count(DISTINCT move.move_id) AS move_count,
       collect(DISTINCT p.name)[0..5] AS example_pokemon
ORDER BY move_count DESC
"""


def _validate_team_size(pokemon_ids: List[int]) -> None:
    """
    팀 분석 요청이 5마리 기준인지 확인하기 위해 작성한 함수입니다.

    Args:
        pokemon_ids: 프론트엔드에서 선택한 포켓몬 ID 목록입니다.
    """
    # 추천 기능은 사용자가 5마리를 고른 뒤 1마리를 추천받는 흐름이므로 5개를 기준으로 제한합니다.
    if len(pokemon_ids) != 5:
        raise ValueError("팀 분석은 포켓몬 5마리를 선택해야 합니다.")

    # set으로 중복을 제거했을 때 길이가 달라지면 같은 포켓몬이 중복 선택된 것입니다.
    if len(set(pokemon_ids)) != len(pokemon_ids):
        raise ValueError("같은 포켓몬을 중복 선택할 수 없습니다.")


def _split_matchups(weakness_rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    AGAINST 배율 결과를 약점/보통/저항 목록으로 나누기 위해 작성한 함수입니다.

    Args:
        weakness_rows: TEAM_WEAKNESS_SUMMARY 쿼리 결과입니다.

    Returns:
        weak_types, neutral_types, resistant_types 세 목록을 담은 딕셔너리입니다.
    """
    # weak_types는 팀 평균 배율이 1보다 큰 공격 타입입니다.
    weak_types = []

    # neutral_types는 팀 평균 배율이 정확히 1에 가까운 공격 타입입니다.
    neutral_types = []

    # resistant_types는 팀 평균 배율이 1보다 작은 공격 타입입니다.
    resistant_types = []

    for row in weakness_rows:
        average_multiplier = float(row["average_multiplier"])
        item = {
            "type_id": row["type_id"],
            "type_name": row["type_name"],
            "weakness_score": float(row["weakness_score"]),
            "average_multiplier": average_multiplier,
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


def analyze_team(
    pokemon_ids: List[int],
    graph: Neo4jClient,
) -> Dict[str, Any]:
    """
    선택한 5마리 포켓몬 팀을 분석하기 위해 작성한 함수입니다.

    Args:
        pokemon_ids: 프론트엔드에서 선택한 포켓몬 ID 5개입니다.
        graph: Neo4j에 Cypher 쿼리를 실행하는 클라이언트입니다.

    Returns:
        프론트엔드가 바로 사용할 수 있는 팀 분석 결과 딕셔너리입니다.
    """
    _validate_team_size(pokemon_ids)

    # selected_pokemon은 선택한 포켓몬의 이름, 이미지, 타입, 능력치 합계입니다.
    selected_pokemon = graph.run_query(
        SELECTED_POKEMON_DETAILS,
        {"selected_pokemon_ids": pokemon_ids},
    )

    # weakness_summary는 팀이 각 공격 타입을 평균적으로 몇 배로 받는지 계산한 결과입니다.
    weakness_summary = graph.run_query(
        queries.TEAM_WEAKNESS_SUMMARY,
        {"selected_pokemon_ids": pokemon_ids},
    )

    # team_type_distribution은 팀 안에 어떤 타입이 몇 번 등장하는지 보여줍니다.
    team_type_distribution = graph.run_query(
        queries.TEAM_TYPE_DISTRIBUTION,
        {"selected_pokemon_ids": pokemon_ids},
    )

    # move_type_coverage는 팀 전체가 배울 수 있는 기술 타입 분포입니다.
    move_type_coverage = graph.run_query(
        TEAM_MOVE_TYPE_COVERAGE,
        {"selected_pokemon_ids": pokemon_ids},
    )

    # matchup_groups는 상성 결과를 약점/보통/저항으로 나눈 값입니다.
    matchup_groups = build_type_matchup_items(
        weakness_summary,
        team_size=len(pokemon_ids),
    )

    # insights:
    # - 숫자 분석 결과를 사용자가 이해하기 쉬운 총평/위험/강점/추천 방향으로 바꾼 값입니다.
    # - RAG를 붙이기 전까지는 규칙 기반 분석 문장으로 사용합니다.
    insights = build_team_insights(
        selected_pokemon=selected_pokemon,
        weak_types=matchup_groups["weak_types"],
        resistant_types=matchup_groups["resistant_types"],
        move_type_coverage=move_type_coverage,
    )

    return {
        "selected_pokemon": selected_pokemon,
        "weak_types": matchup_groups["weak_types"],
        "neutral_types": matchup_groups["neutral_types"],
        "resistant_types": matchup_groups["resistant_types"],
        "team_type_distribution": team_type_distribution,
        "move_type_coverage": move_type_coverage,
        "insights": insights,
    }
