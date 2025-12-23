<!-- OPENSPEC:START -->
<!-- OPENSPEC:END -->
-禁止自动执行git命令
# 智能钓鱼助手 v5.0.2

模块化 Agent 架构 + JWT认证系统 + React管理前端，基于 LangChain 1.0+ 和 7 因子科学评分系统。

**当前版本**: v5.0.2 | **当前分支**: feature/miniprogram-dev (文档重构完成)

## 核心特性
- JWT认证系统 (RBAC权限管理 + Token安全) + 模块化Agent包 + 7因子评分 (温度/天气/风力/气压/湿度/季节/月相)
- 时间段意图识别 (98%+准确率) + 动态Prompt中间件 + 装备管理UI优化
- 智能图片合并 (自动检测文字 + 批量处理 + 本地化处理) + OCR多提供商支持 (Ollama本地 + SiliconFlow云端)
- 路亚装备管理系统 + 数据分析报表 (装备统计/趋势分析/品牌排行) + 系统配置管理 (API密钥/参数配置)
- React管理前端 (React 19.2.0 + TypeScript + Ant Design 5.22.0) + 微信小程序 (uni-app) + 爬虫监控模块 + 工作流管理系统

## 架构
```
packages/                   # 模块化包目录
├── agent_fishing/          # 自包含Agent包
│   ├── core/               # agent.py, model_factory.py, prompts.py, callbacks.py
│   │   └── middleware/     # dynamic_prompt.py
│   ├── tools/              # basic, weather, fishing, lure_tools, lure/, scoring/
│   │   └── lure/           # 路亚装备工具（装备推荐、对比、知识查询）
│   └── utils/
├── data_processing/        # 数据处理包 ⭐ v5.0.2新增
│   ├── image/              # 图片处理 (ImageMerger, BatchMergeProcessor)
│   ├── ocr/                # OCR文字检测 (TextRegionDetector)
│   └── dedup/              # 去重工具
└── scraper/                # 爬虫框架包 ⭐ v5.0.2新增
    ├── spider/             # 爬虫核心 (BaseSpider, CrawlItem)
    ├── spiders/            # 具体爬虫实现 (taobao, jd, forum)
    ├── rpa/                # RPA自动化框架
    ├── platform/           # 平台抽象层
    ├── workflow/           # 工作流引擎
    ├── executor/           # 任务执行器
    ├── monitoring/         # 监控告警
    ├── scheduler/          # 定时调度
    ├── persister/          # 数据持久化
    └── models/             # 独立的爬虫模型 (CrawlerTask, CrawlerLog等)
apps/                       # 应用层
├── cli/                    # CLI应用 (main.py)
├── api/                    # FastAPI后端
│   ├── main.py             # API服务器 (v5.0.0)
│   ├── auth/               # JWT认证模块
│   ├── middleware/         # 认证中间件
│   ├── routes/             # API路由
│   │   ├── analytics.py    # 数据分析路由 ⭐ v5.0.0新增
│   │   ├── config.py       # 配置管理路由 ⭐ v5.0.0新增
│   │   ├── crawler.py      # 爬虫管理路由 ⭐ v4.0.0新增
│   │   └── monitor.py      # 监控管理路由 ⭐ v4.0.0新增
│   ├── schemas/            # 数据模型
│   └── services/           # 业务服务层 ⭐ v5.0.0新增
└── web-admin/              # React管理前端 ⭐ v5.0.0新增
    ├── src/                # 源代码
    │   ├── components/     # 通用组件
    │   ├── pages/          # 页面组件
    │   └── services/       # API服务
    └── package.json        # 前端依赖配置
miniprogram/                # 微信小程序 ⭐ v5.0.2新增
    ├── fishing_agent/      # 小程序主体 (基于uni-app)
    │   ├── pages/          # 页面 (登录、聊天、首页)
    │   ├── api/            # API封装
    │   ├── store/          # 状态管理
    │   ├── static/         # 静态资源
    │   └── manifest.json   # 小程序配置
    └── unpackage/          # 编译输出目录
shared/                     # 共享资源
├── config/                 # 全局配置
└── data/                   # 共享数据
```

## 快速开始
```bash
uv sync                                    # 安装依赖
cp .env.example .env                       # 配置环境
uv run python main.py                      # 运行CLI
uv run uvicorn apps.api.main:app --reload # 运行API
cd apps/web-admin && npm run dev          # 运行React前端 (v5.0.0新增)

# 微信小程序 (v5.0.2新增)
# 1. 使用微信开发者工具打开 miniprogram/fishing_agent/
# 2. 配置小程序AppID和服务器域名
# 3. 在本地设置中关闭"不校验合法域名"选项
```

## 关键导入
```python
# Agent 核心功能
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools
from packages.agent_fishing.core import ModelFactory
from packages.agent_fishing.tools import get_weather, query_fishing_recommendation
from packages.agent_fishing.utils import get_coordinates, parse_date_input

# 数据处理功能（位于 data_processing 包）
from packages.data_processing.image import BatchMergeProcessor, ImageMerger
from packages.data_processing.ocr import OCRMergeProcessor
from packages.data_processing.dedup import Deduplicator

# 爬虫功能（位于 scraper 包）
from packages.scraper import BaseSpider, CrawlItem
from packages.scraper.spiders import TaobaoSpider, JDSpider, ForumSpider
from packages.scraper.rpa import TaobaoRPA
from packages.scraper.workflow import WorkflowManager

# 装备导入功能（v5.0.2新增）
from packages.agent_equipment_import import EquipmentImportAgent
from packages.agent_equipment_import.core import TextCompressor
```

## API端点
```
# 核心API
POST /api/v1/fishing/chat           # 对话接口
GET  /api/v1/fishing/tools          # 工具列表
GET  /health                        # 健康检查

# 认证API
POST /api/v1/auth/login             # 用户登录 (v3.1.1)
GET  /api/v1/auth/me                # 获取用户信息
POST /api/v1/auth/wechat/login      # 微信登录 (v5.0.2)
POST /api/v1/auth/wechat/bind       # 绑定微信账号

# 功能API
POST /api/v1/ocr/recognize-table    # OCR表格识别 (v5.0.2)
GET  /api/v1/ocr/status             # OCR服务状态

# 管理API
GET  /api/v1/admin/analytics/equipment/stats    # 装备统计 (v5.0.0)
GET  /api/v1/admin/analytics/equipment/trends   # 趋势分析
POST /api/v1/admin/analytics/reports/generate   # 生成报表
GET  /api/v1/admin/config/configs               # 查询配置 (v5.0.0)
POST /api/v1/admin/config/configs               # 创建配置
POST /api/v1/admin/config/configs/test-api-key  # 测试API密钥
GET  /api/v1/admin/crawler/tasks                # 爬虫任务列表 (v4.0.0)
POST /api/v1/admin/crawler/tasks/trigger        # 触发爬虫
GET  /api/v1/admin/monitor/api-stats            # API统计 (v4.0.0)
GET  /api/v1/admin/monitor/llm-stats             # LLM统计
```

## 环境变量
```bash
# 必需
CAIYUN_API_KEY=xxx           # 彩云天气
AMAP_API_KEY=xxx             # 高德地图
DASHSCOPE_API_KEY=xxx        # 通义千问 + Embedding
ANTHROPIC_AUTH_TOKEN=xxx     # 智谱AI (推荐)

# JWT认证 (v3.1.1新增)
JWT_SECRET_KEY=xxx           # JWT密钥 (必须设置)
JWT_ALGORITHM=HS256          # JWT算法
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # Token过期时间(分钟)

# 微信小程序 (v5.0.2新增)
WECHAT_APPID=xxx            # 微信小程序AppID
WECHAT_SECRET=xxx           # 微信小程序AppSecret
WECHAT_AUTO_CREATE_USER=true # 是否自动创建新用户
```

## 新增Agent模板
```bash
mkdir -p packages/agent_xxx/{core,tools,utils}
# __init__.py: from .core import XxxAgent, create_agent
# langgraph.json: "xxx": "./packages/agent_xxx:get_agent"
```

## 架构原则
1. Agent自包含 (独立发布) | 2. 基础设施模块化 (scraper/data_processing独立) | 3. 同步优先 (requests) | 4. 诚实数据 (无假数据) | 5. LangChain 1.0+ (@tool装饰器)

## 包依赖说明
- **agent_fishing**: 核心Agent包，独立自包含
- **data_processing**: 数据处理包，独立可用，不依赖agent_fishing
- **scraper**: 爬虫框架包，独立可用，通过configure_database()接收数据库连接

## 📚 文档导航

### 📖 文档中心 (docs/)
重新组织为面向角色的清晰结构：

#### 🎯 [用户指南](docs/01-user-guide/)
- [快速开始](docs/01-user-guide/getting-started.md) - 5分钟上手
- [基础功能](docs/01-user-guide/basic-features.md) - 核心功能
- [故障排除](docs/01-user-guide/troubleshooting.md) - 问题解决
- [常见问题](docs/01-user-guide/faq.md) - 用户FAQ

#### 💻 [开发者指南](docs/02-developer-guide/)
- [环境配置](docs/02-developer-guide/environment-setup.md) - 环境搭建
- [代码结构](docs/02-developer-guide/codebase-structure.md) - 项目架构
- [开发流程](docs/02-developer-guide/development-workflows.md) - 开发规范
- [测试指南](docs/02-developer-guide/testing.md) - 测试策略

#### 🏗️ [架构设计](docs/03-architecture/)
- [系统设计](docs/03-architecture/system-design.md) - 整体架构和设计原则
- [架构概览](docs/03-architecture/README.md) - 架构文档导航

#### 🔧 [运维部署](docs/04-operations/)
- [运维概览](docs/04-operations/README.md) - 运维文档导航

#### 📡 [API参考](docs/05-api-reference/)
- [API概览](docs/05-api-reference/README.md) - 完整API文档和接口说明

#### 📖 [专题指南](docs/06-guides/)
- [图片处理](docs/06-guides/image-processing.md) - OCR和图片处理
- [小程序集成](docs/06-guides/miniprogram-integration.md) - 微信小程序开发
- [装备导入](docs/06-guides/equipment-import.md) - 装备数据导入
- [性能优化](docs/06-guides/performance-optimization.md) - 系统性能优化

#### 📦 [归档文档](docs/archive/)
- [归档中心](docs/archive/README.md) - 历史文档导航
