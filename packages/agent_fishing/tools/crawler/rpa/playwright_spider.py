"""
Playwright RPA 爬虫基类
"""

import time
import random
import logging
from typing import Optional, List
from abc import ABC

from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError,
)

from ..base_spider import BaseSpider
from .config import RPAConfig

logger = logging.getLogger(__name__)


class PlaywrightSpider(BaseSpider, ABC):
    """基于 Playwright 的 RPA 爬虫基类"""

    def __init__(self, config: Optional[dict] = None):
        """
        初始化 Playwright 爬虫

        Args:
            config: 配置字典（兼容 BaseSpider）
        """
        # 调用父类初始化
        super().__init__(config)

        # 加载 RPA 配置
        self.rpa_config = RPAConfig.from_env()

        # Playwright 对象（延迟初始化）
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        logger.info(f"初始化 Playwright 爬虫: {self.rpa_config}")

    def __enter__(self):
        """上下文管理器：启动浏览器"""
        self._start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：关闭浏览器"""
        self._stop_browser()

    def _start_browser(self):
        """启动 Playwright 浏览器"""
        if self.playwright is not None:
            logger.warning("浏览器已启动，跳过重复启动")
            return

        try:
            logger.info(f"启动 {self.rpa_config.browser_type} 浏览器...")
            self.playwright = sync_playwright().start()

            # 选择浏览器类型
            if self.rpa_config.browser_type == "chromium":
                browser_launcher = self.playwright.chromium
            elif self.rpa_config.browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif self.rpa_config.browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                raise ValueError(f"不支持的浏览器类型: {self.rpa_config.browser_type}")

            # 启动浏览器（优先使用系统 Chrome）
            try:
                self.browser = browser_launcher.launch(
                    headless=self.rpa_config.headless,
                    channel="chrome",  # 使用系统 Chrome 浏览器
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ]
                )
                logger.info("✅ 使用系统 Chrome 浏览器")
            except Exception as e:
                # 回退到 Playwright 自带浏览器
                logger.warning(f"无法使用系统 Chrome，使用 Playwright 浏览器: {e}")
                logger.info("提示：如需使用 Playwright 浏览器，请运行: uv run playwright install chromium")
                self.browser = browser_launcher.launch(
                    headless=self.rpa_config.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ]
                )

            # 创建浏览器上下文
            self.context = self._create_context()

            # 创建页面
            self.page = self.context.new_page()
            logger.debug("页面创建成功")

            logger.info(f"浏览器启动成功 (headless={self.rpa_config.headless})")

        except Exception as e:
            logger.error(f"浏览器启动失败: {e}", exc_info=True)
            raise

    def _stop_browser(self):
        """关闭 Playwright 浏览器"""
        try:
            if self.page:
                self.page.close()
                self.page = None
                logger.debug("页面已关闭")

            if self.context:
                self.context.close()
                self.context = None
                logger.debug("浏览器上下文已关闭")

            if self.browser:
                self.browser.close()
                self.browser = None
                logger.debug("浏览器已关闭")

            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                logger.debug("Playwright 已停止")

        except Exception as e:
            logger.error(f"浏览器关闭失败: {e}", exc_info=True)

    def _create_context(self) -> BrowserContext:
        """
        创建隐蔽的浏览器上下文

        Returns:
            BrowserContext 对象
        """
        # 创建上下文
        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=self.ua_rotator.get_random_ua(),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            permissions=["geolocation"],
            color_scheme="light",
        )

        # 注入反检测脚本
        if self.rpa_config.enable_stealth:
            context.add_init_script("""
                // 隐藏 webdriver 特征
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // 模拟 chrome 对象
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };

                // 模拟插件
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin'},
                        {name: 'Chrome PDF Viewer'},
                        {name: 'Native Client'}
                    ]
                });

                // 模拟语言
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en']
                });

                // 模拟 permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

        logger.debug("浏览器上下文创建成功（已注入反检测脚本）")
        return context

    def safe_goto(self, page: Page, url: str, max_retries: Optional[int] = None) -> bool:
        """
        安全导航到页面（带重试）

        Args:
            page: Page 对象
            url: 目标 URL
            max_retries: 最大重试次数（默认使用配置）

        Returns:
            是否成功
        """
        max_retries = max_retries or self.rpa_config.max_retries

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"导航到页面 [{attempt}/{max_retries}]: {url}")

                page.goto(
                    url,
                    timeout=self.rpa_config.timeout,
                    wait_until="domcontentloaded"  # 更快的等待策略
                )

                logger.debug(f"页面加载成功: {url}")
                return True

            except TimeoutError:
                logger.warning(f"页面加载超时 [{attempt}/{max_retries}]: {url}")
                if attempt < max_retries:
                    backoff = 2 ** attempt
                    logger.info(f"等待 {backoff}秒 后重试...")
                    time.sleep(backoff)

            except Exception as e:
                logger.error(f"页面加载失败 [{attempt}/{max_retries}]: {e}")
                if attempt < max_retries:
                    time.sleep(2)

        logger.error(f"页面加载最终失败: {url}")
        return False

    def safe_query_selector(
        self,
        page: Page,
        selector: str,
        timeout: Optional[int] = None
    ) -> Optional[any]:
        """
        安全查询元素

        Args:
            page: Page 对象
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            元素对象或 None
        """
        timeout = timeout or 10000

        try:
            page.wait_for_selector(selector, timeout=timeout)
            return page.locator(selector).first
        except TimeoutError:
            logger.warning(f"元素定位超时: {selector}")
            return None
        except Exception as e:
            logger.error(f"元素定位失败: {e}")
            return None

    def _simulate_scroll(self, page: Page):
        """
        模拟人类滚动行为

        Args:
            page: Page 对象
        """
        if not self.rpa_config.simulate_human:
            return

        try:
            # 随机滚动次数
            scroll_times = random.randint(2, 5)

            for _ in range(scroll_times):
                # 随机滚动距离
                distance = random.randint(300, 800)
                page.mouse.wheel(0, distance)

                # 随机停顿
                time.sleep(random.uniform(0.5, 1.5))

            # 随机鼠标移动
            page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600),
                steps=random.randint(10, 30)
            )

            # 最终停顿
            time.sleep(random.uniform(1, 3))

            logger.debug("完成人类行为模拟（滚动）")

        except Exception as e:
            logger.warning(f"人类行为模拟失败: {e}")

    def _detect_rate_limit(self, page: Page) -> bool:
        """
        检测是否被限流

        Args:
            page: Page 对象

        Returns:
            是否被限流
        """
        try:
            content = page.content()

            # 检测反爬虫关键词
            rate_limit_keywords = [
                "访问过于频繁",
                "请稍后再试",
                "系统繁忙",
                "验证码",
                "请输入验证码",
            ]

            for keyword in rate_limit_keywords:
                if keyword in content:
                    logger.warning(f"检测到反爬虫响应: {keyword}")

                    # 自动降速：延迟翻倍
                    self.throttler.min_delay *= 2
                    self.throttler.max_delay *= 2

                    logger.info(
                        f"自动降速：延迟调整为 "
                        f"{self.throttler.min_delay}-{self.throttler.max_delay}秒"
                    )

                    return True

            return False

        except Exception as e:
            logger.warning(f"限流检测失败: {e}")
            return False
