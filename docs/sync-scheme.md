# 真实持仓同步方案（手动实盘辅助）

> 文档目的：由于当前系统采用 akquant Paper Trading 模式运行，真实交易需在券商 APP 中手动执行。本方案定义模拟盘与真实持仓之间的同步机制，确保数据一致性、降低遗漏概率，并为未来接入 MiniQMT 自动执行预留扩展空间。

---

## 一、核心原则：双账本并行

- **模拟账本**：由 akquant 引擎维护，负责信号生成、模拟撮合、理论盈亏计算。
- **真实账本**：由本系统独立维护，记录用户在券商 APP 中的真实成交和持仓。
- **不 hack akquant 内部状态**：不直接修改 `engine.portfolio.positions`，避免丢失订单历史、成本价和审计链路。

---

## 二、基础功能

### 2.1 一键同步

**触发时机**：策略产生交易信号后，用户在券商 APP 中完成操作，回到系统点击同步。

**弹窗内容（预填充）**：
- 标的代码（从最新信号自动带入）
- 交易方向（Buy / Sell，自动带入）
- 建议数量（从信号自动带入）
- 实际成交数量（默认同建议数量，可修改）
- 实际成交价（默认使用信号触发时的收盘价，可修改）
- 手续费（根据用户在"账户设置"中预设的佣金率自动计算，可微调）
- 备注（可选）

**同步动作**：
1. 写入 `real_trades`（真实成交表）
2. 更新 `real_positions`（真实持仓表，采用 FIFO 或均价法计算成本）
3. 写入 `sync_logs`（同步记录表，记录模拟信号与真实成交的差异）

### 2.2 收盘提醒同步

**触发时机**：交易日 15:05，系统自动执行。

**系统动作**：
1. 拉取 AKShare 当日收盘价
2. 对比 `akquant 模拟持仓` 与 `real_positions 真实持仓`
3. 检测不一致标的，生成"待同步清单"
4. 推送消息："今日还有 N 只标的未同步真实持仓，请核对"
5. 生成当日对账单草稿，展示：
   - 模拟盘当日盈亏
   - 真实账本当日盈亏（如有同步数据）
   - 持仓差异列表
   - 未同步信号列表

---

## 三、数据表设计

### 3.1 real_trades（真实成交表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `signal_id` | VARCHAR(64) | 关联的模拟盘信号 ID（可为空） |
| `strategy_id` | VARCHAR(64) | 关联的策略 ID |
| `symbol` | VARCHAR(16) | 标的代码 |
| `side` | VARCHAR(8) | Buy / Sell |
| `quantity` | FLOAT | 成交数量 |
| `price` | FLOAT | 成交价 |
| `commission` | FLOAT | 佣金 |
| `stamp_tax` | FLOAT | 印花税 |
| `transfer_fee` | FLOAT | 过户费 |
| `total_cost` | FLOAT | 总成本（买入）/ 总回款（卖出） |
| `sync_status` | VARCHAR(16) | synced / partial / cancelled |
| `synced_at` | DATETIME | 同步时间 |
| `source` | VARCHAR(16) | manual / csv_import / ocr |
| `remark` | TEXT | 备注 |

### 3.2 real_positions（真实持仓表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `strategy_id` | VARCHAR(64) | 策略 ID |
| `symbol` | VARCHAR(16) | 标的代码 |
| `quantity` | FLOAT | 当前持仓数量 |
| `available_qty` | FLOAT | 可用数量（T+1） |
| `avg_cost` | FLOAT | 平均成本价 |
| `total_cost` | FLOAT | 总成本 |
| `market_value` | FLOAT | 最新市值（收盘后更新） |
| `floating_pnl` | FLOAT | 浮动盈亏 |
| `updated_at` | DATETIME | 更新时间 |

### 3.3 sync_logs（同步记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增主键 |
| `signal_id` | VARCHAR(64) | 模拟信号 ID |
| `strategy_id` | VARCHAR(64) | 策略 ID |
| `symbol` | VARCHAR(16) | 标的代码 |
| `signal_side` | VARCHAR(8) | 信号方向 |
| `signal_qty` | FLOAT | 信号建议数量 |
| `signal_price` | FLOAT | 信号参考价格 |
| `actual_qty` | FLOAT | 实际成交数量 |
| `actual_price` | FLOAT | 实际成交价格 |
| `diff_reason` | VARCHAR(32) | 差异原因：price_slippage / qty_partial / not_executed / extra_trade |
| `created_at` | DATETIME | 记录时间 |

---

## 四、扩展功能（按优先级排序）

### 4.1 持仓对比看板（Diff Dashboard）

在"模拟盘监控"页面常驻显示持仓一致性：
- 绿色：模拟持仓与真实持仓完全一致
- 黄色：数量不一致（模拟有 / 真实无，或数量差异）
- 红色：真实持仓中有模拟盘未知的标的（额外操作）

点击差异项直接跳转"一键同步"弹窗。

### 4.2 信号超时未同步提醒

策略产生信号后，若超过 N 分钟（默认 30 分钟）未同步：
- 前端 badge 计数 +1
- 推送系统消息/微信提醒

### 4.3 费用自动计算

用户在"账户设置"中维护：
- 佣金率（默认 0.025%，最低 5 元）
- 是否沪市（用于过户费计算）

"一键同步"时自动计算：
- 买入：佣金 + 过户费
- 卖出：佣金 + 印花税 + 过户费

### 4.4 部分成交处理

同步表单支持选择状态：
- `synced`：全部成交
- `partial`：部分成交（仅按实际成交量更新持仓，未成交部分标记为"挂单中"）
- `cancelled`：已撤单（不产生持仓变动）

### 4.5 CSV/Excel 交割单导入

支持从同花顺/通达信/券商客户端导出的交割单批量导入：
- 解析字段：日期、标的、方向、数量、价格、手续费
- 批量写入 `real_trades` 并自动更新 `real_positions`

### 4.6 截图 OCR 识别（远期）

用户上传券商 APP 截图：
- 使用 PaddleOCR / 腾讯云 OCR 识别标的、价格、数量
- 自动填充同步表单

### 4.7 周末批量补录模式

提供"批量录入"页面：
- 左侧：本周交易日列表
- 右侧：选中日期后显示当日所有模拟信号
- 逐条勾选"已执行"并填实际价格，Tab 键快速跳转
- 一次提交，批量写入

---

## 五、与 Milestone 的对应关系

| 功能 | 对应阶段 |
|------|---------|
| 一键同步 + 持仓 Diff 看板 | Milestone 2（模拟盘核心） |
| 收盘自动对账 + 提醒 | Milestone 3（风控 + 审计） |
| 费用自动计算 | Milestone 3 |
| CSV 交割单导入 | Milestone 3 |
| OCR 截图识别 | Milestone 4（预留） |

---

## 六、与未来自动执行的衔接

当系统未来接入 MiniQMT 真实 Gateway 后：
- `real_trades` 的写入来源从"前端手动同步"改为"MiniQMT Gateway 回调"
- `real_positions` 的更新来源从"手动计算"改为"券商柜台查询"
- 表结构完全保持不变，仅 `source` 字段新增 `broker_auto` 类型
- "一键同步"功能退化为"异常兜底"和"非量化交易补录"用途
