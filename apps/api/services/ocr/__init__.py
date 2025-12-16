"""
OCR 服务模块

支持多种OCR提供商：
- SiliconFlow API (云端)
- Ollama (本地)
"""

from .base import BaseOCRProvider
from .siliconflow_provider import SiliconFlowProvider
from .ollama_provider import OllamaProvider
from .factory import OCRProviderFactory
from .exceptions import (
    OCRError,
    SiliconFlowError,
    OllamaError,
    OCRProviderNotAvailableError,
    OCRConfigurationError,
    OCRModelNotFoundError,
    OCRProcessingError
)

__all__ = [
    "BaseOCRProvider",
    "SiliconFlowProvider",
    "OllamaProvider",
    "OCRProviderFactory",
    "OCRError",
    "SiliconFlowError",
    "OllamaError",
    "OCRProviderNotAvailableError",
    "OCRConfigurationError",
    "OCRModelNotFoundError",
    "OCRProcessingError"
]