# Fishing Agent - 智能钓鱼助手 v2.2.0

基于 LangChain 1.0+ 的智能钓鱼助手项目，专注于钓鱼时间推荐和天气分析。

> 🎣 智能分析天气条件，推荐最佳钓鱼时间 - **架构简化版**

## ✨ 核心功能

- **🎣 智能钓鱼推荐**: 基于7因子评分算法的专业钓鱼分析
- **🌤️ 实时天气查询**: 集成彩云天气API，支持全国3,142+地区
- **🗺️ 智能坐标服务**: 高德地图API集成，多级缓存优化
- **🤖 LangChain智能体**: 多模型支持，自然语言交互
- **📊 同步架构**: 稳定可靠的同步版本，避免异步复杂性

## 🏗️ 技术架构

### 核心特性
- **🔄 中央服务管理**: 单例模式管理服务实例，避免重复初始化
- **🔧 接口抽象层**: 松耦合设计，支持依赖注入
- **⚡ 多级缓存**: 内存+文件缓存，90%+命中率
- **🛡️ 同步稳定**: 完全同步架构，消除事件循环问题
- **🧠 智能匹配**: 智能地名匹配和坐标解析
- **🚀 纯LangChain架构**: 简洁高效的LangChain 1.0+实现，无额外包装层
- **📝 异步中间件**: 意图分析、性能监控、日志记录

### 已修复的技术问题
- ✅ **数据库路径问题**: 修复相对路径导致的数据库连接失败
- ✅ **中间件兼容性**: 解决AgentMiddleware基类属性设置冲突
- ✅ **模型配置统一**: 统一GLM-4.6模型配置，支持智谱AI平台
- ✅ **异步中间件**: 完整的异步支持，ModelCallRecord正确实例化
- ✅ **服务管理**: 通过服务管理器统一管理坐标服务依赖
- ✅ **LangGraph集成问题**: 修复404 API端点错误和中间件TypeError
  - 修复环境变量冲突导致的API路径错误
  - 修复ToolCallRecord构造函数参数错误
  - 修复缺失的_extract_token_usage方法
  - 解决total_response_time_ms属性名称错误
- ✅ **天气API容错优化**: 扩展hourly预报从48到72小时，增强hourly/dual API降级机制
- ✅ **时间戳解析问题**: 修复ISO 8601格式解析，支持跨日期数据聚合
- ✅ **架构清理**: 移除tools模块循环依赖，简化为纯LangChain 1.0+架构

### 🎣 钓鱼推荐系统
- **7因子评分算法**: 温度、天气、风力、气压、湿度、季节、月相
- **智能时间段推荐**: 解决传统"86分问题"，提供最佳钓鱼时间
- **自然语言理解**: 支持中文查询，如"明天哪里钓鱼好？"
- **全国覆盖**: 支持3,142+地区的钓鱼条件分析

### 🌤️ 天气服务
- **实时数据**: 彩云天气API集成，实时天气信息
- **日期查询**: 支持相对日期("明天")和绝对日期("2024-12-25")
- **小时预报**: 72小时详细天气预报，完整覆盖3天钓鱼规划
- **智能降级**: hourly/daily双API降级机制，确保高可用性
- **容错机制**: ISO 8601时间戳解析，跨日期数据聚合，零虚假数据原则

### 🗺️ 坐标服务
- **高德地图API**: 精确的地理坐标查询
- **智能缓存**: 90%+命中率，响应时间<1ms
- **地名匹配**: 支持别名简称和模糊匹配
- **全国覆盖**: 中国所有行政区划95%+覆盖率

## 🚀 快速开始

### 环境要求
- Python 3.11+
- uv 包管理器

### 安装依赖
```bash
# 安装依赖
uv sync
```

### 配置环境变量
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑 .env 文件，添加您的API密钥
# 必需的API密钥：
# - CAIYUN_API_KEY: 彩云天气API
# - AMAP_API_KEY: 高德地图API
# - ANTHROPIC_AUTH_TOKEN: 智谱AI API (推荐)
```

### 运行项目

#### 方法一：交互式应用（推荐）
```bash
uv run python main.py
```

#### 方法二：直接运行Agent（新！）
```bash
# 从项目根目录运行
uv run python src/agent.py

# 或者从src目录运行
cd src && uv run python agent.py
```

> ✅ **注意**: v2.2.0新增功能！无需复杂的PYTHONPATH配置，直接运行即可！

#### 方法三：激活虚拟环境
```bash
source .venv/bin/activate
python main.py
```

## 💻 使用示例

### 基础使用
```python
# 导入智能体
from src.agent import create_optimized_fishing_agent

# 创建智能体实例
agent = create_optimized_fishing_agent(model_provider="zhipu")

# 钓鱼推荐查询
response = agent.run("明天什么时段去杭州钓鱼比较好？")
print(response)

# 天气查询
response = agent.run("北京今天天气怎么样？")
print(response)
```

### 直接工具调用
```python
from src.tools.langchain_weather_tools_sync import (
    query_current_weather,
    query_fishing_recommendation
)

# 查询当前天气
result = query_current_weather.invoke({'place': '杭州'})
print(f"当前天气: {result}")

# 钓鱼推荐
result = query_fishing_recommendation.invoke({
    'location': '富阳区',
    'date': '明天'
})
print(f"钓鱼推荐: {result}")
```

### 坐标服务使用
```python
from src.services.coordinate.amap_coordinate_service import AmapCoordinateService

service = AmapCoordinateService()
coords = service.get_coordinate("河桥镇")
print(f"坐标: {coords}")
```

## 📁 项目结构

```
fishing-agent/
├── src/                          # 源代码目录
│   ├── agent.py                  # 🤖 LangChain智能体主入口
│   ├── tools/                    # 🛠️ 简化工具模块
│   │   ├── __init__.py          # 工具统一接口
│   │   ├── basic_tools.py       # 基础工具（时间、数学等）
│   │   ├── weather_tools.py     # 天气工具（实时天气、预报）
│   │   └── fishing_tools.py     # 钓鱼工具（推荐、评分）
│   ├── services/                 # 🌐 服务层（API调用）
│   └── tests/                    # 🧪 测试套件
├── main.py                       # 🚀 程序入口
├── pyproject.toml                # 📦 项目配置
├── CLAUDE.md                     # 📖 Claude开发指南
├── CHANGELOG.md                  # 📋 更新日志
├── README.md                     # 📋 项目说明
└── docs/                         # 📖 详细文档
    ├── TOOLS_GUIDE.md           # 工具使用指南
    ├── API.md                   # API文档
    └── CONFIGURATION_GUIDE.md   # 配置指南
```

## 🧪 测试

```bash
# 运行测试套件
uv run pytest src/tests/

# 运行特定测试
uv run python src/tests/test_enhanced_fishing_scorer.py

# 运行集成测试
uv run python src/tests/integration/verify_national_integration.py
```

## 🔧 开发指南

### 代码规范
- 使用 Python 3.11+ 语法
- 遵循 PEP 8 代码风格
- 添加类型注解和文档字符串
- 编写单元测试

### 添加新功能
1. 在相应模块中实现功能
2. 更新测试用例
3. 运行测试确保通过
4. 更新文档

## 📄 许可证

MIT License

---

> 🎣 智能分析，精准钓鱼！