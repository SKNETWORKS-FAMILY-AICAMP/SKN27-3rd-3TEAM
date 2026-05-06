from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base


class Pokemon(Base):
    __tablename__ = "pokemon"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    height = Column(Integer)
    weight = Column(Integer)
    base_exp = Column(Integer)
    image_url = Column(String(255))
    cry_url = Column(String(255))
    is_default = Column(Boolean, default=True)

    stats = relationship("PokemonStats", back_populates="pokemon", uselist=False, cascade="all, delete-orphan")
    types = relationship("PokemonType", back_populates="pokemon", cascade="all, delete-orphan")
    species = relationship("Species", back_populates="pokemon", uselist=False, cascade="all, delete-orphan")


class PokemonStats(Base):
    __tablename__ = "pokemon_stats"

    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True)
    hp = Column(Integer, nullable=False)
    attack = Column(Integer, nullable=False)
    defense = Column(Integer, nullable=False)
    sp_attack = Column(Integer, nullable=False)
    sp_defense = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)

    pokemon = relationship("Pokemon", back_populates="stats")


class Type(Base):
    __tablename__ = "types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)


class PokemonType(Base):
    __tablename__ = "pokemon_types"

    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True)
    type_id = Column(Integer, ForeignKey("types.id", ondelete="CASCADE"), primary_key=True)
    slot = Column(Integer, nullable=False)

    pokemon = relationship("Pokemon", back_populates="types")
    type_ = relationship("Type", lazy="joined")


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, index=True)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"))
    generation = Column(Integer)
    capture_rate = Column(Integer)

    pokemon = relationship("Pokemon", back_populates="species")
    flavor_texts = relationship("FlavorText", back_populates="species", cascade="all, delete-orphan")


class FlavorText(Base):
    __tablename__ = "flavor_text"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"))
    version_name = Column(String(50))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)

    species = relationship("Species", back_populates="flavor_texts")


class PokemonKnowledge(Base):
    __tablename__ = "pokemon_knowledge"

    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
