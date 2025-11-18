# Tools Module Refactoring - OpenSpec Change Proposal

## 📋 Feature Overview

**Feature Name**: Tools Module Refactoring
**Priority**: High
**Impact**: Code organization, developer experience, maintainability
**Estimated Effort**: 2-3 days

## 🎯 Problem Statement

The current `src/tools/` directory has several issues:

1. **Scattered Files**: 13+ tool files with inconsistent naming and organization
2. **Duplicate Functionality**: Multiple similar tools (weather_tool.py, weather_tool_sync.py, etc.)
3. **Mixed Complexity**: Simple utility tools mixed with complex service-based tools
4. **No Clear Structure**: Difficult to understand where to add new tools
5. **Inconsistent Patterns**: Some tools are simple functions, others are complex classes

## 🏗️ Proposed Solution

### Core Design Principles
- **Simple Tools**: Easy to write and add (single function approach)
- **Complex Tools**: Modular, registered, and managed separately
- **Simple Directory Structure**: Clear and intuitive, not over-engineered

### New Directory Structure
```
src/tools/
├── __init__.py                 # Tool registry and exports
├── base.py                     # Base utility tools (single file)
├── services/                   # Service-based tools
│   ├── __init__.py
│   ├── weather.py              # Weather tools ecosystem
│   ├── location.py             # Location and coordinate tools
│   └── analysis.py             # Analysis and recommendation tools
└── registry.py                 # Tool registration and management
```

## 🔧 Implementation Details

### 1. Base Tools Pattern (Single File)
```python
# src/tools/base.py
from langchain_core.tools import tool
from datetime import datetime

@tool
def get_current_time() -> str:
    """获取当前时间和日期"""
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        allowed_chars = set('0123456789+-*/().** ')
        if not all(c in allowed_chars for c in expression):
            return "错误: 表达式包含不允许的字符"
        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

@tool
def search_information(query: str) -> str:
    """搜索信息（模拟功能）"""
    knowledge_base = {
        "钓鱼": "钓鱼是一种休闲娱乐活动，根据天气、水温、时间等因素选择合适的钓点和钓法。",
        "路亚": "路亚钓鱼是一种假饵钓法，使用拟饵模仿鱼类食物，适合钓获掠食性鱼类。",
        "鲈鱼": "鲈鱼是常见的路亚钓鱼目标鱼种，喜欢在水草边缘和障碍物附近活动。"
    }
    query_lower = query.lower()
    for keyword, info in knowledge_base.items():
        if keyword in query_lower:
            return f"搜索结果: {info}"
    return f"关于 '{query}' 的信息: 可以尝试更具体的关键词搜索"

def get_base_tools():
    """获取基础工具列表"""
    return [get_current_time, calculate, search_information]
```

### 2. Service Tools Pattern
```python
# src/tools/services/weather.py
from typing import Dict, Any
from src.core.base_tool import BaseTool

class WeatherService:
    """天气服务工具类"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # 初始化天气服务等复杂依赖

    def get_current_weather(self, location: str) -> str:
        """当前天气查询"""
        # 复杂的天气查询逻辑
        pass

    def get_weather_forecast(self, location: str, days: int = 3) -> str:
        """天气预报查询"""
        # 预报逻辑
        pass
```

### 3. Tool Registry System
```python
# src/tools/registry.py
class ToolRegistry:
    """工具注册中心 - 简单设计"""

    def __init__(self):
        self._base_tools = []
        self._service_tools = []

    def register_base_tools(self, tools_list):
        """注册基础工具"""
        self._base_tools.extend(tools_list)

    def register_service_tools(self, tools_list):
        """注册服务工具"""
        self._service_tools.extend(tools_list)

    def get_all_tools(self) -> List:
        """获取所有工具"""
        return self._base_tools + self._service_tools

# 全局注册器实例
tool_registry = ToolRegistry()
```

### 4. Unified Export Interface
```python
# src/tools/__init__.py
from .base import get_base_tools
from .registry import tool_registry

def get_all_tools():
    """统一获取所有工具的接口"""
    # 注册基础工具
    base_tools = get_base_tools()
    tool_registry.register_base_tools(base_tools)

    # 注册服务工具
    from .services.weather import get_weather_tools
    weather_tools = get_weather_tools()
    tool_registry.register_service_tools(weather_tools)

    return tool_registry.get_all_tools()
```

## 📁 File Migration Plan

### Phase 1: Base Tools (Day 1)
- **Consolidate**: `time_tool.py`, `math_tool.py`, `search_tool.py`, `basic_tools.py` → `base.py`
- **Remove**: 多余的基础工具文件
- **Create**: `base.py` 统一基础工具文件

### Phase 2: Service Tools (Day 2)
- **Reorganize**: `weather_tool_sync.py`, `langchain_weather_tools_sync.py` → `services/weather.py`
- **Reorganize**: Location related tools → `services/location.py`
- **Reorganize**: `fishing_analyzer_sync.py`, `enhanced_fishing_scorer.py` → `services/analysis.py`

### Phase 3: Registry & Integration (Day 3)
- **Create**: `registry.py` 工具管理系统
- **Update**: `src/agent.py` 使用新的工具系统
- **Create**: 完整文档和测试
- **Cleanup**: 删除旧的工具文件

## 🎯 Benefits

### Developer Experience
- **Easy Addition**: Simple tools require just one function with `@tool` decorator
- **Clear Organization**: Know exactly where to put different types of tools
- **Discoverability**: Tools are automatically discovered and registered

### Code Quality
- **Separation of Concerns**: Simple vs complex tools clearly separated
- **Reduced Duplication**: Consolidate similar weather tools
- **Better Testing**: Each tool can be tested independently

### Maintainability
- **Modular Structure**: Tools can be developed and maintained independently
- **Clear Interfaces**: Standardized patterns for different tool types
- **Scalable Architecture**: Easy to add new tool categories

## 🚀 Migration Strategy

### Backward Compatibility
1. **Gradual Migration**: Tools work alongside existing structure during transition
2. **Alias Support**: Old import paths redirect to new locations
3. **Fallback Support**: Agent can work with both old and new tool systems

### Risk Mitigation
1. **Incremental Rollout**: Migrate tool categories one at a time
2. **Automated Testing**: Ensure each migrated tool works identically
3. **Documentation**: Clear migration guide for developers

## 📊 Success Metrics

- **Code Organization**: Clear categorization of 90%+ tools
- **Developer Velocity**: 50%+ faster to add new simple tools
- **Reduced Duplication**: Eliminate 5+ duplicate tool files
- **Test Coverage**: Maintain or improve existing test coverage

## 🔄 Timeline

- **Day 1**: Simple tools migration and registry foundation
- **Day 2**: Complex tools reorganization
- **Day 3**: Integration, testing, and documentation

## 🎉 Conclusion

This refactoring will transform the tools directory from a scattered collection into a well-organized, developer-friendly module that scales with the project's growth while maintaining simplicity for common use cases.

---

**Status**: 🟡 Planning - Ready for Implementation
**Next Steps**: Stakeholder review and approval