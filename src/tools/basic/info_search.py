#!/usr/bin/env python3
"""
信息搜索工具
提供知识库查询功能 (简化版本)
"""

from langchain_core.tools import tool

@tool
def search_information(query: str) -> str:
    """
    搜索信息（模拟功能）

    Args:
        query: 搜索查询词

    Returns:
        搜索结果

    Examples:
        search_information("钓鱼")
        search_information("路亚")
    """
    try:
        # 模拟知识库
        knowledge_base = {
            "钓鱼": "钓鱼是一种休闲娱乐活动，根据天气、水温、时间等因素选择合适的钓点和钓法。",
            "路亚": "路亚钓鱼是一种假饵钓法，使用拟饵模仿鱼类食物，适合钓获掠食性鱼类。",
            "鲈鱼": "鲈鱼是常见的路亚钓鱼目标鱼种，喜欢在水草边缘和障碍物附近活动。",
            "天气": "天气对钓鱼有重要影响，多云、阴天和小雨天气通常更适合钓鱼。"
        }

        query_lower = query.lower()
        for keyword, info in knowledge_base.items():
            if keyword in query_lower:
                return f"搜索结果: {info}"

        return f"关于 '{query}' 的信息: 可以尝试更具体的关键词搜索"

    except Exception as e:
        return f"信息搜索失败: {str(e)}"