"""
钓组配置管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional, List
import logging

from apps.api.orm.session import get_db_session
from apps.api.models.rig import RigType, RigSpec, RigComponent
from apps.api.models.lure import LureType
from apps.api.schemas.rig import (
    RigCreate,
    RigUpdate,
    RigResponse,
    RigListResponse,
    RigListItem,
    RigSpecCreate,
    RigSpecUpdate,
    RigSpecResponse,
    RigComponentCreate,
    RigComponentUpdate,
    RigComponentResponse,
    RigLureAssociationRequest,
    LureTypeSimple,
    RigOptionsResponse,
    OptionItem,
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 选项数据 ==========

RIG_CATEGORIES = [
    OptionItem(value="bottom", label="底钓钓组", description="适合底层鱼类，如鲤鱼、鲫鱼", icon="🎣"),
    OptionItem(value="float", label="浮漂钓组", description="适合中上层鱼类", icon="🔴"),
    OptionItem(value="lure", label="路亚钓组", description="假饵钓法，适合掠食性鱼类", icon="🐟"),
    OptionItem(value="fly", label="飞蝇钓组", description="飞蝇钓法，技术要求高", icon="🪰"),
    OptionItem(value="surf", label="海钓钓组", description="海岸或船钓使用", icon="🌊"),
]

RIG_DIFFICULTIES = [
    OptionItem(value="easy", label="简单", color="success"),
    OptionItem(value="medium", label="中等", color="warning"),
    OptionItem(value="hard", label="困难", color="error"),
]

COMPONENT_TYPES = [
    OptionItem(value="hook", label="鱼钩"),
    OptionItem(value="sinker", label="铅坠"),
    OptionItem(value="swivel", label="转环"),
    OptionItem(value="leader", label="前导线"),
    OptionItem(value="float", label="浮漂"),
    OptionItem(value="stopper", label="挡豆"),
    OptionItem(value="snap", label="别针"),
    OptionItem(value="bead", label="珠子"),
    OptionItem(value="sleeve", label="铅皮座"),
    OptionItem(value="other", label="其他"),
]


# ========== 辅助函数 ==========

def rig_to_response(rig: RigType) -> RigResponse:
    """Convert RigType model to RigResponse"""
    return RigResponse(
        rig_id=rig.rig_id,
        name=rig.name,
        category=rig.category or "",
        description=rig.description,
        diagram_url=rig.diagram_url,
        difficulty=rig.difficulty or "medium",
        target_species=rig.target_species,
        best_conditions=rig.best_conditions,
        created_at=rig.created_at,
        updated_at=rig.updated_at,
        specs=[RigSpecResponse(
            spec_id=s.spec_id,
            rig_id=s.rig_id,
            spec_name=s.spec_name,
            spec_value=s.spec_value or "",
            unit=s.unit,
            notes=s.notes,
        ) for s in rig.specs],
        components=[RigComponentResponse(
            component_id=c.component_id,
            rig_id=c.rig_id,
            component_name=c.component_name,
            component_type=c.component_type or "",
            quantity=c.quantity or 1,
            size=c.size,
            position=c.position,
            notes=c.notes,
        ) for c in sorted(rig.components, key=lambda x: x.position or 0)],
    )


def rig_to_list_item(rig: RigType) -> RigListItem:
    """Convert RigType model to RigListItem"""
    return RigListItem(
        rig_id=rig.rig_id,
        name=rig.name,
        category=rig.category or "",
        difficulty=rig.difficulty or "medium",
        target_species=rig.target_species,
        diagram_url=rig.diagram_url,
        component_count=len(rig.components),
        spec_count=len(rig.specs),
        created_at=rig.created_at,
        updated_at=rig.updated_at,
    )


# ========== 选项端点 ==========

@router.get(
    "/rig-options",
    response_model=RigOptionsResponse,
    summary="获取钓组选项数据",
)
async def get_rig_options():
    """获取钓组表单所需的选项数据（分类、难度、组件类型）"""
    return RigOptionsResponse(
        categories=RIG_CATEGORIES,
        difficulties=RIG_DIFFICULTIES,
        component_types=COMPONENT_TYPES,
    )


@router.get(
    "/lure-types/simple",
    response_model=List[LureTypeSimple],
    summary="获取拟饵类型简化列表（用于钓组关联）",
)
async def get_lure_types_simple():
    """获取所有拟饵类型用于关联选择（简化版）"""
    with get_db_session() as session:
        lure_types = session.query(LureType).order_by(LureType.name).all()
        return [
            LureTypeSimple(
                lure_type_id=lt.lure_type_id,
                name=lt.name,
                category=lt.category,
            )
            for lt in lure_types
        ]


# ========== 钓组 CRUD ==========

@router.post(
    "/rigs",
    response_model=RigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建钓组",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def create_rig(
    rig_data: RigCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """创建新钓组，可同时创建规格和组件"""
    with get_db_session() as session:
        # 检查名称是否已存在
        existing = session.query(RigType).filter(RigType.name == rig_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"钓组名称已存在: {rig_data.name}"
            )

        # 创建钓组
        rig = RigType(
            name=rig_data.name,
            category=rig_data.category,
            description=rig_data.description,
            diagram_url=rig_data.diagram_url,
            difficulty=rig_data.difficulty,
            target_species=rig_data.target_species,
            best_conditions=rig_data.best_conditions,
        )
        session.add(rig)
        session.flush()  # 获取 rig_id

        # 创建规格
        if rig_data.specs:
            for spec_data in rig_data.specs:
                spec = RigSpec(
                    rig_id=rig.rig_id,
                    spec_name=spec_data.spec_name,
                    spec_value=spec_data.spec_value,
                    unit=spec_data.unit,
                    notes=spec_data.notes,
                )
                session.add(spec)

        # 创建组件
        if rig_data.components:
            for i, comp_data in enumerate(rig_data.components):
                component = RigComponent(
                    rig_id=rig.rig_id,
                    component_name=comp_data.component_name,
                    component_type=comp_data.component_type,
                    quantity=comp_data.quantity,
                    size=comp_data.size,
                    position=comp_data.position if comp_data.position is not None else i,
                    notes=comp_data.notes,
                )
                session.add(component)

        session.commit()
        session.refresh(rig)

        logger.info(f"钓组创建成功: rig_id={rig.rig_id}, name={rig.name}, user={current_user.username}")
        return rig_to_response(rig)


@router.get(
    "/rigs",
    response_model=RigListResponse,
    summary="获取钓组列表",
)
async def list_rigs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="按分类筛选"),
    difficulty: Optional[str] = Query(None, description="按难度筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
):
    """获取钓组列表，支持分页和筛选"""
    with get_db_session() as session:
        query = session.query(RigType)

        # 筛选条件
        if category:
            query = query.filter(RigType.category == category)
        if difficulty:
            query = query.filter(RigType.difficulty == difficulty)
        if keyword:
            query = query.filter(
                RigType.name.ilike(f"%{keyword}%") |
                RigType.target_species.ilike(f"%{keyword}%") |
                RigType.description.ilike(f"%{keyword}%")
            )

        # 统计总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        rigs = query.order_by(RigType.updated_at.desc()).offset(offset).limit(page_size).all()

        return RigListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[rig_to_list_item(rig) for rig in rigs],
        )


@router.get(
    "/rigs/featured",
    response_model=List[RigResponse],
    summary="获取精选钓组",
)
async def get_featured_rigs(
    limit: int = Query(4, ge=1, le=10, description="数量限制"),
):
    """获取精选钓组用于卡片展示（按更新时间排序）"""
    with get_db_session() as session:
        rigs = session.query(RigType).order_by(
            RigType.updated_at.desc()
        ).limit(limit).all()

        return [rig_to_response(rig) for rig in rigs]


# ========== 采集管理 ==========
# 注意：这些路由必须在 /rigs/{rig_id} 之前定义，否则会被动态路由匹配

@router.get(
    "/rigs/fetch/progress",
    summary="获取钓组采集进度",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_READ))]
)
async def get_fetch_progress(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_READ))
):
    """获取钓组知识采集进度"""
    from apps.api.services.rig_fetcher import get_rig_fetcher_service
    service = get_rig_fetcher_service()
    return service.get_progress()


@router.post(
    "/rigs/fetch/start",
    summary="开始钓组采集",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def start_fetch(
    use_llm: bool = True,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """开始或继续钓组知识采集"""
    from apps.api.services.rig_fetcher import get_rig_fetcher_service
    service = get_rig_fetcher_service()
    result = service.start_fetch(use_llm=use_llm)
    logger.info(f"钓组采集启动: user={current_user.username}, use_llm={use_llm}")
    return result


@router.post(
    "/rigs/fetch/pause",
    summary="暂停钓组采集",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def pause_fetch(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """暂停钓组知识采集"""
    from apps.api.services.rig_fetcher import get_rig_fetcher_service
    service = get_rig_fetcher_service()
    result = service.pause_fetch()
    logger.info(f"钓组采集暂停: user={current_user.username}")
    return result


@router.post(
    "/rigs/fetch/retry",
    summary="重试失败的钓组采集",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def retry_failed(
    names: Optional[List[str]] = None,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """重试失败的钓组采集项目"""
    from apps.api.services.rig_fetcher import get_rig_fetcher_service
    service = get_rig_fetcher_service()
    result = service.retry_failed(names)
    logger.info(f"钓组采集重试: user={current_user.username}, names={names}")
    return result


@router.post(
    "/rigs/fetch/reset",
    summary="重置钓组采集进度",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_DELETE))]
)
async def reset_progress(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_DELETE))
):
    """重置所有钓组采集进度"""
    from apps.api.services.rig_fetcher import get_rig_fetcher_service
    service = get_rig_fetcher_service()
    result = service.reset_all()
    logger.info(f"钓组采集重置: user={current_user.username}")
    return result


# ========== 钓组详情（动态路由，必须放在静态路由之后） ==========

@router.get(
    "/rigs/{rig_id}",
    response_model=RigResponse,
    summary="获取钓组详情",
)
async def get_rig(rig_id: int):
    """获取钓组详情，包含所有规格和组件"""
    with get_db_session() as session:
        rig = session.query(RigType).filter(RigType.rig_id == rig_id).first()
        if not rig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"钓组不存在: rig_id={rig_id}"
            )
        return rig_to_response(rig)


@router.put(
    "/rigs/{rig_id}",
    response_model=RigResponse,
    summary="更新钓组",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def update_rig(
    rig_id: int,
    rig_data: RigUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """更新钓组基本信息"""
    with get_db_session() as session:
        rig = session.query(RigType).filter(RigType.rig_id == rig_id).first()
        if not rig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"钓组不存在: rig_id={rig_id}"
            )

        # 检查名称是否已被其他钓组使用
        if rig_data.name and rig_data.name != rig.name:
            existing = session.query(RigType).filter(
                RigType.name == rig_data.name,
                RigType.rig_id != rig_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"钓组名称已存在: {rig_data.name}"
                )

        # 更新字段
        update_data = rig_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rig, field, value)

        session.commit()
        session.refresh(rig)

        logger.info(f"钓组更新成功: rig_id={rig_id}, user={current_user.username}")
        return rig_to_response(rig)


@router.delete(
    "/rigs/{rig_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除钓组",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_DELETE))]
)
async def delete_rig(
    rig_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_DELETE))
):
    """删除钓组及其所有规格和组件"""
    with get_db_session() as session:
        rig = session.query(RigType).filter(RigType.rig_id == rig_id).first()
        if not rig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"钓组不存在: rig_id={rig_id}"
            )

        session.delete(rig)
        session.commit()

        logger.info(f"钓组删除成功: rig_id={rig_id}, name={rig.name}, user={current_user.username}")


# ========== 规格管理 ==========

@router.post(
    "/rigs/{rig_id}/specs",
    response_model=RigSpecResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加规格",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def add_rig_spec(
    rig_id: int,
    spec_data: RigSpecCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """为钓组添加规格参数"""
    with get_db_session() as session:
        rig = session.query(RigType).filter(RigType.rig_id == rig_id).first()
        if not rig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"钓组不存在: rig_id={rig_id}"
            )

        spec = RigSpec(
            rig_id=rig_id,
            spec_name=spec_data.spec_name,
            spec_value=spec_data.spec_value,
            unit=spec_data.unit,
            notes=spec_data.notes,
        )
        session.add(spec)
        session.commit()
        session.refresh(spec)

        logger.info(f"规格添加成功: rig_id={rig_id}, spec_id={spec.spec_id}")
        return RigSpecResponse(
            spec_id=spec.spec_id,
            rig_id=spec.rig_id,
            spec_name=spec.spec_name,
            spec_value=spec.spec_value or "",
            unit=spec.unit,
            notes=spec.notes,
        )


@router.put(
    "/rigs/{rig_id}/specs/{spec_id}",
    response_model=RigSpecResponse,
    summary="更新规格",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def update_rig_spec(
    rig_id: int,
    spec_id: int,
    spec_data: RigSpecUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """更新钓组规格参数"""
    with get_db_session() as session:
        spec = session.query(RigSpec).filter(
            RigSpec.spec_id == spec_id,
            RigSpec.rig_id == rig_id
        ).first()
        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规格不存在: spec_id={spec_id}"
            )

        update_data = spec_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(spec, field, value)

        session.commit()
        session.refresh(spec)

        return RigSpecResponse(
            spec_id=spec.spec_id,
            rig_id=spec.rig_id,
            spec_name=spec.spec_name,
            spec_value=spec.spec_value or "",
            unit=spec.unit,
            notes=spec.notes,
        )


@router.delete(
    "/rigs/{rig_id}/specs/{spec_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除规格",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def delete_rig_spec(
    rig_id: int,
    spec_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """删除钓组规格参数"""
    with get_db_session() as session:
        spec = session.query(RigSpec).filter(
            RigSpec.spec_id == spec_id,
            RigSpec.rig_id == rig_id
        ).first()
        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规格不存在: spec_id={spec_id}"
            )

        session.delete(spec)
        session.commit()


# ========== 组件管理 ==========

@router.post(
    "/rigs/{rig_id}/components",
    response_model=RigComponentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加组件",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def add_rig_component(
    rig_id: int,
    component_data: RigComponentCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """为钓组添加组件配件"""
    with get_db_session() as session:
        rig = session.query(RigType).filter(RigType.rig_id == rig_id).first()
        if not rig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"钓组不存在: rig_id={rig_id}"
            )

        # 如果没有指定位置，放到最后
        if component_data.position is None:
            max_position = session.query(RigComponent).filter(
                RigComponent.rig_id == rig_id
            ).count()
            position = max_position
        else:
            position = component_data.position

        component = RigComponent(
            rig_id=rig_id,
            component_name=component_data.component_name,
            component_type=component_data.component_type,
            quantity=component_data.quantity,
            size=component_data.size,
            position=position,
            notes=component_data.notes,
        )
        session.add(component)
        session.commit()
        session.refresh(component)

        logger.info(f"组件添加成功: rig_id={rig_id}, component_id={component.component_id}")
        return RigComponentResponse(
            component_id=component.component_id,
            rig_id=component.rig_id,
            component_name=component.component_name,
            component_type=component.component_type or "",
            quantity=component.quantity or 1,
            size=component.size,
            position=component.position,
            notes=component.notes,
        )


@router.put(
    "/rigs/{rig_id}/components/{component_id}",
    response_model=RigComponentResponse,
    summary="更新组件",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def update_rig_component(
    rig_id: int,
    component_id: int,
    component_data: RigComponentUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """更新钓组组件配件"""
    with get_db_session() as session:
        component = session.query(RigComponent).filter(
            RigComponent.component_id == component_id,
            RigComponent.rig_id == rig_id
        ).first()
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"组件不存在: component_id={component_id}"
            )

        update_data = component_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)

        session.commit()
        session.refresh(component)

        return RigComponentResponse(
            component_id=component.component_id,
            rig_id=component.rig_id,
            component_name=component.component_name,
            component_type=component.component_type or "",
            quantity=component.quantity or 1,
            size=component.size,
            position=component.position,
            notes=component.notes,
        )


@router.delete(
    "/rigs/{rig_id}/components/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除组件",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def delete_rig_component(
    rig_id: int,
    component_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """删除钓组组件配件"""
    with get_db_session() as session:
        component = session.query(RigComponent).filter(
            RigComponent.component_id == component_id,
            RigComponent.rig_id == rig_id
        ).first()
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"组件不存在: component_id={component_id}"
            )

        session.delete(component)
        session.commit()


@router.put(
    "/rigs/{rig_id}/components/reorder",
    response_model=List[RigComponentResponse],
    summary="重新排序组件",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def reorder_rig_components(
    rig_id: int,
    component_ids: List[int],
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """重新排序钓组组件"""
    with get_db_session() as session:
        rig = session.query(RigType).filter(RigType.rig_id == rig_id).first()
        if not rig:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"钓组不存在: rig_id={rig_id}"
            )

        # 更新位置
        for i, component_id in enumerate(component_ids):
            component = session.query(RigComponent).filter(
                RigComponent.component_id == component_id,
                RigComponent.rig_id == rig_id
            ).first()
            if component:
                component.position = i

        session.commit()

        # 返回排序后的组件列表
        components = session.query(RigComponent).filter(
            RigComponent.rig_id == rig_id
        ).order_by(RigComponent.position).all()

        return [
            RigComponentResponse(
                component_id=c.component_id,
                rig_id=c.rig_id,
                component_name=c.component_name,
                component_type=c.component_type or "",
                quantity=c.quantity or 1,
                size=c.size,
                position=c.position,
                notes=c.notes,
            )
            for c in components
        ]
