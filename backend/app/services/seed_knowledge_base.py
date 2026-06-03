"""知识库种子数据初始化.

Phase B 初始化 3个核心模板（经典技术指标家族）+ 2篇示例论文.
"""

from sqlalchemy.orm import Session

from app.models.strategy_template import StrategyTemplate
from app.models.paper_knowledge import PaperKnowledge


def seed_templates(db: Session) -> int:
    """初始化策略模板种子数据."""
    count = 0

    templates = [
        {
            "template_id": "tmpl_ma_crossover",
            "name": "双均线交叉策略",
            "family": "经典技术指标",
            "description": "短期均线上穿长期均线时买入（金叉），下穿时卖出（死叉）。",
            "code": "# 双均线交叉\ndef run(df, params):\n    fast = params.get('fast_ma', 5)\n    slow = params.get('slow_ma', 20)\n    df['fast'] = df['close'].rolling(fast).mean()\n    df['slow'] = df['close'].rolling(slow).mean()\n    # 金叉/死叉逻辑...\n    return signals",
            "param_space": {
                "fast_ma": {"type": "int", "range": [3, 5, 10, 15], "default": 5},
                "slow_ma": {"type": "int", "range": [20, 30, 60], "default": 20},
            },
            "suitable_cycles": ["复苏", "过热"],
            "risk_level": "稳健",
            "asset_classes": ["stock", "etf"],
        },
        {
            "template_id": "tmpl_rsi_reversal",
            "name": "RSI超买超卖策略",
            "family": "经典技术指标",
            "description": "RSI低于超卖线时买入，高于超买线时卖出。",
            "code": "# RSI策略\ndef run(df, params):\n    period = params.get('period', 14)\n    oversold = params.get('oversold', 30)\n    overbought = params.get('overbought', 70)\n    # RSI计算...\n    return signals",
            "param_space": {
                "period": {"type": "int", "range": [7, 14, 21], "default": 14},
                "oversold": {"type": "int", "range": [20, 25, 30], "default": 30},
                "overbought": {"type": "int", "range": [70, 75, 80], "default": 70},
            },
            "suitable_cycles": ["复苏", "衰退"],
            "risk_level": "稳健",
            "asset_classes": ["stock", "etf"],
        },
        {
            "template_id": "tmpl_boll_breakout",
            "name": "布林带突破策略",
            "family": "经典技术指标",
            "description": "价格突破布林带上轨买入，跌破下轨卖出。",
            "code": "# 布林带策略\ndef run(df, params):\n    period = params.get('period', 20)\n    std = params.get('std', 2.0)\n    # 布林带计算...\n    return signals",
            "param_space": {
                "period": {"type": "int", "range": [10, 20, 30], "default": 20},
                "std": {"type": "float", "range": [1.5, 2.0, 2.5], "default": 2.0},
            },
            "suitable_cycles": ["过热", "滞胀"],
            "risk_level": "积极",
            "asset_classes": ["stock", "etf"],
        },
    ]

    for t in templates:
        exists = db.query(StrategyTemplate).filter(
            StrategyTemplate.template_id == t["template_id"]
        ).first()
        if not exists:
            tmpl = StrategyTemplate(
                template_id=t["template_id"],
                name=t["name"],
                family=t["family"],
                description=t["description"],
                code=t["code"],
                param_space=t["param_space"],
                suitable_cycles=t["suitable_cycles"],
                risk_level=t["risk_level"],
                asset_classes=t["asset_classes"],
                health_score=65.0,
                lifespan_months=15.0,
            )
            db.add(tmpl)
            count += 1

    if count > 0:
        db.commit()
    return count


def seed_papers(db: Session) -> int:
    """初始化论文知识库种子数据."""
    count = 0

    papers = [
        {
            "title": "The Cross-Section of Expected Stock Returns",
            "authors": "Eugene F. Fama, Kenneth R. French",
            "arxiv_id": None,
            "publish_date": "1992-06",
            "family": "因子挖掘",
            "core_conclusion": "市值、账面市值比、市盈率等因子对股票收益有显著解释力，提出Fama-French三因子模型。",
            "key_findings": [
                "SMB（市值因子）和HML（价值因子）能显著解释股票收益差异",
                "Beta单独不能解释横截面收益差异",
                "小市值公司和低市净率公司长期跑赢市场",
            ],
            "param_space": {
                "lookback": {"range": [6, 12, 24], "default": 12},
                "rebalance_freq": {"range": ["monthly", "quarterly"], "default": "monthly"},
            },
            "suitable_cycles": ["复苏", "过热", "滞胀", "衰退"],
            "suitable_markets": ["A股", "美股"],
            "backtest_sharpe": 0.85,
            "backtest_max_drawdown": 0.22,
            "backtest_win_rate": 0.55,
            "backtest_annual_return": 0.12,
            "related_template_ids": ["tmpl_ff_3factor"],
        },
        {
            "title": "Dual Momentum Investing: An Innovative Strategy for Higher Returns with Lower Risk",
            "authors": "Gary Antonacci",
            "arxiv_id": None,
            "publish_date": "2014-01",
            "family": "经典技术指标",
            "core_conclusion": "绝对动量+相对动量的双重动量策略能在降低风险的同时提高收益。",
            "key_findings": [
                "绝对动量过滤掉下跌趋势中的资产",
                "相对动量选择表现最好的资产类别",
                "组合使用可降低最大回撤30%以上",
            ],
            "param_space": {
                "lookback_months": {"range": [3, 6, 12], "default": 12},
                "rebalance_freq": {"range": ["monthly", "quarterly"], "default": "monthly"},
            },
            "suitable_cycles": ["复苏", "过热"],
            "suitable_markets": ["A股", "美股", "全球"],
            "backtest_sharpe": 1.05,
            "backtest_max_drawdown": 0.15,
            "backtest_win_rate": 0.58,
            "backtest_annual_return": 0.14,
            "related_template_ids": ["tmpl_dual_momentum"],
        },
    ]

    for p in papers:
        exists = db.query(PaperKnowledge).filter(
            PaperKnowledge.title == p["title"]
        ).first()
        if not exists:
            paper = PaperKnowledge(
                title=p["title"],
                authors=p["authors"],
                arxiv_id=p["arxiv_id"],
                publish_date=p["publish_date"],
                family=p["family"],
                core_conclusion=p["core_conclusion"],
                key_findings=p["key_findings"],
                param_space=p["param_space"],
                suitable_cycles=p["suitable_cycles"],
                suitable_markets=p["suitable_markets"],
                backtest_sharpe=p["backtest_sharpe"],
                backtest_max_drawdown=p["backtest_max_drawdown"],
                backtest_win_rate=p["backtest_win_rate"],
                backtest_annual_return=p["backtest_annual_return"],
                related_template_ids=p["related_template_ids"],
            )
            db.add(paper)
            count += 1

    if count > 0:
        db.commit()
    return count
