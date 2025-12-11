"""
平台爬虫模块

提供统一的平台爬虫接口，支持多个电商平台
"""

from .base_platform import BasePlatform, TaskConfig, TaskType, CrawlResult
from .taobao_platform import TaobaoPlatform
from .jd_platform import JDPlatform
from .registry import PlatformRegistry, platform_registry

__all__ = [
    'BasePlatform',
    'TaskConfig',
    'TaskType',
    'CrawlResult',
    'TaobaoPlatform',
    'JDPlatform',
    'PlatformRegistry',
    'platform_registry'
]