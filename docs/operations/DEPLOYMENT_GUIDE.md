# 部署运维指南

**版本**: v5.0.2
**目标读者**: 运维工程师、DevOps工程师、系统管理员
**用途**: 生产环境部署、监控、维护和故障排除

## 🚀 快速部署

### 系统要求
```
最低配置:
├── CPU: 2核
├── 内存: 4GB
├── 存储: 20GB SSD
└── 网络: 10Mbps

推荐配置:
├── CPU: 4核
├── 内存: 8GB
├── 存储: 50GB SSD
└── 网络: 100Mbps
```

### 依赖软件
```bash
# 基础环境
Python 3.9+
Node.js 18+
Docker 20.10+
Docker Compose 2.0+

# 可选服务
Redis 6.0+
PostgreSQL 13+
Nginx 1.20+
```

### 一键部署脚本
```bash
#!/bin/bash
# deploy.sh - 智能钓鱼助手一键部署

set -e

echo "🚀 开始部署智能钓鱼助手 v5.0.2"

# 1. 环境检查
echo "📋 检查系统环境..."
python3 --version || (echo "❌ Python 3.9+ required" && exit 1)
node --version || (echo "❌ Node.js 18+ required" && exit 1)
docker --version || echo "⚠️  Docker未安装，将使用本地部署"

# 2. 代码获取
echo "📥 获取代码..."
git clone https://github.com/your-org/fishing-agent.git
cd fishing-agent
git checkout v5.0.2

# 3. 依赖安装
echo "📦 安装依赖..."
uv sync
cd apps/web-admin && npm install && cd ../..

# 4. 环境配置
echo "⚙️  配置环境..."
cp .env.example .env
echo "请编辑 .env 文件添加必要的API密钥"

# 5. 数据库初始化
echo "🗄️  初始化数据库..."
uv run python scripts/setup_db.py

# 6. 服务启动
echo "🎯 启动服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    uv run fishing-api &
    cd apps/web-admin && npm run build && cd ../..
fi

echo "✅ 部署完成！"
echo "🌐 API服务: http://localhost:8000"
echo "🖥️  管理界面: http://localhost:5173"
echo "📖 API文档: http://localhost:8000/docs"
```

## 🐳 Docker部署

### Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  # API服务
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - CAIYUN_API_KEY=${CAIYUN_API_KEY}
      - AMAP_API_KEY=${AMAP_API_KEY}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - WECHAT_APPID=${WECHAT_APPID}
      - WECHAT_SECRET=${WECHAT_SECRET}
      - OCR_PROVIDER=ollama
      - DATABASE_URL=postgresql://fishing:${DB_PASSWORD}@postgres:5432/fishing_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - ollama
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./shared:/app/shared

  # React前端
  web:
    image: node:18-alpine
    working_dir: /app
    ports:
      - "5173:5173"
    volumes:
      - ./apps/web-admin:/app
      - web_node_modules:/app/node_modules
    command: sh -c "npm install && npm run dev"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    restart: unless-stopped

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=fishing_db
      - POSTGRES_USER=fishing
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Ollama本地OCR
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_KEEP_ALIVE=24h
    restart: unless-stopped

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./apps/web-admin/dist:/usr/share/nginx/html
    depends_on:
      - api
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  ollama_data:
  web_node_modules:
```

### Dockerfile配置
```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY apps/ ./apps/
COPY shared/ ./shared/
COPY scripts/ ./scripts/

# 安装Python依赖
RUN uv sync --frozen

# 复制应用代码
COPY main.py ./
COPY .env.example .env

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "fishing-api", "--host", "0.0.0.0", "--port", "8000"]
```

### 部署命令
```bash
# 1. 准备环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 构建和启动服务
docker-compose up -d --build

# 3. 初始化Ollama模型
docker-compose exec ollama ollama pull deepseek-ocr

# 4. 查看服务状态
docker-compose ps

# 5. 查看日志
docker-compose logs -f api
```

## 🔧 环境配置

### 生产环境变量
```bash
# .env.production
# 基础配置
NODE_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# 核心API服务 (必需)
DASHSCOPE_API_KEY=your-production-dashscope-key
CAIYUN_API_KEY=your-production-caiyun-key
AMAP_API_KEY=your-production-amap-key

# JWT认证 (必需)
JWT_SECRET_KEY=your-super-secret-jwt-key-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# 微信小程序配置
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret
WECHAT_API_URL=https://api.weixin.qq.com
WECHAT_AUTO_CREATE_USER=true

# OCR配置
OCR_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=deepseek-ocr

# 数据库配置
DATABASE_URL=postgresql://fishing:${DB_PASSWORD}@postgres:5432/fishing_db
DB_PASSWORD=your-secure-db-password

# Redis配置
REDIS_URL=redis://redis:6379

# 向量存储配置
VECTOR_EMBEDDING_MODEL=text-embedding-v3
VECTOR_AUTO_INDEX=true

# 监控配置
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
```

### Nginx配置
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api:8000;
    }

    upstream web_backend {
        server web:5173;
    }

    # HTTP重定向到HTTPS
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS主配置
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL证书配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;

        # 安全头
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API代理
        location /api/ {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 静态文件服务
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # 文件上传大小限制
        client_max_body_size 10M;
    }
}
```

## 📊 监控和告警

### Prometheus监控配置
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fishing-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']
```

### Grafana仪表盘
```json
{
  "dashboard": {
    "title": "智能钓鱼助手监控",
    "panels": [
      {
        "title": "API请求率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "系统资源使用",
        "type": "graph",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU"
          },
          {
            "expr": "memory_usage_percent",
            "legendFormat": "Memory"
          }
        ]
      }
    ]
  }
}
```

### 告警规则
```yaml
# monitoring/alerts.yml
groups:
  - name: fishing-assistant
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API错误率过高"
          description: "API错误率在过去5分钟内超过10%"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过长"
          description: "95%的请求响应时间超过2秒"

      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率持续超过80%"

      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率持续超过85%"
```

## 🔍 日志管理

### 日志配置
```python
# shared/config/logging.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """配置日志系统"""

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_dir / log_file)
        file_handler.setFormatter(formatter)

    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)

    if log_file:
        root_logger.addHandler(file_handler)
```

### 日志轮转配置
```bash
# /etc/logrotate.d/fishing-assistant
/path/to/fishing-agent/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 fishing fishing
    postrotate
        docker-compose exec api kill -USR1 1
    endscript
}
```

## 🚨 故障排除

### 常见问题排查

#### **1. API服务无法启动**
```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 检查日志
docker-compose logs api

# 检查环境变量
docker-compose exec api env | grep -E "(API_KEY|SECRET)"

# 手动启动测试
docker-compose exec api uv run fishing-api --host 0.0.0.0 --port 8000
```

#### **2. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 检查连接配置
docker-compose exec api python -c "
import os
from shared.config.database import get_database_url
print(get_database_url())
"

# 测试连接
docker-compose exec api python -c "
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
print(engine.execute('SELECT 1').scalar())
"
```

#### **3. 前端无法访问API**
```bash
# 检查Nginx配置
docker-compose exec nginx nginx -t

# 测试API代理
curl -H "Host: your-domain.com" http://localhost/api/health

# 检查CORS配置
curl -H "Origin: https://your-domain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://your-domain.com/api/v1/fishing/chat
```

#### **4. OCR服务异常**
```bash
# 检查Ollama状态
docker-compose exec ollama ollama list

# 测试OCR模型
docker-compose exec ollama ollama run deepseek-ocr

# 检查OCR配置
docker-compose exec api python -c "
from packages.data_processing.ocr import OCRMergeProcessor
processor = OCRMergeProcessor(provider='ollama')
print('OCR配置正常')
"
```

### 性能优化

#### **1. 数据库优化**
```sql
-- 创建索引
CREATE INDEX idx_user_equipment_user_id ON user_equipment(user_id);
CREATE INDEX idx_chat_session_user_id ON chat_session(user_id);
CREATE INDEX idx_fishing_recommendation_location ON fishing_recommendation(location, created_at);

-- 分析查询性能
EXPLAIN ANALYZE SELECT * FROM user_equipment WHERE user_id = 1;
```

#### **2. Redis缓存优化**
```python
# 缓存策略配置
CACHE_CONFIG = {
    "weather": {"ttl": 600, "prefix": "weather:"},      # 10分钟
    "embedding": {"ttl": 3600, "prefix": "emb:"},       # 1小时
    "equipment": {"ttl": 1800, "prefix": "equip:"},      # 30分钟
    "user_session": {"ttl": 300, "prefix": "session:"},  # 5分钟
}
```

#### **3. API限流配置**
```python
# 限流中间件
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/fishing/chat")
@limiter.limit("10/minute")  # 每分钟10次请求
async def fishing_chat(request: Request, limiter_limit: str):
    # 处理逻辑
    pass
```

## 🔄 备份和恢复

### 数据库备份
```bash
#!/bin/bash
# backup.sh - 数据库备份脚本

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fishing_db_$DATE.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
docker-compose exec -T postgres pg_dump -U fishing fishing_db > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "数据库备份完成: $BACKUP_FILE.gz"
```

### 数据恢复
```bash
#!/bin/bash
# restore.sh - 数据库恢复脚本

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 停止API服务
docker-compose stop api

# 恢复数据库
gunzip -c $BACKUP_FILE | docker-compose exec -T postgres psql -U fishing fishing_db

# 重启服务
docker-compose start api

echo "数据库恢复完成"
```

### 自动备份配置
```bash
# 添加到crontab
# 每天凌晨2点执行备份
0 2 * * * /path/to/backup.sh

# 每周日凌晨3点执行完整备份
0 3 * * 0 /path/to/full_backup.sh
```

---

**文档版本**: v5.0.2
**最后更新**: 2024-12-20
**维护者**: 智能钓鱼助手运维团队
**相关文档**: [配置管理](CONFIGURATION.md) | [监控告警](MONITORING.md)