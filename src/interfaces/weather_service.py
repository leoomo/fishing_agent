"""
天气服务接口抽象

定义标准的天气服务接口，支持不同实现的替换和扩展。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from dataclasses import dataclass
from .coordinate_service import Coordinate


@dataclass
class WeatherCondition:
    """天气条件数据类"""
    temperature: float      # 温度（摄氏度）
    humidity: float        # 湿度（百分比）
    pressure: float        # 气压（hPa）
    wind_speed: float      # 风速（m/s）
    wind_direction: float  # 风向（度）
    weather: str          # 天气描述
    visibility: float     # 能见度（km）
    timestamp: datetime   # 时间戳


@dataclass
class WeatherForecast:
    """天气预报数据类"""
    date: date
    conditions: List[WeatherCondition]
    daily_high: float
    daily_low: float
    weather_summary: str


class IWeatherService(ABC):
    """天气服务接口"""

    @abstractmethod
    def get_current_weather(self, location: str) -> Optional[WeatherCondition]:
        """
        获取指定位置的当前天气

        Args:
            location: 位置名称或坐标

        Returns:
            当前天气条件，如果获取失败返回 None
        """
        pass

    @abstractmethod
    def get_weather_forecast(self, location: str, days: int = 3) -> Optional[List[WeatherForecast]]:
        """
        获取指定位置的天气预报

        Args:
            location: 位置名称或坐标
            days: 预报天数

        Returns:
            天气预报列表，如果获取失败返回 None
        """
        pass

    @abstractmethod
    def get_weather_by_coordinate(self, coordinate: Coordinate) -> Optional[WeatherCondition]:
        """
        根据坐标获取天气

        Args:
            coordinate: 坐标信息

        Returns:
            天气条件，如果获取失败返回 None
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查服务是否可用

        Returns:
            True 如果服务可用，False 否则
        """
        pass

    @abstractmethod
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息

        Returns:
            包含服务状态信息的字典
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        执行健康检查

        Returns:
            True 如果服务健康，False 否则
        """
        pass