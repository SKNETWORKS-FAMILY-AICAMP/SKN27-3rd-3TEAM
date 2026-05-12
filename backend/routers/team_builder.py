"""
Team builder API router.

목적:
    프론트엔드 팀빌딩 화면에서 선택한 5마리 포켓몬을 받아
    Graph DB 기반 팀 분석과 추천 결과를 반환합니다.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from graph.neo4j_client import Neo4jClient, get_neo4j
from build_services.team_analysis_service import analyze_team
from build_services.team_builder_service import recommend_team_member
from build_services.team_rag_service import run_team_rag


# router는 팀 분석/추천 API 주소를 묶기 위한 FastAPI 라우터입니다.
router = APIRouter(
    prefix="/api/v1/team-builder",
    tags=["team-builder"],
)


# TEAM_BUILDER_POKEMON_OPTIONS:
# - 팀 빌딩 선택 화면에서 사용할 포켓몬 목록 조회 Cypher입니다.
# - Pokemon 노드에서 이름/이미지/기본 종족값을 가져오고,
#   HAS_TYPE 관계를 통해 타입 이름을 함께 모읍니다.
# - Species 노드가 연결되어 있으면 세대 정보도 같이 내려줍니다.
TEAM_BUILDER_POKEMON_OPTIONS = """
MATCH (p:Pokemon)
WHERE p.pokemon_id < 10000
OPTIONAL MATCH (p)-[:HAS_TYPE]->(t:Type)
OPTIONAL MATCH (p)-[:IS_SPECIES]->(s:Species)
OPTIONAL MATCH (p)-[:CAN_HAVE]->(a:Ability)
WITH p,
     s,
     collect(DISTINCT t.name) AS type_names,
     collect(DISTINCT a.name) AS ability_names
RETURN p.pokemon_id AS pokemon_id,
       p.name AS name,
       p.image_url AS image_url,
       s.generation AS generation,
       p.base_total AS base_total,
       type_names AS types,
       ability_names AS abilities
ORDER BY pokemon_id
"""


class TeamBuilderRequest(BaseModel):
    """
    팀 분석/추천 요청 데이터를 표현하기 위해 작성한 모델입니다.

    Attributes:
        pokemon_ids: 사용자가 선택한 포켓몬 ID 5개입니다.
    """

    pokemon_ids: List[int] = Field(
        ...,
        min_length=5,
        max_length=5,
        description="선택한 포켓몬 ID 5개",
    )


    user_id: Optional[int] = Field(
        None,
        description="로그인 사용자가 있을 때만 전달하는 사용자 ID",
    )


class TeamRecommendationRequest(TeamBuilderRequest):
    """
    추천 요청 데이터를 표현하기 위해 작성한 모델입니다.

    Attributes:
        limit: 추천받을 포켓몬 수입니다. 기본값은 3입니다.
    """

    limit: int = Field(
        3,
        ge=1,
        le=10,
        description="추천 후보 개수",
    )
    analysis_result: Optional[Dict[str, Any]] = Field(
        None,
        description="추천 저장 시 함께 보관할 직전 덱 분석 전체 결과",
    )
    analysis_conclusion: Optional[str] = Field(
        None,
        description="추천 저장 시 함께 보관할 직전 덱 분석 결론 문장",
    )


def _handle_value_error(error: ValueError) -> None:
    """
    서비스 레이어에서 발생한 검증 오류를 HTTP 400으로 바꾸기 위해 작성한 함수입니다.

    Args:
        error: 서비스 함수에서 발생한 ValueError입니다.
    """
    raise HTTPException(status_code=400, detail=str(error))


def _extract_conclusion(result: Dict[str, Any]) -> Optional[str]:
    """AI 종합 해설에서 첫 번째 '결론:' 문단만 따로 꺼내 저장하기 위한 함수입니다."""

    # final_answer:
    # - RAG API가 사용자에게 보여주는 최종 AI 해설 문장입니다.
    final_answer = str(result.get("final_answer") or "").strip()
    if not final_answer:
        return None

    # 결론 문단은 화면 요약과 DB 목록 조회에서 바로 쓰기 좋도록 별도 컬럼에 저장합니다.
    if final_answer.startswith("결론:"):
        return final_answer.split("\n\n", 1)[0].strip()

    conclusion_index = final_answer.find("결론:")
    if conclusion_index >= 0:
        return final_answer[conclusion_index:].split("\n\n", 1)[0].strip()

    return final_answer.split("\n\n", 1)[0].strip()


def _extract_recommended_pokemon_ids(result: Dict[str, Any]) -> List[int]:
    """추천 결과 JSON에서 1~3순위 추천 포켓몬 ID만 뽑아 저장하기 위한 함수입니다."""

    # recommendation_result:
    # - RAG 추천 응답은 reranked_result 안에 최종 추천 목록이 들어갈 수 있습니다.
    recommendation_result = result.get("reranked_result") or result.get("graph_result") or result
    recommendations = recommendation_result.get("recommendations", [])

    # recommended_ids:
    # - DB에는 추천 카드 전체 JSON과 별도로 추천 포켓몬 id 목록만 따로 저장합니다.
    recommended_ids: List[int] = []
    for item in recommendations:
        pokemon_id = item.get("pokemon_id")
        if pokemon_id is not None:
            recommended_ids.append(int(pokemon_id))

    return recommended_ids


def _json_ready(data: Dict[str, Any]) -> Dict[str, Any]:
    """DB JSONB 컬럼에 안전하게 들어가도록 FastAPI JSON 변환을 적용합니다."""

    return jsonable_encoder(data)


@router.get("/pokemon-options")
def pokemon_options_endpoint(graph: Neo4jClient = Depends(get_neo4j)):
    """
    팀 빌딩 선택 화면에서 사용할 포켓몬 카드 목록을 반환하는 API입니다.

    프론트엔드 사용 흐름:
        1. teambuilding.py가 이 API를 호출합니다.
        2. Neo4j에서 포켓몬 이름, 이미지, 세대, 타입을 조회합니다.
        3. 프론트는 받은 타입 목록을 카드 안에 배지로 표시합니다.
    """
    return graph.run_query(TEAM_BUILDER_POKEMON_OPTIONS)


@router.post("/analyze")
def analyze_team_endpoint(
    request: TeamBuilderRequest,
    graph: Neo4jClient = Depends(get_neo4j),
):
    """
    선택한 5마리 포켓몬의 팀 약점과 타입 커버리지를 분석하기 위해 작성한 API입니다.

    프론트엔드 사용 흐름:
        1. 사용자가 5마리 포켓몬을 선택합니다.
        2. pokemon_ids를 이 API로 보냅니다.
        3. 약점 타입, 저항 타입, 타입 분포, 기술 타입 커버리지를 반환합니다.
    """
    try:
        return analyze_team(request.pokemon_ids, graph)
    except ValueError as error:
        _handle_value_error(error)


@router.post("/recommend")
def recommend_team_member_endpoint(
    request: TeamRecommendationRequest,
    graph: Neo4jClient = Depends(get_neo4j),
):
    """
    선택한 5마리 포켓몬을 기준으로 부족한 1마리를 추천하기 위해 작성한 API입니다.

    프론트엔드 사용 흐름:
        1. 사용자가 5마리 포켓몬을 선택합니다.
        2. pokemon_ids와 추천 개수를 이 API로 보냅니다.
        3. Graph DB 기반 추천 후보 1~3순위와 추천 이유를 반환합니다.
    """
    try:
        return recommend_team_member(
            pokemon_ids=request.pokemon_ids,
            graph=graph,
            limit=request.limit,
        )
    except ValueError as error:
        _handle_value_error(error)


@router.post("/rag-analyze")
def rag_analyze_team_endpoint(
    request: TeamBuilderRequest,
    graph: Neo4jClient = Depends(get_neo4j),
):
    """
    LangGraph 기반 Hybrid RAG로 팀 분석 설명을 생성하는 API입니다.

    프론트엔드 사용 흐름:
        1. 사용자가 5마리 포켓몬을 선택합니다.
        2. pokemon_ids를 이 API로 보냅니다.
        3. Graph DB 분석 결과, Vector 검색 근거, 최종 설명 문장을 함께 반환합니다.
    """
    try:
        # 분석 단계는 화면에 보여줄 결과만 반환합니다.
        # DB 저장은 추천까지 완료된 시점에 한 번만 수행해서 같은 팀 기록이 중복 저장되지 않게 합니다.
        return run_team_rag(
            pokemon_ids=request.pokemon_ids,
            graph=graph,
            request_type="analysis",
        )
    except ValueError as error:
        _handle_value_error(error)


@router.post("/rag-recommend")
def rag_recommend_team_member_endpoint(
    request: TeamRecommendationRequest,
    graph: Neo4jClient = Depends(get_neo4j),
    db: Session = Depends(get_db),
):
    """
    LangGraph 기반 Hybrid RAG로 6번째 포켓몬 추천 설명을 생성하는 API입니다.

    프론트엔드 사용 흐름:
        1. 사용자가 5마리 포켓몬을 선택합니다.
        2. pokemon_ids와 limit를 이 API로 보냅니다.
        3. Graph DB 추천 후보, 재정렬 결과, 최종 추천 설명 문장을 함께 반환합니다.
    """
    try:
        result = run_team_rag(
            pokemon_ids=request.pokemon_ids,
            graph=graph,
            request_type="recommendation",
            limit=request.limit,
        )

        # 추천 결과가 정상 생성되면 같은 5마리 선택 조합의 최신 분석 로그에 이어서 저장합니다.
        # 추천이 완료된 시점에 분석 결과와 추천 결과를 한 행으로 저장합니다.
        # 이렇게 하면 "분석만 누른 기록"과 "추천까지 완료한 기록"이 따로 쌓이지 않습니다.
        analysis_result = _json_ready(request.analysis_result) if request.analysis_result else None
        analysis_conclusion = request.analysis_conclusion or _extract_conclusion(
            request.analysis_result or {}
        )
        saved_log = crud.create_team_build_log(
            db,
            schemas.TeamBuildLogCreate(
                user_id=request.user_id,
                selected_pokemon_ids=request.pokemon_ids,
                analysis_result=analysis_result,
                analysis_conclusion=analysis_conclusion,
                recommended_pokemon_ids=_extract_recommended_pokemon_ids(result),
                recommendation_result=_json_ready(result),
                recommendation_conclusion=_extract_conclusion(result),
            ),
        )
        result["team_build_log_id"] = saved_log.id
        return result
    except ValueError as error:
        _handle_value_error(error)
