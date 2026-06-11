"""RAG 检索服务 — 统一检索接口.

提供:
- 策略模板语义检索
- 论文知识库语义检索
- 组合设计上下文检索
- RAG 生成（检索 + LLM）
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
class PortfolioContext:
    """组合设计检索上下文."""

    saa_papers: list[RetrievalResult]
    taa_papers: list[RetrievalResult]
    strategy_candidates: list[RetrievalResult]
    risk_papers: list[RetrievalResult]
    combined_rationale: str = ""


class RAGRetriever:
    """RAG 检索器."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        strategy_store: VectorStore | None = None,
        paper_store: VectorStore | None = None,
        llm_service: LLMService | None = None,
    ):
        self.embedding = embedding_service or get_embedding_service()

        # 策略模板向量存储
        self.strategy_store = strategy_store or get_vector_store(
            name="strategy_templates",
            dimension=self.embedding.dimension,
        )

        # 论文向量存储
        self.paper_store = paper_store or get_vector_store(
            name="paper_knowledges",
            dimension=self.embedding.dimension,
        )

        self.llm = llm_service or get_llm_service()

    # ═══════════════════════════════════════════════════════════════
    # 基础检索
    # ═══════════════════════════════════════════════════════════════

    async def retrieve_strategies(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """检索策略模板.

        Args:
            query: 自然语言查询
            top_k: 返回数量
            filters: 元数据过滤 {key: value}

        Returns:
            检索结果列表
        """
        embedding = await self.embedding.encode_async(query)

        results = self.strategy_store.search(
            query_embedding=embedding,
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

    async def retrieve_papers(
        self,
        query: str,
        top_k: int = 3,
        family: str | None = None,
    ) -> list[RetrievalResult]:
        """检索论文.

        Args:
            query: 自然语言查询
            top_k: 返回数量
            family: 按策略家族过滤

        Returns:
            检索结果列表
        """
        embedding = await self.embedding.encode_async(query)

        filters = None
        if family:
            filters = {"family": family}

        results = self.paper_store.search(
            query_embedding=embedding,
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

    # ═══════════════════════════════════════════════════════════════
    # 组合设计检索
    # ═══════════════════════════════════════════════════════════════

    async def retrieve_for_portfolio(
        self,
        profile_vector: dict[str, float],
        market_signal: dict[str, Any],
        target_risk: str,
    ) -> PortfolioContext:
        """为组合设计检索完整上下文.

        Args:
            profile_vector: 用户画像15维向量
            market_signal: 市场五层信号
            target_risk: 目标风险等级

        Returns:
            PortfolioContext
        """
        market_cycle = market_signal.get("cycle", "recovery")
        macro_score = market_signal.get("macro_score", 0.5)

        # 1. 检索 SAA 相关论文
        saa_query = f"{target_risk}投资者在{market_cycle}的资产配置策略"
        saa_papers = await self.retrieve_papers(saa_query, top_k=3)

        # 2. 检索 TAA 相关论文
        top_sectors = market_signal.get("top_sectors", [])
        sector_names = [s.get("name", "") for s in top_sectors[:2]]
        taa_query = f"{'、'.join(sector_names)}行业在{market_cycle}的战术配置"
        taa_papers = await self.retrieve_papers(taa_query, top_k=2)

        # 3. 检索策略候选
        strategy_query = self._build_strategy_query(
            profile_vector, market_signal, target_risk
        )
        strategy_candidates = await self.retrieve_strategies(
            strategy_query,
            top_k=10,
            filters={"risk_level": target_risk} if target_risk else None,
        )

        # 4. 检索风控相关论文
        risk_query = f"{target_risk}风险等级的止损和回撤控制策略"
        risk_papers = await self.retrieve_papers(risk_query, top_k=2)

        return PortfolioContext(
            saa_papers=saa_papers,
            taa_papers=taa_papers,
            strategy_candidates=strategy_candidates,
            risk_papers=risk_papers,
        )

    def _build_strategy_query(
        self,
        profile_vector: dict[str, float],
        market_signal: dict[str, Any],
        target_risk: str,
    ) -> str:
        """构建策略检索查询."""
        market_cycle = market_signal.get("cycle", "复苏")

        # 从画像提取关键特征
        risk_tolerance = profile_vector.get("risk_tolerance", 0.5)
        loss_aversion = profile_vector.get("loss_aversion", 0.5)
        time_horizon = profile_vector.get("time_horizon", 0.5)

        # 构建查询
        parts = [f"{market_cycle}市场环境"]

        if risk_tolerance > 0.6:
            parts.append("积极型")
        elif risk_tolerance < 0.4:
            parts.append("保守型")
        else:
            parts.append("稳健型")

        if loss_aversion > 0.7:
            parts.append("低波动")
        elif loss_aversion < 0.3:
            parts.append("高收益")

        if time_horizon > 0.6:
            parts.append("长期投资")
        else:
            parts.append("短期交易")

        parts.append("策略")

        return " ".join(parts)

    # ═══════════════════════════════════════════════════════════════
    # RAG 生成
    # ═══════════════════════════════════════════════════════════════

    async def generate_with_context(
        self,
        query: str,
        context_type: str = "strategy",
        top_k: int = 3,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """检索增强生成 (RAG).

        Args:
            query: 用户查询
            context_type: "strategy" | "paper" | "portfolio"
            top_k: 检索数量
            system_prompt: 系统提示

        Returns:
            {"answer": str, "sources": list[dict], "model": str}
        """
        # 1. 检索相关文档
        if context_type == "strategy":
            results = await self.retrieve_strategies(query, top_k=top_k)
        elif context_type == "paper":
            results = await self.retrieve_papers(query, top_k=top_k)
        else:
            # portfolio: 混合检索
            strategy_results = await self.retrieve_strategies(query, top_k=top_k)
            paper_results = await self.retrieve_papers(query, top_k=top_k)
            results = strategy_results + paper_results

        # 2. 构建上下文
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(f"[{i}] {r.text}")

        context = "\n\n".join(context_parts)

        # 3. 构建提示
        if system_prompt is None:
            system_prompt = """你是一位专业的量化投资顾问。基于提供的参考资料，回答用户的问题。
请确保回答准确、专业，并引用相关资料的编号。如果参考资料不足以回答问题，请明确说明。"""

        prompt = f"""参考资料:
{context}

用户问题: {query}

请基于以上参考资料回答问题。"""

        # 4. 调用 LLM
        response = await self.llm.generate_async(
            prompt=prompt,
            system_prompt=system_prompt,
        )

        # 5. 整理来源
        sources = [
            {
                "id": r.id,
                "score": r.score,
                "metadata": r.metadata,
            }
            for r in results
        ]

        return {
            "answer": response.text,
            "sources": sources,
            "model": response.model,
            "usage": response.usage,
        }

    async def generate_portfolio_rationale(
        self,
        portfolio: dict[str, Any],
        profile_vector: dict[str, float],
        market_signal: dict[str, Any],
    ) -> dict[str, Any]:
        """生成组合设计的详细理由 (RAG增强).

        Args:
            portfolio: 组合配置
            profile_vector: 用户画像
            market_signal: 市场信号

        Returns:
            {"rationale": str, "sources": list[dict]}
        """
        # 检索上下文
        context = await self.retrieve_for_portfolio(
            profile_vector=profile_vector,
            market_signal=market_signal,
            target_risk=portfolio.get("risk_level", "稳健"),
        )

        # 构建提示
        saa_text = "\n".join([f"- {p.text[:200]}" for p in context.saa_papers])
        strategy_text = "\n".join([f"- {s.text[:150]}" for s in context.strategy_candidates[:3]])

        prompt = f"""基于以下检索到的专业资料，为投资组合生成详细的设计理由：

用户画像: 风险承受度{profile_vector.get('risk_tolerance', 0.5):.0%}, 损失厌恶{profile_vector.get('loss_aversion', 0.5):.0%}
市场环境: {market_signal.get('cycle', '复苏')}期

资产配置:
- 股票: {portfolio.get('saa', {}).get('weights', {}).get('stock', 0):.0%}
- 债券: {portfolio.get('saa', {}).get('weights', {}).get('bond', 0):.0%}
- 商品: {portfolio.get('saa', {}).get('weights', {}).get('commodity', 0):.0%}
- 现金: {portfolio.get('saa', {}).get('weights', {}).get('cash', 0):.0%}

策略绑定: {', '.join([b.get('strategy_name', '') for b in portfolio.get('bindings', [])])}

参考资料:
资产配置研究:
{saa_text}

策略研究:
{strategy_text}

请生成一段专业的组合设计理由，说明：
1. 为什么这样配置资产类别
2. 为什么选择这些策略
3. 当前市场环境下的优势
4. 需要注意的风险
"""

        response = await self.llm.generate_async(
            prompt=prompt,
            system_prompt="你是一位资深量化投资顾问，用中文撰写专业的投资分析报告。",
        )

        all_sources = (
            context.saa_papers
            + context.taa_papers
            + context.strategy_candidates[:3]
            + context.risk_papers
        )

        return {
            "rationale": response.text,
            "sources": [
                {"id": s.id, "score": s.score, "metadata": s.metadata}
                for s in all_sources
            ],
            "model": response.model,
        }

    # ═══════════════════════════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════════════════════════

    def get_stats(self) -> dict[str, Any]:
        """获取检索器统计信息."""
        return {
            "strategy_store": {
                "count": self.strategy_store.count(),
            },
            "paper_store": {
                "count": self.paper_store.count(),
            },
            "embedding": {
                "backend": self.embedding.backend,
                "dimension": self.embedding.dimension,
            },
            "llm": self.llm.get_status(),
        }


@lru_cache()
def get_retriever() -> RAGRetriever:
    """获取全局 RAG 检索器实例（单例）."""
    return RAGRetriever()
