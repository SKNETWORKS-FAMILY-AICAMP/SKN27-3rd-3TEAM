# AI Pipeline

---

## 팀 빌더 — LangGraph Hybrid RAG

포켓몬 5마리를 입력받아 Neo4j 그래프 분석과 pgvector 벡터 검색을 결합한 하이브리드 RAG로 팀을 분석하고 6번째 포켓몬을 추천합니다.

### 파이프라인 흐름

```mermaid
flowchart TD
    Input([pokemon_ids 5개]) --> GraphAnalysis

    subgraph LangGraph["LangGraph RAG 오케스트레이션"]
        GraphAnalysis["① Graph DB 분석\nNeo4j Cypher\n타입 약점 · 저항 · 커버리지"] --> Insight["② 팀 인사이트 생성\n팀 정체성 · 위험 요소 · 방향성"]

        Insight --> GR["③-A Graph 추천\ngraph_score\n(Neo4j GDS)"]
        Insight --> VS["③-B Vector 검색\nvector_score\n(pgvector BM25 + 임베딩)"]

        GR --> Rerank["④ Hybrid Re-ranking\nscore = 0.7 × graph + 0.3 × vector"]
        VS --> Rerank

        Rerank --> LLM["⑤ LLM 해설 생성\nGPT-4o-mini / Groq\n분석 결론 · 추천 이유 문장"]
    end

    LLM --> Save[("PostgreSQL JSONB\nanalysis_result\nrecommendation_result")]
    LLM --> Result([팀 결과 페이지 렌더링])
```

### Re-ranking 수식

```
hybrid_score = 0.7 × graph_score + 0.3 × vector_score
```

- **graph_score**: Neo4j GDS로 팀의 타입 약점을 보완하는 포켓몬에 높은 점수 부여
- **vector_score**: pgvector BM25 + 문장 임베딩으로 팀 인사이트 문장과 유사한 포켓몬 탐색

### 병렬 처리

프론트엔드에서 분석(`/rag-analyze`)과 추천(`/rag-recommend`)을 `ThreadPoolExecutor`로 동시에 호출합니다.  
`user_id`는 메인 스레드에서 캡처 후 각 페이로드에 주입합니다 (Streamlit session_state 스레드 안전성 이슈 방지).

---

## 챗봇 — LangGraph 멀티툴 에이전트

질문 의도에 따라 4가지 툴을 자동 선택해 포켓몬 전문 답변을 생성합니다.

```mermaid
flowchart TD
    Q([사용자 질문]) --> Agent

    subgraph Agent["LangGraph 멀티툴 에이전트 (오박사)"]
        Router{툴 선택\nLLM Router}
        Router --> SQL["SQL Tool\n자연어 → SQL 자동 생성\nPostgreSQL 직접 조회"]
        Router --> Vec["Vector Search\npgvector BM25 + 임베딩\n도감 설명 유사 검색"]
        Router --> Graph["Graph Search\nNeo4j Cypher\n진화 체인 · 타입 상성"]
        Router --> Web["Web Search\nTavily 폴백\n최신 정보 · 미등록 질문"]
        SQL & Vec & Graph & Web --> Merge["결과 합성\nLLM 최종 답변 생성"]
    end

    Agent <-->|멀티턴 히스토리| Mem[("Memory\nDB 저장(로그인)\nUUID 쿠키(비로그인)")]
    Merge --> Answer([마크다운 답변 렌더링])
```

### 툴 선택 기준

| 툴 | 적합한 질문 유형 |
|---|---|
| SQL Tool | 스탯 수치, 타입, 특성 등 구조화된 데이터 조회 |
| Vector Search | "~와 비슷한 포켓몬", 도감 설명 기반 검색 |
| Graph Search | 진화 방법, 타입 상성, 관계 탐색 |
| Web Search | 최신 게임 정보, 대회 메타, DB에 없는 질문 |

---

## 시퀀스 다이어그램

### GitHub OAuth 로그인

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant GH as GitHub API
    participant DB as PostgreSQL

    User->>FE: GitHub 로그인 버튼 클릭
    FE->>BE: GET /auth/github
    BE-->>FE: OAuth URL redirect
    FE->>GH: OAuth 인증 요청
    GH-->>FE: authorization code 반환
    FE->>BE: POST /api/v1/users/sync {code}
    BE->>GH: Access Token 교환
    GH-->>BE: user info (커밋 · 레포 · 스타) 반환
    BE->>DB: UPSERT users
    DB-->>BE: db_id
    BE-->>FE: user JSON
    FE->>FE: 쿠키 저장
    FE->>User: 마이페이지 이동
```

### 팀 빌더 RAG 분석/추천

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend
    participant BE as Backend
    participant Neo as Neo4j
    participant PG as PostgreSQL
    participant LLM as LLM (OpenAI/Groq)

    User->>FE: 포켓몬 5마리 선택 후 [팀 분석 & 추천] 클릭

    par 병렬 API 호출
        FE->>BE: POST /rag-analyze {pokemon_ids, user_id}
        FE->>BE: POST /rag-recommend {pokemon_ids, user_id, limit}
    end

    BE->>Neo: Cypher 타입 약점/저항/커버리지 쿼리
    Neo-->>BE: 분석 결과
    BE->>PG: Vector Search (pgvector)
    PG-->>BE: 유사 문서
    BE->>LLM: 분석 해설 생성 요청
    LLM-->>BE: 분석 결론 문장
    BE-->>FE: analysis_result

    BE->>Neo: 6번째 포켓몬 Graph 추천
    Neo-->>BE: 추천 후보 + graph_score
    BE->>PG: Vector 점수 계산
    PG-->>BE: vector_score
    BE->>LLM: 추천 해설 생성 (Re-ranking 결과 포함)
    LLM-->>BE: 추천 결론 문장
    BE->>PG: INSERT team_build_logs (JSONB)
    PG-->>BE: log_id
    BE-->>FE: recommendation_result + log_id

    FE->>User: team_result.py 결과 페이지 렌더링
```

### 챗봇 멀티턴 대화

```mermaid
sequenceDiagram
    actor User as 사용자
    participant FE as Frontend (챗봇 패널)
    participant BE as Backend
    participant DB as PostgreSQL / Neo4j
    participant LLM as LLM

    User->>FE: "피카츄 스탯 알려줘"
    FE->>BE: POST /api/v1/chatbot/chat {message, session_id}
    BE->>BE: LangGraph Agent 실행 · 툴 선택
    BE->>DB: SQL Tool → SELECT * FROM pokemon WHERE name='피카츄'
    DB-->>BE: 스탯 데이터
    BE->>LLM: 컨텍스트 + 히스토리 + DB 결과 → 답변 생성
    LLM-->>BE: 마크다운 답변
    BE->>DB: 메시지 저장 (chatbot_messages)
    BE-->>FE: answer
    FE->>User: 마크다운 렌더링 답변 표시
```
