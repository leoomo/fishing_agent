#!/usr/bin/env python3
"""
基础工具集 - 独立工具定义
包含时间查询、数学计算、信息搜索等基础功能工具
"""

from datetime import datetime
from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """获取当前时间和日期"""
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})"


@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        allowed_chars = set('0123456789+-*/().** ')
        if not all(c in allowed_chars for c in expression):
            return "错误: 表达式包含不允许的字符"

        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def search_information(query: str) -> str:
    """搜索信息（模拟功能）"""
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


def get_basic_tools():
    """获取基础工具列表"""
    return [get_current_time, calculate, search_information]