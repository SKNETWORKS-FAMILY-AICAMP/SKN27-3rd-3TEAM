# API Reference

Base URL: `http://localhost:8080`  
모든 경로는 `/api/v1` 접두사를 사용합니다.

---

## 포켓몬 `/api/v1/pokemon`

### `GET /api/v1/pokemon/`

포켓몬 목록 조회 (페이지네이션 + 복합 필터)

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `skip` | int | 0 | 오프셋 |
| `limit` | int | 20 | 페이지 크기 |
| `search` | string | — | 이름 또는 번호 검색 |
| `type_names` | string[] | — | 타입 필터 (복수 가능) |
| `ability` | string | — | 특성 이름 필터 |
| `min_id` | int | 1 | 도감번호 최솟값 |
| `max_id` | int | 1025 | 도감번호 최댓값 |

### `GET /api/v1/pokemon/{id}`

포켓몬 상세 조회 — 기본 스탯 · 타입 · 특성 · 진화 체인 · 형태 포함

### `GET /api/v1/pokemon/abilities/`

전체 특성 목록 반환

---

## 유저 `/api/v1/users`

### `POST /api/v1/users/sync`

GitHub OAuth 유저 생성 또는 업데이트

**Body:**
```json
{
  "github_id": 12345678,
  "login": "username",
  "name": "이름",
  "avatar_url": "https://...",
  "email": "...",
  "public_repos": 42,
  "total_commits": 1000,
  "total_stars": 50,
  "followers": 10
}
```

### `GET /api/v1/users/{id}/stats`

유저 게임 통계 반환 — 퀴즈 정답률 · 메모리 게임 · 도감 수집 수 · 배지 목록

### `GET /api/v1/users/{id}/logs`

유저 최근 게임 로그 목록

### `POST /api/v1/users/game-log`

게임 플레이 로그 저장

**Body:**
```json
{
  "user_id": 1,
  "game_type": "silhouette_quiz",
  "pokemon_id": 25,
  "is_correct": true,
  "hint_used": false,
  "wrong_answer_id": null,
  "log_data": "{}"
}
```

### `GET /api/v1/users/{id}/battle-team`

저장된 배틀 팀 조회

### `POST /api/v1/users/{id}/battle-team`

배틀 팀 저장

---

## 팀 빌더 `/api/v1/team-builder`

### `GET /api/v1/team-builder/pokemon-options`

팀 빌더용 포켓몬 목록 (Neo4j 기반, 타입/지방/특성 필터 포함)

### `POST /api/v1/team-builder/analyze`

타입 약점 · 저항 · 커버리지 분석 (Neo4j Cypher)

**Body:**
```json
{ "pokemon_ids": [1, 4, 7, 25, 39] }
```

### `POST /api/v1/team-builder/recommend`

Graph DB 기반 6번째 포켓몬 후보 목록 반환

**Body:**
```json
{ "pokemon_ids": [1, 4, 7, 25, 39], "limit": 3 }
```

### `POST /api/v1/team-builder/rag-analyze`

LangGraph Hybrid RAG 분석 해설 생성 + DB 저장

**Body:**
```json
{
  "pokemon_ids": [1, 4, 7, 25, 39],
  "user_id": 1
}
```

### `POST /api/v1/team-builder/rag-recommend`

LangGraph Hybrid RAG 추천 해설 생성 + Re-ranking + DB 저장

**Body:**
```json
{
  "pokemon_ids": [1, 4, 7, 25, 39],
  "user_id": 1,
  "limit": 3
}
```

### `GET /api/v1/team-builder/history/{user_id}`

유저의 팀 빌더 분석 히스토리 목록 반환

---

## 챗봇 `/api/v1/chatbot`

### `POST /api/v1/chatbot/chat`

챗봇 메시지 전송 → LangGraph 에이전트 실행 → AI 응답 반환

**Body:**
```json
{
  "message": "피카츄 스탯 알려줘",
  "session_id": "uuid-...",
  "model": "gpt-4o-mini"
}
```

### `GET /api/v1/chatbot/sessions`

세션 목록 조회 (로그인 유저: `user_id` 쿼리파라미터)

### `POST /api/v1/chatbot/sessions`

새 세션 생성

### `DELETE /api/v1/chatbot/sessions/{id}`

세션 삭제 (연관 메시지 포함)

### `GET /api/v1/chatbot/sessions/{id}/messages`

세션 메시지 이력 조회

---

## AI 배틀 `/api/v1/chat`

### `POST /api/v1/chat/rap-battle`

두 포켓몬의 랩 배틀 대본 생성 (동기 응답)

**Body:**
```json
{
  "pokemon1": "피카츄",
  "pokemon2": "파이리"
}
```

### `POST /api/v1/chat/rap-battle/stream`

랩 배틀 대본 스트리밍 응답 (`text/event-stream`)

**Body:** 동일
