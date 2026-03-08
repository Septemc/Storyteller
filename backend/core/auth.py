from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.db.base import get_db
from backend.db.models import User, UserRole

SECRET_KEY = "storyteller_secret_key_change_in_production_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    user_id: str
    username: str
    email: Optional[str]
    nickname: Optional[str]
    avatar: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        # 使用 options 允许 sub 为整数类型
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_sub": False}  # 不验证 sub 字段类型
        )
        return payload
    except JWTError as e:
        print(f"[DEBUG] Token decode error: {e}")
        return None


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """通过整数主键 ID 查找用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_user_id(db: Session, user_id: str) -> Optional[User]:
    """通过字符串 user_id 字段查找用户"""
    return db.query(User).filter(User.user_id == user_id).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    import json
    from backend.db.models import DBPreset, DBRegexProfile
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        password_hash=hashed_password,
        email=user_data.email,
        nickname=user_data.nickname or user_data.username,
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 为新用户创建默认预设
    default_preset = db.query(DBPreset).filter(
        DBPreset.id == "preset_default",
        DBPreset.user_id == None
    ).first()
    
    if default_preset:
        user_preset = DBPreset(
            id=f"preset_{user.user_id}",
            user_id=user.user_id,
            name=default_preset.name,
            version=default_preset.version,
            is_active=True,
            is_default=True,
            config_json=default_preset.config_json,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user_preset)
    
    # 为新用户创建默认正则
    default_regex = db.query(DBRegexProfile).filter(
        DBRegexProfile.id == "regex_default",
        DBRegexProfile.user_id == None
    ).first()
    
    if default_regex:
        user_regex = DBRegexProfile(
            id=f"regex_{user.user_id}",
            user_id=user.user_id,
            name=default_regex.name,
            version=default_regex.version,
            is_default=True,
            is_active=True,
            config_json=default_regex.config_json,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user_regex)
    
    db.commit()
    
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    # 根据类型选择查找方式
    if isinstance(user_id, str):
        user = get_user_by_user_id(db, user_id)
    else:
        user = get_user_by_id(db, user_id)
    return user


def get_current_user_sync(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """同步版本的 get_current_user，用于同步路由函数"""
    print(f"[DEBUG] get_current_user_sync - token: {token[:30] if token else 'None'}...")
    
    if not token:
        print("[DEBUG] get_current_user_sync - No token provided")
        return None
    
    payload = decode_token(token)
    print(f"[DEBUG] get_current_user_sync - payload: {payload}")
    
    if not payload:
        print("[DEBUG] get_current_user_sync - Token decode failed")
        return None
    
    user_id = payload.get("sub")
    print(f"[DEBUG] get_current_user_sync - user_id from token: {user_id} (type: {type(user_id).__name__})")
    
    if user_id is None:
        print("[DEBUG] get_current_user_sync - No user_id in payload")
        return None
    
    # 根据类型选择查找方式
    if isinstance(user_id, str):
        # 字符串 user_id（如 "a00000000001"）
        user = get_user_by_user_id(db, user_id)
        print(f"[DEBUG] get_current_user_sync - lookup by user_id (string): {user_id}")
    else:
        # 整数 ID（主键）
        user = get_user_by_id(db, user_id)
        print(f"[DEBUG] get_current_user_sync - lookup by id (int): {user_id}")
    
    print(f"[DEBUG] get_current_user_sync - user found: {user.username if user else 'None'}")
    
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )
    return user


async def get_admin_user(
    user: User = Depends(get_current_user_required),
) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


def create_admin_user(db: Session, username: str = "admin", password: str = "admin123") -> User:
    existing = get_user_by_username(db, username)
    if existing:
        return existing
    hashed_password = get_password_hash(password)
    admin = User(
        username=username,
        password_hash=hashed_password,
        nickname="管理员",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
