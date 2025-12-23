"""
路亚装备数据库模块 (兼容层)

此模块已迁移到 apps.api.database，本文件仅作为兼容层保留。
所有新代码应直接从 apps.api.database 导入。

迁移说明:
- LureDatabase, get_db, reset_db 已迁移到 apps.api.database
- ORM models 已迁移到 apps.api.models
- ORM session 已迁移到 apps.api.orm
"""

# 重导出所有原有接口，保持向后兼容
from apps.api.database import (
    LureDatabase,
    get_db,
    reset_db,
    DB_PATH,
)

__all__ = [
    'LureDatabase',
    'get_db',
    'reset_db',
    'DB_PATH',
]
