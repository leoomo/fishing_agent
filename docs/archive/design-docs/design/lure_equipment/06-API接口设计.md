# 06 - API接口设计

> **文档版本**: v2.0
> **最后更新**: 2025-11-21
> **状态**: 已确定

## 🔧 LangChain工具接口

### query_lure_equipment (主工具)

```python
from langchain.tools import tool
from typing import Optional, Dict, Any

@tool
def query_lure_equipment(
    equipment_type: str,
    specifications: Optional[Dict[str, Any]] = None,
    query_mode: str = "recommend"
) -> str:
    """
    路亚装备智能推荐（支持7大类装备）

    本工具提供专业的路亚装备推荐服务，基于用户需求（预算、规格、品牌等）
    推荐最合适的装备，或进行装备对比、套装配置等。

    适用场景：
    - 用户询问"推荐路亚竿"、"什么渔轮好"
    - 用户提到预算、品牌、规格（硬度、长度等）
    - 用户想要装备对比或套装推荐

    不适用场景：
    - 询问钓鱼时间/天气（使用fishing_tools）
    - 询问钓点位置（使用location_tools）
    - 询问钓鱼技巧（使用knowledge_tools）

    Args:
        equipment_type (str): 装备类型，必填
            支持以下类型：
            - "鱼竿" | "路亚竿" | "竿"
            - "渔轮" | "卷线器" | "轮"
            - "鱼线" | "钓线" | "线"
            - "鱼饵" | "拟饵" | "假饵"
            - "鱼钩" | "钩"
            - "配件" | "辅助配件"
            - "工具" | "辅助工具"

        specifications (Optional[Dict[str, Any]]): 规格要求，可选
            支持的字段：
            - "预算": float - 预算金额（如：300）
            - "品牌": str - 品牌名称（如："禧玛诺"、"达瓦"）
            - "硬度": str - 鱼竿硬度（如："ML"、"M"、"MH"）
            - "长度": float - 鱼竿长度（如：2.4）
            - "用户水平": str - 用户水平（"新手"、"进阶"、"专业"）
            - "型号": str - 具体型号（如："毒牙"、"月光"）

            示例：
            {
                "预算": 300,
                "硬度": "ML",
                "用户水平": "新手"
            }

        query_mode (str): 查询模式，默认"recommend"
            - "recommend": 推荐模式（返回Top 3推荐）
            - "compare": 对比模式（需提供2个具体型号）
            - "package": 套装模式（返回竿+轮+线配置）

    Returns:
        str: Markdown格式的推荐报告

        推荐模式返回示例：
        ```markdown
        # 路亚装备推荐报告

        ## 📊 需求分析
        - 装备类型：鱼竿
        - 预算范围：¥300
        - 硬度要求：ML（中轻硬）
        - 用户水平：新手

        ## 🎣 推荐产品（Top 3）

        ### 1. 光威赤刃264ML（匹配度：92%）
        - **价格**：¥180
        - **规格**：长度2.64m | 硬度ML | 调性F（快调）
        - **推荐理由**：价格在预算内，适合新手操控，性价比优秀
        - **购买建议**：适合钓1-3斤鲈鱼，搭配2500型纺车轮

        ### 2. 禧玛诺毒牙264ML（匹配度：88%）
        - **价格**：¥680（超预算）
        - **规格**：长度2.64m | 硬度ML | 调性F
        - **推荐理由**：一线品牌，质量可靠，适合长期使用
        - **购买建议**：建议增加预算，性能明显优于入门款

        ### 3. 迪卡侬WIXOM-5 270M（匹配度：85%）
        - **价格**：¥199
        - **规格**：长度2.70m | 硬度M | 调性M（中调）
        - **推荐理由**：国际品牌，售后有保障
        - **购买建议**：硬度略高于ML，适合钓大一点的鱼

        ## 💡 选购建议
        - 新手优先考虑ML调性（万能调性）
        - 预算有限选光威赤刃，性价比最高
        - 预算允许选禧玛诺毒牙，一步到位
        - 避坑指南：不要盲目追求碳素吨位，新手感觉不出区别
        ```

    Examples:
        # 示例1：单装备推荐
        >>> query_lure_equipment(
        ...     equipment_type="鱼竿",
        ...     specifications={"预算": 300, "硬度": "ML", "用户水平": "新手"}
        ... )
        "# 路亚装备推荐报告\n..."

        # 示例2：品牌对比
        >>> query_lure_equipment(
        ...     equipment_type="鱼竿",
        ...     specifications={"型号": ["毒牙", "月光"]},
        ...     query_mode="compare"
        ... )
        "# 装备对比报告\n..."

        # 示例3：套装推荐
        >>> query_lure_equipment(
        ...     equipment_type="套装",
        ...     specifications={"预算": 1000, "用户水平": "新手"},
        ...     query_mode="package"
        ... )
        "# 新手入门套装推荐\n..."

    Raises:
        ValueError: 如果equipment_type不在支持的类型中
        TypeError: 如果specifications不是字典类型

    Notes:
        - 推荐结果基于当前数据库中的装备数据
        - 如果没有匹配的装备，会提供替代建议
        - 价格数据可能存在延迟，建议购买前核实
    """
    try:
        # 参数验证
        equipment_type = _normalize_equipment_type(equipment_type)
        specifications = specifications or {}

        # 调用业务逻辑
        from .lure.data_fetcher import LureDataFetcher
        from .lure.recommender import LureRecommender
        from .lure.formatters import format_recommendation, format_comparison, format_package

        # 获取数据
        fetcher = LureDataFetcher()
        equipments = fetcher.fetch_equipment(equipment_type, specifications)

        if not equipments:
            return _no_match_message(equipment_type, specifications)

        # 推荐计算
        recommender = LureRecommender()

        if query_mode == "recommend":
            results = recommender.recommend(equipments, specifications, top_k=3)
            return format_recommendation(results, specifications)

        elif query_mode == "compare":
            if len(equipments) < 2:
                return "对比功能需要至少2款装备，请提供更多型号信息。"
            return format_comparison(equipments[:2])

        elif query_mode == "package":
            package = recommender.recommend_package(
                budget=specifications.get('预算', 1000),
                user_level=specifications.get('用户水平', '新手')
            )
            return format_package(package)

        else:
            return f"不支持的查询模式: {query_mode}"

    except ValueError as e:
        return f"参数错误: {str(e)}\n\n请检查装备类型是否正确，支持的类型：鱼竿、渔轮、鱼线、鱼饵、鱼钩、配件、工具"

    except Exception as e:
        logger.error(f"查询装备失败: {e}")
        return f"查询装备时发生错误，请稍后重试。\n\n如果问题持续，请尝试简化查询条件或联系支持。"


def _normalize_equipment_type(equipment_type: str) -> str:
    """标准化装备类型"""
    type_mapping = {
        '竿': '鱼竿', '路亚竿': '鱼竿', '钓竿': '鱼竿',
        '轮': '渔轮', '卷线器': '渔轮', '线轮': '渔轮',
        '线': '鱼线', '钓线': '鱼线',
        '饵': '鱼饵', '拟饵': '鱼饵', '假饵': '鱼饵',
        '钩': '鱼钩', '钩子': '鱼钩',
    }

    normalized = type_mapping.get(equipment_type, equipment_type)

    valid_types = ['鱼竿', '渔轮', '鱼线', '鱼饵', '鱼钩', '配件', '工具', '套装']
    if normalized not in valid_types:
        raise ValueError(f"不支持的装备类型: {equipment_type}")

    return normalized


def _no_match_message(equipment_type: str, specifications: Dict) -> str:
    """无匹配结果时的友好提示"""
    return f"""
# 暂无匹配的{equipment_type}

根据您的查询条件：
{_format_specs(specifications)}

抱歉，当前数据库中没有完全匹配的装备。

## 💡 建议

1. **放宽条件**：
   - 如果设置了预算，可以适当提高预算范围
   - 如果指定了品牌，可以尝试其他品牌

2. **查看相似推荐**：
   - 修改硬度要求（如ML可以考虑M或L）
   - 调整长度范围（±0.3米）

3. **联系我们**：
   - 如果您有特殊需求，可以提供更详细的信息
   - 我们会根据需求补充数据库
"""


def _format_specs(specifications: Dict) -> str:
    """格式化规格要求"""
    if not specifications:
        return "- 无特定要求"

    lines = []
    for key, value in specifications.items():
        lines.append(f"- {key}: {value}")

    return '\n'.join(lines)
```

---

## 📋 工具注册

```python
# src/tools/__init__.py

from .lure_tools import query_lure_equipment

LURE_TOOLS = [query_lure_equipment]

def get_all_tools():
    """获取所有工具"""
    tools = []
    tools.extend(BASIC_TOOLS)
    tools.extend(WEATHER_TOOLS)
    tools.extend(FISHING_TOOLS)
    tools.extend(LURE_TOOLS)  # 新增路亚工具
    return tools

def get_lure_tools():
    """获取路亚工具"""
    return LURE_TOOLS.copy()
```

---

## 🔗 相关文档

- [01-架构设计.md](./01-架构设计.md) - 整体架构
- [05-实施计划.md](./05-实施计划.md) - 实施计划

---

**版本历史**：
- v2.0 (2025-11-21): 详细API接口设计
- v1.0 (2025-11-20): 初始接口框架
