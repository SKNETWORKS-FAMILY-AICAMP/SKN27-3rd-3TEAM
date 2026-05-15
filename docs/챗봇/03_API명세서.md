# API 명세서 (API Specification)

**프로젝트명:** 포켓몬 AI 챗봇  
**문서 버전:** v1.2  
**작성일:** 2025-05-14  
**최종 수정:** 2025-05-14 (web_search 제거, Hybrid Search 반영, MAX_TOOL_CALLS 5 반영, CRAG 추가)  
**Base URL:** `http://localhost:8000/api/v1`

---

## 1. 공통 사항

### 1.1 요청 헤더

```
Content-Type: application/json
Accept: application/json
```

### 1.2 공통 응답 포맷

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### 1.3 에러 응답 포맷

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DB_CONNECTION_ERROR",
    "message": "데이터베이스 연결에 실패했습니다."
  }
}
```

### 1.4 에러 코드 목록

| 코드 | HTTP 상태 | 설명 |
|------|---------|------|
| `VALIDATION_ERROR` | 400 | 요청 파라미터 형식 오류 |
| `SESSION_NOT_FOUND` | 404 | 존재하지 않는 세션 ID |
| `DB_CONNECTION_ERROR` | 500 | PostgreSQL 연결 실패 |
| `NEO4J_ERROR` | 500 | Neo4j 연결 또는 쿼리 실패 |
| `LLM_API_ERROR` | 502 | OpenAI API 호출 실패 |
| `TOOL_CALL_LIMIT` | 200 | 툴 호출 횟수 초과 (정상 응답, MAX=5) |

---

## 2. 채팅 API

### 2.1 메시지 전송 (Chat)

사용자의 질의를 Agent에 전달하고 답변을 반환한다.

```
POST /chat
```

**Request Body:**

```json
{
  "query": "피카츄의 스탯을 알려줘",
  "session_id": 1,
  "model": "gpt-4o-mini"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `query` | string | ✅ | 사용자 질문 (1~2000자) |
| `session_id` | integer | ❌ | 기존 세션 ID (없으면 새 세션 생성) |
| `model` | string | ❌ | 모델명 (기본값: `gpt-4o-mini`) |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "session_id": 1,
    "answer": "피카츄의 스탯은 다음과 같습니다.\n\n| 항목 | 수치 |\n|------|------|\n| HP | 35 |\n| 공격 | 55 |...",
    "used_tools": ["search_pokemon_db"],
    "model": "gpt-4o-mini",
    "created_at": "2025-05-14T14:32:00Z"
  },
  "error": null
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `session_id` | integer | 생성 또는 재사용된 세션 ID |
| `answer` | string | AI 답변 (마크다운 형식) |
| `used_tools` | string[] | 실제 사용된 툴 이름 목록 (최대 5개) |
| `model` | string | 사용된 모델명 |
| `created_at` | ISO8601 | 응답 생성 시각 |

---

## 3. 세션 API

### 3.1 세션 목록 조회

```
GET /sessions
```

**Query Parameters:**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `limit` | integer | 60 | 최대 반환 수 |
| `user_id` | string | - | 사용자 ID 필터 (선택) |

**Response (200):**

```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "id": 1,
        "title": "피카츄 진화 경로",
        "model": "gpt-4o-mini",
        "created_at": "2025-05-14T14:32:00Z"
      }
    ],
    "total": 1
  },
  "error": null
}
```

---

### 3.2 세션 생성

```
POST /sessions
```

**Request Body:**

```json
{
  "title": "새 대화",
  "model": "gpt-4o-mini",
  "user_id": "user_001"
}
```

**Response (201):**

```json
{
  "success": true,
  "data": {
    "session_id": 3,
    "title": "새 대화",
    "model": "gpt-4o-mini",
    "created_at": "2025-05-14T15:00:00Z"
  },
  "error": null
}
```

---

### 3.3 세션 메시지 조회

```
GET /sessions/{session_id}/messages
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "session_id": 1,
    "messages": [
      {
        "role": "user",
        "content": "피카츄 스탯 알려줘",
        "used_tools": [],
        "created_at": "2025-05-14T14:32:00Z"
      },
      {
        "role": "assistant",
        "content": "피카츄의 스탯은 다음과 같습니다...",
        "used_tools": ["search_pokemon_db"],
        "created_at": "2025-05-14T14:32:05Z"
      }
    ]
  },
  "error": null
}
```

---

### 3.4 세션 삭제

```
DELETE /sessions/{session_id}
```

**Response (200):**

```json
{
  "success": true,
  "data": { "deleted_session_id": 1 },
  "error": null
}
```

---

## 4. 내부 Tool 함수 명세

> Agent 내부에서 LangGraph ToolNode가 호출하는 함수 명세입니다.  
> HTTP API가 아닌 Python 함수 인터페이스입니다.

### 4.1 search_pokemon_db

```python
def search_pokemon_db(sql: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `sql` | str | SELECT 문 (LIMIT 10 권장, 동점 처리 시 서브쿼리 사용) |

**제한:**
- SELECT 이외의 구문 차단 (INSERT / UPDATE / DELETE / DROP / TRUNCATE / ALTER)
- 코드 블록(` ```sql ``` `) 자동 제거 후 실행

**반환 예시:**
```
✅ 3개 결과:
[{"name": "피카츄", "hp": 35, "attack": 55}, ...]
```

---

### 4.2 search_flavor_text

```python
def search_flavor_text(query: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `query` | str | 자연어 검색어 (Query Rewriting 후 전달됨) |

**내부 동작 — Hybrid Search (3-way RRF):**

| 채널 | 방식 | 파라미터 |
|------|------|---------|
| ① Vector (MMR) | PGVector, 코사인 유사도 | k=20, fetch_k=50, lambda_mult=0.7 |
| ② BM25 | rank_bm25, 단어 TF-IDF | 프로세스 메모리 상주, TOP 20 |
| ③ pg_trgm | PostgreSQL 트라이그램 유사도 | similarity > 0.05, TOP 20 |
| 🔀 RRF | k=60 | 3채널 결합 → 상위 5개 반환 |

벡터 결과의 `species_id`를 파싱하여 포켓몬 이름을 DB에서 조회 후 부착한다.  
채널 중 하나가 실패해도 나머지 채널로 RRF를 계속 수행한다.

**반환 예시:**
```
✅ 관련 도감 설명:

피카츄: 전기 주머니에 전기를 모아두고...

---

라이츄: 꼬리로 땅을 찍어 전기를 방전한다...
```

---

### 4.3 search_evolution_chain

```python
def search_evolution_chain(pokemon_name: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `pokemon_name` | str | 포켓몬 이름 (부분 일치, CONTAINS 매칭) |

**내부 동작:**
- 진화 전 체인: `LIMIT 1`로 중복 폼 노드 방지
- 진화 후 체인: `DISTINCT` + 메가/거다이맥스 폼 필터링
- Neo4j 미수록 진화 조건 → `KNOWN_EVO_CONDITIONS` fallback 맵으로 보완

**반환 예시:**
```
🔗 [피카츄] 진화 체인 정보

◀ 진화 전:
  피츄 → 피카츄 (조건: 조건 미상)

▶ 진화 후:
  피카츄 → 라이츄  [아이템: 천둥의돌]
```

---

### 4.4 search_type_relations

```python
def search_type_relations(type_name: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `type_name` | str | 타입명 (부분 일치) |

**내부 동작:** `AGAINST` 관계 + 단일 타입 포켓몬 필터로 순수 배율 추출.  
공격 효율(강함/약함/무효) + 방어 특성(약점/면역/저항) + 포켓몬 예시를 통합 반환.

**반환 예시:**
```
⚔️  [불꽃] 타입 상성

✅ 공격 시 효과적 (2배+): 풀(2배), 얼음(2배), 벌레(2배), 강철(2배)
❌ 공격 시 비효과적 (절반-): 불꽃(0.5배), 물(0.5배), 바위(0.5배), 드래곤(0.5배)
🚫 공격 시 무효 (0배): (해당 없음)
⚠️  이 타입의 약점 (당할 때): 물(2배), 바위(2배), 땅(2배)
✨ 이 타입의 면역 (당할 때 0배): (해당 없음)
🛡️  이 타입의 저항 (당할 때 절반-): 풀, 벌레, 강철, 불꽃, 페어리

📋 약점 포켓몬 예시: 이상해씨, 파이리, ...
🛡️  면역 포켓몬 예시: (해당 없음)
```

---

### 4.5 search_pokemon_weakness

```python
def search_pokemon_weakness(pokemon_name: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `pokemon_name` | str | 포켓몬 이름 (부분 일치) |

**내부 동작:** `AGAINST` 관계에서 전체 공격 타입 배율을 직접 읽어 버킷 분류.  
`search_type_relations`와 달리 **포켓몬 개체 수준** 배율 (듀얼 타입 복합 포함).

| 배율 | 버킷 | 표시 |
|------|------|------|
| 0배 | immune | ✨ 면역 |
| 0 < m ≤ 0.25 | very_resistant | 🛡️ 0.25배 저항 |
| 0.5배 | resistant | 🛡️ 0.5배 저항 |
| 1배 | normal | (생략) |
| 2배 | weak | ⚠️ 2배 약점 |
| ≥ 4배 | very_weak | 💀 4배 약점 |

**반환 예시:**
```
🔍 [리자몽] 타입 상성 (보유 타입: 불꽃, 비행)

💀 4배 약점: 바위(4배)
⚠️  2배 약점: 물(2배), 전기(2배)
🛡️  0.5배 저항: 풀, 벌레, 강철, 불꽃, 페어리
✨ 면역: 땅
```

---

## 5. 내부 헬퍼 함수 명세

### 5.1 _rewrite_query (Query Rewriting)

```python
def _rewrite_query(query: str) -> str
```

Agent의 첫 번째 툴 호출 직전에 실행되는 전처리 함수.  
`gpt-4o-mini`를 호출하여 사용자 질문에서 불필요한 표현을 제거하고 검색 키워드를 명확히 한다.  
실패 시 원본 질문을 그대로 반환한다 (fallback 보장).

### 5.2 crag_check_node (CRAG)

```python
def crag_check_node(state: AgentState) -> AgentState
```

`ToolNode` 실행 직후 호출되는 LangGraph 노드.  
`gpt-4o-mini`로 툴 결과 관련성을 평가하고, 관련 없으면 재검색 유도 `SystemMessage`를 삽입한다.  
`tool_call_count >= MAX_TOOL_CALLS - 1` (4회 이상)이면 평가를 생략하여 무한 루프를 방지한다.

| 판정 결과 | 삽입 메시지 |
|---------|-----------|
| YES (관련 있음) | 메시지 없음 (통과) |
| 빈 결과 / "찾을 수 없음" | "검색어를 바꾸거나 다른 툴로 재시도하세요." |
| NO (전혀 무관) | "⚠️ 직전 결과가 질문과 무관합니다. 재검색하세요." |

### 5.3 _reciprocal_rank_fusion

```python
def _reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]
```

여러 검색 채널의 순위 목록을 입력받아 RRF 점수로 통합 정렬된 단일 목록을 반환한다.  
점수 계산: `score(doc) += 1 / (k + rank + 1)`
