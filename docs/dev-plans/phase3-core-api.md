# Phase 3: 核心管理模块 API 开发详细方案

**目标**: 实现装备、用户、内容管理的完整 CRUD API
**周期**: 第 4-5 周（10 个工作日）
**优先级**: P1（核心功能）

---

## 目标概述

构建管理后台的核心 CRUD API，支持装备数据、用户信息、内容知识库的完整管理。

**核心模块**:
- Week 4: 装备管理 + 用户管理 + 导入导出
- Week 5: 内容管理（鱼类、钓组、拟饵）

---

## Week 4: 装备 + 用户管理（Day 1-5）

### Step 1: 装备管理 API（Day 1-2）

#### 1.1 创建装备 Schema

**文件**: `apps/api/schemas/equipment_admin.py`

**步骤**:
1. 定义装备相关 Schema:

```python
from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ========== 规格 Schema（Union 类型）==========

class RodSpecsBase(BaseModel):
    """鱼竿规格"""
    length: float = Field(..., ge=0.5, le=10.0, description="长度（米）")
    power: str = Field(..., pattern="^(UL|L|ML|M|MH|H|XH)$", description="调性")
    action: str = Field(..., pattern="^(Fast|Medium|Slow)$", description="动作")
    lure_weight_min: float = Field(..., ge=0, description="适用饵重最小值（克）")
    lure_weight_max: float = Field(..., ge=0, description="适用饵重最大值（克）")
    sections: Optional[int] = Field(None, ge=1, le=10, description="节数")
    closed_length: Optional[float] = Field(None, description="收缩长度（厘米）")
    weight: Optional[float] = Field(None, description="自重（克）")


class ReelSpecsBase(BaseModel):
    """渔轮规格"""
    gear_ratio: Optional[str] = Field(None, description="速比（如 5.2:1）")
    bearings: Optional[int] = Field(None, ge=0, description="轴承数")
    max_drag: Optional[float] = Field(None, description="最大拽力（千克）")
    line_capacity: Optional[str] = Field(None, description="线容量（如 0.2mm/100m）")
    weight: Optional[float] = Field(None, description="自重（克）")
    spool_type: Optional[str] = Field(None, description="线杯类型")


class LineSpecsBase(BaseModel):
    """鱼线规格"""
    line_type: str = Field(..., pattern="^(PE|尼龙|碳线|钢丝)$", description="线型")
    diameter: Optional[float] = Field(None, description="线径（毫米）")
    breaking_strength: Optional[float] = Field(None, description="拉力值（千克）")
    length: Optional[float] = Field(None, description="长度（米）")
    material: Optional[str] = Field(None, description="材质")


class LureSpecsBase(BaseModel):
    """拟饵规格"""
    lure_type: str = Field(..., description="拟饵类型")
    weight: Optional[float] = Field(None, description="重量（克）")
    length: Optional[float] = Field(None, description="长度（厘米）")
    diving_depth: Optional[str] = Field(None, description="潜深（如 0.5-1.5米）")
    action_type: Optional[str] = Field(None, description="动作类型")


# Union 类型（根据 category 动态选择）
SpecsUnion = Union[RodSpecsBase, ReelSpecsBase, LineSpecsBase, LureSpecsBase]


# ========== 装备 Schema ==========

class EquipmentCreate(BaseModel):
    """创建装备请求"""
    # 基础信息
    name: str = Field(..., min_length=1, max_length=200, description="装备名称")
    category: str = Field(
        ...,
        pattern="^(鱼竿|渔轮|鱼线|拟饵|套装)$",
        description="装备类别"
    )
    brand_id: int = Field(..., gt=0, description="品牌ID")
    model: Optional[str] = Field(None, max_length=100, description="型号")

    # 价格
    price_min: Optional[float] = Field(None, ge=0, description="最低价格")
    price_max: Optional[float] = Field(None, ge=0, description="最高价格")
    price_currency: str = Field(default="CNY", description="货币单位")

    # 详情
    description: Optional[str] = Field(None, max_length=2000, description="描述")
    features: Optional[str] = Field(None, max_length=1000, description="特点")
    user_level: str = Field(
        default="新手",
        pattern="^(新手|进阶|高手)$",
        description="适用水平"
    )

    # 状态
    is_active: bool = Field(default=True, description="是否启用")
    source: str = Field(default="manual", description="数据来源")
    source_url: Optional[str] = Field(None, description="来源链接")

    # 规格（嵌套对象）
    specs: Optional[SpecsUnion] = Field(None, description="装备规格")


class EquipmentUpdate(BaseModel):
    """更新装备请求（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, pattern="^(鱼竿|渔轮|鱼线|拟饵|套装)$")
    brand_id: Optional[int] = Field(None, gt=0)
    model: Optional[str] = Field(None, max_length=100)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2000)
    features: Optional[str] = Field(None, max_length=1000)
    user_level: Optional[str] = Field(None, pattern="^(新手|进阶|高手)$")
    is_active: Optional[bool] = None
    specs: Optional[SpecsUnion] = None


class EquipmentResponse(BaseModel):
    """装备响应"""
    equipment_id: int
    name: str
    category: str
    brand_id: int
    brand_name: Optional[str] = None  # 品牌中文名（JOIN查询）
    model: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_currency: str
    description: Optional[str] = None
    features: Optional[str] = None
    user_level: str
    is_active: bool
    source: str
    source_url: Optional[str] = None
    created_at: str
    updated_at: str

    # 规格（嵌套对象）
    specs: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class EquipmentListResponse(BaseModel):
    """装备列表响应（分页）"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    items: List[EquipmentResponse] = Field(..., description="装备列表")


# ========== 品牌 Schema ==========

class BrandCreate(BaseModel):
    """创建品牌请求"""
    name_cn: str = Field(..., min_length=1, max_length=100, description="中文名")
    name_en: Optional[str] = Field(None, max_length=100, description="英文名")
    country: Optional[str] = Field(None, max_length=50, description="国家")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    logo_url: Optional[str] = Field(None, description="Logo URL")


class BrandResponse(BaseModel):
    """品牌响应"""
    brand_id: int
    name_cn: str
    name_en: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)
```

#### 1.2 实现装备管理路由

**文件**: `apps/api/routes/equipment_admin.py`

**步骤**:
1. 实现 CRUD 端点:

```python
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional
import logging

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository

from apps.api.schemas.equipment_admin import (
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentListResponse,
    BrandCreate,
    BrandResponse
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


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

            # 创建装备（包含规格）
            equipment = repo.create_with_specs(
                equipment_data=equipment_data.model_dump(exclude={'specs'}),
                spec_data=equipment_data.specs.model_dump() if equipment_data.specs else None,
                category=equipment_data.category
            )

            logger.info(
                f"装备创建成功: equipment_id={equipment.equipment_id}, "
                f"name={equipment.name}, user={current_user.username}"
            )

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
                specs=equipment_data.specs.model_dump() if equipment_data.specs else None
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

            # 构建过滤条件
            filters = {}
            if category:
                filters['category'] = category
            if brand_id:
                filters['brand_id'] = brand_id
            if user_level:
                filters['user_level'] = user_level
            if is_active is not None:
                filters['is_active'] = is_active

            # 查询装备（预加载品牌）
            equipment_list = repo.search(
                filters=filters,
                price_min=price_min,
                price_max=price_max,
                keyword=keyword,
                limit=page_size,
                offset=(page - 1) * page_size
            )

            # 统计总数
            total = repo.count(filters=filters)

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
            # 其他类别规格类似处理...

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
            update_data = equipment_data.model_dump(exclude_none=True)
            updated_equipment = repo.update(equipment_id, update_data)

            logger.info(
                f"装备更新成功: equipment_id={equipment_id}, "
                f"user={current_user.username}"
            )

            # 返回更新后的装备
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
            repo.update(equipment_id, {"is_active": False})

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
            brand = repo.create_brand(brand_data.model_dump())

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
    response_model=List[BrandResponse],
    summary="查询品牌列表",
    dependencies=[Depends(require_permission(PermissionEnum.BRAND_READ))]
)
async def list_brands():
    """查询所有品牌"""
    try:
        with get_db_session() as session:
            repo = BrandRepository(session)
            brands = repo.get_all()

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
```

#### 1.3 测试装备管理 API

**测试文件**: `tests/test_equipment_admin.py`

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

# 测试前需要先登录获取 token
@pytest.fixture
def admin_token():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]


def test_create_equipment(admin_token):
    """测试创建装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    equipment_data = {
        "name": "测试鱼竿",
        "category": "鱼竿",
        "brand_id": 1,
        "model": "TEST-001",
        "price_min": 199,
        "price_max": 299,
        "description": "测试描述",
        "user_level": "新手",
        "specs": {
            "length": 2.1,
            "power": "ML",
            "action": "Fast",
            "lure_weight_min": 2,
            "lure_weight_max": 10
        }
    }

    response = client.post(
        "/api/v1/admin/equipment",
        headers=headers,
        json=equipment_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试鱼竿"
    assert data["category"] == "鱼竿"
    assert "equipment_id" in data


def test_list_equipment(admin_token):
    """测试查询装备列表"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/equipment?page=1&page_size=10&category=鱼竿",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_equipment(admin_token):
    """测试获取装备详情"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/equipment/1",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "equipment_id" in data
    assert "specs" in data  # 详情包含规格


def test_update_equipment(admin_token):
    """测试更新装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    update_data = {
        "price_min": 249,
        "price_max": 349,
        "description": "更新后的描述"
    }

    response = client.put(
        "/api/v1/admin/equipment/1",
        headers=headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["price_min"] == 249
    assert data["description"] == "更新后的描述"


def test_delete_equipment(admin_token):
    """测试删除装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.delete(
        "/api/v1/admin/equipment/1",
        headers=headers
    )

    assert response.status_code == 204

    # 验证已软删除（is_active=False）
    response = client.get(
        "/api/v1/admin/equipment/1",
        headers=headers
    )
    assert response.json()["is_active"] is False
```

---

### Step 2: 用户管理 API（Day 3）

**文件**: `apps/api/routes/users.py`

**步骤**:
1. 实现用户管理端点（用户列表、详情、装备库、钓鱼记录）

```python
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional, List
import logging

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.user_repo import UserRepository

from apps.api.schemas.user import (
    UserResponse,
    UserListResponse,
    UserEquipmentResponse,
    FishingLogResponse
)
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="查询用户列表",
    dependencies=[Depends(require_permission(PermissionEnum.USER_READ))]
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_level: Optional[str] = Query(None, description="用户水平过滤"),
    fishing_experience_years: Optional[int] = Query(None, description="钓龄过滤")
):
    """查询用户列表（分页）"""
    try:
        with get_db_session() as session:
            repo = UserRepository(session)

            filters = {}
            if user_level:
                filters['user_level'] = user_level
            if fishing_experience_years is not None:
                filters['fishing_experience_years'] = fishing_experience_years

            users = repo.get_all(
                filters=filters,
                limit=page_size,
                offset=(page - 1) * page_size
            )

            total = repo.count(filters=filters)

            return UserListResponse(
                total=total,
                page=page,
                page_size=page_size,
                users=[UserResponse.model_validate(user) for user in users]
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
    """获取用户详情"""
    try:
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.get(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户不存在: user_id={user_id}"
                )

            return UserResponse.model_validate(user)

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
async def get_user_equipment(user_id: int):
    """获取用户装备库"""
    try:
        with get_db_session() as session:
            repo = UserRepository(session)

            equipment_list = repo.get_user_equipment(user_id)

            return [
                UserEquipmentResponse.model_validate(eq)
                for eq in equipment_list
            ]

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
async def get_user_fishing_logs(user_id: int):
    """获取用户钓鱼记录"""
    try:
        with get_db_session() as session:
            repo = UserRepository(session)

            logs = repo.get_fishing_logs(user_id)

            return [
                FishingLogResponse.model_validate(log)
                for log in logs
            ]

    except Exception as e:
        logger.error(f"获取钓鱼记录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )
```

---

### Step 3: 导入导出 API（Day 4）

**文件**: `apps/api/routes/import_export.py`

**步骤**:
1. 实现 CSV/JSON 导入导出功能

```python
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
import logging
import io

from apps.api.services.import_service import ImportService
from apps.api.services.export_service import ExportService
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/import/csv",
    summary="CSV 导入装备",
    dependencies=[Depends(require_permission(PermissionEnum.DATA_IMPORT))]
)
async def import_csv(file: UploadFile = File(...)):
    """
    CSV 导入装备

    Args:
        file: CSV 文件

    Returns:
        dict: 导入结果（成功数、失败数、错误列表）
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="仅支持 CSV 文件"
        )

    try:
        # 读取文件内容
        content = await file.read()
        csv_string = content.decode('utf-8')

        # 导入
        import_service = ImportService()
        result = import_service.import_from_csv(csv_string)

        logger.info(
            f"CSV 导入完成: 成功={result['success_count']}, "
            f"失败={result['error_count']}"
        )

        return result

    except Exception as e:
        logger.error(f"CSV 导入失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"导入失败: {str(e)}"
        )


@router.get(
    "/export/csv",
    summary="CSV 导出装备",
    dependencies=[Depends(require_permission(PermissionEnum.DATA_EXPORT))]
)
async def export_csv(
    category: Optional[str] = Query(None, description="类别过滤"),
    is_active: Optional[bool] = Query(None, description="是否启用过滤")
):
    """
    CSV 导出装备

    Returns:
        StreamingResponse: CSV 文件流
    """
    try:
        export_service = ExportService()

        filters = {}
        if category:
            filters['category'] = category
        if is_active is not None:
            filters['is_active'] = is_active

        csv_string = export_service.export_to_csv(filters=filters)

        # 转换为字节流
        output = io.BytesIO(csv_string.encode('utf-8-sig'))  # BOM for Excel

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=equipment_export.csv"
            }
        )

    except Exception as e:
        logger.error(f"CSV 导出失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"导出失败: {str(e)}"
        )


@router.get(
    "/export/json",
    summary="JSON 导出装备",
    dependencies=[Depends(require_permission(PermissionEnum.DATA_EXPORT))]
)
async def export_json(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """JSON 导出装备（包含完整规格和关联数据）"""
    try:
        export_service = ExportService()

        filters = {}
        if category:
            filters['category'] = category
        if is_active is not None:
            filters['is_active'] = is_active

        json_string = export_service.export_to_json(filters=filters)

        output = io.BytesIO(json_string.encode('utf-8'))

        return StreamingResponse(
            output,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=equipment_export.json"
            }
        )

    except Exception as e:
        logger.error(f"JSON 导出失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"导出失败: {str(e)}"
        )
```

**Service 实现**: `apps/api/services/import_service.py`

```python
import csv
import io
import json
from typing import List, Dict
import logging

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository

logger = logging.getLogger(__name__)


class ImportService:
    """导入服务"""

    def import_from_csv(self, csv_string: str) -> Dict:
        """
        从 CSV 导入装备

        Args:
            csv_string: CSV 文件内容

        Returns:
            dict: {
                "success_count": 成功数,
                "error_count": 失败数,
                "errors": [错误列表]
            }
        """
        success_count = 0
        error_count = 0
        errors = []

        # 解析 CSV
        csv_file = io.StringIO(csv_string)
        reader = csv.DictReader(csv_file)

        with get_db_session() as session:
            equipment_repo = EquipmentRepository(session)
            brand_repo = BrandRepository(session)

            for row_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是表头）
                try:
                    # 解析 brand_name → brand_id
                    brand_name = row.get('brand_name')
                    if not brand_name:
                        raise ValueError("缺少品牌名称")

                    brand = brand_repo.get_by_name(brand_name)
                    if not brand:
                        # 自动创建品牌
                        brand = brand_repo.create_brand({
                            "name_cn": brand_name
                        })
                        logger.info(f"自动创建品牌: {brand_name}")

                    # 构造装备数据
                    equipment_data = {
                        "name": row.get('name'),
                        "category": row.get('category'),
                        "brand_id": brand.brand_id,
                        "model": row.get('model'),
                        "price_min": float(row['price_min']) if row.get('price_min') else None,
                        "price_max": float(row['price_max']) if row.get('price_max') else None,
                        "description": row.get('description'),
                        "features": row.get('features'),
                        "user_level": row.get('user_level', '新手'),
                        "source": "csv_import"
                    }

                    # 创建装备
                    equipment_repo.create(equipment_data)
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": row_num,
                        "data": row,
                        "error": str(e)
                    })
                    logger.error(f"CSV 导入错误（行 {row_num}）: {e}")

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
```

---

### Step 4: 注册路由（Day 5）

**文件**: `apps/api/main.py`

**步骤**:
1. 在 FastAPI 应用中注册新路由:

```python
from apps.api.routes.equipment_admin import router as equipment_admin_router
from apps.api.routes.users import router as users_router
from apps.api.routes.import_export import router as import_export_router

app.include_router(
    equipment_admin_router,
    prefix="/api/v1/admin",
    tags=["equipment-admin"]
)

app.include_router(
    users_router,
    prefix="/api/v1/admin",
    tags=["users"]
)

app.include_router(
    import_export_router,
    prefix="/api/v1/admin/import-export",
    tags=["import-export"]
)
```

2. 测试所有端点:

```bash
# 启动服务器
uv run uvicorn apps.api.main:app --reload

# 访问 Swagger 文档
open http://localhost:8000/docs

# 验证端点:
# - POST /api/v1/admin/equipment
# - GET /api/v1/admin/equipment
# - GET /api/v1/admin/equipment/{id}
# - PUT /api/v1/admin/equipment/{id}
# - DELETE /api/v1/admin/equipment/{id}
# - POST /api/v1/admin/brands
# - GET /api/v1/admin/brands
# - GET /api/v1/admin/users
# - GET /api/v1/admin/users/{id}
# - GET /api/v1/admin/users/{id}/equipment
# - POST /api/v1/admin/import-export/import/csv
# - GET /api/v1/admin/import-export/export/csv
```

---

## Week 5: 内容管理（Day 6-10）

### Step 5: 鱼类管理 API（Day 6-7）

**文件**: `apps/api/routes/fish.py`

**关键端点**:
- `GET /fish/species` - 鱼类列表
- `POST /fish/species` - 创建鱼种
- `PUT /fish/species/{id}` - 更新鱼种
- `DELETE /fish/species/{id}` - 删除鱼种
- `GET /fish/species/{id}/knowledge` - 鱼类知识列表
- `POST /fish/species/{id}/knowledge` - 添加知识条目

### Step 6: 钓组管理 API（Day 8)

**文件**: `apps/api/routes/rigs.py`

**关键端点**:
- `GET /rigs/types` - 钓组类型列表
- `POST /rigs/types` - 创建钓组类型
- `PUT /rigs/types/{id}` - 更新钓组类型
- `GET /rigs/types/{id}/specs` - 钓组规格
- `POST /rigs/types/{id}/components` - 添加配件

### Step 7: 拟饵管理 API（Day 9-10）

**文件**: `apps/api/routes/lures.py`

**关键端点**:
- `GET /lures/types` - 拟饵类型列表
- `POST /lures/types` - 创建拟饵类型
- `GET /lures/rod-fitness` - 鱼竿-拟饵兼容性矩阵
- `POST /lures/rod-fitness` - 创建兼容性记录

---

## 测试用例

### 集成测试

```bash
# 运行所有 API 测试
uv run pytest tests/test_equipment_admin.py -v
uv run pytest tests/test_users.py -v
uv run pytest tests/test_import_export.py -v
uv run pytest tests/test_fish.py -v
uv run pytest tests/test_rigs.py -v
uv run pytest tests/test_lures.py -v
```

### Postman 测试集

创建 Postman Collection 包含所有端点，导出为 `postman_collection.json` 用于 CI/CD。

---

## 注意事项

### 1. 分页性能优化

⚠️ **避免 COUNT(*) 性能问题**:
```python
# ✅ 使用索引优化 COUNT
total = session.query(func.count(Equipment.equipment_id))\
    .filter(Equipment.category == category)\
    .scalar()

# ❌ 慢查询
total = len(equipment_list)  # 加载所有数据到内存
```

### 2. N+1 查询优化

🚀 **预加载关联数据**:
```python
# ✅ 使用 joinedload
from sqlalchemy.orm import joinedload

equipment_list = session.query(Equipment)\
    .options(joinedload(Equipment.brand))\
    .all()

# ❌ N+1 查询
equipment_list = session.query(Equipment).all()
for eq in equipment_list:
    print(eq.brand.name_cn)  # 每次都查询数据库
```

### 3. 批量导入事务管理

⚠️ **批量提交 vs 单条提交**:
```python
# ✅ 批量提交（快）
for row in rows:
    session.add(Equipment(...))
session.commit()  # 一次性提交

# ❌ 单条提交（慢）
for row in rows:
    session.add(Equipment(...))
    session.commit()  # 每条都提交
```

### 4. 文件上传大小限制

⚠️ **限制上传文件大小**:
```python
from fastapi import UploadFile, File

@router.post("/import/csv")
async def import_csv(file: UploadFile = File(..., max_length=10 * 1024 * 1024)):  # 10MB
    ...
```

---

## 验收标准

### 必须完成

- ✅ 装备 CRUD 端点全部实现
- ✅ 分页、筛选、搜索功能正常
- ✅ 品牌管理端点正常
- ✅ 用户管理端点正常（列表、详情、装备库、钓鱼记录）
- ✅ CSV/JSON 导入导出功能正常
- ✅ 鱼类、钓组、拟饵管理端点实现
- ✅ Postman 测试全部通过
- ✅ API 文档（Swagger）完整

### 可选优化

- 🔧 添加全文搜索（PostgreSQL FTS）
- 🔧 批量更新端点
- 🔧 导入进度 WebSocket 推送
- 🔧 Excel 导入导出支持

---

## 下一步

完成 Phase 3 后，进入 **Phase 4: 爬虫 + 监控模块**
