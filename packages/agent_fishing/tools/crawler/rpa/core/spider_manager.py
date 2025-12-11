"""Enhanced Spider Manager with improved error handling and monitoring"""

import logging
import time
import random
from typing import Optional, Dict, List, Any, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import traceback
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class BrowserType(Enum):
    """Supported browser types"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@dataclass
class BrowserConfig:
    """Browser configuration"""
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    timeout: int = 30000
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    user_agent: Optional[str] = None
    locale: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    enable_stealth: bool = True
    slow_mo: int = 0
    args: List[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--start-maximized",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # For faster loading
        "--disable-javascript",  # Can be enabled when needed
    ])


@dataclass
class OperationMetrics:
    """Operation metrics for monitoring"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0
    pages_visited: int = 0
    items_extracted: int = 0
    screenshots_taken: int = 0
    duration: Optional[float] = None

    def end(self, success: bool, error_message: Optional[str] = None):
        """Mark operation as ended"""
        self.end_time = datetime.now()
        self.success = success
        self.error_message = error_message
        self.duration = (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "success": self.success,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "pages_visited": self.pages_visited,
            "items_extracted": self.items_extracted,
            "screenshots_taken": self.screenshots_taken,
            "duration": self.duration,
        }


class SpiderManager:
    """Enhanced spider manager with monitoring and error recovery"""

    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        Initialize spider manager

        Args:
            config: Browser configuration
        """
        self.config = config or BrowserConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Browser objects
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Metrics tracking
        self.metrics: List[OperationMetrics] = []
        self.current_operation: Optional[OperationMetrics] = None

        # Error handling
        self.error_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

        # Monitoring
        self.screenshots_dir = Path("shared/data/screenshots")
        self.logs_dir = Path("shared/data/logs")
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _register_default_handlers(self):
        """Register default error handlers"""
        self.error_handlers.update({
            "timeout": self._handle_timeout_error,
            "network": self._handle_network_error,
            "blocked": self._handle_blocked_error,
            "captcha": self._handle_captcha_error,
            "element_not_found": self._handle_element_error,
            "javascript": self._handle_javascript_error,
        })

    @contextmanager
    def browser_session(self):
        """
        Context manager for browser session

        Yields:
            Page object for operations
        """
        try:
            self._start_browser()
            yield self.page
        finally:
            self._stop_browser()

    def _start_browser(self):
        """Start browser with configuration"""
        if self.browser is not None:
            self.logger.warning("Browser already started")
            return

        try:
            self.logger.info(f"Starting {self.config.browser_type.value} browser...")
            self.playwright = sync_playwright().start()

            # Get browser launcher
            launcher = getattr(self.playwright, self.config.browser_type.value)

            # Launch browser
            launch_options = {
                "headless": self.config.headless,
                "slow_mo": self.config.slow_mo,
                "args": self.config.args,
            }

            # Try to use system Chrome for Chromium
            if self.config.browser_type == BrowserType.CHROMIUM:
                try:
                    launch_options["channel"] = "chrome"
                    self.browser = launcher.launch(**launch_options)
                    self.logger.info("✅ Using system Chrome")
                except Exception as e:
                    self.logger.warning(f"Failed to use system Chrome: {e}")
                    self.logger.info("Falling back to Playwright Chromium")
                    launch_options.pop("channel", None)
                    self.browser = launcher.launch(**launch_options)
            else:
                self.browser = launcher.launch(**launch_options)

            # Create context
            context_options = {
                "viewport": self.config.viewport,
                "locale": self.config.locale,
                "timezone_id": self.config.timezone,
            }

            if self.config.user_agent:
                context_options["user_agent"] = self.config.user_agent

            self.context = self.browser.new_context(**context_options)

            # Add stealth scripts if enabled
            if self.config.enable_stealth:
                self._add_stealth_scripts()

            # Create page
            self.page = self.context.new_page()
            self.page.set_default_timeout(self.config.timeout)

            # Add event listeners
            self._add_event_listeners()

            self.logger.info(f"Browser started successfully (headless={self.config.headless})")

        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}", exc_info=True)
            self._cleanup()
            raise

    def _add_stealth_scripts(self):
        """Add stealth scripts to avoid detection"""
        stealth_script = """
        // Remove webdriver traces
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Mock chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin'},
                {name: 'Chrome PDF Viewer'},
                {name: 'Native Client'}
            ]
        });

        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en-US', 'en']
        });

        // Override permissions query
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // Remove automation indicators
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """

        self.context.add_init_script(stealth_script)
        self.logger.debug("Stealth scripts added")

    def _add_event_listeners(self):
        """Add event listeners for monitoring"""
        if not self.page:
            return

        # Log console messages
        def log_console(msg):
            if msg.type == "error":
                self.logger.error(f"Console error: {msg.text}")
            elif msg.type == "warning":
                self.logger.warning(f"Console warning: {msg.text}")

        self.page.on("console", log_console)

        # Log page errors
        def log_page_error(error):
            self.logger.error(f"Page error: {error}")

        self.page.on("pageerror", log_page_error)

        # Track navigation
        def log_navigation(request):
            if request.is_navigation_request():
                self.logger.debug(f"Navigating to: {request.url}")

        self.page.on("request", log_navigation)

    def _stop_browser(self):
        """Stop browser and cleanup resources"""
        try:
            if self.page:
                self.page.close()
                self.page = None

            if self.context:
                self.context.close()
                self.context = None

            if self.browser:
                self.browser.close()
                self.browser = None

            if self.playwright:
                self.playwright.stop()
                self.playwright = None

            self.logger.info("Browser stopped successfully")

        except Exception as e:
            self.logger.error(f"Error stopping browser: {e}")

    def _cleanup(self):
        """Cleanup all resources"""
        self._stop_browser()

    def start_operation(self, name: str) -> str:
        """
        Start tracking an operation

        Args:
            name: Operation name

        Returns:
            Operation ID
        """
        operation_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_operation = OperationMetrics()
        self.logger.info(f"Started operation: {operation_id}")
        return operation_id

    def end_operation(self, success: bool, error_message: Optional[str] = None):
        """End current operation tracking"""
        if self.current_operation:
            self.current_operation.end(success, error_message)
            self.metrics.append(self.current_operation)

            if success:
                self.logger.info(
                    f"Operation completed successfully in {self.current_operation.duration:.2f}s"
                )
            else:
                self.logger.error(
                    f"Operation failed after {self.current_operation.duration:.2f}s: {error_message}"
                )

            # Save metrics
            self._save_metrics()

            self.current_operation = None

    def _save_metrics(self):
        """Save operation metrics to file"""
        try:
            metrics_file = self.logs_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            metrics_data = [m.to_dict() for m in self.metrics]

            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    def take_screenshot(self, name: Optional[str] = None, full_page: bool = False) -> Optional[str]:
        """
        Take a screenshot with metadata

        Args:
            name: Screenshot name
            full_page: Whether to capture full page

        Returns:
            Screenshot path or None
        """
        if not self.page:
            self.logger.warning("No page available for screenshot")
            return None

        try:
            if not name:
                name = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            filename = f"{name}.png"
            filepath = self.screenshots_dir / filename

            self.page.screenshot(path=str(filepath), full_page=full_page)

            # Update metrics
            if self.current_operation:
                self.current_operation.screenshots_taken += 1

            self.logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None

    def simulate_human_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add random delay to simulate human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        self.logger.debug(f"Human delay: {delay:.2f}s")

    def execute_with_retry(
        self,
        operation: Callable,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        error_types: tuple = (Exception,),
    ):
        """
        Execute operation with retry logic

        Args:
            operation: Operation to execute
            max_retries: Maximum retry attempts
            backoff_factor: Backoff multiplier
            error_types: Error types to retry on

        Returns:
            Operation result
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                self.logger.debug(f"Executing operation (attempt {attempt}/{max_retries})")
                result = operation()

                # Update retry count in metrics
                if self.current_operation and attempt > 1:
                    self.current_operation.retry_count += 1

                return result

            except error_types as e:
                last_error = e
                self.logger.warning(f"Operation failed (attempt {attempt}/{max_retries}): {e}")

                if attempt < max_retries:
                    # Calculate backoff delay
                    delay = backoff_factor ** (attempt - 1)
                    self.logger.info(f"Retrying in {delay:.2f}s...")
                    time.sleep(delay)

                    # Try to handle specific error types
                    error_type = self._classify_error(e)
                    if error_type in self.error_handlers:
                        try:
                            self.error_handlers[error_type](e)
                        except Exception as handler_error:
                            self.logger.error(f"Error handler failed: {handler_error}")

                else:
                    self.logger.error(f"Operation failed after {max_retries} attempts")

        raise last_error

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for handling"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        if "timeout" in error_str or "time out" in error_str:
            return "timeout"
        elif "network" in error_str or "connection" in error_str:
            return "network"
        elif "blocked" in error_str or "forbidden" in error_str or "403" in error_str:
            return "blocked"
        elif "captcha" in error_str or "verification" in error_str:
            return "captcha"
        elif "element" in error_str or "selector" in error_str:
            return "element_not_found"
        elif "javascript" in error_str or "js" in error_str:
            return "javascript"
        else:
            return "unknown"

    # Error handlers
    def _handle_timeout_error(self, error: Exception):
        """Handle timeout errors"""
        self.logger.warning("Handling timeout error...")
        self.take_screenshot("timeout_error")
        self.simulate_human_delay(3, 5)

    def _handle_network_error(self, error: Exception):
        """Handle network errors"""
        self.logger.warning("Handling network error...")
        # Try to reload the page
        if self.page:
            self.page.reload(wait_until="domcontentloaded")
            self.simulate_human_delay(2, 4)

    def _handle_blocked_error(self, error: Exception):
        """Handle blocked/captcha errors"""
        self.logger.warning("Handling blocked error...")
        self.take_screenshot("blocked_error")
        # Could implement proxy rotation here
        self.simulate_human_delay(10, 20)

    def _handle_captcha_error(self, error: Exception):
        """Handle captcha errors"""
        self.logger.warning("Handling captcha error...")
        self.take_screenshot("captcha_error")
        # Could integrate with captcha solving service
        raise error  # Re-raise for manual intervention

    def _handle_element_error(self, error: Exception):
        """Handle element not found errors"""
        self.logger.warning("Handling element error...")
        # Try to refresh the page
        if self.page:
            self.page.evaluate("window.scrollTo(0, 0)")
            self.simulate_human_delay(1, 2)

    def _handle_javascript_error(self, error: Exception):
        """Handle JavaScript errors"""
        self.logger.warning("Handling JavaScript error...")
        # Continue but log for debugging
        self.logger.debug(f"JavaScript error details: {traceback.format_exc()}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        if not self.metrics:
            return {}

        total_operations = len(self.metrics)
        successful_operations = sum(1 for m in self.metrics if m.success)
        failed_operations = total_operations - successful_operations

        total_duration = sum(m.duration or 0 for m in self.metrics)
        avg_duration = total_duration / total_operations if total_operations > 0 else 0

        total_items = sum(m.items_extracted for m in self.metrics)

        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "total_items_extracted": total_items,
            "total_screenshots": sum(m.screenshots_taken for m in self.metrics),
        }