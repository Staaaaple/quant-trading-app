"""QuantEvo 端到端全流程测试.

模拟真实用户路径:
1. 用户填写18题问卷
2. 计算18维画像向量
3. 获取市场信号
4. Hybrid组合设计 (带RAG循环质检)
5. 详细记录每一步耗时、LLM调用、修改策略、通过率

测试场景:
- 场景A: 保守型小白 + 熊市
- 场景B: 稳健型投资者 + 复苏期
- 场景C: 积极型熟手 + 牛市
- 场景D: 激进型高手 + 震荡市
"""

import sys
import time
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.profile_service import compute_profile_vector, derive_labels, QUESTIONS
from app.services.saa_engine import get_risk_level_from_profile, get_market_cycle_from_signal


# ─────────────────────────────────────────────────────────────────────────────
# 测试配置
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TestScenario:
    """测试场景定义."""
    name: str
    description: str
    answers: dict[str, Any]  # 问卷答案
    market_scenario: str  # bull/bear/recovery/crash/neutral


@dataclass
class StepLog:
    """单步执行日志."""
    step_name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    passed: bool = False
    score: float = 0.0
    issues: list[str] = field(default_factory=list)
    adjustments: list[dict] = field(default_factory=list)
    adjustment_strategy: str = ""  # 修改策略描述
    llm_prompt_tokens: int = 0
    llm_response_tokens: int = 0
    retry_count: int = 0
    raw_result: dict = field(default_factory=dict)

    def finalize(self):
        self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class PipelineReport:
    """完整流水线报告."""
    scenario_name: str
    scenario_description: str
    total_duration_ms: float = 0.0
    questionnaire_duration_ms: float = 0.0
    profile_vector: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    risk_level: str = ""
    market_cycle: str = ""
    market_signal: dict = field(default_factory=dict)
    steps: list[StepLog] = field(default_factory=list)
    final_portfolio: dict = field(default_factory=dict)
    rag_stats: dict = field(default_factory=dict)
    overall_passed: bool = False
    timestamp: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# 测试场景数据
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS = [
    TestScenario(
        name="保守型小白_熊市",
        description="25岁保守型投资新手，无经验，高损失厌恶，熊市环境",
        answers={
            "q1_capital": "小于5万",
            "q2_age": "18-25岁",
            "q3_experience": ["银行理财/余额宝"],
            "q4_income_stability": "自由职业/不稳定",
            "q5_debt_pressure": "无负债",
            "q6_diversification": "只买一种（如只存银行或只买股票）",
            "q7_risk_tolerance": "不能亏，保本第一",
            "q8_stop_loss": "从不设止损",
            "q9_loss_scenario": "立刻全部清仓",
            "q10_anchoring": "解套就卖，再也不碰",
            "q11_time_horizon": "1个月",
            "q12_security_need": "完全没问题，随时可取",
            "q13_herding": "马上跟买，怕错过",
            "q14_overconfidence": "我眼光好，有天赋",
            "q15_info_processing": "立刻据此操作",
            "q16_delayed_gratification": "立刻卖出落袋为安",
            "q17_social_pressure": "立刻停止，听他们的",
            "q18_emotional_stability": "恐慌清仓，再也不投",
        },
        market_scenario="bear",
    ),
    TestScenario(
        name="稳健型投资者_复苏期",
        description="35岁稳健型投资者，有一定经验，中等风险承受，复苏期",
        answers={
            "q1_capital": "20万-100万",
            "q2_age": "36-45岁",
            "q3_experience": ["银行理财/余额宝", "基金"],
            "q4_income_stability": "较稳定，偶有奖金",
            "q5_debt_pressure": "10%-30%",
            "q6_diversification": "4-5种（股票+债券+基金+黄金等）",
            "q7_risk_tolerance": "10%-20%",
            "q8_stop_loss": "偶尔执行",
            "q9_loss_scenario": "减仓一半",
            "q10_anchoring": "看趋势决定，不纠结成本",
            "q11_time_horizon": "1年",
            "q12_security_need": "要卖一部分投资",
            "q13_herding": "先研究一下再决定",
            "q14_overconfidence": "市场好，运气好",
            "q15_info_processing": "结合多个来源交叉验证",
            "q16_delayed_gratification": "卖出一半，留一半",
            "q17_social_pressure": "不受影响，按自己节奏",
            "q18_emotional_stability": "暂停交易，冷静分析原因",
        },
        market_scenario="recovery",
    ),
    TestScenario(
        name="积极型熟手_牛市",
        description="30岁积极型投资熟手，经验丰富，高 risk tolerance，牛市环境",
        answers={
            "q1_capital": "大于100万",
            "q2_age": "26-35岁",
            "q3_experience": ["银行理财/余额宝", "基金", "股票"],
            "q4_income_stability": "非常稳定（公务员/大厂等）",
            "q5_debt_pressure": "无负债",
            "q6_diversification": "全球多元配置（跨市场跨资产）",
            "q7_risk_tolerance": "20%-30%",
            "q8_stop_loss": "严格执行，触达就卖",
            "q9_loss_scenario": "检查基本面，再决定",
            "q10_anchoring": "该加仓，便宜了",
            "q11_time_horizon": "3年以上",
            "q12_security_need": "凑不齐，大部分都在投资里",
            "q13_herding": "不为所动，有自己的判断",
            "q14_overconfidence": "我做了研究，方法对",
            "q15_info_processing": "结合多个来源交叉验证",
            "q16_delayed_gratification": "用利润再投入",
            "q17_social_pressure": "用数据和收益说服他们",
            "q18_emotional_stability": "按计划执行，情绪不影响决策",
        },
        market_scenario="bull",
    ),
    TestScenario(
        name="激进型高手_震荡市",
        description="40岁激进型投资高手，期货期权经验，极高风险承受，震荡市",
        answers={
            "q1_capital": "大于100万",
            "q2_age": "36-45岁",
            "q3_experience": ["银行理财/余额宝", "基金", "股票", "期货/期权/加密货币"],
            "q4_income_stability": "非常稳定（公务员/大厂等）",
            "q5_debt_pressure": "10%以下",
            "q6_diversification": "全球多元配置（跨市场跨资产）",
            "q7_risk_tolerance": "30%以上，能扛住",
            "q8_stop_loss": "严格执行，触达就卖",
            "q9_loss_scenario": "加仓摊低成本",
            "q10_anchoring": "该加仓，便宜了",
            "q11_time_horizon": "3年以上",
            "q12_security_need": "凑不齐，大部分都在投资里",
            "q13_herding": "觉得涨多了该卖了，不会追高",
            "q14_overconfidence": "我眼光好，有天赋",
            "q15_info_processing": "忽略，等市场消化后再看",
            "q16_delayed_gratification": "用利润再投入",
            "q17_social_pressure": "不受影响，按自己节奏",
            "q18_emotional_stability": "按计划执行，情绪不影响决策",
        },
        market_scenario="volatile",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# 市场信号生成
# ─────────────────────────────────────────────────────────────────────────────

def generate_market_signal(scenario: str) -> dict[str, Any]:
    """根据场景生成市场信号."""
    signals = {
        "bull": {
            "macro_score": 0.75,
            "industry_score": 0.70,
            "sentiment_score": 0.80,
            "geo_risk": 0.30,
            "vix": 15,
            "equity_bond_spread": 4.5,
            "industry_scores": {
                "technology": 0.85, "healthcare": 0.70, "finance": 0.65,
                "energy": 0.55, "consumer": 0.75, "industrial": 0.60,
            },
            "social_trends": ["AI投资热潮", "新能源转型", "消费升级"],
            "cycle_phase": "expansion",
        },
        "bear": {
            "macro_score": 0.25,
            "industry_score": 0.30,
            "sentiment_score": 0.20,
            "geo_risk": 0.75,
            "vix": 35,
            "equity_bond_spread": 1.5,
            "industry_scores": {
                "technology": 0.35, "healthcare": 0.45, "finance": 0.30,
                "energy": 0.40, "consumer": 0.35, "industrial": 0.30,
            },
            "social_trends": ["经济衰退担忧", "地缘政治紧张", "避险情绪升温"],
            "cycle_phase": "contraction",
        },
        "recovery": {
            "macro_score": 0.55,
            "industry_score": 0.60,
            "sentiment_score": 0.55,
            "geo_risk": 0.40,
            "vix": 22,
            "equity_bond_spread": 3.0,
            "industry_scores": {
                "technology": 0.75, "healthcare": 0.65, "finance": 0.55,
                "energy": 0.50, "consumer": 0.60, "industrial": 0.55,
            },
            "social_trends": ["AI投资热潮", "新能源转型"],
            "cycle_phase": "recovery",
        },
        "volatile": {
            "macro_score": 0.50,
            "industry_score": 0.50,
            "sentiment_score": 0.45,
            "geo_risk": 0.60,
            "vix": 28,
            "equity_bond_spread": 2.5,
            "industry_scores": {
                "technology": 0.60, "healthcare": 0.55, "finance": 0.50,
                "energy": 0.65, "consumer": 0.50, "industrial": 0.45,
            },
            "social_trends": ["地缘冲突", "通胀担忧", "政策不确定性"],
            "cycle_phase": "peak",
        },
    }
    base = signals.get(scenario, signals["recovery"])
    return {
        **base,
        "macro": {"cycle_phase": base["cycle_phase"], "score": int(base["macro_score"] * 100)},
        "geopolitical": {"overall_risk": int(base["geo_risk"] * 100)},
        "market_internal": {
            "vix": base["vix"],
            "equity_bond_spread": base["equity_bond_spread"],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Mock RAG 质检 (用于测试，不调用真实LLM)
# ─────────────────────────────────────────────────────────────────────────────

class MockQualityGate:
    """模拟RAG质检门控 — 基于规则判断，记录详细日志，模拟LLM耗时."""

    # 模拟LLM调用耗时配置 (毫秒)
    LLM_LATENCY_MS = {
        "SAA": 85000,      # ~85s (如真实测试报告)
        "风控": 65000,     # ~65s
        "可靠性": 92000,   # ~92s
        "最终": 52000,     # ~52s
    }

    def __init__(self):
        self.step_logs: list[StepLog] = []
        self.call_count = 0

    def _simulate_llm_latency(self, step_type: str):
        """模拟LLM调用耗时."""
        import random
        base_ms = self.LLM_LATENCY_MS.get(step_type, 60000)
        # 添加±20%随机波动
        jitter = random.uniform(0.8, 1.2)
        latency_ms = base_ms * jitter
        time.sleep(latency_ms / 1000)  # 转换为秒
        return latency_ms

    def _log_step(self, step_name: str, start_time: float, **kwargs) -> StepLog:
        """记录步骤日志."""
        log = StepLog(step_name=step_name, start_time=start_time, **kwargs)
        self.step_logs.append(log)
        return log

    def review_saa(self, saa_result: dict, profile_vector: dict, market_signal: dict) -> tuple[bool, list[dict], str]:
        """模拟SAA审核.

        审核规则:
        - 保守型: 股票≤30%
        - 稳健型: 股票≤50%
        - 积极型: 股票≤70%
        - 激进型: 股票≤90%
        - 熊市: 股票应低于周期基准
        """
        self.call_count += 1
        start = time.time()
        llm_time_ms = self._simulate_llm_latency("SAA")

        weights = saa_result.get("weights", {})
        stock_pct = weights.get("stock", 0)
        risk_tolerance = profile_vector.get("risk_tolerance", 5) / 10  # 1-10 -> 0-1
        market_cycle = market_signal.get("cycle_phase", "recovery")

        # 确定风险等级
        if risk_tolerance < 0.3:
            risk_level, stock_limit = "conservative", 0.30
        elif risk_tolerance < 0.6:
            risk_level, stock_limit = "moderate", 0.50
        elif risk_tolerance < 0.8:
            risk_level, stock_limit = "aggressive", 0.70
        else:
            risk_level, stock_limit = "very_aggressive", 0.90

        # 市场周期调整
        if market_cycle in ["contraction", "trough"]:
            stock_limit *= 0.85

        issues = []
        adjustments = []
        strategy = ""

        # 使用容差比较，避免浮点精度问题导致无限循环
        TOLERANCE = 0.005  # 0.5%容差

        if stock_pct > stock_limit + TOLERANCE:
            issues.append(f"股票权重{stock_pct:.1%}超过{risk_level}型上限{stock_limit:.1%}")
            new_stock = stock_limit
            excess = stock_pct - new_stock
            adjustments.append({
                "type": "weight_cap",
                "asset": "stock",
                "cap": new_stock,
            })
            strategy = f"股票权重截断: {stock_pct:.1%}→{new_stock:.1%}, 超额{excess:.1%}转债券"

        # 地缘风险检查
        geo_risk = market_signal.get("geo_risk", 0.5)
        if geo_risk > 0.6 and weights.get("commodity", 0) < 0.05:
            issues.append(f"地缘风险高({geo_risk:.0%})但避险资产不足")
            adjustments.append({
                "type": "add_hedge",
                "hedge_asset": "commodity",
                "target": 0.10,
            })
            strategy += "; 增配商品对冲地缘风险"

        passed = len(issues) == 0
        score = 0.9 if passed else 0.4

        log = self._log_step("SAA审核", start)
        log.end_time = time.time()
        log.finalize()
        log.passed = passed
        log.score = score
        log.issues = issues
        log.adjustments = adjustments
        log.adjustment_strategy = strategy or "无需调整"
        log.llm_prompt_tokens = 1200 + self.call_count * 50  # 模拟递增
        log.llm_response_tokens = 800 + self.call_count * 30
        log.raw_result = {"stock_pct": stock_pct, "stock_limit": stock_limit, "risk_level": risk_level, "llm_time_ms": llm_time_ms}

        return passed, adjustments, strategy

    def review_risk_config(self, risk_config: dict, profile_vector: dict) -> tuple[bool, list[dict], str]:
        """模拟风控审核.

        审核规则:
        - 高损失厌恶 → 紧止损(≤5%)
        - 中损失厌恶 → 适中止损(≤8%)
        - 低损失厌恶 → 宽止损(≤12%)
        """
        self.call_count += 1
        start = time.time()
        llm_time_ms = self._simulate_llm_latency("风控")

        loss_aversion = profile_vector.get("loss_aversion", 5) / 10
        stop_loss = risk_config.get("stop_loss", 0.08)
        max_drawdown = risk_config.get("max_drawdown", 0.15)

        issues = []
        adjustments = []
        strategy = ""

        # 止损线检查
        if loss_aversion > 0.7 and stop_loss > 0.05:
            issues.append(f"高损失厌恶({loss_aversion:.1%})但止损线过宽({stop_loss:.1%})")
            adjustments.append({"type": "stop_loss", "value": 0.05})
            strategy = f"止损线收紧: {stop_loss:.1%}→5%"
        elif loss_aversion > 0.4 and stop_loss > 0.08:
            issues.append(f"中等损失厌恶({loss_aversion:.1%})但止损线偏宽({stop_loss:.1%})")
            adjustments.append({"type": "stop_loss", "value": 0.07})
            strategy = f"止损线收紧: {stop_loss:.1%}→7%"

        # 回撤硬止损检查
        if loss_aversion > 0.7 and max_drawdown > 0.10:
            issues.append(f"高损失厌恶但回撤硬止损过宽({max_drawdown:.1%})")
            adjustments.append({"type": "max_drawdown", "value": 0.10})
            strategy += f"; 回撤硬止损收紧: {max_drawdown:.1%}→10%"

        passed = len(issues) == 0
        score = 0.9 if passed else 0.4

        log = self._log_step("风控审核", start)
        log.end_time = time.time()
        log.finalize()
        log.passed = passed
        log.score = score
        log.issues = issues
        log.adjustments = adjustments
        log.adjustment_strategy = strategy or "无需调整"
        log.llm_prompt_tokens = 980 + self.call_count * 40
        log.llm_response_tokens = 650 + self.call_count * 25
        log.raw_result = {"loss_aversion": loss_aversion, "stop_loss": stop_loss, "llm_time_ms": llm_time_ms}

        return passed, adjustments, strategy

    def review_reliability(self, reliability: dict, backtest: dict) -> tuple[bool, list[dict], str]:
        """模拟可靠性审核."""
        self.call_count += 1
        start = time.time()
        llm_time_ms = self._simulate_llm_latency("可靠性")

        confidence = reliability.get("confidence", 0.6)
        portfolio_return = backtest.get("portfolio_return", 0)
        buy_hold_return = backtest.get("buy_hold_return", 0)

        issues = []
        adjustments = []
        strategy = ""

        if portfolio_return <= buy_hold_return:
            issues.append(f"组合收益({portfolio_return:.1f}%)未跑赢买入持有({buy_hold_return:.1f}%)")
            strategy = "建议调低高波动资产权重或更换策略"

        if confidence < 0.6:
            issues.append(f"可靠性置信度偏低({confidence:.2f})")
            strategy += "; 建议增加策略分散度"

        passed = len(issues) == 0
        score = 0.9 if passed else 0.3

        log = self._log_step("可靠性审核", start)
        log.end_time = time.time()
        log.finalize()
        log.passed = passed
        log.score = score
        log.issues = issues
        log.adjustments = adjustments
        log.adjustment_strategy = strategy or "无需调整"
        log.llm_prompt_tokens = 1500 + self.call_count * 60
        log.llm_response_tokens = 900 + self.call_count * 35
        log.raw_result = {"confidence": confidence, "alpha": portfolio_return - buy_hold_return, "llm_time_ms": llm_time_ms}

        return passed, adjustments, strategy

    def final_review(self, portfolio: dict, profile_vector: dict) -> tuple[bool, list[dict], str]:
        """模拟最终审核."""
        self.call_count += 1
        start = time.time()
        llm_time_ms = self._simulate_llm_latency("最终")

        # 检查组合完整性
        issues = []
        has_summary = bool(portfolio.get("saa", {}).get("rationale"))

        if not has_summary:
            issues.append("组合缺少投资逻辑说明")

        passed = len(issues) == 0
        score = 0.95 if passed else 0.5

        log = self._log_step("最终审核", start)
        log.end_time = time.time()
        log.finalize()
        log.passed = passed
        log.score = score
        log.issues = issues
        log.adjustment_strategy = "无需调整" if passed else "补充投资逻辑"
        log.llm_prompt_tokens = 1100 + self.call_count * 45
        log.llm_response_tokens = 700 + self.call_count * 28
        log.raw_result = {"has_summary": has_summary, "llm_time_ms": llm_time_ms}

        return passed, [], ""


# ─────────────────────────────────────────────────────────────────────────────
# 循环审核执行器
# ─────────────────────────────────────────────────────────────────────────────

def run_loop_audit(
    step_name: str,
    review_fn,
    apply_fn,
    max_retries: int,
    *args,
) -> tuple[Any, list[StepLog]]:
    """执行循环审核.

    Args:
        step_name: 步骤名称
        review_fn: 审核函数，返回 (passed, adjustments, strategy)
        apply_fn: 应用调节函数
        max_retries: 最大重试次数
        *args: 传递给 review_fn 的参数

    Returns:
        (最终结果, 步骤日志列表)
    """
    logs = []
    current_result = args[0] if args else {}
    review_args = list(args)

    for retry in range(max_retries + 1):
        # 更新参数中的当前结果
        review_args[0] = current_result
        passed, adjustments, strategy = review_fn(*review_args)

        log = StepLog(
            step_name=f"{step_name}_尝试{retry}",
            start_time=time.time(),
            passed=passed,
            retry_count=retry,
            adjustments=adjustments,
            adjustment_strategy=strategy,
        )

        if passed:
            log.end_time = time.time()
            log.finalize()
            logs.append(log)
            print(f"  ✅ [{step_name}] 尝试{retry}: 通过")
            break

        # 应用调节
        if adjustments:
            current_result = apply_fn(current_result, adjustments)
            log.end_time = time.time()
            log.finalize()
            logs.append(log)
            print(f"  ❌ [{step_name}] 尝试{retry}: 不通过 → {strategy} (耗时{log.duration_ms:.1f}ms)")
        else:
            log.end_time = time.time()
            log.finalize()
            logs.append(log)
            print(f"  ❌ [{step_name}] 尝试{retry}: 不通过，无调节建议 (耗时{log.duration_ms:.1f}ms)")
            break
    else:
        # 超过最大重试次数
        print(f"  ⚠️ [{step_name}] 超过最大重试次数({max_retries})，仍未通过")

    return current_result, logs


# ─────────────────────────────────────────────────────────────────────────────
# 调节应用函数
# ─────────────────────────────────────────────────────────────────────────────

def apply_saa_adjustments(saa_result: dict, adjustments: list[dict]) -> dict:
    """应用SAA调节."""
    import copy
    result = copy.deepcopy(saa_result)
    weights = result.get("weights", {})

    for adj in adjustments:
        adj_type = adj.get("type", "")
        if adj_type == "weight_cap":
            asset = adj["asset"]
            cap = adj["cap"]
            if weights.get(asset, 0) > cap:
                excess = weights[asset] - cap
                weights[asset] = cap
                # 超额分配给债券
                weights["bond"] = weights.get("bond", 0) + excess
        elif adj_type == "weight_floor":
            # weight_floor 作为 weight_cap 的配套操作，直接设置目标值
            # 不在这里单独处理，避免重复归一化导致的问题
            pass
        elif adj_type == "add_hedge":
            hedge = adj.get("hedge_asset", "commodity")
            target = adj.get("target", 0.1)
            current = weights.get(hedge, 0)
            if current < target:
                deficit = target - current
                weights[hedge] = target
                # 从股票中扣除
                weights["stock"] = max(0, weights.get("stock", 0) - deficit)

    # 归一化确保总和为1
    total = sum(weights.values())
    if total > 0 and abs(total - 1.0) > 0.001:
        weights = {k: round(v / total, 4) for k, v in weights.items()}
    result["weights"] = weights
    result["rag_adjusted"] = True
    return result


def apply_risk_adjustments(risk_config: dict, adjustments: list[dict]) -> dict:
    """应用风控调节."""
    import copy
    result = copy.deepcopy(risk_config)

    for adj in adjustments:
        adj_type = adj.get("type", "")
        if adj_type == "stop_loss":
            result["stop_loss"] = adj["value"]
        elif adj_type == "max_drawdown":
            result["max_drawdown"] = adj["value"]
        elif adj_type == "max_position":
            result["max_position"] = adj["value"]

    result["rag_adjusted"] = True
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 主测试流程
# ─────────────────────────────────────────────────────────────────────────────

def run_scenario(scenario: TestScenario) -> PipelineReport:
    """运行单个测试场景."""
    print(f"\n{'='*80}")
    print(f"【场景】{scenario.name}")
    print(f"描述: {scenario.description}")
    print(f"{'='*80}")

    report = PipelineReport(
        scenario_name=scenario.name,
        scenario_description=scenario.description,
        timestamp=datetime.now().isoformat(),
    )
    pipeline_start = time.time()

    # ── Step 1: 问卷 → 画像向量 ──
    print("\n📋 Step 1: 问卷 → 画像向量")
    q_start = time.time()
    profile_vector = compute_profile_vector(scenario.answers)
    labels = derive_labels(profile_vector)
    q_end = time.time()
    report.questionnaire_duration_ms = (q_end - q_start) * 1000
    report.profile_vector = profile_vector
    report.labels = labels

    print(f"  耗时: {report.questionnaire_duration_ms:.1f}ms")
    print(f"  风险承受: {profile_vector['risk_tolerance']:.1f}/10 ({labels['risk_label']})")
    print(f"  损失厌恶: {profile_vector['loss_aversion']:.1f}/10")
    print(f"  投资期限: {profile_vector['time_horizon_score']:.1f}/10 ({labels['time_horizon_label']})")
    print(f"  经验水平: {profile_vector['experience_level']:.1f}/10 ({labels['experience_label']})")

    # ── Step 2: 市场信号 ──
    print("\n📊 Step 2: 市场信号")
    market_signal = generate_market_signal(scenario.market_scenario)
    report.market_signal = market_signal
    report.market_cycle = market_signal["cycle_phase"]
    print(f"  场景: {scenario.market_scenario}")
    print(f"  周期: {market_signal['cycle_phase']}")
    print(f"  宏观评分: {market_signal['macro_score']:.0%}")
    print(f"  VIX: {market_signal['vix']}")

    # ── Step 3: Hybrid组合设计 (带循环质检) ──
    print("\n🎯 Step 3: Hybrid组合设计 (带RAG循环质检)")

    # 初始化质检门控
    gate = MockQualityGate()

    # 3a. SAA计算
    from app.services.saa_engine import calculate_saa
    risk_level = get_risk_level_from_profile(profile_vector)
    saa_result = calculate_saa(
        risk_tolerance=risk_level,
        market_cycle=report.market_cycle,
        macro_score=market_signal["macro_score"],
        geo_risk=market_signal["geo_risk"],
    )
    print(f"\n  [SAA初始] 股票={saa_result['weights']['stock']:.1%}, "
          f"债券={saa_result['weights']['bond']:.1%}, "
          f"商品={saa_result['weights']['commodity']:.1%}")

    # 3b. SAA循环质检
    saa_result, saa_logs = run_loop_audit(
        "SAA", gate.review_saa, apply_saa_adjustments, 20,
        saa_result, profile_vector, market_signal,
    )
    report.steps.extend(saa_logs)

    print(f"  [SAA最终] 股票={saa_result['weights']['stock']:.1%}, "
          f"债券={saa_result['weights']['bond']:.1%}, "
          f"商品={saa_result['weights']['commodity']:.1%}")

    # 3c. TAA计算 (简化)
    from app.services.taa_engine import calculate_taa
    taa_result = calculate_taa(
        saa_weights=saa_result["weights"],
        market_cycle=report.market_cycle,
        industry_scores=market_signal["industry_scores"],
        social_trends=market_signal["social_trends"],
        market_signal=market_signal,
    )
    print(f"\n  [TAA] 行业配置完成")

    # 3d. 风控配置
    from app.services.hybrid_portfolio_designer_v2 import _generate_risk_config
    risk_config = _generate_risk_config(profile_vector, saa_result)
    print(f"\n  [风控初始] 止损={risk_config['stop_loss']:.1%}, "
          f"最大回撤={risk_config['max_drawdown']:.1%}")

    # 3e. 风控循环质检
    risk_config, risk_logs = run_loop_audit(
        "风控", gate.review_risk_config, apply_risk_adjustments, 20,
        risk_config, profile_vector,
    )
    report.steps.extend(risk_logs)

    print(f"  [风控最终] 止损={risk_config['stop_loss']:.1%}, "
          f"最大回撤={risk_config['max_drawdown']:.1%}")

    # 3f. 可靠性评估 (简化)
    reliability = {
        "confidence": 0.65,
        "backtest_available": True,
        "stress_test_available": True,
    }
    backtest_summary = {
        "portfolio_return": 12.5,
        "buy_hold_return": 10.0,
        "sharpe": 0.7,
        "max_drawdown": 0.15,
    }

    # 3g. 可靠性循环质检
    reliability, rel_logs = run_loop_audit(
        "可靠性", gate.review_reliability, lambda r, a: r, 20,
        reliability, backtest_summary,
    )
    report.steps.extend(rel_logs)

    # 3h. 最终审核
    portfolio = {
        "saa": saa_result,
        "taa": taa_result,
        "risk_config": risk_config,
        "reliability": reliability,
    }
    passed, _, _ = gate.final_review(portfolio, profile_vector)
    report.steps.extend(gate.step_logs[-1:])
    print(f"\n  [最终审核] {'✅通过' if passed else '❌不通过'}")

    # ── 组装报告 ──
    report.final_portfolio = portfolio
    report.risk_level = risk_level
    report.overall_passed = all(log.passed for log in report.steps if "尝试" in log.step_name)
    report.total_duration_ms = (time.time() - pipeline_start) * 1000

    # RAG统计
    attempt_steps = [s for s in report.steps if "尝试" in s.step_name]
    report.rag_stats = {
        "total_llm_calls": gate.call_count,
        "total_steps": len(attempt_steps),
        "passed_steps": sum(1 for s in attempt_steps if s.passed),
        "failed_steps": sum(1 for s in attempt_steps if not s.passed),
        "total_retries": sum(s.retry_count for s in attempt_steps),
        "total_adjustment_time_ms": sum(s.duration_ms for s in attempt_steps),
        "total_prompt_tokens": sum(s.llm_prompt_tokens for s in attempt_steps),
        "total_response_tokens": sum(s.llm_response_tokens for s in attempt_steps),
        "avg_llm_time_per_call_ms": sum(s.duration_ms for s in attempt_steps) / len(attempt_steps) if attempt_steps else 0,
    }

    return report


# ─────────────────────────────────────────────────────────────────────────────
# 报告输出
# ─────────────────────────────────────────────────────────────────────────────

def print_report(report: PipelineReport):
    """打印详细报告."""
    print(f"\n{'='*80}")
    print(f"📊 测试报告: {report.scenario_name}")
    print(f"{'='*80}")
    print(f"总耗时: {report.total_duration_ms:.1f}ms")
    print(f"问卷计算: {report.questionnaire_duration_ms:.1f}ms")
    print(f"\n画像标签:")
    print(f"  风险等级: {report.labels.get('risk_label', '未知')}")
    print(f"  投资期限: {report.labels.get('time_horizon_label', '未知')}")
    print(f"  经验水平: {report.labels.get('experience_label', '未知')}")

    print(f"\nRAG质检统计:")
    stats = report.rag_stats
    print(f"  LLM调用次数: {stats['total_llm_calls']}")
    print(f"  总审核步骤: {stats['total_steps']}")
    print(f"  通过: {stats['passed_steps']} | 未通过: {stats['failed_steps']}")
    print(f"  总重试次数: {stats['total_retries']}")
    print(f"  总调节耗时: {stats['total_adjustment_time_ms']:.1f}ms")
    print(f"  总Prompt Tokens: {stats.get('total_prompt_tokens', 0):,}")
    print(f"  总Response Tokens: {stats.get('total_response_tokens', 0):,}")
    print(f"  平均LLM耗时/次: {stats.get('avg_llm_time_per_call_ms', 0):.1f}ms")

    print(f"\n详细步骤日志:")
    for log in report.steps:
        if "尝试" not in log.step_name:
            continue
        status = "✅" if log.passed else "❌"
        print(f"  {status} {log.step_name}: "
              f"分数={log.score:.2f}, "
              f"耗时={log.duration_ms:.1f}ms, "
              f"重试={log.retry_count}, "
              f"Tokens={log.llm_prompt_tokens}+{log.llm_response_tokens}")
        if log.adjustment_strategy:
            print(f"     策略: {log.adjustment_strategy}")
        if log.issues:
            for issue in log.issues:
                print(f"     问题: {issue}")

    print(f"\n最终组合:")
    portfolio = report.final_portfolio
    saa = portfolio.get("saa", {})
    risk = portfolio.get("risk_config", {})
    print(f"  SAA: 股票={saa.get('weights', {}).get('stock', 0):.1%}, "
          f"债券={saa.get('weights', {}).get('bond', 0):.1%}")
    print(f"  风控: 止损={risk.get('stop_loss', 0):.1%}, "
          f"最大回撤={risk.get('max_drawdown', 0):.1%}")
    print(f"\n整体结果: {'✅通过' if report.overall_passed else '⚠️有未通过项'}")


def save_report(report: PipelineReport, output_dir: str = "./test_reports"):
    """保存报告到JSON文件."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    # 转换为可序列化的字典
    data = {
        "scenario_name": report.scenario_name,
        "scenario_description": report.scenario_description,
        "timestamp": report.timestamp,
        "total_duration_ms": report.total_duration_ms,
        "questionnaire_duration_ms": report.questionnaire_duration_ms,
        "profile_vector": report.profile_vector,
        "labels": report.labels,
        "risk_level": report.risk_level,
        "market_cycle": report.market_cycle,
        "market_signal": report.market_signal,
        "steps": [
            {
                "step_name": s.step_name,
                "duration_ms": s.duration_ms,
                "passed": s.passed,
                "score": s.score,
                "issues": s.issues,
                "adjustment_strategy": s.adjustment_strategy,
                "retry_count": s.retry_count,
            }
            for s in report.steps
        ],
        "rag_stats": report.rag_stats,
        "overall_passed": report.overall_passed,
    }

    filename = f"{output_dir}/report_{report.scenario_name}_{datetime.now().strftime('%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 报告已保存: {filename}")


# ─────────────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """运行所有测试场景."""
    print("=" * 80)
    print("QuantEvo 端到端全流程测试")
    print("测试路径: 问卷 → 画像 → 市场信号 → Hybrid组合设计 → RAG循环质检")
    print("=" * 80)

    all_reports = []
    summary = []

    for scenario in SCENARIOS:
        report = run_scenario(scenario)
        print_report(report)
        save_report(report)
        all_reports.append(report)

        summary.append({
            "场景": scenario.name,
            "风险等级": report.labels.get("risk_label", "未知"),
            "市场": scenario.market_scenario,
            "LLM调用": report.rag_stats["total_llm_calls"],
            "总重试": report.rag_stats["total_retries"],
            "通过": report.rag_stats["passed_steps"],
            "未通过": report.rag_stats["failed_steps"],
            "总耗时(s)": round(report.total_duration_ms / 1000, 1),
            "结果": "✅通过" if report.overall_passed else "⚠️有警告",
        })

    # 汇总表
    print(f"\n{'='*80}")
    print("📋 测试汇总")
    print(f"{'='*80}")
    print(f"{'场景':<20} {'风险等级':<8} {'市场':<8} {'LLM调用':<8} {'重试':<6} {'通过':<6} {'未通过':<8} {'耗时(s)':<10} {'结果'}")
    print("-" * 80)
    for s in summary:
        print(f"{s['场景']:<20} {s['风险等级']:<8} {s['市场']:<8} "
              f"{s['LLM调用']:<8} {s['总重试']:<6} {s['通过']:<6} "
              f"{s['未通过']:<8} {s['总耗时(s)']:<10} {s['结果']}")

    print(f"\n{'='*80}")
    print("✅ 所有场景测试完成!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
