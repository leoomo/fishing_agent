"""
Scraper - 通用数据爬取框架

提供爬虫、RPA自动化、工作流引擎等数据获取能力。
"""

from .spider.base import BaseSpider, CrawlItem, EquipmentData
from .spider.anti_crawler import UserAgentRotator, RequestThrottler, ProxyRotator

__all__ = [
    # 基础爬虫
    "BaseSpider",
    "CrawlItem",
    "EquipmentData",  # 向后兼容别名
    # 反爬虫工具
    "UserAgentRotator",
    "RequestThrottler",
    "ProxyRotator",
]

__version__ = "1.0.0"
