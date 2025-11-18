#!/usr/bin/env python3
"""
钓鱼业务模块
包含钓鱼分析和装备推荐的业务功能（天气功能已独立）
"""

from .advice import get_advice_tools
from .equipment import get_equipment_tools

def get_fishing_tools():
    """获取所有钓鱼工具（不包括天气工具，天气工具已独立）"""
    advice_tools = get_advice_tools()
    equipment_tools = get_equipment_tools()

    return advice_tools + equipment_tools

__all__ = [
    'get_fishing_tools',
    'get_advice_tools',
    'get_equipment_tools'
]