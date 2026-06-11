"""RAG 投资顾问测试套件."""

import pytest
from sqlalchemy.orm import Session

from app.models.rag_knowledge import (
    StockAnalysisCase,
    AllocationTheory,
    FinanceBasic,
    ValuationTimingCase,
    BehavioralCase,
)
from app.services.rag.data_loader import load_all_knowledge
from app.services.rag.index_builder_v2 import IndexBuilderV2
from app.services.rag.retriever_v2 import InvestmentRetriever, InvestmentQueryType
from app.services.rag.investment_advisor import InvestmentAdvisor


class TestDataLoader:
    """测试数据加载."""

    def test_load_stock_cases(self, db: Session):
        """测试加载个股案例."""
        from app.services.rag.data_loader import load_stock_cases
        from pathlib import Path

        data_dir = Path(__file__).parent.parent / "data" / "knowledge"
        count = load_stock_cases(db, data_dir)
        assert count >= 0

        # 验证数据
        cases = db.query(StockAnalysisCase).all()
        assert len(cases) > 0

    def test_load_allocation_theory(self, db: Session):
        """测试加载资产配置理论."""
        from app.services.rag.data_loader import load_allocation_theory
        from pathlib import Path

        data_dir = Path(__file__).parent.parent / "data" / "knowledge"
        count = load_allocation_theory(db, data_dir)
        assert count >= 0

        theories = db.query(AllocationTheory).all()
        assert len(theories) > 0

    def test_load_finance_basics(self, db: Session):
        """测试加载基础常识."""
        from app.services.rag.data_loader import load_finance_basics
        from pathlib import Path

        data_dir = Path(__file__).parent.parent / "data" / "knowledge"
        count = load_finance_basics(db, data_dir)
        assert count >= 0

        basics = db.query(FinanceBasic).all()
        assert len(basics) > 0


class TestQueryClassifier:
    """测试查询分类器."""

    @pytest.fixture
    def retriever(self):
        return InvestmentRetriever()

    def test_classify_stock_analysis(self, retriever):
        """测试个股分析分类."""
        queries = [
            "分析宁德时代",
            "茅台怎么样",
            "中际旭创能买吗",
        ]
        for q in queries:
            result = retriever.classify_query(q)
            assert result == InvestmentQueryType.STOCK_ANALYSIS

    def test_classify_valuation(self, retriever):
        """测试估值分析分类."""
        queries = [
            "茅台贵吗",
            "这个股票估值怎么样",
            "PE多少算合理",
        ]
        for q in queries:
            result = retriever.classify_query(q)
            assert result == InvestmentQueryType.VALUATION_ANALYSIS

    def test_classify_portfolio(self, retriever):
        """测试组合构建分类."""
        queries = [
            "50万怎么配",
            "稳健型组合",
            "资产配置建议",
        ]
        for q in queries:
            result = retriever.classify_query(q)
            assert result == InvestmentQueryType.PORTFOLIO_BUILD

    def test_classify_concept(self, retriever):
        """测试概念解释分类."""
        queries = [
            "什么是PE",
            "ROE什么意思",
            "怎么理解夏普比率",
        ]
        for q in queries:
            result = retriever.classify_query(q)
            assert result == InvestmentQueryType.CONCEPT_EXPLAIN


class TestIndexBuilder:
    """测试索引构建."""

    def test_build_stock_case_index(self, db: Session):
        """测试构建个股案例索引."""
        builder = IndexBuilderV2()

        # 先加载数据
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / "data" / "knowledge"
        load_all_knowledge(db, data_dir)

        # 构建索引
        result = builder.build_stock_case_index(db)
        assert result["status"] in ["built", "loaded_existing", "no_data"]

    def test_build_all_indexes(self, db: Session):
        """测试构建所有索引."""
        builder = IndexBuilderV2()

        # 先加载数据
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / "data" / "knowledge"
        load_all_knowledge(db, data_dir)

        # 构建所有索引
        results = builder.build_all(db)

        for name, result in results.items():
            assert "status" in result
            assert "count" in result


class TestRetriever:
    """测试检索服务."""

    @pytest.fixture
    def retriever(self):
        return InvestmentRetriever()

    @pytest.mark.asyncio
    async def test_retrieve_stock_analysis(self, retriever):
        """测试个股分析检索."""
        query = "分析宁德时代"
        context = await retriever.retrieve(query, InvestmentQueryType.STOCK_ANALYSIS)

        # 应该返回个股案例
        assert len(context.stock_cases) > 0 or len(context.paper_chunks) > 0

    @pytest.mark.asyncio
    async def test_retrieve_valuation(self, retriever):
        """测试估值分析检索."""
        query = "茅台估值"
        context = await retriever.retrieve(query, InvestmentQueryType.VALUATION_ANALYSIS)

        # 应该返回估值案例或基础知识
        assert (
            len(context.valuation_cases) > 0
            or len(context.basics) > 0
            or len(context.paper_chunks) > 0
        )

    @pytest.mark.asyncio
    async def test_retrieve_concept(self, retriever):
        """测试概念解释检索."""
        query = "什么是PE"
        context = await retriever.retrieve(query, InvestmentQueryType.CONCEPT_EXPLAIN)

        # 应该返回基础知识
        assert len(context.basics) > 0 or len(context.paper_chunks) > 0


class TestInvestmentAdvisor:
    """测试投资顾问服务."""

    @pytest.mark.asyncio
    async def test_answer_stock_analysis(self):
        """测试个股分析回答."""
        advisor = InvestmentAdvisor()

        query = "分析宁德时代"
        response = await advisor.answer(query)

        assert response.answer is not None
        assert len(response.answer) > 0
        assert response.query_type == InvestmentQueryType.STOCK_ANALYSIS
        assert response.model is not None

    @pytest.mark.asyncio
    async def test_answer_concept(self):
        """测试概念解释回答."""
        advisor = InvestmentAdvisor()

        query = "什么是市盈率"
        response = await advisor.answer(query)

        assert response.answer is not None
        assert len(response.answer) > 0
        assert response.query_type == InvestmentQueryType.CONCEPT_EXPLAIN

    @pytest.mark.asyncio
    async def test_answer_with_profile(self):
        """测试带画像的回答."""
        advisor = InvestmentAdvisor()

        query = "50万怎么配置"
        profile = {
            "risk_profile": "稳健型",
            "capital": 500000,
        }
        response = await advisor.answer(query, profile)

        assert response.answer is not None
        assert len(response.answer) > 0


class TestIntegration:
    """集成测试."""

    def test_full_pipeline(self, db: Session):
        """测试完整流程：加载数据→构建索引→检索→生成."""
        from pathlib import Path

        # 1. 加载数据
        data_dir = Path(__file__).parent.parent / "data" / "knowledge"
        load_results = load_all_knowledge(db, data_dir)

        for name, count in load_results.items():
            assert count >= 0

        # 2. 构建索引
        builder = IndexBuilderV2()
        index_results = builder.build_all(db)

        for name, result in index_results.items():
            assert result["status"] in ["built", "loaded_existing", "no_data"]

        # 3. 检查统计
        stats = builder.get_stats()
        assert len(stats) == 6

    @pytest.mark.asyncio
    async def test_end_to_end(self, db: Session):
        """测试端到端流程."""
        from pathlib import Path

        # 准备数据
        data_dir = Path(__file__).parent.parent / "data" / "knowledge"
        load_all_knowledge(db, data_dir)

        # 构建索引
        builder = IndexBuilderV2()
        builder.build_all(db)

        # 查询
        from app.services.rag.investment_advisor import get_investment_advice

        response = await get_investment_advice("什么是市盈率")

        assert response.answer is not None
        assert len(response.answer) > 0
        assert len(response.sources) > 0
