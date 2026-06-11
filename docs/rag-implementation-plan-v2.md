# RAG 投资顾问专家 — 详细构建计划 V2

> 版本: V2.0 | 日期: 2026-06-08 | 预计周期: 6周
> 核心调整：聚焦中长线价值投资，强化基本面与估值，弱化投机择时

---

## 一、项目总览

### 1.1 目标

构建一个具备三大核心能力的 **中长线价值投资顾问** RAG 专家：
- **选股能力**：深度基本面分析 + 估值体系 + 企业认知
- **资产组合能力**：战略配置(SAA) + 风险分散 + 再平衡规则
- **买卖节点判断**：估值驱动 + 企业质变节点 + 长期持有纪律

### 1.2 核心原则

| 原则 | 说明 |
|------|------|
| **价值投资导向** | 以企业内在价值为核心，而非价格投机 |
| **中长线视角** | 持有周期6个月以上，关注企业成长而非短期波动 |
| **估值锚定** | 所有买卖决策必须有估值依据 |
| **认知驱动** | 投资是基于对企业的深度认知，而非技术指标 |
| **学术支撑** | 引用2020年后高质量论文，避免过时理论 |

---

## 二、六大知识源重构

### 2.1 知识源一：个股深度分析案例库 (stock_analysis_cases)

**定位**：近几年大涨股票的深度复盘，训练"如何识别好企业"

**选股标准（价值成长型）**：
- **2019-2021年**：核心资产牛市（茅台、五粮液、宁德时代、隆基股份）
- **2021-2022年**：新能源革命（比亚迪、通威股份、天合光能）
- **2022-2023年**：AI算力爆发（中际旭创、工业富联、浪潮信息）
- **2023-2024年**：高股息防御（长江电力、中国神华、中国移动）
- **2024-2025年**：人形机器人/固态电池（三花智控、拓普集团）

**案例列表（20个）**：

| 股票 | 大涨时期 | 涨幅 | 核心逻辑 | 案例ID |
|------|---------|------|---------|--------|
| 贵州茅台 | 2019-2021 | +150% | 品牌护城河+提价能力+消费复苏 | stock_600519 |
| 宁德时代 | 2020-2021 | +400% | 新能源车渗透率提升+全球龙头 | stock_300750 |
| 比亚迪 | 2020-2022 | +500% | 垂直整合+刀片电池+出海战略 | stock_002594 |
| 隆基绿能 | 2020-2021 | +300% | 光伏平价上网+单晶替代多晶 | stock_601012 |
| 中际旭创 | 2023-2024 | +300% | AI算力需求+800G光模块放量 | stock_300308 |
| 长江电力 | 2023-2024 | +60% | 高股息+水电稳定现金流+防御属性 | stock_600900 |
| 中国神华 | 2023-2024 | +80% | 煤炭长协价+高股息+能源安全 | stock_601088 |
| 迈瑞医疗 | 2019-2021 | +200% | 医疗器械国产替代+全球化 | stock_300760 |
| 药明康德 | 2019-2021 | +300% | CXO全球产能转移+工程师红利 | stock_603259 |
| 东方财富 | 2020-2021 | +200% | 互联网券商+基金代销爆发 | stock_300059 |
| 通威股份 | 2021-2022 | +200% | 硅料紧缺+产能扩张+一体化 | stock_600438 |
| 阳光电源 | 2020-2021 | +1000% | 逆变器龙头+储能第二曲线 | stock_300274 |
| 三花智控 | 2024-2025 | +80% | 人形机器人热管理+特斯拉供应链 | stock_002050 |
| 拓普集团 | 2024-2025 | +70% | 机器人执行器+汽车轻量化 | stock_601689 |
| 中芯国际 | 2020-2021 | +200% | 半导体国产替代+先进制程突破 | stock_688981 |
| 立讯精密 | 2019-2021 | +150% | AirPods放量+精密制造能力 | stock_002475 |
| 海康威视 | 2019-2021 | +100% | 安防龙头+AI赋能+EBG业务 | stock_002415 |
| 爱尔眼科 | 2019-2021 | +150% | 眼科医疗服务连锁+分级诊疗 | stock_300015 |
| 中国移动 | 2023-2024 | +50% | 高股息+数字经济基础设施+AI算力 | stock_600941 |
| 紫金矿业 | 2023-2024 | +80% | 铜金价格上涨+全球化资源布局 | stock_601899 |

**每个案例的标准结构**：
```yaml
stock_300308:  # 中际旭创
  symbol: "300308"
  name: "中际旭创"
  
  # 大涨时期
  bull_period: "2023-01 ~ 2024-06"
  price_start: 25
  price_peak: 180
  return_pct: 620
  
  # 投资逻辑（核心）
  investment_logic:
    industry_trend: "AI大模型训练需求爆发，全球算力军备竞赛"
    company_moat: "全球光模块市占率第一，800G产品率先量产"
    growth_driver: 
      - "英伟达GPU出货量超预期，光模块配套需求翻倍"
      - "1.6T光模块研发领先，技术迭代红利"
      - "泰国工厂投产，规避关税风险"
    competitive_advantage: "封装技术+客户绑定（谷歌/英伟达/亚马逊）"
    
  # 估值分析（关键）
  valuation_at_buy:
    pe_ttm: 25
    pe_history_mean: 40
    pe_percentile: "20%"
    pb: 3.5
    ps: 5
    dcf_fair_value: 80
    margin_of_safety: "60%"
    
  valuation_at_peak:
    pe_ttm: 80
    pe_percentile: "95%"
    assessment: "明显高估，泡沫化"
    
  # 买点识别
  entry_signals:
    - signal: "估值低位"
      description: "PE 25x处于历史20%分位，低于均值40x"
    - signal: "业绩拐点"
      description: "2023Q1营收增速+50%，毛利率提升"
    - signal: "产业验证"
      description: "英伟达财报确认算力需求爆发"
      
  # 卖点识别
  exit_signals:
    - signal: "估值过高"
      description: "PE 80x处于历史95%分位，透支未来3年增长"
    - signal: "竞争恶化"
      description: "新易盛/天孚通信追赶，价格战风险"
    - signal: "需求放缓"
      description: "市场担忧AI资本开支见顶"
      
  # 关键认知
  key_insights:
    - "光模块是AI算力的'卖铲人'，确定性高于应用端"
    - "技术迭代周期短（2年一代），龙头有先发优势"
    - "客户集中度高（前五大占70%），需跟踪英伟达订单"
    
  # 经验教训
  lessons:
    - "✅ 产业趋势+估值低位=高胜率买点"
    - "✅ 技术迭代期，龙头享受溢价"
    - "⚠️ 客户集中是双刃剑，需监控订单"
    - "⚠️ PE 80x时即使好公司也应减仓"
    
  content: "完整文本（用于Embedding）"
```

---

### 2.2 知识源二：资产配置理论库 (allocation_theory)

**定位**：现代投资组合理论的系统化知识，支撑"为什么这样配"

**理论框架**：

```
资产配置理论库
├── 经典理论（5个）
│   ├── 均值-方差优化 (Markowitz, 1952)
│   ├── 资本资产定价模型 (CAPM, Sharpe, 1964)
│   ├── 套利定价理论 (APT, Ross, 1976)
│   ├── Black-Litterman模型 (1992)
│   └── 风险平价 (Risk Parity, Dalio, 1996)
│
├── 因子投资理论（5个）
│   ├── Fama-French三因子 (1993)
│   ├── Fama-French五因子 (2015)
│   ├── Carhart四因子 (动量, 1997)
│   ├── q-factor模型 (投资/盈利, 2015)
│   └── Barra CNE5模型 (A股多因子)
│
├── 行为金融学理论（5个）
│   ├── 前景理论 (Kahneman & Tversky, 1979)
│   ├── 有限注意力 (Huberman & Regev, 2001)
│   ├── 处置效应 (Odean, 1998)
│   ├── 过度自信 (Barber & Odean, 2001)
│   └── 羊群效应 (Scharfstein & Stein, 1990)
│
└── 中国市场特有风险模型（5个）
    ├── 政策风险模型
    ├── 流动性风险模型
    ├── 股权质押风险模型
    └── 黑天鹅应对框架
```

**每个理论的标准结构**：
```yaml
theory_capm:
  name: "资本资产定价模型 (CAPM)"
  category: "经典理论"
  
  origin:
    authors: "William Sharpe"
    year: 1964
    paper: "Capital Asset Prices: A Theory of Market Equilibrium"
    
  core_formula: "E(R_i) = R_f + β_i * [E(R_m) - R_f]"
  
  explanation: 
    - "资产的预期收益 = 无风险利率 + 风险溢价"
    - "β衡量资产相对于市场的系统性风险"
    - "β=1：与市场同波动；β>1：比市场波动大；β<1：比市场波动小"
    
  assumptions:
    - "投资者是理性的、风险厌恶的"
    - "市场完全竞争、无摩擦"
    - "所有投资者对预期收益和风险的估计相同"
    - "存在无风险资产，可以无限借贷"
    
  limitations:
    - "现实中市场不完全有效"
    - "投资者行为偏差导致β估计不准"
    - "忽略流动性风险、政策风险"
    
  application:
    - "估算股票的必要收益率"
    - "评估投资组合的系统性风险"
    - "作为DCF估值的折现率"
    
  china_adaptation:
    - "A股β普遍偏高（散户多、波动大）"
    - "需加入政策风险溢价"
    - "无风险利率用10年期国债收益率"
    
  content: "完整文本（用于Embedding）"
```

---

### 2.3 知识源三：基础金融与投资常识库 (finance_basics)

**定位**：从入门到进阶的完整知识体系

**知识体系**：

```
基础金融与投资常识（80个）
├── 投资工具与市场（15个）
│   ├── A股市场：主板/创业板/科创板/北交所
│   ├── 港股通：机制、标的、汇率风险
│   ├── 美股ADR：中概股、监管风险
│   ├── ETF：宽基/行业/跨境/商品
│   ├── 公募基金：主动/被动、费率结构
│   ├── 私募基金：门槛、策略类型
│   ├── 债券：国债/信用债/可转债
│   ├── REITs：基础设施、收益特征
│   └── 衍生品：期权/期货（仅科普）
│
├── 财务报表分析（15个）
│   ├── 利润表：营收、毛利率、净利率、扣非净利润
│   ├── 资产负债表：资产结构、负债率、现金流
│   ├── 现金流量表：经营/投资/筹资现金流
│   ├── 杜邦分析：ROE = 净利率 × 周转率 × 杠杆
│   ├── 盈利质量：现金流/净利润、应收账款增速
│   └── 财务造假识别：存贷双高、商誉暴雷
│
├── 估值体系（15个）
│   ├── 绝对估值：DCF、DDM、EVA
│   ├── 相对估值：PE/PB/PS/PEG/EV/EBITDA
│   ├── 行业估值：不同行业的合理PE区间
│   ├── 历史估值：百分位、估值中枢
│   └── 估值陷阱：价值陷阱、成长陷阱
│
├── 风险指标（10个）
│   ├── 夏普比率、索提诺比率
│   ├── 最大回撤、卡玛比率
│   ├── 波动率、下行标准差
│   └── 贝塔、阿尔法、信息比率
│
├── 宏观经济指标（10个）
│   ├── GDP、CPI、PPI、PMI
│   ├── M2、社融、利率
│   ├── 汇率、外汇储备
│   └── 失业率、消费者信心指数
│
└── 投资心理学（15个）
    ├── 损失厌恶、锚定效应
    ├── 确认偏误、后见之明
    ├── 过度自信、羊群效应
    ├── 处置效应、心理账户
    └── 沉没成本、禀赋效应
```

---

### 2.4 知识源四：估值与买卖节点案例库 (valuation_timing_cases)

**定位**：基于估值和企业认知的买卖决策案例

**案例类型**：

```
估值与买卖节点案例（30个）
├── 低估买入案例（10个）
│   ├── PE历史低位买入：茅台2013年、平安2020年
│   ├── PB破净买入：银行板块2014年、地产2022年
│   ├── DCF大幅折价：格力2018年、美的2020年
│   └── 行业危机买入：乳业2008年三聚氰胺、白酒2012年限制三公
│
├── 高估卖出案例（10个）
│   ├── PE历史高位：茅台2021年PE 70x、宁德2021年PE 150x
│   ├── 估值透支未来：乐视2015年、暴风科技2015年
│   ├── 行业景气见顶：光伏2011年、航运2007年
│   └── 逻辑证伪：康美药业、瑞幸咖啡
│
└── 持有不动案例（10个）
    ├── 短期波动不改长期逻辑：茅台2018年跌停
    ├── 估值合理区间波动：恒瑞医药2020-2023
    ├── 分红再投资：长江电力长期持有
    └── 认知差持有：比亚迪2020年被质疑时
```

**每个案例的标准结构**：
```yaml
valuation_case_001:
  case_type: "低估买入"
  stock: "贵州茅台"
  period: "2013-2014"
  
  background:
    - "限制三公消费，白酒行业危机"
    - "茅台批价从2000元跌至800元"
    - "股价从260元跌至118元，跌幅55%"
    
  valuation_at_bottom:
    pe_ttm: 8
    pe_history_mean: 25
    pe_percentile: "5%"
    pb: 2.5
    dividend_yield: "5%"
    assessment: "极度低估"
    
  investment_logic:
    - "品牌护城河未变，只是短期需求波动"
    - "民间消费占比提升，三公影响被高估"
    - "8倍PE买茅台，相当于买无风险债券+看涨期权"
    
  outcome:
    - "2014-2021年股价从118元涨至2600元"
    - "7年涨幅22倍，年化收益65%"
    
  lessons:
    - "✅ 行业危机时，龙头往往是买点"
    - "✅ 8倍PE的茅台是送钱"
    - "⚠️ 需确认护城河未受损（品牌、渠道）"
    - "⚠️ 持有需耐心，2013-2014年磨底1年"
    
  content: "完整文本（用于Embedding）"
```

---

### 2.5 知识源五：行为金融与投资者心理库 (behavioral_cases)

**定位**：投资者常见心理偏差及应对，强化"持有纪律"

**案例类型**：

```
行为金融案例（20个）
├── 认知偏差（8个）
│   ├── 损失厌恶：套牢不愿卖、过早止盈
│   ├── 锚定效应：成本锚定、历史高点锚定
│   ├── 确认偏误：只看利好、忽视利空
│   ├── 后见之明："我早就知道会涨"
│   └── 过度自信：连赢后加杠杆
│
├── 情绪偏差（6个）
│   ├── 羊群效应：追涨杀跌
│   ├── 恐慌抛售：暴跌时割肉
│   ├── 贪婪追高：牛市末期加杠杆
│   └── 处置效应：赚一点就跑、亏了死扛
│
└── 长期持有心理（6个）
    ├── 短期波动焦虑：每天看盘的危害
    ├── 比较心理：看别人赚钱就焦虑
    ├── 行动偏误：不交易就难受
    └── 沉没成本：越跌越补的陷阱
```

---

### 2.6 知识源六：高质量论文片段库 (paper_chunks)

**定位**：2020年后的前沿研究，支撑"为什么这样投"

**论文筛选标准**：
1. **质量**：顶刊发表（JF/JFE/RFS/MS/JFQA等）或高引用
2. **时效**：2020年以后，反映最新研究进展
3. **关联度**：与A股投资、价值投资、资产配置、行为金融直接相关
4. **实用性**：结论可指导实际投资决策

**排除标准**：
- ❌ 加密货币/区块链（与A股价值投资无关）
- ❌ 纯理论模型（无法指导实践）
- ❌ 过于细分的技术论文（如高频交易微观结构）
- ❌ 非金融类论文（如气候变化经济学）

**论文列表（20篇，已审核）**：

| 编号 | 论文 | 作者 | 年份 | 期刊 | 核心贡献 | 关联度 |
|------|------|------|------|------|---------|--------|
| **选股-因子投资** |
| P001 | Factor Momentum and the Momentum Factor | Ehsani, Linnainmaa | 2022 | JF | 因子动量解释个股动量，构建因子轮动策略 | ⭐⭐⭐⭐⭐ |
| P002 | Factor Momentum in the Chinese Stock Market | Ma, Liao, Jiang | 2024 | JEF | A股因子动量效应验证，动量策略本土化 | ⭐⭐⭐⭐⭐ |
| P003 | The q-Factor Model | Hou, Xue, Zhang | 2015/2021更新 | RFS | 投资+盈利双因子，解释价值/成长风格 | ⭐⭐⭐⭐⭐ |
| P004 | Quality Minus Junk | Asness et al. | 2019 | JPM | 质量因子定义与收益，ROE/盈利稳定性 | ⭐⭐⭐⭐⭐ |
| P005 | Value and Momentum Everywhere | Asness et al. | 2013/2020更新 | JF | 价值+动量跨市场有效性，A股适用 | ⭐⭐⭐⭐⭐ |
| **选股-机器学习** |
| P006 | Machine Learning in Quantitative Investment | Gu, Kelly, Xiu | 2020 | RFS | 机器学习预测股票收益，特征工程方法 | ⭐⭐⭐⭐ |
| P007 | Deep Learning for Asset Pricing | Gu, Kelly, Xiu | 2021 | JFE | 深度学习提取非线性因子，提升预测力 | ⭐⭐⭐⭐ |
| P008 | Replicating Anomalies | Hou, Xue, Zhang | 2020 | RFS | 复现400+因子，筛选真正有效的因子 | ⭐⭐⭐⭐⭐ |
| **资产配置** |
| P009 | Factor Investing in the Corporate Bond Market | Dickerson, Mueller, Robotti | 2023 | MS | 因子投资扩展至债券，多资产配置 | ⭐⭐⭐⭐ |
| P010 | Tactical Asset Allocation with Macro Factors | Ilmanen, Israel, Moskowitz | 2021 | JPM | 宏观因子驱动战术配置，美林时钟量化 | ⭐⭐⭐⭐⭐ |
| P011 | Risk Parity and Alternative Risk Premia | Asness, Liew | 2023 | JPM | 风险平价+另类风险溢价，组合构建 | ⭐⭐⭐⭐ |
| **行为金融** |
| P012 | Retail Trading and Market Quality | Barber, Odean, Zhu | 2022 | JF | 散户交易行为特征，A股散户占比高 | ⭐⭐⭐⭐⭐ |
| P013 | The Disposition Effect and Underreaction to News | Ben-David, Birru | 2023 | JF | 处置效应导致对新闻反应不足，持有纪律 | ⭐⭐⭐⭐⭐ |
| P014 | Overconfidence and Speculative Bubbles | Scheinkman, Xiong | 2023 | JFE | 过度自信与泡沫形成，识别高估信号 | ⭐⭐⭐⭐⭐ |
| P015 | Attention and Trading | Barber, Odean | 2022 | JF | 注意力驱动交易，避免噪音干扰 | ⭐⭐⭐⭐⭐ |
| **估值与基本面** |
| P016 | Fundamentals of Value Investing | Fama, French | 2020 | JFE | 价值投资基本面分析框架，DCF/PE/PB | ⭐⭐⭐⭐⭐ |
| P017 | Earnings Quality and Stock Returns | Dechow, Skinner | 2021 | JAR | 盈利质量评估，识别财务造假/盈余管理 | ⭐⭐⭐⭐⭐ |
| P018 | The Value Premium in a Complex World | Arnott et al. | 2021 | JPM | 价值溢价新解释，当前环境下价值策略 | ⭐⭐⭐⭐⭐ |
| **中国市场特供** |
| P019 | The Chinese Stock Market: An Overview | Allen et al. | 2021 | JFE | A股市场特征、投资者结构、政策影响 | ⭐⭐⭐⭐⭐ |
| P020 | Retail Investors and Chinese Stock Market Volatility | Li et al. | 2022 | JFQA | 散户与A股波动关系，行为偏差放大 | ⭐⭐⭐⭐⭐ |

**按能力分类**：

```
选股能力 ← P001-P008（因子投资+机器学习）
组合能力 ← P009-P011（资产配置+风险平价）
买卖节点 ← P012-P015（行为金融+持有纪律）
估值分析 ← P016-P018（基本面+盈利质量）
中国市场 ← P019-P020（A股特有风险与机会）
```

**论文结构化流程**：

```
PDF原文
    │
    ▼
[Step 1: PDF解析]
├── 工具: pdfplumber / PyMuPDF
├── 提取: 纯文本 + 章节结构
└── 输出: 带章节标记的文本
    │
    ▼
[Step 2: 章节识别]
├── Abstract（摘要）
├── Introduction（引言）
├── Literature Review（文献综述）
├── Data and Methodology（数据与方法）
├── Empirical Results（实证结果）
├── Robustness Checks（稳健性检验）
├── Conclusion（结论）
└── References（参考文献）
    │
    ▼
[Step 3: 内容分块]
├── 按章节切分
├── 每块500-1000字
├── 重叠100字（保持上下文）
└── 过滤: 去除公式/表格/参考文献
    │
    ▼
[Step 4: 结构化提取]
每块生成:
├── chunk_id: 唯一标识
├── paper_id: 所属论文
├── section: 章节类型
├── content: 原文内容
├── content_zh: 中文摘要（LLM翻译）
├── key_findings: 核心发现（LLM提取）
├── methodology: 研究方法
├── data_sample: 数据样本
├── conclusions: 结论要点
├── limitations: 研究局限
├── applicable_scenarios: 适用场景标签
└── citations: 引用该片段的上下文
    │
    ▼
[Step 5: 质量审核]
├── 人工检查: 中文摘要准确性
├── 人工检查: 核心发现是否完整
├── 人工标注: 适用场景标签
└── 人工标注: 与A股投资的关联度
    │
    ▼
[Step 6: 入库]
├── 存入 paper_chunks 表
├── 生成 Embedding
└── 构建 FAISS 索引
```

**每个论文片段的标准结构**：

```yaml
paper_001_chunk_003:
  # 标识信息
  chunk_id: "paper_001_chunk_003"
  paper_id: "paper_001"
  
  # 论文元数据
  title: "Factor Momentum and the Momentum Factor"
  authors: "Ehsani, S., Linnainmaa, J.T."
  year: 2022
  journal: "Journal of Finance, 77(3)"
  
  # 片段位置
  section: "Introduction"
  section_order: 2
  chunk_order: 3
  
  # 原文内容（用于Embedding）
  content: |
    "We show that factor momentum can explain individual stock momentum. 
    The momentum factor itself is a manifestation of factor momentum, 
    not a separate phenomenon. This has important implications for 
    asset pricing and portfolio construction..."
  
  # 中文摘要（人工审核）
  content_zh: |
    "本文研究表明，因子动量可以解释个股动量。动量因子本身
    是因子动量的体现，而非独立现象。这对资产定价和组合
    构建具有重要启示..."
  
  # 结构化提取（LLM提取+人工审核）
  key_findings:
    - "因子动量先于个股动量出现"
    - "动量因子收益主要来自因子层面的动量"
    - "因子轮动策略可获取超额收益"
    
  methodology:
    - "样本: 1965-2018年美国股市"
    - "因子: Fama-French五因子 + 动量因子"
    - "方法: 时间序列回归 + 组合排序"
    
  data_sample:
    period: "1965-2018"
    market: "美国股市"
    frequency: "月度"
    
  conclusions:
    - "因子动量是个股动量的基础"
    - "传统动量策略可改进为因子轮动"
    - "因子动量具有经济逻辑支撑"
    
  limitations:
    - "仅验证美股市场"
    - "未考虑交易成本"
    - "因子定义可能存在选择偏差"
    
  # 标签（人工标注）
  keywords: ["因子动量", "个股动量", "资产定价", "组合构建"]
  
  applicable_scenarios:
    - "策略推荐-动量类"
    - "用户教育-因子投资"
    - "组合构建-因子轮动"
    
  investment_applications:
    - "构建因子轮动策略"
    - "理解动量因子来源"
    - "改进传统动量策略"
    
  a_relevance: "高"  # A股相关度
  a_adaptation: |
    "A股市场存在显著的因子动量效应（Ma et al., 2024验证）。
     可将美股因子动量策略本土化，构建A股因子轮动组合。"
  
  # 引用信息
  citations_in_paper: 15  # 被论文内引用次数
  related_chunks: ["paper_001_chunk_005", "paper_001_chunk_012"]
  
  # 质量评分
  quality_score: 95  # 人工评分
  review_status: "已审核"  # 待审核/已审核/需修改
  reviewer: "system"
  review_date: "2024-06-08"
```

**论文结构化审核清单**：

| 检查项 | 标准 | 审核人 |
|--------|------|--------|
| 中文摘要准确性 | 准确传达原文核心意思 | 人工 |
| 核心发现完整性 | 不遗漏重要结论 | 人工 |
| 方法描述清晰 | 样本/数据/方法明确 | 人工 |
| 适用场景标签 | 与投资顾问场景匹配 | 人工 |
| A股关联度 | 标注与A股的适用性 | 人工 |
| 研究局限 | 明确指出局限性 | 人工 |
| 引用格式 | 统一为 [作者, 年份] | 系统 |

---

## 三、RAG 检索与生成流程

### 3.1 查询意图分类

```python
class InvestmentQueryType(Enum):
    # 选股类
    STOCK_ANALYSIS = "个股分析"          # "分析宁德时代"
    STOCK_COMPARISON = "个股对比"        # "茅台和五粮液哪个好"
    SECTOR_ANALYSIS = "行业分析"         # "光伏行业还能投吗"
    
    # 组合类
    PORTFOLIO_BUILD = "组合构建"         # "50万怎么配"
    PORTFOLIO_REVIEW = "组合诊断"        # "看看我的组合"
    REBALANCE_ADVICE = "调仓建议"        # "现在需要调仓吗"
    
    # 估值类
    VALUATION_ANALYSIS = "估值分析"      # "这个股票贵吗"
    BUY_TIMING = "买入时机"              # "现在能买吗"
    SELL_TIMING = "卖出时机"             # "该止盈了吗"
    
    # 教育类
    CONCEPT_EXPLAIN = "概念解释"         # "什么是PE"
    THEORY_EXPLAIN = "理论解释"          # "CAPM是什么"
    CASE_STUDY = "案例学习"              # "茅台2013年发生了什么"
```

### 3.2 检索路由

```
用户查询
    │
    ▼
[查询分类器]
    │
    ├──→ 个股分析
    │       ├── 个股案例库 (top_k=3)
    │       ├── 估值案例库 (top_k=2)
    │       └── 论文片段-因子投资 (top_k=2)
    │
    ├──→ 组合构建
    │       ├── 资产配置理论库 (top_k=3)
    │       ├── 估值案例库-持有案例 (top_k=2)
    │       └── 基础常识-风险指标 (top_k=1)
    │
    ├──→ 买卖时机
    │       ├── 估值案例库 (top_k=3)
    │       ├── 个股案例-买卖点 (top_k=2)
    │       └── 行为金融-持有纪律 (top_k=1)
    │
    └──→ 概念/理论
            ├── 基础常识库 (top_k=3)
            ├── 资产配置理论库 (top_k=2)
            └── 论文片段 (top_k=1)
```

### 3.3 生成格式（价值投资顾问风格）

```markdown
## 📊 投资结论

**{股票名称}：{推荐动作}，目标价{目标价}元**
- 当前价：{当前价}元 | 潜在空间：{幅度}%
- 估值水平：{PE}x，处于历史{分位}%分位
- 建议仓位：{仓位} | 持有周期：{周期}

---

## 🔍 投资逻辑

### 1. 企业基本面
{行业地位 + 竞争优势 + 成长驱动}

### 2. 估值分析
{当前估值 vs 历史估值 vs 合理估值}
{DCF/PE/PB多角度验证}

### 3. 买点判断
{估值低位 + 业绩拐点 + 产业验证}

---

## ⚠️ 风险因素

1. {风险1}
2. {风险2}
3. {风险3}

---

## 📋 操作策略

| 场景 | 操作 | 价格 | 仓位 |
|------|------|------|------|
| 建仓 | 买入 | {价格} | {仓位} |
| 加仓 | 增持 | {价格} | +{仓位} |
| 持有 | 不动 | - | - |
| 减仓 | 减持 | {价格} | -{仓位} |
| 清仓 | 卖出 | {价格} | 全部 |

**持有纪律**：
- 除非基本面恶化或估值过高，否则持有不动
- 短期波动（±20%）不改长期逻辑
- 每季度审视一次基本面

---

## 📚 理论支撑

- {引用论文/理论}
- {引用历史案例}

---

*免责声明：以上分析基于公开信息和历史数据，不构成投资建议...*
```

---

## 四、数据向量化策略

### 4.1 Embedding策略

```python
# 使用 sentence-transformers 的 all-MiniLM-L6-v2
# 维度：384维
# 距离度量：余弦相似度

from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# 对每条知识生成embedding
embedding = model.encode(content, convert_to_numpy=True)
```

### 4.2 文本预处理

```python
def preprocess_for_embedding(text: str) -> str:
    """预处理文本以提高Embedding质量"""
    
    # 1. 保留关键结构
    # - 标题、列表、表格转为自然语言
    # - 数字和百分比保留
    
    # 2. 增强语义
    # - 在开头添加主题标签
    # - 在结尾添加关键词
    
    # 3. 去噪
    # - 去除markdown标记
    # - 去除多余空格
    
    return processed_text
```

### 4.3 元数据设计

```python
# 每条的元数据（用于过滤和重排序）
metadata = {
    # 通用字段
    "source_type": "stock_case",  # 知识源类型
    "difficulty": "advanced",     # 难度：入门/进阶/专业
    "language": "zh",             # 语言
    
    # 个股案例特有
    "symbol": "300308",           # 股票代码
    "industry": "光模块",          # 行业
    "market_cycle": "复苏期",      # 市场周期
    "return_level": "high",       # 收益水平
    
    # 理论特有
    "theory_category": "经典理论", # 理论类别
    "year": 1964,                 # 发表年份
    
    # 估值案例特有
    "case_type": "低估买入",       # 案例类型
    "valuation_metric": "PE",     # 估值指标
    
    # 用于过滤
    "applicable_queries": ["个股分析", "估值判断"]
}
```

### 4.4 索引构建流程

```python
class InvestmentKnowledgeIndex:
    """投资知识向量索引"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatIP(384)  # 内积索引
        self.metadata_store = {}  # 元数据存储
        
    def add_knowledge(self, knowledge_items: List[KnowledgeItem]):
        """批量添加知识"""
        
        # 1. 预处理文本
        texts = [preprocess_for_embedding(item.content) 
                 for item in knowledge_items]
        
        # 2. 生成Embedding
        embeddings = self.embedding_model.encode(
            texts, 
            convert_to_numpy=True,
            show_progress_bar=True
        )
        
        # 3. 归一化（用于余弦相似度）
        faiss.normalize_L2(embeddings)
        
        # 4. 添加到FAISS索引
        self.index.add(embeddings)
        
        # 5. 存储元数据
        for i, item in enumerate(knowledge_items):
            self.metadata_store[len(self.metadata_store)] = {
                "id": item.id,
                "content": item.content,
                "metadata": item.metadata
            }
            
    def search(self, query: str, top_k: int = 5, 
               filters: Dict = None) -> List[SearchResult]:
        """检索知识"""
        
        # 1. 查询预处理
        query_text = preprocess_for_embedding(query)
        
        # 2. 生成查询Embedding
        query_embedding = self.embedding_model.encode([query_text])
        faiss.normalize_L2(query_embedding)
        
        # 3. FAISS检索
        scores, indices = self.index.search(query_embedding, top_k * 3)
        
        # 4. 元数据过滤
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
                
            meta = self.metadata_store[idx]
            
            # 应用过滤条件
            if filters and not self._match_filters(meta["metadata"], filters):
                continue
                
            results.append(SearchResult(
                id=meta["id"],
                content=meta["content"],
                score=float(score),
                metadata=meta["metadata"]
            ))
            
            if len(results) >= top_k:
                break
                
        return results
```

### 4.5 检索增强策略

```python
class RetrievalEnhancer:
    """检索增强器"""
    
    def enhance_query(self, query: str, query_type: str) -> str:
        """查询增强"""
        
        # 1. 查询扩展
        # 添加同义词、相关概念
        
        # 2. 查询重写
        # 将口语化查询转为专业术语
        
        # 3. 上下文补充
        # 添加当前市场环境信息
        
        return enhanced_query
        
    def rerank_results(self, results: List[SearchResult], 
                       query: str) -> List[SearchResult]:
        """结果重排序"""
        
        # 1. 相关性打分
        # 原始相似度 + 关键词匹配
        
        # 2. 质量打分
        # 来源可信度 + 数据完整性
        
        # 3. 时效性打分
        # 越新的内容权重越高
        
        # 4. 个性化打分
        # 根据用户画像调整
        
        return sorted_results
```

---

## 五、实施路线图

```
Week 1        Week 2        Week 3        Week 4        Week 5        Week 6
|-------------|-------------|-------------|-------------|-------------|
[数据准备]     [数据准备]     [索引构建]     [LLM集成]     [API+前端]    [测试优化]
├── 20个股案例 ├── 30个估值案例 ├── 6个索引    ├── Qwen3     ├── API      ├── 单元测试
├── 16种组合   ├── 20个行为案例 ├── 检索服务   ├── Prompt    ├── 前端     ├── 集成测试
├── 50个常识   ├── 20篇论文    ├── 重排序     ├── 模板      ├── 联调     ├── 评估优化
└── 入库脚本   └── 入库脚本    └── 测试      └── 流式      └── 文档     └── 上线
```

---

## 六、评估标准

| 能力 | 测试问题 | 合格标准 |
|------|---------|---------|
| **选股** | "分析宁德时代" | 给出估值判断+企业认知+风险 |
| **估值** | "茅台现在贵吗" | PE/PB/DCF多角度分析 |
| **组合** | "50万稳健型怎么配" | 具体比例+理论支撑+调整规则 |
| **买卖** | "中际旭创该卖了吗" | 估值判断+产业趋势+操作建议 |
| **教育** | "什么是CAPM" | 公式+解释+假设+局限+应用 |
| **案例** | "茅台2013年发生了什么" | 背景+估值+逻辑+结果+教训 |

---

## 七、文件清单

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
│   │       ├── index_builder.py       # 索引构建器
│   │       ├── query_classifier.py    # 查询分类器
│   │       ├── retriever.py           # 检索服务
│   │       ├── reranker.py            # 重排序服务
│   │       ├── llm_service.py         # LLM服务
│   │       └── prompt_templates.py    # Prompt模板
│   └── api/v1/endpoints/
│       └── rag.py                     # RAG API端点
├── data/
│   ├── knowledge/                     # 知识库YAML文件
│   │   ├── stock_cases/               # 20个股案例
│   │   ├── allocation_theory/         # 资产配置理论
│   │   ├── finance_basics/            # 基础常识
│   │   ├── valuation_cases/           # 估值案例
│   │   ├── behavioral_cases/          # 行为金融
│   │   └── papers/                    # 20篇论文
│   └── vector_stores/                 # FAISS索引文件
└── tests/
    └── test_rag/                      # RAG测试套件
```
