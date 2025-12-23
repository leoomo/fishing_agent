"""
用户装备管理模块

提供用户装备库管理功能，包括：
- 用户装备CRUD操作
- 装备统计分析
- 基于用户装备的推荐增强
"""

from .manager import UserEquipmentManager
from .recommender import UserBasedRecommender
from .tools import USER_EQUIPMENT_TOOLS

__all__ = [
    "UserEquipmentManager",
    "UserBasedRecommender",
    "USER_EQUIPMENT_TOOLS",
]
