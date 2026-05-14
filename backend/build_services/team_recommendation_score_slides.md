---
marp: true
theme: default
paginate: true
size: 16:9
---

# 팀 빌더 추천 점수 계산 설명

## Graph Score + Vector Score + Hybrid Score

이 문서는 팀 빌더가 6번째 포켓몬을 추천할 때  
점수가 어떤 기준으로 계산되는지 발표 자료처럼 이해하기 쉽게 정리한 문서입니다.

---

# 1. 추천 점수의 큰 흐름

팀 빌더 추천은 한 번에 점수를 바로 계산하지 않습니다.

1. 선택한 5마리의 팀 약점을 분석합니다.
2. 약점을 보완할 수 있는 후보 포켓몬을 Graph DB에서 찾습니다.
3. 후보별 Graph 점수를 계산합니다.
4. RAG 추천에서는 Vector 근거 점수를 추가합니다.
5. Graph 점수와 Vector 점수를 섞어 최종 Hybrid 점수를 만듭니다.

---

# 2. 추천 후보를 찾는 기준

후보는 아무 포켓몬이나 가져오지 않습니다.

현재 팀이 약한 공격 타입을 기준으로,  
그 타입을 저항하거나 무효화할 수 있는 포켓몬을 먼저 찾습니다.

```cypher
(candidate:Pokemon)-[:RESISTANT_TO|VERY_RESISTANT_TO|IMMUNE_TO]->(weakType:Type)
```

즉, 추천의 핵심 질문은 다음과 같습니다.

> "현재 팀이 약한 타입을 누가 대신 받아줄 수 있는가?"

---

# 3. Graph Score 공식

Graph Score는 Neo4j 관계와 포켓몬 속성으로 계산하는 기본 추천 점수입니다.

```text
graph_score =
    defensive_score
  + stat_score
  + coverage_score
  - duplicate_penalty
```

이 점수는 "현재 팀에 실제로 필요한 포켓몬인가?"를 판단하는 데 집중합니다.

---

# 4. Graph Score 세부 항목

| 항목 | 계산식 | 의미 |
| --- | --- | --- |
| defensive_score | 보완 약점 타입 수 * 25 | 팀 약점을 많이 막을수록 가산 |
| stat_score | min(base_total / 10, 70) | 기본 능력치가 높을수록 가산 |
| coverage_score | min(기술 타입 수 * 1.5, 20) | 배울 수 있는 기술 타입이 다양할수록 가산 |
| duplicate_penalty | 팀과 겹치는 타입 수 * 4 | 기존 팀 타입과 겹치면 감점 |

---

# 5. defensive_score

## 약점 보완 점수

현재 팀이 약한 타입을 후보 포켓몬이 얼마나 잘 받아줄 수 있는지 계산합니다.

```text
defensive_score = 보완 가능한 약점 타입 개수 * 25
```

예를 들어 후보가 `바위`, `얼음`, `전기`를 저항하거나 무효화하면:

```text
3개 * 25 = 75점
```

추천 로직에서 가장 중요한 점수입니다.

---

# 6. stat_score

## 기본 능력치 점수

포켓몬의 기본 능력치 합계인 `base_total`을 점수화합니다.

```text
stat_score = min(base_total / 10, 70)
```

예시:

```text
base_total = 600
600 / 10 = 60점
```

다만 너무 높은 종족값이 점수를 과도하게 지배하지 않도록 최대 70점으로 제한합니다.

---

# 7. coverage_score

## 기술 타입 커버리지 점수

후보 포켓몬이 배울 수 있는 기술 타입이 다양할수록 점수를 받습니다.

```text
coverage_score = min(기술 타입 수 * 1.5, 20)
```

예시:

```text
기술 타입 수 = 12개
12 * 1.5 = 18점
```

기술 타입이 많으면 상대 상황에 맞춰 대응할 수 있는 폭이 넓어집니다.

---

# 8. duplicate_penalty

## 타입 중복 감점

후보 포켓몬의 타입이 이미 팀에 많이 있는 타입과 겹치면 감점합니다.

```text
duplicate_penalty = 현재 팀과 겹치는 타입 수 * 4
```

예시:

```text
후보 타입이 팀 타입과 2개 겹침
2 * 4 = 8점 감점
```

이 감점은 팀 타입 다양성을 확보하기 위한 장치입니다.

---

# 9. Graph Score 계산 예시 1

## 후보 A

| 조건 | 값 |
| --- | --- |
| 보완 약점 타입 | 바위, 얼음, 전기 |
| base_total | 600 |
| 배울 수 있는 기술 타입 수 | 12 |
| 팀과 겹치는 타입 수 | 1 |

```text
defensive_score = 3 * 25 = 75
stat_score = min(600 / 10, 70) = 60
coverage_score = min(12 * 1.5, 20) = 18
duplicate_penalty = 1 * 4 = 4
graph_score = 75 + 60 + 18 - 4 = 149
```

---

# 10. Graph Score 계산 예시 2

## 후보 B

| 조건 | 값 |
| --- | --- |
| 보완 약점 타입 | 바위 |
| base_total | 680 |
| 배울 수 있는 기술 타입 수 | 16 |
| 팀과 겹치는 타입 수 | 3 |

```text
defensive_score = 1 * 25 = 25
stat_score = min(680 / 10, 70) = 68
coverage_score = min(16 * 1.5, 20) = 20
duplicate_penalty = 3 * 4 = 12
graph_score = 25 + 68 + 20 - 12 = 101
```

후보 B는 능력치는 높지만, 팀 약점 보완이 적어서 후보 A보다 낮습니다.

---

# 11. Vector Score

Vector Score는 RAG에서 사용하는 보조 점수입니다.

후보 포켓몬의 이름, 타입, 보완 타입, 대표 기술명이  
검색된 문서 근거와 얼마나 잘 맞는지 확인합니다.

```text
vector_score = 검색 문서 상위 3개의 유사도 평균을 0~100 기준으로 정규화
```

문서 근거가 없거나 관련성이 낮으면 Vector Score는 낮게 나옵니다.

---

# 12. Hybrid Score

RAG 추천의 최종 순위는 Hybrid Score를 기준으로 정렬합니다.

현재 추천 가중치는 다음과 같습니다.

```text
Graph DB : Vector DB = 7 : 3
```

공식은 다음과 같습니다.

```text
hybrid_score = graph_score * 0.7 + vector_score * 0.3
```

---

# 13. Hybrid Score 계산 예시 1

## 후보 A

```text
graph_score = 149
vector_score = 76
```

```text
hybrid_score = 149 * 0.7 + 76 * 0.3
             = 104.3 + 22.8
             = 127.1
```

Graph 점수가 높고 Vector 근거도 충분해서 최종 점수가 높습니다.

---

# 14. Hybrid Score 계산 예시 2

## 후보 B

```text
graph_score = 101
vector_score = 20
```

```text
hybrid_score = 101 * 0.7 + 20 * 0.3
             = 70.7 + 6
             = 76.7
```

능력치는 높지만 약점 보완과 문서 근거가 부족해 최종 점수가 낮아집니다.

---

# 15. 최종 정리

팀 빌더 추천 점수는 단순히 강한 포켓몬을 고르는 방식이 아닙니다.

가장 중요한 기준은 다음 세 가지입니다.

1. 현재 팀의 약점을 얼마나 잘 보완하는가
2. 기본 능력치와 기술 폭이 충분한가
3. RAG 문서 근거에서도 추천 이유가 뒷받침되는가

따라서 추천 결과는  
**강한 포켓몬**보다 **현재 팀에 필요한 포켓몬**을 우선합니다.

---

# 16. 관련 코드 위치

| 목적 | 파일 |
| --- | --- |
| Graph 추천 점수 계산 | `backend/build_services/team_builder_service.py` |
| 추천 후보 조회 Cypher | `backend/graph/queries.py` |
| Vector 점수 계산 | `backend/team_build_rag/vector_scorer.py` |
| Hybrid 점수 계산 | `backend/team_build_rag/hybrid_scorer.py` |
| 가중치 정책 | `backend/team_build_rag/scoring_policy.py` |

이 문서는 위 코드들의 점수 계산 방식을 발표 자료 형태로 요약한 문서입니다.

