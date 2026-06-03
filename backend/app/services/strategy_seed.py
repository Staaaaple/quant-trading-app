"""策略种子初始化 — 将35个通过验证的策略注入数据库.

使用方式:
    from app.services.strategy_seed import seed_strategies
    seed_strategies(db_session)
"""

from typing import Any
from sqlalchemy.orm import Session

from app.services.template_manager import create_template
from app.services.strategy_pool_final import STRATEGY_POOL


def _generate_strategy_code(strategy_id: str, params: dict) -> str:
    """生成策略代码字符串(用于数据库存储)."""
    param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
    return f"""
# 策略ID: {strategy_id}
# 核心逻辑: 动量-波动率评分
#   score = mom_weight * 动量(mom_window日) - vol_weight * 波动率(vol_window日)
#   score > 0 买入, score < 0 卖出

def run(symbol, df, params):
    import numpy as np
    import pandas as pd
    from app.services.template_runner import make_signal

    mom_window = {params.get('mom_window', 12)}
    vol_window = {params.get('vol_window', 25)}
    mom_weight = {params.get('mom_weight', 1.0)}
    vol_weight = {params.get('vol_weight', 2.0)}
    threshold = 0.0

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    df['score'] = mom_weight * df['mom'] - vol_weight * df['vol']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            continue
        if not in_position and row['score'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['score'] < threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals
"""


def seed_strategies(db: Session, clear_existing: bool = False) -> list[str]:
    """将35个通过验证的策略种子化到数据库.

    Args:
        db: 数据库会话
        clear_existing: 是否清除现有策略

    Returns:
        已创建的策略ID列表
    """
    if clear_existing:
        from app.models.strategy_template import StrategyTemplate
        db.query(StrategyTemplate).delete()
        db.commit()

    created_ids = []

    for strategy in STRATEGY_POOL:
        try:
            # 确定风险等级
            mom_window = strategy['params'].get('mom_window', 12)
            if mom_window <= 5:
                risk_level = "high"  # 高频交易，风险较高
            elif mom_window <= 10:
                risk_level = "medium"
            else:
                risk_level = "low"   # 低频交易，风险较低

            # 确定适用周期
            if mom_window <= 5:
                cycles = ["短线", "中线"]
            elif mom_window <= 10:
                cycles = ["中线"]
            else:
                cycles = ["中线", "长线"]

            code = _generate_strategy_code(strategy['id'], strategy['params'])

            tmpl = create_template(
                db=db,
                template_id=strategy['id'],
                name=strategy['name'],
                family="经典技术指标",  # 统一归类
                code=code,
                param_space=strategy['params'],
                suitable_cycles=cycles,
                risk_level=risk_level,
                description=f"{strategy['family']}策略: 动量窗口{mom_window}日, 波动率窗口{strategy['params'].get('vol_window', 25)}日",
            )

            created_ids.append(strategy['id'])

        except Exception as e:
            print(f"[Seed] 创建策略 {strategy['id']} 失败: {e}")
            continue

    print(f"[Seed] 成功创建 {len(created_ids)}/{len(STRATEGY_POOL)} 个策略")
    return created_ids


def get_strategy_count(db: Session) -> int:
    """获取数据库中策略数量."""
    from app.models.strategy_template import StrategyTemplate
    return db.query(StrategyTemplate).filter(StrategyTemplate.is_active == True).count()
