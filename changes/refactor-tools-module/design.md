# Refactor Tools Module - Technical Design Document

## 🏗️ Architecture Overview

### 设计原则

1. **职责分离**: 每个模块有明确的单一职责
2. **命名规范**: 避免与Python标准库和常用库冲突
3. **业务分层**: fishing模块按数据层→分析层→推荐层分层
4. **扩展友好**: 为未来功能预留清晰的扩展空间
5. **向后兼容**: 保持现有功能接口不变

### 核心架构

```
src/tools/
├── basic/           # 基础工具层 - 简单工具，易于添加
├── fishing/         # 钓鱼业务层 - 完整业务模块
│   ├── weather/     # 数据获取层 - 纯天气数据
│   ├── advice/      # 业务分析层 - 钓鱼分析和建议
│   └── equipment/   # 装备推荐层 - 装备推荐和对比
└── core/            # 核心基础设施 - 注册和工厂
```

## 🔧 Technical Decisions

### 1. 命名冲突避免策略

**问题**: Python标准库和常用库名称冲突
**解决方案**: 使用描述性命名

```python
# ❌ 避免的命名
time.py          # 与 time 库冲突
math.py          # 与 math 库冲突
search.py        # 与 search 库冲突
utils.py         # 太通用，容易冲突
registry.py      # 可能与第三方库冲突

# ✅ 采用的命名
time_utils.py    # 明确的工具用途
math_ops.py      # 数学操作
info_search.py   # 信息搜索
helper_functions.py # 辅助函数
tool_registry.py # 工具注册器
```

### 2. 业务分层架构

**设计思路**: 钓鱼业务按数据流分层

```
数据获取层 → 业务分析层 → 装备推荐层
   ↓            ↓            ↓
天气数据    钓鱼适宜度分析  装备推荐
API调用     时间推荐        装备对比
```

**优势**:
- 避免业务重叠
- 减少重复API调用
- 清晰的数据流
- 易于测试和维护

### 3. 工具注册系统设计

**核心组件**:
```python
# tool_registry.py
class ToolRegistry:
    def __init__(self):
        self._basic_tools = []
        self._fishing_tools = []

    def register_basic_tools(self, tools: List):
        self._basic_tools.extend(tools)

    def register_fishing_tools(self, tools: List):
        self._fishing_tools.extend(tools)

    def get_all_tools(self) -> List:
        return self._basic_tools + self._fishing_tools

# 全局实例
tool_registry = ToolRegistry()
```

**自动发现机制**:
```python
# 每个模块的 __init__.py
def get_weather_tools():
    return [current_weather, weather_forecast, datetime_weather]

def get_advice_tools():
    return [fishing_analyzer, time_recommender]

# 主 __init__.py
def get_all_tools():
    from .weather import get_weather_tools
    from .advice import get_advice_tools

    tool_registry.register_fishing_tools(get_weather_tools())
    tool_registry.register_fishing_tools(get_advice_tools())

    return tool_registry.get_all_tools()
```

### 4. 天气数据复用策略

**问题**: 钓鱼工具和天气工具存在重复API调用
**解决方案**: 钓鱼工具内部调用天气工具

```python
# fishing/advice/time_recommender.py
@tool
def analyze_fishing_time(location: str, date: str = None) -> str:
    # 复用天气数据，避免重复API调用
    from ..weather.weather_forecast import query_weather_by_date
    weather_data = query_weather_by_date(location, date)

    # 基于天气数据进行钓鱼分析
    return analyze_fishing_conditions(weather_data)
```

## 📦 Module Design

### Basic Tools 模块

**设计目标**: 简单工具，易于添加
**添加新工具流程**:
1. 在对应文件添加 `@tool` 装饰器函数
2. 更新 `get_basic_tools()` 导出列表
3. 自动被发现和注册

**示例**:
```python
# basic/time_utils.py
@tool
def get_current_time() -> str:
    """获取当前时间和日期"""
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"

@tool
def format_timezone(time_str: str, timezone: str) -> str:
    """时区转换工具"""
    pass
```

### Fishing Business 模块

**Weather 子模块** (数据获取层):
- **职责**: 纯天气数据查询
- **不包含**: 业务逻辑分析
- **输出**: 结构化天气数据

**Advice 子模块** (业务分析层):
- **职责**: 钓鱼相关分析和建议
- **输入**: 天气数据 + 业务参数
- **输出**: 钓鱼建议、时间推荐

**Equipment 子模块** (装备推荐层):
- **职责**: 装备推荐和对比
- **输入**: 钓鱼场景 + 目标鱼种
- **输出**: 装备清单、对比分析

## 🔄 Integration Strategy

### 1. 渐进式迁移

**阶段1**: 新旧并存
```python
# 临时兼容层
def get_all_tools():
    # 尝试新架构
    try:
        from .new_architecture import get_new_tools
        return get_new_tools()
    except ImportError:
        # 回退到旧架构
        from .old_architecture import get_old_tools
        return get_old_tools()
```

**阶段2**: 完全切换
```python
def get_all_tools():
    from .basic import get_basic_tools
    from .fishing import get_fishing_tools
    return get_basic_tools() + get_fishing_tools()
```

### 2. 向后兼容性

**导入别名**:
```python
# src/tools/__init__.py
# 新接口
from .basic import get_basic_tools
from .fishing import get_fishing_tools

# 旧接口兼容性
def get_weather_tools_sync():
    """向后兼容的天气工具获取函数"""
    from .fishing.weather import get_weather_tools
    return get_weather_tools()

def query_current_weather(location: str) -> str:
    """向后兼容的天气查询函数"""
    from .fishing.weather.current_weather import query_current_weather
    return query_current_weather(location)
```

### 3. Agent Integration

**更新策略**:
```python
# src/agent.py
class OptimizedFishingAgent:
    def _setup_tools(self) -> List:
        """使用新架构设置工具集"""
        from src.tools import get_all_tools
        tools = get_all_tools()

        logger.info(f"🛠️ 新工具集配置完成: {len(tools)} 个工具")
        logger.info(f"   基础工具: {sum(1 for t in tools if hasattr(t, '_basic_category'))} 个")
        logger.info(f"   钓鱼工具: {sum(1 for t in tools if hasattr(t, '_fishing_category'))} 个")
        return tools
```

## 📊 Performance Optimization

### 1. 内存优化
- **延迟加载**: 工具按需导入
- **共享实例**: 工具实例复用
- **缓存机制**: 工具注册结果缓存

### 2. API调用优化
- **数据复用**: 钓鱼工具复用天气数据
- **批量查询**: 相关数据一次性获取
- **智能缓存**: 避免重复API调用

### 3. 加载优化
- **模块缓存**: 已加载模块的缓存
- **并行加载**: 独立模块并行导入
- **预热机制**: 常用工具预加载

## 🧪 Testing Strategy

### 1. 单元测试
- 每个工具独立测试
- 工具注册系统测试
- 模块导入测试

### 2. 集成测试
- 工具间协作测试
- 完整业务流程测试
- 向后兼容性测试

### 3. 性能测试
- 工具加载时间测试
- API调用次数验证
- 内存使用监控

## 📈 Monitoring & Metrics

### 1. 工具使用统计
```python
class ToolMetrics:
    def __init__(self):
        self.call_counts = {}
        self.execution_times = {}

    def record_tool_call(self, tool_name: str, execution_time: float):
        self.call_counts[tool_name] = self.call_counts.get(tool_name, 0) + 1
        self.execution_times[tool_name] = execution_time
```

### 2. 性能监控
- 工具调用频率统计
- 平均响应时间监控
- 错误率跟踪
- 资源使用监控

## 🚀 Future Extensions

### 1. 插件系统
- 动态工具加载
- 外部工具集成
- 配置驱动的工具启用

### 2. 配置管理
- 工具配置文件
- 环境变量支持
- 运行时配置调整

### 3. 高级功能
- 工具链组合
- 智能工具选择
- 自动化工作流

---

**设计状态**: ✅ 完成
**实现状态**: 🟡 进行中
**下一步**: 核心基础设施实现