<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

智能钓鱼助手 v3.1.0 - 模块化 Agent 架构，基于 LangChain 1.0+ 和 7 因子科学评分系统，专注于钓鱼时间推荐、天气分析，支持多种 LLM 提供商和 FastAPI 后端。

**当前版本**: v3.1.0 (模块化 Agent 架构 + FastAPI 后端)
**当前分支**: feature/llm-optimization
**架构**: packages/agent_fishing 独立 Agent 包

### 核心特性
- **模块化 Agent**: 完全自包含的 Agent 包架构，支持独立发布
- **FastAPI 后端**: REST API 支持，便于前端集成
- **LangChain 1.0+**: 原生 LangChain agents
- **7 因子科学评分**: 温度、天气、风力、气压、湿度、季节、月相
- **动态趋势分析**: 识别"黄金钓鱼时段"
- **向量搜索**: 基于 DashScope Embedding API 的语义搜索

## 架构概览

### 目录结构
```
fishing-agent/
├── packages/                      # Agent 包目录
│   └── agent_fishing/             # 钓鱼 Agent（完全自包含）
│       ├── __init__.py            # 包入口
│       ├── core/                  # Agent 核心
│       │   ├── agent.py           # FishingAgent 实现
│       │   ├── model_factory.py   # LLM 工厂
│       │   ├── prompts.py         # 提示词
│       │   └── callbacks.py       # 回调系统
│       ├── tools/                 # Agent 工具
│       │   ├── basic.py           # 基础工具
│       │   ├── weather.py         # 天气工具
│       │   ├── fishing.py         # 钓鱼工具
│       │   ├── lure_tools.py      # 路亚工具
│       │   ├── lure/              # 路亚子模块
│       │   └── scoring/           # 评分系统
│       └── utils/                 # Agent 工具类
├── apps/                          # 应用层
│   ├── cli/                       # CLI 应用
│   │   └── main.py
│   └── api/                       # FastAPI 后端
│       ├── main.py
│       ├── routes/
│       └── schemas/
├── shared/                        # 共享资源
│   ├── config/                    # 全局配置
│   └── data/                      # 共享数据
├── tests/                         # 测试
│   └── agent_fishing/
├── main.py                        # CLI 入口
├── langgraph.json                 # LangGraph 配置
└── pyproject.toml                 # 项目配置
```

### 核心模块
- **`packages/agent_fishing/`** - 钓鱼 Agent 包（完全自包含）
- **`apps/cli/`** - 命令行应用
- **`apps/api/`** - FastAPI REST API
- **`shared/`** - 共享配置和数据

## 开发指南

### 环境配置
```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env

# 运行 CLI
uv run python main.py

# 运行 API 服务
uv run uvicorn apps.api.main:app --reload
```

### 测试
```bash
# 运行所有测试
uv run pytest tests/

# 测试 Agent 导入
uv run python -c "from packages.agent_fishing import create_agent; print('OK')"

# 测试工具列表
uv run python -c "from packages.agent_fishing import get_all_tools; print(len(get_all_tools()))"
```

## 技术栈

### 核心框架
- **langchain>=0.3.0** - LangChain 1.0+ API
- **fastapi>=0.121.2** - REST API 框架
- **uvicorn>=0.38.0** - ASGI 服务器
- **pydantic>=2.0.0** - 数据验证
- **chromadb>=0.4.22** - 向量数据库

### LLM 提供商
- **智谱AI GLM** (ANTHROPIC_AUTH_TOKEN) - 推荐
- **通义千问** (DASHSCOPE_API_KEY) - LLM + Embedding
- **OpenAI GPT** (OPENAI_API_KEY) - 可选

### 外部服务
- **彩云天气 API** (CAIYUN_API_KEY) - 必需
- **高德地图 API** (AMAP_API_KEY) - 必需
- **DashScope Embedding API** (DASHSCOPE_API_KEY) - 必需

## 常用导入

```python
# Agent 创建
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools

# 核心模块
from packages.agent_fishing.core import ModelFactory
from packages.agent_fishing.tools import get_weather, query_fishing_recommendation

# 评分系统
from packages.agent_fishing.tools.scoring.enhanced_scorer import (
    calculate_seasonal_score, analyze_pressure_trend
)

# 工具类
from packages.agent_fishing.utils import get_coordinates, parse_date_input

# 向量搜索
from packages.agent_fishing.tools.lure.embeddings import DashScopeEmbedding
from packages.agent_fishing.tools.lure.vector_store import get_vector_store
```

## API 端点

```
GET  /                     # API 信息
GET  /health               # 健康检查
POST /api/v1/fishing/chat  # 钓鱼助手对话
GET  /api/v1/fishing/tools # 工具列表
```

### 示例请求
```bash
# 健康检查
curl http://localhost:8000/health

# 对话
curl -X POST http://localhost:8000/api/v1/fishing/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "明天杭州钓鱼怎么样？"}'
```

## 环境变量

```bash
# 必需 API
CAIYUN_API_KEY=your-caiyun-api-key
AMAP_API_KEY=your-amap-api-key
DASHSCOPE_API_KEY=your-dashscope-api-key

# LLM 提供商
ANTHROPIC_AUTH_TOKEN=your-zhipu-token

# 向量存储配置（可选）
VECTOR_EMBEDDING_MODEL=text-embedding-v3
VECTOR_AUTO_INDEX=true
```

## 新增 Agent 指南

创建新 Agent 时，遵循以下模板：

```bash
# 1. 创建目录
mkdir -p packages/agent_xxx/{core,tools,utils}

# 2. 创建必要文件
touch packages/agent_xxx/{__init__.py,core/__init__.py,tools/__init__.py,utils/__init__.py}
touch packages/agent_xxx/core/{agent.py,model_factory.py,prompts.py}
```

```python
# packages/agent_xxx/__init__.py
from .core import XxxAgent, create_agent
from .tools import get_all_tools

__all__ = ["XxxAgent", "create_agent", "get_all_tools"]
```

更新 `langgraph.json`:
```json
{
  "graphs": {
    "fishing": "./packages/agent_fishing:get_agent",
    "xxx": "./packages/agent_xxx:get_agent"
  }
}
```

## 架构原则

1. **Agent 自包含**: 每个 Agent 包完全独立，可单独发布
2. **同步优先**: 使用 `requests` 直接 API 调用
3. **诚实数据**: 不生成假数据，提供诚实错误信息
4. **LangChain 1.0+**: 直接使用 `@tool` 装饰器
