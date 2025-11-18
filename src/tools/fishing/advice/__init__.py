#!/usr/bin/env python3
"""
钓鱼意见模块 (业务分析层)
基于天气数据进行钓鱼分析和建议
"""

# 从新模块化文件导入钓鱼推荐工具
try:
    from ..weather.fishing_tools import query_fishing_recommendation
    from .scoring_tools import analyze_fishing_conditions, get_fishing_insights

    def get_advice_tools():
        """获取钓鱼意见工具"""
        return [
            query_fishing_recommendation,
            analyze_fishing_conditions,
            get_fishing_insights
        ]

except ImportError as e:
    print(f"警告: 无法导入新模块化钓鱼推荐工具: {e}")

    # 回退到原始文件
    try:
        from tools.langchain_weather_tools_sync import query_fishing_recommendation

        def get_advice_tools():
            """获取钓鱼意见工具（回退版本）"""
            return [query_fishing_recommendation]

    except ImportError as fallback_e:
        print(f"警告: 无法导入回退钓鱼推荐工具: {fallback_e}")

        def get_advice_tools():
            """返回空列表，如果无法导入所有工具"""
            return []

__all__ = [
    'get_advice_tools',
    'query_fishing_recommendation',
    'analyze_fishing_conditions',
    'get_fishing_insights'
]