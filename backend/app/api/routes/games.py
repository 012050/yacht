"""Game routes: create, join, start, turn info."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.database.models import Game, GamePlayer, Scoreboard, User
from app.schemas.game import (
    GameCreateResponse,
    GameJoinRequest,
    PlayerInfo,
    PlayerScoreboard,
    ScoreboardEntry,
    TurnInfo,
)
from app.services.game_service import GameService
from app.services.security_service import validate_join_code
from app.api.routes.websocket import refresh_turn_timer

router = APIRouter(prefix="/api/games", tags=["games"])
game_svc = GameService()


class GameCreateRequest(BaseModel):
    turn_time_limit: int = Field(default=60, ge=10, le=300)


@router.post("", response_model=GameCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    body: GameCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new game. The creator becomes the host."""
    game = game_svc.create_game(db, current_user.id, body.turn_time_limit)
    return GameCreateResponse(
        id=game.id,
        game_id=game.id,
        join_code=game.join_code,
        status=game.status.upper(),
        host_user_id=game.host_user_id,
    )


@router.post("/join", response_model=GameCreateResponse)
async def join_game(
    body: GameJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Join an existing game by join code."""
    if not validate_join_code(body.join_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid join code format",
        )
    try:
        game = game_svc.join_game(db, body.join_code, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return GameCreateResponse(
        id=game.id,
        game_id=game.id,
        join_code=game.join_code,
        status=game.status.upper(),
        host_user_id=game.host_user_id,
    )


@router.get("/{game_id}")
async def get_game_info(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full game information including players and scoreboards.

    Returns both `id` (for WaitingRoom) and `game_id` (for GameScreen/GameState).
    Status is uppercase to match frontend GameStatus type.
    Scoreboards is a dict keyed by user_id to match GameState type.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

    # Verify the user is a participant.
    gp = db.query(GamePlayer).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not gp:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    players_query = (
        db.query(GamePlayer)
        .filter_by(game_id=game_id)
        .order_by(GamePlayer.join_order)
        .all()
    )

    players = []
    for p in players_query:
        user = db.query(User).filter(User.id == p.user_id).first()
        players.append(
            PlayerInfo(
                user_id=p.user_id,
                display_name=user.nickname if user else "Unknown",
                join_order=p.join_order,
                is_host=(p.user_id == game.host_user_id),
            )
        )

    # Build scoreboards as a dict keyed by user_id (matches GameState type).
    scoreboards_dict: dict[str, dict] = {}
    for p in players_query:
        entries = (
            db.query(Scoreboard)
            .filter_by(game_id=game_id, user_id=p.user_id)
            .all()
        )
        user = db.query(User).filter(User.id == p.user_id).first()
        scoreboards_dict[p.user_id] = {
            "user_id": p.user_id,
            "display_name": user.nickname if user else "Unknown",
            "entries": [
                ScoreboardEntry(category=e.category, score=e.score).model_dump()
                for e in entries
            ],
        }

    return {
        "id": game.id,
        "game_id": game.id,
        "join_code": game.join_code,
        "status": game.status.upper(),
        "host_user_id": game.host_user_id,
        "current_player_index": game.current_player_index,
        "current_round": game.current_round,
        "turn_time_limit": game.turn_time_limit,
        "turn_time_remaining": game.turn_time_limit,
        "players": players,
        "scoreboards": scoreboards_dict,
    }


@router.post("/{game_id}/start")
async def start_game(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Host starts the game. Requires >= 2 players and host auth."""
    try:
        game = game_svc.start_game(db, game_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # First turn starts now; begin its countdown (no-op if not playing).
    refresh_turn_timer(game.id)

    return {
        "id": game.id,
        "game_id": game.id,
        "status": game.status.upper(),
    }


@router.get("/{game_id}/results")
async def get_game_results(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get final results for a finished game (participation required)."""
    try:
        return game_svc.get_game_results(db, game_id)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "Game not found" else 400
        raise HTTPException(status_code=status_code, detail=message)


@router.get("/{game_id}/current-turn", response_model=TurnInfo)
async def get_current_turn(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current turn state."""
    try:
        turn_state = game_svc.get_turn_state(db, game_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Ensure the user is a participant.
    gp = db.query(GamePlayer).filter_by(game_id=game_id, user_id=current_user.id).first()
    if not gp:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    return TurnInfo(**turn_state)
