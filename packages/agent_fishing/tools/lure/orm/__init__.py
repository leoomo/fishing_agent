"""
ORM package for database access layer

This package provides the ORM session management and repository pattern
for accessing the fishing agent database.
"""

from .session import get_db_session, get_engine, init_db, close_db, get_database_url
from .repository import BaseRepository
from .repositories.equipment_repo import EquipmentRepository
from .repositories.brand_repo import BrandRepository
from .repositories.user_repo import UserRepository, UserEquipmentRepository, FishingLogRepository
from .repositories.fish_repo import FishSpeciesRepository, FishKnowledgeRepository, FishSeasonActivityRepository

__all__ = [
    # Session management
    "get_db_session",
    "get_engine",
    "init_db",
    "close_db",
    "get_database_url",

    # Base repository
    "BaseRepository",

    # Equipment repositories
    "EquipmentRepository",
    "BrandRepository",

    # User repositories
    "UserRepository",
    "UserEquipmentRepository",
    "FishingLogRepository",

    # Fish repositories
    "FishSpeciesRepository",
    "FishKnowledgeRepository",
    "FishSeasonActivityRepository",
]
