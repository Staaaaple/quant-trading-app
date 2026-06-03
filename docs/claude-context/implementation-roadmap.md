---
name: implementation-roadmap
description: QuantEvo重构项目分阶段实现路径，从基础设施到全链路服务
metadata: 
  node_type: memory
  type: project
  originSessionId: 61e9a59f-cef2-41bb-a951-ddf0d0e98814
---

# QuantEvo 重构实现路径

## Phase A：基础设施 + 用户系统 + 画像 + 首页（4周）

### 目标
搭建新的数据库模型，实现用户手动切换、15题问卷、profile_vector计算，重构首页为双状态Dashboard。

### 后端

| 文件 | 说明 |
|------|------|
| `models/user.py` | User模型（id, name, created_at） |
| `models/investor_profile.py` | InvestorProfile模型（user_id, profile_vector[15], answers_json, created_at） |
| `models/__init__.py` | 模型注册，DB初始化 |
| `services/profile_service.py` | 问卷答案 → 15维profile_vector计算 |
| `api/v1/endpoints/users.py` | User CRUD API |
| `api/v1/endpoints/profiles.py` | 画像CRUD + 计算API |
| `api/v1/router.py` | 新路由注册 |
| `main.py` | lifespan调整，保留原有调度 |

### 前端

| 文件 | 说明 |
|------|------|
| `assets/design-system.css` | 全局CSS变量（色彩/纹理/字体/阴影/动画） |
| `components/ui/Card.vue` | 统一卡片组件 |
| `components/ui/Button.vue` | 主按钮组件 |
| `components/ui/Tag.vue` | 标签组件 |
| `components/ui/Stat.vue` | 数据展示组件 |
| `views/ProfileWizard.vue` | 问卷Wizard（3步×5题） |
| `views/ProfileResult.vue` | 画像结果页（雷达图+配置预览） |
| `views/HomeView.vue` | 首页双状态重构（空状态/Dashboard） |
| `views/MarketSignalView.vue` | 市场信号页（骨架） |
| `views/PortfolioBuilder.vue` | 组合构建器（骨架） |
| `views/StrategyRecommendation.vue` | 策略推荐（骨架） |
| `views/LifespanCenter.vue` | 寿命监控（骨架） |
| `views/OnboardingGuide.vue` | 教学引导（骨架） |
| `router/index.ts` | 新路由配置 |
| `App.vue` | 全局布局（顶部导航+底部Tab） |

### 关键决策
- 数据库重建：删除旧表，新建User/InvestorProfile/Portfolio等表
- 用户系统：无登录，localStorage存user_id，支持手动切换
- 保留原有功能：策略工坊、回测中心、模拟盘等路由保留，入口适当隐藏

---

## Phase B：市场信号 + 组合生成 + 回测（5周）

### 目标
实现五层市场信号采集、Hybrid组合引擎、资产回测适配（ETF/基金/债券/期货）。

### 后端

| 文件 | 说明 |
|------|------|
| `models/market_signal.py` | MarketSignal模型（五层信号JSON，每日一条） |
| `models/portfolio.py` | Portfolio模型（组合配置JSON） |
| `models/portfolio_holding.py` | PortfolioHolding模型（标的+权重+策略绑定） |
| `models/backtest_result.py` | BacktestResult模型 |
| `services/market_signal_service.py` | 五层信号采集（akshare宏观+爬虫新闻） |
| `services/hybrid_portfolio_designer.py` | Hybrid引擎6步：SAA→TAA→策略绑定→风控→可靠性→寿命 |
| `services/saa_engine.py` | 战略资产配置（规则驱动） |
| `services/taa_engine.py` | 战术资产配置（规则驱动） |
| `services/strategy_binder.py` | 策略-标的绑定（贝叶斯优化） |
| `services/risk_configurator.py` | 风控配置自动生成 |
| `services/reliability_assessor.py` | 可靠性评估（回测+压力测试+蒙特卡洛） |
| `services/backtest_adapter.py` | 回测适配器（个股/ETF用akquant，基金用fund_engine） |
| `services/fund_backtest_engine.py` | 基金回测引擎（NAV+申购赎回费+T+1） |
| `api/v1/endpoints/market_signals.py` | 市场信号API |
| `api/v1/endpoints/portfolios.py` | 组合CRUD + 生成API |
| `api/v1/endpoints/backtests.py` | 回测API |

### 前端

| 文件 | 说明 |
|------|------|
| `views/MarketSignalView.vue` | 五层信号展示（卡片+评分） |
| `views/PortfolioBuilder.vue` | 组合构建器（配置预览+回测+应用） |
| `views/PortfolioDetail.vue` | 组合详情（资产配置+策略绑定+风控） |
| `views/BacktestCenter.vue` | 回测中心（列表+状态） |
| `views/BacktestDetail.vue` | 回测详情（收益曲线+指标+压力测试） |
| `components/charts/DonutChart.vue` | 环形图组件 |
| `components/charts/LineChart.vue` | 折线图组件 |
| `components/charts/RadarChart.vue` | 雷达图组件 |

### 关键决策
- 期货不直接交易，通过商品期货ETF间接配置
- 基金独立回测引擎（区别于akquant的日频OHLCV）
- 组合生成是同步还是异步？→ 先同步（<3秒），慢再改异步

---

## Phase C：策略池 + 策略发现 + 寿命监控（4周）

### 目标
构建策略池（七大策略家族），实现Agent Crawler策略发现，动态寿命监控。

### 后端

| 文件 | 说明 |
|------|------|
| `models/strategy_pool.py` | StrategyPool模型（策略元数据） |
| `models/strategy_dna.py` | StrategyDNA模型（32维基因向量） |
| `models/strategy_phylogeny.py` | StrategyPhylogeny模型（三维同质化） |
| `models/lifespan_history.py` | LifespanHistory模型（寿命轨迹） |
| `services/strategy_pool_manager.py` | 策略池管理（CRUD+家族分类） |
| `services/agent_crawler.py` | 爬虫：GitHub/arXiv/雪球/社区 |
| `services/strategy_validator.py` | 策略验证（回测+DNA+寿命+同质化） |
| `services/dna_sequencer.py` | DNA测序（32维基因向量）→ 复用现有 |
| `services/phylogeny_service.py` | 三维同质化计算 → 复用现有 |
| `services/lifespan_service.py` | 动态寿命计算 → 复用现有，增加组合层面 |
| `services/ecosystem_service.py` | 生态系统聚合 → 复用现有 |
| `api/v1/endpoints/strategies.py` | 策略池API（保留现有） |
| `api/v1/endpoints/lifespan.py` | 寿命监控API |

### 前端

| 文件 | 说明 |
|------|------|
| `views/StrategyWorkshop.vue` | 策略工坊（保留升级） |
| `views/StrategyMapView.vue` | 策略地图（保留） |
| `views/DNAReport.vue` | DNA报告（保留） |
| `views/LifespanCenter.vue` | 寿命监控中心（列表+预警+趋势） |
| `views/RecommendationView.vue` | 策略推荐（基于画像+市场） |

### 关键决策
- 策略池初期手工构建~50个，Agent Crawler逐步补充
- Agent Crawler先Phase C手工启动，评估后再决定自动化程度
- 保留现有生态系统模块（DNA/Phylogeny/Lifespan），增加组合层面聚合

---

## Phase D：全链路服务 + 教学引导 + 推送（3周）

### 目标
打通从画像到实操的完整链路：教学引导、建仓助手、日常推送、调仓提醒、周报月报。

### 后端

| 文件 | 说明 |
|------|------|
| `models/operation_log.py` | OperationLog模型（操作记录） |
| `models/recommendation_log.py` | RecommendationLog模型（推荐记录） |
| `models/notification.py` | Notification模型（推送消息） |
| `services/onboarding_service.py` | 教学引导内容生成 |
| `services/building_service.py` | 建仓助手（分批计划） |
| `services/push_service.py` | 推送系统（有操作才推） |
| `services/rebalance_service.py` | 调仓提醒（5种触发条件） |
| `services/weekly_report.py` | 周报生成 |
| `api/v1/endpoints/operations.py` | 操作API |
| `api/v1/endpoints/notifications.py` | 推送API |

### 前端

| 文件 | 说明 |
|------|------|
| `views/OnboardingGuide.vue` | 教学引导（4步Wizard） |
| `views/TodayOperation.vue` | 今日操作（买入/卖出/持有） |
| `views/WeeklyReport.vue` | 周报（收益+市场回顾+展望） |
| `views/PaperTradingMonitor.vue` | 模拟盘（保留升级） |
| `views/UserManual.vue` | 用户手册（保留） |
| `components/AlertBar.vue` | 告警条组件 |
| `components/ProgressStep.vue` | 步骤指示器 |

### 关键决策
- 不推具体券商，只给挑选标准
- 推送只在有操作时才推（非每日）
- 调仓触发5种条件：定期/偏离度/寿命预警/健康度下降/周期切换

---

## 总计时间线

```
Week  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16
      |--Phase A--|
                  |-----Phase B-----|
                                    |--Phase C--|
                                                |Phase D|
```

**总计约16周（4个月）**

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| akshare数据不稳定 | 增加本地缓存层，降级 gracefully |
| 组合生成速度慢 | 初期规则驱动，成熟期考虑缓存热门组合 |
| 策略池样本不足 | 初期固定模板库兜底，Agent Crawler逐步补充 |
| 回测一致性 | ML策略单独适配器，严格WFA分离训练/验证/测试 |
| 信号融合可比性 | Phase B验证后评估，必要时引入校准层 |

---

## 立即开始（Phase A 第1周）

1. 数据库重建（删除旧表，新建模型）
2. User + InvestorProfile 后端模型
3. 画像计算服务
4. 问卷Wizard前端页面
5. 首页空状态 + Dashboard 骨架
