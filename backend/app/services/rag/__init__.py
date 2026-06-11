"""RAG (Retrieval-Augmented Generation) 模块.

为 QuantEvo 提供向量检索增强能力：
- 策略模板语义检索
- 论文知识库语义检索
- 本地 Qwen3-14B-MLX-4bit LLM 生成
- 组合设计 RAG 增强
- 组合质量门控 (PortfolioQualityGate)

架构:
    EmbeddingService -> VectorStore -> Retriever -> LLMService
    PortfolioQualityGate -> AdjustmentEngine
"""

from .embedding_service import EmbeddingService, get_embedding_service
from .vector_store import VectorStore, get_vector_store
from .retriever import RAGRetriever, get_retriever
from .retriever_v2 import InvestmentRetriever, get_retriever_v2
from .llm_service import LLMService, get_llm_service
from .index_builder import IndexBuilder
from .portfolio_quality_gate import PortfolioQualityGate, RAGGateResult, ReviewStep
from .adjustment_engine import AdjustmentEngine, apply_adjustments

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "VectorStore",
    "get_vector_store",
    "RAGRetriever",
    "get_retriever",
    "InvestmentRetriever",
    "get_retriever_v2",
    "LLMService",
    "get_llm_service",
    "IndexBuilder",
    "PortfolioQualityGate",
    "RAGGateResult",
    "ReviewStep",
    "AdjustmentEngine",
    "apply_adjustments",
]
