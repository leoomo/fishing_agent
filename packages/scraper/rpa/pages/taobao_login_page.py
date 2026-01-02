"""Taobao login page object"""

import logging
import time
from typing import Optional, Dict, Any
from playwright.sync_api import Page, Locator
import os
from datetime import datetime

from .taobao_base_page import TaobaoBasePage
from ..core.base_page import retry_operation

logger = logging.getLogger(__name__)


class TaobaoLoginPage(TaobaoBasePage):
    """Taobao login page object with improved login handling"""

    LOGIN_URL = "https://login.taobao.com/"

    def __init__(self, page: Page, timeout: int = 30000):
        """Initialize login page"""
        super().__init__(page, timeout)

    @retry_operation(max_attempts=3, delay=2.0)
    def load(self) -> bool:
        """
        Load the login page

        Returns:
            True if page loaded successfully, False otherwise
        """
        try:
            self.logger.info("Loading Taobao login page...")
            success = self.navigate_to_url(self.LOGIN_URL)

            if success:
                # Wait for login form to be ready
                time.sleep(3)

                # 检查是否有"快速进入"按钮（用户之前已登录过）
                if self._try_quick_enter():
                    self.logger.info("Quick enter successful, skipping QR login")
                    return True

                self.logger.info("Login page loaded successfully")

            return success
        except Exception as e:
            self.logger.error(f"Failed to load login page: {e}")
            return False

    def _try_quick_enter(self) -> bool:
        """
        尝试点击"快速进入"按钮

        淘宝登录页面在用户之前已登录过时，可能显示"快速进入"按钮，
        点击后可直接进入而无需重新扫码登录。

        Returns:
            True if quick enter button found and clicked successfully, False otherwise
        """
        quick_enter_selectors = [
            # 精确匹配提供的 HTML 结构
            'button.fm-button.fm-submit:has-text("快速进入")',
            'button[type="submit"].fm-button.fm-submit:has-text("快速进入")',
            # 备用选择器
            'button:has-text("快速进入")',
            '.fm-submit:has-text("快速进入")',
            'text=快速进入',
        ]

        for selector in quick_enter_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    self.logger.info(f"Found '快速进入' button, clicking...")
                    element.click()
                    time.sleep(3)  # 等待页面跳转

                    # 验证是否成功进入
                    if self.is_logged_in():
                        self.logger.info("Quick enter login successful")
                        return True
                    else:
                        self.logger.warning("Quick enter clicked but login not verified")
            except Exception as e:
                self.logger.debug(f"Quick enter selector '{selector}' failed: {e}")
                continue

        return False

    def switch_to_qr_login(self) -> bool:
        """
        Switch to QR code login mode

        Returns:
            True if successfully switched to QR login, False otherwise
        """
        self.logger.info("Switching to QR code login...")

        # Multiple strategies to find and click QR login option
        qr_login_strategies = [
            # Strategy 1: Look for QR login tab
            lambda: self._click_qr_tab(),
            # Strategy 2: Look for QR login button
            lambda: self._click_qr_button(),
            # Strategy 3: JavaScript injection
            lambda: self._switch_qr_with_js(),
        ]

        for i, strategy in enumerate(qr_login_strategies):
            try:
                result = strategy()
                if result:
                    self.logger.info(f"Successfully switched to QR login using strategy {i+1}")
                    time.sleep(2)  # Wait for QR code to load
                    return True
            except Exception as e:
                self.logger.debug(f"QR login strategy {i+1} failed: {e}")
                continue

        # Check if QR code is already visible
        if self._is_qr_code_visible():
            self.logger.info("QR code is already visible")
            return True

        self.logger.warning("Failed to switch to QR login mode")
        return False

    def _click_qr_tab(self) -> bool:
        """Click QR login tab"""
        tab_selectors = [
            "text=扫码登录",
            "[data-type='qrcode']",
            ".login-form-qrcode-title",
            ".qrcode-tab",
        ]

        for selector in tab_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    element.click()
                    return True
            except:
                continue

        return False

    def _click_qr_button(self) -> bool:
        """Click QR login button"""
        button_selectors = [
            "button:has-text('扫码')",
            "a:has-text('扫码登录')",
            ".qrcode-btn",
        ]

        for selector in button_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    element.click()
                    return True
            except:
                continue

        return False

    def _switch_qr_with_js(self) -> bool:
        """Switch to QR login using JavaScript"""
        js_code = """
        // Find and click QR login elements
        const qrTexts = ['扫码登录', '二维码登录'];
        for (const text of qrTexts) {
            const elements = document.querySelectorAll('*');
            for (const el of elements) {
                if (el.textContent && el.textContent.includes(text)) {
                    el.click();
                    return true;
                }
            }
        }
        return false;
        """

        try:
            result = self.page.evaluate(js_code)
            return result
        except:
            return False

    def _is_qr_code_visible(self) -> bool:
        """Check if QR code is visible"""
        qr_selectors = [
            "#login .qrcode-img",
            ".qrcode-img",
            'img[src*="qrcode"]',
            "[class*='qrcode'] img",
        ]

        for selector in qr_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    return True
            except:
                continue

        return False

    def wait_for_qr_code(self, timeout: int = 10000) -> bool:
        """
        Wait for QR code to appear

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            True if QR code appeared, False otherwise
        """
        self.logger.info("Waiting for QR code to load...")

        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            if self._is_qr_code_visible():
                self.logger.info("QR code is visible")
                return True
            time.sleep(0.5)

        self.logger.error("QR code did not appear within timeout")
        return False

    def save_qr_screenshot(self) -> Optional[str]:
        """
        Save QR code screenshot

        Returns:
            Screenshot path or None if failed
        """
        try:
            # Create screenshots directory
            screenshot_dir = "shared/data/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"taobao_qr_{timestamp}.png"
            filepath = os.path.join(screenshot_dir, filename)

            # Try to find QR code element and crop screenshot
            qr_element = None
            qr_selectors = [
                ".qrcode-img",
                "#login .qrcode-img",
                'img[src*="qrcode"]',
            ]

            for selector in qr_selectors:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    qr_element = element
                    break

            if qr_element:
                # Screenshot just the QR code element
                qr_element.screenshot(path=filepath)
            else:
                # Fallback to full page screenshot
                self.page.screenshot(path=filepath)

            self.logger.info(f"QR code screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save QR screenshot: {e}")
            return None

    def wait_for_login_completion(
        self,
        max_wait_time: int = 300,
        check_interval: float = 2.0
    ) -> bool:
        """
        Wait for login to complete after QR code scan

        Args:
            max_wait_time: Maximum wait time in seconds
            check_interval: Check interval in seconds

        Returns:
            True if login successful, False otherwise
        """
        self.logger.info("Waiting for QR code scan and login completion...")

        start_time = time.time()
        checked_urls = set()

        while (time.time() - start_time) < max_wait_time:
            current_url = self.page.url
            checked_urls.add(current_url)

            # Check if URL changed away from login page
            if "login.taobao.com" not in current_url:
                self.logger.info(f"Detected URL change to: {current_url}")
                time.sleep(2)  # Wait for redirect to complete

                # Verify login success
                if self.is_logged_in():
                    self.logger.info("Login verification successful")
                    return True
                else:
                    self.logger.warning("URL changed but login not verified")

            # 检查是否出现"快速进入"按钮
            if self._try_quick_enter():
                self.logger.info("Quick enter successful during wait")
                return True

            # Check for login success indicators
            if self._check_login_success_indicators():
                self.logger.info("Login success indicators detected")
                return True

            time.sleep(check_interval)

        self.logger.error(f"Login completion timeout after {max_wait_time} seconds")
        return False

    def _check_login_success_indicators(self) -> bool:
        """Check for indicators of successful login"""
        success_indicators = [
            # User info elements
            ".site-nav-login-info-nick",
            ".site-nav-user",
            # Home page elements
            ".search-combobox",
            "#q",
            ".logo",
        ]

        for indicator in success_indicators:
            try:
                element = self.page.locator(indicator).first
                if element.count() > 0 and element.is_visible(timeout=2000):
                    return True
            except:
                continue

        return False

    def login_with_qr_code(self, interactive: bool = True) -> bool:
        """
        Perform QR code login flow

        Args:
            interactive: Whether to prompt user for interaction

        Returns:
            True if login successful, False otherwise
        """
        try:
            # Load login page
            if not self.load():
                return False

            # Switch to QR login
            if not self.switch_to_qr_login():
                self.logger.error("Failed to switch to QR login mode")
                return False

            # Wait for QR code
            if not self.wait_for_qr_code():
                self.logger.error("QR code did not load")
                return False

            # Save QR screenshot
            qr_screenshot = self.save_qr_screenshot()

            if interactive:
                # Prompt user to scan QR code
                self._prompt_user_to_scan(qr_screenshot)

            # Wait for login completion
            success = self.wait_for_login_completion()

            if success:
                self.logger.info("✅ QR code login successful")
            else:
                self.logger.error("❌ QR code login failed")

            return success

        except Exception as e:
            self.logger.error(f"QR code login failed: {e}", exc_info=True)
            return False

    def _prompt_user_to_scan(self, qr_screenshot: Optional[str]) -> None:
        """
        Prompt user to scan QR code

        Args:
            qr_screenshot: Path to QR code screenshot
        """
        print("\n" + "=" * 60)
        print("📱 Please scan the QR code with your Taobao mobile app")
        print("=" * 60)

        if qr_screenshot:
            print(f"📸 QR code saved to: {qr_screenshot}")
            if not self.page.context.browser.is_connected:
                print("⚠️  Running in headless mode - check the saved screenshot")
            else:
                print("✅ QR code is also visible in the browser")

        print("=" * 60)
        input("👉 Press Enter after scanning the QR code...")
        print("\n⏳ Verifying login status...\n")

    def get_login_error(self) -> Optional[str]:
        """
        Get login error message if any

        Returns:
            Error message or None
        """
        error_selectors = [
            ".error",
            ".error-msg",
            "[class*='error']",
            ".login-error",
        ]

        for selector in error_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible(timeout=2000):
                    error_text = element.text_content() or ""
                    if error_text:
                        return error_text.strip()
            except:
                continue

        return None