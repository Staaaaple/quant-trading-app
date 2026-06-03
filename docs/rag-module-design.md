# RAG 模块设计方案

**版本**: V1
**日期**: 2026-06-03
**定位**: 投资顾问专家，引擎内部模块，用户不可见
**核心功能**: 在选股/组合/策略三阶段执行评估→诊断→微调指令生成

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG 模块 (Investment Advisor)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  知识库层    │    │  检索引擎    │    │  LLM推理层   │     │
│  │             │    │             │    │             │     │
│  │ • 论文向量库 │───→│ • 向量检索   │───→│ • 场景理解   │     │
│  │ • 案例库    │    │ • 关键词检索 │    │ • 诊断推理   │     │
│  │ • 规则库    │    │ • 混合检索   │    │ • 指令生成   │     │
│  │ • 历史记录  │    │             │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  评估接口层 (对外暴露)                                │    │
│  │                                                      │    │
│  │  evaluate_stock_selection(inputs) → verdict + adjust │    │
│  │  evaluate_portfolio(inputs)       → verdict + adjust │    │
│  │  evaluate_strategy(inputs)        → verdict + adjust │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、知识库层设计

### 2.1 知识库组成

| 知识库 | 内容 | 存储方式 | 更新频率 |
|--------|------|---------|---------|
| **论文向量库** | 量化论文的摘要、结论、方法、参数范围、回测结果 | 向量数据库(chroma/faiss) + 结构化字段(SQLite) | 每月 |
| **案例库** | 历史选股/组合/策略的成败案例，含场景描述和结果 | 向量数据库 + 结构化字段 | 每周 |
| **规则库** | 投资基本原则、硬指标门槛、风控规则 | SQLite关系表 | 每季度 |
| **历史记录** | 本系统运行以来的所有RAG决策记录，用于学习 | SQLite | 实时 |

### 2.2 论文向量库详细设计

**每篇论文的存储结构**:

```python
{
    # 结构化字段 (SQLite)
    "paper_id": "paper_001",
    "title": "Factor Momentum and the Momentum Factor",
    "authors": "Ehsani, S., Linnainmaa, J.T.",
    "year": 2022,
    "family": "因子动量",  # 策略家族分类
    
    # 核心结论 (向量化)
    "conclusion_vector": [0.12, -0.05, 0.33, ...],  # 384维
    "conclusion_text": "因子层面的动量可以解释个股动量...",
    
    # 关键发现 (向量化)
    "findings_vectors": [
        {"text": "因子动量先于个股动量", "vector": [...]},
        {"text": "在A股市场效果显著", "vector": [...]},
    ],
    
    # 参数范围 (结构化)
    "param_space": {
        "lookback_period": {"range": [3, 6, 12], "optimal": 6},
        "holding_period": {"range": [1, 3, 6], "optimal": 1},
    },
    
    # 适用条件 (结构化+向量化)
    "suitable_cycles": ["复苏", "扩张"],
    "suitable_markets": ["A股", "美股"],
    "market_conditions_vector": [...],  # 描述适用市场状态的向量
    
    # 回测结果 (结构化)
    "backtest_results": {
        "sharpe": 1.2,
        "max_drawdown": 0.15,
        "win_rate": 0.58,
        "sample_markets": ["A股", "美股"],
        "sample_period": "2010-2020",
    },
    
    # 失效模式 (向量化，用于诊断)
    "failure_modes": [
        {"condition": "高波动市场", "reason": "动量反转频繁", "vector": [...]},
    ],
}
```

**向量化内容**:
- 论文摘要
- 核心结论
- 关键发现（每条单独向量化）
- 适用市场条件描述
- 失效模式描述

**embedding模型**: `sentence-transformers/all-MiniLM-L6-v2` (本地，384维)

### 2.3 案例库详细设计

**每个案例的存储结构**:

```python
{
    "case_id": "case_20240501_001",
    "case_type": "stock_selection",  # stock_selection / portfolio / strategy
    
    # 场景描述 (向量化)
    "scenario_vector": [...],
    "scenario_text": "复苏期+稳健型用户+动量权重35%",
    
    # 输入详情 (结构化)
    "inputs": {
        "market_cycle": "复苏",
        "risk_label": "稳健型",
        "factor_weights": {"momentum": 0.35, "value": 0.20},
        "selected_stocks": [...],
    },
    
    # 问题诊断
    "problem": "科技占比45%，行业过度集中",
    "problem_vector": [...],
    
    # 调整方案
    "adjustment": {
        "type": "factor_weight",
        "changes": {"momentum": 0.25, "value": 0.30},
    },
    
    # 结果
    "result": "成功，科技占比降至28%",
    "result_vector": [...],
    "cycles": 2,
    "final_metrics": {"sector_concentration": 0.28},
    
    # 时间戳
    "created_at": "2024-05-01",
}
```

### 2.4 规则库详细设计

**规则分类**:

```python
# 选股规则
STOCK_SELECTION_RULES = {
    "concentration_limit": {
        "description": "行业集中度上限",
        "condition": "max_sector_weight > threshold",
        "thresholds": {"conservative": 0.20, "moderate": 0.25, "aggressive": 0.30},
        "severity": "hard",  # hard = 必须遵守, soft = 建议遵守
    },
    "quality_threshold": {
        "description": "质量因子门槛",
        "condition": "avg_roe < threshold",
        "threshold": 0.10,
        "severity": "hard",
    },
    # ...
}

# 组合规则
PORTFOLIO_RULES = {
    "single_stock_cap": {
        "description": "单只持仓上限",
        "thresholds": {"conservative": 0.10, "moderate": 0.15, "aggressive": 0.20, "very_aggressive": 0.25},
        "severity": "hard",
    },
    # ...
}

# 策略规则
STRATEGY_RULES = {
    "stop_loss_range": {
        "description": "止损线合理范围",
        "min": 0.02,
        "max": 0.15,
        "severity": "hard",
    },
    "win_rate_threshold": {
        "description": "回测胜率门槛",
        "threshold": 0.40,
        "severity": "hard",
    },
    # ...
}
```

---

## 三、检索引擎设计

### 3.1 混合检索策略

```python
def retrieve_knowledge(query: str, context: dict, top_k: int = 5) -> list[dict]:
    """
    混合检索: 向量检索 + 结构化过滤 + 关键词匹配
    """
    
    # Step 1: 向量检索 (语义相似度)
    query_vector = embedding_model.encode(query)
    vector_results = vector_db.similarity_search(
        query_vector, 
        k=top_k * 2,
        filter={"type": ["paper", "case"]}  # 只检索论文和案例
    )
    
    # Step 2: 结构化过滤 (硬条件匹配)
    # 根据 context 中的市场周期、风险等级等过滤
    filtered_results = []
    for result in vector_results:
        if matches_hard_constraints(result, context):
            filtered_results.append(result)
    
    # Step 3: 关键词匹配 (精确匹配)
    keyword_results = keyword_search(query, context)
    
    # Step 4: 重排序 (RRF - Reciprocal Rank Fusion)
    final_results = reciprocal_rank_fusion(vector_results, keyword_results, top_k)
    
    return final_results
```

### 3.2 检索示例

**场景**: 选股后评估，发现科技占比45%

```python
query = "复苏期 稳健型用户 动量因子权重高 科技股过度集中 如何调整"
context = {
    "market_cycle": "复苏",
    "risk_label": "稳健型",
    "current_factor_weights": {"momentum": 0.35, "value": 0.20},
    "problem": "sector_concentration",
    "current_metrics": {"tech_weight": 0.45},
}

# 检索结果:
results = [
    {
        "source": "case",
        "case_id": "case_20240501_001",
        "similarity": 0.92,
        "scenario": "复苏期+稳健型+动量权重35%→科技45%",
        "adjustment": "动量25%+价值30%→科技28%",
        "result": "成功",
    },
    {
        "source": "paper",
        "paper_id": "paper_003",
        "similarity": 0.85,
        "conclusion": "价值因子在复苏期后半段表现优于动量因子",
        "evidence": "2010-2020年A股数据",
    },
    {
        "source": "rule",
        "rule_id": "concentration_limit",
        "threshold": 0.25,
        "current": 0.45,
        "status": "violated",
    },
]
```

---

## 四、LLM推理层设计

### 4.1 LLM角色设定

```python
SYSTEM_PROMPT = """你是一位资深量化投资顾问，拥有20年A股市场经验。

你的职责:
1. 评估投资方案的质量
2. 发现问题时给出具体的调整建议
3. 调整建议必须基于历史案例和学术研究的支撑

你的工作方式:
- 你会收到当前的投资方案和相关数据
- 你会检索到相似的历史案例和论文结论
- 你需要判断当前方案是否合格
- 如果不合格，你需要诊断原因并给出具体的微调指令

输出格式要求:
你必须输出结构化的JSON，包含以下字段:
- verdict: "pass" 或 "reject"
- confidence: 0-1 的置信度
- diagnosis: 问题诊断（如果有）
- evidence: 支撑你判断的证据列表
- adjustment: 具体的微调指令（如果reject）
- rationale: 你的推理过程简述

重要原则:
- 硬指标必须严格遵守（集中度、回撤、胜率等）
- 相似周期回测表现是核心判断依据
- 不确定时保守处理，建议再优化而非勉强通过
"""
```

### 4.2 LLM输入构建

```python
def build_llm_prompt(phase: str, inputs: dict, retrieved_knowledge: list) -> str:
    """
    构建LLM的输入prompt
    """
    
    prompt = f"""# 评估任务: {phase}

## 当前方案
```json
{json.dumps(inputs, indent=2, ensure_ascii=False)}
```

## 检索到的相关知识
"""
    
    for i, knowledge in enumerate(retrieved_knowledge, 1):
        prompt += f"""
### 知识{i} [{knowledge['source']}]
{knowledge.get('scenario', knowledge.get('conclusion', ''))}

调整方案: {knowledge.get('adjustment', 'N/A')}
结果: {knowledge.get('result', 'N/A')}
"""
    
    prompt += """
## 硬指标要求
"""
    
    # 根据phase添加对应的硬指标
    if phase == "stock_selection":
        prompt += """
- 股票数量 >= 30
- 行业集中度 <= 25% (稳健型)
- 平均ROE >= 10%
- 与画像风险等级匹配
"""
    elif phase == "portfolio":
        prompt += """
- 单只持仓 <= 15% (稳健型)
- 行业集中度 <= 30%
- 预期波动率 < 用户承受阈值
- 夏普比率 > 0.3
"""
    elif phase == "strategy":
        prompt += """
- 策略-特征匹配度 > 70%
- 回测胜率 > 40%
- 止损线在2%-15%之间
- 策略类型多样性 >= 3种
"""
    
    prompt += """
## 请输出评估结果

请判断当前方案是否通过，如果不通过请给出具体的微调指令。
"""
    
    return prompt
```

### 4.3 LLM输出解析

```python
def parse_llm_output(llm_response: str) -> dict:
    """
    解析LLM的输出为结构化数据
    """
    
    # 提取JSON部分
    json_match = re.search(r'```json\n(.*?)\n```', llm_response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = llm_response
    
    result = json.loads(json_str)
    
    # 验证必要字段
    required_fields = ["verdict", "confidence", "rationale"]
    for field in required_fields:
        if field not in result:
            raise ValueError(f"LLM输出缺少必要字段: {field}")
    
    # 如果reject，必须有adjustment
    if result["verdict"] == "reject" and "adjustment" not in result:
        raise ValueError("Reject时必须提供adjustment")
    
    return result
```

### 4.4 LLM输出示例

```json
{
    "verdict": "reject",
    "confidence": 0.92,
    "diagnosis": "行业过度集中，科技占比45%，超过稳健型用户25%的门槛。根本原因是动量因子权重35%过高，科技股市值大、近期涨幅高，在动量因子下得分虚高。",
    "evidence": [
        {
            "source": "case_20240501_001",
            "description": "相似场景：复苏期+稳健型+动量35%→科技45%，调整后成功"
        },
        {
            "source": "paper_003",
            "description": "价值因子在复苏期后半段表现优于动量因子"
        },
        {
            "source": "rule_concentration_limit",
            "description": "稳健型用户行业集中度门槛25%，当前45%严重超标"
        }
    ],
    "adjustment": {
        "type": "factor_weight",
        "target": "static_stock_picker",
        "changes": {
            "momentum_weight": {"from": 0.35, "to": 0.25},
            "value_weight": {"from": 0.20, "to": 0.30}
        },
        "expected_fix": "科技占比从45%降至30%"
    },
    "rationale": "基于历史案例和论文研究，复苏期稳健型用户应降低动量因子权重、提高价值因子权重，以平衡行业分布。参考案例case_20240501_001在相似场景下成功将科技占比从45%降至28%。"
}
```

---

## 五、评估接口层设计

### 5.1 对外接口

```python
class RAGInvestmentAdvisor:
    """RAG投资顾问，对外暴露三个评估接口"""
    
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.retrieval_engine = RetrievalEngine()
        self.llm = LLMClient()
    
    def evaluate_stock_selection(
        self,
        profile_vector: dict,
        market_signal: dict,
        selected_stocks: list,
        factor_weights: dict,
        iteration: int = 1,
    ) -> dict:
        """
        评估选股结果
        
        Returns:
            {
                "verdict": "pass" | "reject",
                "confidence": float,
                "adjustment": dict | None,  # 如果reject
                "diagnosis": str | None,
                "evidence": list,
                "rationale": str,
            }
        """
        
        # 1. 硬指标检查
        hard_check = self._check_hard_metrics("stock_selection", selected_stocks, profile_vector)
        if not hard_check["passed"]:
            # 硬指标不过，直接reject，无需LLM
            return {
                "verdict": "reject",
                "confidence": 1.0,
                "adjustment": self._generate_hard_adjustment(hard_check),
                "diagnosis": hard_check["reason"],
                "evidence": [{"source": "hard_rule", "description": hard_check["reason"]}],
                "rationale": f"硬指标未通过: {hard_check['reason']}",
            }
        
        # 2. 构建查询
        query = self._build_selection_query(profile_vector, market_signal, selected_stocks, factor_weights)
        context = {
            "market_cycle": market_signal["market_cycle"],
            "risk_label": profile_vector["risk_label"],
            "current_metrics": self._extract_selection_metrics(selected_stocks),
        }
        
        # 3. 检索知识
        knowledge = self.retrieval_engine.retrieve(query, context, top_k=5)
        
        # 4. LLM评估
        prompt = build_llm_prompt("stock_selection", {
            "profile": profile_vector,
            "market": market_signal,
            "stocks": selected_stocks[:10],  # 只传前10只示例
            "factor_weights": factor_weights,
            "metrics": context["current_metrics"],
            "iteration": iteration,
        }, knowledge)
        
        llm_response = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        result = parse_llm_output(llm_response)
        
        # 5. 记录历史
        self._log_decision("stock_selection", inputs, result)
        
        return result
    
    def evaluate_portfolio(
        self,
        profile_vector: dict,
        market_signal: dict,
        portfolio: dict,
        iteration: int = 1,
    ) -> dict:
        """评估组合配置"""
        # 类似结构...
        pass
    
    def evaluate_strategy(
        self,
        profile_vector: dict,
        market_signal: dict,
        portfolio: dict,
        strategy_bindings: list,
        iteration: int = 1,
    ) -> dict:
        """评估策略绑定"""
        # 类似结构...
        pass
```

### 5.2 使用示例

```python
# 初始化
advisor = RAGInvestmentAdvisor()

# 选股评估
result = advisor.evaluate_stock_selection(
    profile_vector={"risk_label": "稳健型", "loss_aversion": 7},
    market_signal={"market_cycle": "复苏", "composite_score": 0.6},
    selected_stocks=[...],  # 50-100只股票
    factor_weights={"momentum": 0.35, "value": 0.20, "quality": 0.25, "low_vol": 0.20},
)

if result["verdict"] == "reject":
    # 应用微调指令
    adjustment = result["adjustment"]
    # 重新选股...
    # 再次评估...
else:
    # 进入组合构建
    pass
```

---

## 六、技术实现方案

### 6.1 依赖组件

| 组件 | 选择 | 说明 |
|------|------|------|
| 向量数据库 | Chroma (本地) | 轻量，无需额外服务 |
| Embedding模型 | all-MiniLM-L6-v2 | 本地运行，384维，足够用 |
| LLM | Claude API / OpenAI API | 专家推理需要强LLM |
| 结构化存储 | SQLite | 已有，无需新增 |

### 6.2 文件结构

```
backend/app/services/rag/
├── __init__.py
├── advisor.py              # RAGInvestmentAdvisor 主类
├── knowledge_base.py       # 知识库管理
├── retrieval_engine.py     # 检索引擎
├── llm_client.py           # LLM客户端封装
├── prompt_builder.py       # Prompt构建
├── output_parser.py        # 输出解析
├── hard_metrics.py         # 硬指标检查
├── models/                 # 数据模型
│   ├── paper_vector.py
│   ├── case_vector.py
│   └── decision_log.py
└── config.py               # 配置
```

### 6.3 初始化流程

```python
def initialize_rag_module(db: Session):
    """初始化RAG模块"""
    
    # 1. 加载论文数据到向量库
    papers = db.query(PaperKnowledge).all()
    for paper in papers:
        # 向量化核心结论
        conclusion_vector = embedding_model.encode(paper.core_conclusion)
        # 存入Chroma
        chroma_collection.add(
            ids=[paper.id],
            embeddings=[conclusion_vector],
            metadatas=[{
                "type": "paper",
                "family": paper.family,
                "suitable_cycles": paper.suitable_cycles,
            }]
        )
    
    # 2. 加载历史案例到向量库
    cases = db.query(RAGDecisionLog).filter(RAGDecisionLog.verdict == "pass").all()
    for case in cases:
        scenario_vector = embedding_model.encode(case.scenario_text)
        chroma_collection.add(
            ids=[case.case_id],
            embeddings=[scenario_vector],
            metadatas=[{"type": "case", "case_type": case.case_type}]
        )
    
    # 3. 加载规则库到内存
    load_rules_to_memory()
```

---

## 七、性能与成本考量

### 7.1 LLM调用优化

| 优化策略 | 说明 |
|---------|------|
| 硬指标预过滤 | 硬指标不过直接reject，不调用LLM |
| 缓存相似查询 | 相同场景的查询缓存结果 |
| 异步批处理 | 多只股票评估时批量调用 |
| 降级策略 | LLM不可用时 fallback 到规则引擎 |

### 7.2 成本估算

| 场景 | LLM调用次数 | 预估成本 |
|------|------------|---------|
| 选股评估通过 | 1次 | ~$0.01 |
| 选股评估需2轮 | 2次 | ~$0.02 |
| 完整流程(三阶段) | 3-9次 | ~$0.03-$0.09 |

---

## 八、实施优先级

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 搭建Chroma向量库 | 存储论文/案例向量 |
| P0 | 实现Embedding服务 | 文本→向量转换 |
| P0 | 实现硬指标检查 | 不依赖LLM的快速过滤 |
| P1 | 实现LLM客户端 | 封装Claude/OpenAI API |
| P1 | 实现Prompt构建 | 三阶段各自的prompt模板 |
| P1 | 实现输出解析 | JSON提取和验证 |
| P2 | 实现检索引擎 | 混合检索策略 |
| P2 | 实现完整Advisor类 | 对外暴露三个接口 |
| P2 | 初始化知识库 | 加载现有论文数据 |
| P3 | 学习机制 | 记录决策历史，优化检索 |
