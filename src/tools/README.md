# LangChain Tools 工具系统

此目录包含智能钓鱼助手的所有工具模块，基于 **LangChain 1.0+** 的 `@tool` 装饰器实现。

> **注意**：本项目使用 `langchain>=0.3.0`（LangChain 1.0+）。工具通过 `@tool` 装饰器定义，可被 LLM Agent 自动调用。

## 什么是工具（Tools）？

在 LangChain 中，工具是 **可被 Agent 调用执行操作的组件**，用于：

- **扩展 LLM 能力**：让模型能与外部系统交互（API、数据库、文件系统）
- **结构化输入输出**：通过明确的输入模式和类型提示，确保调用正确
- **自动调用决策**：LLM 根据用户意图自动选择合适的工具及参数

工具封装了一个可调用函数和其输入模式（input schema），可以传递给兼容的聊天模型，让模型决定是否调用工具以及使用什么参数。

## 项目工具结构

```
src/tools/
├── __init__.py              # 统一工具接口
├── basic_tools.py           # 基础工具（时间查询等）
├── weather_tools.py         # 天气查询工具
├── fishing_tools.py         # 钓鱼推荐工具（7因子评分）
├── lure_tools.py            # 路亚装备工具（推荐、对比、知识）
├── scoring/                 # 钓鱼评分系统
│   ├── enhanced_scorer.py   # 7因子科学评分算法
│   └── ...
└── lure/                    # 路亚装备子系统
    ├── database.py          # 数据库管理
    ├── recommender.py       # 装备推荐引擎
    ├── comparator.py        # 装备对比引擎
    └── ...
```

## 工具分类

### 1. 基础工具（basic_tools.py）

提供通用基础功能：

| 工具 | 描述 | 触发场景 |
|------|------|----------|
| `get_current_time` | 获取当前时间和日期信息 | 用户询问"现在几点"、"今天星期几" |

**示例**：
```python
from src.tools.basic_tools import get_current_time

result = get_current_time.invoke({})
# 🕐 当前时间信息：
# 📅 日期: 2025年11月26日
# 📆 星期: 星期二
# 🕐 时间: 14:30:00
```

### 2. 天气工具（weather_tools.py）

提供天气查询和预报：

| 工具 | 描述 | 参数 |
|------|------|------|
| `get_weather` | 获取指定位置的天气信息 | `location`（位置）<br>`dates`（日期列表） |

**特性**：
- **单日查询**：详细的当日天气（实时数据）
- **多日预报**：最多7天天气预报（小时级精度）
- **智能降级**：72小时预报 → 日级预报 → 错误提示
- **全国覆盖**：支持3,142+行政区域
- **坐标解析**：自动转换地名为经纬度

**示例**：
```python
from src.tools.weather_tools import get_weather

# 单日查询
result = get_weather.invoke({"location": "杭州", "dates": ["今天"]})

# 多日预报
result = get_weather.invoke({"location": "北京", "dates": ["今天", "明天", "后天"]})

# 默认今天
result = get_weather.invoke({"location": "余杭区"})
```

### 3. 钓鱼推荐工具（fishing_tools.py）

提供科学的钓鱼时间推荐：

| 工具 | 描述 | 参数 |
|------|------|------|
| `query_fishing_recommendation` | 基于7因子评分的钓鱼推荐 | `location`（位置）<br>`dates`（日期列表） |

**核心特性：7因子科学评分系统**

| 因子 | 权重 | 评分规则 |
|------|------|----------|
| 🌡️ **温度** | 30% | 最适温度15-25°C<br>10-30°C可钓<br>超出范围不适宜 |
| ☁️ **天气** | 20% | 多云/阴天最佳<br>小雨次之<br>大雨/雷暴不适宜 |
| 💨 **风力** | 15% | 1-2级理想<br>3-4级可接受<br>5级以上不适宜 |
| 📊 **气压** | 15% | 高压/稳定最佳<br>低压/快速下降不适宜 |
| 💧 **湿度** | 10% | 60-80%理想<br>50-90%可接受 |
| 🌸 **季节** | 5% | 春秋最佳<br>夏冬次之 |
| 🌙 **月相** | 5% | 新月/满月最佳<br>上弦/下弦次之 |

**动态趋势分析**：
- 识别"黄金钓鱼时段"（连续多小时高分）
- 温度趋势：升温/降温/稳定
- 气压趋势：上升/下降/稳定
- 给出最佳作钓时间段建议

**示例**：
```python
from src.tools.fishing_tools import query_fishing_recommendation

# 单日推荐
result = query_fishing_recommendation.invoke({
    "location": "杭州",
    "dates": ["今天"]
})

# 多日推荐
result = query_fishing_recommendation.invoke({
    "location": "西湖区",
    "dates": ["明天", "后天", "大后天"]
})
```

**输出示例**：
```markdown
🎣 杭州 今天 钓鱼推荐报告

## 综合评分: 78分 (适宜)

### 因子详情
- 🌡️ 温度: 85分 (18°C, 接近理想温度)
- ☁️ 天气: 90分 (多云, 理想条件)
- 💨 风力: 70分 (3级, 可接受)
- 📊 气压: 80分 (1015hPa, 稳定高压)
- 💧 湿度: 75分 (65%, 舒适区间)
- 🌸 季节: 90分 (春季, 最佳季节)
- 🌙 月相: 70分 (上弦月, 较佳)

### 🌟 黄金时段
- **上午 6:00-10:00**: 85分 (温度适宜，气压稳定)
- **下午 16:00-18:00**: 82分 (光线柔和，鱼类活跃)

### 📋 建议
✅ 今天是适宜钓鱼的好日子
✅ 推荐上午6-10点作钓，温度和光线理想
✅ 气压稳定，鱼口较好
⚠️ 注意下午风力可能增强
```

### 4. 路亚装备工具（lure_tools.py）

提供路亚装备推荐、对比、知识查询和图片识别：

| 工具 | 描述 | 使用场景 |
|------|------|----------|
| `recommend_equipment` | 装备推荐（买什么） | 购买建议、选择推荐 |
| `compare_equipment` | 装备对比（比哪个） | 比较产品、选择决策 |
| `lookup_fishing_knowledge` | 知识查询（学什么） | 学习鱼类/钓组/技巧 |
| `identify_from_image` | 图片识别（看什么） | 识别装备/鱼种 |

#### 4.1 装备推荐（recommend_equipment）

**触发关键词**：推荐、买、选、预算、性价比、适合新手、入门

**参数**：
```python
recommend_equipment(
    equipment_type: str,          # 装备类型：鱼竿/渔轮/鱼线/拟饵/套装
    budget: Optional[float],      # 预算金额（元）
    specifications: Optional[str], # 规格要求JSON字符串
    target_fish: Optional[str],   # 目标鱼种
    scenario: Optional[str],      # 使用场景
    user_level: Optional[str]     # 用户水平：新手/进阶/高手
)
```

**推荐算法评分系统**：
- **价格匹配** (35%)：越接近预算越高分
- **规格匹配** (35%)：硬度、长度等参数匹配度
- **品牌声誉** (15%)：大品牌加分
- **用户水平** (15%)：新手推荐入门款，高手推荐专业款

**示例**：
```python
from src.tools.lure_tools import recommend_equipment

# 推荐鱼竿
result = recommend_equipment.invoke({
    "equipment_type": "鱼竿",
    "budget": 500,
    "specifications": '{"硬度": "ML", "长度": "2.1m"}',
    "target_fish": "鲈鱼",
    "user_level": "新手"
})

# 推荐套装
result = recommend_equipment.invoke({
    "equipment_type": "套装",
    "budget": 1000,
    "user_level": "新手",
    "target_fish": "翘嘴"
})
```

**输出示例**：
```markdown
# 路亚鱼竿推荐报告

## 需求分析
- **装备类型**: 鱼竿
- **预算范围**: ¥500
- **硬度要求**: ML
- **目标鱼种**: 鲈鱼
- **用户水平**: 新手

## 推荐产品（共3款）

### 1. 禧玛诺路亚竿 SLX 264ML

![禧玛诺路亚竿](image_url)

**综合评分**: 92.5/100

| 参数 | 值 |
|------|-----|
| 品牌 | 禧玛诺 |
| 价格 | ¥468 |
| 硬度 | ML |
| 长度 | 2.1m |
| 适用鱼种 | 鲈鱼、鳜鱼 |

**推荐理由**: 价格适中 · 规格完全匹配 · 大品牌质量保证 · 适合新手入门

<details>
<summary>评分明细</summary>

| 维度 | 得分 | 权重 |
|------|------|------|
| 价格匹配 | 95.0 | 35% |
| 规格匹配 | 100.0 | 35% |
| 品牌声誉 | 90.0 | 15% |
| 水平匹配 | 85.0 | 15% |

</details>

---

## 选购建议
1. 新手建议选择大品牌，质量和售后有保障
2. 不必追求顶级配置，先熟悉手感再升级
```

#### 4.2 装备对比（compare_equipment）

**触发关键词**：对比、比较、哪个好、区别、差异、VS、和...比

**参数**：
```python
compare_equipment(
    equipment_names: str,         # 装备名称，逗号分隔（2-5个）
    compare_aspects: Optional[str] # 对比维度，逗号分隔
)
```

**对比维度**：
- 价格：价格差异和性价比
- 性能：参数规格对比
- 适用场景：适合的钓场和目标鱼种
- 品牌：品牌定位和口碑
- 综合评价：优缺点总结

**示例**：
```python
from src.tools.lure_tools import compare_equipment

# 对比两款鱼竿
result = compare_equipment.invoke({
    "equipment_names": "禧玛诺毒牙264ML, 达亿瓦月下美人76ML",
    "compare_aspects": "价格, 性能, 适用场景"
})
```

#### 4.3 知识查询（lookup_fishing_knowledge）

**触发关键词**：什么是、怎么用、怎么绑、习性、教程、介绍、特点、方法

**支持查询类型**：
- **鱼类知识**："鲈鱼习性"、"翘嘴什么时候活跃"
- **钓组知识**："德州钓组怎么绑"、"无铅钓组用法"
- **技巧知识**："水草区怎么作钓"、"冬季路亚技巧"

**参数**：
```python
lookup_fishing_knowledge(
    topic: str,                # 查询主题
    include_images: bool = True # 是否包含图解
)
```

**示例**：
```python
from src.tools.lure_tools import lookup_fishing_knowledge

# 查询鱼类知识
result = lookup_fishing_knowledge.invoke({
    "topic": "鲈鱼习性"
})

# 查询钓组知识
result = lookup_fishing_knowledge.invoke({
    "topic": "德州钓组怎么绑",
    "include_images": True
})
```

#### 4.4 图片识别（identify_from_image）

**触发关键词**：这是什么、识别、帮我看看、图片里、照片中

**支持识别**：
- 拟饵类型和品牌
- 钓组配置
- 鱼种识别
- 装备型号

**参数**：
```python
identify_from_image(
    image_path: str,           # 图片路径（本地）
    question: Optional[str]    # 具体问题
)
```

**示例**：
```python
from src.tools.lure_tools import identify_from_image

result = identify_from_image.invoke({
    "image_path": "/tmp/unknown_lure.jpg",
    "question": "这是什么饵？"
})
```

## 创建工具

### 基础工具定义

使用 `@tool` 装饰器创建工具：

```python
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """搜索客户数据库中匹配查询的记录。

    Args:
        query: 要搜索的关键词
        limit: 返回的最大结果数
    """
    return f"找到 {limit} 条关于 '{query}' 的结果"
```

**关键规则**：
- ✅ **类型提示是必需的**：定义工具的输入模式
- ✅ **Docstring 很重要**：帮助 LLM 理解何时使用工具
- ✅ **返回字符串**：工具输出应为字符串格式

### 自定义工具属性

#### 自定义工具名称

```python
@tool("web_search")  # 自定义名称
def search(query: str) -> str:
    """搜索互联网信息。"""
    return f"搜索结果：{query}"

print(search.name)  # web_search
```

#### 自定义工具描述

```python
@tool("calculator", description="执行算术计算。用于任何数学问题。")
def calc(expression: str) -> str:
    """评估数学表达式。"""
    return str(eval(expression))
```

### 高级模式定义

使用 Pydantic 模型定义复杂输入：

```python
from pydantic import BaseModel, Field
from typing import Literal

class WeatherInput(BaseModel):
    """天气查询的输入模式。"""
    location: str = Field(description="城市名称或坐标")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="温度单位偏好"
    )
    include_forecast: bool = Field(
        default=False,
        description="包含5天预报"
    )

@tool(args_schema=WeatherInput)
def get_weather(
    location: str,
    units: str = "celsius",
    include_forecast: bool = False
) -> str:
    """获取当前天气和可选预报。"""
    temp = 22 if units == "celsius" else 72
    result = f"{location}当前天气：{temp}度{units[0].upper()}"
    if include_forecast:
        result += "\n未来5天：晴天"
    return result
```

### 保留参数名称

以下参数名称是保留的，不能用作工具参数：

| 参数名 | 用途 |
|--------|------|
| `config` | 保留给内部传递 `RunnableConfig` |
| `runtime` | 保留给 `ToolRuntime` 参数 |

## 访问运行时上下文

### 为什么需要上下文？

工具在能访问 Agent 状态、运行时上下文和长期记忆时最强大。这使工具能够：
- 做出上下文感知的决策
- 个性化响应
- 跨对话维护信息

### 使用 `ToolRuntime`

通过 `runtime: ToolRuntime` 参数访问所有运行时信息：

```python
from langchain.tools import tool, ToolRuntime

@tool
def summarize_conversation(runtime: ToolRuntime) -> str:
    """总结到目前为止的对话。"""
    messages = runtime.state["messages"]

    human_msgs = sum(1 for m in messages if m.__class__.__name__ == "HumanMessage")
    ai_msgs = sum(1 for m in messages if m.__class__.__name__ == "AIMessage")
    tool_msgs = sum(1 for m in messages if m.__class__.__name__ == "ToolMessage")

    return f"对话包含 {human_msgs} 条用户消息，{ai_msgs} 条AI响应，{tool_msgs} 条工具结果"
```

**重要**：`runtime` 参数对模型隐藏，不会出现在工具模式中。

### 访问状态

```python
@tool
def get_user_preference(
    pref_name: str,
    runtime: ToolRuntime
) -> str:
    """获取用户偏好值。"""
    preferences = runtime.state.get("user_preferences", {})
    return preferences.get(pref_name, "未设置")
```

### 更新状态

使用 `Command` 更新 Agent 状态或控制执行流：

```python
from langgraph.types import Command
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

@tool
def clear_conversation() -> Command:
    """清除对话历史。"""
    return Command(
        update={
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
        }
    )

@tool
def update_user_name(
    new_name: str,
    runtime: ToolRuntime
) -> Command:
    """更新用户名称。"""
    return Command(update={"user_name": new_name})
```

### 访问持久化存储（Memory）

通过 `runtime.store` 访问跨对话的持久化数据：

```python
from typing import Any
from langgraph.store.memory import InMemoryStore

@tool
def get_user_info(user_id: str, runtime: ToolRuntime) -> str:
    """查询用户信息。"""
    store = runtime.store
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "未知用户"

@tool
def save_user_info(
    user_id: str,
    user_info: dict[str, Any],
    runtime: ToolRuntime
) -> str:
    """保存用户信息。"""
    store = runtime.store
    store.put(("users",), user_id, user_info)
    return "成功保存用户信息。"
```

### 流式输出

使用 `runtime.stream_writer` 实时输出工具执行进度：

```python
@tool
def get_weather(city: str, runtime: ToolRuntime) -> str:
    """获取指定城市的天气。"""
    writer = runtime.stream_writer

    # 流式输出自定义更新
    writer(f"正在查询城市：{city}")
    writer(f"已获取数据：{city}")

    return f"{city}永远阳光明媚！"
```

## 使用工具

### 在 Agent 中使用

通过 `create_agent()` 的 `tools` 参数传递工具：

```python
from langchain.agents import create_agent
from src.tools import get_all_tools

agent = create_agent(
    model="gpt-4o",
    tools=get_all_tools(),
    system_prompt="你是一个智能钓鱼助手。"
)
```

### 获取特定工具集

```python
from src.tools import (
    get_all_tools,      # 所有工具
    get_basic_tools,    # 基础工具
    get_weather_tools,  # 天气工具
    get_fishing_tools,  # 钓鱼工具
)

# 使用特定工具集
from src.tools.lure_tools import get_lure_tools

agent = create_agent(
    model="gpt-4o",
    tools=get_basic_tools() + get_weather_tools() + get_fishing_tools() + get_lure_tools()
)
```

### 直接调用工具（测试）

```python
from src.tools.weather_tools import get_weather
from src.tools.fishing_tools import query_fishing_recommendation

# 调用天气工具
result = get_weather.invoke({
    "location": "杭州",
    "dates": ["今天", "明天"]
})

# 调用钓鱼推荐工具
result = query_fishing_recommendation.invoke({
    "location": "西湖区",
    "dates": ["明天"]
})
```

## 工具 vs 工具类（Utils）

**重要区别**：

| 特性 | 工具（tools/） | 工具类（utils/） |
|------|----------------|------------------|
| **用途** | LLM Agent 可调用的操作 | 独立辅助功能 |
| **可见性** | Agent 可见并选择 | 内部使用 |
| **典型场景** | 天气查询、装备推荐 | 日期解析、坐标转换 |
| **依赖** | 依赖 LangChain | 独立模块 |

**判断标准**：
- 需要 LLM 自动选择和调用？ → **工具（tools/）**
- 需要暴露给 Agent？ → **工具（tools/）**
- 独立的辅助函数或数据处理？ → **工具类（utils/）**

## 最佳实践

### 1. 工具设计原则

- **单一职责**：每个工具专注做好一件事
- **清晰的描述**：Docstring 应该简洁明了，帮助 LLM 理解何时使用
- **类型安全**：使用类型提示和 Pydantic 模型验证输入
- **错误处理**：优雅处理错误，返回有意义的错误信息

### 2. 性能优化

- **懒加载**：使用函数级导入避免启动延迟
- **缓存**：对频繁查询的数据使用缓存（如坐标解析）
- **降级策略**：提供备选方案（如天气API失败时的降级）

### 3. 用户体验

- **诚实数据**：不生成虚假数据，API失败时诚实告知
- **格式化输出**：使用 Markdown 格式化输出，提升可读性
- **上下文感知**：利用 `ToolRuntime` 提供个性化响应

### 4. 测试

```python
# 单元测试工具
def test_get_weather():
    result = get_weather.invoke({
        "location": "杭州",
        "dates": ["今天"]
    })
    assert "杭州" in result
    assert "温度" in result

# 测试工具列表
def test_all_tools():
    tools = get_all_tools()
    assert len(tools) > 0

    for tool in tools:
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
```

### 5. 文档

- **Docstring 规范**：使用 Google 风格 docstring
- **示例代码**：在 docstring 中提供使用示例
- **参数说明**：详细说明每个参数的含义和格式

## 项目特色工具

### 7因子科学评分系统

`fishing_tools.py` 实现的7因子评分系统是本项目的核心特色：

```python
from src.tools.scoring.enhanced_scorer import (
    calculate_fishing_score,
    calculate_temperature_score,
    calculate_weather_score,
    calculate_wind_score,
    calculate_pressure_score,
    calculate_humidity_score,
    calculate_seasonal_score,
    calculate_moon_phase_score,
    analyze_pressure_trend,
    identify_golden_periods
)
```

**评分流程**：
1. 获取天气数据（温度、湿度、气压、风力等）
2. 计算7个因子的独立评分
3. 加权求和得到综合评分
4. 动态趋势分析（气压趋势、温度趋势）
5. 识别黄金钓鱼时段

### 路亚装备智能推荐

`lure_tools.py` 实现的装备推荐系统特色：

- **多维度评分**：价格、规格、品牌、用户水平
- **智能匹配**：根据目标鱼种和场景推荐
- **套装组合**：自动配置兼容的竿轮线组合
- **图片识别**：基于图像的装备识别

## 参考资源

- [LangChain Tools 官方文档](https://python.langchain.com/docs/langchain/tools/)
- [Tool API Reference](https://reference.langchain.com/python/langchain/tools/)
- [Built-in Tools](https://python.langchain.com/docs/integrations/tools/)
- [LangChain Agents 文档](https://python.langchain.com/docs/langchain/agents)

## 工具开发检查清单

创建新工具时，确保：

- [ ] 使用 `@tool` 装饰器
- [ ] 提供完整的类型提示
- [ ] 编写清晰的 docstring（包括参数说明）
- [ ] 处理错误并返回有意义的信息
- [ ] 返回格式化的字符串结果
- [ ] 添加到工具列表（如 `BASIC_TOOLS`）
- [ ] 更新 `__init__.py` 的导出
- [ ] 编写单元测试
- [ ] 更新本 README 文档
