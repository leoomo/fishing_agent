# 开发者指南

欢迎来到智能钓鱼助手开发者指南！本指南面向想要参与项目开发、进行二次开发或集成API的开发者。

## 📖 指南内容

### 🔧 [环境配置](./environment-setup.md)
- 开发环境搭建
- 依赖安装和配置
- API密钥申请和配置
- 项目运行验证

### 🏗️ [代码结构](./codebase-structure.md)
- 项目架构概览
- 模块化包结构
- 核心组件说明
- 重要设计模式

### 🔄 [开发流程](./development-workflows.md)
- 开发规范和最佳实践
- Git工作流程
- 代码审查流程
- 发布流程

### 🧪 [测试指南](./testing.md)
- 测试策略和框架
- 单元测试编写
- 集成测试方法
- 性能测试技巧

### 🤝 [贡献指南](./contribution-guide.md)
- 如何参与项目开发
- 代码提交规范
- Issue和PR流程
- 社区行为准则

### 🛠️ [开发工具](./tools-and-utilities.md)
- 可用开发工具
- 调试技巧和方法
- 性能分析工具
- 部署自动化工具

### 🐛 [调试指南](./debugging.md)
- 常见问题排查
- 日志分析技巧
- 性能瓶颈定位
- 错误处理最佳实践

## 🎯 开发者资源

### 核心技术栈
- **后端**: Python 3.11+, LangChain 1.0+, FastAPI
- **前端**: React 19.2.0, TypeScript, Ant Design 5.22.0
- **数据库**: SQLite (开发), PostgreSQL (生产)
- **缓存**: Redis
- **AI模型**: 通义千问, 智谱AI, Ollama本地模型
- **OCR**: Ollama + SiliconFlow

### 项目架构
- **模块化设计**: 4个独立包，完全自包含
- **Agent架构**: 基于LangChain的智能体设计
- **API优先**: RESTful API设计，支持多端接入
- **认证安全**: JWT认证 + RBAC权限管理

## 🚀 快速开始开发

### 1. 环境准备
```bash
# 克隆项目
git clone https://github.com/your-org/fishing-agent.git
cd fishing-agent

# 安装依赖
uv sync --dev

# 配置环境
cp .env.example .env
# 编辑 .env 添加必要配置
```

### 2. 运行项目
```bash
# CLI开发模式
uv run python main.py

# API开发服务
uv run uvicorn apps.api.main:app --reload

# React开发服务
cd apps/web-admin && npm run dev

# 微信小程序开发
# 使用微信开发者工具打开 fishing_agent_app/ 目录
```

### 3. 运行测试
```bash
# 所有测试
uv run pytest

# 特定包测试
uv run pytest packages/agents/fishing/tests/

# 测试覆盖率
uv run pytest --cov=packages.agents.fishing
```

## 📦 包结构概览

```
packages/                          # 模块化包目录
├── agents/                       # Agent统一目录
│   ├── agent_component/          # 共享组件
│   │   └── monitoring/           # 统一监控回调 (MonitoringCallback)
│   ├── fishing/                  # 钓鱼Agent包
│   │   ├── core/                 # Agent核心逻辑
│   │   ├── tools/                # 工具集合
│   │   │   └── user_equipment/   # 用户装备工具
│   │   ├── middleware/           # 中间件
│   │   └── utils/                # 工具函数
│   └── equipment_import/         # 装备导入Agent包
├── data_processing/              # 数据处理包
│   ├── image/                    # 图片处理
│   ├── ocr/                      # OCR识别
│   └── dedup/                    # 去重工具
└── scraper/                      # 爬虫框架包
    ├── spider/                   # 爬虫核心
    ├── platform/                 # 平台抽象
    └── workflow/                 # 工作流引擎

apps/                             # 应用层
├── cli/                          # CLI应用
├── api/                          # FastAPI后端
└── web-admin/                    # React管理前端

fishing_agent_app/                # 微信小程序
```

## 🔗 关键导入

```python
# Agent 核心功能
from packages.agents.fishing import FishingAgent, create_agent, get_all_tools
from packages.agents.fishing.tools import get_weather, query_fishing_recommendation
from packages.agents.fishing.utils import get_coordinates, parse_date_input

# 统一监控组件
from packages.agents.agent_component.monitoring import MonitoringCallback

# 装备导入功能
from packages.agents.equipment_import import EquipmentImportAgent
from packages.agents.equipment_import.core import TextCompressor

# 图片处理功能
from packages.data_processing.image import BatchMergeProcessor, ImageMerger

# OCR 功能
from packages.data_processing.ocr import OCRMergeProcessor

# 爬虫功能
from packages.scraper import BaseSpider, CrawlItem
```

## 🎨 开发约定

### 代码风格
- **Python**: 遵循PEP 8规范，使用black格式化
- **TypeScript**: 使用ESLint + Prettier格式化
- **提交信息**: 使用约定式提交格式

### 命名规范
- **文件名**: 使用snake_case (Python) 或 kebab-case (前端)
- **类名**: 使用PascalCase
- **函数名**: 使用snake_case
- **常量**: 使用UPPER_SNAKE_CASE

### 分支策略
- **main**: 主分支，稳定版本
- **develop**: 开发分支
- **feature/xxx**: 功能分支
- **hotfix/xxx**: 热修复分支

## 🧪 开发工具

### 推荐工具
- **IDE**: VS Code, PyCharm
- **API测试**: Postman, Insomnia
- **数据库**: SQLite Browser, pgAdmin
- **版本控制**: Git, GitHub Desktop

### VS Code扩展
- Python
- TypeScript and JavaScript Language Features
- Pylance
- ESLint
- Prettier
- GitLens
- Thunder Client (API测试)

## 📋 开发检查清单

### 代码提交前
- [ ] 代码通过所有测试
- [ ] 代码格式化检查通过
- [ ] 静态代码分析通过
- [ ] 文档已更新
- [ ] 提交信息符合规范

### 功能开发后
- [ ] 单元测试覆盖
- [ ] 集成测试通过
- [ ] API文档更新
- [ ] 用户文档更新
- [ ] 性能测试通过

## 🆘 获取帮助

### 技术支持
- **Issue**: [GitHub Issues](https://github.com/your-org/fishing-agent/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-org/fishing-agent/discussions)
- **邮件**: dev@fishing-agent.com

### 开发资源
- **API文档**: [API参考](../05-api-reference/)
- **架构文档**: [系统架构](../03-architecture/)
- **运维指南**: [部署运维](../04-operations/)
- **用户指南**: [用户文档](../01-user-guide/)

### 社区
- **开发者群**: 微信群、QQ群
- **技术博客**: 定期发布开发心得
- **开源贡献**: 欢迎提交PR和Issue

## 🎯 开发路线图

### 当前版本 v5.0.2
- [x] 微信小程序支持
- [x] 装备导入Agent
- [x] OCR多提供商
- [x] 智能图片合并

### 计划功能 v5.1.0
- [ ] 多语言支持
- [ ] 实时协作功能
- [ ] 高级数据分析
- [ ] 插件系统

### 长期规划
- [ ] 国际化支持
- [ ] AI模型微调
- [ ] 边缘计算支持
- [ ] 开放平台

## 📚 学习资源

### 推荐学习
- **LangChain**: [官方文档](https://python.langchain.com/)
- **FastAPI**: [官方教程](https://fastapi.tiangolo.com/tutorial/)
- **React**: [官方文档](https://react.dev/)
- **TypeScript**: [官方手册](https://www.typescriptlang.org/docs/)

### 最佳实践
- **Python最佳实践**: [Effective Python](https://effectivepython.com/)
- **API设计**: [RESTful API设计指南](https://restfulapi.net/)
- **前端架构**: [React最佳实践](https://react.dev/learn)

---

**指南版本**: v5.0.2  
**适用系统版本**: v5.0.2+  
**更新时间**: 2024-12-20