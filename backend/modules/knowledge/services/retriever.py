from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from ....db import models
from ....core.tenant import owner_or_public
from .embeddings_config import EmbeddingConfig, EmbeddingError, text_hash
from .embeddings_engine import EmbeddingEngine
from .embeddings_similarity import top_k_similar


class RAGRetriever:
    def __init__(self, db: Session, embedding_config: Optional[EmbeddingConfig] = None, user_id: Optional[str] = None, worldbook_id: Optional[str] = None, disabled_categories: Optional[Set[str]] = None):
        self.db = db
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.user_id = user_id
        self.worldbook_id = worldbook_id
        self.disabled_categories = set(disabled_categories or set())
        self._engine: Optional[EmbeddingEngine] = None

    @property
    def engine(self) -> EmbeddingEngine:
        if self._engine is None:
            self._engine = EmbeddingEngine(self.embedding_config)
        return self._engine

    def _entry_query(self):
        query = owner_or_public(self.db.query(models.WorldbookEntry), models.WorldbookEntry, self.user_id)
        return query.filter(models.WorldbookEntry.worldbook_id == self.worldbook_id) if self.worldbook_id else query

    def _embedding_query(self, entry: models.WorldbookEntry):
        return self.db.query(models.WorldbookEmbedding).filter(models.WorldbookEmbedding.entry_id == entry.entry_id, models.WorldbookEmbedding.user_id == entry.user_id, models.WorldbookEmbedding.worldbook_id == entry.worldbook_id)

    def _entry_enabled(self, entry: models.WorldbookEntry) -> bool:
        meta = json.loads(entry.meta_json) if entry.meta_json else {}
        category_name = (entry.category or "").strip()
        return meta.get("enabled", True) is not False and not bool(meta.get("disable") or meta.get("disabled")) and category_name not in self.disabled_categories

    def _filtered_entries(self, category_filter: Optional[str] = None) -> List[models.WorldbookEntry]:
        query = self._entry_query()
        if category_filter:
            query = query.filter(models.WorldbookEntry.category == category_filter)
        return [entry for entry in query.all() if self._entry_enabled(entry)]

    def _get_embedding_cache(self, entry: models.WorldbookEntry) -> Optional[Tuple[List[float], str, int]]:
        cache = self._embedding_query(entry).first()
        if not cache:
            return None
        try:
            return json.loads(cache.embedding_json), cache.embedding_model, cache.dimension
        except Exception:
            return None

    def _save_embedding_cache(self, entry: models.WorldbookEntry, embedding: List[float], content_hash: str) -> None:
        cache = self._embedding_query(entry).first()
        payload = {"embedding_json": json.dumps(embedding, ensure_ascii=False), "content_hash": content_hash, "embedding_model": self.embedding_config.provider, "dimension": len(embedding), "updated_at": datetime.utcnow()}
        if cache:
            for key, value in payload.items():
                setattr(cache, key, value)
        else:
            self.db.add(models.WorldbookEmbedding(user_id=entry.user_id, worldbook_id=entry.worldbook_id, entry_id=entry.entry_id, **payload))
        self.db.commit()

    def compute_entry_embedding(self, entry: models.WorldbookEntry, use_cache: bool = True) -> List[float]:
        cached = self._get_embedding_cache(entry) if use_cache else None
        content = f"{entry.title} {entry.content}"
        if cached and self._embedding_query(entry).first().content_hash == text_hash(content):
            return cached[0]
        embedding = self.engine.compute_single(content)
        self._save_embedding_cache(entry, embedding, text_hash(content))
        return embedding

    def compute_missing_embeddings(self, limit: int = 100) -> int:
        entries = [entry for entry in self._filtered_entries() if self._embedding_query(entry).first() is None][:limit]
        for entry in entries:
            self.compute_entry_embedding(entry, use_cache=False)
        return len(entries)

    def compute_batch_embeddings(self, texts: List[str], max_dim: int = 500) -> List[List[float]]:
        if self.embedding_config.provider == "tfidf":
            from .embeddings_tfidf import TFIDFVectorizer

            tfidf = TFIDFVectorizer(max_features=max_dim)
            normalized_texts = [text.lower().strip() for text in texts]
            return tfidf.fit_transform(normalized_texts)
        return [self.engine.compute_single(text) for text in texts]

    def semantic_search(self, query: str, top_k: int = 5, min_similarity: float = 0.0, category_filter: Optional[str] = None) -> List[Tuple[models.WorldbookEntry, float]]:
        candidates = self._filtered_entries(category_filter=category_filter)
        if not candidates:
            return []
        if self.embedding_config.provider == "tfidf":
            contents = [f"{entry.title} {entry.content}" for entry in candidates]
            vectors = self.engine.compute_embeddings(contents + [query])
            query_vec, candidate_vecs = vectors[-1], vectors[:-1]
        else:
            query_vec = self.engine.compute_single(query)
            candidate_vecs, candidates = self._semantic_candidate_vectors(candidates)
        similarities = top_k_similar(query_vec, candidate_vecs, top_k=len(candidate_vecs))
        return [(candidates[idx], score) for idx, score in similarities if score >= min_similarity][:top_k]

    def _semantic_candidate_vectors(self, candidates: List[models.WorldbookEntry]) -> Tuple[List[List[float]], List[models.WorldbookEntry]]:
        vectors: List[List[float]] = []
        filtered: List[models.WorldbookEntry] = []
        for candidate in candidates:
            try:
                vectors.append(self.compute_entry_embedding(candidate, use_cache=True))
                filtered.append(candidate)
            except EmbeddingError:
                continue
        return vectors, filtered
