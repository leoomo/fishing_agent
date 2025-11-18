#!/usr/bin/env python3
"""
基础工具模块
包含时间、数学、搜索、系统等基础功能工具
"""

from .time_utils import get_current_time
from .math_ops import calculate
from .info_search import search_information
from .sys_utils import system_info

def get_basic_tools():
    """获取基础工具列表"""
    return [
        get_current_time,
        calculate,
        search_information,
        system_info
    ]

__all__ = [
    'get_current_time',
    'calculate',
    'search_information',
    'system_info',
    'get_basic_tools'
]