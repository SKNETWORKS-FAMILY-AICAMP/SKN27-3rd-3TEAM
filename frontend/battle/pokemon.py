import os
import json
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

class PokemonDB:
    """
    Neo4j 포켓몬 데이터 접근을 위한 기반 클래스입니다.
    기술 조회 방식은 _get_move_query()를 오버라이드하여 서브클래스에서 결정합니다.
    
    기본 동작(PokemonDB 직접 사용)은 PlayerPokemonDB와 동일하게
    'level-up' 방식으로 배우는 기술만 조회합니다.
    """
    """Neo4j Database connection for Pokemon data."""
    
    def __init__(self):
        # Read credentials from .env
        auth = os.environ.get("NEO4J_AUTH", "neo4j/test1234").split("/")
        user, password = auth[0], auth[1]

        # 환경변수가 있으면 우선 사용, 없으면 Docker(neo4j)와 로컬(localhost) 순차 확인
        uri = os.getenv("GRAPH_DB_URI")
        if not uri:
            is_docker = os.path.exists('/.dockerenv')
            uri = "bolt://neo4j:7687" if is_docker else "bolt://localhost:7687"

        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # 연결성 확인 (실제 쿼리 전 확인)
            self.driver.verify_connectivity()
        except Exception as e:
            # 연결 실패 시 에러 메시지 출력 후 다시 시도할 수 있도록 처리
            print(f"Neo4j 연결 실패 ({uri}): {e}")
            raise e

    def close(self):
        """Close the database driver."""
        self.driver.close()

    def _get_move_query(self) -> str:
        """
        기술 조회 Cypher 쿼리를 반환합니다.
        서브클래스에서 오버라이드하여 조회 범위를 변경할 수 있습니다.
        기본 동작은 PlayerPokemonDB와 동일하게 'level-up' 기술만 조회합니다.
        """
        return """
        MATCH (p:Pokemon {pokemon_id: $id})-[r:CAN_KNOW {learn_method: 'level-up'}]->(m:Move)
        RETURN DISTINCT m.name as name, m.move_id as id, m.type_id as type_id,
               m.power as power, m.accuracy as accuracy, m.damage_class as damage_class,
               m.effect_text as effect_text, m.target as target,
               m.category as category, m.stat_chance as stat_chance,
               m.stat_changes as stat_changes, m.ailment as ailment,
               m.ailment_chance as ailment_chance, m.drain as drain,
               m.healing as healing, m.priority as priority,
               m.flinch_chance as flinch_chance, m.crit_rate as crit_rate
        """

    def get_pokemon_data(self, pokemon_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch Pokemon data including stats, types, and moves from Neo4j.
        기술 조회 쿼리는 _get_move_query()를 통해 결정됩니다.
        """
        with self.driver.session() as session:
            # 1. Fetch Basic Pokemon Data and Stats
            pokemon_query = """
            MATCH (p:Pokemon {pokemon_id: $id})
            RETURN p
            """
            result = session.run(pokemon_query, {"id": pokemon_id})
            record = result.single()
            if not record:
                return None
            
            pokemon_info = dict(record["p"])
            
            # 2. Fetch Types
            type_query = """
            MATCH (p:Pokemon {pokemon_id: $id})-[:HAS_TYPE]->(t:Type)
            RETURN t.type_id as id, t.name as name
            """
            types_result = session.run(type_query, {"id": pokemon_id})
            types = [{"id": r["id"], "name": r["name"]} for r in types_result]
            
            # 3. Fetch Moves (서브클래스에서 정의된 쿼리 사용)
            moves_result = session.run(self._get_move_query(), {"id": pokemon_id})

            moves = []
            seen_names = set()
            for r in moves_result:
                move_dict = dict(r)
                
                # Parse JSON fields
                for field in ["target", "stat_changes"]:
                    if move_dict.get(field):
                        try:
                            move_dict[field] = json.loads(move_dict[field])
                        except (json.JSONDecodeError, TypeError):
                            pass
                
                # Filter by target and remove duplicate names
                if move_dict.get("target") in ["user", "selected-pokemon"]:
                    if move_dict["name"] not in seen_names:
                        seen_names.add(move_dict["name"])
                        moves.append(move_dict)
            
            return {
                "id": pokemon_id,
                "name": pokemon_info.get("name"),
                "image_url": pokemon_info.get("image_url"),
                "types": [t["id"] for t in types],
                "type_names": [t["name"] for t in types],
                "stats": {
                    "hp": pokemon_info.get("hp", 80),
                    "attack": pokemon_info.get("attack", 80),
                    "defense": pokemon_info.get("defense", 80),
                    "sp_attack": pokemon_info.get("sp_attack", 80),
                    "sp_defense": pokemon_info.get("sp_defense", 80),
                    "speed": pokemon_info.get("speed", 80)
                },
                "moves": moves # [솔라빔_딕셔너리: {name: 솔라빔, }]
            }
            
    def get_type_efficacy(self) -> Dict[tuple, float]:
        """Fetch type effectiveness (damage factors) between all types."""
        query = """
        MATCH (t1:Type)-[r:ATTACK_EFFECTIVE]->(t2:Type)
        RETURN t1.type_id as attacker_id, t2.type_id as defender_id, r.damage_factor as factor
        """
        with self.driver.session() as session:
            result = session.run(query)
            efficacy = {}
            for record in result:
                efficacy[(record["attacker_id"], record["defender_id"])] = float(record["factor"])
            return efficacy


class PlayerPokemonDB(PokemonDB):
    """
    플레이어 포켓몬 전용 DB 클래스.
    'level-up' 방식으로만 배울 수 있는 기술만 조회합니다.
    팀 빌딩 화면에서 선택 가능한 기술 목록을 제한하는 데 사용됩니다.
    """
    def _get_move_query(self) -> str:
        return """
        MATCH (p:Pokemon {pokemon_id: $id})-[r:CAN_KNOW {learn_method: 'level-up'}]->(m:Move)
        RETURN DISTINCT m.name as name, m.move_id as id, m.type_id as type_id,
               m.power as power, m.accuracy as accuracy, m.damage_class as damage_class,
               m.effect_text as effect_text, m.target as target,
               m.category as category, m.stat_chance as stat_chance,
               m.stat_changes as stat_changes, m.ailment as ailment,
               m.ailment_chance as ailment_chance, m.drain as drain,
               m.healing as healing, m.priority as priority,
               m.flinch_chance as flinch_chance, m.crit_rate as crit_rate
        """


class BotPokemonDB(PokemonDB):
    """
    봇 포켓몬 전용 DB 클래스.
    learn_method 제한 없이 포켓몬이 배울 수 있는 모든 기술을 조회합니다.
    관장 봇의 포켓몬이 더 다양한 기술을 사용할 수 있도록 합니다.
    """
    def _get_move_query(self) -> str:
        return """
        MATCH (p:Pokemon {pokemon_id: $id})-[r:CAN_KNOW]->(m:Move)
        RETURN DISTINCT m.name as name, m.move_id as id, m.type_id as type_id,
               m.power as power, m.accuracy as accuracy, m.damage_class as damage_class,
               m.effect_text as effect_text, m.target as target,
               m.category as category, m.stat_chance as stat_chance,
               m.stat_changes as stat_changes, m.ailment as ailment,
               m.ailment_chance as ailment_chance, m.drain as drain,
               m.healing as healing, m.priority as priority,
               m.flinch_chance as flinch_chance, m.crit_rate as crit_rate
        """


    def get_all_pokemon_names(self) -> List[Dict[str, Any]]:
        """Fetch list of all Pokemon IDs and names for selection."""
        query = """
        MATCH (p:Pokemon)
        WHERE p.is_default = true
        RETURN p.pokemon_id as id, p.name as name
        ORDER BY p.pokemon_id
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

# Streamlit integration for efficient database usage
if "streamlit" in globals() or "st" in globals() or os.getenv("STREAMLIT_SERVER_PORT"):
    import streamlit as st
    
    @st.cache_resource
    def get_db_connection():
        """Returns a cached Neo4j connection."""
        return PokemonDB()