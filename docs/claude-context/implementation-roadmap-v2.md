---
name: implementation-roadmap-v2
description: QuantEvo重构完整实现路径V2（A-D全链路，含遗漏补充）
metadata: 
  node_type: memory
  type: project
  originSessionId: 61e9a59f-cef2-41bb-a951-ddf0d0e98814
---

# QuantEvo 重构实现路径 V2（完整版）

## 核心变更

- **Phase B 扩展为7周**：直接包含知识库基础（35模板+20论文）+ 完整Hybrid 6步链路
- **Phase C 只做增量**：策略池扩展、Agent Crawler、动态寿命，**不动已有框架**
- **补充遗漏**：资产标的表、论文知识库、再平衡触发器、蒙特卡洛、压力测试、定时任务

---

## Phase A：基础设施 + 用户系统 + 画像 + 首页（4周）

### 目标
用户手动切换、15题问卷、profile_vector计算、首页双状态、全局样式系统。

### 后端

| 文件 | 说明 |
|------|------|
| `models/user.py` | User模型 |
| `models/investor_profile.py` | InvestorProfile（15维向量） |
| `services/profile_service.py` | 问卷答案→15维向量计算 |
| `services/user_context.py` | 当前用户上下文管理（localStorage映射） |
| `api/v1/endpoints/users.py` | User CRUD |
| `api/v1/endpoints/profiles.py` | 画像CRUD+预览计算 |

### 前端

| 文件 | 说明 |
|------|------|
| `assets/design-system.css` | 全局样式系统 |
| `views/HomeView.vue` | 首页双状态（空状态/Dashboard骨架） |
| `views/ProfileWizard.vue` | 问卷Wizard（3步×5题） |
| `views/ProfileResult.vue` | 画像结果页（雷达图+标签+配置预览）⭐补充 |
| `components/UserSwitcher.vue` | 用户切换下拉（localStorage存user_id）⭐补充 |
| `components/charts/RadarChart.vue` | 雷达图组件（画像结果用）⭐补充 |

### 遗漏补充
- **画像结果页**：问卷完成后展示15维雷达图+风险标签+建议配置预览
- **用户切换UI**：顶部导航栏的用户下拉，支持切换/新建用户
- **当前用户上下文**：localStorage存active_user_id，全局可用

---

## Phase B：市场信号 + 知识库基础 + Hybrid引擎 + 回测（7周）

### Week 1：市场信号采集

| 文件 | 说明 |
|------|------|
| `models/market_signal.py` | 五层信号模型（每日一条） |
| `services/market_signal_service.py` | 采集：akshare宏观+爬虫新闻+NLP情绪 |
| `services/news_crawler.py` | 新浪财经/财联社/雪球爬虫 ⭐补充 |
| `api/v1/endpoints/market_signals.py` | 信号查询API |
| `views/MarketSignalView.vue` | 五层信号展示页 |

**定时任务**：每日9:00自动采集（`main.py`添加）⭐补充

### Week 2-3：知识库基础

#### 策略模板库（35个核心模板）

| 模型 | 说明 |
|------|------|
| `models/strategy_template.py` | 策略模板元数据（代码/参数空间/适用周期/风险等级）⭐补充 |
| `models/template_backtest_result.py` | 模板回测结果（10股×6月×3段）⭐补充 |

| 服务 | 说明 |
|------|------|
| `services/template_manager.py` | 模板管理（CRUD+家族分类+回测验证）⭐补充 |
| `services/template_runner.py` | 模板运行器（统一输入输出接口）⭐补充 |

**七大策略家族 × 5个 = 35个模板**（详见phase-b-plan-v2.md）

#### 论文知识库（20篇核心）

| 模型 | 说明 |
|------|------|
| `models/paper_knowledge.py` | 论文结构化（元数据/结论/参数/市场映射/回测结果）⭐补充 |

| 服务 | 说明 |
|------|------|
| `services/paper_knowledge_service.py` | 论文CRUD+查询（按家族/周期/市场状态）⭐补充 |

### Week 3-4：完整Hybrid引擎

| 服务 | 说明 |
|------|------|
| `services/hybrid_portfolio_designer.py` | Hybrid引擎总控（6步编排） |
| `services/saa_engine.py` | SAA：画像风险×市场周期→资产权重（硬编码规则，接口预留知识库注入） |
| `services/taa_engine.py` | TAA：行业景气×社会趋势→细分权重调整 |
| `services/strategy_binder.py` | 策略-标的绑定（Optuna贝叶斯优化，35模板做候选集） |
| `services/risk_configurator.py` | 风控配置自动生成（止损/仓位/回撤/再平衡） |
| `services/portfolio_rebalancer.py` | 再平衡触发器（5种条件检测）⭐补充 |
| `services/reliability_assessor.py` | 可靠性评估总控 |
| `services/monte_carlo.py` | 蒙特卡洛模拟器（1000次随机路径）⭐补充 |
| `services/stress_tester.py` | 压力测试（2022熊市/2020疫情/2015股灾回放）⭐补充 |

### Week 4-5：回测适配器

| 服务 | 说明 |
|------|------|
| `services/backtest_adapter.py` | 回测总控（路由到具体引擎） |
| `services/fund_backtest_engine.py` | 基金回测（NAV+申购赎回费+T+1确认） |
| `services/walk_forward_validator.py` | Walk-Forward验证（训练60%/验证20%/测试20%）⭐补充 |

### Week 5-6：资产标的管理

| 模型 | 说明 |
|------|------|
| `models/asset.py` | 资产标的基础信息（code/name/class/数据源）⭐补充 |

| 服务 | 说明 |
|------|------|
| `services/asset_service.py` | 资产数据管理（ETF/基金/债券/期货ETF列表）⭐补充 |
| `services/asset_data_cache.py` | 本地缓存层（应对akshare不稳定）⭐补充 |

### Week 6-7：前端页面

| 页面 | 说明 |
|------|------|
| `views/MarketSignalView.vue` | 市场信号（五层卡片+评分+趋势） |
| `views/PortfolioBuilder.vue` | 组合构建器（6步Wizard展示+配置预览+回测+应用） |
| `views/PortfolioDetail.vue` | 组合详情（资产+策略绑定+风控+回测结果+压力测试） |
| `views/BacktestCenter.vue` | 回测中心 |
| `views/BacktestDetail.vue` | 回测详情（收益曲线+蒙特卡洛+压力测试） |

---

## Phase C：策略池扩展 + Agent Crawler + 寿命监控（4周）

### 目标
策略池从35→150，Agent Crawler补充策略，动态寿命，完整DNA/同质化。

### 后端

| 文件 | 说明 |
|------|------|
| `models/strategy_pool.py` | 策略池（从template迁移，增加status/active_date） |
| `models/lifespan_history.py` | 寿命轨迹（每月记录） |
| `services/agent_crawler.py` | 爬虫：GitHub/arXiv/雪球/社区 |
| `services/strategy_validator.py` | 策略验证（回测+DNA+寿命+同质化） |
| `services/dna_sequencer.py` | DNA测序（32维基因）→ 复用现有 |
| `services/phylogeny_service.py` | 三维同质化 → 复用现有 |
| `services/lifespan_service.py` | 动态寿命计算 → 复用现有，增加组合层面 |
| `services/ecosystem_service.py` | 生态系统聚合 → 复用现有 |

**定时任务**：
- 每月1日3:00：寿命更新（`main.py`添加）⭐补充
- 每周日2:00：Agent Crawler（`main.py`添加）⭐补充

### 前端

| 页面 | 说明 |
|------|------|
| `views/LifespanCenter.vue` | 寿命监控中心（列表+预警+趋势图） |
| `views/StrategyDiscovery.vue` | 策略发现（Agent Crawler结果展示）⭐补充 |
| `views/RecommendationView.vue` | 策略推荐（基于画像+市场+寿命） |

---

## Phase D：全链路服务 + 教学引导 + 推送（3周）

### 目标
画像→组合→教学→建仓→推送→调仓→周报，完整闭环。

### 后端

| 模型 | 说明 |
|------|------|
| `models/operation_log.py` | 操作记录 |
| `models/notification.py` | 推送消息（有操作才推）⭐补充 |
| `models/notification_settings.py` | 推送偏好设置 ⭐补充 |
| `models/operation_plan.py` | 建仓计划（分批方案）⭐补充 |

| 服务 | 说明 |
|------|------|
| `services/onboarding_service.py` | 教学引导内容生成（4步） |
| `services/building_service.py` | 建仓助手（分批计划+金额计算） |
| `services/push_service.py` | 推送系统（今日操作/寿命预警/周期切换） |
| `services/rebalance_service.py` | 调仓提醒（5种触发检测+替代方案推荐） |
| `services/weekly_report.py` | 周报生成（收益/市场回顾/下周展望） |

### 前端

| 页面 | 说明 |
|------|------|
| `views/OnboardingGuide.vue` | 教学引导（4步Wizard：策略原理→券商选择→建仓计划→日常跟进） |
| `views/TodayOperation.vue` | 今日操作（买入/卖出/持有信号+一键确认）⭐补充 |
| `views/WeeklyReport.vue` | 周报（收益回顾+市场回顾+下周展望） |
| `components/AlertBar.vue` | 告警条（寿命预警/周期切换/偏离度）⭐补充 |
| `components/NotificationBadge.vue` | 通知角标（顶部导航）⭐补充 |

---

## 数据流闭环验证

```
Phase A                    Phase B                        Phase C              Phase D
├─画像问卷                  ├─市场信号采集                   ├─Agent Crawler       ├─教学引导
│  └─profile_vector ──────→├─知识库基础（35模板）            │  └─新策略入池        │  └─策略原理卡片
│                          │   └─SAA/TAA规则                 ├─寿命动态更新         ├─建仓助手
│                          ├─Hybrid引擎                      │   └─寿命预警 ─────→├─今日操作推送
│                          │   └─组合配置 ─────────────────→├─调仓提醒            │   └─买入/卖出信号
│                          ├─回测验证                        │   └─替代方案推荐      ├─周报月报
│                          │   └─回测结果 ─────────────────→├─再平衡执行          │
│                          └─组合应用（is_applied=true）      │                     └─持仓监控
│                                                                                   └─寿命到期处理
```

**闭环检查**：
- ✅ 画像 → 组合生成（Profile→Hybrid）
- ✅ 市场信号 → 组合调整（MarketSignal→Rebalancer）
- ✅ 组合 → 回测验证（Portfolio→Backtest）
- ✅ 回测 → 应用组合（BacktestResult→Portfolio.is_applied）
- ✅ 应用 → 寿命监控（Portfolio→LifespanMonitor）
- ✅ 寿命 → 调仓提醒（Lifespan↓→RebalanceAlert）
- ✅ 调仓 → 新组合回测（Rebalance→NewPortfolio→Backtest）
- ✅ 日常 → 推送（每日信号→PushNotification）

---

## 总计时间线

```
Week  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18
      |--Phase A--|
                  |-------Phase B-------|
                                        |--Phase C--|
                                                    |Phase D|
```

**总计约18周（4.5个月）**

---

## 数据库模型清单（完整）

| 模型 | Phase | 说明 |
|------|-------|------|
| User | A | 用户 |
| InvestorProfile | A | 投资者画像（15维） |
| Portfolio | A | 组合配置 |
| PortfolioHolding | B | 组合持仓明细 |
| MarketSignal | B | 市场五层信号 |
| StrategyTemplate | B | 策略模板（35个核心）⭐ |
| TemplateBacktestResult | B | 模板回测结果 ⭐ |
| PaperKnowledge | B | 论文知识库 ⭐ |
| Asset | B | 资产标的基础信息 ⭐ |
| BacktestResult | B | 组合回测结果 |
| StrategyPool | C | 策略池（从template升级） |
| StrategyDNA | C | DNA测序 |
| StrategyPhylogeny | C | 三维同质化 |
| LifespanHistory | C | 寿命轨迹 |
| OperationLog | D | 操作记录 |
| Notification | D | 推送消息 ⭐ |
| NotificationSettings | D | 推送偏好 ⭐ |
| OperationPlan | D | 建仓计划 ⭐ |

---

## 定时任务清单

| 任务 | 频率 | Phase | 说明 |
|------|------|-------|------|
| 市场信号采集 | 每日9:00 | B | 五层信号自动更新 ⭐ |
| builtin选股 | 每周五15:05 | A（保留）| 现有任务 |
| 寿命动态更新 | 每月1日3:00 | C | 波动率/周期/拥挤度计算 ⭐ |
| Agent Crawler | 每周日2:00 | C | 策略发现 ⭐ |

---

## 已知遗留问题（不阻塞开发）

| 问题 | 阶段 | 说明 |
|------|------|------|
| 链路四直观化 | D后 | 全链路服务更直观的方法 |
| LLM辅助策略发现 | C评估 | Agent Crawler是否引入LLM |
| 信号融合风险 | B验证 | 不同策略信号置信度可比性 |
| 回测一致性 | B | ML策略lookahead bias |
| 样本量不足 | C | 画像×市场条件组合样本少 |
