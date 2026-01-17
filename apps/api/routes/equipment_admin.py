"""
装备管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status, Response
from typing import Optional
import logging
from functools import lru_cache
import hashlib
import json

from apps.api.orm.session import get_db_session
from apps.api.orm.repositories.equipment_repo import EquipmentRepository
from apps.api.orm.repositories.brand_repo import BrandRepository

from apps.api.schemas.equipment_admin import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentListResponse,
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BatchDeleteRequest,
    BatchDeleteResponse,
    BatchUpdateRequest,
    BatchUpdateResponse,
    EquipmentStatsResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


def add_cache_headers(response: Response, max_age: int = 60, etag: str = None):
    """添加缓存控制头部"""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    if etag:
        response.headers["ETag"] = f'"{etag}"'


# ========== 装备管理端点 ==========

@router.post(
    "/equipment",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建装备",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def create_equipment(
    equipment_data: EquipmentCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))
):
    """
    创建装备

    Args:
        equipment_data: 装备数据（包含 specs）

    Returns:
        EquipmentResponse: 创建的装备信息

    Raises:
        HTTPException: 品牌不存在或创建失败
    """
    try:
        with get_db_session() as session:
            repo = EquipmentRepository(session)
            brand_repo = BrandRepository(session)

            # 验证品牌是否存在
            brand = brand_repo.get(equipment_data.brand_id)
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"品牌不存在: brand_id={equipment_data.brand_id}"
                )

            # 准备装备数据（排除非模型字段）
            equipment_dict = equipment_data.model_dump(exclude={'specs', 'price_currency'})
            spec_dict = equipment_data.specs.model_dump() if equipment_data.specs else None

            # 创建装备（包含规格）
            equipment = repo.create_with_specs(
                equipment_data=equipment_dict,
                spec_data=spec_dict
            )

            session.commit()

            logger.info(
                f"装备创建成功: equipment_id={equipment.equipment_id}, "
                f"name={equipment.name}, user={current_user.username}"
            )

            # 提取规格数据
            specs = None
            if equipment_data.specs:
                specs = spec_dict

            # 构造响应
            return EquipmentResponse(
                equipment_id=equipment.equipment_id,
                name=equipment.name,
                category=equipment.category,
                brand_id=equipment.brand_id,
                brand_name=brand.name_cn,
                model=equipment.model,
                price_min=equipment.price_min,
                price_max=equipment.price_max,
                price_currency="CNY",  # 默认使用人民币
                description=equipment.description,
                features=equipment.features,
                user_level=equipment.user_level,
                is_active=equipment.is_active,
                source=equipment.source,
                source_url=equipment.source_url,
                created_at=equipment.created_at.isoformat(),
                updated_at=equipment.updated_at.isoformat(),
                specs=specs
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建装备失败: {str(e)}"
        )


@router.get(
    "/equipment",
    response_model=EquipmentListResponse,
    summary="查询装备列表",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_READ))]
)
async def list_equipment(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="类别过滤"),
    brand_id: Optional[int] = Query(None, description="品牌过滤"),
    user_level: Optional[str] = Query(None, description="适用水平过滤"),
    price_min: Optional[float] = Query(None, description="最低价格过滤"),
    price_max: Optional[float] = Query(None, description="最高价格过滤"),
    is_active: Optional[bool] = Query(None, description="是否启用过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索（名称、描述）"),
    # 通用扩展参数
    source: Optional[str] = Query(None, description="数据来源过滤"),
    model: Optional[str] = Query(None, description="型号搜索"),
    created_after: Optional[str] = Query(None, description="创建时间起始（ISO格式）"),
    created_before: Optional[str] = Query(None, description="创建时间截止（ISO格式）"),
    # 鱼竿专属筛选参数
    power: Optional[str] = Query(None, description="调性过滤（鱼竿专属）"),
    action: Optional[str] = Query(None, description="动作过滤（鱼竿专属）"),
    length_min: Optional[float] = Query(None, description="最小长度过滤（鱼竿专属）"),
    length_max: Optional[float] = Query(None, description="最大长度过滤（鱼竿专属）"),
    rod_lure_weight_min: Optional[float] = Query(None, description="适用饵重最小值（鱼竿专属）"),
    rod_lure_weight_max: Optional[float] = Query(None, description="适用饵重最大值（鱼竿专属）"),
    sections: Optional[int] = Query(None, description="节数过滤（鱼竿专属）"),
    # 渔轮专属筛选参数
    reel_type: Optional[str] = Query(None, description="轮类型过滤（渔轮专属）"),
    max_drag_min: Optional[float] = Query(None, description="最大拽力最小值（渔轮专属）"),
    max_drag_max: Optional[float] = Query(None, description="最大拽力最大值（渔轮专属）"),
    reel_weight_min: Optional[float] = Query(None, description="轮自重最小值（渔轮专属）"),
    reel_weight_max: Optional[float] = Query(None, description="轮自重最大值（渔轮专属）"),
    # 鱼线专属筛选参数
    line_type: Optional[str] = Query(None, description="线型过滤（鱼线专属）"),
    diameter_min: Optional[float] = Query(None, description="线径最小值（鱼线专属）"),
    diameter_max: Optional[float] = Query(None, description="线径最大值（鱼线专属）"),
    strength_min: Optional[float] = Query(None, description="拉力最小值（鱼线专属）"),
    strength_max: Optional[float] = Query(None, description="拉力最大值（鱼线专属）"),
    # 拟饵专属筛选参数
    lure_category: Optional[str] = Query(None, description="拟饵分类过滤（拟饵专属）"),
    lure_weight_min: Optional[float] = Query(None, description="拟饵重量最小值（拟饵专属）"),
    lure_weight_max: Optional[float] = Query(None, description="拟饵重量最大值（拟饵专属）"),
    diving_depth_min: Optional[float] = Query(None, description="潜深最小值（拟饵专属）"),
    diving_depth_max: Optional[float] = Query(None, description="潜深最大值（拟饵专属）"),
    # 新增：鱼竿扩展筛选
    rod_weight_min: Optional[float] = Query(None, description="竿自重最小值（鱼竿专属，克）"),
    rod_weight_max: Optional[float] = Query(None, description="竿自重最大值（鱼竿专属，克）"),
    guide_type: Optional[str] = Query(None, description="导环类型过滤（鱼竿专属）"),
    handle_type: Optional[str] = Query(None, description="握把类型过滤（鱼竿专属）"),
    # 新增：渔轮扩展筛选
    gear_ratio: Optional[str] = Query(None, description="齿比过滤（渔轮专属，如5.2:1）"),
    bearings_min: Optional[int] = Query(None, description="轴承数最小值（渔轮专属）"),
    bearings_max: Optional[int] = Query(None, description="轴承数最大值（渔轮专属）"),
    # 新增：拟饵扩展筛选
    lure_type: Optional[str] = Query(None, description="拟饵类型过滤（拟饵专属）"),
    lure_length_min: Optional[float] = Query(None, description="拟饵长度最小值（拟饵专属，cm）"),
    lure_length_max: Optional[float] = Query(None, description="拟饵长度最大值（拟饵专属，cm）"),
    # 排序参数
    sort_by: Optional[str] = Query(None, description="排序字段: name/price_min/price_max/created_at/updated_at/category/brand_name/length/weight/action/power/sections"),
    sort_order: Optional[str] = Query("desc", description="排序方向: asc/desc"),
):
    """
    查询装备列表（分页 + 多条件筛选）

    Returns:
        EquipmentListResponse: 分页装备列表
    """
    try:
        from datetime import datetime
        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 检查是否有各类别专属筛选参数
            has_rod_filters = any([power, action, length_min, length_max, rod_lure_weight_min, rod_lure_weight_max, sections, rod_weight_min, rod_weight_max, guide_type, handle_type])
            has_reel_filters = any([reel_type, max_drag_min, max_drag_max, reel_weight_min, reel_weight_max, gear_ratio, bearings_min, bearings_max])
            has_line_filters = any([line_type, diameter_min, diameter_max, strength_min, strength_max])
            has_lure_filters = any([lure_category, lure_weight_min, lure_weight_max, diving_depth_min, diving_depth_max, lure_type, lure_length_min, lure_length_max])

            # 通用查询参数
            common_kwargs = {
                'brand_id': brand_id,
                'price_min': price_min,
                'price_max': price_max,
                'user_level': user_level,
                'is_active': is_active if is_active is not None else True,
                'keyword': keyword,
                'source': source,
                'model': model,
                'created_after': created_after,
                'created_before': created_before,
                'limit': page_size,
                'offset': (page - 1) * page_size,
                'preload': True,
                'sort_by': sort_by,
                'sort_order': sort_order,
            }

            # 根据类别专属筛选选择查询方法
            if has_rod_filters and (category == '鱼竿' or category is None):
                equipment_list = repo.search_rods(
                    power=power,
                    action=action,
                    length_min=length_min,
                    length_max=length_max,
                    lure_weight_min=rod_lure_weight_min,
                    lure_weight_max=rod_lure_weight_max,
                    sections=sections,
                    weight_min=rod_weight_min,
                    weight_max=rod_weight_max,
                    guide_type=guide_type,
                    handle_type=handle_type,
                    **common_kwargs
                )
            elif has_reel_filters and (category == '渔轮' or category is None):
                equipment_list = repo.search_reels(
                    reel_type=reel_type,
                    max_drag_min=max_drag_min,
                    max_drag_max=max_drag_max,
                    weight_min=reel_weight_min,
                    weight_max=reel_weight_max,
                    gear_ratio=gear_ratio,
                    bearings_min=bearings_min,
                    bearings_max=bearings_max,
                    **common_kwargs
                )
            elif has_line_filters and (category == '鱼线' or category is None):
                equipment_list = repo.search_lines(
                    line_type=line_type,
                    diameter_min=diameter_min,
                    diameter_max=diameter_max,
                    strength_min=strength_min,
                    strength_max=strength_max,
                    **common_kwargs
                )
            elif has_lure_filters and (category == '拟饵' or category is None):
                equipment_list = repo.search_lures(
                    lure_category=lure_category,
                    weight_min=lure_weight_min,
                    weight_max=lure_weight_max,
                    diving_depth_min=diving_depth_min,
                    diving_depth_max=diving_depth_max,
                    lure_type=lure_type,
                    length_min=lure_length_min,
                    length_max=lure_length_max,
                    **common_kwargs
                )
            else:
                # 通用查询
                equipment_list = repo.search(
                    category=category,
                    **common_kwargs
                )

            # 统计总数（使用相同的过滤条件）
            from sqlalchemy import and_, or_
            from apps.api.models.equipment import Equipment, RodSpec, ReelSpec, LineSpec, LureSpec

            # 根据类别专属筛选构建总数查询
            if has_rod_filters and (category == '鱼竿' or category is None):
                total_query = session.query(Equipment).join(RodSpec)
                if power:
                    total_query = total_query.filter(RodSpec.power == power)
                if action:
                    total_query = total_query.filter(RodSpec.action == action)
                if length_min:
                    total_query = total_query.filter(RodSpec.length >= length_min)
                if length_max:
                    total_query = total_query.filter(RodSpec.length <= length_max)
                if rod_lure_weight_min:
                    total_query = total_query.filter(
                        or_(RodSpec.lure_weight_min >= rod_lure_weight_min, RodSpec.lure_weight_max >= rod_lure_weight_min)
                    )
                if rod_lure_weight_max:
                    total_query = total_query.filter(
                        or_(RodSpec.lure_weight_min <= rod_lure_weight_max, RodSpec.lure_weight_max <= rod_lure_weight_max)
                    )
                if sections:
                    total_query = total_query.filter(RodSpec.sections == sections)
            elif has_reel_filters and (category == '渔轮' or category is None):
                total_query = session.query(Equipment).join(ReelSpec)
                if reel_type:
                    total_query = total_query.filter(ReelSpec.reel_type == reel_type)
                if max_drag_min:
                    total_query = total_query.filter(ReelSpec.max_drag >= max_drag_min)
                if max_drag_max:
                    total_query = total_query.filter(ReelSpec.max_drag <= max_drag_max)
                if reel_weight_min:
                    total_query = total_query.filter(ReelSpec.weight >= reel_weight_min)
                if reel_weight_max:
                    total_query = total_query.filter(ReelSpec.weight <= reel_weight_max)
            elif has_line_filters and (category == '鱼线' or category is None):
                total_query = session.query(Equipment).join(LineSpec)
                if line_type:
                    total_query = total_query.filter(LineSpec.line_type == line_type)
                if diameter_min:
                    total_query = total_query.filter(LineSpec.diameter >= diameter_min)
                if diameter_max:
                    total_query = total_query.filter(LineSpec.diameter <= diameter_max)
                if strength_min:
                    total_query = total_query.filter(LineSpec.strength_lb >= strength_min)
                if strength_max:
                    total_query = total_query.filter(LineSpec.strength_lb <= strength_max)
            elif has_lure_filters and (category == '拟饵' or category is None):
                total_query = session.query(Equipment).join(LureSpec)
                if lure_category:
                    total_query = total_query.filter(LureSpec.lure_category == lure_category)
                if lure_weight_min:
                    total_query = total_query.filter(LureSpec.weight >= lure_weight_min)
                if lure_weight_max:
                    total_query = total_query.filter(LureSpec.weight <= lure_weight_max)
                if diving_depth_min:
                    total_query = total_query.filter(
                        or_(LureSpec.diving_depth_min >= diving_depth_min, LureSpec.diving_depth_max >= diving_depth_min)
                    )
                if diving_depth_max:
                    total_query = total_query.filter(
                        or_(LureSpec.diving_depth_min <= diving_depth_max, LureSpec.diving_depth_max <= diving_depth_max)
                    )
            else:
                total_query = session.query(repo.model)
                if category:
                    total_query = total_query.filter(Equipment.category == category)

            # 应用通用过滤条件
            filters = []
            if brand_id:
                filters.append(Equipment.brand_id == brand_id)
            if user_level:
                filters.append(Equipment.user_level == user_level)
            if is_active is not None:
                filters.append(Equipment.is_active == is_active)
            if price_min is not None:
                filters.append(
                    or_(
                        Equipment.price_min >= price_min,
                        Equipment.price_max >= price_min
                    )
                )
            if price_max is not None:
                filters.append(
                    or_(
                        Equipment.price_min <= price_max,
                        Equipment.price_max <= price_max
                    )
                )
            if keyword:
                keyword_filter = or_(
                    Equipment.name.like(f"%{keyword}%"),
                    Equipment.description.like(f"%{keyword}%"),
                    Equipment.features.like(f"%{keyword}%")
                )
                filters.append(keyword_filter)
            # 通用扩展筛选
            if source:
                filters.append(Equipment.source == source)
            if model:
                filters.append(Equipment.model.like(f"%{model}%"))
            if created_after:
                try:
                    dt = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
                    filters.append(Equipment.created_at >= dt)
                except ValueError:
                    pass
            if created_before:
                try:
                    dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
                    filters.append(Equipment.created_at <= dt)
                except ValueError:
                    pass

            if filters:
                total_query = total_query.filter(and_(*filters))

            total = total_query.count()

            # 转换为响应模型
            items = []
            for eq in equipment_list:
                # 提取规格数据
                specs = None
                if eq.category == "鱼竿" and eq.rod_spec:
                    specs = eq.rod_spec.to_dict()
                elif eq.category == "渔轮" and eq.reel_spec:
                    specs = eq.reel_spec.to_dict()
                elif eq.category == "鱼线" and eq.line_spec:
                    specs = eq.line_spec.to_dict()
                elif eq.category == "拟饵" and eq.lure_spec:
                    specs = eq.lure_spec.to_dict()

                items.append(EquipmentResponse(
                    equipment_id=eq.equipment_id,
                    name=eq.name,
                    category=eq.category,
                    brand_id=eq.brand_id,
                    brand_name=eq.brand.name_cn if eq.brand else None,
                    model=eq.model,
                    price_min=eq.price_min,
                    price_max=eq.price_max,
                    price_currency="CNY",  # 默认使用人民币
                    description=eq.description,
                    features=eq.features,
                    user_level=eq.user_level,
                    is_active=eq.is_active,
                    source=eq.source,
                    source_url=eq.source_url,
                    created_at=eq.created_at.isoformat(),
                    updated_at=eq.updated_at.isoformat(),
                    specs=specs
                ))

            return EquipmentListResponse(
                total=total,
                page=page,
                page_size=page_size,
                items=items
            )

    except Exception as e:
        logger.error(f"查询装备列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


# ========== 批量操作端点（必须放在 /equipment/{equipment_id} 之前） ==========

@router.get(
    "/equipment/stats",
    response_model=EquipmentStatsResponse,
    summary="获取装备统计",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_READ))]
)
async def get_equipment_stats():
    """
    获取装备分类统计

    Returns:
        EquipmentStatsResponse: 统计数据
    """
    try:
        from sqlalchemy import func
        from apps.api.models.equipment import Equipment
        from apps.api.models.brand import Brand

        with get_db_session() as session:
            # 总数统计
            total = session.query(func.count(Equipment.equipment_id)).scalar()
            active_count = session.query(func.count(Equipment.equipment_id)).filter(
                Equipment.is_active == True
            ).scalar()
            inactive_count = total - active_count

            # 按类别统计（只统计启用的）
            category_stats = session.query(
                Equipment.category,
                func.count(Equipment.equipment_id).label('count')
            ).filter(
                Equipment.is_active == True
            ).group_by(Equipment.category).all()

            by_category = {cat: count for cat, count in category_stats}

            # 按品牌统计（前10）
            brand_stats = session.query(
                Brand.brand_id,
                Brand.name_cn,
                func.count(Equipment.equipment_id).label('count')
            ).join(
                Equipment, Equipment.brand_id == Brand.brand_id
            ).filter(
                Equipment.is_active == True
            ).group_by(
                Brand.brand_id, Brand.name_cn
            ).order_by(
                func.count(Equipment.equipment_id).desc()
            ).limit(10).all()

            by_brand = [
                {'brand_id': bid, 'name': name, 'count': count}
                for bid, name, count in brand_stats
            ]

            # 按用户水平统计
            level_stats = session.query(
                Equipment.user_level,
                func.count(Equipment.equipment_id).label('count')
            ).filter(
                Equipment.is_active == True
            ).group_by(Equipment.user_level).all()

            by_user_level = {level or '未设置': count for level, count in level_stats}

            return EquipmentStatsResponse(
                total=total,
                active_count=active_count,
                inactive_count=inactive_count,
                by_category=by_category,
                by_brand=by_brand,
                by_user_level=by_user_level
            )

    except Exception as e:
        logger.error(f"获取装备统计失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}"
        )


@router.post(
    "/equipment/batch-delete",
    response_model=BatchDeleteResponse,
    summary="批量删除装备",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_DELETE))]
)
async def batch_delete_equipment(
    request: BatchDeleteRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.EQUIPMENT_DELETE))
):
    """
    批量删除装备（软删除：设置 is_active=False）

    Args:
        request: 包含要删除的装备ID列表

    Returns:
        BatchDeleteResponse: 删除结果
    """
    try:
        from apps.api.models.equipment import Equipment

        with get_db_session() as session:
            # 查询要删除的装备
            equipment_list = session.query(Equipment).filter(
                Equipment.equipment_id.in_(request.ids),
                Equipment.is_active == True  # 只删除启用的装备
            ).all()

            deleted_count = 0
            for equipment in equipment_list:
                equipment.is_active = False
                deleted_count += 1

            session.commit()

            logger.info(
                f"批量删除装备成功: deleted_count={deleted_count}, "
                f"requested_count={len(request.ids)}, user={current_user.username}"
            )

            return BatchDeleteResponse(
                deleted_count=deleted_count,
                message=f"成功删除 {deleted_count} 个装备"
            )

    except Exception as e:
        logger.error(f"批量删除装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除失败: {str(e)}"
        )


@router.post(
    "/equipment/batch-update",
    response_model=BatchUpdateResponse,
    summary="批量更新装备",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_UPDATE))]
)
async def batch_update_equipment(
    request: BatchUpdateRequest,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.EQUIPMENT_UPDATE))
):
    """
    批量更新装备的指定字段

    支持更新的字段：
    - brand_id: 品牌ID
    - user_level: 适用水平（入门/新手/进阶/高手）
    - is_active: 启用/禁用状态

    Args:
        request: 包含要更新的装备ID列表和更新字段

    Returns:
        BatchUpdateResponse: 更新结果
    """
    try:
        from apps.api.models.equipment import Equipment

        # 只允许更新指定字段
        allowed_fields = {'brand_id', 'user_level', 'is_active'}
        invalid_fields = set(request.updates.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持批量更新的字段: {', '.join(invalid_fields)}"
            )

        # 验证 user_level 值
        if 'user_level' in request.updates:
            valid_levels = {'入门', '新手', '进阶', '高手'}
            if request.updates['user_level'] not in valid_levels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的用户水平: {request.updates['user_level']}"
                )

        # 验证 brand_id 存在
        if 'brand_id' in request.updates:
            with get_db_session() as session:
                brand_repo_instance = BrandRepository(session)
                brand = brand_repo_instance.get(request.updates['brand_id'])
                if not brand:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"品牌不存在: brand_id={request.updates['brand_id']}"
                    )

        with get_db_session() as session:
            # 查询要更新的装备
            equipment_list = session.query(Equipment).filter(
                Equipment.equipment_id.in_(request.ids)
            ).all()

            updated_count = 0
            for equipment in equipment_list:
                for field, value in request.updates.items():
                    setattr(equipment, field, value)
                updated_count += 1

            session.commit()

            logger.info(
                f"批量更新装备成功: updated_count={updated_count}, "
                f"fields={list(request.updates.keys())}, user={current_user.username}"
            )

            return BatchUpdateResponse(
                updated_count=updated_count,
                message=f"成功更新 {updated_count} 个装备"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失败: {str(e)}"
        )


# ========== 装备详情端点 ==========

@router.get(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    summary="获取装备详情",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_READ))]
)
async def get_equipment(equipment_id: int):
    """
    获取装备详情（包含规格）

    Args:
        equipment_id: 装备ID

    Returns:
        EquipmentResponse: 装备详细信息

    Raises:
        HTTPException: 装备不存在
    """
    try:
        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 查询装备（预加载关联数据）
            equipment = repo.get_with_details(equipment_id)

            if not equipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"装备不存在: equipment_id={equipment_id}"
                )

            # 提取规格（返回完整字段）
            specs = None
            if equipment.category == "鱼竿" and equipment.rod_spec:
                specs = equipment.rod_spec.to_dict()
            elif equipment.category == "渔轮" and equipment.reel_spec:
                specs = equipment.reel_spec.to_dict()
            elif equipment.category == "鱼线" and equipment.line_spec:
                specs = equipment.line_spec.to_dict()
            elif equipment.category == "拟饵" and equipment.lure_spec:
                specs = equipment.lure_spec.to_dict()

            return EquipmentResponse(
                equipment_id=equipment.equipment_id,
                name=equipment.name,
                category=equipment.category,
                brand_id=equipment.brand_id,
                brand_name=equipment.brand.name_cn if equipment.brand else None,
                model=equipment.model,
                price_min=equipment.price_min,
                price_max=equipment.price_max,
                price_currency="CNY",  # 默认使用人民币
                description=equipment.description,
                features=equipment.features,
                user_level=equipment.user_level,
                is_active=equipment.is_active,
                source=equipment.source,
                source_url=equipment.source_url,
                created_at=equipment.created_at.isoformat(),
                updated_at=equipment.updated_at.isoformat(),
                specs=specs
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取装备详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.put(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    summary="更新装备",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_UPDATE))]
)
async def update_equipment(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.EQUIPMENT_UPDATE))
):
    """
    更新装备（支持部分更新，包含规格）

    Args:
        equipment_id: 装备ID
        equipment_data: 更新数据（包含 specs）

    Returns:
        EquipmentResponse: 更新后的装备信息

    Raises:
        HTTPException: 装备不存在或更新失败
    """
    try:
        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 准备更新数据
            update_dict = equipment_data.model_dump(exclude_none=True, exclude={'specs'})
            spec_dict = equipment_data.specs.model_dump() if equipment_data.specs else None

            # 使用 update_with_specs 同时更新装备和规格
            equipment = repo.update_with_specs(
                equipment_id=equipment_id,
                equipment_data=update_dict,
                spec_data=spec_dict
            )

            if not equipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"装备不存在: equipment_id={equipment_id}"
                )

            session.commit()

            logger.info(
                f"装备更新成功: equipment_id={equipment_id}, "
                f"user={current_user.username}"
            )

            # 返回更新后的装备（通过get_equipment获取完整信息）
            return await get_equipment(equipment_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.delete(
    "/equipment/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除装备",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_DELETE))]
)
async def delete_equipment(
    equipment_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.EQUIPMENT_DELETE))
):
    """
    删除装备（软删除：设置 is_active=False）

    Args:
        equipment_id: 装备ID

    Raises:
        HTTPException: 装备不存在
    """
    try:
        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 检查装备是否存在
            equipment = repo.get(equipment_id)
            if not equipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"装备不存在: equipment_id={equipment_id}"
                )

            # 软删除
            equipment.is_active = False
            session.commit()

            logger.info(
                f"装备删除成功: equipment_id={equipment_id}, "
                f"user={current_user.username}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


# ========== 品牌管理端点 ==========

@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建品牌",
    dependencies=[Depends(require_permission(PermissionEnum.BRAND_CREATE))]
)
async def create_brand(
    brand_data: BrandCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.BRAND_CREATE))
):
    """创建品牌"""
    try:
        with get_db_session() as session:
            repo = BrandRepository(session)

            # 检查品牌名是否已存在
            existing = repo.get_by_name(brand_data.name_cn)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"品牌已存在: {brand_data.name_cn}"
                )

            # 创建品牌
            brand = repo.create_brand(
                name_cn=brand_data.name_cn,
                name_en=brand_data.name_en,
                country=brand_data.country,
                description=brand_data.description,
                logo_url=brand_data.logo_url
            )

            session.commit()

            logger.info(f"品牌创建成功: brand_id={brand.brand_id}, name={brand.name_cn}")

            return BrandResponse(
                brand_id=brand.brand_id,
                name_cn=brand.name_cn,
                name_en=brand.name_en,
                country=brand.country,
                description=brand.description,
                logo_url=brand.logo_url,
                created_at=brand.created_at.isoformat(),
                updated_at=brand.updated_at.isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建品牌失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.get(
    "/brands",
    response_model=list[BrandResponse],
    summary="查询品牌列表",
    dependencies=[Depends(require_permission(PermissionEnum.BRAND_READ))]
)
async def list_brands(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    country: Optional[str] = Query(None, description="国家过滤"),
    with_equipment_count: bool = Query(False, description="包含装备数量")
):
    """查询品牌列表"""
    try:
        with get_db_session() as session:
            repo = BrandRepository(session)

            if with_equipment_count:
                # 获取带装备数量的品牌列表
                brands_data = repo.get_brands_with_equipment_counts(
                    limit=page_size,
                    offset=(page - 1) * page_size
                )

                return [
                    BrandResponse(
                        brand_id=b['brand_id'],
                        name_cn=b['name_cn'],
                        name_en=b.get('name_en'),
                        country=b.get('country'),
                        description=b.get('description'),
                        logo_url=b.get('logo_url'),
                        created_at=b['created_at'].isoformat(),
                        updated_at=b['updated_at'].isoformat(),
                        equipment_count=b.get('equipment_count', 0)
                    )
                    for b in brands_data
                ]
            else:
                # 获取基础品牌列表
                brands = repo.get_active_brands(
                    country=country,
                    limit=page_size,
                    offset=(page - 1) * page_size
                )

                return [
                    BrandResponse(
                        brand_id=brand.brand_id,
                        name_cn=brand.name_cn,
                        name_en=brand.name_en,
                        country=brand.country,
                        description=brand.description,
                        logo_url=brand.logo_url,
                        created_at=brand.created_at.isoformat(),
                        updated_at=brand.updated_at.isoformat()
                    )
                    for brand in brands
                ]

    except Exception as e:
        logger.error(f"查询品牌列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="获取品牌详情",
    dependencies=[Depends(require_permission(PermissionEnum.BRAND_READ))]
)
async def get_brand(
    brand_id: int,
    with_equipment_count: bool = Query(False, description="包含装备数量")
):
    """获取品牌详情"""
    try:
        with get_db_session() as session:
            repo = BrandRepository(session)

            if with_equipment_count:
                brand_data = repo.get_with_equipment_count(brand_id)
                if not brand_data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"品牌不存在: brand_id={brand_id}"
                    )

                return BrandResponse(
                    brand_id=brand_data['brand_id'],
                    name_cn=brand_data['name_cn'],
                    name_en=brand_data.get('name_en'),
                    country=brand_data.get('country'),
                    description=brand_data.get('description'),
                    logo_url=brand_data.get('logo_url'),
                    created_at=brand_data['created_at'].isoformat(),
                    updated_at=brand_data['updated_at'].isoformat(),
                    equipment_count=brand_data.get('equipment_count', 0)
                )
            else:
                brand = repo.get(brand_id)
                if not brand:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"品牌不存在: brand_id={brand_id}"
                    )

                return BrandResponse(
                    brand_id=brand.brand_id,
                    name_cn=brand.name_cn,
                    name_en=brand.name_en,
                    country=brand.country,
                    description=brand.description,
                    logo_url=brand.logo_url,
                    created_at=brand.created_at.isoformat(),
                    updated_at=brand.updated_at.isoformat()
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取品牌详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.put(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="更新品牌",
    dependencies=[Depends(require_permission(PermissionEnum.BRAND_UPDATE))]
)
async def update_brand(
    brand_id: int,
    brand_data: BrandUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.BRAND_UPDATE))
):
    """更新品牌"""
    try:
        with get_db_session() as session:
            repo = BrandRepository(session)

            # 检查品牌是否存在
            brand = repo.get(brand_id)
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"品牌不存在: brand_id={brand_id}"
                )

            # 更新品牌
            update_data = brand_data.model_dump(exclude_none=True)

            for key, value in update_data.items():
                setattr(brand, key, value)

            session.commit()
            session.refresh(brand)

            logger.info(f"品牌更新成功: brand_id={brand_id}, user={current_user.username}")

            return BrandResponse(
                brand_id=brand.brand_id,
                name_cn=brand.name_cn,
                name_en=brand.name_en,
                country=brand.country,
                description=brand.description,
                logo_url=brand.logo_url,
                created_at=brand.created_at.isoformat(),
                updated_at=brand.updated_at.isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新品牌失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.delete(
    "/brands/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除品牌",
    dependencies=[Depends(require_permission(PermissionEnum.BRAND_DELETE))]
)
async def delete_brand(
    brand_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.BRAND_DELETE))
):
    """删除品牌（仅当没有关联装备时）"""
    try:
        with get_db_session() as session:
            repo = BrandRepository(session)

            # 检查品牌是否存在
            brand = repo.get(brand_id)
            if not brand:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"品牌不存在: brand_id={brand_id}"
                )

            # 检查是否有关联装备
            brand_data = repo.get_with_equipment_count(brand_id)
            if brand_data and brand_data.get('equipment_count', 0) > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"品牌下还有 {brand_data['equipment_count']} 个装备，无法删除"
                )

            # 删除品牌
            session.delete(brand)
            session.commit()

            logger.info(f"品牌删除成功: brand_id={brand_id}, user={current_user.username}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除品牌失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )
