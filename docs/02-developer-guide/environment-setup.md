# 环境配置指南 v5.0.2

本指南将帮助您快速搭建智能钓鱼助手 v5.0.2 项目的开发环境。

## 📋 目录

- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [运行项目](#运行项目)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

## 🔧 环境要求

### 必需环境

1. **Python 3.11+**
   ```bash
   # 检查 Python 版本
   python --version
   # 或
   python3 --version
   ```

2. **uv 包管理器**（推荐）
   ```bash
   # 安装 uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # 或使用 pip
   pip install uv
   ```

3. **Node.js 18+**（前端需要）
   ```bash
   # 检查 Node.js 版本
   node --version
   ```

4. **微信开发者工具**（小程序开发）
   - 下载地址：[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)

### API 密钥

您需要准备以下 API 密钥：

| 服务 | 获取地址 | 用途 |
|------|----------|------|
| 彩云天气 | [彩云天气开放平台](https://caiyunapp.com/api) | 天气数据 |
| 高德地图 | [高德开放平台](https://lbs.amap.com/) | 地理坐标服务 |
| 通义千问 | [阿里云百炼平台](https://bailian.console.aliyun.com/) | LLM 和 Embedding |
| 智谱AI | [智谱AI开放平台](https://open.bigmodel.cn/) | LLM 服务（推荐） |
| 微信小程序 | [微信公众平台](https://mp.weixin.qq.com/) | 小程序登录 |

## 📦 安装步骤

### 1. 克隆项目

```bash
# 使用 git 克隆
git clone https://github.com/yourusername/fishing-agent.git
cd fishing-agent

# 切换到 v5.0.2 分支
git checkout v5.0.2
```

### 2. 安装 Python 依赖

```bash
# 使用 uv 安装依赖
uv sync

# 包含开发依赖
uv sync --dev

# 查看已安装的包
uv pip list
```

### 3. 配置环境变量

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

在 `.env` 文件中添加您的 API 密钥：

```bash
# === 天气服务（必需） ===
CAIYUN_API_KEY=your_caiyun_api_key
AMAP_API_KEY=your_amap_api_key

# === LLM 服务（至少配置一个） ===
DASHSCOPE_API_KEY=your_dashscope_api_key      # 通义千问
ANTHROPIC_AUTH_TOKEN=your_anthropic_token    # 智谱AI（推荐）

# === JWT 认证（必需） ===
JWT_SECRET_KEY=your-super-secret-jwt-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# === 微信小程序配置 ===
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret
WECHAT_AUTO_CREATE_USER=true

# === OCR 配置（可选） ===
OCR_PROVIDER=ollama                              # ollama 或 siliconflow
OLLAMA_BASE_URL=http://localhost:11434          # 本地Ollama地址
OLLAMA_MODEL=deepseek-ocr                        # OCR模型
SILICONFLOW_API_KEY=your-siliconflow-api-key    # 云端OCR密钥

# === 其他配置 ===
LOG_LEVEL=INFO
VECTOR_EMBEDDING_MODEL=text-embedding-v3
VECTOR_AUTO_INDEX=true
```

### 4. 安装前端依赖

```bash
# 进入前端目录
cd apps/web-admin

# 安装依赖
npm install

# 返回项目根目录
cd ../..
```

### 5. 设置微信小程序

```bash
# 小程序目录已创建，使用微信开发者工具打开
fishing_agent_app/
```

## ⚙️ 配置说明

### 环境变量详解

#### 核心服务配置

- `CAIYUN_API_KEY`: 彩云天气 API 密钥，用于获取实时天气数据
- `AMAP_API_KEY`: 高德地图 API 密钥，用于地名解析和坐标查询

#### LLM 配置（至少配置一个）

- `DASHSCOPE_API_KEY`: 通义千问 API 密钥
  - 用于 LLM 对话和 Embedding
  - 需要开通百炼平台服务

- `ANTHROPIC_AUTH_TOKEN`: 智谱 AI API 密钥（推荐）
  - 用于 GLM-4.6 模型
  - 响应速度快，中文理解能力强

#### JWT 认证配置（必需）

- `JWT_SECRET_KEY`: JWT 签名密钥（至少32字符），生产环境必须设置
- `JWT_ALGORITHM`: JWT 算法，默认 HS256
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（分钟）

#### 微信小程序配置

- `WECHAT_APPID`: 微信小程序 AppID
- `WECHAT_SECRET`: 微信小程序 AppSecret
- `WECHAT_AUTO_CREATE_USER`: 是否自动创建新用户（默认 true）

#### OCR 配置（可选）

支持两种 OCR 提供商：

1. **Ollama 本地 OCR（推荐）**
   ```bash
   OCR_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=deepseek-ocr
   ```

2. **SiliconFlow 云端 OCR**
   ```bash
   OCR_PROVIDER=siliconflow
   SILICONFLOW_API_KEY=your-api-key
   ```

### 数据库配置

项目使用 SQLite 数据库，自动创建：
- 装备数据：`shared/data/equipment.db`
- 待审核装备：`shared/data/pending_equipment.db`
- 系统配置：`shared/data/system.db`

## 🚀 运行项目

### 方式一：CLI 应用（推荐）

```bash
# 运行交互式 CLI
uv run python main.py

# 或使用项目脚本
uv run fishing
```

### 方式二：FastAPI 服务

```bash
# 启动 API 服务器
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# 或使用项目脚本
uv run fishing-api
```

### 方式三：React 管理前端

```bash
# 进入前端目录
cd apps/web-admin

# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

### 方式四：微信小程序

```bash
# 1. 使用微信开发者工具打开 fishing_agent_app/ 目录
# 2. 在本地设置中勾选"不校验合法域名"
# 3. 修改 fishing_agent_app/utils/api.js 中的 baseURL 为本地地址
```

### 方式五：Docker 部署

```bash
# 构建镜像
docker build -t fishing-agent .

# 运行容器
docker run -p 8000:8000 -v $(pwd)/.env:/app/.env fishing-agent

# 或使用 docker-compose
docker-compose up -d
```

## ✅ 验证安装

### 1. 测试核心包导入

```bash
# 测试所有核心包
uv run python -c "
from packages.agents.fishing import create_agent
from packages.agents.equipment_import import EquipmentImportAgent
from packages.data_processing.image import BatchMergeProcessor
from packages.scraper import BaseSpider
print('✅ 所有核心包导入成功')
"
```

### 2. 测试 CLI 应用

```bash
# 运行测试命令
uv run fishing --help

# 测试对话功能
echo "明天北京钓鱼怎么样？" | uv run fishing
```

### 3. 测试 API 服务

```bash
# 健康检查
curl http://localhost:8000/health

# 测试微信登录
curl -X POST http://localhost:8000/api/v1/auth/wechat/login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_code"}'

# 预期响应
# {"access_token": "...", "user": {...}}
```

### 4. 测试 OCR 功能

```bash
# 检查 OCR 状态
curl http://localhost:8000/api/v1/ocr/status

# 测试图片识别
curl -X POST http://localhost:8000/api/v1/ocr/recognize-table \
  -H "Authorization: Bearer your-token" \
  -F "files=@test-image.jpg"
```

### 5. 测试前端访问

打开浏览器访问：
- API 文档：http://localhost:8000/docs
- React 前端：http://localhost:5173
- 管理后台：http://localhost:5173（登录后访问）

## ❓ 常见问题

### Q: 提示"未设置 API 密钥"错误

**A**: 检查 `.env` 文件是否正确配置：
```bash
# 确认文件存在
ls -la .env

# 检查密钥格式（无空格，无引号）
cat .env | grep -E "API_KEY|SECRET"
```

### Q: 模块导入错误

**A**: 确保使用 uv 运行命令：
```bash
# ✅ 正确方式
uv run python main.py

# ❌ 错误方式
python main.py
```

### Q: 微信小程序无法连接本地 API

**A**: 
1. 确保本地 API 服务已启动
2. 在微信开发者工具中关闭"不校验合法域名"
3. 检查 CORS 配置是否允许小程序域名

### Q: OCR 识别失败

**A**: 
1. 检查 OCR 提供商配置
2. 确保 Ollama 已下载 `deepseek-ocr` 模型
3. 验证 SiliconFlow API Key 是否有效

### Q: JWT Token 错误

**A**: 
1. 确保 JWT_SECRET_KEY 至少 32 字符
2. 检查 Token 是否过期
3. 验证 Token 格式：`Bearer <token>`

### Q: 数据库连接失败

**A**: 检查数据库文件权限：
```bash
# 创建数据目录
mkdir -p shared/data

# 检查权限
ls -la shared/data/
```

### Q: 前端无法连接后端

**A**: 
- 确保 API 服务在 8000 端口运行
- 检查 `apps/api/main.py` 中的 CORS 设置
- 验证 proxy 配置（如果使用）

## 🔄 OCR 功能配置

### 使用 Ollama 本地 OCR（推荐）

1. **安装 Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **下载 OCR 模型**
   ```bash
   ollama pull deepseek-ocr
   ```

3. **启动 Ollama 服务**
   ```bash
   ollama serve
   ```

4. **配置环境变量**
   ```bash
   OCR_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=deepseek-ocr
   ```

### 使用 SiliconFlow 云端 OCR

1. **注册账号**
   - 访问 [SiliconFlow](https://siliconflow.cn/)
   - 获取 API Key

2. **配置环境变量**
   ```bash
   OCR_PROVIDER=siliconflow
   SILICONFLOW_API_KEY=your-api-key
   ```

## 🏗️ 装备导入功能

### 1. 使用 Python API

```python
from packages.agents.equipment_import import EquipmentImportAgent

# 创建导入 Agent
agent = EquipmentImportAgent(
    model_provider="zhipu",
    enable_compression=True  # 启用文本压缩
)

# 提取装备信息
text = """
光威赤刃 GT602L-M 路亚竿，碳纤维材质，超轻硬设计，
适合淡水作钓，长度2.4米，自重120g，售价299元。
"""

result = agent.extract_and_save(
    text=text,
    source_type="ecommerce",
    source_url="https://example.com"
)

print(f"提取结果: {result}")
```

### 2. 使用 API 接口

```bash
# 提取装备信息
curl -X POST http://localhost:8000/api/v1/equipment/import/extract \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "光威赤刃 GT602L-M 路亚竿，价格299元",
    "source_type": "forum",
    "enable_compression": true
  }'
```

## 👤 创建管理员用户

### 使用 Python 脚本

```bash
uv run python -c "
import bcrypt
import os
from sqlalchemy import create_engine
from apps.api.auth.models import User
from shared.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

# 创建管理员用户
password = 'admin123'  # 请使用强密码
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

with engine.connect() as conn:
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=hashed_password.decode('utf-8'),
        role='admin',
        is_active=True
    )
    conn.add(admin)
    conn.commit()
    print('管理员用户创建成功')
"
```

## 🚀 生产环境部署

### 环境变量清单

生产环境需要配置的所有环境变量：

```bash
# === 核心API服务 ===
CAIYUN_API_KEY=xxx
AMAP_API_KEY=xxx
DASHSCOPE_API_KEY=xxx

# === JWT认证（必需） ===
JWT_SECRET_KEY=xxx-at-least-32-characters
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# === 微信小程序（如需要） ===
WECHAT_APPID=xxx
WECHAT_SECRET=xxx

# === OCR配置 ===
OCR_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434

# === 数据库 ===
DATABASE_URL=sqlite:///./data/app.db

# === 日志 ===
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

### Docker Compose 部署

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: fishing-agent:v5.0.2
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env:ro
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_KEEP_ALIVE=24h

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api

volumes:
  ollama_data:
```

## 📖 下一步

- 查看 [API 参考](../../05-api-reference/) 了解所有可用接口
- 阅读 [代码结构指南](./codebase-structure.md) 了解项目架构
- 浏览 [架构文档](../../03-architecture/) 理解系统设计
- 查看 [测试指南](./testing.md) 了解测试策略
- 阅读 [贡献指南](./contribution-guide.md) 参与项目开发

## 🆘 获取帮助

如果您在安装过程中遇到问题：

1. 查看 [GitHub Issues](https://github.com/yourusername/fishing-agent/issues)
2. 提交新的 Issue，包含：
   - 错误信息
   - 操作系统信息
   - Python/Node.js 版本
   - 相关配置（去除敏感信息）

---

祝您开发愉快！🎣

## 版本更新说明

### v5.0.2 新增功能

- ✨ 微信小程序支持
- ✨ 装备导入 Agent（文本压缩 + 批量提取）
- ✨ OCR 多提供商（Ollama 本地 + SiliconFlow 云端）
- ✨ 智能图片合并系统
- ✨ 完善的 JWT 认证和权限管理

### 升级指南

从 v5.0.1 升级：

1. 拉取最新代码
   ```bash
   git pull origin v5.0.2
   ```

2. 更新依赖
   ```bash
   uv sync
   ```

3. 更新环境变量（添加微信小程序配置）
   ```bash
   # 添加到 .env
   WECHAT_APPID=xxx
   WECHAT_SECRET=xxx
   OCR_PROVIDER=ollama
   ```

4. 运行数据库迁移（如需要）
   ```bash
   uv run alembic upgrade head
   ```

---

**指南版本**: v5.0.2  
**适用系统版本**: v5.0.2+  
**更新时间**: 2024-12-20