"""
多级回退 OCR Provider

按配置顺序依次尝试多个 OCR 提供商，直到成功或全部失败
"""

import os
import logging
from typing import List, Dict, Any, Optional

from .base import BaseOCRProvider

logger = logging.getLogger(__name__)


class FallbackProvider(BaseOCRProvider):
    """
    多级回退 OCR Provider

    按配置顺序依次尝试多个 OCR 提供商，直到有一个成功或全部失败。
    这可以提供更好的容错性，例如：本地 OCR 失败时自动切换到云端 OCR。

    示例配置:
        OCR_FALLBACK_PROVIDERS=ollama,siliconflow,baidu
    """

    def __init__(self, provider_types: Optional[List[str]] = None):
        """
        初始化回退 Provider

        Args:
            provider_types: 按优先级排列的提供商列表
                           如 ["ollama", "siliconflow", "baidu"]
                           默认从环境变量 OCR_FALLBACK_PROVIDERS 读取
        """
        # 从环境变量读取回退提供商列表
        if provider_types is None:
            fallback_str = os.getenv(
                "OCR_FALLBACK_PROVIDERS",
                "ollama,siliconflow,baidu"
            )
            provider_types = [p.strip() for p in fallback_str.split(",") if p.strip()]

        self.provider_types = provider_types
        self.providers = []
        self._init_providers()

        logger.info(
            f"FallbackProvider 初始化: "
            f"providers={', '.join([p.__class__.__name__ for p in self.providers])}"
        )

    def _init_providers(self) -> None:
        """初始化所有可用的 Provider"""
        from .factory import OCRProviderFactory

        for provider_type in self.provider_types:
            try:
                provider = OCRProviderFactory.create_provider(provider_type)
                self.providers.append(provider)
                logger.info(f"  ✓ 成功加载: {provider.__class__.__name__}")
            except Exception as e:
                logger.warning(f"  ✗ 跳过 '{provider_type}': {e}")

        if not self.providers:
            raise ValueError(
                f"无法初始化任何 OCR 提供商。"
                f"请检查配置: {', '.join(self.provider_types)}"
            )

    def recognize_table(
        self,
        image_path: str,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        识别单张图片中的表格（带回退机制）

        Args:
            image_path: 图片路径
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
        return self.recognize_table_from_paths([image_path], verbose=verbose)

    def recognize_table_from_paths(
        self,
        image_paths: List[str],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        识别多张图片中的表格（带回退机制）

        按顺序尝试各个 Provider，直到有一个成功或全部失败。

        Args:
            image_paths: 图片路径列表
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
        last_error = None
        last_error_code = None

        for i, provider in enumerate(self.providers):
            try:
                provider_name = provider.__class__.__name__

                if verbose:
                    logger.info(
                        f"[Fallback] 尝试 Provider {i+1}/{len(self.providers)}: {provider_name}"
                    )

                # 尝试调用当前 Provider
                result = provider.recognize_table_from_paths(image_paths, verbose=verbose)

                if result.get("success"):
                    # 成功！记录使用的 Provider 信息
                    result["metadata"]["fallback_used"] = provider_name
                    result["metadata"]["fallback_index"] = i
                    result["metadata"]["fallback_total"] = len(self.providers)

                    if verbose:
                        logger.info(
                            f"[Fallback] ✓ {provider_name} 成功! "
                            f"(尝试了 {i+1} 个提供商)"
                        )

                    return result
                else:
                    # 失败，记录错误
                    last_error = result.get("error")
                    last_error_code = result.get("error_code")

                    if verbose:
                        logger.warning(
                            f"[Fallback] ✗ {provider_name} 失败: {last_error}"
                        )

            except Exception as e:
                # 异常，记录错误
                last_error = str(e)
                last_error_code = "OCR_PROVIDER_EXCEPTION"

                logger.warning(
                    f"[Fallback] ✗ {provider.__class__.__name__} 异常: {e}"
                )

        # 所有 Provider 都失败
        error_msg = (
            f"所有 {len(self.providers)} 个 OCR 提供商均失败。"
        )
        if last_error:
            error_msg += f" 最后错误: {last_error}"

        return self._format_response(
            success=False,
            error=error_msg,
            error_code=last_error_code or "OCR_ALL_PROVIDERS_FAILED",
            metadata={
                "provider": "fallback",
                "fallback_total": len(self.providers),
                "fallback_attempted": len(self.providers)
            }
        )

    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        available_providers = [p.__class__.__name__ for p in self.providers]
        return {
            "provider": "fallback",
            "model": "multi-provider",
            "type": "fallback",
            "providers": ", ".join(available_providers),
            "total_providers": str(len(self.providers))
        }

    def is_available(self) -> bool:
        """检查是否有可用的 Provider"""
        return len(self.providers) > 0

    def recognize_table_from_bytes(
        self,
        image_data_list: List[tuple],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        从字节数据识别表格（带回退机制）

        Args:
            image_data_list: [(图片字节数据, 文件名), ...]
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
        import tempfile
        import os

        temp_files = []

        try:
            # 保存到临时文件
            for data, filename in image_data_list:
                from pathlib import Path
                ext = Path(filename).suffix.lower() or '.jpg'
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                    f.write(data)
                    temp_files.append(f.name)

            # 调用路径版本
            return self.recognize_table_from_paths(temp_files, verbose=verbose)

        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
