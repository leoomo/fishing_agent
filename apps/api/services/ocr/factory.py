"""
OCR 提供商工厂

根据配置创建合适的OCR提供商实例
"""

import os
import logging
from typing import List, Dict, Any, Optional

from .base import BaseOCRProvider
from .siliconflow_provider import SiliconFlowProvider
from .ollama_provider import OllamaProvider
from .baidu_provider import BaiduProvider
from .fallback_provider import FallbackProvider
from .exceptions import OCRConfigurationError, OCRProviderNotAvailableError

logger = logging.getLogger(__name__)


class OCRProviderFactory:
    """OCR提供商工厂类"""

    # 支持的提供商类型
    SUPPORTED_PROVIDERS = {
        "siliconflow": SiliconFlowProvider,
        "ollama": OllamaProvider,
        "baidu": BaiduProvider,
        "fallback": FallbackProvider,
    }

    @staticmethod
    def create_provider(provider_type: str = None) -> BaseOCRProvider:
        """
        创建OCR提供商实例

        Args:
            provider_type: 提供商类型，如果为None则从环境变量读取

        Returns:
            BaseOCRProvider: OCR提供商实例

        Raises:
            OCRConfigurationError: 配置错误
            OCRProviderNotAvailableError: 提供商不可用
        """
        # 从环境变量读取提供商类型
        if provider_type is None:
            provider_type = os.getenv("OCR_PROVIDER", "ollama")  # 默认使用Ollama

        provider_type = provider_type.lower().strip()

        if provider_type not in OCRProviderFactory.SUPPORTED_PROVIDERS:
            raise OCRConfigurationError(
                f"不支持的OCR提供商: {provider_type}，支持的提供商: {', '.join(OCRProvider.SUPPORTED_PROVIDERS.keys())}",
                "OCR_UNSUPPORTED_PROVIDER"
            )

        # 创建提供商实例
        provider_class = OCRProviderFactory.SUPPORTED_PROVIDERS[provider_type]

        try:
            provider = provider_class()

            # 检查提供商是否可用（使用详细检查方法）
            available, error_reason = provider.check_availability()
            if not available:
                raise OCRProviderNotAvailableError(
                    f"OCR提供商 '{provider_type}' 不可用: {error_reason}",
                    "OCR_PROVIDER_NOT_AVAILABLE"
                )

            logger.info(f"已创建OCR提供商: {provider_type} ({provider.__class__.__name__})")
            return provider

        except Exception as e:
            if isinstance(e, (OCRConfigurationError, OCRProviderNotAvailableError)):
                raise

            logger.error(f"创建OCR提供商 '{provider_type}' 失败: {e}")
            raise OCRProviderNotAvailableError(
                f"无法初始化OCR提供商 '{provider_type}': {e}",
                "OCR_PROVIDER_INIT_FAILED"
            )

    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """
        获取所有可用的提供商及其状态

        Returns:
            Dict[str, bool]: 提供商名称和可用性
        """
        availability = {}

        for provider_name, provider_class in OCRProviderFactory.SUPPORTED_PROVIDERS.items():
            try:
                provider = provider_class()
                availability[provider_name] = provider.is_available()
            except Exception as e:
                logger.debug(f"检查提供商 '{provider_name}' 状态失败: {e}")
                availability[provider_name] = False

        return availability

    @staticmethod
    def get_provider_info(provider_type: str = None) -> Dict[str, Any]:
        """
        获取提供商信息

        Args:
            provider_type: 提供商类型

        Returns:
            Dict[str, Any]: 提供商信息
        """
        if provider_type is None:
            provider_type = os.getenv("OCR_PROVIDER", "ollama")

        provider_type = provider_type.lower().strip()

        if provider_type not in OCRProviderFactory.SUPPORTED_PROVIDERS:
            raise OCRConfigurationError(
                f"不支持的OCR提供商: {provider_type}",
                "OCR_UNSUPPORTED_PROVIDER"
            )

        try:
            provider = OCRProviderFactory.create_provider(provider_type)
            return provider.get_model_info()
        except Exception as e:
            logger.error(f"获取提供商信息失败: {e}")
            return {
                "provider": provider_type,
                "error": str(e),
                "type": "unknown"
            }

    @staticmethod
    def create_fallback_provider(
        provider_types: Optional[List[str]] = None
    ) -> FallbackProvider:
        """
        创建带回退机制的 OCR 提供商

        Args:
            provider_types: 提供商列表，按优先级排序
                           如 ["ollama", "siliconflow", "baidu"]
                           默认从环境变量 OCR_FALLBACK_PROVIDERS 读取

        Returns:
            FallbackProvider: 回退提供商实例

        Raises:
            ValueError: 无法初始化任何提供商
        """
        return FallbackProvider(provider_types)