"""调节引擎 — 执行RAG质检建议的调节操作.

支持：权重调整、策略替换、标的替换、参数调优、风控校准
"""

import copy
from typing import Any


class AdjustmentEngine:
    """调节引擎."""

    @staticmethod
    def apply_saa_adjustments(
        saa_result: dict,
        adjustments: list[dict],
        risk_profile: dict | None = None,
    ) -> dict:
        """应用SAA调节（增强版，含冲突解决和验证）.

        Args:
            saa_result: 原始SAA结果
            adjustments: 调节建议列表
            risk_profile: 风险配置 {"stock_max": 0.5, ...}

        Returns:
            调节后的SAA结果
        """
        result = copy.deepcopy(saa_result)
        weights = result.get("weights", {})

        # ── 阶段1: 收集所有调节指令 ──
        caps: dict[str, float] = {}      # asset -> cap
        floors: dict[str, float] = {}    # asset -> floor
        set_weights: dict[str, float] | None = None
        hedge_adjustments: list[dict] = []

        for adj in adjustments:
            adj_type = adj.get("type", "")

            if adj_type == "set_weights":
                # set_weights 优先级最高，直接覆盖
                set_weights = adj.get("weights", {})

            elif adj_type == "weight_cap":
                asset = adj.get("asset", "")
                cap = adj.get("cap", 0)
                # 保留最严格的cap
                if asset not in caps or cap < caps[asset]:
                    caps[asset] = cap

            elif adj_type == "weight_floor":
                asset = adj.get("asset", "")
                floor = adj.get("floor", 0)
                # 保留最高的floor
                if asset not in floors or floor > floors[asset]:
                    floors[asset] = floor

            elif adj_type == "add_hedge":
                hedge_adjustments.append(adj)

        # ── 阶段2: 冲突解决 ──
        # 规则: cap 优先于 floor
        for asset in set(caps.keys()) & set(floors.keys()):
            if caps[asset] < floors[asset]:
                # 冲突: cap < floor，以cap为准，删除floor
                del floors[asset]

        # ── 阶段3: 应用调节 ──
        if set_weights:
            # 直接设置权重（最可靠，无矛盾）
            weights.update(set_weights)
        else:
            # 应用 cap
            for asset, cap in caps.items():
                if asset in weights and weights[asset] > cap:
                    excess = weights[asset] - cap
                    weights[asset] = cap
                    # 超额分配给债券（如债券也被cap，分配给现金）
                    if "bond" in weights and ("bond" not in caps or weights["bond"] + excess <= caps.get("bond", 1.0)):
                        weights["bond"] = weights.get("bond", 0) + excess
                    else:
                        weights["cash"] = weights.get("cash", 0) + excess

            # 应用 floor
            for asset, floor in floors.items():
                if asset in weights and weights[asset] < floor:
                    deficit = floor - weights[asset]
                    weights[asset] = floor
                    # 从股票中扣除（如股票不足，从现金扣）
                    if weights.get("stock", 0) >= deficit:
                        weights["stock"] -= deficit
                    elif weights.get("cash", 0) >= deficit:
                        weights["cash"] -= deficit
                    else:
                        # 从所有非目标资产按比例扣
                        others = [a for a in weights if a != asset]
                        total_others = sum(weights.get(a, 0) for a in others)
                        if total_others > 0:
                            for a in others:
                                weights[a] -= deficit * (weights[a] / total_others)

            # 应用 hedge
            for adj in hedge_adjustments:
                hedge_asset = adj.get("hedge_asset", "commodity")
                target = adj.get("target", 0.1)
                current = weights.get(hedge_asset, 0)
                if current < target:
                    deficit = target - current
                    weights[hedge_asset] = target
                    # 从股票中扣除
                    if weights.get("stock", 0) >= deficit:
                        weights["stock"] -= deficit
                    else:
                        weights["stock"] = 0
                        # 差额从现金补
                        weights["cash"] = max(0, weights.get("cash", 0) - (deficit - weights.get("stock", 0)))

        # ── 阶段4: 强制验证（硬约束）──
        # 确保所有权重 ≥ 0
        for k in weights:
            weights[k] = max(0.0, weights[k])

        # 风险画像硬约束
        if risk_profile:
            stock_max = risk_profile.get("stock_max", 0.90)
            bond_min = risk_profile.get("bond_min", 0.05)
            cash_min = risk_profile.get("cash_min", 0.03)

            # 股票上限强制截断
            if weights.get("stock", 0) > stock_max:
                excess = weights["stock"] - stock_max
                weights["stock"] = stock_max
                weights["bond"] = weights.get("bond", 0) + excess

            # 债券下限强制提升
            if weights.get("bond", 0) < bond_min:
                deficit = bond_min - weights["bond"]
                weights["bond"] = bond_min
                if weights.get("stock", 0) >= deficit:
                    weights["stock"] -= deficit

            # 现金下限强制提升
            if weights.get("cash", 0) < cash_min:
                deficit = cash_min - weights["cash"]
                weights["cash"] = cash_min
                if weights.get("stock", 0) >= deficit:
                    weights["stock"] -= deficit

        # ── 阶段5: 归一化 ──
        total = sum(weights.values())
        if total > 0 and abs(total - 1.0) > 0.001:
            for k in weights:
                weights[k] = round(weights[k] / total, 4)

        # 最终校验: 确保总和=1
        final_total = sum(weights.values())
        if final_total > 0 and abs(final_total - 1.0) > 0.001:
            # 将差额加到最大权重上
            max_asset = max(weights, key=weights.get)
            weights[max_asset] += round(1.0 - final_total, 4)

        result["weights"] = weights
        result["rag_adjusted"] = True
        return result

    @staticmethod
    def apply_taa_adjustments(
        taa_result: dict,
        adjustments: list[dict],
    ) -> dict:
        """应用TAA调节."""
        result = copy.deepcopy(taa_result)
        sectors = result.get("sector_weights", {})

        for adj in adjustments:
            adj_type = adj.get("type", "")

            if adj_type == "sector_cap":
                # 行业集中度上限
                sector = adj.get("sector", "")
                cap = adj.get("cap", 0.5)
                if sector in sectors and sectors[sector] > cap:
                    excess = sectors[sector] - cap
                    sectors[sector] = cap
                    # 分散到次优行业
                    # 简化处理：分配给"其他"
                    sectors["other"] = sectors.get("other", 0) + excess

            elif adj_type == "sector_replace":
                # 替换行业
                old_sector = adj.get("old_sector", "")
                new_sector = adj.get("new_sector", "")
                if old_sector in sectors:
                    weight = sectors.pop(old_sector)
                    sectors[new_sector] = sectors.get(new_sector, 0) + weight

            elif adj_type == "style_balance":
                # 风格平衡
                growth_weight = adj.get("growth_weight", 0.5)
                # 这里简化处理，实际应更复杂
                pass

        result["sector_weights"] = sectors
        result["rag_adjusted"] = True
        return result

    @staticmethod
    def apply_binding_adjustments(
        bindings: list[dict],
        adjustments: list[dict],
    ) -> list[dict]:
        """应用绑定调节.

        Returns:
            调节后的绑定列表 + 需要重新回测的标记
        """
        result = copy.deepcopy(bindings)
        needs_rebacktest = []

        for adj in adjustments:
            adj_type = adj.get("type", "")

            if adj_type == "param_change":
                # 参数调整
                symbol = adj.get("symbol", "")
                param_changes = adj.get("param_changes", {})
                for b in result:
                    if b.get("symbol") == symbol:
                        b["strategy_params"] = b.get("strategy_params", {})
                        b["strategy_params"].update(param_changes)
                        b["rag_adjusted"] = True
                        needs_rebacktest.append(symbol)

            elif adj_type == "strategy_replace":
                # 策略替换
                symbol = adj.get("symbol", "")
                new_strategy = adj.get("new_strategy", {})
                for b in result:
                    if b.get("symbol") == symbol:
                        b["strategy_id"] = new_strategy.get("id")
                        b["strategy_name"] = new_strategy.get("name")
                        b["strategy_family"] = new_strategy.get("family")
                        b["rag_adjusted"] = True
                        needs_rebacktest.append(symbol)

            elif adj_type == "symbol_replace":
                # 标的替换
                old_symbol = adj.get("old_symbol", "")
                new_symbol = adj.get("new_symbol", {})
                for b in result:
                    if b.get("symbol") == old_symbol:
                        b["symbol"] = new_symbol.get("symbol")
                        b["name"] = new_symbol.get("name")
                        b["rag_adjusted"] = True
                        needs_rebacktest.append(new_symbol.get("symbol"))

            elif adj_type == "exclude":
                # 排除标的
                symbol = adj.get("symbol", "")
                result = [b for b in result if b.get("symbol") != symbol]

        return result

    @staticmethod
    def apply_risk_adjustments(
        risk_config: dict,
        adjustments: list[dict],
    ) -> dict:
        """应用风控调节."""
        result = copy.deepcopy(risk_config)

        for adj in adjustments:
            # 处理字符串格式的调节建议（Mock LLM返回）
            if isinstance(adj, str):
                # 尝试从字符串中提取调节信息
                if "止损" in adj or "stop" in adj.lower():
                    # 提取数字
                    import re
                    numbers = re.findall(r'(\d+\.?\d*)%', adj)
                    if numbers:
                        result["stop_loss"] = float(numbers[0]) / 100
                elif "仓位" in adj or "position" in adj.lower():
                    import re
                    numbers = re.findall(r'(\d+\.?\d*)%', adj)
                    if numbers:
                        result["max_position"] = float(numbers[0]) / 100
                elif "回撤" in adj or "drawdown" in adj.lower():
                    import re
                    numbers = re.findall(r'(\d+\.?\d*)%', adj)
                    if numbers:
                        result["max_drawdown"] = float(numbers[0]) / 100
                continue

            # 处理字典格式的调节建议
            adj_type = adj.get("type", "")

            if adj_type == "stop_loss":
                result["stop_loss"] = adj.get("value", result.get("stop_loss", 0.08))

            elif adj_type == "max_position":
                result["max_position"] = adj.get("value", result.get("max_position", 0.2))

            elif adj_type == "max_drawdown":
                result["max_drawdown"] = adj.get("value", result.get("max_drawdown", 0.15))

            elif adj_type == "rebalance_threshold":
                result["rebalance_threshold"] = adj.get(
                    "value", result.get("rebalance_threshold", 0.05)
                )

            elif adj_type == "add_behavior_reminder":
                reminders = result.get("behavior_reminders", [])
                reminders.append(adj.get("reminder", ""))
                result["behavior_reminders"] = reminders

        result["rag_adjusted"] = True
        return result

    @staticmethod
    def apply_reliability_adjustments(
        portfolio: dict,
        adjustments: list[dict],
    ) -> dict:
        """应用可靠性调节.

        可靠性不通过时，可能需要调整权重或排除策略
        """
        result = copy.deepcopy(portfolio)

        for adj in adjustments:
            adj_type = adj.get("type", "")

            if adj_type == "weight_adjust":
                # 调整权重
                symbol = adj.get("symbol", "")
                new_weight = adj.get("weight", 0)
                for b in result.get("bindings", []):
                    if b.get("symbol") == symbol:
                        b["weight"] = new_weight

            elif adj_type == "exclude_strategy":
                # 排除策略
                symbol = adj.get("symbol", "")
                result["bindings"] = [
                    b for b in result.get("bindings", [])
                    if b.get("symbol") != symbol
                ]

            elif adj_type == "add_defensive":
                # 增配防御性资产
                pass  # 由SAA/TAA调节处理

        result["rag_adjusted"] = True
        return result


# 便捷函数
def apply_adjustments(
    step: str,
    current_result: dict | list,
    adjustments: list[dict],
    risk_profile: dict | None = None,
) -> tuple[Any, list[str]]:
    """应用调节建议.

    Args:
        step: 步骤名称
        current_result: 当前结果
        adjustments: 调节建议
        risk_profile: 风险配置 {"stock_max": 0.5, "bond_min": 0.3, ...}（仅SAA步骤）

    Returns:
        (调节后的结果, 需要重新回测的标的列表)
    """
    engine = AdjustmentEngine()
    needs_rebacktest = []

    if step == "saa":
        return engine.apply_saa_adjustments(current_result, adjustments, risk_profile), []

    elif step == "taa":
        return engine.apply_taa_adjustments(current_result, adjustments), []

    elif step == "binding":
        result = engine.apply_binding_adjustments(current_result, adjustments)
        # 提取需要重新回测的标的
        for b in result:
            if b.get("rag_adjusted"):
                needs_rebacktest.append(b.get("symbol"))
        return result, needs_rebacktest

    elif step == "risk_config":
        return engine.apply_risk_adjustments(current_result, adjustments), []

    elif step == "reliability":
        return engine.apply_reliability_adjustments(current_result, adjustments), []

    return current_result, []
