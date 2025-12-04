"""
用户装备管理 API 路由

提供用户装备库管理的 RESTful 接口
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from packages.agent_fishing.tools.user_equipment import (
    UserEquipmentManager,
    UserBasedRecommender,
)
from packages.agent_fishing.tools.lure.database import get_db

from ..schemas.user_equipment import (
    UserCreate,
    UserResponse,
    AddEquipmentRequest,
    UserEquipmentResponse,
    UserEquipmentListResponse,
    RecommendRequest,
    RecommendResponse,
    UserStatisticsResponse,
    CategoryStatistics,
    SuccessResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# 懒加载服务实例
_manager: Optional[UserEquipmentManager] = None
_recommender: Optional[UserBasedRecommender] = None


def get_manager() -> UserEquipmentManager:
    """获取 UserEquipmentManager 实例"""
    global _manager
    if _manager is None:
        db = get_db()
        _manager = UserEquipmentManager(db)
    return _manager


def get_recommender() -> UserBasedRecommender:
    """获取 UserBasedRecommender 实例"""
    global _recommender
    if _recommender is None:
        db = get_db()
        manager = get_manager()
        _recommender = UserBasedRecommender(db, manager)
    return _recommender


# ========== 用户管理端点 ==========


@router.post(
    "/users",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户账户",
)
async def create_user(user_data: UserCreate):
    """
    创建新用户

    Args:
        user_data: 用户创建数据

    Returns:
        SuccessResponse: 包含用户ID的成功响应

    Raises:
        HTTPException: 如果用户名已存在或创建失败
    """
    try:
        manager = get_manager()

        user_id = manager.create_user(
            username=user_data.username,
            nickname=user_data.nickname,
            email=user_data.email,
            user_level=user_data.user_level,
            fishing_experience_years=user_data.fishing_experience_years,
            preferred_fish=user_data.preferred_fish,
        )

        logger.info(f"创建用户成功: user_id={user_id}, username={user_data.username}")

        return SuccessResponse(
            success=True,
            message=f"用户创建成功",
            data={"user_id": user_id, "username": user_data.username},
        )

    except ValueError as e:
        logger.warning(f"创建用户失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        logger.error(f"创建用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}",
        )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="获取用户信息",
    description="根据用户ID获取用户详细信息",
)
async def get_user(user_id: int):
    """
    获取用户信息

    Args:
        user_id: 用户ID

    Returns:
        UserResponse: 用户信息

    Raises:
        HTTPException: 如果用户不存在
    """
    try:
        manager = get_manager()
        user = manager.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"用户不存在: {user_id}"
            )

        return UserResponse(**user)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"获取用户信息失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}",
        )


# ========== 装备管理端点 ==========


@router.post(
    "/users/{user_id}/equipment",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加装备到用户库",
    description="将装备添加到用户的装备库",
)
async def add_equipment(user_id: int, equipment_data: AddEquipmentRequest):
    """
    添加装备到用户库

    Args:
        user_id: 用户ID
        equipment_data: 装备数据

    Returns:
        SuccessResponse: 成功响应

    Raises:
        HTTPException: 如果装备不存在或已添加
    """
    try:
        manager = get_manager()

        # 检查用户是否存在
        user = manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"用户不存在: {user_id}"
            )

        # 添加装备
        record_id = manager.add_equipment(
            user_id=user_id,
            equipment_id=equipment_data.equipment_id,
            purchase_price=equipment_data.purchase_price,
            purchase_date=equipment_data.purchase_date,
            purchase_source=equipment_data.purchase_source,
            notes=equipment_data.notes,
            tags=equipment_data.tags,
        )

        logger.info(
            f"添加装备成功: user_id={user_id}, equipment_id={equipment_data.equipment_id}"
        )

        return SuccessResponse(
            success=True,
            message="装备添加成功",
            data={"record_id": record_id, "equipment_id": equipment_data.equipment_id},
        )

    except ValueError as e:
        logger.warning(f"添加装备失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"添加装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加装备失败: {str(e)}",
        )


@router.get(
    "/users/{user_id}/equipment",
    response_model=UserEquipmentListResponse,
    summary="查询用户装备列表",
    description="获取用户装备库中的所有装备",
)
async def list_equipment(
    user_id: int,
    category: Optional[str] = Query(None, description="装备类别过滤"),
    only_favorites: bool = Query(False, description="仅显示收藏装备"),
):
    """
    查询用户装备列表

    Args:
        user_id: 用户ID
        category: 装备类别（可选）
        only_favorites: 是否只显示收藏

    Returns:
        UserEquipmentListResponse: 装备列表

    Raises:
        HTTPException: 如果用户不存在
    """
    try:
        manager = get_manager()

        # 检查用户是否存在
        user = manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"用户不存在: {user_id}"
            )

        # 查询装备列表
        equipment_list = manager.list_user_equipment(
            user_id=user_id, category=category, only_favorites=only_favorites
        )

        # 转换为响应模型
        equipment_responses = []
        for eq in equipment_list:
            equipment_responses.append(
                UserEquipmentResponse(
                    id=eq.id,
                    user_id=eq.user_id,
                    equipment_id=eq.equipment_id,
                    equipment_name=eq.equipment_name,
                    category=eq.category,
                    brand_name=eq.brand_name,
                    model=eq.model,
                    purchase_date=eq.purchase_date,
                    purchase_price=eq.purchase_price,
                    purchase_source=eq.purchase_source,
                    condition=eq.condition,
                    usage_frequency=eq.usage_frequency,
                    notes=eq.notes,
                    is_favorite=eq.is_favorite,
                    tags=eq.tags,
                    created_at=eq.created_at,
                )
            )

        return UserEquipmentListResponse(
            total=len(equipment_responses), equipment_list=equipment_responses
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"查询装备列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询装备列表失败: {str(e)}",
        )


@router.delete(
    "/users/{user_id}/equipment/{equipment_id}",
    response_model=SuccessResponse,
    summary="删除装备",
    description="从用户装备库中删除指定装备",
)
async def remove_equipment(user_id: int, equipment_id: int):
    """
    删除装备

    Args:
        user_id: 用户ID
        equipment_id: 装备ID

    Returns:
        SuccessResponse: 成功响应

    Raises:
        HTTPException: 如果装备不存在
    """
    try:
        manager = get_manager()

        # 检查用户是否存在
        user = manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"用户不存在: {user_id}"
            )

        # 删除装备
        success = manager.remove_equipment(user_id, equipment_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"装备不在用户库中: equipment_id={equipment_id}",
            )

        logger.info(f"删除装备成功: user_id={user_id}, equipment_id={equipment_id}")

        return SuccessResponse(
            success=True,
            message="装备删除成功",
            data={"equipment_id": equipment_id},
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"删除装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除装备失败: {str(e)}",
        )


# ========== 推荐端点 ==========


@router.post(
    "/users/{user_id}/recommend",
    response_model=RecommendResponse,
    summary="基于用户装备推荐",
    description="根据用户已有装备推荐新装备或提供搭配建议",
)
async def recommend_equipment(user_id: int, request: RecommendRequest):
    """
    基于用户装备推荐

    Args:
        user_id: 用户ID
        request: 推荐请求（包含推荐类型）

    Returns:
        RecommendResponse: Markdown格式的推荐报告

    Raises:
        HTTPException: 如果用户不存在或推荐失败
    """
    try:
        manager = get_manager()
        recommender = get_recommender()

        # 检查用户是否存在
        user = manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"用户不存在: {user_id}"
            )

        # 根据类型调用推荐方法
        if request.need_type == "upgrade":
            recommendation = recommender.recommend_upgrade(user_id)
        elif request.need_type == "complete":
            recommendation = recommender.recommend_complete_set(user_id)
        elif request.need_type == "match":
            recommendation = recommender.recommend_matching(user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的推荐类型: {request.need_type}",
            )

        logger.info(f"推荐成功: user_id={user_id}, need_type={request.need_type}")

        return RecommendResponse(
            recommendation=recommendation, need_type=request.need_type
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"推荐失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推荐失败: {str(e)}",
        )


# ========== 统计端点 ==========


@router.get(
    "/users/{user_id}/statistics",
    response_model=UserStatisticsResponse,
    summary="获取用户装备统计",
    description="获取用户装备的统计信息",
)
async def get_statistics(user_id: int):
    """
    获取用户装备统计

    Args:
        user_id: 用户ID

    Returns:
        UserStatisticsResponse: 统计信息

    Raises:
        HTTPException: 如果用户不存在
    """
    try:
        manager = get_manager()

        # 检查用户是否存在
        user = manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"用户不存在: {user_id}"
            )

        # 获取统计信息
        stats = manager.get_equipment_statistics(user_id)

        # 转换类别统计
        category_stats = [
            CategoryStatistics(
                category=cat["category"],
                count=cat["count"],
                avg_price=cat.get("avg_price"),
                total_price=cat.get("total_price"),
            )
            for cat in stats["by_category"]
        ]

        return UserStatisticsResponse(
            user_id=stats["user_id"],
            total_count=stats["total_count"],
            total_spent=stats["total_spent"],
            favorite_count=stats["favorite_count"],
            by_category=category_stats,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}",
        )
