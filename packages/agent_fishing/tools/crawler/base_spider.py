"""
基础爬虫类和数据结构定义
"""

import time
import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import requests
from requests import Response

from .anti_crawler import UserAgentRotator, RequestThrottler

logger = logging.getLogger(__name__)


@dataclass
class EquipmentData:
    """爬取的装备数据结构"""

    name: str  # 装备名称
    category: str  # 类别（鱼竿/渔轮/鱼线/拟饵）
    brand_name: str  # 品牌名称
    model: Optional[str] = None  # 型号
    price_min: float = 0.0  # 最低价格
    price_max: Optional[float] = None  # 最高价格
    description: Optional[str] = None  # 描述
    features: Optional[str] = None  # 特性（JSON字符串）
    target_fish: Optional[str] = None  # 目标鱼种
    user_level: Optional[str] = None  # 用户水平（新手/进阶/高手）
    source_url: str = ""  # 来源URL
    images: List[Dict[str, str]] = field(default_factory=list)  # [{"url": "...", "type": "main/detail"}]
    specs: Dict[str, Any] = field(default_factory=dict)  # 规格参数（根据category不同）

    def __post_init__(self):
        """数据验证"""
        if not self.name:
            raise ValueError("装备名称不能为空")
        if self.category not in ["鱼竿", "渔轮", "鱼线", "拟饵"]:
            raise ValueError(f"不支持的装备类别: {self.category}")
        if not self.brand_name:
            raise ValueError("品牌名称不能为空")
        if self.price_min < 0:
            raise ValueError("价格不能为负数")
        if self.price_max and self.price_max < self.price_min:
            raise ValueError("最高价格不能低于最低价格")


class BaseSpider(ABC):
    """基础爬虫类"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化爬虫

        Args:
            config: 配置字典
                - request_delay: 请求延迟（秒，默认2）
                - max_retries: 最大重试次数（默认3）
                - timeout: 超时时间（秒，默认30）
        """
        config = config or {}
        self.request_delay = config.get("request_delay", 2)
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 30)

        # 初始化反爬虫组件
        self.ua_rotator = UserAgentRotator()
        self.throttler = RequestThrottler(
            min_delay=max(1.0, self.request_delay - 1),
            max_delay=self.request_delay + 3,
        )

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_results": 0,
        }

        logger.info(
            f"初始化爬虫: {self.__class__.__name__}, "
            f"延迟={self.request_delay}s, 重试={self.max_retries}, 超时={self.timeout}s"
        )

    @abstractmethod
    def search_equipment(
        self, keyword: str, category: Optional[str] = None, max_results: int = 50
    ) -> List[EquipmentData]:
        """
        搜索装备

        Args:
            keyword: 搜索关键词
            category: 装备类别（鱼竿/渔轮/鱼线/拟饵）
            max_results: 最大结果数量

        Returns:
            装备数据列表
        """
        pass

    @abstractmethod
    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        获取商品详情

        Args:
            product_url: 商品URL

        Returns:
            装备数据，如果失败返回None
        """
        pass

    def fetch_with_retry(
        self, url: str, method: str = "GET", **kwargs
    ) -> Optional[Response]:
        """
        带重试的HTTP请求

        Args:
            url: 请求URL
            method: 请求方法（GET/POST）
            **kwargs: requests请求参数

        Returns:
            Response对象，如果失败返回None
        """
        # 更新统计
        self.stats["total_requests"] += 1

        # 请求前延迟
        self.throttler.wait()

        # 合并headers（UA轮换）
        headers = kwargs.get("headers", {})
        headers.update(self.ua_rotator.get_headers(referer=kwargs.pop("referer", None)))
        kwargs["headers"] = headers

        # 设置超时
        kwargs.setdefault("timeout", self.timeout)

        # 重试逻辑
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"请求 [{attempt}/{self.max_retries}]: {method} {url}")

                if method.upper() == "GET":
                    response = requests.get(url, **kwargs)
                elif method.upper() == "POST":
                    response = requests.post(url, **kwargs)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")

                response.raise_for_status()
                self.stats["successful_requests"] += 1
                logger.debug(f"请求成功: {url} (状态码: {response.status_code})")
                return response

            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP错误 [{attempt}/{self.max_retries}]: {e}")
                if response.status_code in [404, 403, 401]:
                    # 不重试的错误
                    break
                if attempt < self.max_retries:
                    # 指数退避
                    backoff = 2 ** (attempt - 1)
                    logger.info(f"等待 {backoff}秒 后重试...")
                    time.sleep(backoff)

            except requests.exceptions.Timeout as e:
                logger.warning(f"请求超时 [{attempt}/{self.max_retries}]: {e}")
                if attempt < self.max_retries:
                    time.sleep(1)

            except requests.exceptions.RequestException as e:
                logger.error(f"请求失败 [{attempt}/{self.max_retries}]: {e}")
                if attempt < self.max_retries:
                    time.sleep(1)

        # 所有重试失败
        self.stats["failed_requests"] += 1
        logger.error(f"请求最终失败: {url}")
        return None

    def get_stats(self) -> Dict[str, Any]:
        """获取爬虫统计信息"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_results": 0,
        }
        logger.info("统计信息已重置")
