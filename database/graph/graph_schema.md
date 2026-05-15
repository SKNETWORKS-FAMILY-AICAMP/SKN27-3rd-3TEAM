# Pokemon Graph DB 스키마 문서

이 문서는 현재 `database/graph/graph_loader.py`가 Neo4j에 적재하는 실제 그래프 구조를 기준으로 정리한 문서입니다.

초기 초안과 달리 현재 그래프는 `Species`, `Nature`, `Team`, `TeamMember` 노드를 만들지 않습니다. 대신 포켓몬 정적 지식, 타입 상성, 기술/특성/아이템 효과, 배틀 페이즈, 날씨, 필드 효과를 중심으로 구성합니다.

## 현재 적재 요약

현재 로컬 Neo4j 기준 적재 개수는 다음과 같습니다.

### 노드

| Label | Count | 설명 |
| --- | ---: | --- |
| `Pokemon` | 1,338 | 포켓몬 및 폼 단위 기본 정보 |
| `Move` | 919 | 기술 정보 |
| `Ability` | 307 | 특성 정보 |
| `Item` | 2,176 | 아이템 정보 |
| `Type` | 18 | 포켓몬/기술 타입 |
| `Generation` | 9 | 등장 세대 |
| `Effect` | 12 | 기술/특성/아이템이 발생시키는 추상 효과 |
| `Stat` | 9 | 능력치 및 명중/회피 계열 스탯 |
| `Ailment` | 18 | 상태 이상 |
| `Phase` | 11 | 배틀 처리 단계 |
| `Weather` | 4 | 날씨 |
| `Field` | 8 | 필드/룸/중력 효과 |

### 관계

| Relationship | Count | 방향 |
| --- | ---: | --- |
| `HAS_TYPE` | 3,012 | `Pokemon -> Type`, `Move -> Type` |
| `CAN_KNOW` | 141,298 | `Pokemon -> Move` |
| `CAN_HAVE` | 2,895 | `Pokemon -> Ability` |
| `ATTACK_EFFECTIVE` | 120 | `Type -> Type` |
| `FROM` | 1,025 | `Pokemon -> Generation` |
| `EVOLVES_TO` | 적재 시 계산 | `Pokemon -> Pokemon` |
| `AGAINST` | 24,084 | `Type -> Pokemon` |
| `VERY_WEAK_AGAINST` | 302 | `Type -> Pokemon` |
| `WEAK_AGAINST` | 4,096 | `Type -> Pokemon` |
| `NORMAL_VULNERABILITY_AGAINST` | 13,450 | `Type -> Pokemon` |
| `RESISTANT_TO` | 4,852 | `Type -> Pokemon` |
| `VERY_RESISTANT_TO` | 509 | `Type -> Pokemon` |
| `IMMUNE_TO` | 875 | `Type -> Pokemon` |
| `TRIGGERS` | 419 | `Move/Ability/Item -> Effect`, `Effect -> Ailment` |
| `APPLIES_AT` | 24 | `Effect -> Phase` |
| `AFFECTS_STAT` | 8 | `Effect -> Stat` |
| `MODIFIES_TYPE` | 36 | `Effect -> Type` |
| `CHANGES_FIELD` | 8 | `Effect -> Field` |
| `CHANGES_WEATHER` | 4 | `Effect -> Weather` |

## 데이터 소스

기본 데이터는 `database/common/data/processed` 아래 JSON을 사용합니다.

| 파일 | 사용처 |
| --- | --- |
| `pokemon.json` | `Pokemon` 노드 기본 정보 |
| `pokemon_stats.json` | `Pokemon` 능력치 속성 |
| `types.json` | `Type` 노드 |
| `pokemon_types.json` | `Pokemon - HAS_TYPE -> Type` |
| `moves.json` | `Move` 노드, `Move - HAS_TYPE -> Type` |
| `pokemon_moves.json` | `Pokemon - CAN_KNOW -> Move` |
| `abilities.json` | `Ability` 노드 |
| `pokemon_abilities.json` | `Pokemon - CAN_HAVE -> Ability` |
| `items.json` | `Item` 노드 |
| `species.json` | `Generation` 노드, `Pokemon - FROM -> Generation` |
| `evolutions.json` | 기본 폼 간 `Pokemon - EVOLVES_TO -> Pokemon` |
| `type_efficacy.json` | `Type - ATTACK_EFFECTIVE -> Type`, 포켓몬 방어 상성 파생 관계 |
| `effects.json` | `Effect` 노드 및 효과 계열 관계 |
| `stats.json` | `Stat` 노드 |
| `ailments.json` | `Ailment` 노드 |
| `phases.json` | `Phase` 노드 |
| `weathers.json` | `Weather` 노드 |
| `fields.json` | `Field` 노드 |
| `database/graph/move_effects.json` | `Move - TRIGGERS -> Effect` |
| `database/graph/ability_effects.json` | `Ability - TRIGGERS -> Effect` |
| `database/graph/item_effects.json` | `Item - TRIGGERS -> Effect` |

## 노드 스키마

### `Pokemon`

포켓몬 및 폼 단위 엔티티입니다. 추천 후보 필터링에는 `is_default = true`를 우선 사용합니다.

| Property | 설명 |
| --- | --- |
| `pokemon_id` | PokeAPI 포켓몬 ID, unique |
| `name` | 포켓몬 이름 |
| `height`, `weight` | 키, 몸무게 |
| `base_exp` | 기본 경험치 |
| `image_url`, `cry_url` | 이미지/울음소리 URL |
| `is_default` | 기본 폼 여부 |
| `species_id` | species 기준 ID. 진화 연결에 사용 |
| `hp`, `attack`, `defense`, `sp_attack`, `sp_defense`, `speed` | 기본 능력치 |
| `base_total` | 6개 기본 능력치 합 |

### `Type`

포켓몬 타입과 기술 타입을 함께 표현합니다.

| Property | 설명 |
| --- | --- |
| `type_id` | PokeAPI 타입 ID, unique |
| `name` | 타입 이름 |

### `Move`

포켓몬이 배울 수 있는 기술입니다. 기존 초안보다 배틀 효과 관련 속성이 많이 추가되었습니다.

| Property | 설명 |
| --- | --- |
| `move_id` | PokeAPI 기술 ID, unique |
| `name` | 기술 이름 |
| `type_id` | 기술 타입 ID |
| `power`, `accuracy`, `pp`, `priority` | 위력, 명중률, PP, 우선도 |
| `damage_class` | `physical`, `special`, `status` |
| `effect_text` | 기술 설명 |
| `ailment`, `ailment_chance` | 상태 이상 및 확률 |
| `category` | 기술 효과 카테고리 |
| `crit_rate`, `drain`, `flinch_chance`, `healing` | 부가 효과 수치 |
| `min_hits`, `max_hits`, `min_turns`, `max_turns` | 연속 공격/턴 범위 |
| `stat_chance`, `stat_changes` | 능력치 변화 확률과 변화 목록 JSON 문자열 |
| `target` | 기술 대상 |
| `fixed_damage` | 고정 데미지 |

### `Ability`

포켓몬 특성입니다.

| Property | 설명 |
| --- | --- |
| `ability_id` | PokeAPI 특성 ID, unique |
| `name` | 특성 이름 |
| `effect_text` | 특성 설명 |

### `Item`

아이템입니다.

| Property | 설명 |
| --- | --- |
| `item_id` | PokeAPI 아이템 ID, unique |
| `name` | 아이템 이름 |
| `category` | 아이템 카테고리 |
| `effect_text` | 아이템 설명 |

### `Generation`

포켓몬 등장 세대를 나타냅니다.

| Property | 설명 |
| --- | --- |
| `generation_id` | 세대 번호, unique |
| `name` | `generation-{id}` 형식 이름 |

### `Effect`

기술, 특성, 아이템이 발생시키는 추상 효과입니다.

| Property | 설명 |
| --- | --- |
| `effect_id` | 효과 ID |
| `name` | 효과 이름 |
| `effect_type` | 효과 분류 |
| `effect_text` | 효과 설명 |

### `Stat`

배틀 계산에 사용되는 능력치 노드입니다.

| Property | 설명 |
| --- | --- |
| `stat_id` | 스탯 ID |
| `name` | 스탯 이름 |
| `battle_stage_applicable` | 랭크 변화 적용 가능 여부. `hp`는 `false` |
| `description` | 설명 |

### `Ailment`

상태 이상 노드입니다.

| Property | 설명 |
| --- | --- |
| `ailment_id` | 상태 이상 ID |
| `name` | 상태 이상 이름 |
| `effect_text` | 효과 설명 |

### `Phase`

효과가 적용되는 배틀 페이즈입니다.

| Property | 설명 |
| --- | --- |
| `phase_id` | 페이즈 ID |
| `name` | 페이즈 이름 |
| `order` | 처리 순서 |
| `description` | 설명 |

### `Weather`

날씨 노드입니다.

| Property | 설명 |
| --- | --- |
| `weather_id` | 날씨 ID |
| `name` | 한글 이름 |
| `name_en` | 영문 이름 |
| `description` | 설명 |

### `Field`

필드, 룸, 중력 계열 효과 노드입니다.

| Property | 설명 |
| --- | --- |
| `field_id` | 필드 ID |
| `name` | 한글 이름 |
| `name_en` | 영문 이름 |
| `description` | 설명 |

## 관계 스키마

### 기본 관계

| 관계 | 방향 | 주요 속성 | 설명 |
| --- | --- | --- | --- |
| `HAS_TYPE` | `Pokemon -> Type` | `slot` | 포켓몬 타입 |
| `HAS_TYPE` | `Move -> Type` | 없음 | 기술 타입 |
| `CAN_KNOW` | `Pokemon -> Move` | `learn_method`, `level_learned_at` | 포켓몬이 배울 수 있는 기술 |
| `CAN_HAVE` | `Pokemon -> Ability` | `is_hidden`, `slot` | 포켓몬이 가질 수 있는 특성 |
| `ATTACK_EFFECTIVE` | `Type -> Type` | `damage_factor` | 공격 타입이 방어 타입에 주는 배율 |
| `FROM` | `Pokemon -> Generation` | 없음 | 포켓몬 등장 세대 |
| `EVOLVES_TO` | `Pokemon -> Pokemon` | `min_level`, `trigger_item_id`, `evolution_kind` | 일반 진화 또는 폼 분기 |

현재 진화는 `Species` 노드를 만들지 않고 `Pokemon.species_id`를 기준으로 `Pokemon -> Pokemon` 직접 관계를 생성합니다.

중요한 규칙은 다음과 같습니다.

| 구분 | 생성 규칙 | 예시 |
| --- | --- | --- |
| 일반 진화 | `evolutions.json`의 species 진화를 `is_default = true`인 대표 포켓몬끼리만 연결 | `파이리 -> 리자드 -> 리자몽` |
| 폼 분기 | 같은 `species_id`를 공유하는 비기본 폼은 대표 포켓몬에서 갈라지도록 연결 | `리자몽 -> 메가 리자몽 X`, `리자몽 -> 거다이맥스 리자몽` |

이 규칙이 필요한 이유는 `리자몽`, `메가 리자몽 X`, `메가 리자몽 Y`, `거다이맥스 리자몽`이 모두 같은 `species_id`를 공유하기 때문입니다. species만으로 단순 매칭하면 `리자드 -> 메가 리자몽 X`처럼 중간 진화가 최종 폼으로 직접 연결되는 잘못된 관계가 생깁니다.

### 포켓몬 방어 상성 파생 관계

`pokemon_types.json`, `types.json`, `type_efficacy.json`를 조합해 포켓몬이 각 공격 타입에 받는 최종 배율을 계산합니다.
방향은 공격 타입에서 방어 포켓몬으로 향하게 둡니다.

| 관계 | 조건 | 속성 |
| --- | --- | --- |
| `AGAINST` | 모든 공격 타입에 대해 생성 | `multiplier` |
| `VERY_WEAK_AGAINST` | `multiplier >= 4.0` | `multiplier` |
| `WEAK_AGAINST` | `multiplier > 1.0` | `multiplier` |
| `NORMAL_VULNERABILITY_AGAINST` | `multiplier == 1.0` | `multiplier` |
| `RESISTANT_TO` | `0.0 < multiplier < 1.0` | `multiplier` |
| `VERY_RESISTANT_TO` | `multiplier <= 0.25` | `multiplier` |
| `IMMUNE_TO` | `multiplier == 0.0` | `multiplier` |

팀 분석과 추천 API는 주로 `AGAINST`, `RESISTANT_TO`, `VERY_RESISTANT_TO`, `IMMUNE_TO`를 사용합니다.

### 효과 관계

기술, 특성, 아이템의 효과를 그래프에서 탐색하기 위한 관계입니다.

| 관계 | 방향 | 주요 속성 | 설명 |
| --- | --- | --- | --- |
| `TRIGGERS` | `Move -> Effect` | `phase_id`, `ailment_id`, `stat_ids`, `chance`, `values`, `target` | 기술이 발생시키는 효과 |
| `TRIGGERS` | `Ability -> Effect` | `phase_id`, `ailment_id`, `stat_ids`, `chance`, `values`, `target` | 특성이 발생시키는 효과 |
| `TRIGGERS` | `Item -> Effect` | `phase_id`, `ailment_id`, `stat_ids`, `chance`, `values`, `target` | 아이템이 발생시키는 효과 |
| `TRIGGERS` | `Effect -> Ailment` | 없음 | 효과가 유발하는 상태 이상 |
| `APPLIES_AT` | `Effect -> Phase` | 없음 | 효과 적용 페이즈 |
| `AFFECTS_STAT` | `Effect -> Stat` | 없음 | 효과가 바꾸는 능력치 |
| `MODIFIES_TYPE` | `Effect -> Type` | 없음 | 타입 무효/흡수/변경 계열 효과 |
| `CHANGES_FIELD` | `Effect -> Field` | 없음 | 필드 변경 효과 |
| `CHANGES_WEATHER` | `Effect -> Weather` | 없음 | 날씨 변경 효과 |

## 추천/분석에서 사용하는 핵심 흐름

### 팀 약점 분석

선택된 포켓몬 5마리의 방어 상성을 합산합니다.

```cypher
MATCH (attackType:Type)-[a:AGAINST]->(p:Pokemon)
WHERE p.pokemon_id IN $selected_pokemon_ids
RETURN attackType.type_id AS type_id,
       attackType.name AS type_name,
       sum(a.multiplier) AS weakness_score,
       avg(a.multiplier) AS average_multiplier
ORDER BY weakness_score DESC
```

### 방어 보완 후보 조회

팀의 약점 타입을 저항, 매우 저항, 무효로 받아낼 수 있는 포켓몬을 찾습니다.

```cypher
MATCH (weakType:Type)-[r:RESISTANT_TO|VERY_RESISTANT_TO|IMMUNE_TO]->(candidate:Pokemon)
WHERE weakType.type_id IN $weak_type_ids
AND candidate.is_default = true
AND NOT candidate.pokemon_id IN $selected_pokemon_ids
RETURN candidate.pokemon_id AS pokemon_id,
       candidate.name AS name,
       candidate.image_url AS image_url,
       candidate.base_total AS base_total,
       collect(DISTINCT {
           type_id: weakType.type_id,
           type_name: weakType.name,
           relation: type(r),
           multiplier: r.multiplier
       }) AS defensive_covers
ORDER BY base_total DESC
LIMIT $limit
```

### 공격 커버리지 조회

후보 포켓몬이 배울 수 있는 기술 타입을 조회합니다.

```cypher
MATCH (candidate:Pokemon)-[:CAN_KNOW]->(move:Move)-[:HAS_TYPE]->(moveType:Type)
WHERE candidate.pokemon_id IN $candidate_pokemon_ids
RETURN candidate.pokemon_id AS pokemon_id,
       collect(DISTINCT {
           type_id: moveType.type_id,
           type_name: moveType.name
       }) AS move_types
```

### 배틀용 방어 배율 조회

특정 포켓몬이 특정 공격 타입에 받는 배율을 빠르게 조회합니다.

```cypher
MATCH (attackType:Type)-[a:AGAINST]->(defender:Pokemon)
WHERE defender.pokemon_id = $defender_pokemon_id
AND attackType.type_id = $attack_type_id
RETURN defender.pokemon_id AS defender_pokemon_id,
       defender.name AS defender_name,
       attackType.type_id AS attack_type_id,
       attackType.name AS attack_type_name,
       a.multiplier AS multiplier
```

## 제약 조건과 인덱스

`database/graph/constraints.cypher` 기준 현재 생성되는 제약 조건과 인덱스입니다.

### Unique constraints

| Label | Property |
| --- | --- |
| `Pokemon` | `pokemon_id` |
| `Type` | `type_id` |
| `Move` | `move_id` |
| `Ability` | `ability_id` |
| `Item` | `item_id` |
| `Generation` | `generation_id` |

### Indexes

| Label | Property | 목적 |
| --- | --- | --- |
| `Pokemon` | `name` | 이름 검색 |
| `Pokemon` | `is_default` | 추천 후보 필터링 |
| `Pokemon` | `base_total` | 후보 정렬 |
| `Pokemon` | `species_id` | 진화 관계 연결 |
| `Type` | `name` | 타입 이름 검색 |
| `Move` | `name` | 기술 이름 검색 |
| `Move` | `damage_class` | 물리/특수/변화 필터링 |
| `Ability` | `name` | 특성 이름 검색 |
| `Item` | `name` | 아이템 이름 검색 |

## 초안 대비 변경 사항

| 초안 내용 | 현재 반영 상태 |
| --- | --- |
| `Species` 노드 | 제거됨. `Pokemon.species_id` 속성으로 유지 |
| `Species - EVOLVES_TO -> Species` | `Pokemon - EVOLVES_TO -> Pokemon`으로 변경. 일반 진화는 기본 폼끼리만 연결 |
| `Nature` 노드 | 현재 로더에서 생성하지 않음 |
| `Team`, `TeamMember` 노드 | 현재 로더에서 생성하지 않음. 서비스 계층 입력값으로 처리 |
| `CAN_MEGA_EVOLVE_TO`, `MEGA_REQUIRES` | 현재 생성하지 않음 |
| `Effect`, `Stat`, `Ailment`, `Phase`, `Weather`, `Field` | 새로 반영됨 |
| `TRIGGERS`, `APPLIES_AT`, `AFFECTS_STAT`, `MODIFIES_TYPE`, `CHANGES_FIELD`, `CHANGES_WEATHER` | 새로 반영됨 |

## 로더 실행 흐름

`database/graph/graph_loader.py`는 다음 순서로 실행됩니다.

1. Neo4j 연결
2. `--fresh` 사용 시 Docker Neo4j 저장소 초기화
3. `--reset` 또는 `--fresh` 사용 시 기존 그래프 데이터 삭제
4. `constraints.cypher` 적용
5. 노드 생성
6. 기본 관계 생성
7. 방어 상성 파생 관계 생성
8. 노드/관계 개수 요약 출력

실행 예시는 다음과 같습니다.

```bash
python database/graph/graph_loader.py --reset
```

완전히 깨끗한 Neo4j 저장소에서 다시 만들 때는 다음 옵션을 사용합니다.

```bash
python database/graph/graph_loader.py --fresh
```

## 최종 구조 요약

현재 Graph DB의 중심은 네 가지입니다.

| 축 | 핵심 노드/관계 |
| --- | --- |
| 포켓몬 기본 지식 | `Pokemon`, `Type`, `Move`, `Ability`, `Item`, `Generation` |
| 타입/방어 상성 | `HAS_TYPE`, `ATTACK_EFFECTIVE`, `AGAINST`, `WEAK_AGAINST`, `RESISTANT_TO`, `IMMUNE_TO` |
| 팀 분석/추천 | `AGAINST`, `RESISTANT_TO`, `VERY_RESISTANT_TO`, `IMMUNE_TO`, `CAN_KNOW`, `CAN_HAVE` |
| 배틀 효과 확장 | `Effect`, `Stat`, `Ailment`, `Phase`, `Weather`, `Field`, `TRIGGERS` 계열 관계 |

따라서 이 그래프는 PostgreSQL을 대체하는 저장소가 아니라, 팀 빌딩과 배틀 판단에 필요한 관계 탐색을 빠르게 수행하기 위한 보조 그래프 DB입니다.
