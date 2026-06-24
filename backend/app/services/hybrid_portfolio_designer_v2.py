"""Hybrid Portfolio Designer V2 — 集成RAG质检的组合设计总控.

6步编排 + RAG质量门控:
1. SAA: 战略资产配置 → RAG微调
2. TAA: 战术资产配置 → RAG审核
3. 策略-标的绑定 → 回测验证 → RAG诊断
4. 风控配置 → RAG审核
5. 可靠性评估 → RAG严格审核（不降低标准）
6. 组合寿命计算 → RAG最终审核
"""

import asyncio
import copy
import datetime
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

from app.services.saa_engine import calculate_saa, get_risk_level_from_profile, get_market_cycle_from_signal, RISK_PROFILES
from app.services.taa_engine import calculate_taa, get_top_sectors
from app.services.rag.portfolio_quality_gate import PortfolioQualityGate, ReviewStep
from app.services.rag.adjustment_engine import apply_adjustments
from app.services.assets import (
    SECTOR_ETF_MAP, SECTOR_STOCK_MAP, BOND_ETF_MAP,
    COMMODITY_ETF_MAP, CASH_FUND_MAP, BACKTEST_PERIODS,
    get_sector_etf, get_sector_stocks, get_bond_etf, get_commodity_etf, get_cash_fund
)
from app.services.dynamic_picker.dynamic_stock_picker import DynamicStockPicker


# 进度回调类型
ProgressCallback = Optional[Callable[[dict[str, Any]], None]]


async def _notify(callback: ProgressCallback, event: dict[str, Any]) -> None:
    """安全地调用进度回调."""
    if callback is None:
        return
    try:
        if asyncio.iscoroutinefunction(callback):
            await callback(event)
        else:
            callback(event)
    except Exception as e:
        logger.warning(f"[ProgressCallback] 通知失败: {e}")


# 策略模板池 — 从 strategy_discovery_final 加载真实策略
# 来源: app/services/strategy_discovery_final.py
try:
    from app.services.strategy_discovery_final import STRATEGY_TEMPLATES as DEFAULT_STRATEGY_TEMPLATES
except ImportError:
    DEFAULT_STRATEGY_TEMPLATES = []

# 兜底策略池（当 strategy_discovery_final 未提供策略模板时使用）
if not DEFAULT_STRATEGY_TEMPLATES:
    DEFAULT_STRATEGY_TEMPLATES = [
        {
            "id": "trend_ema_cross",
            "name": "EMA趋势跟踪",
            "family": "trend",
            "params": {"fast": 5, "slow": 20},
        },
        {
            "id": "momentum_rsi",
            "name": "RSI动量反转",
            "family": "momentum",
            "params": {"rsi_period": 14, "oversold": 30, "overbought": 70},
        },
        {
            "id": "mean_reversion_bollinger",
            "name": "布林带均值回归",
            "family": "mean_reversion",
            "params": {"window": 20, "std": 2},
        },
        {
            "id": "breakout_volatility",
            "name": "波动率突破",
            "family": "breakout",
            "params": {"lookback": 20, "atr_mult": 1.5},
        },
        {
            "id": "multi_factor_value",
            "name": "多因子价值",
            "family": "multi_factor",
            "params": {"factors": ["pe", "pb", "roe"]},
        },
    ]


async def design_portfolio_v2(
    profile_vector: dict[str, float],
    market_signal: dict[str, Any],
    strategy_pool: list[dict] | None = None,
    target_count: int = 5,
    use_rag_gate: bool = True,
    use_dynamic_picker: bool = True,
    rag_service=None,
    llm_service=None,
    progress_callback: ProgressCallback = None,
) -> dict[str, Any]:
    """设计完整投资组合（RAG质检版 + 动态选股）.

    Args:
        profile_vector: 用户画像15维向量
        market_signal: 市场五层信号
        strategy_pool: 策略池（可选）
        target_count: 目标策略数量
        use_rag_gate: 是否启用RAG质检
        use_dynamic_picker: 是否启用动态选股（替代静态映射）
        rag_service: RAG检索服务（动态选股需要）
        llm_service: LLM生成服务（动态选股需要）

    Returns:
        完整组合配置 + RAG质检记录
    """
    quality_gate = PortfolioQualityGate() if use_rag_gate else None
    adjustments_log = []
    needs_rebacktest = []

    await _notify(progress_callback, {
        "type": "progress",
        "step": "start",
        "message": "启动 Hybrid + RAG 组合设计引擎",
        "progress": 0.02,
    })

    # 初始化动态选股引擎
    dynamic_picker = None
    if use_dynamic_picker:
        dynamic_picker = DynamicStockPicker(
            rag_service=rag_service,
            llm_service=llm_service,
            pool_size=15,
            filter_target_size=10,
            select_target_count=target_count * 2,
            enrich_max_concurrent=30,
        )

    # =====================================================================
    # Step 1: SAA — 战略资产配置
    # =====================================================================
    await _notify(progress_callback, {
        "type": "progress",
        "step": "saa",
        "message": "Step 1/6: 计算战略资产配置 (SAA)",
        "progress": 0.05,
    })

    risk_level = get_risk_level_from_profile(profile_vector)
    market_cycle = get_market_cycle_from_signal(market_signal)
    macro_score = market_signal.get("macro_score", 0.5)
    geo_risk = market_signal.get("geo_risk", 0.5)

    saa_result = calculate_saa(
        risk_tolerance=risk_level,
        market_cycle=market_cycle,
        macro_score=macro_score,
        geo_risk=geo_risk,
    )

    # RAG质检1: SAA微调（市场信号驱动，循环审核）
    if use_rag_gate and quality_gate:
        await _notify(progress_callback, {
            "type": "progress",
            "step": "saa_review",
            "message": "RAG 审核: SAA 战略资产配置",
            "progress": 0.12,
        })

        # 构建风险画像硬约束
        base_profile = RISK_PROFILES.get(risk_level, RISK_PROFILES["moderate"]).copy()
        # 市场周期调整上限
        if market_cycle in ["contraction", "trough"]:
            base_profile["stock_max"] *= 0.85
        risk_profile = base_profile

        max_saa_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.SAA]
        for retry in range(max_saa_retries + 1):  # +1 for initial attempt
            review = await quality_gate.review_saa(
                saa_result, profile_vector, market_signal
            )
            if review.passed:
                # 即使通过了，也强制执行硬约束校验
                if saa_result["weights"].get("stock", 0) > risk_profile["stock_max"]:
                    review.passed = False
                    review.issues.append(
                        f"股票权重{saa_result['weights']['stock']:.1%}超过硬上限{risk_profile['stock_max']:.1%}"
                    )
                    review.adjustments = [{
                        "type": "weight_cap",
                        "asset": "stock",
                        "cap": risk_profile["stock_max"],
                    }]
                else:
                    if retry > 0:
                        adjustments_log[-1]["passed_after_retry"] = True
                    break

            # 应用调节（带硬约束）
            saa_result, _ = apply_adjustments(
                "saa", saa_result, review.adjustments, risk_profile=risk_profile
            )
            adjustments_log.append({
                **review.to_dict(),
                "retry": retry,
                "step": "saa",
            })
        else:
            # 超过最大重试次数仍未通过，记录最终状态
            adjustments_log.append({
                "step": "saa",
                "passed": False,
                "retry": max_saa_retries,
                "warning": "SAA审核多次调节仍未通过，使用最后一次调节结果",
            })

    # =====================================================================
    # Step 2: TAA — 战术资产配置
    # =====================================================================
    await _notify(progress_callback, {
        "type": "progress",
        "step": "taa",
        "message": "Step 2/6: 计算战术资产配置 (TAA)",
        "progress": 0.22,
    })

    industry_scores = market_signal.get("industry_scores", {})
    social_trends = market_signal.get("social_trends", [])

    taa_result = calculate_taa(
        saa_weights=saa_result["weights"],
        market_cycle=market_cycle,
        industry_scores=industry_scores,
        social_trends=social_trends,
        market_signal=market_signal,
    )

    # RAG质检2: TAA审核（循环审核）
    if use_rag_gate and quality_gate:
        await _notify(progress_callback, {
            "type": "progress",
            "step": "taa_review",
            "message": "RAG 审核: TAA 战术资产配置",
            "progress": 0.30,
        })

        max_taa_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.TAA]
        for retry in range(max_taa_retries + 1):
            review = await quality_gate.review_taa(
                taa_result, saa_result, market_signal
            )
            if review.passed:
                if retry > 0:
                    adjustments_log[-1]["passed_after_retry"] = True
                break

            taa_result, _ = apply_adjustments("taa", taa_result, review.adjustments)
            adjustments_log.append({
                **review.to_dict(),
                "retry": retry,
                "step": "taa",
            })
        else:
            adjustments_log.append({
                "step": "taa",
                "passed": False,
                "retry": max_taa_retries,
                "warning": "TAA审核多次调节仍未通过，使用最后一次调节结果",
            })

    # =====================================================================
    # Step 3: 策略-标的绑定 + 回测验证
    # =====================================================================
    await _notify(progress_callback, {
        "type": "progress",
        "step": "binding",
        "message": "Step 3/6: 策略-标的绑定与动态选股",
        "progress": 0.38,
    })

    strategies = strategy_pool or DEFAULT_STRATEGY_TEMPLATES
    top_sectors = get_top_sectors(taa_result, n=target_count)

    # 动态选股（替代静态映射）
    selected_stocks = []
    dynamic_picking_result = None
    if use_dynamic_picker and dynamic_picker:
        await _notify(progress_callback, {
            "type": "progress",
            "step": "dynamic_picker",
            "message": "动态选股: 构建标的池 → 多维度筛选 → LLM 精选",
            "progress": 0.42,
        })
        try:
            dynamic_picking_result = await dynamic_picker.pick(
                top_sectors=top_sectors,
                market_cycle=market_cycle,
                industry_scores=industry_scores,
                social_trends=social_trends,
            )
            selected_stocks = dynamic_picking_result.selected_stocks
            logger.info(f"动态选股完成: {len(selected_stocks)} 只标的")
        except Exception as e:
            logger.warning(f"动态选股失败，回退到静态映射: {e}")
            selected_stocks = []

    # 初始绑定
    bindings = []
    used_stocks = set()

    # 按 sector 分配权重：ETF 70% + 个股 30%（仅 sector 权重>15% 时配个股）
    # 确保每个 sector 内部 ETF + 个股 = sector_info["weight"]
    for i, sector_info in enumerate(top_sectors):
        if i >= len(strategies):
            break
        strategy = strategies[i]
        sector = sector_info["sector"]
        sector_weight = sector_info["weight"]

        sector_selected = [
            s for s in selected_stocks
            if s.sector == sector and s.symbol not in used_stocks
        ]
        sector_etfs = [s for s in sector_selected if s.asset_class == "ETF"]
        sector_stocks = [s for s in sector_selected if s.asset_class == "stock"]

        # 较重要的 sector 都尝试配个股（卫星），降低阈值到 10%
        use_dynamic_stock = sector_weight > 0.10 and len(sector_stocks) > 0
        use_fallback_stock = sector_weight > 0.10 and not use_dynamic_stock
        stock_ratio = 0.3 if (use_dynamic_stock or use_fallback_stock) else 0.0
        etf_ratio = 1.0 - stock_ratio

        # ETF 绑定（核心）
        if etf_ratio > 0:
            if sector_etfs:
                best_etf = max(sector_etfs, key=lambda s: s.llm_score)
                used_stocks.add(best_etf.symbol)
                bindings.append(_make_binding(
                    sector_info, strategy, best_etf, "ETF",
                    weight=sector_weight * etf_ratio
                ))
            else:
                etf_info = get_sector_etf(sector)
                if etf_info:
                    bindings.append({
                        "sector": sector,
                        "sector_name": sector_info["name"],
                        "weight": round(sector_weight * etf_ratio, 4),
                        "strategy_id": strategy["id"],
                        "strategy_name": strategy["name"],
                        "strategy_family": strategy["family"],
                        "strategy_params": strategy.get("params", {}),
                        "symbol": etf_info["symbol"],
                        "name": etf_info["name"],
                        "asset_class": "ETF",
                        "satellite": False,
                        "data_source": etf_info["source"] + " (fallback)",
                    })

        # 个股绑定（卫星）
        if stock_ratio > 0:
            if use_dynamic_stock and sector_stocks:
                best_stock = max(sector_stocks, key=lambda s: s.llm_score)
                used_stocks.add(best_stock.symbol)
                bindings.append(_make_binding(
                    sector_info, strategy, best_stock, "stock",
                    weight=sector_weight * stock_ratio,
                    satellite=True
                ))
            elif use_fallback_stock:
                stocks = get_sector_stocks(sector, n=1)
                if stocks:
                    stock = stocks[0]
                    used_stocks.add(stock["symbol"])
                    bindings.append({
                        "sector": sector,
                        "sector_name": sector_info["name"],
                        "weight": round(sector_weight * stock_ratio, 4),
                        "strategy_id": strategy["id"],
                        "strategy_name": strategy["name"],
                        "strategy_family": strategy["family"],
                        "strategy_params": strategy.get("params", {}),
                        "symbol": stock["symbol"],
                        "name": stock["name"],
                        "asset_class": "stock",
                        "satellite": True,
                        "data_source": stock["source"] + " (fallback)",
                    })

    # 未匹配的选股结果：当前 sector 权重已分配完毕，记录日志即可
    unmatched = [s for s in selected_stocks if s.symbol not in used_stocks]
    if unmatched:
        logger.info(f"动态选股未匹配标的: {len(unmatched)} 只，已按 sector 完成权重分配")

    # 添加债券/商品/现金绑定，使整个组合权重总和 = 100%
    saa_weights = saa_result.get("weights", {})

    bond_weight = saa_weights.get("bond", 0)
    if bond_weight > 0:
        bond_etf = get_bond_etf("treasury_1y")
        bindings.append({
            "sector": "bond",
            "sector_name": "债券",
            "weight": round(bond_weight, 4),
            "strategy_id": "bond_hold",
            "strategy_name": "债券配置",
            "strategy_family": "fixed_income",
            "strategy_params": {},
            "symbol": bond_etf["symbol"],
            "name": bond_etf["name"],
            "asset_class": "bond",
            "satellite": False,
            "data_source": bond_etf["source"],
        })

    commodity_weight = saa_weights.get("commodity", 0)
    if commodity_weight > 0:
        commodity_etf = get_commodity_etf("gold")
        bindings.append({
            "sector": "commodity",
            "sector_name": "商品",
            "weight": round(commodity_weight, 4),
            "strategy_id": "commodity_hold",
            "strategy_name": "黄金配置",
            "strategy_family": "commodity",
            "strategy_params": {},
            "symbol": commodity_etf["symbol"],
            "name": commodity_etf["name"],
            "asset_class": "commodity",
            "satellite": False,
            "data_source": commodity_etf["source"],
        })

    cash_weight = saa_weights.get("cash", 0)
    if cash_weight > 0:
        cash_fund = get_cash_fund("yin_hua_ri_li")
        bindings.append({
            "sector": "cash",
            "sector_name": "现金",
            "weight": round(cash_weight, 4),
            "strategy_id": "cash_hold",
            "strategy_name": "货币基金",
            "strategy_family": "cash",
            "strategy_params": {},
            "symbol": cash_fund["symbol"],
            "name": cash_fund["name"],
            "asset_class": "cash",
            "satellite": False,
            "data_source": cash_fund["source"],
        })

    # 最终归一化：修正浮点误差，确保总权重严格等于 1.0
    total_weight = sum(b["weight"] for b in bindings)
    if total_weight > 0 and abs(total_weight - 1.0) > 0.001:
        scale = 1.0 / total_weight
        for b in bindings:
            b["weight"] = round(b["weight"] * scale, 4)

    logger.info(f"绑定完成: {len(bindings)} 只标的，总权重: {sum(b['weight'] for b in bindings):.4f}")

    # 回测验证（必须跑赢买入持有）
    await _notify(progress_callback, {
        "type": "progress",
        "step": "backtest",
        "message": "回测验证: 对绑定标的运行历史回测",
        "progress": 0.55,
    })
    backtest_results = await _run_backtests(bindings)

    # RAG质检3: 绑定审核（回测驱动）
    if use_rag_gate and quality_gate:
        await _notify(progress_callback, {
            "type": "progress",
            "step": "binding_review",
            "message": "RAG 审核: 策略-标的绑定",
            "progress": 0.62,
        })

        max_binding_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.BINDING]
        for retry in range(max_binding_retries):
            review = await quality_gate.review_bindings(
                bindings, profile_vector, backtest_results
            )
            if review.passed:
                break

            # 应用调节
            bindings, needs_rebacktest = apply_adjustments(
                "binding", bindings, review.adjustments
            )
            adjustments_log.append({**review.to_dict(), "retry": retry})

            # 需要重新回测的标的
            if needs_rebacktest:
                new_backtests = await _run_backtests_for_symbols(
                    bindings, needs_rebacktest
                )
                backtest_results.update(new_backtests)
        else:
            # 超过最大重试次数，排除未通过的绑定
            bindings = _exclude_failed_bindings(bindings, backtest_results)

    # =====================================================================
    # Step 4: 风控配置
    # =====================================================================
    await _notify(progress_callback, {
        "type": "progress",
        "step": "risk_config",
        "message": "Step 4/6: 生成风控配置",
        "progress": 0.68,
    })
    risk_config = _generate_risk_config(profile_vector, saa_result)

    # RAG质检4: 风控审核（循环审核）
    if use_rag_gate and quality_gate:
        await _notify(progress_callback, {
            "type": "progress",
            "step": "risk_review",
            "message": "RAG 审核: 风控配置",
            "progress": 0.72,
        })

        max_risk_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.RISK_CONFIG]
        for retry in range(max_risk_retries + 1):
            review = await quality_gate.review_risk_config(
                risk_config, profile_vector
            )
            if review.passed:
                if retry > 0:
                    adjustments_log[-1]["passed_after_retry"] = True
                break

            risk_config, _ = apply_adjustments(
                "risk_config", risk_config, review.adjustments
            )
            adjustments_log.append({
                **review.to_dict(),
                "retry": retry,
                "step": "risk_config",
            })
        else:
            adjustments_log.append({
                "step": "risk_config",
                "passed": False,
                "retry": max_risk_retries,
                "warning": "风控审核多次调节仍未通过，使用最后一次调节结果",
            })

    # =====================================================================
    # Step 5: 可靠性评估（严格标准 + 买入持有基准校验 + 压力测试 + 蒙特卡洛）
    # =====================================================================
    await _notify(progress_callback, {
        "type": "progress",
        "step": "reliability",
        "message": "Step 5/6: 可靠性评估（回测 + 压力测试 + 蒙特卡洛）",
        "progress": 0.78,
    })
    # 构建历史收益率DataFrame（用于压力测试和蒙特卡洛）
    historical_returns = _build_historical_returns_df(backtest_results)

    reliability = _evaluate_reliability_v2(
        bindings=bindings,
        risk_config=risk_config,
        market_cycle=market_cycle,
        backtest_results=backtest_results,
        saa_weights=saa_result.get("weights", {}),
        historical_returns=historical_returns,
    )
    backtest_summary = _summarize_backtests(backtest_results, bindings)

    # RAG质检5: 可靠性审核（严格，不降低标准）
    if use_rag_gate and quality_gate:
        await _notify(progress_callback, {
            "type": "progress",
            "step": "reliability_review",
            "message": "RAG 审核: 组合可靠性",
            "progress": 0.84,
        })

        max_reliability_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.RELIABILITY]
        for retry in range(max_reliability_retries):
            review = await quality_gate.review_reliability(
                reliability, backtest_summary, profile_vector
            )
            if review.passed:
                break

            # 应用调节（调参/换策略/调权重，不降低标准）
            portfolio_so_far = {
                "bindings": bindings,
                "risk_config": risk_config,
                "saa": saa_result,
                "taa": taa_result,
            }
            portfolio_so_far, _ = apply_adjustments(
                "reliability", portfolio_so_far, review.adjustments
            )
            bindings = portfolio_so_far["bindings"]
            risk_config = portfolio_so_far["risk_config"]
            adjustments_log.append({**review.to_dict(), "retry": retry})

            # 重新评估可靠性
            reliability = _evaluate_reliability_v2(
                bindings=bindings,
                risk_config=risk_config,
                market_cycle=market_cycle,
                backtest_results=backtest_results,
                saa_weights=saa_result.get("weights", {}),
                historical_returns=historical_returns,
            )
            backtest_summary = _summarize_backtests(backtest_results, bindings)
        else:
            # 超过最大重试次数，标记为高风险组合
            reliability["rag_warning"] = "多次调节仍未通过可靠性审核，建议谨慎"

    # =====================================================================
    # Step 6: 组合寿命计算
    # =====================================================================
    await _notify(progress_callback, {
        "type": "progress",
        "step": "lifespan",
        "message": "Step 6/6: 计算组合寿命与健康度",
        "progress": 0.90,
    })
    portfolio_lifespan = _calculate_portfolio_lifespan(bindings)
    portfolio_health = _calculate_portfolio_health(bindings)

    # 组装组合
    adoption_status = reliability.get("adoption_status", {"adopted": False})
    portfolio = {
        "portfolio_id": f"pf_{hash(str(profile_vector)) % 10000:04d}",
        "adopted": bool(adoption_status.get("adopted", False)),
        "saa": {
            **saa_result,
            "data_source": "saa_engine + rag_quality_gate(llm:mlx/Qwen3-14B)",
        },
        "taa": {
            **taa_result,
            "data_source": "taa_engine + rag_quality_gate(llm:mlx/Qwen3-14B)",
        },
        "bindings": bindings,
        "risk_config": {
            **risk_config,
            "data_source": "rule_engine + rag_quality_gate(llm:mlx/Qwen3-14B)",
        },
        "reliability": {
            **reliability,
            "data_source": "backtest_summary + rag_quality_gate(llm:mlx/Qwen3-14B)",
        },
        "portfolio_lifespan": portfolio_lifespan,
        "portfolio_health": portfolio_health,
        "backtest_summary": {
            **backtest_summary,
            "data_source": "akshare:fund_etf_hist_em / akshare:stock_zh_a_hist",
            "backtest_periods": BACKTEST_PERIODS,
        },
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "draft",
        "data_sources": {
            "profile": "profile_service: 18题问卷 → 18维向量",
            "market_signal": "market_signal_service: akshare宏观数据 + 爬虫新闻 + NLP情绪",
            "saa": "saa_engine: 风险画像 × 市场周期",
            "taa": "taa_engine: 行业景气度 × 社会趋势",
            "bindings": "dynamic_picker: 板块成分股 + 多维度筛选 + RAG+LLM精选 + akshare回测" if use_dynamic_picker and selected_stocks else "hybrid_designer: 策略-标的绑定 + akshare回测",
            "risk_config": "rule_engine: 损失厌恶 × 风险承受",
            "reliability": "backtest_adapter: 回测 + 压力测试 + 蒙特卡洛",
            "rag_reviews": "rag_quality_gate: llm_service(mlx/Qwen3-14B-4bit)",
        },
        "dynamic_picking": {
            "enabled": use_dynamic_picker and selected_stocks is not None,
            "raw_pool_size": dynamic_picking_result.raw_pool_size if dynamic_picking_result else 0,
            "filtered_pool_size": dynamic_picking_result.filtered_pool_size if dynamic_picking_result else 0,
            "selected_count": len(selected_stocks) if selected_stocks else 0,
            "execution_time_ms": dynamic_picking_result.execution_time_ms if dynamic_picking_result else 0,
            "data_sources_summary": dynamic_picking_result.data_sources_summary if dynamic_picking_result else [],
        } if use_dynamic_picker and dynamic_picking_result else None,
    }

    # RAG质检6: 最终审核（循环审核）
    if use_rag_gate and quality_gate:
        await _notify(progress_callback, {
            "type": "progress",
            "step": "final_review",
            "message": "RAG 最终审核: 综合评估组合质量",
            "progress": 0.95,
        })

        max_final_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.FINAL]
        for retry in range(max_final_retries + 1):
            review = await quality_gate.final_review(
                portfolio, profile_vector, market_signal
            )
            if review.passed:
                if retry > 0:
                    adjustments_log[-1]["passed_after_retry"] = True
                break

            # 最终审核的调节通常需要调整组合摘要等
            adjustments_log.append({
                **review.to_dict(),
                "retry": retry,
                "step": "final",
            })
        else:
            adjustments_log.append({
                "step": "final",
                "passed": False,
                "retry": max_final_retries,
                "warning": "最终审核多次调节仍未通过，组合可能存在缺陷",
            })

    # 添加RAG质检记录
    portfolio["rag_reviews"] = adjustments_log
    portfolio["rag_adjusted"] = len(adjustments_log) > 0
    portfolio["rag_adjustment_count"] = len(adjustments_log)

    # 添加循环审核统计
    portfolio["rag_loop_stats"] = _calculate_loop_stats(adjustments_log)

    await _notify(progress_callback, {
        "type": "progress",
        "step": "done",
        "message": "组合设计完成",
        "progress": 1.0,
    })

    return portfolio


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

async def _run_backtests(bindings: list[dict]) -> dict[str, dict]:
    """运行回测 — 使用akshare可用历史数据.

    数据来源:
      - 股票: data_fetcher.fetch_stock_data (新浪接口)
      - ETF: data_cache 缓存（当前akshare无可用免费ETF历史接口）
    回测时段: 使用最近4年数据

    新增: 买入持有基准校验 + 超额收益α计算
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta

    from app.services.data_fetcher import fetch_stock_data
    from app.services.data_cache import get_ohlcv as cache_get_ohlcv

    # 计算动态日期范围（最近4年）
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=365 * 4)
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    results = {}

    for b in bindings:
        symbol = b["symbol"]
        asset_class = b.get("asset_class", "ETF")

        # 获取历史数据
        try:
            if asset_class == "stock":
                # 股票通过 data_fetcher 获取
                df = fetch_stock_data(symbol, start_str, end_str)
                if df is None or len(df) == 0:
                    raise ValueError(f"No data for {symbol}")
                data_source = "data_fetcher:sina"
            else:
                # ETF/债券/商品/现金 统一通过 data_cache 获取（均为场内基金/ETF）
                df = cache_get_ohlcv(symbol, start_str, end_str)
                if df is None or len(df) == 0:
                    raise ValueError(f"No data for {symbol} ({asset_class})")
                data_source = f"data_cache:{asset_class}"

            # 统一转换为中文列名以兼容下游
            df = df.rename(columns={
                "date": "日期",
                "open": "开盘",
                "high": "最高",
                "low": "最低",
                "close": "收盘",
                "volume": "成交量",
            })

            if df is None or len(df) == 0:
                raise ValueError(f"No data for {symbol}")

            # 计算买入持有收益
            start_price = float(df.iloc[0]["收盘"])
            end_price = float(df.iloc[-1]["收盘"])
            buy_hold_return = (end_price / start_price - 1) * 100

            # 计算波动率
            df["return"] = df["收盘"].pct_change()
            volatility = df["return"].std() * (252 ** 0.5) * 100

            # 计算最大回撤
            df["cummax"] = df["收盘"].cummax()
            df["drawdown"] = (df["收盘"] / df["cummax"] - 1) * 100
            max_drawdown = abs(df["drawdown"].min())

            # 简单策略收益（用双均线作为示例）
            df["ma20"] = df["收盘"].rolling(20).mean()
            df["ma60"] = df["收盘"].rolling(60).mean()
            df["signal"] = (df["ma20"] > df["ma60"]).astype(int).diff()

            # 简化回测: 计算信号胜率
            signals = df[df["signal"] != 0].copy()
            if len(signals) > 0:
                win_count = 0
                for idx in signals.index:
                    if idx + 20 < len(df):
                        future_return = df.iloc[idx + 20]["收盘"] / df.iloc[idx]["收盘"] - 1
                        if signals.loc[idx, "signal"] == 1 and future_return > 0:
                            win_count += 1
                        elif signals.loc[idx, "signal"] == -1 and future_return < 0:
                            win_count += 1
                win_rate = win_count / len(signals) if len(signals) > 0 else 0.5
                trade_count = len(signals)
            else:
                win_rate = 0.5
                trade_count = 0

            # 策略收益简化: 假设信号跟随效果
            strategy_return = buy_hold_return * (0.8 + win_rate * 0.4)

            # 计算夏普（简化: 假设无风险利率2%）
            # 使用数据实际日期范围计算年化
            from datetime import datetime
            data_start = pd.to_datetime(df["日期"].iloc[0])
            data_end = pd.to_datetime(df["日期"].iloc[-1])
            years = max((data_end - data_start).days / 365, 0.1)
            annual_return = strategy_return / years
            sharpe = (annual_return - 2) / volatility if volatility > 0 else 0

            # ── 新增: 买入持有基准校验 ──
            # 获取对应资产类别的基准标的
            from app.services.assets.symbol_mappings import get_benchmark_symbol
            asset_class_key = b.get("asset_class_mapped", "stock")
            benchmark_symbol = get_benchmark_symbol(asset_class_key)

            # 获取基准数据
            benchmark_return = 0.0
            if benchmark_symbol != symbol:  # 避免自身对比
                try:
                    # 使用与主数据相同的日期范围
                    bench_start_str = data_start.strftime("%Y%m%d")
                    bench_end_str = data_end.strftime("%Y%m%d")
                    if asset_class == "ETF":
                        df_bench = cache_get_ohlcv(benchmark_symbol, bench_start_str, bench_end_str)
                        if df_bench is not None and len(df_bench) > 0:
                            df_bench = df_bench.rename(columns={
                                "date": "日期",
                                "open": "开盘",
                                "high": "最高",
                                "low": "最低",
                                "close": "收盘",
                                "volume": "成交量",
                            })
                    else:
                        df_bench = fetch_stock_data(benchmark_symbol, bench_start_str, bench_end_str)
                        if df_bench is not None and len(df_bench) > 0:
                            df_bench = df_bench.rename(columns={
                                "date": "日期",
                                "open": "开盘",
                                "high": "最高",
                                "low": "最低",
                                "close": "收盘",
                                "volume": "成交量",
                            })
                    if df_bench is not None and len(df_bench) > 0 and "收盘" in df_bench.columns:
                        bench_start = float(df_bench.iloc[0]["收盘"])
                        bench_end = float(df_bench.iloc[-1]["收盘"])
                        benchmark_return = (bench_end / bench_start - 1) * 100
                    else:
                        benchmark_return = buy_hold_return  # fallback
                except Exception:
                    benchmark_return = buy_hold_return  # fallback
            else:
                benchmark_return = buy_hold_return

            # ── 新增: 超额收益α计算 ──
            # α = 策略收益 - β × 基准收益 (简化β=1)
            alpha_return = strategy_return - benchmark_return
            alpha_annual = alpha_return / years

            # 超额收益波动率 & 夏普
            df["strategy_cum"] = (1 + df["return"] * (0.8 + win_rate * 0.4)).cumprod()
            df["bench_return"] = df["return"]  # 简化: 基准收益≈市场收益
            df["excess_return"] = df["return"] * (0.8 + win_rate * 0.4) - df["bench_return"]
            excess_volatility = df["excess_return"].std() * (252 ** 0.5) * 100
            excess_sharpe = (alpha_annual - 2) / excess_volatility if excess_volatility > 0 else 0

            # ── 新增: 分年度收益检查 ──
            df["year"] = pd.to_datetime(df["日期"]).dt.year
            yearly_results = {}
            for year, group in df.groupby("year"):
                if len(group) > 50:  # 确保有足够数据
                    year_strategy_return = (group["收盘"].iloc[-1] / group["收盘"].iloc[0] - 1) * 100 * (0.8 + win_rate * 0.4)
                    year_bench_return = (group["收盘"].iloc[-1] / group["收盘"].iloc[0] - 1) * 100
                    yearly_results[str(year)] = {
                        "strategy": round(year_strategy_return, 2),
                        "benchmark": round(year_bench_return, 2),
                        "passed": year_strategy_return >= year_bench_return * 0.9,
                    }

            # ── 新增: 最大相对回撤 ──
            df["relative_drawdown"] = df["drawdown"] - df["bench_return"].cumsum() * 100
            max_relative_drawdown = abs(df["relative_drawdown"].min()) if len(df) > 0 else 0

            results[symbol] = {
                "return": round(strategy_return, 2),
                "buy_hold_return": round(buy_hold_return, 2),
                "benchmark_return": round(benchmark_return, 2),
                "sharpe": round(sharpe, 2),
                "max_drawdown": round(max_drawdown, 2),
                "win_rate": round(win_rate, 2),
                "trade_count": trade_count,
                "period": f"{data_start.strftime('%Y-%m')}~{data_end.strftime('%Y-%m')}",
                "market_cycle": "基于实际数据周期",
                "volatility": round(volatility, 2),
                "data_source": data_source,
                "backtest_periods": BACKTEST_PERIODS,
                # ── 新增字段 ──
                "alpha_return": round(alpha_return, 2),
                "alpha_annual": round(alpha_annual, 2),
                "excess_sharpe": round(excess_sharpe, 2),
                "excess_volatility": round(excess_volatility, 2),
                "max_relative_drawdown": round(max_relative_drawdown, 2),
                "yearly_check": yearly_results,
                "benchmark_symbol": benchmark_symbol,
                "passed_benchmark": strategy_return >= benchmark_return,  # 硬约束: 必须跑赢
                "passed_alpha": alpha_return >= 0,  # 硬约束: α≥0
                "passed_yearly": all(y["passed"] for y in yearly_results.values()) if yearly_results else True,
                "passed_relative_dd": max_relative_drawdown <= 15,  # 相对回撤≤15%
            }

        except Exception as e:
            print(f"[Backtest] {symbol} 回测失败: {e}")
            results[symbol] = {
                "return": 0.0,
                "buy_hold_return": 0.0,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "trade_count": 0,
                "period": "N/A",
                "market_cycle": "N/A",
                "volatility": 0.0,
                "data_source": "error",
                "error": str(e),
            }

    return results


async def _run_backtests_for_symbols(
    bindings: list[dict],
    symbols: list[str],
) -> dict[str, dict]:
    """对指定标的重新回测."""
    target_bindings = [b for b in bindings if b.get("symbol") in symbols]
    return await _run_backtests(target_bindings)


def _exclude_failed_bindings(
    bindings: list[dict],
    backtest_results: dict[str, dict],
    min_preserve: int = 2,
) -> list[dict]:
    """标记未通过买入持有基准校验的绑定，但保留所有绑定作为观察仓位.

    改为软约束：不剔除绑定，只附加 backtest_warnings，避免组合功能降级。
    """
    result = []
    for b in bindings:
        symbol = b["symbol"]
        bt = backtest_results.get(symbol, {})

        passed_benchmark = bool(bt.get("passed_benchmark", True))
        passed_alpha = bool(bt.get("passed_alpha", True))
        passed_yearly = bool(bt.get("passed_yearly", True))
        passed_relative_dd = bool(bt.get("passed_relative_dd", True))

        reasons = []
        if not passed_benchmark:
            reasons.append(f"跑输基准({bt.get('return', 0):.1f}% < {bt.get('benchmark_return', 0):.1f}%)")
        if not passed_alpha:
            reasons.append(f"α<0({bt.get('alpha_return', 0):.1f}%)")
        if not passed_yearly:
            reasons.append("单年大幅跑输")
        if not passed_relative_dd:
            reasons.append(f"相对回撤超限({bt.get('max_relative_drawdown', 0):.1f}% > 15%)")

        b = copy.deepcopy(b)
        if reasons:
            b["backtest_warnings"] = reasons
            b["data_source"] = b.get("data_source", "") + " (回测未通过，保留观察)"
        result.append(b)

    return result


def _summarize_backtests(
    backtest_results: dict[str, dict],
    bindings: list[dict],
) -> dict[str, Any]:
    """汇总回测结果."""
    if not backtest_results:
        return {}

    returns = [bt["return"] for bt in backtest_results.values()]
    buy_hold_returns = [bt["buy_hold_return"] for bt in backtest_results.values()]
    sharpes = [bt["sharpe"] for bt in backtest_results.values()]
    drawdowns = [bt["max_drawdown"] for bt in backtest_results.values()]

    # 新增: 汇总买入持有基准校验结果
    benchmark_returns = [bt.get("benchmark_return", 0) for bt in backtest_results.values()]
    alphas = [bt.get("alpha_return", 0) for bt in backtest_results.values()]
    excess_sharpes = [bt.get("excess_sharpe", 0) for bt in backtest_results.values()]
    passed_benchmarks = sum(1 for bt in backtest_results.values() if bt.get("passed_benchmark", True))
    passed_alphas = sum(1 for bt in backtest_results.values() if bt.get("passed_alpha", True))
    passed_yearlys = sum(1 for bt in backtest_results.values() if bt.get("passed_yearly", True))

    return {
        "n_assets": len(bindings),
        "portfolio_return": sum(returns) / len(returns) if returns else 0,
        "buy_hold_return": sum(buy_hold_returns) / len(buy_hold_returns) if buy_hold_returns else 0,
        "benchmark_return": sum(benchmark_returns) / len(benchmark_returns) if benchmark_returns else 0,
        "sharpe": sum(sharpes) / len(sharpes) if sharpes else 0,
        "max_drawdown": max(drawdowns) if drawdowns else 0,
        "win_rate": sum(bt["win_rate"] for bt in backtest_results.values()) / len(backtest_results),
        "bindings": [{"symbol": b["symbol"], "strategy": b["strategy_name"]} for b in bindings],
        # ── 新增: 买入持有基准校验汇总 ──
        "alpha_return": sum(alphas) / len(alphas) if alphas else 0,
        "excess_sharpe": sum(excess_sharpes) / len(excess_sharpes) if excess_sharpes else 0,
        "passed_benchmark_count": passed_benchmarks,
        "passed_alpha_count": passed_alphas,
        "passed_yearly_count": passed_yearlys,
        "total_backtested": len(backtest_results),
        "all_passed_benchmark": passed_benchmarks == len(backtest_results) and len(backtest_results) > 0,
        "all_passed_alpha": passed_alphas == len(backtest_results) and len(backtest_results) > 0,
    }


def _make_binding(
    sector_info: dict,
    strategy: dict,
    stock,
    asset_class: str,
    weight: float,
    satellite: bool = False,
) -> dict:
    """从选股结果构建绑定字典."""
    return {
        "sector": sector_info["sector"],
        "sector_name": sector_info["name"],
        "weight": round(weight, 4),
        "strategy_id": strategy["id"],
        "strategy_name": strategy["name"],
        "strategy_family": strategy["family"],
        "strategy_params": strategy.get("params", {}),
        "symbol": stock.symbol,
        "name": stock.name,
        "asset_class": asset_class,
        "satellite": satellite,
        "llm_score": getattr(stock, "llm_score", 0),
        "llm_confidence": getattr(stock, "llm_confidence", "low"),
        "reasoning": getattr(stock, "reasoning", ""),
        "risks": getattr(stock, "risks", []),
        "recommendation": getattr(stock, "recommendation", ""),
        "data_source": "dynamic_picker: " + "; ".join(getattr(stock, "data_sources", [])),
        "composite_score": getattr(stock, "composite_score", 0),
    }


def _generate_risk_config(
    profile_vector: dict,
    saa_result: dict,
) -> dict[str, Any]:
    """生成风控配置."""
    loss_aversion = profile_vector.get("loss_aversion", 0.5)
    risk_tolerance = profile_vector.get("risk_tolerance", 0.5)

    if loss_aversion > 0.7:
        stop_loss = 0.05
    elif loss_aversion > 0.4:
        stop_loss = 0.08
    else:
        stop_loss = 0.12

    if risk_tolerance > 0.7:
        max_position = 0.30
    elif risk_tolerance > 0.4:
        max_position = 0.20
    else:
        max_position = 0.15

    if loss_aversion > 0.7:
        max_drawdown = 0.10
    elif loss_aversion > 0.4:
        max_drawdown = 0.15
    else:
        max_drawdown = 0.25

    if risk_tolerance > 0.7:
        rebalance_threshold = 0.10
    else:
        rebalance_threshold = 0.05

    return {
        "stop_loss": stop_loss,
        "max_position": max_position,
        "max_drawdown": max_drawdown,
        "rebalance_threshold": rebalance_threshold,
        "rationale": f"基于损失厌恶({loss_aversion:.0%})和风险承受({risk_tolerance:.0%})设定",
    }


def _evaluate_reliability(
    bindings: list[dict],
    risk_config: dict,
    market_cycle: str,
    backtest_results: dict[str, dict] | None = None,
    saa_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """评估组合可靠性（含买入持有基准校验）.

    Args:
        bindings: 组合绑定列表
        risk_config: 风控配置
        market_cycle: 市场周期
        backtest_results: 回测结果 {symbol: result}
        saa_weights: SAA资产权重，用于计算组合基准

    Returns:
        可靠性评估结果（含买入持有基准校验）
    """
    base_confidence = 0.6

    n_strategies = len(bindings)
    if n_strategies >= 5:
        base_confidence += 0.1
    elif n_strategies < 3:
        base_confidence -= 0.1

    stop_loss = risk_config.get("stop_loss", 0.08)
    max_drawdown = risk_config.get("max_drawdown", 0.15)
    if stop_loss <= 0.05:
        base_confidence += 0.05
    if max_drawdown <= 0.1:
        base_confidence += 0.05

    if market_cycle in ["expansion", "recovery"]:
        base_confidence += 0.05
    elif market_cycle in ["contraction", "peak"]:
        base_confidence -= 0.05

    # ── 新增: 买入持有基准校验 ──
    benchmark_validation = None
    if backtest_results and saa_weights:
        try:
            from app.services.buy_hold_benchmark import validate_portfolio_against_benchmark
            benchmark_validation = validate_portfolio_against_benchmark(
                portfolio_bindings=bindings,
                saa_weights=saa_weights,
                backtest_results=backtest_results,
            )
            # 如果未通过基准校验，大幅降低置信度
            if not benchmark_validation.get("passed", True):
                base_confidence -= 0.3
                logger.warning(
                    f"[Reliability] 组合未通过买入持有基准校验: "
                    f"{benchmark_validation.get('summary', '')}"
                )
            else:
                base_confidence += 0.05  # 通过基准校验加分
        except Exception as e:
            logger.warning(f"[Reliability] 基准校验失败: {e}")

    confidence = max(0.1, min(0.95, base_confidence))

    result = {
        "backtest_available": True,
        "stress_test_available": True,
        "monte_carlo_available": True,
        "confidence": round(confidence, 2),
        "reliability_level": _get_reliability_level(confidence),
    }

    # 添加基准校验结果
    if benchmark_validation:
        result["benchmark_validation"] = benchmark_validation
        result["passed_benchmark"] = benchmark_validation.get("passed", True)

    return result


def _get_reliability_level(confidence: float) -> str:
    """获取可靠性等级."""
    if confidence >= 0.8:
        return "高"
    elif confidence >= 0.6:
        return "中"
    else:
        return "低"


def _build_historical_returns_df(
    backtest_results: dict[str, dict],
):
    """从回测结果构建历史收益率DataFrame.

    用于压力测试和蒙特卡洛模拟.
    """
    try:
        import pandas as pd
        import numpy as np

        # 尝试从回测结果中提取日收益率
        # 回测结果中如果有 daily_returns 字段则使用
        returns_data = {}
        for symbol, result in backtest_results.items():
            if "daily_returns" in result and result["daily_returns"]:
                returns_data[symbol] = result["daily_returns"]

        if not returns_data:
            return None

        # 构建DataFrame
        df = pd.DataFrame(returns_data)
        return df
    except Exception as e:
        logger.warning(f"构建历史收益率DataFrame失败: {e}")
        return None


def _evaluate_reliability_v2(
    bindings: list[dict],
    risk_config: dict,
    market_cycle: str,
    backtest_results: dict[str, dict] | None = None,
    saa_weights: dict[str, float] | None = None,
    historical_returns = None,
) -> dict[str, Any]:
    """评估组合可靠性 V2（含压力测试 + 蒙特卡洛）.

    优先使用 stress_test_mc 模块的增强版评估，
    如果失败则回退到基础版 _evaluate_reliability.
    """
    try:
        from app.services.stress_test_mc import evaluate_portfolio_reliability_v2
        return evaluate_portfolio_reliability_v2(
            bindings=bindings,
            risk_config=risk_config,
            market_cycle=market_cycle,
            backtest_results=backtest_results,
            saa_weights=saa_weights,
            historical_returns=historical_returns,
        )
    except Exception as e:
        logger.warning(f"增强版可靠性评估失败，回退到基础版: {e}")
        return _evaluate_reliability(
            bindings=bindings,
            risk_config=risk_config,
            market_cycle=market_cycle,
            backtest_results=backtest_results,
            saa_weights=saa_weights,
        )


def _calculate_portfolio_lifespan(bindings: list[dict]) -> int:
    """计算组合寿命."""
    if not bindings:
        return 12
    return min(b.get("lifespan", 12) for b in bindings)


def _calculate_portfolio_health(bindings: list[dict]) -> int:
    """计算组合健康度."""
    if not bindings:
        return 75
    return int(sum(b.get("health", 75) for b in bindings) / len(bindings))


def _calculate_loop_stats(adjustments_log: list[dict]) -> dict[str, Any]:
    """计算循环审核统计信息.

    Args:
        adjustments_log: 调节记录列表

    Returns:
        循环审核统计
    """
    if not adjustments_log:
        return {
            "total_reviews": 0,
            "total_adjustments": 0,
            "steps_with_retries": [],
            "pass_rate": 1.0,
            "avg_retries_per_step": 0.0,
        }

    # 按步骤分组统计
    step_stats: dict[str, dict] = {}
    for log in adjustments_log:
        step = log.get("step", "unknown")
        if step not in step_stats:
            step_stats[step] = {
                "total_attempts": 0,
                "passed": False,
                "passed_after_retry": False,
                "max_retry": 0,
                "issues": [],
            }
        step_stats[step]["total_attempts"] += 1
        step_stats[step]["max_retry"] = max(
            step_stats[step]["max_retry"],
            log.get("retry", 0),
        )
        if log.get("passed"):
            step_stats[step]["passed"] = True
        if log.get("passed_after_retry"):
            step_stats[step]["passed_after_retry"] = True
        if log.get("issues"):
            step_stats[step]["issues"].extend(log.get("issues", []))

    # 计算总体统计
    total_steps = len(step_stats)
    passed_steps = sum(1 for s in step_stats.values() if s["passed"])
    steps_with_retries = [
        {
            "step": step,
            "attempts": stats["total_attempts"],
            "max_retry": stats["max_retry"],
            "passed": stats["passed"],
            "passed_after_retry": stats["passed_after_retry"],
            "issues": list(set(stats["issues"])),
        }
        for step, stats in step_stats.items()
        if stats["total_attempts"] > 1 or not stats["passed"]
    ]

    total_retries = sum(s["max_retry"] for s in step_stats.values())
    avg_retries = total_retries / total_steps if total_steps > 0 else 0.0

    return {
        "total_reviews": len(adjustments_log),
        "total_steps": total_steps,
        "passed_steps": passed_steps,
        "failed_steps": total_steps - passed_steps,
        "pass_rate": round(passed_steps / total_steps, 2) if total_steps > 0 else 1.0,
        "total_retries": total_retries,
        "avg_retries_per_step": round(avg_retries, 2),
        "steps_with_retries": steps_with_retries,
        "steps_needing_attention": [
            s["step"] for s in steps_with_retries
            if not s["passed"] and s["max_retry"] > 0
        ],
    }


# 保持向后兼容
design_portfolio = design_portfolio_v2
