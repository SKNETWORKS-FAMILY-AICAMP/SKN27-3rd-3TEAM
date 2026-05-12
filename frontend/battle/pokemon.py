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

    def get_pokemon_data(self, pokemon_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch Pokemon data including stats, types, and moves from Neo4j.
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
            
            # 3. Fetch Moves
            move_query = """
            MATCH (p:Pokemon {pokemon_id: $id})-[r:CAN_KNOW]->(m:Move)
            RETURN DISTINCT m.name as name, m.move_id as id, m.type_id as type_id, 
                   m.power as power, m.accuracy as accuracy, m.damage_class as damage_class,
                   m.effect_text as effect_text, m.target as target,
                   m.category as category, m.stat_chance as stat_chance, 
                   m.stat_changes as stat_changes, m.ailment as ailment, 
                   m.ailment_chance as ailment_chance, m.drain as drain, 
                   m.healing as healing, m.priority as priority
            """
            moves_result = session.run(move_query, {"id": pokemon_id})

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

# Streamlit integration for efficient database usage
if "streamlit" in globals() or "st" in globals() or os.getenv("STREAMLIT_SERVER_PORT"):
    import streamlit as st
    
    @st.cache_resource
    def get_db_connection():
        """Returns a cached Neo4j connection."""
        return PokemonDB()

# Example usage/Test code (Optional)
if __name__ == "__main__":
    db = PokemonDB()
    # Test with Pikachu (ID 25)
    data = db.get_pokemon_data(25)
    if data:
        print(f"Fetched: {data['name']}")
        print(f"Stats: {data['stats']}")
        print(f"Moves count: {len(data['moves'])}")
    
    efficacy = db.get_type_efficacy()
    print(f"Efficacy data points: {len(efficacy)}")
    
    db.close()
