"""User routes: profile, session, leaderboard."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.database.models import User
from app.schemas.user import UserResponse
from app.services.stats_service import get_leaderboard, get_user_stats

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current authenticated user's profile."""
    return current_user


@router.get("/session")
async def get_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return session info including user profile and active games."""
    from app.database.models import Game, GamePlayer

    active_games = (
        db.query(Game)
        .join(GamePlayer, Game.id == GamePlayer.game_id)
        .filter(GamePlayer.user_id == current_user.id)
        .filter(Game.status.in_(["waiting", "playing"]))
        .all()
    )

    games = [
        {
            "id": g.id,
            "join_code": g.join_code,
            "status": g.status,
            "current_round": g.current_round,
        }
        for g in active_games
    ]

    return {
        "user": UserResponse.model_validate(current_user).model_dump(),
        "active_games": games,
    }


@router.get("/leaderboard")
async def get_leaderboard_endpoint(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Return the global leaderboard sorted by cumulative score."""
    return get_leaderboard(db, limit=limit)


@router.get("/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's detailed stats."""
    return get_user_stats(db, current_user.id)
