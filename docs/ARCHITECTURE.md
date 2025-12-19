# 智能钓鱼助手 - 项目架构文档

**版本**: v5.0.2 | **分支**: feature/miniprogram-dev | **架构**: 模块化Agent包 + JWT认证 + 多端支持

---

## 📋 目录

1. [项目概览](#1-项目概览)
2. [系统架构](#2-系统架构)
3. [模块组织](#3-模块组织)
4. [核心组件](#4-核心组件)
5. [开发模式](#5-开发模式)
6. [数据流与状态管理](#6-数据流与状态管理)
7. [LLM导航指南](#7-llm导航指南)
8. [扩展资源](#8-扩展资源)

---

## 1. 项目概览

### 🎯 核心特性
- **模块化Agent架构**: 4个独立包，完全自包含
- **动态Prompt中间件**: 智能选择提示词，Token效率提升50%+
- **7因子科学评分**: 温度、天气、风力、气压、湿度、季节、月相
- **JWT认证系统**: RBAC权限管理 + 微信小程序支持
- **智能处理系统**: OCR多提供商 + 图片合并 + 装备导入
- **多端支持**: CLI、API、React管理前端、微信小程序

### 🏗️ 架构哲学
```python
# 核心原则
1. 模块化包架构 - 每个包独立可发布
2. 零抽象原则 - 直接API调用，减少复杂性
3. 应用层分离 - CLI/API/Web/小程序独立实现
4. 诚实数据处理 - 绝不生成虚假数据
```

---

## 2. 系统架构

### 🏛️ 架构层次
```
用户界面层: CLI | API | React Web | 微信小程序
    ↓
应用层: apps/cli | apps/api | apps/web-admin
    ↓
模块包层: agent_fishing | data_processing | scraper
    ↓
工具集成层: 基础工具 | 天气工具 | 钓鱼工具 | 向量存储
    ↓
外部API层: 彩云天气 | 高德地图 | DashScope | 微信API
```

### 🔄 数据流模式
```
用户输入 → 应用层路由 → Agent包处理 → 工具选择 → API调用
数据处理 → 评分计算 → 结果格式化 → 响应返回
```

---

## 3. 模块组织

### 📁 核心目录结构 (v5.0.2)
```
packages/                      # 模块化包目录
├── agent_fishing/             # 钓鱼Agent包
│   ├── core/                  # Agent核心
│   ├── tools/                 # 工具集
│   └── middleware/            # 动态Prompt中间件
├── agent_equipment_import/    # 装备导入Agent包 ⭐ v5.0.2
├── data_processing/           # 数据处理包
│   ├── image/                 # 图片处理
│   ├── ocr/                   # OCR多提供商
│   └── dedup/                 # 去重工具
└── scraper/                   # 爬虫框架包

apps/                          # 应用层
├── cli/                       # CLI应用
├── api/                       # FastAPI后端
└── web-admin/                 # React管理前端

miniprogram/                   # 微信小程序 ⭐ v5.0.2新增
shared/                        # 共享资源
```

### 🔧 模块职责
- **agent_fishing**: 钓鱼核心功能，完全自包含
- **data_processing**: 图片处理、OCR、去重，独立可用
- **scraper**: 爬虫框架，通过configure_database()接收数据库连接
- **apps**: 各端应用实现，调用Agent包处理业务逻辑
- **miniprogram**: 微信小程序，面向终端用户的移动端应用

### 🎯 主要入口点
```python
# 编程接口
from packages.agent_fishing import FishingAgent, create_agent, get_all_tools
agent = create_agent(model_provider="zhipu")

# 图片处理
from packages.data_processing.image import BatchMergeProcessor
processor = BatchMergeProcessor(source_dir="./images")

# OCR功能
from packages.data_processing.ocr import OCRMergeProcessor
ocr_processor = OCRMergeProcessor(provider="siliconflow")

# 爬虫功能
from packages.scraper import BaseSpider, WorkflowManager
```

---

## 4. 核心组件

### 🔧 动态Prompt中间件
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

### 🔍 OCR多提供商系统
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

### 🤖 装备导入Agent ⭐ v5.0.2新增
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

### 🏫 模块化包模式
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

---

## 5. 开发模式

### 🛠️ 多端应用架构
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
miniprogram/app.js
// 微信登录 + API调用
```

### 🎯 工具模式
```python
# 统一工具访问模式
from packages.agent_fishing.tools import get_all_tools
from packages.agent_fishing.tools.weather import get_weather
from packages.agent_fishing.tools.fishing_tool import query_fishing_recommendation
```

---

## 6. 数据流与状态管理

### 📊 请求处理管道
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

### 💾 缓存策略
```python
# 分层缓存架构
Cache Layers:
├── L1: 内存缓存 (应用内, TTL: 5分钟)
├── L2: Redis缓存 (分布式, TTL: 1小时)
└── L3: 数据库缓存 (持久化, TTL: 24小时)
```

---

## 7. LLM导航指南

### 🎯 理解要点
1. **多端架构**: CLI、API、React Web、微信小程序四端支持
2. **模块化包结构**: 4个独立包，完全自包含
3. **应用层分离**: 每个端独立的应用实现
4. **统一工具接口**: 包级别的工具管理
5. **最小抽象**: 直接API调用减少复杂性

### 🚀 关键文件导航
```python
# 核心包架构
packages/agent_fishing/__init__.py           # 钓鱼Agent包入口
packages/data_processing/__init__.py         # 数据处理包入口
packages/scraper/__init__.py                 # 爬虫包入口

# 应用层实现
apps/cli/main.py                             # CLI应用
apps/api/main.py                             # FastAPI后端
apps/web-admin/src/App.tsx                   # React前端
miniprogram/app.js                           # 微信小程序 ⭐ v5.0.2

# 项目配置
pyproject.toml                              # 项目配置
langgraph.json                              # LangGraph配置
```

### 🔧 开发效率模式
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

---

## 8. 扩展资源

### 📚 角色专属文档
- **架构师**: [系统设计原则](architects/SYSTEM_DESIGN.md) - 深入理解设计理念和架构决策
- **开发者**: [开发工作流](developers/DEVELOPMENT_WORKFLOWS.md) - 日常开发指导和最佳实践
- **运维**: [部署运维指南](operations/DEPLOYMENT_GUIDE.md) - 生产环境部署和维护

> 💡 **提示**: 根据您的角色选择对应的详细文档，获取更深入的技术指导。

### 🔗 相关文档
- [API参考文档](API_REFERENCE.md) - 完整的API接口说明
- [用户指南](USER_GUIDE.md) - 功能使用指南
- [开发指南](DEVELOPMENT.md) - 开发环境配置
- [快速入门](GETTING_STARTED.md) - 项目快速开始

### 🌐 在线资源
- [LangChain官方文档](https://python.langchain.com/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [React官方文档](https://react.dev/)
- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)

---

## 🎯 总结

### v5.0.2 架构优势
- **多端支持**: CLI、API、React Web、微信小程序四端完整
- **模块化包架构**: 4个独立包，支持独立发布和复用
- **基础设施分离**: data_processing、scraper等包独立，提高复用性
- **全栈应用架构**: 前后端分离，各端独立开发
- **微信小程序集成**: 完整的小程序开发支持和API
- **智能处理系统**: OCR、图片合并、装备导入等AI功能
- **LangGraph兼容**: 原生支持LangGraph Studio

### 核心技术演进
```
v3.1.1: 模块化包架构 + 动态Prompt中间件
v4.0.0: 爬虫监控模块 + RPA自动化
v5.0.0: React管理前端 + JWT认证 + 数据分析配置
v5.0.2: 微信小程序 + 装备导入Agent + OCR多提供商
```

---

**文档版本**: v5.0.2
**最后更新**: 2024-12-20
**当前分支**: feature/miniprogram-dev
**维护者**: 智能钓鱼助手开发团队