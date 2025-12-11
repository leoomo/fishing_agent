"""Base page for Taobao-specific functionality"""

import logging
from typing import Optional, List, Dict, Any
from playwright.sync_api import Page, Locator, expect
import time
import random

from ..core.base_page import BasePage, retry_operation

logger = logging.getLogger(__name__)


class TaobaoBasePage(BasePage):
    """Base page with Taobao-specific common functionality"""

    def __init__(self, page: Page, timeout: int = 30000):
        """Initialize Taobao base page"""
        super().__init__(page, timeout)
        self.base_url = "https://www.taobao.com"

    def is_logged_in(self) -> bool:
        """
        Check if user is logged in to Taobao

        Returns:
            True if logged in, False otherwise
        """
        # Look for user-related elements that only appear when logged in
        logged_in_indicators = [
            self.get_element_by_text("请登录", exact=True),
            self.get_element_by_text("亲，请登录", exact=True),
            self.page.locator(".site-nav-login-info-nick"),
            self.page.locator(".site-nav-user"),
        ]

        # Check if any login prompts are visible
        for indicator in logged_in_indicators[:2]:  # Text-based indicators
            try:
                if indicator.is_visible(timeout=2000):
                    return False
            except:
                continue

        # Check if user info is visible
        for indicator in logged_in_indicators[2:]:  # Element-based indicators
            try:
                if indicator.count() > 0 and indicator.first.is_visible(timeout=2000):
                    text = indicator.first.text_content() or ""
                    if text and text not in ["请登录", "登录"]:
                        return True
            except:
                continue

        return False

    def get_user_info(self) -> Optional[Dict[str, str]]:
        """
        Get current user information

        Returns:
            Dictionary with user info or None if not logged in
        """
        try:
            # Try to find user nickname
            user_selectors = [
                ".site-nav-login-info-nick",
                ".site-nav-user .user-nick",
                ".member-nick",
            ]

            for selector in user_selectors:
                element = self.page.locator(selector).first
                if element.count() > 0 and element.is_visible(timeout=2000):
                    username = element.text_content() or ""
                    if username and username not in ["请登录", "登录"]:
                        return {"username": username.strip()}

            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    @retry_operation(max_attempts=3, delay=1.0)
    def navigate_to_url(self, url: str, wait_for_load: bool = True) -> bool:
        """
        Navigate to a URL with error handling

        Args:
            url: Target URL
            wait_for_load: Whether to wait for page load

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            self.logger.info(f"Navigating to: {url}")
            self.page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")

            if wait_for_load:
                # Wait for key elements to load
                time.sleep(2)

                # Check for anti-crawler measures
                self._check_for_anti_crawler()

            self.logger.info(f"Successfully navigated to: {self.page.url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}")
            return False

    def _check_for_anti_crawler(self) -> None:
        """Check and handle anti-crawler measures"""
        # Check for common anti-crawler indicators
        anti_crawler_indicators = [
            "访问过于频繁",
            "请稍后再试",
            "系统繁忙",
            "验证码",
            "请输入验证码",
            "人机验证",
        ]

        page_content = self.page.content()
        for indicator in anti_crawler_indicators:
            if indicator in page_content:
                self.logger.warning(f"Detected anti-crawler measure: {indicator}")
                self._handle_anti_crawler(indicator)
                break

    def _handle_anti_crawler(self, indicator: str) -> None:
        """
        Handle anti-crawler measures

        Args:
            indicator: Type of anti-crawler measure detected
        """
        if "验证码" in indicator:
            self.logger.warning("Captcha detected, manual intervention required")
            self.take_screenshot("captcha_detected")
            # Could integrate with captcha solving service here

        # Add random delay to avoid further detection
        delay = random.uniform(5, 10)
        self.logger.info(f"Adding delay to avoid detection: {delay:.2f}s")
        time.sleep(delay)

    def scroll_to_load_content(
        self,
        max_scrolls: int = 10,
        wait_between_scrolls: float = 2.0
    ) -> None:
        """
        Scroll to dynamically load content

        Args:
            max_scrolls: Maximum number of scroll attempts
            wait_between_scrolls: Wait time between scrolls
        """
        self.logger.info("Scrolling to load dynamic content")

        last_height = self.page.evaluate("document.body.scrollHeight")
        scroll_count = 0
        no_new_content_count = 0

        while scroll_count < max_scrolls:
            # Scroll to bottom
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for new content to load
            time.sleep(wait_between_scrolls)

            # Check if new content loaded
            new_height = self.page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                no_new_content_count += 1
                if no_new_content_count >= 3:
                    self.logger.info("No new content detected, stopping scroll")
                    break
            else:
                no_new_content_count = 0
                last_height = new_height

            scroll_count += 1

        self.logger.info(f"Scrolling completed after {scroll_count} attempts")

    def extract_product_links(self) -> List[str]:
        """
        Extract product links from the current page

        Returns:
            List of product URLs
        """
        product_links = []

        # Multiple strategies to find product links
        link_strategies = [
            # Strategy 1: Look for links with product IDs
            lambda: self._extract_links_by_pattern(r"item\.taobao\.com/item\.htm\?id=(\d+)"),
            # Strategy 2: Look for links with click tracking
            lambda: self._extract_links_by_pattern(r"click\.simba\.taobao\.com"),
            # Strategy 3: Look for common product link containers
            lambda: self._extract_links_from_containers(),
        ]

        for strategy in link_strategies:
            try:
                links = strategy()
                if links:
                    product_links.extend(links)
                    self.logger.debug(f"Found {len(links)} product links using strategy")
                    break
            except Exception as e:
                self.logger.debug(f"Link extraction strategy failed: {e}")
                continue

        # Remove duplicates
        unique_links = list(set(product_links))
        self.logger.info(f"Found {len(unique_links)} unique product links")

        return unique_links

    def _extract_links_by_pattern(self, pattern: str) -> List[str]:
        """Extract links matching a regex pattern"""
        import re
        links = []
        elements = self.page.locator("a[href]").all()

        for element in elements:
            href = element.get_attribute("href")
            if href and re.search(pattern, href):
                # Normalize URL
                if href.startswith("//"):
                    href = "https:" + href
                elif not href.startswith("http"):
                    href = "https://" + href
                links.append(href)

        return links

    def _extract_links_from_containers(self) -> List[str]:
        """Extract links from common product container elements"""
        container_selectors = [
            "[data-spm-anchor-id*='product']",
            ".item",
            ".product",
            ".goods",
            "[class*='item']",
        ]

        for selector in container_selectors:
            containers = self.page.locator(selector).all()
            if containers:
                links = []
                for container in containers:
                    # Look for links within the container
                    link_element = container.locator("a").first
                    if link_element.count() > 0:
                        href = link_element.get_attribute("href")
                        if href and ("item.taobao.com" in href or "detail.tmall.com" in href):
                            if href.startswith("//"):
                                href = "https:" + href
                            links.append(href)

                if links:
                    return links

        return []

    def wait_for_element_with_text(
        self,
        text: str,
        timeout: Optional[int] = None
    ) -> Optional[Locator]:
        """
        Wait for an element containing specific text

        Args:
            text: Text to wait for
            timeout: Custom timeout

        Returns:
            Element locator or None if not found
        """
        try:
            locator = self.get_element_by_text(text)
            locator.wait_for(timeout=timeout or self.timeout)
            return locator
        except Exception as e:
            self.logger.error(f"Element with text '{text}' not found: {e}")
            return None

    def click_navigation_link(
        self,
        text: str,
        exact: bool = False
    ) -> bool:
        """
        Click a navigation link by text

        Args:
            text: Link text
            exact: Whether to match text exactly

        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            # Try multiple strategies
            strategies = [
                # Direct text match
                lambda: self.get_element_by_role("link", name=text, exact=exact).click(),
                # Text search
                lambda: self.get_element_by_text(text, exact=exact).click(),
                # Partial match in navigation
                lambda: self.page.locator("nav, .nav, .navigation").get_by_text(text, exact=exact).click(),
            ]

            for i, strategy in enumerate(strategies):
                try:
                    strategy()
                    self.logger.info(f"Successfully clicked navigation link '{text}' using strategy {i+1}")
                    time.sleep(1)  # Wait for navigation
                    return True
                except:
                    continue

            return False
        except Exception as e:
            self.logger.error(f"Failed to click navigation link '{text}': {e}")
            return False