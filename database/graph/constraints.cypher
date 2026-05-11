// Pokemon Graph DB constraints and indexes
// 목적: Neo4j에 같은 노드가 중복 생성되지 않도록 고유 ID 규칙을 먼저 만든다.
// 사용 위치: graph_loader.py에서 데이터 적재 전에 이 파일을 실행한다.

// ============================================
// 1. Unique constraints
// ============================================
// CONSTRAINT는 특정 라벨의 특정 속성이 중복되지 않도록 보장한다.
// graph_loader.py에서 MERGE를 사용할 때 이 규칙이 있어야 중복 노드 생성을 안정적으로 막을 수 있다.

// Pokemon 노드의 고유 ID
// pokemon_id는 PokeAPI 기준 포켓몬 ID를 의미한다.
CREATE CONSTRAINT pokemon_id IF NOT EXISTS
FOR (p:Pokemon)
REQUIRE p.pokemon_id IS UNIQUE;

// Type 노드의 고유 ID
// type_id는 PokeAPI 기준 타입 ID를 의미한다.
CREATE CONSTRAINT type_id IF NOT EXISTS
FOR (t:Type)
REQUIRE t.type_id IS UNIQUE;

// Move 노드의 고유 ID
// move_id는 PokeAPI 기준 기술 ID를 의미한다.
CREATE CONSTRAINT move_id IF NOT EXISTS
FOR (m:Move)
REQUIRE m.move_id IS UNIQUE;

// Ability 노드의 고유 ID
// ability_id는 PokeAPI 기준 특성 ID를 의미한다.
CREATE CONSTRAINT ability_id IF NOT EXISTS
FOR (a:Ability)
REQUIRE a.ability_id IS UNIQUE;

// Species 노드의 고유 ID
// species_id는 PokeAPI 기준 species ID를 의미한다.
CREATE CONSTRAINT species_id IF NOT EXISTS
FOR (s:Species)
REQUIRE s.species_id IS UNIQUE;

// Item 노드의 고유 ID
// item_id는 PokeAPI 기준 아이템 ID를 의미한다.
CREATE CONSTRAINT item_id IF NOT EXISTS
FOR (i:Item)
REQUIRE i.item_id IS UNIQUE;

// Nature 노드의 고유 ID
// nature_id는 PokeAPI 기준 성격 ID를 의미한다.
CREATE CONSTRAINT nature_id IF NOT EXISTS
FOR (n:Nature)
REQUIRE n.nature_id IS UNIQUE;

// Generation 노드의 고유 ID
// generation_id는 포켓몬 등장 세대 번호를 의미한다.
CREATE CONSTRAINT generation_id IF NOT EXISTS
FOR (g:Generation)
REQUIRE g.generation_id IS UNIQUE;

// Team 노드의 고유 ID
// team_id는 사용자가 저장한 팀 하나를 구분하는 ID를 의미한다.
CREATE CONSTRAINT team_id IF NOT EXISTS
FOR (team:Team)
REQUIRE team.team_id IS UNIQUE;

// TeamMember 노드의 고유 ID
// team_member_id는 팀 안에 들어간 특정 포켓몬 인스턴스 하나를 구분하는 ID를 의미한다.
CREATE CONSTRAINT team_member_id IF NOT EXISTS
FOR (tm:TeamMember)
REQUIRE tm.team_member_id IS UNIQUE;

// ============================================
// 2. Search indexes
// ============================================
// INDEX는 검색 속도를 높이기 위한 규칙이다.
// name은 unique하지 않을 수 있으므로 CONSTRAINT가 아니라 INDEX로 만든다.

// 포켓몬 이름 검색용 인덱스
CREATE INDEX pokemon_name IF NOT EXISTS
FOR (p:Pokemon)
ON (p.name);

// 타입 이름 검색용 인덱스
CREATE INDEX type_name IF NOT EXISTS
FOR (t:Type)
ON (t.name);

// 기술 이름 검색용 인덱스
CREATE INDEX move_name IF NOT EXISTS
FOR (m:Move)
ON (m.name);

// 특성 이름 검색용 인덱스
CREATE INDEX ability_name IF NOT EXISTS
FOR (a:Ability)
ON (a.name);

// 아이템 이름 검색용 인덱스
CREATE INDEX item_name IF NOT EXISTS
FOR (i:Item)
ON (i.name);

// 성격 이름 검색용 인덱스
CREATE INDEX nature_name IF NOT EXISTS
FOR (n:Nature)
ON (n.name);

// 팀 이름 검색용 인덱스
CREATE INDEX team_name IF NOT EXISTS
FOR (team:Team)
ON (team.name);

// ============================================
// 3. Optional helper indexes
// ============================================
// 아래 인덱스들은 추천/배틀 로직에서 자주 필터링할 수 있는 속성이다.
// 필수는 아니지만 데이터가 많아질 때 조회 성능을 안정적으로 만들기 위해 추가한다.

// 기본 폼 여부로 필터링할 때 사용한다.
// 팀 추천 후보에서 메가진화/특수 폼을 제외할 때 p.is_default = true 조건을 자주 사용할 수 있다.
CREATE INDEX pokemon_is_default IF NOT EXISTS
FOR (p:Pokemon)
ON (p.is_default);

// 능력치 총합으로 후보를 정렬할 때 사용한다.
// 추천 후보를 base_total 기준으로 정렬하거나 제한할 때 도움이 된다.
CREATE INDEX pokemon_base_total IF NOT EXISTS
FOR (p:Pokemon)
ON (p.base_total);

// 기술 분류로 필터링할 때 사용한다.
// 배틀 계산에서 physical, special, status 기술을 구분할 때 도움이 된다.
CREATE INDEX move_damage_class IF NOT EXISTS
FOR (m:Move)
ON (m.damage_class);


// Additional constraints for new battle elements
CREATE CONSTRAINT effect_id IF NOT EXISTS FOR (e:Effect) REQUIRE e.effect_id IS UNIQUE;
CREATE CONSTRAINT stat_id IF NOT EXISTS FOR (s:Stat) REQUIRE s.stat_id IS UNIQUE;
CREATE CONSTRAINT status_condition_id IF NOT EXISTS FOR (sc:StatusCondition) REQUIRE sc.status_condition_id IS UNIQUE;
CREATE CONSTRAINT phase_id IF NOT EXISTS FOR (p:Phase) REQUIRE p.phase_id IS UNIQUE;
CREATE CONSTRAINT weather_id IF NOT EXISTS FOR (w:Weather) REQUIRE w.weather_id IS UNIQUE;
CREATE CONSTRAINT field_id IF NOT EXISTS FOR (f:FieldEffect) REQUIRE f.field_id IS UNIQUE;
