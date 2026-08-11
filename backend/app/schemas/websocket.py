from pydantic import BaseModel
from typing import Any


class ClientMessage(BaseModel):
    type: str  # ROLL, KEEP, FINISH_ROLLS, SELECT_CATEGORY, PASS, LEAVE, SESSION_RECOVER
    payload: dict[str, Any] = {}


class ServerMessage(BaseModel):
    type: str  # STATE_UPDATE, PLAYER_JOINED, PLAYER_LEFT, GAME_STARTED, GAME_FINISHED, TIME_WARNING, TIME_EXPIRED, SESSION_RECOVERED, ERROR
    payload: dict[str, Any] = {}
