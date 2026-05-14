# 데이터베이스 설계

## 개요

배틀 시스템을 지원하기 위해 **RDB (PostgreSQL)** 와 **그래프 DB (Neo4j)** 두 가지 데이터베이스를 운영합니다. 현재 배틀 시스템은 RDB의 정보를 활용하며, 그래프 DB는 구축되었으나 활용되지 않습니다.

---

## 1. RDB (PostgreSQL) 설계

### 1.1 핵심 개념

**목표:** 포켓몬 배틀에 필요한 정형 데이터를 구조화된 형태로 저장  
**기술:** pgvector 지원으로 임베딩 저장 가능  
**주요 용도:** 배틀 로직, 포켓몬 조회, 타입 상성, 기술 데이터

### 1.2 주요 스키마

#### 1.2.1 포켓몬 정보 (Core)

```
pokemon (id, name, height, weight, base_exp, image_url, cry_url, is_default, species_id)
pokemon_stats (pokemon_id, hp, attack, defense, sp_attack, sp_defense, speed)
```

- **pokemon**: 포켓몬 기본 정보 (이미지, 울음소리, 고유 ID 매핑)
- **pokemon_stats**: 각 포켓몬의 6개 기본 스탯 (레벨 50 기준)
- **특징**: 이미지 URL로 프론트 렌더링, 울음소리 재생

#### 1.2.2 타입 시스템

```
types (id, name)
pokemon_types (pokemon_id, type_id, slot)
type_efficacy (damage_type_id, target_type_id, damage_factor)
```

- **types**: 18가지 타입 (물, 불, 풀, ...)
- **pokemon_types**: 포켓몬의 타입 (최대 2개, slot 1-2)
- **type_efficacy**: 타입 상성 매트릭스 (2배, 1배, 0.5배, 0배)
- **배틀 활용**: 데미지 계산 시 공격 타입 vs 방어 포켓몬 타입

**예시:**
```
┌─────────────┐
│ type_efficacy
├─────────────┤
│ 불(fire) 기술이 풀(grass) 타입에 → 2.0배
│ 물(water) 기술이 불(fire) 타입에 → 2.0배
│ 속성 기술이 바위(rock) 타입에 → 0.5배
└─────────────┘
```

#### 1.2.3 기술 시스템

```
moves (
  id, name, type_id, 
  power, accuracy, damage_class (physical/special/status),
  ailment, ailment_chance,
  category (damage, damage-raise, damage-lower, heal, damage-fixed, ...),
  crit_rate, drain, flinch_chance, healing,
  stat_chance, stat_changes,
  fixed_damage, effect_text
)

pokemon_moves (pokemon_id, move_id, learn_method, level_learned_at)
```

**배틀에 사용되는 주요 필드:**

| 필드 | 의미 | 배틀에서의 역할 |
|------|------|-----------------|
| `power` | 기술의 위력 | 데미지 계산 기초 |
| `accuracy` | 명중률 (%) | 명중 판정 (0~100) |
| `damage_class` | physical/special/status | 스탯 선택 (공격력/특공) |
| `crit_rate` | 급소율 레벨 (0-3) | 급소 기댓값 (1.5배 증폭) |
| `stat_changes` | {"attack": +2} 등 | 배틀 중 스탯 변화 |
| `ailment` | 마비, 중독, 화상 등 | 상태이상 부여 |
| `category` | damage / damage-fixed / heal | 처리 로직 분기 |
| `fixed_damage` | "20레벨" 등 고정 데미지 | power 없는 기술의 계산 |

**학습 방식:**
- `level-up`: 특정 레벨에서 자동 학습
- `machine`: TM/HM 사용으로 학습
- `egg`: 알에서 태어나며 학습
- `tutor`: 기술 교사에게 배움

#### 1.2.4 배틀 로직에 필요한 추가 정보

```
abilities (id, name, effect_text, embedding)
pokemon_abilities (pokemon_id, ability_id, is_hidden, slot)

natures (id, name, increased_stat, decreased_stat)
```

- **특성(Ability)**: 배틀 중 자동 발동 효과 (현재 미구현)
- **성격(Nature)**: 스탯에 ±10% 영향 (현재 미구현)

#### 1.2.5 사용자 및 게임 로그

```
users (id, github_id, login, name, avatar_url, email, public_repos, total_commits, total_stars)
game_logs (id, user_id, game_type, pokemon_id, is_correct, hint_used, wrong_answer_id, log_data, created_at)
```

---

## 2. 그래프 DB (Neo4j) 설계

### 2.1 개요

**목표:** 포켓몬 간 관계성 표현 (타입 상성, 진화, 기술 습득 경로 등)  
**현재 상태:** 구축되었으나 배틀 시스템에 미활용 (MVP 수준의 배틀은 RDB로 충분)

### 2.2 노드 및 관계

#### 노드 (Node)

```
(:Pokemon)
  - id, name, height, weight, base_exp, species_id
  - stats: {hp, attack, defense, sp_attack, sp_defense, speed}
  - types: [type_ids]

(:Type)
  - id, name

(:Move)
  - id, name, power, accuracy, damage_class, category
  - properties: {crit_rate, drain, flinch_chance, ailment, ...}

(:Species)
  - generation, capture_rate

(:Item)
  - name, category
```

#### 관계 (Relationship)

```
(:Pokemon)-[:HAS_TYPE]->(:Type)
(:Pokemon)-[:CAN_LEARN]->(:Move)
  - learn_method: "level-up" | "machine" | "egg" | "tutor"
  - level_learned_at: 레벨

(:Pokemon)-[:WEAK_TO]->(:Type)
  - damage_factor: 2.0, 1.0, 0.5, 0.0

(:Pokemon)-[:EVOLVES_TO]->(:Pokemon)
  - trigger: "level" | "item" | "trade"
  - level: 진화 레벨

(:Move)-[:HAS_CATEGORY]->(:Category)
```

### 2.3 쿼리 예시 (현재 미사용)

```cypher
-- 불 타입 포켓몬이 배울 수 있는 물 타입 기술
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type {name: "fire"})
MATCH (p)-[:CAN_LEARN]->(m:Move)-[:HAS_TYPE]->(t2:Type {name: "water"})
RETURN p.name, m.name

-- 피카츄의 모든 진화 경로
MATCH (p:Pokemon {name: "pikachu"})-[:EVOLVES_TO*]->(evolved)
RETURN p.name, evolved.name
```

---

## 3. 데이터 흐름 in 배틀 시스템

```
┌─────────────────────────────────────┐
│  Frontend (Streamlit)               │
│  - 포켓몬 선택                       │
│  - 기술 선택                         │
└─────────────┬───────────────────────┘
              │ (HTTP Request)
              ▼
┌──────────────────────────────────────┐
│  Backend API Endpoint                │
│  /api/v1/battle/start                │
│  /api/v1/battle/process_turn         │
└─────────┬────────────────────────────┘
          │ 
    ┌─────▼─────────────┐
    │  Query Database   │
    ├─────────────────┤
    │ 1. Pokemon 기본  │
    │ 2. Stats 조회    │
    │ 3. Types 조회    │
    │ 4. Moves 조회    │
    │ 5. Type Efficacy │
    └─────┬───────────┘
          │
    ┌─────▼──────────────────┐
    │  배틀 로직 실행         │
    │  - 데미지 계산         │
    │  - 우선도 판정         │
    │  - 상태이상 처리       │
    └──────┬────────────────┘
           │
    ┌──────▼──────────────────┐
    │  게임 로그 저장         │
    │  - game_logs 테이블     │
    │  - JSON 형태의 배틀 기록│
    └──────┬────────────────┘
           │
           ▼  (HTTP Response with battle logs)
    ┌──────────────────┐
    │  Frontend Update │
    │  - 데미지 표시   │
    │  - 상태 갱신     │
    └──────────────────┘
```

---

## 4. 배틀에 활용되는 데이터 예시

### 4.1 포켓몬 객체 (배틀 중 메모리에 로드)

```python
{
    "id": 25,
    "name": "피카츄",
    "level": 50,
    "current_hp": 95,  # 최대 HP 중 현재 HP
    "stats": {
        "hp": 95,
        "attack": 55,
        "defense": 40,
        "sp_attack": 50,
        "sp_defense": 50,
        "speed": 90
    },
    "types": [13, 14],  # [electric, normal] IDs
    "moves": [
        {
            "id": 4,
            "name": "전광석화",
            "type_id": 13,
            "power": 90,
            "accuracy": 100,
            "damage_class": "physical",
            "crit_rate": 0,
            "stat_changes": {}
        },
        ...
    ],
    "stat_changes": {"attack": 0, "defense": 0, ...},  # 스탯 스테이지 변화
    "ailment": None,  # "paralysis", "burn", "freeze", ...
    "current_hp": 95
}
```

### 4.2 타입 상성 예시

```
type_efficacy 테이블:
┌─────────────────┬──────────────────┬─────────────┐
│ damage_type_id  │ target_type_id   │ damage_factor
├─────────────────┼──────────────────┼─────────────┤
│ 5 (water)       │ 3 (fire)         │ 2.0
│ 10 (grass)      │ 5 (water)        │ 2.0
│ 13 (electric)   │ 5 (water)        │ 2.0
│ 5 (water)       │ 13 (electric)    │ 1.0
│ 3 (fire)        │ 13 (electric)    │ 1.0
└─────────────────┴──────────────────┴─────────────┘
```

---

## 5. 설계 결정 및 트레이드오프

### 5.1 왜 그래프 DB를 구축했지만 사용하지 않는가?

**당초 계획:**
- 타입 상성, 진화 경로 등 복잡한 관계를 그래프로 표현
- 고급 배틀 AI (예: 상성 분석하여 포켓몬 교체 결정)

**현실:**
- MVP 수준의 배틀 시스템은 RDB 조회만으로 충분
- 복잡한 관계 쿼리가 필수적이지 않음
- 타입 상성도 사전에 계산하여 메모리에 로드 가능

**교훈:** "지식의 저주" — 포켓몬 배틀을 깊이 있게 알아서 최초 설계가 과도했음. 작은 기능부터 시작하여 필요에 따라 확장하는 것이 나음.

### 5.2 벡터 DB 미구축

**고려 사항:**
- 포켓몬 설명, 기술 효과 텍스트 임베딩 → RAG 기반 LLM 질의
- 현재는 LLM이 구조화된 데이터 (포켓몬 스탯, 기술)만 받음

**결정:** MVP에서는 필요 없음 (구조화 데이터로 충분)

---

## 6. 배틀 시스템이 실제로 사용하는 쿼리

### 6.1 포켓몬 데이터 로드

```sql
-- 1. 포켓몬 기본 정보
SELECT p.id, p.name, p.image_url
FROM pokemon p
WHERE p.id = :pokemon_id;

-- 2. 스탯
SELECT hp, attack, defense, sp_attack, sp_defense, speed
FROM pokemon_stats
WHERE pokemon_id = :pokemon_id;

-- 3. 타입
SELECT t.id, t.name
FROM pokemon_types pt
JOIN types t ON pt.type_id = t.id
WHERE pt.pokemon_id = :pokemon_id
ORDER BY pt.slot;

-- 4. 학습 가능 기술 (플레이어는 level-up만)
SELECT m.id, m.name, m.type_id, m.power, m.accuracy, 
       m.damage_class, m.crit_rate, m.stat_changes
FROM pokemon_moves pm
JOIN moves m ON pm.move_id = m.id
WHERE pm.pokemon_id = :pokemon_id 
  AND pm.learn_method = 'level-up'
  AND pm.level_learned_at <= :player_level;
```

### 6.2 타입 상성 조회

```sql
SELECT te.damage_type_id, te.target_type_id, te.damage_factor
FROM type_efficacy te;
-- 메모리에 2D 배열로 로드 후 사용
```

---

## 7. 향후 확장 계획

1. **벡터 DB 추가:** 포켓몬 설명 RAG
2. **그래프 DB 활용:** 고급 AI 전략 (상성 분석)
3. **특성(Ability) 구현:** 배틀 중 자동 효과
4. **성격(Nature) 반영:** 스탯 보정
5. **아이템 시스템:** 배틀 중 아이템 사용 (현재 미구현)

---

## 참고: 데이터 적재 방식

### PostgreSQL
```bash
docker-compose up postgres
# schema.sql이 자동 실행됨
```

### Neo4j
```bash
docker-compose up neo4j
# 수동으로 Cypher 쿼리 실행 (database/graph/graph_loader.py)
```
