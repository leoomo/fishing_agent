#!/usr/bin/env python3
"""
数学计算工具
提供基础数学运算功能 (简化版本)
"""

from langchain_core.tools import tool
from typing import Union

@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式

    Args:
        expression: 要计算的数学表达式，如 "2+3*4"

    Returns:
        计算结果字符串

    Examples:
        calculate("2+3*4")
        calculate("10*5-3")
    """
    try:
        # 安全的数学表达式计算
        allowed_chars = set('0123456789+-*/().** ')
        if not all(c in allowed_chars for c in expression):
            return "错误: 表达式包含不允许的字符"

        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"