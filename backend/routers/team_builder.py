"""
Team builder API router.

목적:
    프론트엔드 팀빌딩 화면에서 선택한 5마리 포켓몬을 받아
    Graph DB 기반 팀 분석과 추천 결과를 반환합니다.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from graph.neo4j_client import Neo4jClient, get_neo4j
from services.team_analysis_service import analyze_team
from services.team_builder_service import recommend_team_member


# router는 팀 분석/추천 API 주소를 묶기 위한 FastAPI 라우터입니다.
router = APIRouter(
    prefix="/api/v1/team-builder",
    tags=["team-builder"],
)


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


def _handle_value_error(error: ValueError) -> None:
    """
    서비스 레이어에서 발생한 검증 오류를 HTTP 400으로 바꾸기 위해 작성한 함수입니다.

    Args:
        error: 서비스 함수에서 발생한 ValueError입니다.
    """
    raise HTTPException(status_code=400, detail=str(error))


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
