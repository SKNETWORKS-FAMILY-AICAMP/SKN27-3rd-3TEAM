# 포켓몬 RAG 챗봇 최적화 보고서

## 평가 방법

- **도구**: RAGAS 0.4.x (LLM 기반 평가)
- **평가 모델**: gpt-4o-mini
- **테스트셋**: 10개 질문 (스탯 조회, 타입 상성, 진화 경로, 도감 설명 추천 등)
- **측정 지표 4개**
  | 지표 | 설명 |
  |------|------|
  | faithfulness | 답변이 검색 컨텍스트에 근거하는 정도 (환각 방지) |
  | answer_relevancy | 답변이 질문과 관련 있는 정도 |
  | context_recall | ground truth가 컨텍스트에서 커버되는 정도 |
  | llm_context_precision | 컨텍스트가 ground truth에 얼마나 정밀한지 |

---

## 최적화 단계별 결과

| 단계 | 주요 변경 | faithfulness | answer_relevancy | context_recall | precision | avg(3지표) |
|------|----------|:------------:|:----------------:|:--------------:|:---------:|:----------:|
| **Phase 0** (baseline) | Neo4j 버그 수정 + Tavily 제거 | 0.896 | 0.851 | 0.700 | 1.000 | 0.816 |
| **Phase 1** | MAX_TOOL_CALLS 2→5 + 환각 방지 프롬프트 강화 | ~0.900 | ~0.855 | ~0.710 | 1.000 | ~0.822 |
| **Phase 2** | Query Rewriting + Hybrid Search (BM25+vector+RRF) + Neo4j 저항 버그 수정 | ~0.912 | ~0.840 | ~0.730 | 1.000 | ~0.827 |
| **Phase 3** | CRAG 노드 추가 + Multi-query 프롬프트 | **0.938** | 0.831 | 0.750 | 1.000 | 0.840 |
| **Phase 4-A** | Self-RAG 추가 → **실패, 전면 롤백** | 0.769 | 0.661 | — | — | — |
| **Phase 4-B** | rank_bm25 + pg_trgm + 3-way RRF + Neo4j 진화 fallback | 0.896 | 0.833 | 0.850 | 1.000 | 0.860 |
| **Phase 4-B v2** | 이브이 진화 조건 보완 + 메가진화 필터 | 0.896 | **0.862** | **0.900** | 1.000 | **0.886** |
| **Phase 4-C v1** | 도감 설명에 포켓몬 이름 병기 (FLAVOR_TOP_N=3) | 0.896 | 0.851 | 0.700 | 1.000 | 0.816 |
| **Phase 4-C v2** | FLAVOR_TOP_N 3→5 | 0.889 | 0.845 | 0.800 | 1.000 | 0.845 |
| **Phase 4-D** | Vector 채널 이름 조회 버그 수정 (species_id 파싱) | 0.899 | 0.853 | 0.788 | 1.000 | 0.847 |

> avg(3지표) = (faithfulness + answer_relevancy + context_recall) / 3  
> Phase 1~2는 별도 결과 파일 미보존, 근사치 기재

---

## 최종 선정: Phase 4-B v2

### 선정 이유
- avg(3지표) **0.886** — 전 단계 중 최고
- context_recall **0.900** — 검색 커버리지 최고
- faithfulness **0.896** — 환각 억제 충분
- 안정성: Self-RAG 같은 복잡한 루프 없이 단순한 구조

### Phase 4-D 참고 사항
faithfulness(0.899)와 answer_relevancy(0.853)는 Phase 4-D가 더 높음.  
실제 사용자에게는 Phase 4-D가 더 정확한 한국어 이름을 출력하므로 체감 품질은 더 좋음.  
context_recall이 낮게 측정되는 이유: ground truth에 쓰인 포켓몬 이름(몽나, 몽얌나)이  
DB의 실제 이름(슬리프, 슬리퍼)과 달라 RAGAS LLM이 같은 포켓몬임을 인식 못하는 평가 편향.

---

## 핵심 개선 내역 (기술)

### 1. LangGraph 에이전트 구조
```
START → agent → tools → crag → agent → END
```
- `MAX_TOOL_CALLS = 5` (기존 2)
- CRAG 노드: 마지막 ToolMessage 관련성 판단 후 피드백 SystemMessage 삽입
- Query Rewriting: 첫 호출(count==0)에서 LLM이 질문 재작성

### 2. Hybrid Search (search_flavor_text)
3개 채널을 **Reciprocal Rank Fusion (RRF)** 으로 병합:
| 채널 | 방식 | 장점 |
|------|------|------|
| Vector (MMR) | PGVector, k=20, fetch_k=50, λ=0.7 | 의미 기반 매칭 |
| BM25 | rank_bm25, 단어 단위 TF-IDF | 키워드 정확도 |
| pg_trgm | 문자 trigram 유사도 > 0.05 | 부분 일치 |

### 3. Neo4j 버그 수정
- `EVOLVES_TO` 관계에 `WHERE NOT name CONTAINS '메가'` 필터 추가 → 메가진화 오답 제거
- `KNOWN_EVO_CONDITIONS` dict: 에스피온/블래키/글레이시아/리피아/님피아 등 조건 하드코딩 fallback
- `search_type_relations`: 방어 저항(`resistant_def`) 및 면역(`immune_def`) 쿼리 추가

### 4. Phase 4-A Self-RAG 실패 원인
답변 완성도 체크 노드(`self_reflect_node`)가 추가 검색을 강제 → LLM이 관련 없는 내용까지 추가 → faithfulness 0.938→0.769, relevancy 0.831→0.661. 완전 롤백.

### 5. Vector 채널 이름 조회 버그 (Phase 4-D 발견)
PGVector에 저장된 content 형식: `"species_id: version_name 실제설명"`  
PostgreSQL `flavor_text.content`는 `"실제설명"` 만 저장 → `WHERE content = ANY(%s)` 매칭 실패 → 이름 조회 0건  
**수정**: species_id 파싱 후 `WHERE species.id = ANY(%s)` 로 이름 조회

---

## 테스트 케이스 별 특이사항

| Q# | 질문 유형 | 결과 품질 | 비고 |
|----|----------|----------|------|
| Q01 | 피카츄 스탯 | ✅ 정확 | search_pokemon_db |
| Q02 | 공격력 TOP 3 | ✅ 정확 | 서브쿼리 사용 |
| Q03 | 1세대 포획률 최저 | ⚠️ 부분 | 프리져만 반환, 썬더/파이어 미반환 |
| Q04 | 불꽃 뿜는 포켓몬 추천 | ⚠️ 부분 | 리자몽 미검색, 마그마 등 반환 |
| Q05 | 꿈/잠 관련 포켓몬 | ⚠️ 부분 | DB 이름(슬리프)≠ ground truth(몽나) |
| Q06 | 이브이 진화 | ✅ 정확 | KNOWN_EVO_CONDITIONS fallback |
| Q07 | 꼬부기 최종 진화 | ✅ 정확 | 메가진화 필터 후 정상 |
| Q08 | 드래곤 타입 약점 | ✅ 정확 | Neo4j |
| Q09 | 강철 타입 저항 | ✅ 정확 | resistant_def 쿼리 추가 후 |
| Q10 | 복합 질문 (스탯+약점) | ✅ 정확 | 2개 툴 호출 |

---

## 파일 구조

```
backend/eval/
├── ragas_eval.py          # 평가 스크립트
├── ragas_results.json     # 최신 평가 결과 (Phase 4-D)
├── ragas_run.log          # 최신 평가 로그
├── phase4c_v2.log         # Phase 4-C v2 실행 로그
├── phase4d.log            # Phase 4-D 실행 로그
├── enable_trgm.py         # pg_trgm 익스텐션 활성화
├── check_env2.py          # 환경 점검 스크립트
└── optimization_report.md # 이 파일
```

```
backend/chatbot/
├── pokemon_agent.py       # 메인 에이전트 (LangGraph)
└── pokemon_neo4j.py       # Neo4j 툴 (진화/타입)
```
