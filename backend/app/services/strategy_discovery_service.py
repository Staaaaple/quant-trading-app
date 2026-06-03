"""策略发现服务 — 统一入口.

提供策略发现、验证、注册的完整流程.
策略部分先留出接口，后续可替换为真实策略.
"""

from typing import Any
from sqlalchemy.orm import Session

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_manager import create_template


# ═══════════════════════════════════════════════════════════════
# 策略接口（可替换）
# ═══════════════════════════════════════════════════════════════

# 当前使用：基于论文的策略池
# 后续可替换为：遗传算法发现、强化学习发现、LLM生成等
try:
    from app.services.strategy_pool_papers import STRATEGY_POOL as _PAPER_STRATEGIES
    DEFAULT_STRATEGIES = _PAPER_STRATEGIES
except ImportError:
    DEFAULT_STRATEGIES = []


# ═══════════════════════════════════════════════════════════════
# 核心服务函数
# ═══════════════════════════════════════════════════════════════

def discover_and_validate(
    target_count: int = 35,
    verbose: bool = False,
    custom_strategies: list[dict] | None = None,
) -> list[dict]:
    """发现并验证策略.

    Args:
        target_count: 目标策略数量
        verbose: 是否打印详情
        custom_strategies: 自定义策略列表（覆盖默认）

    Returns:
        通过验证的策略列表
    """
    strategies = custom_strategies or DEFAULT_STRATEGIES

    if not strategies:
        if verbose:
            print("[DiscoveryService] 警告: 策略池为空")
        return []

    if verbose:
        print(f"[DiscoveryService] 开始验证 {len(strategies)} 个策略")

    data_pool = preload_all_data()
    passed = []

    for strategy in strategies:
        result = validate_template(
            strategy['id'],
            'technical_indicator',
            strategy['func'],
            strategy['params'],
            data_pool=data_pool,
            verbose=verbose,
        )

        if result['passed']:
            passed.append({
                **strategy,
                'validation': {
                    'win_rate': result['overall']['avg_win_rate'],
                    'max_drawdown': result['overall']['worst_drawdown'],
                    'avg_return': result['overall']['avg_strategy_return'],
                }
            })
            if verbose:
                print(f"  ✅ {strategy['name']} 通过")
        else:
            if verbose:
                print(f"  ❌ {strategy['name']} 失败 ({len(result['fail_reasons'])}项)")

        if len(passed) >= target_count:
            break

    if verbose:
        print(f"[DiscoveryService] 完成: {len(passed)} 个策略通过验证")

    return passed


def register_strategies_to_db(
    db: Session,
    strategies: list[dict],
    clear_existing: bool = False,
) -> list[str]:
    """将策略注册到数据库.

    Args:
        db: 数据库会话
        strategies: 通过验证的策略列表
        clear_existing: 是否清除现有策略

    Returns:
        已注册的策略ID列表
    """
    if clear_existing:
        from app.models.strategy_template import StrategyTemplate
        db.query(StrategyTemplate).filter(
            StrategyTemplate.template_id.like("discovered_%")
        ).delete()
        db.commit()

    registered = []

    for strategy in strategies:
        try:
            # 生成策略代码
            code = _generate_strategy_code(strategy)

            # 确定风险等级
            mom_window = strategy['params'].get('mom_window', 12)
            if mom_window <= 5:
                risk_level = "high"
            elif mom_window <= 10:
                risk_level = "medium"
            else:
                risk_level = "low"

            # 确定适用周期
            if mom_window <= 5:
                cycles = ["短线", "中线"]
            elif mom_window <= 10:
                cycles = ["中线"]
            else:
                cycles = ["中线", "长线"]

            # 获取论文引用
            paper = strategy.get('paper', 'Unknown')

            tmpl = create_template(
                db=db,
                template_id=f"discovered_{strategy['id']}",
                name=strategy['name'],
                family="经典技术指标",
                code=code,
                param_space=strategy['params'],
                suitable_cycles=cycles,
                risk_level=risk_level,
                description=f"{strategy.get('family', '策略')} | 来源: {paper}",
            )

            # 更新健康分数
            if 'validation' in strategy:
                tmpl.health_score = min(100, strategy['validation']['win_rate'] * 100)
                db.commit()

            registered.append(strategy['id'])

        except Exception as e:
            print(f"[DiscoveryService] 注册策略 {strategy['id']} 失败: {e}")
            continue

    print(f"[DiscoveryService] 成功注册 {len(registered)}/{len(strategies)} 个策略")
    return registered


def _generate_strategy_code(strategy: dict) -> str:
    """生成策略代码字符串."""
    params_str = ", ".join([f"{k}={v}" for k, v in strategy['params'].items()])
    return f"""
# 策略ID: {strategy['id']}
# 名称: {strategy['name']}
# 来源: {strategy.get('paper', 'Unknown')}
# 参数: {params_str}

def run(symbol, df, params):
    from app.services.template_runner import make_signal
    import pandas as pd
    import numpy as np

    # 策略逻辑由外部函数提供
    # 实际运行时通过 strategy['func'] 调用
    return []
"""


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def get_strategy_pool() -> list[dict]:
    """获取当前策略池（不验证）."""
    return DEFAULT_STRATEGIES.copy()


def get_strategy_pool_size() -> int:
    """获取策略池大小."""
    return len(DEFAULT_STRATEGIES)


def run_discovery_pipeline(
    db: Session,
    target_count: int = 35,
    auto_register: bool = True,
    verbose: bool = True,
) -> dict[str, Any]:
    """运行完整的策略发现流水线.

    Args:
        db: 数据库会话
        target_count: 目标策略数量
        auto_register: 是否自动注册到数据库
        verbose: 是否打印详情

    Returns:
        {
            "discovered": int,
            "validated": int,
            "registered": int,
            "strategies": list[str],
        }
    """
    if verbose:
        print("=" * 80)
        print("[DiscoveryPipeline] 启动策略发现流水线")
        print("=" * 80)

    # Step 1: 获取策略池
    pool = get_strategy_pool()
    discovered = len(pool)

    if verbose:
        print(f"\n[Step 1] 策略池: {discovered} 个策略")

    # Step 2: 验证策略
    passed = discover_and_validate(
        target_count=target_count,
        verbose=verbose,
    )
    validated = len(passed)

    if verbose:
        print(f"\n[Step 2] 验证通过: {validated} 个策略")

    # Step 3: 注册到数据库
    registered = 0
    strategy_ids = []

    if auto_register and validated > 0:
        strategy_ids = register_strategies_to_db(db, passed, clear_existing=True)
        registered = len(strategy_ids)

        if verbose:
            print(f"\n[Step 3] 注册成功: {registered} 个策略")

    result = {
        "discovered": discovered,
        "validated": validated,
        "registered": registered,
        "strategies": strategy_ids,
        "target": target_count,
    }

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryPipeline] 完成: 发现{discovered} -> 验证{validated} -> 注册{registered}")
        print("=" * 80)

    return result
