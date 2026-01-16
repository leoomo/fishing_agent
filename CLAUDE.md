<!-- OPENSPEC:START -->
<!-- OPENSPEC:END -->
-禁止自动执行git命令,除非我明确指令
# 智能钓鱼助手 v5.1.0

模块化 Agent 架构 + JWT认证系统 + React管理前端，基于 LangChain 1.0+ 和 7 因子科学评分系统。

**当前版本**: v5.1.0 | **当前分支**: feature/analytics-optimization

## 核心特性
### 🆕 新增功能 (v5.1.0)
- **鱼百科管理** - 鱼种知识库、季节活动规律、装备推荐查询
- **内容管理系统** - 富文本编辑器、自动保存草稿、语义搜索、向量检索（ChromaDB）
- **文章网络采集** - 从维基百科采集钓鱼知识，LLM翻译增强，草稿审核流程
- **Excel批量导入** - 批量导入装备数据到待审核队列、模板生成系统
- **向量搜索** - 基于ChromaDB的语义搜索和DashScope Embedding
- **配件管理** - 钩子、铅坠、转环、前导线等配件完整管理
- **拟饵类型** - 硬饵、软饵、金属饵、飞蝇分类体系
- **钓组配置** - 德州钓组、卡罗莱纳钓组、倒吊钓组等模板

### 核心功能
- JWT认证系统 (RBAC权限管理 + Token安全) + 模块化Agent包 + 7因子评分 (温度/天气/风力/气压/湿度/季节/月相)
- 时间段意图识别 (98%+准确率) + 动态Prompt中间件 + 装备管理UI优化
- 智能图片合并 (自动检测文字 + 批量处理 + 本地化处理) + OCR多提供商支持 (Ollama本地 + SiliconFlow云端)
- 路亚装备管理系统 + 数据分析报表 (装备统计/趋势分析/品牌排行/价格分布/SQL优化) + 系统配置管理 (API密钥/参数配置)
- React管理前端 (React 19.2.0 + TypeScript + Ant Design 5.22.0) + 微信小程序 (uni-app) + 爬虫监控模块 + 数据工作流系统（五合一：采集/OCR/导入/审核/监控）

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
│   │   ├── fish.py             # 🆕 鱼百科管理
│   │   ├── article.py          # 🆕 内容管理
│   │   ├── accessory.py        # 🆕 配件管理
│   │   ├── lure_type.py        # 🆕 拟饵类型
│   │   ├── rig.py              # 🆕 钓组配置
│   │   ├── data_workflow.py    # 🔄 数据工作流（重构）
│   │   └── analytics.py        # 🔄 数据分析（优化）
│   ├── schemas/                # 请求/响应模型
│   ├── services/               # 业务服务层
│   │   ├── vector_store.py     # 🆕 向量存储服务
│   │   ├── article_fetcher.py  # 🆕 文章网络采集服务
│   │   ├── excel_import_service.py  # 🆕 Excel导入服务
│   │   └── analytics_service.py # 🔄 数据分析服务（优化）
│   ├── models/                 # ⭐ 数据库模型 (v5.2.0 迁移)
│   │   ├── fish.py             # 🆕 鱼百科模型
│   │   ├── article.py          # 🆕 文章模型
│   │   ├── accessory.py        # 🆕 配件模型
│   │   └── rig.py              # 🆕 钓组模型
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
from apps.api.models.fish import FishSpecies, FishKnowledge, FishSeasonActivity  # 🆕
from apps.api.models.article import Article  # 🆕
from apps.api.models.accessory import Accessory  # 🆕
from apps.api.models.rig import RigType, RigSpec, RigComponent  # 🆕
from apps.api.orm import get_db_session, EquipmentRepository, BrandRepository
from apps.api.database import LureDatabase, get_db

# 🆕 向量搜索服务
from apps.api.services.vector_store import ArticleVectorStore

# 🆕 文章网络采集服务
from apps.api.services.article_fetcher import ArticleFetcherService, get_article_fetcher_service

# 🆕 Excel导入服务
from apps.api.services.excel_import_service import ExcelImportService

# 🔄 数据分析服务 (优化)
from apps.api.services.analytics_service import AnalyticsService

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

# 🆕 鱼百科管理API
GET    /api/v1/fish-species              # 鱼种列表
POST   /api/v1/fish-species              # 创建鱼种
GET    /api/v1/fish-species/{id}         # 鱼种详情
PUT    /api/v1/fish-species/{id}         # 更新鱼种
DELETE /api/v1/fish-species/{id}         # 删除鱼种
GET    /api/v1/fish-knowledge            # 知识库列表
POST   /api/v1/fish-knowledge            # 创建知识
GET    /api/v1/fish-seasons              # 季节活动列表
POST   /api/v1/fish-seasons              # 创建季节活动
GET    /api/v1/fish-species/{id}/equipment  # 装备推荐
GET    /api/v1/fish-species/stats/stats    # 分类统计
GET    /api/v1/fish-species/init-data       # 初始化数据

# 🆕 内容管理API
POST   /api/v1/articles                  # 创建文章（草稿）
GET    /api/v1/articles                  # 文章列表（支持过滤）
GET    /api/v1/articles/{id}             # 文章详情
PUT    /api/v1/articles/{id}             # 更新文章（自动保存）
DELETE /api/v1/articles/{id}             # 删除文章
POST   /api/v1/articles/{id}/publish     # 发布文章
POST   /api/v1/articles/{id}/archive     # 归档文章
GET    /api/v1/articles/search           # 语义搜索
GET    /api/v1/articles/{id}/similar     # 相似文章

# 🆕 文章网络采集API
GET    /api/v1/articles/fetch/sources    # 获取可用数据源
GET    /api/v1/articles/fetch/progress   # 获取采集进度
POST   /api/v1/articles/fetch/start      # 开始采集
POST   /api/v1/articles/fetch/pause      # 暂停采集
POST   /api/v1/articles/fetch/retry      # 重试失败项
POST   /api/v1/articles/fetch/reset      # 重置进度

# 🆕 配件管理API
GET    /api/v1/accessory          # 配件列表
POST   /api/v1/accessory          # 创建配件
GET    /api/v1/accessory/{id}     # 配件详情
PUT    /api/v1/accessory/{id}     # 更新配件
DELETE /api/v1/accessory/{id}     # 删除配件
GET    /api/v1/accessory/options  # 配件选项数据
GET    /api/v1/accessory/init-data  # 初始化数据

# 🆕 拟饵类型API
GET    /api/v1/lure-types          # 拟饵类型列表
POST   /api/v1/lure-types          # 创建拟饵类型
GET    /api/v1/lure-types/{id}     # 拟饵类型详情
PUT    /api/v1/lure-types/{id}     # 更新拟饵类型
DELETE /api/v1/lure-types/{id}     # 删除拟饵类型
GET    /api/v1/lure-types/init-data  # 初始化数据

# 🆕 钓组配置API
GET    /api/v1/rigs                # 钓组列表
POST   /api/v1/rigs                # 创建钓组
GET    /api/v1/rigs/{id}           # 钓组详情
PUT    /api/v1/rigs/{id}           # 更新钓组
DELETE /api/v1/rigs/{id}           # 删除钓组
GET    /api/v1/rigs/options        # 钓组选项数据

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

# 🔄 数据工作流API（重构）
GET  /api/v1/admin/workflow/stats         # 工作流统计
GET  /api/v1/admin/workflow/workers       # Worker列表
GET  /api/v1/admin/workflow/ocr/tasks     # OCR任务列表
POST /api/v1/admin/workflow/ocr/tasks/{id}/retry  # 重试任务
GET  /api/v1/admin/workflow/review/tasks   # 审核任务列表
POST /api/v1/admin/workflow/review/tasks/{id}/review  # 审核任务
POST /api/v1/admin/workflow/import/templates  # 🆕 生成导入模板
POST /api/v1/admin/workflow/import/preview    # 🆕 预览导入
POST /api/v1/admin/workflow/import/execute    # 🆕 执行导入

# 监控API
GET  /api/v1/admin/monitor/api-stats            # API统计
GET  /api/v1/admin/monitor/llm-stats            # LLM统计
GET  /api/v1/admin/monitor/crawler-stats        # 采集统计
GET  /api/v1/admin/monitor/agent-stats          # Agent统计

# 🔄 数据分析API（优化）
GET  /api/v1/admin/analytics/equipment/stats         # 装备统计
GET  /api/v1/admin/analytics/equipment/trends        # 趋势分析
GET  /api/v1/admin/analytics/equipment/price-distribution  # 🆕 价格分布
GET  /api/v1/admin/analytics/equipment/brand-stats     # 🆕 品牌统计
GET  /api/v1/admin/analytics/users/activity           # 🆕 用户活动
POST /api/v1/admin/analytics/reports/generate         # 生成报表

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
DASHSCOPE_API_KEY=xxx        # 通义千问 + Embedding (向量搜索需要)
ANTHROPIC_AUTH_TOKEN=xxx     # 智谱AI (推荐)

# JWT认证
JWT_SECRET_KEY=xxx           # JWT密钥 (必须设置)
JWT_ALGORITHM=HS256          # JWT算法
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # Token过期时间(分钟)

# 微信小程序
WECHAT_APPID=xxx            # 微信小程序AppID
WECHAT_SECRET=xxx           # 微信小程序AppSecret
WECHAT_AUTO_CREATE_USER=true # 是否自动创建新用户

# 🆕 向量数据库 (可选)
CHROMA_PERSIST_DIR=shared/data/chroma  # ChromaDB持久化目录

# 🆕 OCR配置
OCR_PROVIDER=ollama          # OCR提供商: ollama/siliconflow
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-ocr
SILICONFLOW_API_KEY=xxx
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
- **apps/api/models**: 数据库模型（v5.2.0 从 lure 迁移，新增 fish/article/accessory/rig 模型）
- **apps/api/orm**: ORM 层和仓储模式（v5.2.0 从 lure 迁移）
- **apps/api/database**: 数据库访问层（v5.2.0 从 lure 迁移）
- **apps/api/services**: 业务服务层（新增 vector_store/article_fetcher/excel_import_service/analytics_service）
- **agents/fishing**: 钓鱼助手Agent，使用统一监控组件
- **agents/fishing/tools/lure**: 路亚工具（兼容层，重导出 apps.api，新增 diff_analyzer/specs_extractor）
- **agents/equipment_import**: 装备导入Agent，使用统一监控组件，支持Excel导入
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
