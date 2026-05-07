# Pokemon Graph DB 설계 문서

이 문서는 포켓몬 팀 추천 기능과 배틀 기능을 위해 Neo4j Graph DB를 어떻게 구성할지 정리한 설계 문서입니다.

현재 프로젝트는 PostgreSQL 기반의 관계형 데이터와 pgvector 기반 RAG 데이터를 이미 가지고 있습니다. Graph DB는 기존 DB를 대체하는 것이 아니라, 포켓몬 사이의 관계를 탐색하고 추천 이유를 만들기 위한 보조 데이터베이스로 사용합니다.

## 문서 아웃라인

이 문서는 아래 순서로 읽으면 됩니다.

| 순서 | 섹션 | 읽는 목적 |
| --- | --- | --- |
| 1 | 전체 목표 | Graph DB를 왜 만드는지 이해합니다. |
| 2 | 설계 원칙 | 기존 PostgreSQL/RAG 구조와 Graph DB 역할을 구분합니다. |
| 3 | 데이터 출처 | 어떤 JSON 파일을 Graph DB 적재에 사용할지 확인합니다. |
| 4 | 데이터 범위 | 1차, 2차, 3차로 무엇을 만들지 나눕니다. |
| 5 | Node 설계 | `Pokemon`, `Type`, `Move`, `Ability`, `Species`, `Item`, `Generation` 노드를 정의합니다. |
| 6 | Relationship 설계 | JSON에서 바로 만드는 관계와 계산해서 만드는 관계를 구분합니다. |
| 7 | 팀 추천 기능 설계 | 5마리 선택 후 1마리를 추천하는 점수 계산 방향을 설명합니다. |
| 8 | 배틀 기능 설계 | 타입, 기술, 특성, 아이템, 메가진화를 단계적으로 반영하는 방향을 설명합니다. |
| 9 | 메가진화와 아이템 설계 | 메가진화에 필요한 아이템 관계를 따로 정리합니다. |
| 10 | 추천/배틀 관계 구분 | 기능별로 어떤 노드와 관계가 중요한지 비교합니다. |
| 11 | 구현 단계 계획 | `constraints.cypher`, `graph_loader.py`, API 구현 순서를 정리합니다. |
| 12 | Graph Loader 작성 계획 | JSON을 Neo4j에 넣는 파이썬 파일 구조를 설명합니다. |
| 13 | Constraints 작성 계획 | 고유 ID와 인덱스를 어떤 기준으로 만들지 정리합니다. |
| 14 | 최종 요약 | 전체 Graph DB 구조를 짧게 다시 확인합니다. |

## 빠른 결론

처음 구현에서 가장 중요한 그래프 중심축은 아래와 같습니다.

```text
Pokemon - HAS_TYPE -> Type
Pokemon - CAN_KNOW -> Move - HAS_TYPE -> Type
Pokemon - CAN_HAVE -> Ability
Pokemon - AGAINST -> Type
Pokemon - RESISTANT_TO -> Type
Pokemon - IMMUNE_TO -> Type
Type - ATTACK_EFFECTIVE -> Type
```

팀 추천은 `Pokemon`, `Type`, `Move`를 중심으로 시작합니다.

배틀 기능은 이후 `Ability`, `Item`, `Team`, `TeamMember`, 메가진화 관계까지 확장합니다.

## 1. 전체 목표

Graph DB를 만드는 이유는 크게 두 가지입니다.

### 1.1 팀 추천 기능

사용자가 6마리 중 5마리를 선택했을 때, 마지막 1마리를 추천합니다.

이 기능에서 Graph DB는 아래 질문에 답해야 합니다.

| 질문 | Graph DB에서 필요한 정보 |
| --- | --- |
| 현재 팀이 어떤 타입 공격에 약한가? | Pokemon과 Type 사이의 방어 상성 관계 |
| 현재 팀이 어떤 타입 공격을 잘 못 하는가? | Pokemon, Move, Type 관계 |
| 현재 팀과 타입이 너무 겹치지 않는 후보는 누구인가? | Pokemon과 Type 관계 |
| 팀의 약점을 보완하는 포켓몬은 누구인가? | Pokemon과 Type 사이의 저항/무효 관계 |
| 추천 이유를 어떻게 설명할 수 있는가? | 후보가 보완하는 약점 타입, 배울 수 있는 기술 타입, 능력치 |

### 1.2 배틀 기능

두 포켓몬 또는 두 팀이 배틀할 때, 타입 상성, 기술, 능력치, 특성, 아이템, 폼 변화를 고려합니다.

이 기능에서 Graph DB는 아래 질문에 답해야 합니다.

| 질문 | Graph DB에서 필요한 정보 |
| --- | --- |
| A 포켓몬이 B 포켓몬에게 어떤 타입 기술로 유리한가? | Move와 Type, Pokemon의 방어 상성 관계 |
| 특정 포켓몬이 어떤 기술을 배울 수 있는가? | Pokemon과 Move 관계 |
| 특정 포켓몬이 어떤 특성을 가질 수 있는가? | Pokemon과 Ability 관계 |
| 특정 포켓몬이 메가진화할 수 있는가? | Pokemon, Item, Form 관계 |
| 배틀 중 아이템이 필요한 변화가 있는가? | Pokemon과 Item 관계 |

## 2. 설계 원칙

이 프로젝트의 Graph DB는 아래 원칙을 따릅니다.

| 원칙 | 설명 |
| --- | --- |
| 기존 데이터 구조 유지 | `data/data/processed/*.json`을 기준으로 적재합니다. 기존 폴더 구조를 바꾸지 않습니다. |
| PostgreSQL과 역할 분리 | 목록 조회, 페이지네이션, RAG 검색은 PostgreSQL이 담당하고, 관계 탐색은 Neo4j가 담당합니다. |
| 처음부터 너무 복잡하게 만들지 않기 | 정적 포켓몬 지식 그래프를 먼저 만들고, 유저 팀/배틀 상태는 이후 확장합니다. |
| 추천과 배틀을 함께 고려 | 팀 추천만을 위한 그래프가 아니라, 배틀 기능까지 확장 가능한 관계 이름을 사용합니다. |
| 원본 관계와 파생 관계 분리 | JSON에서 바로 만들 수 있는 관계와 계산해서 만드는 관계를 구분합니다. |

## 3. 데이터 출처

Graph DB는 아래 JSON 파일을 기준으로 만듭니다.

| 파일 | Graph DB 사용 여부 | 주요 용도 |
| --- | --- | --- |
| `pokemon.json` | 사용 | Pokemon 노드 생성 |
| `pokemon_stats.json` | 사용 | Pokemon 능력치 속성 추가 |
| `types.json` | 사용 | Type 노드 생성 |
| `pokemon_types.json` | 사용 | Pokemon과 Type 관계 생성 |
| `type_efficacy.json` | 사용 | Type 간 공격 상성 생성 |
| `moves.json` | 사용 | Move 노드 생성, Move와 Type 관계 생성 |
| `pokemon_moves.json` | 사용 | Pokemon과 Move 관계 생성 |
| `abilities.json` | 사용 | Ability 노드 생성 |
| `pokemon_abilities.json` | 사용 | Pokemon과 Ability 관계 생성 |
| `species.json` | 사용 | Species 노드 생성, 세대 정보 연결 |
| `evolutions.json` | 사용 | Species 진화 관계 생성 |
| `items.json` | 사용 | Item 노드 생성 |
| `flavor_text.json` | 초기 제외 | 설명/RAG 성격이 강함 |
| `pokemon_knowledge.json` | 초기 제외 | pgvector 검색에 더 적합 |
| `natures.json` | 초기 제외 | 배틀 심화 단계에서 성격 보정용으로 사용 가능 |

## 4. Graph DB에서 다룰 데이터 범위

Graph DB는 한 번에 모든 포켓몬 시스템을 완벽하게 반영하지 않습니다.

먼저 아래 범위부터 구성합니다.

| 단계 | 포함 내용 |
| --- | --- |
| 1단계 | 포켓몬, 타입, 기술, 특성, 종, 아이템 노드 |
| 1단계 | 포켓몬 타입, 기술 타입, 배울 수 있는 기술, 가질 수 있는 특성 |
| 1단계 | 타입 공격 상성 |
| 1단계 | 포켓몬별 방어 상성 파생 관계 |
| 1단계 | 일반 진화 관계 |
| 2단계 | 메가진화, 폼 변화, 아이템 요구 관계 |
| 2단계 | 팀 추천 점수 계산용 관계 |
| 3단계 | 실제 유저 팀 인스턴스, 선택한 기술 4개, 선택한 특성 1개, 장착 아이템 |
| 3단계 | 배틀 상태, 날씨, 필드, 랭크 변화, 상태 이상 |

## 5. Node 설계

노드는 Graph DB에서 점으로 표현되는 데이터입니다.

이 프로젝트에서는 `Pokemon`, `Type`, `Move`, `Ability`, `Species`, `Item`, `Generation`을 기본 노드로 봅니다.

## 5.1 Pokemon 노드

### 목적

포켓몬 한 개체 또는 한 폼을 나타냅니다.

여기서 중요한 점은 `pokemon.json`에는 기본 포켓몬뿐만 아니라 메가진화, 리전폼, 특수 폼도 포함될 수 있다는 점입니다. 따라서 팀 추천 후보로 사용할 때는 `is_default = true` 조건을 우선 사용합니다.

### Source

| 파일 | 사용 필드 |
| --- | --- |
| `pokemon.json` | `id`, `name`, `height`, `weight`, `base_exp`, `image_url`, `cry_url`, `is_default` |
| `pokemon_stats.json` | `hp`, `attack`, `defense`, `sp_attack`, `sp_defense`, `speed` |

### Properties

| property | 설명 | 예시 |
| --- | --- | --- |
| `pokemon_id` | PokeAPI 기준 포켓몬 ID | `1` |
| `name` | 포켓몬 이름 | `"이상해씨"` |
| `height` | 키 | `7` |
| `weight` | 몸무게 | `69` |
| `base_exp` | 기본 경험치 | `64` |
| `image_url` | 공식 이미지 URL | `"https://..."` |
| `cry_url` | 울음소리 URL | `"https://..."` |
| `is_default` | 기본 형태 여부 | `true` |
| `hp` | HP | `45` |
| `attack` | 공격 | `49` |
| `defense` | 방어 | `49` |
| `sp_attack` | 특수공격 | `65` |
| `sp_defense` | 특수방어 | `65` |
| `speed` | 스피드 | `45` |
| `base_total` | 여섯 능력치 총합 | `318` |

### 추천 기능에서 사용

팀 추천에서는 `Pokemon` 노드를 후보 포켓몬으로 사용합니다.

추천 후보 조건은 처음에는 아래처럼 잡는 것이 좋습니다.

```cypher
MATCH (p:Pokemon)
WHERE p.is_default = true
RETURN p
```

이 조건을 쓰면 메가진화 폼이나 특수 폼이 추천 후보에 섞이는 문제를 줄일 수 있습니다.

### 배틀 기능에서 사용

배틀에서는 `is_default = false` 포켓몬도 의미가 생길 수 있습니다.

예를 들어 메가리자몽X는 팀 추천 후보로는 제외하지만, 배틀 중 리자몽이 메가진화할 수 있는 결과 폼으로는 사용할 수 있습니다.

## 5.2 Type 노드

### 목적

포켓몬 타입과 기술 타입을 나타냅니다.

타입은 팀 추천과 배틀 기능의 핵심 노드입니다.

### Source

| 파일 | 사용 필드 |
| --- | --- |
| `types.json` | `id`, `name` |

### Properties

| property | 설명 | 예시 |
| --- | --- | --- |
| `type_id` | PokeAPI 기준 타입 ID | `12` |
| `name` | 타입 이름 | `"풀"` |

### 추천 기능에서 사용

선택된 팀이 어떤 타입 공격에 약한지 계산할 때 사용합니다.

### 배틀 기능에서 사용

기술 타입과 방어 포켓몬 타입의 상성을 계산할 때 사용합니다.

## 5.3 Move 노드

### 목적

포켓몬이 배울 수 있는 기술을 나타냅니다.

기술은 공격 커버리지와 배틀 계산에 필요합니다.

### Source

| 파일 | 사용 필드 |
| --- | --- |
| `moves.json` | `id`, `name`, `type_id`, `power`, `accuracy`, `damage_class`, `effect_text` |

### Properties

| property | 설명 | 예시 |
| --- | --- | --- |
| `move_id` | PokeAPI 기준 기술 ID | `1` |
| `name` | 기술 이름 | `"막치기"` |
| `power` | 위력 | `40` |
| `accuracy` | 명중률 | `100` |
| `damage_class` | 기술 분류 | `"physical"` |
| `effect_text` | 기술 설명 | `"긴 꼬리나 손 등을 사용하여..."` |

### 추천 기능에서 사용

현재 팀이 잘 공격하지 못하는 타입을 보완할 수 있는 기술을 배우는 포켓몬을 찾을 때 사용합니다.

### 배틀 기능에서 사용

기술 위력, 기술 타입, 물리/특수 여부를 바탕으로 데미지 계산에 사용합니다.

## 5.4 Ability 노드

### 목적

포켓몬이 가질 수 있는 특성을 나타냅니다.

초기 팀 추천에서는 낮은 우선순위지만, 배틀 기능에서는 중요도가 올라갑니다.

### Source

| 파일 | 사용 필드 |
| --- | --- |
| `abilities.json` | `id`, `name`, `effect_text` |

### Properties

| property | 설명 | 예시 |
| --- | --- | --- |
| `ability_id` | PokeAPI 기준 특성 ID | `65` |
| `name` | 특성 이름 | `"심록"` |
| `effect_text` | 특성 설명 | `"HP가 줄었을 때 풀 타입 기술의 위력이 올라간다."` |

### 추천 기능에서 사용

초기에는 추천 이유 보조 정보로만 사용합니다.

예를 들어 숨겨진 특성을 제외하거나, 특정 특성이 있는 포켓몬을 우선 추천하는 고급 기능으로 확장할 수 있습니다.

### 배틀 기능에서 사용

상성 무효, 날씨 변화, 타입 변화, 기술 강화 같은 효과를 반영할 때 필요합니다.

## 5.5 Species 노드

### 목적

포켓몬의 종 단위 정보를 나타냅니다.

현재 프로젝트의 `evolutions.json`은 `pokemon_id`가 아니라 `species_id` 기준으로 진화 관계를 가지고 있습니다. 그래서 진화 관계를 정확하게 표현하려면 `Species` 노드가 필요합니다.

### Source

| 파일 | 사용 필드 |
| --- | --- |
| `species.json` | `id`, `pokemon_id`, `generation`, `capture_rate` |

### Properties

| property | 설명 | 예시 |
| --- | --- | --- |
| `species_id` | PokeAPI 기준 species ID | `1` |
| `generation` | 등장 세대 | `1` |
| `capture_rate` | 포획률 | `45` |

### 추천 기능에서 사용

초기 추천에서는 직접 사용 빈도가 낮습니다.

다만 진화 전/후 포켓몬을 추천 후보에서 어떻게 처리할지 결정할 때 사용할 수 있습니다.

### 배틀 기능에서 사용

진화 경로, 폼 관계, 세대 제한 등을 표현할 때 사용합니다.

## 5.6 Item 노드

### 목적

아이템을 나타냅니다.

처음 팀 추천에서는 필수는 아니지만, 배틀 기능과 메가진화까지 고려하면 반드시 필요해집니다.

### Source

| 파일 | 사용 필드 |
| --- | --- |
| `items.json` | `id`, `name`, `category`, `effect_text` |

### Properties

| property | 설명 | 예시 |
| --- | --- | --- |
| `item_id` | PokeAPI 기준 아이템 ID | `1` |
| `name` | 아이템 이름 | `"마스터볼"` |
| `category` | 아이템 카테고리 | `"standard-balls"` |
| `effect_text` | 아이템 설명 | `"야생 포켓몬을 반드시 잡을 수 있는..."` |

### 추천 기능에서 사용

초기 팀 추천에서는 사용하지 않아도 됩니다.

다만 나중에 추천 이유를 더 정교하게 만들 때는 아래처럼 사용할 수 있습니다.

| 사용 예시 | 설명 |
| --- | --- |
| 메가진화 가능 여부 | 특정 포켓몬이 특정 메가스톤을 필요로 하는지 |
| 배틀 아이템 추천 | 후보 포켓몬에게 어울리는 장착 아이템 추천 |
| 진화 아이템 정보 | 진화 경로 설명에 아이템 조건 표시 |

### 배틀 기능에서 사용

아이템은 배틀에서 매우 중요합니다.

예를 들어 메가진화는 보통 특정 메가스톤이 필요합니다.

따라서 배틀 기능에서는 아래 관계가 필요할 수 있습니다.

```text
(Pokemon)-[:CAN_MEGA_EVOLVE_TO]->(Pokemon)
(Pokemon)-[:MEGA_REQUIRES]->(Item)
```

## 5.7 Generation 노드

### 목적

포켓몬 등장 세대를 나타냅니다.

초기에는 `Species.generation` 속성으로만 처리해도 되지만, 나중에 특정 세대 제한 추천이나 배틀 룰을 만들려면 노드로 분리할 수 있습니다.

### Source

| 파일 | 사용 필드 |
| --- | --- |
| `species.json` | `generation` |

### Properties

| property | 설명 | 예시 |
| --- | --- | --- |
| `generation_id` | 세대 번호 | `1` |
| `name` | 세대 이름 | `"generation-1"` |

### 사용 여부

초기 버전에서는 선택입니다.

가독성과 확장성을 생각하면 `Generation` 노드를 만들어도 좋지만, 필수는 아닙니다.

## 6. Relationship 설계

관계는 Graph DB에서 선으로 표현되는 데이터입니다.

이 프로젝트의 핵심은 관계 설계입니다. 특히 팀 추천은 결국 관계를 따라가며 점수를 계산하는 방식입니다.

## 6.1 원본 JSON에서 바로 만들 수 있는 관계

이 섹션의 관계는 JSON 파일에서 직접 만들 수 있습니다.

## 6.1.1 Pokemon - HAS_TYPE -> Type

### 목적

포켓몬이 어떤 타입을 가지는지 나타냅니다.

### Source

`pokemon_types.json`

### Direction

```text
(Pokemon)-[:HAS_TYPE]->(Type)
```

### Properties

| property | 설명 |
| --- | --- |
| `slot` | 1타입/2타입 순서 |

### 사용 예시

```cypher
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type)
WHERE p.name = "이상해씨"
RETURN p.name, t.name
```

### 팀 추천에서의 의미

팀의 타입 중복을 확인할 때 사용합니다.

예를 들어 이미 물 타입 포켓몬이 많으면 또 물 타입 후보를 추천할 때 감점할 수 있습니다.

### 배틀에서의 의미

방어 포켓몬의 타입을 확인해서 기술 데미지 배율을 계산할 때 사용합니다.

## 6.1.2 Move - HAS_TYPE -> Type

### 목적

기술이 어떤 타입인지 나타냅니다.

### Source

`moves.json`

### Direction

```text
(Move)-[:HAS_TYPE]->(Type)
```

### 팀 추천에서의 의미

후보 포켓몬이 배울 수 있는 기술 타입을 확인해서 공격 커버리지를 계산합니다.

### 배틀에서의 의미

공격 기술의 타입을 확인해서 방어 포켓몬에게 몇 배 데미지가 들어가는지 계산합니다.

## 6.1.3 Pokemon - CAN_KNOW -> Move

### 목적

포켓몬이 배울 수 있는 기술을 나타냅니다.

강의 자료의 `CAN_KNOW` 이름을 참고했습니다.

### Source

`pokemon_moves.json`

### Direction

```text
(Pokemon)-[:CAN_KNOW]->(Move)
```

### Properties

| property | 설명 |
| --- | --- |
| `learn_method` | 기술 습득 방식 |
| `level_learned_at` | 습득 레벨 |

### 주의점

`pokemon_moves.json`에는 같은 포켓몬과 같은 기술이 여러 습득 방식으로 들어갈 수 있습니다.

예를 들어 같은 기술을 `level-up`, `machine`, `tutor`로 모두 배울 수 있습니다.

그래서 관계 중복을 완전히 제거할지, 습득 방식을 속성으로 유지할지 결정해야 합니다.

초기 버전에서는 아래처럼 유지하는 것을 추천합니다.

```text
(Pokemon)-[:CAN_KNOW {learn_method, level_learned_at}]->(Move)
```

### 팀 추천에서의 의미

후보 포켓몬이 어떤 타입 기술을 배울 수 있는지 확인합니다.

예를 들어 현재 팀이 페어리 타입 공격이 부족하다면, 페어리 타입 기술을 배울 수 있는 후보에게 점수를 줄 수 있습니다.

### 배틀에서의 의미

실제 배틀에서는 모든 배울 수 있는 기술이 아니라 선택된 4개 기술만 사용해야 합니다.

초기 배틀에서는 `CAN_KNOW`를 사용하고, 나중에 실제 팀 인스턴스를 만들면 `TeamMember - KNOWS -> Move` 관계를 추가합니다.

## 6.1.4 Pokemon - CAN_HAVE -> Ability

### 목적

포켓몬이 가질 수 있는 특성을 나타냅니다.

강의 자료의 `CAN_HAVE` 이름을 참고했습니다.

### Source

`pokemon_abilities.json`

### Direction

```text
(Pokemon)-[:CAN_HAVE]->(Ability)
```

### Properties

| property | 설명 |
| --- | --- |
| `is_hidden` | 숨겨진 특성 여부 |
| `slot` | 특성 슬롯 |

### 팀 추천에서의 의미

초기에는 보조 정보로만 사용합니다.

나중에 특정 특성을 가진 포켓몬을 우선 추천할 수 있습니다.

### 배틀에서의 의미

실제 배틀에서는 포켓몬이 가능한 특성 중 하나만 가집니다.

초기 배틀에서는 `CAN_HAVE`를 참고하고, 나중에 실제 팀 인스턴스에서는 `TeamMember - HAS -> Ability` 관계를 추가합니다.

## 6.1.5 Type - ATTACK_EFFECTIVE -> Type

### 목적

공격 타입이 방어 타입에게 주는 데미지 배율을 나타냅니다.

### Source

`type_efficacy.json`

### Direction

```text
(공격 Type)-[:ATTACK_EFFECTIVE]->(방어 Type)
```

### Properties

| property | 설명 |
| --- | --- |
| `damage_factor` | 데미지 배율 |

### 예시

```text
(불꽃)-[:ATTACK_EFFECTIVE {damage_factor: 2.0}]->(풀)
```

### 주의점

`type_efficacy.json`에는 모든 1.0 관계가 들어있지 않을 수 있습니다.

따라서 관계가 없으면 기본값 1.0으로 처리해야 합니다.

### 팀 추천에서의 의미

후보 포켓몬이 배울 수 있는 기술 타입이 어떤 타입을 잘 공격하는지 확인할 수 있습니다.

### 배틀에서의 의미

기술 타입과 방어 타입 사이의 데미지 배율 계산에 사용합니다.

## 6.1.6 Species - EVOLVES_TO -> Species

### 목적

포켓몬 종의 일반 진화 관계를 나타냅니다.

### Source

`evolutions.json`

### Direction

```text
(Species)-[:EVOLVES_TO]->(Species)
```

### Properties

| property | 설명 |
| --- | --- |
| `min_level` | 진화 최소 레벨 |
| `trigger_item_id` | 진화 아이템 ID |

### 아이템 관련 주의점

현재 `evolutions.json`에는 `trigger_item_id`가 들어있습니다.

처음에는 관계 속성으로만 보관해도 됩니다.

하지만 아이템을 그래프에서 더 적극적으로 쓰려면 아래 관계를 추가할 수 있습니다.

```text
(Species)-[:EVOLUTION_REQUIRES]->(Item)
```

이 관계는 진화 아이템 설명이나 진화 경로 시각화에서 유용합니다.

## 6.1.7 Pokemon - IS_SPECIES -> Species

### 목적

포켓몬과 종 정보를 연결합니다.

### Source

`species.json`

### Direction

```text
(Pokemon)-[:IS_SPECIES]->(Species)
```

### 사용 이유

진화 정보는 `Species` 기준이고, 타입/기술/능력치는 `Pokemon` 기준입니다.

따라서 둘을 연결해야 진화 경로와 실제 포켓몬 정보를 같이 탐색할 수 있습니다.

## 6.1.8 Species - FROM -> Generation

### 목적

해당 종이 몇 세대에 등장했는지 나타냅니다.

### Source

`species.json`

### Direction

```text
(Species)-[:FROM]->(Generation)
```

### 사용 여부

초기에는 선택입니다.

하지만 강의 자료의 `Generation` 노드 구조와 비슷하게 가려면 추가하는 것이 좋습니다.

## 6.2 계산해서 만드는 파생 관계

이 섹션의 관계는 JSON에 직접 들어있지 않습니다.

`pokemon_types.json`과 `type_efficacy.json`를 조합해서 계산해야 합니다.

## 6.2.1 Pokemon - AGAINST -> Type

### 목적

특정 포켓몬이 특정 공격 타입에 몇 배 데미지를 받는지 나타냅니다.

강의 자료의 `AGAINST` 관계를 참고했습니다.

### Direction

```text
(Pokemon)-[:AGAINST]->(공격 Type)
```

### Properties

| property | 설명 |
| --- | --- |
| `multiplier` | 최종 데미지 배율 |

### 계산 방식

포켓몬이 타입을 하나만 가지면 해당 타입에 대한 공격 상성을 그대로 사용합니다.

포켓몬이 타입을 두 개 가지면 두 타입의 배율을 곱합니다.

예시:

```text
이상해씨 = 풀 + 독
불꽃 공격 -> 풀에게 2.0배
불꽃 공격 -> 독에게 1.0배
최종 multiplier = 2.0 * 1.0 = 2.0
```

### 팀 추천에서의 의미

팀의 약점을 계산하는 핵심 관계입니다.

예시:

```cypher
MATCH (p:Pokemon)-[a:AGAINST]->(t:Type)
WHERE p.pokemon_id IN [1, 4, 7, 25, 143]
RETURN t.name AS type, sum(a.multiplier) AS score
ORDER BY score DESC
```

`score`가 높을수록 팀 전체가 그 타입 공격에 약하다는 의미입니다.

### 배틀에서의 의미

공격 기술의 타입이 정해졌을 때, 방어 포켓몬이 몇 배 데미지를 받을지 빠르게 확인할 수 있습니다.

## 6.2.2 Pokemon - WEAK_AGAINST -> Type

### 목적

`AGAINST.multiplier`가 2.0 이상인 타입을 빠르게 찾기 위한 편의 관계입니다.

### Direction

```text
(Pokemon)-[:WEAK_AGAINST]->(Type)
```

### 생성 조건

```text
multiplier >= 2.0
```

### 사용 예시

```cypher
MATCH (p:Pokemon)-[:WEAK_AGAINST]->(t:Type)
WHERE p.name = "이상해씨"
RETURN t.name
```

## 6.2.3 Pokemon - VERY_WEAK_AGAINST -> Type

### 목적

4배 약점을 빠르게 찾기 위한 편의 관계입니다.

### Direction

```text
(Pokemon)-[:VERY_WEAK_AGAINST]->(Type)
```

### 생성 조건

```text
multiplier >= 4.0
```

### 사용 이유

4배 약점은 팀 추천과 배틀 모두에서 매우 큰 리스크입니다.

추천 점수 계산에서 강한 감점 요소로 사용할 수 있습니다.

## 6.2.4 Pokemon - NORMAL_VULNERABILITY_AGAINST -> Type

### 목적

1배 상성을 명시적으로 표현합니다.

### Direction

```text
(Pokemon)-[:NORMAL_VULNERABILITY_AGAINST]->(Type)
```

### 생성 조건

```text
multiplier == 1.0
```

### 사용 여부

초기에는 없어도 됩니다.

하지만 Neo4j Browser에서 전체 상성을 시각화하거나 강의 자료와 유사한 구조를 만들려면 추가할 수 있습니다.

## 6.2.5 Pokemon - RESISTANT_TO -> Type

### 목적

0.5배 저항 타입을 빠르게 찾기 위한 편의 관계입니다.

### Direction

```text
(Pokemon)-[:RESISTANT_TO]->(Type)
```

### 생성 조건

```text
multiplier == 0.5
```

### 팀 추천에서의 의미

현재 팀이 약한 타입에 저항하는 후보를 찾을 때 사용합니다.

예시:

```cypher
MATCH (candidate:Pokemon)-[:RESISTANT_TO]->(weakType:Type)
WHERE weakType.name IN ["얼음", "바위"]
RETURN candidate.name, candidate.base_total
ORDER BY candidate.base_total DESC
```

## 6.2.6 Pokemon - VERY_RESISTANT_TO -> Type

### 목적

0.25배 저항 타입을 빠르게 찾기 위한 편의 관계입니다.

### Direction

```text
(Pokemon)-[:VERY_RESISTANT_TO]->(Type)
```

### 생성 조건

```text
multiplier == 0.25
```

### 팀 추천에서의 의미

팀의 큰 약점을 강하게 보완하는 후보에게 높은 점수를 줄 때 사용합니다.

## 6.2.7 Pokemon - IMMUNE_TO -> Type

### 목적

0배 무효 타입을 빠르게 찾기 위한 편의 관계입니다.

### Direction

```text
(Pokemon)-[:IMMUNE_TO]->(Type)
```

### 생성 조건

```text
multiplier == 0.0
```

### 팀 추천에서의 의미

현재 팀이 특정 타입 공격에 약할 때, 해당 타입을 무효화하는 포켓몬은 매우 좋은 후보가 될 수 있습니다.

### 배틀에서의 의미

상대 기술이 완전히 무효인지 빠르게 판단할 수 있습니다.

## 6.3 아이템과 폼 변화 관계

아이템은 팀 추천 초기 단계에서는 덜 중요하지만, 배틀에서는 중요합니다.

특히 메가진화를 고려하면 `Item` 관계가 필요합니다.

## 6.3.1 Pokemon - CAN_MEGA_EVOLVE_TO -> Pokemon

### 목적

기본 포켓몬이 메가진화 폼으로 변할 수 있음을 나타냅니다.

### Direction

```text
(기본 Pokemon)-[:CAN_MEGA_EVOLVE_TO]->(메가진화 Pokemon)
```

### 사용 예시

```text
(리자몽)-[:CAN_MEGA_EVOLVE_TO]->(메가리자몽X)
```

### 데이터 주의점

현재 `evolutions.json`은 일반 진화 관계만 가지고 있을 가능성이 큽니다.

메가진화 관계는 `pokemon.json`의 폼 이름, PokeAPI species varieties, form 정보 등을 추가로 분석해야 합니다.

따라서 이 관계는 2단계에서 추가하는 것이 좋습니다.

## 6.3.2 Pokemon - MEGA_REQUIRES -> Item

### 목적

메가진화 폼이 어떤 아이템을 요구하는지 나타냅니다.

### Direction

```text
(메가진화 Pokemon)-[:MEGA_REQUIRES]->(Item)
```

### 사용 예시

```text
(메가리자몽X)-[:MEGA_REQUIRES]->(리자몽나이트X)
```

### 배틀에서의 의미

배틀에서 포켓몬이 메가진화 가능한지 확인하려면 아래를 확인해야 합니다.

| 조건 | 확인할 관계 |
| --- | --- |
| 기본 포켓몬이 메가진화 가능한가? | `CAN_MEGA_EVOLVE_TO` |
| 해당 메가진화에 필요한 아이템이 있는가? | `MEGA_REQUIRES` |
| 현재 팀 멤버가 그 아이템을 장착했는가? | `TeamMember - HOLDS -> Item` |

## 6.3.3 TeamMember - HOLDS -> Item

### 목적

실제 팀의 포켓몬이 어떤 아이템을 장착했는지 나타냅니다.

### Direction

```text
(TeamMember)-[:HOLDS]->(Item)
```

### 사용 시점

이 관계는 유저 팀 저장 기능이 생긴 뒤 추가합니다.

초기 정적 포켓몬 그래프에는 만들지 않습니다.

## 6.3.4 Species - EVOLUTION_REQUIRES -> Item

### 목적

일반 진화에 필요한 아이템을 명시적으로 연결합니다.

### Direction

```text
(Species)-[:EVOLUTION_REQUIRES]->(Item)
```

### Source

`evolutions.json`의 `trigger_item_id`

### 사용 예시

진화 경로를 시각화하거나, 특정 아이템으로 진화하는 포켓몬을 찾을 때 사용합니다.

## 6.4 팀 인스턴스 관계

초기에는 팀을 Graph DB에 저장하지 않고 API 요청의 `selected_pokemon_ids`로 분석해도 됩니다.

하지만 나중에 실제 유저 팀을 저장하려면 `Team`과 `TeamMember` 노드가 필요합니다.

## 6.4.1 Team 노드

### 목적

유저가 저장한 팀 하나를 나타냅니다.

### Properties

| property | 설명 |
| --- | --- |
| `team_id` | 팀 ID |
| `name` | 팀 이름 |
| `created_at` | 생성 시간 |

## 6.4.2 TeamMember 노드

### 목적

팀 안에 들어간 특정 포켓몬 인스턴스를 나타냅니다.

강의 자료의 `TeamMember` 개념을 참고했습니다.

`Pokemon`은 도감 데이터이고, `TeamMember`는 실제 팀에서 쓰는 한 칸입니다.

예를 들어 리자몽이라는 포켓몬은 하나지만, 팀 멤버 리자몽은 실제 기술 4개, 특성 1개, 아이템 1개를 가질 수 있습니다.

### Properties

| property | 설명 |
| --- | --- |
| `team_member_id` | 팀 멤버 ID |
| `nickname` | 별명 |
| `level` | 레벨 |
| `slot` | 팀 내 위치 |

## 6.4.3 Team - HAS_MEMBER -> TeamMember

### 목적

팀과 팀 멤버를 연결합니다.

### Direction

```text
(Team)-[:HAS_MEMBER]->(TeamMember)
```

## 6.4.4 TeamMember - IS_POKEMON -> Pokemon

### 목적

팀 멤버가 어떤 포켓몬인지 연결합니다.

### Direction

```text
(TeamMember)-[:IS_POKEMON]->(Pokemon)
```

## 6.4.5 TeamMember - KNOWS -> Move

### 목적

실제 팀 멤버가 선택한 기술 4개를 나타냅니다.

### Direction

```text
(TeamMember)-[:KNOWS]->(Move)
```

### `CAN_KNOW`와 차이

| 관계 | 의미 |
| --- | --- |
| `Pokemon - CAN_KNOW -> Move` | 이 포켓몬이 배울 수 있는 모든 기술 |
| `TeamMember - KNOWS -> Move` | 실제 팀에서 선택한 기술 |

## 6.4.6 TeamMember - HAS -> Ability

### 목적

실제 팀 멤버가 선택한 특성 하나를 나타냅니다.

### Direction

```text
(TeamMember)-[:HAS]->(Ability)
```

### `CAN_HAVE`와 차이

| 관계 | 의미 |
| --- | --- |
| `Pokemon - CAN_HAVE -> Ability` | 이 포켓몬이 가질 수 있는 모든 특성 |
| `TeamMember - HAS -> Ability` | 실제 팀에서 선택한 특성 |

## 6.4.7 TeamMember - HOLDS -> Item

### 목적

실제 팀 멤버가 장착한 아이템을 나타냅니다.

### Direction

```text
(TeamMember)-[:HOLDS]->(Item)
```

### 배틀에서의 의미

메가진화 가능 여부, 장착 아이템 효과, 배틀 중 소모 아이템 등을 판단할 때 사용합니다.

## 7. 팀 추천 기능 설계

팀 추천 기능은 처음부터 AI 모델로 복잡하게 만들기보다, 그래프 기반 점수 계산으로 시작하는 것이 좋습니다.

## 7.1 입력

초기 입력은 선택된 포켓몬 5마리의 ID입니다.

```json
{
  "selected_pokemon_ids": [1, 4, 7, 25, 143]
}
```

## 7.2 추천 후보 기본 조건

초기 추천 후보는 아래 조건을 사용합니다.

| 조건 | 이유 |
| --- | --- |
| `is_default = true` | 메가진화, 특수 폼을 추천 후보에서 제외 |
| 선택된 포켓몬 제외 | 이미 팀에 있는 포켓몬 중복 추천 방지 |
| `base_total` 존재 | 능력치 기반 점수 계산 |

예시:

```cypher
MATCH (candidate:Pokemon)
WHERE candidate.is_default = true
AND NOT candidate.pokemon_id IN $selected_pokemon_ids
RETURN candidate
```

## 7.3 팀 약점 분석

선택된 5마리의 `AGAINST` 관계를 합산합니다.

```cypher
MATCH (p:Pokemon)-[a:AGAINST]->(attackType:Type)
WHERE p.pokemon_id IN $selected_pokemon_ids
RETURN attackType.name AS type, sum(a.multiplier) AS weakness_score
ORDER BY weakness_score DESC
```

해석:

| 값 | 의미 |
| --- | --- |
| 점수가 높음 | 팀 전체가 해당 타입 공격에 약함 |
| 점수가 낮음 | 팀 전체가 해당 타입 공격에 강함 |

## 7.4 후보 방어 보완 점수

현재 팀이 약한 타입에 대해 후보가 저항하거나 무효화하면 점수를 줍니다.

예시:

```cypher
MATCH (candidate:Pokemon)-[r:RESISTANT_TO|VERY_RESISTANT_TO|IMMUNE_TO]->(weakType:Type)
WHERE weakType.name IN $team_weak_types
RETURN candidate.name, collect(weakType.name) AS covers
```

점수 예시:

| 관계 | 점수 |
| --- | --- |
| `IMMUNE_TO` | +4 |
| `VERY_RESISTANT_TO` | +3 |
| `RESISTANT_TO` | +2 |

## 7.5 후보 공격 커버리지 점수

후보가 배울 수 있는 기술 타입이 팀의 부족한 공격 타입을 보완하면 점수를 줍니다.

예시:

```cypher
MATCH (candidate:Pokemon)-[:CAN_KNOW]->(m:Move)-[:HAS_TYPE]->(moveType:Type)
WHERE moveType.name IN $needed_attack_types
RETURN candidate.name, collect(DISTINCT moveType.name) AS move_types
```

점수 예시:

| 조건 | 점수 |
| --- | --- |
| 부족한 공격 타입 기술을 배움 | +2 |
| 위력 있는 공격 기술을 배움 | +1 |
| status 기술만 있음 | +0.5 |

## 7.6 타입 중복 감점

이미 팀에 많은 타입과 후보 타입이 겹치면 감점합니다.

예시:

```cypher
MATCH (candidate:Pokemon)-[:HAS_TYPE]->(candidateType:Type)
WHERE candidate.pokemon_id = $candidate_id
RETURN collect(candidateType.name) AS candidate_types
```

감점 예시:

| 조건 | 감점 |
| --- | --- |
| 팀에 이미 같은 타입이 2마리 이상 | -1 |
| 팀에 이미 같은 타입이 3마리 이상 | -2 |

## 7.7 능력치 점수

`base_total`을 이용해 기본 능력치를 점수화합니다.

예시:

```text
stat_score = base_total / 100
```

## 7.8 최종 점수 예시

초기 버전에서는 아래처럼 단순한 계산부터 시작합니다.

```text
total_score =
  defense_score
  + coverage_score
  + stat_score
  - duplicate_penalty
```

## 7.9 추천 응답 예시

```json
{
  "recommended_pokemon": {
    "pokemon_id": 376,
    "name": "메타그로스"
  },
  "score": 12.5,
  "reason": [
    "현재 팀이 얼음 타입 공격에 약합니다.",
    "메타그로스는 얼음 타입 공격에 저항합니다.",
    "기본 능력치 총합이 높아 안정적인 후보입니다."
  ]
}
```

## 8. 배틀 기능 설계

배틀 기능은 단계적으로 구현하는 것이 좋습니다.

## 8.1 1단계 배틀

처음에는 타입 상성과 기본 능력치만 사용합니다.

포함:

| 항목 | 사용 여부 |
| --- | --- |
| 포켓몬 타입 | 사용 |
| 기술 타입 | 사용 |
| 기술 위력 | 사용 |
| 물리/특수 구분 | 사용 |
| 공격/방어/특공/특방 | 사용 |
| 특성 | 제외 |
| 아이템 | 제외 |
| 날씨/필드 | 제외 |
| 상태 이상 | 제외 |

## 8.2 2단계 배틀

특성과 아이템을 일부 반영합니다.

포함:

| 항목 | 설명 |
| --- | --- |
| `CAN_HAVE` | 가능한 특성 조회 |
| `TeamMember - HAS -> Ability` | 실제 선택 특성 |
| `TeamMember - HOLDS -> Item` | 실제 장착 아이템 |
| `CAN_MEGA_EVOLVE_TO` | 메가진화 가능 여부 |
| `MEGA_REQUIRES` | 필요한 메가스톤 확인 |

## 8.3 3단계 배틀

실전 배틀에 가까운 상태를 추가합니다.

추가 후보:

| 노드 또는 관계 | 설명 |
| --- | --- |
| `Battle` | 배틀 한 판 |
| `BattleSide` | 아군/상대 진영 |
| `BattleState` | 날씨, 필드, 턴 정보 |
| `StatusCondition` | 독, 마비, 화상 등 |
| `Weather` | 비, 쾌청, 모래바람 등 |
| `FieldEffect` | 일렉트릭필드 등 |

이 단계는 초기 구현 범위를 넘어갑니다.

## 9. 메가진화와 아이템 설계

사용자가 말한 것처럼, 메가진화를 배틀에서 다루려면 아이템 관계가 필요합니다.

## 9.1 팀 추천에서 메가진화 포켓몬 제외

팀 추천 후보에서는 메가진화 폼을 제외합니다.

가장 단순한 조건은 아래입니다.

```cypher
MATCH (p:Pokemon)
WHERE p.is_default = true
RETURN p
```

추가로 이름 패턴을 사용할 수도 있습니다.

```cypher
MATCH (p:Pokemon)
WHERE p.is_default = true
AND NOT toLower(p.name) CONTAINS "mega"
RETURN p
```

다만 한글 이름에서는 메가 표기가 어떻게 들어오는지 확인이 필요합니다.

## 9.2 배틀에서 메가진화 처리

배틀에서는 메가진화 폼을 사용할 수 있어야 합니다.

필요 관계:

```text
(기본 Pokemon)-[:CAN_MEGA_EVOLVE_TO]->(메가진화 Pokemon)
(메가진화 Pokemon)-[:MEGA_REQUIRES]->(Item)
(TeamMember)-[:HOLDS]->(Item)
```

확인 흐름:

1. 팀 멤버가 어떤 기본 포켓몬인지 확인합니다.
2. 해당 포켓몬이 `CAN_MEGA_EVOLVE_TO` 관계를 가지는지 확인합니다.
3. 메가진화 폼이 `MEGA_REQUIRES` 관계로 요구 아이템을 가지는지 확인합니다.
4. 팀 멤버가 `HOLDS` 관계로 해당 아이템을 가지고 있는지 확인합니다.
5. 조건을 만족하면 배틀 중 포켓몬을 메가진화 폼으로 변환합니다.

## 9.3 메가진화 데이터 수집 주의점

현재 `evolutions.json`은 일반 진화 체인을 기반으로 만들어진 데이터입니다.

메가진화는 일반 진화가 아니라 폼 변화에 가깝기 때문에, 아래 데이터가 추가로 필요할 수 있습니다.

| 필요 데이터 | 설명 |
| --- | --- |
| 기본 포켓몬 ID | 메가진화 전 포켓몬 |
| 메가진화 포켓몬 ID | 메가진화 후 폼 |
| 필요한 아이템 ID | 메가스톤 |
| 폼 이름 | mega-x, mega-y 등 구분 |

이 데이터는 PokeAPI의 species varieties, pokemon forms, item 정보 등을 추가로 분석해서 만들 수 있습니다.

## 10. 추천과 배틀에서 사용할 관계 구분

모든 관계를 모든 기능에서 똑같이 쓰지는 않습니다.

## 10.1 팀 추천에서 중요한 관계

| 관계 | 중요도 | 이유 |
| --- | --- | --- |
| `Pokemon - HAS_TYPE -> Type` | 매우 높음 | 타입 중복, 팀 구성 분석 |
| `Pokemon - AGAINST -> Type` | 매우 높음 | 팀 약점 계산 |
| `Pokemon - RESISTANT_TO -> Type` | 매우 높음 | 약점 보완 후보 찾기 |
| `Pokemon - IMMUNE_TO -> Type` | 높음 | 특정 타입 무효 후보 찾기 |
| `Pokemon - CAN_KNOW -> Move` | 높음 | 공격 커버리지 분석 |
| `Move - HAS_TYPE -> Type` | 높음 | 기술 타입 분석 |
| `Pokemon - CAN_HAVE -> Ability` | 낮음 | 초기에는 보조 정보 |
| `Species - EVOLVES_TO -> Species` | 낮음 | 초기 추천에는 직접 영향 적음 |
| `Item` 관련 관계 | 낮음 | 초기 추천에서는 제외 |

## 10.2 배틀에서 중요한 관계

| 관계 | 중요도 | 이유 |
| --- | --- | --- |
| `Pokemon - HAS_TYPE -> Type` | 매우 높음 | 방어 타입 계산 |
| `Move - HAS_TYPE -> Type` | 매우 높음 | 공격 기술 타입 계산 |
| `Type - ATTACK_EFFECTIVE -> Type` | 매우 높음 | 타입 상성 계산 |
| `Pokemon - AGAINST -> Type` | 높음 | 빠른 방어 배율 조회 |
| `Pokemon - CAN_KNOW -> Move` | 높음 | 사용 가능한 기술 후보 |
| `TeamMember - KNOWS -> Move` | 매우 높음 | 실제 선택 기술 |
| `Pokemon - CAN_HAVE -> Ability` | 중간 | 가능한 특성 |
| `TeamMember - HAS -> Ability` | 높음 | 실제 특성 |
| `TeamMember - HOLDS -> Item` | 높음 | 실제 장착 아이템 |
| `Pokemon - CAN_MEGA_EVOLVE_TO -> Pokemon` | 중간 | 메가진화 |
| `Pokemon - MEGA_REQUIRES -> Item` | 중간 | 메가진화 조건 |

## 11. 추천 구현 단계 계획

## 11.1 Graph DB 1차 구축

먼저 아래 파일을 만듭니다.

| 파일 | 목적 |
| --- | --- |
| `graph_schema.md` | 지금 보고 있는 설계 문서 |
| `constraints.cypher` | Neo4j 중복 방지 규칙 |
| `graph_loader.py` | JSON을 Neo4j에 적재하는 코드 |

## 11.2 1차 적재 대상

처음에는 아래 노드와 관계만 반드시 만듭니다.

필수 노드:

| 노드 | 이유 |
| --- | --- |
| `Pokemon` | 추천/배틀의 중심 |
| `Type` | 타입 상성 중심 |
| `Move` | 공격 커버리지와 배틀 기술 |
| `Ability` | 배틀 확장 |
| `Species` | 진화 관계 |
| `Item` | 진화 아이템, 메가진화 확장 |

필수 관계:

| 관계 | 이유 |
| --- | --- |
| `HAS_TYPE` | 포켓몬/기술 타입 |
| `CAN_KNOW` | 포켓몬이 배울 수 있는 기술 |
| `CAN_HAVE` | 포켓몬이 가질 수 있는 특성 |
| `ATTACK_EFFECTIVE` | 타입 간 상성 |
| `AGAINST` | 포켓몬별 방어 상성 |
| `RESISTANT_TO` | 추천 후보 보완 |
| `IMMUNE_TO` | 추천 후보 보완 |
| `WEAK_AGAINST` | 팀 약점 분석 |
| `EVOLVES_TO` | 진화 관계 |
| `IS_SPECIES` | Pokemon과 Species 연결 |

## 11.3 2차 확장 대상

다음 단계에서 추가합니다.

| 노드/관계 | 이유 |
| --- | --- |
| `Generation` | 세대 제한 추천 |
| `VERY_WEAK_AGAINST` | 4배 약점 분석 |
| `VERY_RESISTANT_TO` | 0.25배 저항 분석 |
| `NORMAL_VULNERABILITY_AGAINST` | 전체 상성 시각화 |
| `CAN_MEGA_EVOLVE_TO` | 메가진화 |
| `MEGA_REQUIRES` | 메가진화 아이템 |
| `EVOLUTION_REQUIRES` | 진화 아이템 |

## 11.4 3차 확장 대상

유저 팀 저장과 실제 배틀을 만들 때 추가합니다.

| 노드/관계 | 이유 |
| --- | --- |
| `Team` | 유저 팀 저장 |
| `TeamMember` | 실제 팀 멤버 인스턴스 |
| `HAS_MEMBER` | 팀과 멤버 연결 |
| `IS_POKEMON` | 팀 멤버와 도감 포켓몬 연결 |
| `KNOWS` | 실제 선택 기술 |
| `HAS` | 실제 선택 특성 |
| `HOLDS` | 실제 장착 아이템 |

## 12. Graph Loader 작성 계획

`graph_loader.py`는 강의에서 사용한 Neo4j 연결 방식과 비슷한 구조로 작성합니다.

예상 구조:

```text
1. Neo4j 연결 설정
2. JSON 파일 읽기 함수
3. constraints.cypher 실행 함수
4. Node 생성 함수
5. Relationship 생성 함수
6. AGAINST 파생 관계 계산 함수
7. 전체 실행 main 함수
```

함수 예시:

```text
load_json(filename)
create_pokemon_nodes(conn)
create_type_nodes(conn)
create_move_nodes(conn)
create_ability_nodes(conn)
create_item_nodes(conn)
create_has_type_relationships(conn)
create_can_know_relationships(conn)
create_type_efficacy_relationships(conn)
create_pokemon_defense_relationships(conn)
```

모든 함수에는 아래 주석을 달 예정입니다.

| 주석 내용 | 예시 |
| --- | --- |
| 함수 목적 | 이 함수는 Pokemon 노드를 생성하기 위해 작성함 |
| 변수 의미 | `pokemon_rows`는 JSON에서 읽은 포켓몬 목록 |
| 쿼리 의미 | `MERGE`는 같은 ID의 노드 중복 생성을 막음 |
| 관계 의미 | `HAS_TYPE`은 포켓몬과 타입을 연결함 |

## 13. Constraints 작성 계획

`constraints.cypher`에는 중복 방지를 위한 규칙을 작성합니다.

필수 제약조건:

```cypher
CREATE CONSTRAINT pokemon_id IF NOT EXISTS
FOR (p:Pokemon)
REQUIRE p.pokemon_id IS UNIQUE;

CREATE CONSTRAINT type_id IF NOT EXISTS
FOR (t:Type)
REQUIRE t.type_id IS UNIQUE;

CREATE CONSTRAINT move_id IF NOT EXISTS
FOR (m:Move)
REQUIRE m.move_id IS UNIQUE;

CREATE CONSTRAINT ability_id IF NOT EXISTS
FOR (a:Ability)
REQUIRE a.ability_id IS UNIQUE;

CREATE CONSTRAINT species_id IF NOT EXISTS
FOR (s:Species)
REQUIRE s.species_id IS UNIQUE;

CREATE CONSTRAINT item_id IF NOT EXISTS
FOR (i:Item)
REQUIRE i.item_id IS UNIQUE;
```

선택 인덱스:

```cypher
CREATE INDEX pokemon_name IF NOT EXISTS
FOR (p:Pokemon)
ON (p.name);

CREATE INDEX type_name IF NOT EXISTS
FOR (t:Type)
ON (t.name);

CREATE INDEX move_name IF NOT EXISTS
FOR (m:Move)
ON (m.name);
```

## 14. 최종 요약

이 Graph DB의 중심은 `Pokemon`, `Type`, `Move`입니다.

팀 추천은 아래 관계를 중심으로 구현합니다.

```text
Pokemon - HAS_TYPE -> Type
Pokemon - AGAINST -> Type
Pokemon - RESISTANT_TO -> Type
Pokemon - IMMUNE_TO -> Type
Pokemon - CAN_KNOW -> Move - HAS_TYPE -> Type
```

배틀은 아래 관계를 중심으로 구현합니다.

```text
Pokemon - HAS_TYPE -> Type
Move - HAS_TYPE -> Type
Type - ATTACK_EFFECTIVE -> Type
Pokemon - CAN_KNOW -> Move
Pokemon - CAN_HAVE -> Ability
TeamMember - KNOWS -> Move
TeamMember - HAS -> Ability
TeamMember - HOLDS -> Item
Pokemon - CAN_MEGA_EVOLVE_TO -> Pokemon
Pokemon - MEGA_REQUIRES -> Item
```

초기 구현에서는 정적 포켓몬 지식 그래프를 먼저 만들고, 팀 추천 API를 구현합니다.

배틀 기능에서는 처음에 타입과 능력치 중심으로 시작하고, 이후 아이템, 특성, 메가진화, 실제 팀 멤버 인스턴스를 추가합니다.
