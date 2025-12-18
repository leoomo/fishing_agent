"""Taobao shop page object for shop crawling"""

import logging
from typing import List, Optional, Dict, Any
from playwright.sync_api import Page, Locator
import time

from .taobao_base_page import TaobaoBasePage
from ..core.base_page import retry_operation

logger = logging.getLogger(__name__)


class TaobaoShopPage(TaobaoBasePage):
    """Taobao shop page with improved shop navigation and product extraction"""

    def __init__(self, page: Page, timeout: int = 30000):
        """Initialize shop page"""
        super().__init__(page, timeout)

    def load_shop(self, shop_url: str) -> bool:
        """
        Load shop page

        Args:
            shop_url: Shop URL

        Returns:
            True if shop loaded successfully, False otherwise
        """
        self.logger.info(f"Loading shop: {shop_url}")
        return self.navigate_to_url(shop_url)

    def get_shop_info(self) -> Dict[str, Any]:
        """
        Extract shop information

        Returns:
            Shop information dictionary
        """
        shop_info = {}

        # Extract shop name
        shop_info["name"] = self._extract_shop_name()

        # Extract shop rating
        shop_info["rating"] = self._extract_shop_rating()

        # Extract shop stats
        shop_info["total_items"] = self._extract_shop_stats()

        # Extract shop ID from URL
        shop_info["shop_id"] = self._extract_shop_id(self.page.url)

        self.logger.info(f"Shop info extracted: {shop_info.get('name', 'Unknown')}")
        return shop_info

    def _extract_shop_name(self) -> Optional[str]:
        """Extract shop name using multiple strategies"""
        name_strategies = [
            # Strategy 1: Shop header
            lambda: self.get_element_text(".shop-name"),
            lambda: self.get_element_text(".shop-header .title"),
            lambda: self.get_element_text("h1[class*='shop']"),
            # Strategy 2: Page title
            lambda: self._extract_name_from_title(),
            # Strategy 3: Breadcrumb
            lambda: self.get_element_text(".breadcrumb .shop"),
        ]

        for strategy in name_strategies:
            try:
                name = strategy()
                if name and len(name) > 2:
                    return name.strip()
            except:
                continue

        return None

    def _extract_name_from_title(self) -> Optional[str]:
        """Extract shop name from page title"""
        try:
            title = self.page.title()
            if title:
                # Remove common suffixes
                suffixes = ["-淘宝网", "-tmall.com天猫", "-天猫Tmall"]
                for suffix in suffixes:
                    if suffix in title:
                        title = title.split(suffix)[0]
                        break
                return title.strip()
        except:
            pass
        return None

    def _extract_shop_rating(self) -> Optional[str]:
        """Extract shop rating"""
        rating_strategies = [
            lambda: self.get_element_text(".shop-rate .score"),
            lambda: self.get_element_text(".shop-rating"),
            lambda: self.get_element_text("span[class*='rate']"),
            lambda: self.get_element_text(".dsr-info .score"),
        ]

        for strategy in rating_strategies:
            try:
                rating = strategy()
                if rating and any(c in rating for c in "12345"):
                    return rating.strip()
            except:
                continue

        return None

    def _extract_shop_stats(self) -> Optional[str]:
        """Extract shop statistics"""
        stats_strategies = [
            lambda: self.get_element_text(".shop-item-count"),
            lambda: self.get_element_text(".items-count"),
            lambda: self.get_element_text("span[class*='count']"),
        ]

        for strategy in stats_strategies:
            try:
                stats = strategy()
                if stats and stats.strip():
                    return stats.strip()
            except:
                continue

        return None

    def _extract_shop_id(self, url: str) -> str:
        """Extract shop ID from URL"""
        import re

        # Extract shop ID from URL patterns
        patterns = [
            r"shop(\d+)\.taobao\.com",
            r"store/(\d+)",
            r"shopId=(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # Fallback: extract subdomain
        match = re.search(r"//([^.]+)\.taobao\.com", url)
        if match:
            return match.group(1)

        return "unknown"

    def get_shop_categories(self) -> List[str]:
        """
        Extract shop categories

        Returns:
            List of category names
        """
        categories = []

        # Multiple strategies to find categories
        category_strategies = [
            # Strategy 1: Category lists
            lambda: self._extract_from_category_lists(),
            # Strategy 2: Navigation menus
            lambda: self._extract_from_navigation(),
            # Strategy 3: Sidebar categories
            lambda: self._extract_from_sidebar(),
        ]

        for strategy in category_strategies:
            try:
                found_categories = strategy()
                if found_categories:
                    categories.extend(found_categories)
                    break
            except:
                continue

        # Remove duplicates and filter
        unique_categories = list(set(c for c in categories if c and len(c) > 1))
        self.logger.info(f"Found {len(unique_categories)} shop categories")
        return unique_categories

    def _extract_from_category_lists(self) -> List[str]:
        """Extract categories from category lists"""
        category_selectors = [
            ".J_TCategories li",
            ".shop-categories .cat",
            "ul[class*='categor'] li",
            ".categories-menu li",
            ".category-list li",
        ]

        for selector in category_selectors:
            elements = self.page.locator(selector).all()
            if elements:
                categories = []
                for element in elements:
                    text = element.text_content()
                    if text and len(text.strip()) > 1:
                        categories.append(text.strip())
                if categories:
                    return categories

        return []

    def _extract_from_navigation(self) -> List[str]:
        """Extract categories from navigation menus"""
        nav_selectors = [
            ".shop-nav li",
            ".store-nav li",
            ".category-nav li",
        ]

        for selector in nav_selectors:
            elements = self.page.locator(selector).all()
            if elements:
                categories = []
                for element in elements:
                    text = element.text_content()
                    # Filter out non-category items
                    if text and not any(x in text for x in ["首页", "店铺", "首页", "全部"]):
                        categories.append(text.strip())
                if categories:
                    return categories

        return []

    def _extract_from_sidebar(self) -> List[str]:
        """Extract categories from sidebar"""
        sidebar_selectors = [
            ".sidebar .category",
            ".side-cate li",
            ".left-cate li",
        ]

        for selector in sidebar_selectors:
            elements = self.page.locator(selector).all()
            if elements:
                categories = []
                for element in elements:
                    text = element.text_content()
                    if text and len(text.strip()) > 1:
                        categories.append(text.strip())
                if categories:
                    return categories

        return []

    @retry_operation(max_attempts=3, delay=1.0)
    def click_category(self, category_name: str) -> bool:
        """
        Click on a shop category

        Args:
            category_name: Name of category to click

        Returns:
            True if clicked successfully, False otherwise
        """
        self.logger.info(f"Clicking category: {category_name}")

        # Multiple click strategies
        click_strategies = [
            # Strategy 1: Exact text match in links
            lambda: self.get_element_by_role("link", name=category_name, exact=True).click(),
            # Strategy 2: Text search
            lambda: self.get_element_by_text(category_name, exact=True).click(),
            # Strategy 3: Category items
            lambda: self._click_category_item(category_name),
            # Strategy 4: JavaScript click
            lambda: self._click_category_with_js(category_name),
        ]

        for i, strategy in enumerate(click_strategies):
            try:
                strategy()
                self.logger.info(f"Successfully clicked category '{category_name}' using strategy {i+1}")
                time.sleep(2)  # Wait for page load
                return True
            except Exception as e:
                self.logger.debug(f"Category click strategy {i+1} failed: {e}")
                continue

        self.logger.error(f"Failed to click category: {category_name}")
        return False

    def _click_category_item(self, category_name: str) -> None:
        """Click category from list items"""
        item_selectors = [
            ".J_TCategories li",
            ".shop-categories .cat",
            "ul[class*='categor'] li",
        ]

        for selector in item_selectors:
            items = self.page.locator(selector).all()
            for item in items:
                text = item.text_content()
                if text and text.strip() == category_name:
                    item.click()
                    return

    def _click_category_with_js(self, category_name: str) -> bool:
        """Click category using JavaScript"""
        js_code = f"""
        // Find and click category by text
        const elements = document.querySelectorAll('*');
        for (const el of elements) {{
            if (el.textContent && el.textContent.trim() === '{category_name}') {{
                el.click();
                return true;
            }}
        }}
        return false;
        """

        try:
            return self.page.evaluate(js_code)
        except:
            return False

    def wait_for_products_load(self, timeout: int = 10000) -> bool:
        """
        Wait for products to load after category click

        Args:
            timeout: Wait timeout in milliseconds

        Returns:
            True if products loaded, False otherwise
        """
        self.logger.info("Waiting for products to load...")

        # Product indicators
        product_indicators = [
            "[data-spm-anchor-id*='product']",
            ".item",
            ".product",
            ".goods",
            "[class*='item']",
            ".Card--doubleCard",
        ]

        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            for indicator in product_indicators:
                try:
                    elements = self.page.locator(indicator).all()
                    if elements and len(elements) > 0:
                        self.logger.info(f"Products loaded: {len(elements)} items found")
                        return True
                except:
                    continue
            time.sleep(0.5)

        self.logger.error("Products did not load within timeout")
        return False

    def extract_products_from_page(self, max_products: int = 50) -> List[Dict[str, Any]]:
        """
        Extract product information from current page

        Args:
            max_products: Maximum number of products to extract

        Returns:
            List of product dictionaries
        """
        self.logger.info(f"Extracting products from page (max: {max_products})")

        products = []
        product_elements = self._find_product_elements()

        if not product_elements:
            self.logger.warning("No product elements found")
            return products

        self.logger.info(f"Found {len(product_elements)} product elements")

        for i, element in enumerate(product_elements):
            if i >= max_products:
                self.logger.info(f"Reached maximum product limit: {max_products}")
                break

            try:
                product_info = self._extract_product_info(element)
                if product_info:
                    products.append(product_info)
                    self.logger.debug(f"Extracted product {i+1}: {product_info.get('name', 'Unknown')}")
            except Exception as e:
                self.logger.error(f"Failed to extract product {i+1}: {e}")
                continue

        self.logger.info(f"Successfully extracted {len(products)} products")
        return products

    def _find_product_elements(self) -> List[Locator]:
        """Find product elements using multiple strategies"""
        element_strategies = [
            # Strategy 1: Data attributes (most reliable)
            lambda: self.page.locator("[data-spm-anchor-id*='product']").all(),
            # Strategy 2: Common product containers
            lambda: self.page.locator(".Card--doubleCard").all(),
            lambda: self.page.locator("[class*='item']").all(),
            # Strategy 3: Product cards
            lambda: self.page.locator("[class*='product']").all(),
            lambda: self.page.locator("[class*='goods']").all(),
        ]

        for strategy in element_strategies:
            try:
                elements = strategy()
                if elements and len(elements) > 0:
                    self.logger.debug(f"Found {len(elements)} product elements")
                    return elements
            except:
                continue

        return []

    def _extract_product_info(self, element: Locator) -> Optional[Dict[str, Any]]:
        """Extract product information from element"""
        product_info = {}

        # Extract product URL
        product_info["url"] = self._extract_product_url(element)

        # Extract product name
        product_info["name"] = self._extract_product_name(element)

        # Extract product price
        product_info["price"] = self._extract_product_price(element)

        # Validate extracted info
        if not product_info.get("url") or not product_info.get("name"):
            return None

        return product_info

    def _extract_product_url(self, element: Locator) -> Optional[str]:
        """Extract product URL from element"""
        url_strategies = [
            # Strategy 1: Direct href
            lambda: element.get_attribute("href"),
            # Strategy 2: Child link
            lambda: element.locator("a").first.get_attribute("href"),
            # Strategy 3: Parent link
            lambda: element.locator("xpath=./ancestor::a[1]").first.get_attribute("href"),
        ]

        for strategy in url_strategies:
            try:
                url = strategy()
                if url and ("item.taobao.com" in url or "detail.tmall.com" in url):
                    # Normalize URL
                    if url.startswith("//"):
                        url = "https:" + url
                    elif not url.startswith("http"):
                        url = "https://" + url
                    return url
            except:
                continue

        return None

    def _extract_product_name(self, element: Locator) -> Optional[str]:
        """Extract product name from element"""
        name_strategies = [
            # Strategy 1: Title elements
            lambda: element.locator(".title, [class*='title']").first.text_content(),
            # Strategy 2: Link text
            lambda: element.locator("a").first.text_content(),
            # Strategy 3: Element text content
            lambda: element.text_content(),
        ]

        for strategy in name_strategies:
            try:
                name = strategy()
                if name and len(name.strip()) > 3:
                    # Clean up the name
                    name = name.strip()
                    # Remove price and other non-name info
                    lines = name.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('¥') and not line.isdigit() and len(line) > 5:
                            return line
            except:
                continue

        return None

    def _extract_product_price(self, element: Locator) -> Optional[str]:
        """Extract product price from element"""
        import re

        price_strategies = [
            # Strategy 1: Price elements
            lambda: element.locator(".price, [class*='price']").first.text_content(),
            # Strategy 2: Look for price patterns in text
            lambda: self._find_price_in_text(element.text_content()),
        ]

        for strategy in price_strategies:
            try:
                price = strategy()
                if price:
                    # Extract numeric price
                    price_match = re.search(r'[\d,.]+', price)
                    if price_match:
                        return price_match.group()
            except:
                continue

        return None

    def _find_price_in_text(self, text: str) -> Optional[str]:
        """Find price in text content"""
        import re

        # Price patterns
        patterns = [
            r'¥\s*(\d+(?:\.\d+)?)',
            r'￥\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?\s*元)',
            r'(\d+(?:\.\d+)?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def has_next_page(self) -> bool:
        """
        Check if there's a next page

        Returns:
            True if next page exists, False otherwise
        """
        next_page_strategies = [
            # Strategy 1: Next button
            lambda: self._check_next_button(),
            # Strategy 2: Pagination
            lambda: self._check_pagination(),
        ]

        for strategy in next_page_strategies:
            try:
                if strategy():
                    return True
            except:
                continue

        return False

    def _check_next_button(self) -> bool:
        """Check for next page button"""
        next_selectors = [
            ".next:not(.disabled)",
            ".pagination .next:not([disabled])",
            "button.next:not([disabled])",
            "a.next:not(.disabled)",
            "[aria-label='Next']",
        ]

        for selector in next_selectors:
            element = self.page.locator(selector).first
            if element.count() > 0 and element.is_visible(timeout=2000):
                return True

        return False

    def _check_pagination(self) -> bool:
        """Check pagination for next page"""
        # Look for current page number that's not the last
        pagination = self.page.locator(".pagination, .pager").first
        if pagination.count() > 0:
            # Check if there are page numbers
            page_numbers = pagination.locator(".page, [class*='page']").all()
            if len(page_numbers) > 1:
                return True

        return False

    @retry_operation(max_attempts=3, delay=1.0)
    def go_to_next_page(self) -> bool:
        """
        Navigate to next page

        Returns:
            True if navigation successful, False otherwise
        """
        self.logger.info("Navigating to next page...")

        next_strategies = [
            # Strategy 1: Next button
            lambda: self._click_next_button(),
            # Strategy 2: Next page link
            lambda: self._click_next_link(),
        ]

        for i, strategy in enumerate(next_strategies):
            try:
                result = strategy()
                if result:
                    self.logger.info(f"Successfully navigated to next page using strategy {i+1}")
                    time.sleep(2)  # Wait for page load
                    return True
            except Exception as e:
                self.logger.debug(f"Next page strategy {i+1} failed: {e}")
                continue

        self.logger.error("Failed to navigate to next page")
        return False

    def _click_next_button(self) -> bool:
        """Click next page button"""
        button_selectors = [
            ".next:not(.disabled)",
            "button.next:not([disabled])",
            "[aria-label='Next']",
        ]

        for selector in button_selectors:
            element = self.page.locator(selector).first
            if element.count() > 0 and element.is_visible(timeout=2000):
                element.click()
                return True

        return False

    def _click_next_link(self) -> bool:
        """Click next page link"""
        link_selectors = [
            "a.next:not(.disabled)",
            ".pagination a:has-text('下一页')",
            ".pager a:has-text('Next')",
        ]

        for selector in link_selectors:
            element = self.page.locator(selector).first
            if element.count() > 0 and element.is_visible(timeout=2000):
                element.click()
                return True

        return False