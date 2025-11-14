"""
LangChain Learning - Weather Service

天气服务模块提供天气数据获取和处理功能。
"""

from .weather_service import CaiyunWeatherService, WeatherData
from .enhanced_weather_service import EnhancedCaiyunWeatherService
from .enhanced_caiyun_weather_service import EnhancedCaiyunWeatherService as NewEnhancedCaiyunWeatherService
from .datetime_weather_service import DateTimeWeatherService

__all__ = [
    "CaiyunWeatherService",
    "WeatherData",
    "EnhancedCaiyunWeatherService",
    "NewEnhancedCaiyunWeatherService",
    "DateTimeWeatherService",
    "create_weather_service",
]


def create_weather_service() -> DateTimeWeatherService:
    """
    创建天气服务实例的工厂函数

    Returns:
        DateTimeWeatherService: 智能路由天气服务实例，支持多种API接口
    """
    return DateTimeWeatherService()