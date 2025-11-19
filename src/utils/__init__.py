#!/usr/bin/env python3
"""
工具模块 - 提供简化的API调用、缓存和坐标工具支持

这个模块提供了架构简化后的核心工具函数，移除了过度的抽象层，
直接提供API调用、缓存和坐标解析功能。
"""

# 导出核心工具函数
from .cache import SimpleCache
from .coordinate_utils import get_coordinates
from .api_client import APIClient

__all__ = [
    'SimpleCache',
    'get_coordinates',
    'APIClient'
]