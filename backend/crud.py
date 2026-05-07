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
    max_id: int = None
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
        query = query.filter(models.Pokemon.id >= min_id)
    if max_id is not None:
        query = query.filter(models.Pokemon.id <= max_id)
        
    return query.order_by(models.Pokemon.id).offset(skip).limit(limit).all()


def get_pokemon_count(
    db: Session, 
    search: str = None,
    type_names: List[str] = None,
    min_id: int = None,
    max_id: int = None
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
        query = query.filter(models.Pokemon.id >= min_id)
    if max_id is not None:
        query = query.filter(models.Pokemon.id <= max_id)
        
    return query.count()


def get_evolution_chain(db: Session, species_id: int) -> List[dict]:
    # Very basic linear evolution chain resolution for UI
    # Finds the base species, then walks forward
    chain = []
    
    # 1. Find base species (walk backwards)
    current_species_id = species_id
    while True:
        prev_evo = db.query(models.Evolution).filter(models.Evolution.to_species_id == current_species_id).first()
        if not prev_evo:
            break
        current_species_id = prev_evo.from_species_id
        
    # 2. Walk forwards and build chain
    while current_species_id:
        species = db.query(models.Species).filter(models.Species.id == current_species_id).first()
        pokemon = db.query(models.Pokemon).filter(models.Pokemon.id == species.pokemon_id).first() if species else None
        
        if pokemon:
            # Find how we got here to get min_level
            min_level = None
            if len(chain) > 0:
                evo_link = db.query(models.Evolution).filter(
                    models.Evolution.from_species_id == chain[-1]['species_id'],
                    models.Evolution.to_species_id == current_species_id
                ).first()
                if evo_link:
                    min_level = evo_link.min_level
            
            chain.append({
                "id": pokemon.id,
                "name": pokemon.name,
                "image_url": pokemon.image_url,
                "min_level": min_level,
                "species_id": current_species_id
            })
            
        next_evo = db.query(models.Evolution).filter(models.Evolution.from_species_id == current_species_id).first()
        if not next_evo:
            break
        current_species_id = next_evo.to_species_id
        
    return chain


def get_pokemon_by_id(db: Session, pokemon_id: int):
    # This will return the DB model. The router will add evolution_chain manually if needed.
    return db.query(models.Pokemon).filter(models.Pokemon.id == pokemon_id).first()

