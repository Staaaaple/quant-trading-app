"""流水线策略代码生成引擎.

将可视化流水线配置编译为标准 akquant Strategy Python 代码.
生成的代码包含 DNA 测序所需的关键词，确保与现有生态系统兼容.
"""

from typing import Any


# ── 指标辅助函数模板 ──

_INDICATOR_HELPERS = """
    def _calc_rsi(self, closes, period=14):
        import pandas as pd
        s = pd.Series(closes)
        delta = s.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50.0

    def _macd(self, closes, fast=12, slow=26, signal=9):
        import pandas as pd
        s = pd.Series(closes)
        ema_fast = s.ewm(span=fast, adjust=False).mean()
        ema_slow = s.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        hist = dif - dea
        return dif.iloc[-1], dea.iloc[-1], hist.iloc[-1], hist.iloc[-2] if len(hist) > 1 else 0.0

    def _kdj(self, highs, lows, closes, n=9, m1=3, m2=3):
        import pandas as pd
        h, l, c = pd.Series(highs), pd.Series(lows), pd.Series(closes)
        lowest_l = l.rolling(window=n, min_periods=n).min()
        highest_h = h.rolling(window=n, min_periods=n).max()
        rsv = (c - lowest_l) / (highest_h - lowest_l) * 100
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        return k.iloc[-1], d.iloc[-1], j.iloc[-1]

    def _boll(self, closes, period=20, std_dev=2):
        import pandas as pd
        s = pd.Series(closes)
        middle = s.rolling(window=period).mean().iloc[-1]
        std = s.rolling(window=period).std().iloc[-1]
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        return upper, middle, lower
"""


def generate_code(config: dict[str, Any]) -> str:
    """将流水线配置编译为 Python 策略代码."""
    stages = config.get("stages", [])
    if not stages:
        raise ValueError("流水线配置为空")

    # 按阶段类型分组
    stage_map: dict[str, list[dict]] = {
        "init": [],
        "indicator": [],
        "risk": [],
        "signal": [],
        "action": [],
    }
    for s in stages:
        stype = s.get("type")
        if stype in stage_map:
            stage_map[stype].append(s)

    # 收集信号组的 direction 信息，供 action 阶段使用
    signal_directions: dict[str, str] = {}
    for s in stage_map["signal"]:
        for group in s.get("config", {}).get("groups", []):
            signal_directions[group["id"]] = group.get("direction", "buy")

    lines: list[str] = []
    lines.append("from akquant import Strategy")
    lines.append("")
    lines.append("")
    lines.append("class PipelineStrategy(Strategy):")
    lines.append('    """流水线生成策略 — 由可视化配置自动生成."""')
    lines.append("")
    lines.append("    def __init__(self):")
    lines.append("        super().__init__()")
    lines.append("        self._indicators = {}")
    lines.append("        self._indicators_prev = {}")
    lines.append("        self._peak_equity = 0.0")
    lines.append("        self._risk_state = {}")
    lines.append("        self._risk_blocks = []")
    lines.append("")

    # 指标辅助函数
    need_helpers = _needs_indicator_helpers(stage_map)
    if need_helpers:
        for hl in _INDICATOR_HELPERS.strip().split("\n"):
            lines.append(hl)
        lines.append("")

    lines.append("    def on_bar(self, bar):")
    lines.append("        symbol = bar.symbol")
    lines.append("")
    lines.append("        # 保存前一日指标值（用于上穿/下穿判断）")
    lines.append("        self._indicators_prev = dict(self._indicators)")
    lines.append("")

    # Stage 1: Init
    init_code = _gen_init_code(stage_map["init"])
    for c in init_code:
        lines.append(c)
    if init_code:
        lines.append("")

    # Stage 2: Indicators
    ind_code = _gen_indicator_code(stage_map["indicator"])
    for c in ind_code:
        lines.append(c)
    if ind_code:
        lines.append("")

    # Stage 3: Risk
    risk_code = _gen_risk_code(stage_map["risk"])
    for c in risk_code:
        lines.append(c)
    if risk_code:
        lines.append("")

    # Stage 4: Signals
    signal_code = _gen_signal_code(stage_map["signal"])
    for c in signal_code:
        lines.append(c)
    if signal_code:
        lines.append("")

    # Stage 5: Actions
    action_code = _gen_action_code(stage_map["action"], signal_directions)
    for c in action_code:
        lines.append(c)

    return "\n".join(lines) + "\n"


def _needs_indicator_helpers(stage_map: dict) -> bool:
    """检查是否需要生成指标辅助函数."""
    for s in stage_map.get("indicator", []):
        for ind in s.get("config", {}).get("indicators", []):
            if ind.get("type") in ("RSI", "MACD", "KDJ", "BOLL"):
                return True
    return False


def _gen_init_code(init_stages: list[dict]) -> list[str]:
    """生成初始化阶段代码."""
    lines = []
    lines.append("# === Stage: 初始化 ===")
    for s in init_stages:
        cfg = s.get("config", {})
        depth = cfg.get("history_depth", 30)
        max_pos = cfg.get("max_position_pct", 0.95)
        lines.append(f"        self.set_history_depth({depth})")
        lines.append(f"        self._max_position_pct = {max_pos}")
    return lines


def _gen_indicator_code(ind_stages: list[dict]) -> list[str]:
    """生成指标计算阶段代码."""
    lines = []
    lines.append("# === Stage: 指标计算 ===")

    all_indicators: list[dict] = []
    for s in ind_stages:
        all_indicators.extend(s.get("config", {}).get("indicators", []))

    if not all_indicators:
        lines.append("        pass")
        return lines

    # 计算需要的最大历史深度
    max_period = 0
    for ind in all_indicators:
        itype = ind.get("type", "")
        period = ind.get("period", 5)
        if itype == "MA":
            max_period = max(max_period, period + 1)
        elif itype == "EMA":
            max_period = max(max_period, period + 1)
        elif itype == "RSI":
            max_period = max(max_period, period + 1)
        elif itype == "MACD":
            max_period = max(max_period, 60)
        elif itype == "KDJ":
            max_period = max(max_period, period + 1)
        elif itype == "BOLL":
            max_period = max(max_period, period + 1)

    if max_period > 0:
        lines.append(f"        _hist = self.get_history({max_period}, symbol)")
        lines.append("        if len(_hist) < 2:")
        lines.append("            return")
        lines.append("        import pandas as pd")
        lines.append("        _df = pd.DataFrame(_hist)")
        lines.append('        _closes = _df["close"].values if "close" in _df.columns else []')
        lines.append('        _highs = _df["high"].values if "high" in _df.columns else []')
        lines.append('        _lows = _df["low"].values if "low" in _df.columns else []')
        lines.append("")

    for ind in all_indicators:
        name = ind["name"]
        itype = ind["type"]
        period = ind.get("period", 5)
        field = ind.get("field", "close")

        if itype == "MA":
            lines.append(f"        self._indicators['{name}'] = _closes[-{period}:].mean() if len(_closes) >= {period} else 0.0")
        elif itype == "EMA":
            lines.append(f"        self._indicators['{name}'] = pd.Series(_closes).ewm(span={period}, adjust=False).mean().iloc[-1] if len(_closes) >= {period} else 0.0")
        elif itype == "RSI":
            lines.append(f"        self._indicators['{name}'] = self._calc_rsi(_closes, {period}) if len(_closes) >= {period} + 1 else 50.0")
        elif itype == "MACD":
            lines.append(f"        _dif, _dea, _hist_now, _hist_prev = self._macd(pd.Series(_closes), 12, 26, 9) if len(_closes) >= 35 else (0, 0, 0, 0)")
            lines.append(f"        self._indicators['{name}_dif'] = _dif")
            lines.append(f"        self._indicators['{name}_dea'] = _dea")
            lines.append(f"        self._indicators['{name}_hist'] = _hist_now")
        elif itype == "KDJ":
            lines.append(f"        _k, _d, _j = self._kdj(_highs, _lows, _closes, {period}) if len(_closes) >= {period} else (50, 50, 50)")
            lines.append(f"        self._indicators['{name}_k'] = _k")
            lines.append(f"        self._indicators['{name}_d'] = _d")
            lines.append(f"        self._indicators['{name}_j'] = _j")
        elif itype == "BOLL":
            lines.append(f"        _upper, _middle, _lower = self._boll(pd.Series(_closes), {period}) if len(_closes) >= {period} else (0, 0, 0)")
            lines.append(f"        self._indicators['{name}_upper'] = _upper")
            lines.append(f"        self._indicators['{name}_middle'] = _middle")
            lines.append(f"        self._indicators['{name}_lower'] = _lower")
        elif itype == "PRICE":
            lines.append(f"        self._indicators['{name}'] = bar.{field}")
        elif itype == "VOLUME":
            lines.append(f"        self._indicators['{name}'] = bar.volume")

    return lines


def _gen_risk_code(risk_stages: list[dict]) -> list[str]:
    """生成风控检查阶段代码."""
    lines = []
    lines.append("# === Stage: 风控检查 ===")
    lines.append("        _allow_buy = True")
    lines.append("        _allow_sell = True")
    lines.append("        _current_equity = self.get_portfolio_value()")
    lines.append("        if _current_equity > self._peak_equity:")
    lines.append("            self._peak_equity = _current_equity")
    lines.append("        _drawdown = (self._peak_equity - _current_equity) / self._peak_equity if self._peak_equity > 0 else 0.0")
    lines.append("        _pos = self.get_position(symbol)")
    lines.append("        _current_pct = (_pos * bar.close) / _current_equity if _current_equity > 0 else 0.0")
    lines.append("        _today = self.format_time(bar.timestamp, '%Y-%m-%d') if hasattr(bar, 'timestamp') and bar.timestamp else ''")
    lines.append("")

    for s in risk_stages:
        for check in s.get("config", {}).get("checks", []):
            ctype = check["type"]
            threshold = check["threshold"]
            action = check.get("action", "block_buy")

            if ctype == "max_drawdown":
                lines.append(f"        # 风控: 最大回撤限制 {threshold}")
                lines.append(f"        if _drawdown > {threshold}:")
                lines.append(f'            self._risk_blocks.append({{"type": "max_drawdown", "threshold": {threshold}, "actual": round(float(_drawdown), 6), "action": "{action}", "date": _today, "symbol": symbol}})')
                if action == "block_buy":
                    lines.append("            _allow_buy = False")
                elif action == "block_all":
                    lines.append("            _allow_buy = False")
                    lines.append("            _allow_sell = False")
                else:  # warn
                    lines.append("            pass  # 警告: 回撤超限")
            elif ctype == "max_position":
                lines.append(f"        # 风控: 最大持仓限制 {threshold}")
                lines.append(f"        if _current_pct > {threshold}:")
                lines.append(f'            self._risk_blocks.append({{"type": "max_position", "threshold": {threshold}, "actual": round(float(_current_pct), 6), "action": "{action}", "date": _today, "symbol": symbol}})')
                if action == "block_buy":
                    lines.append("            _allow_buy = False")
                elif action == "block_all":
                    lines.append("            _allow_buy = False")
                    lines.append("            _allow_sell = False")
                else:
                    lines.append("            pass  # 警告: 持仓超限")

    return lines


def _gen_signal_code(signal_stages: list[dict]) -> list[str]:
    """生成信号判断阶段代码."""
    lines = []
    lines.append("# === Stage: 信号判断 ===")

    all_groups: list[dict] = []
    for s in signal_stages:
        all_groups.extend(s.get("config", {}).get("groups", []))

    if not all_groups:
        lines.append("        pass")
        return lines

    for group in all_groups:
        gid = group["id"]
        direction = group["direction"]
        logic = group.get("logic", "AND")
        conditions = group.get("conditions", [])

        lines.append(f"        # 信号组: {gid} ({direction})")
        lines.append(f"        _signal_{gid} = False")

        if not conditions:
            continue

        # 生成每个条件的代码
        cond_lines = []
        for cond in conditions:
            left = cond["left"]
            op = cond["op"]
            right = cond["right"]

            left_expr = _operand_to_expr(left)
            right_expr = _operand_to_expr(right)

            if op == "cross_up":
                # 需要前一天的值
                prev_left = _operand_to_prev_expr(left)
                prev_right = _operand_to_prev_expr(right)
                cond_lines.append(f"({prev_left} <= {prev_right} and {left_expr} > {right_expr})")
            elif op == "cross_down":
                prev_left = _operand_to_prev_expr(left)
                prev_right = _operand_to_prev_expr(right)
                cond_lines.append(f"({prev_left} >= {prev_right} and {left_expr} < {right_expr})")
            elif op == "gt":
                cond_lines.append(f"({left_expr} > {right_expr})")
            elif op == "gte":
                cond_lines.append(f"({left_expr} >= {right_expr})")
            elif op == "lt":
                cond_lines.append(f"({left_expr} < {right_expr})")
            elif op == "lte":
                cond_lines.append(f"({left_expr} <= {right_expr})")
            elif op == "eq":
                cond_lines.append(f"({left_expr} == {right_expr})")

        if logic == "AND":
            combined = " and ".join(cond_lines)
        else:
            combined = " or ".join(cond_lines)

        lines.append(f"        if {combined}:")
        lines.append(f"            _signal_{gid} = True")
        lines.append("")

    return lines


def _gen_action_code(action_stages: list[dict], signal_directions: dict[str, str]) -> list[str]:
    """生成交易执行阶段代码."""
    lines = []
    lines.append("# === Stage: 交易执行 ===")

    all_rules: list[dict] = []
    for s in action_stages:
        all_rules.extend(s.get("config", {}).get("rules", []))

    if not all_rules:
        lines.append("        pass")
        return lines

    for rule in all_rules:
        sig_group = rule["signal_group"]
        action = rule["action"]
        weight = rule["weight"]
        direction = signal_directions.get(sig_group, "buy")

        if action == "order_target_percent":
            lines.append(f"        if _signal_{sig_group}:")
            if direction == "buy" and weight > 0:
                # 买入动作，需要 _allow_buy
                lines.append(f"            if _allow_buy:")
                lines.append(f"                self.order_target_percent({weight}, symbol)")
                lines.append(f"                return")
            elif direction == "sell" or weight == 0:
                # 卖出/清仓动作，需要 _allow_sell
                lines.append(f"            if _allow_sell:")
                lines.append(f"                self.order_target_percent({weight}, symbol)")
                lines.append(f"                return")
            else:
                lines.append(f"            self.order_target_percent({weight}, symbol)")
                lines.append(f"            return")

    return lines


def _operand_to_expr(operand: dict) -> str:
    """将操作数转为表达式."""
    if "indicator" in operand and operand["indicator"]:
        return f"self._indicators['{operand['indicator']}']"
    if "value" in operand:
        return str(operand["value"])
    return "0.0"


def _operand_to_prev_expr(operand: dict) -> str:
    """将操作数转为前一天的表达式（用于上穿/下穿）."""
    if "indicator" in operand and operand["indicator"]:
        ind_name = operand["indicator"]
        return f"self._indicators_prev['{ind_name}']"
    if "value" in operand:
        return str(operand["value"])
    return "0.0"
