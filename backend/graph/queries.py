"""
Cypher query collection

목적:
    팀 추천과 배틀 API에서 사용할 Cypher 쿼리를 한 곳에 모아둡니다.

주의:
    이 파일은 쿼리 문자열만 관리합니다.
    실제 쿼리 실행은 neo4j_client.py의 Neo4jClient가 담당합니다.
"""

# ============================================
# 1. Graph 상태 확인용 쿼리
# ============================================
# Neo4j에 노드가 라벨별로 몇 개 들어갔는지 확인합니다.
NODE_COUNT_BY_LABEL = """
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS count
ORDER BY label
"""

# Neo4j에 관계가 타입별로 몇 개 들어갔는지 확인합니다.
RELATIONSHIP_COUNT_BY_TYPE = """
MATCH ()-[r]->()
RETURN type(r) AS type, count(r) AS count
ORDER BY type
"""


# ============================================
# 2. 팀 추천에서 바로 사용할 수 있는 쿼리
# ============================================
# 선택한 포켓몬 5마리의 방어 약점을 타입별로 합산합니다.
# score가 높을수록 팀 전체가 해당 공격 타입에 약하다는 의미입니다.
TEAM_WEAKNESS_SUMMARY = """
MATCH (p:Pokemon)-[a:AGAINST]->(attackType:Type)
WHERE p.pokemon_id IN $selected_pokemon_ids
RETURN attackType.type_id AS type_id,
       attackType.name AS type_name,
       sum(a.multiplier) AS weakness_score,
       avg(a.multiplier) AS average_multiplier
ORDER BY weakness_score DESC
"""

# 팀의 약점 타입 목록을 기준으로, 해당 타입에 저항하거나 무효인 후보를 찾습니다.
# candidate.is_default = true 조건은 메가진화/특수 폼을 추천 후보에서 제외하기 위한 조건입니다.
DEFENSIVE_CANDIDATES_BY_WEAK_TYPES = """
MATCH (candidate:Pokemon)-[r:RESISTANT_TO|VERY_RESISTANT_TO|IMMUNE_TO]->(weakType:Type)
WHERE weakType.type_id IN $weak_type_ids
AND candidate.is_default = true
AND NOT candidate.pokemon_id IN $selected_pokemon_ids
RETURN candidate.pokemon_id AS pokemon_id,
       candidate.name AS name,
       candidate.base_total AS base_total,
       collect(DISTINCT {
           type_id: weakType.type_id,
           type_name: weakType.name,
           relation: type(r),
           multiplier: r.multiplier
       }) AS defensive_covers
ORDER BY base_total DESC
LIMIT $limit
"""

# 후보 포켓몬이 배울 수 있는 기술 타입을 조회합니다.
# 팀 공격 커버리지 점수 계산에서 사용합니다.
CANDIDATE_MOVE_TYPES = """
MATCH (candidate:Pokemon)-[:CAN_KNOW]->(move:Move)-[:HAS_TYPE]->(moveType:Type)
WHERE candidate.pokemon_id IN $candidate_pokemon_ids
RETURN candidate.pokemon_id AS pokemon_id,
       collect(DISTINCT {
           type_id: moveType.type_id,
           type_name: moveType.name
       }) AS move_types
"""

# 선택한 팀의 보유 타입 분포를 조회합니다.
# 후보 타입이 팀과 너무 겹치는지 확인할 때 사용합니다.
TEAM_TYPE_DISTRIBUTION = """
MATCH (p:Pokemon)-[:HAS_TYPE]->(pokemonType:Type)
WHERE p.pokemon_id IN $selected_pokemon_ids
RETURN pokemonType.type_id AS type_id,
       pokemonType.name AS type_name,
       count(*) AS count
ORDER BY count DESC
"""

# 후보 포켓몬의 타입을 조회합니다.
# 타입 중복 감점 계산에서 사용합니다.
CANDIDATE_TYPES = """
MATCH (candidate:Pokemon)-[:HAS_TYPE]->(pokemonType:Type)
WHERE candidate.pokemon_id IN $candidate_pokemon_ids
RETURN candidate.pokemon_id AS pokemon_id,
       collect(DISTINCT {
           type_id: pokemonType.type_id,
           type_name: pokemonType.name
       }) AS pokemon_types
"""


# ============================================
# 3. 배틀 기능에서 사용할 수 있는 기본 쿼리
# ============================================
# 특정 포켓몬이 특정 공격 타입에 몇 배 데미지를 받는지 조회합니다.
BATTLE_DEFENSE_MULTIPLIER = """
MATCH (defender:Pokemon)-[a:AGAINST]->(attackType:Type)
WHERE defender.pokemon_id = $defender_pokemon_id
AND attackType.type_id = $attack_type_id
RETURN defender.pokemon_id AS defender_pokemon_id,
       defender.name AS defender_name,
       attackType.type_id AS attack_type_id,
       attackType.name AS attack_type_name,
       a.multiplier AS multiplier
"""

# 특정 포켓몬이 배울 수 있는 기술 목록을 조회합니다.
# 초기 배틀에서는 실제 선택 기술이 없으므로 CAN_KNOW를 후보 기술로 사용합니다.
POKEMON_AVAILABLE_MOVES = """
MATCH (p:Pokemon)-[learn:CAN_KNOW]->(move:Move)-[:HAS_TYPE]->(moveType:Type)
WHERE p.pokemon_id = $pokemon_id
RETURN move.move_id AS move_id,
       move.name AS move_name,
       move.power AS power,
       move.accuracy AS accuracy,
       move.damage_class AS damage_class,
       moveType.type_id AS type_id,
       moveType.name AS type_name,
       learn.learn_method AS learn_method,
       learn.level_learned_at AS level_learned_at
ORDER BY move.power DESC
"""

# 특정 포켓몬이 가질 수 있는 특성 목록을 조회합니다.
POKEMON_AVAILABLE_ABILITIES = """
MATCH (p:Pokemon)-[canHave:CAN_HAVE]->(ability:Ability)
WHERE p.pokemon_id = $pokemon_id
RETURN ability.ability_id AS ability_id,
       ability.name AS ability_name,
       ability.effect_text AS effect_text,
       canHave.is_hidden AS is_hidden,
       canHave.slot AS slot
ORDER BY canHave.slot
"""

