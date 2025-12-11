"""Configuration validation and type hints for RPA crawler"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Literal
from dataclasses import dataclass, field, fields
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class BrowserType(str, Enum):
    """Supported browser types"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class CaptchaSolverType(str, Enum):
    """Supported captcha solver types"""
    MANUAL = "manual"
    API = "api"
    AUTO = "auto"


@dataclass
class BrowserConfig:
    """Browser configuration with validation"""
    # Required fields
    headless: bool = True
    browser_type: BrowserType = BrowserType.CHROMIUM
    timeout: int = 30000  # milliseconds

    # Optional fields with defaults
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    locale: str = "zh-CN"
    timezone_id: str = "Asia/Shanghai"
    enable_stealth: bool = True
    slow_mo: int = 0  # milliseconds between Playwright operations

    # Browser launch arguments
    launch_args: List[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--start-maximized",
        "--disable-extensions",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
    ])

    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate()

    def _validate(self):
        """Validate browser configuration"""
        # Validate timeout
        if self.timeout < 1000:
            raise ValueError(f"Timeout must be at least 1000ms, got {self.timeout}")

        # Validate viewport
        if self.viewport_width < 800 or self.viewport_height < 600:
            raise ValueError("Viewport must be at least 800x600")

        # Validate browser type
        if self.browser_type not in BrowserType:
            raise ValueError(f"Invalid browser type: {self.browser_type}")

        # Validate locale format
        if not self.locale or "-" not in self.locale:
            raise ValueError(f"Invalid locale format: {self.locale}")

        # Validate timezone
        if not self.timezone_id or "/" not in self.timezone_id:
            raise ValueError(f"Invalid timezone format: {self.timezone_id}")


@dataclass
class LoginConfig:
    """Login configuration"""
    cookie_path: str = "shared/data/cookies/taobao_session.json"
    session_timeout: int = 86400  # 24 hours in seconds
    auto_login: bool = True
    max_login_attempts: int = 3
    qr_code_timeout: int = 300  # seconds

    def __post_init__(self):
        """Validate login configuration"""
        self._validate()

    def _validate(self):
        """Validate login configuration"""
        # Validate cookie path
        cookie_dir = Path(self.cookie_path).parent
        if not cookie_dir.exists():
            try:
                cookie_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create cookie directory: {e}")

        # Validate timeouts
        if self.session_timeout < 60:
            raise ValueError("Session timeout must be at least 60 seconds")

        if self.max_login_attempts < 1:
            raise ValueError("Max login attempts must be at least 1")

        if self.qr_code_timeout < 30:
            raise ValueError("QR code timeout must be at least 30 seconds")


@dataclass
class AntiDetectionConfig:
    """Anti-detection configuration"""
    enable_stealth: bool = True
    random_user_agent: bool = True
    simulate_mouse_movement: bool = True
    simulate_typing: bool = True
    random_delays: bool = True
    min_delay: float = 0.5  # seconds
    max_delay: float = 3.0  # seconds
    proxy_rotation: bool = False
    proxy_list: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate anti-detection configuration"""
        self._validate()

    def _validate(self):
        """Validate anti-detection configuration"""
        if self.min_delay < 0 or self.max_delay < 0:
            raise ValueError("Delays must be positive")

        if self.min_delay >= self.max_delay:
            raise ValueError("min_delay must be less than max_delay")

        if self.proxy_rotation and not self.proxy_list:
            raise ValueError("Proxy rotation enabled but no proxy list provided")


@dataclass
class CrawlConfig:
    """Crawling configuration"""
    max_retries: int = 3
    retry_delay: float = 2.0  # seconds
    max_pages_per_shop: int = 20
    max_items_per_page: int = 100
    scroll_to_load: bool = True
    max_scrolls: int = 50
    scroll_wait: float = 2.0  # seconds
    page_load_timeout: int = 30  # seconds
    element_wait_timeout: int = 10  # seconds

    def __post_init__(self):
        """Validate crawl configuration"""
        self._validate()

    def _validate(self):
        """Validate crawl configuration"""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")

        if self.max_pages_per_shop < 1:
            raise ValueError("max_pages_per_shop must be at least 1")

        if self.max_items_per_page < 1:
            raise ValueError("max_items_per_page must be at least 1")


@dataclass
class CaptchaConfig:
    """Captcha handling configuration"""
    solver_type: CaptchaSolverType = CaptchaSolverType.MANUAL
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    timeout: int = 60  # seconds
    max_attempts: int = 3
    screenshot_path: str = "shared/data/screenshots/captcha"

    def __post_init__(self):
        """Validate captcha configuration"""
        self._validate()

    def _validate(self):
        """Validate captcha configuration"""
        if self.solver_type == CaptchaSolverType.API:
            if not self.api_key:
                raise ValueError("API key required for API captcha solver")
            if not self.api_url:
                raise ValueError("API URL required for API captcha solver")

        # Create screenshot directory
        screenshot_dir = Path(self.screenshot_path)
        if not screenshot_dir.exists():
            try:
                screenshot_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create screenshot directory: {e}")


@dataclass
class RPAConfigV2:
    """Main RPA configuration with all sub-configurations"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    login: LoginConfig = field(default_factory=LoginConfig)
    anti_detection: AntiDetectionConfig = field(default_factory=AntiDetectionConfig)
    crawl: CrawlConfig = field(default_factory=CrawlConfig)
    captcha: CaptchaConfig = field(default_factory=CaptchaConfig)

    # Legacy compatibility
    @property
    def headless(self) -> bool:
        """Legacy headless property"""
        return self.browser.headless

    @headless.setter
    def headless(self, value: bool):
        """Legacy headless setter"""
        self.browser.headless = value

    @property
    def timeout(self) -> int:
        """Legacy timeout property"""
        return self.browser.timeout

    @timeout.setter
    def timeout(self, value: int):
        """Legacy timeout setter"""
        self.browser.timeout = value

    @classmethod
    def from_env(cls) -> "RPAConfigV2":
        """Load configuration from environment variables"""
        # Browser configuration
        browser_config = BrowserConfig(
            headless=os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("true", "1", "yes"),
            browser_type=BrowserType(os.getenv("PLAYWRIGHT_BROWSER", "chromium")),
            timeout=int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000")),
            viewport_width=int(os.getenv("PLAYWRIGHT_VIEWPORT_WIDTH", "1920")),
            viewport_height=int(os.getenv("PLAYWRIGHT_VIEWPORT_HEIGHT", "1080")),
            locale=os.getenv("PLAYWRIGHT_LOCALE", "zh-CN"),
            timezone_id=os.getenv("PLAYWRIGHT_TIMEZONE", "Asia/Shanghai"),
            enable_stealth=os.getenv("RPA_ENABLE_STEALTH", "true").lower() in ("true", "1", "yes"),
        )

        # Login configuration
        login_config = LoginConfig(
            cookie_path=os.getenv("TAOBAO_COOKIE_PATH", "shared/data/cookies/taobao_session.json"),
            session_timeout=int(os.getenv("TAOBAO_SESSION_TIMEOUT", "86400")),
            auto_login=os.getenv("TAOBAO_AUTO_LOGIN", "true").lower() in ("true", "1", "yes"),
            max_login_attempts=int(os.getenv("TAOBAO_MAX_LOGIN_ATTEMPTS", "3")),
            qr_code_timeout=int(os.getenv("TAOBAO_QR_TIMEOUT", "300")),
        )

        # Anti-detection configuration
        anti_detection_config = AntiDetectionConfig(
            enable_stealth=os.getenv("RPA_ENABLE_STEALTH", "true").lower() in ("true", "1", "yes"),
            random_user_agent=os.getenv("RPA_RANDOM_UA", "true").lower() in ("true", "1", "yes"),
            simulate_mouse_movement=os.getenv("RPA_SIMULATE_MOUSE", "true").lower() in ("true", "1", "yes"),
            simulate_typing=os.getenv("RPA_SIMULATE_TYPING", "true").lower() in ("true", "1", "yes"),
            random_delays=os.getenv("RPA_RANDOM_DELAYS", "true").lower() in ("true", "1", "yes"),
            min_delay=float(os.getenv("RPA_MIN_DELAY", "0.5")),
            max_delay=float(os.getenv("RPA_MAX_DELAY", "3.0")),
        )

        # Crawl configuration
        crawl_config = CrawlConfig(
            max_retries=int(os.getenv("RPA_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RPA_RETRY_DELAY", "2.0")),
            max_pages_per_shop=int(os.getenv("TAOBAO_MAX_PAGES", "20")),
            max_items_per_page=int(os.getenv("TAOBAO_MAX_ITEMS_PER_PAGE", "100")),
            scroll_to_load=os.getenv("RPA_SCROLL_TO_LOAD", "true").lower() in ("true", "1", "yes"),
            max_scrolls=int(os.getenv("RPA_MAX_SCROLLS", "50")),
            scroll_wait=float(os.getenv("RPA_SCROLL_WAIT", "2.0")),
            page_load_timeout=int(os.getenv("RPA_PAGE_LOAD_TIMEOUT", "30")),
            element_wait_timeout=int(os.getenv("RPA_ELEMENT_WAIT_TIMEOUT", "10")),
        )

        # Captcha configuration
        captcha_config = CaptchaConfig(
            solver_type=CaptchaSolverType(os.getenv("CAPTCHA_SOLVER_TYPE", "manual")),
            api_key=os.getenv("CAPTCHA_API_KEY"),
            api_url=os.getenv("CAPTCHA_API_URL"),
            timeout=int(os.getenv("CAPTCHA_TIMEOUT", "60")),
            max_attempts=int(os.getenv("CAPTCHA_MAX_ATTEMPTS", "3")),
            screenshot_path=os.getenv("CAPTCHA_SCREENSHOT_PATH", "shared/data/screenshots/captcha"),
        )

        return cls(
            browser=browser_config,
            login=login_config,
            anti_detection=anti_detection_config,
            crawl=crawl_config,
            captcha=captcha_config,
        )

    def validate_all(self) -> List[str]:
        """
        Validate all configurations

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            self.browser._validate()
        except ValueError as e:
            errors.append(f"Browser config: {e}")

        try:
            self.login._validate()
        except ValueError as e:
            errors.append(f"Login config: {e}")

        try:
            self.anti_detection._validate()
        except ValueError as e:
            errors.append(f"Anti-detection config: {e}")

        try:
            self.crawl._validate()
        except ValueError as e:
            errors.append(f"Crawl config: {e}")

        try:
            self.captcha._validate()
        except ValueError as e:
            errors.append(f"Captcha config: {e}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "browser": self.browser.__dict__,
            "login": self.login.__dict__,
            "anti_detection": self.anti_detection.__dict__,
            "crawl": self.crawl.__dict__,
            "captcha": self.captcha.__dict__,
        }

    def save_to_file(self, filepath: Union[str, Path]):
        """Save configuration to JSON file"""
        filepath = Path(filepath)
        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"Configuration saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

    @classmethod
    def load_from_file(cls, filepath: Union[str, Path]) -> "RPAConfigV2":
        """Load configuration from JSON file"""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")

        try:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reconstruct configuration objects
            browser_config = BrowserConfig(**data.get("browser", {}))
            login_config = LoginConfig(**data.get("login", {}))
            anti_detection_config = AntiDetectionConfig(**data.get("anti_detection", {}))
            crawl_config = CrawlConfig(**data.get("crawl", {}))
            captcha_config = CaptchaConfig(**data.get("captcha", {}))

            return cls(
                browser=browser_config,
                login=login_config,
                anti_detection=anti_detection_config,
                crawl=crawl_config,
                captcha=captcha_config,
            )
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise


# Configuration validator utility functions
def validate_config_file(filepath: Union[str, Path]) -> List[str]:
    """
    Validate a configuration file

    Args:
        filepath: Path to configuration file

    Returns:
        List of validation errors
    """
    try:
        config = RPAConfigV2.load_from_file(filepath)
        return config.validate_all()
    except Exception as e:
        return [f"Failed to load configuration: {e}"]


def create_default_config(filepath: Union[str, Path]) -> bool:
    """
    Create a default configuration file

    Args:
        filepath: Path where to save the configuration

    Returns:
        True if successful, False otherwise
    """
    try:
        config = RPAConfigV2()
        config.save_to_file(filepath)
        return True
    except Exception as e:
        logger.error(f"Failed to create default configuration: {e}")
        return False