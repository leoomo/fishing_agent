"""
用户管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional, List
import logging

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.user_repo import (
    UserRepository,
    UserEquipmentRepository
)

from apps.api.schemas.user_admin import (
    UserResponse,
    UserListResponse,
    UserEquipmentResponse,
    FishingLogResponse
)
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 用户管理端点 ==========

@router.get(
    "/users",
    response_model=UserListResponse,
    summary="查询用户列表",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_level: Optional[str] = Query(None, description="用户水平过滤"),
    fishing_experience_years: Optional[int] = Query(None, description="钓龄过滤（年）"),
    location: Optional[str] = Query(None, description="地区过滤")
):
    """
    查询用户列表（分页 + 筛选）

    Returns:
        UserListResponse: 分页用户列表
    """
    try:
        with get_db_session() as session:
            repo = UserRepository(session)

            # 构建过滤条件
            from packages.agent_fishing.tools.lure.models.user import User
            from sqlalchemy import and_

            query = session.query(User)
            filters = []

            if user_level:
                filters.append(User.user_level == user_level)

            if fishing_experience_years is not None:
                filters.append(User.fishing_experience_years == fishing_experience_years)

            # location 字段在当前数据库中不存在，暂时注释掉

            if filters:
                query = query.filter(and_(*filters))

            # 获取总数
            total = query.count()

            # 分页查询
            users = query.offset((page - 1) * page_size).limit(page_size).all()

            # 转换为响应模型
            user_responses = []
            for user in users:
                user_responses.append(UserResponse(
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    phone=user.phone,
                    user_level=user.user_level,
                    fishing_experience_years=user.fishing_experience_years,
                    favorite_fish_species=user.preferred_fish,
                    preferred_fishing_method=user.preferred_scenarios,
                    location=None,  # 数据库中暂无此字段
                    created_at=user.created_at.isoformat(),
                    updated_at=user.updated_at.isoformat()
                ))

            return UserListResponse(
                total=total,
                page=page,
                page_size=page_size,
                users=user_responses
            )

    except Exception as e:
        logger.error(f"查询用户列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="获取用户详情",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def get_user(user_id: int):
    """
    获取用户详情

    Args:
        user_id: 用户ID

    Returns:
        UserResponse: 用户详细信息

    Raises:
        HTTPException: 用户不存在
    """
    try:
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.get(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户不存在: user_id={user_id}"
                )

            return UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                user_level=user.user_level,
                fishing_experience_years=user.fishing_experience_years,
                favorite_fish_species=user.favorite_fish_species,
                preferred_fishing_method=user.preferred_fishing_method,
                location=user.location,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.get(
    "/users/{user_id}/equipment",
    response_model=List[UserEquipmentResponse],
    summary="获取用户装备库",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def get_user_equipment(
    user_id: int,
    category: Optional[str] = Query(None, description="装备类别过滤"),
    is_favorite: Optional[bool] = Query(None, description="仅收藏装备")
):
    """
    获取用户装备库

    Args:
        user_id: 用户ID
        category: 装备类别过滤
        is_favorite: 仅显示收藏装备

    Returns:
        List[UserEquipmentResponse]: 用户装备列表

    Raises:
        HTTPException: 用户不存在
    """
    try:
        with get_db_session() as session:
            # 首先验证用户存在
            user_repo = UserRepository(session)
            user = user_repo.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户不存在: user_id={user_id}"
                )

            # 查询用户装备
            equipment_repo = UserEquipmentRepository(session)
            equipment_list = equipment_repo.get_user_equipment(
                user_id=user_id,
                category=category,
                is_favorite=is_favorite
            )

            # 转换为响应模型
            responses = []
            for eq in equipment_list:
                responses.append(UserEquipmentResponse(
                    user_equipment_id=eq.user_equipment_id,
                    user_id=eq.user_id,
                    equipment_id=eq.equipment_id,
                    equipment_name=eq.equipment.name if eq.equipment else None,
                    category=eq.equipment.category if eq.equipment else None,
                    brand_name=eq.equipment.brand.name_cn if eq.equipment and eq.equipment.brand else None,
                    purchase_date=eq.purchase_date.isoformat() if eq.purchase_date else None,
                    purchase_price=eq.purchase_price,
                    condition=eq.condition,
                    notes=eq.notes,
                    is_favorite=eq.is_favorite,
                    created_at=eq.created_at.isoformat()
                ))

            return responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户装备库失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.get(
    "/users/{user_id}/fishing-logs",
    response_model=List[FishingLogResponse],
    summary="获取用户钓鱼记录",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def get_user_fishing_logs(
    user_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回记录数量"),
    offset: int = Query(0, ge=0, description="跳过记录数")
):
    """
    获取用户钓鱼记录

    Args:
        user_id: 用户ID
        limit: 返回记录数量
        offset: 跳过记录数

    Returns:
        List[FishingLogResponse]: 钓鱼记录列表

    Raises:
        HTTPException: 用户不存在
    """
    try:
        with get_db_session() as session:
            # 首先验证用户存在
            user_repo = UserRepository(session)
            user = user_repo.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户不存在: user_id={user_id}"
                )

            # 查询钓鱼记录
            from packages.agent_fishing.tools.lure.models.user import FishingLog

            logs = (
                session.query(FishingLog)
                .filter(FishingLog.user_id == user_id)
                .order_by(FishingLog.fishing_date.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            # 转换为响应模型
            responses = []
            for log in logs:
                responses.append(FishingLogResponse(
                    log_id=log.log_id,
                    user_id=log.user_id,
                    fishing_date=log.fishing_date.isoformat(),
                    location=log.location,
                    weather_condition=log.weather_condition,
                    temperature=log.temperature,
                    fish_species=log.fish_species,
                    fish_count=log.fish_count,
                    fish_total_weight=log.fish_total_weight,
                    equipment_used=log.equipment_used,
                    lure_used=log.lure_used,
                    notes=log.notes,
                    created_at=log.created_at.isoformat()
                ))

            return responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取钓鱼记录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )
