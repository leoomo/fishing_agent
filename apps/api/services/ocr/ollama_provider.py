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
from pathlib import Path

from .base import BaseOCRProvider
from .exceptions import OllamaError, OCRModelNotFoundError, OCRConfigurationError
from packages.data_processing.image import ImageMerger
from packages.data_processing.ocr import OCRMergeProcessor

logger = logging.getLogger(__name__)


class OllamaProvider(BaseOCRProvider):
    """Ollama OCR 提供商"""

    DEFAULT_MODEL = "deepseek-ocr"
    DEFAULT_TIMEOUT = 60  # Ollama本地处理可能需要更长时间

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
                from httpx import Timeout
                # 设置超时：连接超时10秒，读取超时使用配置值
                timeout = Timeout(
                    connect=10.0,
                    read=float(self.timeout),
                    write=30.0,
                    pool=15.0
                )
                self._client = ollama.Client(host=self.base_url, timeout=timeout)
                logger.info(f"已连接到Ollama服务: {self.base_url}, timeout={self.timeout}s")
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

    def _merge_images(self, image_paths: List[str]) -> Tuple[List[str], int]:
        """
        使用 OCRMergeProcessor 智能合并多张图片

        流程：
        1. 裁剪每张图片的空白区域（crop_single_image）
        2. 跳过文字稀疏区域（skip_sparse_regions）
        3. 智能分组合并（generate_smart_merge_groups）
        4. 如果只有一个输出文件且超过限制，分割处理

        Args:
            image_paths: 图片路径列表

        Returns:
            Tuple[List[str], int]: (输出文件路径列表, 合并数量)
        """
        if len(image_paths) == 1:
            return [image_paths[0]], 1

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="ocr_merge_")
        output_dir = tempfile.mkdtemp(prefix="ocr_output_")

        try:
            # 将所有图片复制到源目录（OCRMergeProcessor 需要源目录）
            import shutil
            source_dir = Path(temp_dir)
            for i, path in enumerate(image_paths):
                shutil.copy2(path, source_dir / f"{i+1}.jpg")

            # 使用 OCRMergeProcessor 处理
            processor = OCRMergeProcessor(
                source_dir=str(source_dir),
                output_dir=output_dir,
                # 裁剪参数
                padding=15,
                min_text_area=100,
                # 合并参数
                quality=95,
                spacing=0,
                # 分割参数（如果合并后还是太大）
                enable_split=True,
                min_segment_height=300,
                max_segment_height=4000,
                # 其他参数
                keep_empty_images=False,
                skip_pure_images=True,
                skip_sparse_regions=True,
                min_chars_per_region=5,
                verbose=False
            )

            result = processor.process()

            if not result.success:
                raise OllamaError(f"图片处理失败: {result.error}", "OCR_MERGE_ERROR")

            output_files = result.output_files

            logger.info(f"智能合并完成: {len(image_paths)} 张图片 -> {len(output_files)} 个文件")
            logger.info(f"统计: {result.statistics}")

            return output_files, len(image_paths)

        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"OCRMergeProcessor 处理失败: {e}")
            # 回退到简单合并
            logger.info("回退到简单合并模式...")
            return self._simple_merge_images(image_paths)
        finally:
            # 清理临时目录
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            # 注意：output_dir 需要保留，因为 merged_path 在里面

    def _simple_merge_images(self, image_paths: List[str]) -> Tuple[List[str], int]:
        """
        简单合并模式（回退方案）

        直接垂直合并所有图片，不进行裁剪和智能分组
        """
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            output_path = f.name

        logger.info(f"简单合并 {len(image_paths)} 张图片...")

        success = self.image_merger.merge_vertically(image_paths, output_path)

        if not success:
            raise OllamaError("图片合并失败", "OCR_MERGE_ERROR")

        logger.info(f"图片合并成功: {output_path}")
        return [output_path], len(image_paths)

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
        merged_paths = []
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
                merged_paths, images_merged = self._merge_images(image_paths)
            else:
                merged_paths = [image_paths[0]]

            # 对所有输出文件进行 OCR，然后合并结果
            all_markdown = []
            total_file_size = 0
            client = self._get_client()

            total_files = len(merged_paths)
            for i, target_path in enumerate(merged_paths):
                # 始终显示 OCR 进度
                file_size = os.path.getsize(target_path)
                total_file_size += file_size
                logger.info(
                    f"  OCR 进度: [{i+1}/{total_files}] "
                    f"{os.path.basename(target_path)} ({file_size/1024:.1f}KB)"
                )

                # 编码图片为base64
                img_data = self._encode_image_to_base64(target_path)

                if verbose:
                    logger.info(f"  正在调用Ollama API (模型: {self._model})...")

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
                all_markdown.append(markdown)

            # 合并所有 markdown 结果
            final_markdown = "\n\n".join(all_markdown)

            # 计算处理时间
            processing_time_ms = int((time.time() - start_time) * 1000)

            if verbose:
                logger.info(f"识别完成，处理了 {len(merged_paths)} 个文件，耗时: {processing_time_ms}ms")

            return self._format_response(
                success=True,
                markdown=final_markdown,
                metadata={
                    "model": self._model,
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged,
                    "output_files_count": len(merged_paths),
                    "total_file_size_bytes": total_file_size
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
            error_str = str(e)
            error_type = type(e).__name__

            # 检查是否为超时错误（httpx.TimeoutException 或其子类）
            is_timeout = (
                "timeout" in error_str.lower() or
                "timed out" in error_str.lower() or
                "TimeoutException" in error_type or
                "ReadTimeout" in error_type or
                "ConnectTimeout" in error_type
            )

            if is_timeout:
                logger.error(f"Ollama OCR 超时 (>{self.timeout}s): {error_type}: {e}")
                return self._format_response(
                    success=False,
                    error=f"Ollama处理超时（>{self.timeout}秒），请稍后重试或增加OLLAMA_TIMEOUT配置",
                    error_code="OCR_TIMEOUT",
                    metadata={
                        "model": self._model,
                        "processing_time_ms": processing_time_ms,
                        "images_merged": images_merged,
                        "timeout_seconds": self.timeout
                    }
                )

            logger.error(f"未知错误 ({error_type}): {e}")
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
            for path in merged_paths:
                if os.path.exists(path):
                    try:
                        os.unlink(path)
                        logger.debug(f"已清理临时文件: {path}")
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

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """
        检查服务是否可用，返回详细信息

        Returns:
            Tuple[bool, Optional[str]]: (是否可用, 错误原因)
        """
        # 1. 检查 ollama 包是否安装
        try:
            import ollama  # noqa: F401
        except ImportError:
            return (False, "未安装 ollama 包，请运行: pip install ollama")

        # 2. 尝试连接 Ollama 服务
        try:
            client = self._get_client()
        except OCRConfigurationError as e:
            return (False, f"无法连接到 Ollama 服务 ({self.base_url}): {e.message}")
        except Exception as e:
            return (False, f"无法连接到 Ollama 服务 ({self.base_url}): {e}")

        # 3. 检查服务状态
        try:
            client.list()
        except Exception as e:
            return (False, f"Ollama 服务响应异常: {e}")

        # 4. 确保模型可用
        try:
            self._ensure_model_available()
        except OCRModelNotFoundError as e:
            return (False, f"模型 '{self._model}' 不可用: {e.message}")
        except Exception as e:
            return (False, f"模型 '{self._model}' 不可用: {e}")

        return (True, None)

    def is_available(self) -> bool:
        """检查服务是否可用（兼容旧接口）"""
        available, error_reason = self.check_availability()
        if not available:
            logger.debug(f"Ollama服务不可用: {error_reason}")
        return available

    def list_available_models(self) -> List[str]:
        """列出可用的模型"""
        try:
            client = self._get_client()
            models = client.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []