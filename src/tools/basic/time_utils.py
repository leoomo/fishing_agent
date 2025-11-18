#!/usr/bin/env python3
"""
时间相关工具
提供时间查询、格式化等功能 (简化版本)
"""

from datetime import datetime
from langchain_core.tools import tool

@tool
def get_current_time() -> str:
    """
    获取当前时间

    Returns:
        当前时间字符串

    Examples:
        get_current_time()
    """
    try:
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})"
    except Exception as e:
        return f"获取时间失败: {str(e)}"