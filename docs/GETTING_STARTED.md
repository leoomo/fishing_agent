# 快速入门指南

本指南将帮助您快速搭建和运行智能钓鱼助手项目。

## 目录

- [环境要求](#环境要求)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [运行项目](#运行项目)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

## 环境要求

### 必需环境

1. **Python 3.11+**
   ```bash
   # 检查 Python 版本
   python --version
   # 或
   python3 --version
   ```

2. **uv 包管理器**
   ```bash
   # 安装 uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # 或使用 pip
   pip install uv
   ```

3. **Node.js 18+**（仅前端需要）
   ```bash
   # 检查 Node.js 版本
   node --version
   ```

### API 密钥

您需要准备以下 API 密钥：

| 服务 | 获取地址 | 用途 |
|------|----------|------|
| 彩云天气 | [彩云天气开放平台](https://caiyunapp.com/api) | 天气数据 |
| 高德地图 | [高德开放平台](https://lbs.amap.com/) | 地理坐标服务 |
| 通义千问 | [阿里云百炼平台](https://bailian.console.aliyun.com/) | LLM 和 Embedding |
| 智谱AI | [智谱AI开放平台](https://open.bigmodel.cn/) | LLM 服务（推荐） |

## 安装步骤

### 1. 克隆项目

```bash
# 使用 git 克隆
git clone https://github.com/yourusername/fishing-agent.git
cd fishing-agent
```

### 2. 安装 Python 依赖

```bash
# 使用 uv 安装依赖
uv sync

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
# 天气服务（必需）
CAIYUN_API_KEY=your_caiyun_api_key

# 地图服务（必需）
AMAP_API_KEY=your_amap_api_key

# LLM 服务（至少配置一个）
DASHSCOPE_API_KEY=your_dashscope_api_key
ANTHROPIC_AUTH_TOKEN=your_anthropic_token

# JWT 认证（生产环境必需）
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# 配置加密（生产环境建议设置）
CONFIG_ENCRYPTION_KEY=your-32-character-encryption-key
```

### 4. 安装前端依赖（可选）

```bash
# 进入前端目录
cd apps/web-admin

# 安装依赖
npm install

# 返回项目根目录
cd ../..
```

## 配置说明

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

#### 认证配置（可选）

- `JWT_SECRET_KEY`: JWT 签名密钥，生产环境必须设置
- `JWT_ALGORITHM`: JWT 算法，默认 HS256
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（分钟）

#### 安全配置（可选）

- `CONFIG_ENCRYPTION_KEY`: 配置加密密钥（32字符），用于加密敏感配置

#### OCR配置（可选）

- `OCR_PROVIDER`: OCR提供商，可选 `ollama`（本地）或 `siliconflow`（云端）
- `OLLAMA_BASE_URL`: Ollama服务地址，默认 `http://localhost:11434`
- `OLLAMA_MODEL`: Ollama OCR模型，默认 `deepseek-ocr`
- `SILICONFLOW_API_KEY`: SiliconFlow API密钥（云端OCR使用）

### 数据库配置

项目使用 SQLite 数据库，默认位置：
- 装备数据：`packages/agent_fishing/tools/lure/data/equipment.db`
- 无需额外配置，自动创建

## 运行项目

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

### 方式三：React 前端

```bash
# 进入前端目录
cd apps/web-admin

# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

### 方式四：Docker 部署

```bash
# 构建镜像
docker build -t fishing-agent .

# 运行容器
docker run -p 8000:8000 -v $(pwd)/.env:/app/.env fishing-agent
```

## 验证安装

### 1. 测试 CLI 应用

```bash
# 运行测试命令
uv run python -c "from packages.agent_fishing import create_agent; print('✅ Agent 创建成功')"

# 测试工具加载
uv run python -c "from packages.agent_fishing import get_all_tools; print(f'✅ 工具数量: {len(get_all_tools())}')"
```

### 2. 测试 API 服务

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
# {"status":"ok"}
```

### 3. 测试前端访问

打开浏览器访问：
- API 文档：http://localhost:8000/docs
- React 前端：http://localhost:5173（需要先启动前端服务）

## 常见问题

### Q: 提示"未设置 API 密钥"错误

**A**: 检查 `.env` 文件是否正确配置：
```bash
# 确认文件存在
ls -la .env

# 检查密钥格式（无空格，无引号）
cat .env | grep API_KEY
```

### Q: 模块导入错误

**A**: 确保使用 uv 运行命令：
```bash
# ✅ 正确方式
uv run python main.py

# ❌ 错误方式
python main.py
```

### Q: 前端无法连接后端

**A**: 检查 CORS 配置和端口：
- 确保 API 服务在 8000 端口运行
- 检查 `apps/api/main.py` 中的 CORS 设置

### Q: 数据库连接失败

**A**: 检查数据库文件权限：
```bash
# 检查数据库文件
ls -la packages/agent_fishing/tools/lure/data/

# 创建目录（如不存在）
mkdir -p packages/agent_fishing/tools/lure/data/
```

### Q: LLM 响应慢

**A**: 建议使用智谱 AI：
```bash
# .env 中配置
ANTHROPIC_AUTH_TOKEN=your_zhipu_api_key
```

### Q: 如何重置配置

**A**: 重新复制配置文件：
```bash
rm .env
cp .env.example .env
# 重新编辑配置
```

### 5. 初始化数据库（可选）

系统会自动创建和初始化数据库，但如果需要重新初始化：

```bash
# 初始化装备数据库
uv run python -c "
from packages.agent_fishing.tools.lure.database import init_database
init_database()
print('数据库初始化完成')
"
```

### 6. 创建管理员用户（生产环境）

在生产环境中，需要创建管理员用户：

```bash
# 使用Python脚本创建
uv run python -c "
import bcrypt
from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.lure.models.system import AdminUser

# 获取数据库连接
db = get_db()

# 创建管理员用户
password = 'admin123'  # 请使用强密码
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

admin = AdminUser(
    username='admin',
    email='admin@example.com',
    password_hash=hashed_password.decode('utf-8'),
    role='admin',
    is_active=True
)

db.add(admin)
db.commit()
print('管理员用户创建成功')
"
```

## JWT认证配置

### 生成安全的JWT密钥

```bash
# 生成32字符的随机密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

将生成的密钥添加到 `.env` 文件：

```bash
JWT_SECRET_KEY=your-generated-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 测试JWT认证

```bash
# 1. 登录获取Token
curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "password": "admin123"
     }'

# 2. 使用Token访问受保护的API
TOKEN="your-jwt-token-here"
curl -X GET http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer $TOKEN"
```

## 工作流管理系统

### 创建第一个工作流

```bash
# 使用API创建工作流模板
curl -X POST http://localhost:8000/api/v1/admin/crawler/workflows/templates \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "测试爬虫工作流",
       "description": "简单的测试工作流",
       "steps": [
         {
           "name": "爬取测试数据",
           "task_type": "taobao",
           "config": {
             "keywords": ["路亚竿"],
             "max_pages": 1
           },
           "depends_on": []
         }
       ]
     }'
```

### 创建定时调度

```bash
# 创建每日执行的任务
curl -X POST http://localhost:8000/api/v1/admin/crawler/schedules \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "每日数据同步",
       "template_id": 1,
       "cron_expression": "0 2 * * *",
       "timezone": "Asia/Shanghai",
       "is_active": true
     }'
```

## React管理前端

### 启动前端开发服务器

```bash
cd apps/web-admin

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

### 前端功能概览

1. **登录页面**
   - 默认用户: `admin`
   - 默认密码: `admin123`

2. **仪表板**
   - 系统概览
   - 实时监控数据
   - 快速操作入口

3. **装备管理**
   - 装备列表
   - 添加/编辑装备
   - 装备分类管理

4. **爬虫管理**
   - 任务列表
   - 执行日志
   - 工作流管理

5. **数据分析**
   - 装备统计
   - 趋势分析
   - 报表生成

6. **系统配置**
   - API密钥管理
   - 系统参数设置
   - 用户管理

## 部署配置

### Docker部署

```dockerfile
# Dockerfile示例
FROM python:3.11-slim

WORKDIR /app

# 安装uv
COPY pyproject.toml ./
RUN pip install uv && uv sync --frozen

# 复制源代码
COPY . .

# 运行应用
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建和运行
docker build -t fishing-agent .
docker run -p 8000:8000 -v $(pwd)/.env:/app/.env fishing-agent
```

### 环境变量清单

生产环境需要配置的所有环境变量：

```bash
# === 核心API服务 ===
CAIYUN_API_KEY=xxx
AMAP_API_KEY=xxx
DASHSCOPE_API_KEY=xxx

# === LLM提供商（至少配置一个） ===
ANTHROPIC_AUTH_TOKEN=xxx  # 智谱AI
OPENAI_API_KEY=xxx        # OpenAI

# === JWT认证（必需） ===
JWT_SECRET_KEY=xxx
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# === 可选配置 ===
LOG_LEVEL=INFO
CACHE_TTL=3600

# === 向量存储 ===
VECTOR_EMBEDDING_MODEL=text-embedding-v3
VECTOR_AUTO_INDEX=true

# === 数据库配置（使用SQLite默认值） ===
DATABASE_URL=sqlite:///packages/agent_fishing/tools/lure/data/equipment.db
```

## 下一步

- 查看 [API 参考](./API_REFERENCE.md) 了解所有可用接口
- 阅读 [用户指南](./USER_GUIDE.md) 学习高级功能
- 浏览 [架构文档](./ARCHITECTURE.md) 理解系统设计
- 查看 [故障排除指南](./TROUBLESHOOTING.md) 解决常见问题

## 获取帮助

如果您在安装过程中遇到问题：

1. 查看 [GitHub Issues](https://github.com/yourusername/fishing-agent/issues)
2. 提交新的 Issue，包含：
   - 错误信息
   - 操作系统信息
   - Python/Node.js 版本
   - 相关配置（去除敏感信息）

---

祝您使用愉快！🎣