from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=4, max_length=100)
    nickname: str = Field(min_length=1, max_length=20)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    nickname: str
    total_games: int = 0
    total_wins: int = 0
    cumulative_score: int = 0
