# Team Builder Services 설명

이 문서는 `backend/build_services` 안에서 팀 빌딩 기능에 직접 연결되는 5개 서비스 파일을 설명합니다.

서비스 계층은 라우터와 데이터베이스 사이에서 실제 비즈니스 로직을 처리합니다.

---

## 1. 전체 구조

| 파일 | 핵심 역할 |
| --- | --- |
| `team_analysis_service.py` | 선택한 5마리 팀의 약점, 저항, 기술 커버리지 분석 |
| `team_score_service.py` | 그래프 상성 데이터를 화면용 점수/등급/문구로 변환 |
| `team_insight_service.py` | 팀 분석 결과를 사람이 읽기 좋은 규칙 기반 해설로 변환 |
| `team_builder_service.py` | 부족한 1마리 추천 후보 계산과 점수화 |
| `team_rag_service.py` | LangGraph 기반 팀 빌드 RAG 워크플로우 실행 |

---

## 2. 서비스 계층의 흐름

일반 팀 분석은 다음 흐름으로 동작합니다.

```text
team_builder router
  -> team_analysis_service.analyze_team()
  -> graph queries
  -> team_score_service.build_type_matchup_items()
  -> team_insight_service.build_team_insights()
```

일반 추천은 다음 흐름으로 동작합니다.

```text
team_builder router
  -> team_builder_service.recommend_team_member()
  -> team_analysis_service.analyze_team()
  -> graph queries
  -> 추천 후보 점수 계산
```

RAG 분석/추천은 다음 흐름으로 동작합니다.

```text
team_builder router
  -> team_rag_service.run_team_rag()
  -> backend/team_build_rag/workflow.py
```

---

## 3. `team_analysis_service.py`

### 목적

선택한 5마리 포켓몬의 팀 상태를 그래프 DB 기준으로 분석합니다.

이 파일은 팀 분석의 중심 파일입니다.

### 주요 함수

| 함수 | 설명 |
| --- | --- |
| `_validate_team_size()` | 포켓몬이 정확히 5마리인지, 중복이 없는지 검증 |
| `analyze_team()` | 선택 팀의 포켓몬 정보, 약점, 저항, 기술 타입 커버리지 조회 |

### 분석 데이터

`analyze_team()`은 다음 데이터를 조합합니다.

| 데이터 | 설명 |
| --- | --- |
| `selected_pokemon` | 선택한 포켓몬 이름, 이미지, 타입, 능력치 |
| `weak_types` | 평균 배율이 1배보다 커서 주의가 필요한 타입 |
| `neutral_types` | 평균 배율이 1배인 타입 |
| `resistant_types` | 평균 배율이 1배보다 낮아 안정적인 타입 |
| `team_type_distribution` | 선택 팀의 타입 분포 |
| `move_type_coverage` | 팀 전체가 배울 수 있는 기술 타입 분포 |
| `insights` | 팀 정체성, 위험 요약, 추천 방향 |

### 설계 의도

Neo4j에서 가져온 원본 상성 데이터는 화면에 바로 보여주기 어렵습니다.

그래서 이 파일은 그래프 데이터를 모으고, `team_score_service.py`와 `team_insight_service.py`를 호출해 프론트가 쓰기 좋은 형태로 정리합니다.

---

## 4. `team_score_service.py`

### 목적

Neo4j에서 가져온 타입 상성 값을 분석용 점수와 등급으로 바꿉니다.

즉, 이 파일의 `score`는 추천 점수가 아니라 “분석 화면에서 위험도/안정성을 표현하기 위한 점수”입니다.

### 주요 함수

| 함수 | 설명 |
| --- | --- |
| `_get_matchup_grade()` | 평균 배율을 기준으로 `매우 위험`, `주의`, `보통`, `안정`, `매우 안정` 등급 생성 |
| `_calculate_matchup_score()` | 평균 배율을 화면 표시용 점수로 변환 |
| `_build_matchup_reason()` | 타입별 설명 문구 생성 |
| `build_type_matchup_items()` | 약점/보통/저항 타입 리스트를 한 번에 생성 |

### 점수 계산 방식

평균 배율이 1보다 크면 위험 점수입니다.

```text
score = (average_multiplier - 1) * 100
```

예를 들어 평균 배율이 `1.8`이면 위험 점수는 `80`입니다.

평균 배율이 1보다 낮으면 안정 점수입니다.

```text
score = (1 - average_multiplier) * 100
```

예를 들어 평균 배율이 `0.6`이면 안정 점수는 `40`입니다.

### 설계 의도

프론트엔드에서 단순히 `1.8배`, `0.6배`만 보여주면 의미가 약합니다.

그래서 이 파일에서 배율을 등급, 점수, 설명으로 바꿔 화면에서 해석하기 쉽게 만들었습니다.

---

## 5. `team_insight_service.py`

### 목적

숫자 중심의 분석 결과를 사람이 읽기 좋은 문장으로 바꿉니다.

RAG를 쓰지 않아도 최소한의 해설이 나오도록 만든 규칙 기반 해설 서비스입니다.

### 주요 함수

| 함수 | 설명 |
| --- | --- |
| `_build_team_identity()` | 팀의 타입 중복, 평균 능력치, 팀 성향 요약 |
| `_build_role_summary()` | 선택 포켓몬 각각의 역할 힌트 생성 |
| `_build_risk_summary()` | 가장 위험한 약점 타입 중심으로 경고 문구 생성 |
| `_build_strength_summary()` | 방어가 안정적인 타입과 기술 커버리지 요약 |
| `_build_recommendation_direction()` | 6번째 포켓몬이 보완해야 할 방향 제안 |
| `build_team_insights()` | 위 내용을 모아 최종 insights 생성 |

### 반환 구조

| 키 | 의미 |
| --- | --- |
| `team_identity` | 팀의 전체 성향 |
| `summary` | 한 줄 요약 |
| `risk_summary` | 위험 요약 |
| `strength_summary` | 강점 요약 |
| `role_summary` | 선택 포켓몬별 역할 |
| `type_balance` | 타입 중복과 분포 |
| `recommendation_direction` | 추천 방향 |

### 설계 의도

그래프 DB는 근거 데이터를 잘 찾지만, 그 자체로 자연스러운 설명을 만들지는 않습니다.

이 파일은 그래프 분석 결과를 프론트에서 바로 보여줄 수 있는 “1차 해설”로 바꿉니다.

RAG가 실패하거나 API 키가 없을 때도 최소한의 설명을 제공하는 안전장치 역할도 합니다.

---

## 6. `team_builder_service.py`

### 목적

선택한 5마리 포켓몬을 기준으로 부족한 1마리를 추천합니다.

추천의 핵심은 “현재 팀의 약점을 얼마나 잘 보완하는가”입니다.

### 주요 함수

| 함수 | 설명 |
| --- | --- |
| `_describe_defensive_relation()` | `RESISTANT_TO`, `VERY_RESISTANT_TO`, `IMMUNE_TO`를 한국어 설명으로 변환 |
| `_build_defensive_reason()` | 후보가 어떤 약점 타입을 어떻게 막는지 설명 |
| `_build_useful_move_notes()` | 후보가 배울 수 있는 대표 기술을 정리 |
| `_build_move_reason()` | 추천 후보의 기술 활용 이유 생성 |
| `_build_candidate_score()` | 후보별 추천 점수 계산 |
| `recommend_team_member()` | 최종 추천 후보 리스트 생성 |

### 추천 점수 기준

| 기준 | 의미 |
| --- | --- |
| 약점 보완 점수 | 현재 팀의 약점 타입을 저항/무효로 받을 수 있는 정도 |
| 능력치 점수 | 후보의 `base_total` 기준 점수 |
| 기술 커버리지 점수 | 후보가 배울 수 있는 기술 타입 다양성 |
| 타입 중복 패널티 | 기존 팀과 타입이 너무 겹칠 때 감점 |

### 추천 결과에 들어가는 정보

| 키 | 의미 |
| --- | --- |
| `pokemon_id` | 추천 후보 ID |
| `name` | 추천 후보 이름 |
| `image_url` | 포켓몬 이미지 |
| `base_total` | 기본 능력치 총합 |
| `score` | 추천 점수 |
| `defensive_covers` | 어떤 약점 타입을 보완하는지 |
| `move_types` | 배울 수 있는 기술 타입 |
| `pokemon_types` | 후보 포켓몬 자체 타입 |
| `useful_moves` | 대표적으로 활용 가능한 기술 |
| `reasons` | 추천 이유 문장 목록 |

### 설계 의도

추천은 단순히 강한 포켓몬을 뽑는 기능이 아닙니다.

현재 팀의 빈틈을 메우는 포켓몬을 찾는 것이 목표입니다.

그래서 그래프 DB에서 약점 보완 관계를 찾고, 서비스 계층에서 능력치/기술/타입 중복을 함께 계산합니다.

---

## 7. `team_rag_service.py`

### 목적

팀 분석/추천 결과를 LangGraph 기반 RAG 워크플로우로 넘기는 진입점입니다.

라우터가 직접 LangGraph를 호출하지 않도록 중간 서비스 역할을 합니다.

### 주요 함수

| 함수 | 설명 |
| --- | --- |
| `run_team_rag()` | RAG 분석 또는 RAG 추천 워크플로우 실행 |

### request type

| 값 | 의미 |
| --- | --- |
| `analysis` | 선택한 팀 분석 해설 생성 |
| `recommendation` | 6번째 포켓몬 추천 해설 생성 |

### 설계 의도

RAG는 내부 단계가 많습니다.

그래서 라우터가 직접 `workflow.py`를 다루지 않고, `team_rag_service.py`에서 상태를 만들고 실행하도록 분리했습니다.

이 구조 덕분에 나중에 LangGraph 상태 구조가 바뀌어도 라우터 수정 범위를 줄일 수 있습니다.

---

## 8. 서비스 간 책임 분리 요약

| 질문 | 담당 파일 |
| --- | --- |
| 선택한 팀은 무엇에 약한가? | `team_analysis_service.py` |
| 약점/저항 점수는 어떻게 표현할까? | `team_score_service.py` |
| 분석을 문장으로 어떻게 요약할까? | `team_insight_service.py` |
| 6번째 포켓몬은 누구를 추천할까? | `team_builder_service.py` |
| RAG 해설은 어떻게 실행할까? | `team_rag_service.py` |

---

## 9. 앞으로 개선할 수 있는 부분

| 개선 포인트 | 설명 |
| --- | --- |
| 추천 점수 가중치 설정화 | 방어/능력치/기술 점수 비중을 설정 파일로 분리 |
| 배틀 룰 반영 | 성격, 아이템, 특성, 기술 위력까지 반영 |
| 후보 기술 품질 개선 | 단순 위력뿐 아니라 명중률, 타입 보완, 변화기 가치 반영 |
| 역할 분류 | 물리 어태커, 특수 어태커, 탱커, 서포터 구분 |
| RAG 근거 강화 | 추천 이유에 실제 기술명과 상성 근거를 더 많이 포함 |
