"""
RPA爬虫配置类
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RPAConfig:
    """RPA爬虫配置"""

    # 浏览器配置
    headless: bool = True
    browser_type: str = "chromium"  # chromium | firefox | webkit
    timeout: int = 30000  # 毫秒

    # 登录配置
    cookie_path: str = "shared/data/cookies/taobao_session.json"

    # 验证码配置
    captcha_solver: str = "manual"  # manual | api

    # 反爬虫配置
    enable_stealth: bool = True
    simulate_human: bool = True
    request_delay: int = 3  # 秒
    max_retries: int = 3
    page_timeout: int = 30  # 秒

    # 滚动配置
    scroll_step_min: float = 0.8  # 最小滚动步长（视窗高度倍数）
    scroll_step_max: float = 1.5  # 最大滚动步长（视窗高度倍数）
    scroll_wait_min: float = 1.5  # 最小等待时间（秒）
    scroll_wait_max: float = 2.5  # 最大等待时间（秒）
    scroll_max_attempts: int = 50  # 最大滚动尝试次数
    scroll_completion_threshold: int = 5  # 完成检测阈值

    # 店铺配置
    shop_config_path: str = "shared/data/shops/shops.json"
    shop_max_items_per_category: int = 100

    @classmethod
    def from_env(cls) -> "RPAConfig":
        """从环境变量加载配置"""

        def str_to_bool(s: str) -> bool:
            """字符串转布尔值"""
            return s.lower() in ("true", "1", "yes")

        return cls(
            # 浏览器配置
            headless=str_to_bool(os.getenv("PLAYWRIGHT_HEADLESS", "true")),
            browser_type=os.getenv("PLAYWRIGHT_BROWSER", "chromium"),
            timeout=int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000")),

            # 登录配置
            cookie_path=os.getenv(
                "TAOBAO_COOKIE_PATH",
                "shared/data/cookies/taobao_session.json"
            ),

            # 验证码配置
            captcha_solver=os.getenv("CAPTCHA_SOLVER_TYPE", "manual"),

            # 反爬虫配置
            enable_stealth=str_to_bool(os.getenv("RPA_ENABLE_STEALTH", "true")),
            simulate_human=str_to_bool(os.getenv("RPA_SIMULATE_HUMAN", "true")),
            request_delay=int(os.getenv("TAOBAO_RPA_REQUEST_DELAY", "3")),
            max_retries=int(os.getenv("TAOBAO_RPA_MAX_RETRIES", "3")),
            page_timeout=int(os.getenv("TAOBAO_RPA_PAGE_TIMEOUT", "30")),

            # 店铺配置
            shop_config_path=os.getenv(
                "TAOBAO_SHOP_CONFIG_PATH",
                "shared/data/shops/shops.json"
            ),
            shop_max_items_per_category=int(
                os.getenv("TAOBAO_SHOP_MAX_ITEMS_PER_CATEGORY", "100")
            ),
        )

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"RPAConfig("
            f"headless={self.headless}, "
            f"browser_type={self.browser_type}, "
            f"request_delay={self.request_delay}s, "
            f"enable_stealth={self.enable_stealth})"
        )
