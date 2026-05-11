from pydantic import BaseModel, ConfigDict
from typing import List, Optional


# ── Stats ──
class PokemonStatsResponse(BaseModel):
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int

    model_config = ConfigDict(from_attributes=True)


# ── Types ──
class TypeResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PokemonTypeResponse(BaseModel):
    slot: int
    type_: TypeResponse

    model_config = ConfigDict(from_attributes=True)


# ── Pokemon (List) ──
class PokemonListResponse(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    types: List[PokemonTypeResponse] = []
    species_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ── Abilities ──
class AbilityResponse(BaseModel):
    id: int
    name: str
    effect_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PokemonAbilityResponse(BaseModel):
    is_hidden: bool
    slot: int
    ability: AbilityResponse

    model_config = ConfigDict(from_attributes=True)

class PokemonVarietyResponse(BaseModel):
    id: int
    name: str
    is_default: bool
    image_url: Optional[str] = None
    types: List[PokemonTypeResponse] = []
    species_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

# ── Evolutions ──
class EvolutionNode(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    min_level: Optional[int] = None
    evolves_to: List['EvolutionNode'] = []
    varieties: List[PokemonVarietyResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# ── Pokemon (Detail) ──
class PokemonDetailResponse(BaseModel):
    id: int
    name: str
    height: Optional[int] = None
    weight: Optional[int] = None
    base_exp: Optional[int] = None
    image_url: Optional[str] = None
    cry_url: Optional[str] = None
    stats: Optional[PokemonStatsResponse] = None
    types: List[PokemonTypeResponse] = []
    abilities: List[PokemonAbilityResponse] = []
    evolution_chain: List[EvolutionNode] = []
    description: Optional[str] = None
    classification: Optional[str] = None
    gender_ratio: Optional[str] = None
    varieties: List[PokemonVarietyResponse] = []
    species_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)



# ── User ──
class UserBase(BaseModel):
    github_id: int
    login: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)


# ── Pagination wrapper ──
class PaginatedPokemonResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[PokemonListResponse]
