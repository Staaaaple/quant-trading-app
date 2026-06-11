"""投资顾问Prompt模板.

提供结构化的Prompt模板，用于Qwen3生成投资顾问式回答.
"""

from typing import Any

from .retriever_v2 import RetrievalResult


class PromptTemplates:
    """Prompt模板库."""

    # ═══════════════════════════════════════════════════════════════
    # 系统Prompt
    # ═══════════════════════════════════════════════════════════════

    SYSTEM_PROMPT = """你是一位资深价值投资顾问，具备以下特点：

1. **价值投资导向**：以企业内在价值为核心，关注长期持有
2. **估值锚定**：所有买卖建议必须有估值依据
3. **数据驱动**：用数据说话，引用研究报告和案例
4. **风险提示**：风险提示必须明确具体
5. **操作建议**：给出具体可执行的操作方案
6. **行为提醒**：考虑用户行为偏差，给出针对性提醒

回答格式要求：
- 使用Markdown格式
- 先说结论，再说理由
- 包含📊/🔍/⚠️/📋等emoji标题
- 引用格式：[作者, 年份] 或 [案例ID]
- 必须包含免责声明

注意事项：
- 不预测短期股价走势
- 不推荐使用杠杆
- 强调长期持有和分散投资
- 提醒用户独立思考"""

    # ═══════════════════════════════════════════════════════════════
    # 个股分析模板
    # ═══════════════════════════════════════════════════════════════

    STOCK_ANALYSIS_TEMPLATE = """## 📊 {stock_name}（{symbol}）投资分析

**投资结论：{recommendation}**
- 当前估值：{current_valuation}
- 合理估值：{fair_valuation}
- 潜在空间：{upside}
- 建议仓位：{position_size}
- 持有周期：{time_horizon}

---

## 🔍 投资逻辑

### 1. 企业基本面
{fundamental_analysis}

### 2. 估值分析
{valuation_analysis}

### 3. 产业趋势
{industry_trend}

---

## ⚠️ 风险因素
{risk_factors}

---

## 📋 操作策略

| 场景 | 操作 | 价格 | 仓位 |
|------|------|------|------|
| 建仓 | {buy_action} | {buy_price} | {buy_position} |
| 加仓 | {add_action} | {add_price} | {add_position} |
| 持有 | 不动 | - | - |
| 减仓 | {reduce_action} | {reduce_price} | {reduce_position} |
| 清仓 | {sell_action} | {sell_price} | 全部 |

**持有纪律**：
- 除非基本面恶化或估值过高，否则持有不动
- 短期波动（±20%）不改长期逻辑
- 每季度审视一次基本面

---

## 📚 理论支撑
{theory_support}

---

*免责声明：以上分析基于公开信息和历史数据，不构成投资建议。投资有风险，入市需谨慎。*"""

    # ═══════════════════════════════════════════════════════════════
    # 估值分析模板
    # ═══════════════════════════════════════════════════════════════

    VALUATION_TEMPLATE = """## 📊 {stock_name} 估值分析

**估值结论：{valuation_conclusion}**
- 当前PE：{current_pe}x（历史{pe_percentile}%分位）
- 当前PB：{current_pb}x（历史{pb_percentile}%分位）
- DCF估值：{dcf_value}元
- 综合判断：{overall_assessment}

---

## 🔍 估值方法

### 1. PE估值法
{pe_analysis}

### 2. PB估值法
{pb_analysis}

### 3. DCF估值法
{dcf_analysis}

### 4. 历史估值对比
{historical_comparison}

---

## ⚠️ 估值陷阱
{valuation_traps}

---

## 📋 操作建议

| 估值水平 | 操作 | 仓位 |
|---------|------|------|
| 极度低估（PE<历史10%） | 重仓买入 | 15-20% |
| 低估（PE<历史30%） | 建仓买入 | 10-15% |
| 合理（PE历史30-70%） | 持有/小幅加仓 | 5-10% |
| 高估（PE>历史70%） | 减仓 | 0-5% |
| 极度高估（PE>历史90%） | 清仓 | 0% |

---

*免责声明：以上分析基于公开信息和历史数据，不构成投资建议。*"""

    # ═══════════════════════════════════════════════════════════════
    # 组合构建模板
    # ═══════════════════════════════════════════════════════════════

    PORTFOLIO_TEMPLATE = """## ⚖️ 资产配置方案

**{risk_profile}型投资者 + {market_cycle}市场环境**

### 配置比例
{allocation_table}

### 具体标的
{holdings_table}

---

## 🔍 配置理由

### 1. 战略配置（SAA）
{saa_rationale}

### 2. 战术配置（TAA）
{taa_rationale}

### 3. 风险控制
{risk_control}

---

## ⚠️ 风险提示
{risk_factors}

---

## 📋 调整规则

### 再平衡触发条件
{rebalance_triggers}

### 调仓流程
1. 评估当前组合偏离度
2. 确定需要调整的标的
3. 分批执行（避免冲击成本）
4. 记录调仓理由

---

## 📚 理论支撑
{theory_support}

---

*免责声明：以上配置方案基于理论模型和历史数据，不构成投资建议。*"""

    # ═══════════════════════════════════════════════════════════════
    # 概念解释模板
    # ═══════════════════════════════════════════════════════════════

    CONCEPT_TEMPLATE = """## 📖 {concept_name}

### 定义
{definition}

### 通俗解释
{simple_explanation}

---

## 🔍 详细说明

### 计算方法
{calculation_method}

### 使用方法
{usage_methods}

### 实战案例
{example}

---

## ⚠️ 注意事项
{cautions}

---

## 📚 相关概念
{related_concepts}

### 常见问题
{common_questions}

---

*免责声明：以上内容仅供学习参考。*"""

    # ═══════════════════════════════════════════════════════════════
    # 行为金融提醒模板
    # ═══════════════════════════════════════════════════════════════

    BEHAVIORAL_REMINDER_TEMPLATE = """## 💡 行为偏差提醒

根据您的画像分析，您在投资中可能存在以下行为偏差：

### 主要偏差
{bias_list}

### 对您的影响
{bias_impact}

### 应对建议
{coping_strategies}

---

## 📋 个性化投资纪律

基于您的行为特征，建议遵守以下纪律：

{personalized_rules}

---

*免责声明：行为分析基于问卷结果，仅供参考。*"""

    @staticmethod
    def build_context(context_items: list[dict[str, Any]]) -> str:
        """构建检索上下文.

        Args:
            context_items: 检索结果列表

        Returns:
            格式化后的上下文文本
        """
        parts = []
        for i, item in enumerate(context_items, 1):
            parts.append(f"[{i}] {item['text'][:500]}...")
        return "\n\n".join(parts)

    @staticmethod
    def build_stock_analysis_prompt(
        query: str,
        context: dict[str, list[RetrievalResult]],
        stock_info: dict[str, Any],
    ) -> str:
        """构建个股分析Prompt.

        Args:
            query: 用户查询
            context: 检索上下文
            stock_info: 股票基本信息

        Returns:
            完整Prompt
        """
        # 构建上下文
        context_parts = []

        if context.get("stock_cases"):
            context_parts.append("## 相关个股案例")
            for i, case in enumerate(context["stock_cases"][:3], 1):
                context_parts.append(f"{i}. {case.text[:300]}...")

        if context.get("valuation_cases"):
            context_parts.append("## 估值案例")
            for i, case in enumerate(context["valuation_cases"][:2], 1):
                context_parts.append(f"{i}. {case.text[:300]}...")

        if context.get("paper_chunks"):
            context_parts.append("## 研究支撑")
            for i, paper in enumerate(context["paper_chunks"][:2], 1):
                context_parts.append(f"{i}. {paper.text[:300]}...")

        context_text = "\n\n".join(context_parts)

        return f"""请基于以下资料，对{stock_info.get('name', '该股票')}进行价值投资分析。

## 用户问题
{query}

## 参考资料
{context_text}

## 要求
1. 给出明确的投资结论（买入/持有/卖出）
2. 提供估值分析（PE/PB/DCF）
3. 分析企业基本面和竞争优势
4. 给出具体操作建议（价格/仓位）
5. 提示关键风险
6. 引用参考资料编号

请按以下格式回答：
- 📊 投资结论
- 🔍 投资逻辑
- ⚠️ 风险因素
- 📋 操作策略
- 📚 理论支撑"""

    @staticmethod
    def build_valuation_prompt(
        query: str,
        context: dict[str, list[RetrievalResult]],
    ) -> str:
        """构建估值分析Prompt."""
        context_text = PromptTemplates.build_context(
            [item.__dict__ for item in context.get("valuation_cases", [])]
        )

        return f"""请基于以下资料，进行估值分析。

## 用户问题
{query}

## 参考资料
{context_text}

## 要求
1. 使用多种估值方法（PE/PB/DCF）
2. 与历史估值对比
3. 与同行业对比
4. 给出估值结论
5. 提示估值陷阱"""

    @staticmethod
    def build_portfolio_prompt(
        query: str,
        context: dict[str, list[RetrievalResult]],
        profile: dict[str, Any],
    ) -> str:
        """构建组合构建Prompt."""
        context_text = PromptTemplates.build_context(
            [item.__dict__ for item in context.get("theories", [])]
        )

        return f"""请基于以下资料，为{profile.get('risk_profile', '稳健型')}投资者构建资产配置方案。

## 用户问题
{query}

## 用户画像
- 风险承受：{profile.get('risk_tolerance', '中等')}
- 投资期限：{profile.get('time_horizon', '3-5年')}
- 资金规模：{profile.get('capital', '50万')}

## 参考资料
{context_text}

## 要求
1. 给出具体配置比例
2. 推荐具体标的
3. 说明配置理由
4. 设定调整规则
5. 提示风险"""

    @staticmethod
    def build_concept_prompt(
        query: str,
        context: dict[str, list[RetrievalResult]],
    ) -> str:
        """构建概念解释Prompt."""
        context_text = PromptTemplates.build_context(
            [item.__dict__ for item in context.get("basics", [])]
        )

        return f"""请基于以下资料，解释投资概念。

## 用户问题
{query}

## 参考资料
{context_text}

## 要求
1. 用通俗语言解释
2. 提供计算公式
3. 说明使用方法
4. 给出实战案例
5. 提示常见误区"""
