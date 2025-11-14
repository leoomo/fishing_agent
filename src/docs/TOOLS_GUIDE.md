# 新工具模块使用指南

本文档详细介绍如何使用项目中的新工具模块，包括架构设计、使用方法和最佳实践。

## 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [详细使用指南](#详细使用指南)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 概述

新工具模块是项目重构的核心成果，实现了工具的模块化、独立化和标准化设计。

### 主要特性

- **🏗️ 模块化架构**: 每个工具都是独立的模块
- **🔌 统一接口**: 所有工具都实现 `ITool` 接口
- **⚡ 异步支持**: 支持高性能异步调用
- **⚙️ 配置化**: 支持灵活的配置管理
- **📊 注册系统**: 提供工具注册和发现机制
- **🧪 完整测试**: 每个工具都有完整的测试覆盖

### 工具列表

| 工具名称 | 功能描述 | 主要特性 |
|---------|---------|---------|
| **TimeTool** | 时间工具 | 时间查询、计算、格式化、时区转换 |
| **MathTool** | 数学工具 | 基本运算、高级函数、统计计算 |
| **WeatherTool** | 天气工具 | 天气查询、预报、批量查询 |
| **SearchTool** | 搜索工具 | 知识库检索、网络搜索、相似匹配 |

## 架构设计

### 核心接口

#### ITool 接口

所有工具都必须实现的核心接口：

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
```

### 基类体系

#### BaseTool 基础类

提供工具的通用实现：

```python
from core.base_tool import BaseTool, ConfigurableTool

class MyTool(ConfigurableTool):
    """自定义工具示例"""

    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        # 初始化工具特定配置
        self._my_config = self.get_config_value("my_setting", "default_value")

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_tool",
            description="我的自定义工具",
            version="1.0.0",
            author="author",
            tags=["custom", "example"],
            dependencies=[]
        )

    def validate_input(self, **kwargs) -> bool:
        # 验证必需参数
        return "required_param" in kwargs

    async def _execute(self, **kwargs) -> ToolResult:
        # 实现具体功能
        try:
            # 业务逻辑
            result = self._process_data(kwargs)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

## 快速开始

### 1. 基本使用

```python
import asyncio
from tools import TimeTool, MathTool, WeatherTool, SearchTool

async def basic_usage():
    # 创建工具实例
    time_tool = TimeTool()
    math_tool = MathTool()
    weather_tool = WeatherTool()
    search_tool = SearchTool()

    # 使用时间工具
    time_result = await time_tool.execute(operation='current_time')
    if time_result.success:
        print(f"当前时间: {time_result.data['formatted']}")

    # 使用数学工具
    math_result = await math_tool.execute(operation='add', a=10, b=5)
    if math_result.success:
        print(f"计算结果: {math_result.data['formatted']}")

    # 使用天气工具
    weather_result = await weather_tool.execute(
        operation='current_weather',
        location='北京'
    )
    if weather_result.success:
        data = weather_result.data
        print(f"北京天气: {data['condition']} {data['temperature']}°C")

    # 使用搜索工具
    search_result = await search_tool.execute(
        operation='knowledge_search',
        query='python'
    )
    if search_result.success:
        print(f"找到 {search_result.data['total_results']} 个结果")

# 运行示例
asyncio.run(basic_usage())
```

### 2. 批量操作

```python
async def batch_operations():
    # 时间工具批量操作
    time_tool = TimeTool()

    operations = [
        {"operation": "add_time", "base_time": "2024-01-01", "days": 1},
        {"operation": "add_time", "base_time": "2024-01-01", "months": 1},
        {"operation": "format_time", "time_input": "2024-01-01T10:30:45"}
    ]

    for op in operations:
        result = await time_tool.execute(**op)
        if result.success:
            print(f"操作成功: {result.data['formatted']}")

    # 天气工具批量查询
    weather_tool = WeatherTool()
    cities = ["北京", "上海", "广州", "深圳"]

    result = await weather_tool.execute(
        operation='batch_weather',
        locations=cities
    )

    if result.success:
        for item in result.data['results']:
            if item['success']:
                weather = item['data']
                print(f"{item['location']}: {weather['condition']} {weather['temperature']}°C")

asyncio.run(batch_operations())
```

### 3. 配置化使用

```python
async def configured_usage():
    # 自定义配置
    time_config = {
        "default_timezone": "America/New_York",
        "precision": 15
    }
    time_tool = TimeTool(time_config)

    math_config = {
        "precision": 20,
        "enable_cache": True
    }
    math_tool = MathTool(math_config)

    weather_config = {
        "api_key": "your-api-key",
        "timeout": 30,
        "cache_ttl": 7200
    }
    weather_tool = WeatherTool(weather_config)

    # 使用配置后的工具
    result = await time_tool.execute(operation='current_time')
    print(f"纽约时间: {result.data['formatted']}")

asyncio.run(configured_usage())
```

## 详细使用指南

### TimeTool 时间工具

#### 支持的操作

| 操作 | 参数 | 说明 |
|------|------|------|
| `current_time` | `timezone_name` (可选) | 获取当前时间 |
| `add_time` | `base_time`, `years`, `months`, `days`, `hours`, `minutes`, `seconds` | 时间加法 |
| `subtract_time` | 同上 | 时间减法 |
| `format_time` | `time_input`, `format_type`, `timezone_name` (可选) | 时间格式化 |
| `convert_timezone` | `time_input`, `from_tz`, `to_tz` | 时区转换 |

#### 详细示例

```python
async def time_tool_examples():
    time_tool = TimeTool()

    # 1. 获取不同时区的当前时间
    timezones = ["Asia/Shanghai", "America/New_York", "Europe/London"]
    for tz in timezones:
        result = await time_tool.execute(operation='current_time', timezone_name=tz)
        if result.success:
            data = result.data
            print(f"{tz}: {data['formatted']}")

    # 2. 复杂时间计算
    result = await time_tool.execute(
        operation='add_time',
        base_time='2024-01-01T10:00:00',
        years=1,
        months=2,
        days=15,
        hours=3
    )
    print(f"复杂计算: {result.data['formatted']}")

    # 3. 多种格式化
    formats = ["default", "date", "time", "iso", "us", "full", "compact"]
    time_input = "2024-01-01T10:30:45"
    for fmt in formats:
        result = await time_tool.execute(
            operation='format_time',
            time_input=time_input,
            format_type=fmt
        )
        print(f"{fmt}: {result.data['formatted']}")

    # 4. 时区转换
    result = await time_tool.execute(
        operation='convert_timezone',
        time_input='2024-01-01T10:00:00',
        from_tz='Asia/Shanghai',
        to_tz='America/New_York'
    )
    print(f"时区转换: {result.data['formatted']}")

asyncio.run(time_tool_examples())
```

### MathTool 数学工具

#### 支持的操作

| 操作 | 参数 | 说明 |
|------|------|------|
| `add`, `subtract`, `multiply`, `divide` | `a`, `b` | 基本运算 |
| `power` | `base`, `exponent` | 幂运算 |
| `sqrt` | `number` | 平方根 |
| `sin`, `cos`, `tan` | `angle`, `degrees` (默认True) | 三角函数 |
| `log` | `number`, `base` (默认10) | 对数函数 |
| `factorial` | `n` | 阶乘 |
| `average`, `median`, `mode` | `numbers` (列表) | 统计函数 |
| `std_dev` | `numbers` (列表) | 标准差 |
| `random` | `min_val`, `max_val`, `integer` (默认True) | 随机数 |
| `round` | `number`, `decimals` (默认0) | 四舍五入 |

#### 详细示例

```python
async def math_tool_examples():
    math_tool = MathTool()

    # 1. 基本运算组合
    operations = [
        ("add", {"a": 10, "b": 5}),
        ("multiply", {"a": 12, "b": 8}),
        ("power", {"base": 2, "exponent": 10}),
        ("sqrt", {"number": 144})
    ]

    for op, params in operations:
        result = await math_tool.execute(operation=op, **params)
        print(f"{op}: {result.data['formatted']}")

    # 2. 三角函数计算
    angles = [0, 30, 45, 60, 90]
    for angle in angles:
        result = await math_tool.execute(operation='sin', angle=angle, degrees=True)
        print(f"sin({angle}°) = {result.data['result']}")

    # 3. 统计计算
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    stats = ["average", "median", "std_dev"]
    for stat in stats:
        result = await math_tool.execute(operation=stat, numbers=numbers)
        if stat == "average":
            print(f"平均值: {result.data['result']}")
        elif stat == "median":
            print(f"中位数: {result.data['result']}")
        else:
            print(f"标准差: {result.data['result']}")

    # 4. 随机数和分布
    import random
    random.seed(42)  # 固定随机种子

    for i in range(5):
        result = await math_tool.execute(
            operation='random',
            min_val=1,
            max_val=100,
            integer=True
        )
        print(f"随机数 {i+1}: {result.data['result']}")

    # 5. 复杂数学表达式
    # 计算 (a + b) * c - d
    a, b, c, d = 5, 3, 4, 2

    # (a + b) * c
    step1 = await math_tool.execute(operation='add', a=a, b=b)
    if step1.success:
        sum_ab = step1.data['result']
        step2 = await math_tool.execute(operation='multiply', a=sum_ab, b=c)
        if step2.success:
            product = step2.data['result']
            # product - d
            step3 = await math_tool.execute(operation='subtract', a=product, b=d)
            if step3.success:
                print(f"({a} + {b}) * {c} - {d} = {step3.data['result']}")

asyncio.run(math_tool_examples())
```

### WeatherTool 天气工具

#### 支持的操作

| 操作 | 参数 | 说明 |
|------|------|------|
| `current_weather` | `location` | 获取当前天气 |
| `get_coordinates` | `location` | 获取坐标 |
| `batch_weather` | `locations` (列表) | 批量查询 |
| `search_locations` | `query`, `limit` | 位置搜索 |
| `weather_forecast` | `location`, `days` | 天气预报 |
| `weather_by_date` | `location`, `date` | 指定日期天气查询 |
| `weather_by_datetime` | `location`, `datetime_str` | 时间段天气查询 |
| `hourly_forecast` | `location`, `hours` | 小时级天气预报 |

#### 详细示例

```python
async def weather_tool_examples():
    weather_tool = WeatherTool()

    # 1. 基本天气查询
    cities = ["北京", "上海", "广州", "深圳", "杭州"]
    for city in cities:
        result = await weather_tool.execute(
            operation='current_weather',
            location=city
        )
        if result.success:
            data = result.data
            print(f"{city}: {data['condition']} {data['temperature']}°C "
                  f"(湿度{data['humidity']}%)")

    # 2. 批量天气查询
    batch_result = await weather_tool.execute(
        operation='batch_weather',
        locations=["北京", "上海", "广州"]
    )
    if batch_result.success:
        for item in batch_result.data['results']:
            if item['success']:
                weather = item['data']
                print(f"批量 - {item['location']}: {weather['condition']} "
                      f"{weather['temperature']}°C")

    # 3. 位置搜索
    search_terms = ["北", "上", "广", "湖"]
    for term in search_terms:
        result = await weather_tool.execute(
            operation='search_locations',
            query=term,
            limit=3
        )
        if result.success:
            print(f"搜索 '{term}': 找到 {result.data['count']} 个结果")
            for match in result.data['matches'][:2]:
                print(f"  - {match['name']}")

    # 4. 天气预报
    forecast_result = await weather_tool.execute(
        operation='weather_forecast',
        location='北京',
        days=5
    )
    if forecast_result.success:
        current = forecast_result.data['current']
        print(f"北京当前天气: {current['condition']} {current['temperature']}°C")
        print("未来5天预报:")
        for day in forecast_result.data['forecast']:
            print(f"  第{day['day']}天: {day['condition']} {day['temperature']}°C")

    # 5. 错误码系统使用
    result = await weather_tool.execute(
        operation='weather_by_date',
        location='北京',
        date='2024-12-25'
    )

    if result.success:
        print("✅ 请求成功")
    else:
        print(f"❌ 请求失败: {result.error}")

        # 检查详细的错误码信息
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

asyncio.run(weather_tool_examples())
```

#### 错误码系统

WeatherTool 集成了完整的错误码系统，提供详细的请求状态反馈：

##### 错误码类型

| 错误码 | 类型 | 描述 | 处理建议 |
|--------|------|------|----------|
| 0 | 成功 | API调用成功 | 正常使用数据 |
| 1 | 成功 | 缓存命中 | 正常使用数据 |
| 2 | API问题 | API错误 | 使用模拟数据 |
| 3 | 数据问题 | 坐标未找到 | 使用模拟数据 |
| 4 | API问题 | 网络超时 | 使用模拟数据 |
| 5 | 数据问题 | 数据解析失败 | 使用模拟数据 |
| 6 | 参数问题 | 参数错误 | 检查输入参数 |
| 7 | 参数问题 | 日期解析错误 | 检查日期格式 |
| 8 | 参数问题 | 时间段错误 | 检查时间表达式 |
| 9 | 数据问题 | 数据超出范围 | 使用模拟数据 |

##### 错误码使用示例

```python
# 检查请求结果
result = await weather_tool.execute(
    operation='hourly_forecast',
    location='北京',
    hours=24
)

# 基础成功检查
if result.success:
    print("✅ 请求成功")
    forecast_data = result.data
    print(f"预报小时数: {forecast_data['forecast_hours']}")
else:
    print(f"❌ 请求失败: {result.error}")

    # 获取详细错误信息
    if result.metadata:
        error_code = result.metadata.get("error_code")
        description = result.metadata.get("description")

        print(f"错误码: {error_code} - {description}")

        # 根据错误码类别处理
        if error_code in [0, 1]:
            print("这是成功情况")
        elif error_code == 6:
            print("参数错误，请检查输入")
        elif error_code in [2, 4]:
            print("API问题，已使用模拟数据")
        elif error_code == 9:
            print("日期范围问题，已使用模拟数据")
```

**详细文档**: 参见 [天气服务错误码系统指南](WEATHER_ERROR_CODES_GUIDE.md)

### SearchTool 搜索工具

#### 支持的操作

| 操作 | 参数 | 说明 |
|------|------|------|
| `web_search` | `query`, `max_results` | 网络搜索 |
| `knowledge_search` | `query`, `category` | 知识库搜索 |
| `search_by_category` | `category` | 按类别搜索 |
| `get_definition` | `topic`, `category` | 获取定义 |
| `get_features` | `topic`, `category` | 获取特性 |
| `get_applications` | `topic`, `category` | 获取应用 |
| `search_similar` | `query`, `threshold` | 相似搜索 |
| `advanced_search` | `query`, `filters` | 高级搜索 |

#### 详细示例

```python
async def search_tool_examples():
    search_tool = SearchTool()

    # 1. 知识库搜索
    topics = ["python", "javascript", "人工智能", "langchain"]
    for topic in topics:
        result = await search_tool.execute(
            operation='knowledge_search',
            query=topic
        )
        if result.success:
            data = result.data
            print(f"{topic}: 找到 {data['total_results']} 个结果")
            for item in data['results'][:2]:
                print(f"  - {item['topic']}: {item['description'][:50]}...")

    # 2. 按类别浏览
    categories = ["technology", "science", "general"]
    for category in categories:
        result = await search_tool.execute(
            operation='search_by_category',
            category=category
        )
        if result.success:
            print(f"类别 '{category}': {result.data['total_topics']} 个主题")

    # 3. 获取详细信息
    result = await search_tool.execute(
        operation='get_definition',
        topic='python',
        category='technology'
    )
    if result.success:
        print(f"Python定义: {result.data['definition']}")

    result = await search_tool.execute(
        operation='get_features',
        topic='python',
        category='technology'
    )
    if result.success:
        print(f"Python特性: {', '.join(result.data['features'])}")

    # 4. 相似度搜索
    queries = ["ai", "web", "data"]
    for query in queries:
        result = await search_tool.execute(
            operation='search_similar',
            query=query,
            threshold=0.3
        )
        if result.success:
            print(f"'{query}' 相似结果: {result.data['total_results']} 个")
            for item in result.data['results'][:3]:
                print(f"  - {item['topic']} (相似度: {item['similarity']:.2f})")

    # 5. 高级搜索
    filters = {
        'max_results': 8,
        'categories': ['technology'],
        'include_web': True,
        'include_knowledge': True
    }
    result = await search_tool.execute(
        operation='advanced_search',
        query='编程语言',
        filters=filters
    )
    if result.success:
        print(f"高级搜索结果: {result.data['total_results']} 个")
        for item in result.data['results']:
            source_type = item.get('source_type', 'unknown')
            if 'title' in item:
                print(f"  🌐 {item['title']} ({source_type})")
            else:
                print(f"  📚 {item['topic']} ({source_type})")

asyncio.run(search_tool_examples())
```

## 最佳实践

### 1. 错误处理

```python
async def best_practice_error_handling():
    time_tool = TimeTool()

    # 检查输入参数
    if not time_tool.validate_input(operation='current_time'):
        print("输入参数无效")
        return

    # 执行并检查结果
    result = await time_tool.execute(operation='current_time')
    if result.success:
        data = result.data
        print(f"时间: {data['formatted']}")
    else:
        print(f"执行失败: {result.error}")
        # 可以尝试回退方案
        fallback_result = await time_tool.execute(
            operation='current_time',
            timezone_name='UTC'
        )
        if fallback_result.success:
            print(f"回退成功: {fallback_result.data['formatted']}")
```

### 2. 配置管理

```python
# config.py
DEFAULT_TIME_CONFIG = {
    "default_timezone": "Asia/Shanghai",
    "precision": 10,
    "cache_ttl": 3600
}

DEFAULT_MATH_CONFIG = {
    "precision": 15,
    "enable_cache": True,
    "cache_ttl": 1800
}

# 使用配置
from config import DEFAULT_TIME_CONFIG
time_tool = TimeTool(DEFAULT_TIME_CONFIG)
```

### 3. 性能优化

```python
import asyncio
from typing import List

async def performance_optimization():
    tools = [
        TimeTool(),
        MathTool(),
        WeatherTool(),
        SearchTool()
    ]

    # 并发执行多个操作
    tasks = []
    for tool in tools:
        if isinstance(tool, TimeTool):
            tasks.append(tool.execute(operation='current_time'))
        elif isinstance(tool, MathTool):
            tasks.append(tool.execute(operation='add', a=10, b=5))

    # 并发等待所有结果
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"工具 {i} 执行失败: {result}")
        elif result.success:
            print(f"工具 {i} 执行成功")
```

### 4. 工具组合使用

```python
async def tool_combination():
    # 获取当前时间
    time_tool = TimeTool()
    time_result = await time_tool.execute(operation='current_time')

    if time_result.success:
        current_time = time_result.data['formatted']
        print(f"当前时间: {current_time}")

        # 基于时间进行数学计算
        math_tool = MathTool()
        hour = time_result.data['hour']

        # 计算今天的剩余小时数
        remaining_hours = 24 - hour
        calc_result = await math_tool.execute(
            operation='multiply',
            a=remaining_hours,
            b=60
        )

        if calc_result.success:
            remaining_minutes = calc_result.data['result']
            print(f"今天剩余时间: {remaining_hours} 小时 ({remaining_minutes} 分钟)")

            # 搜索关于时间管理的信息
            search_tool = SearchTool()
            search_result = await search_tool.execute(
                operation='knowledge_search',
                query='时间管理'
            )

            if search_result.success:
                print(f"找到 {search_result.data['total_results']} 个时间管理相关结果")
```

## 故障排除

### 常见问题

1. **导入错误**
   ```python
   # 错误
   from tools import time_tool  # ❌

   # 正确
   from tools import TimeTool  # ✅
   time_tool = TimeTool()
   ```

2. **异步调用错误**
   ```python
   # 错误
   result = time_tool.execute(operation='current_time')  # ❌

   # 正确
   result = await time_tool.execute(operation='current_time')  # ✅
   ```

3. **参数验证失败**
   ```python
   # 检查参数是否正确
   if not time_tool.validate_input(operation='current_time'):
       print("参数验证失败")
       return
   ```

4. **配置错误**
   ```python
   # 使用默认配置避免错误
   try:
       time_tool = TimeTool(config)
   except Exception as e:
       print(f"配置错误，使用默认配置: {e}")
       time_tool = TimeTool()
   ```

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)

   tool = TimeTool()
   result = await tool.execute(operation='current_time')
   ```

2. **检查工具元数据**
   ```python
   tool = TimeTool()
   print(f"工具名称: {tool.metadata.name}")
   print(f"工具版本: {tool.metadata.version}")
   print(f"工具描述: {tool.metadata.description}")
   ```

3. **验证工具状态**
   ```python
   # 检查工具是否正确初始化
   if hasattr(tool, '_config'):
       print("工具配置正确")
   else:
       print("工具配置异常")
   ```

---

**更新时间**: 2025-11-03
**版本**: 1.0.0
**维护者**: LangChain 学习项目