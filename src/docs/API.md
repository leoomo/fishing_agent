# 智能钓鱼助手 - API 文档 v2.2.0

本文档描述智能钓鱼助手v2.2.0简化架构后的主要 API 接口和使用方法，基于 **纯LangChain 1.0+ 同步架构**设计。

## 🏗️ 版本说明

### 极简架构版本 (v2.2.0) ⭐ **当前版本**

项目已完全重构为**极简架构**，从75+文件简化到5个核心文件，提供最佳开发体验：

- ✅ **架构极简化**: 从75+文件简化到5个核心文件
- ✅ **纯LangChain 1.0+**: 移除LangGraph包装层，直接使用原生API
- ✅ **同步优先设计**: 全面采用同步架构，消除异步调用问题
- ✅ **零抽象调用**: 统一API客户端，无中间层和服务抽象
- ✅ **伦理数据约束**: 绝不编造虚假数据，诚实报告系统状态
- ✅ **原生@tool装饰器**: 使用最新LangChain 1.0+工具系统

---

## 目录

- [核心 API](#核心-api)
  - [create_optimized_fishing_agent](#create_optimized_fishing_agent)
  - [OptimizedFishingAgent 类](#optimizedfishingagent-类)
- [工具 API](#工具-api)
  - [天气工具 (weather_tools.py)](#天气工具-weather_toolspy)
  - [钓鱼工具 (fishing_tools.py)](#钓鱼工具-fishing_toolspy)
  - [基础工具 (basic_tools.py)](#基础工具-basic_toolspy)
- [工具类 API](#工具类-api)
  - [API 客户端 (api_client.py)](#api-客户端-api_clientpy)
  - [坐标工具 (coordinate_utils.py)](#坐标工具-coordinate_utilspy)
  - [缓存系统 (cache.py)](#缓存系统-cachepy)
- [环境配置](#环境配置)
- [错误处理](#错误处理)
- [使用示例](#使用示例)

## 核心 API (v2.2.0)

### create_optimized_fishing_agent

创建极简智能钓鱼助手，基于**纯LangChain 1.0+ 架构**（无中间层）。

```python
from src.agent import create_optimized_fishing_agent

# 创建智能体（默认使用智谱AI GLM-4）
agent = create_optimized_fishing_agent()

# 指定模型提供商
agent_zhipu = create_optimized_fishing_agent(model_provider="zhipu")
agent_qwen = create_optimized_fishing_agent(model_provider="qwen")
agent_doubao = create_optimized_fishing_agent(model_provider="doubao")

# 带配置的创建（v2.2.0简化选项）
agent = create_optimized_fishing_agent(
    model_provider="zhipu",
    enable_logging=True,
    timeout=60
)
```

**参数：**
- `model_provider` (str): 模型提供商，支持：
  - `"zhipu"` - 智谱AI GLM-4-flash (默认，推荐)
  - `"qwen"` - 阿里巴巴通义千问 Qwen-plus
  - `"doubao"` - 字节跳动豆包
- `enable_logging` (bool, 可选): 启用详细日志记录（默认True）
- `timeout` (int, 可选): 请求超时时间（秒，默认60）

**返回：**
- `OptimizedFishingAgent`: 极简智能钓鱼助手实例

### OptimizedFishingAgent 类

简化的智能钓鱼助手类，提供核心功能。

#### 方法

##### run(user_input: str) -> str

运行智能体，处理用户输入并返回回复。

**参数：**
- `user_input` (str): 用户输入的文本

**返回：**
- `str`: 智能体的回复

**示例：**
```python
from agent import create_optimized_fishing_agent

agent = create_optimized_fishing_agent()
response = agent.run("明天余杭区钓鱼怎么样？")
print(response)
```

##### health_check() -> dict

执行系统健康检查，验证所有组件状态。

**返回：**
- `dict`: 健康检查结果，包含：
  - `status`: 系统状态 ("healthy", "degraded", "unhealthy")
  - `checks`: 各组件详细状态
  - `timestamp`: 检查时间

**示例：**
```python
health = agent.health_check()
print(f"系统状态: {health['status']}")

for check, status in health['checks'].items():
    print(f"  {check}: {status}")
```

##### get_llm_stats() -> dict

获取大语言模型调用统计信息。

**返回：**
- `dict`: 统计信息，包含：
  - `total_model_calls`: 总调用次数
  - `successful_calls`: 成功次数
  - `failed_calls`: 失败次数
  - `success_rate`: 成功率

**示例：**
```python
stats = agent.get_llm_stats()
print(f"模型调用统计: {stats['total_model_calls']}次")
print(f"成功率: {stats['success_rate']:.1f}%")
```

## 工具 API

### 天气工具 (weather_tools.py)

基于彩云天气API的真实天气数据工具。

#### 主要工具函数

##### get_current_weather(location: str) -> str

获取指定位置的当前天气信息。

**参数：**
- `location` (str): 位置名称

**返回：**
- `str`: 格式化的天气信息

**示例：**
```python
from tools.weather_tools import get_current_weather

weather = get_current_weather("北京")
print(weather)
# 输出: 🌤️ 北京当前天气: 晴朗，温度 12.5°C，湿度 65.8%，风速 3.2m/s
```

##### get_weather_forecast(location: str, days: int) -> str

获取天气预报（1-7天）。

**参数：**
- `location` (str): 位置名称
- `days` (int): 预报天数 (1-7)

**返回：**
- `str`: 格式化的天气预报信息

**示例：**
```python
from tools.weather_tools import get_weather_forecast

forecast = get_weather_forecast("杭州", 3)
print(forecast)
# 输出详细的3天天气预报
```

##### get_weather_by_date(location: str, date_str: str) -> str

获取指定日期的天气信息。

**参数：**
- `location` (str): 位置名称
- `date_str` (str): 日期字符串，支持多种格式：
  - 标准格式: "2024-12-25"
  - 相对日期: "tomorrow", "yesterday", "today"
  - 中文相对日期: "明天", "后天", "昨天"

**返回：**
- `str`: 指定日期的天气信息

**示例：**
```python
from tools.weather_tools import get_weather_by_date

# 获取明天天气
tomorrow_weather = get_weather_by_date("上海", "tomorrow")
print(tomorrow_weather)

# 获取指定日期天气
christmas_weather = get_weather_by_date("北京", "2024-12-25")
print(christmas_weather)
```

### 钓鱼工具 (fishing_tools.py)

基于真实天气数据的智能钓鱼推荐工具，严格遵循伦理约束。

#### 主要工具函数

##### query_fishing_recommendation(location: str, date: str) -> str

智能钓鱼推荐，基于7因子评分算法。

**参数：**
- `location` (str): 位置名称
- `date` (str): 日期，支持多种格式（同天气工具）

**返回：**
- `str`: 专业的钓鱼推荐分析结果

**特性：**
- 7因子评分算法（温度、天气、风力、气压、湿度、季节、时间）
- 伦理约束：绝不编造虚假数据
- 数据验证：严格验证天气数据完整性

**示例：**
```python
from tools.fishing_tools import query_fishing_recommendation

# 基本查询
recommendation = query_fishing_recommendation("余杭区", "明天")
print(recommendation)

# 输出示例:
# 🎣 余杭区钓鱼推荐分析 (2024-12-25)
#
# 📊 综合评分: 78/100 (良好)
#
# ⏰ 推荐时段:
#   - 早上 6:00-8:00 ⭐⭐⭐⭐⭐
#   - 傍晚 18:00-20:00 ⭐⭐⭐⭐
#
# 🌤️ 天气条件:
#   - 温度: 12°C ✅ 适宜
#   - 天气: 多云转晴 ✅ 良好
#   - 风力: 2级 ✅ 微风
#   - 湿度: 65% ✅ 适中
```

##### analyze_fishing_conditions(weather_data: dict) -> str

分析钓鱼条件。

**参数：**
- `weather_data` (dict): 天气数据字典

**返回：**
- `str`: 钓鱼条件分析结果

**示例：**
```python
from tools.fishing_tools import analyze_fishing_conditions

weather_data = {
    "temperature": 15.0,
    "condition": "多云",
    "wind_speed": 2.5,
    "humidity": 70.0,
    "pressure": 1013.0
}

analysis = analyze_fishing_conditions(weather_data)
print(analysis)
```

##### calculate_fish_activity(weather_data: dict) -> str

计算鱼类活跃度。

**参数：**
- `weather_data` (dict): 天气数据字典

**返回：**
- `str`: 鱼类活跃度分析结果

**示例：**
```python
from tools.fishing_tools import calculate_fish_activity

activity = calculate_fish_activity(weather_data)
print(activity)
```

### 基础工具 (basic_tools.py)

提供基础功能的工具集。

#### 主要工具函数

##### get_current_time() -> str

获取当前时间。

**返回：**
- `str`: 格式化的当前时间信息

**示例：**
```python
from tools.basic_tools import get_current_time

time_info = get_current_time()
print(time_info)
# 输出: 当前时间: 2025-11-19 20:30:15 (星期二)
```

##### calculate(expression: str) -> str

计算数学表达式。

**参数：**
- `expression` (str): 数学表达式

**返回：**
- `str`: 计算结果

**支持的操作：**
- 基本运算: +, -, *, /
- 括号: ()
- 幂运算: **

**示例：**
```python
from tools.basic_tools import calculate

result = calculate("15 * 8 + 32")
print(result)
# 输出: 计算结果: 15 * 8 + 32 = 152
```

##### get_location_coordinates(location: str) -> str

获取位置坐标。

**参数：**
- `location` (str): 位置名称

**返回：**
- `str`: 坐标信息

**示例：**
```python
from tools.basic_tools import get_location_coordinates

coords = get_location_coordinates("北京")
print(coords)
# 输出: 北京 的坐标: 经度 116.407394, 纬度 39.904211
```

##### get_fishing_season_advice(location: str) -> str

获取季节性钓鱼建议。

**参数：**
- `location` (str): 位置名称

**返回：**
- `str`: 季节钓鱼建议

**示例：**
```python
from tools.basic_tools import get_fishing_season_advice

advice = get_fishing_season_advice("杭州")
print(advice)
```

## 工具类 API

### API 客户端 (api_client.py)

统一的API客户端，提供天气和地理编码服务。

#### WeatherAPIClient 类

彩云天气API客户端。

##### 主要方法

```python
from utils.api_client import get_weather_client

# 获取客户端实例
client = get_weather_client()

# 获取实时天气
weather_data = client.get_realtime_weather(latitude=39.904211, longitude=116.407394)

# 获取72小时预报
forecast_data = client.get_hourly_forecast(latitude=39.904211, longitude=116.407394, hours=72)
```

**WeatherAPIClient 方法：**

##### get_realtime_weather(lat: float, lon: float) -> dict

获取实时天气数据。

**参数：**
- `lat` (float): 纬度
- `lon` (float): 经度

**返回：**
- `dict`: 天气数据，包含：
  - `temperature`: 温度
  - `condition`: 天气状况
  - `humidity`: 湿度
  - `wind_speed`: 风速
  - `pressure`: 气压
  - `data_quality`: 数据质量标识

##### get_hourly_forecast(lat: float, lon: float, hours: int = 72) -> dict

获取小时级天气预报。

**参数：**
- `lat` (float): 纬度
- `lon` (float): 经度
- `hours` (int): 预报小时数（默认72小时）

**返回：**
- `dict`: 预报数据，包含：
  - `hourly_temperature`: 小时温度数组
  - `hourly_condition`: 小时天气状况数组
  - `forecast_hours`: 预报小时数

#### GeocodingAPIClient 类

高德地图API客户端。

```python
from utils.api_client import get_geocoding_client

# 获取客户端实例
client = get_geocoding_client()

# 地理编码
coords = client.geocode("北京市")
print(f"坐标: {coords}")  # (纬度, 经度)
```

**GeocodingAPIClient 方法：**

##### geocode(address: str) -> tuple[float, float] | None

地理编码获取坐标。

**参数：**
- `address` (str): 地址

**返回：**
- `tuple[float, float] | None`: (纬度, 经度) 或 None

### 坐标工具 (coordinate_utils.py)

坐标处理工具。

#### 主要函数

```python
from utils.coordinate_utils import get_coordinates, get_location_from_coordinates

# 获取坐标
coords = get_coordinates("杭州")
print(f"杭州坐标: {coords}")

# 逆地理编码
location = get_location_from_coordinates(30.2741, 120.1551)
print(f"位置: {location}")
```

##### get_coordinates(location: str) -> tuple[float, float]

获取位置坐标。

**参数：**
- `location` (str): 位置名称

**返回：**
- `tuple[float, float]`: (纬度, 经度)

##### get_location_from_coordinates(lat: float, lon: float) -> str | None

从坐标获取位置名称。

**参数：**
- `lat` (float): 纬度
- `lon` (float): 经度

**返回：**
- `str | None`: 位置名称

### 缓存系统 (cache.py)

简化的缓存系统，支持内存和文件缓存。

#### SimpleCache 类

```python
from utils.cache import cache

# 设置缓存
cache.set("weather_beijing", weather_data, ttl=600)

# 获取缓存
cached_data = cache.get("weather_beijing")

# 获取统计信息
stats = cache.get_stats()
print(f"内存缓存: {stats['memory_cache_count']}项")
print(f"文件缓存: {stats['file_cache_count']}项")

# 清空缓存
cache.clear()
```

##### 主要方法

###### get(key: str) -> any

获取缓存值。

**参数：**
- `key` (str): 缓存键

**返回：**
- `any`: 缓存值或 None

###### set(key: str, value: any, ttl: int = 3600) -> None

设置缓存值。

**参数：**
- `key` (str): 缓存键
- `value` (any): 缓存值
- `ttl` (int): 生存时间（秒）

###### clear() -> None

清空所有缓存。

###### get_stats() -> dict

获取缓存统计信息。

**返回：**
- `dict`: 统计信息

## 环境配置

### 必需的环境变量

```bash
# .env 文件
# LLM 提供商
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here
# 或
ANTHROPIC_API_KEY=your-anthropic-api-key-here
# 或
OPENAI_API_KEY=your-openai-api-key-here

# 外部API
CAIYUN_API_KEY=your-caiyun-api-key-here
AMAP_API_KEY=your-amap-api-key-here

# 系统配置
FISHING_ENABLE_FAKE_DATA=false
DEBUG_LOGGING=false
```

### 环境变量说明

| 变量名 | 说明 | 必需 | 示例值 |
|--------|------|------|--------|
| `ANTHROPIC_AUTH_TOKEN` | 智谱AI API Token | 是 | `your-zhipu-token` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | 否 | `your-claude-key` |
| `OPENAI_API_KEY` | OpenAI GPT API Key | 否 | `your-openai-key` |
| `CAIYUN_API_KEY` | 彩云天气API密钥 | 是 | `your-caiyun-key` |
| `AMAP_API_KEY` | 高德地图API密钥 | 是 | `your-amap-key` |
| `FISHING_ENABLE_FAKE_DATA` | 禁用虚假数据 | 是 | `false` |
| `DEBUG_LOGGING` | 启用调试日志 | 否 | `false` |

## 错误处理

### 伦理约束和错误处理

系统严格遵循伦理约束，绝不编造虚假数据：

```python
# 天气数据验证示例
def _validate_weather_data(weather_data: dict) -> bool:
    """验证天气数据的完整性和合理性"""
    required_fields = ['temperature', 'condition', 'humidity', 'wind_speed', 'pressure']

    # 检查必需字段
    if not all(field in weather_data for field in required_fields):
        return False

    # 检查温度合理性
    temp = weather_data.get('temperature')
    if temp is None or temp < -50 or temp > 60:
        return False

    return True
```

### 常见错误类型

1. **API密钥未配置**
   ```python
   # 错误示例
   ValueError: 智谱AI API Token 未配置，请设置 ANTHROPIC_AUTH_TOKEN 环境变量

   # 解决方案
   # 在 .env 文件中配置
   ANTHROPIC_AUTH_TOKEN=your-zhipu-token-here
   ```

2. **网络连接失败**
   ```python
   # 系统会自动降级到通用建议
   # 而不是编造虚假数据
   response = "无法获取天气数据，请检查网络连接。建议在天气条件良好时钓鱼。"
   ```

3. **位置不存在**
   ```python
   # 诚实报告无法找到位置
   response = "无法找到指定位置：'xxx'。请检查位置名称是否正确。"
   ```

## 使用示例

### 完整的智能体对话示例

```python
from agent import create_optimized_fishing_agent

def demo_conversation():
    """完整的智能体对话示例"""

    # 创建智能体
    agent = create_optimized_fishing_agent(model_provider="zhipu")

    # 对话示例
    conversations = [
        "现在几点了？",
        "帮我计算 15 * 8",
        "查询杭州的天气",
        "明天余杭区钓鱼怎么样？",
        "未来三天宁波的天气如何？"
    ]

    for user_input in conversations:
        print(f"🤔 用户: {user_input}")

        try:
            response = agent.run(user_input)
            print(f"🤖 助手: {response}")
        except Exception as e:
            print(f"❌ 错误: {e}")

        print("-" * 50)

if __name__ == "__main__":
    demo_conversation()
```

### 单独使用工具示例

```python
# 天气工具
from tools.weather_tools import get_current_weather, get_weather_forecast

print("=== 天气工具示例 ===")
weather = get_current_weather("北京")
print(f"北京天气: {weather}")

forecast = get_weather_forecast("上海", 3)
print(f"上海3天预报: {forecast}")

# 钓鱼工具
from tools.fishing_tools import query_fishing_recommendation

print("\n=== 钓鱼工具示例 ===")
recommendation = query_fishing_recommendation("西湖", "明天")
print(f"钓鱼建议: {recommendation}")

# 基础工具
from tools.basic_tools import get_current_time, calculate, get_location_coordinates

print("\n=== 基础工具示例 ===")
time_info = get_current_time()
print(f"当前时间: {time_info}")

calc_result = calculate("123 * 456")
print(f"计算结果: {calc_result}")

coords = get_location_coordinates("深圳")
print(f"深圳坐标: {coords}")
```

### 健康检查示例

```python
from agent import create_optimized_fishing_agent

def health_check_demo():
    """系统健康检查示例"""

    print("🔍 智能钓鱼助手系统健康检查")
    print("=" * 50)

    try:
        # 创建智能体
        agent = create_optimized_fishing_agent()

        # 执行健康检查
        health = agent.health_check()

        print(f"🏥 系统状态: {health['status']}")
        print("📋 组件状态:")

        for check, status in health['checks'].items():
            print(f"  {check}: {status}")

        # 获取统计信息
        stats = agent.get_llm_stats()
        print(f"\n📊 模型调用统计:")
        print(f"  总调用次数: {stats['total_model_calls']}")
        print(f"  成功次数: {stats['successful_calls']}")
        print(f"  失败次数: {stats['failed_calls']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")

        if health['status'] == 'healthy':
            print("\n✅ 系统运行正常，可以提供服务")
        else:
            print("\n⚠️ 系统存在问题，请检查配置")

    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

if __name__ == "__main__":
    health_check_demo()
```

### 高级使用示例

```python
from agent import create_optimized_fishing_agent
from tools.weather_tools import get_current_weather
from tools.fishing_tools import query_fishing_recommendation
from tools.basic_tools import get_current_time

def advanced_fishing_planning():
    """高级钓鱼规划示例"""

    print("🎣 智能钓鱼规划系统")
    print("=" * 50)

    # 1. 获取当前时间
    current_time = get_current_time()
    print(f"📅 规划时间: {current_time}")

    # 2. 获取天气信息
    locations = ["北京", "上海", "杭州", "广州"]

    print("\n🌤️ 天气信息:")
    for location in locations:
        try:
            weather = get_current_weather(location)
            print(f"  {location}: {weather[:100]}...")
        except Exception as e:
            print(f"  {location}: 获取失败 - {e}")

    # 3. 钓鱼推荐分析
    print("\n🎯 钓鱼推荐:")
    fishing_locations = ["西湖", "余杭区", "千岛湖"]

    for location in fishing_locations:
        try:
            recommendation = query_fishing_recommendation(location, "明天")
            print(f"\n📍 {location}:")
            print(f"  {recommendation[:200]}...")
        except Exception as e:
            print(f"  {location}: 分析失败 - {e}")

    # 4. 使用智能体综合分析
    print("\n🤖 智能体综合分析:")
    agent = create_optimized_fishing_agent()

    complex_query = "综合考虑北京、上海、杭州的天气情况，推荐明天最适合钓鱼的地方和时间段"

    try:
        response = agent.run(complex_query)
        print(f"  分析结果: {response}")
    except Exception as e:
        print(f"  分析失败: {e}")

if __name__ == "__main__":
    advanced_fishing_planning()
```

## API 限制和注意事项

### 伦理约束

- **零虚假数据**: 系统绝不编造天气数据
- **诚实报告**: 数据获取失败时明确告知用户
- **优雅降级**: 提供通用建议而非编造信息
- **数据验证**: 严格验证所有数据完整性

### API 限制

#### 智谱AI API
- 需要有效的 API Token
- 有调用频率限制
- 支持中文对话优化

#### 彩云天气 API
- 免费版本有调用次数限制
- 支持72小时天气预报
- 建议在生产环境中配置付费计划

#### 高德地图 API
- 免费版本有日调用量限制
- 支持中国境内地理编码
- 建议配置合适的QPS限制

### 最佳实践

1. **错误处理**: 始终使用 try-catch 包装 API 调用
2. **环境变量**: 不要在代码中硬编码 API 密钥
3. **数据验证**: 严格验证所有输入数据的完整性
4. **性能考虑**: 避免频繁的 API 调用，善用缓存机制
5. **伦理使用**: 诚实地报告数据获取失败，不编造虚假信息

---

**更新时间**: 2025-11-19
**版本**: 2.2.0-architecture-simplified
**维护者**: 智能钓鱼助手项目

**架构设计原则**: 简洁、直接、可靠、伦理