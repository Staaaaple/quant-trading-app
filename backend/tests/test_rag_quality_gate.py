"""RAG质量门控单元测试."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.rag.portfolio_quality_gate import (
    PortfolioQualityGate,
    RAGGateResult,
    ReviewStep,
)
from app.services.rag.adjustment_engine import AdjustmentEngine, apply_adjustments


class TestRAGGateResult:
    """测试RAGGateResult数据类."""

    def test_basic_creation(self):
        """测试基本创建."""
        result = RAGGateResult(
            step="saa",
            passed=True,
            score=0.9,
            issues=[],
            adjustments=[],
        )
        assert result.step == "saa"
        assert result.passed is True
        assert result.score == 0.9

    def test_to_dict(self):
        """测试转为字典."""
        result = RAGGateResult(
            step="saa",
            passed=False,
            score=0.4,
            issues=["股票权重过高"],
            adjustments=[{"type": "weight_cap", "asset": "stock", "cap": 0.7}],
            theory_cited=["theory_markowitz"],
            cases_cited=["case_001"],
            retry_count=1,
        )
        d = result.to_dict()
        assert d["step"] == "saa"
        assert d["passed"] is False
        assert len(d["issues"]) == 1
        assert len(d["adjustments"]) == 1


class TestAdjustmentEngine:
    """测试调节引擎."""

    def test_apply_saa_weight_cap(self):
        """测试SAA权重上限截断."""
        saa = {"weights": {"stock": 0.8, "bond": 0.15, "commodity": 0.03, "cash": 0.02}}
        adjustments = [{"type": "weight_cap", "asset": "stock", "cap": 0.7}]

        result, _ = apply_adjustments("saa", saa, adjustments)
        weights = result["weights"]

        assert weights["stock"] == pytest.approx(0.7, abs=0.01)
        assert weights["bond"] > 0.15  # 超额分配给债券
        assert result["rag_adjusted"] is True

    def test_apply_saa_add_hedge(self):
        """测试增配避险资产."""
        saa = {"weights": {"stock": 0.6, "bond": 0.3, "commodity": 0.05, "cash": 0.05}}
        adjustments = [{"type": "add_hedge", "hedge_asset": "commodity", "target": 0.1}]

        result, _ = apply_adjustments("saa", saa, adjustments)
        weights = result["weights"]

        assert weights["commodity"] == pytest.approx(0.1, abs=0.01)
        assert weights["stock"] < 0.6  # 从股票扣除

    def test_apply_binding_param_change(self):
        """测试绑定参数调整."""
        bindings = [
            {
                "symbol": "000001",
                "strategy_params": {"window": 5, "threshold": 0.02},
            }
        ]
        adjustments = [
            {
                "type": "param_change",
                "symbol": "000001",
                "param_changes": {"window": 20},
            }
        ]

        result, needs_rebacktest = apply_adjustments("binding", bindings, adjustments)

        assert result[0]["strategy_params"]["window"] == 20
        assert result[0]["rag_adjusted"] is True
        assert "000001" in needs_rebacktest

    def test_apply_binding_exclude(self):
        """测试排除标的."""
        bindings = [
            {"symbol": "000001", "name": "平安银行"},
            {"symbol": "000002", "name": "万科A"},
        ]
        adjustments = [{"type": "exclude", "symbol": "000001"}]

        result, _ = apply_adjustments("binding", bindings, adjustments)

        assert len(result) == 1
        assert result[0]["symbol"] == "000002"

    def test_apply_risk_stop_loss(self):
        """测试风控止损调整."""
        risk_config = {"stop_loss": 0.15, "max_position": 0.2}
        adjustments = [{"type": "stop_loss", "value": 0.05}]

        result, _ = apply_adjustments("risk_config", risk_config, adjustments)

        assert result["stop_loss"] == 0.05
        assert result["rag_adjusted"] is True


class TestPortfolioQualityGate:
    """测试PortfolioQualityGate."""

    @pytest.fixture
    def gate(self):
        """创建质量门控实例（使用mock）."""
        mock_retriever = Mock()
        mock_llm = Mock()
        return PortfolioQualityGate(
            retriever=mock_retriever,
            llm_service=mock_llm,
        )

    @pytest.fixture
    def sample_profile(self):
        """样本用户画像."""
        return {
            "risk_tolerance": 0.3,  # 保守型
            "loss_aversion": 0.8,   # 高损失厌恶
        }

    @pytest.fixture
    def sample_market(self):
        """样本市场信号."""
        return {
            "macro": {"cycle_phase": "衰退", "score": 30},
            "geopolitical": {"overall_risk": 80},
            "market_internal": {"vix": 35, "equity_bond_spread": 1.5},
            "industry_scores": {"科技": 40, "消费": 50},
            "social_trends": ["消费降级"],
        }

    @pytest.fixture
    def sample_saa(self):
        """样本SAA结果."""
        return {"weights": {"stock": 0.5, "bond": 0.4, "commodity": 0.05, "cash": 0.05}}

    def test_build_saa_review_query(self, gate, sample_saa, sample_profile, sample_market):
        """测试SAA审核查询构建."""
        query = gate._build_saa_review_query(sample_saa, sample_profile, sample_market)

        assert "稳健" in query  # risk_tolerance=0.3 -> 稳健型
        assert "股票: 50%" in query
        assert "衰退" in query
        assert "VIX" in query
        assert "JSON" in query

    def test_build_binding_review_query(self, gate):
        """测试绑定审核查询构建."""
        binding = {
            "symbol": "300750",
            "name": "宁德时代",
            "strategy_name": "EMA动量",
            "strategy_family": "动量策略",
            "strategy_params": {"window": 5},
        }
        backtest = {
            "return": 5.0,
            "buy_hold_return": 15.0,
            "sharpe": 0.3,
            "max_drawdown": 0.25,
            "win_rate": 0.4,
            "trade_count": 30,
            "period": "2023-01~2024-12",
            "market_cycle": "复苏",
            "volatility": 0.2,
        }

        query = gate._build_binding_review_query(binding, backtest)

        assert "300750" in query
        assert "跑输" in query
        assert "JSON" in query
        assert "均线周期" in query

    def test_parse_review_passed(self, gate):
        """测试解析通过的结果."""
        review_text = """
        审核结论: 通过
        该配置合理。
        {"passed": true, "issues": [], "adjustments": []}
        """
        result = gate._parse_review("saa", review_text)

        assert result.passed is True
        assert result.score > 0.5
        assert result.step == "saa"

    def test_parse_review_failed(self, gate):
        """测试解析不通过的结果."""
        review_text = """
        审核结论: 不通过
        问题：股票权重过高
        {"passed": false, "issues": ["股票权重过高"], "adjustments": [{"type": "weight_cap", "asset": "stock", "cap": 0.3}]}
        """
        result = gate._parse_review("saa", review_text)

        assert result.passed is False
        assert result.score < 0.5
        assert len(result.issues) > 0
        assert len(result.adjustments) > 0

    def test_get_risk_level_name(self, gate):
        """测试风险等级名称."""
        assert gate._get_risk_level_name(0.2) == "保守"
        assert gate._get_risk_level_name(0.4) == "稳健"
        assert gate._get_risk_level_name(0.7) == "积极"
        assert gate._get_risk_level_name(0.9) == "激进"


class TestIntegration:
    """集成测试."""

    def test_full_adjustment_flow(self):
        """测试完整调节流程."""
        # 1. SAA调节
        saa = {"weights": {"stock": 0.8, "bond": 0.15, "commodity": 0.03, "cash": 0.02}}
        saa_adj = [{"type": "weight_cap", "asset": "stock", "cap": 0.7}]
        saa_result, _ = apply_adjustments("saa", saa, saa_adj)
        assert saa_result["weights"]["stock"] <= 0.7

        # 2. 风控调节
        risk = {"stop_loss": 0.15, "max_position": 0.3}
        risk_adj = [{"type": "stop_loss", "value": 0.05}]
        risk_result, _ = apply_adjustments("risk_config", risk, risk_adj)
        assert risk_result["stop_loss"] == 0.05

        # 3. 绑定调节
        bindings = [
            {"symbol": "000001", "strategy_params": {"window": 5}},
        ]
        binding_adj = [
            {
                "type": "param_change",
                "symbol": "000001",
                "param_changes": {"window": 20},
            }
        ]
        binding_result, rebacktest = apply_adjustments("binding", bindings, binding_adj)
        assert binding_result[0]["strategy_params"]["window"] == 20
        assert "000001" in rebacktest


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
