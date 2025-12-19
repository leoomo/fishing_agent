# 智能钓鱼助手 - 项目架构文档

**版本**: v5.0.2
**分支**: feature/equipment-ui
**目标**: 为大模型(LLM)提供完整的项目架构理解指南
**架构**: 模块化 Agent 包 + FastAPI 后端 + React管理前端 + JWT认证系统 + 工作流管理系统 + 数据分析 + 配置管理 + OCR多提供商系统 + 智能图片合并系统

---

## 📋 目录

1. [项目概览与架构哲学](#1-项目概览与架构哲学)
2. [系统架构](#2-系统架构)
3. [模块组织](#3-模块组织)
4. [核心组件分析](#4-核心组件分析)
5. [开发模式](#5-开发模式)
6. [数据流与状态管理](#6-数据流与状态管理)
7. [配置与部署](#7-配置与部署)
8. [LLM导航指南](#8-llm导航指南)

---

## 1. 项目概览与架构哲学

### 🎯 项目定位
智能钓鱼助手 v5.0.2 是基于 **LangChain 1.0+** 的模块化智能代理系统，采用全新包架构和动态Prompt中间件，专门为路亚钓鱼爱好者提供：
- **动态Prompt中间件**，智能选择提示词，优化Token使用效率50%+
- **实时天气分析**和钓鱼条件评估
- **7因子科学评分系统**（温度、天气、风力、气压、湿度、季节、月相）
- **动态趋势分析**识别黄金钓鱼时段
- **时间段意图识别**，98%+准确率
- **路亚装备智能推荐**和语义搜索
- **全国覆盖**的3,142+行政区划支持
- **FastAPI REST API** 后端支持
- **完全自包含的 Agent 包**架构
- **调试工具**支持多模型测试和环境检查
- **动态Prompt中间件**系统，智能选择提示词
- **React管理前端**（React 19.2.0 + TypeScript + Ant Design 5.22.0）⭐ v5.0新增
- **JWT认证系统**（RBAC权限管理 + Token安全）⭐ v3.1.1新增
- **智能图片合并**（自动检测文字 + 批量处理 + 本地化处理）⭐ v5.0新增
- **OCR多提供商支持**（Ollama本地 + SiliconFlow云端）⭐ v5.0新增
- **路亚装备管理系统**和数据分析报表 ⭐ v5.0新增
- **爬虫监控模块**和工作流管理系统 ⭐ v4.0新增
- **系统配置管理**（API密钥/参数配置）⭐ v5.0新增

### 🏗️ 核心架构哲学

#### **模块化包架构 (Modular Package Architecture)**
```python
# v5.0.2: 完全自包含的 Agent 包 + 动态Prompt中间件 + 智能图片合并
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools

# 每个包都是独立可发布的单元
packages/
├── agent_fishing/          # 钓鱼 Agent 包（已完成）
├── agent_weather/          # 天气 Agent 包（未来）
└── agent_location/         # 地理 Agent 包（未来）
```

#### **零抽象原则 (Zero Abstraction)**
```python
# 直接API调用，无中间层
def get_weather(location: str) -> dict:
    response = requests.get(f"https://api.caiyunapp.com/v2.6/{API_KEY}/{coords}/realtime")
    return response.json()
```

#### **动态Prompt中间件 (Dynamic Prompt Middleware) - v3.1.1核心特性**
```python
# packages/agent_fishing/core/middleware/dynamic_prompt.py
@dynamic_prompt
def select_prompt_by_query_type(request: ModelRequest) -> str:
    """
    智能提示词选择系统 - 根据查询类型动态选择系统prompt

    Token效率优化：
    - 钓鱼查询: BASE(600) + FISHING_OUTPUT_RULES(600) = ~1200 tokens
    - 天气查询: BASE(600) + WEATHER_QUERY_RULES(200) = ~800 tokens
    - 其他查询: BASE = ~600 tokens

    性能提升：Token效率提升50%+，响应时间减少30%
    """
    # 基于关键词的智能类型检测
    if "钓鱼" in user_input:
        return BASE_SYSTEM_PROMPT + FISHING_OUTPUT_RULES
    elif any(kw in user_input for kw in ["天气", "温度", "下雨"]):
        return BASE_SYSTEM_PROMPT + WEATHER_QUERY_RULES
    else:
        return BASE_SYSTEM_PROMPT
```

**技术架构**:
- **基于LangChain 1.0+**: 使用`@dynamic_prompt`装饰器
- **运行时Prompt选择**: 根据用户输入动态选择最合适的系统提示词
- **Token效率优化**: 避免加载不必要的专业规则，节省50%+Token使用
- **三层Prompt架构**:
  - `BASE_SYSTEM_PROMPT`: 基础能力定义 (~600 tokens)
  - `FISHING_OUTPUT_RULES`: 钓鱼专业规则和7因子评分 (~600 tokens)
  - `WEATHER_QUERY_RULES`: 天气查询专用规则 (~200 tokens)

**核心算法**:
```python
# 查询类型检测优先级
1. 钓鱼查询 (关键词: "钓鱼", "路亚", "渔") → 完整钓鱼规则
2. 天气查询 (关键词: "天气", "温度", "下雨", "气温") → 天气专用规则
3. 其他查询 → 基础能力规则
```

**性能指标**:
- **Token使用效率**: 相比静态Prompt节省50%+
- **响应时间**: 减少30%（无需加载专业规则）
- **内存占用**: 大幅降低Prompt缓存压力
- **向后兼容**: 完全兼容现有Agent接口

#### **应用层分离 (Application Layer Separation)**
```python
# CLI 应用
apps/cli/main.py

# FastAPI 后端
apps/api/main.py

# 共享资源
shared/config/
shared/data/
```

#### **诚实数据处理 (Honest Data)**
- 绝不生成虚假或模拟数据
- API失败时透明报告错误
- 提供诚实的降级建议而非编造信息

---

## 2. 系统架构

### 🏛️ 架构层次图

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ fishing CLI │  │fishing-api  │  │  LangGraph  │          │
│  │ (CLI 应用)   │  │ (FastAPI)   │  │ (Studio)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    应用层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │apps/cli/    │  │apps/api/    │  │ shared/     │          │
│  │(CLI 逻辑)   │  │(REST API)   │  │(共享配置)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   模块化 Agent 包层                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │        packages/agent_fishing/ (自包含包)               │ │
│  │  • core/ (Agent核心)                                   │ │
│  │  • tools/ (工具集成)                                   │ │
│  │  • utils/ (工具类)                                     │ │
│  │  • 完全独立，可单独发布                                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   工具集成层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │基础工具     │  │天气工具     │  │钓鱼工具     │          │
│  │(时间/计算)  │  │(直接API)    │  │(7因子评分)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────────────────────────────┐   │
│  │  路亚工具   │  │        向量存储与知识库             │   │
│  │(装备推荐)   │  │   (ChromaDB + DashScope)          │   │
│  └─────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  工具与支持层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │API客户端    │  │坐标工具     │  │缓存/工具    │          │
│  │(HTTP封装)   │  │(地理编码)   │  │(简单缓存)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   评分系统                               │ │
│  │  • 7因子算法 (温度/天气/风力/气压/湿度/季节/月相)     │ │
│  │  • 趋势分析与动态评分                                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   外部API层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │彩云天气API  │  │高德地图API  │  │DashScope API│          │
│  │(天气服务)   │  │(定位服务)   │  │(LLM+嵌入)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 数据流模式

#### **请求处理流程**
```
用户输入 → 应用层路由 → Agent包处理 → 工具选择 → 参数解析 → API调用
    ↓
数据处理 → 评分计算 → 结果格式化 → 输出验证 → 响应返回
```

#### **应用层路由逻辑**
```python
# CLI 应用 (apps/cli/main.py)
def main():
    agent = create_agent(model_provider="zhipu")
    user_input = input("请输入钓鱼相关问题: ")
    result = agent.run(user_input)
    print(result)

# FastAPI 应用 (apps/api/main.py)
@app.post("/api/v1/fishing/chat")
async def chat(request: ChatRequest):
    agent = create_agent(model_provider="zhipu")
    result = agent.run(request.query)
    return {"response": result}
```

---

## 3. 模块组织

### 📁 核心目录结构 (v5.0.2)

```
fishing-agent/
├── packages/                      # 模块化包目录
│   ├── agent_fishing/             # 钓鱼 Agent（完全自包含）
│   │   ├── __init__.py           # 包入口和 LangGraph 兼容
│   │   ├── core/                  # Agent 核心
│   │   │   ├── __init__.py
│   │   │   ├── agent.py           # FishingAgent 实现
│   │   │   ├── model_factory.py   # LLM 工厂
│   │   │   ├── prompts.py         # 提示词
│   │   │   └── callbacks.py       # 回调系统
│   │   ├── middleware/            # 动态Prompt中间件
│   │   │   ├── __init__.py
│   │   │   └── dynamic_prompt.py  # 智能Prompt选择系统
│   │   ├── tools/                 # Agent 工具集
│   │   │   ├── __init__.py
│   │   │   ├── basic.py           # 基础工具（时间功能）
│   │   │   ├── weather.py         # 天气工具
│   │   │   ├── fishing_tool.py    # 钓鱼工具
│   │   │   ├── lure_tools.py      # 路亚装备工具
│   │   │   ├── lure/              # 路亚子模块
│   │   │   │   ├── embeddings.py  # DashScope嵌入服务
│   │   │   │   ├── vector_store.py # ChromaDB向量存储
│   │   │   │   └── knowledge_search.py # 语义搜索
│   │   │   ├── fishing/           # 钓鱼评分子模块
│   │   │   │   ├── weather_api.py # 天气API集成
│   │   │   │   ├── weather_parser.py # 天气数据解析
│   │   │   │   ├── time_optimizer.py # 时间优化器
│   │   │   │   ├── report_generator.py # 报告生成器
│   │   │   │   ├── enhanced_scorer.py # 增强7因子评分
│   │   │   │   └── scorer.py      # 基础评分器
│   │   │   └── scoring/           # 评分系统
│   │   │       └── enhanced_scorer.py
│   │   └── utils/                 # Agent 工具类
│   │       ├── __init__.py
│   │       ├── api_client.py      # API客户端
│   │       ├── coordinate_utils.py # 坐标工具
│   │       └── date_utils.py      # 日期工具
│   ├── data_processing/           # 数据处理包 ⭐ v5.0.2新增（从agent_fishing独立）
│   │   ├── __init__.py           # 包入口
│   │   ├── pyproject.toml        # 包配置
│   │   ├── image/                # 图片处理模块
│   │   │   ├── __init__.py
│   │   │   ├── batch_processor.py # 批量合并处理器
│   │   │   ├── merger.py         # 图片合并器
│   │   │   └── splitter.py       # 图片分割器
│   │   ├── ocr/                  # OCR文字检测模块
│   │   │   ├── __init__.py
│   │   │   ├── ocr_processor.py  # OCR处理器
│   │   │   └── text_detector.py  # 文字区域检测器
│   │   └── dedup/                # 去重模块
│   │       ├── __init__.py
│   │       └── deduplicator.py   # 去重器
│   └── scraper/                  # 爬虫框架包 ⭐ v5.0.2新增（从agent_fishing独立）
│       ├── __init__.py           # 包入口，导出BaseSpider等核心类
│       ├── pyproject.toml        # 包配置
│       ├── spider/               # 爬虫核心模块
│       │   ├── __init__.py
│       │   ├── base.py           # BaseSpider基础类
│       │   ├── anti_crawler.py   # 反爬虫工具
│       │   └── downloader.py     # 下载器
│       ├── spiders/              # 具体爬虫实现
│       │   ├── __init__.py
│       │   ├── taobao_spider.py  # 淘宝爬虫
│       │   ├── jd_spider.py      # 京东爬虫
│       │   └── forum_spider.py   # 论坛爬虫
│       ├── rpa/                  # RPA自动化框架
│       │   ├── __init__.py
│       │   ├── captcha_solver.py # 验证码解决
│       │   ├── session_storage.py # 会话存储
│       │   ├── taobao_rpa.py     # 淘宝RPA
│       │   ├── core/             # RPA核心模块
│       │   ├── extractors/       # 数据提取器
│       │   └── pages/            # 页面对象
│       ├── platform/             # 平台抽象层
│       │   ├── __init__.py
│       │   ├── base_platform.py  # 基础平台类
│       │   ├── registry.py       # 平台注册表
│       │   ├── taobao_platform.py # 淘宝平台
│       │   └── jd_platform.py    # 京东平台
│       ├── workflow/             # 工作流引擎
│       │   ├── __init__.py
│       │   ├── engine.py         # 工作流引擎
│       │   └── manager.py        # 工作流管理器
│       ├── executor/             # 任务执行器
│       │   ├── __init__.py
│       │   ├── crawler_executor.py # 爬虫执行器
│       │   └── task_queue.py     # 任务队列
│       ├── monitoring/           # 监控告警
│       │   ├── __init__.py
│       │   ├── alerts.py         # 告警系统
│       │   ├── metrics.py        # 指标收集
│       │   └── monitor.py        # 监控主程序
│       ├── scheduler/            # 定时调度
│       │   ├── __init__.py
│       │   └── workflow_scheduler.py # 工作流调度器
│       ├── persister/            # 数据持久化
│       │   ├── __init__.py
│       │   └── equipment_persister.py # 装备数据持久化
│       └── models/               # 独立的爬虫模型
│           ├── __init__.py
│           └── [各模型文件]      # CrawlerTask, CrawlerLog等
├── apps/                          # 应用层
│   ├── cli/                       # CLI 应用
│   │   └── main.py                # CLI主程序
│   ├── api/                       # FastAPI 后端
│   │   ├── main.py                # API服务器 (v5.0.0)
│   │   ├── auth/                  # JWT认证模块 ⭐ v3.1.1新增
│   │   │   ├── jwt.py             # JWT工具
│   │   │   ├── dependencies.py    # 认证依赖
│   │   │   └── permissions.py     # 权限管理
│   │   ├── middleware/            # API中间件
│   │   │   └── cors.py            # CORS中间件
│   │   ├── routes/                # API路由
│   │   │   ├── auth.py            # 认证路由
│   │   │   ├── fishing.py         # 钓鱼助手路由
│   │   │   ├── user_equipment.py  # 用户装备路由
│   │   │   ├── analytics.py       # 数据分析路由 ⭐ v5.0新增
│   │   │   ├── config.py          # 配置管理路由 ⭐ v5.0新增
│   │   │   ├── crawler.py         # 爬虫管理路由 ⭐ v4.0新增
│   │   │   └── monitor.py         # 监控管理路由 ⭐ v4.0新增
│   │   ├── schemas/               # 数据模型
│   │   │   ├── auth.py            # 认证相关模型
│   │   │   ├── fishing.py         # 钓鱼相关模型
│   │   │   └── equipment.py       # 装备相关模型
│   │   ├── services/              # 业务服务层 ⭐ v5.0新增
│   │   │   ├── analytics_service.py # 数据分析服务
│   │   │   ├── config_service.py    # 配置管理服务
│   │   │   └── crawler_service.py   # 爬虫管理服务
│   │   ├── utils/                 # API工具
│   │   │   └── security.py        # 安全工具
│   │   └── websocket/             # WebSocket管理 ⭐ v5.0新增
│   │       └── manager.py         # 连接管理器
│   └── web-admin/                 # React管理前端 ⭐ v5.0新增
│       ├── public/                # 静态资源
│       ├── src/                   # 源代码
│       │   ├── components/        # 通用组件
│       │   │   ├── Layout/        # 布局组件
│       │   │   ├── AuthGuard/     # 认证守卫
│       │   │   └── Charts/        # 图表组件
│       │   ├── pages/             # 页面组件
│       │   │   ├── Dashboard/     # 仪表盘
│       │   │   ├── Equipment/     # 装备管理
│       │   │   ├── Analytics/     # 数据分析
│       │   │   ├── Crawler/       # 爬虫管理
│       │   │   ├── Config/        # 配置管理
│       │   │   └── Monitor/       # 监控中心
│       │   ├── services/          # API服务
│       │   │   ├── api.ts         # API客户端
│       │   │   └── auth.ts        # 认证服务
│       │   ├── store/             # Redux状态管理
│       │   │   ├── index.ts       # Store配置
│       │   │   └── slices/        # 状态切片
│       │   ├── utils/             # 工具函数
│       │   ├── types/             # TypeScript类型定义
│       │   └── App.tsx            # 主应用组件
│       ├── package.json           # 前端依赖
│       └── vite.config.ts         # Vite配置
├── shared/                        # 共享资源
│   ├── config/                    # 全局配置
│   │   ├── database.py            # 数据库配置
│   │   └── settings.py            # 应用设置
│   ├── data/                      # 共享数据
│   │   ├── equipment/             # 装备数据
│   │   └── templates/             # 模板文件
│   └── images/                    # 共享图片
├── scripts/                       # 脚本目录
│   ├── debug_ocr.py              # OCR调试脚本
│   └── setup_db.py               # 数据库初始化
├── logs/                          # 日志目录
├── tests/                         # 测试
│   ├── agent_fishing/            # Agent测试
│   └── api/                      # API测试
├── docs/                          # 文档
│   ├── ARCHITECTURE.md           # 架构文档
│   ├── API.md                    # API文档
│   └── DEPLOYMENT.md             # 部署文档
├── main.py                        # CLI 入口（兼容层）
├── debug_agent.py                 # 调试工具
├── langgraph.json                 # LangGraph 配置
├── pyproject.toml                 # 项目配置 (uv)
└── package.json                   # 根级npm配置
```

### 🔧 模块职责边界

#### **`packages/agent_fishing/` - 自包含 Agent 包**
- **`core/`**: Agent 核心实现，LLM 集成和工具管理
- **`tools/`**: 专用工具集，每个工具具有单一职责
- **`utils/`**: 包内部工具类和辅助模块
- **完全独立**: 可单独发布和测试，不依赖其他模块

#### **`packages/data_processing/` - 数据处理包** ⭐ v5.0.2新增
- **`image/`**: 图片处理功能，包括智能合并、批量处理、分割等
- **`ocr/`**: OCR文字检测和提取功能
- **`dedup/`**: 数据去重功能
- **独立可用**: 不依赖 agent_fishing，可独立使用

#### **`packages/scraper/` - 爬虫框架包** ⭐ v5.0.2新增
- **`spider/`**: 爬虫核心，BaseSpider 基础类
- **`spiders/`**: 各平台具体爬虫实现
- **`rpa/`**: RPA 自动化框架
- **`workflow/`**: 工作流管理和调度
- **独立可用**: 不依赖 agent_fishing，通过 configure_database() 接收数据库连接

#### **`apps/` - 应用层**
- **`cli/`**: 命令行应用，用户交互界面
- **`api/`**: FastAPI REST API 后端服务
- **业务逻辑编排**: 调用 Agent 包处理用户请求

#### **`shared/` - 共享资源**
- **`config/`**: 全局配置文件和环境变量
- **`data/`**: 共享数据文件和模板

### 🎯 入口点与接口

#### **主要入口点 (v5.0.2)**
```python
# 1. CLI 命令行
fishing                        # 新版本 CLI 命令
python main.py                 # 兼容旧版本

# 2. FastAPI 服务
fishing-api                    # 启动 REST API 服务
uvicorn apps.api.main:app --reload

# 3. React管理前端 ⭐ v5.0新增
cd apps/web-admin
npm run dev                    # 启动开发服务器
npm run build                  # 构建生产版本

# 4. 编程接口 - 使用新包结构
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools
agent = create_agent(model_provider="zhipu")

# 5. LangGraph 兼容
from packages.agent_fishing import get_agent
agent = get_agent()  # LangGraph Studio 兼容

# 6. 图片合并功能（位于 data_processing 包）
from packages.data_processing.image import BatchMergeProcessor, ImageMerger
processor = BatchMergeProcessor(source_dir="./images")
result = processor.process()

# 7. OCR 功能（位于 data_processing 包）
from packages.data_processing.ocr import OCRMergeProcessor, TextRegionDetector
ocr_processor = OCRMergeProcessor()
text_detector = TextRegionDetector()

# 8. 爬虫功能（位于 scraper 包）
from packages.scraper import BaseSpider, CrawlItem
from packages.scraper.spiders import TaobaoSpider
from packages.scraper.workflow import WorkflowManager
```

#### **工具访问模式**
```python
# 统一工具访问
from packages.agent_fishing import get_all_tools

# 直接工具使用
from packages.agent_fishing.tools.weather import get_weather
from packages.agent_fishing.tools.fishing_tool import query_fishing_recommendation
```

---

## 4. 核心组件分析

### 🔧 调试工具系统 (v3.1.1新增，持续更新)

#### **debug_agent.py - 综合调试工具**
```python
# 调试工具使用示例
uv run python debug_agent.py --model zhipu --interactive
uv run python debug_agent.py --check-env
uv run python debug_agent.py --test-all
```

**核心功能**:
- **环境检查**: 验证API密钥配置和依赖状态
- **多模型测试**: 支持智谱AI、通义千问、豆包、OpenAI等LLM提供商
- **Agent创建测试**: 验证包导入和Agent初始化
- **性能监控**: 实时监控LLM调用、Token消耗、响应时间
- **交互模式**: 提供对话式调试界面
- **完整性检查**: 验证工具列表和功能完整性

**技术特性**:
- 支持所有v5.0.2支持的LLM提供商（智谱AI、通义千问、豆包、OpenAI等）
- 集成动态Prompt中间件测试
- 实时性能统计和错误追踪
- 环境配置自动检测
- OCR多提供商测试（Ollama本地、SiliconFlow云端）⭐ v5.0新增
- 图片合并功能调试 ⭐ v5.0新增

### 🤖 模块化 FishingAgent

#### **包架构实现**
```python
# packages/agent_fishing/__init__.py
from .core import FishingAgent, create_agent, ModelFactory
from .tools import get_all_tools

# LangGraph 兼容性
def get_agent():
    """LangGraph Studio 兼容的 agent 获取函数"""
    return create_agent(model_provider="zhipu").agent

__all__ = ["FishingAgent", "create_agent", "get_all_tools", "get_agent"]
```

#### **Agent 类架构**
```python
class FishingAgent:
    def __init__(self, model_provider="zhipu", timeout=60):
        self.model = ModelFactory.create(model_provider)
        self.tools = get_all_tools()
        self.agent = create_agent(self.model, self.tools, system_prompt)
        self.callback = FishingAgentCallback()

    def run(self, user_input: str) -> str:
        # LangChain代理执行与回调
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"callbacks": [self.callback]}
        )
        return self._extract_response(result)
```

**关键特性**:
- **完全自包含**: 包级别独立，可单独发布
- **LangGraph 兼容**: 支持 LangGraph Studio 集成
- **多LLM支持**: 工厂模式管理模型提供商
- **智能工具选择**: 基于查询意图自动路由
- **输出验证**: 保持钓鱼报告的工具格式化

### 🌐 FastAPI 后端架构

#### **REST API 实现**
```python
# apps/api/main.py
from fastapi import FastAPI
from packages.agent_fishing import create_agent
from .routes import auth_router
from .websocket import manager as websocket_manager

app = FastAPI(title="智能钓鱼助手 API", version="5.0.2")

# 注册路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

@app.post("/api/v1/fishing/chat")
async def fishing_chat(request: ChatRequest):
    """智能钓鱼助手对话接口"""
    agent = create_agent(model_provider="zhipu")
    result = agent.run(request.query)
    return {"response": result}

@app.get("/api/v1/fishing/tools")
async def list_tools():
    """获取可用工具列表"""
    from packages.agent_fishing import get_all_tools
    tools = get_all_tools()
    return {"tools": [{"name": tool.name, "description": tool.description} for tool in tools]}
```

#### **JWT 认证系统**
```python
# apps/api/auth/jwt.py
from jose import jwt
import bcrypt

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    """生成 JWT 访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """验证 JWT 令牌"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

#### **API 端点**
```python
GET  /                     # API 信息
GET  /health               # 健康检查

# 认证相关 ⭐ v3.1.1新增
POST /api/v1/auth/login    # 管理员登录
GET  /api/v1/auth/profile  # 获取用户信息（需认证）
POST /api/v1/auth/logout   # 用户登出（需认证）

# 钓鱼助手
POST /api/v1/fishing/chat  # 钓鱼助手对话
GET  /api/v1/fishing/tools # 工具列表

# 用户装备管理 ⭐ v5.0新增
GET  /api/v1/equipment     # 获取装备列表
POST /api/v1/equipment     # 添加装备
PUT  /api/v1/equipment/{id} # 更新装备
DELETE /api/v1/equipment/{id} # 删除装备

# 数据分析报表 ⭐ v5.0新增
GET  /api/v1/admin/analytics/equipment/stats  # 装备统计
GET  /api/v1/admin/analytics/equipment/trends # 趋势分析
POST /api/v1/admin/analytics/reports/generate # 生成报表

# 配置管理 ⭐ v5.0新增
GET  /api/v1/admin/config/configs # 查询配置
POST /api/v1/admin/config/configs # 创建配置
POST /api/v1/admin/config/configs/test-api-key # 测试API密钥

# 爬虫管理 ⭐ v4.0新增
GET  /api/v1/admin/crawler/tasks # 爬虫任务列表
POST /api/v1/admin/crawler/tasks/trigger # 触发爬虫

# 监控管理 ⭐ v4.0新增
GET  /api/v1/admin/monitor/api-stats # API统计
GET  /api/v1/admin/monitor/llm-stats  # LLM统计

# WebSocket ⭐ v5.0新增
WS   /ws/monitor           # 实时监控推送
```

### 🛠️ 工具系统架构

#### **模块化工具组织**
```python
# packages/agent_fishing/tools/
tools/
├── __init__.py                    # 统一工具导出
├── basic.py                      # 基础工具（时间功能）
├── weather.py                    # 天气查询工具
├── fishing_tool.py               # 钓鱼推荐工具
├── lure_tools.py                 # 路亚装备工具
├── lure/                         # 路亚装备子模块
│   ├── embeddings.py            # DashScope嵌入服务
│   ├── vector_store.py          # ChromaDB向量存储
│   └── knowledge_search.py      # 语义搜索服务
├── fishing/                      # 钓鱼评分子模块 ⭐ v4.0新增
│   ├── weather_api.py           # 天气API集成
│   ├── weather_parser.py        # 天气数据解析
│   ├── time_optimizer.py        # 时间优化器
│   ├── report_generator.py      # 报告生成器
│   ├── enhanced_scorer.py       # 增强7因子评分
│   └── scorer.py                # 基础评分器
├── crawler/                      # 爬虫工具模块 ⭐ v4.0新增
│   ├── downloader.py            # 下载器
│   ├── deduplicator.py          # 去重器
│   ├── rpa/                     # RPA爬虫核心
│   │   ├── captcha_solver.py    # 验证码解决
│   │   ├── session_storage.py   # 会话存储
│   │   ├── core/                # 核心模块
│   │   ├── taobao_rpa.py        # 淘宝RPA
│   │   └── extractors/          # 数据提取器
│   └── workflow/                # 工作流管理 ⭐ v5.0新增
│       ├── manager.py           # 工作流管理器
│       ├── executor.py          # 执行引擎
│       └── scheduler.py         # 任务调度器
└── scoring/                      # 评分系统
    └── enhanced_scorer.py
```

#### **工具分类体系**
```python
# 具有清晰边界的工具类别
BASIC_TOOLS = [get_current_time]                    # 通用工具
WEATHER_TOOLS = [get_weather_by_date]              # 纯天气查询
FISHING_TOOLS = [query_fishing_recommendation]     # 钓鱼+天气分析
LURE_TOOLS = [query_lure_recommendation]           # 装备数据库
CRAWLER_TOOLS = [run_crawler_workflow]             # 爬虫工作流 ⭐ v4.0新增
OCR_TOOLS = [extract_text_from_image]              # OCR文字提取 ⭐ v5.0新增
```

### 📊 评分算法系统

#### **7因子科学评分**
```python
def calculate_fishing_score(weather_data, location_data) -> dict:
    scores = {
        'temperature': calculate_temperature_score(weather_data['temp']),      # 25%权重
        'weather': calculate_weather_score(weather_data['condition']),        # 20%权重
        'wind': calculate_wind_score(weather_data['wind_speed']),            # 15%权重
        'pressure': analyze_pressure_trend(weather_data['pressure_history']), # 15%权重
        'humidity': calculate_humidity_score(weather_data['humidity']),        # 10%权重
        'seasonal': calculate_seasonal_score(weather_data['month']),          # 5%权重
        'lunar': calculate_lunar_score(lunar_phase)                           # 5%权重
    }
    return normalize_and_weight_scores(scores)
```

**算法特性**:
- **动态趋势分析**: 气压/温度变化对钓鱼活跃度的影响
- **季节适应**: 月度/每周钓鱼模式
- **月相集成**: 月相周期对鱼类活动的影响
- **权重评分**: 不同条件的最优平衡

---

## 5. 开发模式

### 🖼️ 智能图片合并系统

图片处理和OCR功能已迁移到独立的 `packages/data_processing` 包。

```python
# 图片合并功能
from packages.data_processing.image import BatchMergeProcessor, ImageMerger

# OCR功能
from packages.data_processing.ocr import OCRMergeProcessor
```

### 🕷️ 爬虫框架系统 ⭐ v5.0.2架构更新

爬虫功能已迁移到独立的 `packages/scraper` 包，提供完整的数据获取能力。

```python
# 基础爬虫使用
from packages.scraper import BaseSpider, CrawlItem
from packages.scraper.spiders import TaobaoSpider

# RPA自动化
from packages.scraper.rpa import TaobaoRPA

# 工作流管理
from packages.scraper.workflow import WorkflowManager
```

#### **两种图片合并方案对比**

系统提供两种图片合并方案，适用于不同场景：

| 特性 | BatchMergeProcessor | MergeAndSplitProcessor |
|------|---------------------|------------------------|
| 位置 | `batch_processor.py` | `splitter.py` |
| 合并策略 | 智能分组，基于内容感知 | 全部合并后按空白区域分割 |
| 文字检测 | OCR + 文字密度分析 | 无（基于亮度检测） |
| 表格检测 | 支持 | 不支持 |
| 分割方式 | 按内容语义分组 | 按空白行/区域分割 |
| 适用场景 | 复杂文档、混合内容、需要OCR | 简单图片序列、无需OCR |
| 依赖 | OCR服务（Ollama/SiliconFlow） | 仅图片处理库（Pillow） |
| 性能 | 较慢（需OCR识别） | 较快（纯图像处理） |

**使用示例**：

```python
# 方案一：智能内容感知合并（推荐用于复杂文档）
from packages.data_processing.image import BatchMergeProcessor
processor = BatchMergeProcessor(source_dir="./images")
result = processor.process()

# 方案二：简单合并分割（适合简单场景，无需OCR）
from packages.data_processing.image import MergeAndSplitProcessor
processor = MergeAndSplitProcessor(source_dir="./images")
result = processor.process()
```

详细使用说明请参考 [图片处理文档](./IMAGE_PROCESSING.md)。

### 🖥️ React管理前端架构 (v5.0新增) ⭐

#### **技术栈**
```typescript
// 前端核心技术栈
{
  "react": "19.2.0",           // React 19 最新版本
  "typescript": "^5.9.3",      // TypeScript
  "antd": "5.22.0",           // Ant Design UI库
  "react-router-dom": "6.28.0", // 路由管理
  "@reduxjs/toolkit": "2.3.0", // Redux状态管理
  "echarts": "5.5.0",         // 图表可视化
  "axios": "1.7.0",           // HTTP客户端
  "vite": "7.2.4"            // 构建工具
}
```

#### **组件架构**
```typescript
// apps/web-admin/src/components/
├── Layout/                    # 布局组件
│   ├── AppHeader.tsx         # 顶部导航
│   ├── AppSider.tsx          # 侧边栏
│   └── AppContent.tsx        # 内容区域
├── AuthGuard/                 # 认证守卫
│   ├── PrivateRoute.tsx      # 路由保护
│   └── PermissionCheck.tsx   # 权限检查
├── Charts/                    # 图表组件
│   ├── LineChart.tsx         # 折线图
│   ├── BarChart.tsx          # 柱状图
│   └── PieChart.tsx          # 饼图
└── Forms/                     # 表单组件
    ├── EquipmentForm.tsx     # 装备表单
    └── ConfigForm.tsx        # 配置表单
```

#### **页面模块**
```typescript
// apps/web-admin/src/pages/
├── Dashboard/                 # 仪表盘
│   ├── index.tsx             # 概览页面
│   └── components/           # 仪表盘组件
├── Equipment/                 # 装备管理
│   ├── List.tsx              # 装备列表
│   ├── Edit.tsx              # 编辑装备
│   └── Category.tsx          # 分类管理
├── Analytics/                 # 数据分析
│   ├── Reports.tsx           # 报表中心
│   ├── Trends.tsx            # 趋势分析
│   └── Statistics.tsx        # 统计图表
├── Crawler/                   # 爬虫管理
│   ├── Tasks.tsx             # 任务列表
│   └── Monitor.tsx           # 实时监控
├── Config/                    # 配置管理
│   ├── ApiKeys.tsx           # API密钥配置
│   └── System.tsx            # 系统配置
└── Monitor/                   # 监控中心
    ├── ApiStats.tsx          # API统计
    └── LlmStats.tsx          # LLM统计
```

#### **状态管理**
```typescript
// apps/web-admin/src/store/
import { configureStore } from '@reduxjs/toolkit'

export const store = configureStore({
  reducer: {
    auth: authSlice,           // 认证状态
    equipment: equipmentSlice, // 装备数据
    analytics: analyticsSlice, // 分析数据
    config: configSlice,       // 配置信息
    crawler: crawlerSlice,     // 爬虫状态
    monitor: monitorSlice,     // 监控数据
  },
})
```

### 🏭 模块化包模式 (Modular Package Pattern)

#### **自包含 Agent 包**
```python
# packages/agent_fishing/__init__.py
"""
Fishing Agent - 智能钓鱼助手（完全自包含）

公共 API:
- FishingAgent: 钓鱼助手 Agent
- create_agent: 工厂函数
- get_all_tools: 获取所有工具
"""

from .core import FishingAgent, create_agent, ModelFactory
from .tools import get_all_tools

# LangGraph 兼容
def get_agent():
    agent = create_agent(model_provider="zhipu")
    return agent.agent

__all__ = ["FishingAgent", "create_agent", "ModelFactory", "get_all_tools", "get_agent"]
```

#### **包级别工厂模式**
```python
# packages/agent_fishing/core/model_factory.py
class ModelFactory:
    PROVIDERS = {
        "zhipu": {
            "class": ChatOpenAI,
            "config": {
                "base_url": "https://open.bigmodel.cn/api/paas/v4/",
                "model": "glm-4-flash"
            }
        },
        "qwen": {
            "class": ChatTongyi,
            "config": {"model": "qwen-plus"}
        }
    }

    @classmethod
    def create(cls, provider: str) -> BaseChatModel:
        provider_config = cls.PROVIDERS[provider]
        return provider_config["class"](**provider_config["config"])
```

### 🛠️ 应用层分离模式

#### **CLI 应用实现**
```python
# apps/cli/main.py
from packages.agent_fishing import create_agent

def main():
    """CLI 应用主入口"""
    parser = argparse.ArgumentParser(description="智能钓鱼助手 CLI")
    parser.add_argument("--model", default="zhipu", help="LLM 提供商")
    args = parser.parse_args()

    agent = create_agent(model_provider=args.model)

    print("🎣 智能钓鱼助手 v3.1.1")
    print("输入 'exit' 退出程序")

    while True:
        try:
            user_input = input("\n请输入钓鱼相关问题: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                break

            result = agent.run(user_input)
            print(f"\n助手回复: {result}")
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    main()
```

#### **FastAPI 应用实现**
```python
# apps/api/main.py
from fastapi import FastAPI
from packages.agent_fishing import create_agent, get_all_tools

app = FastAPI(title="智能钓鱼助手 API", version="3.1.1")

@app.post("/api/v1/fishing/chat")
async def fishing_chat(request: ChatRequest):
    """智能钓鱼助手对话接口"""
    try:
        agent = create_agent(model_provider="zhipu")
        result = agent.run(request.query)
        return {"response": result, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "version": "3.1.1"}
```

### 🎯 工具模式 (Tool Pattern)

#### **模块化工具集成**
```python
# packages/agent_fishing/tools/__init__.py
from .basic import get_current_time
from .weather import get_weather_by_date
from .fishing_tool import query_fishing_recommendation
from .lure_tools import query_lure_recommendation

def get_all_tools():
    """获取所有可用工具"""
    return [
        get_current_time,
        get_weather_by_date,
        query_fishing_recommendation,
        query_lure_recommendation,
    ]
```

---

## 6. 数据流与状态管理

### 📊 请求处理管道

#### **v3.1.1 完整数据流**
```python
# 应用层路由
def process_user_request(user_input: str, app_type: str = "cli") -> str:
    # 步骤1: 应用层路由
    if app_type == "cli":
        return _process_cli_request(user_input)
    elif app_type == "api":
        return _process_api_request(user_input)

    # 步骤2: Agent 包处理
    agent = create_agent(model_provider="zhipu")

    # 步骤3: Agent 内部处理
    return agent.run(user_input)

# Agent 内部处理流程
def agent_processing(user_input: str) -> str:
    # 意图识别 → 工具选择 → 参数解析 → API调用 → 结果格式化
    intent = analyze_intent(user_input)
    tool = select_tool(intent)
    result = tool.invoke(**extract_params(user_input))
    return format_response(result)
```

### 💾 缓存策略

#### **包级别缓存实现**
```python
# packages/agent_fishing/utils/cache.py
class PackageCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str, ttl: int = 600) -> Optional[Any]:
        if key in self.cache:
            if time.time() - self.timestamps[key] < ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
```

### 🔗 外部API集成

#### **必需 API 依赖**
```python
# v3.1.1 API 配置
REQUIRED_APIS = {
    'DASHSCOPE_API_KEY': {
        'purpose': 'LLM + 嵌入服务',
        'provider': '阿里云DashScope',
        'features': ['对话生成', '文本嵌入']
    },
    'CAIYUN_API_KEY': {
        'purpose': '天气服务',
        'provider': '彩云天气',
        'features': ['实时天气', '72小时预报']
    },
    'AMAP_API_KEY': {
        'purpose': '定位服务',
        'provider': '高德地图',
        'features': ['地理编码', '坐标查询']
    }
}
```

---

## 7. 配置与部署

### 🔧 环境变量配置

#### **v3.1.1 配置**
```bash
# .env 文件配置示例

# 核心API服务 (必需)
DASHSCOPE_API_KEY=your-dashscope-api-key      # LLM + 嵌入服务
CAIYUN_API_KEY=your-caiyun-api-key            # 彩云天气API
AMAP_API_KEY=your-amap-api-key                # 高德地图API

# LLM提供商选择 (可选，默认使用zhipu)
ANTHROPIC_AUTH_TOKEN=your-zhipu-token         # 智谱AI GLM
OPENAI_API_KEY=your-openai-key                # OpenAI GPT

# 向量存储配置
VECTOR_EMBEDDING_MODEL=text-embedding-v3      # 嵌入模型
VECTOR_AUTO_INDEX=true                        # 懒加载索引
```

### 🧪 开发工作流

#### **环境设置**
```bash
# 1. 依赖安装
uv sync                    # 安装Python依赖
cd apps/web-admin && npm install  # 安装前端依赖

# 2. 环境变量配置
cp .env.example .env       # 复制环境变量模板

# 3. 验证安装
uv run python -c "from packages.agent_fishing import get_all_tools; print(f'工具数量: {len(get_all_tools())}')"

# 4. 运行 CLI 应用
uv run fishing             # 新版本 CLI 命令
uv run python main.py      # 兼容旧版本

# 5. 运行 API 服务
uv run fishing-api          # 启动 REST API
uv run uvicorn apps.api.main:app --reload  # 开发模式

# 6. 运行 React 前端 ⭐ v5.0新增
cd apps/web-admin
npm run dev                # 启动开发服务器
npm run build              # 构建生产版本
```

#### **测试执行**
```bash
# 运行所有测试
uv run pytest tests/

# 测试 Agent 包导入
uv run python -c "from packages.agent_fishing import create_agent; print('OK')"

# 测试工具列表
uv run python -c "from packages.agent_fishing import get_all_tools; print(len(get_all_tools()))"

# 运行特定测试
uv run pytest tests/agent_fishing/ -v
```

### 📦 项目结构验证

#### **v3.1.1 架构验证**
```bash
#!/bin/bash
# verify_v31_setup.sh - v3.1.1 架构验证

echo "🚀 智能钓鱼助手 v3.1.1 架构验证"
echo "=============================="

# 1. 包结构检查
echo "1. 模块化包结构..."
ls -la packages/agent_fishing/
echo "✅ packages/agent_fishing/ 存在"

# 2. 应用层检查
echo "2. 应用层结构..."
ls -la apps/
echo "✅ apps/ 目录存在"

# 3. Agent 包导入检查
echo "3. Agent 包导入..."
uv run python -c "
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools
print(f'✅ FishingAgent 导入成功')
print(f'✅ 工具数量: {len(get_all_tools())}')
"

# 4. CLI 命令检查
echo "4. CLI 命令..."
uv run fishing --help
echo "✅ fishing 命令可用"

# 5. API 服务检查
echo "5. API 服务..."
uv run fishing-api --help
echo "✅ fishing-api 命令可用"

echo "✅ v3.1.1 架构验证完成"
```

---

## 8. 工作流管理系统架构 (v5.0新增)

### 🔄 工作流管理核心组件

#### **系统架构**
```python
# 工作流核心组件
packages/agent_fishing/tools/crawler/
├── workflow/
│   ├── manager.py          # 工作流管理器
│   ├── executor.py         # 执行引擎
│   ├── scheduler.py        # 任务调度器
│   └── validator.py        # 工作流验证
├── executor/
│   ├── task_queue.py       # 任务队列
│   └── workers.py          # 工作进程
└── models/
    └── workflow.py         # 工作流数据模型
```

#### **核心特性**
1. **DAG执行引擎** - 支持复杂依赖关系的任务调度
2. **可视化编排** - 基于React的拖拽式工作流设计器
3. **实时监控** - WebSocket实时推送执行状态
4. **版本管理** - 工作流模板版本控制和回滚
5. **错误恢复** - 自动重试和断点续传

#### **工作流执行流程**
```python
# 工作流执行示例
from packages.agent_fishing.tools.crawler.workflow.manager import WorkflowManager

workflow = WorkflowManager()
execution = workflow.execute_template(
    template_id=1,
    params={"override_config": {...}}
)

# 执行状态监控
while execution.status == "running":
    status = workflow.get_status(execution.id)
    print(f"进度: {status.progress}")
    time.sleep(1)
```

#### **数据库模型**
```python
# 工作流相关表结构
class CrawlerWorkflowTemplate(Base):
    __tablename__ = "crawler_workflow_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(JSON, nullable=False)  # DAG步骤定义
    is_active = Column(Boolean, default=True)

class CrawlerSchedule(Base):
    __tablename__ = "crawler_schedules"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("crawler_workflow_templates.id"))
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="Asia/Shanghai")
```

#### **API架构层**
```python
# apps/api/routes/crawler.py
@router.post("/workflows/templates")
async def create_workflow_template(
    request: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_MANAGE))
):
    """创建工作流模板"""
    service = CrawlerService(db)
    return await service.create_workflow_template(request.dict())

@router.post("/workflows/execute")
async def execute_workflow(
    request: WorkflowExecutionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))
):
    """执行工作流"""
    manager = WorkflowManager(db)
    execution = await manager.execute_template(
        template_id=request.template_id,
        params=request.params or {}
    )
    return execution
```

### 🌐 WebSocket实时推送

#### **连接管理**
```python
# apps/api/websocket/manager.py
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

# 实时推送工作流状态
async def push_workflow_status(execution_id: str, status: dict):
    await websocket_manager.broadcast({
        "type": "workflow_status",
        "execution_id": execution_id,
        "data": status
    })
```

### 📱 React前端集成

#### **工作流设计器组件**
```typescript
// apps/web-admin/src/components/WorkflowDesigner/index.tsx
import { FlowEditor } from '@flow-designer/react';

export const WorkflowDesigner: React.FC = () => {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  const handleSave = async () => {
    const workflowData = {
      name: workflowName,
      steps: convertToWorkflowFormat(nodes, edges)
    };

    await api.post('/workflows/templates', workflowData);
  };

  return (
    <FlowEditor
      nodes={nodes}
      edges={edges}
      onNodesChange={setNodes}
      onEdgesChange={setEdges}
    />
  );
};
```

#### **实时监控组件**
```typescript
// apps/web-admin/src/components/WorkflowMonitor/index.tsx
export const WorkflowMonitor: React.FC = () => {
  const [executions, setExecutions] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/monitor');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'workflow_status') {
        updateExecutionStatus(data.execution_id, data.data);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <Table
      dataSource={executions}
      columns={workflowColumns}
    />
  );
};
```

### 🛠️ 调度系统

#### **APScheduler集成**
```python
# packages/agent_fishing/tools/crawler/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class WorkflowScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    def add_scheduled_job(
        self,
        schedule_id: int,
        cron_expression: str,
        timezone: str = "Asia/Shanghai"
    ):
        trigger = CronTrigger.from_crontab(cron_expression)
        self.scheduler.add_job(
            func=self.execute_scheduled_workflow,
            trigger=trigger,
            args=[schedule_id],
            id=f"schedule_{schedule_id}",
            timezone=timezone
        )
```

---

## 9. LLM导航指南

### 🎯 LLM理解辅助

#### **v3.1.1 架构理解要点**
1. **模块化包结构**: 每个包完全自包含，可独立发布
2. **应用层分离**: CLI 和 API 分离到 apps/ 目录
3. **LangGraph 兼容**: 支持 LangGraph Studio 集成
4. **统一工具接口**: 包级别的工具管理
5. **最小抽象**: 直接API调用减少复杂性

#### **关键文件导航 (v3.1.1)**
```python
# LLM修改项目时的关键入口点

# 1. 理解包架构
packages/agent_fishing/__init__.py      # 包入口和公共 API
packages/agent_fishing/core/agent.py    # 主代理类
packages/agent_fishing/tools/__init__.py # 统一工具接口

# 2. 应用层实现
apps/cli/main.py                         # CLI 应用
apps/api/main.py                         # FastAPI 后端

# 3. 共享资源
shared/config/                           # 全局配置

# 4. 项目配置
pyproject.toml                          # 项目配置和脚本
langgraph.json                          # LangGraph 配置
```

### 🚀 开发效率模式

#### **统一包接口**
```python
# LLM添加新功能的模式 (v3.1.1)

# 1. 在包中添加新工具
# packages/agent_fishing/tools/your_tool.py
from langchain_core.tools import tool

@tool
def your_new_tool(param1: str, param2: int = None) -> str:
    """新工具描述"""
    return "工具执行结果"

# 2. 在包工具初始化中注册
# packages/agent_fishing/tools/__init__.py
from .your_tool import your_new_tool

def get_all_tools():
    return [
        get_current_time,
        get_weather_by_date,
        query_fishing_recommendation,
        your_new_tool,  # 添加新工具
    ]
```

#### **应用层扩展**
```python
# 3. 在 CLI 应用中使用
# apps/cli/main.py
from packages.agent_fishing import create_agent, get_all_tools

def main():
    agent = create_agent(model_provider="zhipu")
    # CLI 逻辑

# 4. 在 API 应用中使用
# apps/api/main.py
from packages.agent_fishing import create_agent

@app.post("/api/v1/fishing/chat")
async def fishing_chat(request: ChatRequest):
    agent = create_agent(model_provider="zhipu")
    result = agent.run(request.query)
    return {"response": result}
```

### 🔧 扩展点指南

#### **添加新 Agent 包**
```python
# 1. 创建新包结构
mkdir -p packages/agent_weather/{core,tools,utils}

# 2. 创建包文件
touch packages/agent_weather/{__init__.py,core/__init__.py,tools/__init__.py,utils/__init__.py}

# 3. 包入口
# packages/agent_weather/__init__.py
from .core import WeatherAgent, create_agent
from .tools import get_all_tools

__all__ = ["WeatherAgent", "create_agent", "get_all_tools", "get_agent"]

# 4. 更新 langgraph.json
{
  "graphs": {
    "fishing": "./packages/agent_fishing:get_agent",
    "weather": "./packages/agent_weather:get_agent"
  }
}
```

#### **扩展应用层**
```python
# 5. 添加新的 CLI 应用
mkdir -p apps/weather_cli
echo "from packages.agent_weather import create_agent" > apps/weather_cli/main.py

# 6. 更新 pyproject.toml 脚本
[project.scripts]
fishing = "apps.cli.main:main"
fishing-api = "apps.api.main:main"
weather = "apps.weather_cli.main:main"  # 新命令
```

### 📝 开发最佳实践

#### **v3.1.1 包开发原则**
1. **包独立性**: 每个包完全自包含，不依赖其他包
2. **统一接口**: 所有包遵循相同的导入和创建模式
3. **LangGraph 兼容**: 提供 `get_agent()` 函数支持 Studio
4. **测试覆盖**: 每个包都有独立的测试套件

#### **性能优化指南**
```python
# 包级别缓存
from packages.agent_fishing.utils.cache import PackageCache

cache = PackageCache()

def get_weather_cached(location: str) -> dict:
    cached_data = cache.get(f"weather_{location}", ttl=600)
    if cached_data:
        return cached_data

    data = weather_api.get_weather(location)
    cache.set(f"weather_{location}", data)
    return data
```

---

## 🎯 总结

### v5.0.2 架构优势
- **模块化包架构**: 完全自包含的 Agent 包，支持独立发布
- **基础设施分离**: data_processing 和 scraper 包独立，提高复用性 ⭐ v5.0.2新增
- **全栈应用架构**: CLI、FastAPI 后端、React 前端三端分离
- **LangGraph 兼容**: 原生支持 LangGraph Studio
- **统一接口**: 一致的包导入和创建模式
- **向后兼容**: 保持旧版本入口点可用
- **扩展性强**: 易于添加新 Agent 包和应用
- **智能化功能**: 智能图片合并、OCR多提供商、工作流管理 ⭐ v5.0新增

### 核心技术演进
```python
# v3.1.1 → v5.0.2 主要升级
1. v3.1.1: 模块化包架构 + 动态Prompt中间件
2. v4.0.0: 爬虫监控模块 + RPA自动化
3. v5.0.0: React管理前端 + JWT认证 + 数据分析配置
4. v5.0.2: 基础设施模块分离 + 智能图片合并 + OCR多提供商 + 工作流管理
```

### 关键特性对比
| 版本 | 核心特性 | 新增功能 |
|------|----------|----------|
| v3.1.1 | 模块化包架构 | 动态Prompt中间件 |
| v4.0.0 | + RPA爬虫 | 爬虫监控模块 |
| v5.0.0 | + React前端 | JWT认证、数据分析 |
| v5.0.2 | + 智能处理 | 图片合并、OCR系统 |

### 迁移指南
从 v3.0.2.1 到 v5.0.2 的主要变化：
- **src/** → **packages/agent_fishing/**: 模块化包结构
- **新增 apps/**: CLI、API、React 三端应用
- **新增 shared/**: 共享配置和资源
- **CLI 命令**: `fishing` 替代直接运行 `main.py`
- **API 服务**: `fishing-api` 启动 FastAPI 后端
- **前端服务**: `cd apps/web-admin && npm run dev` 启动 React

### LLM导航价值
v5.0.2 架构特别针对LLM理解需求优化：
- **清晰边界**: 包、应用层、共享层分离明确
- **一致模式**: 统一的包结构模式便于理解和扩展
- **扩展指南**: 详细的包创建和应用扩展指南
- **最佳实践**: 模块化开发规范和模式
- **完整生态**: 从 Agent 包到全栈应用的完整解决方案

这个 v5.0.2 架构优先考虑**模块化**、**智能化**、**全栈化**和**扩展性**，为智能钓鱼助手提供现代化、可扩展的完整解决方案。

---

**文档版本**: v5.0.2
**最后更新**: 2025-12-19
**维护者**: 智能钓鱼助手开发团队