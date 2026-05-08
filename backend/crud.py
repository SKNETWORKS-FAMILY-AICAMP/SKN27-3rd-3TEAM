from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import models
from typing import List, Optional

def get_pokemon_list(
    db: Session, 
    skip: int = 0, 
    limit: int = 20, 
    search: str = None,
    type_names: List[str] = None,
    min_id: int = None,
    max_id: int = None,
    ability: str = None
):
    query = db.query(models.Pokemon)
    
    if search:
        filters = [models.Pokemon.name.ilike(f"%{search}%")]
        if search.isdigit():
            filters.append(models.Pokemon.id == int(search))
        query = query.filter(or_(*filters))
        
    if type_names and len(type_names) > 0:
        query = query.join(models.Pokemon.types).join(models.PokemonType.type_)
        # OR logic for types
        query = query.filter(models.Type.name.in_(type_names))
        
    if min_id is not None:
        query = query.filter(models.Pokemon.species_id >= min_id)
    if max_id is not None:
        query = query.filter(models.Pokemon.species_id <= max_id)
        
    if ability:
        query = query.join(models.Pokemon.abilities).join(models.PokemonAbility.ability)
        query = query.filter(models.Ability.name == ability)
        
    return query.order_by(models.Pokemon.species_id, models.Pokemon.id).offset(skip).limit(limit).all()


def get_pokemon_count(
    db: Session, 
    search: str = None,
    type_names: List[str] = None,
    min_id: int = None,
    max_id: int = None,
    ability: str = None
) -> int:
    query = db.query(models.Pokemon)
    
    if search:
        filters = [models.Pokemon.name.ilike(f"%{search}%")]
        if search.isdigit():
            filters.append(models.Pokemon.id == int(search))
        query = query.filter(or_(*filters))
        
    if type_names and len(type_names) > 0:
        query = query.join(models.Pokemon.types).join(models.PokemonType.type_)
        query = query.filter(models.Type.name.in_(type_names))
        
    if min_id is not None:
        query = query.filter(models.Pokemon.species_id >= min_id)
    if max_id is not None:
        query = query.filter(models.Pokemon.species_id <= max_id)
        
    if ability:
        query = query.join(models.Pokemon.abilities).join(models.PokemonAbility.ability)
        query = query.filter(models.Ability.name == ability)
        
    return query.count()


def get_evolution_chain(db: Session, species_id: int) -> List[dict]:
    """
    재귀적으로 전체 진화 트리를 구축합니다. (분기 진화 지원)
    """
    # 1. 최하위(Base) 종 찾기 (뒤로 거슬러 올라감)
    base_species_id = species_id
    while True:
        prev_evo = db.query(models.Evolution).filter(models.Evolution.to_species_id == base_species_id).first()
        if not prev_evo:
            break
        base_species_id = prev_evo.from_species_id

    # 2. 트리 구축을 위한 재귀 함수
    def build_node(s_id: int, min_level: int = None) -> Optional[dict]:
        species = db.query(models.Species).filter(models.Species.id == s_id).first()
        if not species:
            return None
            
        # 대표 포켓몬 찾기 (is_default 우선)
        pokemon = db.query(models.Pokemon).filter(
            models.Pokemon.species_id == s_id,
            models.Pokemon.is_default == True
        ).first()
        if not pokemon:
            pokemon = db.query(models.Pokemon).filter(models.Pokemon.species_id == s_id).first()
        
        if not pokemon:
            return None

        # 해당 종의 모든 형태(Varieties) 가져오기
        varieties = db.query(models.Pokemon).filter(models.Pokemon.species_id == s_id).all()
        
        # 다음 진화 단계들 찾기
        next_evolutions = db.query(models.Evolution).filter(models.Evolution.from_species_id == s_id).all()
        
        return {
            "id": pokemon.id,
            "name": pokemon.name,
            "image_url": pokemon.image_url,
            "min_level": min_level,
            "varieties": [
                {
                    "id": v.id, 
                    "name": v.name, 
                    "is_default": v.is_default, 
                    "image_url": v.image_url,
                    "types": v.types
                }
                for v in varieties
            ],
            "evolves_to": [
                res for res in [build_node(evo.to_species_id, evo.min_level) for evo in next_evolutions]
                if res is not None
            ]
        }

    # 3. 루트(최하위 종)부터 트리 시작
    root_node = build_node(base_species_id)
    return [root_node] if root_node else []


def get_abilities(db: Session) -> List[str]:
    return [a.name for a in db.query(models.Ability).order_by(models.Ability.name).all()]


def get_pokemon_by_id(db: Session, pokemon_id: int):
    # This will return the DB model. The router will add evolution_chain manually if needed.
    return db.query(models.Pokemon).filter(models.Pokemon.id == pokemon_id).first()

