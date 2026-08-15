"""Authentication routes: register, login, refresh, logout."""
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db
from app.database.models import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.security_service import validate_nickname, validate_username

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Register a new user account."""
    if not validate_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be alphanumeric/underscore and <= 20 chars",
        )
    if not validate_nickname(user_data.nickname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nickname must be alphanumeric/underscore and <= 20 chars",
        )

    # Check uniqueness.
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    if db.query(User).filter(User.nickname == user_data.nickname).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Nickname already taken")

    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        nickname=user_data.nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Issue tokens.
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 86400,
    )

    return user


@router.post("/login", response_model=UserResponse)
async def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login with username and password."""
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 86400,
    )

    return user


@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """Refresh access token using the refresh token cookie."""
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )

    return {"message": "Token refreshed"}


@router.post("/logout")
async def logout(response: Response):
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out"}
