#!/usr/bin/env python3
"""
基础工具模块 - 简化架构版本

提供基础的通用工具功能，如时间查询、计算、搜索等。
使用LangChain 1.0+最佳实践，移除过度抽象。
"""

from typing import Dict, Any, Optional
from datetime import datetime, date
import logging
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_current_time() -> str:
    """
    获取当前时间和日期信息

    Returns:
        当前的详细时间信息，包括日期、时间、星期等
    """
    try:
        now = datetime.now()

        # 获取星期名称
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[now.weekday()]

        result = f"🕐 当前时间信息：\n\n"
        result += f"📅 日期: {now.strftime('%Y年%m月%d日')}\n"
        result += f"📆 星期: {weekday}\n"
        result += f"🕐 时间: {now.strftime('%H:%M:%S')}\n"
        result += f"🌟 完整时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"

        return result

    except Exception as e:
        logger.error(f"获取当前时间失败: {e}")
        return f"获取当前时间时发生错误: {str(e)}"




# 工具列表，用于agent创建
BASIC_TOOLS = [
    get_current_time
]