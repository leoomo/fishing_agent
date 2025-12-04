"""
RPA爬虫模块

提供基于 Playwright 的淘宝 RPA 爬虫实现
"""

# 配置类
from .config import RPAConfig

# 基类
from .playwright_spider import PlaywrightSpider

# 淘宝RPA实现
from .taobao_rpa import TaobaoRPA

# 店铺管理和店铺爬虫
from .shop_manager import ShopManager
from .taobao_shop_rpa import TaobaoShopRPA

__all__ = [
    "RPAConfig",
    "PlaywrightSpider",
    "TaobaoRPA",
    "ShopManager",
    "TaobaoShopRPA",
]
