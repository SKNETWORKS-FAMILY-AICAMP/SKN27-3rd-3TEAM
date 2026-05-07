from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

import crud
import schemas
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
    특정 포켓몬 상세 조회 (스탯, 타입, 특성, 진화 트리 포함).
    """
    db_pokemon = crud.get_pokemon_by_id(db, pokemon_id=pokemon_id)
    if db_pokemon is None:
        raise HTTPException(status_code=404, detail=f"Pokemon #{pokemon_id} not found")
        
    # Convert SQLAlchemy model to dict so we can inject the evolution chain
    # Pydantic's from_attributes=True will handle the rest
    response_data = schemas.PokemonDetailResponse.model_validate(db_pokemon).model_dump()
    
    # Resolve evolution chain if species exists
    if db_pokemon.species:
        evo_chain = crud.get_evolution_chain(db, db_pokemon.species.id)
        response_data["evolution_chain"] = evo_chain
    else:
        response_data["evolution_chain"] = []
        
    return response_data

