"""
图片合并与分割模块

提供图片垂直合并和智能横向分割功能，支持多种图片格式和高质量输出。
"""

import os
import logging
from typing import List, Tuple, Optional
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
    HAS_NUMPY = True
except ImportError as e:
    HAS_PIL = False
    HAS_NUMPY = False
    raise ImportError("PIL/Pillow and numpy are required for image merging")

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

    # ==================== 图片分割功能 ====================

    def _analyze_row_characteristics(self, img_array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        分析每一行的特征：变化程度和平均亮度

        Args:
            img_array: 图片的numpy数组 (灰度图)

        Returns:
            Tuple[np.ndarray, np.ndarray]: (每行方差数组, 每行平均亮度数组)
        """
        # 每行的方差（变化程度）
        row_variance = np.var(img_array, axis=1)
        # 每行的平均亮度
        row_mean = np.mean(img_array, axis=1)

        return row_variance, row_mean

    def _detect_horizontal_lines(self, img_array: np.ndarray, threshold: int = 30) -> List[int]:
        """
        检测水平线（表格的横线特征）

        Args:
            img_array: 图片的numpy数组 (灰度图)
            threshold: 暗像素阈值

        Returns:
            List[int]: 检测到横线的行索引列表
        """
        horizontal_lines = []
        height, width = img_array.shape

        for y in range(height):
            row = img_array[y, :]
            # 计算暗像素比例
            dark_pixels = np.sum(row < threshold)
            dark_ratio = dark_pixels / width

            # 如果暗像素比例超过50%，认为是横线
            if dark_ratio > 0.5:
                horizontal_lines.append(y)

        return horizontal_lines

    def _detect_table_regions(
        self,
        img_array: np.ndarray,
        min_line_count: int = 3,
        max_line_gap: int = 100
    ) -> List[Tuple[int, int]]:
        """
        检测表格区域

        通过检测多条连续或接近的横线来识别表格

        Args:
            img_array: 图片的numpy数组 (灰度图)
            min_line_count: 最少横线数量才认为是表格
            max_line_gap: 横线之间最大间隔

        Returns:
            List[Tuple[int, int]]: 表格区域列表 [(start_y, end_y), ...]
        """
        horizontal_lines = self._detect_horizontal_lines(img_array)

        if len(horizontal_lines) < min_line_count:
            return []

        # 合并连续的横线点
        line_groups = []
        current_group = [horizontal_lines[0]]

        for i in range(1, len(horizontal_lines)):
            if horizontal_lines[i] - horizontal_lines[i-1] <= 3:  # 连续的横线像素
                current_group.append(horizontal_lines[i])
            else:
                if len(current_group) >= 1:
                    line_groups.append((min(current_group), max(current_group)))
                current_group = [horizontal_lines[i]]

        if current_group:
            line_groups.append((min(current_group), max(current_group)))

        if len(line_groups) < min_line_count:
            return []

        # 识别表格区域（多条横线接近的区域）
        table_regions = []
        current_table_start = line_groups[0][0]
        current_table_end = line_groups[0][1]

        for i in range(1, len(line_groups)):
            line_start, line_end = line_groups[i]
            # 如果与前一条线的间隔不超过阈值，继续扩展表格区域
            if line_start - current_table_end <= max_line_gap:
                current_table_end = line_end
            else:
                # 检查是否有足够的横线
                lines_in_region = sum(
                    1 for lg in line_groups
                    if lg[0] >= current_table_start and lg[1] <= current_table_end
                )
                if lines_in_region >= min_line_count:
                    table_regions.append((current_table_start, current_table_end))
                current_table_start = line_start
                current_table_end = line_end

        # 检查最后一个区域
        lines_in_region = sum(
            1 for lg in line_groups
            if lg[0] >= current_table_start and lg[1] <= current_table_end
        )
        if lines_in_region >= min_line_count:
            table_regions.append((current_table_start, current_table_end))

        return table_regions

    def _find_blank_regions(
        self,
        row_variance: np.ndarray,
        row_mean: np.ndarray,
        variance_threshold: float = 100,
        brightness_threshold: int = 240,
        min_height: int = 5
    ) -> List[Tuple[int, int, float]]:
        """
        寻找空白/低变化区域

        Args:
            row_variance: 每行的方差数组
            row_mean: 每行的平均亮度数组
            variance_threshold: 方差阈值，低于此值认为是低变化区域
            brightness_threshold: 亮度阈值，高于此值认为是浅色/空白
            min_height: 最小区域高度

        Returns:
            List[Tuple[int, int, float]]: 空白区域列表 [(start_y, end_y, score), ...]
            score越高表示越适合作为分割点
        """
        blank_regions = []
        height = len(row_variance)
        in_blank = False
        blank_start = 0

        for y in range(height):
            is_blank = (row_variance[y] < variance_threshold and
                       row_mean[y] > brightness_threshold)

            if is_blank and not in_blank:
                # 进入空白区域
                blank_start = y
                in_blank = True
            elif not is_blank and in_blank:
                # 离开空白区域
                if y - blank_start >= min_height:
                    # 计算分数：区域高度 + 亮度 - 方差
                    region_height = y - blank_start
                    avg_brightness = np.mean(row_mean[blank_start:y])
                    avg_variance = np.mean(row_variance[blank_start:y])
                    score = region_height * 0.5 + (avg_brightness / 255) * 30 - (avg_variance / 100) * 10
                    blank_regions.append((blank_start, y, score))
                in_blank = False

        # 处理最后一个区域
        if in_blank and height - blank_start >= min_height:
            region_height = height - blank_start
            avg_brightness = np.mean(row_mean[blank_start:height])
            avg_variance = np.mean(row_variance[blank_start:height])
            score = region_height * 0.5 + (avg_brightness / 255) * 30 - (avg_variance / 100) * 10
            blank_regions.append((blank_start, height, score))

        return blank_regions

    def _is_mostly_table(
        self,
        table_regions: List[Tuple[int, int]],
        total_height: int,
        threshold: float = 0.7
    ) -> bool:
        """
        判断图片是否大部分都是表格

        Args:
            table_regions: 表格区域列表
            total_height: 图片总高度
            threshold: 表格占比阈值

        Returns:
            bool: 是否大部分是表格
        """
        if not table_regions:
            return False

        table_height = sum(end - start for start, end in table_regions)
        table_ratio = table_height / total_height

        logger.debug(f"Table coverage: {table_ratio:.1%}")
        return table_ratio >= threshold

    def _find_best_split_point(
        self,
        height: int,
        blank_regions: List[Tuple[int, int, float]],
        table_regions: List[Tuple[int, int]],
        center_weight: float = 0.3,
        min_ratio: float = 0.3,
        max_ratio: float = 0.7
    ) -> Optional[int]:
        """
        找到最佳分割点

        Args:
            height: 图片高度
            blank_regions: 空白区域列表
            table_regions: 表格区域列表
            center_weight: 靠近中心的权重
            min_ratio: 最小分割位置比例
            max_ratio: 最大分割位置比例

        Returns:
            Optional[int]: 最佳分割点的Y坐标，None表示不应分割
        """
        if not blank_regions:
            logger.info("No blank regions found, cannot split")
            return None

        center = height / 2
        min_y = int(height * min_ratio)
        max_y = int(height * max_ratio)

        best_point = None
        best_score = float('-inf')

        for start_y, end_y, region_score in blank_regions:
            # 分割点取区域中间
            split_y = (start_y + end_y) // 2

            # 检查是否在允许范围内
            if split_y < min_y or split_y > max_y:
                continue

            # 检查是否在表格区域内
            in_table = any(
                table_start <= split_y <= table_end
                for table_start, table_end in table_regions
            )
            if in_table:
                logger.debug(f"Skip split point {split_y}: inside table region")
                continue

            # 计算综合分数
            # 1. 区域本身的分数
            # 2. 靠近中心的加分
            distance_to_center = abs(split_y - center)
            center_score = (1 - distance_to_center / center) * 100 * center_weight

            total_score = region_score + center_score

            if total_score > best_score:
                best_score = total_score
                best_point = split_y

        return best_point

    def split_horizontally(
        self,
        image_path: str,
        output_dir: str = None,
        output_format: str = 'JPEG',
        min_split_height: int = 500,
        force_split: bool = False
    ) -> List[str]:
        """
        智能横向分割图片

        将图片在自然断点或空白区域分割成两部分，
        但不会破坏表格。如果整页都是表格则不分割。

        Args:
            image_path: 输入图片路径
            output_dir: 输出目录（默认与输入同目录）
            output_format: 输出格式
            min_split_height: 最小分割高度，低于此高度不分割
            force_split: 强制在中间分割（忽略智能检测）

        Returns:
            List[str]: 输出文件路径列表，如果不分割则返回原文件路径
        """
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return [image_path]

        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                width, height = img.size

                # 检查最小高度
                if height < min_split_height:
                    logger.info(f"Image height {height} < {min_split_height}, skip splitting")
                    return [image_path]

                # 转换为灰度进行分析
                gray = img.convert('L')
                img_array = np.array(gray)

                # 分析行特征
                row_variance, row_mean = self._analyze_row_characteristics(img_array)

                # 检测表格区域
                table_regions = self._detect_table_regions(img_array)
                logger.info(f"Detected {len(table_regions)} table regions")

                # 检查是否大部分是表格
                if self._is_mostly_table(table_regions, height):
                    logger.info("Image is mostly table, skip splitting")
                    return [image_path]

                # 查找空白区域
                blank_regions = self._find_blank_regions(row_variance, row_mean)
                logger.info(f"Found {len(blank_regions)} blank regions")

                # 找到最佳分割点
                if force_split:
                    split_y = height // 2
                    logger.info(f"Force split at y={split_y}")
                else:
                    split_y = self._find_best_split_point(
                        height, blank_regions, table_regions
                    )

                if split_y is None:
                    logger.info("No suitable split point found, keep original")
                    return [image_path]

                logger.info(f"Best split point: y={split_y} ({split_y/height:.1%})")

                # 执行分割
                img_rgb = img.copy()
                top_part = img_rgb.crop((0, 0, width, split_y))
                bottom_part = img_rgb.crop((0, split_y, width, height))

                # 准备输出路径
                input_path = Path(image_path)
                if output_dir:
                    out_dir = Path(output_dir)
                else:
                    out_dir = input_path.parent
                out_dir.mkdir(parents=True, exist_ok=True)

                stem = input_path.stem
                ext = '.jpg' if output_format.upper() == 'JPEG' else '.png'

                top_path = out_dir / f"{stem}_part1{ext}"
                bottom_path = out_dir / f"{stem}_part2{ext}"

                # 保存分割后的图片
                save_kwargs = {}
                if output_format.upper() == 'JPEG':
                    save_kwargs['quality'] = self.quality
                    save_kwargs['optimize'] = True

                top_part.save(str(top_path), format=output_format, **save_kwargs)
                bottom_part.save(str(bottom_path), format=output_format, **save_kwargs)

                logger.info(f"Split into: {top_path.name} ({top_part.height}px) and {bottom_path.name} ({bottom_part.height}px)")

                return [str(top_path), str(bottom_path)]

        except Exception as e:
            logger.error(f"Error splitting image: {e}")
            return [image_path]

    def analyze_split_potential(self, image_path: str) -> dict:
        """
        分析图片的分割潜力

        Args:
            image_path: 图片路径

        Returns:
            dict: 分析结果
        """
        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                width, height = img.size
                gray = img.convert('L')
                img_array = np.array(gray)

                # 分析特征
                row_variance, row_mean = self._analyze_row_characteristics(img_array)
                table_regions = self._detect_table_regions(img_array)
                blank_regions = self._find_blank_regions(row_variance, row_mean)

                # 计算表格覆盖率
                table_coverage = sum(end - start for start, end in table_regions) / height if table_regions else 0

                # 找最佳分割点
                split_point = self._find_best_split_point(height, blank_regions, table_regions)

                return {
                    "dimensions": (width, height),
                    "table_regions": len(table_regions),
                    "table_coverage": f"{table_coverage:.1%}",
                    "blank_regions": len(blank_regions),
                    "can_split": split_point is not None,
                    "suggested_split_y": split_point,
                    "suggested_split_ratio": f"{split_point/height:.1%}" if split_point else None,
                    "is_mostly_table": self._is_mostly_table(table_regions, height)
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