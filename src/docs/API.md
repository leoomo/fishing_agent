# API 文档

本文档描述了 LangChain 智能体项目中的主要 API 接口和使用方法。

## 🔄 版本说明

### 同步版本架构 (v2.1.0+) ⭐ **推荐**

项目已完全重构为**同步版本**，提供更好的稳定性和易用性：

- ✅ **完全同步**: 移除所有 `async/await` 代码，消除事件循环复杂性
- ✅ **稳定性提升**: 彻底解决 "Event loop is closed" 错误
- ✅ **简化架构**: 标准Python函数调用，易于理解和维护
- ✅ **同步API客户端**: 使用 `requests` 替代 `aiohttp`，性能稳定
- ✅ **工具集成完善**: LangChain工具完全同步化，支持智能体调用

### 异步版本 (已弃用)

为保持向后兼容性，保留原有的异步版本文件，但不推荐在新项目中使用。

---

## 目录

- [核心架构 API](#核心架构-api)
  - [ITool 接口](#itool-接口)
  - [BaseTool 基类](#basetool-基类)
  - [ToolRegistry 注册器](#toolregistry-注册器)
- [新工具模块 API](#新工具模块-api)
  - [TimeTool 时间工具](#timetool-时间工具)
  - [MathTool 数学工具](#mathtool-数学工具)
  - [WeatherTool 天气工具](#weathertool-天气工具)
  - [SearchTool 搜索工具](#searchtool-搜索工具)
- [智能体 API](#智能体-api)
- [天气服务 API](#天气服务-api)
  - [EnhancedCaiyunWeatherService (增强版)](#enhancedcaiyunweatherservice-类-)
  - [CaiyunWeatherService (基础版)](#caiyunweatherservice-类)
- [地名匹配 API](#地名匹配-api)
- [缓存系统 API](#缓存系统-api)
- [数据库 API](#数据库-api)
- [同步工具函数 API](#同步工具函数-api-)
  - [LangChain 同步工具](#langchain-同步工具)
  - [同步天气工具](#同步天气工具)
  - [同步钓鱼分析工具](#同步钓鱼分析工具)
- [环境配置](#环境配置)
- [错误处理](#错误处理)
- [使用示例](#使用示例)

## 核心架构 API

### ITool 接口

所有工具必须实现的核心接口，定义了工具的基本规范。

```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass

@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    version: str
    author: str
    tags: List[str]
    dependencies: List[str]

@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: str = None
    metadata: Dict[str, Any] = None

class ITool(ABC):
    """工具接口"""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具操作"""
        pass

    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        pass

### 同步工具接口 (Sync Version)

**新增同步版本的工具接口**，提供更简单易用的API：

```python
@dataclass
class SyncToolResult:
    """同步工具执行结果"""
    success: bool
    data: Any = None
    error: str = None
    metadata: Dict[str, Any] = None

class ISyncTool(ABC):
    """同步工具接口"""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> SyncToolResult:
        """执行工具操作 (同步版本)"""
        pass

    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        pass
```
```

### BaseTool 基类

提供工具的基础实现，包含通用功能。

```python
from core.base_tool import BaseTool

class MyTool(BaseTool):
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        # 初始化工具特定配置

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_tool",
            description="我的自定义工具",
            version="1.0.0",
            author="author",
            tags=["custom"],
            dependencies=[]
        )

    def validate_input(self, **kwargs) -> bool:
        # 验证输入参数
        return True

    async def _execute(self, **kwargs) -> ToolResult:
        # 实现具体功能
        return ToolResult(success=True, data="result")
```

### ToolRegistry 注册器

工具注册和管理系统，支持动态注册和发现。

```python
from core.registry import ToolRegistry

# 创建注册器
registry = ToolRegistry()

# 注册工具实例
registry.register("my_tool", MyTool())

# 注册工具类（延迟实例化）
registry.register_class(MyTool)

# 获取工具
tool = registry.get_tool("my_tool")
result = await tool.execute(param="value")

# 列出所有工具
tools = registry.list_tools()
print(tools)  # ["my_tool", ...]
```

## 新工具模块 API

### TimeTool 时间工具

提供时间查询、计算、格式化和时区转换功能。

#### 初始化

```python
from tools import TimeTool

# 使用默认配置
time_tool = TimeTool()

# 使用自定义配置
config = {
    "default_timezone": "Asia/Shanghai",
    "precision": 10
}
time_tool = TimeTool(config)
```

#### 主要方法

##### async execute(operation: str, **kwargs) -> ToolResult

执行时间操作。

**支持的操作：**
- `current_time` - 获取当前时间
- `add_time` - 时间加法
- `subtract_time` - 时间减法
- `format_time` - 时间格式化
- `convert_timezone` - 时区转换

**示例：**
```python
# 获取当前时间
result = await time_tool.execute(operation='current_time')
if result.success:
    data = result.data
    print(f"当前时间: {data['formatted']} ({data['timezone']})")

# 时间加法
result = await time_tool.execute(
    operation='add_time',
    base_time='2024-01-01T10:00:00',
    days=1,
    hours=2
)
print(f"新时间: {result.data['formatted']}")

# 时间格式化
result = await time_tool.execute(
    operation='format_time',
    time_input='2024-01-01T10:30:45',
    format_type='full'
)
print(f"格式化: {result.data['formatted']}")
```

### MathTool 数学工具

提供数学计算和统计功能。

#### 初始化

```python
from tools import MathTool

# 使用默认配置
math_tool = MathTool()

# 使用自定义配置
config = {
    "precision": 15,
    "enable_cache": True
}
math_tool = MathTool(config)
```

#### 主要方法

##### async execute(operation: str, **kwargs) -> ToolResult

执行数学操作。

**支持的操作：**
- `add`, `subtract`, `multiply`, `divide` - 基本运算
- `power`, `sqrt` - 幂运算和平方根
- `sin`, `cos`, `tan` - 三角函数
- `log` - 对数函数
- `factorial` - 阶乘
- `average`, `median`, `mode` - 统计函数
- `std_dev` - 标准差
- `random` - 随机数生成
- `round` - 四舍五入

**示例：**
```python
# 基本运算
result = await math_tool.execute(operation='add', a=10, b=5)
print(result.data['formatted'])  # 10 + 5 = 15

# 高级函数
result = await math_tool.execute(operation='sqrt', number=144)
print(result.data['formatted'])  # √144 = 12.0

# 三角函数
result = await math_tool.execute(operation='sin', angle=30, degrees=True)
print(result.data['formatted'])  # sin(30°) = 0.5

# 统计计算
numbers = [1, 2, 3, 4, 5]
result = await math_tool.execute(operation='average', numbers=numbers)
print(f"平均值: {result.data['result']}")

# 随机数
result = await math_tool.execute(operation='random', min_val=1, max_val=100)
print(f"随机数: {result.data['result']}")
```

### WeatherTool 天气工具

提供天气查询和预报功能。

#### 初始化

```python
from tools import WeatherTool

# 使用默认配置
weather_tool = WeatherTool()

# 使用自定义配置
config = {
    "api_key": "your-api-key",
    "timeout": 15,
    "cache_ttl": 1800,
    "max_results": 10
}
weather_tool = WeatherTool(config)
```

#### 主要方法

##### async execute(operation: str, **kwargs) -> ToolResult

执行天气操作。

**支持的操作：**
- `current_weather` - 获取当前天气
- `get_coordinates` - 获取位置坐标
- `get_weather` - 获取天气信息（兼容方法）
- `batch_weather` - 批量天气查询
- `search_locations` - 位置搜索
- `weather_forecast` - 天气预报
- `weather_by_date` - 指定日期天气查询（带错误码）
- `weather_by_datetime` - 时间段天气查询（带错误码）
- `hourly_forecast` - 小时级天气预报（带错误码）

**示例：**
```python
# 获取当前天气
result = await weather_tool.execute(
    operation='current_weather',
    location='北京'
)
if result.success:
    data = result.data
    print(f"北京天气: {data['condition']}")
    print(f"温度: {data['temperature']}°C")
    print(f"湿度: {data['humidity']}%")

# 批量查询
cities = ['北京', '上海', '广州']
result = await weather_tool.execute(
    operation='batch_weather',
    locations=cities
)
for item in result.data['results']:
    if item['success']:
        weather = item['data']
        print(f"{item['location']}: {weather['condition']} {weather['temperature']}°C")

# 位置搜索
result = await weather_tool.execute(
    operation='search_locations',
    query='北',
    limit=5
)
for match in result.data['matches']:
    print(f"{match['name']}: ({match['longitude']}, {match['latitude']})")

# 天气预报
result = await weather_tool.execute(
    operation='weather_forecast',
    location='深圳',
    days=3
)
for day in result.data['forecast']:
    print(f"第{day['day']}天: {day['condition']} {day['temperature']}°C")

# 错误码系统使用
result = await weather_tool.execute(
    operation='weather_by_date',
    location='北京',
    date='2024-12-25'
)

if result.success:
    print("✅ 请求成功")
    if result.data:
        print(f"温度: {result.data.get('temperature', 'N/A')}°C")
else:
    print(f"❌ 请求失败: {result.error}")

    # 获取详细错误信息
    if result.metadata:
        error_code = result.metadata.get("error_code")
        status_message = result.metadata.get("status_message")
        description = result.metadata.get("description")

        print(f"错误码: {error_code}")
        print(f"状态: {status_message}")
        print(f"描述: {description}")
```

### SearchTool 搜索工具

提供网络搜索和知识检索功能。

#### 初始化

```python
from tools import SearchTool

# 使用默认配置
search_tool = SearchTool()

# 使用自定义配置
config = {
    "max_results": 20,
    "timeout": 10,
    "cache_ttl": 3600
}
search_tool = SearchTool(config)
```

#### 主要方法

##### async execute(operation: str, **kwargs) -> ToolResult

执行搜索操作。

**支持的操作：**
- `web_search` - 网络搜索
- `knowledge_search` - 知识库搜索
- `search_by_category` - 按类别搜索
- `get_definition` - 获取定义
- `get_features` - 获取特性
- `get_applications` - 获取应用
- `search_similar` - 相似搜索
- `advanced_search` - 高级搜索

**示例：**
```python
# 知识库搜索
result = await search_tool.execute(
    operation='knowledge_search',
    query='python'
)
if result.success:
    data = result.data
    print(f"找到 {data['total_results']} 个结果")
    for item in data['results']:
        print(f"- {item['topic']}: {item['description']}")

# 网络搜索
result = await search_tool.execute(
    operation='web_search',
    query='人工智能',
    max_results=5
)
for item in result.data['results']:
    print(f"- {item['title']}: {item['snippet']}")

# 按类别搜索
result = await search_tool.execute(
    operation='search_by_category',
    category='technology'
)
for item in result.data['results']:
    print(f"- {item['topic']}: {item['description']}")

# 获取定义
result = await search_tool.execute(
    operation='get_definition',
    topic='langchain',
    category='technology'
)
if result.success:
    print(f"LangChain定义: {result.data['definition']}")

# 相似搜索
result = await search_tool.execute(
    operation='search_similar',
    query='ai',
    threshold=0.3
)
for item in result.data['results']:
    print(f"- {item['topic']} (相似度: {item['similarity']:.2f})")

# 高级搜索
filters = {
    'max_results': 10,
    'categories': ['technology', 'science'],
    'include_web': True,
    'include_knowledge': True
}
result = await search_tool.execute(
    operation='advanced_search',
    query='机器学习',
    filters=filters
)
```

## 智能体 API

### ModernLangChainAgent 类

主要的智能体类，提供基于 LangChain 1.0+ 的对话和工具调用功能。

#### 初始化

```python
from modern_langchain_agent import ModernLangChainAgent

# 创建智能体实例
agent = ModernLangChainAgent(model_provider="zhipu")
```

**参数：**
- `model_provider` (str): 模型提供商，支持：
  - `"zhipu"` - 智谱AI GLM-4.6 (默认)
  - `"anthropic"` - Anthropic Claude
  - `"openai"` - OpenAI GPT

#### 方法

##### run(user_input: str) -> str

运行智能体，处理用户输入并返回回复。

**参数：**
- `user_input` (str): 用户输入的文本

**返回：**
- `str`: 智能体的回复

**示例：**
```python
agent = ModernLangChainAgent("zhipu")
response = agent.run("现在几点了？")
print(response)  # 输出当前时间信息
```

##### interactive_chat()

启动交互式聊天模式，支持持续对话。

**示例：**
```python
agent = ModernLangChainAgent("zhipu")
agent.interactive_chat()
```

## 天气服务 API

### EnhancedCaiyunWeatherService 类 🌟

**增强版彩云天气服务**，支持全国3,142+地区覆盖、智能地名匹配和高性能缓存。

#### 初始化

```python
from enhanced_weather_service import EnhancedCaiyunWeatherService

# 自动初始化所有组件
service = EnhancedCaiyunWeatherService()

# 手动指定组件
from enhanced_place_matcher import EnhancedPlaceMatcher
from weather_cache import WeatherCache
matcher = EnhancedPlaceMatcher()
cache = WeatherCache()
service = EnhancedCaiyunWeatherService(matcher=matcher, cache=cache)
```

#### 方法

##### get_weather(place_name: str) -> tuple[WeatherData, str]

获取任意地区的天气信息，支持智能地名匹配。

**参数：**
- `place_name` (str): 地区名称，支持多种格式：
  - 精确地名: "北京市"、"余杭区"、"景德镇"
  - 别称简称: "京"、"沪"、"羊城"
  - 模糊匹配: "杭州"、"余杭"
  - 层级匹配: "浙江省杭州市"

**返回：**
- `tuple[WeatherData, str]`:
  - `WeatherData`: 天气数据对象
  - `str`: 数据来源和匹配信息

**支持的地区类型：**
- **省级**: 19个省级行政区 (100%覆盖)
- **地级**: 290+个地级市 (主要城市全覆盖)
- **县级**: 2,800+个县区 (95%+覆盖)
- **乡镇级**: 部分重要乡镇

**匹配策略优先级：**
1. 精确匹配
2. 别名匹配 (105+个常见别名)
3. 层级匹配
4. 模糊匹配
5. 包含匹配

**示例：**
```python
service = EnhancedCaiyunWeatherService()

# 基础城市查询
weather_data, source = service.get_weather("北京")
print(f"温度: {weather_data.temperature}°C")

# 智能别名匹配
weather_data, source = service.get_weather("京")  # 自动匹配到北京市

# 县级地区查询
weather_data, source = service.get_weather("余杭区")
print(f"余杭区天气: {weather_data.condition}")

# 地级市查询
weather_data, source = service.get_weather("景德镇")
print(f"景德镇天气: {weather_data.temperature}°C")

# 模糊匹配
weather_data, source = service.get_weather("杭州")  # 可能匹配杭州市或相关地区
```

##### get_weather_batch(place_names: list[str]) -> list[tuple[WeatherData, str]]

批量获取多个地区的天气信息。

**参数：**
- `place_names` (list[str]): 地区名称列表

**返回：**
- `list[tuple[WeatherData, str]]`: 天气数据列表

**示例：**
```python
service = EnhancedCaiyunWeatherService()
cities = ["北京", "上海", "广州", "深圳", "杭州"]
weather_results = service.get_weather_batch(cities)

for city, (weather_data, source) in zip(cities, weather_results):
    print(f"{city}: {weather_data.temperature}°C, {weather_data.condition}")
```

#### 性能特性

- **匹配成功率**: 82.1%
- **平均查询时间**: 1.19ms
- **缓存加速**: 2000倍性能提升（缓存命中时）
- **坐标覆盖**: 100%（所有地区都有经纬度）

### CaiyunWeatherService 类

彩云天气 API 服务类，提供实时天气数据获取功能。

#### 初始化

```python
from weather_service import CaiyunWeatherService

# 自动从环境变量读取 API 密钥
service = CaiyunWeatherService()

# 手动指定 API 密钥
service = CaiyunWeatherService(api_key="your-api-key")
```

#### 方法

##### get_weather(city: str) -> tuple[WeatherData, str]

获取指定城市的天气信息。

**参数：**
- `city` (str): 城市名称，支持中文城市名

**返回：**
- `tuple[WeatherData, str]`:
  - `WeatherData`: 天气数据对象
  - `str`: 数据来源说明

**WeatherData 对象属性：**
- `temperature` (float): 温度（摄氏度）
- `apparent_temperature` (float): 体感温度（摄氏度）
- `humidity` (int): 湿度（百分比）
- `pressure` (float): 气压（hPa）
- `wind_speed` (float): 风速（km/h）
- `wind_direction` (float): 风向（度）
- `condition` (str): 天气状况描述

**示例：**
```python
service = CaiyunWeatherService()
weather_data, source = service.get_weather("北京")

print(f"温度: {weather_data.temperature}°C")
print(f"天气: {weather_data.condition}")
print(f"数据来源: {source}")
```

##### get_coordinates(city: str) -> tuple[float, float] | None

获取城市的地理坐标。

**参数：**
- `city` (str): 城市名称

**返回：**
- `tuple[float, float] | None`: (经度, 纬度) 或 None（如果城市不存在）

**支持的城市：**
北京、上海、广州、深圳、杭州、成都、西安、武汉、南京、重庆、天津、苏州、青岛、大连、厦门

### 便捷函数

##### get_weather_info(city: str) -> str

获取格式化的天气信息字符串。

**参数：**
- `city` (str): 城市名称

**返回：**
- `str`: 格式化的天气信息

**示例：**
```python
from weather_service import get_weather_info

weather_info = get_weather_info("上海")
print(weather_info)
# 输出: 上海天气: 多云，温度 25.0°C (体感 26.0°C)，湿度 65%，风速 8.5km/h
# 数据来源: 实时数据（彩云天气 API）
```

## 工具函数 API

### LangChain 工具装饰器

项目中使用 `@tool` 装饰器定义了以下工具函数：

#### get_current_time() -> str

获取当前时间和日期。

**返回：**
- `str`: 格式化的时间信息

**示例：**
```python
from modern_langchain_agent import get_current_time

time_info = get_current_time.invoke({})
print(time_info)
# 输出: 当前时间: 2025-11-03 18:52:53 (星期日)
```

#### calculate(expression: str) -> str

计算数学表达式。

**参数：**
- `expression` (str): 要计算的数学表达式

**返回：**
- `str`: 计算结果

**支持的操作：**
- 基本运算: `+`, `-`, `*`, `/`
- 括号: `()`
- 幂运算: `**`

**示例：**
```python
from modern_langchain_agent import calculate

result = calculate.invoke({"expression": "123 * 456 + 789"})
print(result)
# 输出: 计算结果: 123 * 456 + 789 = 56088
```

#### get_weather(city: str) -> str

查询城市天气信息（LangChain 工具版本）。

**参数：**
- `city` (str): 城市名称

**返回：**
- `str`: 天气信息字符串

**示例：**
```python
from modern_langchain_agent import get_weather

weather = get_weather.invoke({"city": "北京"})
print(weather)
# 输出: 北京天气: 晴天，温度 15.2°C (体感 13.8°C)，湿度 45%，风速 12.3km/h
```

#### search_information(query: str) -> str

搜索信息（模拟搜索功能）。

**参数：**
- `query` (str): 搜索查询词

**返回：**
- `str`: 搜索结果

**知识库包含：**
- LangChain 框架介绍
- Python 编程语言
- 人工智能相关概念
- 机器学习基础
- 大语言模型介绍

## 环境配置

### 必需的环境变量

```bash
# 智谱AI API 密钥（默认使用）
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# 彩云天气 API 密钥（用于真实天气数据）
CAIYUN_API_KEY=your-caiyun-api-key-here
```

### 可选的环境变量

```bash
# Anthropic Claude API 密钥
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OpenAI GPT API 密钥
OPENAI_API_KEY=your-openai-api-key-here

# LangSmith 调试和追踪（可选）
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=langchain-agent-demo
LANGSMITH_TRACING=true
```

### 环境变量加载

项目使用 `python-dotenv` 自动加载 `.env` 文件中的环境变量：

```python
from dotenv import load_dotenv
load_dotenv()
```

## 错误处理

### 智能体错误

常见错误类型和处理方法：

```python
try:
    agent = ModernLangChainAgent("zhipu")
    response = agent.run("用户输入")
except ValueError as e:
    if "API 密钥" in str(e):
        print("请检查 API 密钥配置")
    else:
        print(f"配置错误: {e}")
except Exception as e:
    print(f"智能体运行错误: {e}")
```

### 天气服务错误

天气服务具有完善的错误处理机制：

1. **API 密钥未配置**: 自动使用模拟数据
2. **网络连接失败**: 自动降级到模拟数据
3. **城市不存在**: 返回模拟数据并说明原因
4. **API 响应异常**: 解析失败时使用备用数据

#### 错误码系统

WeatherTool 集成了完整的错误码系统，提供详细的请求状态反馈：

```python
from tools.weather_tool import WeatherTool

weather_tool = WeatherTool()

# 执行带错误码的查询
result = await weather_tool.execute(
    operation='hourly_forecast',
    location='北京',
    hours=24
)

# 检查结果和错误码
if result.success:
    print("✅ 请求成功")
else:
    print(f"❌ 请求失败: {result.error}")

# 获取详细错误信息
if result.metadata:
    error_code = result.metadata.get("error_code")
    status_message = result.metadata.get("status_message")
    description = result.metadata.get("description")

    print(f"错误码: {error_code}")
    print(f"状态: {status_message}")
    print(f"描述: {description}")

    # 根据错误码采取不同策略
    if error_code == 6:
        print("💡 建议: 检查输入参数")
    elif error_code == 7:
        print("💡 建议: 检查日期格式")
    elif error_code == 9:
        print("💡 建议: 使用有效日期范围")
```

#### 错误码类型

| 错误码 | 类型 | 描述 | 处理建议 |
|--------|------|------|----------|
| 0, 1 | 成功 | API成功或缓存命中 | 正常使用数据 |
| 2, 4 | API问题 | API错误或网络超时 | 使用模拟数据 |
| 3, 5, 9 | 数据问题 | 坐标未找到、解析失败、超出范围 | 使用模拟数据 |
| 6, 7, 8 | 参数问题 | 参数错误、日期错误、时间段错误 | 检查输入参数 |

```python
from weather_service import get_weather_info

# 即使 API 不可用也能正常工作
weather_info = get_weather_info("不存在的城市")
# 输出包含友好的错误提示和模拟数据
```

**详细文档**: 参见 [天气服务错误码系统指南](WEATHER_ERROR_CODES_GUIDE.md)

## 使用示例

### 完整的智能体对话示例

```python
import os
from dotenv import load_dotenv
from modern_langchain_agent import ModernLangChainAgent

# 加载环境变量
load_dotenv()

def main():
    # 创建智能体
    agent = ModernLangChainAgent(model_provider="zhipu")

    # 对话示例
    conversations = [
        "现在几点了？",
        "帮我计算 123 * 456",
        "北京天气怎么样？",
        "介绍一下 LangChain",
        "上海和北京哪个更暖和？"
    ]

    for user_input in conversations:
        print(f"用户: {user_input}")
        response = agent.run(user_input)
        print(f"智能体: {response}\n")

if __name__ == "__main__":
    main()
```

### 天气服务独立使用示例

```python
from weather_service import CaiyunWeatherService, get_weather_info

def demo_weather_service():
    # 使用便捷函数
    print("=== 便捷函数示例 ===")
    cities = ["北京", "上海", "广州"]

    for city in cities:
        weather_info = get_weather_info(city)
        print(weather_info)

    # 使用服务类
    print("\n=== 服务类示例 ===")
    service = CaiyunWeatherService()

    weather_data, source = service.get_weather("深圳")
    print(f"深圳天气详情:")
    print(f"  温度: {weather_data.temperature}°C")
    print(f"  体感: {weather_data.apparent_temperature}°C")
    print(f"  湿度: {weather_data.humidity}%")
    print(f"  风速: {weather_data.wind_speed} km/h")
    print(f"  天气: {weather_data.condition}")
    print(f"  来源: {source}")

if __name__ == "__main__":
    demo_weather_service()
```

### 集成测试示例

```python
import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from weather_service import get_weather_info
from modern_langchain_agent import get_weather

def test_integration():
    """测试智能体与天气服务的集成"""

    # 测试直接天气服务调用
    print("1. 直接天气服务调用:")
    direct_result = get_weather_info("北京")
    print(f"   结果: {direct_result}")

    # 测试通过 LangChain 工具调用
    print("\n2. 通过 LangChain 工具调用:")
    tool_result = get_weather.invoke({"city": "北京"})
    print(f"   结果: {tool_result}")

    # 验证结果一致性
    print("\n3. 结果一致性验证:")
    if "北京" in direct_result and "北京" in tool_result:
        print("   ✅ 两种调用方式都返回了北京的天气信息")
    else:
        print("   ❌ 结果不一致")

if __name__ == "__main__":
    load_dotenv()
    test_integration()
```

## API 限制和注意事项

### 智谱AI API
- 需要有效的 API Token
- 有调用频率限制
- 支持中文对话优化

### 彩云天气 API
- 免费版本有调用次数限制
- 支持的天气数据类型：实时天气
- 建议在生产环境中配置付费计划

### 最佳实践
1. **错误处理**: 始终使用 try-catch 包装 API 调用
2. **环境变量**: 不要在代码中硬编码 API 密钥
3. **降级策略**: 天气服务内置了模拟数据降级机制
4. **性能考虑**: 避免频繁的 API 调用，考虑缓存机制

## 地名匹配 API

### EnhancedPlaceMatcher 类

智能地名匹配系统，支持多种匹配策略和105+个常见别名。

#### 初始化

```python
from enhanced_place_matcher import EnhancedPlaceMatcher

matcher = EnhancedPlaceMatcher()
matcher.connect()
```

#### 方法

##### match_place(place_name: str) -> dict

匹配地名并返回详细信息。

**参数：**
- `place_name` (str): 要匹配的地名

**返回：**
- `dict`: 匹配结果，包含以下字段：
  - `code`: 地区代码
  - `name`: 地区名称
  - `level`: 行政级别 (1=省级, 2=地级, 3=县级)
  - `level_name`: 级别名称
  - `longitude`: 经度
  - `latitude`: 纬度
  - `province`: 省份
  - `city`: 城市
  - `district`: 区县

**示例：**
```python
matcher = EnhancedPlaceMatcher()
matcher.connect()

# 精确匹配
result = matcher.match_place("北京市")
print(f"匹配结果: {result['name']} ({result['level_name']})")

# 别名匹配
result = matcher.match_place("京")  # 匹配到北京市
print(f"别名匹配: {result['name']}")

# 县级匹配
result = matcher.match_place("余杭区")
print(f"县级匹配: {result['province']} - {result['city']} - {result['district']}")
```

#### 匹配策略

1. **精确匹配**: 完全匹配地名
2. **别名匹配**: 使用预定义别名映射
3. **模糊匹配**: 使用相似度算法
4. **层级匹配**: 检查省-市-县层级关系
5. **包含匹配**: 检查地名包含关系

#### 性能指标

- **匹配成功率**: 82.1%
- **平均响应时间**: 1.19ms
- **支持别名数**: 105+个
- **覆盖地区数**: 3,142+个

## 缓存系统 API

### WeatherCache 类

多级缓存系统，提供内存和文件持久化缓存。

#### 初始化

```python
from weather_cache import WeatherCache

# 使用默认配置
cache = WeatherCache()

# 自定义配置
cache = WeatherCache(
    memory_size=1000,      # 内存缓存大小
    file_size=5000,        # 文件缓存大小
    ttl=3600              # 生存时间（秒）
)
```

#### 方法

##### get(key: str) -> any

从缓存中获取数据。

##### set(key: str, value: any, ttl: int = None) -> None

向缓存中存储数据。

##### clear() -> None

清空所有缓存。

#### 示例

```python
cache = WeatherCache()

# 存储天气数据
cache.set("北京天气", weather_data, ttl=1800)  # 30分钟过期
cached_data = cache.get("北京天气")

# 批量操作
cache.set("上海天气", shanghai_weather)
cache.set("广州天气", guangzhou_weather)

# 清空缓存
cache.clear()
```

## 数据库 API

### CityCoordinateDB 类

城市坐标数据库查询类，支持中国行政区划坐标查询。

#### 初始化

```python
from city_coordinate_db import CityCoordinateDB

db = CityCoordinateDB("src/data/admin_divisions.db")
```

#### 方法

##### get_coordinates(place_name: str) -> tuple[float, float]

获取地区的经纬度坐标。

**参数：**
- `place_name` (str): 地区名称

**返回：**
- `tuple[float, float]`: (经度, 纬度)

**示例：**
```python
db = CityCoordinateDB()

# 获取北京坐标
lng, lat = db.get_coordinates("北京")
print(f"北京坐标: ({lng}, {lat})")

# 获取余杭区坐标
lng, lat = db.get_coordinates("余杭区")
print(f"余杭区坐标: ({lng}, {lat})")
```

##### search_places(keyword: str) -> list[dict]

搜索包含关键词的地区。

**参数：**
- `keyword` (str): 搜索关键词

**返回：**
- `list[dict]`: 匹配的地区列表

## 工具函数 API

### 快速开始函数

```python
# 快速天气查询（使用增强服务）
from enhanced_weather_service import get_weather_info_quick

weather_data, source = get_weather_info_quick("北京")
print(f"天气: {weather_data.condition}, 温度: {weather_data.temperature}°C")

# 初始化全国数据库
from national_region_database import main
main()  # 一键初始化全国地区数据库

# 验证系统状态
from verify_national_integration import main
main()  # 验证所有组件集成状态
```

## 同步工具函数 API

### LangChain 同步工具

**推荐使用** - 同步版本的LangChain工具，稳定可靠，无异步问题。

#### 导入和初始化

```python
from tools.langchain_weather_tools_sync import (
    query_current_weather,
    query_weather_by_date,
    query_hourly_forecast,
    query_fishing_recommendation,
    get_weather_tools_sync,
    create_weather_tool_system_prompt
)

# 直接使用工具（推荐）
result = query_current_weather.invoke({'place': '北京'})
print(result)

# 或获取工具列表集成到智能体
weather_tools = get_weather_tools_sync()
system_prompt = create_weather_tool_system_prompt()
```

#### 主要工具函数

##### query_current_weather(place: str) -> str

查询当前天气信息（同步版本）。

**参数：**
- `place` (str): 地点名称

**返回：**
- `str`: 格式化的天气信息

**示例：**
```python
from tools.langchain_weather_tools_sync import query_current_weather

# 稳定的同步调用，无事件循环问题
result = query_current_weather.invoke({'place': '杭州'})
print(result)
# 输出: 📍 杭州当前天气:
# 🌡️ 温度: 22.0°C
# 🌤️ 天气: 多云
# 💧 湿度: 65%
# 🌬️ 风速: 8.5km/h
```

##### query_fishing_recommendation(location: str, date: str) -> str

智能钓鱼推荐（同步版本）。

**参数：**
- `location` (str): 地点名称
- `date` (str): 日期，支持多种格式：
  - 标准格式: "2024-12-25"
  - 相对日期: "tomorrow", "yesterday", "today"
  - 中文相对日期: "明天", "昨天", "今天", "后天"
  - 数字+时间: "2天后", "3天前"

**返回：**
- `str`: 钓鱼推荐分析结果

**示例：**
```python
from tools.langchain_weather_tools_sync import query_fishing_recommendation

# 支持多种日期格式
queries = [
    {'location': '富阳区', 'date': '后天'},     # ✅ 相对日期
    {'location': '余杭区', 'date': 'tomorrow'}, # ✅ 英文相对日期
    {'location': '北京', 'date': '2024-12-25'}, # ✅ 标准日期格式
]

for query in queries:
    result = query_fishing_recommendation.invoke(query)
    print(result)
```

##### query_weather_by_date(place: str, date: str) -> str

指定日期天气查询（同步版本）。

**参数：**
- `place` (str): 地点名称
- `date` (str): 日期，支持同上多种格式

**返回：**
- `str`: 指定日期的天气信息

**示例：**
```python
from tools.langchain_weather_tools_sync import query_weather_by_date

# 历史天气查询
result = query_weather_by_date.invoke({
    'place': '上海',
    'date': '2024-11-01'
})

# 未来天气查询
result = query_weather_by_date.invoke({
    'place': '广州',
    'date': '后天'
})
```

##### query_hourly_forecast(place: str, hours: int = 24) -> str

小时级天气预报（同步版本）。

**参数：**
- `place` (str): 地点名称
- `hours` (int): 预报小时数，默认24小时

**返回：**
- `str`: 小时级天气预报信息

**示例：**
```python
from tools.langchain_weather_tools_sync import query_hourly_forecast

# 查询未来12小时预报
result = query_hourly_forecast.invoke({
    'place': '深圳',
    'hours': 12
})

print(result)
# 输出详细的小时级预报数据，包括温度、天气、风速等
```

#### 工具集合

##### get_weather_tools_sync() -> List[BaseTool]

获取所有同步天气工具的列表。

**返回：**
- `List[BaseTool]`: LangChain工具对象列表

**示例：**
```python
from tools.langchain_weather_tools_sync import get_weather_tools_sync

# 获取所有同步工具
tools = get_weather_tools_sync()

# 集成到智能体
from langchain.agents import create_agent

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=tools,
    system_prompt="你是一个天气助手，可以帮助用户查询天气信息。"
)
```

### 同步天气工具

#### WeatherTool 同步版本

```python
from tools.weather_tool_sync import WeatherTool

# 创建同步天气工具
weather_tool = WeatherTool()

# 执行操作（同步调用）
result = weather_tool.execute(
    operation='current_weather',
    location='北京'
)

if result.success:
    data = result.data
    print(f"温度: {data.get('temperature', 'N/A')}°C")
else:
    print(f"查询失败: {result.error}")
```

**支持的操作：**
- `current_weather` - 当前天气
- `weather_by_date` - 指定日期天气
- `hourly_forecast` - 小时级预报
- `batch_weather` - 批量查询

### 同步钓鱼分析工具

#### FishingAnalyzer 同步版本

```python
from tools.fishing_analyzer_sync import find_best_fishing_time, parse_date_input

# 日期解析（增强版）
date_input = "后天"
parsed_date = parse_date_input(date_input)
print(f"解析结果: {parsed_date.strftime('%Y-%m-%d')}")

# 钓鱼时间推荐
result = find_best_fishing_time(
    location='富阳区',
    date='后天'  # 支持所有日期格式
)

print(result)  # 输出JSON格式的详细分析结果
```

#### Enhanced Fishing Scorer

```python
from tools.enhanced_fishing_scorer import EnhancedFishingScorer

# 创建增强评分器
scorer = EnhancedFishingScorer()

# 分析钓鱼条件
conditions = {
    'datetime': '2024-11-06T14:00:00',
    'temperature': 22.0,
    'condition': '阴',
    'wind_speed': 8.0,
    'humidity': 75.0,
    'pressure': 1008.0
}

from datetime import datetime
date = datetime(2024, 11, 6, 14, 0)
score = scorer.calculate_comprehensive_score(conditions, historical_data, date)

print(f"综合评分: {score.overall:.1f}/100")
print(f"7因子评分: 温度{score.temperature:.1f}, 天气{score.weather:.1f}, 风力{score.wind:.1f}, 气压{score.pressure:.1f}, 湿度{score.humidity:.1f}, 季节{score.seasonal:.1f}, 月相{score.lunar:.1f}")
```

### 同步API客户端

#### CaiyunApiClient 同步版本

```python
from services.weather.clients.caiyun_api_client_sync import CaiyunApiClient

# 创建同步API客户端
client = CaiyunApiClient(api_key="your-api-key")

# 同步调用，无需await
result = client.get_realtime_weather(116.4074, 39.9042)

if result['success']:
    print(f"温度: {result['result']['temperature']}°C")
else:
    print(f"错误: {result['error']}")
```

**优势：**
- 使用 `requests` 库替代 `aiohttp`
- 内置重试机制和错误处理
- 线程安全的会话管理
- 无事件循环问题

---

**更新时间**: 2025-11-05
**版本**: 2.1.0-sync-version
**维护者**: LangChain 学习项目