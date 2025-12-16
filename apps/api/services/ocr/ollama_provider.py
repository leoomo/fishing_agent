"""
Ollama OCR 提供商

使用本地 Ollama deepseek-ocr 模型识别图片中的表格内容
"""

import os
import base64
import time
import tempfile
import logging
from typing import List, Optional, Tuple, Dict, Any

from .base import BaseOCRProvider
from .exceptions import OllamaError, OCRModelNotFoundError, OCRConfigurationError
from packages.agent_fishing.tools.lure.image_merger import ImageMerger

logger = logging.getLogger(__name__)


class OllamaProvider(BaseOCRProvider):
    """Ollama OCR 提供商"""

    DEFAULT_MODEL = "deepseek-ocr"
    DEFAULT_TIMEOUT = 120  # Ollama本地处理可能需要更长时间

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}
    MIME_TYPES = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp'
    }

    def __init__(self):
        """初始化 Ollama 提供商"""
        # 延迟导入，只有在需要时才导入
        self._client = None
        self._model = os.getenv("OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", self.DEFAULT_TIMEOUT))
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.max_size = int(os.getenv("OLLAMA_MAX_SIZE", str(20 * 1024 * 1024)))  # 20MB

        # 初始化图片合并器
        self.image_merger = ImageMerger(quality=95)

        logger.info(f"OllamaProvider initialized: model={self._model}, timeout={self.timeout}s, base_url={self.base_url}")

    def _get_client(self):
        """获取Ollama客户端（延迟初始化）"""
        if self._client is None:
            try:
                import ollama
                self._client = ollama.Client(host=self.base_url)
                logger.info(f"已连接到Ollama服务: {self.base_url}")
            except ImportError as e:
                raise OCRConfigurationError(
                    "未安装ollama包，请运行: pip install ollama",
                    "OCR_OLLAMA_NOT_INSTALLED"
                )
            except Exception as e:
                raise OCRConfigurationError(
                    f"无法连接到Ollama服务: {e}",
                    "OCR_OLLAMA_CONNECTION_ERROR"
                )
        return self._client

    def _ensure_model_available(self) -> None:
        """检查并拉取模型"""
        client = self._get_client()

        try:
            # 检查模型是否存在
            model_info = client.show(self._model)
            logger.info(f"Ollama模型 {self._model} 已就绪")
            logger.debug(f"模型详情: {model_info}")
        except Exception as e:
            # 模型不存在，尝试拉取
            logger.info(f"拉取Ollama模型 {self._model}...")
            try:
                # 使用流式输出显示拉取进度
                stream = client.pull(self._model, stream=True)

                # 显示下载进度
                for digest in stream:
                    if 'status' in digest:
                        logger.info(f"拉取进度: {digest['status']}")
                    if 'digest' in digest:
                        logger.debug(f"层: {digest['digest'][:12]}...")

                logger.info(f"模型 {self._model} 拉取完成")
            except Exception as pull_error:
                raise OCRModelNotFoundError(
                    f"无法拉取模型 {self._model}: {pull_error}",
                    "OCR_MODEL_PULL_FAILED"
                )

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片转换为 base64

        Args:
            image_path: 图片路径

        Returns:
            str: base64编码的图片
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _validate_image_format(self, file_path: str) -> str:
        """
        验证图片格式

        Args:
            file_path: 图片路径

        Returns:
            str: MIME 类型
        """
        from pathlib import Path

        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise OllamaError(
                f"不支持的图片格式: {ext}，支持格式: {', '.join(self.SUPPORTED_FORMATS)}",
                "OCR_INVALID_FORMAT"
            )
        return self.MIME_TYPES[ext]

    def _validate_image_size(self, file_path: str) -> int:
        """
        验证图片大小

        Args:
            file_path: 图片路径

        Returns:
            int: 文件大小（字节）
        """
        file_size = os.path.getsize(file_path)
        if file_size > self.max_size:
            raise OllamaError(
                f"图片大小 {file_size/1024/1024:.1f}MB 超过限制 {self.max_size/1024/1024:.1f}MB",
                "OCR_FILE_TOO_LARGE"
            )
        return file_size

    def _merge_images(self, image_paths: List[str]) -> Tuple[str, int]:
        """
        合并多张图片

        Args:
            image_paths: 图片路径列表

        Returns:
            Tuple[str, int]: (合并后的图片路径, 合并数量)
        """
        if len(image_paths) == 1:
            return image_paths[0], 1

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            output_path = f.name

        logger.info(f"合并 {len(image_paths)} 张图片...")

        success = self.image_merger.merge_vertically(image_paths, output_path)

        if not success:
            raise OllamaError("图片合并失败", "OCR_MERGE_ERROR")

        logger.info(f"图片合并成功: {output_path}")
        return output_path, len(image_paths)

    def recognize_table(
        self,
        image_path: str,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        识别单张图片中的表格

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
        识别多张图片中的表格（自动合并）

        Args:
            image_paths: 图片路径列表
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
        start_time = time.time()
        merged_path = None
        images_merged = 1

        try:
            # 确保模型可用
            if not self.is_available():
                raise OllamaError("Ollama服务不可用", "OCR_SERVICE_UNAVAILABLE")

            if not image_paths:
                raise OllamaError("未提供图片", "OCR_NO_INPUT")

            # 验证所有图片
            for path in image_paths:
                self._validate_image_path(path)
                self._validate_image_format(path)
                self._validate_image_size(path)

            # 合并图片（如果多张）
            if len(image_paths) > 1:
                merged_path, images_merged = self._merge_images(image_paths)
                target_path = merged_path
            else:
                target_path = image_paths[0]

            # 编码图片为base64
            img_data = self._encode_image_to_base64(target_path)
            file_size = os.path.getsize(target_path)

            if verbose:
                logger.info(f"图片大小: {file_size/1024:.1f}KB, 模型: {self._model}")

            # 调用Ollama API
            client = self._get_client()

            if verbose:
                logger.info("正在调用Ollama API...")

            response = client.generate(
                model=self._model,
                prompt="Extract all text from this image and return it in a structured markdown format.",
                images=[img_data],
                options={
                    'temperature': 0.1,  # 较低的温度以获得更一致的结果
                }
            )

            # 获取识别结果
            markdown = response['response'].strip()

            # 计算处理时间
            processing_time_ms = int((time.time() - start_time) * 1000)

            if verbose:
                logger.info(f"识别完成，耗时: {processing_time_ms}ms")

            return self._format_response(
                success=True,
                markdown=markdown,
                metadata={
                    "model": self._model,
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged,
                    "image_size_bytes": file_size
                }
            )

        except OllamaError as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Ollama OCR 错误: {e.message} ({e.error_code})")
            return self._format_response(
                success=False,
                error=e.message,
                error_code=e.error_code,
                metadata={
                    "model": self._model,
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged
                }
            )

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"未知错误: {e}")
            return self._format_response(
                success=False,
                error=str(e),
                error_code="OCR_UNKNOWN_ERROR",
                metadata={
                    "model": self._model,
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged
                }
            )

        finally:
            # 清理临时合并文件
            if merged_path and os.path.exists(merged_path):
                try:
                    os.unlink(merged_path)
                    logger.debug(f"已清理临时文件: {merged_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    def recognize_table_from_bytes(
        self,
        image_data_list: List[Tuple[bytes, str]],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        从字节数据识别表格（用于文件上传场景）

        Args:
            image_data_list: [(图片字节数据, 文件名), ...]
            verbose: 是否输出详细日志

        Returns:
            dict: 识别结果
        """
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

    def get_model_info(self) -> Dict[str, str]:
        """获取模型信息"""
        return {
            "provider": "ollama",
            "model": self._model,
            "type": "local",
            "base_url": self.base_url
        }

    def is_available(self) -> bool:
        """检查服务是否可用"""
        try:
            # 尝试连接Ollama服务
            client = self._get_client()

            # 检查服务状态
            client.list()

            # 确保模型可用
            self._ensure_model_available()

            return True
        except Exception as e:
            logger.debug(f"Ollama服务不可用: {e}")
            return False

    def list_available_models(self) -> List[str]:
        """列出可用的模型"""
        try:
            client = self._get_client()
            models = client.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []