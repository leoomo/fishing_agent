"""
淘宝店铺RPA爬虫实现
"""

import time
import logging
from typing import List, Optional
from urllib.parse import quote

from playwright.sync_api import Page

from ..base_spider import EquipmentData
from .playwright_spider import PlaywrightSpider
from .config import RPAConfig
from .login_manager import LoginManager
from .shop_manager import ShopManager

logger = logging.getLogger(__name__)


class TaobaoShopRPA(PlaywrightSpider):
    """淘宝店铺爬虫（店铺爬取模式）"""

    def __init__(self, config: Optional[RPAConfig] = None):
        """
        初始化

        Args:
            config: RPA配置，如果不提供则从环境变量加载
        """
        if config is None:
            config = RPAConfig.from_env()

        # 将 RPAConfig 转换为 BaseSpider 期望的字典格式
        base_config = {
            "request_delay": config.request_delay,
            "max_retries": config.max_retries,
            "timeout": config.page_timeout,
        }
        super().__init__(base_config)

        # 保存 RPA 配置
        self.config = config
        self.login_manager = LoginManager(config)
        self.shop_manager = ShopManager(config.shop_config_path)

        logger.info("初始化 TaobaoShopRPA（店铺爬取模式）")

    def crawl_shop(
        self,
        shop_url: str,
        categories: Optional[List[str]] = None,
        max_items_per_category: Optional[int] = None,
    ) -> List[EquipmentData]:
        """
        爬取淘宝店铺

        Args:
            shop_url: 店铺URL
            categories: 要爬取的分类列表（None表示全部）
            max_items_per_category: 每个分类最大商品数

        Returns:
            装备数据列表
        """
        if max_items_per_category is None:
            max_items_per_category = self.config.shop_max_items_per_category

        logger.info(f"开始爬取店铺: {shop_url}")

        results = []

        with self as spider:
            page = spider.page
            context = spider.context

            # 1. 确保已登录
            if not self.login_manager.ensure_logged_in(page, context):
                logger.error("❌ 登录失败，无法继续爬取")
                return results

            # 2. 访问店铺首页
            logger.info(f"访问店铺首页: {shop_url}")
            if not self.safe_goto(page, shop_url):
                logger.error("❌ 访问店铺失败")
                return results

            # 等待页面加载
            time.sleep(3)

            # 3. 提取店铺基本信息
            shop_info = self._extract_shop_info(page)
            logger.info(f"店铺信息: {shop_info.get('name', 'Unknown')}")

            # 4. 保存店铺配置
            shop_id = self.shop_manager._extract_shop_id(shop_url)
            existing_shop = self.shop_manager.get_shop(shop_id)

            if not existing_shop:
                # 新店铺，添加到配置
                self.shop_manager.add_shop(
                    shop_url=shop_url,
                    shop_name=shop_info.get("name", "未知店铺"),
                    shop_id=shop_id,
                    categories=shop_info.get("categories", []),
                    is_default=False,
                )
                logger.info(f"✅ 店铺已添加到配置: {shop_info.get('name')}")

            # 5. 获取店铺分类
            available_categories = self._extract_categories(page)
            logger.info(f"店铺分类: {available_categories}")

            # 6. 确定要爬取的分类
            if categories:
                # 过滤：仅爬取指定分类
                target_categories = [c for c in categories if c in available_categories]
                if not target_categories:
                    logger.warning(f"指定的分类不存在，将爬取全部商品")
                    target_categories = None  # 爬取全部
            else:
                target_categories = None  # 爬取全部

            # 7. 爬取商品
            if target_categories:
                # 按分类爬取
                for category in target_categories:
                    logger.info(f"爬取分类: {category}")
                    category_results = self._crawl_category(
                        page, shop_url, category, max_items_per_category
                    )
                    results.extend(category_results)
                    logger.info(f"分类 {category} 爬取 {len(category_results)} 条商品")

                    # 分类间延迟
                    time.sleep(self.config.request_delay)
            else:
                # 爬取全部商品
                logger.info("爬取全部商品...")
                all_results = self._crawl_all_items(page, shop_url, max_items_per_category)
                results.extend(all_results)

            # 8. 标记店铺已爬取
            self.shop_manager.mark_crawled(shop_id)

        logger.info(f"✅ 店铺爬取完成，共获取 {len(results)} 条商品")
        return results

    def crawl_default_shops(self) -> List[EquipmentData]:
        """
        爬取所有默认店铺

        Returns:
            装备数据列表
        """
        logger.info("开始爬取默认店铺列表...")

        # 获取默认店铺列表
        default_shops = self.shop_manager.list_shops(default_only=True)

        if not default_shops:
            logger.warning("未配置默认店铺")
            return []

        logger.info(f"找到 {len(default_shops)} 个默认店铺")

        all_results = []

        for idx, shop in enumerate(default_shops):
            shop_name = shop["shop_name"]
            shop_url = shop["shop_url"]

            logger.info(f"[{idx+1}/{len(default_shops)}] 爬取店铺: {shop_name}")

            try:
                # 爬取店铺
                results = self.crawl_shop(shop_url)
                all_results.extend(results)

                logger.info(f"✅ {shop_name} 爬取 {len(results)} 条商品")

            except Exception as e:
                logger.error(f"❌ {shop_name} 爬取失败: {e}", exc_info=True)

            # 店铺间延迟
            if idx < len(default_shops) - 1:
                delay = self.config.request_delay * 2
                logger.info(f"店铺间延迟: {delay}秒")
                time.sleep(delay)

        logger.info(f"✅ 默认店铺爬取完成，共获取 {len(all_results)} 条商品")
        return all_results

    # ==================== 内部方法 ====================

    def _extract_shop_info(self, page: Page) -> dict:
        """
        提取店铺基本信息

        Args:
            page: Page对象

        Returns:
            店铺信息字典
        """
        info = {}

        # 店铺名称
        name_selectors = [
            ".shop-name",
            ".shop-header .title",
            "h1[class*='shop']",
            ".hd-shop-name",
        ]

        for selector in name_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text:
                        info["name"] = text
                        break
            except:
                continue

        # 店铺评分
        rating_selectors = [
            ".shop-rate .score",
            ".shop-rating",
            "span[class*='rate']",
        ]

        for selector in rating_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text:
                        info["rating"] = text
                        break
            except:
                continue

        # 商品数量
        count_selectors = [
            ".shop-item-count",
            ".items-count",
            "span[class*='count']",
        ]

        for selector in count_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text:
                        info["total_items"] = text
                        break
            except:
                continue

        return info

    def _extract_categories(self, page: Page) -> List[str]:
        """
        提取店铺分类列表

        Args:
            page: Page对象

        Returns:
            分类名称列表
        """
        categories = []

        # 分类选择器
        category_selectors = [
            ".J_TCategories li",
            ".shop-categories .cat",
            "ul[class*='categor'] li",
            ".categories-menu li",
        ]

        for selector in category_selectors:
            try:
                items = page.locator(selector).all()
                for item in items:
                    try:
                        text = item.inner_text().strip()
                        if text and text not in categories:
                            categories.append(text)
                    except:
                        continue

                if categories:
                    break
            except:
                continue

        return categories

    def _crawl_category(
        self, page: Page, shop_url: str, category: str, max_items: int
    ) -> List[EquipmentData]:
        """
        爬取店铺指定分类

        Args:
            page: Page对象
            shop_url: 店铺URL
            category: 分类名称
            max_items: 最大商品数

        Returns:
            装备列表
        """
        results = []

        # 点击分类
        if not self._click_category(page, category):
            logger.warning(f"无法点击分类: {category}")
            return results

        # 等待商品列表加载
        time.sleep(2)

        # 爬取商品列表
        results = self._extract_shop_products(page, shop_url, category, max_items)

        return results

    def _crawl_all_items(
        self, page: Page, shop_url: str, max_items: int
    ) -> List[EquipmentData]:
        """
        爬取店铺全部商品

        Args:
            page: Page对象
            shop_url: 店铺URL
            max_items: 最大商品数

        Returns:
            装备列表
        """
        # 点击"全部商品"链接
        all_items_selectors = [
            ".all-cats",
            ".view-all",
            'a:has-text("全部商品")',
            'a:has-text("全部宝贝")',
        ]

        for selector in all_items_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    elem.click()
                    logger.debug(f"点击全部商品: {selector}")
                    time.sleep(2)
                    break
            except:
                continue

        # 爬取商品列表
        results = self._extract_shop_products(page, shop_url, "全部", max_items)

        return results

    def _click_category(self, page: Page, category: str) -> bool:
        """
        点击店铺分类

        Args:
            page: Page对象
            category: 分类名称

        Returns:
            是否成功
        """
        category_selectors = [
            ".J_TCategories li",
            ".shop-categories .cat",
            "ul[class*='categor'] li",
        ]

        for selector in category_selectors:
            try:
                items = page.locator(selector).all()
                for item in items:
                    text = item.inner_text().strip()
                    if text == category:
                        item.click()
                        logger.debug(f"点击分类: {category}")
                        return True
            except:
                continue

        return False

    def _extract_shop_products(
        self, page: Page, shop_url: str, category: str, max_items: int
    ) -> List[EquipmentData]:
        """
        提取店铺商品列表（支持分页）

        Args:
            page: Page对象
            shop_url: 店铺URL
            category: 分类名称
            max_items: 最大商品数

        Returns:
            装备列表
        """
        results = []
        page_num = 1
        max_pages = 20  # 最多爬取20页

        while len(results) < max_items and page_num <= max_pages:
            logger.info(f"爬取第 {page_num} 页...")

            # 模拟滚动
            self._simulate_scroll(page)

            # 提取商品列表
            page_results = self._extract_shop_items(page, shop_url, category)
            results.extend(page_results)

            logger.info(f"第 {page_num} 页提取 {len(page_results)} 条商品，累计 {len(results)} 条")

            # 检查是否达到目标数量
            if len(results) >= max_items:
                break

            # 检查是否有下一页
            if not self._has_next_page(page):
                logger.info("已到达最后一页")
                break

            # 翻页
            if not self._goto_next_page(page):
                logger.warning("翻页失败，停止爬取")
                break

            page_num += 1

            # 翻页延迟
            time.sleep(self.config.request_delay)

        # 截断到目标数量
        results = results[:max_items]

        return results

    def _extract_shop_items(
        self, page: Page, shop_url: str, category: str
    ) -> List[EquipmentData]:
        """
        提取当前页店铺商品

        Args:
            page: Page对象
            shop_url: 店铺URL
            category: 分类名称

        Returns:
            装备列表
        """
        results = []

        # 商品选择器（与搜索页类似）
        item_selectors = [
            ".item",
            ".shop-item",
            ".J_TItems .item",
            "div[class*='item']",
        ]

        items = []
        for selector in item_selectors:
            try:
                items = page.locator(selector).all()
                if items:
                    logger.debug(f"使用选择器: {selector}，找到 {len(items)} 个商品")
                    break
            except:
                continue

        if not items:
            logger.warning("未找到商品列表")
            return results

        # 逐个提取
        for idx, item in enumerate(items):
            try:
                # 提取商品URL
                url = self._extract_item_url_from_element(item)
                if not url:
                    logger.debug(f"商品 {idx+1} 无URL，跳过")
                    continue

                # 提取基础信息（从列表页）
                name = self._extract_item_name_from_element(item)
                price = self._extract_item_price_from_element(item)

                if not name:
                    logger.debug(f"商品 {idx+1} 无名称，跳过")
                    continue

                # 提取品牌
                brand = self._extract_brand_from_name(name)

                # 构建数据
                equipment = EquipmentData(
                    name=name,
                    brand=brand,
                    price=price,
                    url=url,
                    category=category,
                    source=f"shop:{self.shop_manager._extract_shop_id(shop_url)}",
                )

                results.append(equipment)
                logger.debug(f"提取商品 {idx+1}: {name}")

            except Exception as e:
                logger.debug(f"提取商品 {idx+1} 失败: {e}")
                continue

        return results

    def _extract_item_name_from_element(self, item) -> Optional[str]:
        """从商品元素提取名称"""
        selectors = [
            ".title",
            ".item-name",
            "a[class*='title']",
            "div[class*='title']",
        ]

        for selector in selectors:
            try:
                elem = item.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text:
                        return text
            except:
                continue

        return None

    def _extract_item_price_from_element(self, item) -> Optional[str]:
        """从商品元素提取价格"""
        import re

        selectors = [
            ".price",
            ".item-price",
            "span[class*='price']",
            "strong[class*='price']",
        ]

        for selector in selectors:
            try:
                elem = item.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    # 清理价格
                    text = re.sub(r"[^\d.]", "", text)
                    if text:
                        return text
            except:
                continue

        return None

    def _extract_item_url_from_element(self, item) -> Optional[str]:
        """从商品元素提取URL"""
        selectors = [
            "a[href*='item.taobao.com']",
            "a[href*='detail.tmall.com']",
            "a.item",
            "a",
        ]

        for selector in selectors:
            try:
                elem = item.locator(selector).first
                if elem.count() > 0:
                    href = elem.get_attribute("href")
                    if href:
                        # 修复协议
                        if href.startswith("//"):
                            href = "https:" + href
                        elif not href.startswith("http"):
                            href = "https:" + href

                        # 只返回淘宝/天猫链接
                        if "item.taobao.com" in href or "detail.tmall.com" in href:
                            return href
            except:
                continue

        return None

    def _extract_brand_from_name(self, name: str) -> str:
        """从商品名称推断品牌（复用TaobaoRPA逻辑）"""
        brands = [
            "禧玛诺", "shimano", "SHIMANO",
            "达亿瓦", "daiwa", "DAIWA",
            "Abu Garcia", "阿布", "abu",
            "Penn", "宾威", "penn",
            "光威", "汉鼎", "迪佳", "钓鱼王",
            "化氏", "龙王恨", "天元", "老鬼",
            "佳钓尼", "法莱", "宝飞龙", "狼王",
        ]

        name_lower = name.lower()

        for brand in brands:
            if brand.lower() in name_lower:
                return brand.capitalize()

        return "未知品牌"

    def _has_next_page(self, page: Page) -> bool:
        """检查是否有下一页"""
        next_selectors = [
            ".next:not(.disabled)",
            ".pagination .next:not([disabled])",
            "button.next:not([disabled])",
            "a.next:not(.disabled)",
        ]

        for selector in next_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0 and elem.is_visible(timeout=2000):
                    return True
            except:
                continue

        return False

    def _goto_next_page(self, page: Page) -> bool:
        """翻到下一页"""
        next_selectors = [
            ".next",
            ".pagination .next",
            "button.next",
            "a.next",
        ]

        for selector in next_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0 and elem.is_visible(timeout=2000):
                    elem.click()
                    logger.debug(f"点击下一页: {selector}")
                    time.sleep(2)
                    return True
            except:
                continue

        return False
