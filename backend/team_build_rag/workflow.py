"""
LangGraph workflow for Hybrid RAG.

목적:
    사용자의 팀 분석/추천 요청을 LangGraph 노드 흐름으로 실행합니다.

흐름:
    __start__
      -> supervisor
      -> select_graph_tool
      -> execution_graph_tool
      -> vector_search
      -> evaluate_with_llm
      -> hybrid_scorer
      -> answer_generator
      -> __end__
"""

from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from team_build_rag.answer_generator import generate_answer
from team_build_rag.graph_tools import (
    build_vector_query_from_graph,
    execute_graph_tool,
    select_graph_tool,
)
from team_build_rag.hybrid_retriever import build_hybrid_context
from team_build_rag.hybrid_scorer import calculate_hybrid_score
from team_build_rag.state import HybridRagState, append_error, get_request_type
from team_build_rag.vector_search import search_vector_documents


# WORKFLOW_MERMAID:
# - 문서, README, Streamlit 화면 등에 그대로 붙여서 볼 수 있는 Mermaid 다이어그램입니다.
# - 실제 실행 그래프와 같은 순서를 유지해야 하므로 workflow.add_edge(...) 순서와 함께 관리합니다.
WORKFLOW_MERMAID = """
flowchart TD
    START([__start__])
    SUP[supervisor<br/>요청 검증]
    SELECT[select_graph_tool<br/>분석/추천 도구 선택]
    GRAPH[execution_graph_tool<br/>Neo4j Graph DB 실행]
    VECTOR[vector_search<br/>pgvector 근거 검색]
    EVAL[evaluate_with_llm<br/>Graph + Vector 근거 결합]
    RERANK[hybrid_scorer<br/>Graph + Vector 점수 결합]
    ANSWER[answer_generator<br/>LLM 기반 AI 해설 생성]
    END([__end__])

    START --> SUP
    SUP --> SELECT
    SELECT --> GRAPH
    GRAPH --> VECTOR
    VECTOR --> EVAL
    EVAL --> RERANK
    RERANK --> ANSWER
    ANSWER --> END

    GRAPH -. Graph DB 계산 결과 .-> EVAL
    VECTOR -. Vector DB 검색 근거 .-> EVAL
    EVAL -. RAG Context .-> ANSWER
""".strip()


def describe_workflow() -> Dict[str, Any]:
    """Team Build RAG 워크플로우를 문서화/시각화하기 위한 설명 데이터를 반환합니다."""

    # nodes:
    # - 화면이나 문서에서 각 노드가 어떤 역할인지 보여주기 위한 메타데이터입니다.
    nodes = [
        {"name": "__start__", "purpose": "LangGraph 실행 시작점"},
        {"name": "supervisor", "purpose": "pokemon_ids 5마리 여부와 요청 타입을 검증"},
        {"name": "select_graph_tool", "purpose": "analysis/recommendation에 맞는 Graph 도구 선택"},
        {"name": "execution_graph_tool", "purpose": "Neo4j 기반 팀 분석 또는 추천 실행"},
        {"name": "vector_search", "purpose": "Graph 결과를 검색 문장으로 바꾸고 pgvector 근거 검색"},
        {"name": "evaluate_with_llm", "purpose": "Graph 결과와 Vector 근거를 하나의 RAG context로 결합"},
        {"name": "hybrid_scorer", "purpose": "Graph 점수와 Vector 근거 점수를 합쳐 hybrid_score 계산"},
        {"name": "answer_generator", "purpose": "RAG context를 프롬프트로 만들어 LLM AI 해설 생성"},
        {"name": "__end__", "purpose": "LangGraph 실행 종료점"},
    ]

    # edges:
    # - 실제 workflow.add_edge(...)와 같은 순서입니다.
    edges = [
        ("__start__", "supervisor"),
        ("supervisor", "select_graph_tool"),
        ("select_graph_tool", "execution_graph_tool"),
        ("execution_graph_tool", "vector_search"),
        ("vector_search", "evaluate_with_llm"),
        ("evaluate_with_llm", "hybrid_scorer"),
        ("hybrid_scorer", "answer_generator"),
        ("answer_generator", "__end__"),
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "mermaid": WORKFLOW_MERMAID,
    }


def supervisor(state: HybridRagState) -> Dict[str, Any]:
    """요청 상태를 점검하고 워크플로우 실행 준비를 하는 첫 번째 노드입니다."""

    # pokemon_ids:
    # - 현재 팀 빌더 흐름은 반드시 5마리 포켓몬을 기준으로 분석/추천합니다.
    pokemon_ids = state.get("pokemon_ids", [])
    if len(pokemon_ids) != 5:
        return append_error(state, "하이브리드 RAG는 포켓몬 5마리를 기준으로 실행됩니다.")

    # request_type:
    # - 잘못된 값이 들어오면 analysis로 정규화합니다.
    request_type = get_request_type(state)
    if request_type not in ("analysis", "recommendation"):
        return {"request_type": "analysis"}

    return {"request_type": request_type}


def vector_search_node(state: HybridRagState) -> Dict[str, Any]:
    """Vector DB 검색 전 query 생성과 실제 검색을 순서대로 수행하는 노드입니다."""

    # query_update:
    # - Graph DB 결과에서 Vector DB 검색용 질의문을 만듭니다.
    query_update = build_vector_query_from_graph(state)
    merged_state = {**state, **query_update}

    # search_update:
    # - 현재는 placeholder 검색이지만, 나중에 pgvector/Elasticsearch 검색으로 교체됩니다.
    search_update = search_vector_documents(merged_state)
    return {**query_update, **search_update}


def evaluate_with_llm(state: HybridRagState) -> Dict[str, Any]:
    """
    LLM 평가 단계입니다.

    현재 구현:
        - 실제 LLM 호출 전 단계로 Graph/Vector 근거를 하나의 context로 묶습니다.
        - 이후 OpenAI/Groq 모델을 붙이면 이 함수 내부에서 평가 문장을 생성하면 됩니다.
    """

    return build_hybrid_context(state)


def build_hybrid_rag_workflow():
    """LangGraph 워크플로우를 생성하고 컴파일하는 함수입니다."""

    # workflow:
    # - 각 노드가 HybridRagState를 입력받고 일부 상태 업데이트 dict를 반환합니다.
    workflow = StateGraph(HybridRagState)

    workflow.add_node("supervisor", supervisor)
    workflow.add_node("select_graph_tool", select_graph_tool)
    workflow.add_node("execution_graph_tool", execute_graph_tool)
    workflow.add_node("vector_search", vector_search_node)
    workflow.add_node("evaluate_with_llm", evaluate_with_llm)
    workflow.add_node("hybrid_scorer", calculate_hybrid_score)
    workflow.add_node("answer_generator", generate_answer)

    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "select_graph_tool")
    workflow.add_edge("select_graph_tool", "execution_graph_tool")
    workflow.add_edge("execution_graph_tool", "vector_search")
    workflow.add_edge("vector_search", "evaluate_with_llm")
    workflow.add_edge("evaluate_with_llm", "hybrid_scorer")
    workflow.add_edge("hybrid_scorer", "answer_generator")
    workflow.add_edge("answer_generator", END)

    return workflow.compile()


# hybrid_rag_app:
# - 서비스 계층에서 바로 invoke할 수 있도록 컴파일된 LangGraph 앱을 모듈 로딩 시점에 준비합니다.
hybrid_rag_app = build_hybrid_rag_workflow()
