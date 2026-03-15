from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ....core.tenant import scoped_default_id
from ....db.models import DBPreset, DBRegexProfile, User, UserRole
from .auth_schemas import UserCreate
from .auth_security import get_password_hash, verify_password


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_user_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(username=user_data.username, password_hash=get_password_hash(user_data.password), email=user_data.email, nickname=user_data.nickname or user_data.username, role=UserRole.USER)
    db.add(user)
    db.commit()
    db.refresh(user)
    _create_default_profiles(db, user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    return user if user and verify_password(password, user.password_hash) else None


def create_admin_user(db: Session, username: str = "admin", password: str = "admin123") -> User:
    existing = get_user_by_username(db, username)
    if existing:
        return existing
    admin = User(username=username, password_hash=get_password_hash(password), nickname="管理员", role=UserRole.ADMIN)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _create_default_profiles(db: Session, user: User) -> None:
    default_preset = db.query(DBPreset).filter(DBPreset.id == "preset_default", DBPreset.user_id == None).first()
    if default_preset:
        db.add(DBPreset(id=scoped_default_id("preset_default", user.user_id), user_id=user.user_id, name=default_preset.name, version=default_preset.version, is_active=True, is_default=True, config_json=default_preset.config_json, created_at=datetime.utcnow(), updated_at=datetime.utcnow()))
    default_regex = db.query(DBRegexProfile).filter(DBRegexProfile.id == "regex_default", DBRegexProfile.user_id == None).first()
    if default_regex:
        db.add(DBRegexProfile(id=scoped_default_id("regex_default", user.user_id), user_id=user.user_id, name=default_regex.name, version=default_regex.version, is_default=True, is_active=True, config_json=default_regex.config_json, created_at=datetime.utcnow(), updated_at=datetime.utcnow()))
    db.commit()
