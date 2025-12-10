"""
Authentication routes for admin backend

Provides login, token refresh, and user profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from ..auth.jwt import create_access_token, verify_password
from ..auth.dependencies import get_current_user, CurrentUser
from ..auth.permissions import get_role_permissions
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Schemas
class LoginRequest(BaseModel):
    """Login request payload"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "admin",
                    "password": "admin123"
                }
            ]
        }
    }


class LoginResponse(BaseModel):
    """Login response with token and user info"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: "UserInfo" = Field(..., description="User information")
    permissions: list[str] = Field(..., description="User permissions")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user": {
                        "user_id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "role": "admin",
                        "full_name": "Administrator",
                        "is_active": True
                    },
                    "permissions": ["equipment:create", "equipment:read", "..."]
                }
            ]
        }
    }


class UserInfo(BaseModel):
    """User information in response"""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    role: str = Field(..., description="User role")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(..., description="Is active")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    created_at: str = Field(..., description="Account creation timestamp")


class ProfileResponse(BaseModel):
    """User profile response"""
    user: UserInfo = Field(..., description="User information")
    permissions: list[str] = Field(..., description="User permissions")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Admin user login

    Authenticates user credentials and returns JWT access token.

    Args:
        request: Login credentials (username and password)

    Returns:
        LoginResponse: JWT token and user information

    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 403 if user is inactive
    """
    with get_db_session() as session:
        repo = AdminUserRepository(session)

        # Find user by username
        user = repo.get_by_username(request.username)

        if user is None:
            logger.warning(f"Login failed: user not found - {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"Login failed: incorrect password - {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: user is inactive - {request.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被禁用，请联系管理员",
            )

        # Update last login time
        repo.update_last_login(user.id)
        session.commit()

        # Generate JWT token
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
        access_token = create_access_token(token_data)

        # Get user permissions
        from ..auth.permissions import RoleEnum
        role_enum = RoleEnum(user.role)
        permissions = get_role_permissions(role_enum)

        logger.info(f"Login successful: {request.username} (role: {user.role})")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                full_name=user.full_name,
                is_active=user.is_active,
                last_login=user.last_login,
                created_at=user.created_at.isoformat() if user.created_at else None
            ),
            permissions=permissions
        )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current user profile

    Returns authenticated user's profile and permissions.

    Args:
        current_user: Current authenticated user (from JWT token)

    Returns:
        ProfileResponse: User profile and permissions
    """
    with get_db_session() as session:
        repo = AdminUserRepository(session)
        user = repo.get(current_user.user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        permissions = get_role_permissions(current_user.role)

        return ProfileResponse(
            user=UserInfo(
                user_id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                full_name=user.full_name,
                is_active=user.is_active,
                last_login=user.last_login,
                created_at=user.created_at.isoformat() if user.created_at else None
            ),
            permissions=permissions
        )


@router.post("/logout")
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """
    Logout endpoint

    Note: JWT tokens are stateless, so logout is handled client-side
    by discarding the token. This endpoint exists for consistency
    and potential future server-side token invalidation.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "登出成功"}
