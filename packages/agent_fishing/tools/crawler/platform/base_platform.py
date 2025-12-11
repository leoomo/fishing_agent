"""
平台爬虫基类

定义统一的爬虫接口，适配不同的平台（淘宝、京东等）
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型枚举"""
    KEYWORD_SEARCH = "keyword_search"
    SHOP_CRAWL = "shop_crawl"
    CATEGORY_CRAWL = "category_crawl"
    PRODUCT_DETAIL = "product_detail"
    SHOP_ANALYZE = "shop_analyze"


@dataclass
class CrawlResult:
    """爬虫结果数据结构"""
    items: List[Dict[str, Any]]
    total_count: int
    has_more: bool
    next_page_token: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskConfig:
    """任务配置"""
    task_type: TaskType
    keywords: Optional[List[str]] = None
    shop_url: Optional[str] = None
    category_url: Optional[str] = None
    product_urls: Optional[List[str]] = None
    max_pages: int = 5
    max_items_per_page: int = 100
    delay: float = 1.0
    timeout: int = 300
    proxy: Optional[str] = None
    custom_params: Optional[Dict[str, Any]] = None


class BasePlatform(ABC):
    """
    平台爬虫基类

    所有平台爬虫需要实现此接口
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化平台爬虫

        Args:
            config: 平台配置
        """
        self.config = config or {}
        self.platform_name = self.__class__.__name__.replace("Platform", "").lower()

    @abstractmethod
    async def crawl(self,
                   task_config: TaskConfig,
                   on_progress: Optional[Callable[[str, int], None]] = None) -> CrawlResult:
        """
        执行爬虫任务

        Args:
            task_config: 任务配置
            on_progress: 进度回调函数 (message, percent)

        Returns:
            爬虫结果
        """
        pass

    @abstractmethod
    def detect_platform(self, url: str) -> bool:
        """
        检测URL是否属于当前平台

        Args:
            url: 待检测的URL

        Returns:
            是否属于当前平台
        """
        pass

    @abstractmethod
    def get_platform_domains(self) -> List[str]:
        """
        获取平台支持的域名列表

        Returns:
            域名列表
        """
        pass

    def validate_config(self, task_config: TaskConfig) -> bool:
        """
        验证任务配置

        Args:
            task_config: 任务配置

        Returns:
            配置是否有效
        """
        # 基础验证
        if not task_config:
            logger.error("任务配置不能为空")
            return False

        # 任务类型验证
        if task_config.task_type == TaskType.KEYWORD_SEARCH and not task_config.keywords:
            logger.error("关键词搜索任务必须提供keywords")
            return False

        if task_config.task_type == TaskType.SHOP_CRAWL and not task_config.shop_url:
            logger.error("店铺爬取任务必须提供shop_url")
            return False

        if task_config.task_type == TaskType.CATEGORY_CRAWL and not task_config.category_url:
            logger.error("分类爬取任务必须提供category_url")
            return False

        if task_config.task_type == TaskType.PRODUCT_DETAIL and not task_config.product_urls:
            logger.error("商品详情任务必须提供product_urls")
            return False

        return True

    def get_task_estimate(self, task_config: TaskConfig) -> Dict[str, Any]:
        """
        估算任务执行时间和数据量

        Args:
            task_config: 任务配置

        Returns:
            估算信息
        """
        base_time = 30  # 基础时间（秒）

        if task_config.task_type == TaskType.KEYWORD_SEARCH:
            estimated_time = base_time + len(task_config.keywords or []) * task_config.max_pages * 2
            estimated_items = len(task_config.keywords or []) * task_config.max_pages * task_config.max_items_per_page
        elif task_config.task_type == TaskType.SHOP_CRAWL:
            estimated_time = base_time + task_config.max_pages * 5
            estimated_items = task_config.max_pages * task_config.max_items_per_page
        elif task_config.task_type == TaskType.CATEGORY_CRAWL:
            estimated_time = base_time + task_config.max_pages * 3
            estimated_items = task_config.max_pages * task_config.max_items_per_page
        elif task_config.task_type == TaskType.PRODUCT_DETAIL:
            estimated_time = len(task_config.product_urls or []) * 2
            estimated_items = len(task_config.product_urls or [])
        else:
            estimated_time = base_time
            estimated_items = 0

        return {
            "estimated_time_seconds": estimated_time,
            "estimated_items": estimated_items,
            "complexity": "low" if estimated_time < 60 else "medium" if estimated_time < 300 else "high"
        }