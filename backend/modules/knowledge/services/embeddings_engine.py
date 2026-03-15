from __future__ import annotations

from typing import List, Optional

from .embeddings_config import EmbeddingConfig, EmbeddingError, normalize_text
from .embeddings_openai import openai_embeddings
from .embeddings_tfidf import TFIDFVectorizer


class EmbeddingEngine:
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._tfidf: Optional[TFIDFVectorizer] = None
        self._model = None
        if self.config.provider == "sentence_transformers":
            self._init_sentence_transformers()

    def _init_sentence_transformers(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            model_name = self.config.model or "paraphrase-multilingual-MiniLM-L12-v2"
            self._model = SentenceTransformer(model_name)
            self.config.dimension = self._model.get_sentence_embedding_dimension()
        except Exception:
            self.config.provider = "tfidf"

    def compute_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        normalized_texts = [normalize_text(text) for text in texts]
        if self.config.provider == "openai":
            return self._compute_openai(normalized_texts, batch_size)
        if self.config.provider == "sentence_transformers" and self._model is not None:
            return self._compute_sentence_transformers(normalized_texts, batch_size)
        return self._compute_tfidf(normalized_texts)

    def compute_single(self, text: str) -> List[float]:
        results = self.compute_embeddings([text])
        return results[0] if results else []

    def _compute_openai(self, texts: List[str], batch_size: int) -> List[List[float]]:
        if not self.config.base_url or not self.config.api_key:
            raise EmbeddingError("OpenAI Embedding 需要配置 base_url 和 api_key")
        model = self.config.model or "text-embedding-ada-002"
        batches = []
        for idx in range(0, len(texts), batch_size):
            batches.extend(openai_embeddings(texts[idx : idx + batch_size], self.config.base_url, self.config.api_key, model=model))
        return batches

    def _compute_sentence_transformers(self, texts: List[str], batch_size: int) -> List[List[float]]:
        results: List[List[float]] = []
        for idx in range(0, len(texts), batch_size):
            results.extend(self._model.encode(texts[idx : idx + batch_size], convert_to_numpy=True).tolist())
        return results

    def _compute_tfidf(self, texts: List[str]) -> List[List[float]]:
        if self._tfidf is None:
            self._tfidf = TFIDFVectorizer(max_features=self.config.dimension)
            self._tfidf.fit(texts)
        return self._tfidf.transform(texts)
