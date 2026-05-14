# Team Builder Build Services 설명서

이 문서는 `backend/build_services` 안에서 팀 빌딩 기능에 직접 연결되는 서비스 파일 5개를 설명합니다.

팀 빌더는 크게 두 층으로 나뉩니다.

- `backend/build_services`: Graph DB 조회, 팀 분석, 추천 후보 계산처럼 **결정론적인 서비스 로직**을 담당합니다.
- `backend/team_build_rag`: Vector Search, Hybrid Score, Prompt, LLM 해설처럼 **RAG 기반 설명 생성 로직**을 담당합니다.

> `team_recommendation_score_slides.md`는 추천 점수 설명용 문서이며, 런타임 서비스 파일에는 포함하지 않습니다.

---

## 1. 전체 위치

```text
backend/
  build_services/
    team_analysis_service.py
    team_builder_service.py
    team_insight_service.py
    team_rag_service.py
    team_score_service.py

  team_build_rag/
    graph_tools.py
    vector_search.py
    vector_scorer.py
    hybrid_scorer.py
    scoring_policy.py
    answer_generator.py
    workflow.py
```

---

## 2. 서비스 파일 요약

| 파일 | 핵심 역할 | 주요 사용 위치 |
|---|---|---|
| `team_analysis_service.py` | 선택한 5마리 팀의 약점, 저항, 타입 분포, 기술 타입 커버리지 분석 | 덱 분석, RAG 분석 |
| `team_score_service.py` | 타입 상성 결과를 화면에 보여주기 좋은 점수/등급/문장으로 변환 | 덱 분석 결과 카드 |
| `team_insight_service.py` | 분석 결과를 바탕으로 팀 성향, 핵심 위험, 강점, 추천 방향 생성 | 덱 분석 요약 |
| `team_builder_service.py` | 6번째 포켓몬 추천 후보를 Graph DB 기반으로 계산 | 추천 후보 산출 |
| `team_rag_service.py` | LangGraph Hybrid RAG 워크플로우 실행 래퍼 | RAG 분석, RAG 추천 |

---

## 3. 요청 흐름

### 3.1 덱 분석 흐름

```text
frontend/pages/teambuilding.py
  -> backend/routers/team_builder.py
  -> backend/build_services/team_rag_service.py
  -> backend/team_build_rag/workflow.py
  -> graph_tools.py
  -> team_analysis_service.py
  -> vector_search.py
  -> hybrid_scorer.py
  -> answer_generator.py
```

덱 분석은 선택한 5마리의 방어 상성, 기술 타입 커버리지, 팀 타입 중복을 계산하고, 그 결과를 RAG 해설로 정리합니다.

### 3.2 추천 흐름

```text
frontend/pages/teambuilding.py
  -> backend/routers/team_builder.py
  -> backend/build_services/team_rag_service.py
  -> backend/team_build_rag/workflow.py
  -> graph_tools.py
  -> team_builder_service.py
  -> vector_search.py
  -> hybrid_scorer.py
  -> answer_generator.py
```

추천은 현재 팀의 약점을 보완할 수 있는 후보를 Graph DB에서 계산한 뒤, Vector DB 근거와 결합하여 최종 추천 이유를 생성합니다.

---

## 4. 파일별 상세 설명

## 4.1 `team_analysis_service.py`

선택한 5마리 포켓몬을 기준으로 팀 전체를 분석하는 서비스입니다.

### 주요 책임

- 포켓몬 ID 5개가 유효한지 검증합니다.
- 선택한 포켓몬의 이름, 이미지, 타입, 기본 능력치를 조회합니다.
- 팀이 어떤 공격 타입에 약한지 계산합니다.
- 팀이 어떤 공격 타입을 안정적으로 받아낼 수 있는지 계산합니다.
- 팀이 보유한 기술 타입 커버리지를 계산합니다.
- 분석 결과를 `team_insight_service.py`와 연결하여 요약 인사이트를 만듭니다.

### 주요 함수

| 함수 | 설명 |
|---|---|
| `_validate_team_size` | 선택 포켓몬 수가 5마리인지, 중복이 없는지 검증 |
| `analyze_team` | 덱 분석의 메인 함수 |

### 반환 데이터 예시

```json
{
  "selected_pokemon": [],
  "weak_types": [],
  "resistant_types": [],
  "neutral_types": [],
  "team_type_distribution": [],
  "move_type_coverage": [],
  "insights": {}
}
```

---

## 4.2 `team_score_service.py`

타입 상성 결과를 화면에 표시하기 좋은 형태로 가공하는 서비스입니다.

### 주요 책임

- 평균 데미지 배율을 기준으로 위험도/안정도를 계산합니다.
- 화면에서 사용할 점수, 등급, 설명 문장을 만듭니다.
- 덱 분석 화면의 `주의할 약점 타입`, `방어가 좋은 타입` 카드에 들어가는 데이터를 구성합니다.

### 주의할 점

`team_score_service.py`의 점수는 **덱 분석 표시용 점수**입니다.

추천 후보 순위를 결정하는 `graph_score`와는 목적이 다릅니다.

```text
team_score_service.py
  -> 분석 화면에서 타입 위험도를 이해하기 쉽게 보여주는 점수

team_builder_service.py
  -> 추천 후보의 순위를 계산하는 graph_score
```

---

## 4.3 `team_insight_service.py`

분석 결과를 사람이 읽기 좋은 팀 해석으로 바꾸는 서비스입니다.

### 주요 책임

- 팀의 대표 성향을 만듭니다.
- 핵심 위험 타입을 요약합니다.
- 방어적으로 안정적인 타입을 요약합니다.
- 6번째 포켓몬 추천 방향을 만듭니다.

### 생성되는 인사이트

| 항목 | 설명 |
|---|---|
| `team_identity` | 현재 팀을 한 문장으로 요약 |
| `risk_summary` | 가장 조심해야 할 약점 |
| `strength_summary` | 안정적으로 받아낼 수 있는 타입 |
| `recommendation_direction` | 6번째 포켓몬이 보완해야 할 방향 |

이 서비스는 LLM을 호출하지 않습니다. Graph DB 분석 결과를 규칙 기반으로 정리합니다.

---

## 4.4 `team_builder_service.py`

6번째 포켓몬 추천 후보를 계산하는 핵심 서비스입니다.

### 주요 책임

- 현재 팀의 약점 타입을 가져옵니다.
- 해당 약점 타입을 저항하거나 무효화할 수 있는 후보를 찾습니다.
- 후보의 능력치, 기술 타입 다양성, 현재 팀과의 타입 중복을 반영해 `graph_score`를 계산합니다.
- 추천 후보별 근거 문장을 생성합니다.

### Graph Score 구성

현재 추천 후보의 원본 `graph_score`는 다음 항목을 합산해 계산합니다.

| 항목 | 계산 방식 | 최대/범위 | 의미 |
|---|---:|---:|---|
| `defensive_score` | `min(보완 약점 수, 5) * 25` | 최대 125 | 팀 약점을 얼마나 많이 막는지 |
| `stat_score` | `min(base_total / 140, 5)` | 최대 5 | 기본 능력치 보정 |
| `coverage_score` | `min(기술 타입 수 * 1.5, 20)` | 최대 20 | 배울 수 있는 기술 타입 폭 |
| `duplicate_penalty` | `min(겹치는 타입 수 * 20, 40)` | 최대 -40 | 기존 팀과 타입이 겹칠 때 감점 |

설계상 감점 전 최대 점수는 다음과 같습니다.

```text
graph_score 최대값 = defensive_score 125 + stat_score 5 + coverage_score 20
                 = 150점
```

### 점수 설계 의도

- 추천의 핵심은 6번째 포켓몬이 팀 약점을 보완하는 것이므로 `defensive_score`의 비중을 가장 크게 둡니다.
- `stat_score`는 강한 포켓몬을 약간 우대하되, 약점 보완보다 앞서지 않도록 최대 5점으로 제한합니다.
- `coverage_score`는 기술 선택 폭을 반영하지만, 단순히 기술 타입이 많은 포켓몬이 압도하지 않도록 최대 20점으로 제한합니다.
- `duplicate_penalty`는 팀 타입 다양성을 확보하기 위한 감점이며, 지나친 감점을 막기 위해 최대 40점으로 제한합니다.

---

## 4.5 `team_rag_service.py`

팀 빌더 RAG 워크플로우를 실행하는 서비스입니다.

### 주요 책임

- API 요청 데이터를 LangGraph 워크플로우 입력 형태로 변환합니다.
- `hybrid_rag_app.invoke()`를 호출합니다.
- 응답에서 DB 연결 객체처럼 직렬화할 수 없는 값을 제거합니다.
- 라우터가 그대로 반환할 수 있는 JSON 결과를 만듭니다.

### 실행 흐름

```text
team_rag_service.run_team_rag
  -> workflow.hybrid_rag_app.invoke
  -> supervisor
  -> select_graph_tool
  -> execution_graph_tool
  -> vector_search
  -> evaluate_with_llm
  -> hybrid_scorer
  -> answer_generator
```

---

## 5. 점수 정책 위치

점수 가중치와 정규화 정책은 `build_services`가 아니라 `team_build_rag` 쪽에 있습니다.

| 파일 | 역할 |
|---|---|
| `backend/team_build_rag/scoring_policy.py` | 분석/추천/답변 생성의 Graph DB와 Vector DB 가중치 정의 |
| `backend/team_build_rag/hybrid_scorer.py` | Graph Score 정규화 및 Hybrid Score 계산 |

현재 기준은 다음과 같습니다.

| 목적 | Graph DB | Vector DB | 의미 |
|---|---:|---:|---|
| 덱 분석 계산 | 70% | 30% | 타입 상성 계산을 중심으로 하되 문서 근거를 보조 반영 |
| 추천 순위 계산 | 80% | 20% | 추천 순위는 Graph DB 계산 결과를 더 강하게 신뢰 |
| LLM 해설 생성 | 60% | 40% | 계산 근거를 우선하되 설명 품질을 위해 문서 근거도 충분히 반영 |

### Graph Score 정규화

추천 후보의 원본 `graph_score`는 최대 150점 설계를 기준으로 0~100점으로 정규화됩니다.

```text
normalized_graph_score = min(graph_score, 150) / 150 * 100
```

정규화된 Graph Score와 Vector Score를 가중합하여 최종 `hybrid_score`를 계산합니다.

```text
hybrid_score = normalized_graph_score * graph_weight
             + vector_score * vector_weight
```

---

## 6. 서비스와 RAG의 책임 분리

| 구분 | 담당 폴더 | 책임 |
|---|---|---|
| 팀 분석 계산 | `backend/build_services` | Neo4j 기반 타입 상성, 기술 커버리지, 팀 성향 계산 |
| 추천 후보 계산 | `backend/build_services` | 후보 탐색, 원본 graph_score 계산 |
| Vector 검색 | `backend/team_build_rag` | pgvector 기반 문서 근거 검색 |
| Hybrid 점수 | `backend/team_build_rag` | Graph Score와 Vector Score 결합 |
| AI 해설 | `backend/team_build_rag` | Prompt 구성 및 LLM 호출 |

이렇게 분리한 이유는 계산 로직과 설명 생성 로직의 변경 주기가 다르기 때문입니다.

- Graph DB 계산 로직은 추천 정확도에 직접 영향을 줍니다.
- Vector/RAG 로직은 설명 품질과 근거 표현에 영향을 줍니다.
- 두 영역을 분리하면 점수 정책, 프롬프트, 모델 교체를 비교적 안전하게 수정할 수 있습니다.

---

## 7. 수정 시 주의사항

### 7.1 Graph DB 스키마가 바뀌는 경우

Neo4j 관계명이나 노드 속성이 바뀌면 다음 파일을 함께 확인해야 합니다.

```text
backend/graph/queries.py
backend/build_services/team_analysis_service.py
backend/build_services/team_builder_service.py
backend/team_build_rag/graph_tools.py
```

### 7.2 추천 점수 정책을 바꾸는 경우

추천 후보의 원본 Graph Score는 `team_builder_service.py`에서 계산합니다.

Hybrid Score 가중치와 정규화는 `team_build_rag`에서 처리합니다.

```text
backend/build_services/team_builder_service.py
backend/team_build_rag/scoring_policy.py
backend/team_build_rag/hybrid_scorer.py
```

### 7.3 화면 표시 문구를 바꾸는 경우

화면에 바로 노출되는 카드 문구는 주로 다음 흐름에서 만들어집니다.

```text
team_score_service.py
team_insight_service.py
answer_generator.py
frontend/pages/teambuilding.py
```

### 7.4 저장 로직을 바꾸는 경우

팀 분석/추천 결과 저장은 서비스 계산 로직이 아니라 라우터와 CRUD 흐름에서 처리합니다.

```text
backend/routers/team_builder.py
backend/crud.py
backend/models.py
```

---

## 8. 한 줄 요약

`backend/build_services`는 팀 빌더의 계산 엔진이고, `backend/team_build_rag`는 계산 결과를 문서 근거와 결합해 설명 가능한 추천으로 만드는 RAG 엔진입니다.
