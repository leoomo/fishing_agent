"""
坐标服务模块

提供坐标相关的服务实现。
"""

from .enhanced_amap_coordinate_service import EnhancedAmapCoordinateService
from .amap_coordinate_service import AmapCoordinateService  # 保持向后兼容

__all__ = [
    "EnhancedAmapCoordinateService",
    "AmapCoordinateService",
    "create_coordinate_service",
]


def create_coordinate_service() -> EnhancedAmapCoordinateService:
    """
    创建坐标服务实例的工厂函数

    Returns:
        EnhancedAmapCoordinateService: 新的坐标服务实例
    """
    return EnhancedAmapCoordinateService()