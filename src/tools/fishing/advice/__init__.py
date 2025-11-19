#!/usr/bin/env python3
"""
钓鱼意见模块 (业务分析层)
独立的钓鱼分析和建议功能，不依赖core层
"""

# 导入所有钓鱼相关工具
from .scoring_tools import analyze_fishing_conditions, get_fishing_insights
from .recommendation_tools import query_fishing_recommendation

def get_advice_tools():
    """获取钓鱼意见工具"""
    return [
        query_fishing_recommendation,
        analyze_fishing_conditions,
        get_fishing_insights
    ]

__all__ = [
    'get_advice_tools',
    'query_fishing_recommendation',
    'analyze_fishing_conditions',
    'get_fishing_insights'
]