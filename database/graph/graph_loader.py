"""
Pokemon Graph DB Loader

목적:
    database/common/data/processed/*.json 파일을 읽어서 Neo4j에 포켓몬 그래프를 적재합니다.

큰 흐름:
    1. Neo4j 연결
    2. constraints.cypher 실행
    3. Node 생성
    4. Relationship 생성
    5. 타입 상성을 이용한 파생 Relationship 생성

실행 예시:
    python database/graph/graph_loader.py

초기화 후 다시 적재:
    python database/graph/graph_loader.py --reset
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase


# ============================================
# 1. 기본 경로와 환경변수 설정
# ============================================
# 이 파일은 database/graph/graph_loader.py 위치에 있습니다.
# parents[2]는 프로젝트 루트(SKN27-3rd-3TEAM)를 의미합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# processed JSON 파일들이 저장된 위치입니다.
# 현재 정리된 프로젝트 구조가 database/common/data/processed를 사용하므로 여기에 맞춥니다.
PROCESSED_DATA_DIR = PROJECT_ROOT / "database" / "common" / "data" / "processed"

# Neo4j 제약조건/인덱스가 들어있는 Cypher 파일입니다.
CONSTRAINTS_PATH = Path(__file__).resolve().parent / "constraints.cypher"

# 한 번에 Neo4j로 보낼 데이터 개수입니다.
# 너무 크면 메모리 부담이 생기고, 너무 작으면 느려질 수 있습니다.
BATCH_SIZE = 1000


# .env 파일을 읽어서 NEO4J_URI 같은 값을 사용할 수 있게 합니다.
load_dotenv(PROJECT_ROOT / ".env")

class Singleton(type):
	_instances = {}

	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls)\
				.__call__(*args, **kwargs)
		return cls._instances[cls]

# ============================================
# 2. Neo4j 연결 클래스
# ============================================
class Neo4jConnection(metaclass=Singleton):
    """Neo4j 연결과 Cypher 실행을 담당하는 클래스입니다."""

    def __init__(self, uri: str, user: str, password: str):
        """
        Neo4j 드라이버를 생성합니다.

        Args:
            uri: Neo4j Bolt 주소입니다. 예: bolt://localhost:7687
            user: Neo4j 사용자명입니다. 기본값은 neo4j인 경우가 많습니다.
            password: Neo4j 비밀번호입니다.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        """Neo4j 드라이버 연결을 종료합니다."""
        if self.driver is not None:
            self.driver.close()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Cypher 쿼리를 실행하고 결과를 리스트로 반환합니다.

        Args:
            query: 실행할 Cypher 쿼리 문자열입니다.
            parameters: 쿼리에 전달할 파라미터 딕셔너리입니다.

        Returns:
            Neo4j Record 객체 리스트입니다.
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        데이터를 생성/수정하는 Cypher 쿼리를 실행합니다.

        execute_query와 역할은 비슷하지만, 반환값이 필요 없는 적재 쿼리에 사용합니다.
        """
        with self.driver.session() as session:
            session.run(query, parameters or {}).consume()


# ============================================
# 3. 공통 유틸 함수
# ============================================
def load_json(filename: str) -> List[Dict[str, Any]]:
    """
    processed 폴더에서 JSON 파일을 읽습니다.

    Args:
        filename: 읽을 JSON 파일명입니다. 예: pokemon.json

    Returns:
        JSON 배열을 파이썬 list[dict] 형태로 반환합니다.
    """
    file_path = PROCESSED_DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Processed JSON not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def chunked(rows: List[Dict[str, Any]], size: int = BATCH_SIZE) -> Iterable[List[Dict[str, Any]]]:
    """
    큰 리스트를 일정 크기 단위로 나눕니다.

    Args:
        rows: Neo4j로 보낼 데이터 목록입니다.
        size: 한 번에 보낼 데이터 개수입니다.

    Yields:
        size 개수만큼 잘린 리스트입니다.
    """
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def run_batched(conn: Neo4jConnection, query: str, rows: List[Dict[str, Any]], label: str) -> None:
    """
    UNWIND 기반 Cypher 쿼리를 배치 단위로 실행합니다.

    Args:
        conn: Neo4j 연결 객체입니다.
        query: UNWIND $rows AS row 형태의 Cypher 쿼리입니다.
        rows: 쿼리에 전달할 데이터 목록입니다.
        label: 로그에 표시할 작업 이름입니다.
    """
    total = len(rows)
    if total == 0:
        print(f"{label}: 0 rows skipped")
        return

    done = 0
    for batch in chunked(rows):
        conn.execute_write(query, {"rows": batch})
        done += len(batch)
        print(f"{label}: {done}/{total}")


def parse_cypher_statements(cypher_text: str) -> List[str]:
    """
    constraints.cypher 파일을 개별 문장으로 나눕니다.

    Neo4j Python driver는 여러 Cypher 문장을 한 번에 실행하지 못하므로,
    세미콜론 기준으로 나눠서 하나씩 실행합니다.
    """
    statements = []
    for statement in cypher_text.split(";"):
        cleaned = statement.strip()
        if cleaned:
            statements.append(cleaned)
    return statements


# ============================================
# 4. DB 준비 함수
# ============================================
def apply_constraints(conn: Neo4jConnection) -> None:
    """
    constraints.cypher 파일을 실행합니다.

    목적:
        Pokemon, Type, Move 같은 노드가 중복 생성되지 않도록
        unique constraint와 index를 Neo4j에 먼저 등록합니다.
    """
    cypher_text = CONSTRAINTS_PATH.read_text(encoding="utf-8")
    statements = parse_cypher_statements(cypher_text)

    for statement in statements:
        conn.execute_write(statement)

    print(f"Constraints and indexes applied: {len(statements)} statements")


def reset_graph(conn: Neo4jConnection) -> None:
    """
    Neo4j 안의 모든 노드와 관계를 삭제합니다.

    주의:
        --reset 옵션을 줄 때만 실행합니다.
        개발 중 전체 데이터를 다시 넣고 싶을 때 사용합니다.
    """
    query = """
    MATCH (n)
    DETACH DELETE n
    """
    conn.execute_write(query)
    print("Existing graph data deleted")


# ============================================
# 5. Node 생성 함수
# ============================================
def create_type_nodes(conn: Neo4jConnection) -> None:
    """
    Type 노드를 생성합니다.

    Source:
        types.json
    """
    rows = [
        {
            "type_id": row["id"],
            "name": row["name"],
        }
        for row in load_json("types.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (t:Type {type_id: row.type_id})
    SET t.name = row.name
    """
    run_batched(conn, query, rows, "Type nodes")


def create_pokemon_nodes(conn: Neo4jConnection) -> None:
    """
    Pokemon 노드를 생성합니다.

    Source:
        pokemon.json
        pokemon_stats.json

    설명:
        pokemon.json의 기본 정보와 pokemon_stats.json의 능력치를 합쳐서
        Pokemon 노드 속성으로 저장합니다.
    """
    pokemon_rows = load_json("pokemon.json")
    stats_rows = load_json("pokemon_stats.json")

    # stats_by_id는 pokemon_id를 기준으로 능력치를 빠르게 찾기 위한 딕셔너리입니다.
    stats_by_id = {row["pokemon_id"]: row for row in stats_rows}

    rows = []
    for pokemon in pokemon_rows:
        stats = stats_by_id.get(pokemon["id"], {})

        hp = stats.get("hp", 0)
        attack = stats.get("attack", 0)
        defense = stats.get("defense", 0)
        sp_attack = stats.get("sp_attack", 0)
        sp_defense = stats.get("sp_defense", 0)
        speed = stats.get("speed", 0)

        rows.append(
            {
                "pokemon_id": pokemon["id"],
                "name": pokemon["name"],
                "height": pokemon.get("height"),
                "weight": pokemon.get("weight"),
                "base_exp": pokemon.get("base_exp"),
                "image_url": pokemon.get("image_url"),
                "cry_url": pokemon.get("cry_url"),
                "is_default": pokemon.get("is_default", True),
                "hp": hp,
                "attack": attack,
                "defense": defense,
                "sp_attack": sp_attack,
                "sp_defense": sp_defense,
                "speed": speed,
                "base_total": hp + attack + defense + sp_attack + sp_defense + speed,
            }
        )

    query = """
    UNWIND $rows AS row
    MERGE (p:Pokemon {pokemon_id: row.pokemon_id})
    SET p.name = row.name,
        p.height = row.height,
        p.weight = row.weight,
        p.base_exp = row.base_exp,
        p.image_url = row.image_url,
        p.cry_url = row.cry_url,
        p.is_default = row.is_default,
        p.hp = row.hp,
        p.attack = row.attack,
        p.defense = row.defense,
        p.sp_attack = row.sp_attack,
        p.sp_defense = row.sp_defense,
        p.speed = row.speed,
        p.base_total = row.base_total
    """
    run_batched(conn, query, rows, "Pokemon nodes")


def create_move_nodes(conn: Neo4jConnection) -> None:
    """
    Move 노드를 생성합니다.

    Source:
        moves.json
    """
    rows = [
        {
            "move_id": row["id"],
            "name": row["name"],
            "type_id": row.get("type_id"),
            "power": row.get("power"),
            "accuracy": row.get("accuracy"),
            "damage_class": row.get("damage_class"),
            "effect_text": row.get("effect_text"),
        }
        for row in load_json("moves.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (m:Move {move_id: row.move_id})
    SET m.name = row.name,
        m.type_id = row.type_id,
        m.power = row.power,
        m.accuracy = row.accuracy,
        m.damage_class = row.damage_class,
        m.effect_text = row.effect_text
    """
    run_batched(conn, query, rows, "Move nodes")


def create_ability_nodes(conn: Neo4jConnection) -> None:
    """
    Ability 노드를 생성합니다.

    Source:
        abilities.json
    """
    rows = [
        {
            "ability_id": row["id"],
            "name": row["name"],
            "effect_text": row.get("effect_text"),
        }
        for row in load_json("abilities.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (a:Ability {ability_id: row.ability_id})
    SET a.name = row.name,
        a.effect_text = row.effect_text
    """
    run_batched(conn, query, rows, "Ability nodes")


def create_item_nodes(conn: Neo4jConnection) -> None:
    """
    Item 노드를 생성합니다.

    Source:
        items.json

    설명:
        초기 팀 추천에서는 직접 쓰지 않더라도,
        배틀과 메가진화 확장을 위해 미리 적재합니다.
    """
    rows = [
        {
            "item_id": row["id"],
            "name": row["name"],
            "category": row.get("category"),
            "effect_text": row.get("effect_text"),
        }
        for row in load_json("items.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (i:Item {item_id: row.item_id})
    SET i.name = row.name,
        i.category = row.category,
        i.effect_text = row.effect_text
    """
    run_batched(conn, query, rows, "Item nodes")


def create_nature_nodes(conn: Neo4jConnection) -> None:
    """
    Nature 노드를 생성합니다.

    Source:
        natures.json

    설명:
        성격은 포켓몬 종 자체의 정보가 아니라 실제 배틀 개체의 세팅입니다.
        따라서 지금은 Nature 노드만 만들고, 나중에 TeamMember - HAS_NATURE -> Nature 관계로 연결합니다.
    """
    rows = [
        {
            "nature_id": row["id"],
            "name": row["name"],
            "increased_stat": row.get("increased_stat"),
            "decreased_stat": row.get("decreased_stat"),
        }
        for row in load_json("natures.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (n:Nature {nature_id: row.nature_id})
    SET n.name = row.name,
        n.increased_stat = row.increased_stat,
        n.decreased_stat = row.decreased_stat
    """
    run_batched(conn, query, rows, "Nature nodes")


def create_species_and_generation_nodes(conn: Neo4jConnection) -> None:
    """
    Species와 Generation 노드를 생성합니다.

    Source:
        species.json

    설명:
        진화 관계는 species_id 기준이므로 Species 노드가 필요합니다.
        Generation은 세대 제한 추천이나 배틀 룰 확장에 사용할 수 있습니다.
    """
    species_rows = load_json("species.json")

    species_payload = [
        {
            "species_id": row["id"],
            "pokemon_id": row.get("pokemon_id"),
            "generation": row.get("generation"),
            "capture_rate": row.get("capture_rate"),
        }
        for row in species_rows
    ]

    # species.json에 들어있는 generation 번호를 중복 없이 모읍니다.
    generation_ids = sorted({row.get("generation") for row in species_rows if row.get("generation")})
    generation_payload = [
        {
            "generation_id": generation_id,
            "name": f"generation-{generation_id}",
        }
        for generation_id in generation_ids
    ]

    species_query = """
    UNWIND $rows AS row
    MERGE (s:Species {species_id: row.species_id})
    SET s.pokemon_id = row.pokemon_id,
        s.generation = row.generation,
        s.capture_rate = row.capture_rate
    """
    generation_query = """
    UNWIND $rows AS row
    MERGE (g:Generation {generation_id: row.generation_id})
    SET g.name = row.name
    """

    run_batched(conn, species_query, species_payload, "Species nodes")
    run_batched(conn, generation_query, generation_payload, "Generation nodes")

def create_effect_nodes(conn: Neo4jConnection) -> None:
    """
    Effect 노드를 생성합니다.

    Source:
        effects.json
    
    설명:
        일부 기술, 특성, 도구는 배틀에 영향을 주는 부가 효과를 갖고 있습니다.
    """
    rows = [
        {
            "effect_id": row["id"],
            "name": row["name"],
            "effect_type": row["effect_type"],
            "effect_text": row["effect_text"]
        }
        for row in load_json('effects.json')
    ]

    query = """
    UNWIND $rows AS row
    MERGE (e:Effect {effect_id: row.effect_id})
    SET e.name = row.name,
        e.effect_type = row.effect_type,
        e.effect_text = row.effect_text
    """
    run_batched(conn, query, rows, "Effect nodes")

def create_stat_nodes(conn: Neo4jConnection) -> None:
    """
    Stat 노드를 생성합니다.

    Source:
        pokemon_stats.json
    
    설명:
        포켓몬의 능력치를 나타냅니다.
        배틀에서 기술의 데미지를 계산하는 기준이 되며, 수치는 특성, 기술, 도구 등에 의해 변동될 수 있습니다.
    """
    rows = [
        {
            "stat_id": row['id'],
            "name": row['name'],
            "battle_stage_applicable": False if row['name'] == 'hp' else True,
            "description": row['description']
        }
        for row in load_json('stats.json')
    ]

    query = """
    UNWIND $rows AS row
    MERGE (s:Stat {stat_id: row.stat_id})
    SET s.name = row.name,
        s.battle_stage_applicable = row.battle_stage_applicable,
        s.description = row.description
    """
    run_batched(conn, query, rows, "Stat nodes")

def create_status_condition_nodes(conn: Neo4jConnection) -> None:
    """
    StatusCondition 노드를 생성합니다.

    Source:
        status_conditions.json

    설명:
        배틀에 영향을 주는 상태 이상을 노드로 생성합니다.
    """
    rows = [
        {
            "status_condition_id": row["id"],
            "name": row["name"],
            "effect_text": row["effect_text"]
        }
        for row in load_json("status_conditions.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (s:StatusCondition {status_condition_id: row.status_condition_id})
    SET s.name = row.name,
        s.effect_text = row.effect_text
    """
    run_batched(conn, query, rows, "StatusCondition nodes")

def create_phase_nodes(conn: Neo4jConnection) -> None:
    """
    Phase 노드를 생성합니다.

    Source:
        battle_phases.json

    설명:
        배틀의 단계를 노드로 생성합니다.
    """
    rows = [
        {
            "phase_id": row["id"],
            "name": row["name"],
            "order": row["order"],
            "description": row["description"]
        }
        for row in load_json("phases.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (p:Phase {phase_id: row.phase_id})
    SET p.name = row.name,
        p.order = row.order,
        p.description = row.description
    """
    run_batched(conn, query, rows, "Phase nodes")

def create_weather_nodes(conn: Neo4jConnection) -> None:
    """
    Weather 노드를 생성합니다.

    Source:
        weathers.json

    설명:
        쾌청, 비, 모래바람, 싸라기눈 4가지 날씨 노드를 생성합니다.
    """
    rows = [
        {
            "weather_id": row["id"],
            "name":       row["name"],
            "name_en":    row["name_en"],
            "description": row["description"],
        }
        for row in load_json("weathers.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (w:Weather {weather_id: row.weather_id})
    SET w.name        = row.name,
        w.name_en     = row.name_en,
        w.description = row.description
    """
    run_batched(conn, query, rows, "Weather nodes")


def create_field_effect_nodes(conn: Neo4jConnection) -> None:
    """
    Field 노드를 생성합니다.

    Source:
        fields.json

    설명:
        그래스필드, 미스트필드, 일렉트릭필드, 사이코필드,
        트릭룸, 매직룸, 원더룸, 중력 8가지 필드 노드를 생성합니다.
    """
    rows = [
        {
            "field_id":   row["id"],
            "name":       row["name"],
            "name_en":    row["name_en"],
            "description": row["description"],
        }
        for row in load_json("fields.json")
    ]

    query = """
    UNWIND $rows AS row
    MERGE (f:Field {field_id: row.field_id})
    SET f.name        = row.name,
        f.name_en     = row.name_en,
        f.description = row.description
    """
    run_batched(conn, query, rows, "Field nodes")


# ============================================
# 6. 원본 관계 생성 함수
# ============================================
def create_pokemon_has_type_relationships(conn: Neo4jConnection) -> None:
    """
    Pokemon - HAS_TYPE -> Type 관계를 생성합니다.

    Source:
        pokemon_types.json
    """
    rows = [
        {
            "pokemon_id": row["pokemon_id"],
            "type_id": row["type_id"],
            "slot": row.get("slot"),
        }
        for row in load_json("pokemon_types.json")
    ]

    query = """
    UNWIND $rows AS row
    MATCH (p:Pokemon {pokemon_id: row.pokemon_id})
    MATCH (t:Type {type_id: row.type_id})
    MERGE (p)-[r:HAS_TYPE]->(t)
    SET r.slot = row.slot
    """
    run_batched(conn, query, rows, "Pokemon HAS_TYPE relationships")


def create_move_has_type_relationships(conn: Neo4jConnection) -> None:
    """
    Move - HAS_TYPE -> Type 관계를 생성합니다.

    Source:
        moves.json
    """
    rows = [
        {
            "move_id": row["id"],
            "type_id": row.get("type_id"),
        }
        for row in load_json("moves.json")
        if row.get("type_id") is not None
    ]

    query = """
    UNWIND $rows AS row
    MATCH (m:Move {move_id: row.move_id})
    MATCH (t:Type {type_id: row.type_id})
    MERGE (m)-[:HAS_TYPE]->(t)
    """
    run_batched(conn, query, rows, "Move HAS_TYPE relationships")


def create_pokemon_can_know_relationships(conn: Neo4jConnection) -> None:
    """
    Pokemon - CAN_KNOW -> Move 관계를 생성합니다.

    Source:
        pokemon_moves.json

    설명:
        같은 포켓몬과 기술이라도 습득 방식이 다를 수 있으므로
        learn_method와 level_learned_at을 관계 속성으로 둡니다.
    """
    rows = [
        {
            "pokemon_id": row["pokemon_id"],
            "move_id": row["move_id"],
            "learn_method": row.get("learn_method"),
            "level_learned_at": row.get("level_learned_at"),
        }
        for row in load_json("pokemon_moves.json")
    ]

    query = """
    UNWIND $rows AS row
    MATCH (p:Pokemon {pokemon_id: row.pokemon_id})
    MATCH (m:Move {move_id: row.move_id})
    MERGE (p)-[r:CAN_KNOW {
        learn_method: row.learn_method,
        level_learned_at: row.level_learned_at
    }]->(m)
    """
    run_batched(conn, query, rows, "Pokemon CAN_KNOW relationships")


def create_pokemon_can_have_relationships(conn: Neo4jConnection) -> None:
    """
    Pokemon - CAN_HAVE -> Ability 관계를 생성합니다.

    Source:
        pokemon_abilities.json
    """
    rows = [
        {
            "pokemon_id": row["pokemon_id"],
            "ability_id": row["ability_id"],
            "is_hidden": row.get("is_hidden"),
            "slot": row.get("slot"),
        }
        for row in load_json("pokemon_abilities.json")
    ]

    query = """
    UNWIND $rows AS row
    MATCH (p:Pokemon {pokemon_id: row.pokemon_id})
    MATCH (a:Ability {ability_id: row.ability_id})
    MERGE (p)-[r:CAN_HAVE]->(a)
    SET r.is_hidden = row.is_hidden,
        r.slot = row.slot
    """
    run_batched(conn, query, rows, "Pokemon CAN_HAVE relationships")


def create_type_efficacy_relationships(conn: Neo4jConnection) -> None:
    """
    Type - ATTACK_EFFECTIVE -> Type 관계를 생성합니다.

    Source:
        type_efficacy.json

    방향:
        공격 타입 -> 방어 타입
    """
    rows = [
        {
            "damage_type_id": row["damage_type_id"],
            "target_type_id": row["target_type_id"],
            "damage_factor": row["damage_factor"],
        }
        for row in load_json("type_efficacy.json")
    ]

    query = """
    UNWIND $rows AS row
    MATCH (attackType:Type {type_id: row.damage_type_id})
    MATCH (targetType:Type {type_id: row.target_type_id})
    MERGE (attackType)-[r:ATTACK_EFFECTIVE]->(targetType)
    SET r.damage_factor = row.damage_factor
    """
    run_batched(conn, query, rows, "Type ATTACK_EFFECTIVE relationships")


def create_species_relationships(conn: Neo4jConnection) -> None:
    """
    Pokemon - IS_SPECIES -> Species,
    Species - FROM -> Generation 관계를 생성합니다.

    Source:
        species.json
    """
    rows = [
        {
            "species_id": row["id"],
            "pokemon_id": row.get("pokemon_id"),
            "generation": row.get("generation"),
        }
        for row in load_json("species.json")
    ]

    pokemon_species_query = """
    UNWIND $rows AS row
    MATCH (p:Pokemon {pokemon_id: row.pokemon_id})
    MATCH (s:Species {species_id: row.species_id})
    MERGE (p)-[:IS_SPECIES]->(s)
    """

    species_generation_query = """
    UNWIND $rows AS row
    MATCH (s:Species {species_id: row.species_id})
    MATCH (g:Generation {generation_id: row.generation})
    MERGE (s)-[:FROM]->(g)
    """

    run_batched(conn, pokemon_species_query, rows, "Pokemon IS_SPECIES relationships")
    run_batched(conn, species_generation_query, rows, "Species FROM Generation relationships")


def create_evolution_relationships(conn: Neo4jConnection) -> None:
    """
    Species - EVOLVES_TO -> Species 관계를 생성합니다.

    Source:
        evolutions.json

    설명:
        trigger_item_id가 있는 경우에는 Species - EVOLUTION_REQUIRES -> Item 관계도 생성합니다.
    """
    rows = [
        {
            "from_species_id": row["from_species_id"],
            "to_species_id": row["to_species_id"],
            "min_level": row.get("min_level"),
            "trigger_item_id": row.get("trigger_item_id"),
        }
        for row in load_json("evolutions.json")
    ]

    evolution_query = """
    UNWIND $rows AS row
    MATCH (fromSpecies:Species {species_id: row.from_species_id})
    MATCH (toSpecies:Species {species_id: row.to_species_id})
    MERGE (fromSpecies)-[r:EVOLVES_TO]->(toSpecies)
    SET r.min_level = row.min_level,
        r.trigger_item_id = row.trigger_item_id
    """

    item_rows = [row for row in rows if row.get("trigger_item_id") is not None]
    item_query = """
    UNWIND $rows AS row
    MATCH (fromSpecies:Species {species_id: row.from_species_id})
    MATCH (item:Item {item_id: row.trigger_item_id})
    MERGE (fromSpecies)-[:EVOLUTION_REQUIRES]->(item)
    """

    run_batched(conn, evolution_query, rows, "Species EVOLVES_TO relationships")
    run_batched(conn, item_query, item_rows, "Species EVOLUTION_REQUIRES relationships")

def create_move_effect_relationships(conn: Neo4jConnection) -> None:
    """
    Move - TRIGGERS -> Effect 관계를 생성합니다.

    Source:
        move_effects.json  (graph 폴더)

    관계 속성:
        phase_id    : 효과가 발동하는 배틀 페이즈 ID
        ailment_id  : 상태이상 ID. "etc"는 -1로 정규화, null → None
        stat_ids    : 영향받는 스탯 이름 목록 (리스트), null → []
        chance      : 발동 확률(%). true → 100, null → None
        values      : 랭크/배율 변화량 목록 (리스트), null → []
        target      : 대상 문자열 (null 허용)
    """
    graph_dir = Path(__file__).resolve().parent
    move_effects_path = graph_dir / "move_effects.json"

    if not move_effects_path.exists():
        raise FileNotFoundError(f"move_effects.json not found: {move_effects_path}")

    with move_effects_path.open("r", encoding="utf-8") as f:
        raw_rows = json.load(f)

    rows = []
    for row in raw_rows:
        # chance: true → 100, 숫자 → 그대로, null → None
        chance_raw = row.get("chance")
        if chance_raw is True:
            chance = 100
        elif isinstance(chance_raw, (int, float)):
            chance = int(chance_raw)
        else:
            chance = None

        # ailment_id: "etc" → -1, 숫자 → 그대로, null → None
        ailment_raw = row.get("ailment_id")
        if ailment_raw == "etc":
            ailment_id = -1
        elif isinstance(ailment_raw, int):
            ailment_id = ailment_raw
        else:
            ailment_id = None

        # stat_id: 리스트 → 그대로, null → []
        stat_ids = row.get("stat_id") or []

        # value: 리스트 → 그대로, null → []
        values = row.get("value") or []

        rows.append({
            "move_id": row["move_id"],
            "effect_id": row["effect_id"],
            "phase_id": row.get("phase_id"),
            "ailment_id": ailment_id,
            "stat_ids": stat_ids,
            "chance": chance,
            "values": values,
            "target": row.get("target"),
        })

    query = """
    UNWIND $rows AS row
    MATCH (m:Move {move_id: row.move_id})
    MATCH (e:Effect {effect_id: row.effect_id})
    MERGE (m)-[r:TRIGGERS {phase_id: row.phase_id}]->(e)
    SET r.ailment_id  = row.ailment_id,
        r.stat_ids    = row.stat_ids,
        r.chance      = row.chance,
        r.values      = row.values,
        r.target      = row.target
    """
    run_batched(conn, query, rows, "Move TRIGGERS Effect relationships")

def create_ability_effect_relationships(conn: Neo4jConnection) -> None:
    """
    Ability - TRIGGERS -> Effect 관계를 생성합니다.

    Source:
        ability_effects.json  (graph 폴더)

    관계 속성:
        phase_id   : 효과가 발동하는 배틀 페이즈 ID
        ailment_id : 상태이상 ID (정수 or null)
        stat_id    : 영향받는 스탯 ID (정수 or null)
        chance     : 발동 확률 % (정수 or null)
        value      : 랭크/배율 변화량 (정수 or null)
        target     : 대상 문자열 ("self" / "opponent" / "all" / null)
    """
    graph_dir = Path(__file__).resolve().parent
    ability_effects_path = graph_dir / "ability_effects.json"

    if not ability_effects_path.exists():
        raise FileNotFoundError(f"ability_effects.json not found: {ability_effects_path}")

    with ability_effects_path.open("r", encoding="utf-8") as f:
        raw_rows = json.load(f)

    rows = [
        {
            "ability_id": row["ability_id"],
            "effect_id":  row["effect_id"],
            "phase_id":   row.get("phase_id"),
            "ailment_id": row.get("ailment_id"),
            "stat_id":    row.get("stat_id"),
            "chance":     row.get("chance"),
            "value":      row.get("value"),
            "target":     row.get("target"),
        }
        for row in raw_rows
    ]

    query = """
    UNWIND $rows AS row
    MATCH (a:Ability {ability_id: row.ability_id})
    MATCH (e:Effect {effect_id: row.effect_id})
    MERGE (a)-[r:TRIGGERS {phase_id: row.phase_id}]->(e)
    SET r.ailment_id = row.ailment_id,
        r.stat_id    = row.stat_id,
        r.chance     = row.chance,
        r.value      = row.value,
        r.target     = row.target
    """
    run_batched(conn, query, rows, "Ability TRIGGERS Effect relationships")

def create_item_effect_relationships(conn: Neo4jConnection) -> None:
    """
    Item - TRIGGERS -> Effect 관계를 생성합니다.

    Source:
        item_effects.json  (graph 폴더)

    관계 속성:
        phase_id   : 효과가 발동하는 배틀 페이즈 ID
        ailment_id : 상태이상 ID (정수 or null)
        stat_id    : 영향받는 스탯 ID (정수 or null)
        chance     : 발동 확률 % (정수 or null)
        value      : 변화량 (숫자 or null)
        target     : 대상 문자열 (null 허용)
    """
    graph_dir = Path(__file__).resolve().parent
    item_effects_path = graph_dir / "item_effects.json"

    if not item_effects_path.exists():
        raise FileNotFoundError(f"item_effects.json not found: {item_effects_path}")

    with item_effects_path.open("r", encoding="utf-8") as f:
        raw_rows = json.load(f)

    rows = [
        {
            "item_id":    row["item_id"],
            "effect_id":  row["effect_id"],
            "phase_id":   row.get("phase_id"),
            "ailment_id": row.get("ailment_id"),
            "stat_id":    row.get("stat_id"),
            "chance":     row.get("chance"),
            "value":      row.get("value"),
            "target":     row.get("target"),
        }
        for row in raw_rows
    ]

    query = """
    UNWIND $rows AS row
    MATCH (i:Item   {item_id:   row.item_id})
    MATCH (e:Effect {effect_id: row.effect_id})
    MERGE (i)-[r:TRIGGERS {phase_id: row.phase_id}]->(e)
    SET r.ailment_id = row.ailment_id,
        r.stat_id    = row.stat_id,
        r.chance     = row.chance,
        r.value      = row.value,
        r.target     = row.target
    """
    run_batched(conn, query, rows, "Item TRIGGERS Effect relationships")


def create_effect_phase_relationships(conn: Neo4jConnection) -> None:
    """
    Effect - APPLIES_AT -> Phase 관계를 생성합니다.

    Source:
        move_effects.json / ability_effects.json / item_effects.json 에서
        (effect_id, phase_id) 쌍을 수집합니다.

    설명:
        각 effect_id 가 어느 phase_id 에 발동할 수 있는지를 나타냅니다.
        중복 없이 유일한 (effect_id, phase_id) 쌍만 생성합니다.
    """
    graph_dir = Path(__file__).resolve().parent
    sources = ["move_effects.json", "ability_effects.json", "item_effects.json"]

    seen: set = set()
    rows: List[Dict[str, Any]] = []
    for filename in sources:
        path = graph_dir / filename
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for record in json.load(f):
                eid = record.get("effect_id")
                pid = record.get("phase_id")
                if eid is not None and pid is not None and (eid, pid) not in seen:
                    seen.add((eid, pid))
                    rows.append({"effect_id": eid, "phase_id": pid})

    query = """
    UNWIND $rows AS row
    MATCH (e:Effect {effect_id: row.effect_id})
    MATCH (p:Phase  {phase_id:  row.phase_id})
    MERGE (e)-[:APPLIES_AT]->(p)
    """
    run_batched(conn, query, rows, "Effect APPLIES_AT Phase relationships")


def create_effect_stat_relationships(conn: Neo4jConnection) -> None:
    """
    Effect - AFFECTS_STAT -> Stat 관계를 생성합니다.

    Source:
        move_effects.json  : stat_id 가 문자열 배열 (e.g. ["attack", "speed"])
        ability_effects.json : stat_id 가 정수 (Stat.stat_id)
        item_effects.json  : stat_id 가 정수 (Stat.stat_id)

    설명:
        move_effects 의 stat 이름은 Stat 노드의 name 속성으로 매칭하고,
        ability/item_effects 의 정수 stat_id 는 Stat.stat_id 로 매칭합니다.
        중복 없이 유일한 (effect_id, 식별자) 쌍만 생성합니다.
    """
    graph_dir = Path(__file__).resolve().parent

    seen_name: set = set()
    seen_id:   set = set()
    rows_by_name: List[Dict[str, Any]] = []
    rows_by_id:   List[Dict[str, Any]] = []

    # move_effects: stat_id 는 문자열 배열
    move_path = graph_dir / "move_effects.json"
    if move_path.exists():
        with move_path.open("r", encoding="utf-8") as f:
            for record in json.load(f):
                eid = record.get("effect_id")
                stat_names = record.get("stat_id") or []
                for sname in stat_names:
                    if eid is not None and (eid, sname) not in seen_name:
                        seen_name.add((eid, sname))
                        rows_by_name.append({"effect_id": eid, "stat_name": sname})

    # ability_effects / item_effects: stat_id 는 정수
    for filename in ["ability_effects.json", "item_effects.json"]:
        path = graph_dir / filename
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for record in json.load(f):
                eid = record.get("effect_id")
                sid = record.get("stat_id")
                if eid is not None and sid is not None and (eid, sid) not in seen_id:
                    seen_id.add((eid, sid))
                    rows_by_id.append({"effect_id": eid, "stat_id": sid})

    # stat 이름 기반 연결
    if rows_by_name:
        query_name = """
        UNWIND $rows AS row
        MATCH (e:Effect {effect_id: row.effect_id})
        MATCH (s:Stat   {name:      row.stat_name})
        MERGE (e)-[:AFFECTS_STAT]->(s)
        """
        run_batched(conn, query_name, rows_by_name, "Effect AFFECTS_STAT (by name)")

    # stat_id 기반 연결
    if rows_by_id:
        query_id = """
        UNWIND $rows AS row
        MATCH (e:Effect {effect_id: row.effect_id})
        MATCH (s:Stat   {stat_id:   row.stat_id})
        MERGE (e)-[:AFFECTS_STAT]->(s)
        """
        run_batched(conn, query_id, rows_by_id, "Effect AFFECTS_STAT (by id)")


def create_effect_status_condition_relationships(conn: Neo4jConnection) -> None:
    """
    Effect - TRIGGERS -> StatusCondition 관계를 생성합니다.

    Source:
        move_effects.json / ability_effects.json / item_effects.json 에서
        ailment_id 가 유효한 정수인 레코드를 수집합니다.

    설명:
        ailment_id == -1 ("etc" 정규화 값) 은 제외합니다.
        중복 없이 유일한 (effect_id, ailment_id) 쌍만 생성합니다.
    """
    graph_dir = Path(__file__).resolve().parent
    sources = ["move_effects.json", "ability_effects.json", "item_effects.json"]

    seen: set = set()
    rows: List[Dict[str, Any]] = []
    for filename in sources:
        path = graph_dir / filename
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for record in json.load(f):
                eid = record.get("effect_id")
                # ailment_id: move_effects 는 이미 -1 정규화됨, -1 제외
                aid_raw = record.get("ailment_id")
                if aid_raw == "etc":
                    aid_raw = -1
                if eid is None or not isinstance(aid_raw, int) or aid_raw == -1:
                    continue
                if (eid, aid_raw) not in seen:
                    seen.add((eid, aid_raw))
                    rows.append({"effect_id": eid, "ailment_id": aid_raw})

    query = """
    UNWIND $rows AS row
    MATCH (e:Effect          {effect_id:           row.effect_id})
    MATCH (s:StatusCondition {status_condition_id: row.ailment_id})
    MERGE (e)-[:TRIGGERS]->(s)
    """
    run_batched(conn, query, rows, "Effect TRIGGERS StatusCondition relationships")


def create_effect_type_relationships(conn: Neo4jConnection) -> None:
    """
    Effect - MODIFIES_TYPE -> Type 관계를 생성합니다.

    Source:
        effects.json (effect_type 이 move_immunity / move_absorb / type_modifier 인 Effect)
        types.json   (모든 Type 노드)

    설명:
        특정 기술 타입을 무효화하거나 흡수·변경하는 Effect 를
        모든 Type 노드와 MODIFIES_TYPE 으로 연결합니다.
        (어떤 타입에 작용하는지는 기술/특성 관계 속성에서 결정되므로,
         여기서는 Effect 가 타입을 수정할 수 있다는 가능성 관계를 생성합니다.)
    """
    target_types = {"move_immunity", "move_absorb", "type_modifier"}
    effects = load_json("effects.json")
    types   = load_json("types.json")

    type_effect_ids = [
        row["id"] for row in effects if row["effect_type"] in target_types
    ]
    if not type_effect_ids:
        print("Effect MODIFIES_TYPE: no matching effect_type found, skipped")
        return

    rows = [
        {"effect_id": eid, "type_id": t["id"]}
        for eid in type_effect_ids
        for t in types
    ]

    query = """
    UNWIND $rows AS row
    MATCH (e:Effect {effect_id: row.effect_id})
    MATCH (t:Type   {type_id:   row.type_id})
    MERGE (e)-[:MODIFIES_TYPE]->(t)
    """
    run_batched(conn, query, rows, "Effect MODIFIES_TYPE Type relationships")

def create_effect_field_relationships(conn: Neo4jConnection) -> None:
    """
    Effect - CHANGES_FIELD -> Field 관계를 생성합니다.

    Source:
        effects.json (effect_type == "terrain_change")
        fields.json

    설명:
        effect_type이 terrain_change인 Effect 노드를 모든 Field 노드와
        CHANGES_FIELD 관계로 연결합니다.
        (어떤 필드로 변화시킬지는 기술/특성 레벨 관계 속성에서 결정되므로,
         여기서는 Effect → Field 의 가능성 관계만 생성합니다.)
    """
    effects = load_json("effects.json")
    fields  = load_json("fields.json")

    terrain_effect_ids = [
        row["id"] for row in effects if row["effect_type"] == "terrain_change"
    ]
    if not terrain_effect_ids:
        print("Effect CHANGES_FIELD: terrain_change effect not found, skipped")
        return

    rows = [
        {"effect_id": eid, "field_id": field["id"]}
        for eid in terrain_effect_ids
        for field in fields
    ]

    query = """
    UNWIND $rows AS row
    MATCH (e:Effect {effect_id: row.effect_id})
    MATCH (f:Field  {field_id:  row.field_id})
    MERGE (e)-[:CHANGES_FIELD]->(f)
    """
    run_batched(conn, query, rows, "Effect CHANGES_FIELD relationships")


def create_effect_weather_relationships(conn: Neo4jConnection) -> None:
    """
    Effect - CHANGES_WEATHER -> Weather 관계를 생성합니다.

    Source:
        effects.json (effect_type == "weather_change")
        weathers.json

    설명:
        effect_type이 weather_change인 Effect 노드를 모든 Weather 노드와
        CHANGES_WEATHER 관계로 연결합니다.
    """
    effects  = load_json("effects.json")
    weathers = load_json("weathers.json")

    weather_effect_ids = [
        row["id"] for row in effects if row["effect_type"] == "weather_change"
    ]
    if not weather_effect_ids:
        print("Effect CHANGES_WEATHER: weather_change effect not found, skipped")
        return

    rows = [
        {"effect_id": eid, "weather_id": weather["id"]}
        for eid in weather_effect_ids
        for weather in weathers
    ]

    query = """
    UNWIND $rows AS row
    MATCH (e:Effect  {effect_id:  row.effect_id})
    MATCH (w:Weather {weather_id: row.weather_id})
    MERGE (e)-[:CHANGES_WEATHER]->(w)
    """
    run_batched(conn, query, rows, "Effect CHANGES_WEATHER relationships")


# ============================================
# 7. 파생 관계 생성 함수
# ============================================
def get_type_multiplier(
    attack_type_id: int,
    defender_type_ids: List[int],
    efficacy_map: Dict[tuple, float],
) -> float:
    """
    공격 타입이 특정 포켓몬에게 주는 최종 배율을 계산합니다.

    Args:
        attack_type_id: 공격하는 기술의 타입 ID입니다.
        defender_type_ids: 방어 포켓몬이 가진 타입 ID 목록입니다.
        efficacy_map: (공격 타입 ID, 방어 타입 ID) -> 배율 딕셔너리입니다.

    Returns:
        두 타입 배율을 모두 곱한 최종 multiplier입니다.
    """
    multiplier = 1.0
    for defender_type_id in defender_type_ids:
        # type_efficacy.json에 없는 조합은 기본 1.0배로 봅니다.
        multiplier *= efficacy_map.get((attack_type_id, defender_type_id), 1.0)
    return multiplier


def classify_defense_relation(multiplier: float) -> str:
    """
    multiplier 값을 관계 타입 이름으로 분류합니다.

    Returns:
        VERY_WEAK_AGAINST, WEAK_AGAINST, NORMAL_VULNERABILITY_AGAINST,
        RESISTANT_TO, VERY_RESISTANT_TO, IMMUNE_TO 중 하나를 반환합니다.
    """
    if multiplier == 0.0:
        return "IMMUNE_TO"
    if multiplier <= 0.25:
        return "VERY_RESISTANT_TO"
    if multiplier < 1.0:
        return "RESISTANT_TO"
    if multiplier >= 4.0:
        return "VERY_WEAK_AGAINST"
    if multiplier > 1.0:
        return "WEAK_AGAINST"
    return "NORMAL_VULNERABILITY_AGAINST"


def build_pokemon_defense_rows() -> List[Dict[str, Any]]:
    """
    Pokemon - AGAINST -> Type 파생 관계에 사용할 rows를 만듭니다.

    Source:
        pokemon_types.json
        types.json
        type_efficacy.json

    설명:
        각 포켓몬이 18개 공격 타입에 대해 몇 배 데미지를 받는지 계산합니다.
    """
    type_rows = load_json("types.json")
    pokemon_type_rows = load_json("pokemon_types.json")
    efficacy_rows = load_json("type_efficacy.json")

    all_type_ids = [row["id"] for row in type_rows]

    # efficacy_map은 공격 타입과 방어 타입 조합의 배율을 빠르게 찾기 위한 딕셔너리입니다.
    efficacy_map = {
        (row["damage_type_id"], row["target_type_id"]): row["damage_factor"]
        for row in efficacy_rows
    }

    # pokemon_types_by_id는 포켓몬별 보유 타입 목록입니다.
    pokemon_types_by_id: Dict[int, List[int]] = {}
    for row in pokemon_type_rows:
        pokemon_types_by_id.setdefault(row["pokemon_id"], []).append(row["type_id"])

    rows = []
    for pokemon_id, defender_type_ids in pokemon_types_by_id.items():
        for attack_type_id in all_type_ids:
            multiplier = get_type_multiplier(attack_type_id, defender_type_ids, efficacy_map)
            rows.append(
                {
                    "pokemon_id": pokemon_id,
                    "type_id": attack_type_id,
                    "multiplier": multiplier,
                    "relation_type": classify_defense_relation(multiplier),
                }
            )

    return rows


def create_against_relationships(conn: Neo4jConnection, rows: List[Dict[str, Any]]) -> None:
    """
    Pokemon - AGAINST -> Type 관계를 생성합니다.

    설명:
        multiplier 속성 하나로 모든 방어 상성을 표현합니다.
        팀 약점 점수 계산에서 가장 기본이 되는 관계입니다.
    """
    query = """
    UNWIND $rows AS row
    MATCH (p:Pokemon {pokemon_id: row.pokemon_id})
    MATCH (t:Type {type_id: row.type_id})
    MERGE (p)-[r:AGAINST]->(t)
    SET r.multiplier = row.multiplier
    """
    run_batched(conn, query, rows, "Pokemon AGAINST relationships")


def create_named_defense_relationships(conn: Neo4jConnection, rows: List[Dict[str, Any]]) -> None:
    """
    multiplier별 편의 관계를 생성합니다.

    생성 관계:
        VERY_WEAK_AGAINST
        WEAK_AGAINST
        NORMAL_VULNERABILITY_AGAINST
        RESISTANT_TO
        VERY_RESISTANT_TO
        IMMUNE_TO

    설명:
        Cypher에서는 관계 타입 이름을 파라미터로 넣을 수 없기 때문에,
        relation_type별로 rows를 나누어 각각 실행합니다.
    """
    relation_types = [
        "VERY_WEAK_AGAINST",
        "WEAK_AGAINST",
        "NORMAL_VULNERABILITY_AGAINST",
        "RESISTANT_TO",
        "VERY_RESISTANT_TO",
        "IMMUNE_TO",
    ]

    for relation_type in relation_types:
        relation_rows = [row for row in rows if row["relation_type"] == relation_type]
        query = f"""
        UNWIND $rows AS row
        MATCH (p:Pokemon {{pokemon_id: row.pokemon_id}})
        MATCH (t:Type {{type_id: row.type_id}})
        MERGE (p)-[r:{relation_type}]->(t)
        SET r.multiplier = row.multiplier
        """
        run_batched(conn, query, relation_rows, f"Pokemon {relation_type} relationships")


def create_pokemon_defense_relationships(conn: Neo4jConnection) -> None:
    """
    포켓몬별 방어 상성 파생 관계를 생성합니다.

    생성 관계:
        Pokemon - AGAINST -> Type
        Pokemon - WEAK_AGAINST -> Type
        Pokemon - RESISTANT_TO -> Type
        Pokemon - IMMUNE_TO -> Type
        기타 multiplier별 편의 관계
    """
    rows = build_pokemon_defense_rows()
    create_against_relationships(conn, rows)
    create_named_defense_relationships(conn, rows)


# ============================================
# 8. 전체 실행 함수
# ============================================
def create_all_nodes(conn: Neo4jConnection) -> None:
    """Graph DB에 필요한 기본 노드를 모두 생성합니다."""
    print("\n--- Creating nodes ---")
    create_type_nodes(conn)
    create_pokemon_nodes(conn)
    create_move_nodes(conn)
    create_ability_nodes(conn)
    create_item_nodes(conn)
    create_nature_nodes(conn)
    create_species_and_generation_nodes(conn)
    create_effect_nodes(conn)
    create_stat_nodes(conn)
    create_status_condition_nodes(conn)
    create_phase_nodes(conn)
    create_weather_nodes(conn)
    create_field_effect_nodes(conn)

def create_all_relationships(conn: Neo4jConnection) -> None:
    """Graph DB에 필요한 기본 관계와 파생 관계를 모두 생성합니다."""
    print("\n--- Creating relationships ---")
    create_pokemon_has_type_relationships(conn)
    create_move_has_type_relationships(conn)
    create_pokemon_can_know_relationships(conn)
    create_pokemon_can_have_relationships(conn)
    create_type_efficacy_relationships(conn)
    create_species_relationships(conn)
    create_evolution_relationships(conn)
    create_pokemon_defense_relationships(conn)
    create_move_effect_relationships(conn)
    create_ability_effect_relationships(conn)
    create_item_effect_relationships(conn)
    create_effect_phase_relationships(conn)
    create_effect_stat_relationships(conn)
    create_effect_status_condition_relationships(conn)
    create_effect_type_relationships(conn)
    create_effect_field_relationships(conn)
    create_effect_weather_relationships(conn)

def print_graph_summary(conn: Neo4jConnection) -> None:
    """
    적재가 끝난 뒤 노드와 관계 개수를 출력합니다.

    목적:
        Neo4j에 데이터가 어느 정도 들어갔는지 빠르게 확인합니다.
    """
    summary_query = """
    MATCH (n)
    RETURN labels(n)[0] AS label, count(n) AS count
    ORDER BY label
    """
    relationship_query = """
    MATCH ()-[r]->()
    RETURN type(r) AS type, count(r) AS count
    ORDER BY type
    """

    print("\n--- Node summary ---")
    for record in conn.execute_query(summary_query):
        print(f"{record['label']}: {record['count']}")

    print("\n--- Relationship summary ---")
    for record in conn.execute_query(relationship_query):
        print(f"{record['type']}: {record['count']}")


def get_neo4j_connection_from_env() -> Neo4jConnection:
    """
    .env 환경변수에서 Neo4j 연결 정보를 읽고 연결 객체를 만듭니다.

    필요한 환경변수:
        NEO4J_URI
        NEO4J_USER
        NEO4J_PASSWORD

    기본값:
        NEO4J_URI=bolt://localhost:7687
        NEO4J_USER=neo4j
        NEO4J_PASSWORD=test1234
    """
    uri = os.getenv("GRAPH_DB_URI", "bolt://localhost:7687")
    user = os.getenv("GRAPH_DB_USER", "neo4j")
    password = os.getenv("GRAPH_DB_PASSWORD", "test1234")

    return Neo4jConnection(uri=uri, user=user, password=password)


def main() -> None:
    """
    graph_loader.py의 메인 실행 함수입니다.

    실행 순서:
        1. Neo4j 연결
        2. 필요하면 기존 그래프 삭제
        3. constraints.cypher 실행
        4. 노드 생성
        5. 관계 생성
        6. 요약 출력
    """
    parser = argparse.ArgumentParser(description="Load Pokemon processed JSON into Neo4j")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all existing Neo4j nodes and relationships before loading",
    )
    args = parser.parse_args()

    conn = get_neo4j_connection_from_env()

    try:
        print("Neo4j graph loading started")
        print(f"Processed data dir: {PROCESSED_DATA_DIR}")

        if args.reset:
            reset_graph(conn)

        apply_constraints(conn)
        create_all_nodes(conn)
        create_all_relationships(conn)
        print_graph_summary(conn)

        print("\nNeo4j graph loading complete")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
