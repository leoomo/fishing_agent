"""
Repository package for database access patterns

Provides easy access to all repository classes.
"""

from .equipment_repo import EquipmentRepository
from .brand_repo import BrandRepository
from .user_repo import UserRepository, UserEquipmentRepository, FishingLogRepository
from .fish_repo import FishSpeciesRepository, FishKnowledgeRepository, FishSeasonActivityRepository

__all__ = [
    # Equipment
    "EquipmentRepository",
    "BrandRepository",

    # User
    "UserRepository",
    "UserEquipmentRepository",
    "FishingLogRepository",

    # Fish
    "FishSpeciesRepository",
    "FishKnowledgeRepository",
    "FishSeasonActivityRepository",
]
