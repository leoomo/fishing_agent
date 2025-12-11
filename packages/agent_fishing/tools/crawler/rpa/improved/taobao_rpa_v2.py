"""Improved Taobao RPA implementation with best practices"""

import logging
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from ..core.spider_manager import SpiderManager, BrowserConfig, BrowserType
from ..pages.taobao_login_page import TaobaoLoginPage
from ..pages.taobao_shop_page import TaobaoShopPage
from ..pages.taobao_base_page import TaobaoBasePage
from ...base_spider import EquipmentData
from ..config import RPAConfig
from ..session_storage import SessionStorage

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result of crawl operation"""
    items: List[EquipmentData]
    total_pages: int
    total_items: int
    errors: List[str]
    screenshots: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "items_count": len(self.items),
            "total_pages": self.total_pages,
            "total_items": self.total_items,
            "errors": self.errors,
            "screenshots_count": len(self.screenshots),
            "items": [item.__dict__ for item in self.items],
        }


class TaobaoRPAV2:
    """Improved Taobao RPA with best practices"""

    def __init__(self, config: Optional[RPAConfig] = None):
        """
        Initialize Taobao RPA

        Args:
            config: RPA configuration
        """
        self.config = config or RPAConfig.from_env()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Convert to browser config
        self.browser_config = BrowserConfig(
            browser_type=BrowserType.CHROMIUM,
            headless=self.config.headless,
            timeout=self.config.timeout,
            enable_stealth=self.config.enable_stealth,
        )

        # Initialize spider manager
        self.spider_manager = SpiderManager(self.browser_config)

        # Session storage
        self.session_storage = SessionStorage(self.config.cookie_path)

        # Pages (lazy initialization)
        self._login_page: Optional[TaobaoLoginPage] = None
        self._shop_page: Optional[TaobaoShopPage] = None

        self.logger.info("TaobaoRPAV2 initialized")

    @property
    def login_page(self) -> TaobaoLoginPage:
        """Get login page instance"""
        if not self._login_page and self.spider_manager.page:
            self._login_page = TaobaoLoginPage(self.spider_manager.page)
        return self._login_page

    @property
    def shop_page(self) -> TaobaoShopPage:
        """Get shop page instance"""
        if not self._shop_page and self.spider_manager.page:
            self._shop_page = TaobaoShopPage(self.spider_manager.page)
        return self._shop_page

    def crawl_shop_products(
        self,
        shop_url: str,
        category: Optional[str] = None,
        max_items: int = 100,
        max_pages: int = 10
    ) -> CrawlResult:
        """
        Crawl products from a Taobao shop

        Args:
            shop_url: Shop URL
            category: Specific category to crawl (None for all)
            max_items: Maximum items to crawl
            max_pages: Maximum pages to crawl

        Returns:
            CrawlResult with extracted products
        """
        operation_id = self.spider_manager.start_operation(f"crawl_shop_{Path(shop_url).name}")
        result = CrawlResult(items=[], total_pages=0, total_items=0, errors=[], screenshots=[])

        try:
            with self.spider_manager.browser_session() as page:
                # Ensure logged in
                if not self._ensure_logged_in():
                    raise Exception("Failed to login")

                # Load shop page
                if not self.shop_page.load_shop(shop_url):
                    raise Exception(f"Failed to load shop: {shop_url}")

                # Extract shop info
                shop_info = self.shop_page.get_shop_info()
                self.logger.info(f"Crawling shop: {shop_info.get('name', 'Unknown')}")

                # Navigate to category if specified
                if category:
                    categories = self.shop_page.get_shop_categories()
                    if category not in categories:
                        result.errors.append(f"Category '{category}' not found in shop")
                        category = None  # Fall back to all products
                    else:
                        if not self.shop_page.click_category(category):
                            result.errors.append(f"Failed to click category: {category}")
                            category = None
                        else:
                            if not self.shop_page.wait_for_products_load():
                                result.errors.append("Failed to load products for category")
                                return result

                # Crawl products page by page
                page_num = 1
                while page_num <= max_pages and len(result.items) < max_items:
                    self.logger.info(f"Crawling page {page_num}...")

                    # Extract products from current page
                    page_products = self.shop_page.extract_products_from_page(
                        max_products=max_items - len(result.items)
                    )

                    # Convert to EquipmentData
                    for product_info in page_products:
                        try:
                            equipment = self._convert_to_equipment_data(
                                product_info,
                                shop_info.get("shop_id"),
                                category or "unknown"
                            )
                            result.items.append(equipment)
                            result.total_items += 1
                        except Exception as e:
                            error_msg = f"Failed to convert product {product_info.get('url', 'unknown')}: {e}"
                            result.errors.append(error_msg)
                            self.logger.error(error_msg)

                    result.total_pages = page_num

                    # Check if we need more pages
                    if len(result.items) >= max_items:
                        self.logger.info(f"Reached maximum item limit: {max_items}")
                        break

                    # Check for next page
                    if not self.shop_page.has_next_page():
                        self.logger.info("No more pages available")
                        break

                    # Go to next page
                    if not self.shop_page.go_to_next_page():
                        self.logger.warning("Failed to go to next page")
                        break

                    page_num += 1

                    # Add delay between pages
                    self.spider_manager.simulate_human_delay(2, 4)

                # Save screenshot of final page
                screenshot = self.spider_manager.take_screenshot(f"shop_{shop_info.get('shop_id')}_final")
                if screenshot:
                    result.screenshots.append(screenshot)

                self.logger.info(f"Crawling completed: {len(result.items)} items from {result.total_pages} pages")
                self.spider_manager.end_operation(success=True)
                return result

        except Exception as e:
            error_msg = f"Shop crawling failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

            # Take error screenshot
            screenshot = self.spider_manager.take_screenshot("crawl_error")
            if screenshot:
                result.screenshots.append(screenshot)

            self.spider_manager.end_operation(success=False, error_message=error_msg)
            return result

    def _ensure_logged_in(self) -> bool:
        """Ensure user is logged in to Taobao"""
        self.logger.info("Checking login status...")

        # Try to use saved session
        if self._load_saved_session():
            if self.login_page.is_logged_in():
                self.logger.info("✅ Logged in with saved session")
                return True
            else:
                self.logger.warning("Saved session is invalid")
                self.session_storage.mark_invalid()

        # Perform QR code login
        return self.login_page.login_with_qr_code(interactive=True)

    def _load_saved_session(self) -> bool:
        """Load saved session cookies"""
        try:
            if not self.session_storage.exists():
                return False

            cookies = self.session_storage.get_cookies()
            if not cookies:
                return False

            # Add cookies to context
            self.spider_manager.context.add_cookies(cookies)
            self.logger.debug(f"Loaded {len(cookies)} cookies")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            return False

    def _convert_to_equipment_data(
        self,
        product_info: Dict[str, Any],
        shop_id: Optional[str],
        category: str
    ) -> EquipmentData:
        """
        Convert product info to EquipmentData

        Args:
            product_info: Product information from shop page
            shop_id: Shop ID
            category: Product category

        Returns:
            EquipmentData object
        """
        # Extract brand from name
        brand = self._extract_brand_from_name(product_info.get("name", ""))

        # Parse price
        price = None
        price_str = product_info.get("price")
        if price_str:
            try:
                # Remove non-numeric characters
                import re
                price_match = re.search(r'[\d.]+', price_str.replace(',', ''))
                if price_match:
                    price = float(price_match.group())
            except:
                pass

        return EquipmentData(
            name=product_info.get("name", ""),
            brand=brand or "未知品牌",
            price=price,
            url=product_info.get("url", ""),
            category=category,
            source=f"taobao_shop:{shop_id}",
            description=None,
            images=[],
            specs={},
        )

    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """Extract brand from product name"""
        if not name:
            return None

        # Common fishing equipment brands
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
                return brand

        return None

    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        Get detailed product information

        Args:
            product_url: Product detail page URL

        Returns:
            EquipmentData with full details or None
        """
        operation_id = self.spider_manager.start_operation(f"product_detail_{Path(product_url).name}")

        try:
            with self.spider_manager.browser_session() as page:
                # Ensure logged in
                if not self._ensure_logged_in():
                    raise Exception("Failed to login")

                # Navigate to product page
                base_page = TaobaoBasePage(page)
                if not base_page.navigate_to_url(product_url):
                    raise Exception(f"Failed to load product: {product_url}")

                # Extract detailed information
                product_info = self._extract_detailed_product_info(page)

                # Convert to EquipmentData
                equipment = self._convert_detailed_to_equipment_data(product_info)

                self.logger.info(f"Successfully extracted product details: {equipment.name}")
                self.spider_manager.end_operation(success=True)
                return equipment

        except Exception as e:
            error_msg = f"Failed to get product detail: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.spider_manager.end_operation(success=False, error_message=error_msg)
            return None

    def _extract_detailed_product_info(self, page) -> Dict[str, Any]:
        """Extract detailed product information from page"""
        product_info = {}

        # Extract basic info
        product_info["name"] = self._extract_detail_name(page)
        product_info["price"] = self._extract_detail_price(page)
        product_info["description"] = self._extract_detail_description(page)
        product_info["images"] = self._extract_detail_images(page)
        product_info["specs"] = self._extract_detail_specs(page)

        return product_info

    def _extract_detail_name(self, page) -> Optional[str]:
        """Extract product name from detail page"""
        name_selectors = [
            "h1",
            ".tb-detail-hd h1",
            ".ItemHeader--mainTitle",
            "h1[class*='title']",
            ".tb-main-title",
        ]

        for selector in name_selectors:
            try:
                element = page.locator(selector).first
                if element.count() > 0:
                    text = element.text_content()
                    if text and len(text.strip()) > 0:
                        return text.strip()
            except:
                continue

        return None

    def _extract_detail_price(self, page) -> Optional[str]:
        """Extract price from detail page"""
        import re

        price_selectors = [
            ".tb-rmb-num",
            ".Price--priceText",
            "span[class*='price']",
            ".tm-price",
            ".price",
        ]

        for selector in price_selectors:
            try:
                element = page.locator(selector).first
                if element.count() > 0:
                    text = element.text_content()
                    if text:
                        # Extract numeric price
                        price_match = re.search(r'[\d.]+', text)
                        if price_match:
                            return price_match.group()
            except:
                continue

        return None

    def _extract_detail_description(self, page) -> Optional[str]:
        """Extract product description"""
        desc_selectors = [
            "#description",
            ".detail-content",
            "div[class*='detail']",
            ".tb-detail",
        ]

        for selector in desc_selectors:
            try:
                element = page.locator(selector).first
                if element.count() > 0:
                    text = element.text_content()
                    if text and len(text.strip()) > 10:
                        # Truncate long descriptions
                        desc = text.strip()
                        if len(desc) > 1000:
                            desc = desc[:1000] + "..."
                        return desc
            except:
                continue

        return None

    def _extract_detail_images(self, page) -> List[str]:
        """Extract product images"""
        images = []

        # Main images
        main_selectors = [
            "#J_UlThumb img",
            ".tb-thumb img",
            "ul[class*='pic-thumb'] img",
        ]

        for selector in main_selectors:
            try:
                elements = page.locator(selector).all()
                for element in elements[:5]:
                    src = element.get_attribute("src") or element.get_attribute("data-src")
                    if src and "alicdn.com" in src:
                        if src.startswith("//"):
                            src = "https:" + src
                        images.append(src)
                if images:
                    break
            except:
                continue

        # Detail images
        detail_selectors = [
            "#description img",
            ".detail-content img",
        ]

        for selector in detail_selectors:
            try:
                elements = page.locator(selector).all()
                for element in elements[:5]:
                    src = element.get_attribute("src") or element.get_attribute("data-src")
                    if src and "alicdn.com" in src and src not in images:
                        if src.startswith("//"):
                            src = "https:" + src
                        images.append(src)
                if len(images) >= 10:
                    break
            except:
                continue

        return images

    def _extract_detail_specs(self, page) -> Dict[str, str]:
        """Extract product specifications"""
        specs = {}

        spec_selectors = [
            ".attributes-list",
            ".Specs--attributes",
            ".tm-tableAttr",
            "#J_AttrUL",
        ]

        for selector in spec_selectors:
            try:
                container = page.locator(selector).first
                if container.count() == 0:
                    continue

                items = container.locator("li").all()
                for item in items:
                    try:
                        text = item.text_content().strip()
                        if "：" in text:
                            key, value = text.split("：", 1)
                        elif ":" in text:
                            key, value = text.split(":", 1)
                        else:
                            continue

                        key = key.strip()
                        value = value.strip()

                        if key and value:
                            specs[key] = value
                    except:
                        continue

                if specs:
                    break
            except:
                continue

        return specs

    def _convert_detailed_to_equipment_data(self, product_info: Dict[str, Any]) -> EquipmentData:
        """Convert detailed product info to EquipmentData"""
        # Extract brand
        brand = None
        if product_info.get("specs") and "品牌" in product_info["specs"]:
            brand = product_info["specs"]["品牌"]
        else:
            brand = self._extract_brand_from_name(product_info.get("name", ""))

        # Parse price
        price = None
        if product_info.get("price"):
            try:
                price = float(product_info["price"])
            except:
                pass

        # Convert images to expected format
        images = []
        if product_info.get("images"):
            images = [{"url": img, "type": "detail"} for img in product_info["images"]]

        # Infer category from specs and name
        category = self._infer_category(product_info)

        return EquipmentData(
            name=product_info.get("name", ""),
            brand=brand or "未知品牌",
            price=price,
            url="",  # Will be set by caller
            category=category,
            source="taobao_rpa_detail",
            description=product_info.get("description"),
            images=images,
            specs=product_info.get("specs", {}),
        )

    def _infer_category(self, product_info: Dict[str, Any]) -> str:
        """Infer product category from information"""
        name = (product_info.get("name") or "").lower()
        specs = product_info.get("specs", {})

        # Check specs first
        if any(k in specs for k in ["长度", "调性", "硬度"]):
            return "鱼竿"
        elif any(k in specs for k in ["速比", "轴承", "线容量"]):
            return "渔轮"
        elif any(k in specs for k in ["线径", "拉力", "线长"]):
            return "鱼线"
        elif "饵型" in specs:
            return "拟饵"

        # Check name keywords
        if any(kw in name for kw in ["鱼竿", "钓竿", "竿"]):
            return "鱼竿"
        elif any(kw in name for kw in ["渔轮", "纺车", "轮"]):
            return "渔轮"
        elif any(kw in name for kw in ["鱼线", "线"]):
            return "鱼线"
        elif any(kw in name for kw in ["路亚", "拟饵", "饵"]):
            return "拟饵"
        elif "钩" in name:
            return "鱼钩"
        elif "漂" in name:
            return "浮漂"

        return "通用"

    def get_crawl_statistics(self) -> Dict[str, Any]:
        """Get crawling statistics"""
        return self.spider_manager.get_metrics_summary()