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
    # 鱼竿专属筛选参数
    power: Optional[str] = Query(None, description="调性过滤（鱼竿专属）"),
    action: Optional[str] = Query(None, description="动作过滤（鱼竿专属）"),
    length_min: Optional[float] = Query(None, description="最小长度过滤（鱼竿专属）"),
    length_max: Optional[float] = Query(None, description="最大长度过滤（鱼竿专属）")
):
    """
    查询装备列表（分页 + 多条件筛选）

    Returns:
        EquipmentListResponse: 分页装备列表
    """
    try:
        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 检查是否有鱼竿专属筛选参数
            has_rod_filters = any([power, action, length_min, length_max])

            # 如果有鱼竿专属筛选，使用 search_rods 方法
            if has_rod_filters and (category == '鱼竿' or category is None):
                equipment_list = repo.search_rods(
                    power=power,
                    action=action,
                    length_min=length_min,
                    length_max=length_max,
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
            else:
                # 通用查询
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
            from sqlalchemy import and_, or_
            from apps.api.models.equipment import Equipment, RodSpec

            # 如果有鱼竿专属筛选，需要 join RodSpec 表
            if has_rod_filters and (category == '鱼竿' or category is None):
                total_query = session.query(Equipment).join(RodSpec)
                # 应用鱼竿专属过滤条件
                if power:
                    total_query = total_query.filter(RodSpec.power == power)
                if action:
                    total_query = total_query.filter(RodSpec.action == action)
                if length_min:
                    total_query = total_query.filter(RodSpec.length >= length_min)
                if length_max:
                    total_query = total_query.filter(RodSpec.length <= length_max)
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
                    price_currency="CNY",  # 默认使用人民币
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
