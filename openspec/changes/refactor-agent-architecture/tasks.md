# Tasks: Agent 模块收束架构重构

## 1. 创建新目录结构

- [x] 1.1 创建 `packages/agent_fishing/` 目录及子目录
  - `core/`, `tools/`, `tools/lure/`, `tools/scoring/`, `utils/`
- [x] 1.2 创建 `apps/` 目录及子目录
  - `cli/`, `api/routes/`, `api/schemas/`
- [x] 1.3 创建 `shared/` 目录及子目录
  - `config/`, `data/`
- [x] 1.4 创建根目录 `tests/` 结构
  - `agent_fishing/`, `api/`, `integration/`

## 2. 迁移 Agent 核心文件

- [x] 2.1 迁移 `src/fishing_agent/core.py` → `packages/agent_fishing/core/agent.py`
- [x] 2.2 迁移 `src/fishing_agent/model_factory.py` → `packages/agent_fishing/core/model_factory.py`
- [x] 2.3 迁移 `src/fishing_agent/prompts.py` → `packages/agent_fishing/core/prompts.py`
- [x] 2.4 迁移 `src/fishing_agent/callbacks.py` → `packages/agent_fishing/core/callbacks.py`

## 3. 迁移工具模块

- [x] 3.1 迁移 `src/tools/basic_tools.py` → `packages/agent_fishing/tools/basic.py`
- [x] 3.2 迁移 `src/tools/weather_tools.py` → `packages/agent_fishing/tools/weather.py`
- [x] 3.3 迁移 `src/tools/fishing_tools.py` → `packages/agent_fishing/tools/fishing.py`
- [x] 3.4 迁移 `src/tools/lure_tools.py` → `packages/agent_fishing/tools/lure_tools.py`
- [x] 3.5 迁移 `src/tools/lure/*` → `packages/agent_fishing/tools/lure/*`
- [x] 3.6 迁移 `src/tools/scoring/*` → `packages/agent_fishing/tools/scoring/*`

## 4. 迁移工具类

- [x] 4.1 迁移 `src/utils/cache.py` → `packages/agent_fishing/utils/cache.py`
- [x] 4.2 迁移 `src/utils/coordinate_utils.py` → `packages/agent_fishing/utils/coordinate.py`
- [x] 4.3 迁移 `src/utils/date_utils.py` → `packages/agent_fishing/utils/date.py`
- [x] 4.4 迁移 `src/utils/api_client.py` → `packages/agent_fishing/utils/api_client.py`
- [x] 4.5 迁移 `src/utils/health_check.py` → `packages/agent_fishing/utils/health_check.py`

## 5. 迁移共享资源

- [x] 5.1 迁移 `src/config/*` → `shared/config/*`
- [x] 5.2 迁移 `src/data/*` → `shared/data/*`

## 6. 迁移测试文件

- [x] 6.1 迁移 `src/tests/*` → `tests/agent_fishing/*`
- [x] 6.2 创建 `tests/conftest.py` pytest 配置

## 7. 创建包初始化文件

- [x] 7.1 创建 `packages/agent_fishing/__init__.py`
- [x] 7.2 创建 `packages/agent_fishing/core/__init__.py`
- [x] 7.3 创建 `packages/agent_fishing/tools/__init__.py`
- [x] 7.4 创建 `packages/agent_fishing/utils/__init__.py`

## 8. 创建应用层文件

- [x] 8.1 创建 `apps/cli/__init__.py` 和 `apps/cli/main.py`
- [x] 8.2 创建 `apps/api/__init__.py` 和 `apps/api/main.py`
- [x] 8.3 创建 `apps/api/routes/fishing.py`
- [x] 8.4 创建 `apps/api/schemas/chat.py`

## 9. 更新所有导入路径

- [x] 9.1 更新 `packages/agent_fishing/` 内所有文件的导入
- [x] 9.2 更新 `apps/` 内所有文件的导入
- [x] 9.3 更新 `tests/` 内所有文件的导入

## 10. 更新配置文件

- [x] 10.1 更新 `langgraph.json` - 路径改为 `./packages/agent_fishing:get_agent`
- [x] 10.2 更新 `pyproject.toml` - 添加包配置和脚本
- [x] 10.3 更新根目录 `main.py` - 委托到 `apps/cli/main.py`

## 11. 验证与测试

- [x] 11.1 验证 Agent 包导入: `from packages.agent_fishing import FishingAgent`
- [x] 11.2 验证 CLI 模块导入: `from apps.cli.main import main`
- [x] 11.3 验证 FastAPI 导入: `from apps.api.main import app`
- [x] 11.4 验证工具列表: 7 个工具正常加载
- [x] 11.5 验证 Agent 创建: `create_agent()` 成功

## 12. 清理旧代码

- [x] 12.1 删除 `src/` 目录
- [x] 12.2 更新 `CLAUDE.md` 文档
