from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List, Optional


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
    public_repos: Optional[int] = 0
    total_commits: Optional[int] = 0
    total_stars: Optional[int] = 0

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)


# ── Game Log ──
class GameLogCreate(BaseModel):
    user_id: Optional[int] = None
    game_type: str  # "silhouette", "memory"
    pokemon_id: Optional[int] = None
    is_correct: bool = False
    hint_used: bool = False
    wrong_answer_id: Optional[int] = None
    log_data: Optional[str] = None


# ?? Team Builder Log ??
class TeamBuildLogCreate(BaseModel):
    # user_id는 로그인 사용자가 있을 때만 들어오는 값입니다.
    user_id: Optional[int] = None

    # selected_pokemon_ids는 사용자가 팀 빌더에서 선택한 5마리 포켓몬 id 목록입니다.
    selected_pokemon_ids: List[int]

    # analysis_result는 덱 분석 화면의 전체 결과 JSON입니다.
    analysis_result: Optional[Dict[str, Any]] = None

    # analysis_conclusion은 분석 AI 해설의 "결론:" 부분만 따로 저장하는 요약 문장입니다.
    analysis_conclusion: Optional[str] = None

    # recommended_pokemon_ids는 추천 결과 1~3순위 포켓몬 id 목록입니다.
    recommended_pokemon_ids: Optional[List[int]] = None

    # recommendation_result는 추천 화면의 전체 결과 JSON입니다.
    recommendation_result: Optional[Dict[str, Any]] = None

    # recommendation_conclusion은 추천 AI 해설의 "결론:" 부분만 따로 저장하는 요약 문장입니다.
    recommendation_conclusion: Optional[str] = None


class TeamBuildLogResponse(TeamBuildLogCreate):
    # id는 저장된 팀 빌더 기록 1건을 식별하는 고유 번호입니다.
    id: int

    model_config = ConfigDict(from_attributes=True)


# ── Pagination wrapper ──
class PaginatedPokemonResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[PokemonListResponse]
