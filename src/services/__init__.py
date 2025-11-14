"""
LangChain Learning - Services Module

服务模块提供了各种后端服务实现，包括：
- 中央服务管理器
- 坐标服务
- 天气服务
- 地名匹配服务
- 缓存服务
- 日志服务
"""

from .service_manager import (
    ServiceManager,
    get_service_manager,
    get_coordinate_service,
    get_weather_service,
)

__version__ = "1.0.0"
__all__ = [
    "ServiceManager",
    "get_service_manager",
    "get_coordinate_service",
    "get_weather_service",
]