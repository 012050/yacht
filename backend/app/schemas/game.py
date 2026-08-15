from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GameCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    game_id: str
    join_code: str
    status: str
    host_user_id: str


class GameJoinRequest(BaseModel):
    join_code: str = Field(min_length=6, max_length=6)


class PlayerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str
    join_order: int
    is_host: bool


class TurnInfo(BaseModel):
    game_id: str
    current_player_user_id: str
    current_player_display_name: str
    current_round: int
    status: str
    dice: Optional[list[int]] = None
    kept_indices: Optional[list[int]] = None
    rolls_remaining: Optional[int] = None
    turn_time_limit: int
    available_categories: list[str]


class ScoreboardEntry(BaseModel):
    category: str
    score: int


class PlayerScoreboard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str
    entries: list[ScoreboardEntry] = []


class StartGameRequest(BaseModel):
    pass
