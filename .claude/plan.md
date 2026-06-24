# 模拟盘改造计划：基于每日市场报告的累计收益统计

## 背景与目标

用户要求模拟盘不再执行原有“读取外部行情、生成交易信号、模拟撮合”的逻辑，改为：

1. 每天读取资产组合的市场报告（`market_reports.page2_portfolio_performance`）中的日收益率；
2. 以“累计收益率”为核心指标进行日复利累加（净值曲线）；
3. 每到下一个月，自动统计上一个月的月度收益率。

本质上，模拟盘变为“基于每日报告的业绩统计器”。

## 需求确认结果

- **标的范围**：不是跑模拟盘，而是对每日报告数据进行统计；面向每个用户的当前激活组合（与现有市场报告逻辑一致：取 `Portfolio.is_active=True` 中最近更新的一个）。
- **累加指标**：累计收益率（推荐），即日复利：`nav_t = nav_{t-1} * (1 + daily_return)`，`cumulative_return = nav_t - 1`。
- **月度统计**：月度收益率（从月初第一个交易日到月末最后一个交易日的累计收益）。

## 总体方案

新增两张表：

- `paper_trading_daily_records`：每日记录，保存从市场报告提取的日收益、净值、累计收益。
- `paper_trading_monthly_stats`：月度统计，保存每个自然月的月度收益率与月末累计收益。

将旧的 `paper_trading_sessions`、`paper_signals` 表及相关 API/前端页面移除或重构为“统计看板”。

每日市场报告生成后，自动同步生成/更新当天的 `paper_trading_daily_records`；在每月 1 日运行月度统计任务，计算上一个月的数据。

## 关键文件变更

### 后端

1. **`backend/app/models/paper_trading.py`**
   - 删除 `PaperTradingSession`、`PaperSignal`。
   - 新增 `PaperTradingDailyRecord` 模型：
     - `id`, `user_id`, `portfolio_id`
     - `record_date` (YYYY-MM-DD)
     - `daily_return` (来自 page2 `portfolio_return`)
     - `cumulative_return`
     - `nav`（净值，初始为 1.0）
     - `asset_snapshot`（可选，保存 page2 `asset_performances` 快照）
     - `report_id`（关联 `market_reports.id`）
     - `created_at`, `updated_at`
   - 新增 `PaperTradingMonthlyStat` 模型：
     - `id`, `user_id`, `portfolio_id`
     - `year_month` (YYYY-MM)
     - `monthly_return`
     - `cumulative_return_at_month_end`
     - `record_count`
     - `created_at`, `updated_at`

2. **`backend/app/schemas/paper_trading.py`**
   - 删除 `PaperTradingSessionCreate/Read/Update`、`PaperSignalRead`。
   - 新增 `PaperTradingDailyRecordRead`、`PaperTradingMonthlyStatRead`、过滤参数 Schema。

3. **`backend/app/services/paper_trading_service.py`**
   - 删除 `run_paper_trading_session`、信号生成、策略流解析、临时文件等旧逻辑。
   - 新增核心服务函数：
     - `sync_daily_record_from_report(db, user_id, portfolio_id, report_id, report_date, page2)`：从 page2 提取 `portfolio_return`，计算净值/累计收益，写入 `paper_trading_daily_records`；若同一天已存在则幂等更新。
     - `calculate_cumulative(db, user_id, portfolio_id, record_date, daily_return)`：查找上一交易日记录，按日复利计算净值。
     - `generate_monthly_stat(db, user_id, portfolio_id, year_month)`：统计指定月份第一个和最后一个有记录的日收益，计算月度收益率和月末累计收益。
     - `list_daily_records(db, user_id, portfolio_id, start_date, end_date)`
     - `list_monthly_stats(db, user_id, portfolio_id)`
     - `get_latest_record(db, user_id, portfolio_id)`

4. **`backend/app/main.py`**
   - 在 `_run_daily_market_report_job` 里，每生成一条 `MarketReport` 后，调用 `paper_trading_service.sync_daily_record_from_report` 同步当天的模拟盘记录。
   - 新增 `_run_paper_trading_monthly_job` 调度任务：每月 1 日 04:00，遍历所有活跃用户与当前激活组合，为上一个月生成 `PaperTradingMonthlyStat`。
   - 在 lifespan 的 scheduler 配置中加入该月度任务。

5. **`backend/app/api/v1/endpoints/paper_trading.py`**
   - 删除旧的 session/signal 相关端点（create/list/get/delete/run/stop/signals）。
   - 新增端点：
     - `GET /paper-trading/daily-records`：返回累计收益曲线数据。
     - `GET /paper-trading/monthly-stats`：返回月度收益率列表。
     - `POST /paper-trading/sync-daily/{report_id}`（可选，用于手动触发单条报告同步）。
     - `POST /paper-trading/calc-monthly/{year_month}`（可选，用于手动触发月度统计）。

6. **`backend/app/api/v1/router.py`**
   - 保持 `/paper-trading` 路由挂载，无需新增路由。

7. **数据库初始化**
   - 项目未使用 Alembic，依赖 SQLAlchemy `Base.metadata.create_all`。
   - 新增模型后首次启动会自动建表；旧表 `paper_trading_sessions`、`paper_signals` 如不需要可保留空表，或在应用启动时手动删除（风险较低，建议保留旧表避免历史数据丢失，前端/API 已禁用访问）。

### 前端

1. **`frontend/src/views/PaperTradingMonitor.vue`**
   - 替换为“模拟盘业绩统计”看板：
     - 累计收益率折线图（使用已有图表库，如 ECharts/Vue3 项目中的 chart 组件）。
     - 月度收益率表格。
     - 最新一日报告摘要（当日收益、累计收益、最佳/最差资产）。

2. **`frontend/src/api/paperTrading.ts`**
   - 删除旧 session/signal API 函数。
   - 新增 `getDailyRecords`、`getMonthlyStats` 函数。

3. **`frontend/src/router/index.ts`**
   - 保持 `/paper-trading` 路由路径，指向改造后的页面。

## 数据流

```
APScheduler 每日 15:30
  → _run_daily_market_report_job
      → 对每个活跃用户生成 MarketReport（page1 + page2）
      → 调用 paper_trading_service.sync_daily_record_from_report
          → 从 page2 读取 portfolio_return
          → 取上一交易日 nav 计算今日 nav
          → 写入 paper_trading_daily_records

APScheduler 每月 1 日 04:00
  → _run_paper_trading_monthly_job
      → 对每个活跃用户/当前组合
          → 调用 generate_monthly_stat(上个月)
          → 写入 paper_trading_monthly_stats

用户访问前端 /paper-trading
  → GET /paper-trading/daily-records
  → GET /paper-trading/monthly-stats
  → 渲染累计曲线 + 月度表
```

## 关键计算逻辑

### 每日累计收益率

```python
prev = 上一交易日记录
if prev:
    nav = prev.nav * (1 + daily_return)
else:
    nav = 1.0 * (1 + daily_return)
cumulative_return = nav - 1
```

### 月度收益率

```python
month_start = 该月第一条 daily_record
month_end   = 该月最后一条 daily_record
monthly_return = (1 + month_end.cumulative_return) / (1 + month_start_前一天.cumulative_return) - 1
# 或简化为：若月初净值为 month_start.nav，则 monthly_return = month_end.nav / month_start.nav - 1
```

采用“月初净值 → 月末净值”计算月度收益，避免跨月复利断裂。

## 边界情况

- **无组合/无持仓**：page2 `portfolio_return` 为 0，净值不变，仍生成记录，保证月度统计的连续性。
- **节假日/报告缺失**：按实际有报告的天数记录；月度统计以当月第一条和最后一条有效记录为准。
- **重复运行**：`sync_daily_record_from_report` 对 `(user_id, portfolio_id, record_date)` 做唯一约束或先查询后更新，确保幂等。
- **用户切换激活组合**：记录按 `portfolio_id` 独立，切换组合后净值从 1.0 重新开始累计（符合“当前激活组合”语义）。

## 测试要点

1. 生成一条 daily market report，验证 `paper_trading_daily_records` 是否正确写入。
2. 连续多天生成报告，验证累计收益率是否按日复利正确。
3. 跨月后运行月度任务，验证月度收益率正确。
4. 删除旧 session API 后，确认前端页面可正常加载新看板。

## 实施步骤

1. 修改模型与 Schema（`paper_trading.py`）。
2. 重写 `paper_trading_service.py` 核心统计逻辑。
3. 修改 `paper_trading.py` API 端点。
4. 在 `main.py` 中接入每日同步与月度调度。
5. 改造前端页面与 API 封装。
6. 启动后端验证建表与调度任务。
7. 运行手动测试。
