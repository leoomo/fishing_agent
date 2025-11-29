# Design: Agent 模块收束架构重构

## Context

智能钓鱼助手 v3.0.2.1 当前采用 `src/` 扁平目录结构，Agent 核心代码与工具、配置、数据混合。随着项目发展，需要支持：
- 多 Agent 场景（钓鱼、天气、路亚等独立 Agent）
- 多端应用（CLI、Web API、前端、移动端）
- 独立发布（各 Agent 可单独发布为 PyPI 包）

**约束条件**:
- 用户选择 `packages/agent` 命名空间
- 用户选择立即移除旧路径，不保留向后兼容
- 后端框架选择 FastAPI

## Goals / Non-Goals

**Goals**:
- Agent 完全自包含，可独立开发、测试、发布
- 支持多 Agent 并存
- 清晰的应用层边界（CLI、API 分离）
- 使用 `git mv` 保留文件历史

**Non-Goals**:
- 本次不实现新 Agent（如 weather、lure）
- 本次不实现 Web 前端或移动端
- 不支持旧导入路径的向后兼容

## Decisions

### Decision 1: 目录结构设计

采用三层结构：

```
fishing-agent/
├── packages/                  # Agent 包目录
│   └── agent_fishing/         # 钓鱼 Agent（完全自包含）
│       ├── __init__.py
│       ├── core/              # Agent 核心
│       ├── tools/             # Agent 专属工具
│       └── utils/             # Agent 专属工具类
├── apps/                      # 应用层
│   ├── cli/                   # CLI 应用
│   └── api/                   # FastAPI 后端
├── shared/                    # 跨模块共享
│   ├── config/
│   └── data/
└── tests/                     # 测试
```

**Rationale**: 每个 Agent 完全自包含，可独立发布；应用层与 Agent 层分离，便于扩展。

**Alternatives considered**:
1. `src/agents/fishing/` - 仍在 src 下，与旧结构混淆
2. `lib/agent_fishing/` - lib 通常用于第三方库

### Decision 2: Agent 包命名

使用 `agent_fishing` 而非 `fishing_agent`。

**Rationale**:
- 所有 Agent 包以 `agent_` 前缀开头，便于识别和排序
- 未来 Agent: `agent_weather`, `agent_lure`, `agent_xxx`

### Decision 3: LangGraph 集成

```json
{
  "graphs": {
    "fishing": "./packages/agent_fishing:agent"
  }
}
```

**Rationale**:
- 每个 Agent 包导出模块级 `agent` 对象
- 支持多 Agent 注册: `"weather": "./packages/agent_weather:agent"`

### Decision 4: 导入路径策略

包内部使用相对导入，外部使用绝对导入：

```python
# 包内部（agent_fishing/tools/fishing.py）
from ..utils.coordinate import get_coordinates
from .scoring.enhanced_scorer import calculate_score

# 外部（apps/api/routes/fishing.py）
from packages.agent_fishing import FishingAgent, create_agent
```

**Rationale**: 相对导入使包可移植，绝对导入使调用清晰。

### Decision 5: FastAPI 路由设计

```
/api/v1/fishing/chat    - 钓鱼 Agent 对话
/api/v1/agents/         - Agent 列表
/health                 - 健康检查
```

**Rationale**: RESTful 设计，版本化 API，支持多 Agent 扩展。

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 导入路径大量变更 | 高 | 使用批量替换工具，分阶段验证 |
| LangGraph 路径格式 | 中 | 迁移后立即验证 `langgraph dev` |
| 测试覆盖遗漏 | 中 | 迁移前后运行完整测试套件对比 |
| git 历史丢失 | 低 | 严格使用 `git mv` 迁移 |

## Migration Plan

### 阶段 1: 创建目录结构（无破坏性）
创建所有新目录，不影响现有代码

### 阶段 2: 迁移文件（使用 git mv）
按依赖顺序迁移：utils → tools → core → tests

### 阶段 3: 创建初始化文件
编写所有 `__init__.py` 文件

### 阶段 4: 更新导入路径
批量更新所有导入语句

### 阶段 5: 更新配置
更新 langgraph.json、pyproject.toml、main.py

### 阶段 6: 验证
运行完整测试套件和功能验证

### 阶段 7: 清理
删除 src/ 目录，更新文档

### 回滚方案

```bash
# 如果迁移失败
git checkout HEAD -- src/
git checkout HEAD -- langgraph.json
git checkout HEAD -- pyproject.toml
git checkout HEAD -- main.py
rm -rf packages/ apps/ shared/
```

## Open Questions

1. ~~是否保留向后兼容层？~~ 已决定：不保留
2. ~~后端框架选择？~~ 已决定：FastAPI
3. 是否需要为 shared/ 模块创建独立的 pyproject.toml？（建议暂不需要）
4. ChromaDB 向量存储数据目录是否迁移？（建议保持在 data/ 下）
