"""
SiliconFlow OCR 提供商

使用硅基流动 DeepSeek-OCR 模型识别图片中的表格内容
"""

import os
import base64
import time
import tempfile
import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

import requests

from .base import BaseOCRProvider
from .exceptions import SiliconFlowError, OCRConfigurationError
from packages.data_processing.image import ImageMerger
from packages.data_processing.ocr import OCRMergeProcessor

# 导入PIL用于图片处理
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)


class SiliconFlowProvider(BaseOCRProvider):
    """SiliconFlow OCR 提供商"""

    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    MODEL = "deepseek-ai/DeepSeek-OCR"

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.webp'}
    MIME_TYPES = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp'
    }

    def __init__(self):
        """初始化 SiliconFlow 提供商"""
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        self.timeout = int(os.getenv("SILICONFLOW_OCR_TIMEOUT", "30"))
        self.max_size = int(os.getenv("SILICONFLOW_OCR_MAX_SIZE", str(10 * 1024 * 1024)))  # 10MB
        self.max_retries = 3

        # 初始化图片合并器
        self.image_merger = ImageMerger(quality=95)

        logger.info(f"SiliconFlowProvider initialized: timeout={self.timeout}s, max_size={self.max_size/1024/1024:.1f}MB")

    def _validate_api_key(self) -> None:
        """验证 API 密钥是否已配置"""
        if not self.api_key:
            raise OCRConfigurationError(
                "未配置硅基流动 API 密钥，请在 .env 中设置 SILICONFLOW_API_KEY",
                "OCR_API_KEY_MISSING"
            )

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
            raise SiliconFlowError(
                f"不支持的图片格式: {ext}，支持格式: {', '.join(self.SUPPORTED_FORMATS)}",
                "OCR_INVALID_FORMAT"
            )
        return self.MIME_TYPES[ext]

    def _image_to_base64(self, file_path: str) -> Tuple[str, int]:
        """
        将图片转换为 base64

        Args:
            file_path: 图片路径

        Returns:
            Tuple[str, int]: (base64字符串, 文件大小)
        """
        with open(file_path, 'rb') as f:
            data = f.read()

        file_size = len(data)
        if file_size > self.max_size:
            raise SiliconFlowError(
                f"图片大小 {file_size/1024/1024:.1f}MB 超过限制 {self.max_size/1024/1024:.1f}MB",
                "OCR_FILE_TOO_LARGE"
            )

        return base64.b64encode(data).decode('utf-8'), file_size

    def _build_payload(self, image_base64: str, mime_type: str) -> dict:
        """
        构建 API 请求 payload

        Args:
            image_base64: base64 编码的图片
            mime_type: MIME 类型

        Returns:
            dict: 请求 payload
        """
        return {
            "model": self.MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "<image>\nFree OCR"
                    }
                ]
            }]
        }

    def _call_api(self, payload: dict, verbose: bool = False) -> dict:
        """
        调用硅基流动 API

        Args:
            payload: 请求数据
            verbose: 是否输出详细日志

        Returns:
            dict: API 响应
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        last_error = None

        for attempt in range(self.max_retries):
            try:
                if verbose:
                    logger.info(f"SiliconFlow API 请求 (尝试 {attempt + 1}/{self.max_retries})...")

                response = requests.post(
                    self.API_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                if verbose:
                    logger.info(f"SiliconFlow API 响应状态码: {response.status_code}")

                response.raise_for_status()
                return response.json()

            except requests.Timeout:
                last_error = SiliconFlowError(f"API 请求超时 ({self.timeout}秒)", "OCR_TIMEOUT")
                logger.warning(f"请求超时，第 {attempt + 1} 次重试...")
                time.sleep(1)

            except requests.RequestException as e:
                last_error = SiliconFlowError(f"API 请求失败: {str(e)}", "OCR_API_ERROR")
                logger.warning(f"请求异常: {e}，第 {attempt + 1} 次重试...")
                time.sleep(1)

        raise last_error

    def _parse_response(self, response: dict) -> str:
        """
        解析 API 响应，提取 Markdown 内容

        Args:
            response: API 响应

        Returns:
            str: Markdown 格式的内容
        """
        if "choices" not in response or not response["choices"]:
            raise SiliconFlowError("API 响应格式错误：无 choices", "OCR_PARSE_ERROR")

        content = response["choices"][0].get("message", {}).get("content", "")

        if not content:
            raise SiliconFlowError("API 响应内容为空", "OCR_PARSE_ERROR")

        # DeepSeek-OCR 可能返回带有特殊标记的内容，提取实际文本
        # 如果有 <|ref|>...<|/ref|> 标记，提取其中的内容
        import re
        refs = re.findall(r'<\|ref\|>(.*?)<\|/ref\|>', content, re.DOTALL)

        if refs:
            # 合并所有提取的文本
            return '\n'.join(refs)

        # 否则返回原始内容
        return content

    def detect_text_in_region(self, image_path: str, region: Tuple[float, float, float, float]) -> dict:
        """
        检测图片指定区域内的文字（使用本地方法）

        Args:
            image_path: 图片路径
            region: (x_min, y_min, x_max, y_max) 相对坐标 (0-1)

        Returns:
            dict: {"has_text": bool, "confidence": float, "text": str, "error": str}
        """
        try:
            if not HAS_PIL:
                raise ImportError("PIL (Pillow) is required for local text detection")

            if not os.path.exists(image_path):
                raise SiliconFlowError(f"图片文件不存在: {image_path}", "OCR_FILE_NOT_FOUND")

            # 验证区域参数
            x_min, y_min, x_max, y_max = region
            if not (0 <= x_min <= x_max <= 1 and 0 <= y_min <= y_max <= 1):
                raise SiliconFlowError("区域坐标无效，必须是0-1之间的相对坐标", "OCR_INVALID_REGION")

            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                img_width, img_height = img.size

                # 计算实际像素区域
                actual_x_min = int(x_min * img_width)
                actual_y_min = int(y_min * img_height)
                actual_x_max = int(x_max * img_width)
                actual_y_max = int(y_max * img_height)

                # 裁剪底部区域
                region_img = img.crop((actual_x_min, actual_y_min, actual_x_max, actual_y_max))

                # 转换为灰度图以便分析
                gray_img = region_img.convert('L')

                # 简单的文字检测方法：
                # 1. 检查是否有足够多的暗像素（文字通常是暗的）
                # 2. 检查是否有颜色变化（对比度）
                import numpy as np

                # 转换为numpy数组
                img_array = np.array(gray_img)

                # 计算暗像素比例（文字通常是黑色的）
                dark_threshold = 200  # 0-255，小于这个值的被认为是暗像素
                dark_pixels = np.sum(img_array < dark_threshold)
                dark_ratio = dark_pixels / img_array.size

                # 计算标准差（衡量图像的复杂度，有文字的区域通常更复杂）
                std_dev = np.std(img_array)

                # 计算垂直方向的变化（文字有垂直边缘）
                h_diff = np.abs(np.diff(img_array, axis=0))
                v_changes = np.sum(h_diff > 30) / h_diff.size if h_diff.size > 0 else 0

                # 综合判断是否有文字
                # 调整阈值使其更敏感
                has_text = (dark_ratio > 0.01) or (std_dev > 10) or (v_changes > 0.05)

                # 置信度计算
                if has_text:
                    confidence = min(0.9, dark_ratio * 10 + std_dev / 30 + v_changes * 3)
                else:
                    confidence = 1.0 - min(0.9, dark_ratio * 10 + std_dev / 30 + v_changes * 3)

                logger.debug(f"Text detection stats for {image_path}: "
                           f"dark_ratio={dark_ratio:.3f}, std_dev={std_dev:.1f}, v_changes={v_changes:.3f}")

                return {
                    "has_text": has_text,
                    "confidence": confidence,
                    "text": "",  # 本地方法不提取具体文字内容
                    "error": None
                }

        except Exception as e:
            logger.error(f"区域文字检测异常: {e}")
            return {
                "has_text": False,
                "confidence": 0.0,
                "text": "",
                "error": str(e)
            }

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
                raise SiliconFlowError(f"图片处理失败: {result.error}", "OCR_MERGE_ERROR")

            output_files = result.output_files

            logger.info(f"智能合并完成: {len(image_paths)} 张图片 -> {len(output_files)} 个文件")
            logger.info(f"统计: {result.statistics}")

            return output_files, len(image_paths)

        except SiliconFlowError:
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
            raise SiliconFlowError("图片合并失败", "OCR_MERGE_ERROR")

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
            # 1. 验证 API 密钥
            self._validate_api_key()

            if not image_paths:
                raise SiliconFlowError("未提供图片", "OCR_NO_INPUT")

            # 2. 验证所有图片格式
            for path in image_paths:
                self._validate_image_path(path)
                self._validate_image_format(path)

            # 3. 合并图片（如果多张）
            if len(image_paths) > 1:
                merged_paths, images_merged = self._merge_images(image_paths)
            else:
                merged_paths = [image_paths[0]]

            # 4. 对所有输出文件进行 OCR，然后合并结果
            all_markdown = []
            total_file_size = 0

            for i, target_path in enumerate(merged_paths):
                if verbose and len(merged_paths) > 1:
                    logger.info(f"正在处理第 {i+1}/{len(merged_paths)} 个文件...")

                # 获取 MIME 类型和转换为 base64
                mime_type = self._validate_image_format(target_path)
                image_base64, file_size = self._image_to_base64(target_path)
                total_file_size += file_size

                if verbose:
                    logger.info(f"  图片大小: {file_size/1024:.1f}KB, 格式: {mime_type}")

                # 5. 构建 payload 并调用 API
                payload = self._build_payload(image_base64, mime_type)

                if verbose:
                    logger.info("  正在调用硅基流动 API...")

                response = self._call_api(payload, verbose=verbose)

                # 6. 解析响应
                markdown = self._parse_response(response)
                all_markdown.append(markdown)

            # 7. 合并所有 markdown 结果
            final_markdown = "\n\n".join(all_markdown)

            # 8. 计算处理时间
            processing_time_ms = int((time.time() - start_time) * 1000)

            if verbose:
                logger.info(f"识别完成，处理了 {len(merged_paths)} 个文件，耗时: {processing_time_ms}ms")

            return self._format_response(
                success=True,
                markdown=final_markdown,
                metadata={
                    "model": self.MODEL,
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged,
                    "output_files_count": len(merged_paths),
                    "total_file_size_bytes": total_file_size
                }
            )

        except SiliconFlowError as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"SiliconFlow OCR 错误: {e.message} ({e.error_code})")
            return self._format_response(
                success=False,
                error=e.message,
                error_code=e.error_code,
                metadata={
                    "model": self.MODEL,
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
                    "model": self.MODEL,
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged
                }
            )

        # 注意：OCRMergeProcessor 生成的临时文件在 /tmp/ocr_output_* 目录下
        # 系统会定期清理 /tmp 目录，或者可以手动清理

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
            "provider": "siliconflow",
            "model": self.MODEL,
            "type": "cloud",
            "api_url": self.API_URL
        }

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """
        检查服务是否可用，返回详细信息

        Returns:
            Tuple[bool, Optional[str]]: (是否可用, 错误原因)
        """
        # 1. 检查 API 密钥
        try:
            self._validate_api_key()
        except OCRConfigurationError as e:
            return (False, f"API 密钥配置错误: {e.message}")
        except Exception as e:
            return (False, f"API 密钥验证失败: {e}")

        return (True, None)

    def is_available(self) -> bool:
        """检查服务是否可用（兼容旧接口）"""
        available, error_reason = self.check_availability()
        if not available:
            logger.debug(f"SiliconFlow服务不可用: {error_reason}")
        return available