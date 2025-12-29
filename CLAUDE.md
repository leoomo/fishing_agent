<!-- OPENSPEC:START -->
<!-- OPENSPEC:END -->
-禁止自动执行git命令
# 智能钓鱼助手 v5.0.2

模块化 Agent 架构 + JWT认证系统 + React管理前端，基于 LangChain 1.0+ 和 7 因子科学评分系统。

**当前版本**: v5.0.2 | **当前分支**: feat/ocr-optimization

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
│   │   ├── tools/              # basic, weather, fishing, lure/, user_equipment/
│   │   │   ├── lure/           # 路亚工具 (兼容层，重导出 apps.api)
│   │   │   └── user_equipment/ # 用户装备管理 (manager, recommender)
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
fishing_agent_app/             # 微信小程序
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

# 用户装备管理
from packages.agents.fishing.tools.user_equipment import (
    UserEquipmentManager,
    EquipmentRecommender
)

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
POST /api/v1/chat/message           # 聊天消息
GET  /api/v1/chat/sessions          # 会话列表

# 认证API
POST /api/v1/auth/login             # 用户登录
GET  /api/v1/auth/me                # 获取用户信息
POST /api/v1/auth/wechat/login      # 微信登录
POST /api/v1/auth/wechat/bind       # 绑定微信账号

# 用户装备API
GET  /api/v1/user-equipment/equipment          # 用户装备列表
POST /api/v1/user-equipment/equipment          # 添加装备
PUT  /api/v1/user-equipment/equipment/{id}     # 更新装备
DELETE /api/v1/user-equipment/equipment/{id}   # 删除装备
GET  /api/v1/user-equipment/recommendations    # 装备推荐
POST /api/v1/user-equipment/recommend          # 获取推荐

# 装备管理API
GET  /api/v1/equipment/equipment       # 装备列表
POST /api/v1/equipment/batch            # 批量添加
PUT  /api/v1/equipment/equipment/{id}   # 更新装备
DELETE /api/v1/equipment/equipment/{id} # 删除装备
GET  /api/v1/equipment/attributes       # 属性选项

# 数据导入API
POST /api/v1/import-export/import           # 导入装备
POST /api/v1/import-export/export           # 导出装备
POST /api/v1/import-export/preview          # 预览导入
GET  /api/v1/import-export/templates        # 导入模板

# OCR API
POST /api/v1/ocr/recognize-table    # OCR表格识别
GET  /api/v1/ocr/status             # OCR服务状态
POST /api/v1/ocr/workflow/execute   # OCR工作流

# 爬虫API
GET  /api/v1/crawler/tasks                # 采集任务列表
POST /api/v1/crawler/tasks                # 创建任务
PUT  /api/v1/crawler/tasks/{id}           # 更新任务
DELETE /api/v1/crawler/tasks/{id}         # 删除任务
POST /api/v1/crawler/tasks/{id}/trigger   # 触发任务
GET  /api/v1/crawler/tasks/{id}/logs      # 任务日志

# Worker API
GET  /api/v1/worker/status                # Worker状态
GET  /api/v1/worker/tasks                 # 待领取任务
POST /api/v1/worker/tasks/{id}/claim      # 领取任务
POST /api/v1/worker/tasks/{id}/complete   # 完成任务

# OCR Worker API
GET  /api/v1/ocr-worker/status            # OCR Worker状态
POST /api/v1/ocr-worker/process           # 处理OCR任务
GET  /api/v1/ocr-worker/queue             # 任务队列

# 数据工作流API
GET  /api/v1/admin/workflow/stats         # 工作流统计
GET  /api/v1/admin/workflow/workers       # Worker列表
GET  /api/v1/admin/workflow/ocr/tasks     # OCR任务列表
POST /api/v1/admin/workflow/ocr/tasks/{id}/retry  # 重试任务
GET  /api/v1/admin/workflow/review/tasks   # 审核任务列表
POST /api/v1/admin/workflow/review/tasks/{id}/review  # 审核任务

# 监控API
GET  /api/v1/admin/monitor/api-stats            # API统计
GET  /api/v1/admin/monitor/llm-stats            # LLM统计
GET  /api/v1/admin/monitor/crawler-stats        # 采集统计
GET  /api/v1/admin/monitor/agent-stats          # Agent统计

# 数据分析API
GET  /api/v1/admin/analytics/equipment/stats    # 装备统计
GET  /api/v1/admin/analytics/equipment/trends   # 趋势分析
POST /api/v1/admin/analytics/reports/generate   # 生成报表

# 配置管理API
GET  /api/v1/admin/config/configs               # 查询配置
POST /api/v1/admin/config/configs               # 创建配置
PUT  /api/v1/admin/config/configs/{id}          # 更新配置
DELETE /api/v1/admin/config/configs/{id}        # 删除配置

# 用户管理API
GET  /api/v1/admin/users/users                 # 用户列表
GET  /api/v1/admin/users/{id}                   # 用户详情
PUT  /api/v1/admin/users/{id}                   # 更新用户
DELETE /api/v1/admin/users/{id}                 # 删除用户
GET  /api/v1/admin/users/{id}/equipment         # 用户装备
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
