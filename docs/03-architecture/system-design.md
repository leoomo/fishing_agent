# 智能钓鱼助手 - 系统架构设计

**版本**: v5.1.0 | **架构**: 模块化Agent包 + JWT认证 + 多端支持

## 🎯 核心特性

- **模块化Agent架构**: 4个独立包，完全自包含
- **动态Prompt中间件**: 智能选择提示词，Token效率提升50%+
- **7因子科学评分**: 温度、天气、风力、气压、湿度、季节、月相
- **JWT认证系统**: RBAC权限管理 + 微信小程序支持
- **智能处理系统**: OCR多提供商 + 图片合并 + 装备导入
- **内容管理系统**: 文章管理 + 网络采集 + LLM翻译增强 + 向量搜索
- **多端支持**: CLI、API、React Web、微信小程序

## 🏗️ 架构哲学

```python
# 核心原则
1. 模块化包架构 - 每个包独立可发布
2. 零抽象原则 - 直接API调用，减少复杂性
3. 应用层分离 - CLI/API/Web/小程序独立实现
4. 诚实数据处理 - 绝不生成虚假数据
```

## 🌐 系统架构

### 架构层次
```
用户界面层: CLI | API | Web UI | Miniprogram
    ↓
应用层: apps/cli | apps/api | apps/web-admin
    ↓
模块包层: agent_fishing | data_processing | scraper
    ↓
工具集成层: 基础工具 | 天气工具 | 钓鱼工具 | 向量存储
    ↓
外部API层: 彩云天气 | 高德地图 | DashScope | 微信API
```

### 数据流模式
```
用户输入 → 应用层路由 → Agent包处理 → 工具选择 → API调用
数据处理 → 评分计算 → 结果格式化 → 响应返回
```

## 📦 模块组织

### 核心目录结构 (v5.1.0)
```
packages/                      # 模块化包目录
├── agents/                   # Agent统一目录 (v5.1.0 重构)
│   ├── agent_component/      # 共享组件
│   │   └── monitoring/       # 统一监控回调
│   ├── fishing/              # 钓鱼Agent包
│   │   ├── core/             # Agent核心
│   │   ├── tools/            # 工具集
│   │   │   ├── user_equipment/ # 用户装备管理
│   │   │   └── lure/          # 路亚工具
│   │   └── middleware/       # 动态Prompt中间件
│   └── equipment_import/     # 装备导入Agent包
├── data_processing/          # 数据处理包
│   ├── image/                # 图片处理
│   ├── ocr/                  # OCR多提供商
│   └── dedup/                # 去重工具
└── scraper/                  # 爬虫框架包 (分布式Master-Worker)
    ├── master/               # Master节点服务
    ├── worker/               # Worker节点
    ├── spiders/              # 具体爬虫实现
    └── rpa/                  # RPA自动化 (Playwright)

apps/                          # 应用层
├── cli/                      # CLI应用
├── api/                      # FastAPI后端
│   ├── routes/               # API路由
│   ├── services/             # 业务服务层 ⭐ v5.1.0 新增
│   │   ├── article_fetcher.py  # 文章网络采集服务
│   │   ├── rig_fetcher.py      # 钓组网络采集服务
│   │   ├── vector_store.py     # 向量存储服务
│   │   └── analytics_service.py # 数据分析服务
│   ├── models/               # 数据库模型
│   └── schemas/              # 请求/响应模型
└── web-admin/                # React管理前端

fishing_agent_app/            # 微信小程序
shared/                        # 共享资源
├── config/                   # 全局配置
└── data/                     # 数据库文件
```

### 模块职责
- **agents/fishing**: 钓鱼核心功能，完全自包含
- **agents/equipment_import**: 装备导入功能，支持文本压缩
- **agents/agent_component**: 统一监控组件 (MonitoringCallback)
- **data_processing**: 图片处理、OCR、去重，独立可用
- **scraper**: 分布式爬虫框架 (Master-Worker架构)
- **apps/api/services**: 业务服务层，包含网络采集、向量存储等服务 ⭐ v5.1.0
- **apps**: 各端应用实现，调用Agent包处理业务逻辑
- **fishing_agent_app**: 微信小程序，面向终端用户的移动端应用

## 🎯 主要入口点

```python
# Agent 核心功能 (v5.1.0 新路径)
from packages.agents.fishing import FishingAgent, create_agent, get_all_tools
agent = create_agent(model_provider="zhipu")

# 统一监控组件 (v5.1.0 新增)
from packages.agents.agent_component.monitoring import MonitoringCallback

# 用户装备管理 (v5.1.0 新增)
from packages.agents.fishing.tools.user_equipment import (
    UserEquipmentManager,
    EquipmentRecommender
)

# 装备导入功能
from packages.agents.equipment_import import EquipmentImportAgent

# 图片处理
from packages.data_processing.image import BatchMergeProcessor
processor = BatchMergeProcessor(source_dir="./images")

# OCR功能
from packages.data_processing.ocr import OCRMergeProcessor
ocr_processor = OCRMergeProcessor(provider="siliconflow")

# 爬虫功能 (分布式Master-Worker)
from packages.scraper import BaseSpider, WorkflowManager
from packages.scraper.worker import CrawlerWorker

# 内容采集服务 (v5.1.0 新增)
from apps.api.services.article_fetcher import ArticleFetcherService
fetcher = ArticleFetcherService(db_path="shared/data/equipment.db")
fetcher.start_fetch(source_id="wikipedia", use_llm=True)

# 向量搜索服务 (v5.1.0 新增)
from apps.api.services.vector_store import ArticleVectorStore
vector_store = ArticleVectorStore()
results = vector_store.search("钓鱼技巧", limit=10)
```

## 🔧 核心组件

### 动态Prompt中间件
```python
# 智能提示词选择系统
@dynamic_prompt
def select_prompt_by_query_type(request: ModelRequest) -> str:
    """
    Token效率优化：
    - 钓鱼查询: BASE(600) + FISHING_OUTPUT_RULES(600) = ~1200 tokens
    - 天气查询: BASE(600) + WEATHER_QUERY_RULES(200) = ~800 tokens
    - 其他查询: BASE = ~600 tokens
    """
    if "钓鱼" in user_input:
        return BASE_SYSTEM_PROMPT + FISHING_OUTPUT_RULES
    elif any(kw in user_input for kw in ["天气", "温度"]):
        return BASE_SYSTEM_PROMPT + WEATHER_QUERY_RULES
    else:
        return BASE_SYSTEM_PROMPT
```

### OCR多提供商系统
```python
# 提供商抽象层
class BaseOCRProvider:
    async def recognize(self, image: bytes) -> OCRResult:
        pass

# Ollama本地OCR
class OllamaOCRProvider(BaseOCRProvider):
    def __init__(self, model: str = "deepseek-ocr"):
        self.client = Ollama(base_url="http://localhost:11434")

# SiliconFlow云端OCR
class SiliconFlowOCRProvider(BaseOCRProvider):
    def __init__(self, api_key: str):
        self.base_url = "https://api.siliconflow.cn"
```

### 装备导入Agent ⭐ v5.0.2
```python
# 文本压缩中间件
class TextCompressor:
    def compress(self, text: str) -> CompressionResult:
        # 1. 删除冗余内容
        cleaned = self._remove_redundant(text)
        # 2. 提取核心信息
        core_info = self._extract_core(cleaned)
        # 3. 重建压缩文本
        compressed = self._rebuild_text(core_info)
        return CompressionResult(compressed_text=compressed)
```

### 文章网络采集服务 ⭐ v5.1.0
```python
# 维基百科文章采集 + LLM翻译增强
class ArticleFetcherService:
    def start_fetch(self, source_id: str = "wikipedia", use_llm: bool = True):
        """
        采集流程：
        1. 从预设的维基百科钓鱼文章列表获取URL
        2. 调用Wikipedia REST API获取英文内容
        3. 使用LLM(Qwen Plus)翻译为中文
        4. 生成摘要、标签、分类
        5. 保存为草稿文章待审核
        """
        pass

# 支持的操作
fetcher.start_fetch()    # 开始采集
fetcher.pause_fetch()    # 暂停采集
fetcher.retry_failed()   # 重试失败项
fetcher.get_progress()   # 获取进度
```

### 模块化包模式
```python
# 包级别的统一接口
from packages.agent_fishing import get_all_tools

def get_all_tools():
    return [
        get_current_time,
        get_weather_by_date,
        query_fishing_recommendation,
        query_lure_recommendation,
    ]
```

## 🚀 开发模式

### 多端应用架构
```python
# CLI应用
apps/cli/main.py
from packages.agent_fishing import create_agent

# FastAPI应用
apps/api/main.py
@app.post("/api/v1/fishing/chat")
async def fishing_chat(request: ChatRequest):
    agent = create_agent(model_provider="zhipu")
    result = agent.run(request.query)
    return {"response": result}

# React前端应用
apps/web-admin/src/App.tsx
// 使用React 19.2.0 + TypeScript + Ant Design

# 微信小程序应用
fishing_agent_app/app.js
// 微信登录 + API调用
```

### 工具模式
```python
# 统一工具访问模式
from packages.agent_fishing.tools import get_all_tools
from packages.agent_fishing.tools.weather import get_weather
from packages.agent_fishing.tools.fishing_tool import query_fishing_recommendation
```

## 🌊 数据流与状态管理

### 请求处理管道
```python
def process_user_request(user_input: str, app_type: str = "cli") -> str:
    # 1. 认证验证 (API/Web/小程序需要)
    if app_type in ["api", "web", "miniprogram"]:
        user = verify_token(auth_token)

    # 2. Agent包处理
    agent = create_agent(model_provider="zhipu")

    # 3. 返回结果
    return agent.run(user_input)
```

### 缓存策略
```python
# 分层缓存架构
Cache Layers:
├── L1: 内存缓存 (应用内, TTL: 5分钟)
├── L2: Redis缓存 (分布式, TTL: 1小时)
└── L3: 数据库缓存 (持久化, TTL: 24小时)
```

## 🎨 LLM导航指南

### 理解要点
1. **多端架构**: CLI、API、React Web、微信小程序四端支持
2. **模块化包结构**: 4个独立包，完全自包含
3. **应用层分离**: 每个端独立的应用实现
4. **统一工具接口**: 包级别的工具管理
5. **最小抽象**: 直接API调用减少复杂性

### 关键文件导航
```python
# 核心包架构 (v5.1.0 新路径)
packages/agents/fishing/__init__.py           # 钓鱼Agent包入口
packages/agents/agent_component/monitoring/  # 统一监控组件
packages/agents/equipment_import/__init__.py  # 装备导入Agent包入口
packages/data_processing/__init__.py         # 数据处理包入口
packages/scraper/__init__.py                 # 爬虫包入口

# 应用层实现
apps/cli/main.py                             # CLI应用
apps/api/main.py                             # FastAPI后端
apps/web-admin/src/App.tsx                   # React前端
fishing_agent_app/app.js                    # 微信小程序 ⭐ v5.0.2

# 项目配置
pyproject.toml                              # 项目配置
langgraph.json                              # LangGraph配置
```

### 开发效率模式
```python
# LLM添加新功能的模式
# 1. 在包中添加新工具
@tool
def your_new_tool(param1: str, param2: int = None) -> str:
    """新工具描述"""
    return "工具执行结果"

# 2. 在包工具初始化中注册
def get_all_tools():
    return [
        # 现有工具...
        your_new_tool,  # 添加新工具
    ]

# 3. 在各端应用中使用
# CLI/API/Web/小程序都会自动获得新工具
```

## 🏗️ 架构优势

### v5.1.0 架构优势
- **多端支持**: CLI、API、React Web、微信小程序四端完整
- **模块化包架构**: 4个独立包，支持独立发布和复用
- **基础设施分离**: data_processing、scraper等包独立，提高复用性
- **全栈应用架构**: 前后端分离，各端独立开发
- **内容管理系统**: 文章管理、网络采集、LLM翻译增强、向量搜索 ⭐ 新增
- **智能处理系统**: OCR、图片合并、装备导入等AI功能
- **LangGraph兼容**: 原生支持LangGraph Studio

### 核心技术演进
```
v3.1.1: 模块化包架构 + 动态Prompt中间件
v4.0.0: 爬虫监控模块 + RPA自动化
v5.0.0: React管理前端 + JWT认证 + 数据分析配置
v5.0.2: 微信小程序 + 装备导入Agent + OCR多提供商
v5.1.0: 内容管理系统 + 网络采集 + LLM翻译增强 + 向量搜索 ⭐ 当前
```

## 📊 性能指标

### 系统性能
- **响应时间**: API平均响应 < 500ms
- **并发处理**: 支持1000+并发请求
- **Token效率**: 动态Prompt减少50%+ Token消耗
- **缓存命中率**: 85%+ 缓存命中率

### 可扩展性
- **包独立性**: 每个包可独立部署和扩展
- **数据库**: 支持SQLite到PostgreSQL迁移
- **模型支持**: 支持多种LLM模型热切换
- **OCR提供商**: 支持本地和云端OCR动态切换

## 🔮 未来架构规划

### v6.0.0 计划特性
- **微服务架构**: 包级别服务化
- **事件驱动**: 基于消息队列的异步处理
- **AI平台化**: 支持自定义AI模型训练
- **多租户**: 企业级多租户支持
- **国际化**: 多语言和多地区支持

### 技术债务管理
- **API版本化**: 向后兼容的API演进
- **测试覆盖**: 90%+ 代码测试覆盖率
- **文档完善**: 自动生成API文档
- **监控告警**: 全链路监控和智能告警

## 🔗 相关资源

### 架构文档
- [模块架构](./module-architecture.md) - 详细模块设计
- [数据库设计](./database-schema.md) - 数据模型设计
- [安全架构](./security-design.md) - 认证和安全设计
- [可扩展性](./scalability.md) - 性能和扩展设计
- [设计决策](./design-decisions.md) - 重要架构决策

### 开发资源
- [开发指南](../02-developer-guide/) - 开发环境和流程
- [API参考](../05-api-reference/) - 完整API文档
- [部署指南](../04-operations/deployment-guide.md) - 生产部署
- [运维指南](../04-operations/) - 系统运维

---

**文档版本**: v5.1.0
**最后更新**: 2026-01-17
**当前分支**: feature/article-optimization
**维护者**: 智能钓鱼助手开发团队