"""
HTTP ?????: ??? ??, ??, ?? ??
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
from app.core.dependencies import get_current_user, get_user_id
from app.schemas.game import UserStats
from app.services.stats_service import get_user_stats, get_leaderboard

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserStats)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stats = get_user_stats(db, current_user.id)
    return UserStats(
        user_id=current_user.id,
        username=current_user.username,
        nickname=current_user.nickname,
        games_played=stats["games_played"],
        wins=stats["wins"],
        win_rate=stats["win_rate"],
        average_score=stats["average_score"],
    )


@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    return get_leaderboard(db)


@router.get("/session")
def session_recovery(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """?? ?? ?? ?? ?? (?? ???)"""
    from app.database.models import GamePlayer
    active_games = (
        db.query(Game)
        .join(GamePlayer, Game.id == GamePlayer.game_id)
        .filter(GamePlayer.user_id == current_user.id)
        .filter(Game.state.in_(["created", "waiting", "playing"]))
        .all()
    )
    return [
        {
            "game_id": g.id,
            "state": g.state,
            "join_code": g.join_code,
        }
        for g in active_games
    ]
