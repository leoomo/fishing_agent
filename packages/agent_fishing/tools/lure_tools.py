"""
路亚装备LangChain工具模块

提供4个核心工具供LLM Agent使用：
1. recommend_equipment - 装备推荐（买什么）
2. compare_equipment - 装备对比（比哪个）
3. lookup_fishing_knowledge - 知识查询（学什么）
4. identify_from_image - 图片识别（看什么）
"""

from langchain.tools import tool
from typing import Optional, Dict, Any, List
import json

# 服务缓存（懒加载）
_services: Dict[str, Any] = {}


def _get_services():
    """获取服务实例（懒加载）"""
    global _services

    if not _services:
        from .lure.database import get_db
        from .lure.vector_store import get_vector_store
        from .lure.image_manager import ImageManager, LocalImageStorage
        from .lure.fish_knowledge import FishKnowledgeService
        from .lure.comparator import EquipmentComparator
        from .lure.knowledge_search import KnowledgeSearchService
        from .lure.knowledge_indexer import KnowledgeIndexer
        from .lure.recommender import LureRecommender
        from pathlib import Path

        base_path = Path(__file__).parent / "lure" / "data"

        db = get_db()
        vector_store = get_vector_store(use_simple=True)  # 默认使用简化版
        storage = LocalImageStorage(str(base_path / "images"))
        image_manager = ImageManager(db, storage)

        _services['db'] = db
        _services['vector_store'] = vector_store
        _services['image_manager'] = image_manager
        _services['comparator'] = EquipmentComparator(db, image_manager)
        _services['fish_service'] = FishKnowledgeService(db, image_manager, vector_store)
        _services['search_service'] = KnowledgeSearchService(db, vector_store, image_manager)
        _services['indexer'] = KnowledgeIndexer(db, vector_store, image_manager)
        _services['recommender'] = LureRecommender(db)

    return _services


def _normalize_equipment_type(equipment_type: str) -> Optional[str]:
    """标准化装备类型"""
    type_mapping = {
        # 鱼竿
        "鱼竿": "鱼竿", "竿子": "鱼竿", "路亚竿": "鱼竿", "竿": "鱼竿",
        # 渔轮
        "渔轮": "渔轮", "轮子": "渔轮", "纺车轮": "渔轮", "水滴轮": "渔轮", "轮": "渔轮",
        # 鱼线
        "鱼线": "鱼线", "线": "鱼线", "PE线": "鱼线", "碳线": "鱼线", "尼龙线": "鱼线",
        # 拟饵
        "拟饵": "拟饵", "饵": "拟饵", "假饵": "拟饵", "软饵": "拟饵", "硬饵": "拟饵",
        # 套装
        "套装": "套装", "全套": "套装", "入门套装": "套装",
    }
    return type_mapping.get(equipment_type)


def _classify_topic(topic: str) -> str:
    """分类查询主题"""
    FISH_KEYWORDS = ["鱼", "鲈", "翘嘴", "鳜", "黑鱼", "鲶", "习性", "活跃", "吃什么", "捕食"]
    RIG_KEYWORDS = ["钓组", "怎么绑", "怎么用", "组装", "德州", "卡罗", "倒吊", "无铅", "配重"]
    TECHNIQUE_KEYWORDS = ["技巧", "怎么钓", "作钓", "方法", "操作", "收线", "抽停"]

    topic_lower = topic.lower()

    if any(kw in topic_lower for kw in RIG_KEYWORDS):
        return "rig"
    elif any(kw in topic_lower for kw in FISH_KEYWORDS):
        return "fish"
    elif any(kw in topic_lower for kw in TECHNIQUE_KEYWORDS):
        return "technique"
    else:
        return "unknown"


# ========== 工具1：装备推荐 ==========

@tool
def recommend_equipment(
    equipment_type: str,
    budget: Optional[float] = None,
    specifications: Optional[str] = None,
    target_fish: Optional[str] = None,
    scenario: Optional[str] = None,
    user_level: Optional[str] = None
) -> str:
    """
    推荐路亚装备 - 用于购买决策

    当用户想要【购买建议】或【选择推荐】时使用。

    触发关键词: 推荐、买、选、预算、性价比、适合新手、入门

    Args:
        equipment_type: 装备类型（鱼竿/渔轮/鱼线/拟饵/套装）
        budget: 预算金额（元），如 500、1000
        specifications: 规格要求JSON字符串，如 '{"硬度": "ML", "长度": "2.1m"}'
        target_fish: 目标鱼种，如 鲈鱼、翘嘴、鳜鱼
        scenario: 使用场景（水草区/深水区/障碍区/岸钓/船钓）
        user_level: 用户水平（新手/进阶/高手）

    Returns:
        Markdown格式的推荐报告

    Examples:
        >>> recommend_equipment("鱼竿", budget=500, specifications='{"硬度": "ML"}')
        >>> recommend_equipment("套装", budget=1000, user_level="新手")
    """
    services = _get_services()
    recommender = services['recommender']
    image_manager = services['image_manager']

    # 1. 参数验证
    normalized_type = _normalize_equipment_type(equipment_type)
    if not normalized_type:
        return f"无法识别的装备类型'{equipment_type}'，支持: 鱼竿、渔轮、鱼线、拟饵、套装"

    # 2. 解析规格参数
    specs = {}
    if specifications:
        try:
            specs = json.loads(specifications)
        except json.JSONDecodeError:
            pass

    # 3. 套装特殊处理
    if normalized_type == "套装":
        return _recommend_package(
            budget=budget or 1000,
            user_level=user_level or "新手",
            target_fish=target_fish,
            services=services
        )

    # 4. 构建用户需求规格
    user_specs = {
        "budget": budget,
        "specifications": specs,
        "target_fish": target_fish,
        "scenario": scenario,
        "user_level": user_level or "新手"
    }

    # 5. 使用推荐算法
    results = recommender.recommend(normalized_type, user_specs, top_k=3)

    if not results:
        return f"未找到符合条件的{normalized_type}，建议放宽筛选条件"

    # 6. 格式化输出
    output = f"# 路亚{normalized_type}推荐报告\n\n"

    # 需求分析
    output += "## 需求分析\n\n"
    output += f"- **装备类型**: {normalized_type}\n"
    if budget:
        output += f"- **预算范围**: ¥{budget}\n"
    if specs:
        for k, v in specs.items():
            output += f"- **{k}要求**: {v}\n"
    if target_fish:
        output += f"- **目标鱼种**: {target_fish}\n"
    if scenario:
        output += f"- **使用场景**: {scenario}\n"
    if user_level:
        output += f"- **用户水平**: {user_level}\n"

    # 推荐产品（带评分）
    output += f"\n## 推荐产品（共{len(results)}款）\n\n"

    for i, rec in enumerate(results, 1):
        output += f"### {i}. {rec.name}\n\n"

        # 获取主图
        main_image = image_manager.get_main_image(rec.equipment_id)
        if main_image:
            output += f"![{rec.name}]({main_image})\n\n"

        # 综合评分
        output += f"**综合评分**: {rec.total_score:.1f}/100\n\n"

        output += "| 参数 | 值 |\n|------|-----|\n"
        if rec.brand:
            output += f"| 品牌 | {rec.brand} |\n"
        if rec.price:
            output += f"| 价格 | ¥{rec.price} |\n"

        # 规格参数
        for spec_name, spec_value in rec.specs.items():
            output += f"| {spec_name} | {spec_value} |\n"

        # 匹配理由
        if rec.match_reasons:
            output += f"\n**推荐理由**: {' · '.join(rec.match_reasons)}\n"

        # 评分明细
        output += "\n<details>\n<summary>评分明细</summary>\n\n"
        output += "| 维度 | 得分 | 权重 |\n|------|------|------|\n"
        weights = {"price_match": "35%", "spec_match": "35%", "brand_reputation": "15%", "user_level": "15%"}
        names = {"price_match": "价格匹配", "spec_match": "规格匹配", "brand_reputation": "品牌声誉", "user_level": "水平匹配"}
        for key, score in rec.score_breakdown.items():
            output += f"| {names.get(key, key)} | {score:.1f} | {weights.get(key, '-')} |\n"
        output += "\n</details>\n"

        output += "\n---\n\n"

    # 选购建议
    output += "## 选购建议\n\n"
    if user_level in ["新手", "初学者", "入门"]:
        output += "1. 新手建议选择大品牌，质量和售后有保障\n"
        output += "2. 不必追求顶级配置，先熟悉手感再升级\n"
    if budget and budget < 300:
        output += "3. 预算有限可考虑国产品牌，性价比更高\n"

    return output


def _recommend_package(
    budget: float,
    user_level: str,
    target_fish: Optional[str],
    services: Dict
) -> str:
    """推荐套装组合"""
    recommender = services['recommender']
    image_manager = services['image_manager']

    result = recommender.recommend_package(budget, user_level, target_fish)

    output = "# 路亚套装推荐报告\n\n"

    # 需求分析
    output += "## 需求分析\n\n"
    output += f"- **总预算**: ¥{budget}\n"
    output += f"- **用户水平**: {user_level}\n"
    if target_fish:
        output += f"- **目标鱼种**: {target_fish}\n"

    # 套装配置
    output += f"\n## 推荐套装（预估总价: ¥{result['total_price']:.0f}）\n\n"

    items = result.get('items', {})

    if 'rod' in items:
        rod = items['rod']
        output += f"### 鱼竿: {rod.name}\n\n"
        main_image = image_manager.get_main_image(rod.equipment_id)
        if main_image:
            output += f"![{rod.name}]({main_image})\n\n"
        output += f"- **品牌**: {rod.brand or '未知'}\n"
        output += f"- **价格**: ¥{rod.price or '未知'}\n"
        output += f"- **评分**: {rod.total_score:.1f}/100\n\n"

    if 'reel' in items:
        reel = items['reel']
        output += f"### 渔轮: {reel.name}\n\n"
        main_image = image_manager.get_main_image(reel.equipment_id)
        if main_image:
            output += f"![{reel.name}]({main_image})\n\n"
        output += f"- **品牌**: {reel.brand or '未知'}\n"
        output += f"- **价格**: ¥{reel.price or '未知'}\n"
        output += f"- **评分**: {reel.total_score:.1f}/100\n\n"

    if 'line' in items:
        line = items['line']
        output += f"### 鱼线: {line.name}\n\n"
        main_image = image_manager.get_main_image(line.equipment_id)
        if main_image:
            output += f"![{line.name}]({main_image})\n\n"
        output += f"- **品牌**: {line.brand or '未知'}\n"
        output += f"- **价格**: ¥{line.price or '未知'}\n"
        output += f"- **评分**: {line.total_score:.1f}/100\n\n"

    # 兼容性说明
    compatibility = result.get('compatibility', {})
    if compatibility.get('notes'):
        output += "## 兼容性说明\n\n"
        for note in compatibility['notes']:
            output += f"- {note}\n"

    # 预算节省
    if result.get('savings', 0) > 0:
        output += f"\n**节省预算**: ¥{result['savings']:.0f}\n"

    return output


# ========== 工具2：装备对比 ==========

@tool
def compare_equipment(
    equipment_names: str,
    compare_aspects: Optional[str] = None
) -> str:
    """
    对比多款装备的差异 - 用于选择决策

    当用户想要【比较】【对比】多款具体产品时使用。

    触发关键词: 对比、比较、哪个好、区别、差异、VS、和...比

    Args:
        equipment_names: 要对比的装备名称，用逗号分隔（2-5个）
            示例: "禧玛诺毒牙, 达亿瓦月下美人"
        compare_aspects: 对比维度，用逗号分隔（可选）
            可选值: 价格、性能、适用场景、品牌、性价比

    Returns:
        Markdown格式的对比报告

    Examples:
        >>> compare_equipment("禧玛诺毒牙264ML, 达亿瓦月下美人76ML")
        >>> compare_equipment("红蝎2500, 卢亚2500", "价格, 性能")
    """
    services = _get_services()
    comparator = services['comparator']
    from .lure import formatters

    # 1. 解析装备名称
    names = [n.strip() for n in equipment_names.split(",") if n.strip()]

    if len(names) < 2:
        return "请提供至少2个装备名称进行对比，用逗号分隔"
    if len(names) > 5:
        return "对比装备数量不能超过5个"

    # 2. 解析对比维度
    aspects = None
    if compare_aspects:
        aspects = [a.strip() for a in compare_aspects.split(",") if a.strip()]

    # 3. 执行对比
    try:
        result = comparator.compare(equipment_names=names, aspects=aspects)
    except ValueError as e:
        return str(e)

    # 4. 格式化输出
    return formatters.format_comparison(result)


# ========== 工具3：知识查询 ==========

@tool
def lookup_fishing_knowledge(
    topic: str,
    include_images: bool = True
) -> str:
    """
    查询钓鱼知识 - 用于学习和了解

    当用户想要【了解】【学习】某种鱼/钓组/技巧时使用。

    触发关键词: 什么是、怎么用、怎么绑、习性、教程、介绍、特点、方法

    支持查询类型:
    - 鱼类知识: "鲈鱼习性"、"翘嘴什么时候活跃"
    - 钓组知识: "德州钓组怎么绑"、"无铅钓组用法"
    - 技巧知识: "水草区怎么作钓"、"冬季路亚技巧"

    Args:
        topic: 查询主题（鱼种名/钓组名/技巧名）
        include_images: 是否包含图解（默认True）

    Returns:
        Markdown格式的知识内容

    Examples:
        >>> lookup_fishing_knowledge("鲈鱼")
        >>> lookup_fishing_knowledge("德州钓组怎么绑")
    """
    services = _get_services()
    db = services['db']
    fish_service = services['fish_service']
    search_service = services['search_service']
    from .lure import formatters

    # 1. 分类主题
    topic_type = _classify_topic(topic)

    # 2. 根据类型查询
    if topic_type == "fish":
        return _query_fish_knowledge(topic, include_images, services)
    elif topic_type == "rig":
        return _query_rig_knowledge(topic, include_images, services)
    else:
        # 语义搜索兜底
        return _semantic_search_knowledge(topic, include_images, services)


def _query_fish_knowledge(topic: str, include_images: bool, services: dict) -> str:
    """查询鱼类知识"""
    fish_service = services['fish_service']
    db = services['db']
    from .lure import formatters

    # 尝试直接匹配鱼名
    fish = fish_service.get_fish_by_name(topic)

    # 如果没找到，尝试提取鱼名
    if not fish:
        # 常见鱼名列表
        fish_names = ["鲈鱼", "大嘴鲈", "翘嘴", "鳜鱼", "黑鱼", "鲶鱼"]
        for name in fish_names:
            if name in topic:
                fish = fish_service.get_fish_by_name(name)
                if fish:
                    break

    if not fish:
        # 降级到语义搜索
        return _semantic_search_knowledge(topic, include_images, services)

    # 获取鱼类完整信息
    fish_data = fish_service.get_fish_with_images(fish.id)
    if not fish_data:
        return f"未找到关于'{topic}'的详细信息"

    # 获取相关知识
    knowledge = fish_service.get_knowledge_by_fish(fish.id)

    # 格式化输出
    return formatters.format_fish_knowledge(fish_data, knowledge, include_images)


def _query_rig_knowledge(topic: str, include_images: bool, services: dict) -> str:
    """查询钓组知识"""
    db = services['db']
    image_manager = services['image_manager']
    from .lure import formatters

    # 钓组名称映射
    rig_names = {
        "德州": "德州钓组", "德州钓组": "德州钓组",
        "无铅": "无铅钓组", "无铅钓组": "无铅钓组",
        "卡罗": "卡罗莱纳钓组", "卡罗莱纳": "卡罗莱纳钓组",
        "倒吊": "倒吊钓组", "倒吊钓组": "倒吊钓组",
        "铅头钩": "铅头钩钓组",
        "wacky": "Wacky钓组", "维基": "Wacky钓组",
    }

    # 尝试匹配钓组名
    rig_name = None
    for key, value in rig_names.items():
        if key in topic.lower():
            rig_name = value
            break

    if not rig_name:
        return _semantic_search_knowledge(topic, include_images, services)

    # 查询钓组信息
    query = "SELECT * FROM rig_types WHERE name_cn = ?"
    rows = db.execute(query, (rig_name,))

    if not rows:
        return f"未找到关于'{topic}'的详细信息"

    rig = rows[0]

    # 获取图片
    images = []
    if include_images:
        images = image_manager.get_rig_images(rig['id'])

    # 格式化输出
    return formatters.format_rig_guide(rig, images)


def _semantic_search_knowledge(topic: str, include_images: bool, services: dict) -> str:
    """语义搜索知识"""
    search_service = services['search_service']

    # 搜索鱼类知识
    fish_results = search_service.search_knowledge(topic, top_k=3)

    # 搜索钓组知识
    rig_results = search_service.search_rig(topic, top_k=3)

    if not fish_results and not rig_results:
        return f"未找到关于'{topic}'的相关知识，请尝试其他关键词"

    output = f"# 关于「{topic}」的搜索结果\n\n"

    if fish_results:
        output += "## 相关知识\n\n"
        for r in fish_results:
            output += f"### {r['title']}\n\n"
            if r.get('fish_name'):
                output += f"**相关鱼种**: {r['fish_name']}\n\n"
            content = r.get('content', '')[:500]
            output += f"{content}...\n\n"
            output += "---\n\n"

    if rig_results:
        output += "## 相关钓组\n\n"
        for r in rig_results:
            output += f"- **{r['name']}**: {r.get('description', '')[:100]}...\n"

    return output


# ========== 工具4：图片识别 ==========

@tool
def identify_from_image(
    image_path: str,
    question: Optional[str] = None
) -> str:
    """
    识别图片中的装备或鱼类 - 用于视觉识别

    当用户【上传图片】想要识别或询问时使用。

    触发关键词: 这是什么、识别、帮我看看、图片里、照片中

    支持识别:
    - 拟饵类型和品牌
    - 钓组配置
    - 鱼种识别
    - 装备型号

    Args:
        image_path: 图片路径（本地路径或URL）
        question: 用户的具体问题（可选），如"这是什么饵？"

    Returns:
        识别结果

    Examples:
        >>> identify_from_image("/tmp/unknown_lure.jpg", "这是什么饵？")
        >>> identify_from_image("https://example.com/fish.jpg", "这是什么鱼？")
    """
    services = _get_services()
    search_service = services['search_service']
    from .lure import formatters
    from pathlib import Path

    # 1. 验证图片路径
    if image_path.startswith("http"):
        return "暂不支持URL图片，请提供本地图片路径"

    if not Path(image_path).exists():
        return f"图片文件不存在: {image_path}"

    # 2. 执行图片搜索
    try:
        results = search_service.identify_image(image_path, top_k=3)
    except Exception as e:
        return f"图片识别失败: {str(e)}"

    if not results:
        return "未能识别图片内容，请确保图片清晰且包含路亚相关内容"

    # 3. 获取最佳匹配
    best_match = results[0]
    entity_type = best_match.entity_type
    entity = best_match.entity
    score = best_match.score

    # 4. 格式化输出
    return formatters.format_identification(
        entity_type=entity_type,
        entity=entity,
        score=score,
        similar_items=[r.entity for r in results[1:]] if len(results) > 1 else []
    )


# ========== 工具列表导出 ==========

LURE_TOOLS = [
    recommend_equipment,
    compare_equipment,
    lookup_fishing_knowledge,
    identify_from_image
]


def get_lure_tools() -> List:
    """获取所有路亚装备工具"""
    return LURE_TOOLS
