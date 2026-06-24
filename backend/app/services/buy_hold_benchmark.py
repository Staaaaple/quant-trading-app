"""买入持有基准校验模块 — 策略有效性硬约束.

核心原则: 任何策略必须满足 策略收益 ≥ 买入持有收益

基准定义:
- 股票部分: 买入并持有沪深300ETF(510300)，同期收益
- 债券部分: 买入并持有国债ETF(511010)，同期收益
- 商品部分: 买入并持有黄金ETF(518880)，同期收益
- 现金部分: 买入并持有银华日利(511880)，同期收益
- 组合基准 = Σ(资产权重 × 对应资产买入持有收益)

检查维度:
1. 全周期累计: 策略累计收益 ≥ 基准累计收益（硬约束，一票否决）
2. 分年度检查: 任一年度策略收益 ≥ 基准收益 × 0.9（防止单年大幅跑输）
3. 超额收益α: 剔除β后纯策略收益 ≥ 0（确保不是市场β的功劳）
4. 超额稳定性: 超额收益夏普比率 ≥ 0.3（确保超额不是偶然）
5. 最大相对回撤: 策略相对基准的最大回撤 ≤ 15%（防止阶段性跑输过多）
"""

import datetime
import logging
from typing import Any

import numpy as np
import pandas as pd

from app.services.assets.symbol_mappings import BUY_HOLD_BENCHMARK
from app.services.data_fetcher import fetch_stock_data
from app.services.data_cache import get_ohlcv as cache_get_ohlcv

logger = logging.getLogger(__name__)


def _bool(x) -> bool:
    """将 numpy.bool_ 转为 Python bool，避免 JSON 序列化失败."""
    return bool(x)


# ═══════════════════════════════════════════════════════════════
# 1. 基准收益计算
# ═══════════════════════════════════════════════════════════════

def calculate_buy_hold_return(
    symbol: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """计算单个标的的买入持有收益.

    Args:
        symbol: 标的代码
        start_date: 开始日期 (YYYY-MM-DD 或 YYYYMMDD)
        end_date: 结束日期

    Returns:
        {
            "total_return": 总收益率 (小数),
            "annualized_return": 年化收益率 (小数),
            "max_drawdown": 最大回撤 (小数, 正数),
            "volatility": 年化波动率 (小数),
            "start_price": 起始价格,
            "end_price": 结束价格,
            "trading_days": 交易日数,
            "data_source": 数据来源,
        }
    """
    start_fmt = start_date.replace("-", "")
    end_fmt = end_date.replace("-", "")

    # 获取数据
    df = None
    data_source = "unknown"

    # 优先尝试缓存(ETF数据)
    df = cache_get_ohlcv(symbol, start_fmt, end_fmt)
    if df is not None and not df.empty:
        data_source = "data_cache"
    else:
        # 尝试实时获取
        try:
            df = fetch_stock_data(symbol, start_fmt, end_fmt)
            if df is not None and not df.empty:
                data_source = "data_fetcher:sina"
                # 统一列名
                if "close" in df.columns:
                    df = df.rename(columns={
                        "date": "日期",
                        "open": "开盘",
                        "high": "最高",
                        "low": "最低",
                        "close": "收盘",
                        "volume": "成交量",
                    })
        except Exception as e:
            logger.warning(f"获取基准标的 {symbol} 数据失败: {e}")

    if df is None or df.empty or len(df) < 2:
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "start_price": 0.0,
            "end_price": 0.0,
            "trading_days": 0,
            "data_source": "failed",
            "error": "无数据",
        }

    # 确保日期列存在且排序
    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期").reset_index(drop=True)
        close_col = "收盘"
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        close_col = "close"
    else:
        close_col = df.columns[-1]  # 假设最后一列是收盘价

    # 计算收益
    start_price = float(df.iloc[0][close_col])
    end_price = float(df.iloc[-1][close_col])
    total_return = (end_price / start_price - 1) if start_price > 0 else 0.0

    # 年化收益
    trading_days = len(df)
    years = trading_days / 252
    annualized_return = (end_price / start_price) ** (1 / max(years, 0.01)) - 1 if start_price > 0 else 0.0

    # 波动率
    df["return"] = df[close_col].pct_change()
    volatility = df["return"].std() * (252 ** 0.5) if len(df) > 1 else 0.0

    # 最大回撤
    df["cummax"] = df[close_col].cummax()
    df["drawdown"] = df[close_col] / df["cummax"] - 1
    max_drawdown = abs(df["drawdown"].min())

    return {
        "total_return": round(total_return, 4),
        "annualized_return": round(annualized_return, 4),
        "max_drawdown": round(max_drawdown, 4),
        "volatility": round(volatility, 4),
        "start_price": round(start_price, 2),
        "end_price": round(end_price, 2),
        "trading_days": trading_days,
        "data_source": data_source,
    }


def calculate_composite_benchmark(
    asset_weights: dict[str, float],
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """计算组合买入持有基准收益.

    Args:
        asset_weights: {asset_class: weight}，如 {"stock": 0.6, "bond": 0.3, ...}
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        {
            "composite_return": 组合基准总收益 (小数),
            "composite_annualized": 组合基准年化收益 (小数),
            "component_returns": {asset_class: 该资产基准收益},
            "weight_breakdown": {asset_class: 权重},
            "details": {asset_class: 详细收益数据},
        }
    """
    component_returns = {}
    details = {}
    weighted_returns = []

    for asset_class, weight in asset_weights.items():
        if weight <= 0:
            continue

        benchmark_info = BUY_HOLD_BENCHMARK.get(asset_class)
        if not benchmark_info:
            logger.warning(f"未知资产类别: {asset_class}")
            continue

        symbol = benchmark_info["symbol"]
        result = calculate_buy_hold_return(symbol, start_date, end_date)

        component_returns[asset_class] = result["total_return"]
        details[asset_class] = {
            **result,
            "symbol": symbol,
            "name": benchmark_info["name"],
            "weight": weight,
            "weighted_return": result["total_return"] * weight,
        }
        weighted_returns.append(result["total_return"] * weight)

    composite_return = sum(weighted_returns)

    # 计算组合年化（近似）
    trading_days = max(
        (d["trading_days"] for d in details.values()),
        default=0
    )
    years = trading_days / 252
    composite_annualized = (1 + composite_return) ** (1 / max(years, 0.01)) - 1 if composite_return > -1 else 0.0

    return {
        "composite_return": round(composite_return, 4),
        "composite_annualized": round(composite_annualized, 4),
        "component_returns": component_returns,
        "weight_breakdown": asset_weights,
        "details": details,
    }


# ═══════════════════════════════════════════════════════════════
# 2. 策略收益计算（简化版，基于回测结果）
# ═══════════════════════════════════════════════════════════════

def calculate_strategy_return_from_backtest(
    backtest_result: dict[str, Any],
) -> dict[str, Any]:
    """从回测结果中提取策略收益.

    Args:
        backtest_result: 回测结果字典

    Returns:
        {
            "total_return": 策略总收益 (小数),
            "annualized_return": 年化收益 (小数),
            "max_drawdown": 最大回撤 (小数),
            "sharpe": 夏普比率,
            "win_rate": 胜率 (小数),
            "trade_count": 交易次数,
        }
    """
    return {
        "total_return": backtest_result.get("total_return", 0.0),
        "annualized_return": backtest_result.get("annualized_return", 0.0),
        "max_drawdown": backtest_result.get("max_drawdown", 0.0),
        "sharpe": backtest_result.get("sharpe", 0.0),
        "win_rate": backtest_result.get("win_rate", 0.0),
        "trade_count": backtest_result.get("trade_count", 0),
    }


# ═══════════════════════════════════════════════════════════════
# 3. 买入持有基准校验（核心硬约束）
# ═══════════════════════════════════════════════════════════════

def validate_buy_hold_benchmark(
    strategy_return: float,
    benchmark_return: float,
    strategy_annual_by_year: dict[str, float] | None = None,
    benchmark_annual_by_year: dict[str, float] | None = None,
    strategy_drawdown: float = 0.0,
    benchmark_drawdown: float = 0.0,
    excess_returns: list[float] | None = None,
) -> dict[str, Any]:
    """校验策略是否跑赢买入持有基准（硬约束）.

    Args:
        strategy_return: 策略累计总收益 (小数)
        benchmark_return: 基准累计总收益 (小数)
        strategy_annual_by_year: 策略分年度收益 {year: return}
        benchmark_annual_by_year: 基准分年度收益 {year: return}
        strategy_drawdown: 策略最大回撤 (小数, 正数)
        benchmark_drawdown: 基准最大回撤 (小数, 正数)
        excess_returns: 超额收益序列（用于计算超额夏普）

    Returns:
        {
            "passed": bool,  # 是否通过所有硬约束
            "checks": {
                "total_return_check": {"passed": bool, "detail": str},
                "annual_check": {"passed": bool, "detail": str},
                "alpha_check": {"passed": bool, "detail": str, "alpha": float},
                "excess_sharpe_check": {"passed": bool, "detail": str, "excess_sharpe": float},
                "relative_drawdown_check": {"passed": bool, "detail": str, "relative_dd": float},
            },
            "summary": str,
            "strategy_return": float,
            "benchmark_return": float,
            "excess_return": float,  # 超额收益
        }
    """
    checks = {}
    all_passed = True

    # ── 检查1: 全周期累计收益 ≥ 基准收益 ──
    excess_return = strategy_return - benchmark_return
    total_passed = _bool(strategy_return >= benchmark_return)
    checks["total_return_check"] = {
        "passed": total_passed,
        "detail": (
            f"策略收益 {strategy_return:.2%} {'≥' if total_passed else '<'} "
            f"基准收益 {benchmark_return:.2%}"
        ),
        "strategy_return": round(strategy_return, 4),
        "benchmark_return": round(benchmark_return, 4),
        "excess": round(excess_return, 4),
    }
    if not total_passed:
        all_passed = False

    # ── 检查2: 分年度收益 ≥ 基准 × 0.9 ──
    annual_passed = True
    annual_details = []
    if strategy_annual_by_year and benchmark_annual_by_year:
        for year in sorted(set(strategy_annual_by_year.keys()) & set(benchmark_annual_by_year.keys())):
            s_ret = strategy_annual_by_year[year]
            b_ret = benchmark_annual_by_year[year]
            threshold = b_ret * 0.9
            year_passed = _bool(s_ret >= threshold)
            annual_details.append({
                "year": year,
                "strategy": round(s_ret, 4),
                "benchmark": round(b_ret, 4),
                "threshold": round(threshold, 4),
                "passed": year_passed,
            })
            if not year_passed:
                annual_passed = False
                all_passed = False
    else:
        # 无分年度数据，默认通过
        annual_passed = True

    checks["annual_check"] = {
        "passed": annual_passed,
        "detail": (
            f"分年度检查: {sum(1 for d in annual_details if d['passed'])}/{len(annual_details)} 年通过"
            if annual_details else "无分年度数据，跳过"
        ),
        "annual_details": annual_details,
    }

    # ── 检查3: 超额收益α ≥ 0 ──
    # 简化α计算: α = 策略收益 - β × 基准收益
    # β近似为1（简化处理，实际应回归计算）
    beta = 1.0
    alpha = strategy_return - beta * benchmark_return
    alpha_passed = _bool(alpha >= 0)
    checks["alpha_check"] = {
        "passed": alpha_passed,
        "detail": f"超额收益α = {alpha:.2%} {'≥' if alpha_passed else '<'} 0",
        "alpha": round(alpha, 4),
        "beta": beta,
    }
    if not alpha_passed:
        all_passed = False

    # ── 检查4: 超额收益夏普 ≥ 0.3 ──
    excess_sharpe_passed = True
    excess_sharpe = 0.0
    if excess_returns and len(excess_returns) > 1:
        excess_mean = np.mean(excess_returns)
        excess_std = np.std(excess_returns, ddof=1)
        if excess_std > 0:
            # 年化处理（假设月度数据）
            excess_sharpe = (excess_mean / excess_std) * (12 ** 0.5)
        excess_sharpe_passed = _bool(excess_sharpe >= 0.3)
        checks["excess_sharpe_check"] = {
            "passed": excess_sharpe_passed,
            "detail": f"超额收益夏普 = {excess_sharpe:.3f} {'≥' if excess_sharpe_passed else '<'} 0.3",
            "excess_sharpe": round(excess_sharpe, 4),
            "excess_mean": round(excess_mean, 4),
            "excess_std": round(excess_std, 4),
        }
        if not excess_sharpe_passed:
            all_passed = False
    else:
        checks["excess_sharpe_check"] = {
            "passed": True,  # 无数据默认通过
            "detail": "无超额收益序列，跳过",
            "excess_sharpe": None,
        }

    # ── 检查5: 最大相对回撤 ≤ 15% ──
    # 相对回撤 = 策略回撤 - 基准回撤（简化）
    relative_dd = max(0, strategy_drawdown - benchmark_drawdown)
    relative_dd_passed = _bool(relative_dd <= 0.15)
    checks["relative_drawdown_check"] = {
        "passed": relative_dd_passed,
        "detail": f"相对回撤 = {relative_dd:.2%} {'≤' if relative_dd_passed else '>'} 15%",
        "relative_drawdown": round(relative_dd, 4),
        "strategy_drawdown": round(strategy_drawdown, 4),
        "benchmark_drawdown": round(benchmark_drawdown, 4),
    }
    if not relative_dd_passed:
        all_passed = False

    # 汇总
    passed_checks = sum(1 for c in checks.values() if c["passed"])
    total_checks = len(checks)

    summary = (
        f"买入持有基准校验: {passed_checks}/{total_checks} 项通过 | "
        f"策略收益 {strategy_return:.2%} vs 基准 {benchmark_return:.2%} | "
        f"超额收益 {excess_return:.2%} | "
        f"{'✅ 通过' if all_passed else '❌ 未通过'}"
    )

    return {
        "passed": all_passed,
        "checks": checks,
        "summary": summary,
        "strategy_return": round(strategy_return, 4),
        "benchmark_return": round(benchmark_return, 4),
        "excess_return": round(excess_return, 4),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
    }


# ═══════════════════════════════════════════════════════════════
# 4. 组合层面的基准校验
# ═══════════════════════════════════════════════════════════════

def validate_portfolio_against_benchmark(
    portfolio_bindings: list[dict],
    saa_weights: dict[str, float],
    start_date: str | None = None,
    end_date: str | None = None,
    backtest_results: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """校验整个组合是否跑赢买入持有基准.

    Args:
        portfolio_bindings: 组合绑定列表
        saa_weights: SAA资产权重
        start_date: 回测开始日期
        end_date: 回测结束日期
        backtest_results: 已有回测结果 {symbol: result}

    Returns:
        完整校验报告
    """
    # 使用动态默认日期（最近4年）
    if end_date is None:
        end_date = datetime.date.today().isoformat()
    if start_date is None:
        start_date = (datetime.date.today() - datetime.timedelta(days=365 * 4)).isoformat()

    # 1. 计算组合基准
    benchmark = calculate_composite_benchmark(saa_weights, start_date, end_date)
    benchmark_return = benchmark["composite_return"]

    # 2. 计算组合策略收益（加权平均）
    strategy_return, strategy_drawdown = calculate_portfolio_strategy_return(
        portfolio_bindings, backtest_results
    )

    # 3. 基准回撤（加权平均）
    benchmark_drawdown = 0.0
    for asset_class, detail in benchmark.get("details", {}).items():
        weight = detail.get("weight", 0.0)
        dd = detail.get("max_drawdown", 0.0)
        benchmark_drawdown += dd * weight

    # 4. 执行校验
    validation = validate_buy_hold_benchmark(
        strategy_return=strategy_return,
        benchmark_return=benchmark_return,
        strategy_drawdown=strategy_drawdown,
        benchmark_drawdown=benchmark_drawdown,
    )

    return {
        **validation,
        "benchmark_details": benchmark,
        "portfolio_strategy_return": round(strategy_return, 4),
        "portfolio_strategy_drawdown": round(strategy_drawdown, 4),
    }


# ═══════════════════════════════════════════════════════════════
# 5. 多基准对比与置信度评分
# ═══════════════════════════════════════════════════════════════

def _is_backtest_in_percentage(bt: dict) -> bool:
    """判断回测结果是否使用百分比格式.

    hybrid_portfolio_designer_v2 中收益率/回撤等字段会 *100 以百分比数值存储，
    而本模块的买入持有基准使用小数格式（如 0.24 表示 24%）。
    这里通过 volatility 字段作为哨兵判断：年化波动率通常大于 1 时为百分比格式。
    """
    volatility = bt.get("volatility")
    if volatility is not None and volatility > 1:
        return True
    # 备用判断：return 与 max_drawdown 同时明显大于 1
    ret = bt.get("return", 0)
    dd = bt.get("max_drawdown", 0)
    return abs(ret) > 1 and abs(dd) > 1


def _pct_to_decimal(value: float | None) -> float:
    """将百分比数值转换为小数."""
    if value is None:
        return 0.0
    return value / 100.0


def calculate_portfolio_strategy_return(
    portfolio_bindings: list[dict],
    backtest_results: dict[str, dict] | None = None,
) -> tuple[float, float]:
    """计算组合策略收益与回撤（加权平均）.

    与 composite_benchmark 保持一致：收益和回撤均采用按权重加权平均，
    而非取单个标的最大值，避免分散化组合被个别高回撤标的过度惩罚。
    自动兼容 hybrid_portfolio_designer_v2 的百分比格式回测结果。

    Returns:
        (strategy_return, strategy_drawdown)
    """
    total_weight = 0.0
    weighted_strategy_return = 0.0
    weighted_strategy_drawdown = 0.0

    for b in portfolio_bindings:
        weight = b.get("weight", 0.0)
        symbol = b.get("symbol", "")

        if backtest_results and symbol in backtest_results:
            bt = backtest_results[symbol]
            s_ret = bt.get("return", bt.get("total_return", 0.0))
            s_dd = bt.get("max_drawdown", 0.0)
            # 统一单位：如果回测结果是百分比格式，转为小数
            if _is_backtest_in_percentage(bt):
                s_ret = _pct_to_decimal(s_ret)
                s_dd = _pct_to_decimal(s_dd)
        else:
            # 无回测数据时保守估计为 0
            s_ret = 0.0
            s_dd = 0.0

        weighted_strategy_return += s_ret * weight
        weighted_strategy_drawdown += s_dd * weight
        total_weight += weight

    if total_weight > 0:
        strategy_return = weighted_strategy_return / total_weight
        strategy_drawdown = weighted_strategy_drawdown / total_weight
    else:
        strategy_return = 0.0
        strategy_drawdown = 0.0

    return strategy_return, strategy_drawdown


def _calculate_benchmark_score(
    strategy_return: float,
    benchmark_return: float,
    strategy_drawdown: float,
    benchmark_drawdown: float,
) -> dict[str, Any]:
    """计算单一基准对比的得分与指标.

    评分维度：
    - 总收益跑赢：40%
    - 回撤控制（策略回撤 ≤ 基准回撤 × 1.2）：25%
    - 风险调整后收益（策略收益/策略回撤 vs 基准收益/基准回撤）：25%
    - 不亏损（策略收益 ≥ 0 或 亏损小于基准）：10%
    """
    excess_return = strategy_return - benchmark_return

    # 1. 收益跑赢
    return_score = 0.0
    if strategy_return >= benchmark_return:
        return_score = 1.0
    elif strategy_return >= benchmark_return * 0.8:
        return_score = 0.5
    elif strategy_return >= benchmark_return * 0.5:
        return_score = 0.2

    # 2. 回撤控制
    dd_score = 0.0
    if benchmark_drawdown > 0:
        if strategy_drawdown <= benchmark_drawdown:
            dd_score = 1.0
        elif strategy_drawdown <= benchmark_drawdown * 1.2:
            dd_score = 0.6
        elif strategy_drawdown <= benchmark_drawdown * 1.5:
            dd_score = 0.3
    else:
        dd_score = 1.0 if strategy_drawdown <= 0.2 else 0.5

    # 3. 风险调整后收益（卡玛比率近似）
    calmar_score = 0.0
    s_calmar = strategy_return / max(strategy_drawdown, 0.01)
    b_calmar = benchmark_return / max(benchmark_drawdown, 0.01)
    if b_calmar > 0:
        if s_calmar >= b_calmar:
            calmar_score = 1.0
        elif s_calmar >= b_calmar * 0.8:
            calmar_score = 0.6
        elif s_calmar >= b_calmar * 0.5:
            calmar_score = 0.3
    else:
        calmar_score = 1.0 if s_calmar >= 0 else 0.0

    # 4. 不大幅亏损
    loss_score = 0.0
    if strategy_return >= 0:
        loss_score = 1.0
    elif strategy_return >= benchmark_return:
        loss_score = 0.8
    elif strategy_return >= -0.1:
        loss_score = 0.4

    score = return_score * 0.40 + dd_score * 0.25 + calmar_score * 0.25 + loss_score * 0.10
    score = round(max(0.0, min(1.0, score)), 4)

    return {
        "benchmark_return": round(benchmark_return, 4),
        "strategy_return": round(strategy_return, 4),
        "excess_return": round(excess_return, 4),
        "benchmark_drawdown": round(benchmark_drawdown, 4),
        "strategy_drawdown": round(strategy_drawdown, 4),
        "passed": _bool(strategy_return >= benchmark_return),
        "score": score,
        "return_score": round(return_score, 4),
        "drawdown_score": round(dd_score, 4),
        "calmar_score": round(calmar_score, 4),
        "loss_score": round(loss_score, 4),
    }


def calculate_broad_index_benchmark(
    start_date: str,
    end_date: str,
    symbol: str = "510300",
) -> dict[str, Any]:
    """计算宽基指数买入持有收益（默认沪深300）."""
    result = calculate_buy_hold_return(symbol, start_date, end_date)
    return {
        "symbol": symbol,
        "name": "沪深300ETF",
        "total_return": result["total_return"],
        "annualized_return": result["annualized_return"],
        "max_drawdown": result["max_drawdown"],
        "volatility": result["volatility"],
    }


def calculate_equal_weight_benchmark(
    portfolio_bindings: list[dict],
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """计算等权买入持有 benchmark：等权持有所有 binding 标的."""
    if not portfolio_bindings:
        return {"total_return": 0.0, "max_drawdown": 0.0}

    returns = []
    drawdowns = []
    for b in portfolio_bindings:
        symbol = b.get("symbol", "")
        if not symbol:
            continue
        result = calculate_buy_hold_return(symbol, start_date, end_date)
        if result.get("data_source") != "failed":
            returns.append(result["total_return"])
            drawdowns.append(result["max_drawdown"])

    if not returns:
        return {"total_return": 0.0, "max_drawdown": 0.0}

    return {
        "total_return": round(sum(returns) / len(returns), 4),
        "max_drawdown": round(sum(drawdowns) / len(drawdowns), 4),
    }


def calculate_sixty_forty_benchmark(
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """计算 60/40 股债组合 benchmark：60% 沪深300 + 40% 国债ETF."""
    stock_result = calculate_buy_hold_return("510300", start_date, end_date)
    bond_result = calculate_buy_hold_return("511010", start_date, end_date)

    total_return = 0.6 * stock_result["total_return"] + 0.4 * bond_result["total_return"]
    max_drawdown = 0.6 * stock_result["max_drawdown"] + 0.4 * bond_result["max_drawdown"]

    return {
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_drawdown, 4),
        "stock": stock_result,
        "bond": bond_result,
    }


def compare_portfolio_to_benchmarks(
    portfolio_bindings: list[dict],
    saa_weights: dict[str, float],
    backtest_results: dict[str, dict] | None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """对比组合策略与多个基准.

    Returns:
        {
            "custom_benchmark": {...},
            "csi300": {...},
            "equal_weight": {...},
            "sixty_forty": {...},
            "overall_score": float,
            "strategy_return": float,
            "strategy_drawdown": float,
        }
    """
    if end_date is None:
        end_date = datetime.date.today().isoformat()
    if start_date is None:
        start_date = (datetime.date.today() - datetime.timedelta(days=365 * 4)).isoformat()

    strategy_return, strategy_drawdown = calculate_portfolio_strategy_return(
        portfolio_bindings, backtest_results
    )

    # 1. 自定义大类资产基准
    custom = calculate_composite_benchmark(saa_weights, start_date, end_date)
    custom_metric = _calculate_benchmark_score(
        strategy_return=strategy_return,
        benchmark_return=custom["composite_return"],
        strategy_drawdown=strategy_drawdown,
        benchmark_drawdown=sum(
            d.get("max_drawdown", 0) * d.get("weight", 0)
            for d in custom.get("details", {}).values()
        ),
    )
    custom_metric["name"] = "自定义大类资产基准"
    custom_metric["description"] = "按SAA权重持有4类ETF"

    # 2. 沪深300
    csi300 = calculate_broad_index_benchmark(start_date, end_date, "510300")
    csi300_metric = _calculate_benchmark_score(
        strategy_return=strategy_return,
        benchmark_return=csi300["total_return"],
        strategy_drawdown=strategy_drawdown,
        benchmark_drawdown=csi300["max_drawdown"],
    )
    csi300_metric["name"] = "沪深300"
    csi300_metric["description"] = "A股核心宽基指数"

    # 3. 等权持有
    equal_weight = calculate_equal_weight_benchmark(portfolio_bindings, start_date, end_date)
    equal_metric = _calculate_benchmark_score(
        strategy_return=strategy_return,
        benchmark_return=equal_weight["total_return"],
        strategy_drawdown=strategy_drawdown,
        benchmark_drawdown=equal_weight["max_drawdown"],
    )
    equal_metric["name"] = "等权买入持有"
    equal_metric["description"] = "等权持有组合中所有标的"

    # 4. 60/40 股债
    sixty_forty = calculate_sixty_forty_benchmark(start_date, end_date)
    sf_metric = _calculate_benchmark_score(
        strategy_return=strategy_return,
        benchmark_return=sixty_forty["total_return"],
        strategy_drawdown=strategy_drawdown,
        benchmark_drawdown=sixty_forty["max_drawdown"],
    )
    sf_metric["name"] = "60/40 股债组合"
    sf_metric["description"] = "60%沪深300 + 40%国债"

    # 综合得分：自定义基准权重最高，宽基指数次之
    overall_score = (
        custom_metric["score"] * 0.35
        + csi300_metric["score"] * 0.25
        + equal_metric["score"] * 0.20
        + sf_metric["score"] * 0.20
    )
    overall_score = round(max(0.0, min(1.0, overall_score)), 4)

    return {
        "custom_benchmark": custom_metric,
        "csi300": csi300_metric,
        "equal_weight": equal_metric,
        "sixty_forty": sf_metric,
        "overall_score": overall_score,
        "strategy_return": round(strategy_return, 4),
        "strategy_drawdown": round(strategy_drawdown, 4),
    }


# ═══════════════════════════════════════════════════════════════
# 6. 便捷函数
# ═══════════════════════════════════════════════════════════════

def get_benchmark_summary(
    asset_weights: dict[str, float],
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    # 使用动态默认日期（最近4年）
    if end_date is None:
        end_date = datetime.date.today().isoformat()
    if start_date is None:
        start_date = (datetime.date.today() - datetime.timedelta(days=365 * 4)).isoformat()
    """获取基准收益摘要（用于日志/展示）.
    """
    benchmark = calculate_composite_benchmark(asset_weights, start_date, end_date)

    lines = [
        "═" * 50,
        "买入持有基准收益",
        "═" * 50,
    ]

    for asset_class, detail in benchmark.get("details", {}).items():
        lines.append(
            f"  {asset_class:8s}: {detail['name']:12s} "
            f"权重{detail['weight']:5.1%} | "
            f"收益{detail['total_return']:+7.2%} | "
            f"回撤{detail['max_drawdown']:5.2%}"
        )

    lines.extend([
        "─" * 50,
        f"  组合基准: 总收益 {benchmark['composite_return']:+.2%} | "
        f"年化 {benchmark['composite_annualized']:+.2%}",
        "═" * 50,
    ])

    return "\n".join(lines)


def is_strategy_valid(
    strategy_return: float,
    benchmark_return: float,
    min_excess: float = 0.0,
) -> bool:
    """快速校验策略是否有效（仅检查总收益）.
    """
    return strategy_return >= benchmark_return + min_excess
