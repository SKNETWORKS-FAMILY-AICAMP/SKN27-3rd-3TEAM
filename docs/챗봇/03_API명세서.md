# API 명세서 (API Specification)

**프로젝트명:** 포켓몬 AI 챗봇  
**문서 버전:** v1.1  
**작성일:** 2025-05-14  
**최종 수정:** 2025-05-14 (search_pokemon_weakness 툴 추가, search_type_relations / search_evolution_chain 변경사항 반영)  
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
| `TOOL_CALL_LIMIT` | 200 | 툴 호출 횟수 초과 (정상 응답) |

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
| `used_tools` | string[] | 실제 사용된 툴 이름 목록 |
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
      },
      {
        "id": 2,
        "title": "불꽃 타입 약점",
        "model": "gpt-4o-mini",
        "created_at": "2025-05-13T09:10:00Z"
      }
    ],
    "total": 2
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

**Path Parameters:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `session_id` | integer | 조회할 세션 ID |

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
  "data": {
    "deleted_session_id": 1
  },
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
| `sql` | str | SELECT 문 (LIMIT 10 권장) |

**반환 예시:**

```
✅ 3개 결과:
[{"name": "피카츄", "hp": 35, "attack": 55}, ...]
```

**제한:**
- SELECT 이외의 구문 차단
- `INSERT / UPDATE / DELETE / DROP / TRUNCATE / ALTER` 포함 시 오류 반환

---

### 4.2 search_flavor_text

```python
def search_flavor_text(query: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `query` | str | 자연어 검색어 |

**반환 예시:**

```
✅ 관련 도감 설명:

25: 레드 전기 주머니에 전기를 모아두고...

---

25: 블루 꼬리로 땅의 상태를 파악한다...
```

**검색 설정:** MMR, k=20, fetch_k=50, lambda_mult=0.7

---

### 4.3 search_evolution_chain

```python
def search_evolution_chain(pokemon_name: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `pokemon_name` | str | 포켓몬 이름 (부분 일치, CONTAINS 매칭) |

**내부 동작:** 진화 전 체인과 진화 후 체인(최대 3단계)을 별도 쿼리로 분리 조회.  
`LIMIT 1` + `DISTINCT`로 여러 폼(form) 노드가 존재할 때 중복 경로 방지.

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

**내부 동작:** `ATTACK_EFFECTIVE` 관계 대신 `AGAINST` 관계를 기반으로 단일 타입 포켓몬을 필터링하여 순수 타입 배율을 추출. 무효 타입·약점 포켓몬 예시·면역 포켓몬 예시도 함께 반환.

**반환 예시:**

```
⚔️  [불꽃] 타입 상성

✅ 공격 시 효과적 (2배+): 풀(2배), 얼음(2배), 벌레(2배), 강철(2배)
❌ 공격 시 비효과적 (절반-): 불꽃(0.5배), 물(0.5배), 바위(0.5배), 드래곤(0.5배)
🚫 공격 시 무효 (0배): 바위
⚠️  이 타입의 약점 (당할 때): 물(2배), 바위(2배), 땅(2배)

📋 약점 포켓몬 예시: 이상해씨, 파이리, 꼬부기, ...
🛡️  면역 포켓몬 예시: 가디, ...
```

---

### 4.5 search_pokemon_weakness ✨ NEW

```python
def search_pokemon_weakness(pokemon_name: str) -> str
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `pokemon_name` | str | 포켓몬 이름 (부분 일치, CONTAINS 매칭) |

**설명:** 포켓몬 이름이 주어졌을 때 해당 포켓몬의 실제 방어 배율을 반환한다.  
`AGAINST` 관계에 저장된 복합 배율을 직접 읽어 듀얼 타입의 4배/0.25배 등을 정확히 반영한다.  
`search_type_relations`가 타입 개념 수준의 상성을 반환하는 것과 달리, 이 툴은 **포켓몬 개체 수준**의 상성을 반환한다.

**Agent 우선순위:** 질문에 포켓몬 이름이 명시된 경우 `search_type_relations` 대신 이 툴을 우선 사용한다.

**반환 예시:**

```
🔍 [리자몽] 타입 상성 (보유 타입: 불꽃, 비행)

💀 4배 약점: 바위(4배)
⚠️  2배 약점: 물(2배), 전기(2배)
🛡️  0.5배 저항: 풀, 벌레, 강철, 불꽃, 페어리
🛡️  0.25배 저항: (해당 없음)
✨ 면역: 땅
```

**배율 분류 기준:**

| 배율 | 분류 | 표시 |
|------|------|------|
| 0배 | 면역 | ✨ 면역 |
| 0.25배 이하 | 매우 저항 | 🛡️ 0.25배 저항 |
| 0.5배 | 저항 | 🛡️ 0.5배 저항 |
| 1배 | 보통 | (생략) |
| 2배 | 약점 | ⚠️ 2배 약점 |
| 4배 이상 | 매우 약점 | 💀 4배 약점 |

---
