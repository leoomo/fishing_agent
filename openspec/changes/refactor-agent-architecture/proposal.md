# Change: Agent 模块收束架构重构

## Why

当前 `src/` 目录结构将 Agent 核心代码与工具、配置混合在一起，导致：
1. Agent 无法独立发布为 PyPI 包
2. 难以支持多 Agent 场景（未来可能添加天气 Agent、路亚 Agent 等）
3. 后端 API、前端、移动端等应用层无清晰边界
4. 代码复用和团队协作受限

需要将 Agent 模块收束为完全自包含的独立包，支持后续扩展。

## What Changes

### 核心变更

1. **创建 `packages/agent_fishing/` 目录** - 完全自包含的钓鱼 Agent 包
   - `core/` - Agent 核心实现（agent.py, model_factory.py, prompts.py, callbacks.py）
   - `tools/` - Agent 专属工具（basic, weather, fishing, lure, scoring）
   - `utils/` - Agent 专属工具类（cache, coordinate, date, api_client, health_check）

2. **创建 `apps/` 应用层目录**
   - `cli/` - 命令行应用
   - `api/` - FastAPI 后端（新增）

3. **创建 `shared/` 共享资源目录**
   - `config/` - 全局配置
   - `data/` - 共享数据（如 national_region_database）

4. **迁移 `tests/` 到根目录** - 按模块组织测试

5. **删除 `src/` 目录** - **BREAKING** 立即移除，不保留向后兼容层

### 配置更新

- `langgraph.json` - 更新路径为 `./packages/agent_fishing:agent`
- `pyproject.toml` - 添加包配置和脚本入口
- `main.py` - 简化为委托到 `apps/cli/main.py`

## Impact

- Affected specs: `agent-architecture` (新建)
- Affected code:
  - `src/` - 完全移除
  - `packages/agent_fishing/` - 新建
  - `apps/` - 新建
  - `shared/` - 新建
  - `tests/` - 迁移重组
  - `langgraph.json` - 路径更新
  - `pyproject.toml` - 包配置
  - `main.py` - 入口更新
- Breaking changes:
  - 所有 `from src.xxx` 导入路径失效
  - 所有 `from fishing_agent.xxx` 导入路径变更
  - `src/agent.py` 兼容层移除
