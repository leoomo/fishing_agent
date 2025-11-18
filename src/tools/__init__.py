#!/usr/bin/env python3
"""
工具模块统一入口
提供基础工具和钓鱼工具的统一访问接口
"""

from .basic import get_basic_tools
from .fishing import get_fishing_tools

def get_all_tools():
    """
    获取所有工具

    Returns:
        List: 所有工具的列表
    """
    tools = []
    tools.extend(get_basic_tools())
    tools.extend(get_fishing_tools())
    return tools

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

__all__ = [
    'get_all_tools',
    'get_basic_tools',
    'get_fishing_tools',
    'get_weather_tools_sync',
    'query_current_weather'
]