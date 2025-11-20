# 智能钓鱼助手 - 工具使用指南 v3.0.0

本文档介绍智能钓鱼助手v3.0.0简化架构后的工具使用方法，基于 **纯LangChain 1.0+ 同步架构**设计，包含7因子科学评分体系和时间段意图理解功能。

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

### 主要特性 (v3.0.0)

- **🏗️ 极简架构**: 从75+文件简化到5个核心文件
- **🔌 纯LangChain 1.0+**: 移除LangGraph包装层，直接使用`@tool`装饰器
- **⚡ 同步设计**: 全面采用同步架构，消除异步调用问题
- **🎯 直接调用**: 统一API客户端，无中间层和抽象
- **🎣 7因子科学评分**: 温度(25%) + 天气(20%) + 风力(15%) + 气压(15%) + 湿度(10%) + 季节(5%) + 月相(5%)
- **📈 动态趋势分析**: 气压/温度/风速趋势实时分析，识别"钓鱼黄金期"
- **🕒 时间段意图理解**: 智能识别时间限定词，精确过滤推荐时段
- **📊 伦理约束**: 绝不编造虚假数据，诚实报告系统状态
- **🧪 真实数据**: 基于真实API数据，提供可靠的钓鱼建议

### 工具列表 (v3.0.0)

| 工具模块 | 文件位置 | 功能描述 | 主要特性 |
|---------|---------|---------|---------|
| **天气工具集** | `src/tools/weather_tools.py` | 天气查询和预报 | 实时天气、72小时预报、直接API调用 |
| **钓鱼工具集** | `src/tools/fishing_tools.py` | 钓鱼推荐和评分 | 7因子科学评分 + 动态趋势分析、伦理约束、智能推荐 |
| **评分模块** | `src/tools/scoring/enhanced_scorer.py` | 科学评分算法 | 季节性评分、月相计算、趋势分析 |
| **基础工具集** | `src/tools/basic_tools.py` | 基础实用工具 | 时间查询、数学计算、坐标服务 |

## 🕒 时间段意图理解功能

### 核心特性

**时间段意图理解**是v2.3.0版本引入的功能，在v3.0.0中继续支持，能够智能识别用户输入中的时间限定词，并提供对应时间段的精准钓鱼推荐。

#### ✨ 主要优势

- **🎯 精准识别**: 自动识别"白天"、"晚上"、"上午"等时间限定词
- **📋 多时段支持**: 支持6种标准时间段 + 全天模式
- **🔄 智能过滤**: 根据时间段精确过滤最佳钓鱼时段
- **🔙 完全兼容**: 向后兼容，不影响现有调用方式
- **🤖 Few-Shot增强**: 基于LangChain Few-Shot示例的意图识别

### 支持的时间段

| 时间段 | 时间范围 | 中文别名 | 英文别名 | 钓鱼特点 |
|--------|---------|---------|---------|---------|
| **白天** | 6:00-18:00 | 白昼 | daytime | 温度适宜，光照充足 |
| **晚上** | 18:00-次日6:00 | 夜间、夜晚 | night | 夜钓黄金时段 |
| **上午** | 6:00-12:00 | 早上、早晨 | morning | 清晨活性好 |
| **下午** | 12:00-18:00 | - | afternoon | 下午活性恢复 |
| **傍晚** | 16:00-19:00 | 黄昏 | evening | 第二个觅食高峰 |
| **深夜** | 0:00-6:00 | 凌晨 | midnight | 特定鱼种活跃 |
| **全天** | 0:00-24:00 | 整天、24小时 | all | 综合推荐（默认） |

### 使用示例

#### 基础用法
```python
from src.tools.fishing_tools import query_fishing_recommendation

# 白天推荐（仅返回6:00-18:00时段）
result = query_fishing_recommendation.invoke({
    'location': '杭州',
    'date': '明天',
    'time_period': '白天'
})

# 晚上推荐（仅返回18:00-次日6:00时段）
result = query_fishing_recommendation.invoke({
    'location': '北京',
    'date': '今天',
    'time_period': '晚上'
})

# 上午推荐（仅返回6:00-12:00时段）
result = query_fishing_recommendation.invoke({
    'location': '佛山',
    'date': '后天',
    'time_period': '上午'
})
```

#### 向后兼容用法
```python
# 传统用法（完全兼容）
result = query_fishing_recommendation.invoke({
    'location': '余杭区',
    'date': '明天'
    # time_period 默认为 None，返回全天推荐
})

# 使用英文名称
result = query_fishing_recommendation.invoke({
    'location': '上海',
    'date': '今天',
    'time_period': 'night'  # 自动映射为"晚上"
})
```

### 智能时段识别

#### LLM意图识别示例

| 用户输入 | LLM识别结果 | 生成的工具调用 |
|---------|-------------|---------------|
| "明天白天佛山钓鱼怎么样？" | time_period="白天" | `{"location": "佛山", "date": "明天", "time_period": "白天"}` |
| "今晚杭州适合钓鱼吗？" | time_period="晚上" | `{"location": "杭州", "date": "今天", "time_period": "晚上"}` |
| "后天上午北京钓鱼" | time_period="上午" | `{"location": "北京", "date": "后天", "time_period": "上午"}` |
| "明天钓鱼" | time_period=None | `{"location": "杭州", "date": "明天"}` |

#### 支持的时间限定词
- **白天**: 白天、白昼、daytime
- **晚上**: 晚上、夜间、夜晚、今晚
- **上午**: 上午、早上、早晨、morning
- **下午**: 下午、afternoon
- **傍晚**: 傍晚、黄昏、evening
- **深夜**: 深夜、凌晨、midnight

## 架构简化

### 简化前后对比

```
# 简化前 (75+ 文件) - 复杂架构
src/
├── tools/
│   ├── async/                    # 异步工具模块
│   ├── interfaces/               # 接口定义层
│   ├── base_tool.py             # 基础抽象类
│   └── 20+ 工具实现文件
├── services/
│   ├── manager.py               # 复杂服务管理器
│   ├── registry/                # 注册系统
│   └── 15+ 服务实现文件
├── core/                        # 核心抽象层
│   ├── interfaces/              # 核心接口
│   └── architecture/            # 架构组件
└── middleware/                  # 中间件系统
    ├── logging/                 # 日志中间件
    └── performance/             # 性能监控

# 简化后 (5个核心文件) - v2.2.0 极简架构
src/
├── agent.py                    # 🤖 主智能体 (纯LangChain 1.0+)
├── tools/                      # 🛠️ 工具目录
│   ├── weather_tools.py        # ☁️ 天气工具集 (直接API调用)
│   ├── fishing_tools.py        # 🎣 钓鱼工具集 (7因子算法)
│   ├── basic_tools.py          # 🔧 基础工具集 (实用工具)
│   └── __init__.py             # 📦 工具统一导出
├── utils/                      # 🔨 工具类目录
│   ├── api_client.py           # 🌐 统一API客户端
│   ├── coordinate_utils.py     # 📍 坐标工具
│   └── cache.py                # 💾 简化缓存系统
└── config/                     # ⚙️ 配置管理
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

## 快速开始 (v2.2.0)

### 1. 环境配置

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加必需的API密钥
```

### 2. 基本工具使用

```python
# 导入工具 - v2.2.0 统一接口
from src.tools import get_all_tools
from src.tools.weather_tools import get_current_weather, get_weather_forecast
from src.tools.fishing_tools import query_fishing_recommendation
from src.tools.basic_tools import get_current_time, calculate

# 1. 获取所有工具
tools = get_all_tools()
print(f"🛠️ 可用工具数量: {len(tools)}")

# 2. 获取当前时间
time_result = get_current_time.invoke({})
print(f"🕐 当前时间: {time_result}")

# 3. 数学计算
math_result = calculate.invoke({"expression": "123 * 456"})
print(f"🔢 计算结果: {math_result}")

# 4. 查询天气（直接API调用）
weather_result = get_current_weather.invoke({
    'place': '北京',
    'date': '今天'
})
print(f"🌤️ 北京天气: {weather_result}")

# 5. 智能钓鱼推荐（7因子算法 + 时间段过滤）
fishing_result = query_fishing_recommendation.invoke({
    'location': '余杭区',
    'date': '明天',
    'time_period': '白天'  # 🆕 新增时间段参数
})
print(f"🎣 白天钓鱼建议: {fishing_result[:200]}...")

# 5.1 全天推荐（向后兼容）
full_day_result = query_fishing_recommendation.invoke({
    'location': '杭州',
    'date': '明天'
    # time_period 默认为 None，返回全天推荐
})
print(f"🎣 全天钓鱼建议: {full_day_result[:200]}...")

# 5.2 不同时间段对比示例
time_periods = ['白天', '晚上', '上午', '下午']
for period in time_periods:
    result = query_fishing_recommendation.invoke({
        'location': '上海',
        'date': '明天',
        'time_period': period
    })
    print(f"\n🕒 {period}钓鱼推荐:")
    print(result[:150] + "..." if len(result) > 150 else result)
```

### 3. 命令行测试 (v3.0.0)

```bash
# 测试统一工具接口
uv run python -c "
from src.tools import get_all_tools
tools = get_all_tools()
print(f'🛠️ 总工具数: {len(tools)}')
for tool in tools:
    print(f'  - {tool.name}: {tool.description[:50]}...')
"

# 天气工具测试
uv run python -c "
from src.tools.weather_tools import get_current_weather
print(get_current_weather.invoke({'place': '上海', 'date': '今天'}))
"

# 钓鱼推荐工具测试
uv run python -c "
from src.tools.fishing_tools import query_fishing_recommendation
print(query_fishing_recommendation.invoke({'location': '杭州', 'date': '明天', 'time_period': '白天'}))
"

# 时间段推荐示例
uv run python -c "
from src.tools.fishing_tools import query_fishing_recommendation
print('白天推荐:')
print(query_fishing_recommendation.invoke({'location': '佛山', 'date': '明天', 'time_period': '白天'}))
print('\n晚上推荐:')
print(query_fishing_recommendation.invoke({'location': '佛山', 'date': '明天', 'time_period': '晚上'}))
print('\n全天推荐（传统方式）:')
print(query_fishing_recommendation.invoke({'location': '杭州', 'date': '明天'}))
"

# 基础工具测试
uv run python -c "
from src.tools.basic_tools import get_current_time, calculate
print('🕐 时间:', get_current_time.invoke({}))
print('🔢 计算:', calculate.invoke({'expression': '12 * 8'}))
"
```

### 4. 智能体集成 (v2.2.0)

```python
from src.agent import create_optimized_fishing_agent

# 创建简化智能体（无中间件，纯LangChain 1.0+）
agent = create_optimized_fishing_agent(model_provider="zhipu")

# 智能对话示例
queries = [
    "明天余杭区钓鱼怎么样？",
    "现在几点了？",
    "计算 15 * 8",
    "杭州未来三天天气如何？",
    "推荐一个钓鱼地点"
]

for query in queries:
    print(f"🤔 用户: {query}")
    result = agent.run(query)
    print(f"🤖 助手: {result[:200]}...")
    print("-" * 50)
```

### 5. 交互式CLI使用 (v2.2.0)

```bash
# 启动交互式命令行界面
uv run python main.py

# 示例交互对话：
🎣 智能钓鱼助手 - LangChain 1.0+
==================================================
输入您的问题，例如：
- 明天杭州钓鱼怎么样？
- 北京今天天气如何？
- 推荐一个钓鱼地点
输入 'quit' 退出程序
==================================================

🎣 请输入您的问题: 明天杭州钓鱼怎么样？
🤔 正在思考...
🎯 回答: 根据明天的天气预报...
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
| **query_fishing_recommendation** | 智能钓鱼推荐 | `location: str, date: str, time_period: str` - 位置、日期和时间段限制 |
| | | **参数详解**: | |
| | | - `location`: 地区名称（如"杭州"、"北京"） | |
| | | - `date`: 日期（支持"明天"、"2024-12-25"） | |
| | | - `time_period`: 时间段限制（可选） | |
| | |   * "白天"/"daytime": 6:00-18:00 | |
| | |   * "晚上"/"night": 18:00-次日6:00 | |
| | |   * "上午"/"morning": 6:00-12:00 | |
| | |   * "下午"/"afternoon": 12:00-18:00 | |
| | |   * "傍晚"/"evening": 16:00-19:00 | |
| | |   * "深夜"/"midnight": 0:00-6:00 | |
| | |   * None/不传: 全天推荐（默认） | |
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

### 5. 时间段使用最佳实践 (v3.0.0)

#### 5.1 智能时段选择策略

```python
from src.tools.fishing_tools import query_fishing_recommendation

def smart_time_period_selector(user_query: str, location: str, date: str) -> str:
    """基于用户查询智能选择时间段"""

    # 时间段关键词映射
    time_keywords = {
        '夜钓': '晚上',
        '晚上': '晚上',
        '夜晚': '晚上',
        '今晚': '晚上',
        '夜间': '晚上',
        '清晨': '上午',
        '早上': '上午',
        '早晨': '上午',
        '白天': '白天',
        '白昼': '白天',
        '下午': '下午',
        '傍晚': '傍晚',
        '黄昏': '傍晚',
        '深夜': '深夜',
        '凌晨': '深夜'
    }

    # 检查查询中是否包含时间关键词
    for keyword, period in time_keywords.items():
        if keyword in user_query:
            return period

    # 根据季节智能推荐
    import datetime
    current_month = datetime.datetime.now().month

    if current_month in [12, 1, 2]:  # 冬季
        return '白天'  # 冬季白天温度相对适宜
    elif current_month in [6, 7, 8]:  # 夏季
        return '晚上'  # 夏季晚上更凉爽
    else:
        return None  # 其他季节使用全天推荐

# 使用示例
def get_optimal_fishing_recommendation(user_input: str):
    """获取最优钓鱼推荐"""

    # 提取地点和日期信息
    location = "杭州"  # 实际应用中应该从用户输入中提取
    date = "明天"

    # 智能选择时间段
    time_period = smart_time_period_selector(user_input, location, date)

    # 获取推荐
    result = query_fishing_recommendation.invoke({
        'location': location,
        'date': date,
        'time_period': time_period
    })

    return result, time_period
```

#### 5.2 多时间段对比分析

```python
def comprehensive_time_analysis(location: str, date: str):
    """全面时间段分析"""

    time_periods = ['白天', '上午', '下午', '傍晚', '晚上']
    results = {}

    print(f"🎯 {location} {date} 钓鱼时段分析")
    print("=" * 50)

    for period in time_periods:
        result = query_fishing_recommendation.invoke({
            'location': location,
            'date': date,
            'time_period': period
        })

        results[period] = result

        # 提取关键信息
        if "推荐时段" in result:
            # 提取最佳时段信息
            lines = result.split('\n')
            time_info = [line for line in lines if "推荐" in line or "时段" in line][:3]
            print(f"\n🕒 {period}时段:")
            for info in time_info:
                print(f"  {info}")

    # 综合建议
    print(f"\n📊 综合建议:")
    best_period = max(results.keys(), key=lambda p: "评分" in results[p])
    print(f"推荐时段: {best_period}")

    return results

# 使用示例
# comprehensive_time_analysis("西湖", "明天")
```

#### 5.3 性能优化建议

```python
import time
from functools import lru_cache
from src.tools.fishing_tools import query_fishing_recommendation

@lru_cache(maxsize=100)
def cached_fishing_recommendation(location: str, date: str, time_period: str = None):
    """缓存版本的钓鱼推荐（提高性能）"""
    return query_fishing_recommendation.invoke({
        'location': location,
        'date': date,
        'time_period': time_period
    })

def batch_time_period_analysis(locations: list, date: str, time_period: str):
    """批量时间段分析（提高效率）"""

    results = []
    start_time = time.time()

    for location in locations:
        try:
            result = cached_fishing_recommendation(location, date, time_period)
            results.append({
                'location': location,
                'result': result,
                'success': True
            })
        except Exception as e:
            results.append({
                'location': location,
                'error': str(e),
                'success': False
            })

    end_time = time.time()

    success_count = sum(1 for r in results if r['success'])

    print(f"📊 批量分析结果:")
    print(f"  - 成功查询: {success_count}/{len(locations)}")
    print(f"  - 总耗时: {end_time - start_time:.2f}秒")
    print(f"  - 平均耗时: {(end_time - start_time) / len(locations):.2f}秒/查询")

    return results

# 使用示例
cities = ['北京', '上海', '杭州', '深圳']
# batch_time_period_analysis(cities, '明天', '白天')
```

#### 5.4 用户体验优化

```python
def enhanced_fishing_recommendation(location: str, date: str, user_preference: str = None):
    """增强版钓鱼推荐（考虑用户偏好）"""

    # 默认时间段
    time_period = None

    # 根据用户偏好调整
    if user_preference:
        if "夜钓" in user_preference:
            time_period = '晚上'
        elif "早起" in user_preference:
            time_period = '上午'
        elif "懒觉" in user_preference:
            time_period = '下午'

    # 获取推荐
    result = query_fishing_recommendation.invoke({
        'location': location,
        'date': date,
        'time_period': time_period
    })

    # 生成友好提示
    if time_period:
        time_tips = {
            '白天': '☀️ 白天时段光照充足，适合大多数鱼类活动',
            '晚上': '🌙️ 夜钓时段，大鱼更活跃',
            '上午': '🌅 清晨鱼类觅食活跃，是黄金时段',
            '下午': '⛅ 下午可避开强光，适合耐心垂钓',
            '傍晚': '🌇 傍晚是第二个觅食高峰期'
        }

        tip = time_tips.get(time_period, '')
        if tip:
            result = f"{tip}\n\n{result}"

    return result

# 使用示例
# result = enhanced_fishing_recommendation('西湖', '明天', '喜欢夜钓')
```

#### 5.5 时间段验证和调试

```python
def validate_time_period_logic(location: str, date: str):
    """验证时间段过滤逻辑的正确性"""

    # 测试所有时间段
    test_periods = ['白天', '上午', '下午', '傍晚', '晚上', '深夜']

    print(f"🔍 {location} {date} 时间段验证")
    print("=" * 40)

    for period in test_periods:
        print(f"\n📋 测试时间段: {period}")

        result = query_fishing_recommendation.invoke({
            'location': location,
            'date': date,
            'time_period': period
        })

        # 验证时间段标识
        if f"（{period}）" in result:
            print(f"  ✅ 时间段标识正确显示")
        else:
            print(f"  ❌ 缺少时间段标识")

        # 验证时段过滤
        period_ranges = {
            '白天': (6, 18),
            '上午': (6, 12),
            '下午': (12, 18),
            '傍晚': (16, 19),
            '晚上': (18, 24),
            '深夜': (0, 6)
        }

        if period in period_ranges:
            start_hour, end_hour = period_ranges[period]
            if period in ['晚上']:  # 特殊处理跨午夜
                if '00:' in result or '01:' in result or '02:' in result or '03:' in result:
                    print(f"  ✅ 包含深夜时段 ({start_hour}-{end_hour}点范围)")
            elif '18:' in result or '19:' in result or '20:' in result:
                    print(f"  ✅ 包含晚上时段 ({start_hour}点-{end_hour}点范围)")
            else:
                print(f"  ⚠️ 时段过滤可能有问题")
            else:
                # 检查是否在正常时间范围内
                expected_hours = range(start_hour, end_hour)
                found_expected = any(f"{h:02d}:" in result for h in expected_hours)
                if found_expected:
                    print(f"  ✅ 包含预期时段 ({start_hour}:00-{end_hour}:00)")
                else:
                    print(f"  ❌ 缺少预期时段")

        print(f"  📄 推荐长度: {len(result)} 字符")

# 使用示例
# validate_time_period_logic('杭州', '明天')
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

#### 6. 时间段功能故障排除

##### 6.1 时间段过滤无效

**问题现象**：设置time_period参数后仍返回全天推荐

```python
def debug_time_period_filtering(location: str, date: str, time_period: str):
    """调试时间段过滤逻辑"""
    print(f"🔍 调试时间段过滤: {location} {date} {time_period}")
    print("=" * 50)

    try:
        from tools.fishing_tools import (
            query_fishing_recommendation,
            normalize_time_period,
            TIME_PERIOD_DEFINITIONS
        )

        # 1. 检查时间段标准化
        normalized = normalize_time_period(time_period)
        print(f"1️⃣ 时间段标准化: '{time_period}' → '{normalized}'")

        if normalized in TIME_PERIOD_DEFINITIONS:
            definition = TIME_PERIOD_DEFINITIONS[normalized]
            print(f"2️⃣ 时间段定义: {definition}")
        else:
            print(f"2️⃣ 警告: 未识别的时间段 '{normalized}'")
            return

        # 3. 测试工具调用
        print(f"3️⃣ 测试钓鱼推荐工具...")
        result = query_fishing_recommendation.invoke({
            'location': location,
            'date': date,
            'time_period': time_period
        })

        # 4. 验证结果
        if f"（{normalized}）" in result:
            print(f"4️⃣ ✅ 时间段标识正确显示")
        else:
            print(f"4️⃣ ❌ 时间段标识缺失")

        # 5. 检查时段范围
        time_ranges = {
            '白天': '6:00-18:00',
            '上午': '6:00-12:00',
            '下午': '12:00-18:00',
            '傍晚': '16:00-19:00',
            '晚上': '18:00-次日6:00',
            '深夜': '0:00-6:00'
        }

        if normalized in time_ranges:
            expected_range = time_ranges[normalized]
            print(f"5️⃣ 期望时段范围: {expected_range}")

            # 检查结果中是否包含预期时段
            has_expected_time = False
            for hour in range(24):
                hour_str = f"{hour:02d}:"
                if hour_str in result:
                    print(f"   发现时段: {hour_str}")
                    if normalized == '白天' and 6 <= hour < 18:
                        has_expected_time = True
                    elif normalized == '上午' and 6 <= hour < 12:
                        has_expected_time = True
                    elif normalized == '下午' and 12 <= hour < 18:
                        has_expected_time = True
                    elif normalized == '晚上' and (hour >= 18 or hour < 6):
                        has_expected_time = True

            if has_expected_time:
                print(f"   ✅ 包含预期时段")
            else:
                print(f"   ❌ 缺少预期时段")

        print(f"\n📄 推荐结果预览（前500字符）:")
        print(result[:500] + "..." if len(result) > 500 else result)

    except Exception as e:
        print(f"❌ 调试过程中出错: {e}")
        import traceback
        traceback.print_exc()

# 使用示例
# debug_time_period_filtering('杭州', '明天', '白天')
```

##### 6.2 LLM意图识别不准确

**问题现象**：用户输入时间段但LLM未正确提取time_period参数

```python
def test_llm_time_intent_recognition():
    """测试LLM时间段意图识别"""
    print("🧠 LLM时间段意图识别测试")
    print("=" * 40)

    from agent import create_optimized_fishing_agent

    # 创建智能体（需要配置API密钥）
    try:
        agent = create_optimized_fishing_agent()

        # 测试用例
        test_queries = [
            ("明天白天杭州钓鱼", "白天"),
            ("今晚上海钓鱼时机", "晚上"),
            ("后天上午北京钓鱼", "上午"),
            ("明天下午深圳钓鱼", "下午"),
            ("明天广州钓鱼", None),  # 无时间段
        ]

        for query, expected_period in test_queries:
            print(f"\n📝 测试查询: '{query}'")
            print(f"期望时间段: {expected_period}")

            # 这里需要实际的agent.invoke来测试
            # 由于需要API密钥，仅提供测试框架
            print("   需要真实API调用来验证LLM意图识别")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("   请检查API密钥配置")

# 使用示例
# test_llm_time_intent_recognition()
```

##### 6.3 时间段过滤返回空结果

**问题现象**：某些时间段组合返回无推荐结果

```python
def handle_empty_time_period_results(location: str, date: str, time_period: str):
    """处理时间段过滤为空的情况"""
    print(f"⚠️ 处理空结果: {location} {date} {time_period}")

    from tools.fishing_tools import (
        query_fishing_recommendation,
        normalize_time_period
    )

    # 1. 首先验证时间段是否有效
    normalized = normalize_time_period(time_period)
    if normalized == "全天":
        print("   → 无效时间段，将使用全天推荐")
        return query_fishing_recommendation.invoke({
            'location': location,
            'date': date
        })

    # 2. 尝试获取全天推荐作为备选
    print("   → 获取全天推荐作为备选方案...")
    full_day_result = query_fishing_recommendation.invoke({
        'location': location,
        'date': date
    })

    # 3. 检查全天推荐中是否有符合目标时间段的时段
    if contains_time_period(full_day_result, normalized):
        print(f"   ✅ 在全天推荐中找到{normalized}时段")
        # 手动过滤并添加时间段标识
        return f"（{normalized}时段推荐）\n\n" + extract_relevant_time_slots(full_day_result, normalized)
    else:
        print(f"   ❌ 全天推荐中无{normalized}时段")
        return f"很抱歉，{date}{location}的{normalized}时段可能不适合钓鱼。建议您：\n\n" \
               f"1. 尝试其他时间段（如白天、下午）\n" \
               f"2. 查看全天推荐了解整体情况\n" \
               f"3. 考虑其他日期的钓鱼条件"

def contains_time_period(result: str, time_period: str) -> bool:
    """检查推荐结果是否包含特定时间段"""
    time_ranges = {
        '白天': [h for h in range(6, 18)],
        '上午': [h for h in range(6, 12)],
        '下午': [h for h in range(12, 18)],
        '傍晚': [h for h in range(16, 19)],
        '晚上': [h for h in range(18, 24)] + [h for h in range(0, 6)],
        '深夜': [h for h in range(0, 6)]
    }

    if time_period in time_ranges:
        for hour in time_ranges[time_period]:
            if f"{hour:02d}:" in result:
                return True
    return False

def extract_relevant_time_slots(result: str, time_period: str) -> str:
    """从全天推荐中提取相关时间段"""
    # 简化实现，实际需要更复杂的解析逻辑
    lines = result.split('\n')
    relevant_lines = []

    time_ranges = {
        '白天': [h for h in range(6, 18)],
        '上午': [h for h in range(6, 12)],
        '下午': [h for h in range(12, 18)],
        '傍晚': [h for h in range(16, 19)],
        '晚上': [h for h in range(18, 24)] + [h for h in range(0, 6)],
        '深夜': [h for h in range(0, 6)]
    }

    if time_period in time_ranges:
        target_hours = time_ranges[time_period]
        for line in lines:
            for hour in target_hours:
                if f"{hour:02d}:" in line:
                    relevant_lines.append(line)
                    break

    return '\n'.join(relevant_lines) if relevant_lines else "暂无相关时段推荐"

# 使用示例
# handle_empty_time_period_results('杭州', '明天', '深夜')
```

##### 6.4 性能问题诊断

**问题现象**：时间段过滤导致响应时间过长

```python
def benchmark_time_period_performance():
    """时间段功能性能基准测试"""
    import time
    from tools.fishing_tools import (
        query_fishing_recommendation,
        _filter_time_slots_by_period,
        normalize_time_period
    )

    print("⏱️ 时间段功能性能测试")
    print("=" * 40)

    # 测试用例
    test_cases = [
        ('杭州', '明天', None),
        ('杭州', '明天', '白天'),
        ('杭州', '明天', '晚上'),
        ('杭州', '明天', '上午'),
        ('杭州', '明天', '下午'),
    ]

    results = []

    for location, date, time_period in test_cases:
        print(f"\n🧪 测试: {location} {date} {time_period or '全天'}")

        # 测试标准化性能
        start_time = time.time()
        normalized = normalize_time_period(time_period) if time_period else None
        normalize_time = time.time() - start_time

        # 测试完整工具调用
        start_time = time.time()
        try:
            result = query_fishing_recommendation.invoke({
                'location': location,
                'date': date,
                'time_period': time_period
            })
            success = True
            result_length = len(result)
        except Exception as e:
            success = False
            result_length = 0
        total_time = time.time() - start_time

        result_data = {
            'case': f"{location}_{date}_{time_period or '全天'}",
            'normalize_time': normalize_time * 1000,  # ms
            'total_time': total_time * 1000,  # ms
            'success': success,
            'result_length': result_length
        }

        results.append(result_data)

        print(f"   标准化时间: {normalize_time * 1000:.2f}ms")
        print(f"   总耗时: {total_time * 1000:.2f}ms")
        print(f"   结果状态: {'✅ 成功' if success else '❌ 失败'}")
        if success:
            print(f"   结果长度: {result_length}字符")

    # 性能分析
    print(f"\n📊 性能分析:")
    successful_results = [r for r in results if r['success']]
    if successful_results:
        avg_total_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
        avg_normalize_time = sum(r['normalize_time'] for r in successful_results) / len(successful_results)

        print(f"   平均总耗时: {avg_total_time:.2f}ms")
        print(f"   平均标准化耗时: {avg_normalize_time:.2f}ms")
        print(f"   标准化开销占比: {(avg_normalize_time/avg_total_time)*100:.1f}%")

        # 性能建议
        if avg_total_time > 5000:  # 5秒
            print(f"   ⚠️ 警告: 响应时间过长，建议优化")
        if avg_normalize_time > 10:  # 10ms
            print(f"   ⚠️ 警告: 标准化耗时过长，检查逻辑")

# 使用示例
# benchmark_time_period_performance()
```

---

**更新时间**: 2025-11-20
**版本**: 3.0.0-7factor-scientific-scoring
**维护者**: 智能钓鱼助手项目