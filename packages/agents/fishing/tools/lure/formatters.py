"""
输出格式化模块（优化版）

提供Markdown格式的报告生成功能：
- 推荐报告
- 对比报告（增强版：综合评分、关键差异、对比总结）
- 知识内容
- 识别结果
"""

from typing import List, Dict, Any, Optional
from .fish_knowledge import FishInfo, KnowledgeItem
from .comparator import ComparisonResult, ComparisonItem
from .diff_analyzer import SpecDifference


def format_recommendation(
    results: List[Dict[str, Any]],
    user_specs: Dict[str, Any]
) -> str:
    """
    格式化推荐报告

    Args:
        results: 推荐结果列表，每项包含装备信息和匹配度
        user_specs: 用户需求规格

    Returns:
        Markdown格式的推荐报告
    """
    output = "# 路亚装备推荐报告\n\n"

    # 需求分析
    output += "## 需求分析\n\n"
    if user_specs.get('equipment_type'):
        output += f"- **装备类型**: {user_specs['equipment_type']}\n"
    if user_specs.get('budget'):
        output += f"- **预算范围**: ¥{user_specs['budget']}\n"
    if user_specs.get('specifications'):
        specs = user_specs['specifications']
        if specs.get('硬度'):
            output += f"- **硬度要求**: {specs['硬度']}\n"
        if specs.get('调性'):
            output += f"- **调性要求**: {specs['调性']}\n"
    if user_specs.get('target_fish'):
        output += f"- **目标鱼种**: {user_specs['target_fish']}\n"
    if user_specs.get('user_level'):
        output += f"- **用户水平**: {user_specs['user_level']}\n"
    output += "\n"

    # 推荐产品
    output += f"## 推荐产品（Top {len(results)}）\n\n"

    for i, item in enumerate(results, 1):
        score = item.get('score', 0)
        name = item.get('name', '未知产品')

        output += f"### {i}. {name}（匹配度：{score:.0f}%）\n\n"

        # 图片
        if item.get('main_image'):
            output += f"![{name}]({item['main_image']})\n\n"

        # 参数表格
        output += "| 参数 | 值 |\n"
        output += "|------|-----|\n"

        if item.get('price'):
            output += f"| 价格 | ¥{item['price']:.0f} |\n"
        if item.get('brand'):
            output += f"| 品牌 | {item['brand']} |\n"

        # 规格参数
        specs = item.get('specs', {})
        for key, value in specs.items():
            if value:
                output += f"| {key} | {value} |\n"

        output += "\n"

        # 推荐理由
        if item.get('reasons'):
            output += "**推荐理由**:\n"
            for reason in item['reasons']:
                output += f"- {reason}\n"
            output += "\n"

        # 购买建议
        if item.get('tips'):
            output += f"**购买建议**: {item['tips']}\n\n"

        output += "---\n\n"

    # 选购建议
    output += "## 选购建议\n\n"
    output += _generate_buying_tips(user_specs)

    return output


def format_comparison(comparison: ComparisonResult) -> str:
    """
    格式化对比报告（增强版）

    Args:
        comparison: ComparisonResult对象

    Returns:
        Markdown格式的对比报告
    """
    output = "# 装备对比报告\n\n"

    items = comparison.items
    if len(items) < 2:
        return output + "对比数据不足\n"

    # 1. 对比总结（新增）
    if comparison.summary:
        output += "## 快速结论\n\n"
        output += f"> {comparison.summary}\n\n"

    # 2. 关键差异分析（核心新增）
    if comparison.key_differences:
        output += "## 关键差异\n\n"
        output += "> 以下是对比中差异最显著的参数，帮助您快速做出决策\n\n"

        for diff in comparison.key_differences:
            # 差异程度标记
            magnitude_icon = {
                "large": "显著差异",
                "medium": "明显差异",
                "small": "轻微差异"
            }.get(diff.diff_magnitude, "")

            output += f"### {diff.spec_name} ({magnitude_icon})\n\n"
            output += f"{diff.analysis}\n\n"

            # 展示各装备的值
            output += "| 装备 | 数值 |\n"
            output += "|------|------|\n"
            for name, val in diff.values.items():
                # 标记最优/最差
                marker = ""
                if diff.best_item and name == diff.best_item:
                    marker = " (最优)"
                elif diff.worst_item and name == diff.worst_item:
                    marker = " (较弱)"
                output += f"| {name} | {val}{marker} |\n"

            output += "\n"

        output += "---\n\n"

    # 3. 综合评分表格（新增）
    output += "## 综合评分\n\n"
    output += "| 装备 | 综合评分 | 价格 | 品牌 |\n"
    output += "|------|---------|------|------|\n"

    # 按评分排序展示
    sorted_items = sorted(items, key=lambda x: x.overall_score, reverse=True)
    for i, item in enumerate(sorted_items):
        rank = "第1名" if i == 0 else (f"第{i+1}名")
        price_str = f"¥{item.price:.0f}" if item.price else "-"
        output += f"| {rank} {item.name} | **{item.overall_score:.1f}**/100 | {price_str} | {item.brand or '-'} |\n"

    output += "\n"

    # 4. 详细参数对比表格
    output += "## 详细参数对比\n\n"

    headers = ["参数"] + [item.name for item in items]
    output += "| " + " | ".join(headers) + " |\n"
    output += "|" + "|".join(["------"] * len(headers)) + "|\n"

    # 价格行
    prices = ["价格"] + [f"¥{item.price:.0f}" if item.price else "-" for item in items]
    output += "| " + " | ".join(prices) + " |\n"

    # 品牌行
    brands = ["品牌"] + [item.brand or "-" for item in items]
    output += "| " + " | ".join(brands) + " |\n"

    # 收集所有规格键
    all_spec_keys = set()
    for item in items:
        all_spec_keys.update(item.specs.keys())

    # 按重要性排序的规格键
    priority_keys = ["自重", "长度", "硬度", "调性", "速比", "刹车力", "适用饵范围"]
    sorted_keys = [k for k in priority_keys if k in all_spec_keys]
    sorted_keys += [k for k in sorted(all_spec_keys) if k not in priority_keys]

    for key in sorted_keys:
        row = [key] + [str(item.specs.get(key, "-")) for item in items]
        output += "| " + " | ".join(row) + " |\n"

    output += "\n"

    # 5. 优劣势分析
    output += "## 优劣势分析\n\n"

    for item in items:
        output += f"### {item.name}\n\n"

        if item.main_image:
            output += f"![{item.name}]({item.main_image})\n\n"

        if item.strengths:
            output += "**优势**：\n"
            for strength in item.strengths:
                output += f"- {strength}\n"
            output += "\n"

        if item.weaknesses:
            output += "**不足**：\n"
            for weakness in item.weaknesses:
                output += f"- {weakness}\n"
            output += "\n"

        output += "---\n\n"

    # 6. 选购建议
    if comparison.recommendations:
        output += "## 选购建议\n\n"
        output += "| 使用场景 | 推荐选择 |\n"
        output += "|---------|--------|\n"

        # 优先展示综合最优
        priority_scenarios = ["综合最优", "预算有限", "长时间作钓"]
        for scenario in priority_scenarios:
            if scenario in comparison.recommendations:
                product = comparison.recommendations[scenario]
                output += f"| **{scenario}** | {product} |\n"

        # 其他建议
        for scenario, product in comparison.recommendations.items():
            if scenario not in priority_scenarios:
                output += f"| {scenario} | {product} |\n"

        output += "\n"

    # 7. 对比总结表格（核心新增：相同项 vs 差异项）
    output += format_comparison_summary_table(comparison)

    return output


def format_comparison_summary_table(comparison: ComparisonResult) -> str:
    """
    生成对比总结表格

    清晰区分：相同项 vs 差异项
    """
    output = "## 对比总结\n\n"

    items = comparison.items
    if len(items) < 2:
        return output

    # 收集所有规格
    all_specs = {}
    for item in items:
        for key, value in item.specs.items():
            if key not in all_specs:
                all_specs[key] = {}
            all_specs[key][item.name] = value

    # 添加价格
    all_specs["价格"] = {item.name: f"¥{item.price:.0f}" if item.price else "-" for item in items}

    # 添加品牌
    all_specs["品牌"] = {item.name: item.brand or "-" for item in items}

    # 分类：相同项 vs 差异项
    same_specs = []
    diff_specs = []

    for spec_name, values in all_specs.items():
        unique_values = set(str(v) for v in values.values() if v and v != "-")
        if len(unique_values) <= 1:
            same_specs.append((spec_name, values))
        else:
            diff_specs.append((spec_name, values))

    # 获取差异分析信息
    diff_info = {d.spec_name: d for d in comparison.spec_differences} if comparison.spec_differences else {}

    # 表头
    headers = ["参数"] + [item.name for item in items] + ["差异说明"]
    output += "| " + " | ".join(headers) + " |\n"
    output += "|" + "|".join(["------"] * len(headers)) + "|\n"

    # 差异项（优先展示，带高亮）
    if diff_specs:
        output += "| **== 差异项 ==** |" + " |".join([""] * (len(items) + 1)) + "\n"

        # 按差异程度排序
        def get_diff_priority(spec_tuple):
            spec_name = spec_tuple[0]
            if spec_name in diff_info:
                magnitude = diff_info[spec_name].diff_magnitude
                return {"large": 0, "medium": 1, "small": 2}.get(magnitude, 3)
            return 3

        diff_specs.sort(key=get_diff_priority)

        for spec_name, values in diff_specs:
            # 获取差异信息
            diff = diff_info.get(spec_name)

            # 差异程度标记
            if diff:
                magnitude_mark = {
                    "large": "[显著]",
                    "medium": "[明显]",
                    "small": "[轻微]"
                }.get(diff.diff_magnitude, "")
            else:
                magnitude_mark = ""

            # 构建每个值的展示（标记最优/最差）
            value_cells = []
            for item in items:
                val = str(values.get(item.name, "-"))
                if diff:
                    if diff.best_item == item.name:
                        val = f"**{val}** (优)"
                    elif diff.worst_item == item.name:
                        val = f"{val} (弱)"
                value_cells.append(val)

            # 差异说明
            if diff and diff.diff_percent > 0:
                diff_note = f"{magnitude_mark} 差异{diff.diff_percent:.0f}%"
            elif diff:
                diff_note = f"{magnitude_mark} {diff.analysis[:15]}..."
            else:
                diff_note = "不同"

            row = [f"**{spec_name}**"] + value_cells + [diff_note]
            output += "| " + " | ".join(row) + " |\n"

    # 相同项
    if same_specs:
        output += "| **== 相同项 ==** |" + " |".join([""] * (len(items) + 1)) + "\n"

        for spec_name, values in same_specs:
            # 获取共同值
            common_value = next((str(v) for v in values.values() if v and v != "-"), "-")
            value_cells = [common_value] * len(items)

            row = [spec_name] + value_cells + ["相同"]
            output += "| " + " | ".join(row) + " |\n"

    output += "\n"

    # 添加图例
    output += "> **说明**: [显著]差异>30% | [明显]差异10-30% | [轻微]差异<10% | (优)该项最优 | (弱)该项较弱\n\n"

    return output


def format_fish_knowledge(
    fish_info: Dict[str, Any],
    knowledge: List[KnowledgeItem],
    include_images: bool = True
) -> str:
    """
    格式化鱼类知识

    Args:
        fish_info: 包含fish和images的字典
        knowledge: 相关知识列表
        include_images: 是否包含图片

    Returns:
        Markdown格式的知识内容
    """
    fish: FishInfo = fish_info['fish']
    images = fish_info.get('images', [])
    main_image = fish_info.get('main_image')

    output = f"# {fish.name_cn}"
    if fish.name_en:
        output += f" ({fish.name_en})"
    output += "\n\n"

    # 主图
    if include_images and main_image:
        output += f"![{fish.name_cn}]({main_image.image_url})\n\n"

    # 基础信息表格
    output += "## 基础信息\n\n"
    output += "| 属性 | 值 |\n"
    output += "|------|-----|\n"
    output += f"| 分类 | {fish.category} |\n"
    output += f"| 栖息水层 | {fish.habitat} |\n"

    if fish.active_temp_min and fish.active_temp_max:
        output += f"| 活跃温度 | {fish.active_temp_min}-{fish.active_temp_max}℃ |\n"
    if fish.feeding_habits:
        output += f"| 食性 | {fish.feeding_habits} |\n"
    output += f"| 路亚难度 | {fish.lure_difficulty} |\n"
    if fish.fight_intensity:
        output += f"| 搏鱼强度 | {fish.fight_intensity} |\n"

    output += "\n"

    # 路亚建议
    output += "## 路亚建议\n\n"

    if fish.recommended_lures:
        output += "### 推荐拟饵\n"
        for lure in fish.recommended_lures:
            output += f"- {lure}\n"
        output += "\n"

    if fish.recommended_rigs:
        output += "### 推荐钓组\n"
        for rig in fish.recommended_rigs:
            output += f"- {rig}\n"
        output += "\n"

    # 详细知识
    if knowledge:
        # 按类型分组
        knowledge_by_type: Dict[str, List[KnowledgeItem]] = {}
        for k in knowledge:
            if k.knowledge_type not in knowledge_by_type:
                knowledge_by_type[k.knowledge_type] = []
            knowledge_by_type[k.knowledge_type].append(k)

        type_titles = {
            "behavior": "生态习性",
            "habitat": "栖息环境",
            "season": "季节特点",
            "technique": "钓法技巧",
            "lure_match": "拟饵匹配",
            "rig_match": "钓组匹配",
        }

        for ktype, items in knowledge_by_type.items():
            title = type_titles.get(ktype, ktype)
            output += f"## {title}\n\n"

            for item in items:
                if item.title != title:  # 避免重复标题
                    output += f"### {item.title}\n\n"
                output += item.content + "\n\n"

    return output


def format_rig_guide(
    rig_info: Dict[str, Any],
    images: List[Any] = None
) -> str:
    """
    格式化钓组指南

    Args:
        rig_info: 钓组信息字典
        images: 图片列表

    Returns:
        Markdown格式的钓组指南
    """
    name = rig_info.get('name_cn', '钓组')
    name_en = rig_info.get('name_en', '')

    output = f"# {name}"
    if name_en:
        output += f" ({name_en})"
    output += "\n\n"

    # 简介
    if rig_info.get('description'):
        output += "## 简介\n\n"
        output += rig_info['description'] + "\n\n"

    # 组装图解
    if images:
        infographics = [img for img in images if img.image_type == 'infographic']
        if infographics:
            output += "## 组装图解\n\n"
            for img in infographics:
                desc = img.description or "组装图解"
                output += f"![{desc}]({img.image_url})\n\n"

    # 所需配件
    if rig_info.get('components'):
        output += "## 所需配件\n\n"
        output += "| 配件 | 规格建议 | 作用 |\n"
        output += "|------|---------|------|\n"

        import json
        components = rig_info['components']
        if isinstance(components, str):
            try:
                components = json.loads(components)
            except json.JSONDecodeError:
                components = []

        for comp in components:
            if isinstance(comp, dict):
                output += f"| {comp.get('name', '')} | {comp.get('spec', '')} | {comp.get('role', '')} |\n"

        output += "\n"

    # 组装步骤
    if rig_info.get('assembly_steps'):
        output += "## 组装步骤\n\n"

        steps = rig_info['assembly_steps']
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except json.JSONDecodeError:
                steps = [steps]

        for i, step in enumerate(steps, 1):
            if isinstance(step, dict):
                output += f"### 第{i}步：{step.get('title', '')}\n\n"
                output += step.get('content', '') + "\n\n"
            else:
                output += f"**第{i}步**: {step}\n\n"

    # 操作技巧
    if rig_info.get('operation_tips'):
        output += "## 操作技巧\n\n"
        output += rig_info['operation_tips'] + "\n\n"

    # 适用场景
    if rig_info.get('suitable_scenarios'):
        output += "## 适用场景\n\n"

        scenarios = rig_info['suitable_scenarios']
        if isinstance(scenarios, str):
            try:
                scenarios = json.loads(scenarios)
            except json.JSONDecodeError:
                scenarios = [scenarios]

        output += "| 场景 | 适合度 | 说明 |\n"
        output += "|------|--------|------|\n"

        for scenario in scenarios:
            if isinstance(scenario, dict):
                rating = "⭐" * scenario.get('rating', 3)
                output += f"| {scenario.get('name', '')} | {rating} | {scenario.get('note', '')} |\n"

        output += "\n"

    return output


def format_identification(
    entity_type: str,
    entity: Dict[str, Any],
    score: float,
    usage_tips: Optional[str] = None,
    similar_products: Optional[List[Dict]] = None
) -> str:
    """
    格式化识别结果

    Args:
        entity_type: 实体类型 (equipment/rig/fish)
        entity: 实体信息
        score: 识别置信度
        usage_tips: 使用建议
        similar_products: 相似产品列表

    Returns:
        Markdown格式的识别结果
    """
    output = "# 识别结果\n\n"
    output += f"**置信度**: {score*100:.0f}%\n\n"

    name = entity.get('name') or entity.get('name_cn', '未知')
    output += f"## 这是: {name}\n\n"

    # 图片
    if entity.get('main_image'):
        output += f"![{name}]({entity['main_image']})\n\n"

    # 基本信息
    if entity_type == "equipment":
        output += f"**类型**: {entity.get('category', '未知')}\n"
        if entity.get('brand'):
            output += f"**品牌**: {entity['brand']}\n"
        if entity.get('price'):
            output += f"**参考价格**: ¥{entity['price']}\n"

    elif entity_type == "fish":
        output += f"**分类**: {entity.get('category', '未知')}\n"
        output += f"**栖息水层**: {entity.get('habitat', '未知')}\n"

    elif entity_type == "rig":
        output += f"**难度**: {entity.get('difficulty', '未知')}\n"

    output += "\n"

    # 使用建议
    if usage_tips:
        output += "## 使用建议\n\n"
        output += usage_tips + "\n\n"

    # 相似产品
    if similar_products:
        output += "## 相关产品\n\n"
        for product in similar_products:
            price_str = f" - ¥{product['price']}" if product.get('price') else ""
            output += f"- {product.get('name', '未知')}{price_str}\n"
        output += "\n"

    return output


def format_package_recommendation(
    package: Dict[str, Any],
    user_specs: Dict[str, Any]
) -> str:
    """
    格式化套装推荐

    Args:
        package: 套装配置
        user_specs: 用户需求

    Returns:
        Markdown格式的套装推荐报告
    """
    output = "# 路亚套装推荐\n\n"

    # 需求分析
    output += "## 需求分析\n\n"
    if user_specs.get('budget'):
        output += f"- **总预算**: ¥{user_specs['budget']}\n"
    if user_specs.get('user_level'):
        output += f"- **用户水平**: {user_specs['user_level']}\n"
    if user_specs.get('target_fish'):
        output += f"- **目标鱼种**: {user_specs['target_fish']}\n"
    output += "\n"

    # 套装配置
    output += "## 推荐配置\n\n"

    total_price = 0
    components = ['rod', 'reel', 'line', 'lure']
    component_names = {'rod': '鱼竿', 'reel': '渔轮', 'line': '鱼线', 'lure': '拟饵'}

    for comp in components:
        item = package.get(comp)
        if item:
            output += f"### {component_names.get(comp, comp)}\n\n"

            if item.get('main_image'):
                output += f"![{item.get('name')}]({item['main_image']})\n\n"

            output += f"**{item.get('name', '未知')}**\n\n"

            if item.get('price'):
                output += f"- 价格: ¥{item['price']}\n"
                total_price += item['price']

            if item.get('specs'):
                for key, value in item['specs'].items():
                    output += f"- {key}: {value}\n"

            if item.get('reason'):
                output += f"\n*推荐理由: {item['reason']}*\n"

            output += "\n"

    # 总价
    output += "## 价格汇总\n\n"
    output += f"**套装总价**: ¥{total_price}\n"

    if user_specs.get('budget'):
        remaining = user_specs['budget'] - total_price
        if remaining >= 0:
            output += f"\n*预算剩余: ¥{remaining}*\n"
        else:
            output += f"\n*超出预算: ¥{-remaining}*\n"

    return output


def _generate_buying_tips(user_specs: Dict[str, Any]) -> str:
    """生成选购建议"""
    tips = []

    user_level = user_specs.get('user_level', '')
    if '新手' in user_level or '入门' in user_level:
        tips.append("新手建议选择知名品牌，售后有保障")
        tips.append("不必追求顶级装备，中端性价比更高")

    budget = user_specs.get('budget')
    if budget:
        if budget <= 300:
            tips.append("预算有限时，优先保证鱼竿质量，渔轮可适当降档")
        elif budget >= 1000:
            tips.append("预算充足可考虑日系品牌，手感和做工更精细")

    target_fish = user_specs.get('target_fish', '')
    if '鲈鱼' in target_fish:
        tips.append("钓鲈鱼建议配备德州钓组和无铅钓组")
    elif '翘嘴' in target_fish:
        tips.append("钓翘嘴以米诺和VIB为主，注重远投性能")

    if not tips:
        tips.append("建议根据实际作钓场景选择合适的装备")
        tips.append("多看评测视频，了解实际使用体验")

    return "\n".join(f"{i}. {tip}" for i, tip in enumerate(tips, 1))
