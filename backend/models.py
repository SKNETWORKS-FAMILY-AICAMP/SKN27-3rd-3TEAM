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
    species_id = Column(Integer, ForeignKey("species.id", ondelete="SET NULL"), nullable=True)

    stats = relationship("PokemonStats", back_populates="pokemon", uselist=False, cascade="all, delete-orphan")
    types = relationship("PokemonType", back_populates="pokemon", cascade="all, delete-orphan")
    species = relationship("Species", back_populates="pokemon_varieties", foreign_keys=[species_id])
    abilities = relationship("PokemonAbility", back_populates="pokemon", cascade="all, delete-orphan")



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
    classification = Column(String(50))
    gender_rate = Column(Integer)

    pokemon_varieties = relationship("Pokemon", back_populates="species", foreign_keys="Pokemon.species_id")
    flavor_texts = relationship("FlavorText", back_populates="species", cascade="all, delete-orphan")


class FlavorText(Base):
    __tablename__ = "flavor_text"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"))
    version_name = Column(String(50))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)

    species = relationship("Species", back_populates="flavor_texts")


class Ability(Base):
    __tablename__ = "abilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    effect_text = Column(Text)
    embedding = Column(Vector(1536), nullable=True)


class PokemonAbility(Base):
    __tablename__ = "pokemon_abilities"

    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True)
    ability_id = Column(Integer, ForeignKey("abilities.id", ondelete="CASCADE"), primary_key=True)
    is_hidden = Column(Boolean, nullable=False)
    slot = Column(Integer, nullable=False)

    pokemon = relationship("Pokemon", back_populates="abilities")
    ability = relationship("Ability", lazy="joined")


class Evolution(Base):
    __tablename__ = "evolutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"))
    to_species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"))
    min_level = Column(Integer, nullable=True)
    trigger_item_id = Column(Integer, nullable=True)

    from_species = relationship("Species", foreign_keys=[from_species_id], backref="evolves_to")
    to_species = relationship("Species", foreign_keys=[to_species_id], backref="evolves_from")


class PokemonKnowledge(Base):
    __tablename__ = "pokemon_knowledge"

    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="CASCADE"), primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)

