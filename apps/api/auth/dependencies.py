"""
FastAPI dependencies for authentication and authorization

Provides dependency functions for JWT token validation and permission checking.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .jwt import verify_token
from .permissions import RoleEnum, PermissionEnum, has_permission
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


class CurrentUser:
    """Current authenticated user information"""

    def __init__(self, user_id: int, username: str, role: RoleEnum):
        self.user_id = user_id
        self.username = username
        self.role = role

    def __repr__(self):
        return f"<CurrentUser(user_id={self.user_id}, username='{self.username}', role='{self.role.value}')>"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Extract current user from JWT token

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        CurrentUser: Current authenticated user

    Raises:
        HTTPException: If token is invalid or expired

    Example:
        @router.get("/profile")
        async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    """
    token = credentials.credentials

    try:
        # Verify token
        payload = verify_token(token)

        # Extract user information (支持 user_id 或 sub 字段)
        user_id = payload.get("user_id") or payload.get("sub")
        username = payload.get("username")
        role_str = payload.get("role")

        if not all([user_id, username, role_str]):
            raise ValueError("Token payload 缺少必需字段")

        # 确保 user_id 是整数
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise ValueError(f"无效的用户ID: {user_id}")

        # Validate role
        try:
            role = RoleEnum(role_str)
        except ValueError:
            raise ValueError(f"无效的角色: {role_str}")

        return CurrentUser(user_id=user_id, username=username, role=role)

    except ValueError as e:
        logger.warning(f"Token 验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"身份验证失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: PermissionEnum):
    """
    Permission check dependency factory

    Args:
        permission: Required permission

    Returns:
        Callable: FastAPI dependency function

    Example:
        @router.post(
            "/equipment",
            dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
        )
        async def create_equipment(...):
            ...
    """
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if not has_permission(current_user.role, permission):
            logger.warning(
                f"权限拒绝: user={current_user.username}, "
                f"role={current_user.role.value}, "
                f"required_permission={permission.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足: 需要 {permission.value}"
            )

        return current_user

    return permission_checker


def require_admin():
    """
    Require admin role

    Returns:
        Callable: FastAPI dependency function

    Example:
        @router.delete("/users/{user_id}", dependencies=[Depends(require_admin())])
        async def delete_user(user_id: int):
            ...
    """
    async def admin_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        if current_user.role != RoleEnum.ADMIN:
            logger.warning(
                f"Admin 权限拒绝: user={current_user.username}, role={current_user.role.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )

        return current_user

    return admin_checker


# Optional: Get current user without requiring authentication (for public endpoints)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[CurrentUser]:
    """
    Extract current user from JWT token if present, otherwise return None

    Args:
        credentials: Optional HTTP Authorization header

    Returns:
        Optional[CurrentUser]: Current user if authenticated, None otherwise

    Example:
        @router.get("/public")
        async def public_endpoint(current_user: Optional[CurrentUser] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": f"Hello {current_user.username}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
