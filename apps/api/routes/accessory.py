"""
钓鱼配件管理 API 路由

提供钓鱼配件的 CRUD 操作和初始化数据功能
包括钩子、铅坠、转环、前导线、浮漂、别针等
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func

from apps.api.auth.dependencies import get_current_user, require_permission
from apps.api.models import Accessory
from apps.api.orm import get_db_session
from apps.api.schemas.accessory import (
    AccessoryCategoryEnum,
    AccessoryCategoryStats,
    AccessoryCategoryStatsResponse,
    AccessoryCreate,
    AccessoryInitDataResponse,
    AccessoryListItem,
    AccessoryListResponse,
    AccessoryOptionsResponse,
    AccessoryResponse,
    AccessoryUpdate,
    UserLevelEnum,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 分类配置
CATEGORY_CONFIG = {
    "hook": {"label": "钩子", "icon": "🪝", "color": "#1890ff"},
    "sinker": {"label": "铅坠", "icon": "⚓", "color": "#722ed1"},
    "swivel": {"label": "转环", "icon": "🔗", "color": "#52c41a"},
    "leader": {"label": "前导线", "icon": "〰️", "color": "#faad14"},
    "float": {"label": "浮漂", "icon": "🔴", "color": "#eb2f96"},
    "snap": {"label": "别针", "icon": "📎", "color": "#13c2c2"},
    "other": {"label": "其他", "icon": "🎣", "color": "#8c8c8c"},
}

# 用户等级配置
USER_LEVEL_CONFIG = {
    "beginner": {"label": "新手", "color": "#52c41a"},
    "intermediate": {"label": "进阶", "color": "#1890ff"},
    "advanced": {"label": "高级", "color": "#722ed1"},
}

# 常用材质
COMMON_MATERIALS = [
    "碳钢",
    "不锈钢",
    "钨合金",
    "铅",
    "尼龙",
    "碳素",
    "氟碳",
    "钛合金",
    "黄铜",
    "PE材质",
]

# 初始化数据
DEFAULT_ACCESSORIES = [
    # 钩子类
    {
        "name": "曲柄钩",
        "category": "hook",
        "description": "路亚软饵专用钩，钩柄弯曲设计便于挂装软饵",
        "features": "防挂底、软饵专用、多种号数",
        "size": "#1/0 - #5/0",
        "material": "碳钢",
        "target_species": "黑鲈、鳜鱼",
        "applicable_rigs": "Texas钓组、Carolina钓组",
        "user_level": "beginner",
    },
    {
        "name": "铅头钩",
        "category": "hook",
        "description": "带铅头的钩子，可直接挂软饵使用",
        "features": "自带配重、快速下沉、操作简单",
        "size": "3.5g - 21g",
        "weight": 7.0,
        "material": "铅+碳钢",
        "target_species": "黑鲈、鳜鱼、翘嘴",
        "applicable_rigs": "铅头钩钓组",
        "user_level": "beginner",
    },
    {
        "name": "虫钩",
        "category": "hook",
        "description": "适合挂装细长型软饵的钩子",
        "features": "细长钩条、适合面条虫",
        "size": "#1 - #4",
        "material": "碳钢",
        "target_species": "黑鲈、鲤鱼",
        "applicable_rigs": "Wacky钓组、Neko钓组",
        "user_level": "intermediate",
    },
    {
        "name": "三本钩",
        "category": "hook",
        "description": "硬饵常用的三叉钩",
        "features": "三个钩尖、中鱼率高、适合硬饵",
        "size": "#4 - #1/0",
        "material": "碳钢",
        "target_species": "各类路亚对象鱼",
        "applicable_rigs": "硬饵钓组",
        "user_level": "beginner",
    },
    # 铅坠类
    {
        "name": "子弹铅",
        "category": "sinker",
        "description": "子弹形状的铅坠，可穿过障碍区",
        "features": "子弹造型、防挂底、穿透力强",
        "size": "3.5g - 21g",
        "weight": 7.0,
        "material": "铅",
        "target_species": "黑鲈、鳜鱼",
        "applicable_rigs": "Texas钓组",
        "user_level": "beginner",
    },
    {
        "name": "钨钢子弹铅",
        "category": "sinker",
        "description": "钨合金材质的子弹铅，体积更小密度更大",
        "features": "高密度、体积小、灵敏度高、环保",
        "size": "3.5g - 14g",
        "weight": 7.0,
        "material": "钨合金",
        "target_species": "黑鲈、鳜鱼",
        "applicable_rigs": "Texas钓组、Carolina钓组",
        "user_level": "intermediate",
        "price_min": 15,
        "price_max": 50,
    },
    {
        "name": "Drop Shot铅",
        "category": "sinker",
        "description": "倒吊钓组专用的圆柱形铅坠",
        "features": "底部触感好、适合精细作钓",
        "size": "3.5g - 10.5g",
        "weight": 5.0,
        "material": "铅",
        "target_species": "黑鲈、鳜鱼",
        "applicable_rigs": "Drop Shot钓组",
        "user_level": "intermediate",
    },
    {
        "name": "夹铅",
        "category": "sinker",
        "description": "可夹在线上的小铅粒",
        "features": "可调节位置、微调配重",
        "size": "B - 4B",
        "weight": 0.5,
        "material": "铅",
        "target_species": "各类对象鱼",
        "applicable_rigs": "多种钓组",
        "user_level": "beginner",
    },
    # 转环类
    {
        "name": "八字环",
        "category": "swivel",
        "description": "连接主线和前导线的基础转环",
        "features": "防缠绕、连接稳固",
        "size": "#3 - #7",
        "material": "不锈钢",
        "target_species": "各类对象鱼",
        "applicable_rigs": "多种钓组",
        "user_level": "beginner",
    },
    {
        "name": "滚珠轴承转环",
        "category": "swivel",
        "description": "内置滚珠轴承的高端转环",
        "features": "超顺滑旋转、适合亮片等旋转饵",
        "size": "#1 - #5",
        "material": "不锈钢+黄铜",
        "target_species": "翘嘴、鲈鱼",
        "applicable_rigs": "亮片钓组",
        "user_level": "intermediate",
        "price_min": 5,
        "price_max": 20,
    },
    # 前导线类
    {
        "name": "碳素前导线",
        "category": "leader",
        "description": "氟碳材质的前导线，水下近乎隐形",
        "features": "高透明、耐磨、抗紫外线",
        "size": "6lb - 20lb",
        "material": "氟碳",
        "target_species": "各类对象鱼",
        "applicable_rigs": "多种钓组",
        "user_level": "beginner",
    },
    {
        "name": "钢丝前导线",
        "category": "leader",
        "description": "防咬断的钢丝前导线",
        "features": "防咬断、适合有牙齿的鱼种",
        "size": "20lb - 80lb",
        "material": "不锈钢丝",
        "target_species": "狗鱼、鳡鱼、带鱼",
        "applicable_rigs": "多种钓组",
        "user_level": "intermediate",
    },
    # 浮漂类
    {
        "name": "路亚浮漂",
        "category": "float",
        "description": "路亚专用浮漂，用于控制饵的泳层",
        "features": "控制泳层、增加抛投距离",
        "size": "3g - 15g",
        "weight": 8.0,
        "material": "泡沫+塑料",
        "target_species": "翘嘴、鲈鱼",
        "applicable_rigs": "浮漂钓组",
        "user_level": "intermediate",
    },
    {
        "name": "水滴浮漂",
        "category": "float",
        "description": "水滴形状的透明浮漂",
        "features": "可注水调节重量、隐蔽性好",
        "size": "中号 - 大号",
        "material": "透明塑料",
        "target_species": "翘嘴、鲈鱼",
        "applicable_rigs": "浮漂钓组",
        "user_level": "beginner",
    },
    # 别针类
    {
        "name": "快速别针",
        "category": "snap",
        "description": "快速更换拟饵的连接器",
        "features": "快速更换、操作便捷",
        "size": "#0 - #3",
        "material": "不锈钢",
        "target_species": "各类对象鱼",
        "applicable_rigs": "多种钓组",
        "user_level": "beginner",
    },
    {
        "name": "O型环",
        "category": "snap",
        "description": "连接拟饵的O型分体环",
        "features": "动作自由、适合硬饵",
        "size": "#2 - #4",
        "material": "不锈钢",
        "target_species": "各类对象鱼",
        "applicable_rigs": "硬饵钓组",
        "user_level": "intermediate",
    },
]


# ========== CRUD Endpoints ==========


@router.post(
    "/accessories",
    response_model=AccessoryResponse,
    summary="创建配件",
    status_code=201,
)
async def create_accessory(
    data: AccessoryCreate,
    current_user=Depends(require_permission("content:create")),
):
    """创建新的钓鱼配件"""
    with get_db_session() as session:
        # 检查名称是否已存在
        existing = (
            session.query(Accessory).filter(Accessory.name == data.name).first()
        )
        if existing:
            raise HTTPException(status_code=400, detail=f"配件 '{data.name}' 已存在")

        accessory = Accessory(
            name=data.name,
            category=data.category.value,
            description=data.description,
            features=data.features,
            size=data.size,
            weight=data.weight,
            material=data.material,
            color=data.color,
            quantity_per_pack=data.quantity_per_pack,
            target_species=data.target_species,
            applicable_rigs=data.applicable_rigs,
            best_conditions=data.best_conditions,
            brand=data.brand,
            price_min=data.price_min,
            price_max=data.price_max,
            user_level=data.user_level.value if data.user_level else "beginner",
            image_url=data.image_url,
        )
        session.add(accessory)
        session.commit()
        session.refresh(accessory)

        logger.info(
            f"配件创建成功: accessory_id={accessory.accessory_id}, "
            f"name={accessory.name}, user={current_user.username}"
        )

        return AccessoryResponse.model_validate(accessory)


@router.get(
    "/accessories",
    response_model=AccessoryListResponse,
    summary="获取配件列表",
)
async def list_accessories(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    user_level: Optional[str] = Query(None, description="用户等级筛选"),
    current_user=Depends(get_current_user),
):
    """获取配件分页列表"""
    with get_db_session() as session:
        query = session.query(Accessory)

        # 分类筛选
        if category:
            query = query.filter(Accessory.category == category)

        # 用户等级筛选
        if user_level:
            query = query.filter(Accessory.user_level == user_level)

        # 关键词搜索
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                (Accessory.name.ilike(search_pattern))
                | (Accessory.target_species.ilike(search_pattern))
                | (Accessory.description.ilike(search_pattern))
                | (Accessory.brand.ilike(search_pattern))
            )

        # 统计总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        accessories = (
            query.order_by(Accessory.category, Accessory.name)
            .offset(offset)
            .limit(page_size)
            .all()
        )

        total_pages = (total + page_size - 1) // page_size

        return AccessoryListResponse(
            items=[AccessoryListItem.model_validate(a) for a in accessories],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


@router.get(
    "/accessories/stats",
    response_model=AccessoryCategoryStatsResponse,
    summary="获取分类统计",
)
async def get_category_stats(
    current_user=Depends(get_current_user),
):
    """获取各分类的配件数量统计"""
    with get_db_session() as session:
        stats = (
            session.query(Accessory.category, func.count(Accessory.accessory_id))
            .group_by(Accessory.category)
            .all()
        )

        stats_dict = {category: count for category, count in stats}
        total = sum(stats_dict.values())

        categories = []
        for cat_key, config in CATEGORY_CONFIG.items():
            categories.append(
                AccessoryCategoryStats(
                    category=cat_key,
                    count=stats_dict.get(cat_key, 0),
                    label=config["label"],
                    icon=config["icon"],
                    color=config["color"],
                )
            )

        return AccessoryCategoryStatsResponse(categories=categories, total=total)


@router.get(
    "/accessories/options",
    response_model=AccessoryOptionsResponse,
    summary="获取表单选项",
)
async def get_accessory_options(
    current_user=Depends(get_current_user),
):
    """获取配件表单的选项数据"""
    categories = [
        {"value": key, "label": config["label"], "icon": config["icon"], "color": config["color"]}
        for key, config in CATEGORY_CONFIG.items()
    ]

    user_levels = [
        {"value": key, "label": config["label"], "color": config["color"]}
        for key, config in USER_LEVEL_CONFIG.items()
    ]

    return AccessoryOptionsResponse(
        categories=categories,
        user_levels=user_levels,
        materials=COMMON_MATERIALS,
    )


@router.get(
    "/accessories/{accessory_id}",
    response_model=AccessoryResponse,
    summary="获取配件详情",
)
async def get_accessory(
    accessory_id: int,
    current_user=Depends(get_current_user),
):
    """获取配件详情"""
    with get_db_session() as session:
        accessory = (
            session.query(Accessory)
            .filter(Accessory.accessory_id == accessory_id)
            .first()
        )
        if not accessory:
            raise HTTPException(status_code=404, detail="配件不存在")

        return AccessoryResponse.model_validate(accessory)


@router.put(
    "/accessories/{accessory_id}",
    response_model=AccessoryResponse,
    summary="更新配件",
)
async def update_accessory(
    accessory_id: int,
    data: AccessoryUpdate,
    current_user=Depends(require_permission("content:update")),
):
    """更新配件"""
    with get_db_session() as session:
        accessory = (
            session.query(Accessory)
            .filter(Accessory.accessory_id == accessory_id)
            .first()
        )
        if not accessory:
            raise HTTPException(status_code=404, detail="配件不存在")

        # 检查名称唯一性
        if data.name and data.name != accessory.name:
            existing = (
                session.query(Accessory).filter(Accessory.name == data.name).first()
            )
            if existing:
                raise HTTPException(
                    status_code=400, detail=f"配件 '{data.name}' 已存在"
                )

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        if "category" in update_data and update_data["category"]:
            update_data["category"] = update_data["category"].value
        if "user_level" in update_data and update_data["user_level"]:
            update_data["user_level"] = update_data["user_level"].value

        for field, value in update_data.items():
            setattr(accessory, field, value)

        session.commit()
        session.refresh(accessory)

        logger.info(
            f"配件更新成功: accessory_id={accessory_id}, user={current_user.username}"
        )

        return AccessoryResponse.model_validate(accessory)


@router.delete(
    "/accessories/{accessory_id}",
    summary="删除配件",
    status_code=204,
)
async def delete_accessory(
    accessory_id: int,
    current_user=Depends(require_permission("content:delete")),
):
    """删除配件"""
    with get_db_session() as session:
        accessory = (
            session.query(Accessory)
            .filter(Accessory.accessory_id == accessory_id)
            .first()
        )
        if not accessory:
            raise HTTPException(status_code=404, detail="配件不存在")

        name = accessory.name
        session.delete(accessory)
        session.commit()

        logger.info(
            f"配件删除成功: accessory_id={accessory_id}, "
            f"name={name}, user={current_user.username}"
        )


# ========== Init Data Endpoint ==========


@router.post(
    "/accessories/init",
    response_model=AccessoryInitDataResponse,
    summary="初始化默认配件数据",
)
async def init_accessories(
    current_user=Depends(require_permission("content:create")),
):
    """初始化常用钓鱼配件数据（仅在数据库为空时执行）"""
    with get_db_session() as session:
        # 检查是否已有数据
        existing_count = session.query(Accessory).count()
        if existing_count > 0:
            return AccessoryInitDataResponse(
                created_count=0,
                message=f"数据库已有 {existing_count} 条配件数据，跳过初始化",
            )

        # 创建默认数据
        created_count = 0
        for accessory_data in DEFAULT_ACCESSORIES:
            accessory = Accessory(**accessory_data)
            session.add(accessory)
            created_count += 1

        session.commit()

        logger.info(
            f"配件数据初始化完成: created_count={created_count}, "
            f"user={current_user.username}"
        )

        return AccessoryInitDataResponse(
            created_count=created_count,
            message=f"成功创建 {created_count} 条配件数据",
        )
