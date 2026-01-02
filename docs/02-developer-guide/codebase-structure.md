# 代码结构指南 v5.0.2

深入了解智能钓鱼助手的项目架构、模块设计和代码组织。

## 📋 目录

- [项目概览](#项目概览)
- [技术栈](#技术栈)
- [包结构](#包结构)
- [应用层结构](#应用层结构)
- [核心组件](#核心组件)
- [开发模式](#开发模式)
- [数据流](#数据流)
- [设计模式](#设计模式)

## 🎯 项目概览

### 核心架构
```
智能钓鱼助手 v5.0.2
├── 模块化包架构 (4个独立包)
├── 多端应用支持 (CLI/API/Web/小程序)
├── 智能处理系统 (OCR/图片合并/装备导入)
└── 现代技术栈 (LangChain 1.0+ / FastAPI / React 19)
```

### 架构特点
- **模块化设计**: 每个包独立可发布
- **Agent架构**: 基于LangChain的智能体系统
- **API优先**: RESTful API设计，支持多端接入
- **微服务就绪**: 包可独立部署和扩展

## 🛠️ 技术栈

### 后端技术
- **Python**: 3.11+ (主要开发语言)
- **LangChain**: 1.0+ (AI Agent框架)
- **FastAPI**: Web API框架
- **SQLAlchemy**: ORM数据库操作
- **uv**: 现代Python包管理器
- **pytest**: 测试框架

### 前端技术
- **React**: 19.2.0 (前端框架)
- **TypeScript**: 类型安全
- **Ant Design**: 5.22.0 (UI组件库)
- **Vite**: 构建工具

### AI和数据
- **通义千问**: 阿里云LLM服务
- **智谱AI**: GLM-4.6模型
- **Ollama**: 本地OCR模型
- **SiliconFlow**: 云端OCR服务

### 基础设施
- **SQLite**: 开发数据库
- **PostgreSQL**: 生产数据库
- **Redis**: 缓存服务
- **Docker**: 容器化部署

## 📦 包结构

### packages/ 模块化包目录
```
packages/                           # 模块化包目录
├── agents/                        # Agent统一目录 (v5.1.0 重构)
│   ├── agent_component/           # 共享组件
│   │   └── monitoring/            # 统一监控回调
│   │       └── callback.py        # MonitoringCallback
│   ├── fishing/                   # 钓鱼Agent包
│   │   ├── __init__.py            # 包入口和导出
│   │   ├── core/                  # Agent核心逻辑
│   │   │   ├── __init__.py
│   │   │   ├── agent.py           # 主要Agent类
│   │   │   ├── model_factory.py   # LLM模型工厂
│   │   │   ├── prompts.py         # 系统提示词
│   │   │   └── callbacks.py       # 回调处理
│   │   ├── tools/                 # 工具集合
│   │   │   ├── __init__.py        # 工具注册和导出
│   │   │   ├── basic.py           # 基础工具(时间等)
│   │   │   ├── weather.py         # 天气相关工具
│   │   │   ├── fishing_tool.py    # 钓鱼推荐工具
│   │   │   ├── lure_tools.py      # 路亚装备工具
│   │   │   ├── lure/              # 路亚装备子模块
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py    # 装备数据库
│   │   │   │   ├── search.py      # 装备搜索
│   │   │   │   └── recommendation.py # 装备推荐
│   │   │   ├── user_equipment/    # 用户装备管理 ⭐v5.1.0
│   │   │   │   ├── manager.py     # 装备管理器
│   │   │   │   ├── recommender.py # 装备推荐器
│   │   │   │   └── tools.py       # Agent工具
│   │   │   └── fishing/           # 钓鱼工具
│   │   │       ├── scorer.py      # 评分器
│   │   │       └── ...
│   │   ├── middleware/            # 中间件
│   │   │   ├── __init__.py
│   │   │   └── dynamic_prompt.py  # 动态Prompt选择
│   │   └── utils/                 # 工具函数
│   │       ├── __init__.py
│   │       ├── coordinate.py      # 坐标处理
│   │       ├── date_parser.py     # 日期解析
│   │       └── weather_parser.py  # 天气解析
│   └── equipment_import/          # 装备导入Agent包 ⭐v5.0.2
│       ├── __init__.py
│       ├── core/
│       │   ├── agent.py           # 装备导入Agent
│       │   ├── extractor.py       # 信息提取器
│       │   └── prompts.py         # 提取提示词
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── patterns.py        # 提取模式
│       │   └── text_compressor.py # 文本压缩中间件
│       ├── models/                # 数据模型
│       │   ├── __init__.py
│       │   └── pending.py         # 待审核装备模型
│       ├── schemas/               # 数据模式
│       │   ├── __init__.py
│       │   └── extracted.py       # 提取结果模式
│       └── tools/
│           ├── __init__.py
│           └── import_tool.py     # 导入工具
├── data_processing/                # 数据处理包 ⭐v5.0.2
│   ├── __init__.py
│   ├── image/                      # 图片处理
│   │   ├── __init__.py
│   │   ├── merger.py               # 图片合并
│   │   ├── batch_processor.py      # 批量处理
│   │   ├── preprocessor.py         # 图片预处理
│   │   └── detector.py             # 文字区域检测
│   ├── ocr/                        # OCR文字检测
│   │   ├── __init__.py
│   │   ├── ocr_processor.py        # OCR处理器
│   │   ├── base_provider.py        # OCR提供商基类
│   │   ├── ollama_provider.py      # Ollama OCR
│   │   └── siliconflow_provider.py # SiliconFlow OCR
│   └── dedup/                      # 去重工具
│       ├── __init__.py
│       ├── deduplicator.py         # 去重器
│       └── similarity.py           # 相似度计算
└── scraper/                        # 爬虫框架包 ⭐v5.0.2
    ├── __init__.py
    ├── spider/                     # 爬虫核心
    │   ├── __init__.py
    │   ├── base_spider.py          # 基础爬虫类
    │   └── crawl_item.py           # 爬虫数据项
    ├── spiders/                    # 具体爬虫实现
    │   ├── __init__.py
    │   ├── taobao_spider.py        # 淘宝爬虫
    │   ├── jd_spider.py            # 京东爬虫
    │   └── forum_spider.py         # 论坛爬虫
    ├── rpa/                        # RPA自动化 (Playwright)
    │   ├── core/                   # 核心RPA引擎 ⭐v5.1.0
    │   ├── extractors/             # 数据提取器
    │   ├── pages/                  # 页面对象
    │   └── utils/                  # 工具函数
    ├── platform/                   # 平台抽象层
    │   ├── __init__.py
    │   ├── taobao_platform.py      # 淘宝平台
    │   └── jd_platform.py          # 京东平台
    ├── workflow/                   # 工作流引擎 (DAG)
    │   ├── __init__.py
    │   ├── manager.py              # 工作流管理器
    │   └── executor.py             # 任务执行器
    ├── executor/                   # 任务执行器 ⭐v5.1.0
    │   ├── __init__.py
    │   └── crawler_executor.py     # 爬虫执行器
    ├── monitoring/                 # 监控告警
    │   ├── __init__.py
    │   ├── monitor.py              # 监控器
    │   └── alerting.py             # 告警器
    ├── scheduler/                  # 定时调度 ⭐v5.1.0
    │   ├── __init__.py
    │   └── workflow_scheduler.py   # 工作流调度
    ├── persister/                  # 数据持久化 ⭐v5.0.2
    │   ├── __init__.py
    │   └── equipment_persister.py  # 装备数据持久化
    ├── master/                     # Master节点服务 ⭐v5.1.0
    │   ├── app.py                  # FastAPI应用
    │   ├── auth/                   # 节点认证
    │   ├── routes/                 # API路由
    │   └── schemas/                # 数据模式
    ├── worker/                     # Worker节点 ⭐v5.1.0
    │   ├── worker.py               # Worker基类
    │   ├── api_worker.py           # API Worker
    │   ├── ocr_worker.py           # OCR Worker
    │   └── client.py               # Master客户端
    └── models/                     # 爬虫模型
        ├── __init__.py
        ├── base.py                 # 基础模型
        ├── task.py                 # 任务模型
        └── node.py                 # 节点模型
```

## 🏗️ 应用层结构

### apps/ 应用层目录
```
apps/                              # 应用层
├── cli/                           # CLI应用
│   ├── main.py                    # CLI入口点
│   ├── commands/                  # CLI命令
│   │   ├── __init__.py
│   │   ├── chat.py                # 对话命令
│   │   └── equipment.py           # 装备命令
│   └── utils/                     # CLI工具
│       ├── __init__.py
│       └── formatter.py           # 输出格式化
├── api/                           # FastAPI后端
│   ├── main.py                    # API服务器入口
│   ├── auth/                      # JWT认证模块
│   │   ├── __init__.py
│   │   ├── models.py              # 认证数据模型
│   │   ├── routes.py              # 认证路由
│   │   └── dependencies.py        # 认证依赖
│   ├── middleware/                # 中间件
│   │   ├── __init__.py
│   │   ├── cors.py                # CORS中间件
│   │   └── auth.py                # 认证中间件
│   ├── routes/                    # API路由 (17个模块)
│   │   ├── __init__.py
│   │   ├── fishing.py             # 钓鱼相关API
│   │   ├── chat.py                # 聊天API ⭐v5.0.2
│   │   ├── auth.py                # 认证API ⭐v3.1.1
│   │   ├── user_equipment.py      # 用户装备API ⭐v5.0.2
│   │   ├── equipment_admin.py     # 装备管理API ⭐v5.0.2
│   │   ├── equipment_batch.py     # 批量操作API ⭐v5.0.2
│   │   ├── import_export.py       # 导入导出API ⭐v5.0.2
│   │   ├── user_admin.py          # 用户管理API ⭐v5.0.2
│   │   ├── admin.py               # 管理员API
│   │   ├── analytics.py           # 数据分析API ⭐v5.0.2
│   │   ├── config.py              # 配置管理API ⭐v5.0.2
│   │   ├── crawler.py             # 数据采集API ⭐v4.0.0
│   │   ├── monitor.py             # 监控API ⭐v4.0.0
│   │   ├── ocr.py                 # OCR API ⭐v5.0.2
│   │   ├── ocr_worker.py          # OCR Worker API ⭐v5.0.2
│   │   ├── worker.py              # Worker API ⭐v5.0.2
│   │   └── data_workflow.py       # 数据工作流API ⭐v5.0.2
│   ├── schemas/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── fishing.py             # 钓鱼相关模型
│   │   ├── equipment.py           # 装备相关模型
│   │   ├── user.py                # 用户相关模型
│   │   └── common.py              # 通用模型
│   ├── services/                  # 业务服务层 ⭐v5.0.2
│   │   ├── __init__.py
│   │   ├── fishing_service.py     # 钓鱼服务
│   │   ├── equipment_service.py   # 装备服务
│   │   ├── analytics_service.py   # 分析服务
│   │   ├── ocr/                   # OCR服务
│   │   ├── config_service.py      # 配置服务
│   │   ├── crawler_service.py     # 爬虫服务
│   │   ├── monitor_service.py     # 监控服务
│   │   ├── websocket_manager.py   # WebSocket管理
│   │   └── workflow_ws_manager.py # 工作流WebSocket管理
│   ├── models/                    # 数据库模型 (30个) ⭐v5.2.0
│   │   ├── base.py                # Base, TimestampMixin
│   │   ├── equipment.py           # Equipment, RodSpec, ReelSpec, LineSpec, LureSpec
│   │   ├── brand.py               # Brand
│   │   ├── user.py                # User, UserEquipment, FishingLog
│   │   ├── fish.py                # FishSpecies, FishKnowledge, FishSeasonActivity
│   │   ├── rig.py                 # RigType, RigSpec, RigComponent
│   │   ├── lure.py                # LureType, RodLureFitness
│   │   ├── admin_user.py          # AdminUser
│   │   ├── system.py              # CrawlerTask, CrawlerLog, APILog, LLMLog, SystemConfig, AnalyticsReport
│   │   ├── agent_log.py           # AgentExecutionLog, ToolCallLog
│   │   └── chat.py                # ChatSession, ChatMessage
│   ├── orm/                       # ORM层 ⭐v5.2.0
│   │   ├── session.py             # 会话管理
│   │   └── repositories/          # 仓储模式
│   │       ├── equipment.py       # EquipmentRepository
│   │       ├── brand.py           # BrandRepository
│   │       ├── user.py            # UserRepository, UserEquipmentRepository
│   │       ├── fish.py            # FishSpeciesRepository
│   │       └── admin_user.py      # AdminUserRepository
│   └── database/                  # 数据库配置
│       ├── __init__.py
│       ├── connection.py          # 数据库连接
│       └── migrations/            # 数据库迁移
└── web-admin/                     # React管理前端 ⭐v5.0.2
    ├── public/                    # 静态资源
    ├── src/                       # 源代码
    │   ├── components/             # 通用组件
    │   │   ├── Layout/             # 布局组件
    │   │   ├── Charts/             # 图表组件
    │   │   └── Forms/              # 表单组件
    │   ├── pages/                  # 页面组件
    │   │   ├── Dashboard/          # 仪表板
    │   │   ├── Equipment/          # 装备管理
    │   │   ├── Analytics/          # 数据分析
    │   │   ├── Config/             # 配置管理
    │   │   └── Crawler/            # 爬虫管理
    │   ├── services/               # API服务
    │   │   ├── api.ts              # API客户端
    │   │   ├── auth.ts             # 认证服务
    │   │   └── equipment.ts        # 装备服务
    │   ├── utils/                  # 工具函数
    │   │   ├── constants.ts        # 常量定义
    │   │   └── helpers.ts          # 辅助函数
    │   ├── types/                  # TypeScript类型
    │   │   ├── api.ts              # API类型
    │   │   └── common.ts           # 通用类型
    │   ├── hooks/                  # React Hooks
    │   │   ├── useAuth.ts          # 认证Hook
    │   │   └── useApi.ts           # API Hook
    │   ├── store/                  # 状态管理
    │   │   ├── authStore.ts        # 认证状态
    │   │   └── appStore.ts         # 应用状态
    │   ├── App.tsx                 # 应用根组件
    │   └── main.tsx                # 应用入口
    ├── package.json               # 前端依赖配置
    └── vite.config.ts             # Vite配置
```

## 🧩 核心组件

### Agent Core
```python
# packages/agent_fishing/core/agent.py
class FishingAgent:
    def __init__(self, model_provider: str = "zhipu"):
        self.model = ModelFactory.create(model_provider)
        self.tools = get_all_tools()
        self.chain = self._create_chain()

    def run(self, query: str) -> str:
        # 动态Prompt选择
        prompt = DynamicPromptMiddleware.select(query)
        response = self.chain.invoke({"input": query, "tools": self.tools})
        return response["output"]
```

### 装备导入Agent ⭐ v5.0.2
```python
# packages/agent_equipment_import/core/agent.py
class EquipmentImportAgent:
    def extract_and_save(self, text: str, source_type: str = "forum"):
        # 文本压缩 → 信息提取 → 保存待审核
        if len(text) > 2000:
            text = TextCompressor.compress(text)
        equipment_list = self._extract_equipment(text)
        return [self._save_to_pending(eq, source_type) for eq in equipment_list]
```

### 图片处理系统 ⭐ v5.0.2
```python
# packages/data_processing/image/batch_processor.py
class BatchMergeProcessor:
    def process(self):
        # OCR文字检测 → 智能分组 → 批量合并
        images = self._get_image_list()
        merge_groups = self._detect_merge_groups(images)
        return [self._merge_group(group) for group in merge_groups]
```

## 🔄 开发模式

### 添加新功能

#### 1. 新Agent包
```bash
mkdir -p packages/agent_xxx/{core,tools,utils}
# 创建 __init__.py 和核心文件
# 在 langgraph.json 中注册
```

#### 2. 新OCR提供商
```python
# packages/data_processing/ocr/providers/new_provider.py
class NewOCRProvider(BaseOCRProvider):
    async def recognize(self, image: bytes) -> OCRResult:
        # 实现OCR逻辑
        pass

# 注册到 OCR_PROVIDERS 字典
```

#### 3. 新爬虫
```python
# packages/scraper/spiders/new_spider.py
class NewSpider(BaseSpider):
    async def crawl(self, keywords: List[str]) -> List[CrawlItem]:
        # 实现爬取逻辑
        pass

# 注册到 SPIDER_REGISTRY
```

## 🌊 数据流

### 分层架构
```
Presentation Layer    ← CLI, API, Web UI, Miniprogram
Application Layer     ← Routes, Middleware, Services
Domain Layer          ← Agents, Tools, Business Logic
Infrastructure Layer ← Database, External APIs, OCR
```

### 数据流向
```
用户输入 → 应用层路由 → Agent包处理 → 工具选择 → API调用
数据处理 → 评分计算 → 结果格式化 → 响应返回
```

## 🎨 设计模式

### 1. 工厂模式
```python
# LLM模型工厂
class ModelFactory:
    @staticmethod
    def create(provider: str) -> BaseLLM:
        if provider == "zhipu":
            return ZhipuModel()
        elif provider == "dashscope":
            return DashScopeModel()
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

### 2. 策略模式
```python
# OCR提供商策略
class OCRProcessor:
    def __init__(self, provider: str):
        self.provider = OCR_PROVIDERS[provider]()

    async def recognize(self, image: bytes):
        return await self.provider.recognize(image)
```

### 3. 观察者模式
```python
# Agent回调系统
class AgentCallback:
    def on_tool_start(self, tool_name: str, inputs: dict):
        # 工具开始执行
        pass

    def on_tool_end(self, tool_name: str, outputs: dict):
        # 工具执行完成
        pass
```

### 4. 建造者模式
```python
# 装备信息构建
class EquipmentBuilder:
    def __init__(self):
        self.equipment = {}

    def with_brand(self, brand: str):
        self.equipment['brand'] = brand
        return self

    def with_model(self, model: str):
        self.equipment['model'] = model
        return self

    def build(self) -> dict:
        return self.equipment
```

## 🔗 关键导入

### 核心功能导入
```python
# Agent 核心功能 (v5.1.0 新路径)
from packages.agents.fishing import FishingAgent, create_agent, get_all_tools
from packages.agents.fishing.core import ModelFactory
from packages.agents.fishing.tools import get_weather, query_fishing_recommendation
from packages.agents.fishing.utils import get_coordinates, parse_date_input

# 统一监控组件 (v5.1.0 新增)
from packages.agents.agent_component.monitoring import MonitoringCallback

# 用户装备管理 (v5.1.0 新增)
from packages.agents.fishing.tools.user_equipment import (
    UserEquipmentManager,
    EquipmentRecommender
)

# 装备导入功能
from packages.agents.equipment_import import EquipmentImportAgent
from packages.agents.equipment_import.core import TextCompressor

# 图片处理功能（位于 data_processing 包）
from packages.data_processing.image import BatchMergeProcessor, ImageMerger
from packages.data_processing.image.batch_processor import BatchMergeProcessor
from packages.data_processing.image.merger import ImageMerger

# OCR 功能（位于 data_processing 包）
from packages.data_processing.ocr import OCRMergeProcessor
from packages.data_processing.ocr.ocr_processor import OCRMergeProcessor
from packages.data_processing.ocr.text_detector import TextRegionDetector

# 去重功能（位于 data_processing 包）
from packages.data_processing.dedup import Deduplicator
from packages.data_processing.dedup.deduplicator import Deduplicator

# 爬虫功能（位于 scraper 包）
from packages.scraper import BaseSpider, CrawlItem
from packages.scraper.spider import BaseSpider, CrawlItem
from packages.scraper.spiders import TaobaoSpider, JDSpider, ForumSpider
from packages.scraper.rpa import TaobaoRPA
from packages.scraper.workflow import WorkflowManager
```

## 📝 代码约定

### 命名规范
- **文件名**: 使用snake_case (Python) 或 kebab-case (前端)
- **类名**: 使用PascalCase
- **函数名**: 使用snake_case
- **常量**: 使用UPPER_SNAKE_CASE
- **包名**: 使用小写字母和下划线

### 文档规范
- 所有公共函数和类必须有docstring
- 使用Google风格的docstring
- 复杂逻辑需要添加行内注释
- 重要的业务逻辑需要添加TODO注释

### 测试规范
- 测试文件名以`test_`开头
- 测试函数名以`test_`开头
- 使用描述性的测试名称
- 每个测试用例应该是独立的

## 📚 相关文档

- [环境配置](./environment-setup.md) - 开发环境搭建
- [开发流程](./development-workflows.md) - 开发规范和流程
- [测试指南](./testing.md) - 测试策略和方法
- [贡献指南](./contribution-guide.md) - 如何参与开发
- [架构设计](../03-architecture/system-design.md) - 系统架构详情

---

**指南版本**: v5.0.2  
**适用系统版本**: v5.0.2+  
**更新时间**: 2024-12-20