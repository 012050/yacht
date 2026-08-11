"""
JWT ?? ?? ???: ????, ???, ?? ??/??, ????
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
from app.schemas.user import UserCreate, UserLogin
from app.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expire, "type": "access"}, settings.SECRET_KEY, settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": user_id, "exp": expire, "type": "refresh"}, settings.SECRET_KEY, settings.ALGORITHM)


def decode_token(token: str) -> str:
    """???? user_id ??. ?? ? HTTPException"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="???? ?? ??")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="????? ???? ?? ??")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """HTTP Bearer ???? ?? ??? ??"""
    user_id = decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="???? ?? ? ????.")
    return user


def register_user(db: Session, req: UserCreate) -> User:
    """? ??? ??"""
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="?? ???? ??????.")
    if db.query(User).filter(User.nickname == req.nickname).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="?? ???? ??????.")
    import uuid
    user = User(
        id=str(uuid.uuid4()),
        username=req.username,
        nickname=req.nickname,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, req: UserLogin) -> tuple[User, str, str]:
    """???: ???/???? ?? ? ?? ??"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="??? ?? ????? ???????.")
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return user, access, refresh


def refresh_access_token(refresh_token: str) -> str:
    """???? ???? ? ??? ?? ??"""
    user_id = decode_token(refresh_token)
    return create_access_token(user_id)
