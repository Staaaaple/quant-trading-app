"""RAG 检索服务V2 — 投资顾问专用.

支持六大知识源的检索，按查询意图路由。
"""

import json
from typing import Any
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .embedding_service import EmbeddingService, get_embedding_service
from .vector_store import VectorStore, get_vector_store
from .llm_service import LLMService, get_llm_service


@dataclass
class RetrievalResult:
    """检索结果项."""

    id: str
    score: float
    text: str
    metadata: dict[str, Any]


@dataclass
class InvestmentContext:
    """投资顾问检索上下文."""

    stock_cases: list[RetrievalResult]
    valuation_cases: list[RetrievalResult]
    theories: list[RetrievalResult]
    basics: list[RetrievalResult]
    behavioral_cases: list[RetrievalResult]
    paper_chunks: list[RetrievalResult]


class InvestmentQueryType:
    """查询类型常量."""

    STOCK_ANALYSIS = "个股分析"
    STOCK_COMPARISON = "个股对比"
    SECTOR_ANALYSIS = "行业分析"
    PORTFOLIO_BUILD = "组合构建"
    PORTFOLIO_REVIEW = "组合诊断"
    REBALANCE_ADVICE = "调仓建议"
    VALUATION_ANALYSIS = "估值分析"
    BUY_TIMING = "买入时机"
    SELL_TIMING = "卖出时机"
    CONCEPT_EXPLAIN = "概念解释"
    THEORY_EXPLAIN = "理论解释"
    CASE_STUDY = "案例学习"
    UNKNOWN = "未知"


class InvestmentRetriever:
    """投资顾问检索器."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        llm_service: LLMService | None = None,
    ):
        self.embedding = embedding_service or get_embedding_service()
        self.llm = llm_service or get_llm_service()

        # 初始化各知识源的向量存储
        self.stock_store = get_vector_store("stock_case_index", dimension=self.embedding.dimension)
        self.theory_store = get_vector_store("allocation_theory_index", dimension=self.embedding.dimension)
        self.basic_store = get_vector_store("finance_basic_index", dimension=self.embedding.dimension)
        self.valuation_store = get_vector_store("valuation_case_index", dimension=self.embedding.dimension)
        self.behavioral_store = get_vector_store("behavioral_case_index", dimension=self.embedding.dimension)
        self.paper_store = get_vector_store("paper_chunk_index", dimension=self.embedding.dimension)

        # 加载已有索引
        self._load_indexes()

    def _load_indexes(self) -> None:
        """加载已构建的索引."""
        index_configs = [
            (self.stock_store, "stock_case_index"),
            (self.theory_store, "allocation_theory_index"),
            (self.basic_store, "finance_basic_index"),
            (self.valuation_store, "valuation_case_index"),
            (self.behavioral_store, "behavioral_case_index"),
            (self.paper_store, "paper_chunk_index"),
        ]

        for store, index_name in index_configs:
            if store.exists(index_name):
                try:
                    store.load(index_name)
                    print(f"[Retriever] 已加载索引: {index_name} ({store.count()} 条)")
                except Exception as e:
                    print(f"[Retriever] 加载索引失败 {index_name}: {e}")
            else:
                print(f"[Retriever] 索引不存在: {index_name}")

    def classify_query(self, query: str) -> str:
        """基于关键词分类查询意图.

        Args:
            query: 用户查询

        Returns:
            查询类型
        """
        query_lower = query.lower()

        # 估值分析（优先于个股分析）
        if any(kw in query for kw in ["估值", "贵吗", "便宜", "PE", "PB", "值多少钱", "合理价位"]):
            return InvestmentQueryType.VALUATION_ANALYSIS

        # 个股分析
        if any(kw in query for kw in ["分析", "怎么样", "能买吗", "值得投", "看好"]):
            if any(kw in query for kw in [
                "茅台", "宁德", "比亚迪", "中际", "长江电力", "神华",
                "迈瑞", "药明", "东方财富", "通威", "阳光", "三花",
                "拓普", "中芯", "立讯", "海康", "爱尔", "移动", "紫金"
            ]):
                return InvestmentQueryType.STOCK_ANALYSIS

        # 估值分析
        if any(kw in query for kw in ["贵吗", "便宜", "估值", "PE", "PB", "值多少钱"]):
            return InvestmentQueryType.VALUATION_ANALYSIS

        # 买卖时机
        if any(kw in query for kw in ["现在买", "买点", "入场", "建仓", "能买吗"]):
            return InvestmentQueryType.BUY_TIMING
        if any(kw in query for kw in ["该卖", "止盈", "止损", "减仓", "清仓"]):
            return InvestmentQueryType.SELL_TIMING

        # 组合构建
        if any(kw in query for kw in ["怎么配", "组合", "资产配置", "多少钱买", "仓位"]):
            return InvestmentQueryType.PORTFOLIO_BUILD

        # 概念解释
        if any(kw in query for kw in ["什么是", "什么意思", "怎么理解", "什么是"]):
            return InvestmentQueryType.CONCEPT_EXPLAIN

        # 理论解释
        if any(kw in query for kw in ["CAPM", "Barra", "因子", "模型", "理论"]):
            return InvestmentQueryType.THEORY_EXPLAIN

        # 案例学习
        if any(kw in query for kw in ["案例", "发生了什么", "历史", "回顾"]):
            return InvestmentQueryType.CASE_STUDY

        return InvestmentQueryType.UNKNOWN

    async def retrieve(
        self,
        query: str,
        query_type: str | None = None,
        top_k: int = 5,
    ) -> InvestmentContext:
        """检索投资知识.

        Args:
            query: 用户查询
            query_type: 查询类型（可选，自动分类）
            top_k: 每类返回数量

        Returns:
            InvestmentContext
        """
        if query_type is None:
            query_type = self.classify_query(query)

        # 生成查询向量
        query_embedding = await self.embedding.encode_async(query)

        # 根据查询类型路由到不同知识源
        if query_type == InvestmentQueryType.STOCK_ANALYSIS:
            return await self._retrieve_stock_analysis(query_embedding, top_k)
        elif query_type == InvestmentQueryType.VALUATION_ANALYSIS:
            return await self._retrieve_valuation(query_embedding, top_k)
        elif query_type == InvestmentQueryType.BUY_TIMING:
            return await self._retrieve_buy_timing(query_embedding, top_k)
        elif query_type == InvestmentQueryType.SELL_TIMING:
            return await self._retrieve_sell_timing(query_embedding, top_k)
        elif query_type == InvestmentQueryType.PORTFOLIO_BUILD:
            return await self._retrieve_portfolio(query_embedding, top_k)
        elif query_type == InvestmentQueryType.CONCEPT_EXPLAIN:
            return await self._retrieve_concept(query_embedding, top_k)
        elif query_type == InvestmentQueryType.THEORY_EXPLAIN:
            return await self._retrieve_theory(query_embedding, top_k)
        elif query_type == InvestmentQueryType.CASE_STUDY:
            return await self._retrieve_case_study(query_embedding, top_k)
        else:
            # 未知类型，检索所有
            return await self._retrieve_all(query_embedding, top_k)

    async def _retrieve_stock_analysis(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """个股分析检索：个股案例 + 估值常识 + 因子论文."""
        stock_cases = self._search_store(self.stock_store, query_embedding, top_k)
        valuation_cases = self._search_store(self.valuation_store, query_embedding, top_k // 2)
        paper_chunks = self._search_store(self.paper_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=stock_cases,
            valuation_cases=valuation_cases,
            theories=[],
            basics=[],
            behavioral_cases=[],
            paper_chunks=paper_chunks,
        )

    async def _retrieve_valuation(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """估值分析检索：估值案例 + 基础常识 + 论文."""
        valuation_cases = self._search_store(self.valuation_store, query_embedding, top_k)
        basics = self._search_store(self.basic_store, query_embedding, top_k // 2)
        paper_chunks = self._search_store(self.paper_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=[],
            valuation_cases=valuation_cases,
            theories=[],
            basics=basics,
            behavioral_cases=[],
            paper_chunks=paper_chunks,
        )

    async def _retrieve_buy_timing(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """买入时机检索：估值案例（低估买入）+ 个股案例 + 行为金融."""
        # 过滤低估买入案例
        valuation_cases = self._search_store(
            self.valuation_store, query_embedding, top_k,
            filters={"case_type": "低估买入"}
        )
        stock_cases = self._search_store(self.stock_store, query_embedding, top_k // 2)
        behavioral_cases = self._search_store(self.behavioral_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=stock_cases,
            valuation_cases=valuation_cases,
            theories=[],
            basics=[],
            behavioral_cases=behavioral_cases,
            paper_chunks=[],
        )

    async def _retrieve_sell_timing(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """卖出时机检索：估值案例（高估卖出）+ 行为金融."""
        valuation_cases = self._search_store(
            self.valuation_store, query_embedding, top_k,
            filters={"case_type": "高估卖出"}
        )
        behavioral_cases = self._search_store(self.behavioral_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=[],
            valuation_cases=valuation_cases,
            theories=[],
            basics=[],
            behavioral_cases=behavioral_cases,
            paper_chunks=[],
        )

    async def _retrieve_portfolio(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """组合构建检索：资产配置理论 + 行为金融."""
        theories = self._search_store(self.theory_store, query_embedding, top_k)
        behavioral_cases = self._search_store(self.behavioral_store, query_embedding, top_k // 2)
        basics = self._search_store(self.basic_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=[],
            valuation_cases=[],
            theories=theories,
            basics=basics,
            behavioral_cases=behavioral_cases,
            paper_chunks=[],
        )

    async def _retrieve_concept(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """概念解释检索：基础常识 + 论文."""
        basics = self._search_store(self.basic_store, query_embedding, top_k)
        paper_chunks = self._search_store(self.paper_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=[],
            valuation_cases=[],
            theories=[],
            basics=basics,
            behavioral_cases=[],
            paper_chunks=paper_chunks,
        )

    async def _retrieve_theory(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """理论解释检索：资产配置理论 + 论文."""
        theories = self._search_store(self.theory_store, query_embedding, top_k)
        paper_chunks = self._search_store(self.paper_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=[],
            valuation_cases=[],
            theories=theories,
            basics=[],
            behavioral_cases=[],
            paper_chunks=paper_chunks,
        )

    async def _retrieve_case_study(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """案例学习检索：所有案例."""
        stock_cases = self._search_store(self.stock_store, query_embedding, top_k)
        valuation_cases = self._search_store(self.valuation_store, query_embedding, top_k)
        behavioral_cases = self._search_store(self.behavioral_store, query_embedding, top_k // 2)

        return InvestmentContext(
            stock_cases=stock_cases,
            valuation_cases=valuation_cases,
            theories=[],
            basics=[],
            behavioral_cases=behavioral_cases,
            paper_chunks=[],
        )

    async def _retrieve_all(
        self, query_embedding: np.ndarray, top_k: int
    ) -> InvestmentContext:
        """检索所有知识源."""
        return InvestmentContext(
            stock_cases=self._search_store(self.stock_store, query_embedding, top_k),
            valuation_cases=self._search_store(self.valuation_store, query_embedding, top_k),
            theories=self._search_store(self.theory_store, query_embedding, top_k),
            basics=self._search_store(self.basic_store, query_embedding, top_k),
            behavioral_cases=self._search_store(self.behavioral_store, query_embedding, top_k),
            paper_chunks=self._search_store(self.paper_store, query_embedding, top_k),
        )

    def _search_store(
        self,
        store: VectorStore,
        query_embedding: np.ndarray,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """搜索向量存储."""
        results = store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_dict=filters,
        )

        return [
            RetrievalResult(
                id=r["id"],
                score=r["score"],
                text=r["text"],
                metadata=r["metadata"],
            )
            for r in results
        ]

    def get_stats(self) -> dict[str, Any]:
        """获取检索器统计信息."""
        return {
            "stock_cases": {"count": self.stock_store.count()},
            "allocation_theory": {"count": self.theory_store.count()},
            "finance_basics": {"count": self.basic_store.count()},
            "valuation_cases": {"count": self.valuation_store.count()},
            "behavioral_cases": {"count": self.behavioral_store.count()},
            "paper_chunks": {"count": self.paper_store.count()},
            "embedding": {
                "backend": self.embedding.backend,
                "dimension": self.embedding.dimension,
            },
            "llm": self.llm.get_status(),
        }


@lru_cache()
def get_retriever_v2() -> InvestmentRetriever:
    """获取全局投资顾问检索器实例（单例）."""
    return InvestmentRetriever()
