# Project Progress

- **Project:** quant-trading-app
- **Started:** 2026-04-14T18:30:00+08:00
- **Last Updated:** 2026-04-14T22:35:00+08:00

## Status
- Total Tasks: 9
- Completed: 9
- In Progress: 0
- Pending: 0

## Task List
- [x] Task 1: 初始化后端项目结构（FastAPI、依赖配置、目录结构）
- [x] Task 2: 设计并实现 SQLite 数据模型（策略、回测结果、模拟盘状态）
- [x] Task 3: 实现策略管理 API（CRUD、策略代码持久化）
- [x] Task 4: 实现回测调度 API（集成 akquant.run_backtest）
- [x] Task 5: 实现模拟盘调度核心（AKShare 数据适配器 + LiveRunner 封装）
- [x] Task 6: 初始化前端项目（Vue 3 + Vite + 基础路由配置）
- [x] Task 7: 实现策略工坊页面（编辑器、保存、加载）
- [x] Task 8: 实现回测中心与模拟盘监控页面
- [x] Task 9: 前后端联调与一键启动脚本

## Activity Log
- [2026-04-14T19:35:00+08:00] Task 1: 初始化后端项目结构 — 完成。创建了 FastAPI 后端目录结构、requirements.txt、main.py、config.py、db 基础模块及 API 路由占位文件。
- [2026-04-14T19:35:00+08:00] Task 2: 设计并实现 SQLite 数据模型 — 完成。已创建 Strategy、BacktestResult、PaperSignal、RealTrade、RealPosition、SyncLog 六个 ORM 模型及对应 Pydantic Schema。
- [2026-04-14T20:10:00+08:00] Task 3: 实现策略管理 API — 完成。实现了策略的创建、列表、详情、更新、删除 5 个 REST 端点，服务层做了数据库操作封装，pytest 7 个用例全部通过。
- [2026-04-14T20:20:00+08:00] Task 4: 实现回测调度 API — 完成。调研了 akquant 0.2.8 的 run_backtest 接口，发现 strategy_source 需传文件路径；后端通过临时文件桥接用户策略代码。实现了回测记录创建、列表、详情、以及 POST /run 触发回测流程。测试中 mock 了 akshare 数据获取和 akquant 引擎，3 个用例全部通过。
- [2026-04-14T21:00:00+08:00] Task 4 扩展 — 扩展 _normalize_akquant_df 列名映射，增加 turnover_rate、market_cap、pe、pb、vwap、ma5/10/20/60 等字段，支持更多策略通过 bar.extra 访问扩展数据。
- [2026-04-14T21:05:00+08:00] Task 4 扩展测试 — 补充 test_normalize_akquant_df_preserves_extra_columns，验证中文列名映射、扩展列保留及数值类型转换。backend/tests/test_backtests.py 共 4 个用例全部通过。
- [2026-04-14T21:55:00+08:00] Task 5 Step 1 — 新增 PaperTradingSession 模型与 Schema，定义模拟盘会话表结构及对应 Pydantic 模型。
- [2026-04-14T22:10:00+08:00] Task 5 完成 — 实现 PaperTradingService（含 LiveRunner 封装、AKShare 数据适配、akquant 回测信号提取），新增 paper-trading API 端点（sessions CRUD + run/stop）。补充 4 个 pytest 用例，全部 15 个测试在 quant 环境中通过。
- [2026-04-14T22:15:00+08:00] Task 6 完成 — 初始化前端项目（Vue 3 + Vite + TypeScript + Pinia + Vue Router）。创建了 `frontend/` 目录，配置了基础路由（首页、策略工坊、回测中心、模拟盘监控），替换 App.vue 为侧边栏布局，`npm run build` 通过。
- [2026-04-14T22:25:00+08:00] Task 7 完成 — 实现策略工坊页面（StrategyWorkshop.vue），集成 CodeMirror Python 编辑器，支持策略的创建、保存、加载、删除。
- [2026-04-14T22:30:00+08:00] Task 8 完成 — 实现回测中心（BacktestCenter.vue）和模拟盘监控（PaperTradingMonitor.vue）。新增 `api/backtest.ts`、`api/paperTrading.ts`，支持创建/运行回测、创建/运行/停止模拟盘会话。`npm run build` 通过。
- [2026-04-14T22:35:00+08:00] Task 9 完成 — 前后端联调与一键启动脚本。通过 Python urllib 联调验证了 strategy/backtest/paper-trading 三个模块的 API 端到端可用；修复了前端 API 尾斜杠导致的 307 重定向问题。新增项目根目录 `start.py`，支持 `conda quant` 环境下同时启动后端 uvicorn 和前端 npm dev。
- [2026-04-14T20:30:00+08:00] 环境隔离与网络问题排查 — 完成。创建了 conda 环境 `quant`（Python 3.11），将项目依赖完全隔离于 base 环境。测试确认 akshare 因系统代理无法访问，已编写 `docs/network-notes.md` 供前端实现代理弹窗提醒。解决 numpy 版本冲突：因 akquant 要求 `numpy>=2.2.2`，将 `requirements.txt` 修正为 `numpy>=2.2.2,<2.4`（当前安装 2.3.5），避免与 numba 的 `<2.4` 要求冲突。全部 10 个 pytest 用例在 `quant` 环境中通过。
