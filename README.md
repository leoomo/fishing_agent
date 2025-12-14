# Fishing Agent - 智能钓鱼助手 v5.0.0

基于 LangChain 1.0+ 的智能钓鱼助手，提供钓鱼时间推荐、天气分析和路亚装备管理功能。

> 🎣 智能分析天气条件，推荐最佳钓鱼时间 - **模块化 Agent 架构 v5.0.0 + JWT认证系统 + React管理前端 + 7因子科学评分 + 工作流管理系统**

## 🌟 核心特性

- **🎣 智能钓鱼推荐** - 基于7因子科学评分体系，准确推荐最佳钓鱼时间和地点
- **🎒 路亚装备管理** - 智能装备推荐、用户装备库、电商数据同步
- **📊 数据分析报表** - 装备统计、趋势分析、用户行为洞察
- **🔐 JWT认证系统** - 完整的用户认证和RBAC权限管理
- **🖥️ 管理前端** - 基于React的现代化管理界面
- **🕷️ 爬虫管理** - 多平台爬虫、任务调度、实时监控
- **⚙️ 系统配置** - API密钥管理、系统参数配置
- **🔄 工作流管理** - 可视化工作流编排、DAG依赖管理、任务调度系统

## 🚀 快速开始

### 环境要求
- Python 3.11+
- uv 包管理器
- Node.js 18+ (前端)

### 安装运行

```bash
# 1. 克隆并安装依赖
git clone <repository>
cd fishing_agent
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 添加 API 密钥

# 3. 运行 CLI 应用
uv run python main.py

# 4. 或运行 API 服务
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# 5. 运行前端（可选）
cd apps/web-admin && npm install && npm run dev
```

## 📚 文档导航

- [📖 快速入门](docs/GETTING_STARTED.md) - 详细的安装配置指南
- [🔧 API 参考](docs/API_REFERENCE.md) - 完整的 REST API 文档
- [👥 用户指南](docs/USER_GUIDE.md) - 详细的使用说明和示例
- [🏗️ 架构文档](docs/ARCHITECTURE.md) - 系统架构说明
- [🔄 更新日志](CHANGELOG.md) - 版本更新记录
- [🛠️ 开发指南](docs/DEVELOPMENT.md) - 开发环境搭建和贡献指南

## 🎯 快速体验

```python
# 简单示例
from packages.agent_fishing import create_agent

agent = create_agent(model_provider="zhipu")
response = agent.run("明天杭州钓鱼怎么样？")
print(response)
```

## 🌐 访问地址

- **API 服务器**: http://localhost:8000
- **React 管理前端**: http://localhost:5174
- **API 文档**: http://localhost:8000/docs

## 📊 技术栈

### 后端
- **Python 3.11+** - 编程语言
- **LangChain 1.0+** - LLM 应用框架
- **FastAPI** - Web 框架
- **SQLite** - 数据库
- **JWT** - 认证系统
- **APScheduler** - 任务调度
- **Playwright** - 网页自动化

### 前端
- **React 19.2.0** - 前端框架
- **TypeScript** - 类型安全
- **Ant Design 5.22.0** - UI 组件库
- **Vite** - 构建工具
- **Redux Toolkit** - 状态管理
- **ECharts** - 数据可视化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

> 🎣 智能分析，精准钓鱼！
>
> 当前版本：v5.0.0 (Phase 5 数据分析和配置管理 + Phase 4 爬虫监控模块 + Phase 3 React管理前端 + Phase 2 JWT认证系统 + Phase 1 模块化Agent架构)