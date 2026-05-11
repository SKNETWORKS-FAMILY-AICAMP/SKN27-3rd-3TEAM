# Team Build RAG 모듈 설명

`backend/team_build_rag`는 포켓몬 팀 빌딩 전용 Hybrid RAG 흐름을 담고 있습니다.

이 모듈은 단순히 LLM에게 질문을 던지는 구조가 아니라, `Neo4j Graph DB`로 계산한 팀 분석/추천 결과와 `pgvector`로 검색한 문서 근거를 함께 사용합니다.

## 전체 흐름

```text
START
  -> supervisor
  -> select_graph_tool
  -> execution_graph_tool
  -> vector_search
  -> evaluate_with_llm
  -> hybrid_scorer
  -> answer_generator
  -> END
```

## 파일 역할

| 파일 | 역할 |
| --- | --- |
| `state.py` | LangGraph 노드들이 공유하는 상태 구조를 정의합니다. |
| `graph_tools.py` | 덱 분석/포켓몬 추천 중 어떤 Graph 도구를 쓸지 고르고 실행합니다. |
| `vector_search.py` | Graph 결과를 검색 문장으로 바꾸고 pgvector 문서를 검색합니다. |
| `vector_scorer.py` | 검색된 Vector 문서가 후보 포켓몬/덱 분석을 얼마나 잘 뒷받침하는지 점수화합니다. |
| `scoring_policy.py` | Graph 점수와 Vector 점수를 합칠 가중치를 관리합니다. |
| `hybrid_scorer.py` | `graph_score`와 `vector_score`를 합쳐 `hybrid_score`를 계산합니다. |
| `hybrid_retriever.py` | Graph 결과와 Vector 문서를 LLM이 읽기 좋은 context로 묶습니다. |
| `answer_generator.py` | OpenAI LLM을 호출해서 최종 AI 해설 문장을 생성합니다. |
| `workflow.py` | LangGraph 워크플로우를 구성하고 컴파일합니다. |
| `workflow_diagram.md` | 워크플로우 구조를 Mermaid 다이어그램으로 설명합니다. |

## 점수 구조

| 점수 | 의미 |
| --- | --- |
| `graph_score` | 타입 약점 보완, 종족값, 기술 타입 커버리지 등 Graph DB 계산 기반 점수입니다. |
| `vector_score` | 후보 이름, 타입, 기술명과 Vector DB 문서가 얼마나 잘 연결되는지 나타내는 근거 점수입니다. |
| `hybrid_score` | Graph 점수와 Vector 점수를 가중합한 최종 추천 점수입니다. |

## 현재 가중치

| 요청 | Graph | Vector |
| --- | ---: | ---: |
| 덱 분석 | 60% | 40% |
| 포켓몬 추천 | 70% | 30% |
| AI 답변 생성 | 50% | 50% |

가중치를 바꾸고 싶으면 `backend/team_build_rag/scoring_policy.py`만 수정하면 됩니다.

주의할 점:

- 덱 분석/포켓몬 추천 가중치는 `hybrid_score` 같은 계산 결과에 영향을 줍니다.
- AI 답변 생성 가중치는 LLM이 설명을 만들 때 Graph DB 계산 근거와 Vector DB 검색 근거를 어느 정도 비중으로 설명할지 정하는 정책입니다.

## 왜 build_services와 분리했나

`backend/build_services`는 Graph DB 기반의 순수 계산 로직을 담당합니다.

`backend/team_build_rag`는 그 계산 결과를 Vector DB 근거와 합치고, LLM 답변으로 바꾸는 RAG 흐름을 담당합니다.

이렇게 나누면 추천 점수 계산과 RAG 해설 생성이 섞이지 않아서, 나중에 배틀 기능이나 다른 팀원이 만든 서비스와 충돌할 가능성이 줄어듭니다.
