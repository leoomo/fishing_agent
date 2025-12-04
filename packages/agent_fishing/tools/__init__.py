"""
工具模块

导出:
- get_all_tools: 获取所有钓鱼 Agent 工具
- 各个工具函数
"""
from .basic import get_current_time
from .weather import get_weather
from .fishing_tool import query_fishing_recommendation
from .lure_tools import recommend_equipment, compare_equipment, lookup_fishing_knowledge, identify_from_image
from .user_equipment.tools import USER_EQUIPMENT_TOOLS


def get_all_tools():
    """返回钓鱼 Agent 的所有工具"""
    return [
        get_current_time,
        get_weather,
        query_fishing_recommendation,
        recommend_equipment,
        compare_equipment,
        lookup_fishing_knowledge,
        identify_from_image,
        *USER_EQUIPMENT_TOOLS,  # 用户装备管理工具
    ]


__all__ = [
    "get_all_tools",
    "get_current_time",
    "get_weather",
    "query_fishing_recommendation",
    "recommend_equipment",
    "compare_equipment",
    "lookup_fishing_knowledge",
    "identify_from_image",
]
