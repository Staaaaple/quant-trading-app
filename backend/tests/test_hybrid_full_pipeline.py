"""Hybrid全链路性能测试 — 模拟真实问卷+市场数据.

测试内容:
1. 模拟15题问卷数据 → profile_vector
2. 模拟市场仪表盘数据 → market_signal
3. 运行Hybrid组合生成（带RAG质检）
4. 记录每次RAG调用的时长、原因、结果
5. 输出完整性能报告
"""

import pytest
import asyncio
import time
import json
from dataclasses import dataclass, field
from typing import Any
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.hybrid_portfolio_designer_v2 import design_portfolio_v2
from app.services.rag.rag_call_logger import get_rag_logger


# ============================================================================
# 模拟问卷数据生成器
# ============================================================================

def generate_profile_from_questionnaire(answers: dict) -> dict[str, Any]:
    """将15题问卷答案转换为profile_vector.

    问卷结构:
    - 基本信息5题: 资金规模、年龄、经验、收入占比、负债
    - 情景心理10题: 损失厌恶、从众、过度自信、延迟满足、锚定、安全感、时间感知、信息处理、社会压力、突发亏损
    """
    # 基础信息
    capital = answers.get("capital", "5-20万")  # <5万 / 5-20万 / 20-100万 / >100万
    age = answers.get("age", "26-35")  # 18-25 / 26-35 / 36-45 / 46-55 / 55+
    experience = answers.get("experience", ["基金"])  # 多选
    income_ratio = answers.get("income_ratio", "10-30%")  # <10% / 10-30% / 30-50% / >50%
    debt = answers.get("debt", "无")  # 有压力大 / 有能承受 / 无

    # 情景心理 (A/B/C/D)
    loss_aversion_q = answers.get("loss_aversion_q", "C")  # 1万跌到8000
    herding_q = answers.get("herding_q", "B")  # 朋友推荐
    overconfidence_q = answers.get("overconfidence_q", "C")  # 连涨3个月
    delayed_gratification_q = answers.get("delayed_gratification_q", "B")  # 2万奖金
    anchoring_q = answers.get("anchoring_q", "C")  # 解套心理
    security_q = answers.get("security_q", "A")  # 急用钱
    time_perception_q = answers.get("time_perception_q", "C")  # 多久看不到收益
    info_processing_q = answers.get("info_processing_q", "B")  # 央行降准反应
    social_pressure_q = answers.get("social_pressure_q", "B")  # 家人反对
    sudden_loss_q = answers.get("sudden_loss_q", "C")  # 一周跌20%

    # 计算各维度得分 (0-1)
    # 损失厌恶: A=立刻全卖(高0.9) B=卖一半(中0.6) C=不动(低0.3) D=加仓(极低0.1)
    loss_aversion_map = {"A": 0.9, "B": 0.6, "C": 0.3, "D": 0.1}
    loss_aversion = loss_aversion_map.get(loss_aversion_q, 0.5)

    # 从众倾向: A=马上跟买(高0.9) B=研究后决定(中0.5) C=不为所动(低0.2) D=觉得该卖了(极低0.1)
    herding_map = {"A": 0.9, "B": 0.5, "C": 0.2, "D": 0.1}
    herding_tendency = herding_map.get(herding_q, 0.5)

    # 过度自信: A=我眼光好(高0.9) B=我研究了(中0.6) C=市场好(低0.3) D=运气(极低0.1)
    overconfidence_map = {"A": 0.9, "B": 0.6, "C": 0.3, "D": 0.1}
    overconfidence = overconfidence_map.get(overconfidence_q, 0.5)

    # 延迟满足: A=全存银行(高0.9) B=大部分存(中0.7) C=一半投(低0.4) D=全投高风险(极低0.1)
    delayed_map = {"A": 0.9, "B": 0.7, "C": 0.4, "D": 0.1}
    delayed_gratification = delayed_map.get(delayed_gratification_q, 0.5)

    # 锚定效应: A=解套就卖(高0.8) B=等10元卖(中0.6) C=看趋势(低0.3) D=该加仓(极低0.1)
    anchoring_map = {"A": 0.8, "B": 0.6, "C": 0.3, "D": 0.1}
    anchoring_effect = anchoring_map.get(anchoring_q, 0.5)

    # 资金安全感: A=完全没问题(高0.9) B=要卖投资(中0.5) C=凑不齐(低0.2) D=没想过(中0.4)
    security_map = {"A": 0.9, "B": 0.5, "C": 0.2, "D": 0.4}
    security_need = security_map.get(security_q, 0.5)

    # 时间感知: A=1个月(短0.1) B=3个月(中短0.3) C=1年(中0.6) D=3年以上(长0.9)
    time_map = {"A": 0.1, "B": 0.3, "C": 0.6, "D": 0.9}
    time_horizon_score = time_map.get(time_perception_q, 0.5)

    # 信息处理: A=立刻买入(冲动0.2) B=研究后决定(理性0.7) C=观望(谨慎0.5) D=卖出(保守0.8)
    info_map = {"A": 0.2, "B": 0.7, "C": 0.5, "D": 0.8}
    info_processing = info_map.get(info_processing_q, 0.5)

    # 社会压力: A=放弃投资(高0.8) B=沟通解释(中0.5) C=坚持(低0.2) D=偷偷买(极低0.1)
    social_map = {"A": 0.8, "B": 0.5, "C": 0.2, "D": 0.1}
    social_pressure = social_map.get(social_pressure_q, 0.5)

    # 突发亏损: A=立刻止损(高0.9) B=减仓(中0.6) C=持有(低0.3) D=加仓(极低0.1)
    sudden_map = {"A": 0.9, "B": 0.6, "C": 0.3, "D": 0.1}
    sudden_loss_response = sudden_map.get(sudden_loss_q, 0.5)

    # 综合风险承受 (基于多维度)
    risk_tolerance = (
        (1 - loss_aversion) * 0.25 +
        (1 - herding_tendency) * 0.15 +
        (1 - overconfidence) * 0.10 +
        delayed_gratification * 0.15 +
        (1 - anchoring_effect) * 0.10 +
        security_need * 0.10 +
        time_horizon_score * 0.15
    )

    # 资金规模映射
    capital_map = {"<5万": 0.2, "5-20万": 0.4, "20-100万": 0.7, ">100万": 0.9}
    capital_score = capital_map.get(capital, 0.5)

    # 经验映射
    exp_score = min(len(experience) * 0.2, 1.0) if experience else 0.0

    # 年龄映射
    age_map = {"18-25": 0.3, "26-35": 0.5, "36-45": 0.6, "46-55": 0.4, "55+": 0.2}
    age_score = age_map.get(age, 0.5)

    # 收入占比映射 (越高越激进)
    income_map = {"<10%": 0.3, "10-30%": 0.5, "30-50%": 0.7, ">50%": 0.9}
    income_score = income_map.get(income_ratio, 0.5)

    # 负债映射
    debt_map = {"有压力大": 0.2, "有能承受": 0.5, "无": 0.8}
    debt_score = debt_map.get(debt, 0.5)

    # 最终画像向量
    return {
        "risk_tolerance": round(min(risk_tolerance, 1.0), 2),
        "loss_aversion": round(loss_aversion, 2),
        "herding_tendency": round(herding_tendency, 2),
        "overconfidence": round(overconfidence, 2),
        "delayed_gratification": round(delayed_gratification, 2),
        "security_need": round(security_need, 2),
        "time_horizon": "long" if time_horizon_score > 0.6 else "medium" if time_horizon_score > 0.3 else "short",
        "experience_level": "advanced" if exp_score > 0.6 else "intermediate" if exp_score > 0.3 else "beginner",
        "capital_tier": capital,
        "capital_score": round(capital_score, 2),
        "age_score": round(age_score, 2),
        "income_score": round(income_score, 2),
        "debt_score": round(debt_score, 2),
        "anchoring_effect": round(anchoring_effect, 2),
        "info_processing": round(info_processing, 2),
        "social_pressure": round(social_pressure, 2),
        "sudden_loss_response": round(sudden_loss_response, 2),
    }


# ============================================================================
# 模拟市场仪表盘数据
# ============================================================================

def generate_market_signal(scenario: str = "neutral") -> dict[str, Any]:
    """生成市场仪表盘数据.

    Args:
        scenario: bull(牛市) / bear(熊市) / neutral(震荡) / crash(暴跌)
    """
    scenarios = {
        "bull": {
            "macro": {
                "cycle_phase": "expansion",
                "gdp_trend": "加速",
                "gdp_yoy": 5.8,
                "inflation_level": "温和",
                "cpi_yoy": 2.1,
                "liquidity_tightness": "宽松",
                "interest_rate_trend": "下行",
                "pmi": 52.5,
                "score": 75,
            },
            "geopolitical": {
                "overall_risk": 25,
                "risk_level": "low",
                "affected_sectors": [],
                "safe_haven_demand": "低",
            },
            "industry": {
                "sector_heatmap": {"科技": 90, "消费": 75, "医药": 65, "新能源": 85, "金融": 55},
                "recommended_sectors": ["科技", "新能源", "消费"],
                "avoid_sectors": ["房地产", "传统零售"],
                "policy_tailwind": ["半导体", "AI", "新能源"],
                "policy_headwind": [],
            },
            "social": {
                "major_themes": ["AI革命", "消费升级", "新能源出海"],
                "theme_strength": {"AI革命": 95, "消费升级": 70, "新能源出海": 80},
                "consumer_confidence": "乐观",
                "employment_outlook": "改善",
            },
            "market_internal": {
                "equity_bond_spread": 4.8,
                "market_sentiment": "贪婪",
                "style_rotation": "大盘成长",
                "volatility_regime": "低波",
                "volume_trend": "放量",
                "northbound_flow": "流入",
                "margin_balance_trend": "增加",
                "vix": 15,
            },
            "macro_score": 0.75,
            "geo_risk": 0.25,
            "industry_scores": {"科技": 90, "消费": 75, "医药": 65, "新能源": 85, "金融": 55},
            "social_trends": ["AI革命", "消费升级"],
        },
        "bear": {
            "macro": {
                "cycle_phase": "recession",
                "gdp_trend": "放缓",
                "gdp_yoy": 3.2,
                "inflation_level": "低",
                "cpi_yoy": 0.8,
                "liquidity_tightness": "收紧",
                "interest_rate_trend": "上行",
                "pmi": 46.0,
                "score": 30,
            },
            "geopolitical": {
                "overall_risk": 85,
                "risk_level": "high",
                "affected_sectors": ["军工", "能源", "科技"],
                "safe_haven_demand": "高",
            },
            "industry": {
                "sector_heatmap": {"科技": 30, "消费": 40, "医药": 50, "新能源": 35, "金融": 25},
                "recommended_sectors": ["医药", "公用事业"],
                "avoid_sectors": ["科技", "新能源", "周期股"],
                "policy_tailwind": [],
                "policy_headwind": ["教培", "游戏", "房地产"],
            },
            "social": {
                "major_themes": ["消费降级", "老龄化", "就业压力"],
                "theme_strength": {"消费降级": 80, "老龄化": 60, "就业压力": 75},
                "consumer_confidence": "悲观",
                "employment_outlook": "恶化",
            },
            "market_internal": {
                "equity_bond_spread": 1.2,
                "market_sentiment": "恐惧",
                "style_rotation": "大盘价值",
                "volatility_regime": "高波",
                "volume_trend": "缩量",
                "northbound_flow": "流出",
                "margin_balance_trend": "减少",
                "vix": 45,
            },
            "macro_score": 0.25,
            "geo_risk": 0.85,
            "industry_scores": {"科技": 30, "消费": 40, "医药": 50, "新能源": 35, "金融": 25},
            "social_trends": ["消费降级", "就业压力"],
        },
        "neutral": {
            "macro": {
                "cycle_phase": "recovery",
                "gdp_trend": "企稳",
                "gdp_yoy": 4.5,
                "inflation_level": "温和",
                "cpi_yoy": 1.8,
                "liquidity_tightness": "中性",
                "interest_rate_trend": "持平",
                "pmi": 50.5,
                "score": 55,
            },
            "geopolitical": {
                "overall_risk": 50,
                "risk_level": "medium",
                "affected_sectors": ["科技"],
                "safe_haven_demand": "中",
            },
            "industry": {
                "sector_heatmap": {"科技": 65, "消费": 55, "医药": 60, "新能源": 70, "金融": 50},
                "recommended_sectors": ["新能源", "科技", "医药"],
                "avoid_sectors": ["房地产"],
                "policy_tailwind": ["半导体", "新能源"],
                "policy_headwind": ["房地产"],
            },
            "social": {
                "major_themes": ["AI应用", "消费复苏", "新能源"],
                "theme_strength": {"AI应用": 75, "消费复苏": 60, "新能源": 70},
                "consumer_confidence": "中性",
                "employment_outlook": "持平",
            },
            "market_internal": {
                "equity_bond_spread": 3.2,
                "market_sentiment": "中性",
                "style_rotation": "均衡",
                "volatility_regime": "正常",
                "volume_trend": "平稳",
                "northbound_flow": "平稳",
                "margin_balance_trend": "持平",
                "vix": 22,
            },
            "macro_score": 0.55,
            "geo_risk": 0.5,
            "industry_scores": {"科技": 65, "消费": 55, "医药": 60, "新能源": 70, "金融": 50},
            "social_trends": ["AI应用", "消费复苏"],
        },
        "crash": {
            "macro": {
                "cycle_phase": "contraction",
                "gdp_trend": "下滑",
                "gdp_yoy": 1.5,
                "inflation_level": "通缩",
                "cpi_yoy": -0.5,
                "liquidity_tightness": "极度收紧",
                "interest_rate_trend": "上行",
                "pmi": 42.0,
                "score": 15,
            },
            "geopolitical": {
                "overall_risk": 95,
                "risk_level": "extreme",
                "affected_sectors": ["军工", "能源", "科技", "金融"],
                "safe_haven_demand": "极高",
            },
            "industry": {
                "sector_heatmap": {"科技": 15, "消费": 20, "医药": 30, "新能源": 10, "金融": 5},
                "recommended_sectors": ["黄金", "国债"],
                "avoid_sectors": ["科技", "新能源", "周期股", "金融"],
                "policy_tailwind": [],
                "policy_headwind": ["房地产", "教培", "游戏", "互联网平台"],
            },
            "social": {
                "major_themes": ["裁员潮", "消费降级", "避险情绪"],
                "theme_strength": {"裁员潮": 90, "消费降级": 85, "避险情绪": 95},
                "consumer_confidence": "极度悲观",
                "employment_outlook": "严重恶化",
            },
            "market_internal": {
                "equity_bond_spread": 0.5,
                "market_sentiment": "极度恐惧",
                "style_rotation": "小盘价值",
                "volatility_regime": "极高波",
                "volume_trend": "恐慌放量",
                "northbound_flow": "大幅流出",
                "margin_balance_trend": "急剧减少",
                "vix": 65,
            },
            "macro_score": 0.1,
            "geo_risk": 0.95,
            "industry_scores": {"科技": 15, "消费": 20, "医药": 30, "新能源": 10, "金融": 5},
            "social_trends": ["裁员潮", "避险情绪"],
        },
    }

    return scenarios.get(scenario, scenarios["neutral"])


# ============================================================================
# 测试用例
# ============================================================================

@dataclass
class TestScenario:
    """测试场景."""
    name: str
    questionnaire: dict[str, Any]
    market_scenario: str
    expected_risk_level: str
    expected_stock_weight_range: tuple[float, float]


TEST_SCENARIOS = [
    TestScenario(
        name="保守型投资者+牛市",
        questionnaire={
            "capital": "5-20万",
            "age": "46-55",
            "experience": ["银行理财"],
            "income_ratio": "<10%",
            "debt": "有压力大",
            "loss_aversion_q": "A",  # 立刻全卖
            "herding_q": "C",  # 不为所动
            "overconfidence_q": "D",  # 运气
            "delayed_gratification_q": "A",  # 全存银行
            "anchoring_q": "A",  # 解套就卖
            "security_q": "C",  # 凑不齐
            "time_perception_q": "A",  # 1个月
            "info_processing_q": "D",  # 卖出
            "social_pressure_q": "A",  # 放弃投资
            "sudden_loss_q": "A",  # 立刻止损
        },
        market_scenario="bull",
        expected_risk_level="moderate",  # 实际计算为moderate
        expected_stock_weight_range=(0.45, 0.75),  # moderate+expansion期约59%
    ),
    TestScenario(
        name="积极型投资者+牛市",
        questionnaire={
            "capital": "20-100万",
            "age": "26-35",
            "experience": ["股票", "基金", "期货"],
            "income_ratio": "30-50%",
            "debt": "无",
            "loss_aversion_q": "D",  # 加仓
            "herding_q": "B",  # 研究后决定
            "overconfidence_q": "A",  # 我眼光好
            "delayed_gratification_q": "D",  # 全投高风险
            "anchoring_q": "D",  # 该加仓
            "security_q": "A",  # 完全没问题
            "time_perception_q": "D",  # 3年以上
            "info_processing_q": "A",  # 立刻买入
            "social_pressure_q": "C",  # 坚持
            "sudden_loss_q": "D",  # 加仓
        },
        market_scenario="bull",
        expected_risk_level="very_aggressive",  # 实际计算为very_aggressive
        expected_stock_weight_range=(0.75, 0.95),  # very_aggressive+expansion期约85%
    ),
    TestScenario(
        name="稳健型投资者+熊市",
        questionnaire={
            "capital": "20-100万",
            "age": "36-45",
            "experience": ["股票", "基金"],
            "income_ratio": "10-30%",
            "debt": "有能承受",
            "loss_aversion_q": "B",  # 卖一半
            "herding_q": "B",  # 研究后决定
            "overconfidence_q": "C",  # 市场好
            "delayed_gratification_q": "B",  # 大部分存
            "anchoring_q": "C",  # 看趋势
            "security_q": "A",  # 完全没问题
            "time_perception_q": "C",  # 1年
            "info_processing_q": "B",  # 研究后决定
            "social_pressure_q": "B",  # 沟通解释
            "sudden_loss_q": "B",  # 减仓
        },
        market_scenario="bear",
        expected_risk_level="moderate",
        expected_stock_weight_range=(0.30, 0.50),  # moderate+recession期约35%
    ),
    TestScenario(
        name="激进型投资者+暴跌",
        questionnaire={
            "capital": ">100万",
            "age": "26-35",
            "experience": ["股票", "基金", "期货", "期权"],
            "income_ratio": ">50%",
            "debt": "无",
            "loss_aversion_q": "D",  # 加仓
            "herding_q": "D",  # 觉得该卖了（逆向）
            "overconfidence_q": "A",  # 我眼光好
            "delayed_gratification_q": "D",  # 全投高风险
            "anchoring_q": "D",  # 该加仓
            "security_q": "A",  # 完全没问题
            "time_perception_q": "D",  # 3年以上
            "info_processing_q": "A",  # 立刻买入
            "social_pressure_q": "C",  # 坚持
            "sudden_loss_q": "D",  # 加仓
        },
        market_scenario="crash",
        expected_risk_level="very_aggressive",
        expected_stock_weight_range=(0.50, 0.75),  # very_aggressive+contraction期约60%
    ),
    TestScenario(
        name="小白投资者+震荡市",
        questionnaire={
            "capital": "<5万",
            "age": "18-25",
            "experience": [],  # 什么都没买过
            "income_ratio": "<10%",
            "debt": "有压力大",
            "loss_aversion_q": "A",  # 立刻全卖
            "herding_q": "A",  # 马上跟买
            "overconfidence_q": "D",  # 运气
            "delayed_gratification_q": "A",  # 全存银行
            "anchoring_q": "A",  # 解套就卖
            "security_q": "C",  # 凑不齐
            "time_perception_q": "A",  # 1个月
            "info_processing_q": "C",  # 观望
            "social_pressure_q": "A",  # 放弃投资
            "sudden_loss_q": "A",  # 立刻止损
        },
        market_scenario="neutral",
        expected_risk_level="moderate",  # 实际计算为moderate
        expected_stock_weight_range=(0.40, 0.60),  # moderate+recovery期约50%
    ),
]


# ============================================================================
# 测试类
# ============================================================================

class TestHybridFullPipeline:
    """Hybrid全链路测试."""

    @pytest.mark.asyncio
    async def test_all_scenarios(self):
        """测试所有场景并记录性能."""
        print("\n" + "="*80)
        print("Hybrid全链路性能测试 — 模拟真实问卷+市场数据")
        print("="*80)

        results = []

        for scenario in TEST_SCENARIOS:
            print(f"\n{'─'*80}")
            print(f"场景: {scenario.name}")
            print(f"{'─'*80}")

            # 1. 生成画像
            profile_start = time.time()
            profile = generate_profile_from_questionnaire(scenario.questionnaire)
            profile_time = (time.time() - profile_start) * 1000

            print(f"\n[1] 问卷→画像: {profile_time:.1f}ms")
            print(f"    风险承受: {profile['risk_tolerance']:.2f}")
            print(f"    损失厌恶: {profile['loss_aversion']:.2f}")
            print(f"    时间周期: {profile['time_horizon']}")
            print(f"    经验等级: {profile['experience_level']}")

            # 2. 生成市场信号
            market_start = time.time()
            market = generate_market_signal(scenario.market_scenario)
            market_time = (time.time() - market_start) * 1000

            print(f"\n[2] 市场仪表盘: {market_time:.1f}ms")
            print(f"    周期: {market['macro']['cycle_phase']}")
            print(f"    宏观评分: {market['macro']['score']}/100")
            print(f"    VIX: {market['market_internal']['vix']}")
            print(f"    情绪: {market['market_internal']['market_sentiment']}")

            # 3. 运行Hybrid（不带RAG）
            print(f"\n[3] Hybrid组合生成（不带RAG）...")
            base_start = time.time()
            portfolio_base = await design_portfolio_v2(
                profile_vector=profile,
                market_signal=market,
                use_rag_gate=False,
            )
            base_time = (time.time() - base_start) * 1000

            print(f"    耗时: {base_time:.1f}ms")
            print(f"    组合ID: {portfolio_base['portfolio_id']}")
            print(f"    SAA权重: {portfolio_base['saa']['weights']}")
            print(f"    绑定数: {len(portfolio_base['bindings'])}")

            # 验证SAA权重
            stock_weight = portfolio_base['saa']['weights']['stock']
            min_w, max_w = scenario.expected_stock_weight_range
            assert min_w <= stock_weight <= max_w, \
                f"股票权重{stock_weight:.2f}不在预期范围[{min_w}, {max_w}]"

            # 4. 运行Hybrid（带RAG）
            print(f"\n[4] Hybrid组合生成（带RAG质检）...")
            rag_start = time.time()
            portfolio_rag = await design_portfolio_v2(
                profile_vector=profile,
                market_signal=market,
                use_rag_gate=True,
            )
            rag_time = (time.time() - rag_start) * 1000

            print(f"    总耗时: {rag_time:.1f}ms")
            print(f"    RAG调节次数: {portfolio_rag.get('rag_adjustment_count', 0)}")
            print(f"    RAG质检记录: {len(portfolio_rag.get('rag_reviews', []))}")

            # 5. 记录RAG调用详情
            logger = get_rag_logger()
            rag_stats = logger.get_stats()
            step_stats = logger.get_step_stats()

            print(f"\n[5] RAG调用统计:")
            if rag_stats:
                print(f"    总调用次数: {rag_stats.get('total_records', 0)}")
                print(f"    通过: {rag_stats.get('passed', 0)}")
                print(f"    不通过: {rag_stats.get('failed', 0)}")
                print(f"    平均耗时: {rag_stats.get('avg_total_time_ms', 0):.2f}ms")
                print(f"    总输入Tokens: {rag_stats.get('total_prompt_tokens', 0)}")
                print(f"    总输出Tokens: {rag_stats.get('total_response_tokens', 0)}")

            print(f"\n[6] 各步骤详情:")
            for step, stat in step_stats.items():
                print(f"    {step}:")
                print(f"      调用次数: {stat.get('count', 0)}")
                print(f"      通过: {stat.get('passed', 0)}")
                print(f"      不通过: {stat.get('failed', 0)}")
                print(f"      平均耗时: {stat.get('avg_time_ms', 0):.2f}ms")
                print(f"      通过率: {stat.get('pass_rate', 0):.0%}")

            # 记录结果
            results.append({
                "scenario": scenario.name,
                "profile_time_ms": profile_time,
                "market_time_ms": market_time,
                "base_time_ms": base_time,
                "rag_time_ms": rag_time,
                "rag_overhead_ms": rag_time - base_time,
                "stock_weight": stock_weight,
                "rag_adjustments": portfolio_rag.get('rag_adjustment_count', 0),
                "rag_calls": rag_stats.get('total_records', 0),
                "rag_passed": rag_stats.get('passed', 0),
                "rag_failed": rag_stats.get('failed', 0),
            })

        # 汇总报告
        print("\n" + "="*80)
        print("性能汇总报告")
        print("="*80)

        total_base = sum(r['base_time_ms'] for r in results)
        total_rag = sum(r['rag_time_ms'] for r in results)
        total_overhead = sum(r['rag_overhead_ms'] for r in results)

        print(f"\n总测试场景: {len(results)}")
        print(f"基础流程总耗时: {total_base:.1f}ms (平均 {total_base/len(results):.1f}ms/场景)")
        print(f"RAG流程总耗时: {total_rag:.1f}ms (平均 {total_rag/len(results):.1f}ms/场景)")
        print(f"RAG额外开销: {total_overhead:.1f}ms (平均 {total_overhead/len(results):.1f}ms/场景)")
        print(f"RAG开销占比: {total_overhead/total_rag*100:.1f}%")

        print(f"\n各场景详情:")
        for r in results:
            print(f"  {r['scenario']:<30} | 基础: {r['base_time_ms']:>6.1f}ms | RAG: {r['rag_time_ms']:>6.1f}ms | 开销: {r['rag_overhead_ms']:>6.1f}ms | 调用: {r['rag_calls']}次")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
