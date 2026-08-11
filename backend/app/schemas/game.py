from pydantic import BaseModel, Field, field_validator


CATEGORIES = [
    "1", "2", "3", "4", "5", "6",
    "yacht", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "chance",
]


class GameCreate(BaseModel):
    timeout_duration: int = Field(default=60, ge=10, le=300)


class GameJoin(BaseModel):
    join_code: str = Field(..., min_length=6, max_length=6)

    @field_validator("join_code")
    @classmethod
    def valid_code(cls, v: str) -> str:
        if not all(c.isalnum() for c in v):
            raise ValueError("??? ???? ?????.")
        return v.upper()


class GameResponse(BaseModel):
    id: str
    join_code: str
    state: str
    timeout_duration: int
    host_user_id: str

    model_config = {"from_attributes": True}


class CategorySelect(BaseModel):
    category: str

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"??? ????? ?????. ??? ?: {CATEGORIES}")
        return v


class DiceRollResponse(BaseModel):
    dice: list[int] = Field(..., min_length=5, max_length=5)
    rolls_left: int


class PlayerInGame(BaseModel):
    user_id: str
    nickname: str
    is_host: bool
    total_score: int = 0

    model_config = {"from_attributes": True}


class GameDetailResponse(BaseModel):
    id: str
    state: str
    timeout_duration: int
    players: list[PlayerInGame] = []
    current_player_index: int = -1
    current_round: int = 0
    dice: list[int] = []
    rolls_left: int = 3


class GameResultResponse(BaseModel):
    game_id: str
    players: list["ResultPlayer"]
    finished_at: str | None = None


class ResultPlayer(BaseModel):
    user_id: str
    nickname: str
    rank: int
    total_score: int
    top_section_sum: int
    bottom_section_sum: int
    bonus: int
    scores: dict[str, int] = {}


class UserStats(BaseModel):
    user_id: str
    username: str
    nickname: str
    games_played: int = 0
    wins: int = 0
    win_rate: float = 0.0
    average_score: float = 0.0

    model_config = {"from_attributes": True}
