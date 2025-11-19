#!/usr/bin/env python3
"""
工具模块 - 简化架构版本

提供基础工具、天气工具和钓鱼工具的统一访问接口。
使用LangChain 1.0+最佳实践，移除过度抽象。
"""

# 导入新架构的工具
from .basic_tools import BASIC_TOOLS
from .weather_tools import WEATHER_TOOLS
from .fishing_tools import FISHING_TOOLS


def get_all_tools():
    """
    获取所有工具（新架构版本）

    Returns:
        List: 所有LangChain工具的列表
    """
    tools = []
    tools.extend(BASIC_TOOLS)
    tools.extend(WEATHER_TOOLS)
    tools.extend(FISHING_TOOLS)
    return tools


def get_basic_tools():
    """
    获取基础工具

    Returns:
        List: 基础工具列表
    """
    return BASIC_TOOLS.copy()


def get_weather_tools():
    """
    获取天气工具

    Returns:
        List: 天气工具列表
    """
    return WEATHER_TOOLS.copy()


def get_fishing_tools():
    """
    获取钓鱼工具

    Returns:
        List: 钓鱼工具列表
    """
    return FISHING_TOOLS.copy()


# 向后兼容的函数（保持API兼容性）
def get_weather_tools_sync():
    """
    向后兼容：获取天气工具

    Returns:
        List: 天气工具列表（同步版本）
    """
    return get_weather_tools()




def query_fishing_recommendation(location: str, date: str = None):
    """
    向后兼容：查询钓鱼推荐

    Args:
        location: 位置名称
        date: 日期字符串

    Returns:
        str: 钓鱼推荐报告
    """
    from .fishing_tools import query_fishing_recommendation
    return query_fishing_recommendation.invoke({"location": location, "date": date})


__all__ = [
    'get_all_tools',
    'get_basic_tools',
    'get_weather_tools',
    'get_fishing_tools',
    'get_weather_tools_sync',
    'query_fishing_recommendation',
    # 新架构导出
    'BASIC_TOOLS',
    'WEATHER_TOOLS',
    'FISHING_TOOLS'
]