"""
工具模块

导出:
- get_all_tools: 获取所有钓鱼 Agent 工具
- 各个工具函数
"""
from .basic import get_current_time
# from .weather import get_weather  # 已移除：统一使用 query_fishing_recommendation
from .fishing_tool import query_fishing_recommendation
from .lure_tools import recommend_equipment, compare_equipment, lookup_fishing_knowledge, query_equipment, identify_from_image
from .article_tools import search_fishing_articles
from .user_equipment.tools import USER_EQUIPMENT_TOOLS


def get_all_tools():
    """返回钓鱼 Agent 的所有工具"""
    return [
        get_current_time,
        # get_weather,  # 已移除：统一使用 query_fishing_recommendation
        query_fishing_recommendation,
        recommend_equipment,
        compare_equipment,
        lookup_fishing_knowledge,
        query_equipment,
        identify_from_image,
        search_fishing_articles,  # 文章语义搜索
        *USER_EQUIPMENT_TOOLS,  # 用户装备管理工具
    ]


__all__ = [
    "get_all_tools",
    "get_current_time",
    # "get_weather",  # 已移除：统一使用 query_fishing_recommendation
    "query_fishing_recommendation",
    "recommend_equipment",
    "compare_equipment",
    "lookup_fishing_knowledge",
    "query_equipment",
    "identify_from_image",
    "search_fishing_articles",
]
