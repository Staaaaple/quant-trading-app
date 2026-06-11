# RAG 接入 Hybrid 组合引擎计划

> 目标：让 RAG 投资顾问成为 Hybrid 引擎的"质量总监"，在每个阶段间进行控制、把关和调节
> 版本: V1.1 | 日期: 2026-06-08 | 预计周期: 3周

---

## 一、设计哲学：RAG 作为"质量总监"

```
传统流程:  Step1 → Step2 → Step3 → Step4 → Step5 → Step6 → 输出
              ↑      ↑      ↑      ↑      ↑      ↑
RAG介入:   [质检]  [质检]  [质检]  [质检]  [质检]  [质检]
              ↓      ↓      ↓      ↓      ↓      ↓
            不通过时: 调节参数 → 重新执行当前Step → 再次质检 → 直到合格或达到最大重试次数
```

**RAG 的核心职责**：
1. **把关 (Gatekeeping)**：检查当前Step输出是否符合投资常识、理论支撑、历史经验
2. **控制 (Controlling)**：当输出偏离合理范围时，触发调节机制
3. **调节 (Regulating)**：提供具体调节建议（参数调整、策略替换、风险提示）

---

## 二、接入架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Hybrid Portfolio Designer                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Step 1  │───→│ Step 2  │───→│ Step 3  │───→│ Step 4  │───→│ Step 5  │  │
│  │   SAA   │    │   TAA   │    │ 绑定    │    │ 风控    │    │ 可靠性  │  │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘  │
│       │              │              │              │              │        │
│       ▼              ▼              ▼              ▼              ▼        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │RAG质检1 │    │RAG质检2 │    │RAG质检3 │    │RAG质检4 │    │RAG质检5 │  │
│  │SAA审核  │    │TAA审核  │    │绑定审核 │    │风控审核 │    │可靠性审 │  │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘  │
│       │              │              │              │              │        │
│       ▼              ▼              ▼              ▼              ▼        │
│     [通过]         [通过]         [通过]         [通过]         [通过]      │
│       │              │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┴──────────────┘        │
│                                    │                                        │
│                                    ▼                                        │
│                              ┌─────────┐                                    │
│                              │ Step 6  │                                    │
│                              │ 寿命计算│                                    │
│                              └────┬────┘                                    │
│                                   │                                         │
│                                   ▼                                         │
│                             ┌─────────┐                                     │
│                             │RAG质检6 │                                     │
│                             │最终审核 │                                     │
│                             └────┬────┘                                     │
│                                  │                                          │
│                                  ▼                                          │
│                              [输出组合]                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、6个质检点的详细设计

### 质检点1：SAA 战略资产配置审核（市场信号驱动微调）

**触发时机**：SAA计算出资产类别权重后

**核心变化**：RAG不只是"审核"，而是**主动结合市场信号进行微调**。股票债券权重不能只看用户画像，必须结合信号仪表盘的市场行情。

**RAG检索内容**：
- 资产配置理论库（均值方差、风险平价、全天候等）
- 基础常识库（股债配比常识、风险收益关系）
- 估值案例库（类似市场环境下的配置案例）
- **信号仪表盘数据**（宏观/地缘政治/行业景气/社会实事/资产内部信号）

**RAG工作方式**：

```
输入: SAA原始权重 + 用户画像 + 市场五层信号
    │
    ▼
RAG检索: "{market_cycle}期 + {geo_risk}风险 + {macro_score}宏观" 的配置案例
    │
    ▼
RAG分析:
├── 画像基准: 保守型股票≤30%, 稳健型≤50%, 积极型≤70%
├── 信号微调:
│   ├── 行情很差(恐慌指数高+股债利差极低) → 极度压缩股票, 增配债券/现金
│   ├── 地缘风险极高 → 增配黄金/现金对冲
│   ├── 衰退期确认 → 股票降至画像下限, 债券上调
│   └── 复苏期+低估值 → 股票可提升至画像上限
└── 理论支撑: 检索全天候/风险平价等理论验证
    │
    ▼
输出: 微调后的SAA权重 + 调节理由
```

**审核维度**：

| 检查项 | 合格标准 | 不通过时调节 |
|--------|---------|-------------|
| 画像基准 | 保守型≤30%, 稳健型≤50%, 积极型≤70% | 按画像风险等级强制截断 |
| 行情适配 | 行情极差时股票应低于画像基准 | 结合恐慌指数/VIX/股债利差压缩股票 |
| 周期匹配 | 衰退期股票权重应低于复苏期 | 检索"衰退期配置"案例，按历史经验调整 |
| 地缘对冲 | 地缘风险高时应有黄金/现金对冲 | 检索"地缘风险"案例，建议增配避险资产 |
| 单一资产上限 | 任何单一资产≤60% | 超限则按比例压缩 |
| 债券底线 | 保守型≥50%, 稳健型≥30%, 积极型≥10% | 低于底线时上调债券 |

**RAG Prompt模板**：
```
你是一位资深资产配置专家。请结合当下市场行情，对以下战略资产配置方案进行微调。

## 用户画像
风险等级: {risk_level}型
损失厌恶: {loss_aversion}

## 原始SAA方案
股票: {stock}%, 债券: {bond}%, 商品: {commodity}%, 现金: {cash}%

## 当前市场信号（来自信号仪表盘）
- 市场周期: {market_cycle}
- 宏观评分: {macro_score}/100
- 地缘政治风险: {geo_risk}/100
- 恐慌指数(VIX): {vix}
- 股债利差: {equity_bond_spread}%
- 行业景气度: {sector_heatmap}
- 社会趋势: {social_trends}

## 参考知识
{retrieved_theory}
{retrieved_cases}

## 任务
1. 分析当前市场信号对资产配置的影响
2. 判断原始方案是否需要微调
3. 如需微调，给出调整后的权重和理由
4. 调整必须基于市场信号，不能仅看画像

## 输出格式
1. 市场分析: [当前市场环境简述]
2. 调整结论: [无需调整/需要调整]
3. 调整后方案: 股票{x}%, 债券{y}%, 商品{z}%, 现金{w}%
4. 调整理由: [结合具体信号说明]
5. 理论依据: [引用的理论/案例]
```

---

### 质检点2：TAA 战术资产配置审核

**触发时机**：TAA计算出细分资产权重后

**RAG检索内容**：
- 资产配置理论库（战术配置规则、行业轮动规律）
- 个股案例库（当前热门行业的历史表现）
- 论文片段库（因子轮动、行业动量相关研究）

**审核维度**：

| 检查项 | 合格标准 | 不通过时调节 |
|--------|---------|-------------|
| 行业集中度 | 单一行业占股票部分≤50% | 超限则分散到次优行业 |
| 风格平衡 | 成长/价值应有合理配比 | 根据市场周期调整 |
| 趋势一致性 | TAA方向应与市场信号一致 | 检索"行业景气度"案例验证 |
| 估值合理性 | 超配行业不应处于历史估值高位 | 检索估值案例，高估则降权 |
| 流动性考量 | 小市值/低流动性占比≤20% | 超限则替换为流动性更好的标的 |

---

### 质检点3：策略-标的绑定审核（回测驱动）

**触发时机**：贝叶斯优化完成策略-标的绑定后

**核心变化**：绑定后**自动回测**，回测要求**跑赢买入持有（Buy & Hold）**。不通过时接入RAG分析原因并制定新策略。

**流程**：

```
Hybrid绑定策略→标的
    │
    ▼
[自动回测]
├── 回测期: 近2年（覆盖牛熊）
├── 基准: 买入持有该标的（不操作）
├── 通过标准: 策略收益 > 买入持有收益
└── 输出: 回测报告（收益/夏普/回撤/胜率）
    │
    ├──→ 通过 → 继续下一步
    │
    └──→ 不通过 → 接入RAG分析
                │
                ▼
            [RAG诊断]
            ├── 检索: 该策略+该标的历史案例
            ├── 检索: 类似失败案例及原因
            ├── 检索: 替代策略建议
            └── 分析: 为什么跑输持有？
                - 策略参数不当？
                - 标的特性不匹配？
                - 市场环境不适配？
                - 交易频率过高（摩擦成本）？
                │
                ▼
            [RAG制定新策略]
            ├── 调节建议1: 调参（如均线周期从5日→20日）
            ├── 调节建议2: 换策略（如动量→均值回归）
            ├── 调节建议3: 换标的（如个股→ETF）
            └── 输出: 具体调节方案
                │
                ▼
            [重新绑定+回测]
            ├── 通过 → 继续
            └── 不通过 → 再次RAG分析（最多3次）
                │
                └── 3次仍不通过 → 排除该标的，选下一个
```

**RAG检索内容**：
- 个股案例库（标的的历史策略表现）
- 论文片段库（策略有效性研究）
- 行为金融案例库（策略适用的心理条件）
- **回测报告**（当前绑定的回测数据）

**审核维度**：

| 检查项 | 合格标准 | 不通过时调节 |
|--------|---------|-------------|
| 回测收益 | **必须跑赢买入持有** | RAG分析原因→调参/换策略/换标的 |
| 策略-标的相关性 | 策略逻辑应与标的特性匹配 | 不匹配则更换策略或标的 |
| 策略同质化 | 组合内策略相似度<0.6 | 过高则替换为不同家族策略 |
| 策略寿命 | 绑定策略寿命≥3个月 | 过短则排除，选寿命更长的 |
| 策略健康度 | 绑定策略健康度≥60 | 过低则排除 |
| 风险匹配 | 策略风险等级≤用户承受 | 超限则降级为低风险策略 |

**RAG Prompt模板（回测不通过时）**：
```
以下策略-标的绑定回测未通过，请分析原因并制定改进方案。

## 绑定信息
标的: {symbol} ({name})
策略: {strategy_name} ({strategy_family})
策略参数: {strategy_params}

## 回测结果（未通过）
策略收益: {strategy_return}%
买入持有收益: {buy_hold_return}%
超额收益: {alpha}% (负数表示跑输)
夏普比率: {sharpe}
最大回撤: {max_drawdown}%
胜率: {win_rate}%
交易次数: {trade_count}

## 市场环境
回测期: {backtest_period}
市场周期: {market_cycle}
波动率: {volatility}

## 参考知识
{retrieved_stock_cases}
{retrieved_papers}

## 任务
1. 分析跑输买入持有的原因（至少3个可能原因）
2. 判断是参数问题、策略不匹配、还是标的选错
3. 给出具体改进方案（调参/换策略/换标的）
4. 改进方案必须具体，如"均线周期从5日改为20日"

## 输出格式
1. 失败原因分析:
   - 原因1: [具体说明]
   - 原因2: [具体说明]
   - 原因3: [具体说明]
2. 根因判断: [参数问题/策略不匹配/标的选错/市场环境]
3. 改进方案:
   - 方案: [调参/换策略/换标的]
   - 具体调整: [如"均线周期: 5→20"]
   - 预期效果: [说明为什么这样能改善]
4. 替代建议（如需要）:
   - 替代策略: [名称]
   - 替代标的: [代码]
```

---

### 质检点4：风控配置审核

**触发时机**：自动生成风控配置后

**RAG检索内容**：
- 行为金融案例库（损失厌恶与止损设置的关系）
- 基础常识库（止损线设置的合理范围）
- 估值案例库（历史回撤数据参考）

**审核维度**：

| 检查项 | 合格标准 | 不通过时调节 |
|--------|---------|-------------|
| 止损线合理性 | 应与画像损失厌恶匹配 | 偏离则按画像校准 |
| 仓位上限 | 单票≤30%, 单一行业≤50% | 超限则下调 |
| 回撤硬止损 | 保守型≤10%, 积极型≤25% | 偏离则调整 |
| 再平衡阈值 | 保守型5%, 积极型10% | 偏离则调整 |
| 行为适配 | 高损失厌恶用户应有更严格风控 | 检索行为金融案例，提供心理适配建议 |

---

### 质检点5：可靠性评估审核（严格标准，不降低门槛）

**触发时机**：回测+压力测试+蒙特卡洛完成后

**核心变化**：
1. **新增核心检查项**：组合必须**跑赢买入持有**（Buy & Hold）
2. **严格原则**：审核不通过时**不允许降低通过要求**，必须调参或换策略直到通过
3. **硬性门槛**：所有检查项必须全部通过，没有"差不多就行"

**审核维度**：

| 检查项 | 合格标准 | 不通过时调节 |
|--------|---------|-------------|
| **跑赢买入持有（新增）** | **组合收益 > 买入持有收益** | **必须调参或换策略，不允许降低标准** |
| 回测可信度 | 回测期≥3年，包含牛熊周期 | 延长回测期，或排除数据不足的策略 |
| 夏普比率 | 组合夏普≥0.5 | 调参优化，或换夏普更高的策略 |
| 最大回撤 | 应≤用户能承受的范围 | 降低权益仓位，或换低回撤策略 |
| 胜率 | 胜率≥40% | 调参优化，或换高胜率策略 |
| 压力测试 | 2022熊市、2020疫情场景应通过 | 加强防御配置，或换抗跌策略 |

**严格原则说明**：

```
传统做法（已废弃）:
审核不通过 → 降低标准 → 勉强通过 ❌

新做法（严格执行）:
审核不通过 → 分析原因 → 调参/换策略 → 重新回测 → 再次审核
    ↓
仍不通过 → 再次调参/换策略 → 重新回测 → 再次审核
    ↓
最多重试5次 → 仍不通过 → 排除该组合方案，返回Step3重新绑定
```

**RAG Prompt模板**：
```
以下组合可靠性评估未通过，请分析原因并制定改进方案。

## 组合信息
标的数量: {n_assets}
策略绑定: {bindings}

## 可靠性评估结果（未通过）
组合收益: {portfolio_return}%
买入持有收益: {buy_hold_return}%
跑赢持有: {beat_buy_hold} (必须为正)
夏普比率: {sharpe} (要求≥0.5)
最大回撤: {max_drawdown}% (要求≤{user_limit}%)
胜率: {win_rate}% (要求≥40%)

## 压力测试
2022熊市表现: {bear_2022_return}%
2020疫情表现: {covid_2020_return}%

## 参考知识
{retrieved_papers}
{retrieved_cases}

## 任务
1. 分析未通过的具体原因
2. 判断是参数问题、策略选择问题、还是权重配置问题
3. 给出具体改进方案（必须能落实到操作）

## 重要原则
- 不允许降低通过标准
- 必须给出具体可执行的改进方案
- 如果当前组合无法通过，建议排除并重新构建

## 输出格式
1. 未通过项: [列出所有未通过的检查项]
2. 原因分析:
   - 原因1: [具体说明]
   - 原因2: [具体说明]
3. 改进方案:
   - 方案类型: [调参/换策略/调权重/重建]
   - 具体调整: [如"股票权重从60%降至50%"]
   - 预期改善: [说明为什么能通过]
4. 如无法改进:
   - 排除建议: [排除哪个标的/策略]
   - 替代建议: [替代方案]
```

---

### 质检点6：最终组合审核（综合把关）

**触发时机**：所有步骤完成后，输出前

**RAG检索内容**：
- 全部六大知识源
- 特别关注：与用户画像高度相关的行为金融案例

**审核维度**：

| 检查项 | 合格标准 | 不通过时调节 |
|--------|---------|-------------|
| 画像匹配度 | 组合风险等级应与画像一致 | 不一致则重新调整SAA |
| 市场适配度 | 组合应与当前市场周期适配 | 不适配则调整TAA |
| 可执行性 | 标的应为可交易的常见品种 | 不可交易则替换 |
| 教育价值 | 组合应附带投资逻辑解释 | 缺失则生成教学卡片 |
| 行为提醒 | 高损失厌恶用户应有止损提醒 | 缺失则添加 |

---

## 四、调节机制设计

### 4.1 调节触发条件

```python
class RAGGateResult:
    """RAG质检结果"""
    passed: bool           # 是否通过
    score: float           # 质量评分 0-1
    issues: list[str]      # 问题列表
    adjustments: list[dict] # 调节建议
    max_retries: int = 3   # 最大重试次数
```

### 4.2 调节策略

| 问题类型 | 调节策略 | 示例 |
|---------|---------|------|
| 权重不合理 | 强制截断/缩放 | 股票权重从80%→70%（积极型上限） |
| 策略不匹配 | 替换策略 | 高风险策略→低风险策略 |
| 标的不可行 | 替换标的 | 小市值股票→ETF |
| 风控过松 | 收紧参数 | 止损从15%→10% |
| 缺乏理论支撑 | 补充说明 | 添加"为什么这样配"的解释 |
| 行为不适配 | 添加提醒 | 高损失厌恶用户添加"严格执行止损"提醒 |

### 4.3 重试机制

```
第一次质检不通过 → 应用调节建议 → 重新执行当前Step → 第二次质检
    ↓
第二次不通过 → 更激进的调节 → 重新执行 → 第三次质检
    ↓
第三次不通过 → 记录问题 → 降级输出（如"建议咨询人工顾问"）→ 继续下一步
```

---

## 五、RAG 质检服务实现

### 5.1 核心类设计

```python
# services/rag/portfolio_quality_gate.py

class PortfolioQualityGate:
    """组合质量门控 — RAG投资顾问作为质量总监"""

    def __init__(
        self,
        retriever: InvestmentRetriever | None = None,
        llm_service: LLMService | None = None,
    ):
        self.retriever = retriever or get_retriever_v2()
        self.llm = llm_service or get_llm_service()

    async def review_saa(
        self,
        saa_result: dict,
        profile_vector: dict,
        market_signal: dict,
    ) -> RAGGateResult:
        """审核SAA配置"""
        # 1. 构建审核查询
        query = self._build_saa_review_query(saa_result, profile_vector, market_signal)

        # 2. RAG检索相关知识
        context = await self.retriever.retrieve(query, query_type="组合构建")

        # 3. LLM审核
        review = await self._llm_review("saa", query, context, saa_result)

        # 4. 解析审核结果
        return self._parse_review(review)

    async def review_taa(self, taa_result: dict, ...) -> RAGGateResult: ...
    async def review_bindings(
        self,
        bindings: list,
        profile_vector: dict,
        backtest_results: dict,
    ) -> RAGGateResult:
        """审核策略-标的绑定（含回测验证）"""
        # 1. 检查回测是否跑赢买入持有
        for binding in bindings:
            symbol = binding["symbol"]
            strategy_return = backtest_results.get(symbol, {}).get("return", 0)
            buy_hold_return = backtest_results.get(symbol, {}).get("buy_hold_return", 0)

            if strategy_return <= buy_hold_return:
                # 跑输持有，接入RAG分析
                query = self._build_binding_review_query(binding, backtest_results)
                context = await self.retriever.retrieve(query, query_type="个股分析")
                review = await self._llm_review("binding", query, context, binding)
                return self._parse_review(review)

        # 全部跑赢，直接通过
        return RAGGateResult(passed=True, score=0.9, issues=[], adjustments=[])
    async def review_risk_config(self, risk_config: dict, ...) -> RAGGateResult: ...
    async def review_reliability(self, reliability: dict, ...) -> RAGGateResult: ...
    async def final_review(self, portfolio: dict, ...) -> RAGGateResult: ...

    def _build_saa_review_query(self, saa_result, profile, market) -> str:
        """构建SAA审核查询"""
        weights = saa_result.get("weights", {})
        return f"""
        请审核以下资产配置方案：
        用户风险等级: {profile.get('risk_tolerance', '未知')}
        市场周期: {market.get('cycle', '未知')}
        配置方案: 股票{weights.get('stock', 0):.0%}, 债券{weights.get('bond', 0):.0%}, 
                 商品{weights.get('commodity', 0):.0%}, 现金{weights.get('cash', 0):.0%}
        该配置是否合理？是否符合投资理论和历史经验？
        """

    async def _llm_review(
        self,
        review_type: str,
        query: str,
        context: InvestmentContext,
        current_result: dict,
    ) -> str:
        """调用LLM进行审核"""
        prompt = self._build_review_prompt(review_type, query, context, current_result)
        response = await self.llm.generate_async(prompt)
        return response.text

    def _parse_review(self, review_text: str) -> RAGGateResult:
        """解析LLM审核结果"""
        # 解析通过/不通过
        passed = "审核结论: 通过" in review_text or "通过" in review_text[:100]

        # 解析问题列表
        issues = []
        if "问题列表" in review_text:
            # 提取问题
            ...

        # 解析调节建议
        adjustments = []
        if "调节建议" in review_text:
            # 提取建议
            ...

        return RAGGateResult(
            passed=passed,
            score=0.8 if passed else 0.4,
            issues=issues,
            adjustments=adjustments,
        )
```

### 5.2 与 Hybrid Designer 集成

```python
# services/hybrid_portfolio_designer.py (修改后)

async def design_portfolio_v2(
    profile_vector: dict,
    market_signal: dict,
    strategy_pool: list[dict] | None = None,
    target_count: int = 5,
    use_rag_gate: bool = True,  # 新增：是否启用RAG质检
) -> dict[str, Any]:
    """设计完整投资组合（RAG质检版）"""

    quality_gate = PortfolioQualityGate() if use_rag_gate else None
    adjustments_log = []  # 记录所有调节

    # Step 1: SAA
    saa_result = calculate_saa(...)

    if use_rag_gate:
        review = await quality_gate.review_saa(saa_result, profile_vector, market_signal)
        if not review.passed:
            saa_result = _apply_adjustments(saa_result, review.adjustments)
            adjustments_log.append({"step": "saa", "review": review})

    # Step 2: TAA
    taa_result = calculate_taa(saa_result, ...)

    if use_rag_gate:
        review = await quality_gate.review_taa(taa_result, ...)
        if not review.passed:
            taa_result = _apply_adjustments(taa_result, review.adjustments)
            adjustments_log.append({"step": "taa", "review": review})

    # Step 3-6 类似...

    # 最终输出包含调节记录
    return {
        ...,
        "rag_reviews": adjustments_log,  # RAG质检记录
        "rag_adjusted": len(adjustments_log) > 0,  # 是否经过RAG调节
    }
```

---

## 六、实施路线图

### Week 1: 基础设施（RAG质检服务）

**Day 1-2: 实现 PortfolioQualityGate 核心类**
- [ ] `portfolio_quality_gate.py` 框架
- [ ] 6个review方法骨架
- [ ] RAGGateResult数据模型

**Day 3-4: 实现审核Prompt模板**
- [ ] SAA审核Prompt
- [ ] TAA审核Prompt
- [ ] 绑定审核Prompt
- [ ] 风控审核Prompt
- [ ] 可靠性审核Prompt
- [ ] 最终审核Prompt

**Day 5: 集成到Hybrid Designer**
- [ ] 修改 `design_portfolio` 支持RAG质检
- [ ] 调节机制实现（权重截断、策略替换等）
- [ ] 重试机制实现

**Day 6-7: 单元测试**
- [ ] 各质检点独立测试
- [ ] 调节机制测试
- [ ] 端到端流程测试

### Week 2: 知识库增强（支撑质检）

**Day 1-2: 补充资产配置案例**
- [ ] 16种画像×周期组合案例（已有理论，需补充具体配置案例）
- [ ] 每种案例包含：配置比例+理由+历史回测

**Day 3-4: 补充风控案例**
- [ ] 不同画像的止损线设置案例
- [ ] 历史回撤与风控效果案例
- [ ] 行为金融与风控适配案例

**Day 5-6: 补充策略绑定案例**
- [ ] 策略-标的不匹配的历史教训
- [ ] 策略同质化导致的风险案例
- [ ] 策略寿命到期后的处理案例

**Day 7: 索引重建与测试**
- [ ] 重建所有索引
- [ ] 验证检索质量

### Week 3: 集成测试与优化

**Day 1-2: 端到端测试**
- [ ] 完整链路测试（画像→组合→RAG质检→输出）
- [ ] 各种边界条件测试
- [ ] 性能测试（RAG质检耗时）

**Day 3-4: 调节机制调优**
- [ ] 调节阈值校准
- [ ] 重试次数优化
- [ ] 降级策略设计

**Day 5-6: 前端展示**
- [ ] 质检记录展示（"为什么这样调节"）
- [ ] 理论依据卡片
- [ ] 风险提示弹窗

**Day 7: 文档与上线**
- [ ] API文档更新
- [ ] 操作手册
- [ ] 上线检查清单

---

## 七、API 设计

### 7.1 新增端点

```python
# POST /api/v1/portfolios/design-with-rag
{
    "profile_vector": {...},
    "market_signal": {...},
    "use_rag_gate": true,  # 是否启用RAG质检
    "rag_strictness": "normal",  # strict/normal/loose
}

# 响应
{
    "portfolio": {...},  # 组合配置
    "rag_reviews": [  # RAG质检记录
        {
            "step": "saa",
            "passed": false,
            "score": 0.6,
            "issues": ["股票权重过高"],
            "adjustments": [
                {"type": "weight_cap", "asset": "stock", "from": 0.8, "to": 0.7}
            ],
            "theory_cited": ["theory_markowitz", "theory_all_weather"]
        }
    ],
    "rag_adjusted": true,
    "generation_time_ms": 2500
}
```

### 7.2 质检详情端点

```python
# GET /api/v1/portfolios/{id}/rag-reviews
{
    "reviews": [...],
    "total_adjustments": 3,
    "theories_cited": [...],
    "cases_cited": [...]
}
```

---

## 八、评估标准

| 测试场景 | 输入 | 预期RAG行为 | 合格标准 |
|---------|------|-----------|---------|
| **SAA: 保守型+高股票权重** | 画像保守, SAA股票50% | 不通过, 建议降至30% | 调节后股票≤30% |
| **SAA: 行情极差+高配股票** | VIX>40, 股债利差<2%, SAA股票50% | 不通过, 结合信号压缩至20% | 调节后股票≤画像基准 |
| **SAA: 地缘风险+无对冲** | 地缘风险高, 黄金0% | 不通过, 建议增配黄金10% | 调节后有避险资产 |
| **TAA: 行业过度集中** | 单一行业占股票60% | 不通过, 建议分散 | 调节后≤50% |
| **绑定: 跑输持有** | 策略收益5%, 持有收益15% | 不通过, RAG分析原因→调参 | 重新回测后跑赢持有 |
| **绑定: 策略不匹配** | 均值回归策略绑定强趋势股 | 不通过, 换动量策略 | 新策略跑赢持有 |
| **风控: 高损失厌恶+宽止损** | 损失厌恶0.9, 止损15% | 不通过, 建议收紧至5% | 调节后止损≤8% |
| **可靠性: 未跑赢持有** | 组合收益8%, 持有收益12% | 不通过, 调参/换策略 | 重新回测后组合>持有 |
| **可靠性: 压力测试失败** | 2022熊市回撤35% | 不通过, 加强防御 | 调节后通过压力测试 |
| **完美组合** | 所有指标合理 | 通过, 无调节 | 直接输出 |

---

## 九、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| RAG质检耗时过长 | 组合生成变慢 | 设置超时(5s), 超时则跳过质检 |
| LLM审核不稳定 | 结果不一致 | 多次采样取多数, 或降级为规则审核 |
| 过度调节 | 组合过于保守 | 设置调节上限, 最多调节3次 |
| 知识库覆盖不足 | 某些场景无参考 | 默认通过+记录待补充知识 |
| 用户不理解调节 | 体验下降 | 前端展示"为什么这样调节"的解释 |

---

## 十、文件变更清单

```
backend/
├── app/
│   ├── services/
│   │   ├── rag/
│   │   │   ├── portfolio_quality_gate.py      # 新增: RAG质检服务
│   │   │   ├── review_prompts.py              # 新增: 审核Prompt模板
│   │   │   └── adjustment_engine.py           # 新增: 调节引擎
│   │   ├── hybrid_portfolio_designer.py       # 修改: 集成RAG质检
│   │   └── saa_engine.py                      # 修改: 支持调节
│   ├── api/v1/endpoints/
│   │   └── portfolios.py                      # 修改: 新增/design-with-rag端点
│   └── schemas/
│       └── portfolio.py                       # 修改: 新增RAG相关字段
├── data/knowledge/
│   ├── allocation_cases/                      # 新增: 16种配置案例
│   ├── risk_control_cases/                    # 新增: 风控案例
│   └── strategy_binding_cases/                # 新增: 策略绑定案例
└── docs/
    └── rag-hybrid-integration-plan.md           # 本文档
```

---

*计划制定: 2026-06-08 | 预计完成: 2026-06-29*
