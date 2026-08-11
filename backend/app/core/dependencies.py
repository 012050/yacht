"""
??? ?? ??
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.auth_service import get_current_user
from app.database.models import User


def get_user_id(user: User = Depends(get_current_user)) -> str:
    """JWT?? user_id? ??"""
    return user.id
