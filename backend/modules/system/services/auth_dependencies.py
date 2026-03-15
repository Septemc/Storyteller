from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....db.base import get_db
from ....db.models import User, UserRole
from .auth_security import decode_token, oauth2_scheme
from .auth_users import get_user_by_id, get_user_by_user_id


async def get_current_user(token=Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return _resolve_current_user(token, db)


def get_current_user_sync(token=Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return _resolve_current_user(token, db)


def _resolve_current_user(token, db: Session):
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return get_user_by_user_id(db, user_id) if isinstance(user_id, str) else get_user_by_id(db, user_id)


async def get_current_user_required(user: User = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用")
    return user


async def get_admin_user(user: User = Depends(get_current_user_required)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user
