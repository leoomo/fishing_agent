"""
图片下载器

负责下载爬虫获取的图片并保存到本地存储。
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse

import requests

from ..lure.image_manager import ImageManager, LocalImageStorage

logger = logging.getLogger(__name__)


class ImageDownloader:
    """图片下载器"""

    def __init__(
        self,
        image_manager: ImageManager,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        初始化图片下载器

        Args:
            image_manager: 图片管理器实例
            timeout: 下载超时时间（秒）
            max_retries: 最大重试次数
        """
        self.image_manager = image_manager
        self.storage = image_manager.storage
        self.timeout = timeout
        self.max_retries = max_retries

        # 统计信息
        self.stats = {
            "total_downloads": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "skipped_downloads": 0,
        }

        logger.info("初始化图片下载器")

    def download_and_save(
        self,
        image_url: str,
        equipment_name: str,
        image_type: str = "main",
    ) -> Optional[str]:
        """
        下载并保存图片到LocalImageStorage

        Args:
            image_url: 图片URL
            equipment_name: 装备名称（用于生成文件名）
            image_type: 图片类型（main/detail/review等）

        Returns:
            本地图片URL（file://...），失败返回None
        """
        self.stats["total_downloads"] += 1

        # 验证URL
        if not image_url or not image_url.startswith("http"):
            logger.warning(f"无效的图片URL: {image_url}")
            self.stats["skipped_downloads"] += 1
            return None

        # 检查是否已下载（基于URL哈希）
        url_hash = self._generate_url_hash(image_url)
        relative_path = f"crawler/{self._safe_filename(equipment_name)}_{image_type}_{url_hash[:8]}.jpg"

        # 检查文件是否已存在
        if self._file_exists(relative_path):
            logger.debug(f"图片已存在，跳过下载: {relative_path}")
            self.stats["skipped_downloads"] += 1
            return self.storage.get_url(relative_path)

        # 下载图片
        image_data = self._download_image(image_url)
        if not image_data:
            self.stats["failed_downloads"] += 1
            return None

        # 推断图片格式
        image_format = self._guess_image_format(image_data, image_url)
        if image_format:
            # 更新文件扩展名
            relative_path = relative_path.replace(".jpg", f".{image_format}")

        # 保存到存储
        try:
            local_url = self.storage.save(image_data, relative_path)
            self.stats["successful_downloads"] += 1
            logger.info(f"图片下载成功: {relative_path}")
            return local_url
        except Exception as e:
            logger.error(f"保存图片失败: {e}", exc_info=True)
            self.stats["failed_downloads"] += 1
            return None

    def download_multiple(
        self,
        images: list,
        equipment_name: str,
    ) -> list:
        """
        批量下载图片

        Args:
            images: 图片列表 [{"url": "...", "type": "main/detail"}]
            equipment_name: 装备名称

        Returns:
            本地图片URL列表
        """
        local_images = []

        for img in images:
            img_url = img.get("url")
            img_type = img.get("type", "main")

            if not img_url:
                continue

            local_url = self.download_and_save(img_url, equipment_name, img_type)
            if local_url:
                local_images.append({"url": local_url, "type": img_type})

        logger.info(
            f"批量下载完成: {len(local_images)}/{len(images)} 成功，装备={equipment_name}"
        )
        return local_images

    def _download_image(self, url: str) -> Optional[bytes]:
        """
        下载图片数据

        Args:
            url: 图片URL

        Returns:
            图片二进制数据，失败返回None
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"下载图片 [{attempt}/{self.max_retries}]: {url}")

                response = requests.get(
                    url,
                    timeout=self.timeout,
                    stream=True,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                )
                response.raise_for_status()

                # 检查内容类型
                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    logger.warning(f"URL不是图片: {content_type}")
                    return None

                # 读取图片数据
                image_data = response.content

                # 检查图片大小（避免下载过大文件）
                if len(image_data) > 10 * 1024 * 1024:  # 10MB
                    logger.warning(f"图片过大: {len(image_data) / 1024 / 1024:.2f} MB")
                    return None

                if len(image_data) < 100:  # 太小可能是错误
                    logger.warning(f"图片过小: {len(image_data)} bytes")
                    return None

                logger.debug(f"图片下载成功: {len(image_data)} bytes")
                return image_data

            except requests.exceptions.Timeout:
                logger.warning(f"下载超时 [{attempt}/{self.max_retries}]: {url}")
                if attempt < self.max_retries:
                    continue

            except requests.exceptions.RequestException as e:
                logger.warning(f"下载失败 [{attempt}/{self.max_retries}]: {e}")
                if attempt < self.max_retries:
                    continue

        logger.error(f"图片下载最终失败: {url}")
        return None

    def _guess_image_format(self, image_data: bytes, url: str) -> Optional[str]:
        """
        推断图片格式

        Args:
            image_data: 图片二进制数据
            url: 图片URL

        Returns:
            图片格式（jpg/png/webp等）
        """
        # 方法1: 从文件头推断（Magic Number）
        if image_data[:2] == b"\xff\xd8":
            return "jpg"
        elif image_data[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        elif image_data[:4] == b"RIFF" and image_data[8:12] == b"WEBP":
            return "webp"
        elif image_data[:2] == b"BM":
            return "bmp"
        elif image_data[:6] in (b"GIF87a", b"GIF89a"):
            return "gif"

        # 方法2: 从URL推断
        url_lower = url.lower()
        for ext in ["jpg", "jpeg", "png", "webp", "gif", "bmp"]:
            if f".{ext}" in url_lower:
                return "jpg" if ext == "jpeg" else ext

        # 默认jpg
        return "jpg"

    def _safe_filename(self, name: str) -> str:
        """
        生成安全的文件名（移除特殊字符）

        Args:
            name: 原始名称

        Returns:
            安全的文件名
        """
        # 移除非字母数字字符
        safe_name = re.sub(r"[^\w\s-]", "", name)
        # 替换空格为下划线
        safe_name = re.sub(r"[\s]+", "_", safe_name)
        # 限制长度
        safe_name = safe_name[:50]
        return safe_name

    def _generate_url_hash(self, url: str) -> str:
        """
        生成URL哈希（用于去重）

        Args:
            url: 图片URL

        Returns:
            MD5哈希值
        """
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def _file_exists(self, relative_path: str) -> bool:
        """
        检查文件是否已存在

        Args:
            relative_path: 相对路径

        Returns:
            是否存在
        """
        try:
            # 获取完整路径
            full_path = Path(self.storage.base_dir) / relative_path
            return full_path.exists() and full_path.is_file()
        except Exception:
            return False

    def get_stats(self) -> Dict[str, int]:
        """获取下载统计信息"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_downloads": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "skipped_downloads": 0,
        }
        logger.info("下载统计已重置")
