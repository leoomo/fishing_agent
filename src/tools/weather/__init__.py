#!/usr/bin/env python3
"""
天气工具模块 (独立业务模块)
提供纯天气数据查询功能，不包含任何钓鱼业务逻辑
"""

# 从工具文件导入天气工具
from .weather_tools import (
    query_current_weather,
    query_weather_by_date,
    query_weather_by_datetime,
    query_hourly_forecast,
    query_time_period_weather
)

def get_weather_tools():
    """获取所有天气工具"""
    return [
        query_current_weather,
        query_weather_by_date,
        query_weather_by_datetime,
        query_hourly_forecast,
        query_time_period_weather
    ]

# get_all_tools() 方法已移除，因为天气模块不再包含钓鱼工具
# 如需获取所有工具，请使用 src.tools.get_all_tools()

__all__ = [
    'get_weather_tools',
    'query_current_weather',
    'query_weather_by_date',
    'query_weather_by_datetime',
    'query_hourly_forecast',
    'query_time_period_weather'
]