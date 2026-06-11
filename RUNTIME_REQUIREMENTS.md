# QuantEvo 运行环境要求文档

> **项目**: QuantEvo — 策略即有机体的量化投资平台  
> **版本**: v2.0  
> **更新日期**: 2026-06-11

---

## 目录

1. [系统要求](#一系统要求)
2. [开发环境依赖](#二开发环境依赖)
3. [生产环境依赖](#三生产环境依赖)
4. [环境变量配置](#四环境变量配置)
5. [数据库初始化](#五数据库初始化)
6. [LLM 模型配置](#六llm-模型配置)
7. [启动方式](#七启动方式)
8. [常见问题](#八常见问题)

---

## 一、系统要求

### 1.1 最低配置

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 双核 x86_64 或 Apple Silicon | 四核及以上 |
| 内存 | 4 GB | 8 GB+（本地 LLM 需 16 GB+） |
| 磁盘 | 10 GB 可用空间 | 20 GB+（含模型缓存） |
| 网络 | 可访问 PyPI / npm / AKShare | 稳定互联网连接 |
| 操作系统 | macOS 12+ / Linux / Windows WSL2 | macOS 14+ 或 Ubuntu 22.04 |

### 1.2 Apple Silicon 特别说明

本项目原生支持 Apple Silicon（M1/M2/M3/M4）的 **MLX 框架** 进行本地 LLM 推理：

- **推荐机型**: MacBook Pro 16GB+ 内存
- **模型**: Qwen3-14B-MLX-4bit（约 8.5GB）
- **无需**: Docker、虚拟机、CUDA

---

## 二、开发环境依赖

### 2.1 前端依赖

#### 必需环境

| 工具 | 版本要求 | 用途 |
|------|---------|------|
| Node.js | `^20.19.0 \|\| >=22.12.0` | 运行时 |
| npm | >= 10.0 | 包管理 |
| 浏览器 | Chrome 120+ / Safari 17+ / Edge 120+ | 开发调试 |

#### 核心 npm 依赖

```json
{
  "vue": "^3.5.31",
  "vite": "^8.0.3",
  "typescript": "~6.0.0",
  "vue-router": "^5.0.4",
  "pinia": "^3.0.4",
  "vue-i18n": "^11.3.2",
  "echarts": "^6.0.0",
  "vue-echarts": "^8.0.1",
  "tailwindcss": "^4.1.17",
  "@tailwindcss/vite": "^4.1.17"
}
```

#### 安装命令

```bash
cd frontend
npm install
```

### 2.2 后端依赖

#### 必需环境

| 工具 | 版本要求 | 用途 |
|------|---------|------|
| Python | >= 3.10（推荐 3.11） | 运行时 |
| pip | >= 23.0 | 包管理 |
| SQLite | 3.35+ | 内置，无需额外安装 |

> **推荐**: 使用 Conda 创建独立环境：
> ```bash
> conda create -n quant python=3.11
> conda activate quant
> ```

#### 核心 Python 依赖

```
# Web 框架
fastapi==0.115.0
uvicorn==0.32.0

# 数据验证与配置
pydantic==2.9.2
pydantic-settings==2.6.1

# ORM 与数据库
sqlalchemy==2.0.36

# 数据处理
pandas==2.2.3
numpy>=2.2.2,<2.4

# A 股数据源
akshare==1.18.55

# 量化回测引擎
akquant==0.2.8

# 定时任务
apscheduler==3.11.0

# RAG / 向量检索（可选）
faiss-cpu>=1.7.4
sentence-transformers>=2.2.0

# Apple Silicon 本地 LLM（可选）
mlx-lm>=0.31.0

# 测试
pytest==8.3.3
httpx==0.27.2
```

#### 安装命令

```bash
cd backend
pip install -r requirements.txt
```

### 2.3 可选依赖（需额外手动安装）

| 依赖 | 用途 | 安装命令 | 说明 |
|------|------|---------|------|
| `openai` | 云端 LLM 推理 | `pip install openai` | 仅当使用 `LLM_BACKEND=openai` 时需要，默认未安装 |
| Playwright | E2E 测试 | `npm install -D @playwright/test` | 前端测试框架 |
| Vue DevTools | 开发调试 | 浏览器插件 | Chrome / Edge 插件市场安装 |

---

## 三、生产环境依赖

### 3.1 Docker 部署

| 工具 | 版本要求 |
|------|---------|
| Docker | 20.10+ |
| Docker Compose | 2.0+ |

#### 容器化服务

```yaml
# docker-compose.yml 包含以下服务：
services:
  backend:    # Python 3.11 + FastAPI，端口 8000
  frontend:   # Nginx + 静态资源，端口 80
  watchtower: # 自动容器更新，每小时检查
```

#### 持久化卷

| 宿主机路径 | 容器路径 | 用途 |
|-----------|---------|------|
| `./backend/data` | `/app/data` | SQLite 数据库 |
| `./backend/logs` | `/app/logs` | 应用日志 |
| `./backend/data_cache` | `/app/data_cache` | 数据缓存 |

### 3.2 Nginx 配置

生产环境通过 Nginx 提供前端静态资源并反向代理 API：

- **监听端口**: 80
- **API 代理**: `/api/*` → `http://backend:8000`
- **SPA 回退**: 所有路由 → `index.html`
- **Gzip 压缩**: 启用
- **静态缓存**: 1 年

---

## 四、环境变量配置

### 4.1 后端环境变量（`.env`）

创建 `backend/.env` 文件，参考 `backend/.env.example`：

```bash
# ============================================
# 数据库配置
# ============================================
SQLITE_DB_PATH=./quant_trading.db

# ============================================
# LLM 后端（三选一）
# ============================================
# 选项 1: Apple Silicon 本地 MLX（推荐 M 系列 Mac）
LLM_BACKEND=mlx
QWEN_MLX_MODEL_PATH=/Users/macbookair/.cache/huggingface/hub/models--Qwen--Qwen3-14B-MLX-4bit/blobs

# 选项 2: OpenAI API
# LLM_BACKEND=openai
# OPENAI_API_KEY=sk-xxxxxxxx
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini

# 选项 3: Mock（开发测试，无实际推理）
# LLM_BACKEND=mock

# ============================================
# Embedding 后端（三选一）
# ============================================
# 选项 1: 本地 Sentence Transformers
EMBEDDING_BACKEND=sentence_transformers
EMBEDDING_MODEL_NAME=BAAI/bge-large-zh-v1.5

# 选项 2: OpenAI Embedding
# EMBEDDING_BACKEND=openai
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# 选项 3: Mock
# EMBEDDING_BACKEND=mock

# ============================================
# CORS 配置
# ============================================
BACKEND_CORS_ORIGINS=["*"]
```

### 4.2 前端环境变量

#### 开发环境（`.env.development`，自动生效）

```
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

#### 生产环境（`.env.production`）

```
VITE_API_BASE_URL=/api/v1
```

> 生产环境通过 Nginx 代理 `/api` 到后端，前端使用相对路径。

---

## 五、数据库初始化

### 5.1 自动初始化

首次启动后端时，以下操作**自动执行**：

1. **创建表结构**: SQLAlchemy `Base.metadata.create_all()`
2. **列迁移兼容**: `_ensure_db_columns()` 自动添加新列
3. **内置选股器**: `ensure_builtin_picker()`
4. **种子知识库**: 策略模板 + 论文数据
5. **初始市场信号**: 首次市场数据采集

### 5.2 手动导入策略种子

```bash
cd backend
python seed_strategies.py
```

导入 18 个预设交易策略（趋势跟踪、动量、均值回归、多因子、风控增强）。

### 5.3 数据库文件位置

| 环境 | 路径 |
|------|------|
| 开发 | `backend/quant_trading.db` |
| Docker | `backend/data/quant_trading.db` |

---

## 六、LLM 模型配置

### 6.1 MLX 本地模型（Apple Silicon 推荐）

#### 模型下载

```bash
# 使用 huggingface-cli 下载
pip install huggingface-hub
huggingface-cli download --local-dir-use-symlinks False \
  --local-dir ~/.cache/huggingface/hub/models--Qwen--Qwen3-14B-MLX-4bit \
  Qwen/Qwen3-14B-MLX-4bit
```

#### 配置验证

```bash
# 测试模型加载
python -c "
from mlx_lm import load
model, tokenizer = load('Qwen/Qwen3-14B-MLX-4bit')
print('模型加载成功')
"
```

### 6.2 OpenAI API（需额外安装）

> ⚠️ `openai` 包**不在** `requirements.txt` 中，使用前需手动安装。

```bash
# 1. 安装 openai 包
pip install openai

# 2. 在 .env 中配置
LLM_BACKEND=openai
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

### 6.3 Embedding 模型

| 后端 | 模型 | 大小 | 适用场景 |
|------|------|------|---------|
| sentence_transformers | `BAAI/bge-large-zh-v1.5` | ~1.3GB | 中文语义搜索 |
| OpenAI | `text-embedding-3-small` | 云端 | 轻量快速 |

---

## 七、启动方式

### 7.1 一键启动（推荐开发）

```bash
# 同时启动前后端
python start.py

# 访问地址：
# 前端: http://localhost:3000
# 后端 API: http://127.0.0.1:8000
# API 文档: http://127.0.0.1:8000/docs
```

### 7.2 分别启动

```bash
# 终端 1: 后端
cd backend
conda activate quant  # 如使用 Conda
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2: 前端
cd frontend
npm run dev
```

### 7.3 Docker 启动（推荐生产）

```bash
# 一键部署
./deploy.sh

# 或手动
sudo docker-compose up -d --build

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 7.4 定时任务说明

后端启动后自动注册以下定时任务：

| 任务 | 频率 | 说明 |
|------|------|------|
| 内置选股器运行 | 每周五 15:05 | 自动选股 |
| 市场信号采集 | 每日 09:00、15:00 | 五层市场评估 |
| 策略寿命检查 | 每月 1 日 03:00 | 动态寿命管理 |

---

## 八、常见问题

### Q1: `akquant` 安装失败？

```bash
# 确保系统已安装编译工具
# macOS:
xcode-select --install

# Ubuntu/Debian:
sudo apt-get install build-essential python3-dev
```

### Q2: `faiss-cpu` 安装失败？

```bash
# macOS 使用 conda 安装
conda install -c pytorch faiss-cpu

# 或跳过 RAG 功能
# 在 .env 中设置 EMBEDDING_BACKEND=mock
```

### Q3: 前端端口冲突？

```bash
# 修改 frontend/vite.config.ts
server: {
  port: 3001,  # 修改为其他端口
}
```

### Q4: Apple Silicon 上 MLX 模型加载慢？

- 首次加载需编译缓存，约 1-3 分钟
- 后续启动秒级
- 确保模型路径正确且文件完整

### Q5: 数据库文件过大？

```bash
# SQLite 清理历史数据
sqlite3 backend/quant_trading.db "VACUUM;"
```

---

## 附录：文件速查

| 文件 | 路径 | 用途 |
|------|------|------|
| 前端依赖 | `frontend/package.json` | npm 包清单 |
| 后端依赖 | `backend/requirements.txt` | Python 包清单 |
| 环境变量模板 | `backend/.env.example` | 后端配置参考 |
| Docker 编排 | `docker-compose.yml` | 生产部署 |
| 后端 Dockerfile | `backend/Dockerfile` | 后端容器构建 |
| 前端 Dockerfile | `frontend/Dockerfile` | 前端容器构建 |
| Nginx 配置 | `frontend/nginx.conf` | 生产代理规则 |
| 启动脚本 | `start.py` | 一键开发启动 |
| 部署脚本 | `deploy.sh` | 一键生产部署 |
| 策略种子 | `backend/seed_strategies.py` | 初始策略数据 |
