"""
HTTP ?????: ????, ???, ?? ??, ?? ??
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import register_user, login_user, refresh_access_token, decode_token
from app.services.security_service import limiter
from app.database.models import User, Game

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
@limiter.limit("10/minute")
def register(request: Request, body: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, body)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, body: UserLogin, db: Session = Depends(get_db)):
    user, access, refresh = login_user(db, body)
    return Token(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=Token)
def refresh(body: dict, db: Session = Depends(get_db)):
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="???? ??? ?????.")
    new_access = refresh_access_token(refresh_token)
    return Token(access_token=new_access, refresh_token=refresh_token)


@router.get("/session")
def get_session(user_id: str = Depends(lambda: None), db: Session = Depends(get_db)):
    """??? ???? ? ?? ?? ?? ?? (?? ?? ?)"""
    return {}
