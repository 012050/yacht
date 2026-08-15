"""Player statistics: update stats, leaderboard, user stats."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import GameResult, User


def update_stats(db: Session, user_id: str, total_score: int, is_win: bool) -> None:
    """Update cumulative stats for a user after a game."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    user.total_games += 1
    user.cumulative_score += total_score
    if is_win:
        user.total_wins += 1


def get_leaderboard(db: Session, limit: int = 20) -> list[dict]:
    """Return top players sorted by cumulative_score descending."""
    users = (
        db.query(User)
        .order_by(User.cumulative_score.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "user_id": u.id,
            "nickname": u.nickname,
            "total_games": u.total_games,
            "total_wins": u.total_wins,
            "cumulative_score": u.cumulative_score,
            "win_rate": round(u.total_wins / u.total_games, 2) if u.total_games else 0,
        }
        for u in users
    ]


def get_user_stats(db: Session, user_id: str) -> dict:
    """Return detailed stats for a single user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    results = db.query(GameResult).filter(GameResult.user_id == user_id).all()

    best_score = max((r.total_score for r in results), default=0)
    worst_score = min((r.total_score for r in results), default=0)

    return {
        "user_id": user.id,
        "nickname": user.nickname,
        "total_games": user.total_games,
        "total_wins": user.total_wins,
        "cumulative_score": user.cumulative_score,
        "win_rate": round(user.total_wins / user.total_games, 2) if user.total_games else 0,
        "best_score": best_score,
        "worst_score": worst_score,
    }
