"""教学引导服务 — 生成4步个性化新手指引内容.

Phase D: 全链路服务
根据用户画像 + 组合配置 → 动态生成教学卡片内容.

4步教学:
1. 了解你的组合策略（为什么选这些标的+策略原理）
2. 挑选券商（不推具体券商，只给标准）
3. 建仓计划（分批买入方案）
4. 日常跟进（如何持续管理）
"""

from typing import Any


# ── 教学卡片模板库 ──

TEACHING_CARDS = {
    "strategy": {
        "momentum": {
            "title": "动量策略",
            "content": "动量策略基于'强者恒强'的市场现象。当某只ETF的价格趋势向上时，策略会继续持有；当趋势转弱时卖出。适合在市场上涨期使用。",
            "concept": "动量",
        },
        "mean_reversion": {
            "title": "均值回归策略",
            "content": "均值回归策略认为价格会围绕长期平均值波动。当价格偏离均值过远时，策略会反向操作——超卖时买入，超买时卖出。",
            "concept": "均值回归",
        },
        "trend_following": {
            "title": "趋势跟踪策略",
            "content": "趋势跟踪策略通过识别市场的中长期趋势来操作。当趋势向上时买入，趋势向下时卖出或空仓。适合趋势明显的市场环境。",
            "concept": "趋势跟踪",
        },
        "low_volatility": {
            "title": "低波动策略",
            "content": "低波动策略选择历史波动率较低的标的，利用'低波动异象'获取稳健收益。适合风险厌恶型投资者。",
            "concept": "低波动",
        },
        "multi_factor": {
            "title": "多因子策略",
            "content": "多因子策略同时考虑多个维度（价值、质量、动量、低波动等）来选股，通过分散因子风险提高稳健性。",
            "concept": "多因子",
        },
    },
    "market": {
        "expansion": {
            "title": "扩张期投资策略",
            "content": "经济扩张期，企业盈利增长，股市通常表现较好。此时适合增配股票类资产，尤其是周期性行业。",
        },
        "peak": {
            "title": "顶部期投资策略",
            "content": "经济顶部期，通胀压力上升，央行可能加息。此时应逐步降低股票仓位，增配债券和现金。",
        },
        "contraction": {
            "title": "收缩期投资策略",
            "content": "经济收缩期，企业盈利下滑，股市承压。此时应以防御为主，增配债券、黄金等避险资产。",
        },
        "recovery": {
            "title": "复苏期投资策略",
            "content": "经济复苏期，政策宽松，市场信心恢复。此时适合逐步建仓，关注前期跌幅较大的优质资产。",
        },
    },
    "risk": {
        "stop_loss": {
            "title": "止损线",
            "content": "止损线是预先设定的最大亏损比例。当组合亏损达到该比例时，系统会提醒考虑减仓或调仓，防止亏损进一步扩大。",
        },
        "rebalance": {
            "title": "再平衡",
            "content": "再平衡是指定期将组合权重调整回目标配置。例如股票涨多了占比过高，就卖出一部分股票买入债券，维持原定风险水平。",
        },
        "max_drawdown": {
            "title": "最大回撤控制",
            "content": "最大回撤是指从最高点到最低点的最大跌幅。设置最大回撤硬止损可以在极端行情下保护本金。",
        },
    },
    "operation": {
        "batch_build": {
            "title": "分批建仓",
            "content": "分批建仓是将资金分成多笔投入，而不是一次性全买。这样可以降低'买在高点'的风险，平滑建仓成本。",
        },
        "dca": {
            "title": "定投策略",
            "content": "定投（定期定额投资）是指在固定时间投入固定金额。长期坚持定投可以摊平成本，降低择时压力。",
        },
    },
}


# ── 券商挑选标准 ──

BROKER_CRITERIA = [
    {
        "category": "交易成本",
        "items": [
            "股票佣金率 ≤ 0.025%（万2.5）",
            "ETF交易免最低5元限制",
            "基金申购费1折优惠",
        ],
    },
    {
        "category": "APP体验",
        "items": [
            "支持条件单（止盈止损/网格交易）",
            "智能盯盘和推送提醒",
            "界面简洁，操作流畅",
        ],
    },
    {
        "category": "投研服务",
        "items": [
            "提供研报和市场分析",
            "有投顾咨询服务",
            "新手教学资源丰富",
        ],
    },
    {
        "category": "资金安全",
        "items": [
            "大型券商，资金实力雄厚",
            "支持第三方存管",
            "有完善的客户服务体系",
        ],
    },
]


# ── 日常跟进指南 ──

DAILY_GUIDE = {
    "daily": {
        "title": "每日查看",
        "items": [
            "开盘前查看今日操作推送（有操作才推）",
            "无操作时显示'今日持有'，无需操作",
            "关注市场重大新闻和公告",
        ],
    },
    "weekly": {
        "title": "每周回顾",
        "items": [
            "每周五查看周报（收益/市场回顾/下周展望）",
            "检查组合偏离度，是否触发再平衡",
            "关注策略寿命变化",
        ],
    },
    "monthly": {
        "title": "每月检查",
        "items": [
            "查看月度收益报告",
            "评估是否需要调整画像",
            "检查是否有策略寿命到期预警",
        ],
    },
    "quarterly": {
        "title": "季度调仓",
        "items": [
            "执行季度再平衡",
            "根据市场周期变化调整配置",
            "替换到期或失效的策略",
        ],
    },
}


def generate_step1_strategy_reasoning(
    profile: dict[str, Any],
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    """Step1: 生成组合策略原理说明.

    根据用户画像风险等级和市场周期，解释为什么选这些标的和策略.
    """
    risk_label = profile.get("risk_label", "稳健型")
    market_cycle = portfolio.get("market_cycle", "复苏期")
    holdings = portfolio.get("holdings", [])
    saa_weights = portfolio.get("saa_weights", {})

    # 根据风险等级生成说明
    risk_explanations = {
        "保守型": "你的风险承受能力较低，组合以债券和现金为主，股票占比控制在30%以内，追求稳健收益。",
        "稳健型": "你的风险承受能力适中，组合股债平衡，股票占比约40-50%，在控制风险的同时获取合理收益。",
        "积极型": "你的风险承受能力较高，组合以股票为主，占比约60-70%，愿意承担更大波动以追求更高收益。",
        "激进型": "你的风险承受能力很高，组合股票占比可达80%以上，追求最大化收益，能承受较大回撤。",
    }

    # 根据市场周期生成说明
    cycle_explanations = {
        "expansion": "当前处于经济扩张期，企业盈利增长，适合增配股票类资产。",
        "peak": "当前处于经济顶部期，需警惕回调风险，逐步降低股票仓位。",
        "contraction": "当前处于经济收缩期，以防御为主，增配债券和避险资产。",
        "recovery": "当前处于复苏期，市场信心恢复，适合逐步增配股票。",
    }

    # 为每个持仓生成策略说明
    holding_cards = []
    for h in holdings:
        strategy_type = h.get("strategy_type", "multi_factor")
        card = TEACHING_CARDS["strategy"].get(
            strategy_type,
            {
                "title": "多因子策略",
                "content": "该策略综合考虑多个维度进行资产配置，通过分散风险提高稳健性。",
                "concept": "多因子",
            }
        )
        holding_cards.append({
            "symbol": h.get("symbol", ""),
            "name": h.get("name", ""),
            "weight": h.get("weight", 0),
            "strategy_name": card["title"],
            "strategy_explanation": card["content"],
            "concept": card["concept"],
        })

    return {
        "step": 1,
        "title": "了解你的组合策略",
        "subtitle": "为什么选这些标的？",
        "profile_explanation": risk_explanations.get(risk_label, risk_explanations["稳健型"]),
        "market_explanation": cycle_explanations.get(market_cycle, cycle_explanations["recovery"]),
        "holdings": holding_cards,
        "asset_allocation": saa_weights,
    }


def generate_step2_broker_guide() -> dict[str, Any]:
    """Step2: 生成券商挑选指南.

    不推具体券商，只给挑选标准.
    """
    return {
        "step": 2,
        "title": "挑选券商",
        "subtitle": "不推具体券商，只给挑选标准",
        "note": "建议选择大型券商，资金安全有保障。不要轻信'免佣金'等过度营销。",
        "criteria": BROKER_CRITERIA,
        "common_brokers": [
            {"name": "华泰证券", "feature": "APP体验好，条件单功能强"},
            {"name": "中信证券", "feature": "综合实力强，研报资源丰富"},
            {"name": "国泰君安", "feature": "客户服务好，线下网点多"},
            {"name": "招商证券", "feature": "APP简洁，适合新手"},
        ],
    }


def generate_step3_building_plan(
    profile: dict[str, Any],
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    """Step3: 生成分批建仓计划.

    根据资金规模和组合配置，生成分批买入方案.
    """
    capital_tier = profile.get("capital_tier", 5)
    total_capital = _capital_tier_to_amount(capital_tier)

    # 根据风险等级确定分批次数
    risk_label = profile.get("risk_label", "稳健型")
    batch_config = {
        "保守型": {"batches": 4, "interval_days": 14, "first_pct": 0.25},
        "稳健型": {"batches": 3, "interval_days": 14, "first_pct": 0.40},
        "积极型": {"batches": 3, "interval_days": 10, "first_pct": 0.50},
        "激进型": {"batches": 2, "interval_days": 7, "first_pct": 0.60},
    }
    config = batch_config.get(risk_label, batch_config["稳健型"])

    # 生成每批计划
    batches = []
    remaining_pct = 1.0
    for i in range(config["batches"]):
        if i == 0:
            pct = config["first_pct"]
        elif i == config["batches"] - 1:
            pct = remaining_pct
        else:
            pct = remaining_pct / (config["batches"] - i)
        remaining_pct -= pct

        amount = total_capital * pct
        week = i + 1

        batches.append({
            "batch_no": i + 1,
            "timing": f"第{week}批" + ("(本周)" if i == 0 else f"({i * config['interval_days']}天后)"),
            "amount": round(amount, 2),
            "percentage": round(pct * 100, 1),
            "focus": _get_batch_focus(i, portfolio),
        })

    return {
        "step": 3,
        "title": "建仓计划",
        "subtitle": "分批买入，降低择时风险",
        "total_capital": total_capital,
        "batches": batches,
        "tips": [
            "市场大跌时可适当加快建仓节奏",
            "市场大涨时可适当放缓，避免追高",
            "每批买入后记录成本，便于后续管理",
        ],
    }


def generate_step4_daily_guide() -> dict[str, Any]:
    """Step4: 生成日常跟进指南."""
    return {
        "step": 4,
        "title": "日常跟进",
        "subtitle": "如何持续管理你的组合",
        "guide": DAILY_GUIDE,
        "push_settings": {
            "title": "推送偏好设置",
            "options": [
                {"key": "daily_op", "label": "每日操作提醒", "default": True},
                {"key": "weekly_report", "label": "周报推送", "default": True},
                {"key": "lifespan_alert", "label": "寿命预警", "default": True},
                {"key": "rebalance_alert", "label": "再平衡提醒", "default": True},
                {"key": "cycle_alert", "label": "周期切换提醒", "default": False},
            ],
        },
    }


def generate_full_onboarding(
    profile: dict[str, Any],
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    """生成完整的4步教学引导内容.

    Args:
        profile: 用户画像（含risk_label, capital_tier等）
        portfolio: 组合配置（含holdings, saa_weights等）

    Returns:
        4步教学引导的完整内容
    """
    return {
        "user_id": profile.get("user_id"),
        "portfolio_id": portfolio.get("id"),
        "steps": [
            generate_step1_strategy_reasoning(profile, portfolio),
            generate_step2_broker_guide(),
            generate_step3_building_plan(profile, portfolio),
            generate_step4_daily_guide(),
        ],
        "teaching_cards": _collect_all_teaching_cards(profile, portfolio),
    }


def get_teaching_card(card_id: str) -> dict[str, Any] | None:
    """获取单个教学卡片内容."""
    for category in TEACHING_CARDS.values():
        if card_id in category:
            return category[card_id]
    return None


def _capital_tier_to_amount(tier: int) -> float:
    """将资金等级转换为具体金额."""
    mapping = {
        1: 10000,
        2: 30000,
        3: 50000,
        4: 100000,
        5: 200000,
        6: 500000,
        7: 1000000,
        8: 3000000,
        9: 5000000,
        10: 10000000,
    }
    return mapping.get(tier, 100000)


def _get_batch_focus(batch_index: int, portfolio: dict[str, Any]) -> str:
    """确定每批建仓的重点."""
    holdings = portfolio.get("holdings", [])
    if not holdings:
        return "按目标配置比例买入"

    # 按权重排序
    sorted_holdings = sorted(holdings, key=lambda x: x.get("weight", 0), reverse=True)

    if batch_index == 0:
        # 第一批：买入权重最大的1-2个
        top = sorted_holdings[:2]
        names = [h.get("name", h.get("symbol", "")) for h in top]
        return f"优先买入: {', '.join(names)}"
    elif batch_index == 1:
        # 第二批：买入中等权重的
        mid = sorted_holdings[2:4] if len(sorted_holdings) > 2 else sorted_holdings[1:3]
        names = [h.get("name", h.get("symbol", "")) for h in mid]
        return f"继续配置: {', '.join(names)}"
    else:
        # 最后一批：补齐剩余
        return "补齐剩余仓位，完成配置"


def _collect_all_teaching_cards(
    profile: dict[str, Any],
    portfolio: dict[str, Any],
) -> list[dict[str, Any]]:
    """收集所有相关的教学卡片."""
    cards = []

    # 添加策略相关卡片
    for h in portfolio.get("holdings", []):
        st = h.get("strategy_type", "")
        if st in TEACHING_CARDS["strategy"]:
            card = TEACHING_CARDS["strategy"][st].copy()
            card["related_symbol"] = h.get("symbol", "")
            cards.append(card)

    # 添加市场周期卡片
    cycle = portfolio.get("market_cycle", "")
    if cycle in TEACHING_CARDS["market"]:
        cards.append(TEACHING_CARDS["market"][cycle])

    # 添加风控卡片
    cards.append(TEACHING_CARDS["risk"]["stop_loss"])
    cards.append(TEACHING_CARDS["risk"]["rebalance"])

    # 添加操作卡片
    cards.append(TEACHING_CARDS["operation"]["batch_build"])

    return cards
