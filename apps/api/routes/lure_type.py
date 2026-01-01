"""
拟饵类型管理 API 路由

提供拟饵类型的 CRUD 操作和初始化数据功能
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.auth.dependencies import get_current_user, require_permission
from apps.api.models import LureType
from apps.api.orm import get_db_session
from apps.api.schemas.lure_type import (
    CategoryStats,
    CategoryStatsResponse,
    InitDataResponse,
    LureCategoryEnum,
    LureTypeCreate,
    LureTypeListItem,
    LureTypeListResponse,
    LureTypeResponse,
    LureTypeUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 分类配置
CATEGORY_CONFIG = {
    "hard": {"label": "硬饵", "icon": "🎯", "color": "#1890ff"},
    "soft": {"label": "软饵", "icon": "🐛", "color": "#52c41a"},
    "metal": {"label": "金属饵", "icon": "✨", "color": "#faad14"},
    "fly": {"label": "飞蝇", "icon": "🦋", "color": "#722ed1"},
    "other": {"label": "其他", "icon": "🎣", "color": "#8c8c8c"},
}

# 初始化数据
DEFAULT_LURE_TYPES = [
    # 硬饵类
    {
        "name": "米诺",
        "category": "hard",
        "description": "模仿小鱼的经典硬饵，通过唇板控制潜深和动作",
        "action_description": "摇摆游动，模拟受伤小鱼",
        "target_species": "黑鲈、鳜鱼、翘嘴",
        "typical_weight_min": 5,
        "typical_weight_max": 20,
    },
    {
        "name": "波趴",
        "category": "hard",
        "description": "水面系硬饵，通过抽动产生水花和声响",
        "action_description": "水面爆裂声，吸引掠食者攻击",
        "target_species": "黑鲈、翘嘴、狗鱼",
        "typical_weight_min": 7,
        "typical_weight_max": 15,
    },
    {
        "name": "铅笔",
        "category": "hard",
        "description": "水面系硬饵，需要通过抽竿技巧操控",
        "action_description": "左右摇摆的walking-the-dog动作",
        "target_species": "黑鲈、翘嘴",
        "typical_weight_min": 8,
        "typical_weight_max": 18,
    },
    {
        "name": "VIB",
        "category": "hard",
        "description": "无唇震动饵，快速下沉，适合搜索深水",
        "action_description": "高频震动，产生强烈侧线刺激",
        "target_species": "黑鲈、鳜鱼、翘嘴",
        "typical_weight_min": 10,
        "typical_weight_max": 30,
    },
    {
        "name": "摇滚",
        "category": "hard",
        "description": "方唇硬饵，适合障碍区作钓",
        "action_description": "撞击障碍物后产生不规则动作",
        "target_species": "黑鲈、鳜鱼",
        "typical_weight_min": 10,
        "typical_weight_max": 25,
    },
    {
        "name": "深潜米诺",
        "category": "hard",
        "description": "大唇板米诺，可潜至3-6米深度",
        "action_description": "深水摇摆游动",
        "target_species": "黑鲈、鳜鱼",
        "typical_weight_min": 15,
        "typical_weight_max": 35,
    },
    # 软饵类
    {
        "name": "卷尾蛆",
        "category": "soft",
        "description": "最经典的软饵，尾部卷曲产生摆动",
        "action_description": "尾部持续摆动，模拟蠕虫",
        "target_species": "黑鲈、鳜鱼",
        "typical_weight_min": 3,
        "typical_weight_max": 10,
    },
    {
        "name": "T尾",
        "category": "soft",
        "description": "T型尾部软饵，游动时尾部摆动幅度大",
        "action_description": "大幅度尾部摆动",
        "target_species": "黑鲈、鳜鱼、翘嘴",
        "typical_weight_min": 5,
        "typical_weight_max": 15,
    },
    {
        "name": "面条虫",
        "category": "soft",
        "description": "细长型软饵，动作自然飘逸",
        "action_description": "自然飘动，模拟蚯蚓或水蛭",
        "target_species": "黑鲈、鲤鱼",
        "typical_weight_min": 2,
        "typical_weight_max": 8,
    },
    {
        "name": "虾型软饵",
        "category": "soft",
        "description": "模仿虾类的软饵，带有多条触须",
        "action_description": "模拟虾类的游动和弹跳",
        "target_species": "黑鲈、鳜鱼、石斑",
        "typical_weight_min": 5,
        "typical_weight_max": 20,
    },
    {
        "name": "蜥蜴",
        "category": "soft",
        "description": "模仿蜥蜴或蝾螈的软饵",
        "action_description": "四肢摆动，吸引大型掠食者",
        "target_species": "黑鲈",
        "typical_weight_min": 8,
        "typical_weight_max": 25,
    },
    # 金属饵类
    {
        "name": "亮片",
        "category": "metal",
        "description": "金属旋转饵，通过旋转反光吸引鱼",
        "action_description": "高速旋转，闪光诱鱼",
        "target_species": "翘嘴、鲈鱼、马口",
        "typical_weight_min": 3,
        "typical_weight_max": 30,
    },
    {
        "name": "铁板",
        "category": "metal",
        "description": "扁平金属饵，适合远投和深水垂钓",
        "action_description": "下沉时左右飘摆，模拟受伤小鱼",
        "target_species": "翘嘴、鲈鱼、带鱼",
        "typical_weight_min": 20,
        "typical_weight_max": 100,
    },
    {
        "name": "胡须佬",
        "category": "metal",
        "description": "带裙摆的复合饵，金属头配合橡胶裙",
        "action_description": "裙摆飘动配合金属反光",
        "target_species": "黑鲈、鳜鱼",
        "typical_weight_min": 7,
        "typical_weight_max": 20,
    },
    # 飞蝇类
    {
        "name": "干蝇",
        "category": "fly",
        "description": "浮于水面的飞蝇钓毛钩",
        "action_description": "模拟落水昆虫",
        "target_species": "虹鳟、马口、溪哥",
        "typical_weight_min": 0.1,
        "typical_weight_max": 1,
    },
    {
        "name": "湿蝇",
        "category": "fly",
        "description": "沉入水下的飞蝇钓毛钩",
        "action_description": "模拟水生昆虫若虫",
        "target_species": "虹鳟、马口",
        "typical_weight_min": 0.1,
        "typical_weight_max": 1.5,
    },
    {
        "name": "若虫",
        "category": "fly",
        "description": "模拟水生昆虫幼虫阶段的毛钩",
        "action_description": "底层缓慢移动",
        "target_species": "虹鳟、马口",
        "typical_weight_min": 0.2,
        "typical_weight_max": 2,
    },
    {
        "name": "飘带",
        "category": "fly",
        "description": "长条状毛钩，模拟小鱼或水蛭",
        "action_description": "游动时尾部飘动",
        "target_species": "虹鳟、狗鱼",
        "typical_weight_min": 0.5,
        "typical_weight_max": 5,
    },
]


# ========== CRUD Endpoints ==========


@router.post(
    "/lure-types",
    response_model=LureTypeResponse,
    summary="创建拟饵类型",
    status_code=201,
)
async def create_lure_type(
    data: LureTypeCreate,
    current_user=Depends(require_permission("content:create")),
):
    """创建新的拟饵类型"""
    with get_db_session() as session:
        # 检查名称是否已存在
        existing = (
            session.query(LureType).filter(LureType.name == data.name).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail=f"拟饵类型 '{data.name}' 已存在")

        lure_type = LureType(
            name=data.name,
            category=data.category.value,
            description=data.description,
            action_description=data.action_description,
            best_conditions=data.best_conditions,
            target_species=data.target_species,
            typical_weight_min=data.typical_weight_min,
            typical_weight_max=data.typical_weight_max,
            image_url=data.image_url,
        )
        session.add(lure_type)
        session.commit()
        session.refresh(lure_type)

        logger.info(
            f"拟饵类型创建成功: lure_type_id={lure_type.lure_type_id}, "
            f"name={lure_type.name}, user={current_user.username}"
        )

        return LureTypeResponse.model_validate(lure_type)


@router.get(
    "/lure-types",
    response_model=LureTypeListResponse,
    summary="获取拟饵类型列表",
)
async def list_lure_types(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user=Depends(get_current_user),
):
    """获取拟饵类型分页列表"""
    with get_db_session() as session:
        query = session.query(LureType)

        # 分类筛选
        if category:
            query = query.filter(LureType.category == category)

        # 关键词搜索
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                (LureType.name.ilike(search_pattern))
                | (LureType.target_species.ilike(search_pattern))
                | (LureType.description.ilike(search_pattern))
            )

        # 统计总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        lure_types = query.order_by(LureType.category, LureType.name).offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size

        return LureTypeListResponse(
            items=[LureTypeListItem.model_validate(lt) for lt in lure_types],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


@router.get(
    "/lure-types/stats",
    response_model=CategoryStatsResponse,
    summary="获取分类统计",
)
async def get_category_stats(
    current_user=Depends(get_current_user),
):
    """获取各分类的拟饵类型数量统计"""
    with get_db_session() as session:
        # 统计各分类数量
        from sqlalchemy import func

        stats = (
            session.query(LureType.category, func.count(LureType.lure_type_id))
            .group_by(LureType.category)
            .all()
        )

        stats_dict = {category: count for category, count in stats}
        total = sum(stats_dict.values())

        categories = []
        for cat_key, config in CATEGORY_CONFIG.items():
            categories.append(
                CategoryStats(
                    category=cat_key,
                    count=stats_dict.get(cat_key, 0),
                    label=config["label"],
                    icon=config["icon"],
                    color=config["color"],
                )
            )

        return CategoryStatsResponse(categories=categories, total=total)


@router.get(
    "/lure-types/{lure_type_id}",
    response_model=LureTypeResponse,
    summary="获取拟饵类型详情",
)
async def get_lure_type(
    lure_type_id: int,
    current_user=Depends(get_current_user),
):
    """获取拟饵类型详情"""
    with get_db_session() as session:
        lure_type = (
            session.query(LureType)
            .filter(LureType.lure_type_id == lure_type_id)
            .first()
        )
        if not lure_type:
            raise HTTPException(status_code=404, detail="拟饵类型不存在")

        return LureTypeResponse.model_validate(lure_type)


@router.put(
    "/lure-types/{lure_type_id}",
    response_model=LureTypeResponse,
    summary="更新拟饵类型",
)
async def update_lure_type(
    lure_type_id: int,
    data: LureTypeUpdate,
    current_user=Depends(require_permission("content:update")),
):
    """更新拟饵类型"""
    with get_db_session() as session:
        lure_type = (
            session.query(LureType)
            .filter(LureType.lure_type_id == lure_type_id)
            .first()
        )
        if not lure_type:
            raise HTTPException(status_code=404, detail="拟饵类型不存在")

        # 检查名称唯一性
        if data.name and data.name != lure_type.name:
            existing = (
                session.query(LureType).filter(LureType.name == data.name).first()
            )
            if existing:
                raise HTTPException(
                    status_code=400, detail=f"拟饵类型 '{data.name}' 已存在"
                )

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        if "category" in update_data and update_data["category"]:
            update_data["category"] = update_data["category"].value

        for field, value in update_data.items():
            setattr(lure_type, field, value)

        session.commit()
        session.refresh(lure_type)

        logger.info(
            f"拟饵类型更新成功: lure_type_id={lure_type_id}, user={current_user.username}"
        )

        return LureTypeResponse.model_validate(lure_type)


@router.delete(
    "/lure-types/{lure_type_id}",
    summary="删除拟饵类型",
    status_code=204,
)
async def delete_lure_type(
    lure_type_id: int,
    current_user=Depends(require_permission("content:delete")),
):
    """删除拟饵类型"""
    with get_db_session() as session:
        lure_type = (
            session.query(LureType)
            .filter(LureType.lure_type_id == lure_type_id)
            .first()
        )
        if not lure_type:
            raise HTTPException(status_code=404, detail="拟饵类型不存在")

        name = lure_type.name
        session.delete(lure_type)
        session.commit()

        logger.info(
            f"拟饵类型删除成功: lure_type_id={lure_type_id}, "
            f"name={name}, user={current_user.username}"
        )


# ========== Init Data Endpoint ==========


@router.post(
    "/lure-types/init",
    response_model=InitDataResponse,
    summary="初始化默认拟饵类型数据",
)
async def init_lure_types(
    current_user=Depends(require_permission("content:create")),
):
    """初始化常用拟饵类型数据（仅在数据库为空时执行）"""
    with get_db_session() as session:
        # 检查是否已有数据
        existing_count = session.query(LureType).count()
        if existing_count > 0:
            return InitDataResponse(
                created_count=0,
                message=f"数据库已有 {existing_count} 条拟饵类型数据，跳过初始化",
            )

        # 创建默认数据
        created_count = 0
        for lure_data in DEFAULT_LURE_TYPES:
            lure_type = LureType(**lure_data)
            session.add(lure_type)
            created_count += 1

        session.commit()

        logger.info(
            f"拟饵类型数据初始化完成: created_count={created_count}, "
            f"user={current_user.username}"
        )

        return InitDataResponse(
            created_count=created_count,
            message=f"成功创建 {created_count} 条拟饵类型数据",
        )
