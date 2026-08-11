import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.game_service import game_service
from app.services.auth_service import decode_token

router = APIRouter()

active_connections = {}

async def broadcast(game_id, msg_type, payload):
    connections = active_connections.get(game_id, {})
    message = json.dumps({"type": msg_type, "payload": payload})
    for ws in connections.values():
        try:
            await ws.send_text(message)
        except Exception:
            pass

@router.websocket("/ws/games/{game_id}")
async def game_websocket(websocket, game_id):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        user_id = decode_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    active_connections.setdefault(game_id, {})[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type")
                payload = msg.get("payload", {})

                if msg_type == "SESSION_RECOVER":
                    await game_service.handle_session_recover(game_id, user_id, websocket)

                elif msg_type == "ROLL":
                    dice, rolls_left = await game_service.handle_roll(game_id, user_id)
                    await broadcast(game_id, "STATE_UPDATE", {
                        "dice": dice, "rolls_left": rolls_left,
                        "current_player_index": game_service._games[game_id].current_player_index,
                        "current_round": game_service._games[game_id].current_round,
                    })

                elif msg_type == "KEEP":
                    await game_service.handle_keep(game_id, user_id, payload.get("indices", []))

                elif msg_type == "FINISH_ROLLS":
                    await game_service.handle_finish_rolls(game_id, user_id)

                elif msg_type == "SELECT_CATEGORY":
                    cat = payload.get("category")
                    score, next_idx = await game_service.handle_select_category(game_id, user_id, cat)
                    await broadcast(game_id, "STATE_UPDATE", {
                        "score": score, "category": cat,
                        "current_player_index": next_idx,
                    })

                elif msg_type == "PASS":
                    next_idx = await game_service.handle_pass(game_id, user_id)
                    await broadcast(game_id, "STATE_UPDATE", {"current_player_index": next_idx})

                elif msg_type == "LEAVE":
                    await game_service.handle_player_leave(game_id, user_id)
                    await broadcast(game_id, "PLAYER_LEFT", {"user_id": user_id})

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "ERROR", "payload": {"message": "Invalid JSON"}}))
            except ValueError as e:
                await websocket.send_text(json.dumps({"type": "ERROR", "payload": {"message": str(e)}}))

    except WebSocketDisconnect:
        active_connections[game_id].pop(user_id, None)
        await game_service.handle_player_leave(game_id, user_id)
        await broadcast(game_id, "PLAYER_LEFT", {"user_id": user_id})
