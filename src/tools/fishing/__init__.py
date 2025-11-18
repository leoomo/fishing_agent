#!/usr/bin/env python3
"""
钓鱼业务模块
包含天气查询、钓鱼分析和装备推荐的完整业务功能
"""

from .weather import get_weather_tools
from .advice import get_advice_tools
from .equipment import get_equipment_tools

def get_fishing_tools():
    """获取所有钓鱼工具"""
    weather_tools = get_weather_tools()
    advice_tools = get_advice_tools()
    equipment_tools = get_equipment_tools()

    return weather_tools + advice_tools + equipment_tools

__all__ = [
    'get_fishing_tools',
    'get_weather_tools',
    'get_advice_tools',
    'get_equipment_tools'
]