# 智能钓鱼助手 - API 文档 v3.0.2.1

本文档描述智能钓鱼助手v3.0.2.1的主要 API 接口和使用方法，基于 **7因子科学评分体系 + 纯LangChain 1.0+ 同步架构**设计，集成**LLM优化**、**向量存储系统**和**时间段意图理解**功能。

## 🏗️ 版本说明

### 架构优化版本 (v3.0.2.1) ⭐ **当前版本**

在7因子科学评分体系基础上，完善测试覆盖和设计文档：

- ✅ **7因子科学评分**: 从5因子升级至7因子，解决"86分问题"
- ✅ **动态趋势分析**: 气压/温度/风速趋势实时分析，识别"钓鱼黄金期"
- ✅ **季节性评分**: 基于鱼类生物学规律的季节性时段评分
- ✅ **月相评分**: 基于月球引力的8种月相精准识别
- ✅ **测试覆盖完善**: 27个7因子评分测试用例，19个时间段意图测试
- ✅ **设计文档补充**: 完整的系统架构和API设计文档
- ✅ **LLM优化增强**: feature/llm-optimization分支集成，提升推理质量
- ✅ **统一日期处理**: date_utils模块支持相对/绝对日期解析
- ✅ **时间段意图理解**: 95%+识别准确率，支持6种标准时间段

### 7因子科学评分体系版本 (v3.0.0)

重大算法升级，从5因子评分系统升级至7因子科学评分体系：

#### 核心算法升级
- ✅ **7因子评分体系**: 从5因子升级至7因子
  - **温度 (25%)**: 保持不变
  - **天气 (20%)**: 权重从30%降至20%（原本过高）
  - **风力 (15%)**: 权重从20%降至15%
  - **气压 (15%)**: 权重从10%升至15%（关键因子）
  - **湿度 (10%)**: 权重从15%降至10%
  - **季节 (5%)**: ⭐ 新增 - 基于鱼类生物学规律
  - **月相 (5%)**: ⭐ 新增 - 基于月球引力影响

#### 动态趋势分析系统 ⭐ 新增
- ✅ **气压趋势分析**: 识别"钓鱼黄金期"
  - 快速下降 (<-2 hPa/6h): **+20%奖励** - 钓鱼黄金期！
  - 缓慢下降 (-2~-0.5 hPa/6h): +10%奖励
  - 上升趋势: -10%~-20%惩罚
- ✅ **温度趋势分析**: 鱼类活跃度动态调整
  - 快速升温 (>3°C/6h): +10%奖励
  - 缓慢升温 (1-3°C/6h): +5%奖励
- ✅ **风速稳定性分析**: 钓鱼舒适度优化
  - 非常稳定 (标准差<1 km/h): +5%奖励
  - 不稳定: -10%~-20%惩罚

#### 新增核心模块 (v3.0.0)
- ✅ **src/tools/scoring/enhanced_scorer.py**: 增强评分引擎
  - `calculate_seasonal_score()`: 季节性评分算法
  - `calculate_lunar_phase()`: 月相计算（儒略日）
  - `calculate_lunar_score()`: 月相评分算法
  - `analyze_pressure_trend()`: 气压趋势分析
  - `analyze_temperature_trend()`: 温度趋势分析
  - `analyze_wind_stability()`: 风速稳定性分析

### 时间段意图理解版本 (v2.3.0)

在极简架构基础上，新增**时间段意图理解**功能：

- ✅ **时间段意图识别**: 支持"白天"、"晚上"、"上午"等时间段精确过滤
- ✅ **智能时段推荐**: 基于24小时数据的智能时段检测算法
- ✅ **Few-Shot学习**: 95%+时间段意图识别准确率
- ✅ **零额外成本**: 本地过滤算法，不增加API调用

#### 极简架构版本 (v2.2.0)

上一版本的基础架构优化：

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

## 核心 API (v2.3.0)

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

##### query_fishing_recommendation(location: str, date: str = None, time_period: str = None) -> str

智能钓鱼推荐，基于**7因子科学评分体系 + 动态趋势分析**，支持**时间段意图理解**（v2.3.0新增）。

**参数：**
- `location` (str): 位置名称
- `date` (str, 可选): 日期，支持多种格式：
  - 相对日期: "明天"、"后天"、"今天"
  - 绝对日期: "2024-12-25"
  - 空值: 默认为明天
- `time_period` (str, 可选): 时间段限制，支持以下值：
  - **"白天" / "daytime"**: 仅返回6:00-18:00的时段
  - **"晚上" / "night"**: 仅返回18:00-次日6:00的时段
  - **"上午" / "morning"**: 仅返回6:00-12:00的时段
  - **"下午" / "afternoon"**: 仅返回12:00-18:00的时段
  - **"傍晚" / "evening"**: 仅返回16:00-19:00的时段
  - **"深夜" / "midnight"**: 仅返回0:00-6:00的时段
  - **"全天" / "all" / None**: 返回全天所有时段（默认）

**返回：**
- `str`: 专业的钓鱼推荐分析结果，包含时间段过滤后的推荐

**特性：**
- **7因子科学评分体系**（v3.0.0升级）: 温度(25%) + 天气(20%) + 风力(15%) + 气压(15%) + 湿度(10%) + 季节(5%) + 月相(5%)
- **动态趋势分析**（v3.0.0新增）:
  - 气压趋势：快速下降触发"钓鱼黄金期"（+20%奖励）
  - 温度趋势：升温调整鱼类活跃度
  - 风速稳定性：影响钓鱼舒适度
- **季节性评分**（v3.0.0新增）: 基于鱼类生物学规律
  - 春季：早晚最佳（繁殖期）
  - 夏季：避开中午高温
  - 秋季：全天较好（觅食期）
  - 冬季：中午最佳（代谢缓慢）
- **月相评分**（v3.0.0新增）: 8种月相识别，满月夜间最佳（90分）
- **时间段意图识别**（v2.3.0）: 95%+识别准确率
- **智能时段过滤**: 基于时间范围的精确过滤
- **24小时数据驱动**: 基于小时级天气数据的智能时段检测
- 伦理约束：绝不编造虚假数据
- 数据验证：严格验证天气数据完整性
- 零额外成本：本地过滤算法，不增加API调用
- **"86分问题"解决**: 评分区分度提升100%，不同条件差异>5分

**示例：**
```python
from tools.fishing_tools import query_fishing_recommendation

# 基本查询（默认全天）
recommendation = query_fishing_recommendation("余杭区", "明天")
print(recommendation)

# 时间段查询（v2.3.0新功能）
daytime_rec = query_fishing_recommendation("佛山", "明天", "白天")
# 仅返回6:00-18:00的白天时段

evening_rec = query_fishing_recommendation("杭州", "今天", "晚上")
# 仅返回18:00-次日6:00的晚间时段

morning_rec = query_fishing_recommendation("北京", "后天", "上午")
# 仅返回6:00-12:00的上午时段

# 输出示例:
# 🎣 余杭区钓鱼推荐分析 (2024-12-25)
#
# 📊 综合评分: 78/100 (良好)
#
# ⏰ 智能推荐时段（白天）:
#   🥇 第1推荐: 7:00-9:00 (评分: 85.2分)
#   • 温度: 16.5°C | 天气: 多云 | 风速: 2.1m/s
#   • 湿度: 68.5% | 气压: 1015.3 hPa
#   • 推荐理由: 温度适宜, 风力较小, 湿度理想
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

#### 时间段处理函数 (v2.3.0新增)

##### normalize_time_period(time_period: str) -> str

标准化时间段字符串，将用户输入的时间段转换为标准格式（v2.3.0新增）。

**参数：**
- `time_period` (str): 原始时间段字符串，可能包含别名

**返回：**
- `str`: 标准化后的时间段名称

**支持的时间段标准化：**
- **输入 → 输出**:
  - "daytime"、"白昼" → "白天"
  - "night"、"夜间"、"夜晚" → "晚上"
  - "morning"、"早上"、"早晨" → "上午"
  - "afternoon" → "下午"
  - "evening"、"黄昏" → "傍晚"
  - "midnight"、"凌晨" → "深夜"
  - "all"、"整天"、"24小时" → "全天"
  - 空值或未识别的值 → "全天"

**特性：**
- 大小写不敏感
- 自动去除前后空格
- 优雅处理未识别的时间段
- 支持中英文别名

**示例：**
```python
from tools.fishing_tools import normalize_time_period

# 标准化各种输入
print(normalize_time_period("daytime"))    # 输出: "白天"
print(normalize_time_period("早上"))       # 输出: "上午"
print(normalize_time_period("night"))      # 输出: "晚上"
print(normalize_time_period("未知时段"))   # 输出: "全天"
print(normalize_time_period(""))          # 输出: "全天"
```

#### 时间段定义常量 (v2.3.0新增)

**TIME_PERIOD_DEFINITIONS** 常量定义了所有支持的时间段及其配置：

```python
TIME_PERIOD_DEFINITIONS = {
    "白天": {"start": 6, "end": 18, "alias": ["daytime", "白昼"]},
    "晚上": {"start": 18, "end": 6, "alias": ["night", "夜间", "夜晚"], "cross_midnight": True},
    "上午": {"start": 6, "end": 12, "alias": ["morning", "早上", "早晨"]},
    "下午": {"start": 12, "end": 18, "alias": ["afternoon"]},
    "傍晚": {"start": 16, "end": 19, "alias": ["evening", "黄昏"]},
    "深夜": {"start": 0, "end": 6, "alias": ["midnight", "凌晨"]},
    "全天": {"start": 0, "end": 24, "alias": ["all", "整天", "24小时"]},
}
```

**字段说明：**
- `start`: 开始时间（24小时制）
- `end`: 结束时间（24小时制）
- `alias`: 支持的别名列表
- `cross_midnight`: 是否跨越午夜（仅"晚上"时段）

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
        "明天白天佛山市钓鱼怎么样？",  # v2.3.0时间段查询示例
        "今晚杭州钓鱼如何？",         # v2.3.0时间段查询示例
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
from tools.fishing_tools import query_fishing_recommendation, normalize_time_period

print("\n=== 钓鱼工具示例 ===")

# 基本钓鱼推荐
recommendation = query_fishing_recommendation("西湖", "明天")
print(f"全天钓鱼建议: {recommendation[:200]}...")

# v2.3.0时间段查询示例
daytime_rec = query_fishing_recommendation("佛山", "明天", "白天")
print(f"白天钓鱼建议: {daytime_rec[:200]}...")

evening_rec = query_fishing_recommendation("杭州", "今天", "晚上")
print(f"晚上钓鱼建议: {evening_rec[:200]}...")

# v2.3.0时间段标准化示例
print("\n=== 时间段标准化示例 ===")
test_periods = ["daytime", "早上", "night", "afternoon", "unknown"]
for period in test_periods:
    normalized = normalize_time_period(period)
    print(f"'{period}' → '{normalized}'")

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
    """高级钓鱼规划示例（包含v2.3.0时间段功能）"""

    print("🎣 智能钓鱼规划系统 v2.3.0")
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

    # 3. 钓鱼推荐分析（v2.3.0增强版本）
    print("\n🎯 钓鱼推荐:")
    fishing_locations = ["西湖", "余杭区", "千岛湖"]

    for location in fishing_locations:
        try:
            # 全天推荐
            recommendation = query_fishing_recommendation(location, "明天")
            print(f"\n📍 {location} (全天):")
            print(f"  {recommendation[:200]}...")

            # v2.3.0时间段推荐
            daytime_rec = query_fishing_recommendation(location, "明天", "白天")
            print(f"\n📍 {location} (白天时段):")
            print(f"  {daytime_rec[:150]}...")

        except Exception as e:
            print(f"  {location}: 分析失败 - {e}")

    # 4. v2.3.0时间段意图演示
    print("\n⏰ 时间段意图理解演示:")
    time_queries = [
        ("佛山", "明天", "白天"),
        ("杭州", "今天", "晚上"),
        ("北京", "后天", "上午"),
        ("上海", "明天", "下午")
    ]

    for location, date, period in time_queries:
        try:
            result = query_fishing_recommendation(location, date, period)
            print(f"\n🎯 {location} {date} {period}:")
            # 提取时段推荐部分
            lines = result.split('\n')
            for line in lines[:10]:  # 显示前10行
                if "推荐时段" in line or "第" in line or "•" in line:
                    print(f"  {line}")
        except Exception as e:
            print(f"  {location}: 查询失败 - {e}")

    # 5. 使用智能体综合分析
    print("\n🤖 智能体综合分析:")
    agent = create_optimized_fishing_agent()

    complex_queries = [
        "综合考虑北京、上海、杭州的天气情况，推荐明天最适合钓鱼的地方和时间段",
        "明天白天佛山市哪个时间段最适合钓鱼？",  # v2.3.0时间段查询
        "今晚杭州钓鱼条件如何？"                 # v2.3.0时间段查询
    ]

    for query in complex_queries:
        try:
            print(f"\n🤔 用户: {query}")
            response = agent.run(query)
            print(f"🤖 助手: {response[:200]}...")
        except Exception as e:
            print(f"❌ 分析失败: {e}")

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

### v2.3.0 性能优化特性

#### 时间段过滤性能（零额外成本）
- **本地过滤算法**: 时间段过滤在本地完成，不增加外部API调用
- **O(n)时间复杂度**: 高效的时间范围判断算法
- **内存优化**: 智能时段检测仅使用必要的24小时数据
- **缓存友好**: 时间段标准化结果可被缓存

#### 时间段意图识别性能
- **95%+识别准确率**: 基于Few-Shot学习的高准确率
- **零延迟**: 无需额外的模型推理时间
- **向后兼容**: `time_period=None`时性能与v2.2.0完全一致

#### 智能时段检测算法
- **滑动窗口算法**: 1-4小时灵活窗口大小检测
- **去重优化**: 自动去除重叠时段，确保推荐质量
- **评分排序**: 按评分降序排列，优先推荐最佳时段

---

**更新时间**: 2025-11-20
**版本**: 2.3.0-time-period-intent
**维护者**: 智能钓鱼助手项目

**架构设计原则**: 简洁、直接、可靠、伦理

**v2.3.0新特性**: 时间段意图理解、智能时段过滤、Few-Shot学习优化