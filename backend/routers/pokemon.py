from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

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
    limit: int = Query(20, ge=1, le=100, description="가져올 항목 수 (최대 100)"),
    search: Optional[str] = Query(None, description="이름 또는 ID로 검색"),
    db: Session = Depends(get_db)
):
    """
    포켓몬 목록 조회. 페이지네이션 및 이름/ID 검색 지원.
    """
    total = crud.get_pokemon_count(db, search=search)
    items = crud.get_pokemon_list(db, skip=skip, limit=limit, search=search)
    return schemas.PaginatedPokemonResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items
    )


@router.get("/{pokemon_id}", response_model=schemas.PokemonDetailResponse)
def read_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    """
    특정 포켓몬 상세 조회 (스탯, 타입 포함).
    """
    db_pokemon = crud.get_pokemon_by_id(db, pokemon_id=pokemon_id)
    if db_pokemon is None:
        raise HTTPException(status_code=404, detail=f"Pokemon #{pokemon_id} not found")
    return db_pokemon
