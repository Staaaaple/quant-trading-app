# 智投助手 — 项目逻辑链路结构 V2

## 一、顶层架构

```
用户交互层 (Frontend)
    │
    ▼
API Gateway (FastAPI)
    │
    ├──→ 核心服务层 ──→ 数据持久层 (SQLite)
    │
    ├──→ 后台服务层 (APScheduler定时任务)
    │
    └──→ 外部数据源 (akshare + 爬虫)
```

## 二、核心业务链路（5条）

### 链路1: 用户画像链路（首次使用）

```
用户访问首页
    │
    ├──→ [检查画像] ──无──→ 显示空状态引导
    │                        │
    │                        ▼
    │                   [点击"开始画像"]
    │                        │
    │                        ▼
    │                   问卷Wizard（10题）
    │                   ├── 基本信息3题（资金/经验/收入）
    │                   └── 情景心理7题（损失厌恶/从众/过度自信/延迟满足/锚定/安全感/时间感知）
    │                        │
    │                        ▼
    │                   计算profile_vector（10维结构化输出）
    │                   {
    │                     risk_tolerance, loss_aversion, herding_tendency,
    │                     overconfidence, delayed_gratification, security_need,
    │                     time_horizon, experience_level, capital_tier, income_type
    │                   }
    │                        │
    │                        ▼
    │                   保存画像 ──→ 跳转Dashboard
    │
    └──→ [有画像] ──→ 直接展示Dashboard
```

### 链路2: 组合设计与推荐链路（核心）

```
三个输入向量:
├── profile_vector（用户画像）
├── market_state_vector（五层市场信号加权）
│   ├── Layer1宏观(30%): GDP/CPI/PMI/M2/利率/周期判断
│   ├── Layer2地缘政治(20%): 中美关系/台海/俄乌/中东/NLP情绪提取
│   ├── Layer3行业景气(20%): 各行业PMI/利润/政策/产业链
│   ├── Layer4社会实事(15%): AI/老龄化/新能源/消费趋势
│   └── Layer5资产内部(15%): 股债利差/风格轮动/成交量/北向资金/融资余额
└── pool_state_vector（策略池状态）
    └── 各策略健康度/寿命/同质化风险

           │
           ▼
    ┌─────────────────────────────┐
    │   Hybrid Portfolio Designer │
    ├─────────────────────────────┤
    │                             │
    │ Step1: 战略资产配置(SAA)    │
    │   profile.risk × market.macro × market.geo → 资产类别权重
    │   例: 积极+复苏+低风险 → 股票60% 债券25% 商品10% 现金5%
    │                             │
    │ Step2: 战术资产配置(TAA)    │
    │   market.industry × market.social × market.internal → 细分权重
    │   例: 科技景气高+AI趋势强 → 科技ETF占股票50%
    │                             │
    │ Step3: 策略-标的绑定(贝叶斯优化) │
    │   max(策略夏普 × 健康度 × 寿命 × 标的相关性)
    │   约束: 风险等级≤用户承受 / 适合周期∩当前周期 / 寿命≥3月 / 同质化<0.6
    │                             │
    │ Step4: 风控配置自动生成     │
    │   画像.loss_aversion → 自动设置止损线/仓位上限/再平衡触发/最大回撤硬止损
    │                             │
    │ Step5: 可靠性评估           │
    │   - 组合回测(近3年)         │
    │   - 压力测试(2022熊市/2020疫情) │
    │   - 蒙特卡洛模拟(1000次随机路径) │
    │                             │
    │ Step6: 组合寿命计算         │
    │   组合寿命 = min(各组件寿命)
    │   组合健康度 = 加权平均(各组件健康度)
    │                             │
    └───────────┬─────────────────┘
                │
                ▼
    完整组合配置 = {
      assets: [标的+权重+绑定策略],
      risk_config: {止损/仓位/回撤控制},
      backtest_result: {回测+压力测试+蒙特卡洛},
      portfolio_lifespan: 15,
      portfolio_health: 78,
      operation_plan: {分批建仓计划}
    }
```

### 链路3: 策略发现与入池链路（后台异步）

```
定时任务（每周日凌晨2:00）
    │
    ▼
Agent Crawler:
├── 爬取: GitHub Trending / arXiv q-fin.TR / 雪球热门 / 量化社区
├── 筛选: 代码可获取 / 有回测展示 / 近半年更新 / Star>50
├── 安全扫描: 无恶意代码
├── 语法适配: 迁移到akquant框架
├── 回测验证: 10只不同类型股票 × 6个月 × 3段
├── DNA测序: 健康度>60
├── 寿命预测: >6个月
├── 同质化检查: 综合风险<0.7
└── 入池:
    ├── 通过 → strategy_pool (status: active)
    └── 未通过 → 记录原因，供人工review
```

### 链路4: 全链路服务链路（用户操作后）

```
用户应用组合
    │
    ├──→ [教学系统] ──→ 投资策略原理卡片（为什么选这些标的+策略）
    │
    ├──→ [开户引导] ──→ 挑选券商标准说明（费率/APP体验/研报）
    │
    ├──→ [建仓助手] ──→ 分批买入计划+具体操作截图教程
    │
    ├──→ [日常推送] ──→ 有操作时才推送（买入/卖出/持有信号）
    │
    ├──→ [调仓提醒] ──→ 策略到期/周期切换/寿命预警时推送替换方案
    │
    ├──→ [周报月报] ──→ 组合表现+市场回顾+下周展望
    │
    └──→ [教学卡片] ──→ 每次操作附带原理解释
```

### 链路5: 动态寿命监控链路（定时任务）

```
每月1日凌晨3:00
    │
    ├──→ 采集市场环境数据
    │   ├── 波动率20日ATR / 历史波动率百分位
    │   ├── 当前周期阶段
    │   └── 家族拥挤度（近3月超额收益）
    │
    ├──→ 遍历所有活跃策略
    │   ├── 基础寿命（静态）
    │   ├── × 波动率加速因子（高波1.3 / 低波0.85）
    │   ├── × 周期适配因子（匹配1.0 / 相邻0.9 / 不适0.7）
    │   └── × 拥挤度因子（sigmoid映射超额收益）
    │
    ├──→ 计算组合层面寿命
    │   ├── 组合寿命 = min(各组件寿命)
    │   └── 组合健康度 = 加权平均
    │
    ├──→ 寿命变化检测
    │   ├── 减少>20% → 黄色预警
    │   └── 减少>40% 或 <3月 → 红色预警
    │
    ├──→ 写入寿命历史表
    │
    └──→ 推送预警到Dashboard
```

## 三、模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│  前端视图层                                                   │
│  Home/Dashboard/ProfileWizard/MarketSignal/PortfolioBuilder/ │
│  StrategyRecommendation/LifespanCenter/BacktestCenter/...    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  API层 (FastAPI Router)                                      │
│  /users /profiles /market-signals /portfolios /recommendations│
│  /lifespan-monitor /backtests /strategies /paper-trading     │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  业务服务层                                                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 核心链路服务                                             ││
│  │ profile_service ──→ market_signal_service ──→          ││
│  │ hybrid_portfolio_designer ──→ recommendation_engine    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 后台服务                                                 ││
│  │ agent_crawler ──→ strategy_validator ──→ pool_manager  ││
│  │ lifespan_monitor ──→ economic_cycle_updater            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 回测引擎                                                 ││
│  │ akquant(个股/ETF/债券) + fund_backtest_engine(基金)    ││
│  │ walk_forward_validator + monte_carlo_simulator         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 生态系统（保留升级）                                      ││
│  │ dna_sequencer ──→ phylogeny_service(3D) ──→           ││
│  │ metabolic_profiler ──→ lifespan_service(动态)          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  数据持久层 (SQLite)                                         │
│  User/InvestorProfile/MarketSignal/Portfolio/PortfolioHolding│
│  StrategyPool/BacktestResult/StrategyDNA/StrategyPhylogeny   │
│  LifespanHistory/RecommendationLog/OperationLog              │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  外部数据源                                                  │
│  akshare(宏观/行情/行业) + 爬虫(新闻/地缘政治/社会实事)      │
│  GitHub API + arXiv API                                      │
└─────────────────────────────────────────────────────────────┘
```

## 四、数据模型关系

```
User (1) ────────∞ InvestorProfile (1 active)
    │
    ├────────────∞ Portfolio (多个组合)
    │                │
    │                └────∞ PortfolioHolding (资产配置明细)
    │                         │
    │                         └────→ StrategyPool (策略绑定)
    │
    ├────────────∞ BacktestResult (回测记录)
    │
    ├────────────∞ RecommendationLog (推荐记录)
    │
    └────────────∞ OperationLog (操作日志)

MarketSignal (1 per day)
    │
    └──→ 驱动 Portfolio 的再平衡决策

StrategyPool (策略池)
    │
    ├──→ StrategyDNA (基因测序)
    │
    ├──→ StrategyPhylogeny (三维同质化)
    │
    └──→ LifespanHistory (寿命轨迹)
```

## 五、再平衡触发条件（5种）

```python
REBALANCE_TRIGGERS = {
    "time_based":       "定期再平衡（季度/月度）",
    "deviation_based":  "权重偏离度 > 阈值（保守5%/积极10%）",
    "lifespan_based":   "任一组件寿命 < 3个月",
    "health_based":     "组合健康度下降 > 20%",
    "cycle_based":      "市场周期阶段切换",
}
```
