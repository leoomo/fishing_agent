"""
坐标服务接口抽象

定义标准的坐标服务接口，支持不同实现的替换和扩展。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class Coordinate:
    """坐标数据类"""
    longitude: float  # 经度
    latitude: float   # 纬度
    confidence: float = 1.0  # 置信度
    source: str = "unknown"  # 数据源


@dataclass
class LocationInfo:
    """位置信息数据类"""
    name: str           # 位置名称
    adcode: str         # 行政区划代码
    province: str       # 省份
    city: str          # 城市
    district: str      # 区县
    coordinate: Coordinate  # 坐标信息
    level: str = "unknown"  # 行政级别


class ICoordinateService(ABC):
    """坐标服务接口"""

    @abstractmethod
    def get_coordinate(self, location_name: str) -> Optional[Coordinate]:
        """
        根据位置名称获取坐标

        Args:
            location_name: 位置名称

        Returns:
            坐标信息，如果未找到返回 None
        """
        pass

    @abstractmethod
    def get_location_info(self, location_name: str) -> Optional[LocationInfo]:
        """
        根据位置名称获取详细位置信息

        Args:
            location_name: 位置名称

        Returns:
            位置信息，如果未找到返回 None
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查服务是否已初始化

        Returns:
            True 如果已初始化，False 否则
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