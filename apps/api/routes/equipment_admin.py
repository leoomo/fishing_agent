"""
装备管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status, Response
from typing import Optional
import logging
from functools import lru_cache
import hashlib
import json

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository

from apps.api.schemas.equipment_admin import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentListResponse,
    BrandCreate,
    BrandUpdate,
    BrandResponse
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

            # 准备装备数据
            equipment_dict = equipment_data.model_dump(exclude={'specs'})
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
                price_currency=equipment.price_currency,
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
    keyword: Optional[str] = Query(None, description="关键词搜索（名称、描述）")
):
    """
    查询装备列表（分页 + 多条件筛选）

    Returns:
        EquipmentListResponse: 分页装备列表
    """
    try:
        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 查询装备（预加载品牌）
            equipment_list = repo.search(
                category=category,
                brand_id=brand_id,
                price_min=price_min,
                price_max=price_max,
                user_level=user_level,
                is_active=is_active if is_active is not None else True,
                keyword=keyword,
                limit=page_size,
                offset=(page - 1) * page_size,
                preload=True
            )

            # 统计总数（使用相同的过滤条件）
            total_query = session.query(repo.model)

            # 应用相同的过滤条件
            from sqlalchemy import and_, or_
            from packages.agent_fishing.tools.lure.models.equipment import Equipment

            filters = []
            if category:
                filters.append(Equipment.category == category)
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

            if filters:
                total_query = total_query.filter(and_(*filters))

            total = total_query.count()

            # 转换为响应模型
            items = []
            for eq in equipment_list:
                items.append(EquipmentResponse(
                    equipment_id=eq.equipment_id,
                    name=eq.name,
                    category=eq.category,
                    brand_id=eq.brand_id,
                    brand_name=eq.brand.name_cn if eq.brand else None,
                    model=eq.model,
                    price_min=eq.price_min,
                    price_max=eq.price_max,
                    price_currency=eq.price_currency,
                    description=eq.description,
                    features=eq.features,
                    user_level=eq.user_level,
                    is_active=eq.is_active,
                    source=eq.source,
                    source_url=eq.source_url,
                    created_at=eq.created_at.isoformat(),
                    updated_at=eq.updated_at.isoformat(),
                    specs=None  # 列表不返回详细规格，减少数据量
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

            # 提取规格
            specs = None
            if equipment.category == "鱼竿" and equipment.rod_spec:
                specs = {
                    "length": equipment.rod_spec.length,
                    "power": equipment.rod_spec.power,
                    "action": equipment.rod_spec.action,
                    "lure_weight_min": equipment.rod_spec.lure_weight_min,
                    "lure_weight_max": equipment.rod_spec.lure_weight_max,
                    "sections": equipment.rod_spec.sections,
                    "closed_length": equipment.rod_spec.closed_length,
                    "weight": equipment.rod_spec.weight
                }
            elif equipment.category == "渔轮" and equipment.reel_spec:
                specs = {
                    "gear_ratio": equipment.reel_spec.gear_ratio,
                    "bearings": equipment.reel_spec.bearings,
                    "max_drag": equipment.reel_spec.max_drag,
                    "line_capacity": equipment.reel_spec.line_capacity,
                    "weight": equipment.reel_spec.weight,
                    "spool_type": equipment.reel_spec.spool_type
                }
            elif equipment.category == "鱼线" and equipment.line_spec:
                specs = {
                    "line_type": equipment.line_spec.line_type,
                    "diameter": equipment.line_spec.diameter,
                    "breaking_strength": equipment.line_spec.breaking_strength,
                    "length": equipment.line_spec.length,
                    "material": equipment.line_spec.material
                }
            elif equipment.category == "拟饵" and equipment.lure_spec:
                specs = {
                    "lure_type": equipment.lure_spec.lure_type,
                    "weight": equipment.lure_spec.weight,
                    "length": equipment.lure_spec.length,
                    "diving_depth": equipment.lure_spec.diving_depth,
                    "action_type": equipment.lure_spec.action_type
                }

            return EquipmentResponse(
                equipment_id=equipment.equipment_id,
                name=equipment.name,
                category=equipment.category,
                brand_id=equipment.brand_id,
                brand_name=equipment.brand.name_cn if equipment.brand else None,
                model=equipment.model,
                price_min=equipment.price_min,
                price_max=equipment.price_max,
                price_currency=equipment.price_currency,
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
    更新装备（支持部分更新）

    Args:
        equipment_id: 装备ID
        equipment_data: 更新数据

    Returns:
        EquipmentResponse: 更新后的装备信息

    Raises:
        HTTPException: 装备不存在或更新失败
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

            # 更新装备（仅更新非 None 字段）
            update_data = equipment_data.model_dump(exclude_none=True, exclude={'specs'})

            for key, value in update_data.items():
                setattr(equipment, key, value)

            session.commit()
            session.refresh(equipment)

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
