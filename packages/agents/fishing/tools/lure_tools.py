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
        specifications: 规格要求JSON字符串，如 '{"硬度": "ML", "长度": "2.1m", "适用饵范围": "2-10g", "重量": "<120g"}'
        target_fish: [保留字段] 目标鱼种，当前版本暂未使用
        scenario: [保留字段] 使用场景，当前版本暂未使用
        user_level: 用户水平（新手/进阶/高手）

    Returns:
        Markdown格式的推荐报告，突出最佳推荐并引导对比

    Examples:
        >>> recommend_equipment("鱼竿", budget=500, specifications='{"硬度": "ML"}')
        >>> recommend_equipment("套装", budget=1000, user_level="新手")
        >>> recommend_equipment("鱼竿", specifications='{"适用饵范围": "2-10g"}')
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

    # 6. 格式化输出（方案A：突出第一名 + 引导对比）
    output = f"# 路亚{normalized_type}推荐\n\n"

    # 第一名：最佳推荐（详细展示）
    best = results[0]
    output += f"## 最佳推荐：{best.name}\n\n"

    # 获取主图
    main_image = image_manager.get_main_image(best.equipment_id)
    if main_image:
        output += f"![{best.name}]({main_image})\n\n"

    # 关键信息一行展示
    info_parts = [f"评分: {best.total_score:.0f}/100"]
    if best.price:
        info_parts.append(f"价格: ¥{best.price:.0f}")
    # 添加关键规格（最多3个）
    key_specs = list(best.specs.items())[:3]
    for spec_name, spec_value in key_specs:
        info_parts.append(f"{spec_name}: {spec_value}")
    output += " | ".join(info_parts) + "\n\n"

    # 为什么推荐（基于得分生成个性化文案）
    why_reasons = _generate_why_recommend(best, user_specs)
    output += f"**为什么推荐**：{why_reasons}\n\n"

    # 其他候选（简洁展示）
    if len(results) > 1:
        output += "---\n\n"
        output += "**其他候选**：\n"
        for rec in results[1:]:
            price_str = f"¥{rec.price:.0f}" if rec.price else "价格未知"
            output += f"- {rec.name} ({rec.total_score:.0f}分, {price_str})\n"
        output += "\n"

        # 引导对比
        equipment_names = ", ".join([r.name for r in results])
        output += f"> 想详细对比？请说「对比 {equipment_names}」\n"

    return output


def _generate_why_recommend(rec, user_specs: Dict) -> str:
    """基于得分生成个性化推荐理由"""
    reasons = []
    scores = rec.score_breakdown

    # 找出得分最高的维度
    score_names = {
        "price_match": "价格匹配",
        "spec_match": "规格匹配",
        "brand_reputation": "品牌声誉",
        "user_level": "水平匹配"
    }

    # 按得分排序
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    for key, score in sorted_scores:
        if score >= 90:
            if key == "price_match":
                reasons.append("价格完美匹配预算")
            elif key == "spec_match":
                reasons.append("规格完全符合需求")
            elif key == "brand_reputation":
                reasons.append("一线品牌质量有保障")
            elif key == "user_level":
                reasons.append("非常适合当前水平")
        elif score >= 75:
            if key == "price_match":
                reasons.append("性价比高")
            elif key == "spec_match":
                reasons.append("规格基本符合")
            elif key == "brand_reputation":
                reasons.append("知名品牌")
            elif key == "user_level":
                reasons.append("适合当前水平")

        # 最多3个理由
        if len(reasons) >= 3:
            break

    # 如果没有高分理由，使用通用理由
    if not reasons:
        reasons = ["综合评分最高"]

    return " + ".join(reasons)


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


# ========== 工具4：装备查询 ==========

@tool
def query_equipment(
    query_text: str,
    category: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    查询装备信息 - 用于了解特定品牌/型号/系列的装备

    当用户想要【查询】【了解】某个品牌、型号或系列的装备时使用。
    支持灵活的查询方式,会自动匹配品牌名、型号、产品名等字段。

    触发关键词: 有哪些、什么型号、型号、品牌、系列、产品、查一下

    Args:
        query_text: 查询关键词（品牌名/型号/系列名/产品名）
            示例: "多普"、"KINHONG"、"月下美人"、"C661"
        category: 装备类别过滤（可选）
            可选值: 路亚竿、纺车轮、水滴轮、鱼线、拟饵
        max_results: 最多返回结果数（默认10）

    Returns:
        Markdown格式的装备列表

    Examples:
        >>> query_equipment("多普")  # 查询所有多普品牌装备
        >>> query_equipment("多普", category="路亚竿")  # 查询多普的鱼竿
        >>> query_equipment("KINHONG")  # 查询KINHONG系列
        >>> query_equipment("C661")  # 查询型号包含C661的装备
    """
    services = _get_services()
    db = services['db']
    image_manager = services['image_manager']

    # 1. 构建灵活的查询SQL（匹配多个字段）
    query = """
        SELECT e.equipment_id, e.name, e.model, e.category,
               e.description, e.features, e.price_min, e.price_max,
               b.name_cn as brand_name, b.name_en as brand_name_en
        FROM equipment e
        LEFT JOIN brands b ON e.brand_id = b.id
        WHERE e.is_active = 1
        AND (
            b.name_cn LIKE ? OR
            b.name_en LIKE ? OR
            e.name LIKE ? OR
            e.model LIKE ?
        )
    """
    search_pattern = f"%{query_text}%"
    params = [search_pattern, search_pattern, search_pattern, search_pattern]

    # 2. 添加类别过滤
    if category:
        query += " AND e.category = ?"
        params.append(category)

    query += f" ORDER BY e.created_at DESC LIMIT ?"
    params.append(max_results)

    # 3. 执行查询
    rows = db.execute(query, tuple(params))

    if not rows:
        filter_text = f"关键词「{query_text}」"
        if category:
            filter_text += f" + 类别「{category}」"
        return f"未找到符合{filter_text}的装备。请尝试：\n- 检查关键词拼写\n- 使用品牌中文名（如「多普」而非「DOOP」）\n- 去掉类别过滤看看是否有其他类别的产品"

    # 4. 格式化输出
    output = "# 装备查询结果\n\n"

    # 查询条件摘要
    output += "## 查询条件\n\n"
    output += f"- **关键词**: {query_text}\n"
    if category:
        output += f"- **类别**: {category}\n"
    output += f"- **找到**: {len(rows)} 款装备\n\n"

    # 按类别分组展示（更清晰）
    from collections import defaultdict
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['category']].append(row)

    for cat, items in grouped.items():
        output += f"## {cat} ({len(items)}款)\n\n"

        for i, row in enumerate(items, 1):
            # 紧凑的标题格式
            brand = row.get('brand_name', '未知品牌')
            model = row.get('model', '')
            title = f"{brand} {model}" if model else brand

            output += f"### {i}. {title}\n\n"

            # 获取主图
            main_image = image_manager.get_main_image(row['equipment_id'])
            if main_image:
                output += f"![{row['name']}]({main_image})\n\n"

            # 信息表格
            output += "| 参数 | 值 |\n|------|-----|\n"
            output += f"| 完整名称 | {row['name']} |\n"

            # 价格信息
            if row.get('price_min'):
                if row.get('price_max') and row['price_max'] != row['price_min']:
                    output += f"| 价格 | ¥{row['price_min']:.0f} - ¥{row['price_max']:.0f} |\n"
                else:
                    output += f"| 价格 | ¥{row['price_min']:.0f} |\n"

            output += "\n"

            # 简要描述（精简版）
            if row.get('features'):
                features_text = row['features'][:150]
                output += f"**特性**: {features_text}...\n\n"
            elif row.get('description'):
                desc_text = row['description'][:150]
                output += f"**描述**: {desc_text}...\n\n"

            output += "---\n\n"

    # 提示语
    if len(rows) == max_results:
        output += f"\n💡 **提示**: 结果已达到最大显示数量({max_results}款)，可能还有更多产品未显示。\n"

    return output


# ========== 工具5：图片识别 ==========

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
    query_equipment,
    identify_from_image
]


def get_lure_tools() -> List:
    """获取所有路亚装备工具"""
    return LURE_TOOLS
