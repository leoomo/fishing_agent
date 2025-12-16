"""
图片合并模块

提供图片垂直合并功能，支持多种图片格式和高质量输出。
"""

import os
import logging
from typing import List, Tuple, Optional
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    raise ImportError("PIL/Pillow is required for image merging")

logger = logging.getLogger(__name__)


class ImageMerger:
    """图片合并器

    提供图片垂直合并功能，支持：
    - 多种图片格式（jpg, png, etc.）
    - 自动尺寸调整
    - 居中对齐
    - 高质量输出
    """

    def __init__(
        self,
        quality: int = 95,
        background_color: Tuple[int, int, int] = (255, 255, 255),
        max_width: Optional[int] = None,
        spacing: int = 0
    ):
        """
        初始化图片合并器

        Args:
            quality: JPEG输出质量 (1-100)
            background_color: 背景色 (R, G, B)
            max_width: 最大宽度（None表示使用最宽图片的宽度）
            spacing: 图片间距（像素）
        """
        self.quality = max(1, min(100, quality))
        self.background_color = background_color
        self.max_width = max_width
        self.spacing = spacing

        logger.info(f"ImageMerger initialized: quality={self.quality}, max_width={self.max_width}")

    def merge_vertically(
        self,
        image_paths: List[str],
        output_path: str,
        output_format: str = 'JPEG'
    ) -> bool:
        """
        垂直合并多张图片

        Args:
            image_paths: 图片路径列表
            output_path: 输出路径
            output_format: 输出格式（JPEG/PNG）

        Returns:
            bool: 是否成功
        """
        if not image_paths:
            logger.error("No images to merge")
            return False

        try:
            # 1. 加载所有图片
            images = []
            target_width = 0
            total_height = 0

            logger.info(f"Loading {len(image_paths)} images for merging")

            for i, image_path in enumerate(image_paths):
                if not os.path.exists(image_path):
                    logger.error(f"Image not found: {image_path}")
                    return False

                # 加载图片
                with Image.open(image_path) as img:
                    # 转换为RGB模式（处理RGBA等格式）
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 创建副本以便后续操作
                    img_copy = img.copy()
                    images.append(img_copy)

                    # 计算尺寸
                    target_width = max(target_width, img_copy.width)
                    total_height += img_copy.height

                logger.debug(f"Loaded image {i+1}/{len(image_paths)}: {Path(image_path).name}")

            # 应用最大宽度限制
            if self.max_width and target_width > self.max_width:
                target_width = self.max_width
                # 重新计算总高度（考虑缩放）
                total_height = 0
                for img in images:
                    ratio = target_width / img.width
                    new_height = int(img.height * ratio)
                    total_height += new_height
                    logger.debug(f"Image will be scaled to {target_width}x{new_height}")

            # 添加间距
            total_height += self.spacing * (len(images) - 1)

            # 2. 创建合并后的图片
            logger.info(f"Creating merged image: {target_width}x{total_height}")
            merged = Image.new('RGB', (target_width, total_height), self.background_color)

            # 3. 拼接图片
            y_offset = 0
            for i, img in enumerate(images):
                # 计算缩放（如果需要）
                if self.max_width and img.width > self.max_width:
                    ratio = self.max_width / img.width
                    new_width = self.max_width
                    new_height = int(img.height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.debug(f"Resized image {i+1} to {new_width}x{new_height}")

                # 计算居中位置
                x_offset = (target_width - img.width) // 2

                # 粘贴图片
                merged.paste(img, (x_offset, y_offset))
                y_offset += img.height + self.spacing

                logger.debug(f"Pasted image {i+1} at position ({x_offset}, {y_offset - img.height - self.spacing})")

            # 4. 保存结果
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            save_kwargs = {}
            if output_format.upper() == 'JPEG':
                save_kwargs['quality'] = self.quality
                save_kwargs['optimize'] = True
            elif output_format.upper() == 'PNG':
                save_kwargs['compress_level'] = 6

            merged.save(output_path, format=output_format, **save_kwargs)

            # 5. 清理内存
            for img in images:
                img.close()
            merged.close()

            file_size = os.path.getsize(output_path)
            logger.info(f"Successfully merged {len(image_paths)} images to {output_path} ({file_size/1024/1024:.2f} MB)")

            return True

        except Exception as e:
            logger.error(f"Error merging images: {e}")
            return False

    def merge_with_text_overlay(
        self,
        image_paths: List[str],
        output_path: str,
        texts: List[str] = None,
        font_size: int = 20,
        text_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> bool:
        """
        合并图片并添加文字覆盖（可选功能）

        Args:
            image_paths: 图片路径列表
            output_path: 输出路径
            texts: 要添加的文字列表（可选）
            font_size: 字体大小
            text_color: 文字颜色

        Returns:
            bool: 是否成功
        """
        try:
            # 先执行基本合并
            if not self.merge_vertically(image_paths, output_path):
                return False

            # 如果没有文字需要添加，直接返回
            if not texts:
                return True

            # 重新打开合并后的图片添加文字
            with Image.open(output_path) as img:
                # 创建可绘制对象
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)

                # 尝试加载字体
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        # 尝试系统字体
                        font = ImageFont.load_default()
                    except:
                        font = None

                # 添加文字
                y_offset = 10
                for text in texts:
                    if font:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    else:
                        text_width = len(text) * font_size * 0.6
                        text_height = font_size

                    x_position = (img.width - text_width) // 2
                    draw.text((x_position, y_offset), text, fill=text_color, font=font)
                    y_offset += text_height + 10

                # 保存带文字的图片
                img.save(output_path, quality=self.quality, optimize=True)

            logger.info(f"Added text overlay to merged image: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error adding text overlay: {e}")
            return False

    def get_merge_info(self, image_paths: List[str]) -> dict:
        """
        获取合并信息预览

        Args:
            image_paths: 图片路径列表

        Returns:
            dict: 合并信息
        """
        try:
            if not image_paths:
                return {"error": "No images provided"}

            total_width = 0
            max_width = 0
            total_height = 0
            formats = []
            total_size = 0

            for image_path in image_paths:
                if not os.path.exists(image_path):
                    continue

                file_size = os.path.getsize(image_path)
                total_size += file_size

                with Image.open(image_path) as img:
                    max_width = max(max_width, img.width)
                    total_height += img.height
                    formats.append(img.format or 'Unknown')

            # 应用最大宽度限制
            if self.max_width and max_width > self.max_width:
                max_width = self.max_width
                # 重新计算高度
                total_height = 0
                for image_path in image_paths:
                    if not os.path.exists(image_path):
                        continue
                    with Image.open(image_path) as img:
                        ratio = self.max_width / img.width
                        total_height += int(img.height * ratio)

            # 添加间距
            total_height += self.spacing * (len(image_paths) - 1)

            return {
                "image_count": len(image_paths),
                "input_size_mb": total_size / 1024 / 1024,
                "output_dimensions": (max_width, total_height),
                "formats": list(set(formats)),
                "estimated_size_mb": (max_width * total_height * 3) / 1024 / 1024  # 粗略估算
            }

        except Exception as e:
            return {"error": str(e)}


def create_image_merger(**kwargs) -> ImageMerger:
    """创建图片合并器的工厂函数"""
    return ImageMerger(**kwargs)


if __name__ == "__main__":
    # 简单测试
    import sys

    if len(sys.argv) < 3:
        print("Usage: python image_merger.py <output_path> <image1> <image2> ...")
        sys.exit(1)

    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 创建合并器
    merger = create_image_merger(quality=95)

    # 合并图片
    output_path = sys.argv[1]
    image_paths = sys.argv[2:]

    success = merger.merge_vertically(image_paths, output_path)

    if success:
        print(f"Successfully merged {len(image_paths)} images to {output_path}")
    else:
        print("Failed to merge images")