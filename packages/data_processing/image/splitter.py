"""
合并切割处理器

新策略：先合并所有图片 -> 删除无文字区域 -> 按空白切割
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

try:
    from PIL import Image
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from .merger import ImageMerger

logger = logging.getLogger(__name__)


@dataclass
class BlankRegion:
    """空白区域"""
    start: int      # 起始行
    end: int        # 结束行
    center: int     # 中心点（切割位置）
    height: int     # 区域高度


@dataclass
class ContentRegion:
    """内容区域"""
    start: int      # 起始行
    end: int        # 结束行
    height: int     # 区域高度


class BlankRowDetector:
    """空白行检测器"""

    def __init__(
        self,
        brightness_threshold: int = 250,
        min_blank_rows: int = 10,
        max_removable_blank: int = 100,
        edge_margin: int = 50
    ):
        """
        初始化空白行检测器

        Args:
            brightness_threshold: 亮度阈值，像素RGB平均值超过此值认为是空白
            min_blank_rows: 切割点最小连续空白行数
            max_removable_blank: 可删除的空白区域最小高度
            edge_margin: 边缘忽略像素数
        """
        self.brightness_threshold = brightness_threshold
        self.min_blank_rows = min_blank_rows
        self.max_removable_blank = max_removable_blank
        self.edge_margin = edge_margin

    def _is_blank_row(self, row_pixels: np.ndarray) -> bool:
        """
        检测行是否为空白行

        Args:
            row_pixels: 行像素数据 (width, 3)

        Returns:
            bool: 是否为空白行
        """
        # 忽略边缘
        if len(row_pixels) > self.edge_margin * 2:
            center_pixels = row_pixels[self.edge_margin:-self.edge_margin]
        else:
            center_pixels = row_pixels

        # 计算平均亮度
        avg_brightness = np.mean(center_pixels)
        return avg_brightness > self.brightness_threshold

    def find_blank_regions(self, image: Image.Image) -> List[BlankRegion]:
        """
        查找所有连续空白区域

        Args:
            image: PIL图片对象

        Returns:
            List[BlankRegion]: 空白区域列表
        """
        if not HAS_PIL:
            return []

        pixels = np.array(image)
        height = pixels.shape[0]

        blank_regions = []
        current_start = None

        for y in range(height):
            row = pixels[y]
            is_blank = self._is_blank_row(row)

            if is_blank:
                if current_start is None:
                    current_start = y
            else:
                if current_start is not None:
                    region_height = y - current_start
                    if region_height >= self.min_blank_rows:
                        blank_regions.append(BlankRegion(
                            start=current_start,
                            end=y,
                            center=(current_start + y) // 2,
                            height=region_height
                        ))
                    current_start = None

        # 处理最后一个区域
        if current_start is not None:
            region_height = height - current_start
            if region_height >= self.min_blank_rows:
                blank_regions.append(BlankRegion(
                    start=current_start,
                    end=height,
                    center=(current_start + height) // 2,
                    height=region_height
                ))

        logger.info(f"Found {len(blank_regions)} blank regions")
        return blank_regions

    def find_content_regions(self, image: Image.Image) -> List[ContentRegion]:
        """
        查找所有有内容的区域

        Args:
            image: PIL图片对象

        Returns:
            List[ContentRegion]: 内容区域列表
        """
        if not HAS_PIL:
            return []

        pixels = np.array(image)
        height = pixels.shape[0]

        content_regions = []
        current_start = None

        for y in range(height):
            row = pixels[y]
            has_content = not self._is_blank_row(row)

            if has_content:
                if current_start is None:
                    current_start = y
            else:
                if current_start is not None:
                    region_height = y - current_start
                    content_regions.append(ContentRegion(
                        start=current_start,
                        end=y,
                        height=region_height
                    ))
                    current_start = None

        # 处理最后一个区域
        if current_start is not None:
            region_height = height - current_start
            content_regions.append(ContentRegion(
                start=current_start,
                end=height,
                height=region_height
            ))

        logger.info(f"Found {len(content_regions)} content regions")
        return content_regions


class ImageSplitter:
    """图片切割器"""

    def __init__(
        self,
        min_segment_height: int = 300,
        max_segment_height: int = 4000
    ):
        """
        初始化图片切割器

        Args:
            min_segment_height: 最小片段高度
            max_segment_height: 最大片段高度
        """
        self.min_segment_height = min_segment_height
        self.max_segment_height = max_segment_height

    def select_split_points(
        self,
        blank_regions: List[BlankRegion],
        image_height: int
    ) -> List[int]:
        """
        选择切割点

        Args:
            blank_regions: 空白区域列表
            image_height: 图片总高度

        Returns:
            List[int]: 切割点y坐标列表
        """
        if not blank_regions:
            return []

        split_points = []
        last_split = 0

        for region in blank_regions:
            # 跳过图片顶部和底部的空白
            if region.start < self.min_segment_height:
                continue
            if region.end > image_height - self.min_segment_height:
                continue

            # 计算如果在此切割，前一片段的高度
            segment_height = region.center - last_split

            # 确保片段不会太小
            if segment_height < self.min_segment_height:
                continue

            # 添加切割点
            split_points.append(region.center)
            last_split = region.center

        # 过滤太小的最后一个片段
        split_points = self._filter_small_segments(split_points, image_height)

        logger.info(f"Selected {len(split_points)} split points")
        return split_points

    def _filter_small_segments(
        self,
        split_points: List[int],
        image_height: int
    ) -> List[int]:
        """
        过滤太小的片段

        Args:
            split_points: 切割点列表
            image_height: 图片总高度

        Returns:
            List[int]: 过滤后的切割点列表
        """
        if not split_points:
            return []

        filtered = []
        points = [0] + split_points + [image_height]

        for i in range(1, len(points) - 1):
            prev_point = filtered[-1] if filtered else 0
            current_point = points[i]
            next_point = points[i + 1]

            # 当前片段高度
            current_height = current_point - prev_point
            # 下一片段高度
            next_height = next_point - current_point

            # 如果下一片段太小，跳过当前切割点
            if next_height < self.min_segment_height:
                continue

            # 如果当前片段太小，也跳过
            if current_height < self.min_segment_height:
                continue

            filtered.append(current_point)

        return filtered

    def split_image(
        self,
        image: Image.Image,
        split_points: List[int]
    ) -> List[Image.Image]:
        """
        执行图片切割

        Args:
            image: 要切割的图片
            split_points: 切割点列表

        Returns:
            List[Image.Image]: 切割后的图片列表
        """
        if not HAS_PIL:
            return [image]

        segments = []
        width, height = image.size

        # 添加起始和结束位置
        points = [0] + split_points + [height]

        for i in range(len(points) - 1):
            start_y = points[i]
            end_y = points[i + 1]

            # 跳过空片段
            if end_y <= start_y:
                continue

            # 裁剪图片
            segment = image.crop((0, start_y, width, end_y))
            segments.append(segment)

            logger.debug(f"Created segment {i+1}: y={start_y}-{end_y}, height={end_y-start_y}")

        logger.info(f"Split image into {len(segments)} segments")
        return segments


class MergeAndSplitProcessor:
    """合并切割处理器

    新策略：先合并所有图片 -> 删除无文字区域 -> 按空白切割
    支持分批处理，避免超过 JPEG 高度限制。
    """

    # JPEG 最大高度限制，留一些余量
    MAX_MERGE_HEIGHT = 60000

    def __init__(
        self,
        source_dir: str,
        output_dir: str = None,
        quality: int = 95,
        # 空白检测参数
        brightness_threshold: int = 250,
        min_blank_rows: int = 10,
        max_removable_blank: int = 100,
        edge_margin: int = 50,
        # 切割参数
        min_segment_height: int = 300,
        max_segment_height: int = 4000,
        # 分批参数
        max_merge_height: int = None
    ):
        """
        初始化合并切割处理器

        Args:
            source_dir: 源图片目录
            output_dir: 输出目录
            quality: 输出图片质量
            brightness_threshold: 亮度阈值
            min_blank_rows: 切割点最小连续空白行数
            max_removable_blank: 可删除的空白区域最小高度
            edge_margin: 边缘忽略像素
            min_segment_height: 最小片段高度
            max_segment_height: 最大片段高度
            max_merge_height: 单批次最大合并高度（默认60000，避免超过JPEG限制）
        """
        self.source_dir = Path(source_dir).resolve()
        if not self.source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")

        self.output_dir = Path(output_dir) if output_dir else self.source_dir / "split"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.quality = quality
        self.max_merge_height = max_merge_height or self.MAX_MERGE_HEIGHT

        # 初始化组件
        self.image_merger = ImageMerger(quality=quality, spacing=0)
        self.blank_detector = BlankRowDetector(
            brightness_threshold=brightness_threshold,
            min_blank_rows=min_blank_rows,
            max_removable_blank=max_removable_blank,
            edge_margin=edge_margin
        )
        self.splitter = ImageSplitter(
            min_segment_height=min_segment_height,
            max_segment_height=max_segment_height
        )

        # 配置
        self.brightness_threshold = brightness_threshold
        self.min_blank_rows = min_blank_rows
        self.max_removable_blank = max_removable_blank
        self.edge_margin = edge_margin
        self.min_segment_height = min_segment_height
        self.max_segment_height = max_segment_height

        # 统计
        self.stats = {
            "total_images": 0,
            "merged_height": 0,
            "cleaned_height": 0,
            "output_count": 0,
            "blank_regions_removed": 0
        }

        logger.info(f"MergeAndSplitProcessor initialized")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")

    def scan_images(self) -> List[str]:
        """
        扫描并排序图片文件

        Returns:
            List[str]: 排序后的图片路径列表
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        image_files = []

        for file_path in self.source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(str(file_path))

        # 自然排序
        image_files.sort(key=self._natural_sort_key)

        self.stats["total_images"] = len(image_files)
        logger.info(f"Found {len(image_files)} images")

        return image_files

    def _natural_sort_key(self, file_path: str):
        """自然排序键"""
        import re
        path = Path(file_path)
        numbers = re.findall(r'\d+', path.stem)
        if numbers:
            return (path.suffix, int(numbers[-1]))
        return (path.suffix, path.name)

    def _get_image_heights(self, image_files: List[str]) -> List[int]:
        """
        获取所有图片的高度

        Args:
            image_files: 图片路径列表

        Returns:
            List[int]: 高度列表
        """
        heights = []
        for path in image_files:
            try:
                with Image.open(path) as img:
                    heights.append(img.height)
            except Exception as e:
                logger.warning(f"Failed to get height for {path}: {e}")
                heights.append(0)
        return heights

    def _create_batches(
        self,
        image_files: List[str],
        heights: List[int]
    ) -> List[List[str]]:
        """
        将图片分成多个批次，每批次合并高度不超过限制

        Args:
            image_files: 图片路径列表
            heights: 对应的高度列表

        Returns:
            List[List[str]]: 批次列表，每个批次是图片路径列表
        """
        batches = []
        current_batch = []
        current_height = 0

        for path, height in zip(image_files, heights):
            # 如果添加这张图片会超过限制，开始新批次
            if current_height + height > self.max_merge_height and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_height = 0

            current_batch.append(path)
            current_height += height

        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)

        logger.info(f"Split {len(image_files)} images into {len(batches)} batches")
        for i, batch in enumerate(batches):
            batch_height = sum(heights[image_files.index(p)] for p in batch)
            logger.info(f"  Batch {i+1}: {len(batch)} images, ~{batch_height}px")

        return batches

    def _process_batch(
        self,
        batch_files: List[str],
        batch_index: int
    ) -> List[Image.Image]:
        """
        处理单个批次：合并 -> 删除空白 -> 切割

        Args:
            batch_files: 批次内的图片路径列表
            batch_index: 批次索引

        Returns:
            List[Image.Image]: 切割后的图片列表
        """
        import tempfile

        logger.info(f"Processing batch {batch_index + 1} with {len(batch_files)} images...")

        # 1. 合并批次内的图片
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            merged_path = f.name

        try:
            success = self.image_merger.merge_vertically(batch_files, merged_path)
            if not success:
                logger.error(f"Failed to merge batch {batch_index + 1}")
                return []

            # 2. 加载合并后的图片
            with Image.open(merged_path) as merged_image:
                batch_merged_height = merged_image.height
                self.stats["merged_height"] += batch_merged_height
                logger.info(f"Batch {batch_index + 1} merged: {merged_image.width}x{batch_merged_height}")

                # 3. 删除无文字区域
                cleaned_image = self.remove_blank_regions(merged_image)
                self.stats["cleaned_height"] += cleaned_image.height

                # 4. 检测空白区域（用于切割）
                blank_regions = self.blank_detector.find_blank_regions(cleaned_image)

                # 5. 选择切割点
                split_points = self.splitter.select_split_points(
                    blank_regions,
                    cleaned_image.height
                )

                # 6. 执行切割
                segments = self.splitter.split_image(cleaned_image, split_points)

                # 复制segments，因为cleaned_image会被关闭
                result_segments = []
                for seg in segments:
                    result_segments.append(seg.copy())

                return result_segments

        finally:
            # 清理临时文件
            try:
                os.unlink(merged_path)
            except Exception:
                pass

    def remove_blank_regions(self, image: Image.Image) -> Image.Image:
        """
        删除图片中的大片空白区域

        Args:
            image: 输入图片

        Returns:
            Image.Image: 删除空白后的图片
        """
        if not HAS_PIL:
            return image

        # 找到所有内容区域
        content_regions = self.blank_detector.find_content_regions(image)

        if not content_regions:
            logger.warning("No content regions found, returning original image")
            return image

        width, original_height = image.size

        # 合并相邻的内容区域（允许小间隙）
        merged_regions = self._merge_adjacent_regions(content_regions)

        # 计算新图片高度
        new_height = sum(r.height for r in merged_regions)

        # 创建新图片
        new_image = Image.new('RGB', (width, new_height), (255, 255, 255))

        # 复制内容区域
        y_offset = 0
        for region in merged_regions:
            segment = image.crop((0, region.start, width, region.end))
            new_image.paste(segment, (0, y_offset))
            y_offset += region.height

        removed_height = original_height - new_height
        self.stats["blank_regions_removed"] = removed_height

        logger.info(f"Removed {removed_height}px blank regions ({original_height} -> {new_height})")

        return new_image

    def _merge_adjacent_regions(
        self,
        regions: List[ContentRegion],
        gap_threshold: int = 50
    ) -> List[ContentRegion]:
        """
        合并相邻的内容区域

        Args:
            regions: 内容区域列表
            gap_threshold: 间隙阈值，小于此值的间隙会被保留

        Returns:
            List[ContentRegion]: 合并后的区域列表
        """
        if not regions:
            return []

        merged = []
        current = regions[0]

        for next_region in regions[1:]:
            gap = next_region.start - current.end

            if gap <= gap_threshold:
                # 合并区域（包含间隙）
                current = ContentRegion(
                    start=current.start,
                    end=next_region.end,
                    height=next_region.end - current.start
                )
            else:
                merged.append(current)
                current = next_region

        merged.append(current)
        return merged

    def save_segments(
        self,
        segments: List[Image.Image]
    ) -> List[str]:
        """
        保存切割后的图片

        Args:
            segments: 切割后的图片列表

        Returns:
            List[str]: 输出文件路径列表
        """
        output_files = []

        for i, segment in enumerate(segments):
            output_name = f"segment_{i+1:03d}.jpg"
            output_path = self.output_dir / output_name

            segment.save(str(output_path), 'JPEG', quality=self.quality, optimize=True)
            output_files.append(str(output_path))

            logger.debug(f"Saved: {output_name}")

        self.stats["output_count"] = len(output_files)
        logger.info(f"Saved {len(output_files)} segments")

        return output_files

    def generate_metadata(
        self,
        image_files: List[str],
        blank_regions: List[BlankRegion],
        split_points: List[int],
        output_files: List[str]
    ) -> Dict[str, Any]:
        """
        生成处理元数据

        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "strategy": "merge_split",
            "source_directory": str(self.source_dir),
            "output_directory": str(self.output_dir),
            "configuration": {
                "quality": self.quality,
                "brightness_threshold": self.brightness_threshold,
                "min_blank_rows": self.min_blank_rows,
                "max_removable_blank": self.max_removable_blank,
                "edge_margin": self.edge_margin,
                "min_segment_height": self.min_segment_height,
                "max_segment_height": self.max_segment_height
            },
            "statistics": self.stats,
            "files": {
                "input_files": [Path(f).name for f in image_files],
                "output_files": [Path(f).name for f in output_files]
            },
            "blank_regions": [
                {"start": r.start, "end": r.end, "height": r.height}
                for r in blank_regions
            ],
            "split_points": split_points
        }

        return metadata

    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        保存元数据到文件

        Returns:
            str: 元数据文件路径
        """
        metadata_path = self.output_dir / "split_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Metadata saved to: {metadata_path}")
        return str(metadata_path)

    def process(self) -> Dict[str, Any]:
        """
        执行完整的处理流程

        Returns:
            Dict[str, Any]: 处理结果
        """
        import tempfile

        try:
            # 1. 扫描图片
            image_files = self.scan_images()
            if not image_files:
                logger.warning("No images found in source directory")
                return {"success": False, "error": "No images found"}

            # 2. 合并所有图片
            logger.info("Step 1: Merging all images...")
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                merged_path = f.name

            success = self.image_merger.merge_vertically(image_files, merged_path)
            if not success:
                return {"success": False, "error": "Failed to merge images"}

            # 3. 加载合并后的图片
            with Image.open(merged_path) as merged_image:
                self.stats["merged_height"] = merged_image.height
                logger.info(f"Merged image size: {merged_image.width}x{merged_image.height}")

                # 4. 删除无文字区域
                logger.info("Step 2: Removing blank regions...")
                cleaned_image = self.remove_blank_regions(merged_image)
                self.stats["cleaned_height"] = cleaned_image.height

                # 5. 检测空白区域（用于切割）
                logger.info("Step 3: Finding split points...")
                blank_regions = self.blank_detector.find_blank_regions(cleaned_image)

                # 6. 选择切割点
                split_points = self.splitter.select_split_points(
                    blank_regions,
                    cleaned_image.height
                )

                # 7. 执行切割
                logger.info("Step 4: Splitting image...")
                segments = self.splitter.split_image(cleaned_image, split_points)

            # 8. 保存切割后的图片
            logger.info("Step 5: Saving segments...")
            output_files = self.save_segments(segments)

            # 9. 生成元数据
            metadata = self.generate_metadata(
                image_files,
                blank_regions,
                split_points,
                output_files
            )

            # 10. 保存元数据
            metadata_path = self.save_metadata(metadata)

            # 11. 清理临时文件
            try:
                os.unlink(merged_path)
            except Exception:
                pass

            logger.info("Processing completed successfully")

            return {
                "success": True,
                "metadata_path": metadata_path,
                "statistics": self.stats,
                "output_files": output_files
            }

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def create_merge_split_processor(source_dir: str, **kwargs) -> MergeAndSplitProcessor:
    """创建合并切割处理器的工厂函数"""
    return MergeAndSplitProcessor(source_dir, **kwargs)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python merge_split_processor.py <source_directory>")
        sys.exit(1)

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建处理器
    processor = create_merge_split_processor(sys.argv[1])

    # 执行处理
    result = processor.process()

    if result["success"]:
        print("Processing completed successfully!")
        print(f"Statistics: {result['statistics']}")
        print(f"Output files: {len(result['output_files'])}")
    else:
        print(f"Processing failed: {result['error']}")
