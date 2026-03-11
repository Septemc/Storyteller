"""
正则化配置API路由

重构说明：
不再使用硬编码的备用正则，完全依赖数据库或JSON文件。
默认正则配置也会被导入数据库中。
"""
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models
from ..core.auth import get_current_user_sync, User as AuthUser
from ..core.tenant import current_user_id, owner_only, resolve_scoped_id, scoped_default_id

router = APIRouter(prefix="/regex", tags=["regex"])

DEFAULT_REGEX_PATH = Path(__file__).parent.parent.parent / "data" / "default_regex.json"
DEFAULT_REGEX_ID = "regex_default"


def load_default_regex_from_file() -> Dict[str, Any]:
    """从JSON文件加载默认正则配置"""
    if DEFAULT_REGEX_PATH.exists():
        with open(DEFAULT_REGEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def create_minimal_regex() -> Dict[str, Any]:
    """创建最小化的正则配置（仅作为最后的备用方案）"""
    return {
        "id": DEFAULT_REGEX_ID,
        "name": "默认正则化",
        "version": 1,
        "is_default": True,
        "root": {
            "id": "node_regex_root",
            "identifier": "regex_root",
            "kind": "group",
            "title": "正则化规则组",
            "enabled": True,
            "children": [
                {
                    "id": "node_tag_extraction",
                    "identifier": "tag_extraction",
                    "kind": "group",
                    "title": "标签提取规则",
                    "enabled": True,
                    "children": [
                        {
                            "id": "node_thinking_tag",
                            "kind": "regex",
                            "title": "思考过程标签",
                            "enabled": True,
                            "identifier": "thinking_tag",
                            "pattern": "<思考过程>([\\s\\S]*?)</思考过程>",
                            "extract_group": 1,
                            "target_section": "thinking",
                            "description": "提取<思考过程>标签内的内容"
                        },
                        {
                            "id": "node_body_tag",
                            "kind": "regex",
                            "title": "正文部分标签",
                            "enabled": True,
                            "identifier": "body_tag",
                            "pattern": "<正文部分>([\\s\\S]*?)</正文部分>",
                            "extract_group": 1,
                            "target_section": "body",
                            "description": "提取<正文部分>标签内的内容"
                        },
                        {
                            "id": "node_summary_tag",
                            "kind": "regex",
                            "title": "内容总结标签",
                            "enabled": True,
                            "identifier": "summary_tag",
                            "pattern": "<内容总结>([\\s\\S]*?)</内容总结>",
                            "extract_group": 1,
                            "target_section": "summary",
                            "description": "提取<内容总结>标签内的内容"
                        },
                        {
                            "id": "node_action_tag",
                            "kind": "regex",
                            "title": "行动选项标签",
                            "enabled": True,
                            "identifier": "action_tag",
                            "pattern": "<行动选项>([\\s\\S]*?)</行动选项>",
                            "extract_group": 1,
                            "target_section": "actions",
                            "description": "提取<行动选项>标签内的内容"
                        }
                    ]
                }
            ]
        },
        "meta": {}
    }


def ensure_default_regex_in_db(db: Session, user_id: Optional[str] = None) -> models.DBRegexProfile:
    """确保默认正则配置存在于数据库中"""
    query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.is_default == True),
        models.DBRegexProfile,
        user_id,
    )
    existing = query.first()
    
    if existing:
        return existing
    
    file_regex = load_default_regex_from_file()
    if not file_regex:
        file_regex = create_minimal_regex()
    
    preset_id = scoped_default_id(file_regex.get("id", DEFAULT_REGEX_ID), user_id)
    file_regex["id"] = preset_id
    
    existing_query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.id == preset_id),
        models.DBRegexProfile,
        user_id,
    )
    existing = existing_query.first()
    
    if existing:
        existing.is_default = True
        db.commit()
        return existing
    
    default_regex = models.DBRegexProfile(
        id=preset_id,
        name=file_regex.get("name", "默认正则化"),
        version=file_regex.get("version", 1),
        is_default=True,
        is_active=True,
        config_json=json.dumps(file_regex, ensure_ascii=False),
        user_id=user_id,
    )
    db.add(default_regex)
    db.commit()
    db.refresh(default_regex)
    
    return default_regex


class RegexProfileCreate(BaseModel):
    name: str
    config: Optional[Dict[str, Any]] = None


class RegexProfileUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class RegexProfileResponse(BaseModel):
    id: str
    name: str
    version: int
    is_default: bool
    is_active: bool
    config: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RegexProfileListItem(BaseModel):
    id: str
    name: str
    version: int
    is_default: bool
    is_active: bool


@router.get("/profiles", response_model=List[RegexProfileListItem])
def list_regex_profiles(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    query = owner_only(db.query(models.DBRegexProfile), models.DBRegexProfile, user_id)
    profiles = query.order_by(
        models.DBRegexProfile.is_default.desc(),
        models.DBRegexProfile.created_at.asc()
    ).all()
    
    result = []
    for p in profiles:
        result.append(
            RegexProfileListItem(
                id=p.id,
                name=p.name,
                version=p.version,
                is_default=p.is_default,
                is_active=p.is_active
            )
        )
    
    return result


@router.get("/profiles/{profile_id}", response_model=RegexProfileResponse)
def get_regex_profile(profile_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.id == profile_id),
        models.DBRegexProfile,
        user_id,
    )
    profile = query.first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    return RegexProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        is_default=profile.is_default,
        is_active=profile.is_active,
        config=json.loads(profile.config_json) if profile.config_json else {},
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None
    )


@router.get("/active", response_model=RegexProfileResponse)
def get_active_regex_profile(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    active_query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.is_active == True),
        models.DBRegexProfile,
        user_id,
    )
    profile = active_query.first()
    
    if not profile:
        default_query = owner_only(
            db.query(models.DBRegexProfile).filter(models.DBRegexProfile.is_default == True),
            models.DBRegexProfile,
            user_id,
        )
        profile = default_query.first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="No regex profile found")
    
    return RegexProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        is_default=profile.is_default,
        is_active=profile.is_active,
        config=json.loads(profile.config_json) if profile.config_json else {},
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None
    )


@router.post("/profiles", response_model=RegexProfileResponse)
def create_regex_profile(req: RegexProfileCreate, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    profile_id = resolve_scoped_id(db, models.DBRegexProfile, "id", f"regex_{uuid.uuid4().hex[:10]}", user_id)
    
    if req.config:
        config = req.config
    else:
        config = {
            "id": profile_id,
            "name": req.name,
            "version": 1,
            "is_default": False,
            "root": {
                "id": f"node_{uuid.uuid4().hex[:8]}",
                "kind": "group",
                "title": "正则化规则组",
                "identifier": "regex_root",
                "enabled": True,
                "children": []
            },
            "meta": {}
        }
    
    if "id" not in config:
        config["id"] = profile_id
    if "name" not in config:
        config["name"] = req.name
    config["is_default"] = False
    
    profile = models.DBRegexProfile(
        id=profile_id,
        name=req.name,
        version=1,
        is_default=False,
        is_active=False,
        config_json=json.dumps(config, ensure_ascii=False),
        user_id=user_id,
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return RegexProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        is_default=False,
        is_active=False,
        config=config,
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None
    )


@router.put("/profiles/{profile_id}", response_model=RegexProfileResponse)
def update_regex_profile(
    profile_id: str,
    req: RegexProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync)
):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.id == profile_id),
        models.DBRegexProfile,
        user_id,
    )
    profile = query.first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    if req.name:
        profile.name = req.name
    
    if req.config:
        config = req.config
        config["id"] = profile.id
        config["name"] = profile.name
        config["is_default"] = profile.is_default
        profile.config_json = json.dumps(config, ensure_ascii=False)
    
    db.commit()
    db.refresh(profile)
    
    return RegexProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        is_default=profile.is_default,
        is_active=profile.is_active,
        config=json.loads(profile.config_json) if profile.config_json else {},
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None
    )


@router.put("/active")
def set_active_regex_profile(
    profile_id: str = Query(..., description="正则化配置ID"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync)
):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.id == profile_id),
        models.DBRegexProfile,
        user_id,
    )
    profile = query.first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    update_query = owner_only(db.query(models.DBRegexProfile), models.DBRegexProfile, user_id)
    update_query.update({"is_active": False})
    
    profile.is_active = True
    db.commit()
    
    return {"success": True, "active_id": profile_id, "is_default": profile.is_default}


@router.delete("/profiles/{profile_id}")
def delete_regex_profile(profile_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.id == profile_id),
        models.DBRegexProfile,
        user_id,
    )
    profile = query.first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    if profile.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default regex profile")
    
    db.delete(profile)
    db.commit()
    
    return {"success": True}


@router.post("/profiles/{profile_id}/toggle")
def toggle_regex_profile(profile_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    
    query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.id == profile_id),
        models.DBRegexProfile,
        user_id,
    )
    profile = query.first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    config = json.loads(profile.config_json) if profile.config_json else {}
    
    if "root" in config:
        config["root"]["enabled"] = not config["root"].get("enabled", True)
    
    profile.config_json = json.dumps(config, ensure_ascii=False)
    db.commit()
    
    return {"success": True, "enabled": config["root"].get("enabled", True), "is_default": profile.is_default}
