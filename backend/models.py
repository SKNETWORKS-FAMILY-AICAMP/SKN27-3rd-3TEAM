from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Float, ForeignKey, Text, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(BigInteger, unique=True, index=True)
    login = Column(String(100), unique=True, index=True)
    name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    email = Column(String(100), nullable=True)
    public_repos = Column(Integer, default=0)
    total_commits = Column(Integer, default=0)
    total_stars = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    game_logs = relationship("GameLog", back_populates="user")


class GameLog(Base):
    __tablename__ = "game_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    game_type = Column(String(50), nullable=False)  # "silhouette", "memory"
    pokemon_id = Column(Integer, ForeignKey("pokemon.id", ondelete="SET NULL"), nullable=True)
    is_correct = Column(Boolean, default=False)
    hint_used = Column(Boolean, default=False)
    wrong_answer_id = Column(Integer, ForeignKey("pokemon.id", ondelete="SET NULL"), nullable=True)
    log_data = Column(Text, nullable=True)  # 추가적인 데이터 (예: 메모리 게임 이동 횟수 등 JSON 저장)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="game_logs")
    pokemon = relationship("Pokemon", foreign_keys=[pokemon_id])
    wrong_pokemon = relationship("Pokemon", foreign_keys=[wrong_answer_id])


class TeamBuildLog(Base):
    __tablename__ = "team_build_logs"

    # id는 팀 빌더 저장 기록 1건을 구분하기 위한 고유 번호입니다.
    id = Column(Integer, primary_key=True, index=True)

    # user_id는 어떤 사용자가 만든 팀인지 연결하기 위한 값입니다. 로그인 없이도 저장할 수 있게 nullable=True로 둡니다.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # selected_pokemon_ids는 사용자가 선택한 5마리 포켓몬 id 목록을 JSON 배열로 저장합니다.
    selected_pokemon_ids = Column(JSONB, nullable=False)

    # analysis_result는 덱 분석 화면에 보여준 전체 분석 결과를 JSON 형태로 저장합니다.
    analysis_result = Column(JSONB, nullable=True)

    # analysis_conclusion은 분석 AI 종합 해설 중 "결론:" 문장만 따로 저장합니다.
    analysis_conclusion = Column(Text, nullable=True)

    # recommended_pokemon_ids는 추천된 1~3순위 포켓몬 id 목록을 JSON 배열로 저장합니다.
    recommended_pokemon_ids = Column(JSONB, nullable=True)

    # recommendation_result는 추천 화면에 보여준 전체 추천 결과를 JSON 형태로 저장합니다.
    recommendation_result = Column(JSONB, nullable=True)

    # recommendation_conclusion은 추천 AI 종합 해설 중 "결론:" 문장만 따로 저장합니다.
    recommendation_conclusion = Column(Text, nullable=True)
