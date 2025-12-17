"""
OCR 智能合并处理器

结合 PaddleOCR 文字检测与图片合并/分割功能：
1. 使用 PaddleOCR 精准检测每张图片的文字区域
2. 裁剪掉无文字的空白区域
3. 将裁剪后的图片智能合并
4. 可选：根据空白区域分割成多个片段

作者: Claude Code
版本: 1.0.0
"""

import os
import json
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 延迟导入
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class ProcessedImage:
    """处理后的图片信息"""
    original_path: str
    cropped_path: Optional[str] = None
    original_size: Tuple[int, int] = (0, 0)
    cropped_size: Tuple[int, int] = (0, 0)
    text_boxes_count: int = 0
    has_text: bool = False
    error: Optional[str] = None


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    output_files: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class OCRMergeProcessor:
    """
    OCR 智能合并处理器

    使用 PaddleOCR 检测文字区域，精准裁剪并合并图片。
    """

    def __init__(
        self,
        source_dir: str,
        output_dir: str = None,
        # 裁剪参数
        padding: int = 15,
        min_text_area: int = 100,
        # 合并参数
        quality: int = 95,
        spacing: int = 0,  # 默认间距 0 像素，通过 padding 避免重叠
        # 分割参数
        enable_split: bool = False,
        min_segment_height: int = 300,
        max_segment_height: int = 4000,
        # 其他参数
        keep_empty_images: bool = False,
        skip_pure_images: bool = True,  # 跳过纯图片（无文字）
        skip_sparse_regions: bool = True,  # 跳过文字稀疏区域
        min_chars_per_region: int = 5,  # 区域最小文字数量
        verbose: bool = False
    ):
        """
        初始化处理器

        Args:
            source_dir: 源图片目录
            output_dir: 输出目录
            padding: 裁剪边距
            min_text_area: 最小文字区域面积
            quality: 输出图片质量
            spacing: 合并时的间距（默认0像素，通过padding避免重叠）
            enable_split: 是否启用分割
            min_segment_height: 最小片段高度
            max_segment_height: 最大片段高度
            keep_empty_images: 是否保留无文字的图片（即使没有文字也合并）
            skip_pure_images: 跳过纯图片（无文字的图片不参与合并）
            skip_sparse_regions: 跳过文字稀疏区域（文字数少于阈值的横向区域）
            min_chars_per_region: 区域最小文字数量阈值
            verbose: 详细日志
        """
        self.source_dir = Path(source_dir).resolve()
        if not self.source_dir.exists():
            raise ValueError(f"源目录不存在: {source_dir}")

        self.output_dir = Path(output_dir) if output_dir else self.source_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 参数
        self.padding = padding
        self.min_text_area = min_text_area
        self.quality = quality
        self.spacing = spacing
        self.enable_split = enable_split
        self.min_segment_height = min_segment_height
        self.max_segment_height = max_segment_height
        self.keep_empty_images = keep_empty_images
        self.skip_pure_images = skip_pure_images
        self.skip_sparse_regions = skip_sparse_regions
        self.min_chars_per_region = min_chars_per_region
        self.verbose = verbose

        # 延迟初始化的组件
        self._detector = None
        self._merger = None
        self._splitter = None

        # 统计
        self.stats = {
            "total_images": 0,
            "images_with_text": 0,
            "images_without_text": 0,
            "images_skipped": 0,  # 跳过的纯图片数量
            "sparse_regions_skipped": 0,  # 跳过的稀疏区域数量
            "empty_images_skipped": 0,  # 跳过的空白图片数量
            "total_text_boxes": 0,
            "original_total_height": 0,
            "cropped_total_height": 0,
            "spacing_total": 0,  # 间距总高度
            "output_count": 0,
            "processing_time_ms": 0
        }

        logger.info(f"OCRMergeProcessor initialized")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")

    @property
    def detector(self):
        """延迟加载文字区域检测器"""
        if self._detector is None:
            from .text_region_detector import TextRegionDetector
            self._detector = TextRegionDetector(
                padding=self.padding,
                min_text_area=self.min_text_area
            )
        return self._detector

    @property
    def merger(self):
        """延迟加载图片合并器"""
        if self._merger is None:
            from .image_merger import ImageMerger
            self._merger = ImageMerger(
                quality=self.quality,
                spacing=self.spacing
            )
        return self._merger

    @property
    def splitter(self):
        """延迟加载图片分割器"""
        if self._splitter is None:
            from .merge_split_processor import BlankRowDetector, ImageSplitter
            self._blank_detector = BlankRowDetector()
            self._splitter = ImageSplitter(
                min_segment_height=self.min_segment_height,
                max_segment_height=self.max_segment_height
            )
        return self._splitter

    def scan_images(self) -> List[str]:
        """
        扫描并排序图片文件

        Returns:
            List[str]: 排序后的图片路径列表
        """
        import re

        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        image_files = []

        for file_path in self.source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(str(file_path))

        # 自然排序
        def natural_sort_key(path):
            p = Path(path)
            numbers = re.findall(r'\d+', p.stem)
            if numbers:
                return (p.suffix, int(numbers[-1]))
            return (p.suffix, p.name)

        image_files.sort(key=natural_sort_key)

        self.stats["total_images"] = len(image_files)
        logger.info(f"Found {len(image_files)} images")

        return image_files

    def crop_single_image(self, image_path: str) -> ProcessedImage:
        """
        裁剪单张图片的文字区域（只裁剪上下，保留原始宽度）
        支持跳过文字稀疏区域

        Args:
            image_path: 图片路径

        Returns:
            ProcessedImage: 处理结果
        """
        import cv2

        result = ProcessedImage(original_path=image_path)

        try:
            # 读取图片获取尺寸
            img = cv2.imread(image_path)
            if img is None:
                result.error = "无法读取图片"
                return result

            h, w = img.shape[:2]
            result.original_size = (w, h)

            # 根据是否跳过稀疏区域选择检测方法
            if self.skip_sparse_regions:
                # 使用带内容识别的检测方法
                text_boxes = self.detector.detect_text_with_content(image_path)
            else:
                # 只检测位置，不识别内容（更快）
                text_boxes = self.detector.detect_text_boxes(image_path)

            result.text_boxes_count = len(text_boxes)

            if not text_boxes:
                result.has_text = False
                if self.verbose:
                    logger.info(f"无文字: {Path(image_path).name}")
                return result

            result.has_text = True

            # 如果启用跳过稀疏区域，分析横向区域
            if self.skip_sparse_regions:
                regions = self.detector.analyze_horizontal_regions(text_boxes, h)

                # 过滤掉文字稀疏的区域
                dense_regions = [r for r in regions if r.total_chars >= self.min_chars_per_region]
                sparse_count = len(regions) - len(dense_regions)

                if sparse_count > 0:
                    self.stats["sparse_regions_skipped"] += sparse_count
                    if self.verbose:
                        logger.info(f"跳过 {sparse_count} 个稀疏区域: {Path(image_path).name}")

                if not dense_regions:
                    # 所有区域都是稀疏的
                    result.has_text = False
                    if self.verbose:
                        logger.info(f"全部为稀疏区域，跳过: {Path(image_path).name}")
                    return result

                # 根据密集区域计算裁剪范围
                y_min = min(r.y_min for r in dense_regions)
                y_max = max(r.y_max for r in dense_regions)
            else:
                # 不跳过稀疏区域，使用所有文字框
                y_min = min(box.y_min for box in text_boxes)
                y_max = max(box.y_max for box in text_boxes)

            # 应用 padding 并防止越界
            y1 = max(0, y_min - self.padding)
            y2 = min(h, y_max + self.padding)

            # 裁剪图片（只裁剪上下，保留完整宽度）
            cropped = img[y1:y2, 0:w]
            crop_height = y2 - y1
            result.cropped_size = (w, crop_height)

            # 保存到临时文件
            with tempfile.NamedTemporaryFile(
                suffix='.jpg',
                delete=False,
                dir=str(self.output_dir)
            ) as f:
                temp_path = f.name

            cv2.imwrite(temp_path, cropped, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            result.cropped_path = temp_path

            if self.verbose:
                logger.info(
                    f"裁剪: {Path(image_path).name} "
                    f"{w}x{h} -> {w}x{crop_height} "
                    f"({len(text_boxes)} 文字框)"
                )

            return result

        except Exception as e:
            result.error = str(e)
            logger.error(f"处理图片失败 {image_path}: {e}")
            return result

    def crop_all_images(self, image_files: List[str]) -> List[ProcessedImage]:
        """
        裁剪所有图片

        Args:
            image_files: 图片文件列表

        Returns:
            List[ProcessedImage]: 处理结果列表
        """
        results = []

        for i, image_path in enumerate(image_files):
            if self.verbose:
                logger.info(f"处理 {i+1}/{len(image_files)}: {Path(image_path).name}")

            result = self.crop_single_image(image_path)
            results.append(result)

            # 更新统计
            if result.has_text:
                self.stats["images_with_text"] += 1
                self.stats["total_text_boxes"] += result.text_boxes_count
                self.stats["original_total_height"] += result.original_size[1]
                self.stats["cropped_total_height"] += result.cropped_size[1]
            else:
                self.stats["images_without_text"] += 1

        return results

    def _should_merge_with_next(
        self,
        processed_images: List[ProcessedImage],
        index: int
    ) -> bool:
        """
        判断当前图片是否应该与下一张合并

        合并条件：
        1. 当前图片尾部有文字 AND 下一张图片头部有文字
        2. 或者表格跨行等特殊情况

        Args:
            processed_images: 处理后的图片列表
            index: 当前图片索引

        Returns:
            bool: 是否应该与下一张合并
        """
        # 如果是最后一张，不能合并
        if index >= len(processed_images) - 1:
            return False

        current = processed_images[index]
        next_img = processed_images[index + 1]

        # 必须两张图片都有文字才考虑合并
        if not (current.has_text and next_img.has_text):
            return False

        # 检测当前图片底部是否有文字
        current_has_bottom_text = self._detect_text_at_edge(
            current.original_path if not current.cropped_path else current.cropped_path,
            edge="bottom"
        )

        # 检测下一张图片头部是否有文字
        next_has_top_text = self._detect_text_at_edge(
            next_img.original_path if not next_img.cropped_path else next_img.cropped_path,
            edge="top"
        )

        # 合并条件1：底部+头部都有文字
        if current_has_bottom_text and next_has_top_text:
            if self.verbose:
                logger.info(
                    f"图片 {index + 1} 底部有文字 AND 图片 {index + 2} 头部有文字，需要合并"
                )
            return True

        # 合并条件2：两张图片文字框都很多（>30），可能是一个连续文档
        if current.text_boxes_count > 30 and next_img.text_boxes_count > 5:
            if self.verbose:
                logger.info(
                    f"图片 {index + 1}({current.text_boxes_count}框) + 图片 {index + 2}({next_img.text_boxes_count}框) 文字框较多，可能需要合并"
                )
            return True

        # 合并条件3：高图片+矮图片的组合（常见于表格跨页）
        current_height = current.original_size[1]
        next_height = next_img.original_size[1]
        if (current_height > 2000 and next_height < 500 and
            current.text_boxes_count > 10 and next_img.text_boxes_count > 3):
            if self.verbose:
                logger.info(
                    f"高图片 {index + 1}({current_height}px)+矮图片 {index + 2}({next_height}px)组合，需要合并"
                )
            return True

        if current_has_bottom_text and not next_has_top_text:
            if self.verbose:
                logger.debug(
                    f"图片 {index + 1} 底部有文字，但图片 {index + 2} 头部无文字，不合并"
                )
        elif not current_has_bottom_text and next_has_top_text:
            if self.verbose:
                logger.debug(
                    f"图片 {index + 1} 底部无文字，图片 {index + 2} 头部有文字，不合并"
                )

        return False

    def _detect_text_at_edge(self, image_path: str, edge: str = "bottom") -> bool:
        """
        检测图片边缘是否有文字

        Args:
            image_path: 图片路径
            edge: 边缘位置，"bottom" 或 "top"

        Returns:
            bool: 是否有文字
        """
        import cv2
        import numpy as np

        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                return False

            h, w = img.shape[:2]

            # 检测区域比例（使用底部20%区域）
            edge_ratio = 0.2
            edge_height = int(h * edge_ratio)

            if edge == "bottom":
                # 裁剪底部区域
                region = img[h - edge_height:h, 0:w]
            else:
                # 裁剪顶部区域
                region = img[0:edge_height, 0:w]

            # 转换为灰度
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

            # 使用 OCR 检测文字（如果有文字检测器）
            if hasattr(self.detector, 'detect_text_boxes'):
                temp_path = f"/tmp/temp_edge_{Path(image_path).stem}.jpg"
                cv2.imwrite(temp_path, region)
                text_boxes = self.detector.detect_text_boxes(temp_path)
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return len(text_boxes) > 0

            # 回退到像素统计方法
            # 计算暗像素比例（文字通常是暗色）
            dark_pixels = np.sum(gray < 200)  # 200以下的认为是暗像素
            dark_ratio = dark_pixels / (edge_height * w)

            # 计算标准差（有文字的区域变化更丰富）
            std_dev = np.std(gray)

            # 判断规则（更宽松）
            has_text = dark_ratio > 0.02 or std_dev > 10

            if self.verbose and has_text:
                logger.debug(
                    f"检测 {edge} 边缘文字: {Path(image_path).name} "
                    f"暗像素: {dark_ratio:.2%}, 标准差: {std_dev:.1f}"
                )

            return has_text

        except Exception as e:
            logger.error(f"检测边缘文字失败 {image_path}: {e}")
            return False

    def generate_smart_merge_groups(
        self,
        processed_images: List[ProcessedImage]
    ) -> List[List[int]]:
        """
        生成智能合并分组

        只合并相邻且有上下文关系的图片
        过滤掉无文字的图片（不保留）

        Args:
            processed_images: 处理后的图片列表

        Returns:
            List[List[int]]: 分组列表，每个组包含要合并的图片索引
        """
        groups = []
        i = 0
        n = len(processed_images)

        while i < n:
            # 当前图片
            current = processed_images[i]

            # 如果当前图片没有文字，跳过（不保留到输出）
            if not current.has_text:
                self.stats["empty_images_skipped"] += 1
                if self.verbose:
                    logger.info(f"跳过无文字图片: {Path(current.original_path).name}")
                i += 1
                continue

            # 如果有文字但文字框太少，可能是误检，跳过
            if current.text_boxes_count < 1:
                self.stats["empty_images_skipped"] += 1
                if self.verbose:
                    logger.info(f"跳过疑似误检图片: {Path(current.original_path).name} (文字框数: {current.text_boxes_count})")
                i += 1
                continue

            # 检查是否应该与下一张合并
            if self._should_merge_with_next(processed_images, i):
                # 创建合并组（当前+下一张）
                groups.append([i, i + 1])
                i += 2  # 跳过下一张
            else:
                # 单独一组
                groups.append([i])
                i += 1

        return groups

    def merge_cropped_images(
        self,
        processed_images: List[ProcessedImage]
    ) -> List[str]:
        """
        智能合并裁剪后的图片

        新逻辑：
        1. 检测图片间的上下文关系（当前底部+下一张头部）
        2. 只合并有上下文关系的相邻图片（如表格跨行）
        3. 其他图片保持独立

        Args:
            processed_images: 处理后的图片列表

        Returns:
            List[str]: 输出文件路径列表
        """
        output_files = []

        # 生成智能合并分组
        merge_groups = self.generate_smart_merge_groups(processed_images)

        logger.info(f"生成了 {len(merge_groups)} 个合并组")
        logger.info(f"合并策略: {len([g for g in merge_groups if len(g) > 1])} 组需要合并")

        for group_idx, group in enumerate(merge_groups):
            # 准备输入图片
            group_images = []
            group_names = []

            for idx in group:
                result = processed_images[idx]
                if result.cropped_path and os.path.exists(result.cropped_path):
                    group_images.append(result.cropped_path)
                elif result.original_path:
                    group_images.append(result.original_path)
                group_names.append(Path(result.original_path).name)

            # 生成输出文件名
            if len(group) == 1:
                # 单张图片，直接复制
                output_name = f"page_{group_idx + 1:03d}.jpg"
                reason = f"单页: {group_names[0]}"
            else:
                # 多张图片合并
                output_name = f"page_{group_idx + 1:03d}_merged.jpg"
                start_idx = group[0] + 1
                end_idx = group[-1] + 1
                reason = f"合并图片 {start_idx}-{end_idx}: {', '.join(group_names)}"

            output_path = self.output_dir / output_name

            logger.info(f"处理组 {group_idx + 1}/{len(merge_groups)}: {reason}")

            # 执行合并或复制
            if len(group_images) == 1:
                # 单张图片直接复制
                import shutil
                shutil.copy2(group_images[0], output_path)
            else:
                # 多张图片合并
                success = self.merger.merge_vertically(group_images, str(output_path))
                if not success:
                    logger.error(f"合并失败: 组 {group_idx + 1}")
                    continue

            output_files.append(str(output_path))

        # 更新统计
        merged_groups = len([g for g in merge_groups if len(g) > 1])
        self.stats["merge_groups"] = merged_groups
        self.stats["output_count"] = len(output_files)
        self.stats["spacing_total"] = self.spacing * merged_groups if merged_groups > 0 else 0

        logger.info(f"智能合并完成: {len(processed_images)} -> {len(output_files)} 文件")
        logger.info(f"  合并组数: {merged_groups}")

        return output_files

    def split_merged_image(self, merged_path: str) -> List[str]:
        """
        分割合并后的图片

        Args:
            merged_path: 合并后的图片路径

        Returns:
            List[str]: 分割后的图片路径列表
        """
        if not self.enable_split:
            return [merged_path]

        if not HAS_PIL:
            logger.warning("PIL 未安装，跳过分割")
            return [merged_path]

        from .merge_split_processor import BlankRowDetector, ImageSplitter

        try:
            with Image.open(merged_path) as img:
                # 检测空白区域
                blank_detector = BlankRowDetector()
                blank_regions = blank_detector.find_blank_regions(img)

                # 选择切割点
                splitter = ImageSplitter(
                    min_segment_height=self.min_segment_height,
                    max_segment_height=self.max_segment_height
                )
                split_points = splitter.select_split_points(
                    blank_regions,
                    img.height
                )

                if not split_points:
                    logger.info("未找到合适的切割点，保持完整图片")
                    return [merged_path]

                # 执行切割
                segments = splitter.split_image(img, split_points)

                # 保存分割后的图片
                output_files = []
                for i, segment in enumerate(segments):
                    output_name = f"segment_{i+1:03d}.jpg"
                    output_path = self.output_dir / output_name
                    segment.save(str(output_path), 'JPEG', quality=self.quality)
                    output_files.append(str(output_path))

                logger.info(f"分割完成: {len(output_files)} 个片段")

                # 删除合并的临时文件
                try:
                    os.unlink(merged_path)
                except Exception:
                    pass

                return output_files

        except Exception as e:
            logger.error(f"分割失败: {e}")
            return [merged_path]

    def cleanup_temp_files(self, processed_images: List[ProcessedImage]):
        """清理临时文件"""
        for result in processed_images:
            if result.cropped_path and os.path.exists(result.cropped_path):
                try:
                    # 检查是否是临时文件（在 output_dir 中）
                    if Path(result.cropped_path).parent == self.output_dir:
                        # 检查文件名是否是临时格式
                        if 'tmp' in result.cropped_path:
                            os.unlink(result.cropped_path)
                except Exception:
                    pass

    def generate_metadata(
        self,
        image_files: List[str],
        processed_images: List[ProcessedImage],
        output_files: List[str]
    ) -> Dict[str, Any]:
        """生成处理元数据"""
        return {
            "timestamp": datetime.now().isoformat(),
            "processor": "OCRMergeProcessor",
            "version": "1.0.0",
            "source_directory": str(self.source_dir),
            "output_directory": str(self.output_dir),
            "configuration": {
                "padding": self.padding,
                "min_text_area": self.min_text_area,
                "quality": self.quality,
                "spacing": self.spacing,
                "enable_split": self.enable_split,
                "keep_empty_images": self.keep_empty_images,
                "skip_pure_images": self.skip_pure_images,
                "skip_sparse_regions": self.skip_sparse_regions,
                "min_chars_per_region": self.min_chars_per_region
            },
            "statistics": self.stats,
            "files": {
                "input_files": [Path(f).name for f in image_files],
                "output_files": [Path(f).name for f in output_files]
            },
            "processing_details": [
                {
                    "filename": Path(r.original_path).name,
                    "has_text": r.has_text,
                    "text_boxes": r.text_boxes_count,
                    "original_size": r.original_size,
                    "cropped_size": r.cropped_size if r.has_text else None,
                    "error": r.error
                }
                for r in processed_images
            ]
        }

    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        """保存元数据"""
        metadata_path = self.output_dir / "processing_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"元数据已保存: {metadata_path}")
        return str(metadata_path)

    def process(self) -> ProcessingResult:
        """
        执行完整的处理流程

        Returns:
            ProcessingResult: 处理结果
        """
        import time
        start_time = time.time()

        try:
            # 1. 扫描图片
            logger.info("Step 1: 扫描图片...")
            image_files = self.scan_images()
            if not image_files:
                return ProcessingResult(
                    success=False,
                    error="未找到图片文件"
                )

            # 2. 裁剪所有图片
            logger.info("Step 2: 检测文字区域并裁剪...")
            processed_images = self.crop_all_images(image_files)

            # 检查是否有成功处理的图片
            successful_crops = [r for r in processed_images if r.cropped_path]
            if not successful_crops and not self.keep_empty_images:
                return ProcessingResult(
                    success=False,
                    error="所有图片都没有检测到文字",
                    statistics=self.stats
                )

            # 3. 智能合并图片
            logger.info("Step 3: 智能合并图片...")
            output_files = self.merge_cropped_images(processed_images)
            if not output_files:
                return ProcessingResult(
                    success=False,
                    error="图片合并失败",
                    statistics=self.stats
                )

            # 4. 可选：分割图片（如果只输出一个文件且启用了分割）
            if self.enable_split and len(output_files) == 1:
                logger.info("Step 4: 分割图片...")
                output_files = self.split_merged_image(output_files[0])

            # 5. 清理临时文件
            logger.info("Step 5: 清理临时文件...")
            self.cleanup_temp_files(processed_images)

            # 6. 更新统计
            self.stats["output_count"] = len(output_files)
            self.stats["processing_time_ms"] = int((time.time() - start_time) * 1000)

            # 7. 生成元数据
            metadata = self.generate_metadata(image_files, processed_images, output_files)
            metadata_path = self.save_metadata(metadata)

            logger.info("处理完成!")
            logger.info(f"统计: {self.stats}")

            return ProcessingResult(
                success=True,
                output_files=output_files,
                statistics=self.stats,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"处理失败: {e}")
            self.stats["processing_time_ms"] = int((time.time() - start_time) * 1000)
            return ProcessingResult(
                success=False,
                error=str(e),
                statistics=self.stats
            )


def create_ocr_merge_processor(source_dir: str, **kwargs) -> OCRMergeProcessor:
    """创建 OCR 合并处理器的工厂函数"""
    return OCRMergeProcessor(source_dir, **kwargs)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ocr_merge_processor.py <source_directory> [--split]")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    source_dir = sys.argv[1]
    enable_split = "--split" in sys.argv

    processor = create_ocr_merge_processor(
        source_dir,
        enable_split=enable_split,
        verbose=True
    )

    result = processor.process()

    if result.success:
        print("处理成功!")
        print(f"输出文件: {result.output_files}")
        print(f"统计: {result.statistics}")
    else:
        print(f"处理失败: {result.error}")
