# Team Builder Router 설명

이 문서는 `backend/routers/team_builder.py`의 역할과 API 흐름을 설명합니다.

이 파일은 프론트엔드의 팀 빌딩 페이지와 백엔드 서비스 계층 사이를 연결하는 FastAPI 라우터입니다.

---

## 1. 파일의 목적

`team_builder.py`는 사용자가 프론트에서 포켓몬을 선택하고 버튼을 눌렀을 때 호출되는 API를 정의합니다.

직접 복잡한 계산을 많이 하기보다는, 요청을 검증하고 적절한 서비스로 넘기는 역할을 담당합니다.

```text
프론트엔드 teambuilding.py
  -> backend/routers/team_builder.py
  -> backend/build_services/*
  -> backend/graph/*
  -> Neo4j / Vector DB / LLM
```

---

## 2. API Prefix

이 라우터는 다음 prefix를 사용합니다.

```text
/api/v1/team-builder
```

그래서 실제 API 주소는 다음처럼 만들어집니다.

| 기능 | HTTP Method | URL |
| --- | --- | --- |
| 팀 빌딩용 포켓몬 목록 | `GET` | `/api/v1/team-builder/pokemon-options` |
| 팀 분석 | `POST` | `/api/v1/team-builder/analyze` |
| 포켓몬 추천 | `POST` | `/api/v1/team-builder/recommend` |
| RAG 기반 팀 분석 | `POST` | `/api/v1/team-builder/rag-analyze` |
| RAG 기반 추천 | `POST` | `/api/v1/team-builder/rag-recommend` |

---

## 3. Request 모델

### `TeamBuilderRequest`

팀 분석에 사용하는 기본 요청 모델입니다.

```json
{
  "pokemon_ids": [3, 6, 9, 25, 448]
}
```

| 필드 | 의미 |
| --- | --- |
| `pokemon_ids` | 사용자가 선택한 5마리 포켓몬 ID |

현재 팀 분석은 5마리를 기준으로 설계되어 있습니다.

중복 선택은 서비스 계층에서 검증합니다.

### `TeamRecommendationRequest`

추천 API에서 사용하는 요청 모델입니다.

```json
{
  "pokemon_ids": [3, 6, 9, 25, 448],
  "limit": 3
}
```

| 필드 | 의미 |
| --- | --- |
| `pokemon_ids` | 현재 선택한 5마리 포켓몬 ID |
| `limit` | 추천 후보를 몇 개 반환할지 |

---

## 4. Endpoint 설명

## `GET /pokemon-options`

### 목적

프론트엔드 팀 빌딩 화면에서 카드로 보여줄 포켓몬 목록을 가져옵니다.

기존 `pokemon.py`의 포켓몬 목록 API와 분리한 이유는 팀 빌딩 화면에서 필요한 정보가 조금 다르기 때문입니다.

팀 빌딩 카드에는 최소한 다음 정보가 필요합니다.

| 데이터 | 사용 위치 |
| --- | --- |
| `pokemon_id` | 선택/해제 상태 관리 |
| `name` | 카드 이름 표시 |
| `image_url` | 포켓몬 이미지 표시 |
| `generation` | 세대 필터 |
| `base_total` | 추천/분석 참고 |
| `types` | 타입 뱃지 표시 |

### 설계 이유

프론트에서 포켓몬 타입을 표시하려면 백엔드가 타입 정보를 함께 내려줘야 합니다.

그래서 Neo4j에서 `Pokemon -> HAS_TYPE -> Type` 관계를 조회해 카드 데이터에 포함하도록 만들었습니다.

---

## `POST /analyze`

### 목적

선택한 5마리 포켓몬의 팀 약점과 방어 안정성을 분석합니다.

### 내부 흐름

```text
request.pokemon_ids
  -> analyze_team()
  -> Neo4j에서 약점/저항/기술 타입 조회
  -> team_score_service에서 점수와 등급 생성
  -> 프론트에 분석 결과 반환
```

### 반환 데이터 예시

| 키 | 의미 |
| --- | --- |
| `selected_pokemon` | 선택된 포켓몬 상세 정보 |
| `weak_types` | 주의해야 할 공격 타입 |
| `resistant_types` | 방어가 안정적인 타입 |
| `move_type_coverage` | 팀이 배울 수 있는 기술 타입 분포 |
| `insights` | 규칙 기반 팀 해설 |

---

## `POST /recommend`

### 목적

선택한 5마리 기준으로 부족한 1마리를 추천합니다.

### 내부 흐름

```text
request.pokemon_ids
  -> recommend_team_member()
  -> 팀 약점 분석
  -> 약점을 보완할 후보 조회
  -> 후보 점수 계산
  -> 상위 후보 반환
```

### 추천 기준

추천은 단순히 강한 포켓몬을 고르는 것이 아니라 아래 요소를 함께 봅니다.

| 기준 | 설명 |
| --- | --- |
| 약점 보완 | 현재 팀이 약한 타입을 저항/무효로 받을 수 있는지 |
| 기본 능력치 | `base_total`이 충분히 높은지 |
| 기술 타입 다양성 | 배울 수 있는 기술 타입이 넓은지 |
| 타입 중복 패널티 | 기존 팀과 타입이 너무 겹치지 않는지 |

---

## `POST /rag-analyze`

### 목적

그래프 DB 분석 결과와 벡터 검색 문서를 함께 사용해서 AI 해설용 분석 결과를 생성합니다.

일반 `/analyze`보다 설명형 응답에 가깝습니다.

### 내부 흐름

```text
pokemon_ids
  -> team_build_rag.workflow
  -> graph tool: team_analysis
  -> vector search
  -> hybrid context
  -> answer generator
```

---

## `POST /rag-recommend`

### 목적

추천 후보를 계산한 뒤, RAG 기반으로 추천 이유를 더 자연스럽게 설명하기 위한 API입니다.

일반 `/recommend`는 점수 중심이고, `/rag-recommend`는 “왜 추천하는지”를 설명하는 방향입니다.

### 내부 흐름

```text
pokemon_ids
  -> team_build_rag.workflow
  -> graph tool: team_recommendation
  -> vector search
  -> hybrid_scorer
  -> answer generator
```

---

## 5. 에러 처리

서비스에서 `ValueError`가 발생하면 `_handle_value_error()`를 통해 HTTP 400으로 변환합니다.

예를 들어 아래 상황은 사용자의 요청이 잘못된 경우입니다.

| 상황 | 응답 |
| --- | --- |
| 5마리가 아닌 경우 | `400 Bad Request` |
| 같은 포켓몬을 중복 선택한 경우 | `400 Bad Request` |
| 추천 후보를 만들 수 없는 경우 | `400 Bad Request` |

Neo4j 연결 실패나 서버 내부 오류는 별도 예외로 처리됩니다.

---

## 6. 이 라우터가 직접 하지 않는 일

이 파일은 API 입구입니다.

다음 작업은 다른 계층에서 처리합니다.

| 작업 | 담당 파일 |
| --- | --- |
| 팀 분석 계산 | `backend/build_services/team_analysis_service.py` |
| 분석 점수 변환 | `backend/build_services/team_score_service.py` |
| 추천 후보 계산 | `backend/build_services/team_builder_service.py` |
| RAG 워크플로우 실행 | `backend/build_services/team_rag_service.py` |
| Neo4j 쿼리 실행 | `backend/graph/neo4j_client.py` |

---

## 7. 확장 시 주의점

프론트엔드가 필요로 하는 응답 키 이름이 바뀌면 화면 오류가 생길 수 있습니다.

그래서 API 응답 구조를 바꿀 때는 다음 파일도 함께 확인해야 합니다.

```text
frontend/pages/teambuilding.py
```

특히 `score`, `types`, `image_url`, `recommendations`, `final_answer` 같은 키는 프론트 표시와 직접 연결됩니다.
