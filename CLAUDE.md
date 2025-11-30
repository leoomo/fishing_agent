<!-- OPENSPEC:START -->
# OpenSpec Instructions
Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding
<!-- OPENSPEC:END -->

# 智能钓鱼助手 v3.1.1

模块化 Agent 架构 + 动态Prompt中间件，基于 LangChain 1.0+ 和 7 因子科学评分系统。

**当前版本**: v3.1.1 | **当前分支**: feature/llm-optimization (功能已完成)

## 核心特性
- 动态Prompt中间件 (Token效率↑50%+) + 模块化Agent包 + 7因子评分 (温度/天气/风力/气压/湿度/季节/月相)
- 时间段意图识别 (98%+准确率) + 向量搜索 (DashScope Embedding) + FastAPI后端

## 架构
```
packages/agent_fishing/     # 自包含Agent包
├── core/                   # agent.py, model_factory.py, prompts.py, callbacks.py
│   └── middleware/         # dynamic_prompt.py (v3.1.1新增)
├── tools/                  # basic, weather, fishing, lure_tools, lure/, scoring/
└── utils/
apps/                       # cli/main.py, api/main.py
shared/                     # config/, data/
```

## 快速开始
```bash
uv sync                                    # 安装依赖
cp .env.example .env                       # 配置环境
uv run python main.py                      # 运行CLI
uv run uvicorn apps.api.main:app --reload # 运行API
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
POST /api/v1/fishing/chat  # 对话接口
GET  /api/v1/fishing/tools # 工具列表
GET  /health               # 健康检查
```

## 环境变量
```bash
# 必需
CAIYUN_API_KEY=xxx           # 彩云天气
AMAP_API_KEY=xxx             # 高德地图
DASHSCOPE_API_KEY=xxx        # 通义千问 + Embedding
ANTHROPIC_AUTH_TOKEN=xxx     # 智谱AI (推荐)
```

## 新增Agent模板
```bash
mkdir -p packages/agent_xxx/{core,tools,utils}
# __init__.py: from .core import XxxAgent, create_agent
# langgraph.json: "xxx": "./packages/agent_xxx:get_agent"
```

## 架构原则
1. Agent自包含 (独立发布) | 2. 同步优先 (requests) | 3. 诚实数据 (无假数据) | 4. LangChain 1.0+ (@tool装饰器)
