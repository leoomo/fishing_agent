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
from apps.api.orm.session import get_db_session
from apps.api.orm.repositories.admin_user_repo import AdminUserRepository
from ..services.wechat_service import wechat_service

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


@router.get("/me", response_model=ProfileResponse)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current user profile (alias for /profile)

    This endpoint is for mobile app compatibility.
    Mobile apps typically call /auth/me to get current user info.

    Args:
        current_user: Current authenticated user (from JWT token)

    Returns:
        ProfileResponse: User profile and permissions
    """
    return await get_profile(current_user)


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


# WeChat Login Schemas
class WeChatLoginRequest(BaseModel):
    """WeChat login request payload"""
    code: str = Field(..., description="微信登录code")
    nickname: Optional[str] = Field(None, description="微信昵称")
    avatar_url: Optional[str] = Field(None, description="微信头像URL")
    gender: Optional[int] = Field(0, description="性别：0未知，1男，2女")
    city: Optional[str] = Field(None, description="城市")
    province: Optional[str] = Field(None, description="省份")
    country: Optional[str] = Field(None, description="国家")
    language: Optional[str] = Field("zh_CN", description="语言")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "031Kc1002CqHL31hR0002VvLTK3Kc10g",
                    "nickname": "微信用户",
                    "avatar_url": "https://thirdwx.qlogo.cn/...",
                    "gender": 1,
                    "city": "深圳",
                    "province": "广东",
                    "country": "中国"
                }
            ]
        }
    }


class WeChatBindRequest(BaseModel):
    """WeChat bind request payload"""
    admin_user_id: int = Field(..., description="管理员用户ID")
    code: str = Field(..., description="微信登录code")
    nickname: Optional[str] = Field(None, description="微信昵称")
    avatar_url: Optional[str] = Field(None, description="微信头像URL")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "admin_user_id": 1,
                    "code": "031Kc1002CqHL31hR0002VvLTK3Kc10g",
                    "nickname": "微信用户"
                }
            ]
        }
    }


@router.post("/wechat/login", response_model=LoginResponse)
async def wechat_login(request: WeChatLoginRequest):
    """
    WeChat login endpoint

    Authenticate user using WeChat miniprogram code and returns JWT access token.

    Args:
        request: WeChat login data (code and user info)

    Returns:
        LoginResponse: JWT token and user information

    Raises:
        HTTPException: 400 if login fails
        HTTPException: 500 if server error
    """
    import os

    # 开发模式：模拟登录
    if os.getenv("WECHAT_DEV_MODE", "").lower() == "true":
        logger.info(f"[DEV MODE] Mock WeChat login for code: {request.code}")
        from ..auth.jwt import create_access_token
        from datetime import datetime

        # 生成模拟用户数据
        mock_openid = f"mock_openid_{request.code[:8] if request.code else 'dev'}"
        nickname = request.nickname or "测试用户"

        # 生成 token
        access_token = create_access_token(data={
            "sub": "1",
            "username": nickname,
            "role": "readonly",
            "openid": mock_openid,
        })

        # 模拟权限列表
        mock_permissions = [
            "equipment:read",
            "fishing:query",
            "weather:query",
        ]

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(
                user_id=1,
                username=nickname,
                email=f"{mock_openid}@wechat.mock",
                role="readonly",
                full_name=nickname,
                is_active=True,
                created_at=datetime.now().isoformat(),
            ),
            permissions=mock_permissions,
        )

    try:
        # Initialize WeChat service
        wechat_service.initialize()

        # Perform WeChat login or create user
        result = await wechat_service.login_or_create_user(
            code=request.code,
            nickname=request.nickname,
            avatar_url=request.avatar_url,
            gender=request.gender or 0,
            city=request.city,
            province=request.province,
            country=request.country,
            language=request.language or "zh_CN"
        )

        return LoginResponse(**result)

    except ValueError as e:
        logger.error(f"WeChat login configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信登录服务配置错误"
        )
    except Exception as e:
        logger.error(f"WeChat login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/wechat/bind")
async def wechat_bind(
    request: WeChatBindRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Bind WeChat account to current admin user

    Args:
        request: WeChat bind data
        current_user: Current authenticated user

    Returns:
        dict: Binding result

    Raises:
        HTTPException: 400 if binding fails
        HTTPException: 403 if permission denied
    """
    try:
        # Initialize WeChat service
        wechat_service.initialize()

        # Only allow binding to own account or admin can bind to others
        if current_user.role != "admin" and request.admin_user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能绑定自己的账号"
            )

        # Perform WeChat binding
        result = await wechat_service.bind_wechat_to_admin(
            admin_user_id=request.admin_user_id,
            code=request.code,
            nickname=request.nickname,
            avatar_url=request.avatar_url
        )

        return result

    except ValueError as e:
        logger.error(f"WeChat bind configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信登录服务配置错误"
        )
    except Exception as e:
        logger.error(f"WeChat bind failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/wechat/config")
async def get_wechat_config():
    """
    Get WeChat configuration for frontend

    Returns:
        dict: WeChat app configuration
    """
    import os

    app_id = os.getenv("WECHAT_APP_ID") or os.getenv("WECHAT_APPID")
    if not app_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信配置缺失"
        )

    return {
        "app_id": app_id,
        "api_url": os.getenv("WECHAT_API_URL", "https://api.weixin.qq.com"),
        "auto_create_user": os.getenv("WECHAT_AUTO_CREATE_USER", "true").lower() == "true"
    }
