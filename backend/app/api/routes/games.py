"""
HTTP ?????: ?? ??, ??, ?? ??, ?? ??
"""

import uuid
import string
import random
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import Game, GamePlayer, Scoreboard
from app.schemas.game import (
    GameCreate, GameJoin, GameResponse, CategorySelect,
    GameDetailResponse, GameResultResponse, ResultPlayer,
)
from app.core.dependencies import get_current_user
from app.database.models import User
from app.services.game_service import game_service
from app.services.security_service import limiter
from app.services.scoring import (
    calculate_bonus, TOP_CATEGORIES, BOTTOM_CATEGORIES, CATEGORIES,
)

router = APIRouter(prefix="/api/games", tags=["games"])


def _generate_join_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))


@router.post("/create", response_model=GameResponse)
@limiter.limit("10/minute")
def create_game(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    body = GameCreate()
    game_id = str(uuid.uuid4())
    join_code = _generate_join_code()
    # UNIQUE ?? ??
    existing = db.query(Game).filter(Game.join_code == join_code).first()
    while existing:
        join_code = _generate_join_code()
        existing = db.query(Game).filter(Game.join_code == join_code).first()

    game = Game(
        id=game_id,
        join_code=join_code,
        host_user_id=current_user.id,
        state="created",
        timeout_duration=body.timeout_duration,
    )
    db.add(game)
    db.commit()
    db.refresh(game)

    # ???? ?? ??
    game_service.create_game(game_id, current_user.id, body.timeout_duration)

    return game


@router.post("/join")
@limiter.limit("30/minute")
def join_game(request: Request, body: GameJoin, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.join_code == body.join_code.upper()).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="???? ?? ?? ?????.")
    if game.state not in ("created",):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="?? ??? ???? ??? ? ????.")

    # ?? ?? ??
    existing = db.query(GamePlayer).filter(
        GamePlayer.game_id == game.id, GamePlayer.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="?? ??? ?????.")

    gp = GamePlayer(
        game_id=game.id,
        user_id=current_user.id,
        join_order=len(game.players) + 1,
        is_host=current_user.id == game.host_user_id,
    )
    db.add(gp)
    db.commit()

    # ???? ???? ??
    game_service.join_player(game.id, current_user.id)

    return {"status": "joined", "game_id": game.id}


@router.get("/{game_id}", response_model=GameDetailResponse)
def get_game_detail(game_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        state = game_service.get_game_state(game_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="??? ?? ? ????.")

    return GameDetailResponse(
        id=state["game_id"],
        state=state["state"],
        timeout_duration=state["timeout_duration"],
        current_player_index=state.get("current_player_index", -1),
        current_round=state.get("current_round", 0),
        dice=state.get("dice", []),
        rolls_left=state.get("rolls_left", 3),
    )


@router.post("/{game_id}/start")
def start_game(game_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="??? ?? ? ????.")
    if current_user.id != game.host_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="???? ??? ??? ? ????.")

    game_service.start_game(game_id)
    game.state = "playing"
    game.started_at = __import__("datetime").datetime.utcnow()
    db.commit()
    return {"status": "started"}


@router.post("/{game_id}/roll")
@limiter.limit("30/minute")
def roll_dice(request: Request, game_id: str, current_user: User = Depends(get_current_user)):
    try:
        dice = game_service.roll_dice(game_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    state = game_service.get_game_state(game_id)
    return {"dice": dice, "rolls_left": state["rolls_left"]}


@router.post("/{game_id}/keep")
def keep_dice(game_id: str, body: dict, current_user: User = Depends(get_current_user)):
    indices = body.get("indices", [])
    try:
        game_service.keep_dice(game_id, indices)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"status": "kept"}


@router.post("/{game_id}/finish-rolls")
def finish_rolls(game_id: str, current_user: User = Depends(get_current_user)):
    game_service.finish_rolls(game_id)
    state = game_service.get_game_state(game_id)
    return {"dice": state["dice"], "rolls_left": state["rolls_left"]}


@router.post("/{game_id}/select-category")
@limiter.limit("30/minute")
def select_category(request: Request, game_id: str, body: CategorySelect, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        game_service.select_category(game_id, current_user.id, body.category, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    state = game_service.get_game_state(game_id)
    return {
        "category": body.category,
        "score": state["scoreboards"].get(current_user.id, {}).get(body.category, 0),
        "next_player_index": state["current_player_index"],
    }


@router.post("/{game_id}/pass")
def pass_turn(game_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        game_service.pass_category(game_id, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"status": "passed"}


@router.get("/{game_id}/result")
def get_result(game_id: str, db: Session = Depends(get_db)):
    from app.database.models import GameResult as GR
    results = db.query(GR).filter(GR.game_id == game_id).order_by(GR.rank).all()
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="??? ????.")

    players = []
    for r in results:
        user = db.query(User).filter(User.id == r.user_id).first()
        players.append(ResultPlayer(
            user_id=r.user_id,
            nickname=user.nickname if user else "Unknown",
            rank=r.rank,
            total_score=r.total_score,
            top_section_sum=r.top_section_sum,
            bottom_section_sum=r.bottom_section_sum,
            bonus=r.bonus,
        ))
    return GameResultResponse(game_id=game_id, players=players)
