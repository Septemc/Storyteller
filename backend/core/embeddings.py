from ..modules.knowledge.services.embeddings_config import EmbeddingConfig, EmbeddingError, normalize_text as _normalize_text, text_hash as _text_hash
from ..modules.knowledge.services.embeddings_engine import EmbeddingEngine
from ..modules.knowledge.services.embeddings_similarity import cosine_similarity, top_k_similar
from ..modules.knowledge.services.embeddings_tfidf import TFIDFVectorizer


def compute_text_similarity(text1: str, text2: str, engine: EmbeddingEngine) -> float:
    vec1 = engine.compute_single(text1)
    vec2 = engine.compute_single(text2)
    return cosine_similarity(vec1, vec2)


def batch_compute_similarities(query_texts, candidate_texts, engine):
    query_vecs = engine.compute_embeddings(query_texts)
    candidate_vecs = engine.compute_embeddings(candidate_texts)
    return [[cosine_similarity(q_vec, c_vec) for c_vec in candidate_vecs] for q_vec in query_vecs]


__all__ = [
    "EmbeddingConfig",
    "EmbeddingEngine",
    "EmbeddingError",
    "TFIDFVectorizer",
    "_normalize_text",
    "_text_hash",
    "batch_compute_similarities",
    "compute_text_similarity",
    "cosine_similarity",
    "top_k_similar",
]
