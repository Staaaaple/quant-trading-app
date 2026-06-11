# RAG 知识库重构计划 V2

> 基于 project-report-v1.md 重新设计，不再索引策略模板，改为三类知识源

---

## 一、问题：当前实现的问题

当前 `index_builder.py` 把 **策略模板** 和 **论文** 都索引进向量库：

| 问题 | 说明 |
|------|------|
| 策略模板是代码+参数 | 不是自然语言知识，语义检索效果差 |
| 论文只有元数据 | 没有PDF全文，检索内容太浅 |
| 缺少"历史策略案例" | 报告规划中有，但未实现 |
| 缺少"市场规律文档" | 报告规划中有，但未实现 |

---

## 二、正确做法：三类知识源

根据报告第3.4节规划，RAG 应该检索三类内容：

```
向量检索（FAISS）
├── 匹配相关论文片段 ← 论文PDF解析+分块
├── 匹配历史策略案例 ← 回测报告/策略表现记录
└── 匹配市场规律文档 ← 经济周期/资产配置规则/行为金融学原理
```

### 2.1 知识源一：论文片段库 (paper_chunks)

**数据来源**：
- 20篇核心论文的 PDF 全文（需要下载/解析）
- arXiv 摘要 + 结论段落
- 关键图表说明文字

**文档结构示例**：
```
[chunk_id]: paper_001_chunk_003
[来源]: Ehsani & Linnainmaa (2022), Journal of Finance
[章节]: Abstract + Introduction
[内容]: "We show that factor momentum can explain individual stock momentum... 
        The momentum factor itself is a manifestation of factor momentum..."
[关键词]: 因子动量, 个股动量, 横截面收益
[适用场景]: 策略推荐-动量类, 用户提问-为什么动量有效
```

**索引字段**：
- `chunk_id`, `paper_id`, `title`, `authors`, `year`
- `section` (abstract/introduction/methodology/conclusion)
- `content` (要Embedding的文本)
- `keywords` (人工标注或LLM提取)
- `applicable_scenarios` (适用场景标签)

---

### 2.2 知识源二：历史策略案例库 (strategy_cases)

**数据来源**：
- 回测报告摘要（35个策略的回测结果）
- 策略在特定市场环境下的表现记录
- 策略失效案例分析

**文档结构示例**：
```
[case_id]: case_mv_2022_bear
[策略]: 动量-波动率评分策略 (mom_window=5, vol_window=30)
[市场环境]: 2022年熊市, 沪深300下跌21%, 高波动
[表现]: 胜率38%, 最大回撤18%, 夏普-0.3
[结论]: 该参数组合在熊市中表现不佳，建议缩短动量窗口或提高波动率权重
[适用查询]: "熊市用什么策略", "动量策略失效怎么办"
```

**索引字段**：
- `case_id`, `strategy_name`, `strategy_params`
- `market_period`, `market_cycle`, `market_conditions`
- `performance_summary` (胜率/夏普/回撤)
- `lesson_learned` (经验教训)
- `content` (要Embedding的完整描述)

---

### 2.3 知识源三：市场规律文档库 (market_rules)

**数据来源**：
- 经济周期与资产配置规则（美林时钟等）
- 行为金融学原理（损失厌恶、锚定效应等）
- 量化投资常识（因子有效性、策略同质化等）
- 股票/基金基础金融常识（面向小白用户）

**文档结构示例**：
```
[rule_id]: rule_merrill_clock_001
[主题]: 美林时钟-复苏期配置
[内容]: "复苏期特征：经济增长↑, 通胀↓。最优配置：股票>债券>现金>商品。
        历史数据：复苏期股票平均年化收益15%，债券8%。
        注意事项：复苏早期市场可能仍有波动，建议分批建仓。"
[来源]: 美林证券研究报告 + 历史回测验证
[适用场景]: SAA配置, 用户提问-现在该买什么
```

**索引字段**：
- `rule_id`, `category` (经济周期/行为金融/量化常识/风险管理/**基础金融**)
- `topic`, `content` (要Embedding的文本)
- `source`, `verified` (是否经过回测验证)
- `difficulty` (入门/进阶/专业) —— 基础金融常识标记为"入门"

### 2.4 知识源四：基础金融常识库 (finance_basics)

**定位**：面向投资小白的"词典式"知识库

**为什么需要**：
- 用户问"什么是ETF"、"股票和基金有什么区别"
- 用户不理解"夏普比率"、"最大回撤"是什么意思
- 用户不知道"T+1"、"涨跌停板"等基本规则
- 这些知识不应该让LLM"编造"，需要准确、统一的解释

**数据来源**：
- 证监会/交易所官方投资者教育材料
- 经典投资入门书籍（《聪明的投资者》《漫步华尔街》等）
- 券商投资者教育文章
- 自行编写的标准化解释

**文档结构示例**：
```
[entry_id]: basic_etf_001
[主题]: ETF是什么
[难度]: 入门
[内容]: "ETF（Exchange Traded Fund，交易型开放式指数基金）是一种在交易所上市交易的基金。
        特点：
        1. 像股票一样买卖，实时交易
        2. 跟踪特定指数（如沪深300ETF跟踪沪深300指数）
        3. 费用低（管理费通常0.5%以下）
        4. 分散投资，降低个股风险
        
        适合人群：想投资股市但不懂选股的投资者
        注意事项：ETF也有波动，不是保本产品"
[相关概念]: ["指数基金", "场内基金", "沪深300"]
[常见问题]: ["ETF和股票有什么区别", "ETF和基金有什么区别"]
[来源]: 上交所投资者教育 + 自行整理
```

**索引字段**：
- `entry_id`, `category` (投资工具/交易规则/风险指标/市场机制)
- `topic`, `content` (要Embedding的文本)
- `difficulty` (入门/进阶/专业)
- `related_concepts` (相关概念列表)
- `common_questions` (常见问题列表)
- `source`

**与 market_rules 的区别**：

| 维度 | market_rules | finance_basics |
|------|-------------|----------------|
| 内容 | "复苏期该买什么" | "ETF是什么" |
| 目的 | 支撑策略决策 | 教育用户基础概念 |
| 难度 | 进阶-专业 | 入门 |
| 用户场景 | "为什么推荐这个" | "这个词是什么意思" |

---

## 三、RAG 检索流程（重写）

### 3.1 查询分类器

用户查询/策略生成时，先分类查询意图：

```python
class QueryIntent(Enum):
    STRATEGY_RECOMMEND = "策略推荐"      # → 检索论文+案例
    MARKET_EXPLANATION = "市场解释"      # → 检索市场规律
    RISK_ANALYSIS = "风险分析"           # → 检索论文+规律
    PORTFOLIO_RATIONALE = "组合理由"     # → 检索三类全部
    GENERAL_QUESTION = "一般问题"        # → 检索市场规律
```

### 3.2 检索路由

```
用户查询
    │
    ▼
[查询分类器] ──→ 确定检索意图
    │
    ▼
[多路检索]
├── 论文片段库 (top_k=3)
│   └── 过滤: 与查询意图相关的场景标签
├── 历史案例库 (top_k=2)
│   └── 过滤: 匹配当前市场环境
└── 市场规律库 (top_k=2)
    └── 过滤: 与查询主题相关
    │
    ▼
[重排序] ──→ 按相关度+时效性+可信度排序
    │
    ▼
[上下文组装] ──→ 构建带引用的prompt
    │
    ▼
[Qwen3生成] ──→ 带论文引用的专业回答
```

### 3.3 生成格式要求

LLM 输出必须包含引用标记：

```markdown
根据 [Ehsani & Linnainmaa, 2022] 的研究，因子动量可以解释个股动量效应。
这意味着...（解释）

历史数据显示，在类似2022年熊市环境下 [case_mv_2022_bear]，
动量策略表现不佳，建议...（建议）

按照美林时钟理论 [rule_merrill_clock_001]，当前复苏期应超配股票...
```

---

## 四、数据模型变更

### 4.1 新增模型

```python
# models/rag_knowledge.py

class PaperChunk(Base):
    """论文片段"""
    __tablename__ = "paper_chunks"
    
    id = Column(Integer, primary_key=True)
    chunk_id = Column(String(64), unique=True, index=True)
    paper_id = Column(String(64), index=True)  # 关联 paper_knowledges
    
    # 来源信息
    title = Column(String(512))
    authors = Column(String(512))
    year = Column(Integer)
    journal = Column(String(256))
    
    # 内容
    section = Column(String(64))  # abstract/introduction/method/conclusion
    content = Column(Text)  # 片段全文（用于Embedding）
    content_zh = Column(Text, nullable=True)  # 中文翻译（如有）
    
    # 标签
    keywords = Column(JSON)  # ["因子动量", "横截面收益"]
    applicable_scenarios = Column(JSON)  # ["策略推荐-动量类", "用户教育"]
    
    # 向量（可选，也可以只存ID，向量放FAISS）
    # embedding = Column(Vector(384))  # pgvector扩展


class StrategyCase(Base):
    """历史策略案例"""
    __tablename__ = "strategy_cases"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(String(64), unique=True, index=True)
    
    # 策略信息
    strategy_name = Column(String(128))
    strategy_family = Column(String(32))
    strategy_params = Column(JSON)
    
    # 市场环境
    market_period = Column(String(32))  # "2022-01~2022-12"
    market_cycle = Column(String(16))  # 复苏/过热/滞胀/衰退
    market_conditions = Column(Text)  # 描述性文字
    
    # 表现
    performance_summary = Column(JSON)  # {"sharpe": -0.3, "max_dd": 0.18, "win_rate": 0.38}
    backtest_detail = Column(JSON, nullable=True)
    
    # 结论
    lesson_learned = Column(Text)  # 经验教训
    recommendation = Column(Text)  # 建议
    
    # 内容（用于Embedding）
    content = Column(Text)  # 完整描述文本


class MarketRule(Base):
    """市场规律/投资原理"""
    __tablename__ = "market_rules"
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(String(64), unique=True, index=True)
    
    category = Column(String(32), index=True)  # 经济周期/行为金融/量化常识/风险管理
    topic = Column(String(128))
    
    content = Column(Text)  # 规律描述（用于Embedding）
    content_zh = Column(Text, nullable=True)
    
    source = Column(String(256))  # 来源
    verified = Column(Boolean, default=False)  # 是否经过验证
    applicable_cycles = Column(JSON)  # ["复苏", "过热"]
```

### 4.2 索引构建器重写

```python
# services/rag/index_builder_v2.py

class IndexBuilderV2:
    """新版索引构建器 - 三类知识源"""
    
    INDEX_NAMES = {
        "paper_chunks": "paper_chunk_index",
        "strategy_cases": "strategy_case_index", 
        "market_rules": "market_rule_index",
    }
    
    def build_paper_chunk_index(self, db: Session):
        """构建论文片段索引"""
        chunks = db.query(PaperChunk).all()
        # ... 生成embedding，存入FAISS
        
    def build_strategy_case_index(self, db: Session):
        """构建历史案例索引"""
        cases = db.query(StrategyCase).all()
        # ... 生成embedding，存入FAISS
        
    def build_market_rule_index(self, db: Session):
        """构建市场规律索引"""
        rules = db.query(MarketRule).all()
        # ... 生成embedding，存入FAISS
```

---

## 五、实施步骤

### Phase 1: 数据准备（本周）

1. **论文PDF下载与解析**
   - 从 arXiv/Sci-Hub 下载20篇论文PDF
   - 用 PyPDF2/pdfplumber 提取文本
   - 按章节分块（每块500-1000字）
   - 存入 `paper_chunks` 表

2. **历史案例整理**
   - 从 `backtest_summary` 提取35个策略的回测结果
   - 按市场环境分类（牛市/熊市/震荡）
   - 人工编写 `lesson_learned`
   - 存入 `strategy_cases` 表

3. **市场规律文档编写**
   - 整理美林时钟、行为金融学等知识
   - 编写中文解释文档
   - 存入 `market_rules` 表

### Phase 2: 索引构建（下周）

1. 实现 `IndexBuilderV2`
2. 三类知识源分别构建FAISS索引
3. 添加元数据过滤（category/section/applicable_scenarios）

### Phase 3: 检索服务重写（下周）

1. 实现查询分类器
2. 多路检索+重排序
3. 引用溯源功能
4. 与 Qwen3 集成

### Phase 4: 前端展示（后续）

1. 策略推荐页显示"理论依据"卡片
2. 论文引用可点击展开
3. 历史案例对比图表

---

## 六、关键变更总结

| 维度 | 旧实现 | 新实现 |
|------|--------|--------|
| **索引内容** | 策略模板代码 + 论文元数据 | 论文片段 + 历史案例 + 市场规律 |
| **检索对象** | 策略参数匹配 | 知识片段语义匹配 |
| **生成输出** | 策略配置JSON | 带论文引用的解释文本 |
| **用户价值** | "给你策略" | "告诉你为什么" |
| **可信度** | 低（黑盒） | 高（论文支撑） |

---

## 七、与现有系统的集成点

```
现有系统
├── 策略池 (35个模板) ──→ 提供策略参数，不索引
├── 论文库 (20篇元数据) ──→ 扩展为PDF全文+分块
├── 回测结果 ──→ 生成历史案例
└── 市场信号 ──→ 作为案例检索的过滤条件

RAG系统（新）
├── 论文片段索引 ──→ 支撑策略理论依据
├── 历史案例索引 ──→ 支撑"类似环境表现"
├── 市场规律索引 ──→ 支撑"为什么这样配"
└── Qwen3 ──→ 生成带引用的自然语言解释
```
