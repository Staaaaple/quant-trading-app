# 智投助手 — 项目逻辑链路结构

> 本文档描述系统内部的数据流、模块依赖关系和核心业务链路。

---

## 一、顶层架构视图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层 (Frontend)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 首页     │ │ 画像问卷 │ │ 市场信号 │ │ 组合构建 │ │ 策略推荐 │          │
│  │ Dashboard│ │ Wizard   │ │ Signal   │ │ Portfolio│ │ Recommend│          │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       │            │            │            │            │                 │
│  ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐        │
│  │ 回测中心 │ │ 模拟盘   │ │ 寿命监控 │ │ 策略工坊 │ │ 用户设置 │        │
│  │ Backtest │ │ Paper    │ │ Lifespan │ │ Workshop │ │ Settings │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
└───────┼────────────┼────────────┼────────────┼────────────┼──────────────┘
        │            │            │            │            │
        └────────────┴────────────┴────────────┴────────────┘
                                      │
                              ┌───────▼────────┐
                              │   API Gateway  │
                              │  (FastAPI)     │
                              └───────┬────────┘
                                      │
┌─────────────────────────────────────┼─────────────────────────────────────┐
│                           业务服务层 (Backend Services)                     │
│                                                                             │
│  ┌──────────────────────────────────┼──────────────────────────────────┐  │
│  │      核心推荐链路 (实时，<1s)      │                                   │  │
│  │  ┌─────────────┐    ┌───────────┴┐   ┌─────────────┐   ┌─────────┐ │  │
│  │  │User Profile │───→│ Portfolio  │──→│Strategy Rec │──→│Backtest │ │  │
│  │  │  Service    │    │  Builder   │   │   Engine   │   │ Verify  │ │  │
│  │  └─────────────┘    └────────────┘   └─────────────┘   └─────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │      后台生成链路 (异步，3-5min)                                     │  │
│  │  ┌─────────────┐    ┌────────────┐   ┌─────────────┐   ┌─────────┐ │  │
│  │  │  RAG Retriever│──→│ Strategy   │──→│  Bayesian   │──→│  Pool   │ │  │
│  │  │   (知识检索)  │    │  Designer  │   │  Optimizer  │   │  Entry  │ │  │
│  │  └─────────────┘    └────────────┘   └─────────────┘   └─────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │      监控更新链路 (定时任务)                                         │  │
│  │  ┌─────────────┐    ┌────────────┐   ┌─────────────┐   ┌─────────┐ │  │
│  │  │  Macro Data │───→│  Economic  │──→│  Market     │──→│ Lifespan│ │  │
│  │  │   Crawler   │    │   Cycle    │   │  Signal     │   │ Update  │ │  │
│  │  └─────────────┘    └────────────┘   └─────────────┘   └─────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │      回测引擎层                                                      │  │
│  │  ┌─────────────┐    ┌────────────┐   ┌─────────────┐               │  │
│  │  │  akquant    │    │ Fund Engine│   │  Walk-      │               │  │
│  │  │  (Stock/ETF│    │ (Mutual    │   │  Forward    │               │  │
│  │  │  /Bond)     │    │  Fund)     │   │  Validator  │               │  │
│  │  └─────────────┘    └────────────┘   └─────────────┘               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │      生态系统层 (保留升级)                                           │  │
│  │  ┌─────────────┐    ┌────────────┐   ┌─────────────┐   ┌─────────┐ │  │
│  │  │   DNA       │    │ Phylogeny  │   │  Metabolic  │   │ Lifespan│ │  │
│  │  │  Sequencer  │    │  (3D Risk) │   │  Profiler   │   │ Predict │ │  │
│  │  └─────────────┘    └────────────┘   └─────────────┘   └─────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                              ┌───────▼────────┐
                              │   数据持久层    │
                              │   (SQLite)     │
                              └────────────────┘
```

---

## 二、核心业务链路详解

### 链路1: 用户首次使用链路（Onboarding）

```
用户打开首页
    │
    ▼
[检查画像状态] ──无画像──→ 显示空状态引导页
    │                          │
    │有画像                    ▼
    │                    [点击"开始画像"]
    │                          │
    ▼                          ▼
[展示Dashboard]          [画像问卷Wizard]
    │                    (6-8步问卷)
    │                          │
    │                          ▼
    │                    [保存画像]
    │                          │
    │                          ▼
    │                    [计算建议配置]
    │                          │
    └──────────────────────→ [跳转到Dashboard]
```

**数据流：**
```
Frontend: InvestorProfileWizard.vue
    │ POST /api/v1/investor-profiles
    ▼
Backend: investor_profile_service.py
    │ 1. 解析问卷答案
    │ 2. 计算风险评分(risk_tolerance: 1-10)
    │ 3. 确定画像类型(conservative/balanced/aggressive/speculative)
    │ 4. 生成建议配置(suggested_allocation)
    │ 5. 保存到 investor_profiles 表
    ▼
Frontend: DashboardView.vue (刷新)
    │ GET /api/v1/investor-profiles/me
    ▼
显示: 用户画像卡片 + 建议配置饼图 + 快速操作按钮
```

---

### 链路2: 投资组合推荐链路（核心）

```
用户查看Dashboard
    │
    ▼
[系统后台自动运行]
    │
    ├──→ [获取用户画像] ──→ risk_tolerance, preferred_assets, horizon
    │
    ├──→ [获取市场状态] ──→ economic_cycle_phase, market_sentiment, environment_score
    │                        (economic_cycle_service.py 每月更新)
    │
    ├──→ [调用组合构建器]
    │      │
    │      ├── 战略配置: 画像 → 资产类别权重
    │      │              例: 积极型+复苏期 → 股票60% + 债券25% + 商品10% + 现金5%
    │      │
    │      ├── 战术配置: 周期 → 具体标的
    │      │              例: 复苏期 → 沪深300ETF(30%) + 中证500ETF(20%) + 黄金ETF(10%)
    │      │
    │      └── 策略绑定: 每个标的配置一个策略流
    │                   例: 沪深300ETF → 双均线趋势跟踪策略
    │
    ├──→ [策略推荐引擎过滤]
    │      │
    │      ├── 硬过滤: risk_level ≤ user_risk_tolerance
    │      ├── 硬过滤: suitable_cycle ∩ current_cycle ≠ ∅
    │      ├── 硬过滤: lifespan_months ≥ 3
    │      └── 排序: 近半年夏普比率降序
    │
    └──→ [生成推荐组合]
           │
           ├── 组合配置JSON
           ├── 每个资产对应的策略ID
           ├── 预期收益/风险指标（基于历史回测）
           └── 再平衡规则（频率/触发条件）
```

**数据流：**
```
Frontend: DashboardView.vue (页面加载时)
    │ GET /api/v1/portfolios/recommended
    ▼
Backend: portfolio_service.py
    │ 1. 获取当前用户画像
    │    db.query(InvestorProfile).filter(user_id=current_user)
    │
    │ 2. 获取当前市场状态
    │    db.query(MarketSignal).order_by(date.desc()).first()
    │
    │ 3. 调用组合构建器
    │    portfolio = build_portfolio(profile, market_state)
    │    - 战略配置: 基于画像类型模板
    │    - 战术配置: 基于周期-资产映射表
    │
    │ 4. 调用策略推荐引擎
    │    strategies = recommendation_engine.recommend(
    │        profile=profile,
    │        market_state=market_state,
    │        portfolio=portfolio,
    │        top_k=5
    │    )
    │
    │ 5. 回测验证组合
    │    backtest_result = run_portfolio_backtest(portfolio, strategies)
    │
    │ 6. 返回推荐结果
    ▼
Frontend: 展示推荐组合卡片 + 预期收益/风险 + "应用组合"按钮
```

---

### 链路3: 策略生成与入池链路（后台异步）

```
定时任务触发 (每周日凌晨2:00)
    │
    ▼
[策略生成器启动]
    │
    ├──→ [RAG知识检索]
    │      │
    │      ├── 检索近期论文: "2025年表现最好的量化策略类型"
    │      ├── 检索策略池: 哪些家族近期表现好/差
    │      └── 输出: 推荐生成的策略家族 + 参数范围建议
    │
    ├──→ [模板加载]
    │      │
    │      ├── 从策略家族加载参数化模板
    │      └── 根据RAG建议动态调整参数搜索空间
    │
    ├──→ [贝叶斯优化]
    │      │
    │      ├── 目标函数: 综合评分(夏普+卡玛+胜率+回撤+泛化)
    │      ├── 搜索算法: Optuna TPE
    │      ├── Walk-Forward验证: 训练60% / 验证20% / 测试20%
    │      └── 早停: 验证集连续3轮不提升则停止
    │
    ├──→ [泛化验证]
    │      │
    │      ├── 10只不同类型股票 × 每段≥6个月 × 3个时间段
    │      ├── 样本外测试(最近6个月未参与训练)
    │      ├── DNA测序健康度 > 60
    │      ├── 寿命预测 > 6个月
    │      └── 综合同质化风险 < 0.7
    │
    └──→ [入池决策]
           │
           ├── 通过全部验证 ──→ 写入 strategy_pool 表
           │                      状态: active
           │                      加入推荐候选集
           │
           └── 未通过验证 ──→ 写入 strategy_pool 表
                              状态: rejected
                              记录失败原因(供分析)
```

**数据流：**
```
APScheduler定时任务
    │
    ▼
strategy_generator.py::generate_batch()
    │ 1. RAG检索
    │    rag_service.retrieve("current best strategy types")
    │
    │ 2. 加载模板
    │    template = strategy_pool_service.load_template(family_id)
    │    param_space = adjust_by_rag(template.param_space, rag_result)
    │
    │ 3. 贝叶斯优化
    │    study = optuna.create_study(direction="maximize")
    │    for trial in study.trials:
    │        params = suggest_params(trial, param_space)
    │        strategy_code = template.render(params)
    │        score = evaluate_strategy(strategy_code, walk_forward=True)
    │        study.report(trial.number, score)
    │    best_params = study.best_params
    │
    │ 4. 泛化验证
    │    strategy = template.render(best_params)
    │    results = []
    │    for stock in TEST_STOCKS_10_TYPES:
    │        for period in TEST_PERIODS_3:
    │            result = backtest(strategy, stock, period)
    │            results.append(result)
    │    all_pass = all(r.win_rate > 0.4 for r in results)
    │
    │ 5. DNA测序 + 寿命预测
    │    dna = dna_sequencer.sequence_strategy(strategy_id, strategy.code)
    │    lifespan = lifespan_service.compute_lifespan(dna)
    │
    │ 6. 同质化检查
    │    homogeneity = phylogeny_service.compute_3d_homogeneity(strategy_id)
    │
    │ 7. 入池决策
    │    if all_pass and dna.health > 60 and lifespan > 6 and homogeneity < 0.7:
    │        strategy_pool_service.activate(strategy_id)
    │    else:
    │        strategy_pool_service.reject(strategy_id, reasons)
    ▼
返回: 生成策略数 / 入池数 / 拒绝数
```

---

### 链路4: 动态寿命监控链路（定时任务）

```
每月1日凌晨3:00自动运行
    │
    ▼
[寿命监控服务启动]
    │
    ├──→ [采集市场环境数据]
    │      │
    │      ├── 市场波动率: 20日ATR / 历史波动率百分位
    │      ├── 市场周期: economic_cycle_service.get_current_phase()
    │      ├── 市场风格: 大盘/小盘、成长/价值指数相对强弱
    │      └── 家族拥挤度: 各策略家族近3月超额收益
    │
    ├──→ [遍历所有活跃策略]
    │      │
    │      ├── 读取基础寿命（静态，入库时计算）
    │      ├── 计算波动率加速因子
    │      ├── 计算周期适配因子
    │      ├── 计算拥挤度因子
    │      └── 动态寿命 = 基础寿命 × 三因子
    │
    ├──→ [寿命变化检测]
    │      │
    │      ├── 寿命减少 > 20% → 黄色预警
    │      ├── 寿命减少 > 40% 或 动态寿命 < 3月 → 红色预警
    │      └── 寿命增加 → 绿色提示
    │
    ├──→ [写入寿命历史]
    │      └── strategy_lifespan_history表
    │
    └──→ [推送预警通知]
           └── 前端Dashboard显示预警徽章
```

---

### 链路5: 回测验证链路

```
用户发起回测请求
    │
    ├──→ [解析组合/策略]
    │      │
    │      ├── 资产类型判断:
    │      │   - 个股/ETF/可转债 → akquant引擎
    │      │   - 公募基金 → fund_backtest_engine
    │      │
    │      ├── 多资产混合回测:
    │      │   - 各资产独立回测
    │      │   - 按配置权重合并收益曲线
    │      │   - 考虑再平衡成本
    │
    ├──→ [运行回测]
    │      │
    │      ├── 获取历史数据 (akshare)
    │      ├── 标准化数据格式
    │      ├── 执行策略信号
    │      ├── 记录交易流水
    │      └── 计算收益指标
    │
    ├──→ [基准对比]
    │      └── 同步运行买入持有基准
    │
    └──→ [输出报告]
           ├── 收益曲线图
           ├── 11项核心指标对比
           ├── 交易记录列表
           ├── 风险分析
           └── 策略生态快照（DNA/寿命/家族）
```

---

## 三、模块依赖关系图

```
                            ┌─────────────────┐
                            │   user_service  │
                            └────────┬────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐          ┌─────────────────┐          ┌───────────────┐
│ investor_     │          │  portfolio_     │          │  strategy_    │
│ profile_      │◄────────►│  service        │◄────────►│  recommendation│
│ service       │          │                 │          │  _engine      │
└───────┬───────┘          └────────┬────────┘          └───────┬───────┘
        │                           │                           │
        │                           ▼                           │
        │                  ┌─────────────────┐                  │
        │                  │ economic_cycle_ │                  │
        │                  │ _service        │                  │
        │                  └────────┬────────┘                  │
        │                           │                           │
        │                           ▼                           ▼
        │                  ┌─────────────────┐          ┌───────────────┐
        │                  │  market_signal_ │          │  strategy_    │
        │                  │  _service       │          │  _generator   │
        │                  └────────┬────────┘          └───────┬───────┘
        │                           │                           │
        │                           │                           ▼
        │                           │                  ┌───────────────┐
        │                           │                  │ strategy_pool_│
        │                           │                  │ _service      │
        │                           │                  └───────┬───────┘
        │                           │                          │
        └───────────────────────────┴──────────────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  backtest_      │
                           │  service        │
                           │  (akquant +     │
                           │   fund_engine)  │
                           └────────┬────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
           ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
           │dna_sequencer│ │phylogeny_   │ │lifespan_    │
           │             │ │service(3D)  │ │service      │
           └─────────────┘ └─────────────┘ └─────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │lifespan_monitor_│
                           │_service         │
                           └─────────────────┘
```

---

## 四、数据模型关系图

```
┌──────────┐       ┌──────────────────┐       ┌──────────────┐
│   User   │1─────∞│ InvestorProfile  │       │ MarketSignal │
│          │       │                  │       │  (每月更新)   │
└──────────┘       └────────┬─────────┘       └──────────────┘
                            │
                            │1
                            ▼
                     ┌──────────────┐
                     │   Portfolio  │
                     │              │
                     └──────┬───────┘
                            │1
                            ▼
                   ┌────────────────┐
                   │PortfolioHolding│
                   │  (资产配置明细) │
                   └───────┬────────┘
                           │∞
                           ▼
                    ┌──────────────┐
                    │StrategyPool  │
                    │  (策略池)     │
                    └──────┬───────┘
                           │1
                           ▼
                    ┌──────────────┐
                    │BacktestResult│
                    │  (回测记录)   │
                    └──────┬───────┘
                           │∞
                           ▼
                    ┌──────────────┐
                    │ StrategyDNA  │
                    │              │
                    └──────┬───────┘
                           │1
                           ▼
              ┌────────────────────────┐
              │    StrategyPhylogeny   │
              │      (三维同质化)       │
              └───────────┬────────────┘
                          │1
                          ▼
                   ┌──────────────┐
                   │LifespanHistory│
                   │ (寿命轨迹)    │
                   └──────────────┘
```

---

## 五、外部依赖关系

| 外部系统 | 用途 | 调用频率 | 失败处理 |
|---------|------|---------|---------|
| **akshare** | A股/ETF/基金/债券/期货数据获取 | 每次回测/每日定时 | 多源回退(东方财富→新浪财经) |
| **SQLite** | 本地数据持久化 | 每次API调用 | 事务回滚 |
| **APScheduler** | 定时任务调度 | 后台持续运行 | 重启后恢复 |
| **Optuna** | 贝叶斯优化(策略生成) | 每周批量 | 降级为网格搜索 |
