# RAG / 데이터 파이프라인 설계도

**프로젝트명:** 포켓몬 AI 챗봇  
**문서 버전:** v1.2  
**작성일:** 2025-05-14  
**최종 수정:** 2025-05-14 (Hybrid Search 전면 도입, CRAG 추가, Query Rewriting 추가, web_search 제거)

---

## 1. RAG 아키텍처 개요

본 시스템은 **멀티-소스 RAG + Graph RAG + CRAG(Corrective RAG)** 구조를 채택한다.  
LLM이 질문의 의도에 따라 최적의 검색 경로를 자율 선택하며, Query Rewriting으로 검색 품질을 사전 향상하고, CRAG로 결과 관련성을 사후 보정한다.

```mermaid
flowchart TB
    Q["사용자 질문 (자연어)"]

    subgraph PRE["🔄 전처리 (Query Rewriting)"]
        QR["GPT-4o-mini\n핵심 키워드 재작성\n(첫 호출 시만)"]
    end

    subgraph ROUTING["🧠 LLM 기반 라우팅 (자율 툴 선택)"]
        AGENT["GPT-4o-mini\nTool-calling Agent\nMAX 5회"]
    end

    subgraph RETRIEVAL["📡 검색 레이어"]
        R1["SQL Retrieval\n(정형 데이터)"]
        R2["Hybrid Retrieval\n(Vector+BM25+pg_trgm+RRF)"]
        R3["Graph Retrieval\n(진화·타입·약점)"]
    end

    subgraph EVAL["⚖️ CRAG 평가"]
        CRAG["GPT-4o-mini\n결과 관련성 판정\nYES / NO"]
    end

    subgraph AUGMENT["📚 Augmentation"]
        CTX["컨텍스트 통합\n(ToolNode → 메시지 추가)"]
    end

    subgraph GENERATE["✍️ Generation"]
        GEN["GPT-4o-mini\n최종 답변 생성\n(툴 결과에만 근거)"]
    end

    Q --> QR --> AGENT
    AGENT -->|search_pokemon_db| R1
    AGENT -->|search_flavor_text| R2
    AGENT -->|search_evolution_chain\nsearch_type_relations\nsearch_pokemon_weakness| R3

    R1 & R2 & R3 --> CTX --> CRAG
    CRAG -->|통과| GEN
    CRAG -->|재검색 유도| AGENT
    GEN --> ANS["최종 답변\n(툴 결과 기반, 환각 차단)"]
```

---

## 2. 오프라인 데이터 파이프라인 (Indexing Pipeline)

```mermaid
flowchart LR
    subgraph SOURCE["📥 원천 데이터"]
        RAW_JSON["flavor_text.json\n(도감 설명 원문)"]
        RAW_CSV["pokemon 데이터\n(CSV / PokéAPI)"]
        RAW_GRAPH["진화·타입·약점 관계\n(graph_loader.py)"]
    end

    subgraph PROCESS["⚙️ 전처리"]
        P1["텍스트 조합\n'species_id: version_name content'"]
        P2["Document 객체 생성\n(LangChain Document)"]
        P3["정형 테이블 변환\n(psycopg2 INSERT)"]
        P4["그래프 노드·엣지 생성\n(Cypher MERGE)\nAGAINST 관계 포함"]
    end

    subgraph EMBED["🔢 임베딩"]
        EMB["OpenAI Embeddings API\ntext-embedding-ada-002\n1536차원"]
    end

    subgraph INDEX["🗄️ 인덱싱"]
        PG_IDX[("PostgreSQL\n정형 테이블 적재\npg_trgm GIN 인덱스")]
        VEC_IDX[("PGVector\nlangchain_pg_embedding")]
        BM25_BUILD["BM25 인덱스\n모듈 로드 시 DB에서 읽어\n인메모리 빌드"]
        NEO_IDX[("Neo4j\n포켓몬·타입·아이템\n그래프")]
    end

    RAW_JSON --> P1 --> P2 --> EMB --> VEC_IDX
    RAW_CSV --> P3 --> PG_IDX
    PG_IDX -->|"SELECT ... flavor_text JOIN"| BM25_BUILD
    RAW_GRAPH --> P4 --> NEO_IDX
```

---

## 3. 온라인 RAG 파이프라인 (Inference Pipeline)

### 3.1 Query Rewriting

```mermaid
flowchart LR
    Q["원본 사용자 질문\n(첫 호출 시)"]
    Q --> GPT["GPT-4o-mini\n핵심 의도 유지\n검색 키워드 명확화\n한 문장 출력"]
    GPT --> RQ["재작성된 질문"]
    GPT -->|"실패 시 fallback"| Q2["원본 질문 그대로"]
```

### 3.2 Hybrid Search 파이프라인 (search_flavor_text)

```mermaid
flowchart TD
    Q["검색 쿼리 (재작성됨)"]

    subgraph CH1["① Vector Search (PGVector MMR)"]
        VEC_Q["쿼리 임베딩\n(OpenAI API)"]
        VEC_SEARCH["코사인 유사도 검색\nfetch_k=50\nMMR k=20, λ=0.7"]
        SID_PARSE["species_id 파싱\n포켓몬명 DB 조회 부착"]
    end

    subgraph CH2["② BM25 (rank_bm25 인메모리)"]
        BM25_Q["query.split() → 토큰화"]
        BM25_SCORE["BM25Okapi.get_scores()\nscore > 0 TOP 20"]
    end

    subgraph CH3["③ pg_trgm (PostgreSQL)"]
        TRGM_Q["similarity(content, query) > 0.05\nORDER BY similarity DESC\nLIMIT 20"]
    end

    subgraph FUSE["🔀 RRF Fusion (k=60)"]
        RRF["_reciprocal_rank_fusion()\n3채널 통합 정렬"]
        TOP5["상위 5개 반환\n(FLAVOR_TOP_N=5)"]
    end

    Q --> CH1 & CH2 & CH3
    CH1 --> VEC_Q --> VEC_SEARCH --> SID_PARSE
    CH2 --> BM25_Q --> BM25_SCORE
    CH3 --> TRGM_Q
    SID_PARSE & BM25_SCORE & TRGM_Q --> RRF --> TOP5
```

**채널 실패 처리:**
- 각 채널은 독립적으로 `try-except` 처리
- 실패한 채널은 빈 리스트로 대체
- 1개 채널만 성공해도 해당 채널 결과 반환

**MMR 파라미터:**

| 파라미터 | 값 | 의미 |
|---------|-----|------|
| `k` | 20 | 최종 반환 벡터 문서 수 |
| `fetch_k` | 50 | 유사도 기반 초기 후보 풀 |
| `lambda_mult` | 0.7 | 유사도(1.0) ↔ 다양성(0.0) 가중치 |

### 3.3 SQL 검색 파이프라인 (search_pokemon_db)

```mermaid
flowchart LR
    Q["자연어 질문 (재작성됨)"]
    Q --> LLM_SQL["LLM SQL 생성\n동점 처리: WHERE col=(SELECT MIN/MAX)\n코드블록 자동 제거"]
    LLM_SQL --> VALID["SQL 검증\nSELECT 여부 확인\n금지 키워드 차단"]
    VALID -->|"통과"| EXEC["psycopg2 실행"]
    VALID -->|"위반"| ERR1["오류 반환"]
    EXEC -->|"성공"| JSON_R["JSON 직렬화 반환"]
    EXEC -->|"실패"| ERR2["SQL 오류+힌트\n→ CRAG 스킵\nAgent 재시도"]
```

### 3.4 그래프 RAG 파이프라인 (Neo4j)

```mermaid
flowchart LR
    Q["포켓몬명 또는 타입명"]

    subgraph EVO["search_evolution_chain"]
        CYP1["진화 전: ←[:EVOLVES_TO] LIMIT 1"]
        CYP2["진화 후: [:EVOLVES_TO*1..3]→ DISTINCT\n메가/거다이맥스 필터"]
        FB["KNOWN_EVO_CONDITIONS\nfallback (친밀도 등)"]
    end

    subgraph TYPE["search_type_relations"]
        CYP3["AGAINST 기반 단일 타입 필터\n공격 효율 + 방어 특성\n+ 포켓몬 예시"]
    end

    subgraph WEAK["search_pokemon_weakness"]
        CYP4["HAS_TYPE → 타입 확인"]
        CYP5["AGAINST → 전 배율 조회\n버킷 분류 (4x/2x/0.5x/0.25x/0x)"]
    end

    Q --> EVO & TYPE & WEAK
```

### 3.5 CRAG 평가 파이프라인

```mermaid
flowchart LR
    RESULT["툴 실행 결과"]
    RESULT --> CHECK{"빈 결과?\nSQL 오류?\ncount≥4?"}
    CHECK -->|"예"| SKIP["평가 생략\n(빈 메시지 or 재검색 SystemMessage)"]
    CHECK -->|"아니오"| GRADE["GPT-4o-mini 판정\nYES / NO"]
    GRADE -->|"YES"| PASS["통과 (빈 메시지)"]
    GRADE -->|"NO"| RETRY["재검색 유도\nSystemMessage 삽입"]
```

---

## 4. 컨텍스트 윈도우 관리 전략

```
┌────────────────────────────────────────────────────────┐
│  LLM 컨텍스트 윈도우                                   │
│                                                        │
│  [SystemMessage]  ← SYSTEM_PROMPT (환각 방지 강화)     │
│  [HumanMessage]   ← 재작성된 사용자 질문               │
│  [AIMessage]      ← tool_calls 포함 응답               │
│  [ToolMessage]    ← 툴 실행 결과                       │
│  [SystemMessage]  ← CRAG 재검색 유도 (관련 없을 때)    │
│  [AIMessage]      ← 재시도 tool_calls                  │
│  [ToolMessage]    ← 재시도 툴 결과                     │
│  ...              ← 최대 5회 반복                      │
│  [SystemMessage]  ← "5회 초과, 지금 바로 답변하세요"   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**툴 호출 제한 정책:**

| 조건 | 동작 |
|------|------|
| `tool_call_count < 5` | 정상 툴 호출 허용 |
| `tool_call_count >= 5` | 강제 종료 SystemMessage 삽입 |
| LLM이 여전히 tool_calls 반환 시 | `response.tool_calls = []` 강제 초기화 |
| CRAG 평가 시점 | `tool_call_count >= 4` 이면 평가 생략 |

---

## 5. 임베딩 모델 사양

| 항목 | 값 |
|------|-----|
| 모델명 | `text-embedding-ada-002` |
| 벡터 차원 | 1536 |
| 최대 입력 토큰 | 8,191 |
| 인덱스 타입 (PGVector) | IVFFlat 또는 HNSW |
| 유사도 측정 | 코사인 유사도 |
| 적용 컬렉션 | `langchain_pg_embedding` (`collection_name="flavor_text"`) |

---

## 6. 데이터 품질 관리

| 항목 | 처리 방식 |
|------|---------|
| 중복 임베딩 방지 | `similarity_search` 사전 확인 → 있으면 건너뜀 (idempotent) |
| NULL 콘텐츠 | `WHERE content IS NOT NULL` 조건으로 필터링 |
| SQL 인젝션 방지 | SELECT 전용 + 금지 키워드 차단 |
| 벡터 결과 중복 억제 | MMR (lambda_mult=0.7) |
| 키워드 결과 다양성 | BM25 + pg_trgm 채널 추가 → RRF로 통합 |
| 관련 없는 결과 보정 | CRAG 평가 후 재검색 유도 |
| 환각 방지 | System Prompt에 "결과에 없는 내용 절대 생성 금지" 명시 |
| 동점 처리 | 서브쿼리 `WHERE col = (SELECT MIN/MAX ...)` 강제 |
| 진화 조건 누락 보완 | `KNOWN_EVO_CONDITIONS` fallback 맵 적용 |
