# 🚀 智能钓鱼助手开发指南

> 完整的12周开发计划和实施指南

## 📋 项目概述

智能钓鱼助手是一个基于LangChain 1.0+的智能钓鱼推荐系统，采用模块化Agent架构，提供钓鱼时间推荐、装备管理、天气分析等核心功能。

### 技术栈
- **后端**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **AI框架**: LangChain 1.0+, 多LLM支持（通义千问、智谱AI、OpenAI）
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **认证**: JWT + RBAC权限系统
- **前端**: React 19.2.0 + TypeScript + Ant Design 5.22.0 + Vite 7.2.4
- **状态管理**: Redux Toolkit + React Router 6.28.0
- **数据可视化**: ECharts 5.5.0
- **部署**: Docker, Docker Compose

## 🗺️ 开发路线图

### Phase 1: 数据库ORM层 ✅ 已完成
**周期**: 第1-2周 | **优先级**: P0

#### 核心任务
- [x] SQLAlchemy模型定义（23张表）
- [x] Repository模式实现
- [x] Alembic数据库迁移
- [x] 多数据库支持（SQLite/PostgreSQL/MySQL）

#### 关键文件
```
packages/agent_fishing/tools/lure/
├── models/           # SQLAlchemy模型
├── orm/             # ORM会话和Repository
├── migrations/      # Alembic迁移
└── data/           # 数据库文件
```

#### 验收标准
- ✅ 所有模型定义完成
- ✅ Repository CRUD操作正常
- ✅ Alembic迁移成功
- ✅ 测试覆盖率 > 80%

---

### Phase 2: 认证授权 + 中间件 ✅ 已完成
**周期**: 第3周 | **优先级**: P0

#### 核心任务
- [x] JWT Token认证系统
- [x] RBAC权限管理（Admin/Editor/ReadOnly）
- [x] API日志中间件
- [x] LLM调用监控
- [x] 首个Admin用户创建

#### 关键特性
- **JWT认证**: 30分钟token过期，bcrypt密码哈希
- **权限系统**: 30+细粒度权限控制
- **监控中间件**: 自动记录API调用和LLM使用
- **安全最佳实践**: 防时序攻击、Token验证

#### 关键文件
```
apps/api/
├── auth/           # JWT认证核心
│   ├── jwt.py     # Token生成验证
│   ├── permissions.py  # 权限定义
│   └── dependencies.py  # FastAPI依赖
├── middleware/     # 中间件
│   └── api_logger.py  # API日志
└── routes/
    └── auth.py    # 认证端点
```

---

### Phase 3: 核心管理模块API ✅ 已完成
**周期**: 第4-5周 | **优先级**: P1

#### Week 4: 装备 + 用户管理
- [x] 装备CRUD API（创建/查询/更新/删除）
- [x] 品牌管理API
- [x] 用户管理API（列表/详情/装备库）
- [x] 导入导出功能（CSV/JSON）

#### Week 5: 内容管理
- [x] 鱼类知识管理API
- [x] 钓组配置管理API
- [x] 拟饵类型管理API

#### API设计原则
- RESTful设计规范
- 分页和筛选支持
- 权限控制集成
- 详细的API文档

---

### Phase 4: 爬虫 + 监控模块 ✅ 已完成
**周期**: 第6周 | **优先级**: P1

#### 核心功能
- [x] 多平台爬虫（淘宝/京东/论坛）
- [x] 反爬虫策略（UA轮换/延迟/重试）
- [x] 数据去重算法
- [x] 爬虫任务管理
- [x] WebSocket实时推送

#### 监控系统
- [x] API性能监控
- [x] LLM使用统计
- [x] 错误追踪
- [x] 告警机制
- [x] 系统健康检查

---

### Phase 5: 数据分析与配置 ✅ 已完成
**周期**: 第7周 | **优先级**: P1

#### 数据分析
- [x] 装备统计分析
- [x] 用户行为分析
- [x] 业务报表生成
- [x] 数据可视化

#### 配置管理
- [x] 动态配置系统
- [x] API密钥管理
- [x] 算法参数调整
- [x] 配置版本控制

---

### Phase 6-8: 前端开发 ✅ 已完成
**周期**: 第8-10周 | **优先级**: P1

#### 技术栈
- **框架**: React 19.2.0 + TypeScript
- **状态管理**: Redux Toolkit
- **UI组件**: Ant Design 5.22.0
- **图表**: ECharts 5.5.0
- **构建**: Vite 7.2.4

#### 核心页面
- [x] 登录/认证页面
- [x] 装备管理（列表/详情/编辑）
- [x] 用户管理
- [x] 内容管理
- [x] 爬虫管理
- [x] 数据分析仪表板
- [x] 系统配置

---

### Phase 9: 测试与优化 📋 规划中
**周期**: 第11周 | **优先级**: P1

#### 测试策略
- **后端测试**:
  - 单元测试（pytest）
  - 集成测试（API测试）
  - 性能测试（负载测试）
- **前端测试**:
  - 组件测试（Jest/React Testing Library）
  - 手动测试（当前阶段）
  - 未来可添加：Vitest + @testing-library/react

#### 性能优化
- [ ] 数据库查询优化
- [ ] API响应时间优化
- [ ] 前端打包优化
- [ ] 缓存策略实施

---

### Phase 10: 文档与部署 📋 规划中
**周期**: 第12周 | **优先级**: P0

#### 文档完善
- [x] API文档（Swagger）
- [x] 用户使用手册
- [x] 开发者文档
- [ ] 部署指南

#### 部署配置
- [ ] Docker容器化
- [ ] Docker Compose编排
- [ ] CI/CD流水线
- [ ] 生产环境配置

## 🛠️ 开发环境设置

### 环境要求
- Python 3.11+
- Node.js 18+
- Git
- Docker（可选）

### 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd fishing_agent

# 2. 安装Python依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件，添加必要的API密钥

# 4. 初始化数据库
uv run python -m packages.agent_fishing.tools.lure.alembic upgrade head

# 5. 创建管理员用户
uv run python scripts/create_admin.py

# 6. 启动后端开发服务器
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# 7. 启动前端开发服务器（v5.0.0新增）
cd apps/web-admin
npm install
npm run dev

# 8. 访问系统
# API文档: http://localhost:8000/docs
# 管理前端: http://localhost:5173 (用户名: admin, 密码: admin123)
```

### 前后端同时开发工作流 ⭐ v5.0.0

```bash
# Terminal 1 - 后端API服务
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - React前端服务
cd apps/web-admin
npm run dev

# Terminal 3 - CLI应用（可选）
uv run python main.py
```

### React前端开发详细指南 ⭐ v5.0.0

#### 1. 环境准备
```bash
# 确保Node.js版本 >= 18
node --version
npm --version

# 进入前端目录
cd apps/web-admin

# 安装依赖（首次运行）
npm install

# 查看项目依赖
npm list --depth=0
```

#### 2. 前端环境变量配置
创建 `.env` 文件：
```bash
# API地址
VITE_API_BASE_URL=http://localhost:8000

# 应用标题
VITE_APP_TITLE=智能钓鱼助手管理后台

# 是否启用Mock数据
VITE_USE_MOCK=false
```

#### 3. 开发命令
```bash
# 开发模式（热更新）
npm run dev

# 类型检查
npm run type-check

# 代码检查
npm run lint

# 修复代码格式
npm run lint:fix

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

#### 4. 前端技术栈详情
- **React 19.2.0**: 最新的React版本，支持并发特性
- **TypeScript 5.9.3**: 类型安全的JavaScript超集
- **Vite 7.2.4**: 现代化构建工具，极快的冷启动
- **Ant Design 5.22.0**: 企业级UI组件库
- **Redux Toolkit 2.2.7**: Redux状态管理工具
- **React Router 6.28.0**: React路由管理
- **ECharts 5.5.0**: 数据可视化图表库

### 环境变量配置

```bash
# 必需的API密钥
CAIYUN_API_KEY=your_caiyun_api_key      # 彩云天气
AMAP_API_KEY=your_amap_api_key          # 高德地图
DASHSCOPE_API_KEY=your_dashscope_key    # 通义千问

# 可选的LLM API
ZHIPU_API_KEY=your_zhipu_key            # 智谱AI
OPENAI_API_KEY=your_openai_key          # OpenAI
DOUBAO_API_KEY=your_doubao_key          # 豆包

# JWT认证
JWT_SECRET_KEY=your_jwt_secret          # 生产环境必须更换

# 数据库配置
DB_TYPE=sqlite                          # sqlite/postgresql/mysql
DB_PATH=packages/agent_fishing/tools/lure/data/equipment.db
```

## 📊 项目架构

### 后端架构
```
apps/
├── api/                     # FastAPI后端
│   ├── auth/               # JWT认证模块
│   ├── middleware/         # 中间件
│   ├── routes/            # API路由
│   │   ├── analytics.py   # 数据分析路由 (v5.0.0新增)
│   │   ├── config.py      # 配置管理路由 (v5.0.0新增)
│   │   ├── crawler.py     # 爬虫管理路由 (v4.0.0新增)
│   │   ├── monitor.py     # 监控管理路由 (v4.0.0新增)
│   │   └── auth.py        # 认证路由
│   ├── schemas/           # 数据模型
│   │   ├── analytics.py   # 数据分析Schema (v5.0.0新增)
│   │   ├── config.py      # 配置管理Schema (v5.0.0新增)
│   │   ├── crawler.py     # 爬虫管理Schema (v4.0.0新增)
│   │   └── monitor.py     # 监控管理Schema (v4.0.0新增)
│   └── services/          # 业务服务层 (v4.0.0新增)
│       ├── analytics_service.py  # 数据分析服务 (v5.0.0新增)
│       ├── config_service.py     # 配置管理服务 (v5.0.0新增)
│       ├── crawler_service.py    # 爬虫服务 (v4.0.0新增)
│       └── monitor_service.py    # 监控服务 (v4.0.0新增)
└── cli/                   # CLI应用

packages/
└── agent_fishing/         # 核心Agent包
    ├── core/             # Agent核心
    ├── tools/            # LangChain工具
    ├── models/           # 数据模型
    └── orm/              # 数据访问层

apps/web-admin/            # React管理前端 (v5.0.0新增)
├── src/
│   ├── components/       # 通用组件
│   ├── pages/           # 页面组件
│   ├── services/        # API服务
│   ├── utils/           # 工具函数
│   └── types/           # TypeScript类型定义
├── package.json         # 前端依赖配置
└── vite.config.ts       # Vite构建配置
```

### 数据库设计
- **23张核心表**：装备、品牌、用户、日志等
- **Repository模式**：统一的数据访问接口
- **迁移管理**：Alembic版本控制

### 权限系统
- **3种角色**：Admin（管理员）、Editor（编辑）、ReadOnly（只读）
- **30+权限点**：细粒度功能控制
- **JWT认证**：无状态token认证

## 🔧 开发规范

### 代码规范
- Python: PEP 8 + Black格式化
- TypeScript: ESLint + Prettier
- 提交信息: Conventional Commits

### 测试要求
- 单元测试覆盖率 > 80%
- 所有API端点必须有测试
- 关键业务逻辑必须有集成测试

### Git工作流
```bash
# 功能开发
git checkout -b feature/new-feature
git commit -m "feat: add new feature"
git push origin feature/new-feature

# 创建Pull Request
# 代码审查通过后合并到main分支
```

## 📚 文档资源

### 开发文档
- [API参考文档](API_REFERENCE.md)
- [架构设计文档](ARCHITECTURE.md)
- [数据库设计](BACKEND_ARCHITECTURE.md)
- [测试文档](TESTING.md)

### Phase详细计划
- [Phase 1: 数据库ORM层](dev-plans/phase1-database-orm.md)
- [Phase 2: 认证授权中间件](dev-plans/phase2-auth-middleware.md)
- [Phase 3: 核心管理API](dev-plans/phase3-core-api.md)
- [Phase 4: 爬虫监控](dev-plans/phase4-crawler-monitor.md)
- [Phase 5: 数据分析配置](dev-plans/phase5-analytics-config.md)
- [Phase 6-8: 前端开发](dev-plans/phase6-8-frontend.md)
- [Phase 9: 测试优化](dev-plans/phase9-testing-optimization.md)
- [Phase 10: 文档部署](dev-plans/phase10-deployment-docs.md)

## 🚀 部署指南

### Docker部署

```bash
# 构建后端镜像
docker build -t fishing-agent-api .

# 构建前端镜像
cd apps/web-admin
docker build -t fishing-agent-web .

# 运行容器
docker-compose up -d
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_TYPE=postgresql
      - DB_HOST=postgres
      - DB_USER=fishing
      - DB_PASSWORD=fishing123
    depends_on:
      - postgres
      - redis

  web:
    build: ./apps/web-admin
    ports:
      - "3000:3000"
    depends_on:
      - api

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=fishing_agent
      - POSTGRES_USER=fishing
      - POSTGRES_PASSWORD=fishing123
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 🤝 贡献指南

### 如何贡献
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 编写测试
5. 创建Pull Request

### 问题反馈
- 使用GitHub Issues报告bug
- 提供详细的复现步骤
- 包含错误日志和环境信息

## 📞 联系方式

- 项目维护者: [Your Name]
- 邮箱: [your.email@example.com]
- 项目地址: [GitHub Repository URL]

---

> 📌 **提示**: 本文档会随着项目进展持续更新，请定期查看最新版本。

**最后更新**: 2025-12-11
**文档版本**: v5.0.0
**当前状态**: Phase 5 数据分析配置已完成，React管理前端已集成