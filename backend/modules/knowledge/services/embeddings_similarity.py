from __future__ import annotations

import math
from typing import List, Tuple


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if len(vec1) != len(vec2):
        raise ValueError("向量维度不匹配")
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def top_k_similar(query_vec: List[float], candidate_vecs: List[List[float]], top_k: int = 5) -> List[Tuple[int, float]]:
    similarities = [(idx, cosine_similarity(query_vec, vec)) for idx, vec in enumerate(candidate_vecs)]
    similarities.sort(key=lambda item: item[1], reverse=True)
    return similarities[:top_k]
