<!-- OPENSPEC:START -->
# OpenSpec 快速参考

## TL;DR 检查清单
- 搜索现有工作: `openspec list`, `openspec list --specs`
- 选择唯一的 `change-id`: kebab-case, 动词开头 (`add-`, `update-`, `remove-`, `refactor-`)
- 验证: `openspec validate <id> --strict`
- 归档: `openspec archive <change-id> --yes`

## 三阶段工作流
1. **创建变更** - `changes/<id>/` 目录: `proposal.md`, `tasks.md`, `specs/*/spec.md`
2. **实施变更** - 按tasks.md顺序完成，全部完成后标记 `[x]`
3. **归档变更** - 部署后移动到 `changes/archive/`，更新specs/

## 核心CLI命令
```bash
openspec list                  # 列出活跃变更
openspec list --specs          # 列出规范
openspec show <item>           # 显示详情
openspec validate <id> --strict # 验证变更
openspec archive <id> --yes    # 归档变更
```

> 📖 **详细OpenSpec规范**: 参考 `openspec/AGENTS.md` 获取完整文档

<!-- OPENSPEC:END -->

---

# 智能钓鱼助手 - AI助手参考

**版本**: v5.0.2 | **分支**: feature/miniprogram-dev

## 项目概览
模块化Agent架构 + JWT认证 + React管理前端 + 微信小程序，基于LangChain 1.0+和7因子科学评分系统。

### 核心特性
- **Agent**: 模块化Agent包 + 7因子评分 (温度/天气/风力/气压/湿度/季节/月相)
- **认证**: JWT认证 (RBAC权限) + 微信登录
- **前端**: React 19.2.0 + TypeScript + Ant Design 5.22.0 + uni-app小程序
- **数据**: 图片合并 + OCR多提供商 (Ollama本地 + SiliconFlow云端)
- **爬虫**: 工作流引擎 + 任务调度 + 监控告警

## 目录结构
```
packages/
├── agent_fishing/         # 核心Agent包 (自包含)
├── data_processing/       # 数据处理包 (独立可用)
└── scraper/               # 爬虫框架包 (独立可用)
apps/
├── cli/                   # CLI应用
├── api/                   # FastAPI后端
└── web-admin/             # React管理前端
miniprogram/               # 微信小程序 (uni-app)
shared/
├── config/                # 全局配置
└── data/                  # 共享数据
```

## 关键导入

### Agent核心功能
```python
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools
from packages.agent_fishing.core import ModelFactory
from packages.agent_fishing.tools import get_weather, query_fishing_recommendation
from packages.agent_fishing.utils import get_coordinates, parse_date_input
```

### 数据处理功能
```python
from packages.data_processing.image import BatchMergeProcessor, ImageMerger
from packages.data_processing.ocr import OCRMergeProcessor
from packages.data_processing.dedup import Deduplicator
```

### 爬虫功能
```python
from packages.scraper import BaseSpider, CrawlItem
from packages.scraper.spiders import TaobaoSpider, JDSpider, ForumSpider
from packages.scraper.rpa import TaobaoRPA
from packages.scraper.workflow import WorkflowManager
```

### 装备导入功能
```python
from packages.agent_equipment_import import EquipmentImportAgent
from packages.agent_equipment_import.core import TextCompressor
```

## API端点

### 核心API
```
POST /api/v1/fishing/chat           # 对话接口
GET  /api/v1/fishing/tools          # 工具列表
GET  /health                        # 健康检查
```

### 认证API
```
POST /api/v1/auth/login             # 用户登录
GET  /api/v1/auth/me                # 获取用户信息
POST /api/v1/auth/wechat/login      # 微信登录
POST /api/v1/auth/wechat/bind       # 绑定微信账号
```

### 功能API
```
POST /api/v1/ocr/recognize-table    # OCR表格识别
GET  /api/v1/ocr/status             # OCR服务状态
```

### 管理API
```
GET  /api/v1/admin/analytics/equipment/stats    # 装备统计
GET  /api/v1/admin/analytics/equipment/trends   # 趋势分析
GET  /api/v1/admin/config/configs               # 查询配置
GET  /api/v1/admin/crawler/tasks                # 爬虫任务列表
GET  /api/v1/admin/monitor/api-stats            # API统计
```

## 环境变量

### 必需
```bash
CAIYUN_API_KEY=xxx           # 彩云天气
AMAP_API_KEY=xxx             # 高德地图
DASHSCOPE_API_KEY=xxx        # 通义千问 + Embedding
ANTHROPIC_AUTH_TOKEN=xxx     # 智谱AI (推荐)
```

### JWT认证
```bash
JWT_SECRET_KEY=xxx           # JWT密钥 (必须设置)
JWT_ALGORITHM=HS256          # JWT算法
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # Token过期时间(分钟)
```

### 微信小程序
```bash
WECHAT_APPID=xxx            # 微信小程序AppID
WECHAT_SECRET=xxx           # 微信小程序AppSecret
WECHAT_AUTO_CREATE_USER=true # 是否自动创建新用户
```

## 快速开始

### 包管理 (uv)
```bash
uv sync                                    # 安装依赖
uv run python main.py                      # 运行CLI
```

### 开发服务器
```bash
# 后端
uv run uvicorn apps.api.main:app --reload

# 前端
cd apps/web-admin && npm run dev

# 小程序
# 1. 使用微信开发者工具打开 miniprogram/fishing_agent/
# 2. 配置小程序AppID和服务器域名
```

### 测试
```bash
PYTHONPATH=src uv run pytest               # 运行测试
```

## 架构原则
1. **Agent自包含** (独立发布)
2. **基础设施模块化** (scraper/data_processing独立)
3. **同步优先** (requests)
4. **诚实数据** (无假数据)
5. **LangChain 1.0+** (@tool装饰器)

## 包依赖说明
- **agent_fishing**: 核心Agent包，独立自包含
- **data_processing**: 数据处理包，独立可用，不依赖agent_fishing
- **scraper**: 爬虫框架包，独立可用，通过configure_database()接收数据库连接

## 文档导航

### 用户指南
- [快速开始](docs/01-user-guide/getting-started.md)
- [基础功能](docs/01-user-guide/basic-features.md)
- [故障排除](docs/01-user-guide/troubleshooting.md)

### 开发者指南
- [环境配置](docs/02-developer-guide/environment-setup.md)
- [代码结构](docs/02-developer-guide/codebase-structure.md)
- [开发流程](docs/02-developer-guide/development-workflows.md)
- [测试指南](docs/02-developer-guide/testing.md)

### 架构设计
- [系统设计](docs/03-architecture/system-design.md)

### 专题指南
- [图片处理](docs/06-guides/image-processing.md)
- [小程序集成](docs/06-guides/miniprogram-integration.md)
- [装备导入](docs/06-guides/equipment-import.md)
- [性能优化](docs/06-guides/performance-optimization.md)
