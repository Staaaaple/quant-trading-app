# Quant Trading App

一个面向个人量化投资者的轻量级全栈量化交易平台，支持策略编写、回测验证、模拟盘监控以及真实持仓同步。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite + TypeScript + Pinia + Vue Router + ECharts + Vue I18n + CodeMirror |
| **后端** | FastAPI + SQLAlchemy + SQLite + Pydantic |
| **量化引擎** | [akquant](https://github.com/akfamily/akquant)（回测/模拟盘）+ [akshare](https://www.akshare.xyz/)（数据获取）|
| **测试** | pytest + httpx |

---

## 项目结构

```
quant-trading-app/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/           # 后端 API 封装
│   │   ├── components/    # 公共组件
│   │   ├── i18n/          # 国际化
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── views/         # 页面视图
│   │   ├── App.vue
│   │   └── main.ts
│   └── package.json
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/        # API 路由与端点
│   │   ├── core/          # 配置项
│   │   ├── db/            # 数据库模型与会话
│   │   ├── models/        # SQLAlchemy ORM 模型
│   │   ├── schemas/       # Pydantic 数据校验
│   │   ├── services/      # 业务逻辑层
│   │   └── main.py        # 应用入口
│   ├── tests/             # 测试用例
│   └── requirements.txt
├── docs/                  # 设计文档
│   └── sync-scheme.md     # 真实持仓同步方案
├── start.py               # 一键启动前后端开发环境
└── package.json           # 根目录依赖（CodeMirror 相关）
```

---

## 核心功能

### 1. 策略工坊（Strategy Workshop）
- 在线编写 Python 量化策略，内置 CodeMirror 编辑器
- 支持策略的增删改查与版本管理
- 策略代码持久化到本地数据库

### 2. 回测中心（Backtest Center）
- 为指定策略配置回测参数（标的、时间范围、初始资金）
- 调用 akquant 引擎执行回测
- 记录回测状态与结果，支持历史回测对比

### 3. 模拟盘监控（Paper Trading Monitor）
- 基于 akquant Paper Trading 模式运行策略
- 实时展示模拟持仓、盈亏与交易信号
- 为真实交易执行提供决策参考

### 4. 真实持仓同步（Real Position Sync）
- **双账本并行**：模拟账本（akquant）+ 真实账本（本系统独立维护）
- 一键同步：在券商 APP 完成真实交易后，回填实际成交数据
- 收盘自动对账：对比模拟持仓与真实持仓，生成差异清单
- 未来可平滑扩展至 MiniQMT 自动交易接入

> 详细设计见 [docs/sync-scheme.md](./docs/sync-scheme.md)

---

## 快速开始

### 环境要求

- **Node.js**: `^20.19.0 || >=22.12.0`
- **Python**: `>=3.10`
- **Conda**（推荐用于管理 Python 环境）

### 1. 安装依赖

**前端**

```bash
cd frontend
npm install
```

**后端**

```bash
# 创建并激活 conda 环境（示例）
conda create -n quant python=3.12
conda activate quant

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 2. 启动开发环境

在项目根目录执行一键启动脚本：

```bash
python start.py
```

该脚本会同时启动：
- **后端服务**：`http://127.0.0.1:8000`（uvicorn 热重载）
- **前端服务**：`http://localhost:5173`（vite dev server）

按 `Ctrl+C` 即可优雅关闭所有子进程。

### 3. 手动启动（可选）

```bash
# 后端
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 前端（新终端）
cd frontend
npm run dev
```

---

## API 文档

启动后端后，可访问自动生成的 OpenAPI 文档：

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### 主要接口

| 模块 | 前缀 |
|------|------|
| 策略管理 | `/api/v1/strategies` |
| 回测管理 | `/api/v1/backtests` |
| 模拟盘 | `/api/v1/paper-trading` |
| 持仓同步 | `/api/v1/sync` |
| 健康检查 | `/health` |

---

## 运行测试

```bash
cd backend
pytest
```

---

## 配置文件

后端配置通过 `backend/app/core/config.py` 管理，支持 `.env` 文件覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROJECT_NAME` | `quant-trading-app` | 项目名称 |
| `VERSION` | `0.1.0` | 版本号 |
| `API_V1_STR` | `/api/v1` | API 前缀 |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173` | 允许的跨域来源 |
| `SQLITE_DB_PATH` | `./quant_trading.db` | SQLite 数据库路径 |

---

## 设计原则

1. **不侵入 akquant 内部状态**：模拟盘与真实持仓采用双账本并行，避免直接修改引擎内部 `portfolio.positions`
2. **预留自动交易扩展**：真实持仓表结构兼容未来 MiniQMT Gateway 自动接入
3. **前后端分离**：RESTful API + 现代化前端架构，便于独立演进
4. **本地优先**：SQLite + 本地文件存储，零外部数据库依赖，开箱即用

---

## 相关依赖

- [akquant](https://github.com/akfamily/akquant) — 量化回测与模拟交易引擎
- [akshare](https://www.akshare.xyz/) — 中国金融数据接口库
- [FastAPI](https://fastapi.tiangolo.com/) — 现代高性能 Python Web 框架
- [Vue 3](https://vuejs.org/) — 渐进式前端框架
- [ECharts](https://echarts.apache.org/) — 数据可视化图表库

---

## 许可证

MIT
