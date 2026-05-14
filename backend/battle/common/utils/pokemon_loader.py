"""
Neo4j에서 봇 포켓몬 데이터를 조회하고 배틀용 dict로 변환하는 로더 모듈.

frontend/battle/utils.py의 BotBattlePokemon.__post_init__() 로직을 
순수 함수 형태로 백엔드에 이식합니다.
"""

import random
from typing import List, Optional
from graph.neo4j_client import neo4j_client


def _get_stats(base_stats: dict, level: int = 50) -> dict:
    """레벨 보정 스탯 계산 (frontend/battle/utils.py get_stats와 동일)"""
    new_stats = {}
    for stat, value in base_stats.items():
        if stat == 'hp':
            new_stats[stat] = int((((value * 2) + 100) * (level / 100)) + 10)
        else:
            new_stats[stat] = int((((value * 2) + 5) * (level / 100)) + 5)
    return new_stats


def _normalize(name: Optional[str]) -> str:
    return name.replace(" ", "").lower() if name else ""


def load_bot_pokemon(
    pokemon_id: int,
    name: str,
    selected_moves: List[str],
    multiplier: float = 1.1,
    level: int = 50
) -> dict:
    """
    Neo4j에서 봇 포켓몬 데이터를 조회하고 배틀 시작에 필요한 dict를 반환합니다.
    learn_method 제한 없이 모든 기술을 조회합니다 (BotPokemonDB와 동일).

    반환 형식은 frontend BotBattlePokemon을 asdict() 한 결과와 동일합니다.
    """
    with neo4j_client.driver.session() as session:
        # 1. 기본 포켓몬 정보 조회
        result = session.run(
            "MATCH (p:Pokemon {pokemon_id: $id}) RETURN p",
            {"id": pokemon_id}
        ).single()
        if not result:
            raise ValueError(f"Pokemon ID {pokemon_id} not found in Neo4j")
        info = dict(result["p"])

        # 2. 타입 조회
        type_records = session.run(
            "MATCH (p:Pokemon {pokemon_id: $id})-[:HAS_TYPE]->(t:Type) RETURN t.type_id as id, t.name as name",
            {"id": pokemon_id}
        )
        types = []
        type_names = []
        for r in type_records:
            types.append(r["id"])
            type_names.append(r["name"])

        # 3. 기술 조회 (learn_method 제한 없음 — 봇 전용)
        move_records = session.run(
            """
            MATCH (p:Pokemon {pokemon_id: $id})-[r:CAN_KNOW]->(m:Move)
            RETURN DISTINCT m.name as name, m.move_id as id, m.type_id as type_id,
                   m.power as power, m.accuracy as accuracy, m.damage_class as damage_class,
                   m.effect_text as effect_text, m.target as target,
                   m.category as category, m.stat_chance as stat_chance,
                   m.stat_changes as stat_changes, m.ailment as ailment,
                   m.ailment_chance as ailment_chance, m.drain as drain,
                   m.healing as healing, m.priority as priority,
                   m.flinch_chance as flinch_chance, m.crit_rate as crit_rate
            """,
            {"id": pokemon_id}
        )
        all_moves = []
        seen_names = set()
        for r in move_records:
            m_name = r["name"]
            if m_name and m_name not in seen_names:
                seen_names.add(m_name)
                all_moves.append(dict(r))

    # 4. 스탯 계산 (레벨 50 기준 + multiplier 보정)
    base_stats = {
        "hp": info.get("hp", 80),
        "attack": info.get("attack", 80),
        "defense": info.get("defense", 80),
        "sp_attack": info.get("sp_attack", 80),
        "sp_defense": info.get("sp_defense", 80),
        "speed": info.get("speed", 80)
    }
    stats = _get_stats(base_stats, level)
    if multiplier != 1.0:
        stats = {k: int(v * multiplier) for k, v in stats.items()}

    # 5. 기술 매칭 (선택된 기술 이름 → DB 기술 dict)
    normalized_targets = {_normalize(m) for m in selected_moves if m}
    matched_moves = [m for m in all_moves if _normalize(m["name"]) in normalized_targets]
    if not matched_moves:
        matched_moves = random.sample(all_moves, min(4, len(all_moves)))

    return {
        "id": pokemon_id,
        "name": name,
        "image_url": info.get("image_url", ""),
        "types": types,
        "type_names": type_names,
        "stats": stats,
        "max_hp": stats["hp"],
        "current_hp": stats["hp"],
        "moves": matched_moves,
        "level": level,
        "multiplier": multiplier,
        # 배틀 상태 초기값
        "attack_stage": 0,
        "sp_attack_stage": 0,
        "defense_stage": 0,
        "sp_defense_stage": 0,
        "speed_stage": 0,
        "accuracy_stage": 0,
        "evasion_stage": 0,
        "ailment": None,
        "sleep_turns": 0,
        "flinched": False,
        "last_damage_taken": 0,
        "last_move_received": None,
    }
