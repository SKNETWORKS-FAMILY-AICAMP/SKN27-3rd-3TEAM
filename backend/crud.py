from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException
import models
import schemas
import json
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
        for type_name in type_names:
            type_subq = (
                db.query(models.PokemonType.pokemon_id)
                .join(models.Type)
                .filter(models.Type.name == type_name)
                .subquery()
            )
            query = query.filter(models.Pokemon.id.in_(type_subq))

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
        for type_name in type_names:
            type_subq = (
                db.query(models.PokemonType.pokemon_id)
                .join(models.Type)
                .filter(models.Type.name == type_name)
                .subquery()
            )
            query = query.filter(models.Pokemon.id.in_(type_subq))

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


def create_or_update_user(db: Session, user_data: schemas.UserCreate):
    try:
        print(f"DEBUG: Syncing user data for {user_data.login} (ID: {user_data.github_id})")
        db_user = db.query(models.User).filter(models.User.github_id == user_data.github_id).first()
        
        if db_user:
            print(f"DEBUG: Updating existing user ID {db_user.id}")
            db_user.login = user_data.login
            db_user.name = user_data.name
            db_user.avatar_url = user_data.avatar_url
            db_user.email = user_data.email
            # 이 지점에서 컬럼이 없으면 에러가 날 수 있음
            db_user.public_repos = user_data.public_repos
            db_user.total_commits = user_data.total_commits
            db_user.total_stars = user_data.total_stars
        else:
            print("DEBUG: Creating new user")
            db_user = models.User(
                github_id=user_data.github_id,
                login=user_data.login,
                name=user_data.name,
                avatar_url=user_data.avatar_url,
                email=user_data.email,
                public_repos=user_data.public_repos,
                total_commits=user_data.total_commits,
                total_stars=user_data.total_stars
            )
            db.add(db_user)
        
        db.commit()
        db.refresh(db_user)
        print(f"DEBUG: Successfully synced user {db_user.login}")
        return db_user
    except Exception as e:
        print(f"CRITICAL: User Sync Failed: {str(e)}")
        db.rollback()
        # 500 에러 원인을 클라이언트에게 조금 더 힌트 주기 위해 에러 메시지 포함
        raise HTTPException(status_code=500, detail=f"Database Sync Error: {str(e)}")


def create_game_log(db: Session, log_data: schemas.GameLogCreate):
    print(f"DEBUG: Attempting to save game log: {log_data}")
    try:
        db_log = models.GameLog(
            user_id=log_data.user_id,
            game_type=log_data.game_type,
            pokemon_id=log_data.pokemon_id,
            is_correct=log_data.is_correct,
            hint_used=log_data.hint_used,
            wrong_answer_id=log_data.wrong_answer_id,
            log_data=log_data.log_data
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        print(f"DEBUG: Successfully saved log with ID: {db_log.id}")
        return db_log
    except Exception as e:
        print(f"DEBUG: Error saving game log: {str(e)}")
        db.rollback()
        raise e


def create_team_build_log(db: Session, log_data: schemas.TeamBuildLogCreate):
    """팀 빌더의 분석/추천 완료 결과를 team_build_logs 테이블에 새 기록으로 저장합니다."""

    try:
        # db_log:
        # - 추천까지 완료된 팀 빌더 결과를 한 번에 저장하는 기록입니다.
        db_log = models.TeamBuildLog(
            user_id=log_data.user_id,
            selected_pokemon_ids=log_data.selected_pokemon_ids,
            analysis_result=log_data.analysis_result,
            analysis_conclusion=log_data.analysis_conclusion,
            recommended_pokemon_ids=log_data.recommended_pokemon_ids,
            recommendation_result=log_data.recommendation_result,
            recommendation_conclusion=log_data.recommendation_conclusion,
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    except Exception as e:
        db.rollback()
        raise e


def get_user_team_build_logs(db: Session, user_id: int, limit: int = 10):
    """사용자의 팀 빌더 분석/추천 히스토리를 최신순으로 조회합니다."""
    return (
        db.query(models.TeamBuildLog)
        .filter(models.TeamBuildLog.user_id == user_id)
        .order_by(models.TeamBuildLog.id.desc())
        .limit(limit)
        .all()
    )


def update_latest_team_build_recommendation(
    db: Session,
    selected_pokemon_ids: List[int],
    recommended_pokemon_ids: List[int],
    recommendation_result: dict,
    recommendation_conclusion: Optional[str] = None,
    user_id: Optional[int] = None,
):
    """같은 5마리 선택 조합의 최신 분석 기록에 추천 결과를 이어서 저장합니다."""

    # query:
    # - 추천은 보통 분석 이후에 실행되므로, 같은 selected_pokemon_ids를 가진 최신 로그를 찾습니다.
    query = db.query(models.TeamBuildLog).filter(
        models.TeamBuildLog.selected_pokemon_ids == selected_pokemon_ids
    )

    # user_id:
    # - 로그인 사용자가 전달된 경우에는 같은 사용자 기록 안에서만 최신 로그를 찾습니다.
    if user_id is not None:
        query = query.filter(models.TeamBuildLog.user_id == user_id)

    db_log = query.order_by(models.TeamBuildLog.id.desc()).first()

    try:
        # 추천만 먼저 실행된 경우에도 기록이 남도록 새 로그를 만들어 둡니다.
        if db_log is None:
            db_log = models.TeamBuildLog(
                user_id=user_id,
                selected_pokemon_ids=selected_pokemon_ids,
            )
            db.add(db_log)

        db_log.recommended_pokemon_ids = recommended_pokemon_ids
        db_log.recommendation_result = recommendation_result
        db_log.recommendation_conclusion = recommendation_conclusion

        db.commit()
        db.refresh(db_log)
        return db_log
    except Exception as e:
        db.rollback()
        raise e

def get_user_stats(db: Session, user_id: int):
    """마이페이지용 유저 통계 데이터를 조회합니다."""
    logs = db.query(models.GameLog).filter(models.GameLog.user_id == user_id).all()
    
    stats = {
        "silhouette": {"total": 0, "correct": 0, "hint_used": 0},
        "memory": {"total": 0, "correct": 0, "hint_used": 0},
        "battle": {"total": 0},
        "gym_badges": [],
        "collected_pokemon_ids": []
    }
    
    collected_ids = set()
    gym_badges = set()
    
    for log in logs:
        g_type = log.game_type
        
        # 퀴즈/메모리 게임 통계
        if g_type in ["silhouette", "memory"]:
            stats[g_type]["total"] += 1
            if log.is_correct:
                stats[g_type]["correct"] += 1
            if log.hint_used:
                stats[g_type]["hint_used"] += 1
        
        # 배틀 참여 통계
        if g_type == "gym_battle":
            stats["battle"]["total"] += 1
        
        # 도감 수집 목록 (정답 맞힌 경우)
        if log.is_correct and log.pokemon_id:
            collected_ids.add(log.pokemon_id)
            
        # 체육관 관장 승리 뱃지
        if g_type == "gym_battle" and log.is_correct and log.log_data:
            try:
                # log_data가 문자열(Text)인 경우 파싱
                data = json.loads(log.log_data)
                leader = data.get("leader")
                if leader:
                    gym_badges.add(leader)
            except Exception as e:
                print(f"DEBUG: Error parsing gym_battle log_data: {e}")
    
    stats["collected_pokemon_ids"] = sorted(list(collected_ids))
    stats["gym_badges"] = list(gym_badges)
    return stats


def get_user_logs(db: Session, user_id: int, limit: int = 10):
    """최근 게임 로그를 조회합니다."""
    return db.query(models.GameLog).filter(models.GameLog.user_id == user_id)\
             .order_by(models.GameLog.created_at.desc()).limit(limit).all()


def save_user_battle_team(db: Session, user_id: int, team_data: list):
    """사용자의 커스텀 배틀 팀을 저장합니다."""
    db_team = db.query(models.UserBattleTeam).filter(models.UserBattleTeam.user_id == user_id).first()
    
    if db_team:
        db_team.team_data = team_data
    else:
        db_team = models.UserBattleTeam(user_id=user_id, team_data=team_data)
        db.add(db_team)
        
    try:
        db.commit()
        db.refresh(db_team)
        return db_team
    except Exception as e:
        db.rollback()
        raise e


def get_user_battle_team(db: Session, user_id: int):
    """사용자의 커스텀 배틀 팀을 조회합니다."""
    return db.query(models.UserBattleTeam).filter(models.UserBattleTeam.user_id == user_id).first()
