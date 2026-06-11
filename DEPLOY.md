# QuantEvo 部署指南

## 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ 可用内存
- 10GB+ 磁盘空间

### 2. 一键部署

```bash
# 克隆项目
git clone <your-repo-url>
cd quant-trading-app

# 运行部署脚本
./deploy.sh
```

### 3. 手动部署

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 访问服务

| 服务 | URL | 说明 |
|------|-----|------|
| 前端 | http://localhost | 主界面 |
| 后端 API | http://localhost:8000 | REST API |
| API 文档 | http://localhost:8000/api/v1/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 后端状态 |

### 5. 自动维护

容器已配置以下自动维护机制：

- **自动重启**: `restart: unless-stopped` - 服务崩溃后自动重启
- **健康检查**: 每30秒检查一次，失败3次后自动重启容器
- **日志轮转**: 最大100MB，保留5个文件
- **Watchtower**: 每小时检查镜像更新并自动部署

### 6. 环境变量配置

编辑 `docker-compose.yml` 中的环境变量：

```yaml
environment:
  - LLM_BACKEND=mock          # 生产环境改为 mlx/openai
  - EMBEDDING_BACKEND=mock    # 生产环境改为 sentence_transformers
  - QWEN_MLX_MODEL_PATH=      # MLX模型路径（Apple Silicon）
  - OPENAI_API_KEY=           # OpenAI API密钥
```

### 7. 数据持久化

以下数据通过 Docker Volume 持久化：

- `./backend/data` - SQLite数据库
- `./backend/logs` - 应用日志
- `./backend/data_cache` - 数据缓存

### 8. 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
./deploy.sh

# 或仅更新容器
docker-compose pull && docker-compose up -d
```

### 9. 故障排查

```bash
# 查看容器状态
docker-compose ps

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 进入容器调试
docker exec -it quantevo-backend bash

# 重启单个服务
docker-compose restart backend
```

### 10. 生产环境建议

1. **HTTPS**: 使用 Nginx 或 Traefik 配置 SSL
2. **域名**: 配置 DNS 指向服务器 IP
3. **防火墙**: 仅开放 80/443 端口
4. **监控**: 集成 Prometheus + Grafana
5. **备份**: 定期备份 `./backend/data` 目录

---

## 服务器部署示例（Ubuntu）

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo apt-get install docker-compose-plugin

# 克隆项目
git clone <your-repo-url>
cd quant-trading-app

# 部署
./deploy.sh

# 配置开机自启
sudo systemctl enable docker
```
