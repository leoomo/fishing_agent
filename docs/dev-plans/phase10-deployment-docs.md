# Phase 10: 文档与部署详细方案

**目标**: 完善文档和生产部署
**周期**: 第 12 周（5 个工作日）
**优先级**: P0（上线准备）

---

## 目标概述

完成项目文档、部署配置和生产环境准备，确保系统可以顺利上线。

**核心任务**:
- 更新 README 和快速开始指南
- 编写 API 文档（Swagger）
- 编写用户手册和开发者文档
- 配置 Docker 部署
- 数据库迁移方案
- 监控告警配置

---

## Day 1: 更新项目文档

### Step 1: 更新 README

**文件**: `README.md`

```markdown
# 智能钓鱼助手 v3.2.0

模块化 Agent 架构 + Web 管理后台，基于 LangChain 1.0+ 和 7 因子科学评分系统。

## 功能特性

### 核心功能
- 🎣 智能钓鱼推荐（7因子评分：温度/天气/风力/气压/湿度/季节/月相）
- 🛠️ 装备查询和推荐（4因子评分：价格/规格/品牌/用户水平）
- 🌤️ 实时天气查询（彩云天气 API）
- 📍 地理编码（高德地图 API）
- 🤖 多模型支持（通义千问、智谱AI、OpenAI、豆包）

### 管理后台
- 📊 装备数据管理（CRUD、批量导入导出）
- 👥 用户管理（用户列表、装备库、钓鱼记录）
- 📚 内容管理（鱼类、钓组、拟饵知识库）
- 🕷️ 爬虫管理（淘宝/京东数据采集）
- 📈 系统监控（API/LLM 统计、性能监控）
- 📊 数据分析（装备统计、用户行为、业务报表）
- ⚙️ 配置管理（Agent/算法/API 密钥）

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- SQLite 3.x（开发）/ PostgreSQL 14+（生产）

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/fishing_agent.git
cd fishing_agent

# 安装 Python 依赖（使用 uv）
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API 密钥
```

### 配置环境变量

```bash
# 必需配置
CAIYUN_API_KEY=your_caiyun_key           # 彩云天气 API
AMAP_API_KEY=your_amap_key               # 高德地图 API
DASHSCOPE_API_KEY=your_dashscope_key     # 通义千问 API

# 可选配置
ZHIPU_API_KEY=your_zhipu_key             # 智谱AI API
OPENAI_API_KEY=your_openai_key           # OpenAI API

# 管理后台配置
JWT_SECRET_KEY=your_secret_key           # JWT 密钥（生产环境必须更换）
CONFIG_ENCRYPTION_KEY=your_encryption_key # 配置加密密钥
```

### 运行

#### 运行 CLI Agent

```bash
# 交互模式
uv run python main.py

# 直接查询
uv run python debug_agent.py qwen direct "明天杭州钓鱼怎么样？"

# 查看帮助
uv run python debug_agent.py --help
```

#### 运行 API 服务

```bash
# 启动 FastAPI 后端
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# 访问 API 文档
open http://localhost:8000/docs
```

#### 运行 Web 管理后台

```bash
# 安装前端依赖
cd apps/web-admin
npm install

# 启动开发服务器
npm run dev

# 访问
open http://localhost:5173

# 默认账户
# 用户名: admin
# 密码: admin123
```

## 项目结构

```
fishing_agent/
├── packages/agent_fishing/     # Agent 核心包
│   ├── core/                   # Agent、模型、中间件
│   ├── tools/                  # 工具集（天气、钓鱼、装备）
│   └── utils/                  # 工具函数
├── apps/                       # 应用
│   ├── api/                    # FastAPI 后端
│   │   ├── routes/            # API 路由
│   │   ├── schemas/           # Pydantic Schema
│   │   └── services/          # 业务逻辑
│   └── web-admin/             # React 前端
│       ├── src/
│       │   ├── api/           # API 客户端
│       │   ├── components/    # 组件
│       │   ├── pages/         # 页面
│       └── └── store/         # Redux 状态管理
├── docs/                       # 文档
│   ├── dev-plans/             # 开发计划
│   ├── api/                   # API 文档
│   └── user-guide/            # 用户手册
└── scripts/                    # 脚本
    └── create_admin.py        # 创建管理员
```

## 数据库迁移

### 初始化数据库

```bash
cd packages/agent_fishing/tools/lure

# 初始化 Alembic
alembic init alembic

# 生成初始迁移
alembic revision --autogenerate -m "initial migration"

# 应用迁移
alembic upgrade head
```

### 创建管理员账户

```bash
# 交互式创建
uv run python scripts/create_admin.py

# 命令行创建
uv run python scripts/create_admin.py \
  --username admin \
  --password your_password \
  --email admin@example.com
```

## 部署

### Docker 部署（推荐）

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动部署

详见 [部署文档](docs/deployment.md)

## 开发

### 运行测试

```bash
# 后端测试
uv run pytest tests/ -v --cov

# 前端测试
cd apps/web-admin
npm run test
```

### 代码规范

```bash
# Python 格式化
uv run ruff format .

# Python 检查
uv run ruff check .

# TypeScript 检查
cd apps/web-admin
npm run lint
```

## 文档

- [开发文档](docs/development.md)
- [API 文档](docs/api/README.md)
- [用户手册](docs/user-guide/README.md)
- [部署指南](docs/deployment.md)

## 常见问题

### Q: 如何更换 LLM 提供商？

A: 修改 `.env` 文件中的 API 密钥，或在管理后台「配置管理」中切换。

### Q: 如何添加新的装备数据？

A: 登录管理后台，进入「装备管理」页面，点击「新增装备」或使用批量导入功能。

### Q: 如何备份数据库？

A: SQLite: `cp equipment.db equipment.db.backup`
   PostgreSQL: `pg_dump fishing_agent > backup.sql`

## 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md)。

## 许可证

MIT License

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/your-org/fishing_agent/issues)
- 邮箱: support@example.com
```

---

## Day 2: API 文档

### Step 2: 配置 Swagger 文档

**文件**: `apps/api/main.py`

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="智能钓鱼助手 API",
    version="3.2.0",
    description="""
# 智能钓鱼助手 REST API

基于 LangChain 的智能钓鱼助手管理后台 API。

## 功能模块

- **认证**: JWT token 认证
- **装备管理**: CRUD 装备、品牌、导入导出
- **用户管理**: 用户列表、装备库、钓鱼记录
- **内容管理**: 鱼类、钓组、拟饵知识库
- **爬虫管理**: 任务管理、实时监控
- **系统监控**: API/LLM 统计、性能监控
- **数据分析**: 装备统计、用户行为、报表
- **配置管理**: Agent/算法/API 密钥

## 认证

所有需要认证的端点都需要在 Header 中携带 JWT token:

```
Authorization: Bearer <your_token>
```

获取 token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"username": "admin", "password": "admin123"}'
```

## 权限

- **Admin**: 所有权限
- **Editor**: 创建、读取、更新（不能删除）
- **ReadOnly**: 仅读取

## 分页

列表接口支持分页参数:

- `page`: 页码（从 1 开始）
- `page_size`: 每页数量（最大 100）

响应格式:

```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [...]
}
```

## 错误处理

HTTP 状态码:

- `200`: 成功
- `201`: 创建成功
- `204`: 删除成功（无内容）
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器错误

错误响应格式:

```json
{
  "detail": "错误信息"
}
```
    """,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # 添加认证配置
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # 添加全局安全要求
    openapi_schema["security"] = [{"bearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
```

**访问文档**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Day 3: 用户手册和开发文档

### Step 3: 用户手册

**文件**: `docs/user-guide/README.md`

```markdown
# 智能钓鱼助手 - 用户手册

## 目录

1. [快速开始](#快速开始)
2. [登录系统](#登录系统)
3. [装备管理](#装备管理)
4. [用户管理](#用户管理)
5. [内容管理](#内容管理)
6. [爬虫管理](#爬虫管理)
7. [系统监控](#系统监控)
8. [数据分析](#数据分析)
9. [配置管理](#配置管理)
10. [常见问题](#常见问题)

## 快速开始

### 访问系统

1. 打开浏览器，访问: `http://your-domain.com`
2. 使用管理员账户登录

### 首次登录

默认管理员账户:
- 用户名: `admin`
- 密码: `admin123`

⚠️ **安全提示**: 首次登录后请立即修改密码！

## 登录系统

### 登录步骤

1. 在登录页面输入用户名和密码
2. 点击「登录」按钮
3. 登录成功后自动跳转到装备管理页面

### 忘记密码

联系系统管理员重置密码。

## 装备管理

### 查看装备列表

1. 点击左侧菜单「装备管理」
2. 使用筛选条件缩小范围:
   - 类别: 鱼竿/渔轮/鱼线/拟饵/套装
   - 关键词搜索: 输入装备名称
3. 点击表格列头可排序

### 新增装备

1. 点击右上角「新增装备」按钮
2. 填写装备基本信息:
   - 装备名称（必填）
   - 类别（必填）
   - 品牌（必填）
   - 型号
   - 价格范围
   - 描述
   - 特点
   - 适用水平
3. 根据类别填写规格信息:
   - **鱼竿**: 长度、调性、动作、适用饵重
   - **渔轮**: 速比、轴承数、拽力、线容量
   - **鱼线**: 线型、线径、拉力值
   - **拟饵**: 类型、重量、长度、潜深
4. 点击「保存」按钮

### 编辑装备

1. 在装备列表中找到要编辑的装备
2. 点击「编辑」按钮
3. 修改装备信息
4. 点击「保存」按钮

### 删除装备

1. 在装备列表中找到要删除的装备
2. 点击「删除」按钮
3. 在确认对话框中点击「确定」

⚠️ **注意**: 删除操作不可恢复，请谨慎操作！

### 批量导入

1. 点击「导入」按钮
2. 选择 CSV 文件
3. 系统会自动解析并验证数据
4. 查看导入结果（成功数、失败数、错误详情）

**CSV 格式要求**:

```csv
name,category,brand_name,model,price_min,price_max,description,features,user_level
DOOP 路亚竿,鱼竿,DOOP,Warrior,199,299,轻量化设计,高碳素材质,新手
```

### 导出数据

1. 设置筛选条件（可选）
2. 点击「导出」按钮
3. 选择导出格式（CSV/JSON）
4. 浏览器会自动下载文件

## 用户管理

### 查看用户列表

1. 点击左侧菜单「用户管理」
2. 查看所有注册用户
3. 使用筛选条件:
   - 用户水平: 新手/进阶/高手
   - 钓龄

### 查看用户详情

1. 点击用户列表中的用户
2. 查看用户详细信息:
   - 基础信息: 用户名、昵称、邮箱、用户水平、钓龄
   - 装备库: 用户拥有的装备列表
   - 钓鱼记录: 用户的钓鱼日志
   - 统计信息: 装备总数、总花费、收藏数

## 内容管理

### 鱼类管理

1. 点击左侧菜单「内容管理」→「鱼类管理」
2. 可以添加、编辑、删除鱼类信息
3. 管理鱼类知识库条目

### 钓组管理

1. 点击左侧菜单「内容管理」→「钓组管理」
2. 管理钓组类型和规格
3. 添加钓组配件信息

### 拟饵管理

1. 点击左侧菜单「内容管理」→「拟饵管理」
2. 管理拟饵类型
3. 配置鱼竿-拟饵兼容性矩阵

## 爬虫管理

### 查看爬虫任务

1. 点击左侧菜单「爬虫管理」
2. 查看所有爬虫任务列表
3. 查看任务状态:
   - 待处理（pending）
   - 运行中（running）
   - 成功（success）
   - 失败（failed）

### 手动触发爬虫

1. 点击「触发任务」按钮
2. 选择任务类型:
   - 淘宝爬虫
   - 京东爬虫
   - 论坛爬虫
3. 配置爬虫参数:
   - 搜索关键词
   - 最大爬取页数
   - 代理服务器（可选）
4. 点击「开始」按钮

### 实时监控任务进度

1. 点击任务列表中的「查看详情」
2. 系统会实时显示爬取进度
3. 查看成功数、失败数、错误日志

### 重试失败任务

1. 找到失败的任务
2. 点击「重试」按钮
3. 系统会创建新任务重新执行

## 系统监控

### API 调用统计

1. 点击左侧菜单「系统监控」
2. 查看 API 统计数据:
   - 总调用量
   - 平均响应时间
   - 错误率
   - Top 10 端点

### LLM 使用统计

1. 查看 LLM 统计数据:
   - 总调用次数
   - Token 消耗
   - 成本统计
   - 成功率
2. 按提供商查看（通义千问、智谱AI、OpenAI）

### 数据库性能

1. 查看数据库性能指标:
   - 平均查询时间
   - 慢查询数量
   - 连接池状态
   - 表大小统计

### 实时监控

1. 点击「实时监控」标签
2. 系统会实时推送:
   - 每分钟 API 调用量
   - 每分钟 LLM Token 消耗
   - 错误率变化

## 数据分析

### 装备数据统计

1. 点击左侧菜单「数据分析」
2. 查看装备统计:
   - 装备总数
   - 品牌总数
   - 平均价格
   - 价格分布直方图
   - Top 10 品牌
   - 按类别统计

### 装备数量趋势

1. 点击「装备趋势」标签
2. 查看按月统计的装备新增趋势
3. 按类别查看趋势

### 用户行为分析

1. 点击「用户行为」标签
2. 查看用户活跃度
3. 查看查询热点
4. 查看用户留存率

### 生成报表

1. 点击「报表生成」按钮
2. 选择报表类型:
   - 周报
   - 月报
   - 自定义
3. 选择时间范围
4. 点击「生成」按钮
5. 查看报表内容（Markdown 格式）

## 配置管理

### Agent 配置

1. 点击左侧菜单「配置管理」→「Agent 配置」
2. 修改模型配置:
   - 模型提供商（qwen/zhipu/openai/doubao）
   - 模型名称
   - 超时时间
3. 编辑提示词模板
4. 管理工具开关（启用/禁用特定工具）

### 推荐算法参数

1. 点击「推荐算法」标签
2. 调整评分权重:
   - 价格权重
   - 规格权重
   - 品牌权重
   - 用户水平权重
3. 设置筛选阈值
4. 设置推荐数量上限

### API 密钥管理

1. 点击「API 密钥」标签
2. 查看和编辑 API 密钥:
   - 通义千问 API
   - 彩云天气 API
   - 高德地图 API
3. 点击「测试」按钮验证密钥有效性
4. 点击「保存」按钮

⚠️ **安全提示**: API 密钥加密存储，显示时部分隐藏。

## 常见问题

### Q: 登录提示"用户名或密码错误"？

A: 请检查用户名和密码是否正确。如果忘记密码，联系系统管理员重置。

### Q: 导入 CSV 失败？

A: 请检查 CSV 格式是否正确，特别注意:
- 文件编码必须是 UTF-8
- 必填字段不能为空
- 品牌名称必须存在（或系统会自动创建）

### Q: 爬虫任务一直处于"运行中"状态？

A: 可能是爬虫进程异常退出。请检查爬虫日志，或手动停止任务后重试。

### Q: 如何提高推荐准确率？

A: 调整推荐算法参数，增加规格权重和品牌权重，降低价格权重。

### Q: 系统响应慢？

A: 可能是数据量过大。建议:
- 使用筛选条件缩小查询范围
- 定期清理历史数据
- 联系系统管理员优化数据库

### Q: 如何备份数据？

A: 数据库备份方法:
- SQLite: 直接复制 `equipment.db` 文件
- PostgreSQL: 使用 `pg_dump` 命令

### Q: 如何联系技术支持？

A: 发送邮件至: support@example.com
```

### Step 4: 开发者文档

**文件**: `docs/development.md`

```markdown
# 开发者文档

## 开发环境设置

### 必需工具

- Python 3.10+
- Node.js 18+
- Git
- SQLite 3.x / PostgreSQL 14+

### 安装依赖

```bash
# Python 依赖
uv sync

# 前端依赖
cd apps/web-admin
npm install
```

## 项目架构

### 后端架构

```
apps/api/
├── routes/          # API 路由
├── schemas/         # Pydantic Schema
├── services/        # 业务逻辑层
├── middleware/      # 中间件
├── auth/            # 认证授权
└── utils/           # 工具函数

packages/agent_fishing/tools/lure/
├── models/          # SQLAlchemy 模型
├── orm/             # ORM 仓库层
│   ├── session.py
│   ├── repository.py
│   └── repositories/
└── alembic/         # 数据库迁移
```

**分层设计**:
```
Route → Service → Repository → Model → Database
```

### 前端架构

```
apps/web-admin/src/
├── api/             # API 客户端
│   ├── client.ts    # Axios 实例
│   └── services/    # API 服务封装
├── store/           # Redux 状态管理
│   ├── store.ts
│   └── slices/
├── components/      # 组件
├── pages/           # 页面
└── utils/           # 工具函数
```

## 开发规范

### Python 代码规范

使用 `ruff` 进行格式化和检查:

```bash
# 格式化
uv run ruff format .

# 检查
uv run ruff check .

# 修复
uv run ruff check --fix .
```

**命名规范**:
- 类名: `PascalCase`
- 函数名: `snake_case`
- 常量: `UPPER_SNAKE_CASE`
- 私有成员: `_leading_underscore`

### TypeScript 代码规范

使用 ESLint 检查:

```bash
cd apps/web-admin
npm run lint
```

**命名规范**:
- 组件: `PascalCase`
- 函数: `camelCase`
- 常量: `UPPER_SNAKE_CASE`
- 接口: `IPascalCase` 或 `PascalCase`

### Git 提交规范

使用 Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**type**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**:
```
feat(equipment): 添加装备批量导入功能

- 支持 CSV 格式导入
- 自动解析品牌名称
- 返回导入结果统计

Closes #123
```

## 添加新功能

### 添加新的 API 端点

1. **创建 Schema** (`apps/api/schemas/xxx.py`)
2. **创建 Service** (`apps/api/services/xxx_service.py`)
3. **创建 Route** (`apps/api/routes/xxx.py`)
4. **注册路由** (`apps/api/main.py`)
5. **编写测试** (`tests/test_xxx.py`)

### 添加新的前端页面

1. **创建 API Service** (`src/api/services/xxx.ts`)
2. **创建 Redux Slice**（如需要）(`src/store/slices/xxxSlice.ts`)
3. **创建页面组件** (`src/pages/Xxx/`)
4. **添加路由** (`src/App.tsx`)

## 数据库迁移

### 生成迁移

```bash
cd packages/agent_fishing/tools/lure
alembic revision --autogenerate -m "描述"
```

### 应用迁移

```bash
alembic upgrade head
```

### 回滚迁移

```bash
alembic downgrade -1
```

## 测试

### 运行后端测试

```bash
# 所有测试
uv run pytest tests/ -v

# 特定测试
uv run pytest tests/test_models.py -v

# 覆盖率报告
uv run pytest tests/ --cov --cov-report=html
```

### 运行前端测试

```bash
cd apps/web-admin
npm run test
```

## 调试

### 后端调试

使用 VS Code 调试配置:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "apps.api.main:app",
        "--reload"
      ],
      "jinja": true
    }
  ]
}
```

### 前端调试

使用 Chrome DevTools 或 VS Code 调试。

## 常见问题

### Q: 如何添加新的数据库表？

A:
1. 在 `models/` 目录创建新模型
2. 生成 Alembic 迁移
3. 应用迁移
4. 创建对应的 Repository

### Q: 如何添加新的权限？

A: 在 `apps/api/auth/permissions.py` 中:
1. 添加新的 `PermissionEnum`
2. 更新 `ROLE_PERMISSIONS` 映射

### Q: 前端如何调用新的 API？

A:
1. 在 `src/api/services/` 创建 API 函数
2. 在组件中 import 并调用
3. 使用 Redux（如需要）

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request
```

---

## Day 4: Docker 部署配置

### Step 5: Docker 配置

**文件**: `Dockerfile`

```dockerfile
# 后端 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY apps/api/ apps/api/

# 安装依赖
RUN uv sync --no-dev

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**文件**: `apps/web-admin/Dockerfile`

```dockerfile
# 前端 Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**文件**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: fishing_agent
      POSTGRES_USER: fishing_admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  # 后端 API
  backend:
    build: .
    environment:
      DB_TYPE: postgresql
      DB_USER: fishing_admin
      DB_PASSWORD: ${DB_PASSWORD}
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: fishing_agent
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      CONFIG_ENCRYPTION_KEY: ${CONFIG_ENCRYPTION_KEY}
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
      CAIYUN_API_KEY: ${CAIYUN_API_KEY}
      AMAP_API_KEY: ${AMAP_API_KEY}
    depends_on:
      - postgres
    ports:
      - "8000:8000"
    restart: unless-stopped

  # 前端
  frontend:
    build: ./apps/web-admin
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

**文件**: `.env.production`

```bash
# 数据库
DB_PASSWORD=your_secure_password

# JWT
JWT_SECRET_KEY=your_jwt_secret_key_here
CONFIG_ENCRYPTION_KEY=your_encryption_key_here

# API 密钥
DASHSCOPE_API_KEY=your_dashscope_key
CAIYUN_API_KEY=your_caiyun_key
AMAP_API_KEY=your_amap_key
```

---

## Day 5: 部署和监控

### Step 6: 生产部署

**部署步骤**:

```bash
# 1. 克隆代码
git clone https://github.com/your-org/fishing_agent.git
cd fishing_agent

# 2. 配置环境变量
cp .env.production .env
vim .env  # 修改为实际值

# 3. 构建并启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 应用数据库迁移
docker-compose exec backend uv run alembic upgrade head

# 6. 创建管理员
docker-compose exec backend uv run python scripts/create_admin.py

# 7. 验证部署
curl http://localhost:8000/health
```

### Step 7: 监控配置（可选）

**Prometheus + Grafana 监控**:

**文件**: `docker-compose.monitoring.yml`

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

---

## 验收标准

### 必须完成

- ✅ README 更新完整
- ✅ API 文档（Swagger）可访问
- ✅ 用户手册编写完成
- ✅ 开发者文档编写完成
- ✅ Docker 配置可用
- ✅ docker-compose 一键部署成功
- ✅ 数据库迁移脚本完整
- ✅ 生产环境部署成功
- ✅ 健康检查端点正常

### 可选优化

- 🔧 Kubernetes 部署配置
- 🔧 CI/CD 流程（GitHub Actions）
- 🔧 Prometheus + Grafana 监控
- 🔧 ELK 日志收集
- 🔧 备份恢复方案

---

## 项目完成！

🎉 恭喜！智能钓鱼助手管理后台开发完成！

**项目统计**:
- 开发周期: 12 周
- 后端文件: ~60 个
- 前端文件: ~50 个
- 数据库表: 23 张
- API 端点: ~80 个
- 前端页面: ~30 个
- 测试覆盖率: 70%+

**下一步**:
1. 持续监控系统运行状态
2. 收集用户反馈
3. 迭代优化功能
4. 添加新特性
