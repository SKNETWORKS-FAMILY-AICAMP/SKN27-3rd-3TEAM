"""
Graph tools for Hybrid RAG.

목적:
    LangGraph 워크플로우에서 사용할 Neo4j 기반 도구 함수를 모아둡니다.
    실제 계산은 기존 service 계층을 재사용하고, 이 파일은 RAG 노드에서 호출하기 쉬운 형태로 감싸는 역할을 합니다.
"""

from typing import Any, Dict

from services.team_analysis_service import analyze_team
from services.team_builder_service import recommend_team_member

from team_build_rag.state import HybridRagState, get_limit, get_request_type


# GRAPH_TOOL_TEAM_ANALYSIS:
# - 선택한 5마리 포켓몬의 약점/저항/타입 분포/기술 커버리지를 조회하는 도구 이름입니다.
GRAPH_TOOL_TEAM_ANALYSIS = "team_analysis"

# GRAPH_TOOL_TEAM_RECOMMENDATION:
# - 선택한 5마리를 기준으로 6번째 포켓몬 후보를 추천하는 도구 이름입니다.
GRAPH_TOOL_TEAM_RECOMMENDATION = "team_recommendation"


def select_graph_tool(state: HybridRagState) -> Dict[str, Any]:
    """요청 타입에 따라 실행할 Graph DB 도구를 선택하는 함수입니다."""

    # request_type:
    # - analysis면 덱 분석 도구를 사용하고, recommendation이면 추천 도구를 사용합니다.
    request_type = get_request_type(state)
    if request_type == "recommendation":
        return {"selected_graph_tool": GRAPH_TOOL_TEAM_RECOMMENDATION}

    return {"selected_graph_tool": GRAPH_TOOL_TEAM_ANALYSIS}


def execute_graph_tool(state: HybridRagState) -> Dict[str, Any]:
    """선택된 Graph DB 도구를 실제로 실행하는 함수입니다."""

    # graph:
    # - Neo4jClient 객체입니다. FastAPI dependency에서 만들어진 객체를 상태로 전달받습니다.
    graph = state["graph"]

    # pokemon_ids:
    # - 사용자가 선택한 5마리 포켓몬 ID입니다.
    pokemon_ids = state["pokemon_ids"]

    # selected_graph_tool:
    # - 이전 단계 select_graph_tool에서 결정된 도구 이름입니다.
    selected_graph_tool = state.get("selected_graph_tool", GRAPH_TOOL_TEAM_ANALYSIS)

    if selected_graph_tool == GRAPH_TOOL_TEAM_RECOMMENDATION:
        result = recommend_team_member(
            pokemon_ids=pokemon_ids,
            graph=graph,
            limit=get_limit(state),
        )
        return {"graph_result": result}

    result = analyze_team(pokemon_ids=pokemon_ids, graph=graph)
    return {"graph_result": result}


def build_vector_query_from_graph(state: HybridRagState) -> Dict[str, Any]:
    """Graph DB 결과를 바탕으로 Vector DB 검색용 문장을 만드는 함수입니다."""

    # graph_result:
    # - 분석/추천 결과에서 검색 키워드가 될 타입, 포켓몬 이름, 추천 이유를 꺼냅니다.
    graph_result = state.get("graph_result", {})
    request_type = get_request_type(state)

    if request_type == "recommendation":
        analysis = graph_result.get("analysis", {})
        recommendations = graph_result.get("recommendations", [])
        weak_types = analysis.get("weak_types", [])
        candidate_names = [item.get("name", "") for item in recommendations[:3]]
        weak_type_names = [item.get("type_name", "") for item in weak_types[:3]]
        useful_move_names = [
            move.get("move_name", "")
            for candidate in recommendations[:3]
            for move in candidate.get("useful_moves", [])[:3]
        ]
        query = (
            "포켓몬 팀 추천 설명 "
            f"후보: {', '.join(candidate_names)} "
            f"보완 약점 타입: {', '.join(weak_type_names)} "
            f"대표 기술: {', '.join(useful_move_names)}"
        )
        return {"vector_query": query.strip()}

    insights = graph_result.get("insights", {})
    weak_types = graph_result.get("weak_types", [])
    selected_pokemon = graph_result.get("selected_pokemon", [])
    pokemon_names = [item.get("name", "") for item in selected_pokemon]
    weak_type_names = [item.get("type_name", "") for item in weak_types[:3]]
    query = (
        "포켓몬 덱 분석 설명 "
        f"팀 성격: {insights.get('team_identity', '')} "
        f"선택 포켓몬: {', '.join(pokemon_names)} "
        f"주의 타입: {', '.join(weak_type_names)}"
    )
    return {"vector_query": query.strip()}
