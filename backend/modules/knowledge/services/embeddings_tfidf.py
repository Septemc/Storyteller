from __future__ import annotations

import math
import re
from typing import Dict, List

from .embeddings_config import EmbeddingError, normalize_text


class TFIDFVectorizer:
    def __init__(self, max_features: int = 768):
        self.max_features = max_features
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self._fitted = False

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z]+", normalize_text(text))
        return [token.lower() for token in tokens if token]

    def fit(self, documents: List[str]) -> "TFIDFVectorizer":
        doc_freq: Dict[str, int] = {}
        all_tokens = set()
        for doc in documents:
            for token in set(self._tokenize(doc)):
                doc_freq[token] = doc_freq.get(token, 0) + 1
                all_tokens.add(token)
        sorted_tokens = sorted(all_tokens, key=lambda token: doc_freq[token], reverse=True)[: self.max_features]
        self.vocabulary = {token: idx for idx, token in enumerate(sorted_tokens)}
        n_docs = len(documents)
        self.idf = {token: math.log((n_docs + 1) / (doc_freq.get(token, 0) + 1)) + 1 for token in self.vocabulary}
        self._fitted = True
        return self

    def transform(self, documents: List[str]) -> List[List[float]]:
        if not self._fitted:
            raise EmbeddingError("TFIDFVectorizer 未拟合，请先调用 fit()")
        return [self._transform_single(doc) for doc in documents]

    def fit_transform(self, documents: List[str]) -> List[List[float]]:
        return self.fit(documents).transform(documents)

    def _transform_single(self, doc: str) -> List[float]:
        tf: Dict[str, int] = {}
        for token in self._tokenize(doc):
            if token in self.vocabulary:
                tf[token] = tf.get(token, 0) + 1
        max_tf = max(tf.values()) if tf else 1
        vec = [0.0] * len(self.vocabulary)
        for token, idx in self.vocabulary.items():
            if token in tf:
                vec[idx] = (tf[token] / max_tf) * self.idf.get(token, 1.0)
        norm = math.sqrt(sum(value * value for value in vec))
        return [value / norm for value in vec] if norm > 0 else vec
