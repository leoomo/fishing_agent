#!/usr/bin/env python3
"""
系统工具
提供系统信息功能 (简化版本)
"""

from langchain_core.tools import tool
import platform

@tool
def system_info(info_type: str = "basic") -> str:
    """
    获取系统信息

    Args:
        info_type: 信息类型 ("basic")

    Returns:
        系统信息详情

    Examples:
        system_info()
    """
    try:
        if info_type == "basic":
            return f"""系统基本信息:
操作系统: {platform.system()} {platform.release()}
Python版本: {platform.python_version()}
架构: {platform.architecture()[0]}
主机名: {platform.node()}"""
        else:
            return f"不支持的信息类型: {info_type}，请选择 basic"

    except Exception as e:
        return f"系统信息获取失败: {str(e)}"