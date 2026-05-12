import streamlit as st
from .pokemon import PokemonDB

@st.cache_data
def load_type_efficacy_matrix() -> dict:
    """
    Neo4j에서 타입 상성 매트릭스를 불러와 딕셔너리로 반환합니다.
    형태: {(attack_type_id, defend_type_id): damage_factor}
    """
    db = PokemonDB()
    if not db:
        return {}
        
    query = """
    MATCH (t1:Type)-[r:ATTACK_EFFECTIVE]->(t2:Type)
    RETURN t1.type_id as atk, t2.type_id as def, r.damage_factor as factor
    """
    try:
        with db.driver.session() as session:
            result = session.run(query)
            matrix = {}
            for record in result:
                matrix[(record["atk"], record["def"])] = float(record["factor"])
            return matrix
    except Exception as e:
        print(f"Error loading type efficacy: {e}")
        return {}

def calculate_type_multiplier(attack_type_id: int, defender_type_ids: list[int]) -> float:
    """
    공격 기술의 타입과 방어 포켓몬의 타입(들)을 기반으로 상성 배율을 계산합니다.
    """
    if not attack_type_id or not defender_type_ids:
        return 1.0
        
    matrix = load_type_efficacy_matrix()
    if not matrix:
        return 1.0
        
    multiplier = 1.0
    for def_type in defender_type_ids:
        # 데이터베이스에 관계가 명시되지 않은 경우 기본 배율은 1.0
        factor = matrix.get((attack_type_id, def_type), 1.0)
        multiplier *= factor
        
    return multiplier

def calculate_stab_multiplier(attack_type_id: int, attacker_type_ids: list[int]) -> float:
    """
    자속 보정(Same Type Attack Bonus, STAB)을 계산합니다.
    공격 포켓몬의 타입과 기술의 타입이 일치하면 1.5배, 아니면 1.0배
    """
    if not attack_type_id or not attacker_type_ids:
        return 1.0
        
    if attack_type_id in attacker_type_ids:
        return 1.5
    return 1.0
