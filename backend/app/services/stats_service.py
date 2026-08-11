"""
?? ?? ??, ???? ?? ??
"""

import uuid
from sqlalchemy.orm import Session
from app.database.models import GameResult
from app.services.scoring import (
    calculate_bonus,
    TOP_CATEGORIES,
    BOTTOM_CATEGORIES,
)


def save_game_results(db: Session, game_id: str, game_state) -> None:
    """?? ?? ? ?? ????? ??? DB? ??"""
    scores = game_state.scoreboards
    # ?? ?? ???? ??
    ranked = []
    for uid, cat_scores in scores.items():
        top_sum = sum(cat_scores.get(c, 0) for c in TOP_CATEGORIES)
        bottom_sum = sum(cat_scores.get(c, 0) for c in BOTTOM_CATEGORIES)
        bonus = calculate_bonus(cat_scores)
        total = top_sum + bottom_sum + bonus
        ranked.append((uid, total, top_sum, bottom_sum, bonus, cat_scores))

    ranked.sort(key=lambda x: (-x[1], x[0]))

    # ?? ??
    rank = 1
    for i, (uid, total, top_sum, bottom_sum, bonus, cat_scores) in enumerate(ranked):
        if i > 0 and total < ranked[i - 1][1]:
            rank = i + 1
        result = GameResult(
            id=str(uuid.uuid4()),
            game_id=game_id,
            user_id=uid,
            rank=rank,
            total_score=total,
            top_section_sum=top_sum,
            bottom_section_sum=bottom_sum,
            bonus=bonus,
        )
        db.add(result)

    db.commit()


def get_user_stats(db: Session, user_id: str) -> dict:
    """????? ?? ?? ??"""
    results = db.query(GameResult).filter(GameResult.user_id == user_id).all()
    games_played = len(results)
    if games_played == 0:
        return {
            "user_id": user_id,
            "games_played": 0,
            "wins": 0,
            "win_rate": 0.0,
            "average_score": 0.0,
        }
    wins = sum(1 for r in results if r.rank == 1)
    avg_score = sum(r.total_score for r in results) / games_played
    return {
        "user_id": user_id,
        "games_played": games_played,
        "wins": wins,
        "win_rate": wins / games_played,
        "average_score": avg_score,
    }


def get_leaderboard(db: Session, limit: int = 10) -> list[dict]:
    """?? ?? ?? ????"""
    from sqlalchemy import func
    user_ids = db.query(GameResult.user_id).distinct().all()
    leaderboard = []
    for (uid,) in user_ids:
        stats = get_user_stats(db, uid)
        if stats["games_played"] > 0:
            leaderboard.append(stats)
    leaderboard.sort(key=lambda x: (-x["wins"], -x["average_score"]))
    return leaderboard[:limit]
