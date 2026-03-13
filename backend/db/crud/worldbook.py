from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .. import models


def cleanup_orphan_worldbook_embeddings(db: Session, user_id: Optional[str] = None) -> int:
    embeddings = db.query(models.WorldbookEmbedding).all()
    deleted = 0

    for embedding in embeddings:
        if user_id is not None and embedding.user_id not in {None, user_id}:
            continue

        matched_entry = (
            db.query(models.WorldbookEntry)
            .filter(models.WorldbookEntry.entry_id == embedding.entry_id)
            .first()
        )

        if matched_entry and matched_entry.worldbook_id == embedding.worldbook_id:
            continue

        db.delete(embedding)
        deleted += 1

    if deleted:
        db.commit()

    return deleted
