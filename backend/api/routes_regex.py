import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models

router = APIRouter(prefix="/regex", tags=["regex"])

DEFAULT_REGEX_PATH = Path(__file__).parent.parent.parent / "data" / "default_regex.json"


def load_default_regex() -> Dict[str, Any]:
    if DEFAULT_REGEX_PATH.exists():
        with open(DEFAULT_REGEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "id": "regex_default",
        "name": "默认正则化",
        "version": 1,
        "is_default": True,
        "root": {
            "id": "node_regex_root",
            "identifier": "regex_root",
            "kind": "group",
            "title": "正则化规则组",
            "enabled": True,
            "children": []
        },
        "meta": {}
    }


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
def list_regex_profiles(db: Session = Depends(get_db)):
    default_regex = load_default_regex()
    default_id = default_regex["id"]
    
    profiles = db.query(models.DBRegexProfile).order_by(
        models.DBRegexProfile.created_at.desc()
    ).all()
    
    result = [
        RegexProfileListItem(
            id=default_regex["id"],
            name=default_regex["name"],
            version=default_regex.get("version", 1),
            is_default=True,
            is_active=False
        )
    ]
    
    active_id = None
    for p in profiles:
        if p.id == default_id:
            continue
        if p.is_active:
            active_id = p.id
        result.append(
            RegexProfileListItem(
                id=p.id,
                name=p.name,
                version=p.version,
                is_default=False,
                is_active=p.is_active
            )
        )
    
    if active_id is None:
        result[0].is_active = True
    
    return result


@router.get("/profiles/{profile_id}", response_model=RegexProfileResponse)
def get_regex_profile(profile_id: str, db: Session = Depends(get_db)):
    default_regex = load_default_regex()
    
    if profile_id == default_regex["id"]:
        return RegexProfileResponse(
            id=default_regex["id"],
            name=default_regex["name"],
            version=default_regex.get("version", 1),
            is_default=True,
            is_active=True,
            config=default_regex,
            created_at=None,
            updated_at=None
        )
    
    profile = db.query(models.DBRegexProfile).filter(
        models.DBRegexProfile.id == profile_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    return RegexProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        is_default=False,
        is_active=profile.is_active,
        config=json.loads(profile.config_json) if profile.config_json else {},
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None
    )


@router.get("/active", response_model=RegexProfileResponse)
def get_active_regex_profile(db: Session = Depends(get_db)):
    default_regex = load_default_regex()
    
    profile = db.query(models.DBRegexProfile).filter(
        models.DBRegexProfile.is_active == True
    ).first()
    
    if not profile:
        return RegexProfileResponse(
            id=default_regex["id"],
            name=default_regex["name"],
            version=default_regex.get("version", 1),
            is_default=True,
            is_active=True,
            config=default_regex,
            created_at=None,
            updated_at=None
        )
    
    return RegexProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        is_default=False,
        is_active=True,
        config=json.loads(profile.config_json) if profile.config_json else {},
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None
    )


@router.post("/profiles", response_model=RegexProfileResponse)
def create_regex_profile(req: RegexProfileCreate, db: Session = Depends(get_db)):
    default_regex = load_default_regex()
    
    profile_id = f"regex_{uuid.uuid4().hex[:10]}"
    
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
                "children": [
                    {
                        "id": f"node_{uuid.uuid4().hex[:8]}",
                        "kind": "group",
                        "title": "新建规则组",
                        "identifier": "new_group",
                        "enabled": True,
                        "children": [
                            {
                                "id": f"node_{uuid.uuid4().hex[:8]}",
                                "kind": "regex",
                                "title": "未命名规则",
                                "identifier": "new_rule",
                                "enabled": True,
                                "pattern": "",
                                "replacement": "",
                                "extract_group": 0,
                                "apply_to": "body",
                                "description": ""
                            }
                        ]
                    }
                ]
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
        config_json=json.dumps(config, ensure_ascii=False)
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
    db: Session = Depends(get_db)
):
    default_regex = load_default_regex()
    
    if profile_id == default_regex["id"]:
        raise HTTPException(status_code=400, detail="Cannot modify default profile")
    
    profile = db.query(models.DBRegexProfile).filter(
        models.DBRegexProfile.id == profile_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    if req.name:
        profile.name = req.name
    
    if req.config:
        config = req.config
        config["id"] = profile.id
        config["name"] = profile.name
        config["is_default"] = False
        profile.config_json = json.dumps(config, ensure_ascii=False)
    
    db.commit()
    db.refresh(profile)
    
    return RegexProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        is_default=False,
        is_active=profile.is_active,
        config=json.loads(profile.config_json) if profile.config_json else {},
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None
    )


@router.put("/active")
def set_active_regex_profile(
    profile_id: str = Query(..., description="正则化配置ID"),
    db: Session = Depends(get_db)
):
    default_regex = load_default_regex()
    
    if profile_id == default_regex["id"]:
        db.query(models.DBRegexProfile).update({"is_active": False})
        db.commit()
        return {"success": True, "active_id": profile_id, "is_default": True}
    
    profile = db.query(models.DBRegexProfile).filter(
        models.DBRegexProfile.id == profile_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    db.query(models.DBRegexProfile).update({"is_active": False})
    
    profile.is_active = True
    db.commit()
    
    return {"success": True, "active_id": profile_id, "is_default": False}


@router.delete("/profiles/{profile_id}")
def delete_regex_profile(profile_id: str, db: Session = Depends(get_db)):
    default_regex = load_default_regex()
    
    if profile_id == default_regex["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete default profile")
    
    profile = db.query(models.DBRegexProfile).filter(
        models.DBRegexProfile.id == profile_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    db.delete(profile)
    db.commit()
    
    return {"success": True}


@router.post("/profiles/{profile_id}/toggle")
def toggle_regex_profile(profile_id: str, db: Session = Depends(get_db)):
    default_regex = load_default_regex()
    
    if profile_id == default_regex["id"]:
        return {"success": True, "enabled": True, "is_default": True}
    
    profile = db.query(models.DBRegexProfile).filter(
        models.DBRegexProfile.id == profile_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Regex profile not found")
    
    config = json.loads(profile.config_json) if profile.config_json else {}
    
    if "root" in config:
        config["root"]["enabled"] = not config["root"].get("enabled", True)
    
    profile.config_json = json.dumps(config, ensure_ascii=False)
    db.commit()
    
    return {"success": True, "enabled": config["root"].get("enabled", True), "is_default": False}
