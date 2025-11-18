#!/usr/bin/env python3
"""
钓鱼意见模块 (业务分析层)
基于天气数据进行钓鱼分析和建议
"""

try:
    # 复用现有的钓鱼推荐工具
    from ....langchain_weather_tools_sync import query_fishing_recommendation

    def get_advice_tools():
        """获取钓鱼意见工具"""
        return [query_fishing_recommendation]

except ImportError as e:
    print(f"警告: 无法导入现有钓鱼推荐工具: {e}")

    def get_advice_tools():
        """返回空列表，如果无法导入现有工具"""
        return []

__all__ = [
    'get_advice_tools',
    'query_fishing_recommendation'
]