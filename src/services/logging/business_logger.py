#!/usr/bin/env python3
"""
通用业务日志类

统一管理调试日志开关和日志格式。
注意：此模块已被增强版本替代，建议使用 enhanced_business_logger
"""

import os
import logging
import json
from typing import Optional, Dict, Any

# 导入增强版本并重新导出以保持向后兼容
from .enhanced_business_logger import EnhancedBusinessLogger

class BusinessLogger(EnhancedBusinessLogger):
    """
    通用业务日志记录器（兼容版本）

    注意：此类已被 EnhancedBusinessLogger 替代，
    建议新代码使用 EnhancedBusinessLogger 以获得更好的类型注解和文档。
    """

    def __init__(self, name: str):
        """
        初始化日志记录器

        Args:
            name: 日志记录器名称
        """
        super().__init__(name)
        # 保持原有的默认调试日志行为
        if os.getenv('DEBUG_LOGGING', 'true').lower() in ('true', '1', 'yes', 'on'):
            self.debug_enabled = True

# 向后兼容性：确保原有的导入方式仍然工作
__all__ = ['BusinessLogger', 'EnhancedBusinessLogger']