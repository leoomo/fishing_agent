<!-- OPENSPEC:START -->
<!-- OPENSPEC:END -->
-禁止自动执行git命令
# 智能钓鱼助手 v5.2.0

模块化 Agent 架构 + JWT认证系统 + React管理前端，基于 LangChain 1.0+ 和 7 因子科学评分系统。

**当前版本**: v5.2.0 | **当前分支**: feat/crawler-data-persistence (数据库模型迁移)

## 核心特性
- JWT认证系统 (RBAC权限管理 + Token安全) + 模块化Agent包 + 7因子评分 (温度/天气/风力/气压/湿度/季节/月相)
- 时间段意图识别 (98%+准确率) + 动态Prompt中间件 + 装备管理UI优化
- 智能图片合并 (自动检测文字 + 批量处理 + 本地化处理) + OCR多提供商支持 (Ollama本地 + SiliconFlow云端)
- 路亚装备管理系统 + 数据分析报表 (装备统计/趋势分析/品牌排行) + 系统配置管理 (API密钥/参数配置)
- React管理前端 (React 19.2.0 + TypeScript + Ant Design 5.22.0) + 微信小程序 (uni-app) + 爬虫监控模块 + 工作流管理系统

## 架构
```
packages/                       # 模块化包目录
├── agents/                     # Agent 统一目录 (v5.1.0 重构)
│   ├── agent_component/        # 共享组件
│   │   └── monitoring/         # 统一监控回调 (MonitoringCallback)
│   ├── fishing/                # 钓鱼助手 Agent
│   │   ├── core/               # agent.py, model_factory.py, prompts.py
│   │   ├── tools/              # basic, weather, fishing, lure/, scoring/
│   │   │   └── lure/           # 路亚工具 (兼容层，重导出 apps.api)
│   │   ├── middleware/         # dynamic_prompt.py
│   │   └── utils/
│   └── equipment_import/       # 装备导入 Agent
│       ├── core/               # agent.py, extractor.py
│       ├── tools/              # 导入工具
│       └── middleware/         # 文本压缩
├── data_processing/            # 数据处理包
│   ├── image/                  # 图片处理 (ImageMerger, BatchMergeProcessor)
│   ├── ocr/                    # OCR文字检测 (TextRegionDetector)
│   └── dedup/                  # 去重工具
└── scraper/                    # 爬虫框架包
    ├── spider/                 # 爬虫核心 (BaseSpider, CrawlItem)
    ├── spiders/                # 具体爬虫实现 (taobao, jd, forum)
    ├── rpa/                    # RPA自动化框架
    ├── platform/               # 平台抽象层
    ├── workflow/               # 工作流引擎
    ├── executor/               # 任务执行器
    ├── monitoring/             # 监控告警
    ├── scheduler/              # 定时调度
    ├── persister/              # 数据持久化
    └── models/                 # 独立的爬虫模型
apps/                           # 应用层
├── cli/                        # CLI应用 (main.py)
├── api/                        # FastAPI后端
│   ├── main.py                 # API服务器
│   ├── auth/                   # JWT认证模块
│   ├── middleware/             # 认证中间件
│   ├── routes/                 # API路由
│   ├── schemas/                # 请求/响应模型
│   ├── services/               # 业务服务层
│   ├── models/                 # ⭐ 数据库模型 (v5.2.0 迁移)
│   ├── orm/                    # ⭐ ORM层 (v5.2.0 迁移)
│   │   ├── session.py          # 会话管理
│   │   └── repositories/       # 仓储模式
│   └── database.py             # ⭐ 数据库访问 (v5.2.0 迁移)
└── web-admin/                  # React管理前端
miniprogram/                    # 微信小程序
shared/                         # 共享资源
├── config/                     # 全局配置
└── data/                       # ⭐ 数据库文件 (equipment.db)
```

## 快速开始
```bash
uv sync                                    # 安装依赖
cp .env.example .env                       # 配置环境
uv run python main.py                      # 运行CLI
uv run uvicorn apps.api.main:app --reload # 运行API
cd apps/web-admin && npm run dev          # 运行React前端
```

## 关键导入
```python
# Agent 核心功能 (v5.1.0 新路径)
from packages.agents.fishing import FishingAgent, create_agent, get_all_tools
from packages.agents.fishing.core import ModelFactory
from packages.agents.fishing.tools import get_weather, query_fishing_recommendation
from packages.agents.fishing.utils import get_coordinates, parse_date_input

# 统一监控组件 (v5.1.0 新增)
from packages.agents.agent_component.monitoring import MonitoringCallback

# 装备导入功能
from packages.agents.equipment_import import EquipmentImportAgent
from packages.agents.equipment_import.core import TextCompressor

# 数据库模型和 ORM (v5.2.0 迁移到 apps.api)
from apps.api.models import Base, Equipment, Brand, AdminUser, ChatSession
from apps.api.orm import get_db_session, EquipmentRepository, BrandRepository
from apps.api.database import LureDatabase, get_db

# 数据处理功能
from packages.data_processing.image import BatchMergeProcessor, ImageMerger
from packages.data_processing.ocr import OCRMergeProcessor
from packages.data_processing.dedup import Deduplicator

# 爬虫功能
from packages.scraper import BaseSpider, CrawlItem
from packages.scraper.spiders import TaobaoSpider, JDSpider, ForumSpider
from packages.scraper.rpa import TaobaoRPA
from packages.scraper.workflow import WorkflowManager
```

## API端点
```
# 核心API
POST /api/v1/fishing/chat           # 对话接口
GET  /api/v1/fishing/tools          # 工具列表
GET  /health                        # 健康检查

# 认证API
POST /api/v1/auth/login             # 用户登录
GET  /api/v1/auth/me                # 获取用户信息
POST /api/v1/auth/wechat/login      # 微信登录
POST /api/v1/auth/wechat/bind       # 绑定微信账号

# 功能API
POST /api/v1/ocr/recognize-table    # OCR表格识别
GET  /api/v1/ocr/status             # OCR服务状态

# 管理API
GET  /api/v1/admin/analytics/equipment/stats    # 装备统计
GET  /api/v1/admin/analytics/equipment/trends   # 趋势分析
POST /api/v1/admin/analytics/reports/generate   # 生成报表
GET  /api/v1/admin/config/configs               # 查询配置
POST /api/v1/admin/config/configs               # 创建配置
GET  /api/v1/admin/crawler/tasks                # 爬虫任务列表
POST /api/v1/admin/crawler/tasks/trigger        # 触发爬虫
GET  /api/v1/admin/monitor/api-stats            # API统计
GET  /api/v1/admin/monitor/llm-stats            # LLM统计
```

## 环境变量
```bash
# 必需
CAIYUN_API_KEY=xxx           # 彩云天气
AMAP_API_KEY=xxx             # 高德地图
DASHSCOPE_API_KEY=xxx        # 通义千问 + Embedding
ANTHROPIC_AUTH_TOKEN=xxx     # 智谱AI (推荐)

# JWT认证
JWT_SECRET_KEY=xxx           # JWT密钥 (必须设置)
JWT_ALGORITHM=HS256          # JWT算法
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # Token过期时间(分钟)

# 微信小程序
WECHAT_APPID=xxx            # 微信小程序AppID
WECHAT_SECRET=xxx           # 微信小程序AppSecret
WECHAT_AUTO_CREATE_USER=true # 是否自动创建新用户
```

## 新增Agent模板
```bash
mkdir -p packages/agents/xxx/{core,tools,utils}
# __init__.py: from .core import XxxAgent, create_agent
# 使用 agent_component.monitoring.MonitoringCallback 作为统一监控
```

## 架构原则
1. Agent统一管理 (packages/agents/) | 2. 共享组件抽取 (agent_component) | 3. 同步优先 (requests) | 4. 诚实数据 (无假数据) | 5. LangChain 1.0+ (@tool装饰器)

## 包依赖说明
- **apps/api/models**: 数据库模型（v5.2.0 从 lure 迁移）
- **apps/api/orm**: ORM 层和仓储模式（v5.2.0 从 lure 迁移）
- **apps/api/database**: 数据库访问层（v5.2.0 从 lure 迁移）
- **agents/fishing**: 钓鱼助手Agent，使用统一监控组件
- **agents/fishing/tools/lure**: 路亚工具（兼容层，重导出 apps.api）
- **agents/equipment_import**: 装备导入Agent，使用统一监控组件
- **agents/agent_component**: 共享组件（MonitoringCallback等）
- **data_processing**: 数据处理包，独立可用
- **scraper**: 爬虫框架包，独立可用

## 文档导航

### 文档中心 (docs/)

#### [用户指南](docs/01-user-guide/)
- [快速开始](docs/01-user-guide/getting-started.md) - 5分钟上手
- [基础功能](docs/01-user-guide/basic-features.md) - 核心功能
- [故障排除](docs/01-user-guide/troubleshooting.md) - 问题解决
- [常见问题](docs/01-user-guide/faq.md) - 用户FAQ

#### [开发者指南](docs/02-developer-guide/)
- [环境配置](docs/02-developer-guide/environment-setup.md) - 环境搭建
- [代码结构](docs/02-developer-guide/codebase-structure.md) - 项目架构
- [开发流程](docs/02-developer-guide/development-workflows.md) - 开发规范
- [测试指南](docs/02-developer-guide/testing.md) - 测试策略

#### [架构设计](docs/03-architecture/)
- [系统设计](docs/03-architecture/system-design.md) - 整体架构和设计原则
- [架构概览](docs/03-architecture/README.md) - 架构文档导航

#### [运维部署](docs/04-operations/)
- [运维概览](docs/04-operations/README.md) - 运维文档导航

#### [API参考](docs/05-api-reference/)
- [API概览](docs/05-api-reference/README.md) - 完整API文档和接口说明

#### [专题指南](docs/06-guides/)
- [图片处理](docs/06-guides/image-processing.md) - OCR和图片处理
- [小程序集成](docs/06-guides/miniprogram-integration.md) - 微信小程序开发
- [装备导入](docs/06-guides/equipment-import.md) - 装备数据导入
- [性能优化](docs/06-guides/performance-optimization.md) - 系统性能优化

#### [归档文档](docs/archive/)
- [归档中心](docs/archive/README.md) - 历史文档导航
