<!-- OPENSPEC:START -->
# OpenSpec Instructions
Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding
<!-- OPENSPEC:END -->

# 智能钓鱼助手 v5.0.0

模块化 Agent 架构 + JWT认证系统 + React管理前端，基于 LangChain 1.0+ 和 7 因子科学评分系统。

**当前版本**: v5.0.0 | **当前分支**: feature/equipment-ui (功能已完成)

## 核心特性
- JWT认证系统 (RBAC权限管理 + Token安全) + 模块化Agent包 + 7因子评分 (温度/天气/风力/气压/湿度/季节/月相)
- 时间段意图识别 (98%+准确率) + 动态Prompt中间件 + 装备管理UI优化
- 数据分析报表 (装备统计/趋势分析/品牌排行) + 系统配置管理 (API密钥/参数配置)
- React管理前端 (React 19.2.0 + TypeScript + Ant Design 5.22.0) + 爬虫监控模块

## 架构
```
packages/agent_fishing/     # 自包含Agent包
├── core/                   # agent.py, model_factory.py, prompts.py, callbacks.py
│   └── middleware/         # dynamic_prompt.py
├── tools/                  # basic, weather, fishing, lure_tools, lure/, scoring/
└── utils/
apps/                       # 应用层
├── cli/                    # CLI应用 (main.py)
├── api/                    # FastAPI后端
│   ├── main.py             # API服务器 (v5.0.0)
│   ├── auth/               # JWT认证模块
│   ├── middleware/         # 认证中间件
│   ├── routes/             # API路由
│   │   ├── analytics.py    # 数据分析路由 ⭐ v5.0.0新增
│   │   ├── config.py       # 配置管理路由 ⭐ v5.0.0新增
│   │   ├── crawler.py      # 爬虫管理路由 ⭐ v4.0.0新增
│   │   └── monitor.py      # 监控管理路由 ⭐ v4.0.0新增
│   ├── schemas/            # 数据模型
│   └── services/           # 业务服务层 ⭐ v5.0.0新增
└── web-admin/              # React管理前端 ⭐ v5.0.0新增
    ├── src/                # 源代码
    │   ├── components/     # 通用组件
    │   ├── pages/          # 页面组件
    │   └── services/       # API服务
    └── package.json        # 前端依赖配置
shared/                     # 共享资源
├── config/                 # 全局配置
└── data/                   # 共享数据
```

## 快速开始
```bash
uv sync                                    # 安装依赖
cp .env.example .env                       # 配置环境
uv run python main.py                      # 运行CLI
uv run uvicorn apps.api.main:app --reload # 运行API
cd apps/web-admin && npm run dev          # 运行React前端 (v5.0.0新增)
```

## 关键导入
```python
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools
from packages.agent_fishing.core import ModelFactory
from packages.agent_fishing.tools import get_weather, query_fishing_recommendation
from packages.agent_fishing.utils import get_coordinates, parse_date_input
```

## API端点
```
# 钓鱼助手 API
POST /api/v1/fishing/chat     # 对话接口
GET  /api/v1/fishing/tools    # 工具列表
GET  /health                  # 健康检查

# 认证 API (v3.1.1新增)
POST /api/v1/auth/login       # 用户登录
GET  /api/v1/auth/me          # 获取用户信息

# 数据分析 API (v5.0.0新增)
GET  /api/v1/admin/analytics/equipment/stats      # 装备统计
GET  /api/v1/admin/analytics/equipment/trends     # 趋势分析
POST /api/v1/admin/analytics/reports/generate     # 生成报表

# 配置管理 API (v5.0.0新增)
GET  /api/v1/admin/config/configs                 # 查询配置
POST /api/v1/admin/config/configs                 # 创建配置
POST /api/v1/admin/config/configs/test-api-key    # 测试API密钥

# 爬虫管理 API (v4.0.0新增)
GET  /api/v1/admin/crawler/tasks                  # 爬虫任务列表
POST /api/v1/admin/crawler/tasks/trigger          # 触发爬虫

# 监控管理 API (v4.0.0新增)
GET  /api/v1/admin/monitor/api-stats              # API统计
GET  /api/v1/admin/monitor/llm-stats               # LLM统计
```

## 环境变量
```bash
# 必需
CAIYUN_API_KEY=xxx           # 彩云天气
AMAP_API_KEY=xxx             # 高德地图
DASHSCOPE_API_KEY=xxx        # 通义千问 + Embedding
ANTHROPIC_AUTH_TOKEN=xxx     # 智谱AI (推荐)

# JWT认证 (v3.1.1新增)
JWT_SECRET_KEY=xxx           # JWT密钥 (必须设置)
JWT_ALGORITHM=HS256          # JWT算法
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # Token过期时间(分钟)
```

## 新增Agent模板
```bash
mkdir -p packages/agent_xxx/{core,tools,utils}
# __init__.py: from .core import XxxAgent, create_agent
# langgraph.json: "xxx": "./packages/agent_xxx:get_agent"
```

## 架构原则
1. Agent自包含 (独立发布) | 2. 同步优先 (requests) | 3. 诚实数据 (无假数据) | 4. LangChain 1.0+ (@tool装饰器)
