from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=20)
    nickname: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=1, max_length=20)

    @field_validator("username", "nickname", "password")
    @classmethod
    def alphanumeric_only(cls, v: str) -> str:
        if not all(c.isalnum() or c in "-!@#$%^&*" for c in v):
            raise ValueError("???, ??, ???(-)? ?????.")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    nickname: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
