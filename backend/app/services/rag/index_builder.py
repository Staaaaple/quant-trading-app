"""索引构建器 — 从数据库构建向量索引.

支持:
- 策略模板索引 (strategy_templates)
- 论文知识库索引 (paper_knowledges)
- 增量更新
- 全量重建
"""

import json
from typing import Any
from sqlalchemy.orm import Session

from app.models.strategy_template import StrategyTemplate
from app.models.paper_knowledge import PaperKnowledge
from .embedding_service import EmbeddingService
from .vector_store import VectorStore, get_vector_store


class IndexBuilder:
    """向量索引构建器."""

    STRATEGY_INDEX_NAME = "strategy_templates"
    PAPER_INDEX_NAME = "paper_knowledges"

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.embedding = embedding_service or EmbeddingService()
        # 使用命名存储实例，与 retriever 中使用的名称一致
        self.store = vector_store or get_vector_store(
            name="strategy_templates",
            dimension=self.embedding.dimension,
        )

    # ═══════════════════════════════════════════════════════════════
    # 策略模板索引
    # ═══════════════════════════════════════════════════════════════

    def build_strategy_index(self, db: Session, force_rebuild: bool = False) -> dict[str, Any]:
        """构建策略模板向量索引.

        Args:
            db: 数据库会话
            force_rebuild: 是否强制重建

        Returns:
            {"index_name": str, "count": int, "status": str}
        """
        if not force_rebuild and self.store.exists(self.STRATEGY_INDEX_NAME):
            # 加载已有索引
            self.store.load(self.STRATEGY_INDEX_NAME)
            return {
                "index_name": self.STRATEGY_INDEX_NAME,
                "count": self.store.count(),
                "status": "loaded_existing",
            }

        # 从数据库读取所有策略模板
        templates = db.query(StrategyTemplate).filter(
            StrategyTemplate.is_active == True
        ).all()

        if not templates:
            return {
                "index_name": self.STRATEGY_INDEX_NAME,
                "count": 0,
                "status": "no_data",
            }

        # 生成文档和元数据
        ids = []
        texts = []
        metadatas = []

        for tmpl in templates:
            doc = self._template_to_doc(tmpl)
            ids.append(tmpl.template_id)
            texts.append(doc)
            metadatas.append({
                "name": tmpl.name,
                "family": tmpl.family,
                "risk_level": tmpl.risk_level,
                "suitable_cycles": tmpl.suitable_cycles or [],
                "asset_classes": tmpl.asset_classes or [],
                "health_score": tmpl.health_score,
                "lifespan_months": tmpl.lifespan_months,
            })

        # 生成 Embedding
        embeddings = self.embedding.encode(texts)

        # 添加到向量存储
        self.store.add_items(ids=ids, embeddings=embeddings, metadatas=metadatas, texts=texts)

        # 保存索引
        self.store.save(self.STRATEGY_INDEX_NAME)

        return {
            "index_name": self.STRATEGY_INDEX_NAME,
            "count": self.store.count(),
            "status": "built",
        }

    def _template_to_doc(self, tmpl: StrategyTemplate) -> str:
        """将策略模板转换为文档文本."""
        parts = [
            f"策略名称: {tmpl.name}",
            f"策略家族: {tmpl.family}",
            f"风险等级: {tmpl.risk_level}",
            f"适用周期: {', '.join(tmpl.suitable_cycles or [])}",
            f"资产类别: {', '.join(tmpl.asset_classes or [])}",
        ]

        if tmpl.description:
            parts.append(f"策略描述: {tmpl.description}")

        if tmpl.param_space:
            parts.append(f"参数空间: {json.dumps(tmpl.param_space, ensure_ascii=False)}")

        if tmpl.health_score:
            parts.append(f"健康度评分: {tmpl.health_score}")

        if tmpl.lifespan_months:
            parts.append(f"预期寿命: {tmpl.lifespan_months}个月")

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════
    # 论文知识库索引
    # ═══════════════════════════════════════════════════════════════

    def build_paper_index(self, db: Session, force_rebuild: bool = False) -> dict[str, Any]:
        """构建论文知识库向量索引.

        Args:
            db: 数据库会话
            force_rebuild: 是否强制重建

        Returns:
            {"index_name": str, "count": int, "status": str}
        """
        # 论文使用独立的存储实例
        from .vector_store import get_vector_store
        paper_store = get_vector_store(
            name="paper_knowledges",
            dimension=self.embedding.dimension,
        )

        if not force_rebuild and paper_store.exists(self.PAPER_INDEX_NAME):
            paper_store.load(self.PAPER_INDEX_NAME)
            return {
                "index_name": self.PAPER_INDEX_NAME,
                "count": paper_store.count(),
                "status": "loaded_existing",
            }

        papers = db.query(PaperKnowledge).all()

        if not papers:
            return {
                "index_name": self.PAPER_INDEX_NAME,
                "count": 0,
                "status": "no_data",
            }

        ids = []
        texts = []
        metadatas = []

        for paper in papers:
            doc = self._paper_to_doc(paper)
            paper_id = paper.arxiv_id or f"paper_{paper.id}"
            ids.append(paper_id)
            texts.append(doc)
            metadatas.append({
                "title": paper.title,
                "authors": paper.authors,
                "family": paper.family,
                "publish_date": paper.publish_date,
                "suitable_cycles": paper.suitable_cycles or [],
                "suitable_markets": paper.suitable_markets or [],
                "backtest_sharpe": paper.backtest_sharpe,
            })

        embeddings = self.embedding.encode(texts)
        paper_store.add_items(ids=ids, embeddings=embeddings, metadatas=metadatas, texts=texts)
        paper_store.save(self.PAPER_INDEX_NAME)

        return {
            "index_name": self.PAPER_INDEX_NAME,
            "count": paper_store.count(),
            "status": "built",
        }

    def _paper_to_doc(self, paper: PaperKnowledge) -> str:
        """将论文转换为文档文本."""
        parts = [
            f"论文标题: {paper.title}",
            f"作者: {paper.authors or '未知'}",
            f"发表时间: {paper.publish_date or '未知'}",
            f"所属家族: {paper.family}",
        ]

        if paper.core_conclusion:
            parts.append(f"核心结论: {paper.core_conclusion}")

        if paper.key_findings:
            findings = paper.key_findings
            if isinstance(findings, list):
                parts.append(f"关键发现: {'; '.join(findings)}")
            else:
                parts.append(f"关键发现: {findings}")

        if paper.suitable_cycles:
            parts.append(f"适用周期: {', '.join(paper.suitable_cycles)}")

        if paper.suitable_markets:
            markets = paper.suitable_markets
            if isinstance(markets, list):
                parts.append(f"适用市场: {', '.join(markets)}")
            else:
                parts.append(f"适用市场: {markets}")

        if paper.backtest_sharpe is not None:
            parts.append(f"回测夏普比率: {paper.backtest_sharpe}")

        if paper.backtest_max_drawdown is not None:
            parts.append(f"回测最大回撤: {paper.backtest_max_drawdown}")

        if paper.backtest_win_rate is not None:
            parts.append(f"回测胜率: {paper.backtest_win_rate}")

        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════════
    # 批量构建
    # ═══════════════════════════════════════════════════════════════

    def build_all(self, db: Session, force_rebuild: bool = False) -> dict[str, Any]:
        """构建所有索引.

        Returns:
            {"strategy": {...}, "paper": {...}}
        """
        strategy_result = self.build_strategy_index(db, force_rebuild)
        paper_result = self.build_paper_index(db, force_rebuild)

        return {
            "strategy": strategy_result,
            "paper": paper_result,
        }

    # ═══════════════════════════════════════════════════════════════
    # 增量更新
    # ═══════════════════════════════════════════════════════════════

    def add_strategy(self, tmpl: StrategyTemplate) -> dict[str, Any]:
        """添加单个策略到索引."""
        doc = self._template_to_doc(tmpl)
        embedding = self.embedding.encode([doc])

        self.store.add_items(
            ids=[tmpl.template_id],
            embeddings=embedding,
            metadatas=[{
                "name": tmpl.name,
                "family": tmpl.family,
                "risk_level": tmpl.risk_level,
                "suitable_cycles": tmpl.suitable_cycles or [],
                "asset_classes": tmpl.asset_classes or [],
                "health_score": tmpl.health_score,
                "lifespan_months": tmpl.lifespan_months,
            }],
            texts=[doc],
        )

        self.store.save(self.STRATEGY_INDEX_NAME)

        return {"id": tmpl.template_id, "status": "added"}

    def add_paper(self, paper: PaperKnowledge) -> dict[str, Any]:
        """添加单篇论文到索引."""
        doc = self._paper_to_doc(paper)
        embedding = self.embedding.encode([doc])
        paper_id = paper.arxiv_id or f"paper_{paper.id}"

        from .vector_store import get_vector_store
        paper_store = get_vector_store(
            name="paper_knowledges",
            dimension=self.embedding.dimension,
        )

        paper_store.add_items(
            ids=[paper_id],
            embeddings=embedding,
            metadatas=[{
                "title": paper.title,
                "authors": paper.authors,
                "family": paper.family,
                "publish_date": paper.publish_date,
                "suitable_cycles": paper.suitable_cycles or [],
                "suitable_markets": paper.suitable_markets or [],
            }],
            texts=[doc],
        )

        paper_store.save(self.PAPER_INDEX_NAME)

        return {"id": paper_id, "status": "added"}
