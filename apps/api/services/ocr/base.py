"""
OCR 提供商抽象基类

定义所有OCR提供商必须实现的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseOCRProvider(ABC):
    """OCR提供商抽象基类"""

    @abstractmethod
    def recognize_table(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        识别图片中的表格内容

        Args:
            image_path: 图片路径
            **kwargs: 其他参数

        Returns:
            Dict: {
                "success": bool,
                "markdown": Optional[str],
                "metadata": {
                    "provider": str,
                    "model": str,
                    "processing_time_ms": int,
                    "images_merged": int,
                    "image_size_bytes": Optional[int]
                },
                "error": Optional[str],
                "error_code": Optional[str]
            }
        """
        pass

    @abstractmethod
    def recognize_table_from_paths(
        self,
        image_paths: list,
        **kwargs
    ) -> Dict[str, Any]:
        """
        识别多张图片中的表格（自动合并）

        Args:
            image_paths: 图片路径列表
            **kwargs: 其他参数

        Returns:
            Dict: 识别结果，格式同 recognize_table
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """
        获取模型信息

        Returns:
            Dict: {
                "provider": str,
                "model": str,
                "type": str  # "cloud" or "local"
            }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查服务是否可用

        Returns:
            bool: 服务可用性
        """
        pass

    def _validate_image_path(self, image_path: str) -> None:
        """验证图片路径"""
        import os
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

    def _format_response(
        self,
        success: bool,
        markdown: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """格式化统一响应"""
        response = {
            "success": success,
            "markdown": markdown,
            "metadata": metadata or {},
        }

        if error:
            response["error"] = error
        if error_code:
            response["error_code"] = error_code

        # 确保metadata包含必要字段
        if "provider" not in response["metadata"]:
            response["metadata"]["provider"] = self.__class__.__name__.replace("Provider", "").lower()

        return response