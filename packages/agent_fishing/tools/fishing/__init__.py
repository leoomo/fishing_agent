#!/usr/bin/env python3
"""
钓鱼推荐子模块

提供完整的钓鱼决策支持功能:
- 天气数据获取和解析
- 7因子科学评分体系
- 24小时智能时段推荐
- 多日对比推荐
"""

from .weather_api import get_weather_data, safe_convert_temperature, translate_weather_condition
from .weather_parser import parse_weather_response
from .scorer import calculate_fishing_score, calculate_hourly_scores
from .time_optimizer import find_best_time_slots, filter_time_slots_by_period, generate_score_trend
from .report_generator import generate_fishing_report
from .enhanced_scorer import (
    calculate_seasonal_score,
    calculate_lunar_score,
    analyze_pressure_trend,
    analyze_temperature_trend,
    analyze_wind_stability
)

__all__ = [
    'get_weather_data',
    'safe_convert_temperature',
    'translate_weather_condition',
    'parse_weather_response',
    'calculate_fishing_score',
    'calculate_hourly_scores',
    'find_best_time_slots',
    'filter_time_slots_by_period',
    'generate_score_trend',
    'generate_fishing_report',
    'calculate_seasonal_score',
    'calculate_lunar_score',
    'analyze_pressure_trend',
    'analyze_temperature_trend',
    'analyze_wind_stability',
]
