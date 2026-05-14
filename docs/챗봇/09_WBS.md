# WBS (Work Breakdown Structure)

**프로젝트명:** 포켓몬 AI 챗봇  
**문서 버전:** v1.2  
**작성일:** 2025-05-14  
**최종 수정:** 2025-05-14 (Hybrid Search, CRAG, Query Rewriting, KNOWN_EVO_CONDITIONS 작업 추가 / web_search 제거)  
**총 기간:** 10주 (Phase 1~5)

---

## 1. WBS 전체 구조

```mermaid
gantt
    title 포켓몬 AI 챗봇 개발 WBS
    dateFormat  YYYY-MM-DD
    section Phase 1: 환경 구성 및 데이터
        요구사항 분석 및 문서화         :done,    p1-1, 2025-05-01, 5d
        개발 환경 구성 (Docker)         :done,    p1-2, 2025-05-05, 3d
        PostgreSQL 스키마 설계 및 생성  :done,    p1-3, 2025-05-05, 3d
        Neo4j 그래프 스키마 설계        :done,    p1-4, 2025-05-06, 3d
        데이터 수집 및 적재 (PokéAPI)   :done,    p1-5, 2025-05-06, 3d

    section Phase 2: 기본 검색 엔진 개발
        search_pokemon_db Tool        :done,    p2-3, 2025-05-09, 1d
        search_flavor_text (벡터만)    :done,    p2-4, 2025-05-09, 1d
        Neo4j Tool 3종 개발            :done,    p2-5, 2025-05-10, 1d
        기본 LangGraph Agent 구성      :done,    p2-6, 2025-05-11, 1d
        Neo4j 그래프 로더 개발         :done,    p2-2, 2025-05-12, 1d
        PGVector 임베딩 파이프라인     :done,    p2-1, 2025-05-13, 1d

    section Phase 3: 고도화 (Hybrid Search + CRAG)
        BM25 인덱스 빌드 및 통합       :done,  p3-1, 2025-05-14, 1d
        pg_trgm 검색 통합              :done,  p3-2, 2025-05-14, 1d
        RRF 결합 및 search_flavor_text 리팩터 :done, p3-3, 2025-05-14, 1d
        Query Rewriting 구현          : done,        p3-4, 2025-05-14, 1d
        CRAG 노드 구현                : done,        p3-5, 2025-05-14, 1d
        KNOWN_EVO_CONDITIONS fallback :  done,       p3-6, 2025-05-14, 1d
        동점 처리 SQL 패턴 검증        : done,        p3-7, 2025-05-14, 1d
        System Prompt v1.2 개정       :  done,       p3-8, 2025-05-14, 1d

    section Phase 4: API 및 UI 통합 
        FastAPI 서버 연결             :done,         p4-1, 2025-05-09, 1d
        Agent ↔ API 통합 테스트        :done,         p4-2, 2025-05-14, 1d
        채팅 UI 연결                   : done,        p4-3, 2025-05-09, 1d
        E2E 통합 테스트                :done,         p4-4, 2025-05-14, 1d

    section Phase 5: 품질 및 배포 
        RAG 평가 (RAGAS + 커스텀 지표) : done,,        p5-1, 2025-05-14, 4d
        성능 최적화 (BM25·pg_trgm 튜닝): done,        p5-2, 2025-05-14, 3d
        문서 정리 및 배포              :done,         p5-3, 2025-05-14, 4d
```

---

## 2. 상세 작업 분류

### Phase 1: 환경 구성 및 데이터 (1~2주차)

| ID | 작업명 | 담당 | 기간 | 산출물 | 상태 |
|----|--------|------|------|--------|------|
| 1.1 | 요구사항 분석 | 전체 | 5일 | 요구사항명세서 v1.2 | ✅ 완료 |
| 1.2 | Docker Compose 환경 구성 | 인프라 | 3일 | docker-compose.yml | ✅ 완료 |
| 1.3 | PostgreSQL 스키마 설계 및 DDL | DB | 3일 | schema.sql (pg_trgm 포함) | ✅ 완료 |
| 1.4 | Neo4j 그래프 스키마 설계 | DB | 2일 | 그래프 스키마 문서 | ✅ 완료 |
| 1.5 | PokéAPI 데이터 수집 스크립트 | 백엔드 | 3일 | data_collector.py | ✅ 완료 |
| 1.6 | 정형 데이터 적재 (pokemon 테이블) | DB | 2일 | 적재 완료 확인서 | ✅ 완료 |

### Phase 2: 기본 검색 엔진 개발 (3~5주차)

| ID | 작업명 | 담당 | 기간 | 산출물 | 상태 |
|----|--------|------|------|--------|------|
| 2.1 | flavor_text.json 전처리 | 백엔드 | 2일 | flavor_text.json | ✅ 완료 |
| 2.2 | ingest.py — PGVector 임베딩 파이프라인 | 백엔드 | 2일 | ingest.py | ✅ 완료 |
| 2.3 | graph_loader.py — Neo4j 적재 (AGAINST 관계 포함) | 백엔드 | 4일 | graph_loader.py | ✅ 완료 |
| 2.4 | search_pokemon_db Tool 개발 | 백엔드 | 2일 | pokemon_agent.py | ✅ 완료 |
| 2.5 | search_flavor_text Tool (벡터 단독) | 백엔드 | 2일 | pokemon_agent.py | ✅ 완료 |
| 2.6 | search_evolution_chain Tool + KNOWN_EVO_CONDITIONS 기초 | 백엔드 | 2일 | pokemon_neo4j.py | ✅ 완료 |
| 2.7 | search_type_relations Tool (AGAINST 기반, 방어 섹션 포함) | 백엔드 | 2일 | pokemon_neo4j.py | ✅ 완료 |
| 2.8 | search_pokemon_weakness Tool | 백엔드 | 1일 | pokemon_neo4j.py | ✅ 완료 |
| 2.9 | 기본 LangGraph Agent (agent/tools 2-노드) | AI | 2일 | pokemon_agent.py | ✅ 완료 |
| 2.10 | chat_history.py — 세션 CRUD | 백엔드 | 2일 | chat_history.py | ✅ 완료 |
| 2.11 | System Prompt v1.0 작성 | AI | 2일 | 프롬프트 명세서 | ✅ 완료 |

### Phase 3: 고도화 (6~7주차)

| ID | 작업명 | 담당 | 기간 | 산출물 | 상태 |
|----|--------|------|------|--------|------|
| 3.1 | BM25 인덱스 빌드 (rank_bm25, 인메모리) | AI | 3일 | pokemon_agent.py | ✅ 완료 |
| 3.2 | pg_trgm GIN 인덱스 설정 및 검색 통합 | DB/백엔드 | 2일 | pokemon_agent.py, schema.sql | ✅ 완료 |
| 3.3 | RRF 결합 및 search_flavor_text 리팩터링 | AI | 3일 | pokemon_agent.py | ✅ 완료 |
| 3.4 | Query Rewriting 구현 (`_rewrite_query`) | AI | 2일 | pokemon_agent.py | ✅ 완료 |
| 3.5 | CRAG 노드 구현 (`crag_check_node`) | AI | 3일 | pokemon_agent.py | ✅ 완료 |
| 3.6 | agent→tools→crag 3-노드 LangGraph 재구성 | AI | 1일 | pokemon_agent.py | ✅ 완료 |
| 3.7 | KNOWN_EVO_CONDITIONS fallback 맵 완성 | AI | 2일 | pokemon_neo4j.py | ✅ 완료 |
| 3.8 | 동점 처리 SQL 서브쿼리 패턴 검증 | QA | 2일 | 테스트 케이스 | ✅ 완료 |
| 3.9 | System Prompt v1.2 개정 (핵심 규칙 신설) | AI | 2일 | 프롬프트 명세서 | ✅ 완료 |
| 3.10 | MAX_TOOL_CALLS 5로 상향 및 회귀 테스트 | QA | 1일 | 테스트 결과서 | ✅ 완료 |

### Phase 4: API 및 UI 통합 (8주차) — 타 담당자

| ID | 작업명 | 담당 | 기간 | 산출물 | 상태 |
|----|--------|------|------|--------|------|
| 4.1 | FastAPI 기본 구조 설정 | `[외부]` 백엔드 | 1일 | main.py | ✅ 완료 |
| 4.2 | POST /chat 엔드포인트 구현 | `[외부]` 백엔드 | 2일 | routers/chat.py | ✅ 완료 |
| 4.3 | GET/POST/DELETE /sessions 구현 | `[외부]` 백엔드 | 2일 | routers/sessions.py | ✅ 완료 |
| 4.4 | Agent-API 통합 테스트 | `[외부]` QA | 3일 | 테스트 결과서 | ✅ 완료 |
| 4.5 | 채팅 UI 메인 화면 개발 (SCR-01) | `[외부]` 프론트 | 3일 | ChatPage.tsx | ✅ 완료 |
| 4.6 | 세션 사이드바 개발 (SCR-02) | `[외부]` 프론트 | 1일 | SessionSidebar.tsx | ✅ 완료 |
| 4.7 | 툴 뱃지 + CRAG 재검색 표시 (SCR-04) | `[외부]` 프론트 | 1일 | ToolBadge.tsx | ✅ 완료 |
| 4.8 | E2E 시나리오 테스트 (12개) | `[외부]` QA | 3일 | E2E 테스트 결과서 | ✅ 완료 |

### Phase 5: 품질 및 배포 (9~10주차) — 타 담당자

| ID | 작업명 | 담당 | 기간 | 산출물 | 상태 |
|----|--------|------|------|--------|------|
| 5.1 | RAG 평가 (RAGAS + Tool Routing + Dual-type 지표) | `[외부]` AI | 4일 | RAG 평가 보고서 | ✅ 완료 |
| 5.2 | System Prompt 최종 튜닝 | `[외부]` AI | 2일 | 프롬프트 v1.2 Final | ✅ 완료 |
| 5.3 | Hybrid Search 파라미터 최적화 (RRF k, MMR λ) | `[외부]` AI | 2일 | 성능 보고서 | ✅ 완료 |
| 5.4 | CRAG 판정 임계값 조정 | `[외부]` AI | 1일 | CRAG 튜닝 기록 | ✅ 완료 |
| 5.5 | 쿼리 응답 시간 측정 및 인덱스 최적화 | `[외부]` DB | 2일 | 성능 보고서 | ✅ 완료 |
| 5.6 | Docker 이미지 빌드 및 배포 스크립트 | `[외부]` 인프라 | 2일 | Dockerfile, CI/CD | ✅ 완료 |

### Phase 5: 품질 및 배포 (9~10주차) — 본인

| ID | 작업명 | 담당 | 기간 | 산출물 | 상태 |
|----|--------|------|------|--------|------|
| 5.7 | 최종 문서 정리 (11개 문서 패키지) | **본인** | 2일 | 전체 문서 패키지 | ✅ 완료 |

---

## 3. 마일스톤

| 마일스톤 | 목표일 | 완료 기준 |
|---------|--------|---------|
| M1: 데이터 적재 완료 | 2주차 말 | 모든 DB 적재, ingest.py 실행 성공 |
| M2: 기본 Agent 동작 확인 | 5주차 말 | 5개 Tool 호출 성공, 멀티턴 대화 동작 |
| M3: 고도화 완료 | 7주차 말 | Hybrid Search, CRAG, Query Rewriting 동작 확인 |
| M4: API 통합 완료 | 8주차 말 | 전 엔드포인트 통합 테스트 통과 |
| M5: 서비스 배포 | 10주차 말 | Docker Compose 배포, RAG 평가 기준 충족 |

---

## 4. 리스크 및 대응 방안

| 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|--------|---------|--------|---------|
| OpenAI API 비용 초과 | 중 | 중 | Query Rewriting·CRAG도 gpt-4o-mini 사용, 토큰 모니터링 |
| BM25 빌드 시간 지연 (대규모 도감) | 낮 | 중 | 비동기 초기화 또는 서버 시작 시 사전 빌드 |
| pg_trgm similarity 임계값 부적절 | 중 | 낮 | 0.05 기준값을 평가 후 조정 |
| CRAG 과도한 재검색 루프 | 낮 | 중 | count >= MAX-1 생략 + 완화 판정 기준(YES 우선) |
| LangGraph 버전 호환성 | 낮 | 고 | requirements.txt 버전 고정 |
| Neo4j 쿼리 성능 저하 | 낮 | 중 | 인덱스 추가, 쿼리 최적화 |
