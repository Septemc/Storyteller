"""RAG (检索增强生成) - 世界书语义检索模块。

功能：
- 自动计算世界书条目的向量表示
- 支持语义搜索（基于向量相似度）
- 混合搜索（语义 + 关键词 + 重要性权重）
- 向量缓存管理（避免重复计算）
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..db import models
from .embeddings import (
    EmbeddingConfig,
    EmbeddingEngine,
    EmbeddingError,
    cosine_similarity,
    top_k_similar,
    _text_hash,
)


class RAGRetriever:
    """世界书 RAG 检索器"""
    
    def __init__(
        self,
        db: Session,
        embedding_config: Optional[EmbeddingConfig] = None,
    ):
        self.db = db
        self.embedding_config = embedding_config or EmbeddingConfig()
        self._engine: Optional[EmbeddingEngine] = None
    
    @property
    def engine(self) -> EmbeddingEngine:
        """懒加载 Embedding 引擎"""
        if self._engine is None:
            self._engine = EmbeddingEngine(self.embedding_config)
        return self._engine
    
    # ============================================================
    # 向量计算与缓存管理
    # ============================================================
    
    def _get_embedding_cache(
        self,
        entry_id: str,
    ) -> Optional[Tuple[List[float], str, int]]:
        """获取缓存的向量
        
        Returns:
            (embedding, model, dimension) 或 None
        """
        cache = (
            self.db.query(models.WorldbookEmbedding)
            .filter(models.WorldbookEmbedding.entry_id == entry_id)
            .first()
        )
        
        if not cache:
            return None
        
        try:
            embedding = json.loads(cache.embedding_json)
            return embedding, cache.embedding_model, cache.dimension
        except Exception:
            return None
    
    def _save_embedding_cache(
        self,
        entry_id: str,
        embedding: List[float],
        content_hash: str,
    ) -> None:
        """保存向量缓存"""
        cache = (
            self.db.query(models.WorldbookEmbedding)
            .filter(models.WorldbookEmbedding.entry_id == entry_id)
            .first()
        )
        
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
                entry_id=entry_id,
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
        """判断是否需要重新计算向量"""
        if not cache:
            return True
        
        # 检查内容是否变化
        content = f"{entry.title} {entry.content}"
        current_hash = _text_hash(content)
        
        if cache.content_hash != current_hash:
            return True
        
        # 检查模型是否变化
        if cache.embedding_model != self.embedding_config.provider:
            return True
        
        return False
    
    def compute_entry_embedding(
        self,
        entry: models.WorldbookEntry,
        use_cache: bool = True,
    ) -> List[float]:
        """计算单个条目的向量"""
        # 检查缓存
        if use_cache:
            cached = self._get_embedding_cache(entry.entry_id)
            if cached:
                cache_model = (
                    self.db.query(models.WorldbookEmbedding)
                    .filter(models.WorldbookEmbedding.entry_id == entry.entry_id)
                    .first()
                )
                if not self._should_recompute_embedding(entry, cache_model):
                    return cached[0]
        
        # 计算新向量
        content = f"{entry.title} {entry.content}"
        
        # 对于 TF-IDF，使用批量计算以确保词汇表一致
        if self.embedding_config.provider == "tfidf":
            # 重新拟合整个语料库（简单但有效的方法）
            self._refit_tfidf_all_entries()
            # 从缓存获取
            cached = self._get_embedding_cache(entry.entry_id)
            if cached:
                return cached[0]
        
        embedding = self.engine.compute_single(content)
        
        # 保存缓存
        content_hash = _text_hash(content)
        self._save_embedding_cache(entry.entry_id, embedding, content_hash)
        
        return embedding
    
    def _refit_tfidf_all_entries(self) -> None:
        """重新拟合所有条目的 TF-IDF 向量"""
        if self.embedding_config.provider != "tfidf":
            return
        
        # 获取所有条目
        entries = self.db.query(models.WorldbookEntry).all()
        if not entries:
            return
        
        # 批量计算所有内容的向量
        contents = [f"{e.title} {e.content}" for e in entries]
        embeddings = self.engine.compute_embeddings(contents)
        
        # 保存所有缓存
        for entry, content, embedding in zip(entries, contents, embeddings):
            content_hash = _text_hash(content)
            self._save_embedding_cache(entry.entry_id, embedding, content_hash)
    
    def compute_missing_embeddings(
        self,
        limit: int = 100,
    ) -> int:
        """批量计算缺失的向量
        
        Returns:
            计算的条目数量
        """
        # 找出所有没有向量的条目
        entries = (
            self.db.query(models.WorldbookEntry)
            .outerjoin(
                models.WorldbookEmbedding,
                models.WorldbookEntry.entry_id == models.WorldbookEmbedding.entry_id
            )
            .filter(models.WorldbookEmbedding.id.is_(None))
            .limit(limit)
            .all()
        )
        
        if not entries:
            return 0
        
        # 批量计算
        contents = [f"{e.title} {e.content}" for e in entries]
        embeddings = self.engine.compute_embeddings(contents)
        
        # 保存缓存
        for entry, content, embedding in zip(entries, contents, embeddings):
            content_hash = _text_hash(content)
            self._save_embedding_cache(entry.entry_id, embedding, content_hash)
        
        return len(entries)
    
    def compute_batch_embeddings(
        self,
        texts: List[str],
        max_dim: int = 500,
    ) -> List:
        """批量计算文本的向量（用于导入时快速计算）
        
        Args:
            texts: 文本列表
            max_dim: 最大维度（仅用于 TF-IDF）
        
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        # 对于 TF-IDF，使用批量计算
        if self.embedding_config.provider == "tfidf":
            # 重新拟合 TF-IDF 模型以包含新文本
            from .embeddings import TFIDFVectorizer
            tfidf = TFIDFVectorizer(max_features=max_dim)
            normalized_texts = [t.lower().strip() for t in texts]
            tfidf.fit(normalized_texts)
            return tfidf.transform(normalized_texts)
        
        # 对于其他引擎，使用通用方法
        return [self.engine.compute_single(text) for text in texts]
    
    # ============================================================
    # 检索功能
    # ============================================================
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0,  # 降低默认阈值，TF-IDF 分数通常较低
        category_filter: Optional[str] = None,
    ) -> List[Tuple[models.WorldbookEntry, float]]:
        """语义搜索：基于向量相似度
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_similarity: 最低相似度阈值
            category_filter: 分类过滤
        
        Returns:
            [(entry, similarity_score), ...]
        """
        # 获取候选条目
        query_candidates = self.db.query(models.WorldbookEntry)
        if category_filter:
            query_candidates = query_candidates.filter(
                models.WorldbookEntry.category == category_filter
            )
        
        candidates = query_candidates.all()
        
        if not candidates:
            return []
        
        # 对于 TF-IDF，使用批量计算确保词汇表一致
        if self.embedding_config.provider == "tfidf":
            # 重新拟合所有条目 + 查询
            contents = [f"{e.title} {e.content}" for e in candidates]
            all_texts = contents + [query]
            
            # 批量计算所有向量
            all_vecs = self.engine.compute_embeddings(all_texts)
            candidate_vecs = all_vecs[:-1]  # 最后一个是查询
            query_vec = all_vecs[-1]
        else:
            # 其他方案：单独计算
            query_vec = self.engine.compute_single(query)
            candidate_vecs = []
            candidates_list = []
            
            for candidate in candidates:
                try:
                    vec = self.compute_entry_embedding(candidate, use_cache=True)
                    candidate_vecs.append(vec)
                except EmbeddingError as e:
                    print(f"[RAG] 计算向量失败 {candidate.entry_id}: {e}")
                    continue
        
        if not candidate_vecs:
            return []
        
        # 计算相似度
        similarities = top_k_similar(query_vec, candidate_vecs, top_k=len(candidate_vecs))
        
        # 过滤并排序
        results = []
        for idx, sim in similarities:
            if sim >= min_similarity:
                results.append((candidates[idx], sim))
        
        # 按相似度降序排列，取 top-k
        results.sort(key=lambda x: x[1], reverse=True)
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
        """混合搜索：语义 + 重要性 + 时效性
        
        Args:
            query: 查询文本
            top_k: 返回数量
            semantic_weight: 语义权重（默认 0.6）
            importance_weight: 重要性权重（默认 0.3）
            recency_weight: 时效性权重（默认 0.1）
            category_filter: 分类过滤
        
        Returns:
            [(entry, combined_score), ...]
        """
        # 1. 语义搜索
        semantic_results = self.semantic_search(
            query,
            top_k=top_k * 2,  # 先多取一些
            category_filter=category_filter,
        )
        
        if not semantic_results:
            return []
        
        # 2. 归一化各分数
        max_semantic = max(sim for _, sim in semantic_results) or 1.0
        now = datetime.utcnow()
        max_days = 30  # 最大时间范围
        
        # 3. 计算综合分数
        scored_entries = []
        for entry, semantic_sim in semantic_results:
            # 语义分数归一化
            norm_semantic = semantic_sim / max_semantic
            
            # 重要性分数归一化 (假设重要性范围 0-1)
            norm_importance = entry.importance or 0.5
            
            # 时效性分数
            if entry.updated_at:
                days_old = (now - entry.updated_at).days
                norm_recency = max(0, 1 - days_old / max_days)
            else:
                norm_recency = 0.5
            
            # 加权综合
            combined_score = (
                semantic_weight * norm_semantic +
                importance_weight * norm_importance +
                recency_weight * norm_recency
            )
            
            scored_entries.append((entry, combined_score))
        
        # 4. 按综合分数排序，取 top-k
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        return scored_entries[:top_k]
    
    # ============================================================
    # 剧情上下文检索（给 orchestrator 使用）
    # ============================================================
    
    def retrieve_for_story(
        self,
        recent_context: str,
        top_k: int = 8,
        use_hybrid: bool = True,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """为剧情生成检索相关的世界书内容
        
        Args:
            recent_context: 最近的剧情上下文
            top_k: 返回数量
            use_hybrid: 是否使用混合搜索
            category_filter: 分类过滤（可选）
        
        Returns:
            世界书条目列表（含分数）
        """
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
        
        # 转换为字典格式
        output = []
        for entry, score in results:
            output.append({
                "entry_id": entry.entry_id,
                "title": entry.title,
                "category": entry.category,
                "content": entry.content[:800],  # 限制长度
                "importance": entry.importance,
                "canonical": entry.canonical,
                "relevance_score": round(score, 4),
            })
        
        return output


# ============================================================
# 便捷函数
# ============================================================

def create_retriever(db: Session) -> RAGRetriever:
    """创建检索器（使用默认配置）"""
    # TODO: 从配置表读取 Embedding 配置
    # 默认使用 sentence-transformers，如失败则回退到 TF-IDF
    try:
        config = EmbeddingConfig(
            provider="sentence_transformers",
            model="paraphrase-multilingual-MiniLM-L12-v2",
        )
        retriever = RAGRetriever(db, config)
        # 触发引擎初始化，确保模型可用
        _ = retriever.engine
        return retriever
    except Exception as e:
        print(f"[RAG] sentence-transformers 初始化失败，回退 TF-IDF: {e}")
        fallback = EmbeddingConfig(provider="tfidf")
        return RAGRetriever(db, fallback)


def retrieve_worldbook_context(
    db: Session,
    query: str,
    top_k: int = 8,
) -> List[Dict[str, Any]]:
    """便捷函数：检索世界书上下文"""
    retriever = create_retriever(db)
    return retriever.retrieve_for_story(query, top_k=top_k)
