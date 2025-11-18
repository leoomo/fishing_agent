#!/usr/bin/env python3
"""
天气工具模块 (数据获取层)
提供纯粹的天气数据查询功能，不包含业务分析逻辑
"""

# 从新模块化文件导入天气工具
try:
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

except ImportError as e:
    print(f"警告: 无法导入新模块化天气工具: {e}")

    # 回退到core层
    try:
        from ..core.tools.weather_tool_core import (
            query_current_weather,
            query_weather_by_date,
            query_weather_by_datetime,
            query_hourly_forecast,
            query_time_period_weather
        )

        def get_weather_tools():
            """获取所有天气工具（core版本）"""
            return [
                query_current_weather,
                query_weather_by_date,
                query_weather_by_datetime,
                query_hourly_forecast,
                query_time_period_weather
            ]

    except ImportError as fallback_e:
        print(f"警告: 无法导入core天气工具: {fallback_e}")

        def get_weather_tools():
            """返回空列表，如果无法导入所有工具"""
            return []

__all__ = [
    'get_weather_tools',
    'query_current_weather',
    'query_weather_by_date',
    'query_weather_by_datetime',
    'query_hourly_forecast',
    'query_time_period_weather'
]