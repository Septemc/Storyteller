"""文本向量化模块 - 支持多种 Embedding 方案。

支持：
- OpenAI Embeddings API (兼容所有 OpenAI 兼容接口)
- sentence-transformers (本地模型，如 paraphrase-multilingual-MiniLM)
- 简单的词频向量 (降级方案，无需依赖)
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx


@dataclass
class EmbeddingConfig:
    """Embedding 配置"""
    provider: str = "openai"  # "openai" | "sentence_transformers" | "tfidf"
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    dimension: int = 768


class EmbeddingError(RuntimeError):
    """Embedding 相关错误"""
    pass


def _normalize_text(text: str) -> str:
    """标准化文本：去除多余空白、统一大小写等"""
    if not text:
        return ""
    # 去除首尾空白，压缩连续空白
    text = " ".join(text.split())
    return text


def _text_hash(text: str) -> str:
    """计算文本哈希，用于缓存"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ============================================================
# OpenAI Embeddings API 实现
# ============================================================

def _openai_embeddings(
    texts: List[str],
    base_url: str,
    api_key: str,
    model: str = "text-embedding-ada-002",
    timeout_s: float = 60.0,
) -> List[List[float]]:
    """调用 OpenAI 兼容的 Embedding API"""
    url = base_url.rstrip("/") + "/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "input": texts,
    }

    try:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                raise EmbeddingError(f"Embedding API 请求失败：HTTP {r.status_code}: {r.text}")
            
            data = r.json()
            
            if "data" not in data:
                raise EmbeddingError(f"Embedding API 返回格式错误：{data}")
            
            # 按原始顺序返回
            embeddings_map = {item["index"]: item["embedding"] for item in data["data"]}
            return [embeddings_map[i] for i in range(len(texts))]
            
    except httpx.TimeoutException:
        raise EmbeddingError("Embedding API 请求超时")
    except Exception as e:
        raise EmbeddingError(f"Embedding 计算失败：{str(e)}")


# ============================================================
# TF-IDF 降级方案 (无需外部依赖)
# ============================================================

class TFIDFVectorizer:
    """简易 TF-IDF 向量化器 (降级方案)"""
    
    def __init__(self, max_features: int = 768):
        self.max_features = max_features
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self._fitted = False
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词：按空白和标点分割"""
        import re
        # 中文按字符分割，英文按单词分割
        text = _normalize_text(text)
        # 提取所有字符和单词
        tokens = re.findall(r'[\u4e00-\u9fa5]|[a-zA-Z]+', text)
        return [t.lower() for t in tokens if t]
    
    def fit(self, documents: List[str]) -> "TFIDFVectorizer":
        """拟合 IDF 权重"""
        doc_freq: Dict[str, int] = {}
        all_tokens: set = set()
        
        for doc in documents:
            tokens = set(self._tokenize(doc))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
                all_tokens.add(token)
        
        # 选择 top-K 特征
        sorted_tokens = sorted(
            all_tokens,
            key=lambda t: doc_freq[t],
            reverse=True
        )[:self.max_features]
        
        self.vocabulary = {token: idx for idx, token in enumerate(sorted_tokens)}
        
        # 计算 IDF
        n_docs = len(documents)
        self.idf = {
            token: math.log((n_docs + 1) / (doc_freq.get(token, 0) + 1)) + 1
            for token in self.vocabulary
        }
        
        self._fitted = True
        return self
    
    def transform(self, documents: List[str]) -> List[List[float]]:
        """将文档转换为 TF-IDF 向量"""
        if not self._fitted:
            raise EmbeddingError("TFIDFVectorizer 未拟合，请先调用 fit()")
        
        result = []
        for doc in documents:
            tokens = self._tokenize(doc)
            tf: Dict[str, int] = {}
            for token in tokens:
                if token in self.vocabulary:
                    tf[token] = tf.get(token, 0) + 1
            
            # 归一化 TF
            max_tf = max(tf.values()) if tf else 1
            tf_normalized = {k: v / max_tf for k, v in tf.items()}
            
            # 计算 TF-IDF 向量
            vec = [0.0] * len(self.vocabulary)
            for token, idx in self.vocabulary.items():
                if token in tf_normalized:
                    vec[idx] = tf_normalized[token] * self.idf.get(token, 1.0)
            
            # L2 归一化
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            
            result.append(vec)
        
        return result
    
    def fit_transform(self, documents: List[str]) -> List[List[float]]:
        """拟合并转换"""
        self.fit(documents)
        return self.transform(documents)


# ============================================================
# 统一 Embedding 接口
# ============================================================

class EmbeddingEngine:
    """统一的 Embedding 引擎"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._tfidf: Optional[TFIDFVectorizer] = None
        
        # 如果是 sentence_transformers 模式，尝试导入
        if self.config.provider == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer
                model_name = self.config.model or "paraphrase-multilingual-MiniLM-L12-v2"
                self._model = SentenceTransformer(model_name)
                self.config.dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                print("[警告] sentence-transformers 未安装，降级为 TF-IDF 模式")
                self.config.provider = "tfidf"
            except Exception as e:
                # 例如模型下载失败 / 权限问题等
                print(f"[警告] sentence-transformers 初始化失败，降级为 TF-IDF 模式: {e}")
                self.config.provider = "tfidf"
    
    def compute_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> List[List[float]]:
        """批量计算文本向量"""
        if not texts:
            return []
        
        texts = [_normalize_text(t) for t in texts]
        
        if self.config.provider == "openai":
            if not self.config.base_url or not self.config.api_key:
                raise EmbeddingError("OpenAI Embedding 需要配置 base_url 和 api_key")
            
            model = self.config.model or "text-embedding-ada-002"
            
            # 分批处理
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = _openai_embeddings(
                    batch,
                    self.config.base_url,
                    self.config.api_key,
                    model=model,
                )
                all_embeddings.extend(embeddings)
            
            return all_embeddings
        
        elif self.config.provider == "sentence_transformers":
            # 本地模型批量处理
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self._model.encode(batch, convert_to_numpy=True).tolist()
                all_embeddings.extend(embeddings)
            
            return all_embeddings
        
        else:  # tfidf
            if self._tfidf is None:
                # 首次使用，用当前文本拟合
                self._tfidf = TFIDFVectorizer(max_features=self.config.dimension)
                self._tfidf.fit(texts)
            return self._tfidf.transform(texts)
    
    def compute_single(self, text: str) -> List[float]:
        """计算单个文本的向量"""
        result = self.compute_embeddings([text])
        return result[0] if result else []
    
    def update_tfidf_corpus(self, new_texts: List[str]) -> None:
        """更新 TF-IDF 语料库 (增量学习)"""
        if self.config.provider != "tfidf":
            return
        
        if self._tfidf is None:
            self._tfidf = TFIDFVectorizer(max_features=self.config.dimension)
            self._tfidf.fit(new_texts)
        else:
            # 简单方案：重新拟合 (可以优化为增量更新)
            # TODO: 实现真正的增量 TF-IDF 更新
            pass


# ============================================================
# 向量相似度计算
# ============================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    if len(vec1) != len(vec2):
        raise ValueError("向量维度不匹配")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def top_k_similar(
    query_vec: List[float],
    candidate_vecs: List[List[float]],
    top_k: int = 5,
) -> List[Tuple[int, float]]:
    """找出与查询向量最相似的 top-k 个候选向量
    
    Returns:
        [(index, similarity_score), ...] 按相似度降序排列
    """
    similarities = [
        (i, cosine_similarity(query_vec, vec))
        for i, vec in enumerate(candidate_vecs)
    ]
    
    # 按相似度降序排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_k]


# ============================================================
# 便捷函数
# ============================================================

def compute_text_similarity(text1: str, text2: str, engine: EmbeddingEngine) -> float:
    """计算两个文本的语义相似度"""
    vec1 = engine.compute_single(text1)
    vec2 = engine.compute_single(text2)
    return cosine_similarity(vec1, vec2)


def batch_compute_similarities(
    query_texts: List[str],
    candidate_texts: List[str],
    engine: EmbeddingEngine,
) -> List[List[float]]:
    """批量计算查询文本与候选文本的相似度矩阵"""
    query_vecs = engine.compute_embeddings(query_texts)
    candidate_vecs = engine.compute_embeddings(candidate_texts)
    
    matrix = []
    for q_vec in query_vecs:
        row = [cosine_similarity(q_vec, c_vec) for c_vec in candidate_vecs]
        matrix.append(row)
    
    return matrix
