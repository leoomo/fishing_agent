"""
Role-based access control (RBAC) permissions system

Defines roles and permissions for the fishing agent admin system.
"""

from enum import Enum
from typing import Set, List


class RoleEnum(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"          # Administrator: all permissions
    EDITOR = "editor"        # Editor: create, read, update
    READONLY = "readonly"    # Read-only: only read permissions


class PermissionEnum(str, Enum):
    """Permission enumeration"""

    # Equipment management
    EQUIPMENT_CREATE = "equipment:create"
    EQUIPMENT_READ = "equipment:read"
    EQUIPMENT_UPDATE = "equipment:update"
    EQUIPMENT_DELETE = "equipment:delete"

    # Brand management
    BRAND_CREATE = "brand:create"
    BRAND_READ = "brand:read"
    BRAND_UPDATE = "brand:update"
    BRAND_DELETE = "brand:delete"

    # User management
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_MANAGE = "user:manage"  # Disable/enable users

    # Content management (fish, rigs, lures)
    CONTENT_CREATE = "content:create"
    CONTENT_READ = "content:read"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"

    # Crawler management
    CRAWLER_READ = "crawler:read"
    CRAWLER_EXECUTE = "crawler:execute"  # Trigger tasks
    CRAWLER_UPDATE = "crawler:update"    # Update task configuration
    CRAWLER_DELETE = "crawler:delete"

    # System monitoring
    MONITOR_READ = "monitor:read"

    # Data analytics
    ANALYTICS_READ = "analytics:read"

    # Configuration management
    CONFIG_READ = "config:read"
    CONFIG_UPDATE = "config:update"
    CONFIG_CREATE = "config:create"
    CONFIG_DELETE = "config:delete"
    CONFIG_TEST = "config:test"  # Test API keys

    # Import/Export
    DATA_IMPORT = "data:import"
    DATA_EXPORT = "data:export"

    # OCR
    OCR_USE = "ocr:use"


# Role-permission mapping
ROLE_PERMISSIONS: dict[RoleEnum, Set[PermissionEnum]] = {
    RoleEnum.ADMIN: {
        # Admin has all permissions
        perm for perm in PermissionEnum
    },

    RoleEnum.EDITOR: {
        # Equipment and brand: create, read, update
        PermissionEnum.EQUIPMENT_CREATE,
        PermissionEnum.EQUIPMENT_READ,
        PermissionEnum.EQUIPMENT_UPDATE,
        PermissionEnum.BRAND_CREATE,
        PermissionEnum.BRAND_READ,
        PermissionEnum.BRAND_UPDATE,

        # User: read only
        PermissionEnum.USER_READ,

        # Content: create, read, update
        PermissionEnum.CONTENT_CREATE,
        PermissionEnum.CONTENT_READ,
        PermissionEnum.CONTENT_UPDATE,

        # Crawler: read only
        PermissionEnum.CRAWLER_READ,

        # Monitoring and analytics: read only
        PermissionEnum.MONITOR_READ,
        PermissionEnum.ANALYTICS_READ,

        # Config: read only
        PermissionEnum.CONFIG_READ,

        # Export data
        PermissionEnum.DATA_EXPORT,

        # OCR
        PermissionEnum.OCR_USE,
    },

    RoleEnum.READONLY: {
        # All modules: read only
        PermissionEnum.EQUIPMENT_READ,
        PermissionEnum.BRAND_READ,
        PermissionEnum.USER_READ,
        PermissionEnum.CONTENT_READ,
        PermissionEnum.CRAWLER_READ,
        PermissionEnum.MONITOR_READ,
        PermissionEnum.ANALYTICS_READ,
        PermissionEnum.CONFIG_READ,

        # OCR
        PermissionEnum.OCR_USE,
    }
}


def has_permission(role: RoleEnum, permission: PermissionEnum) -> bool:
    """
    Check if role has specified permission

    Args:
        role: User role
        permission: Permission to check

    Returns:
        bool: True if role has permission, False otherwise

    Example:
        >>> has_permission(RoleEnum.ADMIN, PermissionEnum.EQUIPMENT_DELETE)
        True
        >>> has_permission(RoleEnum.READONLY, PermissionEnum.EQUIPMENT_CREATE)
        False
    """
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_role_permissions(role: RoleEnum) -> List[str]:
    """
    Get all permissions for a role

    Args:
        role: User role

    Returns:
        List[str]: List of permission strings

    Example:
        >>> perms = get_role_permissions(RoleEnum.ADMIN)
        >>> len(perms)
        27
    """
    return [perm.value for perm in ROLE_PERMISSIONS.get(role, set())]
