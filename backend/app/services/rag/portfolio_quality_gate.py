"""组合质量门控 — RAG投资顾问作为质量总监.

在Hybrid组合引擎的每个阶段间进行控制、把关和调节.
"""

import json
import time
import asyncio
from typing import Any
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from .retriever_v2 import InvestmentRetriever, get_retriever_v2, InvestmentContext
from .llm_service import LLMService, get_llm_service
from .rag_call_logger import RAGCallLogger, get_rag_logger


class ReviewStep(Enum):
    """质检步骤."""

    SAA = "saa"
    TAA = "taa"
    BINDING = "binding"
    RISK_CONFIG = "risk_config"
    RELIABILITY = "reliability"
    FINAL = "final"


@dataclass
class RAGGateResult:
    """RAG质检结果."""

    step: str
    passed: bool
    score: float = 0.0
    issues: list[str] = field(default_factory=list)
    adjustments: list[dict] = field(default_factory=list)
    theory_cited: list[str] = field(default_factory=list)
    cases_cited: list[str] = field(default_factory=list)
    review_text: str = ""
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转为字典."""
        return {
            "step": self.step,
            "passed": self.passed,
            "score": self.score,
            "issues": self.issues,
            "adjustments": self.adjustments,
            "theory_cited": self.theory_cited,
            "cases_cited": self.cases_cited,
            "retry_count": self.retry_count,
        }


class PortfolioQualityGate:
    """组合质量门控 — RAG投资顾问作为质量总监."""

    # 各步骤最大重试次数（统一设为20次，确保充分调节）
    MAX_RETRIES = {
        ReviewStep.SAA: 20,
        ReviewStep.TAA: 20,
        ReviewStep.BINDING: 20,
        ReviewStep.RISK_CONFIG: 20,
        ReviewStep.RELIABILITY: 20,
        ReviewStep.FINAL: 20,
    }

    def __init__(
        self,
        retriever: InvestmentRetriever | None = None,
        llm_service: LLMService | None = None,
        logger: RAGCallLogger | None = None,
    ):
        self.retriever = retriever or get_retriever_v2()
        self.llm = llm_service or get_llm_service()
        self.logger = logger or get_rag_logger()

    # ------------------------------------------------------------------
    # Step 1: SAA 审核（市场信号驱动微调）
    # ------------------------------------------------------------------
    async def review_saa(
        self,
        saa_result: dict,
        profile_vector: dict,
        market_signal: dict,
    ) -> RAGGateResult:
        """审核SAA配置（结合市场信号微调）."""
        query = self._build_saa_review_query(saa_result, profile_vector, market_signal)

        # RAG检索
        context = await self.retriever.retrieve(query, query_type="组合构建")

        # LLM审核
        review = await self._llm_review("saa", query, context, saa_result)

        return self._parse_review(ReviewStep.SAA.value, review, saa_result)

    def _build_saa_review_query(
        self,
        saa_result: dict,
        profile: dict,
        market: dict,
    ) -> str:
        """构建SAA审核查询 - 优化版，明确风险上限，要求一次性调整到位."""
        weights = saa_result.get("weights", {})
        # profile_vector 中的值是 1-10，需要转换为 0-1
        risk_tolerance = profile.get("risk_tolerance", 5) / 10
        loss_aversion = profile.get("loss_aversion", 5) / 10
        risk_level_name = self._get_risk_level_name(risk_tolerance)

        # 确定股票上限
        if risk_tolerance < 0.3:
            stock_limit, risk_label = 0.30, "保守型"
        elif risk_tolerance < 0.6:
            stock_limit, risk_label = 0.50, "稳健型"
        elif risk_tolerance < 0.8:
            stock_limit, risk_label = 0.70, "积极型"
        else:
            stock_limit, risk_label = 0.90, "激进型"

        # 市场周期调整
        market_cycle = market.get("cycle_phase", "recovery")
        if market_cycle in ["contraction", "trough"]:
            stock_limit *= 0.85

        # 提取市场信号
        macro = market.get("macro", {})
        geo = market.get("geopolitical", {})
        market_internal = market.get("market_internal", {})
        geo_risk = geo.get("overall_risk", 50)

        return f"""你是一位资深资产配置专家。请严格审核以下战略资产配置方案。

## 用户画像（硬约束）
- 风险等级: {risk_label}（风险承受{risk_tolerance:.0%}）
- 损失厌恶: {loss_aversion:.0%}
- **股票权重上限: ≤{stock_limit:.0%}（不可突破）**
- 债券权重下限: ≥{max(0.05, 1 - stock_limit - 0.15):.0%}
- 现金权重下限: ≥3%

## 当前SAA方案（待审核）
- 股票: {weights.get('stock', 0):.0%}
- 债券: {weights.get('bond', 0):.0%}
- 商品: {weights.get('commodity', 0):.0%}
- 现金: {weights.get('cash', 0):.0%}

## 市场环境
- 周期: {macro.get('cycle_phase', '未知')}
- 宏观评分: {macro.get('score', 50)}/100
- 地缘政治风险: {geo_risk}/100
- VIX: {market_internal.get('vix', '未知')}
- 股债利差: {market_internal.get('equity_bond_spread', '未知')}%

## 审核规则（必须遵守）
1. **如果股票>{stock_limit:.0%}，必须一次性降至≤{stock_limit:.0%}**
2. 地缘风险>{geo_risk}时，商品应≥5%
3. 现金应≥3%保证流动性
4. 所有权重之和必须=100%
5. 债券是股票的主要替代，超额优先给债券

## 输出格式（严格JSON，必须可解析）
{{
    "passed": true/false,
    "adjusted_weights": {{
        "stock": 0.XX,
        "bond": 0.XX,
        "commodity": 0.XX,
        "cash": 0.XX
    }},
    "adjustment_reason": "简洁说明调整原因",
    "theory_cited": ["theory_markowitz"],
    "issues": ["问题描述"]
}}

注意：
- 如果方案已合理，passed=true，adjusted_weights与原始相同
- 如果方案不合理，passed=false，adjusted_weights给出修正后的权重
- 不要返回adjustments字段，只返回adjusted_weights"""

    # ------------------------------------------------------------------
    # Step 2: TAA 审核
    # ------------------------------------------------------------------
    async def review_taa(
        self,
        taa_result: dict,
        saa_result: dict,
        market_signal: dict,
    ) -> RAGGateResult:
        """审核TAA配置."""
        query = self._build_taa_review_query(taa_result, saa_result, market_signal)
        context = await self.retriever.retrieve(query, query_type="组合构建")
        review = await self._llm_review("taa", query, context, taa_result)
        return self._parse_review(ReviewStep.TAA.value, review, taa_result)

    def _build_taa_review_query(
        self,
        taa_result: dict,
        saa_result: dict,
        market: dict,
    ) -> str:
        """构建TAA审核查询."""
        sectors = taa_result.get("sector_weights", {})
        return f"""请审核以下战术资产配置方案：

SAA权重: {saa_result.get('weights', {})}
TAA行业配置: {sectors}
市场周期: {market.get('macro', {}).get('cycle_phase', '未知')}
行业景气度: {market.get('industry_scores', {})}

请检查：
1. 单一行业集中度是否≤50%
2. 成长/价值风格是否平衡
3. 超配行业估值是否合理
4. 小市值/低流动性占比是否≤20%

输出JSON格式：{{"passed": true/false, "issues": [], "adjustments": []}}"""

    # ------------------------------------------------------------------
    # Step 3: 绑定审核（回测驱动）
    # ------------------------------------------------------------------
    async def review_bindings(
        self,
        bindings: list[dict],
        profile_vector: dict,
        backtest_results: dict[str, dict],
    ) -> RAGGateResult:
        """审核策略-标的绑定（含回测验证，含买入持有基准硬约束）.

        Args:
            bindings: 绑定列表
            profile_vector: 用户画像
            backtest_results: 回测结果 {symbol: {return, buy_hold_return, sharpe, ...}}
        """
        # 1. 检查买入持有基准硬约束（4项）
        failed_bindings = []
        issues = []
        adjustments = []

        for binding in bindings:
            symbol = binding.get("symbol", "")
            bt = backtest_results.get(symbol, {})

            # 硬约束1: 策略累计收益 ≥ 买入持有收益
            passed_benchmark = bt.get("passed_benchmark", True)
            # 硬约束2: 超额收益α ≥ 0
            passed_alpha = bt.get("passed_alpha", True)
            # 硬约束3: 分年度检查通过
            passed_yearly = bt.get("passed_yearly", True)
            # 硬约束4: 最大相对回撤 ≤ 15%
            passed_relative_dd = bt.get("passed_relative_dd", True)

            if not all([passed_benchmark, passed_alpha, passed_yearly, passed_relative_dd]):
                failed_bindings.append({
                    "binding": binding,
                    "backtest": bt,
                    "failed_checks": {
                        "benchmark": passed_benchmark,
                        "alpha": passed_alpha,
                        "yearly": passed_yearly,
                        "relative_dd": passed_relative_dd,
                    },
                })

        if failed_bindings:
            issues.append(f"{len(failed_bindings)}个标的未通过买入持有基准校验")
            for fb in failed_bindings:
                symbol = fb["binding"].get("symbol", "")
                bt = fb["backtest"]
                failed_checks = fb["failed_checks"]
                if not failed_checks["benchmark"]:
                    issues.append(f"{symbol}: 跑输基准({bt.get('return', 0):.1f}% < {bt.get('benchmark_return', 0):.1f}%)")
                if not failed_checks["alpha"]:
                    issues.append(f"{symbol}: α<0({bt.get('alpha_return', 0):.1f}%)")
                if not failed_checks["yearly"]:
                    issues.append(f"{symbol}: 单年大幅跑输")
                if not failed_checks["relative_dd"]:
                    issues.append(f"{symbol}: 相对回撤超限({bt.get('max_relative_drawdown', 0):.1f}% > 15%)")

            # 生成排除调节建议
            adjustments.append({
                "type": "exclude_symbols",
                "symbols": [fb["binding"].get("symbol", "") for fb in failed_bindings],
                "reason": "未通过买入持有基准校验",
            })

        if not issues:
            # 全部通过
            return RAGGateResult(
                step=ReviewStep.BINDING.value,
                passed=True,
                score=0.9,
                issues=[],
                adjustments=[],
            )

        # 有绑定未通过，接入RAG分析第一个失败的
        failed = failed_bindings[0]
        query = self._build_binding_review_query(
            failed["binding"],
            failed["backtest"],
        )
        context = await self.retriever.retrieve(query, query_type="个股分析")
        review = await self._llm_review("binding", query, context, failed)
        result = self._parse_review(ReviewStep.BINDING.value, review, failed)

        # 合并硬约束检查的问题
        result.issues = issues + result.issues
        if adjustments:
            result.adjustments = adjustments + result.adjustments
        result.passed = False

        return result

    def _build_binding_review_query(
        self,
        binding: dict,
        backtest: dict,
    ) -> str:
        """构建绑定审核查询."""
        return f"""以下策略-标的绑定回测未通过，请分析原因并制定改进方案。

## 绑定信息
标的: {binding.get('symbol', '')} ({binding.get('name', '')})
策略: {binding.get('strategy_name', '')} ({binding.get('strategy_family', '')})
策略参数: {binding.get('strategy_params', {})}

## 回测结果（未通过）
策略收益: {backtest.get('return', 0):.2f}%
买入持有收益: {backtest.get('buy_hold_return', 0):.2f}%
超额收益: {backtest.get('return', 0) - backtest.get('buy_hold_return', 0):.2f}% (负数表示跑输)
夏普比率: {backtest.get('sharpe', 0):.2f}
最大回撤: {backtest.get('max_drawdown', 0):.2f}%
胜率: {backtest.get('win_rate', 0):.1f}%
交易次数: {backtest.get('trade_count', 0)}

## 市场环境
回测期: {backtest.get('period', '未知')}
市场周期: {backtest.get('market_cycle', '未知')}
波动率: {backtest.get('volatility', '未知')}

## 任务
1. 分析跑输买入持有的原因（至少3个）
2. 判断是参数问题、策略不匹配、还是标的选错
3. 给出具体改进方案（调参/换策略/换标的）
4. 改进方案必须具体，如"均线周期从5日改为20日"

## 输出格式（严格JSON）
{{
    "passed": false,
    "root_cause": "参数问题/策略不匹配/标的选错/市场环境",
    "failure_reasons": ["原因1", "原因2", "原因3"],
    "improvement_plan": {{
        "type": "调参/换策略/换标的",
        "specific_changes": "如'均线周期: 5→20'",
        "expected_effect": "说明为什么能改善"
    }},
    "alternative": {{
        "strategy": "替代策略名称",
        "symbol": "替代标的代码"
    }},
    "issues": ["跑输买入持有"]
}}"""

    # ------------------------------------------------------------------
    # Step 4: 风控审核
    # ------------------------------------------------------------------
    async def review_risk_config(
        self,
        risk_config: dict,
        profile_vector: dict,
    ) -> RAGGateResult:
        """审核风控配置."""
        query = self._build_risk_review_query(risk_config, profile_vector)
        context = await self.retriever.retrieve(query, query_type="概念解释")
        review = await self._llm_review("risk", query, context, risk_config)
        return self._parse_review(ReviewStep.RISK_CONFIG.value, review, risk_config)

    def _build_risk_review_query(
        self,
        risk_config: dict,
        profile: dict,
    ) -> str:
        """构建风控审核查询 - 优化版."""
        loss_aversion = profile.get('loss_aversion', 0.5)
        risk_tolerance = profile.get('risk_tolerance', 0.5)

        # 推断合理范围
        if loss_aversion > 0.7:
            suggest_stop = "3%-5%"
            suggest_drawdown = "8%-10%"
        elif loss_aversion > 0.4:
            suggest_stop = "5%-8%"
            suggest_drawdown = "10%-15%"
        else:
            suggest_stop = "8%-12%"
            suggest_drawdown = "15%-25%"

        if risk_tolerance > 0.7:
            suggest_position = "25%-30%"
        elif risk_tolerance > 0.4:
            suggest_position = "15%-20%"
        else:
            suggest_position = "10%-15%"

        return f"""你是一位资深风控专家。请审核以下风控配置是否与用户画像匹配。

## 用户画像
- 损失厌恶: {loss_aversion:.0%}（{'高' if loss_aversion > 0.7 else '中' if loss_aversion > 0.4 else '低'}）
- 风险承受: {risk_tolerance:.0%}（{'高' if risk_tolerance > 0.7 else '中' if risk_tolerance > 0.4 else '低'}）

## 当前风控配置（待审核）
- 止损线: {risk_config.get('stop_loss', 0):.1%}
- 单票仓位上限: {risk_config.get('max_position', 0):.1%}
- 最大回撤硬止损: {risk_config.get('max_drawdown', 0):.1%}
- 再平衡阈值: {risk_config.get('rebalance_threshold', 0):.1%}

## 参考标准
- 损失厌恶>70% → 止损{suggest_stop}，回撤{suggest_drawdown}
- 损失厌恶40-70% → 止损5%-8%，回撤10%-15%
- 风险承受>70% → 仓位上限{suggest_position}

## 审核规则
1. 止损线必须与损失厌恶匹配
2. 回撤硬止损必须与风险承受匹配
3. 单票仓位上限必须与风险承受匹配

## 输出格式（严格JSON）
{{
    "passed": true/false,
    "issues": ["问题描述"],
    "adjustments": [
        {{"type": "stop_loss", "value": 0.05}},
        {{"type": "max_drawdown", "value": 0.10}},
        {{"type": "max_position", "value": 0.20}}
    ],
    "theory_cited": ["theory_behavioral_finance"]
}}

注意：
- 如果配置合理，passed=true，adjustments为空
- 如果配置不合理，passed=false，adjustments必须包含具体的type和value
- 只调整确实不合理的参数，不要调整已合理的参数"""

    # ------------------------------------------------------------------
    # Step 5: 可靠性审核（严格标准）
    # ------------------------------------------------------------------
    async def review_reliability(
        self,
        reliability: dict,
        backtest_summary: dict,
        profile_vector: dict,
    ) -> RAGGateResult:
        """审核可靠性评估（严格标准，不降低门槛）."""
        query = self._build_reliability_review_query(
            reliability, backtest_summary, profile_vector
        )
        context = await self.retriever.retrieve(query, query_type="案例学习")
        review = await self._llm_review("reliability", query, context, reliability)
        return self._parse_review(ReviewStep.RELIABILITY.value, review, reliability)

    def _build_reliability_review_query(
        self,
        reliability: dict,
        backtest: dict,
        profile: dict,
    ) -> str:
        """构建可靠性审核查询（含买入持有基准硬约束）."""
        return f"""以下组合可靠性评估未通过，请分析原因并制定改进方案。

## 组合信息
标的数量: {backtest.get('n_assets', 0)}
策略绑定: {backtest.get('bindings', [])}

## 可靠性评估结果
组合收益: {backtest.get('portfolio_return', 0):.2f}%
买入持有收益: {backtest.get('buy_hold_return', 0):.2f}%
跑赢持有: {backtest.get('portfolio_return', 0) - backtest.get('buy_hold_return', 0):.2f}% (必须为正)
夏普比率: {backtest.get('sharpe', 0):.2f} (要求≥0.5)
最大回撤: {backtest.get('max_drawdown', 0):.2f}% (要求≤{profile.get('risk_tolerance', 0.5) * 30:.0f}%)
胜率: {backtest.get('win_rate', 0):.1f}% (要求≥40%)

## 买入持有基准校验（硬约束）
基准收益: {backtest.get('benchmark_return', 0):.2f}%
超额收益α: {backtest.get('alpha_return', 0):.2f}% (要求≥0)
超额收益夏普: {backtest.get('excess_sharpe', 0):.2f} (要求≥0.3)
通过基准校验数: {backtest.get('passed_benchmark_count', 0)}/{backtest.get('total_backtested', 0)}
通过α校验数: {backtest.get('passed_alpha_count', 0)}/{backtest.get('total_backtested', 0)}
全部通过基准: {backtest.get('all_passed_benchmark', False)}
全部通过α: {backtest.get('all_passed_alpha', False)}

## 压力测试
2022熊市表现: {backtest.get('bear_2022_return', '未知')}%
2020疫情表现: {backtest.get('covid_2020_return', '未知')}%

## 重要原则（不可违背）
1. **不允许降低通过标准**
2. **策略收益必须≥买入持有收益（硬约束）**
3. **超额收益α必须≥0（硬约束）**
4. **必须给出具体可执行的改进方案**
5. **如果当前组合无法通过，建议排除并重新构建**

## 任务
1. 分析未通过的具体原因
2. 判断是参数问题、策略选择问题、还是权重配置问题
3. 给出具体改进方案
4. **如果买入持有基准未通过，必须建议排除该标的并替换**

## 输出格式（严格JSON）
{{
    "passed": false,
    "failed_items": ["未通过项1", "未通过项2"],
    "root_causes": ["原因1", "原因2"],
    "improvement_plan": {{
        "type": "调参/换策略/调权重/重建",
        "specific_changes": "具体调整",
        "expected_effect": "预期改善"
    }},
    "exclusion_advice": {{
        "exclude": "排除的标的/策略",
        "alternative": "替代方案"
    }},
    "issues": ["问题1", "问题2"]
}}"""

    # ------------------------------------------------------------------
    # Step 6: 最终审核
    # ------------------------------------------------------------------
    async def final_review(
        self,
        portfolio: dict,
        profile_vector: dict,
        market_signal: dict,
    ) -> RAGGateResult:
        """最终组合审核."""
        query = self._build_final_review_query(portfolio, profile_vector, market_signal)
        context = await self.retriever.retrieve(query, query_type="组合构建")
        review = await self._llm_review("final", query, context, portfolio)
        return self._parse_review(ReviewStep.FINAL.value, review, portfolio)

    def _build_final_review_query(
        self,
        portfolio: dict,
        profile: dict,
        market: dict,
    ) -> str:
        """构建最终审核查询."""
        summary = portfolio.get("summary", {})
        return f"""请对以下最终组合进行综合审核：

## 组合摘要
{json.dumps(summary, ensure_ascii=False, indent=2)}

## 用户画像
风险等级: {self._get_risk_level_name(profile.get('risk_tolerance', 0.5))}
损失厌恶: {profile.get('loss_aversion', 0.5):.0%}

## 市场环境
周期: {market.get('macro', {}).get('cycle_phase', '未知')}

## 审核维度
1. 画像匹配度: 组合风险等级是否与画像一致
2. 市场适配度: 组合是否与当前市场周期适配
3. 可执行性: 标的是否为可交易的常见品种
4. 教育价值: 是否附带投资逻辑解释
5. 行为提醒: 高损失厌恶用户是否有止损提醒

输出JSON格式：{{"passed": true/false, "issues": [], "adjustments": []}}"""

    # ------------------------------------------------------------------
    # 并行质检方法
    # ------------------------------------------------------------------
    async def review_all_parallel(
        self,
        portfolio: dict,
        profile_vector: dict,
        market_signal: dict,
        backtest_results: dict[str, dict],
    ) -> dict[str, RAGGateResult]:
        """并行执行所有质检步骤.

        并行策略:
        - 批次1: SAA + 风控 (两者独立，都只依赖画像和市场)
        - 批次2: TAA + 绑定 (TAA依赖SAA结果，但绑定也独立)
        - 批次3: 可靠性 (依赖前面所有结果)
        - 批次4: 最终审核 (必须等所有前面完成)

        Args:
            portfolio: 完整组合配置
            profile_vector: 用户画像
            market_signal: 市场信号
            backtest_results: 回测结果

        Returns:
            {step: RAGGateResult}
        """
        results = {}

        # 批次1: SAA + 风控 (并行)
        saa_task = self.review_saa(
            portfolio.get("saa", {}), profile_vector, market_signal
        )
        risk_task = self.review_risk_config(
            portfolio.get("risk_config", {}), profile_vector
        )

        saa_result, risk_result = await asyncio.gather(saa_task, risk_task)
        results["saa"] = saa_result
        results["risk_config"] = risk_result

        # 批次2: TAA + 绑定 (并行，但TAA需要SAA结果)
        taa_task = self.review_taa(
            portfolio.get("taa", {}), portfolio.get("saa", {}), market_signal
        )
        binding_task = self.review_bindings(
            portfolio.get("bindings", []), profile_vector, backtest_results
        )

        taa_result, binding_result = await asyncio.gather(taa_task, binding_task)
        results["taa"] = taa_result
        results["binding"] = binding_result

        # 批次3: 可靠性 (依赖前面结果)
        reliability_result = await self.review_reliability(
            portfolio.get("reliability", {}),
            portfolio.get("backtest_summary", {}),
            profile_vector,
        )
        results["reliability"] = reliability_result

        # 批次4: 最终审核 (必须等所有完成)
        final_result = await self.final_review(
            portfolio, profile_vector, market_signal
        )
        results["final"] = final_result

        return results

    # ------------------------------------------------------------------
    # 通用方法
    # ------------------------------------------------------------------
    async def _llm_review(
        self,
        review_type: str,
        query: str,
        context: InvestmentContext,
        current_result: dict | list,
        portfolio_id: str = "",
        retry_count: int = 0,
    ) -> str:
        """调用LLM进行审核（带性能记录）."""
        # 构建上下文文本
        context_text = self._build_context_text(context)

        prompt = f"""{query}

## 参考资料
{context_text}

请基于以上资料进行审核。输出必须是严格的JSON格式。"""

        # 记录检索耗时
        retrieval_start = time.time()
        # 检索已在调用前完成，这里记录上下文构建时间
        retrieval_time_ms = (time.time() - retrieval_start) * 1000

        # 调用LLM
        llm_start = time.time()
        try:
            response = await self.llm.generate_async(
                prompt=prompt,
                system_prompt="你是一位资深投资顾问，负责审核投资组合的质量。请严格基于提供的资料进行审核，输出必须是JSON格式。",
            )
            llm_time_ms = (time.time() - llm_start) * 1000
            response_text = response.text
            error = None
        except Exception as e:
            llm_time_ms = (time.time() - llm_start) * 1000
            response_text = f'{{"passed": true, "issues": [], "adjustments": [], "error": "{str(e)}"}}'
            error = str(e)

        # 解析耗时
        parse_start = time.time()
        result = self._parse_review(review_type, response_text)
        parse_time_ms = (time.time() - parse_start) * 1000

        # 记录调用
        self.logger.log_call(
            step=review_type,
            portfolio_id=portfolio_id,
            prompt=prompt,
            response=response_text,
            passed=result.passed,
            score=result.score,
            issues=result.issues,
            adjustments=result.adjustments,
            retrieval_time_ms=retrieval_time_ms,
            llm_time_ms=llm_time_ms,
            parse_time_ms=parse_time_ms,
            retry_count=retry_count,
            error=error,
        )

        return response_text

    def _build_context_text(self, context: InvestmentContext) -> str:
        """构建上下文文本."""
        parts = []

        if context.stock_cases:
            parts.append("## 个股案例")
            for r in context.stock_cases[:3]:
                parts.append(f"- [{r.id}] {r.text[:200]}...")

        if context.valuation_cases:
            parts.append("## 估值案例")
            for r in context.valuation_cases[:2]:
                parts.append(f"- [{r.id}] {r.text[:200]}...")

        if context.theories:
            parts.append("## 资产配置理论")
            for r in context.theories[:2]:
                parts.append(f"- [{r.id}] {r.text[:200]}...")

        if context.basics:
            parts.append("## 基础常识")
            for r in context.basics[:2]:
                parts.append(f"- [{r.id}] {r.text[:200]}...")

        if context.behavioral_cases:
            parts.append("## 行为金融")
            for r in context.behavioral_cases[:2]:
                parts.append(f"- [{r.id}] {r.text[:200]}...")

        if context.paper_chunks:
            parts.append("## 论文研究")
            for r in context.paper_chunks[:2]:
                parts.append(f"- [{r.id}] {r.text[:200]}...")

        return "\n".join(parts)

    def _parse_review(self, step: str, review_text: str, current_result: dict | None = None) -> RAGGateResult:
        """解析LLM审核结果，支持自动推断调节策略.

        Args:
            step: 审核步骤
            review_text: LLM返回的文本
            current_result: 当前结果（用于自动推断调节）
        """
        try:
            # 尝试提取JSON
            json_start = review_text.find("{")
            json_end = review_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = review_text[json_start:json_end]
                data = json.loads(json_str)
            else:
                data = {}
        except json.JSONDecodeError:
            data = {}

        passed = data.get("passed", data.get("needs_adjustment", True) is False)
        if "通过" in review_text[:200] and not passed:
            passed = True
        issues = data.get("issues", [])
        adjustments = data.get("adjustments", [])

        # === 自动推断调节策略 ===
        if current_result is not None:
            # 1. 优先从 adjusted_weights 直接设置权重 (最可靠)
            adjusted_weights = data.get("adjusted_weights", {})
            if adjusted_weights and step == ReviewStep.SAA.value:
                current_weights = current_result.get("weights", {})
                has_changes = False
                for asset, new_val in adjusted_weights.items():
                    old_val = current_weights.get(asset, 0)
                    if abs(new_val - old_val) > 0.001:
                        has_changes = True
                        break
                if has_changes:
                    # 使用 set_weights 一次性设置所有权重，避免cap/floor矛盾
                    adjustments = [{
                        "type": "set_weights",
                        "weights": adjusted_weights,
                    }]
                    passed = False  # 有调整就是不通过
                    issues = issues or ["权重需要调整"]

            # 2. 从 issues 文本推断 (备用)
            if not passed and not adjustments and issues:
                adjustments = self._infer_adjustments_from_issues(step, issues, current_result, review_text)

        # 提取理论引用
        theory_cited = data.get("theory_cited", [])
        if not theory_cited and "theory_" in review_text:
            import re
            theory_cited = re.findall(r"theory_\w+", review_text)

        # 提取案例引用
        cases_cited = data.get("cases_cited", [])
        if not cases_cited:
            import re
            cases_cited = re.findall(r"(?:case_|stock_|behavior_)[\w_]+", review_text)

        # 计算分数
        score = 0.9 if passed else 0.4
        if issues:
            score -= len(issues) * 0.1

        return RAGGateResult(
            step=step,
            passed=passed,
            score=max(0, score),
            issues=issues,
            adjustments=adjustments,
            theory_cited=list(set(theory_cited))[:5],
            cases_cited=list(set(cases_cited))[:5],
            review_text=review_text[:2000],
        )

    def _infer_adjustments_from_issues(self, step: str, issues: list[str], current_result: dict, review_text: str) -> list[dict]:
        """从问题描述自动推断调节策略.

        Args:
            step: 审核步骤
            issues: 问题列表
            current_result: 当前结果
            review_text: 完整审核文本

        Returns:
            推断出的调节建议列表
        """
        adjustments = []
        review_lower = review_text.lower()
        issues_text = " ".join(issues).lower()

        # === SAA 调节推断 ===
        if step == ReviewStep.SAA.value:
            weights = current_result.get("weights", {})
            stock_pct = weights.get("stock", 0)
            bond_pct = weights.get("bond", 0)
            commodity_pct = weights.get("commodity", 0)
            cash_pct = weights.get("cash", 0)

            # 股票权重过高
            if any(k in issues_text for k in ["股票", "stock", "权益", "过高", "太多", "风险"]):
                # 从文本中提取建议的百分比
                import re
                # 查找 "X%" 或 "XX%" 格式
                pct_matches = re.findall(r'(\d+)%', review_text)
                target_stock = None
                for pct_str in pct_matches:
                    pct = int(pct_str) / 100
                    if 0.1 <= pct <= 0.9 and pct < stock_pct:
                        target_stock = pct
                        break

                if target_stock is None:
                    # 默认降低到合理范围
                    if stock_pct > 0.7:
                        target_stock = 0.60
                    elif stock_pct > 0.5:
                        target_stock = 0.45
                    elif stock_pct > 0.3:
                        target_stock = 0.25
                    else:
                        target_stock = stock_pct * 0.9

                if target_stock < stock_pct:
                    excess = stock_pct - target_stock
                    adjustments.append({
                        "type": "weight_cap",
                        "asset": "stock",
                        "cap": round(target_stock, 4),
                    })
                    # 超额给债券
                    adjustments.append({
                        "type": "weight_floor",
                        "asset": "bond",
                        "floor": round(bond_pct + excess, 4),
                    })

            # 现金过低
            if any(k in issues_text for k in ["现金", "cash", "流动性", "过低"]):
                if cash_pct < 0.05:
                    target_cash = 0.05
                    deficit = target_cash - cash_pct
                    adjustments.append({
                        "type": "weight_floor",
                        "asset": "cash",
                        "floor": target_cash,
                    })
                    # 从股票中扣除
                    if stock_pct > deficit:
                        adjustments.append({
                            "type": "weight_cap",
                            "asset": "stock",
                            "cap": round(stock_pct - deficit, 4),
                        })

            # 商品/避险资产不足
            if any(k in issues_text for k in ["商品", "commodity", "避险", "对冲", "黄金"]):
                if commodity_pct < 0.05:
                    adjustments.append({
                        "type": "add_hedge",
                        "hedge_asset": "commodity",
                        "target": 0.10,
                    })

        # === 风控调节推断 ===
        elif step == ReviewStep.RISK_CONFIG.value:
            stop_loss = current_result.get("stop_loss", 0.08)
            max_drawdown = current_result.get("max_drawdown", 0.15)

            # 止损过宽
            if any(k in issues_text for k in ["止损", "stop", "过宽", "过松", "太宽"]):
                if stop_loss > 0.08:
                    adjustments.append({
                        "type": "stop_loss",
                        "value": 0.07,
                    })
                elif stop_loss > 0.05:
                    adjustments.append({
                        "type": "stop_loss",
                        "value": 0.05,
                    })

            # 回撤过大
            if any(k in issues_text for k in ["回撤", "drawdown", "过大"]):
                if max_drawdown > 0.15:
                    adjustments.append({
                        "type": "max_drawdown",
                        "value": 0.15,
                    })
                elif max_drawdown > 0.10:
                    adjustments.append({
                        "type": "max_drawdown",
                        "value": 0.10,
                    })

        # === TAA 调节推断 ===
        elif step == ReviewStep.TAA.value:
            # 行业集中度过高
            if any(k in issues_text for k in ["集中", "集中度过高", "单一行业"]):
                adjustments.append({
                    "type": "sector_cap",
                    "sector": "max_sector",
                    "cap": 0.5,
                })

        return adjustments

    @staticmethod
    def _get_risk_level_name(risk_tolerance: float) -> str:
        """获取风险等级名称."""
        if risk_tolerance < 0.3:
            return "保守"
        elif risk_tolerance < 0.6:
            return "稳健"
        elif risk_tolerance < 0.8:
            return "积极"
        else:
            return "激进"


# 全局实例
_quality_gate_instance: PortfolioQualityGate | None = None


def get_quality_gate() -> PortfolioQualityGate:
    """获取全局质量门控实例."""
    global _quality_gate_instance
    if _quality_gate_instance is None:
        _quality_gate_instance = PortfolioQualityGate()
    return _quality_gate_instance
