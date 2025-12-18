"""Base Page Object Model for RPA automation"""

import logging
import time
from typing import Optional, List, Dict, Any, Callable, Union
from abc import ABC, abstractmethod
from playwright.sync_api import Page, Locator, TimeoutError, FrameLocator, expect
from functools import wraps
import random

logger = logging.getLogger(__name__)


def retry_operation(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (TimeoutError, Exception)
):
    """Decorator to retry operations with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(self, *args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"Operation failed after {max_attempts} attempts: {e}")
                        raise

                    wait_time = delay * (backoff ** (attempt - 1))
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)

            raise last_exception
        return wrapper
    return decorator


class BasePage(ABC):
    """Base page object with common functionality"""

    def __init__(self, page: Page, timeout: int = 30000):
        """
        Initialize base page

        Args:
            page: Playwright page object
            timeout: Default timeout in milliseconds
        """
        self.page = page
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

        # Configure default timeouts
        self.page.set_default_timeout(timeout)

    def wait_for_page_load(self, state: str = "domcontentloaded") -> None:
        """
        Wait for page to load completely

        Args:
            state: Load state to wait for ('domcontentloaded', 'load', 'networkidle')
        """
        try:
            self.page.wait_for_load_state(state, timeout=self.timeout)
            self.logger.debug(f"Page load state '{state}' reached")
        except TimeoutError:
            self.logger.warning(f"Timeout waiting for load state: {state}")

    def get_element_by_role(
        self,
        role: str,
        name: Optional[str] = None,
        exact: bool = False,
        timeout: Optional[int] = None
    ) -> Locator:
        """
        Get element by accessibility role (preferred method)

        Args:
            role: Accessibility role (button, link, textbox, etc.)
            name: Accessible name
            exact: Whether to match name exactly
            timeout: Custom timeout

        Returns:
            Element locator
        """
        try:
            kwargs = {"name": name, "exact": exact} if name is not None else {}
            return self.page.get_by_role(role, **kwargs)
        except Exception as e:
            self.logger.error(f"Failed to get element by role {role}: {e}")
            raise

    def get_element_by_text(
        self,
        text: str,
        exact: bool = False,
        timeout: Optional[int] = None
    ) -> Locator:
        """
        Get element by visible text

        Args:
            text: Text to search for
            exact: Whether to match text exactly
            timeout: Custom timeout

        Returns:
            Element locator
        """
        try:
            return self.page.get_by_text(text, exact=exact)
        except Exception as e:
            self.logger.error(f"Failed to get element by text '{text}': {e}")
            raise

    def get_element_by_label(
        self,
        label: str,
        exact: bool = False,
        timeout: Optional[int] = None
    ) -> Locator:
        """
        Get element by associated label

        Args:
            label: Label text
            exact: Whether to match label exactly
            timeout: Custom timeout

        Returns:
            Element locator
        """
        try:
            return self.page.get_by_label(label, exact=exact)
        except Exception as e:
            self.logger.error(f"Failed to get element by label '{label}': {e}")
            raise

    def get_element_by_placeholder(
        self,
        placeholder: str,
        exact: bool = False,
        timeout: Optional[int] = None
    ) -> Locator:
        """
        Get element by placeholder text

        Args:
            placeholder: Placeholder text
            exact: Whether to match placeholder exactly
            timeout: Custom timeout

        Returns:
            Element locator
        """
        try:
            return self.page.get_by_placeholder(placeholder, exact=exact)
        except Exception as e:
            self.logger.error(f"Failed to get element by placeholder '{placeholder}': {e}")
            raise

    @retry_operation(max_attempts=3, delay=1.0)
    def click_element(
        self,
        locator: Union[Locator, str],
        timeout: Optional[int] = None,
        wait_for: Optional[str] = None
    ) -> None:
        """
        Safely click an element with retry

        Args:
            locator: Element locator or selector string
            timeout: Custom timeout
            wait_for: Wait condition after click ('navigation', 'load', etc.)
        """
        if isinstance(locator, str):
            locator = self.page.locator(locator)

        # Ensure element is visible and enabled
        self.wait_for_element(locator, state="visible")

        # Click with force fallback
        try:
            locator.click(timeout=timeout or self.timeout)
            self.logger.debug(f"Successfully clicked element: {locator}")
        except TimeoutError:
            self.logger.warning(f"Click failed, trying with force: {locator}")
            locator.click(force=True, timeout=timeout or self.timeout)

        # Wait for navigation if requested
        if wait_for:
            if wait_for == "navigation":
                self.page.wait_for_load_state("networkidle")
            else:
                self.page.wait_for_load_state(wait_for)

    @retry_operation(max_attempts=3, delay=0.5)
    def type_text(
        self,
        locator: Union[Locator, str],
        text: str,
        clear_first: bool = True,
        delay: float = 50,
        timeout: Optional[int] = None
    ) -> None:
        """
        Type text into an element

        Args:
            locator: Element locator or selector string
            text: Text to type
            clear_first: Whether to clear the field first
            delay: Delay between keystrokes (ms)
            timeout: Custom timeout
        """
        if isinstance(locator, str):
            locator = self.page.locator(locator)

        # Ensure element is visible and editable
        self.wait_for_element(locator, state="visible")

        if clear_first:
            locator.clear()

        # Type with human-like delay
        locator.fill(text, timeout=timeout or self.timeout)
        self.logger.debug(f"Successfully typed text into element: {locator}")

    def wait_for_element(
        self,
        locator: Union[Locator, str],
        state: str = "visible",
        timeout: Optional[int] = None
    ) -> Locator:
        """
        Wait for element to reach specific state

        Args:
            locator: Element locator or selector string
            state: State to wait for ('visible', 'hidden', 'attached', 'detached')
            timeout: Custom timeout

        Returns:
            Element locator
        """
        if isinstance(locator, str):
            locator = self.page.locator(locator)

        wait_options = {"timeout": timeout or self.timeout}

        if state == "visible":
            locator.wait_for_element_state("visible", **wait_options)
        elif state == "hidden":
            locator.wait_for_element_state("hidden", **wait_options)
        elif state == "attached":
            locator.wait_for_element_state("attached", **wait_options)
        elif state == "detached":
            locator.wait_for_element_state("detached", **wait_options)

        return locator

    def scroll_to_element(
        self,
        locator: Union[Locator, str],
        timeout: Optional[int] = None
    ) -> None:
        """
        Scroll to make element visible

        Args:
            locator: Element locator or selector string
            timeout: Custom timeout
        """
        if isinstance(locator, str):
            locator = self.page.locator(locator)

        locator.scroll_into_view_if_needed(timeout=timeout or self.timeout)
        self.logger.debug(f"Scrolled to element: {locator}")

    def get_element_text(
        self,
        locator: Union[Locator, str],
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Get text content of an element

        Args:
            locator: Element locator or selector string
            timeout: Custom timeout

        Returns:
            Element text content or None
        """
        if isinstance(locator, str):
            locator = self.page.locator(locator)

        try:
            self.wait_for_element(locator, state="visible", timeout=timeout)
            text = locator.text_content(timeout=timeout or self.timeout)
            self.logger.debug(f"Got text from element: {locator}")
            return text.strip() if text else None
        except Exception as e:
            self.logger.error(f"Failed to get text from element: {e}")
            return None

    def get_element_attribute(
        self,
        locator: Union[Locator, str],
        attribute: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Get attribute value of an element

        Args:
            locator: Element locator or selector string
            attribute: Attribute name
            timeout: Custom timeout

        Returns:
            Attribute value or None
        """
        if isinstance(locator, str):
            locator = self.page.locator(locator)

        try:
            self.wait_for_element(locator, state="visible", timeout=timeout)
            value = locator.get_attribute(attribute, timeout=timeout or self.timeout)
            self.logger.debug(f"Got attribute '{attribute}' from element: {locator}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get attribute '{attribute}' from element: {e}")
            return None

    def is_element_visible(
        self,
        locator: Union[Locator, str],
        timeout: int = 5000
    ) -> bool:
        """
        Check if element is visible

        Args:
            locator: Element locator or selector string
            timeout: Timeout to wait for visibility

        Returns:
            True if element is visible, False otherwise
        """
        if isinstance(locator, str):
            locator = self.page.locator(locator)

        try:
            locator.wait_for_element_state("visible", timeout=timeout)
            return True
        except TimeoutError:
            return False

    def safe_click_with_multiple_strategies(
        self,
        text_or_role: str,
        element_type: str = "text",
        fallback_selectors: Optional[List[str]] = None
    ) -> bool:
        """
        Safely click an element using multiple strategies

        Args:
            text_or_role: Text to find or role name
            element_type: Type of locator ('text', 'role', 'label', 'placeholder')
            fallback_selectors: List of CSS selectors to try as fallback

        Returns:
            True if click was successful, False otherwise
        """
        strategies = []

        # Primary strategies based on element type
        if element_type == "text":
            strategies = [
                lambda: self.get_element_by_text(text_or_role).click(),
                lambda: self.get_element_by_text(text_or_role, exact=True).click(),
            ]
        elif element_type == "role":
            strategies = [
                lambda: self.get_element_by_role("button", name=text_or_role).click(),
                lambda: self.get_element_by_role("link", name=text_or_role).click(),
            ]
        elif element_type == "label":
            strategies = [
                lambda: self.get_element_by_label(text_or_role).click(),
            ]
        elif element_type == "placeholder":
            strategies = [
                lambda: self.get_element_by_placeholder(text_or_role).click(),
            ]

        # Add fallback selectors
        if fallback_selectors:
            for selector in fallback_selectors:
                strategies.append(lambda s=selector: self.page.locator(s).first.click())

        # Try each strategy
        for i, strategy in enumerate(strategies):
            try:
                strategy()
                self.logger.info(f"Successfully clicked element using strategy {i+1}")
                return True
            except Exception as e:
                self.logger.debug(f"Strategy {i+1} failed: {e}")
                continue

        self.logger.error(f"All strategies failed to click element: {text_or_role}")
        return False

    def simulate_human_behavior(
        self,
        min_delay: float = 0.5,
        max_delay: float = 2.0
    ) -> None:
        """
        Add random delay to simulate human behavior

        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        self.logger.debug(f"Human simulation delay: {delay:.2f}s")

    def handle_potential_modal(self) -> bool:
        """
        Detect and handle potential modal dialogs

        Returns:
            True if a modal was handled, False otherwise
        """
        try:
            # Check for common modal overlays
            modal_selectors = [
                "[role='dialog']",
                ".modal",
                ".popup",
                ".overlay",
                ".dialog"
            ]

            for selector in modal_selectors:
                if self.is_element_visible(selector, timeout=1000):
                    self.logger.info(f"Detected modal: {selector}")

                    # Try to find close button
                    close_strategies = [
                        lambda: self.get_element_by_role("button", name="Close").click(),
                        lambda: self.get_element_by_role("button", name="关闭").click(),
                        lambda: self.get_element_by_role("button", name="×").click(),
                        lambda: self.page.locator(selector).locator(".close").first.click(),
                        lambda: self.page.locator(selector).locator("[aria-label='Close']").first.click(),
                    ]

                    for strategy in close_strategies:
                        try:
                            strategy()
                            self.logger.info("Successfully closed modal")
                            time.sleep(0.5)
                            return True
                        except:
                            continue

                    # If no close button found, try ESC key
                    try:
                        self.page.keyboard.press("Escape")
                        self.logger.info("Closed modal with ESC key")
                        time.sleep(0.5)
                        return True
                    except:
                        pass

            return False
        except Exception as e:
            self.logger.error(f"Error handling modal: {e}")
            return False

    def take_screenshot(
        self,
        filename: Optional[str] = None,
        full_page: bool = False
    ) -> Optional[str]:
        """
        Take a screenshot for debugging

        Args:
            filename: Screenshot filename
            full_page: Whether to capture full page

        Returns:
            Screenshot path or None
        """
        try:
            from datetime import datetime

            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"

            screenshot_path = f"shared/data/screenshots/{filename}"
            self.page.screenshot(path=screenshot_path, full_page=full_page)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None