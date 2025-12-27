"""
百度 OCR 提供商

使用百度 AI Studio API 识别图片中的表格内容
"""

import os
import base64
import time
import tempfile
import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .base import BaseOCRProvider
from .exceptions import BaiduError, OCRConfigurationError
from packages.data_processing.image import ImageMerger
from packages.data_processing.ocr import OCRMergeProcessor

logger = logging.getLogger(__name__)


class BaiduProvider(BaseOCRProvider):
    """百度 OCR 提供商（使用百度 AI Studio API）"""

    API_URL = "https://17pdfbx8mbh6jfb4.aistudio-app.com/layout-parsing"
    DEFAULT_TOKEN = "2bd26c0083441cc29419808330b3dc3ac0504376"

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}

    def __init__(self):
        """初始化百度 OCR 提供商"""
        self.token = os.getenv("BAIDU_OCR_TOKEN", self.DEFAULT_TOKEN)
        self.timeout = int(os.getenv("BAIDU_OCR_TIMEOUT", "30"))
        self.max_size = int(os.getenv("BAIDU_OCR_MAX_SIZE", str(10 * 1024 * 1024)))  # 10MB
        self.max_retries = 3

        # 初始化图片合并器
        self.image_merger = ImageMerger(quality=95)

        # 请求头
        self.headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json"
        }

        logger.info(f"BaiduProvider initialized: timeout={self.timeout}s, max_size={self.max_size/1024/1024:.1f}MB")

    def _validate_token(self) -> None:
        """验证 Token 是否已配置"""
        if not self.token:
            raise OCRConfigurationError(
                "未配置百度 OCR Token，请在 .env 中设置 BAIDU_OCR_TOKEN",
                "OCR_TOKEN_MISSING"
            )

    def _validate_image_format(self, file_path: str) -> None:
        """
        验证图片格式

        Args:
            file_path: 图片路径

        Raises:
            BaiduError: 格式不支持
        """
        ext = Path(file_path).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            raise BaiduError(
                f"不支持的图片格式: {ext}，支持格式: {', '.join(self.SUPPORTED_FORMATS)}",
                "OCR_INVALID_FORMAT"
            )

    def _validate_image_size(self, file_path: str) -> int:
        """
        验证图片大小

        Args:
            file_path: 图片路径

        Returns:
            int: 文件大小（字节）

        Raises:
            BaiduError: 文件过大
        """
        file_size = os.path.getsize(file_path)
        if file_size > self.max_size:
            raise BaiduError(
                f"图片大小 {file_size/1024/1024:.1f}MB 超过限制 {self.max_size/1024/1024:.1f}MB",
                "OCR_FILE_TOO_LARGE"
            )
        return file_size

    def _prepare_payload(self, file_path: str) -> Dict[str, Any]:
        """
        准备 API 请求载荷

        Args:
            file_path: 图片文件路径

        Returns:
            请求载荷字典
        """
        with open(file_path, "rb") as file:
            file_bytes = file.read()
            file_data = base64.b64encode(file_bytes).decode("ascii")

        # 检测文件类型
        file_ext = Path(file_path).suffix.lower()
        file_type = 0 if file_ext == '.pdf' else 1  # 0 for PDF, 1 for images

        return {
            "file": file_data,
            "fileType": file_type,
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useChartRecognition": False,
        }

    def _call_api(self, payload: dict, verbose: bool = False) -> dict:
        """
        调用百度 AI Studio API

        Args:
            payload: 请求数据
            verbose: 是否输出详细日志

        Returns:
            dict: API 响应

        Raises:
            BaiduError: API 调用失败
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if verbose:
                    logger.info(f"百度 OCR API 请求 (尝试 {attempt + 1}/{self.max_retries})...")

                response = requests.post(
                    self.API_URL,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )

                if verbose:
                    logger.info(f"百度 OCR API 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    return response.json()
                else:
                    last_error = BaiduError(
                        f"API 错误: HTTP {response.status_code} - {response.text}",
                        "OCR_API_ERROR"
                    )
                    logger.warning(f"API 返回错误: {response.status_code}，第 {attempt + 1} 次重试...")
                    time.sleep(1)

            except requests.Timeout:
                last_error = BaiduError(f"API 请求超时 ({self.timeout}秒)", "OCR_TIMEOUT")
                logger.warning(f"请求超时，第 {attempt + 1} 次重试...")
                time.sleep(1)

            except requests.RequestException as e:
                last_error = BaiduError(f"API 请求失败: {str(e)}", "OCR_API_ERROR")
                logger.warning(f"请求异常: {e}，第 {attempt + 1} 次重试...")
                time.sleep(1)

        raise last_error

    def _html_table_to_markdown(self, html_content: str) -> str:
        """
        将 HTML 表格转换为 Markdown 格式

        Args:
            html_content: HTML 内容

        Returns:
            Markdown 格式的内容
        """
        # 清理 HTML 内容
        html_content = re.sub(r'<div[^>]*>', '', html_content)
        html_content = re.sub(r'</div>', '', html_content)
        html_content = re.sub(r'<table[^>]*>', '<table>', html_content)
        html_content = re.sub(r"</?style[^>]*>", "", html_content)

        # 解析 HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找表格
        table = soup.find('table')
        if not table:
            # 如果没有表格，提取文本内容
            text = soup.get_text(strip=True)
            return text if text else "未找到内容"

        markdown_rows = []

        # 处理表格行
        for i, row in enumerate(table.find_all('tr')):
            cells = []

            # 处理单元格（th 或 td）
            for cell in row.find_all(['th', 'td']):
                text = cell.get_text(strip=True)
                text = re.sub(r'\s+', ' ', text)
                cells.append(text if text else ' ')

            if cells:
                markdown_row = '| ' + ' | '.join(cells) + ' |'
                markdown_rows.append(markdown_row)

                # 在第一行后添加分隔线
                if i == 0:
                    separator = '|' + '---|' * len(cells)
                    markdown_rows.append(separator)

        return '\n'.join(markdown_rows)

    def _parse_response(self, response: dict) -> str:
        """
        解析 API 响应，提取 Markdown 内容

        Args:
            response: API 响应

        Returns:
            str: Markdown 格式的内容

        Raises:
            BaiduError: 响应格式错误
        """
        if "result" not in response:
            raise BaiduError("API 响应格式错误：无 result 字段", "OCR_PARSE_ERROR")

        result = response["result"]

        if "layoutParsingResults" not in result:
            raise BaiduError("API 响应格式错误：无 layoutParsingResults", "OCR_PARSE_ERROR")

        contents = []

        for res in result["layoutParsingResults"]:
            if res.get("markdown", {}).get("text"):
                # 转换 HTML 为 Markdown
                html_content = res["markdown"]["text"]
                markdown_content = self._html_table_to_markdown(html_content)
                contents.append(markdown_content)

        if not contents:
            raise BaiduError("API 响应内容为空", "OCR_PARSE_ERROR")

        return "\n\n".join(contents)

    def _merge_images(self, image_paths: List[str]) -> Tuple[List[str], int]:
        """
        使用 OCRMergeProcessor 智能合并多张图片

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
            # 将所有图片复制到源目录
            import shutil
            source_dir = Path(temp_dir)
            for i, path in enumerate(image_paths):
                shutil.copy2(path, source_dir / f"{i+1}.jpg")

            # 使用 OCRMergeProcessor 处理
            # 注意：使用默认参数即可，已在 OCRMergeProcessor 中优化
            processor = OCRMergeProcessor(
                source_dir=str(source_dir),
                output_dir=output_dir,
                verbose=False
            )

            result = processor.process()

            if not result.success:
                raise BaiduError(f"图片处理失败: {result.error}", "OCR_MERGE_ERROR")

            output_files = result.output_files

            logger.info(f"智能合并完成: {len(image_paths)} 张图片 -> {len(output_files)} 个文件")
            logger.info(f"统计: {result.statistics}")

            return output_files, len(image_paths)

        except BaiduError:
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

    def _simple_merge_images(self, image_paths: List[str]) -> Tuple[List[str], int]:
        """
        简单合并模式（回退方案）
        """
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            output_path = f.name

        logger.info(f"简单合并 {len(image_paths)} 张图片...")

        success = self.image_merger.merge_vertically(image_paths, output_path)

        if not success:
            raise BaiduError("图片合并失败", "OCR_MERGE_ERROR")

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
            # 1. 验证 Token
            self._validate_token()

            if not image_paths:
                raise BaiduError("未提供图片", "OCR_NO_INPUT")

            # 2. 验证所有图片格式
            for path in image_paths:
                self._validate_image_path(path)
                self._validate_image_format(path)
                self._validate_image_size(path)

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

                file_size = os.path.getsize(target_path)
                total_file_size += file_size

                if verbose:
                    logger.info(f"  图片大小: {file_size/1024:.1f}KB")

                # 5. 准备 payload 并调用 API
                payload = self._prepare_payload(target_path)

                if verbose:
                    logger.info("  正在调用百度 OCR API...")

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
                    "model": "baidu-aistudio",
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged,
                    "output_files_count": len(merged_paths),
                    "total_file_size_bytes": total_file_size
                }
            )

        except BaiduError as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"百度 OCR 错误: {e.message} ({e.error_code})")
            return self._format_response(
                success=False,
                error=e.message,
                error_code=e.error_code,
                metadata={
                    "model": "baidu-aistudio",
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
                    "model": "baidu-aistudio",
                    "processing_time_ms": processing_time_ms,
                    "images_merged": images_merged
                }
            )

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
            "provider": "baidu",
            "model": "baidu-aistudio",
            "type": "cloud",
            "api_url": self.API_URL
        }

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """
        检查服务是否可用，返回详细信息

        Returns:
            Tuple[bool, Optional[str]]: (是否可用, 错误原因)
        """
        # 1. 检查 Token 配置
        try:
            self._validate_token()
        except OCRConfigurationError as e:
            return (False, f"配置错误: {e.message}")
        except Exception as e:
            return (False, f"Token 验证失败: {e}")

        return (True, None)

    def is_available(self) -> bool:
        """检查服务是否可用（兼容旧接口）"""
        available, error_reason = self.check_availability()
        if not available:
            logger.debug(f"百度OCR服务不可用: {error_reason}")
        return available
