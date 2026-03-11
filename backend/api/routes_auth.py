from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.auth import (
    PasswordChange,
    Token,
    UserCreate,
    UserInfo,
    UserLogin,
    UserUpdate,
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user_required,
    get_user_by_email,
    get_user_by_username,
)
from backend.db.base import get_db
from backend.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserInfo] = None


class PasswordChangeCompat(BaseModel):
    current_password: str
    new_password: str


def _to_user_info(user: User) -> UserInfo:
    return UserInfo(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        nickname=user.nickname,
        avatar=user.avatar,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/register", response_model=RegisterResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    if user_data.email:
        existing_email = get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    if len(user_data.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters")

    user = create_user(db, user_data)
    return RegisterResponse(success=True, message="Registered successfully", user=_to_user_info(user))


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    user.last_login_at = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": user.user_id})
    return Token(
        access_token=access_token,
        user_id=user.user_id,
        username=user.username,
        role=user.role.value,
    )


@router.get("/me", response_model=UserInfo)
def get_current_user_info(user: User = Depends(get_current_user_required)):
    return _to_user_info(user)


@router.put("/me", response_model=UserInfo)
def update_current_user(
    update_data: UserUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    if update_data.nickname is not None:
        user.nickname = update_data.nickname

    if update_data.email is not None:
        existing = get_user_by_email(db, update_data.email)
        if existing and existing.user_id != user.user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already used by another account")
        user.email = update_data.email

    if update_data.avatar is not None:
        user.avatar = update_data.avatar

    db.commit()
    db.refresh(user)
    return _to_user_info(user)


@router.get("/profile", response_model=UserInfo)
def get_profile_alias(user: User = Depends(get_current_user_required)):
    return _to_user_info(user)


@router.put("/profile", response_model=UserInfo)
def update_profile_alias(
    update_data: UserUpdate,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    return update_current_user(update_data=update_data, user=user, db=db)


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    from backend.core.auth import get_password_hash, verify_password

    if not verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 6 characters")

    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    return {"success": True, "message": "Password updated"}


@router.put("/password")
def change_password_alias(
    password_data: PasswordChangeCompat,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    return change_password(
        password_data=PasswordChange(
            old_password=password_data.current_password,
            new_password=password_data.new_password,
        ),
        user=user,
        db=db,
    )


@router.post("/logout")
def logout():
    return {"success": True, "message": "Logged out"}


@router.get("/check-username/{username}")
def check_username(username: str, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, username)
    return {"available": existing is None}
