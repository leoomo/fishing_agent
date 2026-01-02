"""
ORM 兼容层

此模块已迁移到 apps.api.orm，本文件仅作为兼容层保留。
所有新代码应直接从 apps.api.orm 导入。
"""

# 重导出所有 ORM 接口
from apps.api.orm import (
    # Session management
    get_db_session,
    get_engine,
    init_db,
    close_db,
    get_database_url,
    # Base repository
    BaseRepository,
    # Equipment repositories
    EquipmentRepository,
    BrandRepository,
    # User repositories
    UserRepository,
    UserEquipmentRepository,
    FishingLogRepository,
    # Fish repositories
    FishSpeciesRepository,
    FishKnowledgeRepository,
    FishSeasonActivityRepository,
)

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
