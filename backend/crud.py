from sqlalchemy.orm import Session
from sqlalchemy import or_
import models


def get_pokemon_list(db: Session, skip: int = 0, limit: int = 20, search: str = None):
    query = db.query(models.Pokemon)
    if search:
        filters = [models.Pokemon.name.ilike(f"%{search}%")]
        if search.isdigit():
            filters.append(models.Pokemon.id == int(search))
        query = query.filter(or_(*filters))
    return query.order_by(models.Pokemon.id).offset(skip).limit(limit).all()


def get_pokemon_count(db: Session, search: str = None) -> int:
    query = db.query(models.Pokemon)
    if search:
        filters = [models.Pokemon.name.ilike(f"%{search}%")]
        if search.isdigit():
            filters.append(models.Pokemon.id == int(search))
        query = query.filter(or_(*filters))
    return query.count()


def get_pokemon_by_id(db: Session, pokemon_id: int):
    return db.query(models.Pokemon).filter(models.Pokemon.id == pokemon_id).first()


def get_pokemon_by_name(db: Session, name: str):
    return db.query(models.Pokemon).filter(models.Pokemon.name.ilike(f"%{name}%")).first()
