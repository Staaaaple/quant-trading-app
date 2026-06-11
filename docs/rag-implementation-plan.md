# RAG 投资顾问专家 — 详细构建计划

> 版本: V1.0 | 日期: 2026-06-08 | 预计周期: 6周

---

## 一、项目总览

### 1.1 目标

构建一个具备三大核心能力的 RAG 投资顾问专家：
- **选股能力**：基本面分析 + 估值判断 + 因子选股
- **资产组合能力**：战略配置(SAA) + 战术配置(TAA) + 风险分散
- **买卖节点判断**：买入信号 + 卖出信号 + 止损纪律 + 仓位管理

### 1.2 交付物清单

| 序号 | 交付物 | 说明 |
|------|--------|------|
| 1 | 六大知识库数据 | 20个股案例 + 16种组合 + 30个择时信号 + 20个行为案例 + 50个基础概念 + 20篇论文 |
| 2 | 数据库模型 | 6张知识表 + 向量索引 |
| 3 | 索引构建服务 | 自动构建/更新 FAISS 索引 |
| 4 | 检索服务 | 查询分类 + 多路检索 + 重排序 |
| 5 | LLM生成服务 | Qwen3 集成 + 投资顾问式回答模板 |
| 6 | API接口 | 6个REST端点 |
| 7 | 前端组件 | 3个Vue组件 |
| 8 | 测试套件 | 单元测试 + 集成测试 + 评估脚本 |

### 1.3 技术栈

```
数据层: SQLite + SQLAlchemy
向量层: FAISS (sentence-transformers Embedding)
LLM层: Qwen3-14B-MLX-4bit (本地) / OpenAI API (备选)
API层: FastAPI
前端层: Vue 3 + TypeScript
```

---

## 二、实施路线图

```
Week 1        Week 2        Week 3        Week 4        Week 5        Week 6
|-------------|-------------|-------------|-------------|-------------|
[数据准备Phase1] [数据准备Phase2] [索引+检索]   [LLM集成]     [API+前端]    [测试优化]
├── 个股案例    ├── 择时信号    ├── 模型实现   ├── Qwen3集成  ├── API开发   ├── 单元测试
├── 组合规则    ├── 行为案例    ├── 索引构建   ├── 回答模板   ├── 前端组件  ├── 集成测试
├── 基础常识    ├── 论文解析    ├── 检索服务   ├── 引用溯源   ├── 联调      ├── 评估优化
└── 数据入库    └── 数据入库    └── 单元测试   └── Prompt调优 └── 文档      └── 上线准备
```

---

## 三、Week 1: 核心知识库数据准备（Phase 1）

### 3.1 任务清单

| 任务 | 负责人 | 工时 | 产出 |
|------|--------|------|------|
| 3.1.1 设计数据库模型 | AI | 4h | 6张表的SQLAlchemy模型 |
| 3.1.2 编写20个股分析案例 | AI+人工审核 | 8h | 20个结构化案例文档 |
| 3.1.3 编写16种资产配置规则 | AI+人工审核 | 6h | 16个组合配置方案 |
| 3.1.4 编写50个基础金融常识 | AI | 6h | 50个概念解释文档 |
| 3.1.5 数据入库脚本 | AI | 4h | Python入库脚本 |
| 3.1.6 数据质量检查 | 人工 | 2h | 检查报告 |

### 3.2 详细任务: 3.1.1 数据库模型设计

**文件**: `backend/app/models/rag_knowledge.py`

```python
# 需要创建的6张表
1. paper_chunks      # 论文片段
2. stock_analysis_cases   # 个股分析案例
3. allocation_rules       # 资产配置规则
4. timing_signal_cases    # 择时信号案例
5. behavioral_cases       # 行为金融案例
6. finance_basics         # 基础金融常识
```

**字段设计要点**:
- 每张表必须有 `content` 字段（用于Embedding的完整文本）
- 每张表必须有 `embedding_id` 字段（关联FAISS索引）
- 使用JSON字段存储结构化数据（避免过多列）

### 3.3 详细任务: 3.1.2 个股分析案例（20个）

**选股标准**:
- 覆盖5大行业：消费(4) + 科技(4) + 新能源(4) + 医药(4) + 金融(4)
- 包含龙头白马 + 成长黑马 + 周期股 + 价值股
- 每个案例必须有明确的投资逻辑和估值判断

**案例列表**:

| 行业 | 股票 | 类型 | 案例ID |
|------|------|------|--------|
| 消费 | 贵州茅台 | 龙头白马 | stock_600519 |
| 消费 | 五粮液 | 龙头白马 | stock_000858 |
| 消费 | 海天味业 | 稳健成长 | stock_603288 |
| 消费 | 中国中免 | 消费复苏 | stock_601888 |
| 科技 | 宁德时代 | 新能源龙头 | stock_300750 |
| 科技 | 比亚迪 | 整车龙头 | stock_002594 |
| 科技 | 中芯国际 | 半导体龙头 | stock_688981 |
| 科技 | 立讯精密 | 消费电子 | stock_002475 |
| 新能源 | 隆基绿能 | 光伏龙头 | stock_601012 |
| 新能源 | 通威股份 | 硅料龙头 | stock_600438 |
| 新能源 | 阳光电源 | 逆变器龙头 | stock_300274 |
| 新能源 | 亿纬锂能 | 电池二线 | stock_300014 |
| 医药 | 恒瑞医药 | 创新药龙头 | stock_600276 |
| 医药 | 迈瑞医疗 | 医疗器械 | stock_300760 |
| 医药 | 药明康德 | CXO龙头 | stock_603259 |
| 医药 | 爱尔眼科 | 医疗服务 | stock_300015 |
| 金融 | 招商银行 | 零售银行 | stock_600036 |
| 金融 | 中国平安 | 保险龙头 | stock_601318 |
| 金融 | 东方财富 | 互联网券商 | stock_300059 |
| 金融 | 中信证券 | 传统券商 | stock_600030 |

**每个案例的标准结构**:
```yaml
stock_300750:  # 宁德时代
  symbol: "300750"
  name: "宁德时代"
  analysis_date: "2024-06-01"
  
  investment_logic:
    industry_position: "全球动力电池市占率37%，连续6年第一"
    growth_driver: "海外建厂加速，欧洲市场份额提升"
    financial_health: "ROE 18%，毛利率22%，现金流充裕"
    risk_factors: "原材料价格波动、地缘政治风险"
  
  key_metrics:
    revenue_growth: "+35% YoY"
    profit_growth: "+42% YoY"
    gross_margin: "22.3%"
    net_margin: "11.5%"
    debt_ratio: "58%"
  
  valuation:
    pe_ttm: 25
    pe_history_mean: 30
    pe_percentile: "30%"
    dcf_fair_value: 220
    current_price: 180
    upside: "22%"
  
  catalysts:
    - "2024Q2新产能投产"
    - "特斯拉新订单落地"
    - "固态电池技术突破预期"
  
  recommendation:
    action: "买入"
    target_price: 220
    stop_loss: 150
    position_size: "10%-15%"
    time_horizon: "6-12个月"
  
  content: "完整文本（用于Embedding）"
```

### 3.4 详细任务: 3.1.3 资产配置规则（16种）

**组合矩阵**:

| 画像＼周期 | 复苏期 | 过热期 | 滞胀期 | 衰退期 |
|-----------|--------|--------|--------|--------|
| **保守型** | alloc_con_exp | alloc_con_peak | alloc_con_stag | alloc_con_cont |
| **稳健型** | alloc_mod_exp | alloc_mod_peak | alloc_mod_stag | alloc_mod_cont |
| **积极型** | alloc_agg_exp | alloc_agg_peak | alloc_agg_stag | alloc_agg_cont |
| **激进型** | alloc_vag_exp | alloc_vag_peak | alloc_vag_stag | alloc_vag_cont |

**每个组合的标准结构**:
```yaml
alloc_mod_exp:  # 稳健型-复苏期
  risk_profile: "稳健型"
  market_cycle: "复苏期"
  
  allocation:
    stock: 45%
    bond: 35%
    commodity: 10%
    cash: 10%
  
  stock_detail:
    - name: "沪深300ETF"
      weight: "20%"
      reason: "核心资产配置"
    - name: "中证500ETF"
      weight: "15%"
      reason: "中小盘成长"
    - name: "创业板ETF"
      weight: "10%"
      reason: "高弹性"
  
  bond_detail:
    - name: "国债ETF"
      weight: "20%"
      reason: "安全垫"
    - name: "高等级信用债"
      weight: "15%"
      reason: "收益增强"
  
  rationale: "复苏期股票性价比最高，稳健型保持45%权益..."
  
  backtest:
    annual_return: "10.5%"
    max_drawdown: "12%"
    sharpe_ratio: "0.85"
    win_rate: "75%"
  
  rebalance_triggers:
    - "周期切换"
    - "偏离度>5%"
    - "寿命到期"
  
  content: "完整文本（用于Embedding）"
```

### 3.5 详细任务: 3.1.4 基础金融常识（50个）

**分类结构**:

```
基础金融常识（50个）
├── 投资工具（15个）
│   ├── 股票：A股/港股/美股、主板/创业板/科创板
│   ├── 基金：ETF/LOF/场外基金、主动/被动
│   ├── 债券：国债/企业债/可转债
│   ├── 商品：黄金/原油/大宗商品
│   └── 衍生品：期权/期货/融资融券
│
├── 交易规则（10个）
│   ├── T+1制度、涨跌停板、集合竞价
│   ├── 分红除权、配股增发、停牌复牌
│   └── 交易费用：佣金/印花税/过户费
│
├── 估值指标（10个）
│   ├── PE/PB/PS/PEG
│   ├── ROE/ROA/毛利率/净利率
│   └── 自由现金流/DCF估值
│
├── 风险指标（8个）
│   ├── 夏普比率/索提诺比率
│   ├── 最大回撤/波动率
│   ├── 贝塔系数/阿尔法收益
│   └── 跟踪误差/信息比率
│
└── 市场机制（7个）
    ├── 指数：沪深300/中证500/创业板50
    ├── 行业分类：申万/中信
    └── 融资融券/北向资金/龙虎榜
```

**每个概念的标准结构**:
```yaml
basic_pe_ratio:
  topic: "市盈率 (PE)"
  category: "估值指标"
  difficulty: "入门"
  
  definition: "市盈率 = 股价 / 每股收益(EPS)"
  simple_explanation: "PE就像'回本年限'。PE=20意味着按当前盈利，20年回本。"
  
  usage:
    - method: "横向比较"
      description: "同行业内PE低的可能被低估"
    - method: "纵向比较"
      description: "与自身历史PE比，低于均值可能便宜"
    - method: "绝对判断"
      description: "PE<15通常便宜，PE>30通常贵（非绝对）"
    - method: "结合增长"
      description: "PEG=PE/盈利增速，PEG<1更合理"
  
  cautions:
    - "亏损企业PE为负，无法使用"
    - "周期性行业PE低时可能见顶"
    - "不同行业PE不可比"
  
  example: "2024年1月，贵州茅台PE 28x，处于历史30%分位..."
  
  related_concepts: ["PB", "PEG", "估值", "每股收益"]
  common_questions: ["PE越低越好吗", "为什么银行PE这么低"]
  
  content: "完整文本（用于Embedding）"
```

### 3.6 Week 1 交付检查清单

- [ ] `rag_knowledge.py` 模型文件完成
- [ ] 20个股分析案例YAML文件完成
- [ ] 16种资产配置规则YAML文件完成
- [ ] 50个基础常识YAML文件完成
- [ ] 数据入库脚本运行成功
- [ ] 数据库中可查询到所有数据

---

## 四、Week 2: 扩展知识库数据准备（Phase 2）

### 4.1 任务清单

| 任务 | 工时 | 产出 |
|------|------|------|
| 4.1.1 编写30个择时信号案例 | 8h | 30个结构化信号文档 |
| 4.1.2 编写20个行为金融案例 | 6h | 20个偏差案例文档 |
| 4.1.3 下载+解析20篇论文PDF | 8h | 论文分块数据 |
| 4.1.4 数据入库 | 4h | 所有数据入库完成 |
| 4.1.5 数据质量检查 | 2h | 检查报告 |

### 4.2 详细任务: 4.1.1 择时信号案例（30个）

**信号类型分布**:

```
择时信号案例（30个）
├── 技术分析信号（12个）
│   ├── 均线类：金叉买入(2)、死叉卖出(2)、均线多头排列(1)
│   ├── 突破类：平台突破(2)、趋势线突破(1)、新高买入(1)
│   └── 指标类：MACD底背离(1)、RSI超卖反弹(1)、成交量放量(1)
│
├── 估值信号（6个）
│   ├── 低估买入：PE历史低位(2)、PB破净(1)
│   └── 高估卖出：PE历史高位(2)、PEG>2(1)
│
├── 宏观事件信号（6个）
│   ├── 政策驱动：降准降息(2)、行业政策利好(2)
│   └── 事件驱动：业绩超预期(1)、黑天鹅应对(1)
│
└── 情绪信号（6个）
    ├── 恐慌买入：VIX飙升(2)、融资余额暴跌(1)
    └── 贪婪卖出：新基金天量发行(2)、散户开户数激增(1)
```

**每个信号的标准结构**:
```yaml
timing_ma_golden_cross_202401:
  signal_type: "均线金叉"
  symbol: "沪深300"
  signal_date: "2024-01-15"
  
  market_environment:
    cycle: "复苏期早期"
    sentiment: "极度悲观后开始修复"
    policy: "央行降准释放流动性"
    valuation: "沪深300 PE 10.5x，历史底部"
  
  signal_description:
    - "5日均线上穿20日均线"
    - "成交量放大至20日均量1.5倍"
    - "MACD柱状线由负转正"
    - "RSI(14)从超卖区回升至45"
  
  entry_plan:
    initial_position:
      price: 3300
      size: "30%"
    add_position:
      trigger: "突破3400"
      size: "+20%"
    stop_loss:
      price: 3150
      pct: "-4.5%"
    target:
      price: 3600
      pct: "+9%"
  
  actual_outcome:
    - date: "2024-01-20"
      event: "突破3400，加仓"
    - date: "2024-02-15"
      event: "达到3600，减仓止盈"
    - return: "+8.5%"
    - holding_period: "1个月"
  
  lessons:
    - "✅ 金叉+放量+政策底，多重确认提高胜率"
    - "✅ 分仓建仓降低择时风险"
    - "⚠️ 若未突破3400而是回落，应严格执行止损"
  
  content: "完整文本（用于Embedding）"
```

### 4.3 详细任务: 4.1.2 行为金融案例（20个）

**偏差类型分布**:

```
行为金融案例（20个）
├── 认知偏差（8个）
│   ├── 损失厌恶：套牢不愿卖、过早止盈
│   ├── 锚定效应：成本锚定、历史高点锚定
│   ├── 确认偏误：只看利好、忽视利空
│   ├── 后见之明："我早就知道会跌"
│   └── 过度自信：连赢后加杠杆、频繁交易
│
├── 情绪偏差（6个）
│   ├── 羊群效应：追涨杀跌、跟风买入
│   ├── 恐慌抛售：暴跌时割肉
│   ├── 贪婪追高：牛市末期加杠杆
│   └── 处置效应：赚一点就跑、亏了死扛
│
└── 决策偏差（6个）
    ├── 心理账户：不同账户不同风险态度
    ├── 沉没成本：越亏越补
    ├── 禀赋效应：持仓的股票越看越喜欢
    └── 狭窄框架：只看短期涨跌
```

### 4.4 详细任务: 4.1.3 论文解析（20篇）

**论文列表**:

| 编号 | 论文 | 作者 | 年份 | 核心贡献 | 适用能力 |
|------|------|------|------|---------|---------|
| P001 | Fama-French五因子 | Fama, French | 2015 | 盈利+投资因子 | 选股 |
| P002 | 因子动量 | Ehsani, Linnainmaa | 2022 | 因子层面动量 | 选股 |
| P003 | 质量因子 | Asness | 2019 | 高质量股票跑赢 | 选股 |
| P004 | A股因子动量 | Ma, Liao | 2024 | A股因子动量效应 | 选股 |
| P005 | 机器学习选股 | Gu, Kelly, Xiu | 2020 | 机器学习预测收益 | 选股 |
| P006 | 均值方差优化 | Markowitz | 1952 | 现代组合理论 | 组合 |
| P007 | 风险平价 | Dalio | 1996 | 等风险贡献配置 | 组合 |
| P008 | Black-Litterman | Black, Litterman | 1992 | 贝叶斯资产配置 | 组合 |
| P009 | 动量策略 | Jegadeesh, Titman | 1993 | 个股动量效应 | 择时 |
| P010 | 价值溢价 | Fama, French | 1992 | 价值因子 | 选股 |
| P011 | 低波动异象 | Blitz, van Vliet | 2007 | 低波动高收益 | 选股 |
| P012 | 前景理论 | Kahneman, Tversky | 1979 | 损失厌恶2.5倍 | 行为 |
| P013 | 市场微观结构 | O'Hara | 1995 | 订单流信息 | 择时 |
| P014 | 波动率择时 | Fleming, Kirby, Ostdiek | 2001 | 波动率预测收益 | 择时 |
| P015 | 分析师预期 | Stickel | 1991 | 预期修正策略 | 选股 |
| P016 | 盈利动量 | Chan, Jegadeesh, Lakonishok | 1996 | SUE效应 | 选股 |
| P017 | 资产配置跨期 | Campbell, Viceira | 2002 | 长期投资者配置 | 组合 |
| P018 | 情绪指标 | Baker, Wurgler | 2006 | 投资者情绪指数 | 择时 |
| P019 | 流动性溢价 | Amihud, Mendelson | 1986 | 非流动性补偿 | 选股 |
| P020 | 规模效应 | Banz | 1981 | 小市值溢价 | 选股 |

**PDF处理流程**:
```
1. 从arXiv下载PDF（或找开源版本）
2. 用pdfplumber提取文本
3. 按章节分块：
   - Abstract（摘要）
   - Introduction（引言）
   - Methodology（方法）
   - Results（结果）
   - Conclusion（结论）
4. 每块500-1000字，重叠100字
5. 提取关键句，生成中文摘要
6. 标注适用场景标签
```

### 4.5 Week 2 交付检查清单

- [ ] 30个择时信号案例YAML完成
- [ ] 20个行为金融案例YAML完成
- [ ] 20篇论文PDF下载完成
- [ ] 论文分块数据入库完成
- [ ] 所有扩展数据入库完成

---

## 五、Week 3: 索引构建与检索服务

### 5.1 任务清单

| 任务 | 工时 | 产出 |
|------|------|------|
| 5.1.1 实现数据库模型 | 4h | SQLAlchemy模型文件 |
| 5.1.2 实现索引构建器V2 | 6h | 支持6类知识源的索引构建 |
| 5.1.3 实现查询分类器 | 4h | 意图识别模块 |
| 5.1.4 实现多路检索服务 | 6h | 路由+检索+重排序 |
| 5.1.5 单元测试 | 4h | 测试覆盖率>80% |

### 5.2 详细任务: 5.1.1 数据库模型

**文件**: `backend/app/models/rag_knowledge.py`

```python
# 6张表的完整定义
# 详见设计文档，此处省略
```

**数据库迁移**:
```bash
cd backend
python -c "from app.db.base import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 5.3 详细任务: 5.1.2 索引构建器V2

**文件**: `backend/app/services/rag/index_builder_v2.py`

**功能**:
```python
class IndexBuilderV2:
    def build_all(self, db: Session) -> dict:
        """构建所有索引"""
        return {
            "paper_chunks": self.build_paper_index(db),
            "stock_cases": self.build_stock_index(db),
            "allocation_rules": self.build_allocation_index(db),
            "timing_signals": self.build_timing_index(db),
            "behavioral_cases": self.build_behavioral_index(db),
            "finance_basics": self.build_basic_index(db),
        }
    
    def build_stock_index(self, db: Session) -> dict:
        """构建个股案例索引"""
        cases = db.query(StockAnalysisCase).all()
        # 生成embedding，存入FAISS
        # 元数据：symbol, industry, recommendation
```

**索引命名**:
- `stock_case_index` — 个股案例
- `allocation_rule_index` — 资产配置
- `timing_signal_index` — 择时信号
- `behavioral_case_index` — 行为金融
- `finance_basic_index` — 基础常识
- `paper_chunk_index` — 论文片段

### 5.4 详细任务: 5.1.3 查询分类器

**文件**: `backend/app/services/rag/query_classifier.py`

**分类逻辑**:
```python
class QueryClassifier:
    def classify(self, query: str) -> QueryIntent:
        """基于关键词+Embedding相似度分类"""
        
        # 1. 关键词匹配（快速路径）
        keywords = {
            InvestmentQueryType.STOCK_ANALYSIS: 
                ["怎么样", "分析", "能买吗", "值得投"],
            InvestmentQueryType.PORTFOLIO_BUILD: 
                ["怎么配", "组合", "资产配置", "多少钱买"],
            InvestmentQueryType.BUY_SIGNAL: 
                ["现在买", "买点", "入场", "建仓"],
            InvestmentQueryType.CONCEPT_EXPLAIN: 
                ["什么是", "什么意思", "怎么理解"],
        }
        
        # 2. Embedding相似度（精确路径）
        # 与各类样本查询计算相似度
        
        # 3. 返回最可能的意图+置信度
```

### 5.5 详细任务: 5.1.4 多路检索服务

**文件**: `backend/app/services/rag/retriever_v2.py`

**检索路由**:
```python
class InvestmentRetriever:
    def retrieve(self, query: str, query_type: QueryIntent, 
                 context: dict = None) -> RetrievalResult:
        """
        根据查询类型路由到不同知识源
        """
        routers = {
            InvestmentQueryType.STOCK_ANALYSIS: self._retrieve_stock,
            InvestmentQueryType.PORTFOLIO_BUILD: self._retrieve_portfolio,
            InvestmentQueryType.BUY_SIGNAL: self._retrieve_timing,
            InvestmentQueryType.CONCEPT_EXPLAIN: self._retrieve_basic,
        }
        
        return routers[query_type](query, context)
    
    def _retrieve_stock(self, query, context):
        """选股类检索：个股案例 + 估值常识 + 因子论文"""
        stock_cases = self.stock_index.search(query, top_k=3)
        basics = self.basic_index.search("估值 PE PB", top_k=2)
        papers = self.paper_index.search("factor stock picking", top_k=2)
        return self._merge_and_rerank([stock_cases, basics, papers])
```

### 5.6 Week 3 交付检查清单

- [ ] 6张数据库表创建成功
- [ ] 6个FAISS索引构建完成
- [ ] 查询分类器准确率>80%
- [ ] 多路检索返回结果正确
- [ ] 单元测试全部通过

---

## 六、Week 4: LLM集成与生成优化

### 6.1 任务清单

| 任务 | 工时 | 产出 |
|------|------|------|
| 6.1.1 Qwen3服务集成 | 4h | LLM生成服务 |
| 6.1.2 投资顾问回答模板 | 6h | 5种回答模板 |
| 6.1.3 引用溯源功能 | 4h | 引用标记+来源链接 |
| 6.1.4 Prompt工程优化 | 6h | 高质量Prompt库 |
| 6.1.5 流式生成支持 | 4h | SSE流式输出 |

### 6.2 详细任务: 6.1.2 回答模板

**模板一：个股分析回答**
```markdown
## 📊 {股票名称}（{代码}）分析结论

**{推荐动作}，目标价{目标价}元**
- 当前价：{当前价}元 | 潜在{涨跌}：{幅度}%
- 止损位：{止损价}元（{止损幅度}%）
- 建议仓位：{仓位}

---

## 🔍 分析逻辑

### 1. 基本面
{基本面分析，引用stock_case}

### 2. 估值水平
{估值分析，引用basic_pe}

### 3. 催化剂
{催化剂列表}

---

## ⚠️ 风险提示
{risk_factors}

---

## 📋 操作建议
| 操作 | 价格 | 仓位 | 说明 |
|------|------|------|------|
{operation_table}

{behavioral_reminder}

---

*免责声明：以上分析仅供参考...*
```

**模板二：组合配置回答**
```markdown
## ⚖️ 资产配置方案

**{画像类型} + {市场周期}**

### 配置比例
{allocation_pie_chart}

### 具体标的
{holding_details}

### 配置理由
{rationale，引用allocation_rule}

### 调整规则
{rebalance_triggers}
```

### 6.3 详细任务: 6.1.4 Prompt工程

**系统Prompt（投资顾问角色）**:
```
你是一位资深投资顾问，具备以下特点：
1. 先说结论，再说理由
2. 用数据说话，引用研究报告
3. 风险提示必须明确
4. 操作建议具体可执行
5. 考虑用户的行为偏差，给出针对性提醒

回答格式要求：
- 使用Markdown格式
- 包含📊/🔍/⚠️/📋等emoji标题
- 引用格式：[作者, 年份] 或 [案例ID]
- 必须包含免责声明
```

### 6.4 Week 4 交付检查清单

- [ ] Qwen3生成服务正常运行
- [ ] 5种回答模板完成
- [ ] 引用溯源功能正常
- [ ] Prompt调优后回答质量合格
- [ ] 流式生成支持SSE

---

## 七、Week 5: API开发与前端集成

### 7.1 任务清单

| 任务 | 工时 | 产出 |
|------|------|------|
| 7.1.1 RAG API接口 | 6h | 6个REST端点 |
| 7.1.2 前端RAG组件 | 8h | 3个Vue组件 |
| 7.1.3 前后端联调 | 4h | 端到端测试通过 |
| 7.1.4 文档编写 | 2h | API文档 + 使用说明 |

### 7.2 API接口设计

```yaml
# API端点

POST /api/v1/rag/query
  请求: { query: string, user_id?: int }
  响应: { answer: string, sources: [], model: string }

POST /api/v1/rag/stock-analysis
  请求: { symbol: string, user_id?: int }
  响应: { analysis: object, sources: [] }

POST /api/v1/rag/portfolio-advice
  请求: { profile_id: int, capital?: float }
  响应: { allocation: object, holdings: [], rationale: string }

POST /api/v1/rag/timing-signal
  请求: { symbol: string, strategy?: string }
  响应: { signal: object, confidence: float }

GET /api/v1/rag/knowledge/{entry_id}
  响应: { entry: object, related: [] }

POST /api/v1/rag/build-index
  请求: { force_rebuild?: boolean }
  响应: { status: string, counts: {} }
```

### 7.3 前端组件

```vue
<!-- RAGQueryInput.vue -->
<!-- 投资顾问问答输入框 -->

<!-- StockAnalysisCard.vue -->
<!-- 个股分析结果卡片，含引用展开 -->

<!-- PortfolioAdviceView.vue -->
<!-- 组合建议页面，含配置比例和操作按钮 -->
```

### 7.4 Week 5 交付检查清单

- [ ] 6个API端点全部可用
- [ ] 3个前端组件完成
- [ ] 前后端联调通过
- [ ] API文档完成

---

## 八、Week 6: 测试与优化

### 8.1 任务清单

| 任务 | 工时 | 产出 |
|------|------|------|
| 8.1.1 单元测试 | 4h | 测试覆盖率>85% |
| 8.1.2 集成测试 | 4h | 端到端测试用例 |
| 8.1.3 评估脚本 | 4h | 自动评估RAG质量 |
| 8.1.4 性能优化 | 4h | 检索延迟<500ms |
| 8.1.5 上线准备 | 4h | 部署文档 + 监控 |

### 8.2 评估标准

| 能力 | 测试问题 | 合格标准 |
|------|---------|---------|
| 选股 | "分析宁德时代" | 给出买入/卖出结论+估值+风险 |
| 组合 | "50万稳健型怎么配" | 具体比例+标的+调整规则 |
| 择时 | "现在该买沪深300吗" | 信号判断+建仓方案+止损 |
| 教育 | "什么是夏普比率" | 通俗解释+用法+注意 |
| 综合 | "看看这个组合" | 诊断+调仓建议+解释 |

### 8.3 Week 6 交付检查清单

- [ ] 单元测试覆盖率>85%
- [ ] 集成测试全部通过
- [ ] 评估脚本运行正常
- [ ] 检索延迟<500ms
- [ ] 部署文档完成
- [ ] 生产环境配置完成

---

## 九、风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| Qwen3加载慢/内存不足 | 中 | 高 | 使用4bit量化，必要时换用OpenAI API |
| 论文PDF下载失败 | 中 | 中 | 优先使用arXiv开放获取版本 |
| 数据质量不达标 | 低 | 高 | 每个案例人工审核，建立检查清单 |
| 检索准确率低 | 中 | 高 | 调优Embedding模型，增加重排序 |
| 生成回答质量差 | 中 | 高 | Prompt工程+ few-shot示例优化 |

---

## 十、每日站会模板

```
昨日完成：
- 

今日计划：
- 

阻塞问题：
- 

需要帮助：
- 
```

---

## 附录

### A. 文件清单

```
backend/
├── app/
│   ├── models/
│   │   └── rag_knowledge.py          # 6张表模型
│   ├── services/
│   │   └── rag/
│   │       ├── __init__.py
│   │       ├── embedding_service.py   # Embedding服务
│   │       ├── vector_store.py        # FAISS向量存储
│   │       ├── index_builder_v2.py    # 索引构建器V2
│   │       ├── query_classifier.py    # 查询分类器
│   │       ├── retriever_v2.py        # 检索服务V2
│   │       ├── llm_service.py         # LLM服务
│   │       └── prompt_templates.py    # Prompt模板
│   └── api/v1/endpoints/
│       └── rag.py                     # RAG API端点
├── data/
│   ├── knowledge/                     # 知识库YAML文件
│   │   ├── stock_cases/               # 20个股案例
│   │   ├── allocation_rules/          # 16种组合
│   │   ├── timing_signals/            # 30个择时信号
│   │   ├── behavioral_cases/          # 20个行为案例
│   │   ├── finance_basics/            # 50个基础概念
│   │   └── papers/                    # 20篇论文
│   └── vector_stores/                 # FAISS索引文件
└── tests/
    └── test_rag/                      # RAG测试套件

frontend/
├── src/
│   ├── components/
│   │   ├── RAGQueryInput.vue
│   │   ├── StockAnalysisCard.vue
│   │   └── PortfolioAdviceView.vue
│   └── api/
│       └── rag.ts

docs/
├── rag-investment-expert-plan.md      # 设计方案
└── rag-implementation-plan.md         # 本文件
```

### B. 依赖清单

```
# 新增Python依赖
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4
pdfplumber>=0.10.0
mlx-lm>=0.31.0

# 已有依赖（确认版本兼容）
fastapi==0.115.0
sqlalchemy==2.0.36
pydantic==2.9.2
```

### C. 环境变量

```bash
# LLM配置
LLM_BACKEND=mlx
QWEN_MLX_MODEL_PATH=/path/to/Qwen3-14B-MLX-4bit

# Embedding配置
EMBEDDING_BACKEND=sentence_transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2

# 可选：OpenAI备用
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
```
