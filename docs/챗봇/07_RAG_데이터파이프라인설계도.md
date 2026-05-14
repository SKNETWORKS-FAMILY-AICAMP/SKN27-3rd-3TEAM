# RAG / 데이터 파이프라인 설계도

**프로젝트명:** 포켓몬 AI 챗봇  
**문서 버전:** v1.1  
**작성일:** 2025-05-14  
**최종 수정:** 2025-05-14 (search_pokemon_weakness 툴 추가, Graph RAG 경로 업데이트)

---

## 1. RAG 아키텍처 개요

본 시스템은 단일 벡터 검색 RAG가 아닌, **멀티-소스 RAG + Graph RAG** 구조를 채택한다.  
LLM이 질문의 의도에 따라 최적의 검색 경로를 자율 선택한다.

```mermaid
flowchart TB
    Q["사용자 질문 (자연어)"]

    subgraph ROUTING["🧠 LLM 기반 라우팅 (자율 툴 선택)"]
        AGENT["GPT-4o-mini\nTool-calling Agent"]
    end

    subgraph RETRIEVAL["📡 검색 레이어"]
        R1["SQL Retrieval\n(정형 데이터)"]
        R2["Vector Retrieval\n(비정형 텍스트)"]
        R3["Graph Retrieval\n(관계 데이터)"]
    end

    subgraph AUGMENT["📚 Augmentation"]
        CTX["컨텍스트 통합\n(ToolNode → 메시지 추가)"]
    end

    subgraph GENERATE["✍️ Generation"]
        GEN["GPT-4o-mini\n최종 답변 생성"]
    end

    Q --> AGENT
    AGENT -->|search_pokemon_db| R1
    AGENT -->|search_flavor_text| R2
    AGENT -->|"search_evolution_chain\nsearch_type_relations\nsearch_pokemon_weakness ✨"| R3

    R1 & R2 & R3 & R4 --> CTX
    CTX --> GEN
    GEN --> ANS["최종 답변"]
```

---

## 2. 오프라인 데이터 파이프라인 (Indexing Pipeline)

데이터를 수집·가공하여 각 DB에 적재하는 사전 파이프라인이다.

```mermaid
flowchart LR
    subgraph SOURCE["📥 원천 데이터"]
        RAW_JSON["flavor_text.json\n(도감 설명 원문)"]
        RAW_CSV["pokemon 데이터\n(CSV / PokéAPI)"]
        RAW_GRAPH["진화·타입 관계\n(graph_loader.py)"]
    end

    subgraph PROCESS["⚙️ 전처리"]
        P1["텍스트 정제\n(species_id + version + content 조합)"]
        P2["Document 객체 생성\n(LangChain Document)"]
        P3["정형 테이블 변환\n(psycopg2 INSERT)"]
        P4["그래프 노드·엣지 생성\n(Cypher MERGE)"]
    end

    subgraph EMBED["🔢 임베딩"]
        EMB["OpenAI Embeddings API\ntext-embedding-ada-002\n1536차원"]
    end

    subgraph INDEX["🗄️ 인덱싱"]
        PG_IDX[("PostgreSQL\n정형 테이블 적재")]
        VEC_IDX[("PGVector\nlangchain_pg_embedding 컬렉션")]
        NEO_IDX[("Neo4j\n포켓몬·타입·아이템 그래프")]
    end

    RAW_JSON --> P1 --> P2 --> EMB --> VEC_IDX
    RAW_CSV --> P3 --> PG_IDX
    RAW_GRAPH --> P4 --> NEO_IDX
```

### 2.1 ingest.py 실행 흐름 (상세)

```mermaid
flowchart TD
    START(["ingest.py 실행"])
    CHECK["PGVector 컬렉션\n데이터 존재 확인\nsimilarity_search('포켓몬', k=1)"]
    
    CHECK -->|"결과 있음"| SKIP["⏭ 인덱싱 건너뜀\n(idempotent)"]
    CHECK -->|"결과 없음"| LOAD["flavor_text.json 로드"]
    
    LOAD --> BUILD["Document 객체 생성\n형식: 'species_id: version content'"]
    BUILD --> ADD["vectorstore.add_documents()\nOpenAI 임베딩 → PGVector 저장"]
    ADD --> DONE(["✅ 인덱싱 완료"])
    SKIP --> DONE
```

---

## 3. 온라인 RAG 파이프라인 (Inference Pipeline)

사용자 질문이 들어올 때 실시간으로 동작하는 RAG 흐름이다.

### 3.1 벡터 검색 파이프라인 (search_flavor_text)

```mermaid
flowchart LR
    Q["검색 쿼리\n예: '귀여운 전기 포켓몬'"]
    
    Q --> EMB["OpenAI Embeddings\n쿼리 벡터화 (1536차원)"]
    EMB --> FETCH["PGVector\nMMR fetch_k=50\n코사인 유사도 상위 50개 후보"]
    FETCH --> MMR["MMR 알고리즘\nk=20, lambda_mult=0.7\n유사도 + 다양성 균형"]
    MMR --> TOP["상위 20개 문서 선택"]
    TOP --> SLICE["상위 5개 반환\n(FLAVOR_TOP_N=5)"]
    SLICE --> CTX["Agent 컨텍스트 추가"]
```

**MMR 파라미터 설명:**

| 파라미터 | 값 | 의미 |
|---------|-----|------|
| `k` | 20 | 최종 반환 문서 수 |
| `fetch_k` | 50 | 유사도 기반 초기 후보 풀 |
| `lambda_mult` | 0.7 | 1.0에 가까울수록 유사도 중시, 0.0에 가까울수록 다양성 중시 |

### 3.2 SQL 검색 파이프라인 (search_pokemon_db)

```mermaid
flowchart LR
    Q["자연어 질문\n예: '공격력 높은 풀 타입'"]
    
    Q --> LLM_SQL["LLM SQL 생성\n(System Prompt의 스키마 참조)"]
    LLM_SQL --> VALID["SQL 검증\nSELECT 여부 확인\n금지 키워드 차단"]
    VALID -->|"통과"| EXEC["psycopg2\n쿼리 실행"]
    VALID -->|"위반"| ERR1["오류 메시지 반환"]
    EXEC -->|"성공"| JSON_R["JSON 직렬화\n결과 반환"]
    EXEC -->|"실패"| ERR2["SQL 오류 + 힌트\nLLM 재시도 유도"]
```

### 3.3 그래프 RAG 파이프라인 (Neo4j)

```mermaid
flowchart LR
    Q["포켓몬명 또는 타입명"]
    
    subgraph EVO["진화 체인 탐색 (search_evolution_chain)"]
        CYP1["Cypher: 진화 전 탐색\n(←[:EVOLVES_TO] LIMIT 1)"]
        CYP2["Cypher: 진화 후 탐색\n([:EVOLVES_TO*1..3]→ DISTINCT)"]
        ITEM["아이템 ID → 이름\n일괄 조회"]
    end
    
    subgraph TYPE["타입 상성 탐색 (search_type_relations)"]
        CYP3["공격 시 효과적\n(AGAINST: multiplier ≥ 2.0\n단일 타입 포켓몬 필터)"]
        CYP4["공격 시 비효과적\n(AGAINST: 0 < multiplier ≤ 0.5)"]
        CYP5["무효 타입\n(AGAINST: multiplier = 0.0)"]
        CYP6["약점·면역 포켓몬 예시\n(WEAK_AGAINST / IMMUNE_TO)"]
    end

    subgraph WEAK["포켓몬 약점 조회 (search_pokemon_weakness) ✨"]
        CYP7["타입 확인\n(HAS_TYPE)"]
        CYP8["전체 배율 조회\n(AGAINST: 모든 공격 타입)"]
        CYP9["버킷 분류\n4배 / 2배 / 0.5배 / 0.25배 / 0배"]
    end

    Q --> EVO & TYPE & WEAK
    EVO --> RESULT_E["진화 체인 텍스트"]
    TYPE --> RESULT_T["타입 상성 분석 텍스트\n(공격 효율 + 포켓몬 예시)"]
    WEAK --> RESULT_W["포켓몬 개체 약점/저항/면역\n(듀얼 타입 복합 배율 포함)"]
```

---

## 4. 컨텍스트 윈도우 관리 전략

LangGraph의 메시지 기반 상태 관리에서 컨텍스트를 효율적으로 구성한다.

```
┌────────────────────────────────────────────────────────┐
│  LLM 컨텍스트 윈도우                                   │
│                                                        │
│  [SystemMessage]  ← SYSTEM_PROMPT + DB 스키마 정의     │
│  [HumanMessage]   ← 사용자 이전 메시지 1               │
│  [AIMessage]      ← AI 이전 응답 1                     │
│  [HumanMessage]   ← 사용자 이전 메시지 2               │
│  [AIMessage]      ← AI 이전 응답 2                     │
│  ...              ← 대화 히스토리 (멀티턴)              │
│  [HumanMessage]   ← 현재 사용자 질문                   │
│  [AIMessage]      ← tool_calls 포함 응답               │
│  [ToolMessage]    ← 툴 실행 결과 (search_pokemon_db)   │
│  [ToolMessage]    ← 툴 실행 결과 (search_flavor_text)  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**툴 호출 제한 정책:**

| 조건 | 동작 |
|------|------|
| `tool_call_count < 2` | 정상 툴 호출 허용 |
| `tool_call_count >= 2` | SystemMessage로 강제 종료 유도 |
| LLM이 여전히 tool_calls 반환 시 | `response.tool_calls = []` 강제 초기화 |

---

## 5. 임베딩 모델 사양

| 항목 | 값 |
|------|-----|
| 모델명 | `text-embedding-ada-002` |
| 벡터 차원 | 1536 |
| 최대 입력 토큰 | 8,191 |
| 인덱스 타입 (PGVector) | IVFFlat 또는 HNSW |
| 유사도 측정 | 코사인 유사도 |
| 적용 테이블 | `flavor_text.embedding` |
| 적용 컬렉션 | `langchain_pg_embedding` (`collection_name="flavor_text"`) |

---

## 6. 데이터 품질 관리

| 항목 | 처리 방식 |
|------|---------|
| 중복 임베딩 방지 | `similarity_search` 사전 확인 후 건너뜀 |
| NULL 콘텐츠 | `WHERE content IS NOT NULL` 조건으로 필터링 |
| SQL 인젝션 방지 | SELECT 전용 허용 + 금지 키워드 차단 |
| 벡터 결과 품질 | MMR으로 중복 유사 문서 억제 |
| 웹 검색 결과 신뢰도 | 최후 수단으로만 사용, 출처 명시 필수 |
