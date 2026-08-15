# WebSocket message type constants
STATE_UPDATE = "STATE_UPDATE"
DICE_ROLL = "DICE_ROLL"
DICE_KEEP = "DICE_KEEP"
SELECT_CATEGORY = "SELECT_CATEGORY"
TIME_EXPIRED = "TIME_EXPIRED"
GAME_STARTED = "GAME_STARTED"
GAME_FINISHED = "GAME_FINISHED"
ERROR = "ERROR"
TIMER_UPDATE = "TIMER_UPDATE"
PLAYER_LEFT = "PLAYER_LEFT"

ALL_TYPES = {
    STATE_UPDATE,
    DICE_ROLL,
    DICE_KEEP,
    SELECT_CATEGORY,
    TIME_EXPIRED,
    GAME_STARTED,
    GAME_FINISHED,
    ERROR,
    TIMER_UPDATE,
    PLAYER_LEFT,
}


def build_ws_message(msg_type: str, payload: dict) -> dict:
    """Build a standard WebSocket message dict."""
    return {"type": msg_type, "payload": payload}
