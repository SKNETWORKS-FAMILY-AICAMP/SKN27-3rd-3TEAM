---
marp: true
theme: default
paginate: true
size: 16:9
---

<style>
section {
  font-size: 22px;
  line-height: 1.45;
  padding: 38px 52px;
}

h1 {
  font-size: 34px;
  margin-bottom: 18px;
}

h2 {
  font-size: 26px;
  margin-top: 8px;
  margin-bottom: 14px;
}

p,
li {
  font-size: 22px;
}

table {
  font-size: 18px;
}

pre,
code {
  font-size: 18px;
}

blockquote {
  font-size: 21px;
}
</style>

# Pokemon Graph DB 설계 설명

## 실제 생성된 6개 노드와 13개 관계 기준

이 자료는 Neo4j Browser에 실제로 생성된 그래프 구조를 기준으로 정리했습니다.

생성된 노드는 6개입니다.

`Pokemon`, `Type`, `Move`, `Ability`, `Item`, `Generation`

생성된 관계는 13개입니다.

`HAS_TYPE`, `CAN_KNOW`, `CAN_HAVE`, `FROM`, `EVOLVES_TO`,  
`ATTACK_EFFECTIVE`, `AGAINST`, `WEAK_AGAINST`, `VERY_WEAK_AGAINST`,  
`NORMAL_VULNERABILITY_AGAINST`, `RESISTANT_TO`, `VERY_RESISTANT_TO`, `IMMUNE_TO`

---

# 1. Graph DB를 설계한 이유

포켓몬 팀 빌딩은 단순 조회보다 관계 탐색이 중요합니다.

예를 들어 사용자는 이런 질문을 하게 됩니다.

1. 이 포켓몬은 어떤 타입인가?
2. 이 팀은 어떤 공격 타입에 약한가?
3. 그 약점을 누가 저항하거나 무효화할 수 있는가?
4. 후보 포켓몬은 어떤 기술을 배울 수 있는가?
5. 진화 흐름은 어떻게 이어지는가?

그래서 Graph DB는 포켓몬 데이터를 저장하는 목적보다  
**팀 분석과 추천에 필요한 관계를 빠르게 따라가기 위한 구조**로 설계했습니다.

---

# 2. 전체 구조

현재 그래프는 포켓몬 팀 빌딩에 필요한 핵심만 남긴 구조입니다.

| 구분 | 노드/관계 | 설계 목적 |
| --- | --- | --- |
| 기본 정보 | `Pokemon`, `Type`, `Move`, `Ability`, `Item`, `Generation` | 포켓몬 도감과 추천 후보의 기본 단위 |
| 소유 관계 | `HAS_TYPE`, `CAN_KNOW`, `CAN_HAVE`, `FROM` | 포켓몬이 가진 타입, 기술, 특성, 세대 연결 |
| 진화 관계 | `EVOLVES_TO` | 일반 진화와 폼 분기 표현 |
| 타입 상성 | `ATTACK_EFFECTIVE`, `AGAINST` 계열 | 팀 약점 분석과 방어 보완 후보 탐색 |

핵심은 `Pokemon`을 중심에 두고,  
타입 상성, 기술, 특성, 진화를 주변 관계로 연결하는 것입니다.

---

# 3. `Pokemon` 노드

`Pokemon`은 그래프의 중심 노드입니다.

팀 빌딩에서 사용자가 실제로 선택하는 대상이 포켓몬이기 때문에,  
모든 추천과 분석은 `Pokemon`을 기준으로 시작합니다.

주요 속성은 다음과 같습니다.

| 속성 | 사용 이유 |
| --- | --- |
| `pokemon_id` | 포켓몬 고유 식별자 |
| `name` | 화면 표시와 검색 |
| `is_default` | 기본 폼 추천 후보 필터링 |
| `species_id` | 진화와 폼 분기 연결 |
| `base_total` | 추천 점수의 능력치 보조 기준 |

---

# 4. `Type` 노드

`Type`은 포켓몬 타입과 기술 타입을 함께 표현합니다.

예를 들어 `불꽃` 타입은 두 의미로 쓰입니다.

1. 리자몽이 가진 방어 타입
2. 화염방사가 가진 공격 타입

그래서 타입을 문자열 속성으로만 두지 않고,  
별도 노드로 만들어 여러 관계가 공유하게 했습니다.

이 구조 덕분에 방어 상성과 기술 커버리지를  
같은 타입 기준으로 계산할 수 있습니다.

---

# 5. `Move` 노드

`Move`는 포켓몬이 배울 수 있는 기술입니다.

추천에서는 후보 포켓몬이 단순히 약점만 막는지보다,  
어떤 공격 선택지를 가질 수 있는지도 중요합니다.

그래서 기술을 별도 노드로 두고,  
포켓몬과 `CAN_KNOW` 관계로 연결했습니다.

또한 기술은 `HAS_TYPE`으로 타입과 연결됩니다.

```cypher
(Pokemon)-[:CAN_KNOW]->(Move)-[:HAS_TYPE]->(Type)
```

이 흐름으로 후보의 기술 타입 커버리지를 계산합니다.

---

# 6. `Ability` 노드

`Ability`는 포켓몬의 특성입니다.

특성은 포켓몬의 역할을 설명하는 중요한 정보입니다.

예를 들어 어떤 포켓몬은 방어적으로 쓰기 좋고,  
어떤 포켓몬은 공격 보조나 상태 이상 대응에 의미가 있습니다.

그래서 특성을 `Pokemon`의 단순 텍스트 속성으로 넣지 않고,  
`Ability` 노드로 분리했습니다.

```cypher
(Pokemon)-[:CAN_HAVE]->(Ability)
```

---

# 7. `Item` 노드

`Item`은 아이템 정보를 나타냅니다.

현재 팀 추천의 핵심 쿼리에서 가장 많이 쓰는 노드는 아니지만,  
포켓몬 데이터에서 아이템 효과를 별도 엔티티로 관리하기 위해 생성했습니다.

아이템을 노드로 두면 다음 확장이 가능합니다.

1. 진화 아이템 정보와 연결
2. 배틀 아이템 효과 설명
3. 추천/배틀 시스템에서 아이템 조건 추가

즉, `Item`은 현재 구조에서 확장 가능한 보조 노드입니다.

---

# 8. `Generation` 노드

`Generation`은 포켓몬이 등장한 세대를 나타냅니다.

```cypher
(Pokemon)-[:FROM]->(Generation)
```

세대 정보는 타입 상성 계산의 핵심은 아니지만,  
포켓몬을 세대별로 설명하거나 필터링할 때 유용합니다.

포켓몬 도감 데이터의 출처와 범위를 이해하기 위해  
별도 노드로 분리했습니다.

---

# 9. `HAS_TYPE` 관계

`HAS_TYPE`은 두 종류의 연결에 사용됩니다.

| 방향 | 의미 |
| --- | --- |
| `Pokemon -> Type` | 포켓몬의 타입 |
| `Move -> Type` | 기술의 타입 |

현재 DB 기준으로는 `Pokemon -> Type` 관계가 2,093개,  
`Move -> Type` 관계가 919개 생성되어 있습니다.

같은 관계 이름을 사용한 이유는  
둘 다 "이 대상이 어떤 타입을 가지는가"를 뜻하기 때문입니다.

포켓몬 타입은 방어 상성 계산에 쓰이고,  
기술 타입은 공격 커버리지 계산에 쓰입니다.

---

# 10. `CAN_KNOW` 관계

`CAN_KNOW`는 포켓몬이 배울 수 있는 기술을 연결합니다.

```cypher
(Pokemon)-[:CAN_KNOW]->(Move)
```

이 관계가 필요한 이유는 추천 후보의 공격 선택지를 보기 위해서입니다.

예를 들어 어떤 후보가 팀 약점을 잘 막더라도,  
배울 수 있는 기술 타입이 너무 좁으면 추천 가치가 낮아질 수 있습니다.

그래서 추천 점수에서 기술 폭을 계산할 때  
`CAN_KNOW -> Move -> HAS_TYPE -> Type` 흐름을 사용합니다.

---

# 11. `CAN_HAVE` 관계

`CAN_HAVE`는 포켓몬이 가질 수 있는 특성을 연결합니다.

```cypher
(Pokemon)-[:CAN_HAVE]->(Ability)
```

주요 속성은 다음과 같습니다.

| 속성 | 의미 |
| --- | --- |
| `slot` | 특성 슬롯 |
| `is_hidden` | 숨겨진 특성 여부 |

이 관계는 포켓몬의 전투 역할을 설명하거나,  
특성 기반 필터링을 확장할 때 사용할 수 있습니다.

---

# 12. `FROM` 관계

`FROM`은 포켓몬과 등장 세대를 연결합니다.

```cypher
(Pokemon)-[:FROM]->(Generation)
```

이 관계는 다음 목적을 가집니다.

1. 포켓몬이 어느 세대에 등장했는지 표시
2. 세대별 포켓몬 검색 지원
3. 도감 데이터의 범위 설명

추천의 핵심 점수보다  
서비스 설명과 필터링에 가까운 보조 관계입니다.

---

# 13. `EVOLVES_TO` 관계

`EVOLVES_TO`는 포켓몬 간 진화 흐름을 연결합니다.

```cypher
(Pokemon)-[:EVOLVES_TO]->(Pokemon)
```

일반 진화는 기본 폼끼리 연결합니다.

```text
파이리 -> 리자드 -> 리자몽
```

폼 분기는 최종 대표 포켓몬에서 갈라지도록 연결합니다.

```text
리자몽 -> 메가 리자몽 X
리자몽 -> 메가 리자몽 Y
리자몽 -> 거다이맥스 리자몽
```

---

# 14. 왜 `EVOLVES_TO`를 이렇게 만들었는가

진화 데이터는 species 기준으로 제공됩니다.

하지만 사용자가 보는 것은 species가 아니라  
실제 포켓몬과 폼입니다.

단순히 species만 기준으로 연결하면  
`리자드 -> 메가 리자몽 X`처럼 어색한 관계가 생길 수 있습니다.

그래서 일반 진화는 기본 폼끼리 연결하고,  
메가진화나 거다이맥스 같은 폼은 최종 진화체에서 분기되게 했습니다.

이 방식이 사용자가 이해하는 진화 흐름과 가장 가깝습니다.

---

# 15. `ATTACK_EFFECTIVE` 관계

`ATTACK_EFFECTIVE`는 타입 대 타입의 기본 공격 상성입니다.

```cypher
(공격 Type)-[:ATTACK_EFFECTIVE]->(방어 Type)
```

예를 들어 불꽃 타입이 풀 타입에 2배라면  
이 관계의 `damage_factor`가 `2.0`입니다.

이 관계는 포켓몬 복합 타입까지 계산하기 전의  
원본 타입 상성표 역할을 합니다.

즉, `Type -> Type` 관계는 기본 상성 계산의 출발점입니다.

---

# 16. `AGAINST` 관계

`AGAINST`는 공격 타입이 특정 포켓몬에게 주는 최종 배율입니다.

```cypher
(공격 Type)-[:AGAINST]->(Pokemon)
```

예를 들어 이상해씨는 풀/독 타입입니다.

어떤 공격 타입이 들어오면  
풀 타입 상성과 독 타입 상성을 곱해서 최종 배율을 계산합니다.

이 결과를 미리 `AGAINST.multiplier`에 저장했습니다.

---

# 17. 왜 `AGAINST`를 미리 만들었는가

팀 분석에서는 선택된 5마리에 대해  
모든 공격 타입의 방어 배율을 계속 확인해야 합니다.

매번 다음 과정을 반복하면 비효율적입니다.

1. 포켓몬 타입 조회
2. 각 타입의 상성 조회
3. 복합 타입 배율 곱셈
4. 팀 단위 합산

그래서 최종 방어 배율을 미리 관계로 저장했습니다.

덕분에 팀 약점 분석은 `AGAINST.multiplier`를 합산하는 문제로 단순해집니다.

---

# 18. 방어 상성 파생 관계

`AGAINST`의 `multiplier` 값에 따라  
방어 상성을 더 읽기 쉬운 관계로 나누었습니다.

| 관계 | 조건 | 의미 |
| --- | --- | --- |
| `VERY_WEAK_AGAINST` | 4배 이상 | 매우 큰 약점 |
| `WEAK_AGAINST` | 1배 초과 | 약점 |
| `NORMAL_VULNERABILITY_AGAINST` | 1배 | 보통 |
| `RESISTANT_TO` | 0~1배 | 저항 |
| `VERY_RESISTANT_TO` | 0.25배 이하 | 강한 저항 |
| `IMMUNE_TO` | 0배 | 무효 |

이 관계들은 추천 쿼리를 더 직관적으로 만듭니다.

---

# 19. 방어 관계 방향을 `Type -> Pokemon`으로 둔 이유

방어 상성 관계는 공격 타입에서 방어 포켓몬으로 향합니다.

```cypher
(Type)-[:AGAINST]->(Pokemon)
```

이 방향을 선택한 이유는 팀 추천의 질문이  
공격 타입에서 시작하기 때문입니다.

예를 들어 팀이 바위 타입에 약하다면 질문은 다음과 같습니다.

> 바위 공격을 잘 받아줄 포켓몬은 누구인가?

그래서 `Type -> Pokemon` 방향이  
약점 보완 후보를 찾기에 더 자연스럽습니다.

---

# 20. 팀 약점 분석에서의 사용

선택된 5마리의 팀 약점은  
공격 타입별 `AGAINST.multiplier`를 합산해서 계산합니다.

```cypher
MATCH (attackType:Type)-[a:AGAINST]->(p:Pokemon)
WHERE p.pokemon_id IN $selected_pokemon_ids
RETURN attackType.name AS type_name,
       sum(a.multiplier) AS weakness_score,
       avg(a.multiplier) AS average_multiplier
ORDER BY weakness_score DESC
```

즉, 팀 약점 분석은  
타입별 방어 배율 합산 문제로 바뀝니다.

---

# 21. 추천 후보 탐색에서의 사용

추천은 팀의 약점 타입을 기준으로 시작합니다.

```cypher
MATCH (weakType:Type)
      -[r:RESISTANT_TO|VERY_RESISTANT_TO|IMMUNE_TO]
      ->(candidate:Pokemon)
```

이 쿼리는 다음 질문에 답합니다.

> 현재 팀이 약한 공격 타입을 저항하거나 무효화할 수 있는 포켓몬은 누구인가?

추천은 여기서 후보를 찾고,  
능력치와 기술 커버리지를 추가로 반영합니다.

---

# 22. 공격 커버리지에서의 사용

후보 포켓몬의 공격 선택지는  
`CAN_KNOW`와 `HAS_TYPE`을 따라가며 확인합니다.

```cypher
MATCH (candidate:Pokemon)
      -[:CAN_KNOW]->(move:Move)
      -[:HAS_TYPE]->(moveType:Type)
```

이 흐름으로 후보가 배울 수 있는 기술 타입을 모읍니다.

추천에서는 방어 보완뿐 아니라  
다양한 기술 타입을 사용할 수 있는지도 함께 봅니다.

---

# 23. 배틀 방어 배율 조회에서의 사용

배틀 중 특정 공격 타입이  
특정 포켓몬에게 몇 배로 들어가는지도 바로 조회할 수 있습니다.

```cypher
MATCH (attackType:Type)-[a:AGAINST]->(defender:Pokemon)
WHERE defender.pokemon_id = $defender_pokemon_id
AND attackType.type_id = $attack_type_id
RETURN a.multiplier AS multiplier
```

복합 타입 계산 결과가 이미 관계에 있기 때문에,  
배틀 로직에서도 빠르게 방어 배율을 가져올 수 있습니다.

---

# 24. 최종 정리

현재 Graph DB는 6개 노드와 13개 관계로 구성됩니다.

| 구분 | 핵심 |
| --- | --- |
| 중심 노드 | `Pokemon` |
| 타입 기준 | `Type` |
| 선택지 | `Move`, `Ability`, `Item`, `Generation` |
| 기본 관계 | `HAS_TYPE`, `CAN_KNOW`, `CAN_HAVE`, `FROM`, `EVOLVES_TO` |
| 상성 관계 | `ATTACK_EFFECTIVE`, `AGAINST` 계열 |

결론적으로 이 그래프는  
**현재 팀의 약점을 찾고, 그 약점을 보완할 포켓몬을 설명 가능하게 추천하기 위한 구조**입니다.

---

# 25. 관련 코드 위치

| 목적 | 파일 |
| --- | --- |
| Graph 적재 로더 | `database/graph/graph_loader.py` |
| Graph 스키마 문서 | `database/graph/graph_schema.md` |
| 제약 조건/인덱스 | `database/graph/constraints.cypher` |
| 추천/분석 Cypher | `backend/graph/queries.py` |
| 팀 분석 서비스 | `backend/build_services/team_analysis_service.py` |
| 팀 추천 서비스 | `backend/build_services/team_builder_service.py` |

이 문서는 실제 생성된 노드와 관계만 기준으로  
Graph DB 설계 의도를 발표용으로 정리한 자료입니다.
