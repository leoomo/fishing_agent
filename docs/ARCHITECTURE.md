# 智能钓鱼助手 - 项目架构文档

**版本**: v3.0.2.1
**分支**: feature/llm-optimization
**目标**: 为大模型(LLM)提供完整的项目架构理解指南

---

## 📋 目录

1. [项目概览与架构哲学](#1-项目概览与架构哲学)
2. [系统架构](#2-系统架构)
3. [模块组织](#3-模块组织)
4. [核心组件分析](#4-核心组件分析)
5. [开发模式](#5-开发模式)
6. [数据流与状态管理](#6-数据流与状态管理)
7. [配置与部署](#7-配置与部署)
8. [LLM导航指南](#8-llm导航指南)

---

## 1. 项目概览与架构哲学

### 🎯 项目定位
智能钓鱼助手是一个基于 **LangChain 1.0+** 的智能代理系统，专门为路亚钓鱼爱好者提供：
- **实时天气分析**和钓鱼条件评估
- **7因子科学评分系统**（温度、天气、风力、气压、湿度、季节、月相）
- **动态趋势分析**识别黄金钓鱼时段
- **路亚装备智能推荐**和语义搜索
- **全国覆盖**的3,142+行政区划支持

### 🏗️ 核心架构哲学

#### **零抽象原则 (Zero Abstraction)**
```python
# 直接API调用，无中间层
def get_weather(location: str) -> dict:
    response = requests.get(f"https://api.caiyunapp.com/v2.6/{API_KEY}/{coords}/realtime")
    return response.json()
```

#### **同步优先 (Synchronous Priority)**
- 消除异步复杂性和事件循环问题
- 使用 `requests` 直接进行HTTP调用
- 简化错误处理和调试

#### **工具中心化 (Tool-Centric Design)**
- 清晰分离核心代理逻辑和专用工具
- 每个工具具有单一职责和明确边界
- 统一的工具接口和装饰器模式

#### **诚实数据处理 (Honest Data)**
- 绝不生成虚假或模拟数据
- API失败时透明报告错误
- 提供诚实的降级建议而非编造信息

---

## 2. 系统架构

### 🏛️ 架构层次图

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  main.py   │  │  agent.py   │  │   CLI Demo  │          │
│  │  (交互界面) │  │  (兼容层)   │  │  (演示工具)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    核心代理层                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           FishingAgent (src/fishing_agent/)           │ │
│  │  • ModelFactory (多LLM支持)                           │ │
│  │  • Core Agent (LangChain 1.0+)                       │ │
│  │  • Callback System (统计/验证)                        │ │
│  │  • Prompt Engineering (系统上下文)                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   工具集成层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │基础工具     │  │天气工具     │  │钓鱼工具     │          │
│  │(时间/计算)  │  │(直接API)    │  │(7因子评分)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────────────────────────────┐   │
│  │  路亚工具   │  │        向量存储与知识库             │   │
│  │(装备推荐)   │  │   (ChromaDB + DashScope)          │   │
│  └─────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  工具与支持层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │API客户端    │  │坐标工具     │  │缓存/工具    │          │
│  │(HTTP封装)   │  │(地理编码)   │  │(简单缓存)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   评分系统                               │ │
│  │  • 7因子算法 (温度/天气/风力/气压/湿度/季节/月相)     │ │
│  │  • 趋势分析与动态评分                                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   外部API层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │彩云天气API  │  │高德地图API  │  │DashScope API│          │
│  │(天气服务)   │  │(定位服务)   │  │(LLM+嵌入)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 数据流模式

#### **请求处理流程**
```
用户输入 → 意图识别 → 工具选择 → 参数解析 → API调用
    ↓
数据处理 → 评分计算 → 结果格式化 → 输出验证 → 响应返回
```

#### **工具选择逻辑**
```python
def select_tool(query: str) -> callable:
    query_lower = query.lower()

    if "钓鱼" in query_lower:
        return query_fishing_recommendation  # 包含天气分析
    elif any(kw in query_lower for kw in ["天气", "温度", "下雨"]):
        return get_weather                    # 纯天气查询
    else:
        return get_current_time              # 基础工具
```

---

## 3. 模块组织

### 📁 核心目录结构

```
fishing-agent/
├── src/                           # 源代码根目录
│   ├── agent.py                   # 主代理入口（向后兼容）
│   ├── fishing_agent/             # 核心代理实现
│   │   ├── __init__.py           # 公共API导出
│   │   ├── core.py               # 主要代理类
│   │   ├── model_factory.py      # 多LLM工厂
│   │   ├── prompts.py            # 系统提示词
│   │   └── callbacks.py          # 统计与验证
│   ├── tools/                     # 工具模块
│   │   ├── __init__.py           # 统一工具接口
│   │   ├── basic_tools.py        # 基础工具（时间功能）
│   │   ├── weather_tools.py      # 天气查询工具
│   │   ├── fishing_tools.py      # 钓鱼推荐工具
│   │   ├── lure_tools.py         # 路亚装备工具
│   │   └── lure/                 # 路亚装备完整模块
│   │       ├── embeddings.py     # DashScope嵌入服务
│   │       ├── vector_store.py   # ChromaDB向量存储
│   │       ├── knowledge_search.py # 语义搜索服务
│   │       ├── cli.py           # 向量存储管理CLI
│   │       └── [12个支持文件]    # 数据库/推荐/对比等
│   ├── utils/                     # 工具类和辅助模块
│   │   ├── api_client.py         # HTTP客户端封装
│   │   ├── coordinate_utils.py   # 地理坐标工具
│   │   ├── cache.py              # 简单缓存实现
│   │   ├── date_utils.py         # 日期处理工具
│   │   └── health_check.py       # 系统健康检查
│   ├── tools/scoring/             # 7因子科学评分系统
│   │   └── enhanced_scorer.py    # 增强评分算法
│   ├── data/                      # 数据存储
│   └── tests/                     # 测试套件
├── docs/                          # 项目文档
├── main.py                        # CLI交互入口
└── pyproject.toml                 # 项目配置
```

### 🔧 模块职责边界

#### **`src/fishing_agent/` - 代理核心**
- **`core.py`**: 主代理类，LangChain集成和工具管理
- **`model_factory.py`**: LLM提供商抽象工厂，支持多种模型
- **`prompts.py`**: 系统提示词和上下文管理
- **`callbacks.py`**: 使用统计、性能监控、输出验证

#### **`src/tools/` - 工具模块**
- **`basic_tools.py`**: 通用工具（时间查询、计算等）
- **`weather_tools.py`**: 天气API集成（彩云天气）
- **`fishing_tools.py`**: 钓鱼推荐和7因子评分系统
- **`lure/`**: 路亚装备数据库和语义搜索系统

#### **`src/utils/` - 基础设施**
- **`api_client.py`**: HTTP客户端封装，包含缓存和重试
- **`coordinate_utils.py`**: 地理编码和坐标服务
- **`cache.py`**: 基于TTL的简单内存缓存
- **`date_utils.py`**: 日期解析和格式化工具

### 🎯 入口点与接口

#### **主要入口点**
```python
# 1. CLI交互界面
main.py → 交互式命令行界面

# 2. 编程接口
from src.fishing_agent import FishingAgent
agent = FishingAgent(model_provider="zhipu")

# 3. 向后兼容接口
from src.agent import create_optimized_fishing_agent
```

#### **工具访问模式**
```python
# 统一工具访问
from src.tools import get_all_tools, get_weather_tools

# 直接工具使用
from src.tools.weather_tools import get_current_weather
from src.tools.fishing_tools import query_fishing_recommendation
```

---

## 4. 核心组件分析

### 🤖 FishingAgent核心实现

#### **代理类架构**
```python
class FishingAgent:
    def __init__(self, model_provider="zhipu", timeout=60):
        self.model = ModelFactory.create(model_provider)
        self.tools = get_all_tools()
        self.agent = create_agent(self.model, self.tools, system_prompt)
        self.callback = FishingAgentCallback()  # 统计追踪

    def run(self, user_input: str) -> str:
        # LangChain代理执行与回调
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config={"callbacks": [self.callback]}
        )
        return self._extract_response(result)
```

**关键特性**:
- **零中间件**: 直接创建LangChain代理
- **多LLM支持**: 工厂模式管理模型提供商
- **智能工具选择**: 基于查询意图自动路由
- **输出验证**: 保持钓鱼报告的工具格式化
- **优雅降级**: 诚实报告失败并提供回退方案

### 🛠️ 工具系统架构

#### **工具分类体系**
```python
# 具有清晰边界的工具类别
BASIC_TOOLS = [get_current_time]           # 通用工具
WEATHER_TOOLS = [get_weather]              # 纯天气查询
FISHING_TOOLS = [query_fishing_recommendation] # 钓鱼+天气分析
LURE_TOOLS = [query_lure_recommendation]  # 装备数据库
```

#### **工具装饰器模式**
```python
@tool
def query_fishing_recommendation(
    location: str,
    date: str = None,
    time_period: str = None
) -> str:
    """
    查询钓鱼时间推荐，基于天气条件分析最佳钓鱼时间

    Args:
        location: 地区名称
        date: 日期字符串
        time_period: 时间段限制（白天/晚上/上午/下午）
    """
```

### 📊 评分算法系统

#### **7因子科学评分**
```python
def calculate_fishing_score(weather_data, location_data) -> dict:
    scores = {
        'temperature': calculate_temperature_score(weather_data['temp']),      # 25%权重
        'weather': calculate_weather_score(weather_data['condition']),        # 20%权重
        'wind': calculate_wind_score(weather_data['wind_speed']),            # 15%权重
        'pressure': analyze_pressure_trend(weather_data['pressure_history']), # 15%权重
        'humidity': calculate_humidity_score(weather_data['humidity']),        # 10%权重
        'seasonal': calculate_seasonal_score(weather_data['month']),          # 5%权重
        'lunar': calculate_lunar_score(lunar_phase)                           # 5%权重
    }
    return normalize_and_weight_scores(scores)
```

**算法特性**:
- **动态趋势分析**: 气压/温度变化对钓鱼活跃度的影响
- **季节适应**: 月度/每周钓鱼模式
- **月相集成**: 月相周期对鱼类活动的影响
- **权重评分**: 不同条件的最优平衡

### 🔍 向量存储与知识库

#### **路亚装备系统**
```python
# ChromaDB + DashScope集成
class VectorStore:
    def __init__(self):
        self.embedding_model = DashScopeEmbedding("text-embedding-v3")
        self.chroma_client = ChromaClient()

    def search_equipment(self, query: str) -> List[Equipment]:
        vector = self.embedding_model.embed_query(query)
        results = self.chroma_client.similarity_search(vector)
        return rank_by_relevance(results, query)
```

**核心组件**:
- **语义搜索**: 基于钓鱼场景的装备匹配
- **知识库**: 鱼类行为、路亚类型、钓鱼技巧
- **CLI管理**: 索引重建、状态监控、搜索测试
- **懒加载**: 首次搜索时自动建立索引

### 🌐 LLM集成模式

#### **多提供商支持**
```python
# 统一的LLM提供商接口
class ModelFactory:
    PROVIDERS = {
        "zhipu": ChatOpenAI,      # GLM模型
        "qwen": ChatTongyi,       # 通义千问
        "doubao": ChatOpenAI,     # 豆包模型
        "openai": ChatOpenAI      # GPT模型
    }

    @classmethod
    def create(cls, provider: str, timeout: int = 60) -> BaseChatModel:
        if provider == "zhipu":
            return ChatOpenAI(
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
                model="glm-4-flash",
                timeout=timeout
            )
        # ... 其他提供商配置
```

#### **提示词工程**
```python
FISHING_SYSTEM_PROMPT = """
你是一个专业的智能钓鱼助手，具备以下核心能力：

🎯 专业领域:
- 路亚钓鱼天气分析和条件评估
- 7因子科学评分系统（温度/天气/风力/气压/湿度/季节/月相）
- 动态趋势分析识别黄金钓鱼时段
- 基于地理位置的个性化钓鱼建议
- 路亚装备智能匹配和推荐

🛠️ 核心工具:
1. get_current_time - 获取时间信息
2. get_weather_forecast - 获取多日天气预报
3. get_weather_by_date - 查询指定日期天气
4. query_fishing_recommendation - 智能钓鱼推荐分析（核心）
5. query_lure_recommendation - 路亚装备推荐

📊 决策原则:
- 钓鱼查询 → 使用 query_fishing_recommendation（已包含天气分析）
- 纯天气查询 → 使用天气工具
- 时间查询 → 使用基础工具
- 避免冗余工具调用

请根据用户查询，选择最合适的工具提供准确的钓鱼建议。
"""
```

---

## 5. 开发模式

### 🏭 工厂模式 (Factory Pattern)

#### **多LLM提供商管理**
```python
class ModelFactory:
    PROVIDERS = {
        "zhipu": {
            "class": ChatOpenAI,
            "config": {
                "base_url": "https://open.bigmodel.cn/api/paas/v4/",
                "model": "glm-4-flash"
            }
        },
        "qwen": {
            "class": ChatTongyi,
            "config": {"model": "qwen-plus"}
        }
    }

    @classmethod
    def create(cls, provider: str) -> BaseChatModel:
        provider_config = cls.PROVIDERS[provider]
        return provider_config["class"](**provider_config["config"])
```

### 🛠️ 工具模式 (Tool Pattern)

#### **LangChain工具集成**
```python
# 直接工具装饰，边界清晰
@tool
def get_weather_by_date(location: str, date: str = None) -> str:
    """获取指定日期的天气预报"""
    # 工具实现

@tool
def query_fishing_recommendation(location: str, date: str = None) -> str:
    """钓鱼推荐查询，包含7因子评分"""
    # 工具实现
```

### 🎯 策略模式 (Strategy Pattern)

#### **模块化评分组件**
```python
class ScoringStrategy:
    def calculate_score(self, data: dict) -> float:
        raise NotImplementedError

class TemperatureScoring(ScoringStrategy):
    def calculate_score(self, temperature: float) -> float:
        # 温度评分逻辑
        if 10 <= temperature <= 25:
            return 90 + (temperature - 10) * 2
        # 其他温度区间处理

class PressureScoring(ScoringStrategy):
    def calculate_score(self, pressure_data: list) -> float:
        # 气压趋势分析逻辑
        trend = analyze_pressure_trend(pressure_data)
        return base_score * trend['multiplier']
```

### 🔄 API弹性模式

#### **优雅降级策略**
```python
def get_weather_with_fallback(location: str) -> dict:
    try:
        return weather_api.get_realtime_weather(location)
    except APIError as e:
        # 诚实报告失败，不提供虚假数据
        return {
            'status': 'api_error',
            'message': f'天气服务暂时不可用: {str(e)}',
            'fallback_advice': '建议关注当地天气预报，选择天气条件较好的时候出行。'
        }
```

---

## 6. 数据流与状态管理

### 📊 请求处理管道

#### **完整数据流**
```python
def process_fishing_query(user_input: str) -> str:
    # 步骤1: 意图识别
    intent = analyze_intent(user_input)

    # 步骤2: 参数提取
    location = extract_location(user_input)
    date = extract_date(user_input) or "明天"

    # 步骤3: 工具选择
    if intent == "fishing":
        tool = query_fishing_recommendation
    elif intent == "weather":
        tool = get_weather_by_date
    else:
        tool = get_current_time

    # 步骤4: 数据获取
    coords = coordinate_utils.get_coordinates(location)
    weather_data = weather_api.get_weather(coords, date)

    # 步骤5: 评分计算
    if intent == "fishing":
        scores = calculate_fishing_scores(weather_data, date)
        recommendation = generate_fishing_recommendation(scores, weather_data)

    # 步骤6: 响应格式化
    return format_response(recommendation if intent == "fishing" else weather_data)
```

### 💾 缓存策略

#### **TTL缓存实现**
```python
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str, ttl: int = 600) -> Optional[Any]:
        if key in self.cache:
            if time.time() - self.timestamps[key] < ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self.cache[key] = value
        self.timestamps[key] = time.time()
```

#### **缓存配置**
```python
CACHE_CONFIG = {
    'realtime_weather': 600,      # 10分钟
    'hourly_forecast': 1800,      # 30分钟
    'coordinates': 86400,         # 24小时
    'lure_embeddings': 604800,   # 7天
}
```

### 🔗 外部API集成

#### **主要API依赖**
```python
# 必需API (Mandatory)
REQUIRED_APIS = {
    'DASHSCOPE_API_KEY': {
        'purpose': 'LLM + 嵌入服务',
        'provider': '阿里云DashScope',
        'features': ['对话生成', '文本嵌入']
    },
    'CAIYUN_API_KEY': {
        'purpose': '天气服务',
        'provider': '彩云天气',
        'features': ['实时天气', '72小时预报']
    },
    'AMAP_API_KEY': {
        'purpose': '定位服务',
        'provider': '高德地图',
        'features': ['地理编码', '坐标查询']
    }
}

# 可选API (Optional)
OPTIONAL_APIS = {
    'ANTHROPIC_AUTH_TOKEN': {
        'purpose': '替代LLM',
        'provider': '智谱AI GLM',
        'features': ['GLM-4模型']
    },
    'OPENAI_API_KEY': {
        'purpose': '替代LLM',
        'provider': 'OpenAI',
        'features': ['GPT模型']
    }
}
```

### ⚠️ 错误处理与回退

#### **分层错误处理**
```python
def api_call_with_retry(url: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                return {'error': 'timeout', 'message': 'API请求超时'}
            time.sleep(2 ** attempt)  # 指数退避
        except requests.exceptions.HTTPError as e:
            return {'error': 'http_error', 'message': f'HTTP错误: {e}'}
        except Exception as e:
            return {'error': 'unknown', 'message': f'未知错误: {e}'}
```

---

## 7. 配置与部署

### 🔧 环境变量配置

#### **必需配置**
```bash
# .env 文件配置示例

# 核心API服务 (必需)
DASHSCOPE_API_KEY=your-dashscope-api-key      # LLM + 嵌入服务
CAIYUN_API_KEY=your-caiyun-api-key            # 彩云天气API
AMAP_API_KEY=your-amap-api-key                # 高德地图API

# LLM提供商选择 (可选，默认使用zhipu)
ANTHROPIC_AUTH_TOKEN=your-zhipu-token         # 智谱AI GLM
OPENAI_API_KEY=your-openai-key                # OpenAI GPT

# 向量存储配置
VECTOR_EMBEDDING_MODEL=text-embedding-v3      # 嵌入模型 (v2/v3)
VECTOR_AUTO_INDEX=true                        # 懒加载索引

# 缓存配置
CACHE_ENABLED=true                            # 启用缓存
CACHE_TTL=600                                # 默认缓存时间(秒)
```

### 🧪 开发工作流

#### **环境设置**
```bash
# 1. 依赖安装
uv sync                    # 安装所有依赖

# 2. 环境变量配置
cp .env.example .env       # 复制环境变量模板
# 编辑 .env 文件，填入实际API密钥

# 3. 验证安装
uv run python -c "from src.tools import get_all_tools; print(f'工具数量: {len(get_all_tools())}')"

# 4. 运行应用
uv run python main.py      # 启动交互式CLI
```

#### **测试执行**
```bash
# 运行所有测试
uv run pytest src/tests/

# 运行特定测试套件
uv run pytest src/tests/scoring/test_enhanced_scorer.py -v  # 7因子评分测试
uv run python src/tests/test_time_period_intent.py -v       # 时间段意图测试

# 向量存储管理
uv run python -m src.tools.lure.cli status     # 查看索引状态
uv run python -m src.tools.lure.cli rebuild   # 重建向量索引
```

### 🛠️ CLI管理工具

#### **向量存储管理**
```bash
# 状态查看
uv run python -m src.tools.lure.cli status
# 输出: 索引状态、文档数量、向量维度等

# 重建索引
uv run python -m src.tools.lure.cli rebuild --force
# 强制重建所有向量索引

# 搜索测试
uv run python -m src.tools.lure.cli search "鲈鱼习性" --type fish --top-k 3
# 测试语义搜索功能

# 配置查看
uv run python -m src.tools.lure.cli config
# 查看当前配置信息
```

#### **系统健康检查**
```bash
# 运行健康检查
uv run python -c "
from src.utils.health_check import HealthChecker
checker = HealthChecker()
status = checker.check_all()
print(f'系统状态: {status}')
"
```

### 📦 项目结构验证

#### **快速验证脚本**
```bash
#!/bin/bash
# verify_setup.sh - 项目设置验证

echo "🚀 智能钓鱼助手架构验证"
echo "========================"

# 1. 环境检查
echo "1. Python环境..."
uv run python --version

# 2. 依赖检查
echo "2. 依赖检查..."
uv run python -c "
import sys
required_modules = ['langchain', 'requests', 'chromadb']
for module in required_modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        print(f'❌ {module} - 未安装')
"

# 3. 工具加载检查
echo "3. 工具系统..."
uv run python -c "
from src.tools import get_all_tools
tools = get_all_tools()
print(f'✅ 工具数量: {len(tools)}')
for tool in tools:
    print(f'  - {tool.name}')
"

# 4. API配置检查
echo "4. API配置..."
uv run python -c "
import os
required_keys = ['DASHSCOPE_API_KEY', 'CAIYUN_API_KEY', 'AMAP_API_KEY']
for key in required_keys:
    status = '✅' if os.getenv(key) else '❌'
    print(f'{status} {key}')
"

echo "✅ 验证完成"
```

---

## 8. LLM导航指南

### 🎯 LLM理解辅助

#### **代码理解优化**
1. **清晰模块边界**: 每个模块具有单一、明确定义的职责
2. **一致模式**: 工厂模式、工具模式、策略模式贯穿项目
3. **全面文档**: 文档字符串解释目的和用法
4. **最小抽象**: 直接API调用减少复杂性
5. **类型提示**: 完整的类型支持改善IDE辅助

#### **关键文件导航**
```python
# LLM修改项目时的关键入口点

# 1. 了解工具系统
src/tools/__init__.py           # 统一工具接口
src/tools/basic_tools.py        # 基础工具示例
src/tools/fishing_tools.py      # 核心业务逻辑

# 2. 理解代理架构
src/fishing_agent/core.py       # 主要代理类
src/fishing_agent/model_factory.py  # LLM抽象
src/fishing_agent/prompts.py    # 系统提示词

# 3. 掌握评分算法
src/tools/scoring/enhanced_scorer.py  # 7因子算法

# 4. 扩展功能
src/tools/lure/knowledge_search.py    # 语义搜索
src/utils/coordinate_utils.py         # 地理工具
```

### 🚀 开发效率模式

#### **统一工具接口**
```python
# LLM添加新工具的标准模式
from langchain_core.tools import tool

@tool
def your_new_tool(param1: str, param2: int = None) -> str:
    """
    工具描述 - LLM会据此选择工具

    Args:
        param1: 参数描述
        param2: 可选参数描述

    Returns:
        str: 返回结果描述

    Examples:
        >>> your_new_tool("测试", 10)
        "预期返回结果"
    """
    # 工具实现
    return "工具执行结果"

# 在 src/tools/__init__.py 中注册
def get_all_tools():
    tools = [
        get_current_time,
        get_weather,
        query_fishing_recommendation,
        your_new_tool,  # 添加新工具
    ]
    return tools
```

#### **测试驱动开发**
```python
# LLM编写功能时的测试模板
import pytest
from src.your_module import your_function

class TestYourFunction:
    def test_basic_functionality(self):
        """基础功能测试"""
        result = your_function("测试输入")
        assert result is not None
        assert "预期内容" in result

    def test_edge_cases(self):
        """边界情况测试"""
        result = your_function("")
        assert result == "预期默认值"

    def test_error_handling(self):
        """错误处理测试"""
        with pytest.raises(ValueError):
            your_function(invalid_input)
```

### 🔧 扩展点指南

#### **添加新LLM提供商**
```python
# 1. 在 ModelFactory 中添加提供商配置
# src/fishing_agent/model_factory.py

class ModelFactory:
    PROVIDERS = {
        # 现有提供商...
        "new_provider": {
            "class": NewProviderModel,
            "config": {
                "model": "new-model-name",
                "api_key": os.getenv("NEW_PROVIDER_KEY")
            }
        }
    }
```

#### **扩展评分算法**
```python
# 2. 添加新的评分因子
# src/tools/scoring/enhanced_scorer.py

def calculate_new_factor_score(data: dict) -> float:
    """
    新评分因子算法

    Args:
        data: 相关数据字典

    Returns:
        float: 评分结果 (0-100)
    """
    # 实现新因子的评分逻辑
    base_score = 70.0
    # 根据数据调整评分
    return min(100.0, max(0.0, base_score + adjustment))

# 在主评分函数中集成
def calculate_fishing_score(weather_data, location_data) -> dict:
    scores = {
        # 现有因子...
        'new_factor': calculate_new_factor_score(weather_data)
    }
    return normalize_and_weight_scores(scores)
```

#### **增强向量搜索**
```python
# 3. 扩展知识库搜索
# src/tools/lure/knowledge_search.py

class KnowledgeSearchService:
    def search_custom_knowledge(self, query: str, knowledge_type: str) -> List[Result]:
        """
        自定义知识类型搜索

        Args:
            query: 搜索查询
            knowledge_type: 知识类型（如 'techniques', 'locations'）

        Returns:
            List[Result]: 搜索结果列表
        """
        # 实现自定义搜索逻辑
        vector = self.embedding_model.embed_query(query)
        collection = self.vector_store.get_collection(f"{knowledge_type}_collection")
        results = collection.similarity_search(vector)
        return [self._format_result(r) for r in results]
```

### 📝 开发最佳实践

#### **代码组织原则**
1. **单一职责**: 每个函数和类只做一件事
2. **依赖注入**: 通过参数传递依赖，便于测试
3. **错误优先**: 优先处理错误情况，诚实报告失败
4. **文档先行**: 在实现前编写文档和类型提示
5. **测试覆盖**: 为每个新功能编写相应测试

#### **性能优化指南**
```python
# 缓存优化示例
from functools import lru_cache
from src.utils.cache import SimpleCache

# 使用装饰器缓存
@lru_cache(maxsize=128)
def expensive_calculation(param: str) -> float:
    # 计算密集型操作
    return result

# 使用项目缓存
cache = SimpleCache()

def get_weather_cached(location: str) -> dict:
    cached_data = cache.get(f"weather_{location}", ttl=600)
    if cached_data:
        return cached_data

    data = weather_api.get_weather(location)
    cache.set(f"weather_{location}", data)
    return data
```

---

## 🎯 总结

### 架构优势
- **清晰分离**: 模块边界明确，职责单一
- **最小抽象**: 直接API调用，降低复杂性
- **全面工具系统**: 7个核心工具覆盖所有功能域
- **多LLM支持**: 灵活的模型提供商切换
- **科学评分**: 基于证据的7因子算法
- **健全测试**: 46+测试用例覆盖核心功能

### LLM导航价值
本架构文档特别针对LLM理解需求设计，提供：
- **快速定位**: 关键文件和组件的明确指引
- **模式识别**: 一致的设计模式便于理解和扩展
- **扩展指南**: 清晰的扩展点和修改指南
- **最佳实践**: 代码组织和开发规范

### 开发效率
- **统一接口**: `src/tools/__init__.py` 提供单一导入点
- **向后兼容**: 旧版本导入仍然有效
- **模块测试**: 每个组件独立测试套件
- **CLI工具**: 内置管理和调试工具

这个架构优先考虑**可维护性**、**清晰性**和**实用效果**，同时为智能钓鱼助手提供全面功能支持。简化的设计模式使LLM能够轻松理解和修改代码库。

---

**文档版本**: v3.0.2.1
**最后更新**: 2025-11-27
**维护者**: 智能钓鱼助手开发团队