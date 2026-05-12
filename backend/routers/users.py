from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
from database import get_db

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)

@router.post("/", response_model=schemas.UserResponse)
def create_or_update_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    유저 정보를 생성하거나 이미 존재하는 경우 업데이트합니다.
    """
    return crud.create_or_update_user(db, user)

@router.get("/{github_id}", response_model=schemas.UserResponse)
def get_user(github_id: int, db: Session = Depends(get_db)):
    """
    GitHub ID를 기반으로 유저 정보를 조회합니다.
    """
    import models
    db_user = db.query(models.User).filter(models.User.github_id == github_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/game-log")
def create_game_log(log_data: schemas.GameLogCreate, db: Session = Depends(get_db)):
    """
    미니게임 플레이 로그를 저장합니다.
    """
    return crud.create_game_log(db, log_data)
@router.get("/{user_id}/stats")
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """유저의 미니게임 통계 정보를 조회합니다."""
    return crud.get_user_stats(db, user_id)

@router.get("/{user_id}/logs")
def get_user_logs(user_id: int, db: Session = Depends(get_db), limit: int = 10):
    """유저의 최근 미니게임 플레이 로그를 조회합니다."""
    return crud.get_user_logs(db, user_id, limit)
