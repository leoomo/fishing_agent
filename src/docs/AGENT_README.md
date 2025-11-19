# 智能钓鱼助手 - LangChain 1.0+ 简化架构指南

本项目基于最新的 LangChain 1.0+ API 创建了一个智能钓鱼助手，采用**架构简化设计**（从75+文件简化到5个核心文件），**默认使用智谱AI GLM-4.6 模型**。

## 🆕 LangChain 1.0+ 主要特性

- **新的 `create_agent` API**: 替代了旧版本的 `createReactAgent`
- **架构极简化**: 从75+文件简化到5个核心文件
- **同步设计**: 全面采用同步架构，消除异步调用问题
- **伦理数据约束**: 绝不编造虚假天气数据
- **统一数据获取**: 直接API调用，避免文本解析数据丢失
- **多模型支持**: 支持智谱AI、Anthropic Claude、OpenAI GPT

## 📁 项目文件（简化架构）

```
src/
├── agent.py                    # 🤖 主要智能体实现（简化版）
├── tools/                      # 🛠️ 工具目录
│   ├── weather_tools.py        # 🌤️ 天气工具集
│   ├── fishing_tools.py        # 🎣 钓鱼工具集（伦理约束）
│   ├── basic_tools.py          # ⚙️ 基础工具集
│   └── __init__.py             # 工具导出
├── utils/                      # 🔧 工具类目录
│   ├── api_client.py           # 📡 统一API客户端
│   ├── coordinate_utils.py     # 📍 坐标工具
│   ├── cache.py                # 💾 简化缓存系统
│   └── __init__.py             # 工具类导出
└── docs/                       # 📚 项目文档
    ├── AGENT_README.md         # 本文档
    ├── QUICK_START.md          # 快速开始指南
    └── PROJECT_STATUS.md       # 项目状态
```

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 设置环境变量

创建 `.env` 文件并配置 API 密钥：

```env
# 智谱AI (默认使用，当前已过期需要更新)
ANTHROPIC_AUTH_TOKEN=your-zhipu-api-token-here

# 彩云天气 API (正常工作)
CAIYUN_API_KEY=your-caiyun-api-key-here

# 高德地图 API (正常工作)
AMAP_API_KEY=your-amap-api-key-here

# 其他可选模型
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# 伦理数据约束配置
FISHING_ENABLE_FAKE_DATA=false
```

### 3. 获取API密钥

**智谱AI API** (当前过期):
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册并登录账号
3. 在控制台获取 API Token
4. 将 Token 设置为 `ANTHROPIC_AUTH_TOKEN` 环境变量

**彩云天气API** (正常工作):
1. 访问 [彩云天气开发者平台](https://caiyunapp.com/)
2. 注册并创建应用
3. 获取 API Key
4. 设置为 `CAIYUN_API_KEY`

**高德地图API** (正常工作):
1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册并创建应用
3. 获取 API Key
4. 设置为 `AMAP_API_KEY`

### 4. 启动简化智能体

设置好 API 密钥后，运行简化架构的主程序：

```bash
uv run python src/agent.py
```

### 5. 健康检查

验证系统状态：

```bash
uv run python -c "
from agent import create_optimized_fishing_agent
agent = create_optimized_fishing_agent()
health = agent.health_check()
print('系统状态:', health['status'])
for check, status in health['checks'].items():
    print(f'  {check}: {status}')
"
```

## 🛠️ 智能体工具（简化架构）

智能体内置了以下核心工具：

### 🌤️ 天气工具集 (weather_tools.py)
1. **get_current_weather(location)** - 获取实时天气信息（真实API数据）
2. **get_weather_forecast(location, days)** - 获取天气预报（1-7天）
3. **get_weather_by_date(location, date_str)** - 获取指定日期天气

### 🎣 钓鱼工具集 (fishing_tools.py)
1. **query_fishing_recommendation(location, date)** - 智能钓鱼推荐（伦理约束）
2. **analyze_fishing_conditions(weather_data)** - 钓鱼条件分析
3. **calculate_fish_activity(weather_data)** - 鱼类活跃度计算
4. **get_fishing_insights(location, days)** - 多天钓鱼洞察

### ⚙️ 基础工具集 (basic_tools.py)
1. **get_current_time()** - 获取当前时间
2. **calculate(expression)** - 数学表达式计算
3. **get_location_coordinates(location)** - 位置坐标查询
4. **get_fishing_season_advice(location)** - 季节性钓鱼建议

## 🤖 支持的模型

### 智谱AI (默认)
- **模型**: GLM-4.6
- **环境变量**: `ANTHROPIC_AUTH_TOKEN`
- **特点**: 中文优化，性价比高

### Anthropic Claude
- **模型**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- **环境变量**: `ANTHROPIC_API_KEY`
- **特点**: 推理能力强，对话质量高

### OpenAI GPT
- **模型**: GPT-4o-mini
- **环境变量**: `OPENAI_API_KEY`
- **特点**: 速度快，成本较低

### 切换模型

使用新的简化创建函数切换模型：

```python
from agent import create_optimized_fishing_agent

# 使用智谱AI (默认)
agent = create_optimized_fishing_agent(model_provider="zhipu")

# 使用 Claude
agent = create_optimized_fishing_agent(model_provider="anthropic")

# 使用 OpenAI
agent = create_optimized_fishing_agent(model_provider="openai")

# 使用配置创建
agent = create_optimized_fishing_agent(
    model_provider="zhipu",
    enable_logging=True,
    timeout=60
)

# 获取统计信息
stats = agent.get_llm_stats()
print(f"模型调用次数: {stats['total_model_calls']}")
print(f"成功率: {stats['success_rate']:.1f}%")
```

## 💡 使用示例

### 基本钓鱼查询

```
用户: 现在几点了？
智能体: 当前时间: 2025-11-19 19:30:15 (星期二)

用户: 帮我计算 15 * 8
智能体: 计算结果: 15 * 8 = 120

用户: 明天余杭区钓鱼怎么样？
智能体: 根据最新天气数据分析，为您整理出明天余杭区的钓鱼建议：
**天气概况：**- 天气状况：CLEAR_NIGHT- 温度范围：8°C ~ 10°C- 风速：4.7 m/s
**钓鱼评分：** 78/100 (良好)
**推荐时段：** 早上6-8点、傍晚18-20点
```

### 复杂钓鱼查询

```
用户: 今天是什么日子？如果明天适合钓鱼的话，提醒我准备装备
智能体: 当前时间: 2025-11-19 19:30:15 (星期二)。今天是星期二。关于明天的钓鱼安排，我查询了余杭区的天气预报：
温度8-10°C，晴朗夜间，风力适中，钓鱼评分78分，属于良好条件。建议您准备：
- 装备：轻量级钓竿，小号钩子
- 饵料：适合低温活饵
- 时间：建议早6-8点或晚18-20点
- 服装：保暖外套，帽子手套
```

### 天气查询

```
用户: 杭州未来三天天气如何？
智能体: 🌤️ 杭州 3天天气预报：
第1天: 11-20 周三
   🌡️ 温度: 8.2°C ~ 15.6°C (平均11.9°C)
   ☁️ 天气: 晴朗

第2天: 11-21 周四
   🌡️ 温度: 9.1°C ~ 16.3°C (平均12.7°C)
   ☁️ 天气: 多云

第3天: 11-22 周五
   🌡️ 温度: 10.5°C ~ 17.8°C (平均14.2°C)
   ☁️ 天气: 阴天
```

## 🔧 代码特点（简化架构）

### 使用最新 LangChain 1.0+ API

```python
# 简化架构 - 无服务管理器复杂层
from agent import create_optimized_fishing_agent

# 一行创建智能体
agent = create_optimized_fishing_agent(model_provider="zhipu")

# 直接调用
result = agent.run("明天余杭区钓鱼怎么样？")

# 标准调用格式（与原版兼容）
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "杭州天气如何？"}
    ]
})
```

### 现代工具定义（直接@tool装饰器）

```python
from langchain.tools import tool

@tool
def get_current_weather(location: str) -> str:
    """获取指定位置的当前天气信息"""
    # 直接调用API客户端，无中间层
    weather_client = get_weather_client()
    coords = get_coordinates(location)
    weather_data = weather_client.get_realtime_weather(coords[0], coords[1])
    return _format_weather_response(weather_data, location)
```

### 伦理数据约束实现

```python
def _calculate_fishing_score(weather_data: Dict[str, Any]) -> Dict[str, float]:
    """计算钓鱼评分 - 严格模式，不使用虚假数据"""

    # 严格验证天气数据完整性
    required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
    missing_fields = [field for field in required_fields if weather_data.get(field) is None]

    if missing_fields:
        logger.error(f"天气数据不完整，缺少字段: {missing_fields}")
        # 返回所有0分，表示无法计算（绝不编造数据）
        return {
            'overall': 0.0,
            'data_quality': 'incomplete'
        }

    # 只有数据完整时才进行评分计算
    return _calculate_valid_score(weather_data)
```

### 统一API客户端

```python
from utils.api_client import get_weather_client, get_geocoding_client

# 统一的API客户端，支持缓存和错误处理
weather_client = get_weather_client()
geocoding_client = get_geocoding_client()

# 直接调用，无需中间层
weather_data = weather_client.get_hourly_forecast(longitude, latitude, 72)
coord_data = geocoding_client.geocode(location)
```

## 📚 相关文档

- [LangChain 官方文档](https://docs.langchain.com)
- [LangChain 1.0 迁移指南](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [工具开发指南](https://docs.langchain.com/oss/python/contributing/implement-langchain)

## 🧪 测试和调试

### 健康检查和测试

```bash
# 系统健康检查
uv run python -c "
from agent import create_optimized_fishing_agent
agent = create_optimized_fishing_agent()
health = agent.health_check()
print('🏥 系统健康检查:')
print(f'  状态: {health[\"status\"]}')
for check, status in health['checks'].items():
    print(f'  {check}: {status}')
"

# 完整功能测试（需要 API 密钥）
uv run python src/agent.py

# 单独测试工具
uv run python -c "
from tools.fishing_tools import query_fishing_recommendation
print('🎣 钓鱼工具测试:')
result = query_fishing_recommendation('余杭区', '明天')
print(result[:300] + '...')
"
```

### 启用详细日志

```bash
# 创建带详细日志的智能体
uv run python -c "
from agent import create_optimized_fishing_agent
agent = create_optimized_fishing_agent(enable_logging=True)
print('📊 统计信息:', agent.get_llm_stats())
"
```

### 降级模式测试

当API密钥过期时，系统会自动降级：

```bash
# 测试降级机制
ANTHROPIC_AUTH_TOKEN=invalid_token uv run python -c "
from agent import create_optimized_fishing_agent
agent = create_optimized_fishing_agent()
result = agent.run('测试查询')
print('降级模式回复:', result[:100] + '...')
"
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个智能体示例！

## 📄 许可证

本项目仅供学习和参考使用。