#!/usr/bin/env python3
"""
工具模块统一入口
提供基础工具和钓鱼工具的统一访问接口
"""

from .basic import get_basic_tools
from .fishing import get_fishing_tools
from .core.tool_registry import tool_registry

def get_all_tools():
    """
    获取所有已注册的工具

    Returns:
        List: 所有工具的列表
    """
    # 清空注册器，重新注册所有工具
    tool_registry.reset()

    # 注册基础工具
    basic_tools = get_basic_tools()
    tool_registry.register_tools_by_category(basic_tools, "basic")

    # 注册钓鱼工具
    fishing_tools = get_fishing_tools()
    tool_registry.register_tools_by_category(fishing_tools, "weather")  # 暂时归类为天气工具

    return tool_registry.get_all_tools()

def get_tools_by_category(category: str):
    """
    按类别获取工具

    Args:
        category: 工具类别 ("basic", "weather", "advice", "equipment")

    Returns:
        List: 指定类别的工具列表
    """
    return tool_registry.get_tools_by_category(category)

def get_tool_stats():
    """
    获取工具统计信息

    Returns:
        Dict: 工具统计信息
    """
    return tool_registry.get_stats()

# 向后兼容的函数
def get_weather_tools_sync():
    """
    向后兼容：获取天气工具
    """
    from .fishing.weather import get_weather_tools
    return get_weather_tools()

def query_current_weather(location: str):
    """
    向后兼容：查询当前天气
    """
    from .fishing.weather import query_current_weather
    return query_current_weather(location)

# 注册所有工具
def register_all_tools():
    """注册所有工具到全局注册器"""
    tools = get_all_tools()
    return tools

# 自动注册
all_tools = register_all_tools()

__all__ = [
    'get_all_tools',
    'get_basic_tools',
    'get_fishing_tools',
    'get_tools_by_category',
    'get_tool_stats',
    'get_weather_tools_sync',
    'query_current_weather',
    'tool_registry',
    'all_tools'
]