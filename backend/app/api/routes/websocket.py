"""WebSocket endpoint for real-time game communication."""
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database.db import SessionLocal
from app.database.models import Game, GamePlayer, Scoreboard, User
from app.schemas.websocket import (
    DICE_KEEP,
    DICE_ROLL,
    ERROR,
    GAME_FINISHED,
    PLAYER_LEFT,
    SELECT_CATEGORY,
    STATE_UPDATE,
    TIME_EXPIRED,
    build_ws_message,
)
from app.services.auth_service import decode_token
from app.services.dice_service import resolve_final_dice, roll_5_dice
from app.services.game_service import GameService
from app.services.scoring import CATEGORIES, calculate_score
from app.services.turn_timer import turn_timer
from app.services.websocket_service import ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

manager = ConnectionManager()
game_svc = GameService()


def _build_state_update(game_id: str) -> dict:
    """Build a STATE_UPDATE message from the current DB state."""
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return None

        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )

        if not players:
            return None

        player_infos = []
        for p in players:
            user = db.query(User).filter(User.id == p.user_id).first()
            player_infos.append({
                "user_id": p.user_id,
                "display_name": user.nickname if user else "Unknown",
                "join_order": p.join_order,
                "is_host": p.user_id == game.host_user_id,
            })

        scoreboards = {}
        for p in players:
            entries = (
                db.query(Scoreboard)
                .filter_by(game_id=game_id, user_id=p.user_id)
                .all()
            )
            user = db.query(User).filter(User.id == p.user_id).first()
            scoreboards[p.user_id] = {
                "user_id": p.user_id,
                "display_name": user.nickname if user else "Unknown",
                "entries": [{"category": e.category, "score": e.score} for e in entries],
            }

        return {
            "game_id": game_id,
            "status": game.status.upper(),
            "current_player_index": game.current_player_index,
            "current_round": game.current_round,
            "turn_time_limit": game.turn_time_limit,
            "turn_time_remaining": game.turn_time_limit,
            "players": player_infos,
            "scoreboards": scoreboards,
                    }
    finally:
        db.close()


# ── Turn timer helpers ─────────────────────────────────────────────────

def refresh_turn_timer(game_id: str) -> None:
    """(Re)schedule the turn timer for the game's current player.

    Cancels any pending timer first. Schedules nothing unless the game is
    PLAYING. Must be called from a running event loop (async context).
    """
    turn_timer.cancel(game_id)
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game or game.status != "playing":
            return
        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )
        if not players:
            return
        current_user_id = players[game.current_player_index % len(players)].user_id
        limit = game.turn_time_limit
    finally:
        db.close()

    turn_timer.schedule_turn(
        game_id, limit,
        lambda: _handle_turn_timeout(game_id, current_user_id),
    )


async def _handle_turn_timeout(game_id: str, expected_user_id: str) -> None:
    """Auto-play a timed-out turn.

    Per docs/game-state-machine.md 4.2: keep the player's kept dice, roll
    the rest once, and record the highest-scoring available category.
    """
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game or game.status != "playing":
            return

        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )
        if not players:
            return

        current_gp = players[game.current_player_index % len(players)]
        if current_gp.user_id != expected_user_id:
            return  # Stale timer: the turn already advanced.

        turn_state = turn_timer.get_turn_state(game_id)
        if turn_state and turn_state.get("values"):
            dice = resolve_final_dice(
                turn_state["values"], turn_state["kept_indices"]
            )
        else:
            dice = roll_5_dice()

        result = game_svc.handle_timeout(db, game_id, current_gp.user_id, dice)
        timed_out_user_id = current_gp.user_id
    except ValueError:
        logger.exception("Turn timeout failed for game %s", game_id)
        return
    finally:
        db.close()

    turn_timer.clear_turn(game_id)

    await manager.broadcast(
        game_id,
        build_ws_message(TIME_EXPIRED, {
            "user_id": timed_out_user_id,
            "category": result["category"],
            "score": result["score"],
        }),
    )

    state = _build_state_update(game_id)
    if state:
        await manager.broadcast(game_id, build_ws_message(STATE_UPDATE, state))

    if result.get("game_finished"):
        await manager.broadcast(
            game_id,
            build_ws_message(GAME_FINISHED, {"game_id": game_id}),
        )

    refresh_turn_timer(game_id)


@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """Per-game WebSocket: authenticate, register, handle messages.

    Authentication uses the same-origin access_token cookie, which the
    browser sends automatically on the WebSocket upgrade request.
    """
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.accept()
        await websocket.send_json(
            build_ws_message(ERROR, {"message": "Missing authentication token"})
        )
        await websocket.close()
        return

    try:
        payload = decode_token(token)
        user_id: str = payload["sub"]
    except Exception:
        await websocket.accept()
        await websocket.send_json(
            build_ws_message(ERROR, {"message": "Invalid token"})
        )
        await websocket.close()
        return

    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            await websocket.accept()
            await websocket.send_json(
                build_ws_message(ERROR, {"message": "Game not found"})
            )
            await websocket.close()
            return

        gp = db.query(GamePlayer).filter_by(game_id=game_id, user_id=user_id).first()
        if not gp:
            await websocket.accept()
            await websocket.send_json(
                build_ws_message(ERROR, {"message": "Not a participant"})
            )
            await websocket.close()
            return
    finally:
        db.close()

    await manager.connect(websocket, game_id, user_id)

    # Send full state on connect so client syncs.
    state = _build_state_update(game_id)
    if state:
        await manager.send_to_user(
            game_id, user_id,
            build_ws_message(STATE_UPDATE, state),
        )

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await manager.send_to_user(
                    game_id, user_id,
                    build_ws_message(ERROR, {"message": "Invalid JSON"}),
                )
                continue

            msg_type = msg.get("type")
            payload_data = msg.get("payload", {})

            if msg_type == DICE_ROLL:
                await _handle_dice_roll(game_id, user_id, payload_data, manager)

            elif msg_type == DICE_KEEP:
                await _handle_dice_keep(game_id, user_id, payload_data, manager)

            elif msg_type == SELECT_CATEGORY:
                await _handle_select_category(game_id, user_id, payload_data, manager)

            elif msg_type == PLAYER_LEFT:
                await _handle_player_left(game_id, user_id, manager)

            else:
                await manager.send_to_user(
                    game_id, user_id,
                    build_ws_message(ERROR, {"message": f"Unknown message type: {msg_type}"}),
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
    except Exception:
        manager.disconnect(websocket, game_id)


async def _handle_dice_roll(game_id: str, user_id: str, payload: dict, mgr: ConnectionManager):
    """Handle dice roll from a player."""
    db = SessionLocal()
    try:
        kept_indices = payload.get("keptIndices")
        current_values = payload.get("values")
        rolls_remaining = payload.get("rollsRemaining")

        result = game_svc.roll_dice(db, game_id, user_id, kept_indices, current_values, rolls_remaining)

        # Track the current turn's dice so a timeout can auto-play them.
        turn_timer.record_roll(
            game_id, user_id,
            result["values"], result["keptIndices"], result["rollsRemaining"],
        )

        await mgr.broadcast(
            game_id,
            build_ws_message(DICE_ROLL, {**result, "user_id": user_id}),
        )
    except ValueError as exc:
        await mgr.send_to_user(
            game_id, user_id,
            build_ws_message(ERROR, {"message": str(exc)}),
        )
    finally:
        db.close()


async def _handle_dice_keep(game_id: str, user_id: str, payload: dict, mgr: ConnectionManager):
    """Handle dice keep from a player."""
    db = SessionLocal()
    try:
        indices = payload.get("indices", [])
        result = game_svc.keep_dice(db, game_id, user_id, indices)

        # Include the latest known dice values so clients stay in sync.
        turn_state = turn_timer.get_turn_state(game_id)
        if turn_state and turn_state.get("values"):
            result["values"] = turn_state["values"]
            result["rollsRemaining"] = turn_state["rolls_remaining"]

        await mgr.broadcast(
            game_id,
            build_ws_message(DICE_KEEP, {**result, "user_id": user_id}),
        )
    except ValueError as exc:
        await mgr.send_to_user(
            game_id, user_id,
            build_ws_message(ERROR, {"message": str(exc)}),
        )
    finally:
        db.close()


async def _handle_select_category(game_id: str, user_id: str, payload: dict, mgr: ConnectionManager):
    """Handle category selection. Backend calculates the score from dice values."""
    db = SessionLocal()
    try:
        category = payload.get("category")
        dice = payload.get("dice")  # The player's final dice values
        is_pass = payload.get("isPass", False)

        if not category or category not in CATEGORIES:
            raise ValueError(f"Invalid category: {category}")

        # Calculate score from dice on the backend (authoritative)
        if is_pass:
            score = 0
        elif dice and len(dice) == 5:
            score = calculate_score(category, dice)
        else:
            raise ValueError("Dice values required to calculate score")

        result = game_svc.record_score(db, game_id, user_id, category, score)
    except ValueError as exc:
        await mgr.send_to_user(
            game_id, user_id,
            build_ws_message(ERROR, {"message": str(exc)}),
        )
        return
    finally:
        db.close()

    # Turn advanced: reset dice tracking and start the next player's timer.
    turn_timer.clear_turn(game_id)

    await mgr.broadcast(
        game_id,
        build_ws_message(SELECT_CATEGORY, {
            "user_id": user_id,
            "category": category,
            "score": score,
        }),
    )

    # Broadcast updated game state so all clients know whose turn is next.
    state = _build_state_update(game_id)
    if state:
        await mgr.broadcast(
            game_id,
            build_ws_message(STATE_UPDATE, state),
        )

    if result.get("game_finished"):
        await mgr.broadcast(
            game_id,
            build_ws_message(GAME_FINISHED, {"game_id": game_id}),
        )

    refresh_turn_timer(game_id)


async def _handle_player_left(game_id: str, user_id: str, mgr: ConnectionManager):
    db = SessionLocal()
    try:
        result = game_svc.handle_player_leave(db, game_id, user_id)
    except ValueError as exc:
        await mgr.broadcast(
            game_id,
            build_ws_message(ERROR, {"message": str(exc)}),
        )
        return
    finally:
        db.close()

    # The leaving player's turn (if any) is over; refresh for the next player.
    turn_timer.clear_turn(game_id)

    await mgr.broadcast(
        game_id,
        build_ws_message(PLAYER_LEFT, {"user_id": user_id}),
    )

    if result.get("game_finished"):
        await mgr.broadcast(
            game_id,
            build_ws_message(GAME_FINISHED, {"game_id": game_id}),
        )

    refresh_turn_timer(game_id)
