"""
OCR 服务

支持多种OCR提供商：
- SiliconFlow API (云端)
- Ollama (本地)
"""

import os
import logging
import tempfile
from typing import List, Optional, Dict, Any, Tuple

from .ocr import (
    BaseOCRProvider,
    OCRProviderFactory,
    OCRError,
    OCRConfigurationError,
    OCRProviderNotAvailableError
)
from packages.agent_fishing.tools.lure.image_merger import ImageMerger

logger = logging.getLogger(__name__)


class OCRService:
    """
    OCR服务

    支持多种OCR提供商，通过配置选择使用哪种服务。
    默认使用本地Ollama提供商。
    """

    def __init__(self):
        """初始化 OCR 服务"""
        # 获取提供商类型配置，默认为 ollama
        provider_type = os.getenv("OCR_PROVIDER", "ollama")

        try:
            # 创建OCR提供商实例
            self.provider: BaseOCRProvider = OCRProviderFactory.create_provider(provider_type)
            self.provider_type = provider_type

            # 保留图片合并器（用于处理多图片合并）
            self.image_merger = ImageMerger(quality=95)

            # 为了向后兼容，保留一些原有属性
            if provider_type == "siliconflow":
                self.api_key = os.getenv("SILICONFLOW_API_KEY")
                self.timeout = int(os.getenv("SILICONFLOW_OCR_TIMEOUT", "30"))
                self.max_size = int(os.getenv("SILICONFLOW_OCR_MAX_SIZE", str(10 * 1024 * 1024)))
            else:
                # 对于Ollama，使用其默认超时
                self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
                self.max_size = int(os.getenv("OLLAMA_MAX_SIZE", str(20 * 1024 * 1024)))

            logger.info(f"OCRService initialized: provider={provider_type}, model={self.provider.get_model_info()['model']}")

        except (OCRConfigurationError, OCRProviderNotAvailableError) as e:
            logger.error(f"OCR服务初始化失败: {e.message}")
            # 创建一个空的提供商以避免应用崩溃
            self.provider = None
            self.provider_type = None
            raise

    def _validate_provider(self) -> None:
        """验证提供商是否已初始化"""
        if self.provider is None:
            raise OCRError(
                "OCR服务未正确初始化，请检查配置",
                "OCR_SERVICE_NOT_INITIALIZED"
            )

    def detect_text_in_region(self, image_path: str, region: Tuple[float, float, float, float]) -> dict:
        """
        检测图片指定区域内的文字

        委托给当前使用的提供商
        如果提供商不支持此方法，返回默认值

        Args:
            image_path: 图片路径
            region: (x_min, y_min, x_max, y_max) 相对坐标 (0-1)

        Returns:
            dict: {"has_text": bool, "confidence": float, "text": str, "error": str}
        """
        self._validate_provider()

        # 只有SiliconFlowProvider实现了此方法
        if hasattr(self.provider, 'detect_text_in_region'):
            return self.provider.detect_text_in_region(image_path, region)
        else:
            # 对于不支持此方法的提供商，返回默认值
            return {
                "has_text": False,
                "confidence": 0.0,
                "text": "",
                "error": f"提供商 {self.provider_type} 不支持区域文字检测"
            }

    def recognize_table(
        self,
        image_path: str,
        verbose: bool = False
    ) -> dict:
        """
        识别单张图片中的表格

        委托给当前使用的提供商

        Args:
            image_path: 图片路径
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
        self._validate_provider()
        return self.provider.recognize_table(image_path, verbose=verbose)

    def recognize_table_from_paths(
        self,
        image_paths: List[str],
        verbose: bool = False
    ) -> dict:
        """
        识别多张图片中的表格（自动合并）

        委托给当前使用的提供商

        Args:
            image_paths: 图片路径列表
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
        self._validate_provider()
        return self.provider.recognize_table_from_paths(image_paths, verbose=verbose)

    def recognize_table_from_bytes(
        self,
        image_data_list: List[Tuple[bytes, str]],
        verbose: bool = False
    ) -> dict:
        """
        从字节数据识别表格（用于文件上传场景）

        委托给当前使用的提供商

        Args:
            image_data_list: [(图片字节数据, 文件名), ...]
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
        self._validate_provider()
        return self.provider.recognize_table_from_bytes(image_data_list, verbose=verbose)


# 创建全局服务实例
_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """获取 OCR 服务实例（单例）"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
