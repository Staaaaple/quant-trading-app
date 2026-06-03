"""自然语言策略解析引擎（分词版）.

将中文自然语言策略描述解析为流水线配置，同时暴露匹配/未匹配文本区间，
让用户明确知道系统理解了什么、没理解什么.

核心改进：采用"先分词、后组装"的两阶段架构。
第一阶段用带优先级的正则全局提取 token（指标、操作符、数值、方向、逻辑、风控、仓位、复杂关键词）；
第二阶段基于 token 序列组装条件。这样数值 token 被独立识别，不再依赖操作符后的局部文本截取。
"""

import re
from typing import Any

# ── 复杂策略关键词黑名单 ──
# 命中这些词时，系统应提示"包含复杂逻辑，建议切换开发者模式"
COMPLEX_KEYWORDS = [
    "轮动", "选股", "排名", "前\\d*只", "最强", "最弱", "机器学习", "AI", "预测",
    "网格", "定投", "分批", "滚动", "跟踪", "动态", "自适应", "智能",
    "跨周期", "多周期", "分钟线", "分钟K", "T\\+0", "T加0",
    "配对", "对冲", "套利", "期现", "跨品种",
    "事件", "公告", "财报", "龙虎榜", "北向", "资金流向", "主力",
    "止盈", "止损", "回撤控制", "移动止损", "阶梯", "滑点",
    "杠杆", "保证金", "融资", "融券",
]


# ── 指标模式 ──
# (regex, type, default_period, field_extractor)
INDICATOR_PATTERNS: list[tuple[str, str, int | None, str | None]] = [
    (r"(?<![A-Za-z])MA(\d+)", "MA", 1, None),
    (r"(\d+)日均线", "MA", 1, None),
    (r"均线(\d+)", "MA", 1, None),
    (r"(?<![A-Za-z])EMA(\d+)", "EMA", 1, None),
    (r"(?<![A-Za-z])RSI(\d+)", "RSI", 1, None),
    (r"RSI", "RSI", 14, None),
    (r"MACD", "MACD", None, None),
    (r"KDJ", "KDJ", 9, None),
    (r"布林带", "BOLL", 20, None),
    (r"BOLL", "BOLL", 20, None),
    (r"上轨", "PRICE", None, "boll_upper"),
    (r"中轨", "PRICE", None, "boll_middle"),
    (r"下轨", "PRICE", None, "boll_lower"),
    (r"收盘价", "PRICE", None, "close"),
    (r"收盘", "PRICE", None, "close"),
    (r"close", "PRICE", None, "close"),
    (r"开盘价", "PRICE", None, "open"),
    (r"开盘", "PRICE", None, "open"),
    (r"open", "PRICE", None, "open"),
    (r"最高价", "PRICE", None, "high"),
    (r"最高", "PRICE", None, "high"),
    (r"high", "PRICE", None, "high"),
    (r"最低价", "PRICE", None, "low"),
    (r"最低", "PRICE", None, "low"),
    (r"low", "PRICE", None, "low"),
    (r"成交量", "VOLUME", None, None),
    (r"volume", "VOLUME", None, None),
    (r"量能", "VOLUME", None, None),
]

# ── 条件操作符模式 ──
OP_PATTERNS: list[tuple[str, str]] = [
    (r"上穿", "cross_up"),
    (r"金叉", "cross_up"),
    (r"突破向上", "cross_up"),
    (r"向上突破", "cross_up"),
    (r"下穿", "cross_down"),
    (r"死叉", "cross_down"),
    (r"跌破", "cross_down"),
    (r"向下突破", "cross_down"),
    (r"大于等于|>=|≥", "gte"),
    (r"小于等于|<=|≤", "lte"),
    (r"大于|超过|高于|>", "gt"),
    (r"小于|低于|<", "lt"),
    (r"等于|==|是", "eq"),
]

# ── 逻辑连接词 ──
LOGIC_PATTERNS: list[tuple[str, str]] = [
    (r"且|并且|同时|，且|,且", "AND"),
    (r"或|或者", "OR"),
]

# ── 方向 ──
DIRECTION_PATTERNS: list[tuple[str, str]] = [
    (r"买入|做多|开仓|进场|建仓", "buy"),
    (r"卖出|清仓|平仓|做空|退场|减仓", "sell"),
]

# ── 仓位 ──
WEIGHT_PATTERNS: list[tuple[str, float | None]] = [
    (r"全仓|满仓|100%", 1.0),
    (r"八成仓|80%", 0.8),
    (r"半仓|50%", 0.5),
    (r"三成仓|30%", 0.3),
    (r"两成仓|20%", 0.2),
    (r"一成仓|10%", 0.1),
    (r"清仓|空仓|0%", 0.0),
    (r"(\d+(?:\.\d+)?)%", None),  # 动态提取
]

# ── 风控 ──
RISK_PATTERNS: list[tuple[str, str]] = [
    (r"最大回撤(?:超过|大于|达到)?(?:\s*)(\d+(?:\.\d+)?)%", "max_drawdown"),
    (r"回撤(?:控制|限制|不超过|小于)?(?:\s*)(\d+(?:\.\d+)?)%", "max_drawdown"),
    (r"(?:最大)?持仓(?:不超过|限制|小于)?(?:\s*)(\d+(?:\.\d+)?)%", "max_position"),
    (r"仓位(?:不超过|限制|小于)?(?:\s*)(\d+(?:\.\d+)?)%", "max_position"),
]


# ── Token 优先级 ──
# 数字越大优先级越高，重叠时保留高优先级的
TOKEN_PRIORITY = {
    "indicator": 100,
    "complex": 90,
    "op": 80,
    "direction": 70,
    "logic": 60,
    "risk": 50,
    "weight": 50,
    "number": 10,
}


def _tokenize(text: str) -> list[dict[str, Any]]:
    """全局分词：用正则提取所有 token，按优先级解决重叠."""
    raw_tokens: list[dict[str, Any]] = []

    # 1. 指标（最高优先级，避免 MA5 被拆成 MA + 5）
    for pattern, ind_type, default_period, field in INDICATOR_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            name: str | None = None
            period = default_period
            ind_field = field or "close"

            if ind_type == "MA" and default_period == 1 and len(m.groups()) > 0 and m.group(1):
                period = int(m.group(1))
                name = f"ma{period}"
            elif ind_type == "EMA" and len(m.groups()) > 0 and m.group(1):
                period = int(m.group(1))
                name = f"ema{period}"
            elif ind_type == "RSI":
                if len(m.groups()) > 0 and m.group(1):
                    period = int(m.group(1))
                name = f"rsi{period}"
            elif ind_type == "MACD":
                name = "macd"
            elif ind_type == "KDJ":
                name = "kdj"
            elif ind_type == "BOLL":
                name = "boll"
            elif ind_type == "PRICE":
                name = ind_field
            elif ind_type == "VOLUME":
                name = "volume"

            if name:
                cfg: dict[str, Any] = {"name": name, "type": ind_type}
                if period is not None:
                    cfg["period"] = period
                if field:
                    cfg["field"] = field
                raw_tokens.append({
                    "start": m.start(),
                    "end": m.end(),
                    "type": "indicator",
                    "priority": TOKEN_PRIORITY["indicator"],
                    "data": cfg,
                    "text": m.group(),
                })

    # 2. 复杂关键词
    for kw in COMPLEX_KEYWORDS:
        for m in re.finditer(kw, text, re.IGNORECASE):
            raw_tokens.append({
                "start": m.start(),
                "end": m.end(),
                "type": "complex",
                "priority": TOKEN_PRIORITY["complex"],
                "data": m.group(),
                "text": m.group(),
            })

    # 3. 操作符
    for pattern, op in OP_PATTERNS:
        for m in re.finditer(pattern, text):
            raw_tokens.append({
                "start": m.start(),
                "end": m.end(),
                "type": "op",
                "priority": TOKEN_PRIORITY["op"],
                "data": op,
                "text": m.group(),
            })

    # 4. 方向
    for pattern, direction in DIRECTION_PATTERNS:
        for m in re.finditer(pattern, text):
            raw_tokens.append({
                "start": m.start(),
                "end": m.end(),
                "type": "direction",
                "priority": TOKEN_PRIORITY["direction"],
                "data": direction,
                "text": m.group(),
            })

    # 5. 逻辑连接词
    for pattern, logic in LOGIC_PATTERNS:
        for m in re.finditer(pattern, text):
            raw_tokens.append({
                "start": m.start(),
                "end": m.end(),
                "type": "logic",
                "priority": TOKEN_PRIORITY["logic"],
                "data": logic,
                "text": m.group(),
            })

    # 6. 风控（整句匹配，包含数值）
    for pattern, risk_type in RISK_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            try:
                threshold = float(m.group(1)) / 100.0
                raw_tokens.append({
                    "start": m.start(),
                    "end": m.end(),
                    "type": "risk",
                    "priority": TOKEN_PRIORITY["risk"],
                    "data": {"type": risk_type, "threshold": threshold, "action": "block_buy"},
                    "text": m.group(),
                })
            except (ValueError, IndexError):
                continue

    # 7. 仓位（整句匹配，包含数值）
    for pattern, val in WEIGHT_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            weight = val
            if val is None:
                try:
                    weight = float(m.group(1)) / 100.0
                except (ValueError, IndexError):
                    continue
            raw_tokens.append({
                "start": m.start(),
                "end": m.end(),
                "type": "weight",
                "priority": TOKEN_PRIORITY["weight"],
                "data": weight,
                "text": m.group(),
            })

    # 8. 独立数值 token（最低优先级，跳过已被高优先级覆盖的区间）
    for m in re.finditer(r"\d+(?:\.\d+)?", text):
        # 若该位置已被 indicator/risk/weight 覆盖则跳过
        covered = False
        for t in raw_tokens:
            if t["type"] in ("indicator", "risk", "weight") and t["start"] <= m.start() < t["end"]:
                covered = True
                break
        if covered:
            continue
        raw_tokens.append({
            "start": m.start(),
            "end": m.end(),
            "type": "number",
            "priority": TOKEN_PRIORITY["number"],
            "data": float(m.group()),
            "text": m.group(),
        })

    # 解决重叠：按 (起始位置, -优先级) 排序，优先保留高优先级且互不重叠的 token
    raw_tokens.sort(key=lambda t: (t["start"], -t["priority"]))
    tokens: list[dict[str, Any]] = []
    last_end = -1
    for t in raw_tokens:
        if t["start"] >= last_end:
            tokens.append(t)
            last_end = t["end"]

    return tokens


def _token_to_operand(token: dict[str, Any]) -> dict[str, Any]:
    """将 token 转为 ConditionOperand."""
    if token["type"] == "indicator":
        return {"indicator": token["data"]["name"], "value": None}
    elif token["type"] == "number":
        return {"indicator": None, "value": token["data"]}
    return {"indicator": None, "value": None}


def _build_conditions_from_tokens(tokens: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], set[int]]:
    """基于 token 序列构建条件列表.

    策略：遍历每个操作符 token，在其左侧找最近的未使用指标，右侧找最近的未使用指标或数值。
    cross_up/cross_down 优先配对两个指标；数值比较操作符可配指标+数值或指标+指标。
    """
    conditions: list[dict[str, Any]] = []
    used: set[int] = set()

    op_indices = [i for i, t in enumerate(tokens) if t["type"] == "op"]

    for op_idx in op_indices:
        if op_idx in used:
            continue

        op_type = tokens[op_idx]["data"]

        # 找左边最近的未使用指标
        left_idx: int | None = None
        for i in range(op_idx - 1, -1, -1):
            if i in used:
                continue
            if tokens[i]["type"] == "indicator":
                left_idx = i
                break

        if left_idx is None:
            continue

        # 找右边最近的未使用指标或数值
        # 遇到另一个操作符或逻辑连接词时停止，避免跨条件配对
        right_idx: int | None = None
        for i in range(op_idx + 1, len(tokens)):
            if i in used:
                continue
            ttype = tokens[i]["type"]
            if ttype in ("op", "logic"):
                break
            if ttype == "indicator":
                right_idx = i
                break
            if ttype == "number" and op_type not in ("cross_up", "cross_down"):
                right_idx = i
                break

        if right_idx is None:
            continue

        conditions.append({
            "left": _token_to_operand(tokens[left_idx]),
            "op": op_type,
            "right": _token_to_operand(tokens[right_idx]),
        })
        used.add(left_idx)
        used.add(op_idx)
        used.add(right_idx)

    return conditions, used


def _calc_unmatched_spans(text: str, matched_spans: list[tuple[int, int, Any]]) -> list[tuple[int, int]]:
    """计算未被匹配的文本区间."""
    if not matched_spans:
        return [(0, len(text))]
    unmatched = []
    matched_sorted = sorted(matched_spans, key=lambda x: x[0])
    # 去重重叠区间
    merged = [list(matched_sorted[0][:2])]
    for start, end, *_ in matched_sorted[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    # 计算间隙
    if merged[0][0] > 0:
        unmatched.append((0, merged[0][0]))
    for i in range(len(merged) - 1):
        if merged[i][1] < merged[i + 1][0]:
            unmatched.append((merged[i][1], merged[i + 1][0]))
    if merged[-1][1] < len(text):
        unmatched.append((merged[-1][1], len(text)))

    # 过滤掉纯空白/标点区间
    filtered = []
    for s, e in unmatched:
        seg = text[s:e].strip()
        if seg and not re.match(r"^[，。？！；：、\s]+$", seg):
            filtered.append((s, e))
    return filtered


def _calc_confidence(
    text: str,
    matched_spans: list[tuple[int, int, str]],
    indicators: list[dict[str, Any]],
    signal_groups: list[dict[str, Any]],
    has_weight: bool,
    risk_checks: list[dict[str, Any]],
    complex_found: list[str],
) -> float:
    """计算解析置信度."""
    # 基础分
    score = 0.0
    if indicators:
        score += min(0.2, len(indicators) * 0.1)
    if signal_groups:
        score += 0.3
    if has_weight:
        score += 0.1
    if risk_checks:
        score += 0.1

    # 文本覆盖率
    total_chars = len(text.strip())
    matched_chars = 0
    sorted_spans = sorted(set((s, e) for s, e, _ in matched_spans), key=lambda x: x[0])
    merged: list[list[int]] = []
    for s, e in sorted_spans:
        if not merged or s > merged[-1][1]:
            merged.append([s, e])
        else:
            merged[-1][1] = max(merged[-1][1], e)
    for s, e in merged:
        matched_chars += e - s

    coverage = matched_chars / max(1, total_chars)
    score += coverage * 0.3

    # 复杂关键词封顶
    if complex_found:
        score = min(score, 0.35)

    return min(1.0, max(0.0, score))


def parse_nl(text: str) -> dict[str, Any]:
    """解析自然语言策略描述.

    返回:
        {
            "pipeline_config": dict | None,
            "matched_spans": [(start, end, "label"), ...],
            "unmatched_spans": [(start, end), ...],
            "complex_keywords_found": [str, ...],
            "confidence": float,
            "warnings": [str, ...],
        }
    """
    if not text or not text.strip():
        return {
            "pipeline_config": None,
            "matched_spans": [],
            "unmatched_spans": [],
            "complex_keywords_found": [],
            "confidence": 0.0,
            "warnings": ["输入为空"],
        }

    original_text = text
    matched_spans: list[tuple[int, int, str]] = []
    warnings: list[str] = []

    # ── 1. 全局分词 ──
    tokens = _tokenize(text)

    # 所有 token 的区间都进入 matched_spans
    for t in tokens:
        matched_spans.append((t["start"], t["end"], f"{t['type']}:{t['text']}"))

    # ── 2. 收集复杂关键词 ──
    complex_found = [t["data"] for t in tokens if t["type"] == "complex"]
    if complex_found:
        warnings.append(f"检测到复杂策略关键词：{', '.join(set(complex_found))}，建议切换开发者模式")

    # ── 3. 提取指标定义（去重） ──
    indicators: list[dict[str, Any]] = []
    seen_ind_names: set[str] = set()
    for t in tokens:
        if t["type"] == "indicator":
            cfg = t["data"]
            name = cfg["name"]
            if name not in seen_ind_names:
                seen_ind_names.add(name)
                indicators.append(cfg)

    # ── 4. 提取风控 ──
    risk_checks: list[dict[str, Any]] = []
    seen_risk: set[tuple[str, float]] = set()
    for t in tokens:
        if t["type"] == "risk":
            d = t["data"]
            key = (d["type"], round(d["threshold"], 6))
            if key not in seen_risk:
                seen_risk.add(key)
                risk_checks.append(d)

    # ── 5. 提取仓位 ──
    weight: float | None = None
    for t in tokens:
        if t["type"] == "weight":
            weight = t["data"]
            break

    # ── 6. 基于 token 构建信号条件 ──
    conditions, used_token_indices = _build_conditions_from_tokens(tokens)

    # 提取方向和逻辑
    direction = "buy"
    logic = "AND"
    for t in tokens:
        if t["type"] == "direction":
            direction = t["data"]
            break
    for t in tokens:
        if t["type"] == "logic":
            logic = t["data"]
            break

    signal_groups: list[dict[str, Any]] = []
    if conditions:
        signal_groups.append({
            "id": f"{'buy' if direction == 'buy' else 'sell'}-signal",
            "direction": direction,
            "logic": logic,
            "conditions": conditions,
        })

    # 兜底：有指标和方向但无条件
    if not signal_groups and indicators and any(t["type"] == "direction" for t in tokens):
        first_ind = indicators[0]["name"]
        signal_groups.append({
            "id": f"{'buy' if direction == 'buy' else 'sell'}-signal",
            "direction": direction,
            "logic": "AND",
            "conditions": [
                {"left": {"indicator": first_ind, "value": None}, "op": "gt", "right": {"indicator": None, "value": 0}}
            ],
        })
        warnings.append(f"未识别具体条件，默认使用 {first_ind} > 0，请确认")

    # ── 7. 构建 Action ──
    actions: list[dict[str, Any]] = []
    if signal_groups:
        if weight is None:
            weight = 0.5
            warnings.append("未识别仓位比例，默认使用 50%")
        actions.append({
            "signal_group": signal_groups[0]["id"],
            "action": "order_target_percent",
            "weight": weight,
        })

    # ── 8. 组装 Pipeline Config ──
    pipeline_config: dict[str, Any] | None = None
    if indicators or signal_groups:
        stages = []
        stages.append({
            "id": "init-1",
            "type": "init",
            "config": {"history_depth": 30, "max_position_pct": 0.95},
        })
        if indicators:
            stages.append({
                "id": "ind-1",
                "type": "indicator",
                "config": {"indicators": indicators},
            })
        if risk_checks:
            stages.append({
                "id": "risk-1",
                "type": "risk",
                "config": {"checks": risk_checks},
            })
        if signal_groups:
            stages.append({
                "id": "sig-1",
                "type": "signal",
                "config": {"groups": signal_groups},
            })
        if actions:
            stages.append({
                "id": "act-1",
                "type": "action",
                "config": {"rules": actions},
            })
        pipeline_config = {"version": "1.0", "stages": stages}

    # ── 9. 计算未匹配区间 ──
    unmatched = _calc_unmatched_spans(original_text, matched_spans)

    # ── 10. 计算置信度 ──
    confidence = _calc_confidence(
        original_text, matched_spans, indicators, signal_groups,
        weight is not None, risk_checks, complex_found
    )

    # 如果有未匹配文本且置信度较高，提示用户检查
    if unmatched and confidence > 0.6:
        snippets = [original_text[s:e].strip()[:20] for s, e in unmatched[:3]]
        warnings.append(f"系统未能完全理解以下表述：{', '.join(snippets)}...")

    return {
        "pipeline_config": pipeline_config,
        "matched_spans": matched_spans,
        "unmatched_spans": unmatched,
        "complex_keywords_found": list(set(complex_found)),
        "confidence": round(confidence, 2),
        "warnings": warnings,
    }
