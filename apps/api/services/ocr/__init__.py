"""
OCR 服务模块

支持多种OCR提供商：
- SiliconFlow API (云端)
- Ollama (本地)
- Baidu AI Studio (云端)
- Fallback (多级回退)
"""

from .base import BaseOCRProvider
from .siliconflow_provider import SiliconFlowProvider
from .ollama_provider import OllamaProvider
from .baidu_provider import BaiduProvider
from .fallback_provider import FallbackProvider
from .factory import OCRProviderFactory
from .exceptions import (
    OCRError,
    SiliconFlowError,
    OllamaError,
    BaiduError,
    OCRProviderNotAvailableError,
    OCRConfigurationError,
    OCRModelNotFoundError,
    OCRProcessingError
)

__all__ = [
    "BaseOCRProvider",
    "SiliconFlowProvider",
    "OllamaProvider",
    "BaiduProvider",
    "FallbackProvider",
    "OCRProviderFactory",
    "OCRError",
    "SiliconFlowError",
    "OllamaError",
    "BaiduError",
    "OCRProviderNotAvailableError",
    "OCRConfigurationError",
    "OCRModelNotFoundError",
    "OCRProcessingError"
]