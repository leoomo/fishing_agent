"""
反爬虫策略模块

提供User-Agent轮换、请求节流等反爬虫措施。
"""

import time
import random
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class UserAgentRotator:
    """User-Agent轮换器"""

    # 真实浏览器User-Agent列表
    USER_AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        # Mobile Chrome
        "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ]

    def __init__(self):
        logger.debug(f"初始化UA轮换器，共{len(self.USER_AGENTS)}个UA")

    def get_random_ua(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.USER_AGENTS)

    def get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        生成模拟真实浏览器的请求头

        Args:
            referer: 引用页URL

        Returns:
            请求头字典
        """
        headers = {
            "User-Agent": self.get_random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        # 添加Referer（如果提供）
        if referer:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "same-origin"

        return headers


class RequestThrottler:
    """请求节流器"""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        初始化请求节流器

        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time: Optional[float] = None
        logger.debug(f"初始化请求节流器: {min_delay}s - {max_delay}s")

    def wait(self):
        """智能延迟（随机 + 自适应）"""
        # 计算随机延迟
        delay = random.uniform(self.min_delay, self.max_delay)

        # 如果有上次请求时间，确保最小间隔
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                delay = max(delay, self.min_delay - elapsed)

        # 执行延迟
        if delay > 0:
            logger.debug(f"请求延迟: {delay:.2f}秒")
            time.sleep(delay)

        # 更新请求时间
        self.last_request_time = time.time()

    def reset(self):
        """重置节流器"""
        self.last_request_time = None
        logger.debug("节流器已重置")


class ProxyRotator:
    """
    代理池轮换器（可选功能）

    当前版本保留接口，后续可扩展代理池支持。
    """

    def __init__(self, proxy_list: Optional[List[str]] = None):
        """
        初始化代理池

        Args:
            proxy_list: 代理列表（格式: ["http://proxy1:8080", "http://proxy2:8080"]）
        """
        self.proxy_list = proxy_list or []
        self.current_index = 0
        logger.info(f"初始化代理池: {len(self.proxy_list)}个代理")

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        获取下一个代理

        Returns:
            代理字典，格式: {"http": "http://proxy:8080", "https": "http://proxy:8080"}
            如果代理池为空，返回None
        """
        if not self.proxy_list:
            return None

        proxy_url = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)

        return {
            "http": proxy_url,
            "https": proxy_url,
        }

    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """获取随机代理"""
        if not self.proxy_list:
            return None

        proxy_url = random.choice(self.proxy_list)
        return {
            "http": proxy_url,
            "https": proxy_url,
        }
