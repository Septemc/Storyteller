from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import get_db
from .regex_schemas import RegexProfileCreate, RegexProfileListItem, RegexProfileResponse, RegexProfileUpdate

router = APIRouter(prefix="/regex")
DEFAULT_REGEX_PATH = Path(__file__).resolve().parents[4] / "data" / "default_regex.json"


def ensure_default_regex_in_db(db: Session, user_id: Optional[str] = None) -> models.DBRegexProfile:
    default_profile = owner_only(db.query(models.DBRegexProfile).filter(models.DBRegexProfile.is_default == True), models.DBRegexProfile, user_id).first()
    if default_profile:
        return default_profile
    config = json.loads(DEFAULT_REGEX_PATH.read_text(encoding="utf-8")) if DEFAULT_REGEX_PATH.exists() else {"rules": []}
    profile = models.DBRegexProfile(id=f"regex_{uuid.uuid4().hex[:10]}", name="默认正则", version=1, is_default=True, is_active=True, config_json=json.dumps(config, ensure_ascii=False), user_id=user_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profiles", response_model=list[RegexProfileListItem])
def list_regex_profiles(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    profiles = owner_only(db.query(models.DBRegexProfile), models.DBRegexProfile, user_id).order_by(models.DBRegexProfile.created_at.asc()).all()
    return [RegexProfileListItem(id=profile.id, name=profile.name, version=profile.version, is_default=profile.is_default, is_active=profile.is_active) for profile in profiles]


@router.get("/profiles/{profile_id}", response_model=RegexProfileResponse)
def get_regex_profile(profile_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    return _to_profile_response(_get_profile_or_404(db, profile_id, current_user_id(current_user)))


@router.get("/active", response_model=RegexProfileResponse)
def get_active_regex_profile(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    profile = owner_only(db.query(models.DBRegexProfile).filter(models.DBRegexProfile.is_active == True), models.DBRegexProfile, user_id).first()
    return _to_profile_response(profile or ensure_default_regex_in_db(db, user_id))


@router.post("/profiles", response_model=RegexProfileResponse)
def create_regex_profile(req: RegexProfileCreate, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_regex_in_db(db, user_id)
    profile = models.DBRegexProfile(id=f"regex_{uuid.uuid4().hex[:10]}", name=req.name, version=1, is_default=False, is_active=False, config_json=json.dumps({"rules": req.rules}, ensure_ascii=False), user_id=user_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _to_profile_response(profile)


@router.put("/profiles/{profile_id}", response_model=RegexProfileResponse)
def update_regex_profile(profile_id: str, req: RegexProfileUpdate, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    profile = _get_profile_or_404(db, profile_id, current_user_id(current_user))
    config = json.loads(profile.config_json) if profile.config_json else {"rules": []}
    if req.name is not None:
        profile.name = req.name
    if req.rules is not None:
        config["rules"] = req.rules
        profile.config_json = json.dumps(config, ensure_ascii=False)
        profile.version += 1
    db.commit()
    db.refresh(profile)
    return _to_profile_response(profile)


@router.put("/active")
def set_active_regex_profile(profile_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    profile = _get_profile_or_404(db, profile_id, user_id)
    owner_only(db.query(models.DBRegexProfile), models.DBRegexProfile, user_id).update({models.DBRegexProfile.is_active: False})
    profile.is_active = True
    db.commit()
    return {"success": True, "profile_id": profile.id}


@router.delete("/profiles/{profile_id}")
def delete_regex_profile(profile_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    profile = _get_profile_or_404(db, profile_id, current_user_id(current_user))
    if profile.is_default:
        raise HTTPException(status_code=400, detail="默认正则配置不可删除")
    db.delete(profile)
    db.commit()
    return {"success": True}


@router.post("/profiles/{profile_id}/toggle")
def toggle_regex_profile(profile_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    profile = _get_profile_or_404(db, profile_id, current_user_id(current_user))
    profile.is_active = not profile.is_active
    db.commit()
    return {"success": True, "is_active": profile.is_active}


def _get_profile_or_404(db: Session, profile_id: str, user_id: Optional[str]) -> models.DBRegexProfile:
    profile = owner_only(db.query(models.DBRegexProfile).filter(models.DBRegexProfile.id == profile_id), models.DBRegexProfile, user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="正则配置不存在")
    return profile


def _to_profile_response(profile: models.DBRegexProfile) -> RegexProfileResponse:
    config = json.loads(profile.config_json) if profile.config_json else {"rules": []}
    return RegexProfileResponse(id=profile.id, name=profile.name, version=profile.version, is_default=profile.is_default, is_active=profile.is_active, rules=config.get("rules", []))
