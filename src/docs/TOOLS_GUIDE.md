# 智能钓鱼助手 - 简化工具使用指南

本文档介绍智能钓鱼助手简化架构后的工具使用方法，基于 LangChain 1.0+ 同步架构设计。

## 目录

- [概述](#概述)
- [架构简化](#架构简化)
- [快速开始](#快速开始)
- [工具详细使用](#工具详细使用)
- [智能体集成](#智能体集成)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 概述

智能钓鱼助手在架构简化后，将原有的复杂异步工具系统重构为简洁的同步工具，直接使用 LangChain 1.0+ 的 `@tool` 装饰器。

### 主要特性

- **🏗️ 极简架构**: 从75+文件简化到5个核心文件
- **🔌 同步设计**: 全面采用同步架构，消除异步调用问题
- **⚡ 直接调用**: 统一API客户端，无中间层
- **⚙️ 零配置**: 开箱即用，无需复杂配置
- **📊 伦理约束**: 绝不编造虚假数据，诚实报告系统状态
- **🧪 真实数据**: 基于真实API数据，提供可靠的钓鱼建议

### 工具列表

| 工具模块 | 功能描述 | 主要特性 |
|---------|---------|---------|
| **weather_tools.py** | 天气工具集 | 实时天气、72小时预报、真实API数据 |
| **fishing_tools.py** | 钓鱼工具集 | 智能推荐、7因子评分、伦理约束 |
| **basic_tools.py** | 基础工具集 | 时间查询、数学计算、坐标服务 |

## 架构简化

### 简化前后对比

```
# 简化前 (75+ 文件)
src/
├── tools/
│   ├── async/                    # 异步工具模块
│   ├── interfaces/               # 接口定义
│   ├── base_tool.py             # 基础类
│   └── 20+ 工具实现文件
├── services/
│   ├── manager.py               # 服务管理器
│   ├── registry/                # 注册系统
│   └── 15+ 服务实现文件
└── core/
    ├── interfaces/              # 核心接口
    └── architecture/            # 架构组件

# 简化后 (5个核心文件)
src/
├── agent.py                    # 主智能体 (LangChain 1.0+)
├── tools/                      # 工具目录
│   ├── weather_tools.py        # 天气工具集
│   ├── fishing_tools.py        # 钓鱼工具集
│   ├── basic_tools.py          # 基础工具集
│   └── __init__.py             # 工具导出
├── utils/                      # 工具类目录
│   ├── api_client.py           # 统一API客户端
│   ├── coordinate_utils.py     # 坐标工具
│   ├── cache.py                # 简化缓存系统
│   └── __init__.py             # 工具类导出
└── docs/                       # 项目文档
```

### LangChain 1.0+ 工具装饰器

```python
from langchain.tools import tool

@tool
def get_current_weather(location: str) -> str:
    """获取指定位置的当前天气信息"""
    # 直接调用API客户端，无中间层
    from ..utils.api_client import get_weather_client
    from ..utils.coordinate_utils import get_coordinates

    try:
        coords = get_coordinates(location)
        weather_client = get_weather_client()
        weather_data = weather_client.get_realtime_weather(coords[0], coords[1])
        return _format_weather_response(weather_data, location)
    except Exception as e:
        return f"获取天气数据失败: {str(e)}"
```

## 快速开始

### 1. 基本使用

```python
# 导入工具 - 支持相对和绝对导入
from tools.weather_tools import get_current_weather, get_weather_forecast
from tools.fishing_tools import query_fishing_recommendation
from tools.basic_tools import get_current_time, calculate

# 1. 获取当前时间
time_result = get_current_time()
print(f"🕐 当前时间: {time_result}")

# 2. 数学计算
math_result = calculate("123 * 456")
print(f"🔢 计算结果: {math_result}")

# 3. 查询天气
weather_result = get_current_weather("北京")
print(f"🌤️ 北京天气: {weather_result}")

# 4. 智能钓鱼推荐
fishing_result = query_fishing_recommendation("余杭区", "明天")
print(f"🎣 钓鱼建议: {fishing_result[:200]}...")
```

### 2. 命令行测试

```bash
# 天气工具测试
uv run python -c "
from tools.weather_tools import get_current_weather
print(get_current_weather('上海'))
"

# 钓鱼推荐工具测试
uv run python -c "
from tools.fishing_tools import query_fishing_recommendation
print(query_fishing_recommendation('杭州', '明天'))
"

# 时间工具测试
uv run python -c "
from tools.basic_tools import get_current_time
print(get_current_time())
"

# 计算工具测试
uv run python -c "
from tools.basic_tools import calculate
print(calculate('12 * 8'))
"
```

### 3. 智能体集成

```python
from agent import create_optimized_fishing_agent

# 创建智能钓鱼助手
agent = create_optimized_fishing_agent(model_provider="zhipu")

# 智能对话示例
queries = [
    "明天余杭区钓鱼怎么样？",
    "现在几点了？",
    "计算 15 * 8",
    "杭州未来三天天气如何？"
]

for query in queries:
    print(f"🤔 用户: {query}")
    result = agent.run(query)
    print(f"🤖 助手: {result[:200]}...")
    print("-" * 50)
```

## 工具详细使用

### weather_tools.py - 天气工具集

#### 核心功能

天气工具集提供实时天气查询、72小时天气预报、指定日期天气查询等功能，基于彩云天气API。

#### 主要工具

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| **get_current_weather** | 获取实时天气 | `location: str` - 位置名称 |
| **get_weather_forecast** | 获取天气预报 | `location: str, days: int` - 位置和天数(1-7) |
| **get_weather_by_date** | 获取指定日期天气 | `location: str, date_str: str` - 位置和日期 |

#### 使用示例

```python
from tools.weather_tools import get_current_weather, get_weather_forecast, get_weather_by_date

# 1. 获取实时天气
weather = get_current_weather("杭州")
print(f"杭州当前天气: {weather}")

# 2. 获取3天预报
forecast = get_weather_forecast("北京", 3)
print(f"北京3天预报: {forecast}")

# 3. 获取指定日期天气
date_weather = get_weather_by_date("上海", "2024-12-25")
print(f"上海圣诞节天气: {date_weather}")
```

#### 数据格式

天气数据返回格式示例：

```
🌤️ 杭州 当前天气:
温度: 12.5°C
天气状况: 晴朗
湿度: 65.8%
风速: 3.2 m/s
气压: 1018.2 hPa
更新时间: 2025-11-19 20:30:15
```

### fishing_tools.py - 钓鱼工具集

#### 核心功能

钓鱼工具集基于真实天气数据提供专业的钓鱼推荐分析，采用7因子评分算法，严格遵循伦理约束。

#### 主要工具

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| **query_fishing_recommendation** | 智能钓鱼推荐 | `location: str, date: str` - 位置和日期 |
| **analyze_fishing_conditions** | 钓鱼条件分析 | `weather_data: dict` - 天气数据 |
| **calculate_fish_activity** | 鱼类活跃度计算 | `weather_data: dict` - 天气数据 |
| **get_fishing_insights** | 多天钓鱼洞察 | `location: str, days: int` - 位置和天数 |

#### 7因子评分算法

1. **温度因子**: 10-25°C为最佳范围
2. **天气因子**: 多云、阴天为佳
3. **风力因子**: 1-3级微风最适宜
4. **气压因子**: 稳定高压天气
5. **湿度因子**: 60-80%适度湿度
6. **季节因子**: 考虑季节性钓鱼规律
7. **时间因子**: 黄金时段(早上6-8点, 傍晚18-20点)

#### 使用示例

```python
from tools.fishing_tools import (
    query_fishing_recommendation,
    analyze_fishing_conditions,
    calculate_fish_activity,
    get_fishing_insights
)

# 1. 智能钓鱼推荐
recommendation = query_fishing_recommendation("余杭区", "明天")
print(f"钓鱼推荐: {recommendation}")

# 2. 钓鱼条件分析
# 首先获取天气数据
from tools.weather_tools import get_current_weather
weather_data = get_current_weather("杭州")
# 然后分析条件
analysis = analyze_fishing_conditions({"temperature": 15, "condition": "多云"})
print(f"条件分析: {analysis}")

# 3. 鱼类活跃度计算
activity = calculate_fish_activity({"temperature": 18, "wind_speed": 2})
print(f"鱼类活跃度: {activity}")

# 4. 多天钓鱼洞察
insights = get_fishing_insights("西湖", 3)
print(f"3天钓鱼洞察: {insights}")
```

#### 伦理约束

- **零虚假数据**: 绝不编造天气数据
- **诚实报告**: 数据获取失败时明确告知用户
- **优雅降级**: 提供通用钓鱼建议而非编造信息
- **数据验证**: 严格验证天气数据完整性

### basic_tools.py - 基础工具集

#### 核心功能

基础工具集提供时间查询、数学计算、坐标服务等基础功能。

#### 主要工具

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| **get_current_time** | 获取当前时间 | 无参数 |
| **calculate** | 数学表达式计算 | `expression: str` - 数学表达式 |
| **get_location_coordinates** | 获取位置坐标 | `location: str` - 位置名称 |
| **get_fishing_season_advice** | 季节性钓鱼建议 | `location: str` - 位置名称 |

#### 使用示例

```python
from tools.basic_tools import (
    get_current_time,
    calculate,
    get_location_coordinates,
    get_fishing_season_advice
)

# 1. 获取当前时间
current_time = get_current_time()
print(f"当前时间: {current_time}")

# 2. 数学计算
result = calculate("15 * 8 + 32")
print(f"计算结果: {result}")

# 3. 获取坐标
coords = get_location_coordinates("北京")
print(f"北京坐标: {coords}")

# 4. 季节钓鱼建议
season_advice = get_fishing_season_advice("杭州")
print(f"季节建议: {season_advice}")
```

## 智能体集成

### 创建智能体

```python
from agent import create_optimized_fishing_agent

# 使用不同模型提供商创建智能体
agent_zhipu = create_optimized_fishing_agent(model_provider="zhipu")
agent_claude = create_optimized_fishing_agent(model_provider="anthropic")
agent_openai = create_optimized_fishing_agent(model_provider="openai")
```

### 智能对话

```python
def demo_conversation():
    agent = create_optimized_fishing_agent(model_provider="zhipu")

    # 对话示例
    conversations = [
        "现在几点了？",
        "帮我计算 24 * 15",
        "查询杭州的天气",
        "明天西湖钓鱼怎么样？",
        "未来三天宁波的天气如何？"
    ]

    for query in conversations:
        print(f"用户: {query}")
        response = agent.run(query)
        print(f"助手: {response}")
        print("-" * 50)

demo_conversation()
```

### 健康检查

```python
def health_check():
    agent = create_optimized_fishing_agent()

    # 检查系统状态
    health = agent.health_check()
    print(f"系统状态: {health['status']}")

    # 显示各组件状态
    for check, status in health['checks'].items():
        print(f"  {check}: {status}")

    # 获取统计信息
    stats = agent.get_llm_stats()
    print(f"模型调用统计: {stats}")

health_check()
```

## 最佳实践

### 1. 错误处理

```python
from tools.weather_tools import get_current_weather

def safe_weather_query(location):
    """安全的天气查询"""
    try:
        result = get_current_weather(location)
        if "获取天气数据失败" in result:
            print("天气数据获取失败，请检查网络连接")
            return None
        return result
    except Exception as e:
        print(f"查询出错: {e}")
        return None

# 使用示例
weather = safe_weather_query("北京")
if weather:
    print(f"天气信息: {weather}")
```

### 2. 数据验证

```python
from tools.fishing_tools import query_fishing_recommendation

def validate_fishing_data(location, date):
    """验证钓鱼推荐数据质量"""
    recommendation = query_fishing_recommendation(location, date)

    # 检查是否包含评分信息
    if "评分" in recommendation:
        print("✅ 包含专业评分")
    else:
        print("⚠️ 缺少评分信息")

    # 检查是否有天气数据
    if "温度" in recommendation:
        print("✅ 包含天气数据")
    else:
        print("⚠️ 缺少天气数据")

    return recommendation

# 使用示例
result = validate_fishing_data("西湖", "明天")
print(f"钓鱼推荐: {result}")
```

### 3. 缓存优化

```python
from tools.weather_tools import get_current_weather
from utils.cache import cache

def cached_weather_query(location):
    """带缓存的天气查询"""
    cache_key = f"weather_{location}"

    # 尝试从缓存获取
    cached_result = cache.get(cache_key)
    if cached_result:
        print(f"从缓存获取 {location} 天气数据")
        return cached_result

    # 获取新数据并缓存
    result = get_current_weather(location)
    cache.set(cache_key, result, ttl=600)  # 缓存10分钟

    return result

# 使用示例
weather = cached_weather_query("上海")
print(weather)
```

### 4. 组合工具使用

```python
def comprehensive_fishing_planning(location):
    """综合钓鱼规划"""

    # 1. 获取当前时间
    from tools.basic_tools import get_current_time
    current_time = get_current_time()
    print(f"规划时间: {current_time}")

    # 2. 获取天气信息
    from tools.weather_tools import get_current_weather, get_weather_forecast
    current_weather = get_current_weather(location)
    forecast = get_weather_forecast(location, 3)

    # 3. 获取钓鱼推荐
    from tools.fishing_tools import query_fishing_recommendation
    recommendation = query_fishing_recommendation(location, "明天")

    # 4. 获取季节建议
    from tools.basic_tools import get_fishing_season_advice
    season_advice = get_fishing_season_advice(location)

    # 综合输出
    planning_result = f"""
🎣 {location} 钓鱼规划报告
📅 规划时间: {current_time}

🌤️ 当前天气: {current_weather}
📊 天气预报: {forecast[:200]}...

🎯 钓鱼推荐: {recommendation[:300]}...
🗓️ 季节建议: {season_advice}
"""

    return planning_result

# 使用示例
plan = comprehensive_fishing_planning("西湖")
print(plan)
```

## 故障排除

### 常见问题及解决方案

#### 1. 导入错误

```python
# 错误的导入方式
from tools.weather_tools import get_current_weather  # 可能因路径问题失败

# 正确的导入方式 - 使用动态导入
try:
    from tools.weather_tools import get_current_weather
except ImportError:
    try:
        from src.tools.weather_tools import get_current_weather
    except ImportError:
        # 绝对导入作为最后选择
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from tools.weather_tools import get_current_weather
```

#### 2. API密钥问题

```bash
# 检查环境变量
echo $CAIYUN_API_KEY
echo $AMAP_API_KEY

# 或在Python中检查
import os
print("彩云天气API密钥:", "已配置" if os.getenv("CAIYUN_API_KEY") else "未配置")
print("高德地图API密钥:", "已配置" if os.getenv("AMAP_API_KEY") else "未配置")
```

#### 3. 网络连接问题

```python
import requests

def check_network_connectivity():
    """检查网络连接"""
    try:
        response = requests.get("https://api.caiyunapp.com/v2/weather", timeout=5)
        print("✅ 网络连接正常")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络连接失败: {e}")
        return False

check_network_connectivity()
```

#### 4. 数据质量问题

```python
def validate_weather_data(weather_data):
    """验证天气数据质量"""
    required_fields = ['temperature', 'condition', 'humidity', 'wind_speed']
    missing_fields = [field for field in required_fields if field not in weather_data]

    if missing_fields:
        print(f"⚠️ 天气数据不完整，缺少字段: {missing_fields}")
        return False

    # 检查温度合理性
    temp = weather_data.get('temperature')
    if temp is None or temp < -50 or temp > 60:
        print(f"⚠️ 温度数据异常: {temp}")
        return False

    print("✅ 天气数据验证通过")
    return True
```

#### 5. 智能体状态检查

```python
def diagnostic_check():
    """系统诊断检查"""
    print("🔍 智能钓鱼助手系统诊断")
    print("=" * 50)

    # 1. 检查工具导入
    tools_status = {}
    try:
        from tools.weather_tools import get_current_weather
        tools_status['weather_tools'] = '✅ 正常'
    except Exception as e:
        tools_status['weather_tools'] = f'❌ 错误: {e}'

    try:
        from tools.fishing_tools import query_fishing_recommendation
        tools_status['fishing_tools'] = '✅ 正常'
    except Exception as e:
        tools_status['fishing_tools'] = f'❌ 错误: {e}'

    try:
        from tools.basic_tools import get_current_time
        tools_status['basic_tools'] = '✅ 正常'
    except Exception as e:
        tools_status['basic_tools'] = f'❌ 错误: {e}'

    for tool, status in tools_status.items():
        print(f"{tool}: {status}")

    # 2. 检查智能体
    try:
        from agent import create_optimized_fishing_agent
        agent = create_optimized_fishing_agent()
        health = agent.health_check()
        print(f"智能体状态: {health['status']}")
    except Exception as e:
        print(f"智能体状态: ❌ 错误: {e}")

    # 3. 检查API密钥
    import os
    api_keys = {
        'CAIYUN_API_KEY': os.getenv("CAIYUN_API_KEY"),
        'AMAP_API_KEY': os.getenv("AMAP_API_KEY"),
    }

    print("\nAPI密钥状态:")
    for key, value in api_keys.items():
        status = "✅ 已配置" if value else "❌ 未配置"
        print(f"{key}: {status}")

# 运行诊断
diagnostic_check()
```

### 调试技巧

#### 启用详细日志

```python
import logging
import os

# 设置日志级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 启用工具调试模式
os.environ['DEBUG_LOGGING'] = 'true'

# 使用工具时会输出详细日志
from tools.weather_tools import get_current_weather
result = get_current_weather("北京")
```

#### 性能监控

```python
import time
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"⏱️ {func.__name__} 执行时间: {execution_time:.2f}秒")

        return result
    return wrapper

# 使用监控装饰器
@monitor_performance
def test_weather_tool():
    from tools.weather_tools import get_current_weather
    return get_current_weather("杭州")

result = test_weather_tool()
```

---

**更新时间**: 2025-11-19
**版本**: 2.2.0-architecture-simplified
**维护者**: 智能钓鱼助手项目