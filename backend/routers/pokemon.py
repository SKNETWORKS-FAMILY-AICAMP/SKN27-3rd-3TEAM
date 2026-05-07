from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

import crud
import schemas
import models
from database import get_db

router = APIRouter(
    prefix="/api/v1/pokemon",
    tags=["pokemon"],
)


@router.get("/", response_model=schemas.PaginatedPokemonResponse)
def read_pokemon_list(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(1025, ge=1, le=1025, description="가져올 항목 수 (최대 1025)"),
    search: Optional[str] = Query(None, description="이름 또는 ID로 검색"),
    types: Optional[List[str]] = Query(None, description="타입 이름 목록 (예: '불꽃', '물')"),
    min_id: Optional[int] = Query(None, description="최소 도감 번호"),
    max_id: Optional[int] = Query(None, description="최대 도감 번호"),
    db: Session = Depends(get_db)
):
    """
    포켓몬 목록 조회. 페이지네이션, 이름/ID 검색, 타입 및 번호 범위 필터링 지원.
    """
    total = crud.get_pokemon_count(db, search=search, type_names=types, min_id=min_id, max_id=max_id)
    items = crud.get_pokemon_list(db, skip=skip, limit=limit, search=search, type_names=types, min_id=min_id, max_id=max_id)
    return schemas.PaginatedPokemonResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items
    )


@router.get("/{pokemon_id}", response_model=schemas.PokemonDetailResponse)
def read_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    """
    특정 포켓몬 상세 조회 (스탯, 타입, 설명, 진화 트리 포함).
    """
    db_pokemon = crud.get_pokemon_by_id(db, pokemon_id=pokemon_id)
    if db_pokemon is None:
        raise HTTPException(status_code=404, detail=f"Pokemon #{pokemon_id} not found")
        
    # Pydantic 모델로 변환 후 수동으로 데이터 주입
    response_data = schemas.PokemonDetailResponse.model_validate(db_pokemon).model_dump()
    
    # 설명(Flavor Text), 진화 트리, 분류, 성별 정보 주입
    if db_pokemon.species:
        # 진화 트리 가져오기
        response_data["evolution_chain"] = crud.get_evolution_chain(db, db_pokemon.species.id)
        
        # 설명 가져오기
        if db_pokemon.species.flavor_texts:
            response_data["description"] = db_pokemon.species.flavor_texts[0].content
        else:
            response_data["description"] = "설명이 등록되어 있지 않습니다."
            
        # 분류 주입
        response_data["classification"] = db_pokemon.species.classification or "기록 없음"
        
        # 성별 비율 계산
        gr = db_pokemon.species.gender_rate
        if gr == -1:
            response_data["gender_ratio"] = "성별 불명"
        elif gr is not None:
            female_percent = (gr / 8.0) * 100
            male_percent = 100 - female_percent
            response_data["gender_ratio"] = f"♂ {male_percent}% ♀ {female_percent}%"
        else:
            response_data["gender_ratio"] = "데이터 없음"
            
        # 형태 전환(Varieties) 정보 주입
        if db_pokemon.species_id:
            varieties = db.query(models.Pokemon).filter(
                models.Pokemon.species_id == db_pokemon.species_id
            ).all()
            response_data["varieties"] = [
                {"id": v.id, "name": v.name, "is_default": v.is_default, "image_url": v.image_url}
                for v in varieties
            ]
        else:
            response_data["varieties"] = []
    else:
        response_data["description"] = "종 정보가 없습니다."
        response_data["evolution_chain"] = []
        response_data["classification"] = "기록 없음"
        response_data["gender_ratio"] = "데이터 없음"
        response_data["varieties"] = []
        
    return response_data

