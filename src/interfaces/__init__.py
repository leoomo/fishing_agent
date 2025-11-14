"""
服务接口抽象层

提供统一的服务接口定义，实现松耦合架构。
"""

from .coordinate_service import ICoordinateService
from .weather_service import IWeatherService

__all__ = [
    "ICoordinateService",
    "IWeatherService",
]