"""
装备爬虫模块

提供电商装备爬虫功能，从淘宝、京东、论坛等网站爬取装备信息并入库。
"""

from .base_spider import EquipmentData, BaseSpider
from .anti_crawler import UserAgentRotator, RequestThrottler, ProxyRotator
from .deduplicator import EquipmentDeduplicator
from .downloader import ImageDownloader
from .data_persister import DataPersister
from .jd_spider import JDSpider
from .taobao_spider import TaobaoSpider
from .forum_spider import ForumSpider

__all__ = [
    # 基础类
    "EquipmentData",
    "BaseSpider",
    # 反爬虫
    "UserAgentRotator",
    "RequestThrottler",
    "ProxyRotator",
    # 去重
    "EquipmentDeduplicator",
    # 数据持久化
    "ImageDownloader",
    "DataPersister",
    # 具体爬虫
    "JDSpider",
    "TaobaoSpider",
    "ForumSpider",
]
