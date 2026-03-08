from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.db.base import get_db
from backend.db.models import User
from backend.core.auth import (
    Token,
    UserCreate,
    UserLogin,
    UserInfo,
    UserUpdate,
    PasswordChange,
    authenticate_user,
    create_user,
    create_access_token,
    get_current_user_required,
    get_user_by_username,
    get_user_by_email,
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


class RegisterResponse(BaseModel):
    success: bool
    message: str
    user: UserInfo = None


@router.post("/register", response_model=RegisterResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    if user_data.email:
        existing_email = get_user_by_email(db, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6位"
        )
    
    user = create_user(db, user_data)
    
    return RegisterResponse(
        success=True,
        message="注册成功",
        user=UserInfo(
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
    )


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
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
        if existing and existing.id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
        user.email = update_data.email
    if update_data.avatar is not None:
        user.avatar = update_data.avatar
    
    db.commit()
    db.refresh(user)
    
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


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    from backend.core.auth import verify_password, get_password_hash
    
    if not verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少6位"
        )
    
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"success": True, "message": "密码修改成功"}


@router.post("/logout")
def logout():
    return {"success": True, "message": "已退出登录"}


@router.get("/check-username/{username}")
def check_username(username: str, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, username)
    return {"available": existing is None}
