from __future__ import annotations

import json
import uuid
from typing import Dict, Iterable, Optional

from sqlalchemy.orm import Session

from ....core.tenant import owner_only
from ....db import models


def persist_segment_log(db: Session, story_id: str, session_id: str, segment_id: str, payload: Dict, user_id: Optional[str]) -> None:
    existing = owner_only(db.query(models.AgentSegmentLog).filter(models.AgentSegmentLog.segment_id == segment_id), models.AgentSegmentLog, user_id).first()
    public_log = json.dumps(payload.get("publicLog") or {}, ensure_ascii=False)
    developer_log = json.dumps(payload, ensure_ascii=False)
    if existing:
        existing.public_log_json = public_log
        existing.developer_log_json = developer_log
        db.commit()
        return
    db.add(
        models.AgentSegmentLog(
            log_id=f"seglog_{uuid.uuid4().hex[:12]}",
            story_id=story_id,
            session_id=session_id,
            segment_id=segment_id,
            public_log_json=public_log,
            developer_log_json=developer_log,
            user_id=user_id,
        )
    )
    db.commit()


def load_segment_logs(db: Session, session_id: str, user_id: Optional[str]) -> Dict[str, Dict]:
    rows = owner_only(db.query(models.AgentSegmentLog).filter(models.AgentSegmentLog.session_id == session_id), models.AgentSegmentLog, user_id).order_by(models.AgentSegmentLog.created_at.desc()).all()
    return {row.segment_id: _build_log_payload(row) for row in rows}


def delete_logs_for_session(db: Session, session_id: str, user_id: Optional[str]) -> None:
    owner_only(db.query(models.AgentSegmentLog).filter(models.AgentSegmentLog.session_id == session_id), models.AgentSegmentLog, user_id).delete()
    db.commit()


def delete_logs_for_segments(db: Session, segment_ids: Iterable[str], user_id: Optional[str]) -> None:
    ids = [segment_id for segment_id in segment_ids if segment_id]
    if not ids:
        return
    owner_only(db.query(models.AgentSegmentLog).filter(models.AgentSegmentLog.segment_id.in_(ids)), models.AgentSegmentLog, user_id).delete(synchronize_session=False)
    db.commit()


def copy_segment_logs(db: Session, source_session_id: str, target_session_id: str, segment_pairs: Dict[str, str], user_id: Optional[str]) -> None:
    if not segment_pairs:
        return
    rows = owner_only(db.query(models.AgentSegmentLog).filter(models.AgentSegmentLog.session_id == source_session_id), models.AgentSegmentLog, user_id).all()
    for row in rows:
        new_segment_id = segment_pairs.get(row.segment_id)
        if not new_segment_id:
            continue
        db.add(
            models.AgentSegmentLog(
                log_id=f"seglog_{uuid.uuid4().hex[:12]}",
                story_id=row.story_id,
                session_id=target_session_id,
                segment_id=new_segment_id,
                public_log_json=row.public_log_json,
                developer_log_json=row.developer_log_json,
                user_id=user_id,
            )
        )
    db.commit()


def _build_log_payload(row: models.AgentSegmentLog) -> Dict:
    return {
        "publicLog": _load_json(row.public_log_json, {}),
        "developerLog": _load_json(row.developer_log_json, {}),
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "segmentId": row.segment_id,
    }


def _load_json(value: Optional[str], default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default
