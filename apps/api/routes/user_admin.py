"""
用户管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging
import csv
import io

from apps.api.orm.session import get_db_session
from apps.api.orm.repositories.user_repo import (
    UserRepository,
    UserEquipmentRepository,
    FishingLogRepository
)

from apps.api.schemas.user_admin import (
    UserResponse,
    UserListResponse,
    UserEquipmentResponse,
    FishingLogResponse,
    UserUpdateRequest,
    BatchUpdateRequest,
    BatchUpdateResponse,
    UserStatsResponse,
    USER_LEVELS,
    FISHING_METHODS
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
            from apps.api.models.user import User
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
                favorite_fish_species=user.preferred_fish,
                preferred_fishing_method=user.preferred_scenarios,
                location=None,  # users 表没有 location 字段
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
            from apps.api.models.user import FishingLog

            logs = (
                session.query(FishingLog)
                .filter(FishingLog.user_id == user_id)
                .order_by(FishingLog.date.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            # 转换为响应模型
            responses = []
            for log in logs:
                responses.append(FishingLogResponse(
                    id=log.id,
                    user_id=log.user_id,
                    date=log.date.isoformat() if log.date else "",
                    location=log.location,
                    weather_condition=log.weather_condition,
                    temperature=log.temperature,
                    fish_caught=log.fish_caught,
                    total_count=log.total_count,
                    total_weight=log.total_weight,
                    equipment_used=log.equipment_used,
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


# ========== 用户统计端点 ==========

@router.get(
    "/users/{user_id}/stats",
    response_model=UserStatsResponse,
    summary="获取用户统计数据",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def get_user_stats(user_id: int):
    """
    获取用户统计数据（装备数量、钓鱼记录等）

    Args:
        user_id: 用户ID

    Returns:
        UserStatsResponse: 用户统计数据
    """
    try:
        with get_db_session() as session:
            # 验证用户存在
            user_repo = UserRepository(session)
            user = user_repo.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户不存在: user_id={user_id}"
                )

            # 获取装备统计
            equipment_repo = UserEquipmentRepository(session)
            equipment_list = equipment_repo.get_user_equipment(user_id=user_id)

            equipment_count = len(equipment_list)
            favorite_count = sum(1 for eq in equipment_list if eq.is_favorite)
            equipment_total_cost = sum(eq.purchase_price or 0 for eq in equipment_list)

            # 获取钓鱼记录统计
            fishing_repo = FishingLogRepository(session)
            fishing_stats = fishing_repo.get_statistics(user_id)

            return UserStatsResponse(
                equipment_count=equipment_count,
                favorite_count=favorite_count,
                equipment_total_cost=equipment_total_cost,
                fishing_logs_count=fishing_stats['total_trips'],
                total_fish_caught=fishing_stats['total_fish'],
                total_weight=fishing_stats['total_weight']
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


# ========== 用户更新端点 ==========

@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="更新用户信息",
    dependencies=[Depends(require_permission(PermissionEnum.USER_UPDATE))]
)
async def update_user(user_id: int, data: UserUpdateRequest):
    """
    更新用户信息

    Args:
        user_id: 用户ID
        data: 更新数据

    Returns:
        UserResponse: 更新后的用户信息
    """
    try:
        with get_db_session() as session:
            user_repo = UserRepository(session)
            user = user_repo.get(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户��存在: user_id={user_id}"
                )

            # 验证用户水平
            if data.user_level and data.user_level not in USER_LEVELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的用户水平，必须是: {USER_LEVELS}"
                )

            # 更新字段
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            session.commit()
            session.refresh(user)

            return UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                user_level=user.user_level,
                fishing_experience_years=user.fishing_experience_years,
                favorite_fish_species=user.preferred_fish,
                preferred_fishing_method=user.preferred_scenarios,
                location=None,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


# ========== 批量更新端点 ==========

@router.post(
    "/users/batch-update",
    response_model=BatchUpdateResponse,
    summary="批量更新用户",
    dependencies=[Depends(require_permission(PermissionEnum.USER_UPDATE))]
)
async def batch_update_users(data: BatchUpdateRequest):
    """
    批量更新用户信息

    Args:
        data: 批量更新请求

    Returns:
        BatchUpdateResponse: 批量更新结果
    """
    try:
        # 验证用户水平
        if data.user_level and data.user_level not in USER_LEVELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的用户水平，必须是: {USER_LEVELS}"
            )

        with get_db_session() as session:
            from apps.api.models.user import User

            # 查找所有用户
            users = session.query(User).filter(User.user_id.in_(data.user_ids)).all()

            if not users:
                return BatchUpdateResponse(
                    success=False,
                    updated_count=0,
                    message="没有找到要更新的用户"
                )

            # 批量更新
            updated_count = 0
            for user in users:
                if data.user_level:
                    user.user_level = data.user_level
                updated_count += 1

            session.commit()

            return BatchUpdateResponse(
                success=True,
                updated_count=updated_count,
                message=f"成功更新 {updated_count} 个用户"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失败: {str(e)}"
        )


# ========== 用户导出端点 ==========

@router.get(
    "/users/export",
    summary="导出用户列表",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def export_users(
    user_level: Optional[str] = Query(None, description="用户水平过滤"),
    user_ids: Optional[str] = Query(None, description="用户ID列表，逗号分隔")
):
    """
    导出用户列表为CSV

    Args:
        user_level: 用户水平过滤
        user_ids: 用户ID列表

    Returns:
        StreamingResponse: CSV文件流
    """
    try:
        with get_db_session() as session:
            from apps.api.models.user import User
            from sqlalchemy import and_

            query = session.query(User)
            filters = []

            if user_level:
                filters.append(User.user_level == user_level)

            if user_ids:
                id_list = [int(id.strip()) for id in user_ids.split(',') if id.strip()]
                if id_list:
                    filters.append(User.user_id.in_(id_list))

            if filters:
                query = query.filter(and_(*filters))

            users = query.all()

            # 生成CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # 写入标题行
            writer.writerow([
                'ID', '用户名', '邮箱', '手机', '用户水平',
                '钓龄(年)', '喜欢鱼种', '偏好钓法', '注册时间'
            ])

            # 写入数据
            for user in users:
                writer.writerow([
                    user.user_id,
                    user.username,
                    user.email or '',
                    user.phone or '',
                    user.user_level,
                    user.fishing_experience_years or '',
                    user.preferred_fish or '',
                    user.preferred_scenarios or '',
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
                ])

            output.seek(0)

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=users_export.csv"
                }
            )

    except Exception as e:
        logger.error(f"导出用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


# ========== 选项数据端点 ==========

@router.get(
    "/users/options",
    summary="获取用户管理选项数据",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def get_user_options():
    """
    获取用户管理相关的选项数据

    Returns:
        dict: 选项数据
    """
    return {
        "user_levels": USER_LEVELS,
        "fishing_methods": FISHING_METHODS
    }
