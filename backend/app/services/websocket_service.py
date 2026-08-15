"""WebSocket connection manager for per-game real-time updates."""
from typing import Dict, List

from fastapi import WebSocket

from app.schemas.websocket import build_ws_message, STATE_UPDATE


class ConnectionManager:
    """Manage WebSocket connections grouped by game_id."""

    def __init__(self) -> None:
        # game_id -> list of (websocket, user_id)
        self.active_connections: Dict[str, List[tuple[WebSocket, str]]] = {}

    async def connect(
        self, websocket: WebSocket, game_id: str, user_id: str
    ) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append((websocket, user_id))

    def disconnect(self, websocket: WebSocket, game_id: str) -> None:
        """Remove a WebSocket connection."""
        if game_id not in self.active_connections:
            return
        self.active_connections[game_id] = [
            (ws, uid)
            for ws, uid in self.active_connections[game_id]
            if ws != websocket
        ]
        # Clean up empty game entries.
        if not self.active_connections[game_id]:
            del self.active_connections[game_id]

    async def broadcast(self, game_id: str, message: dict) -> None:
        """Send a message to all connected clients in a game."""
        if game_id not in self.active_connections:
            return
        targets = [ws for ws, _ in self.active_connections[game_id]]
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                pass  # Client disconnected; cleanup on next disconnect call.

    async def send_to_user(self, game_id: str, user_id: str, message: dict) -> None:
        """Send a message to a specific user within a game."""
        if game_id not in self.active_connections:
            return
        for ws, uid in self.active_connections[game_id]:
            if uid == user_id:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    @staticmethod
    def build_state_update(game_id: str, state: dict) -> dict:
        """Build a STATE_UPDATE message."""
        return build_ws_message(STATE_UPDATE, {"game_id": game_id, "state": state})
