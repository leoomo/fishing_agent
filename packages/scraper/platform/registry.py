"""
平台爬虫注册表

管理所有平台的爬虫实例，提供统一的调用接口
"""

import logging
from typing import Dict, List, Type, Optional, Any
from urllib.parse import urlparse

from .base_platform import BasePlatform, TaskConfig
from .taobao_platform import TaobaoPlatform
from .jd_platform import JDPlatform

logger = logging.getLogger(__name__)


class PlatformRegistry:
    """
    平台注册表

    负责管理所有平台的爬虫实例，提供平台检测和实例获取功能
    """

    def __init__(self):
        """初始化平台注册表"""
        self._platforms: Dict[str, BasePlatform] = {}
        self._platform_classes: Dict[str, Type[BasePlatform]] = {}
        self._domain_mapping: Dict[str, str] = {}

        # 注册内置平台
        self._register_builtin_platforms()

    def _register_builtin_platforms(self):
        """注册内置平台"""
        self.register_platform("taobao", TaobaoPlatform)
        self.register_platform("tmall", TaobaoPlatform)  # 天猫使用淘宝的爬虫
        self.register_platform("jd", JDPlatform)

    def register_platform(self, name: str, platform_class: Type[BasePlatform]):
        """
        注册平台

        Args:
            name: 平台名称
            platform_class: 平台爬虫类
        """
        if not issubclass(platform_class, BasePlatform):
            raise ValueError(f"平台类必须继承自BasePlatform: {platform_class}")

        self._platform_classes[name] = platform_class
        logger.info(f"注册平台: {name} -> {platform_class.__name__}")

        # 更新域名映射
        try:
            # 创建临时实例获取域名列表
            temp_instance = platform_class()
            for domain in temp_instance.get_platform_domains():
                self._domain_mapping[domain] = name
        except Exception as e:
            logger.warning(f"无法获取平台 {name} 的域名列表: {e}")

    def get_platform(self, platform_name: str, config: Optional[Dict[str, Any]] = None) -> BasePlatform:
        """
        获取平台爬虫实例

        Args:
            platform_name: 平台名称
            config: 平台配置

        Returns:
            平台爬虫实例
        """
        # 检查是否已有缓存实例
        cache_key = f"{platform_name}:{id(config) if config else 'default'}"
        if cache_key not in self._platforms:
            # 创建新实例
            if platform_name not in self._platform_classes:
                raise ValueError(f"未注册的平台: {platform_name}")

            platform_class = self._platform_classes[platform_name]
            instance = platform_class(config)
            self._platforms[cache_key] = instance

            logger.info(f"创建平台实例: {platform_name}")

        return self._platforms[cache_key]

    def detect_platform_by_url(self, url: str) -> Optional[str]:
        """
        通过URL检测平台

        Args:
            url: 目标URL

        Returns:
            平台名称，如果无法识别则返回None
        """
        try:
            domain = urlparse(url).netloc.lower()

            # 精确匹配
            if domain in self._domain_mapping:
                return self._domain_mapping[domain]

            # 模糊匹配
            for registered_domain, platform_name in self._domain_mapping.items():
                if registered_domain in domain or domain in registered_domain:
                    return platform_name

        except Exception as e:
            logger.error(f"URL平台检测失败: {e}")

        return None

    def get_supported_platforms(self) -> List[str]:
        """
        获取支持的平台列表

        Returns:
            平台名称列表
        """
        return list(self._platform_classes.keys())

    def get_platform_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有平台的详细信息

        Returns:
            平台信息字典
        """
        info = {}

        for name, platform_class in self._platform_classes.items():
            try:
                temp_instance = platform_class()
                info[name] = {
                    "class": platform_class.__name__,
                    "domains": temp_instance.get_platform_domains(),
                    "instance_exists": any(k.startswith(f"{name}:") for k in self._platforms.keys())
                }
            except Exception as e:
                logger.error(f"获取平台 {name} 信息失败: {e}")
                info[name] = {
                    "class": platform_class.__name__,
                    "error": str(e)
                }

        return info

    def validate_task_config(self, task_config: TaskConfig) -> bool:
        """
        验证任务配置

        Args:
            task_config: 任务配置

        Returns:
            配置是否有效
        """
        # 如果指定了平台，检查平台是否存在
        if hasattr(task_config, 'platform') and task_config.platform:
            if task_config.platform not in self._platform_classes:
                logger.error(f"不支持的平台: {task_config.platform}")
                return False

        return True

    def get_platform_for_config(self, task_config: TaskConfig) -> BasePlatform:
        """
        根据任务配置获取平台实例

        Args:
            task_config: 任务配置

        Returns:
            平台爬虫实例
        """
        # 优先使用配置中指定的平台
        platform_name = None

        if hasattr(task_config, 'platform') and task_config.platform:
            platform_name = task_config.platform
        elif task_config.shop_url:
            platform_name = self.detect_platform_by_url(task_config.shop_url)
        elif task_config.category_url:
            platform_name = self.detect_platform_by_url(task_config.category_url)
        elif task_config.product_urls:
            # 使用第一个商品的URL
            platform_name = self.detect_platform_by_url(task_config.product_urls[0])

        if not platform_name:
            # 默认使用淘宝
            platform_name = "taobao"
            logger.warning(f"无法自动检测平台，使用默认平台: {platform_name}")

        return self.get_platform(platform_name)


# 全局平台注册表实例
platform_registry = PlatformRegistry()