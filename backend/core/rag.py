from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..db import models
from .embeddings import EmbeddingConfig, EmbeddingEngine, EmbeddingError, _text_hash, top_k_similar
from .tenant import owner_or_public


class RAGRetriever:
    def __init__(
        self,
        db: Session,
        embedding_config: Optional[EmbeddingConfig] = None,
        user_id: Optional[str] = None,
        worldbook_id: Optional[str] = None,
    ):
        self.db = db
        self.embedding_config = embedding_config or EmbeddingConfig()
        self.user_id = user_id
        self.worldbook_id = worldbook_id
        self._engine: Optional[EmbeddingEngine] = None

    @property
    def engine(self) -> EmbeddingEngine:
        if self._engine is None:
            self._engine = EmbeddingEngine(self.embedding_config)
        return self._engine

    def _entry_query(self):
        query = owner_or_public(self.db.query(models.WorldbookEntry), models.WorldbookEntry, self.user_id)
        if self.worldbook_id:
            query = query.filter(models.WorldbookEntry.worldbook_id == self.worldbook_id)
        return query

    def _embedding_query(self, entry: models.WorldbookEntry):
        return self.db.query(models.WorldbookEmbedding).filter(
            models.WorldbookEmbedding.entry_id == entry.entry_id,
            models.WorldbookEmbedding.user_id == entry.user_id,
            models.WorldbookEmbedding.worldbook_id == entry.worldbook_id,
        )

    def _get_embedding_cache(
        self,
        entry: models.WorldbookEntry,
    ) -> Optional[Tuple[List[float], str, int]]:
        cache = self._embedding_query(entry).first()
        if not cache:
            return None
        try:
            embedding = json.loads(cache.embedding_json)
            return embedding, cache.embedding_model, cache.dimension
        except Exception:
            return None

    def _save_embedding_cache(
        self,
        entry: models.WorldbookEntry,
        embedding: List[float],
        content_hash: str,
    ) -> None:
        cache = self._embedding_query(entry).first()
        embedding_json = json.dumps(embedding, ensure_ascii=False)
        model = self.embedding_config.provider
        dimension = len(embedding)

        if cache:
            cache.embedding_json = embedding_json
            cache.content_hash = content_hash
            cache.embedding_model = model
            cache.dimension = dimension
            cache.updated_at = datetime.utcnow()
        else:
            cache = models.WorldbookEmbedding(
                user_id=entry.user_id,
                worldbook_id=entry.worldbook_id,
                entry_id=entry.entry_id,
                embedding_json=embedding_json,
                content_hash=content_hash,
                embedding_model=model,
                dimension=dimension,
            )
            self.db.add(cache)

        self.db.commit()

    def _should_recompute_embedding(
        self,
        entry: models.WorldbookEntry,
        cache: Optional[models.WorldbookEmbedding],
    ) -> bool:
        if not cache:
            return True

        content = f"{entry.title} {entry.content}"
        current_hash = _text_hash(content)
        if cache.content_hash != current_hash:
            return True
        if cache.embedding_model != self.embedding_config.provider:
            return True
        return False

    def compute_entry_embedding(
        self,
        entry: models.WorldbookEntry,
        use_cache: bool = True,
    ) -> List[float]:
        if use_cache:
            cached = self._get_embedding_cache(entry)
            if cached:
                cache_model = self._embedding_query(entry).first()
                if not self._should_recompute_embedding(entry, cache_model):
                    return cached[0]

        content = f"{entry.title} {entry.content}"

        if self.embedding_config.provider == "tfidf":
            self._refit_tfidf_all_entries()
            cached = self._get_embedding_cache(entry)
            if cached:
                return cached[0]

        embedding = self.engine.compute_single(content)
        self._save_embedding_cache(entry, embedding, _text_hash(content))
        return embedding

    def _refit_tfidf_all_entries(self) -> None:
        if self.embedding_config.provider != "tfidf":
            return

        entries = self._entry_query().all()
        if not entries:
            return

        contents = [f"{entry.title} {entry.content}" for entry in entries]
        embeddings = self.engine.compute_embeddings(contents)
        for entry, content, embedding in zip(entries, contents, embeddings):
            self._save_embedding_cache(entry, embedding, _text_hash(content))

    def compute_missing_embeddings(
        self,
        limit: int = 100,
    ) -> int:
        entries: List[models.WorldbookEntry] = []
        for entry in self._entry_query().all():
            if self._embedding_query(entry).first() is None:
                entries.append(entry)
            if len(entries) >= limit:
                break

        if not entries:
            return 0

        contents = [f"{entry.title} {entry.content}" for entry in entries]
        embeddings = self.engine.compute_embeddings(contents)
        for entry, content, embedding in zip(entries, contents, embeddings):
            self._save_embedding_cache(entry, embedding, _text_hash(content))
        return len(entries)

    def compute_batch_embeddings(
        self,
        texts: List[str],
        max_dim: int = 500,
    ) -> List:
        if not texts:
            return []

        if self.embedding_config.provider == "tfidf":
            from .embeddings import TFIDFVectorizer

            tfidf = TFIDFVectorizer(max_features=max_dim)
            normalized_texts = [text.lower().strip() for text in texts]
            tfidf.fit(normalized_texts)
            return tfidf.transform(normalized_texts)

        return [self.engine.compute_single(text) for text in texts]

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
        category_filter: Optional[str] = None,
    ) -> List[Tuple[models.WorldbookEntry, float]]:
        candidate_query = self._entry_query()
        if category_filter:
            candidate_query = candidate_query.filter(models.WorldbookEntry.category == category_filter)

        candidates = candidate_query.all()
        if not candidates:
            return []

        if self.embedding_config.provider == "tfidf":
            contents = [f"{entry.title} {entry.content}" for entry in candidates]
            all_texts = contents + [query]
            all_vecs = self.engine.compute_embeddings(all_texts)
            candidate_vecs = all_vecs[:-1]
            query_vec = all_vecs[-1]
        else:
            query_vec = self.engine.compute_single(query)
            candidate_vecs = []
            filtered_candidates: List[models.WorldbookEntry] = []
            for candidate in candidates:
                try:
                    candidate_vecs.append(self.compute_entry_embedding(candidate, use_cache=True))
                    filtered_candidates.append(candidate)
                except EmbeddingError:
                    continue
            candidates = filtered_candidates

        if not candidate_vecs:
            return []

        similarities = top_k_similar(query_vec, candidate_vecs, top_k=len(candidate_vecs))
        results: List[Tuple[models.WorldbookEntry, float]] = []
        for idx, similarity in similarities:
            if similarity >= min_similarity:
                results.append((candidates[idx], similarity))

        results.sort(key=lambda item: item[1], reverse=True)
        return results[:top_k]

    def hybrid_search(
        self,
        query: str,
        top_k: int = 8,
        semantic_weight: float = 0.6,
        importance_weight: float = 0.3,
        recency_weight: float = 0.1,
        category_filter: Optional[str] = None,
    ) -> List[Tuple[models.WorldbookEntry, float]]:
        semantic_results = self.semantic_search(
            query,
            top_k=top_k * 2,
            category_filter=category_filter,
        )
        if not semantic_results:
            return []

        max_semantic = max(similarity for _, similarity in semantic_results) or 1.0
        now = datetime.utcnow()
        max_days = 30
        scored_entries: List[Tuple[models.WorldbookEntry, float]] = []

        for entry, semantic_similarity in semantic_results:
            normalized_semantic = semantic_similarity / max_semantic
            normalized_importance = entry.importance or 0.5
            if entry.updated_at:
                days_old = (now - entry.updated_at).days
                normalized_recency = max(0, 1 - days_old / max_days)
            else:
                normalized_recency = 0.5

            combined_score = (
                semantic_weight * normalized_semantic
                + importance_weight * normalized_importance
                + recency_weight * normalized_recency
            )
            scored_entries.append((entry, combined_score))

        scored_entries.sort(key=lambda item: item[1], reverse=True)
        return scored_entries[:top_k]

    def retrieve_for_story(
        self,
        recent_context: str,
        top_k: int = 8,
        use_hybrid: bool = True,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if use_hybrid:
            results = self.hybrid_search(
                recent_context,
                top_k=top_k,
                category_filter=category_filter,
            )
        else:
            results = self.semantic_search(
                recent_context,
                top_k=top_k,
                category_filter=category_filter,
            )

        output: List[Dict[str, Any]] = []
        for entry, score in results:
            output.append(
                {
                    "worldbook_id": entry.worldbook_id,
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "category": entry.category,
                    "content": entry.content[:800],
                    "importance": entry.importance,
                    "canonical": entry.canonical,
                    "relevance_score": round(score, 4),
                }
            )
        return output


def create_retriever(
    db: Session,
    user_id: Optional[str] = None,
    worldbook_id: Optional[str] = None,
) -> RAGRetriever:
    try:
        config = EmbeddingConfig(
            provider="sentence_transformers",
            model="paraphrase-multilingual-MiniLM-L12-v2",
        )
        retriever = RAGRetriever(db, config, user_id=user_id, worldbook_id=worldbook_id)
        _ = retriever.engine
        return retriever
    except Exception:
        fallback = EmbeddingConfig(provider="tfidf")
        return RAGRetriever(db, fallback, user_id=user_id, worldbook_id=worldbook_id)


def retrieve_worldbook_context(
    db: Session,
    query: str,
    top_k: int = 8,
    user_id: Optional[str] = None,
    worldbook_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    retriever = create_retriever(db, user_id=user_id, worldbook_id=worldbook_id)
    return retriever.retrieve_for_story(query, top_k=top_k)
