from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from .embeddings_config import EmbeddingConfig
from .retriever import RAGRetriever


def create_retriever(db: Session, user_id: Optional[str] = None, worldbook_id: Optional[str] = None, disabled_categories: Optional[Set[str]] = None) -> RAGRetriever:
    try:
        retriever = RAGRetriever(db, EmbeddingConfig(provider="sentence_transformers", model="paraphrase-multilingual-MiniLM-L12-v2"), user_id=user_id, worldbook_id=worldbook_id, disabled_categories=disabled_categories)
        _ = retriever.engine
        return retriever
    except Exception:
        return RAGRetriever(db, EmbeddingConfig(provider="tfidf"), user_id=user_id, worldbook_id=worldbook_id, disabled_categories=disabled_categories)


def hybrid_search(retriever: RAGRetriever, query: str, top_k: int = 8, semantic_weight: float = 0.6, importance_weight: float = 0.3, recency_weight: float = 0.1, category_filter: Optional[str] = None) -> List[Tuple[Any, float]]:
    semantic_results = retriever.semantic_search(query, top_k=top_k * 2, category_filter=category_filter)
    if not semantic_results:
        return []
    max_semantic = max(score for _, score in semantic_results) or 1.0
    now = datetime.utcnow()
    scored = []
    for entry, semantic_similarity in semantic_results:
        normalized_recency = max(0, 1 - ((now - entry.updated_at).days if entry.updated_at else 15) / 30)
        combined = semantic_weight * (semantic_similarity / max_semantic) + importance_weight * (entry.importance or 0.5) + recency_weight * normalized_recency
        scored.append((entry, combined))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]


def retrieve_for_story(retriever: RAGRetriever, recent_context: str, top_k: int = 8, use_hybrid: bool = True, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    results = hybrid_search(retriever, recent_context, top_k=top_k, category_filter=category_filter) if use_hybrid else retriever.semantic_search(recent_context, top_k=top_k, category_filter=category_filter)
    return [
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
        for entry, score in results
    ]


def retrieve_worldbook_context(db: Session, query: str, top_k: int = 8, user_id: Optional[str] = None, worldbook_id: Optional[str] = None, disabled_categories: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    retriever = create_retriever(db, user_id=user_id, worldbook_id=worldbook_id, disabled_categories=disabled_categories)
    return retrieve_for_story(retriever, query, top_k=top_k)
