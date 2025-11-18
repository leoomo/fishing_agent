#!/usr/bin/env python3
"""
钓鱼意见模块 (业务分析层)
基于天气数据进行钓鱼分析和建议
"""

# 从core层直接导入钓鱼推荐工具，保持业务独立性
try:
    from src.core.tools.fishing_tool_core import find_best_fishing_time
    from .scoring_tools import analyze_fishing_conditions, get_fishing_insights

    # 创建钓鱼推荐工具
    from langchain_core.tools import tool

    @tool
    def query_fishing_recommendation(location: str, date: str = None) -> str:
        """查询钓鱼时间推荐，基于天气条件分析最佳的钓鱼时间"""
        return find_best_fishing_time(location, date)

    def get_advice_tools():
        """获取钓鱼意见工具"""
        return [
            query_fishing_recommendation,
            analyze_fishing_conditions,
            get_fishing_insights
        ]

except ImportError as e:
    print(f"警告: 无法导入core钓鱼推荐工具: {e}")

    def get_advice_tools():
        """返回空列表，如果无法导入所有工具"""
        return []

__all__ = [
    'get_advice_tools',
    'query_fishing_recommendation',
    'analyze_fishing_conditions',
    'get_fishing_insights'
]