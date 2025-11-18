#!/usr/bin/env python3
"""
天气工具模块 (数据获取层)
提供纯粹的天气数据查询功能，不包含业务分析逻辑
"""

# 从现有模块导入天气工具
try:
    # 复用现有的天气工具，然后重新组织和导出
    from ....langchain_weather_tools_sync import (
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

except ImportError as e:
    print(f"警告: 无法导入现有天气工具: {e}")

    def get_weather_tools():
        """返回空列表，如果无法导入现有工具"""
        return []

__all__ = [
    'get_weather_tools',
    'query_current_weather',
    'query_weather_by_date',
    'query_weather_by_datetime',
    'query_hourly_forecast',
    'query_time_period_weather'
]