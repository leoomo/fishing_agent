"""
鱼百科管理 API 路由

提供鱼种、知识库、季节活动的 CRUD 操作和装备推荐查询
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func

from apps.api.auth.dependencies import get_current_user, require_permission
from apps.api.models.fish import FishSpecies, FishKnowledge, FishSeasonActivity, ActivityLevel
from apps.api.orm import get_db_session
from apps.api.schemas.fish import (
    CategoryStats,
    CategoryStatsResponse,
    EquipmentRecommendation,
    FishKnowledgeCreate,
    FishKnowledgeResponse,
    FishKnowledgeUpdate,
    FishSeasonActivityCreate,
    FishSeasonActivityResponse,
    FishSeasonActivityUpdate,
    FishSpeciesCreate,
    FishSpeciesListItem,
    FishSpeciesListResponse,
    FishSpeciesResponse,
    FishSpeciesUpdate,
    InitDataResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 分类配置
CATEGORY_CONFIG = {
    "freshwater": {"label": "淡水鱼", "icon": "🐟", "color": "#1890ff"},
    "saltwater": {"label": "海水鱼", "icon": "🐠", "color": "#13c2c2"},
    "brackish": {"label": "广盐鱼", "icon": "🐡", "color": "#722ed1"},
}

# 装备推荐数据 (来自 init_data.py)
EQUIPMENT_RECOMMENDATIONS = {
    "大嘴鲈": {
        "recommended_lures": ["软虫", "米诺", "摇滚", "VIB", "铅头钩"],
        "recommended_rigs": ["德州钓组", "无铅钓组", "卡罗莱纳钓组", "倒吊钓组"],
        "recommended_rod_power": ["ML", "M", "MH"],
        "recommended_line_lb_min": 8,
        "recommended_line_lb_max": 20,
        "lure_difficulty": "新手",
        "fight_intensity": "中等",
    },
    "翘嘴鲌": {
        "recommended_lures": ["米诺", "VIB", "亮片", "波爬"],
        "recommended_rigs": ["直接连接", "前导线钓组"],
        "recommended_rod_power": ["L", "ML", "M"],
        "recommended_line_lb_min": 6,
        "recommended_line_lb_max": 15,
        "lure_difficulty": "新手",
        "fight_intensity": "中等",
    },
    "鳜鱼": {
        "recommended_lures": ["软虫", "卷尾蛆", "T尾", "铅头钩"],
        "recommended_rigs": ["德州钓组", "铅头钩钓组", "倒吊钓组"],
        "recommended_rod_power": ["M", "MH", "H"],
        "recommended_line_lb_min": 10,
        "recommended_line_lb_max": 25,
        "lure_difficulty": "进阶",
        "fight_intensity": "激烈",
    },
    "黑鱼": {
        "recommended_lures": ["雷蛙", "软饵", "米诺", "VIB"],
        "recommended_rigs": ["雷蛙钓组", "德州钓组", "无铅钓组"],
        "recommended_rod_power": ["MH", "H", "XH"],
        "recommended_line_lb_min": 20,
        "recommended_line_lb_max": 50,
        "lure_difficulty": "新手",
        "fight_intensity": "激烈",
    },
    "鲶鱼": {
        "recommended_lures": ["软虫", "卷尾蛆", "铅头钩", "VIB"],
        "recommended_rigs": ["德州钓组", "卡罗莱纳钓组", "铅头钩钓组"],
        "recommended_rod_power": ["M", "MH"],
        "recommended_line_lb_min": 10,
        "recommended_line_lb_max": 30,
        "lure_difficulty": "新手",
        "fight_intensity": "中等",
    },
    "马口鱼": {
        "recommended_lures": ["微型米诺", "微型亮片", "飞蝇"],
        "recommended_rigs": ["直接连接", "马口专用钓组"],
        "recommended_rod_power": ["UL", "L"],
        "recommended_line_lb_min": 2,
        "recommended_line_lb_max": 6,
        "lure_difficulty": "新手",
        "fight_intensity": "温和",
    },
    "鲤鱼": {
        "recommended_lures": ["软虫", "米诺", "摇滚", "VIB"],
        "recommended_rigs": ["德州钓组", "无铅钓组", "铅头钩钓组"],
        "recommended_rod_power": ["M", "MH"],
        "recommended_line_lb_min": 10,
        "recommended_line_lb_max": 25,
        "lure_difficulty": "新手",
        "fight_intensity": "中等",
    },
}

# 初始化数据
DEFAULT_FISH_DATA = [
    {
        "name_cn": "大嘴鲈",
        "name_en": "Largemouth Bass",
        "scientific_name": "Micropterus salmoides",
        "category": "freshwater",
        "habitat": "中上层",
        "description": "最受欢迎的路亚对象鱼之一，原产北美，现已在中国广泛养殖和分布。体型侧扁，口大，下颌突出。",
        "min_weight": 0.3,
        "max_weight": 5.0,
        "min_length": 20,
        "max_length": 60,
        "season_activity": [
            {"season": "spring", "activity_level": "高", "best_time": "清晨和傍晚", "recommended_lures": "软虫,米诺,摇滚", "fishing_tips": "产卵期护巢行为强烈，雄鱼会主动攻击入侵者"},
            {"season": "summer", "activity_level": "高", "best_time": "早晨和黄昏", "recommended_lures": "VIB,米诺,铅头钩", "fishing_tips": "避开高温时段，在阴凉处和深水区作钓"},
            {"season": "fall", "activity_level": "高", "best_time": "全天", "recommended_lures": "摇滚,VIB,软饵", "fishing_tips": "觅食积极，为越冬储能，是最佳作钓季节"},
            {"season": "winter", "activity_level": "低", "best_time": "中午温暖时段", "recommended_lures": "金属饵,软虫慢拖", "fishing_tips": "动作放慢，使用小型拟饵缓慢作钓"},
        ],
    },
    {
        "name_cn": "翘嘴鲌",
        "name_en": "Topmouth Culter",
        "scientific_name": "Culter alburnus",
        "category": "freshwater",
        "habitat": "中上层",
        "description": "中国本土凶猛鱼类，体型修长，口向上翘，善于追逐猎物。全年活跃，是路亚入门的好对象鱼。",
        "min_weight": 0.5,
        "max_weight": 8.0,
        "min_length": 30,
        "max_length": 80,
        "season_activity": [
            {"season": "spring", "activity_level": "中", "best_time": "上午", "recommended_lures": "米诺,亮片", "fishing_tips": "水温回升后开始活跃"},
            {"season": "summer", "activity_level": "高", "best_time": "清晨和傍晚", "recommended_lures": "米诺,VIB,亮片,波爬", "fishing_tips": "全天活跃，水面系拟饵效果好"},
            {"season": "fall", "activity_level": "高", "best_time": "全天", "recommended_lures": "VIB,米诺,亮片", "fishing_tips": "觅食凶猛，远投搜索效果好"},
            {"season": "winter", "activity_level": "低", "best_time": "中午", "recommended_lures": "VIB,铁板", "fishing_tips": "沉底慢拖，金属饵效果好"},
        ],
    },
    {
        "name_cn": "鳜鱼",
        "name_en": "Mandarin Fish",
        "scientific_name": "Siniperca chuatsi",
        "category": "freshwater",
        "habitat": "底层",
        "description": "中国名贵淡水鱼，肉质鲜美。昼伏夜出，喜欢躲在结构物中伏击猎物。路亚难度较高。",
        "min_weight": 0.3,
        "max_weight": 5.0,
        "min_length": 20,
        "max_length": 70,
        "season_activity": [
            {"season": "spring", "activity_level": "中", "best_time": "傍晚", "recommended_lures": "软虫,铅头钩", "fishing_tips": "水温15度以上开始活跃"},
            {"season": "summer", "activity_level": "高", "best_time": "夜间", "recommended_lures": "软虫,卷尾蛆,T尾", "fishing_tips": "昼伏夜出，夜钓效果最佳"},
            {"season": "fall", "activity_level": "高", "best_time": "傍晚和夜间", "recommended_lures": "软饵,铅头钩", "fishing_tips": "积极觅食，障碍区作钓"},
            {"season": "winter", "activity_level": "低", "best_time": "中午", "recommended_lures": "软虫慢拖", "fishing_tips": "深水区缓慢作钓"},
        ],
    },
    {
        "name_cn": "黑鱼",
        "name_en": "Snakehead",
        "scientific_name": "Channa argus",
        "category": "freshwater",
        "habitat": "中层",
        "description": "又称乌鳢，凶猛的淡水掠食者。耐低氧，可在泥塘等恶劣环境生存。雷蛙作钓极具刺激性。",
        "min_weight": 0.5,
        "max_weight": 10.0,
        "min_length": 30,
        "max_length": 100,
        "season_activity": [
            {"season": "spring", "activity_level": "中", "best_time": "中午", "recommended_lures": "雷蛙,软饵", "fishing_tips": "水温回升后草区活跃"},
            {"season": "summer", "activity_level": "高", "best_time": "清晨和傍晚", "recommended_lures": "雷蛙,软饵,米诺", "fishing_tips": "草洞作钓，雷蛙炸水极具刺激"},
            {"season": "fall", "activity_level": "高", "best_time": "全天", "recommended_lures": "雷蛙,VIB", "fishing_tips": "觅食积极，为越冬储能"},
            {"season": "winter", "activity_level": "低", "best_time": "中午", "recommended_lures": "软饵慢拖", "fishing_tips": "深水泥底缓慢搜索"},
        ],
    },
    {
        "name_cn": "鲶鱼",
        "name_en": "Catfish",
        "scientific_name": "Silurus asotus",
        "category": "freshwater",
        "habitat": "底层",
        "description": "杂食性底层鱼类，昼伏夜出。体型可观，搏斗力强。适合使用软饵底钓。",
        "min_weight": 0.5,
        "max_weight": 20.0,
        "min_length": 30,
        "max_length": 120,
        "season_activity": [
            {"season": "spring", "activity_level": "中", "best_time": "夜间", "recommended_lures": "软虫,铅头钩", "fishing_tips": "水温回升后开始活跃"},
            {"season": "summer", "activity_level": "高", "best_time": "夜间", "recommended_lures": "软虫,卷尾蛆,VIB", "fishing_tips": "夜钓效果最佳，底层搜索"},
            {"season": "fall", "activity_level": "高", "best_time": "傍晚和夜间", "recommended_lures": "软饵,铅头钩", "fishing_tips": "积极觅食，深水区作钓"},
            {"season": "winter", "activity_level": "低", "best_time": "中午", "recommended_lures": "软虫慢拖", "fishing_tips": "深水泥底缓慢作钓"},
        ],
    },
    {
        "name_cn": "马口鱼",
        "name_en": "Chinese Minnow",
        "scientific_name": "Opsariichthys bidens",
        "category": "freshwater",
        "habitat": "中上层",
        "description": "小型溪流鱼类，适合超轻装备作钓。颜色艳丽，咬口积极，是入门路亚的好选择。",
        "min_weight": 0.02,
        "max_weight": 0.3,
        "min_length": 5,
        "max_length": 20,
        "season_activity": [
            {"season": "spring", "activity_level": "高", "best_time": "全天", "recommended_lures": "微型米诺,微型亮片", "fishing_tips": "溪流作钓，水温适中时最活跃"},
            {"season": "summer", "activity_level": "高", "best_time": "清晨和傍晚", "recommended_lures": "微型米诺,飞蝇", "fishing_tips": "避开高温，选择阴凉溪段"},
            {"season": "fall", "activity_level": "高", "best_time": "全天", "recommended_lures": "微型亮片,飞蝇", "fishing_tips": "最佳作钓季节，咬口积极"},
            {"season": "winter", "activity_level": "中", "best_time": "中午", "recommended_lures": "微型米诺", "fishing_tips": "水温较低时活性下降"},
        ],
    },
    {
        "name_cn": "鲤鱼",
        "name_en": "Common Carp",
        "scientific_name": "Cyprinus carpio",
        "category": "freshwater",
        "habitat": "底层",
        "description": "广泛分布的淡水鱼类，体型大，力量强。虽非典型路亚对象鱼，但在特定情况下可用软饵作钓。",
        "min_weight": 0.5,
        "max_weight": 30.0,
        "min_length": 20,
        "max_length": 100,
        "season_activity": [
            {"season": "spring", "activity_level": "中", "best_time": "上午", "recommended_lures": "软虫,铅头钩", "fishing_tips": "水温回升后开始活跃"},
            {"season": "summer", "activity_level": "高", "best_time": "清晨和傍晚", "recommended_lures": "软虫,米诺", "fishing_tips": "浅水觅食，底层搜索"},
            {"season": "fall", "activity_level": "高", "best_time": "全天", "recommended_lures": "软饵,VIB", "fishing_tips": "积极觅食，力量强劲"},
            {"season": "winter", "activity_level": "低", "best_time": "中午", "recommended_lures": "软虫慢拖", "fishing_tips": "深水区缓慢作钓"},
        ],
    },
]


# ========== Helper Functions ==========


def fish_to_response(fish: FishSpecies) -> FishSpeciesResponse:
    """Convert FishSpecies model to response"""
    knowledge_list = []
    for k in fish.knowledge:
        knowledge_list.append(FishKnowledgeResponse(
            id=k.id,
            species_id=k.species_id,
            topic=k.topic,
            content=k.content,
            source=k.source,
            tags=k.tags,
            created_at=k.created_at,
            updated_at=k.updated_at,
        ))

    season_list = []
    for s in fish.season_activity:
        activity_level = s.activity_level
        if isinstance(activity_level, ActivityLevel):
            activity_level = activity_level.value
        season_list.append(FishSeasonActivityResponse(
            id=s.id,
            species_id=s.species_id,
            season=s.season,
            activity_level=activity_level,
            best_time=s.best_time,
            recommended_lures=s.recommended_lures,
            fishing_tips=s.fishing_tips,
            created_at=s.created_at,
            updated_at=s.updated_at,
        ))

    return FishSpeciesResponse(
        species_id=fish.species_id,
        name_cn=fish.name_cn,
        name_en=fish.name_en,
        scientific_name=fish.scientific_name,
        category=fish.category or "",
        habitat=fish.habitat,
        description=fish.description,
        image_url=fish.image_url,
        min_weight=fish.min_weight,
        max_weight=fish.max_weight,
        min_length=fish.min_length,
        max_length=fish.max_length,
        created_at=fish.created_at,
        updated_at=fish.updated_at,
        knowledge=knowledge_list,
        season_activity=season_list,
    )


def fish_to_list_item(fish: FishSpecies) -> FishSpeciesListItem:
    """Convert FishSpecies model to list item"""
    return FishSpeciesListItem(
        species_id=fish.species_id,
        name_cn=fish.name_cn,
        name_en=fish.name_en,
        category=fish.category or "",
        habitat=fish.habitat,
        knowledge_count=len(fish.knowledge),
        season_count=len(fish.season_activity),
        created_at=fish.created_at,
    )


# ========== Stats Endpoint ==========


@router.get(
    "/fish-species/stats",
    response_model=CategoryStatsResponse,
    summary="获取分类统计",
)
async def get_category_stats(
    current_user=Depends(get_current_user),
):
    """获取各分类的鱼种数量统计"""
    with get_db_session() as session:
        stats = (
            session.query(FishSpecies.category, func.count(FishSpecies.species_id))
            .group_by(FishSpecies.category)
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


# ========== FishSpecies CRUD ==========


@router.get(
    "/fish-species",
    response_model=FishSpeciesListResponse,
    summary="获取鱼种列表",
)
async def list_fish_species(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    habitat: Optional[str] = Query(None, description="栖息地筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user=Depends(get_current_user),
):
    """获取鱼种分页列表"""
    with get_db_session() as session:
        query = session.query(FishSpecies)

        # 分类筛选
        if category:
            query = query.filter(FishSpecies.category == category)

        # 栖息地筛选
        if habitat:
            query = query.filter(FishSpecies.habitat.ilike(f"%{habitat}%"))

        # 关键词搜索
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                (FishSpecies.name_cn.ilike(search_pattern))
                | (FishSpecies.name_en.ilike(search_pattern))
                | (FishSpecies.scientific_name.ilike(search_pattern))
                | (FishSpecies.description.ilike(search_pattern))
            )

        # 统计总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        fish_list = query.order_by(FishSpecies.name_cn).offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size

        return FishSpeciesListResponse(
            items=[fish_to_list_item(f) for f in fish_list],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


@router.get(
    "/fish-species/{species_id}",
    response_model=FishSpeciesResponse,
    summary="获取鱼种详情",
)
async def get_fish_species(
    species_id: int,
    current_user=Depends(get_current_user),
):
    """获取鱼种详情(含知识库和季节活动)"""
    with get_db_session() as session:
        fish = session.query(FishSpecies).filter(FishSpecies.species_id == species_id).first()
        if not fish:
            raise HTTPException(status_code=404, detail="鱼种不存在")

        return fish_to_response(fish)


@router.post(
    "/fish-species",
    response_model=FishSpeciesResponse,
    summary="创建鱼种",
    status_code=201,
)
async def create_fish_species(
    data: FishSpeciesCreate,
    current_user=Depends(require_permission("content:create")),
):
    """创建新的鱼种"""
    with get_db_session() as session:
        # 检查名称是否已存在
        existing = session.query(FishSpecies).filter(FishSpecies.name_cn == data.name_cn).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"鱼种 '{data.name_cn}' 已存在")

        fish = FishSpecies(
            name_cn=data.name_cn,
            name_en=data.name_en,
            scientific_name=data.scientific_name,
            category=data.category.value,
            habitat=data.habitat,
            description=data.description,
            image_url=data.image_url,
            min_weight=data.min_weight,
            max_weight=data.max_weight,
            min_length=data.min_length,
            max_length=data.max_length,
        )
        session.add(fish)
        session.commit()
        session.refresh(fish)

        logger.info(f"鱼种创建成功: species_id={fish.species_id}, name={fish.name_cn}, user={current_user.username}")

        return fish_to_response(fish)


@router.put(
    "/fish-species/{species_id}",
    response_model=FishSpeciesResponse,
    summary="更新鱼种",
)
async def update_fish_species(
    species_id: int,
    data: FishSpeciesUpdate,
    current_user=Depends(require_permission("content:update")),
):
    """更新鱼种基本信息"""
    with get_db_session() as session:
        fish = session.query(FishSpecies).filter(FishSpecies.species_id == species_id).first()
        if not fish:
            raise HTTPException(status_code=404, detail="鱼种不存在")

        # 检查名称唯一性
        if data.name_cn and data.name_cn != fish.name_cn:
            existing = session.query(FishSpecies).filter(
                FishSpecies.name_cn == data.name_cn,
                FishSpecies.species_id != species_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"鱼种 '{data.name_cn}' 已存在")

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        if "category" in update_data and update_data["category"]:
            update_data["category"] = update_data["category"].value

        for field, value in update_data.items():
            setattr(fish, field, value)

        session.commit()
        session.refresh(fish)

        logger.info(f"鱼种更新成功: species_id={species_id}, user={current_user.username}")

        return fish_to_response(fish)


@router.delete(
    "/fish-species/{species_id}",
    summary="删除鱼种",
    status_code=204,
)
async def delete_fish_species(
    species_id: int,
    current_user=Depends(require_permission("content:delete")),
):
    """删除鱼种及其关联数据"""
    with get_db_session() as session:
        fish = session.query(FishSpecies).filter(FishSpecies.species_id == species_id).first()
        if not fish:
            raise HTTPException(status_code=404, detail="鱼种不存在")

        name = fish.name_cn
        session.delete(fish)
        session.commit()

        logger.info(f"鱼种删除成功: species_id={species_id}, name={name}, user={current_user.username}")


# ========== Knowledge Management ==========


@router.post(
    "/fish-species/{species_id}/knowledge",
    response_model=FishKnowledgeResponse,
    summary="添加知识条目",
    status_code=201,
)
async def add_knowledge(
    species_id: int,
    data: FishKnowledgeCreate,
    current_user=Depends(require_permission("content:update")),
):
    """为鱼种添加知识条目"""
    with get_db_session() as session:
        fish = session.query(FishSpecies).filter(FishSpecies.species_id == species_id).first()
        if not fish:
            raise HTTPException(status_code=404, detail="鱼种不存在")

        knowledge = FishKnowledge(
            species_id=species_id,
            topic=data.topic,
            content=data.content,
            source=data.source,
            tags=data.tags,
        )
        session.add(knowledge)
        session.commit()
        session.refresh(knowledge)

        logger.info(f"知识条目添加成功: knowledge_id={knowledge.id}, species_id={species_id}")

        return FishKnowledgeResponse.model_validate(knowledge)


@router.put(
    "/fish-species/{species_id}/knowledge/{knowledge_id}",
    response_model=FishKnowledgeResponse,
    summary="更新知识条目",
)
async def update_knowledge(
    species_id: int,
    knowledge_id: int,
    data: FishKnowledgeUpdate,
    current_user=Depends(require_permission("content:update")),
):
    """更新知识条目"""
    with get_db_session() as session:
        knowledge = session.query(FishKnowledge).filter(
            FishKnowledge.id == knowledge_id,
            FishKnowledge.species_id == species_id
        ).first()
        if not knowledge:
            raise HTTPException(status_code=404, detail="知识条目不存在")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(knowledge, field, value)

        session.commit()
        session.refresh(knowledge)

        logger.info(f"知识条目更新成功: knowledge_id={knowledge_id}")

        return FishKnowledgeResponse.model_validate(knowledge)


@router.delete(
    "/fish-species/{species_id}/knowledge/{knowledge_id}",
    summary="删除知识条目",
    status_code=204,
)
async def delete_knowledge(
    species_id: int,
    knowledge_id: int,
    current_user=Depends(require_permission("content:update")),
):
    """删除知识条目"""
    with get_db_session() as session:
        knowledge = session.query(FishKnowledge).filter(
            FishKnowledge.id == knowledge_id,
            FishKnowledge.species_id == species_id
        ).first()
        if not knowledge:
            raise HTTPException(status_code=404, detail="知识条目不存在")

        session.delete(knowledge)
        session.commit()

        logger.info(f"知识条目删除成功: knowledge_id={knowledge_id}")


# ========== Season Activity Management ==========


@router.post(
    "/fish-species/{species_id}/seasons",
    response_model=FishSeasonActivityResponse,
    summary="添加季节活动",
    status_code=201,
)
async def add_season_activity(
    species_id: int,
    data: FishSeasonActivityCreate,
    current_user=Depends(require_permission("content:update")),
):
    """为鱼种添加季节活动"""
    with get_db_session() as session:
        fish = session.query(FishSpecies).filter(FishSpecies.species_id == species_id).first()
        if not fish:
            raise HTTPException(status_code=404, detail="鱼种不存在")

        # 检查季节是否已存在
        existing = session.query(FishSeasonActivity).filter(
            FishSeasonActivity.species_id == species_id,
            FishSeasonActivity.season == data.season.value
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"季节 '{data.season.value}' 的活动已存在")

        activity = FishSeasonActivity(
            species_id=species_id,
            season=data.season.value,
            activity_level=ActivityLevel(data.activity_level.value),
            best_time=data.best_time,
            recommended_lures=data.recommended_lures,
            fishing_tips=data.fishing_tips,
        )
        session.add(activity)
        session.commit()
        session.refresh(activity)

        logger.info(f"季节活动添加成功: activity_id={activity.id}, species_id={species_id}, season={data.season.value}")

        return FishSeasonActivityResponse(
            id=activity.id,
            species_id=activity.species_id,
            season=activity.season,
            activity_level=activity.activity_level.value if isinstance(activity.activity_level, ActivityLevel) else activity.activity_level,
            best_time=activity.best_time,
            recommended_lures=activity.recommended_lures,
            fishing_tips=activity.fishing_tips,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
        )


@router.put(
    "/fish-species/{species_id}/seasons/{activity_id}",
    response_model=FishSeasonActivityResponse,
    summary="更新季节活动",
)
async def update_season_activity(
    species_id: int,
    activity_id: int,
    data: FishSeasonActivityUpdate,
    current_user=Depends(require_permission("content:update")),
):
    """更新季节活动"""
    with get_db_session() as session:
        activity = session.query(FishSeasonActivity).filter(
            FishSeasonActivity.id == activity_id,
            FishSeasonActivity.species_id == species_id
        ).first()
        if not activity:
            raise HTTPException(status_code=404, detail="季节活动不存在")

        update_data = data.model_dump(exclude_unset=True)
        if "season" in update_data and update_data["season"]:
            update_data["season"] = update_data["season"].value
        if "activity_level" in update_data and update_data["activity_level"]:
            update_data["activity_level"] = ActivityLevel(update_data["activity_level"].value)

        for field, value in update_data.items():
            setattr(activity, field, value)

        session.commit()
        session.refresh(activity)

        logger.info(f"季节活动更新成功: activity_id={activity_id}")

        return FishSeasonActivityResponse(
            id=activity.id,
            species_id=activity.species_id,
            season=activity.season,
            activity_level=activity.activity_level.value if isinstance(activity.activity_level, ActivityLevel) else activity.activity_level,
            best_time=activity.best_time,
            recommended_lures=activity.recommended_lures,
            fishing_tips=activity.fishing_tips,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
        )


@router.delete(
    "/fish-species/{species_id}/seasons/{activity_id}",
    summary="删除季节活动",
    status_code=204,
)
async def delete_season_activity(
    species_id: int,
    activity_id: int,
    current_user=Depends(require_permission("content:update")),
):
    """删除季节活动"""
    with get_db_session() as session:
        activity = session.query(FishSeasonActivity).filter(
            FishSeasonActivity.id == activity_id,
            FishSeasonActivity.species_id == species_id
        ).first()
        if not activity:
            raise HTTPException(status_code=404, detail="季节活动不存在")

        session.delete(activity)
        session.commit()

        logger.info(f"季节活动删除成功: activity_id={activity_id}")


# ========== Equipment Recommendation ==========


@router.get(
    "/fish-species/{species_id}/equipment",
    response_model=EquipmentRecommendation,
    summary="获取装备推荐",
)
async def get_equipment_recommendation(
    species_id: int,
    current_user=Depends(get_current_user),
):
    """获取鱼种的装备推荐(只读)"""
    with get_db_session() as session:
        fish = session.query(FishSpecies).filter(FishSpecies.species_id == species_id).first()
        if not fish:
            raise HTTPException(status_code=404, detail="鱼种不存在")

        # 从预定义数据中查找
        recommendation = EQUIPMENT_RECOMMENDATIONS.get(fish.name_cn)
        if recommendation:
            return EquipmentRecommendation(**recommendation)

        # 返回空推荐
        return EquipmentRecommendation()


# ========== Init Data Endpoint ==========


@router.post(
    "/fish-species/init",
    response_model=InitDataResponse,
    summary="初始化默认鱼种数据",
)
async def init_fish_data(
    current_user=Depends(require_permission("content:create")),
):
    """初始化常用鱼种数据（仅在数据库为空时执行）"""
    with get_db_session() as session:
        # 检查是否已有数据
        existing_count = session.query(FishSpecies).count()
        if existing_count > 0:
            return InitDataResponse(
                created_count=0,
                message=f"数据库已有 {existing_count} 条鱼种数据，跳过初始化",
            )

        # 创建默认数据
        created_count = 0
        for fish_data in DEFAULT_FISH_DATA:
            season_data = fish_data.pop("season_activity", [])

            fish = FishSpecies(**fish_data)
            session.add(fish)
            session.flush()

            # 创建季节活动
            for s in season_data:
                activity = FishSeasonActivity(
                    species_id=fish.species_id,
                    season=s["season"],
                    activity_level=ActivityLevel(s["activity_level"]),
                    best_time=s.get("best_time"),
                    recommended_lures=s.get("recommended_lures"),
                    fishing_tips=s.get("fishing_tips"),
                )
                session.add(activity)

            created_count += 1

        session.commit()

        logger.info(f"鱼种数据初始化完成: created_count={created_count}, user={current_user.username}")

        return InitDataResponse(
            created_count=created_count,
            message=f"成功创建 {created_count} 条鱼种数据",
        )
