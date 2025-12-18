"""
批处理图片合并管理器

整合图片合并功能，实现智能批处理。
"""

import os
import json
import logging
from typing import List, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

from .image_merger import ImageMerger

# 导入PIL用于图片处理
try:
    from PIL import Image, ImageStat
    import numpy as np
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


logger = logging.getLogger(__name__)


class MergeGroup:
    """合并组信息"""

    def __init__(self, indices: List[int], reason: str = ""):
        self.indices = indices
        self.reason = reason
        self.source_files = []
        self.output_file = ""
        # 分割相关属性
        self.was_split = False
        self.split_files = []

    def __len__(self):
        return len(self.indices)

    def __str__(self):
        split_info = f", split={self.was_split}" if self.was_split else ""
        return f"MergeGroup({self.indices}, reason='{self.reason}'{split_info})"


class BatchMergeProcessor:
    """批处理合并管理器

    负责：
    1. 扫描和排序图片文件
    2. 生成分组合并策略
    3. 执行图片合并
    4. 生成元数据
    """

    def __init__(
        self,
        source_dir: str,
        output_dir: str = None,
        quality: int = 95,
        # 智能分组配置参数
        bottom_detection_ratio: float = 0.2,  # 底部检测区域比例
        ocr_confidence_threshold: float = 0.5,  # OCR置信度阈值
        min_text_length: int = 2,  # 最小文字长度
        parallel_detection: bool = True,  # 是否并行检测
        max_workers: int = 4,  # 并行检测的最大线程数
        # 分割配置参数
        enable_split: bool = True,  # 是否启用合并后分割
        min_split_height: int = 800,  # 最小分割高度（像素）
        split_min_ratio: float = 0.3,  # 分割点最小位置比例
        split_max_ratio: float = 0.7,  # 分割点最大位置比例
        # 合并限制参数
        max_merge_count: int = 3,  # 每组最多合并的图片数量
        # 文字过滤参数
        skip_low_text_images: bool = True,  # 是否跳过文字过少的图片
        min_char_threshold: int = 3,  # 最小字符数阈值，≤此值的图片将被丢弃
        # 空白区域裁剪参数
        crop_blank_regions: bool = True,  # 是否裁剪空白区域
        crop_padding: int = 20  # 裁剪保留的边距（像素）
    ):
        """
        初始化批处理管理器

        Args:
            source_dir: 源图片目录
            output_dir: 输出目录（默认为源目录下的merged子目录）
            quality: 输出图片质量
            bottom_detection_ratio: 底部检测区域比例（0-1）
            ocr_confidence_threshold: OCR置信度阈值（0-1）
            min_text_length: 最小文字长度
            parallel_detection: 是否并行检测
            max_workers: 并行检测的最大线程数
            enable_split: 是否启用合并后分割
            min_split_height: 最小分割高度（像素），低于此高度不分割
            split_min_ratio: 分割点最小位置比例（0-1）
            split_max_ratio: 分割点最大位置比例（0-1）
            max_merge_count: 每组最多合并的图片数量（默认3张）
            skip_low_text_images: 是否跳过文字过少的图片
            min_char_threshold: 最小字符数阈值，≤此值的图片将被丢弃
            crop_blank_regions: 是否裁剪空白区域
            crop_padding: 裁剪保留的边距（像素）
        """
        self.source_dir = Path(source_dir).resolve()
        if not self.source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")

        self.output_dir = Path(output_dir) if output_dir else self.source_dir / "merged"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.image_merger = ImageMerger(quality=quality)

        # 智能分组配置
        self.smart_grouping_enabled = True  # 强制启用智能分组
        self.bottom_detection_ratio = bottom_detection_ratio
        self.ocr_confidence_threshold = ocr_confidence_threshold
        self.min_text_length = min_text_length
        self.parallel_detection = parallel_detection
        self.max_workers = max_workers

        # 分割配置
        self.enable_split = enable_split
        self.min_split_height = min_split_height
        self.split_min_ratio = split_min_ratio
        self.split_max_ratio = split_max_ratio

        # 合并限制
        self.max_merge_count = max_merge_count

        # 文字过滤配置
        self.skip_low_text_images = skip_low_text_images
        self.min_char_threshold = min_char_threshold

        # 空白区域裁剪配置
        self.crop_blank_regions = crop_blank_regions
        self.crop_padding = crop_padding

        # 缓存检测结果
        self._text_detection_cache = {}

        # 处理统计
        self.stats = {
            "total_images": 0,
            "merge_groups": 0,
            "original_count": 0,
            "output_count": 0,
            "smart_grouping_enabled": True,
            "text_detections": 0,
            "cache_hits": 0,
            "split_enabled": enable_split,
            "images_split": 0,
            "split_skipped_table": 0,
            "split_skipped_no_point": 0,
            # 新增统计
            "images_discarded_low_text": 0,  # 因文字过少被丢弃的图片数
            "images_cropped": 0,  # 被裁剪的图片数
            "crop_saved_height": 0  # 裁剪节省的总高度（像素）
        }

        logger.info(f"BatchMergeProcessor initialized")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Smart grouping: ENABLED")
        logger.info(f"Bottom detection ratio: {self.bottom_detection_ratio}")
        logger.info(f"OCR confidence threshold: {self.ocr_confidence_threshold}")
        logger.info(f"Post-merge split: {'ENABLED' if enable_split else 'DISABLED'}")
        if enable_split:
            logger.info(f"Min split height: {min_split_height}px")
        logger.info(f"Max merge count per group: {max_merge_count}")
        logger.info(f"Skip low text images: {'ENABLED' if skip_low_text_images else 'DISABLED'}")
        if skip_low_text_images:
            logger.info(f"Min char threshold: {min_char_threshold}")
        logger.info(f"Crop blank regions: {'ENABLED' if crop_blank_regions else 'DISABLED'}")
        if crop_blank_regions:
            logger.info(f"Crop padding: {crop_padding}px")

    def _detect_text_by_filename(self, image_path: str) -> dict:
        """
        基于文件名规则检测
        规则：如果是奇数文件名，通常需要与下一个合并
        """
        try:
            filename = Path(image_path).name
            stem = Path(filename).stem  # 不包含扩展名

            # 提取数字
            numbers = re.findall(r'\d+', stem)
            if numbers:
                # 获取最后一个数字
                number = int(numbers[-1])

                # 如果是奇数，通常需要与下一个合并
                if number % 2 == 1:
                    return {
                        "has_text": True,
                        "confidence": 0.6,
                        "text": f"检测到奇数编号: {number}",
                        "error": None
                    }

            return {
                "has_text": False,
                "confidence": 0.4,
                "text": "",
                "error": None
            }

        except Exception as e:
            return {
                "has_text": False,
                "confidence": 0.0,
                "text": "",
                "error": str(e)
            }

    def _detect_text_in_region(self, image_path: str, region: str = "bottom") -> dict:
        """
        基于图像特征检测指定区域是否有文字

        使用边缘检测来识别文字特征：
        - 文字区域有较高的边缘密度
        - 文字边缘通常是细密的、高对比度的
        - 纯图片区域边缘更平滑或不规则

        Args:
            image_path: 图片路径
            region: 检测区域，"bottom"表示底部，"top"表示头部
        """
        if not HAS_PIL:
            return {
                "has_text": False,
                "confidence": 0.0,
                "text": "",
                "error": "PIL not available"
            }

        try:
            from PIL import ImageFilter

            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                width, height = img.size

                # 根据区域裁剪
                region_height = int(height * self.bottom_detection_ratio)
                if region == "bottom":
                    # 裁剪底部区域
                    crop_region = img.crop((0, height - region_height, width, height))
                else:
                    # 裁剪头部区域
                    crop_region = img.crop((0, 0, width, region_height))

                # 转换为灰度
                gray = crop_region.convert('L')
                pixels = np.array(gray)

                # 1. 边缘检测：检测文字的边缘特征
                edges = gray.filter(ImageFilter.FIND_EDGES)
                edge_pixels = np.array(edges)
                edge_density = np.mean(edge_pixels) / 255  # 边缘密度 0-1

                # 2. 强边缘比例：文字有更多清晰的边缘
                strong_edges = np.sum(edge_pixels > 50)
                strong_edge_ratio = strong_edges / edge_pixels.size

                # 3. 行变化分析：文字区域每行的变化较大
                row_stds = np.std(pixels, axis=1)  # 每行的标准差
                avg_row_std = np.mean(row_stds)

                # 4. 深色背景检测：灰色/深色背景上的文字（如表格标题行）
                dark_pixel_ratio = np.sum(pixels < 100) / pixels.size
                light_pixel_ratio = np.sum(pixels > 200) / pixels.size
                # 如果大部分是深色但有少量亮色（文字），可能是深色背景文字
                has_dark_bg_text = dark_pixel_ratio > 0.5 and light_pixel_ratio > 0.05

                # 综合评分判断
                text_score = 0

                # 边缘密度评分（0-40分）
                if edge_density > 0.15:
                    text_score += 40
                elif edge_density > 0.10:
                    text_score += 30
                elif edge_density > 0.05:
                    text_score += 20
                elif edge_density > 0.03:
                    text_score += 10

                # 强边缘比例评分（0-30分）
                if strong_edge_ratio > 0.10:
                    text_score += 30
                elif strong_edge_ratio > 0.05:
                    text_score += 20
                elif strong_edge_ratio > 0.02:
                    text_score += 10

                # 行变化评分（0-30分）
                if avg_row_std > 50:
                    text_score += 30
                elif avg_row_std > 35:
                    text_score += 20
                elif avg_row_std > 20:
                    text_score += 10

                # 判断阈值：总分超过40认为有文字
                has_text = text_score >= 40
                # 置信度计算：确保达到阈值的评分置信度不低于0.5
                confidence = min(0.95, max(0.5, text_score / 100)) if has_text else text_score / 100

                detail = (f"{region}区域 - 边缘密度: {edge_density:.2%}, "
                         f"强边缘: {strong_edge_ratio:.2%}, "
                         f"行变化: {avg_row_std:.1f}, "
                         f"评分: {text_score}")

                return {
                    "has_text": has_text,
                    "confidence": confidence,
                    "text": detail,
                    "error": None
                }

        except Exception as e:
            return {
                "has_text": False,
                "confidence": 0.0,
                "text": "",
                "error": str(e)
            }

    def _detect_table_in_region(self, image_path: str, region: str = "bottom") -> dict:
        """
        检测指定区域是否包含表格内容

        表格特征：
        - 有规则的水平线条
        - 行与行之间有均匀的间隔
        - 垂直方向上有重复的结构

        Args:
            image_path: 图片路径
            region: 检测区域，"bottom"表示底部，"top"表示头部

        Returns:
            dict: {"is_table": bool, "confidence": float, "detail": str, "error": str}
        """
        if not HAS_PIL:
            return {
                "is_table": False,
                "confidence": 0.0,
                "detail": "",
                "error": "PIL not available"
            }

        try:
            from PIL import ImageFilter

            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                width, height = img.size

                # 使用更大的检测区域比例来检测表格（表格通常占据更大区域）
                table_detection_ratio = min(0.35, self.bottom_detection_ratio * 1.5)
                region_height = int(height * table_detection_ratio)

                if region == "bottom":
                    crop_region = img.crop((0, height - region_height, width, height))
                else:
                    crop_region = img.crop((0, 0, width, region_height))

                # 转换为灰度
                gray = crop_region.convert('L')
                pixels = np.array(gray)

                # 1. 检测水平线条：表格有明显的行分隔
                # 计算每行的平均亮度变化
                row_means = np.mean(pixels, axis=1)
                row_diffs = np.abs(np.diff(row_means))

                # 检测明显的行边界（亮度突变）
                threshold = np.std(row_means) * 0.5
                line_positions = np.where(row_diffs > threshold)[0]

                # 2. 检测行间距的规律性
                if len(line_positions) >= 3:
                    line_gaps = np.diff(line_positions)
                    gap_std = np.std(line_gaps)
                    gap_mean = np.mean(line_gaps)
                    # 间距规律性：标准差与均值的比值越小越规律
                    regularity = 1 - min(1, gap_std / (gap_mean + 1))
                else:
                    regularity = 0

                # 3. 检测垂直结构：表格列有重复的垂直线
                col_means = np.mean(pixels, axis=0)
                col_diffs = np.abs(np.diff(col_means))
                col_threshold = np.std(col_means) * 0.3
                vertical_lines = np.sum(col_diffs > col_threshold)
                vertical_density = vertical_lines / len(col_diffs)

                # 4. 检测深色背景行（表格标题行常见）
                dark_rows = np.sum(row_means < 100)
                has_header_row = dark_rows >= 1 and dark_rows <= region_height * 0.3

                # 综合评分
                table_score = 0

                # 水平线条数量评分（0-35分）
                num_lines = len(line_positions)
                if num_lines >= 5:
                    table_score += 35
                elif num_lines >= 3:
                    table_score += 25
                elif num_lines >= 2:
                    table_score += 15

                # 行间距规律性评分（0-30分）
                if regularity > 0.7:
                    table_score += 30
                elif regularity > 0.5:
                    table_score += 20
                elif regularity > 0.3:
                    table_score += 10

                # 垂直结构评分（0-20分）
                if vertical_density > 0.05:
                    table_score += 20
                elif vertical_density > 0.02:
                    table_score += 10

                # 标题行加分（0-15分）
                if has_header_row:
                    table_score += 15

                # 判断阈值：总分超过50认为是表格
                is_table = table_score >= 50
                confidence = min(0.95, table_score / 100)

                detail = (f"{region}区域 - 水平线: {num_lines}, "
                         f"规律性: {regularity:.2f}, "
                         f"垂直密度: {vertical_density:.2%}, "
                         f"标题行: {has_header_row}, "
                         f"评分: {table_score}")

                logger.debug(f"Table detection for {Path(image_path).name}: {detail}")

                return {
                    "is_table": is_table,
                    "confidence": confidence,
                    "detail": detail,
                    "error": None
                }

        except Exception as e:
            logger.warning(f"Table detection failed for {image_path}: {e}")
            return {
                "is_table": False,
                "confidence": 0.0,
                "detail": "",
                "error": str(e)
            }

    def _detect_text_by_image_features(self, image_path: str) -> dict:
        """
        基于图像特征检测底部是否有文字（向后兼容方法）
        """
        return self._detect_text_in_region(image_path, region="bottom")

    def scan_images(self) -> List[str]:
        """
        扫描并排序图片文件

        Returns:
            List[str]: 排序后的图片路径列表
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        image_files = []

        logger.info(f"Scanning images in {self.source_dir}")

        for file_path in self.source_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(str(file_path))

        # 按文件名排序（支持数字排序）
        image_files.sort(key=self._natural_sort_key)

        self.stats["total_images"] = len(image_files)
        logger.info(f"Found {len(image_files)} images")

        return image_files

    def _natural_sort_key(self, file_path: str) -> Tuple:
        """自然排序键，支持数字顺序"""
        path = Path(file_path)
        # 提取文件名中的数字
        import re
        numbers = re.findall(r'\d+', path.stem)
        if numbers:
            # 取最后一个数字作为主要排序依据
            return (path.suffix, int(numbers[-1]))
        return (path.suffix, path.name)

    def _detect_text_in_image(self, image_path: str, region: str = "bottom") -> dict:
        """
        检测图片指定区域是否有文字

        Args:
            image_path: 图片路径
            region: 检测区域，"bottom"表示底部，"top"表示头部

        Returns:
            dict: {"has_text": bool, "confidence": float, "text": str, "error": str}
        """
        # 检查缓存
        try:
            mtime = Path(image_path).stat().st_mtime
            cache_key = f"{image_path}_{mtime}_{region}"
            if cache_key in self._text_detection_cache:
                self.stats["cache_hits"] += 1
                logger.debug(f"Using cached {region} detection result for {Path(image_path).name}")
                return self._text_detection_cache[cache_key]
        except:
            pass

        try:
            logger.debug(f"Detecting text at {region} of image {Path(image_path).name}")

            # 基于图像特征检测指定区域
            result = self._detect_text_in_region(image_path, region=region)

            # 如果特征检测失败或置信度低，且是底部检测，回退到文件名规则
            if region == "bottom" and not result["has_text"] and result["confidence"] < 0.3:
                filename_result = self._detect_text_by_filename(image_path)
                if filename_result["has_text"]:
                    result = filename_result

            # 应用置信度阈值
            if result["has_text"] and result["confidence"] >= self.ocr_confidence_threshold:
                self.stats["text_detections"] += 1
                if result.get("text"):
                    logger.info(f"Text detected at {region} of {Path(image_path).name}: '{result['text'][:50]}...'")
                else:
                    logger.info(f"Text detected at {region} of {Path(image_path).name}")
            elif result["has_text"]:
                result["has_text"] = False
                logger.debug(f"Low confidence {region} text detection in {Path(image_path).name}: {result['confidence']}")

            # 缓存结果
            try:
                self._text_detection_cache[cache_key] = result
            except:
                pass

            return result

        except Exception as e:
            logger.error(f"Failed to detect text at {region} of image {image_path}: {e}")
            # 发生错误时返回默认值，不中断流程
            return {"has_text": False, "confidence": 0.0, "text": "", "error": str(e)}

    def _detect_text_below_image(self, image_path: str) -> dict:
        """
        检测图片底部是否有文字（向后兼容方法）
        """
        return self._detect_text_in_image(image_path, region="bottom")

    def _detect_text_above_image(self, image_path: str) -> dict:
        """
        检测图片头部是否有文字
        """
        return self._detect_text_in_image(image_path, region="top")

    def _count_text_chars(self, image_path: str) -> int:
        """
        统计图片中的文字字符数

        使用 PaddleOCR 检测并识别文字内容，返回总字符数

        Args:
            image_path: 图片路径

        Returns:
            int: 总字符数
        """
        try:
            from .text_region_detector import TextRegionDetector
            detector = TextRegionDetector()
            boxes = detector.detect_text_with_content(image_path)
            total_chars = sum(len(box.text) for box in boxes if box.text)
            logger.debug(f"文字字符数统计: {Path(image_path).name} = {total_chars} 字符")
            return total_chars
        except Exception as e:
            logger.warning(f"OCR字符计数失败 {Path(image_path).name}: {e}")
            return 999  # 返回大值，避免误删

    def _filter_low_text_images(self, image_files: List[str]) -> Tuple[List[str], List[str]]:
        """
        过滤文字过少的图片

        Args:
            image_files: 图片文件列表

        Returns:
            Tuple[List[str], List[str]]: (保留的图片列表, 被丢弃的图片列表)
        """
        if not self.skip_low_text_images:
            return image_files, []

        logger.info(f"开始过滤文字过少的图片（阈值: ≤{self.min_char_threshold}字符）")

        kept = []
        discarded = []

        for img_path in image_files:
            char_count = self._count_text_chars(img_path)
            if char_count <= self.min_char_threshold:
                discarded.append(img_path)
                logger.info(f"丢弃图片(文字≤{self.min_char_threshold}): {Path(img_path).name} ({char_count}字符)")
            else:
                kept.append(img_path)
                logger.debug(f"保留图片: {Path(img_path).name} ({char_count}字符)")

        self.stats["images_discarded_low_text"] = len(discarded)
        logger.info(f"文字过滤完成: 保留 {len(kept)} 张, 丢弃 {len(discarded)} 张")

        return kept, discarded

    def _get_text_vertical_bounds(self, image_path: str) -> Tuple[int, int, int]:
        """
        获取文字区域的垂直边界

        Args:
            image_path: 图片路径

        Returns:
            Tuple[int, int, int]: (y_min, y_max, image_height)
        """
        from PIL import Image

        with Image.open(image_path) as img:
            height = img.height

        try:
            from .text_region_detector import TextRegionDetector
            detector = TextRegionDetector()
            boxes = detector.detect_text_boxes(image_path)

            if not boxes:
                logger.debug(f"未检测到文字框: {Path(image_path).name}")
                return 0, height, height

            y_min = min(box.y_min for box in boxes)
            y_max = max(box.y_max for box in boxes)
            logger.debug(f"文字边界: {Path(image_path).name} y=[{y_min}, {y_max}] / {height}")
            return y_min, y_max, height
        except Exception as e:
            logger.warning(f"获取文字边界失败 {Path(image_path).name}: {e}")
            return 0, height, height

    def _crop_to_text_region(self, image_path: str, output_path: str) -> Tuple[bool, int]:
        """
        裁剪图片到文字区域

        Args:
            image_path: 原图片路径
            output_path: 输出路径

        Returns:
            Tuple[bool, int]: (是否成功裁剪, 节省的高度)
        """
        if not self.crop_blank_regions:
            return False, 0

        y_min, y_max, height = self._get_text_vertical_bounds(image_path)

        # 添加边距
        y_min = max(0, y_min - self.crop_padding)
        y_max = min(height, y_max + self.crop_padding)

        # 如果裁剪区域和原图差不多（超过90%），不裁剪
        if y_max - y_min >= height * 0.9:
            logger.debug(f"无需裁剪（文字区域≥90%）: {Path(image_path).name}")
            return False, 0

        try:
            from PIL import Image
            with Image.open(image_path) as img:
                cropped = img.crop((0, y_min, img.width, y_max))
                cropped.save(output_path, quality=95)

            saved_height = height - (y_max - y_min)
            logger.info(f"裁剪成功: {Path(image_path).name} {height}px → {y_max - y_min}px (节省 {saved_height}px)")
            return True, saved_height
        except Exception as e:
            logger.warning(f"裁剪失败 {Path(image_path).name}: {e}")
            return False, 0

    def _should_merge_with_next(self, image_files: List[str], index: int) -> bool:
        """
        判断当前图片是否应该与下一张合并

        合并条件：当前图片底部有文字 AND 下一张图片头部有文字

        Args:
            image_files: 图片文件列表
            index: 当前图片索引

        Returns:
            bool: 是否应该与下一张合并
        """
        # 如果是最后一张，不能合并
        if index >= len(image_files) - 1:
            return False

        current_image = image_files[index]
        next_image = image_files[index + 1]

        # 检测当前图片底部是否有文字
        bottom_result = self._detect_text_below_image(current_image)
        if bottom_result.get("error"):
            logger.warning(f"Bottom text detection failed for {Path(current_image).name}, keeping separate")
            return False

        # 检测下一张图片头部是否有文字
        top_result = self._detect_text_above_image(next_image)
        if top_result.get("error"):
            logger.warning(f"Top text detection failed for {Path(next_image).name}, keeping separate")
            return False

        # 只有当底部和头部都有文字时才合并
        if bottom_result["has_text"] and top_result["has_text"]:
            logger.info(f"Image {index + 1} bottom has text AND image {index + 2} top has text, will merge")
            return True

        if bottom_result["has_text"] and not top_result["has_text"]:
            logger.debug(f"Image {index + 1} has text below, but image {index + 2} has no text at top, skip merge")
        elif not bottom_result["has_text"] and top_result["has_text"]:
            logger.debug(f"Image {index + 1} has no text below, but image {index + 2} has text at top, skip merge")

        return False

    def generate_merge_groups(self, image_files: List[str]) -> List[MergeGroup]:
        """
        生成分组合并策略

        策略：
        - 只有当当前图片底部有文字 AND 下一张图片头部有文字时，才合并

        Args:
            image_files: 图片文件列表

        Returns:
            List[MergeGroup]: 合并组列表
        """
        return self._generate_smart_merge_groups(image_files)

    def _generate_smart_merge_groups(self, image_files: List[str]) -> List[MergeGroup]:
        """
        基于内容检测的智能分组

        合并条件：当前图片底部有文字 AND 下一张图片头部有文字

        Args:
            image_files: 图片文件列表

        Returns:
            List[MergeGroup]: 合并组列表
        """
        groups = []
        i = 0
        n = len(image_files)

        # 如果启用并行检测，先检测所有图片的底部和头部
        bottom_results = []
        top_results = []

        if self.parallel_detection and n > 1:
            logger.info(f"Parallel text detection (bottom + top) for {n} images using {self.max_workers} workers")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有底部检测任务
                bottom_futures = {
                    executor.submit(self._detect_text_below_image, image_files[i]): ("bottom", i)
                    for i in range(n)
                }
                # 提交所有头部检测任务
                top_futures = {
                    executor.submit(self._detect_text_above_image, image_files[i]): ("top", i)
                    for i in range(n)
                }

                # 初始化结果列表
                bottom_results = [None] * n
                top_results = [None] * n

                # 合并所有任务
                all_futures = {**bottom_futures, **top_futures}

                # 收集结果
                for future in as_completed(all_futures):
                    region, index = all_futures[future]
                    try:
                        result = future.result()
                        if region == "bottom":
                            bottom_results[index] = result
                        else:
                            top_results[index] = result
                    except Exception as e:
                        logger.error(f"Parallel {region} detection failed for image {index}: {e}")
                        error_result = {"has_text": False, "error": str(e)}
                        if region == "bottom":
                            bottom_results[index] = error_result
                        else:
                            top_results[index] = error_result
        else:
            # 串行检测
            logger.info(f"Serial text detection (bottom + top) for {n} images")
            bottom_results = [self._detect_text_below_image(img) for img in image_files]
            top_results = [self._detect_text_above_image(img) for img in image_files]

        # 根据检测结果生成分组
        while i < n:
            group_start = i
            group_end = i + 1  # 至少包含当前图片
            merge_reasons = []

            # 使用 while 循环检测连续合并链
            # 每次检测当前组最后一张图片的底部和下一张图片的顶部
            # 但限制最大合并数量（表格内容除外）
            while group_end < n:
                current_last_idx = group_end - 1  # 当前组的最后一张图片
                next_idx = group_end  # 下一张图片

                # 检查是否达到 max_merge_count 限制
                reached_limit = (group_end - group_start) >= self.max_merge_count

                # 检测当前组最后一张的底部
                current_bottom_has_text = (bottom_results[current_last_idx] and
                                           bottom_results[current_last_idx].get("has_text", False) and
                                           not bottom_results[current_last_idx].get("error"))

                # 检测下一张的顶部
                next_top_has_text = (top_results[next_idx] and
                                     top_results[next_idx].get("has_text", False) and
                                     not top_results[next_idx].get("error"))

                # 如果达到限制，检测是否是表格连续性情况
                if reached_limit:
                    # 检测当前图片底部和下一张图片顶部是否都是表格
                    current_bottom_table = self._detect_table_in_region(
                        image_files[current_last_idx], region="bottom"
                    )
                    next_top_table = self._detect_table_in_region(
                        image_files[next_idx], region="top"
                    )

                    is_table_continuation = (
                        current_bottom_table.get("is_table", False) and
                        next_top_table.get("is_table", False)
                    )

                    if is_table_continuation and current_bottom_has_text and next_top_has_text:
                        # 表格连续，忽略 max_merge_count 限制
                        merge_reasons.append(f"image {current_last_idx + 1} bottom + image {next_idx + 1} top (table continuation)")
                        group_end += 1
                        logger.info(f"Extending merge chain (table continuation): image {current_last_idx + 1} -> image {next_idx + 1}")
                        continue
                    else:
                        # 达到限制且不是表格连续，停止扩展
                        logger.info(f"Reached max merge count ({self.max_merge_count}) for group starting at image {group_start + 1}")
                        break

                # 只有当底部和头部都有文字时才扩展合并链
                if current_bottom_has_text and next_top_has_text:
                    merge_reasons.append(f"image {current_last_idx + 1} bottom + image {next_idx + 1} top")
                    group_end += 1  # 扩展组
                    logger.info(f"Extending merge chain: image {current_last_idx + 1} -> image {next_idx + 1}")
                else:
                    # 记录为什么停止扩展
                    if current_bottom_has_text and not next_top_has_text:
                        logger.debug(f"Stop chain: image {current_last_idx + 1} has text at bottom, but image {next_idx + 1} has no text at top")
                    elif not current_bottom_has_text and next_top_has_text:
                        logger.debug(f"Stop chain: image {current_last_idx + 1} has no text at bottom, but image {next_idx + 1} has text at top")
                    break  # 停止扩展

            # 生成原因描述
            if len(merge_reasons) > 0:
                reason = f"smart merge chain ({len(merge_reasons)} connections): " + " -> ".join(merge_reasons)
                logger.info(f"Created merge group: images {group_start + 1} to {group_end} ({group_end - group_start} images)")
            else:
                reason = f"single image: {Path(image_files[i]).name}"
                if bottom_results[i] and bottom_results[i].get("error"):
                    reason += " (bottom detection error)"
                elif i < n - 1 and top_results[i + 1] and top_results[i + 1].get("error"):
                    reason += " (next top detection error)"
                else:
                    # 检查为什么没有合并
                    current_bottom = (bottom_results[i] and
                                     bottom_results[i].get("has_text", False) and
                                     not bottom_results[i].get("error"))
                    next_top = False
                    if i < n - 1:
                        next_top = (top_results[i + 1] and
                                   top_results[i + 1].get("has_text", False) and
                                   not top_results[i + 1].get("error"))

                    if current_bottom and not next_top:
                        reason += " (bottom has text, next top no text)"
                    elif not current_bottom and next_top:
                        reason += " (bottom no text, next top has text)"
                    elif not current_bottom:
                        reason += " (no text at bottom)"

            # 创建合并组
            indices = list(range(group_start, group_end))
            group = MergeGroup(indices, reason=reason)
            groups.append(group)

            # 移动到下一个未处理的图片
            i = group_end

        logger.info(f"Generated {len(groups)} smart merge groups")
        logger.info(f"Text detections: {self.stats['text_detections']}/{n}")
        logger.info(f"Cache hits: {self.stats['cache_hits']}")

        return groups

    def _split_merged_image(self, image_path: str, group: MergeGroup) -> List[str]:
        """
        对合并后的图片进行智能分割

        分割数量与合并的原始图片数量一致。

        Args:
            image_path: 合并后的图片路径
            group: 合并组信息

        Returns:
            List[str]: 分割后的文件路径列表（如果未分割则返回原路径）
        """
        if not self.enable_split:
            return [image_path]

        # 获取合并的图片数量作为目标分割数量
        num_parts = len(group.indices)

        # 如果只有1张图片，不需要分割
        if num_parts < 2:
            return [image_path]

        try:
            logger.info(f"Splitting {Path(image_path).name} into {num_parts} parts (matching merge count)")

            # 使用新的 split_into_parts 方法，按合并数量分割
            split_results = self.image_merger.split_into_parts(
                image_path,
                num_parts=num_parts,
                output_dir=str(self.output_dir),
                min_part_height=self.min_split_height // 2  # 每部分的最小高度
            )

            # 如果成功分割（返回多个文件），删除原始合并文件
            if len(split_results) >= 2:
                self.stats["images_split"] += 1
                # 删除原始合并文件
                try:
                    os.remove(image_path)
                    logger.info(f"Removed original merged file: {Path(image_path).name}")
                except Exception as e:
                    logger.warning(f"Failed to remove original file: {e}")

                # 更新组信息
                group.split_files = [Path(f).name for f in split_results]
                group.was_split = True

                return split_results
            else:
                group.was_split = False
                return [image_path]

        except Exception as e:
            logger.error(f"Error during split: {e}")
            return [image_path]

    def execute_merge(
        self,
        image_files: List[str],
        merge_groups: List[MergeGroup]
    ) -> List[str]:
        """
        执行图片合并（及可选的分割）

        Args:
            image_files: 图片文件列表
            merge_groups: 合并组列表

        Returns:
            List[str]: 输出文件路径列表
        """
        output_files = []

        logger.info(f"Executing merge for {len(merge_groups)} groups")
        if self.enable_split:
            logger.info(f"Post-merge split is ENABLED (min height: {self.min_split_height}px)")

        for i, group in enumerate(merge_groups):
            # 准备输入文件路径
            group_files = [image_files[idx] for idx in group.indices]

            # 生成输出文件名（统一格式，使用原始图片编号，从1开始）
            if len(group.indices) == 1:
                # 单张图片，使用merge后缀保持一致性
                original_idx = group.indices[0] + 1  # 转换为1-based
                output_name = f"merge_{original_idx:03d}.jpg"
                reason = "single image (no merge needed)"
            else:
                # 多张图片合并
                start_idx = group.indices[0] + 1  # 转换为1-based
                end_idx = group.indices[-1] + 1    # 转换为1-based
                output_name = f"merge_{start_idx:03d}_{end_idx:03d}.jpg"
                reason = f"merge {len(group.indices)} images"

            # 设置输出路径
            output_path = self.output_dir / output_name
            group.source_files = [Path(f).name for f in group_files]
            group.output_file = output_name

            logger.info(f"Processing group {i+1}/{len(merge_groups)}: {reason}")

            # 执行合并或复制
            if len(group.indices) == 1:
                # 单张图片直接复制
                import shutil
                shutil.copy2(group_files[0], output_path)
            else:
                # 多张图片合并
                success = self.image_merger.merge_vertically(group_files, str(output_path))
                if not success:
                    logger.error(f"Failed to merge group {i+1}")
                    continue

            # 对合并后的图片进行分割（如果启用）
            if self.enable_split and len(group.indices) > 1:
                # 只对合并后的图片进行分割，单张图片不分割
                split_results = self._split_merged_image(str(output_path), group)
                output_files.extend(split_results)
            else:
                group.was_split = False
                output_files.append(str(output_path))

            logger.debug(f"Created: {output_name}")

        self.stats["output_count"] = len(output_files)
        self.stats["merge_groups"] = len(merge_groups)
        reduction_ratio = (len(image_files) - len(output_files)) / len(image_files) if len(image_files) > 0 else 0
        self.stats["reduction_ratio"] = reduction_ratio

        logger.info(f"Merge completed: {len(image_files)} -> {len(output_files)} files (reduced by {reduction_ratio:.1%})")
        if self.enable_split:
            logger.info(f"Split stats: {self.stats['images_split']} split, "
                       f"{self.stats['split_skipped_table']} skipped (table), "
                       f"{self.stats['split_skipped_no_point']} skipped (no point)")

        return output_files

    def generate_metadata(
        self,
        image_files: List[str],
        merge_groups: List[MergeGroup]
    ) -> Dict[str, Any]:
        """
        生成处理元数据

        Args:
            image_files: 图片文件列表
            merge_groups: 合并组列表

        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "source_directory": str(self.source_dir),
            "output_directory": str(self.output_dir),
            "configuration": {
                "quality": self.image_merger.quality,
                "bottom_detection_ratio": self.bottom_detection_ratio,
                "ocr_confidence_threshold": self.ocr_confidence_threshold,
                "min_text_length": self.min_text_length,
                "parallel_detection": self.parallel_detection,
                "max_workers": self.max_workers,
                # 分割配置
                "split_enabled": self.enable_split,
                "min_split_height": self.min_split_height,
                "split_min_ratio": self.split_min_ratio,
                "split_max_ratio": self.split_max_ratio
            },
            "statistics": self.stats,
            "files": {
                "input_files": [Path(f).name for f in image_files],
                "output_count": len(merge_groups)
            },
            "merge_groups": []
        }

        # 添加合并组详情
        for i, group in enumerate(merge_groups):
            group_info = {
                "group_id": i + 1,
                "output_file": group.output_file,
                "source_files": group.source_files,
                "file_count": len(group.indices),
                "indices": group.indices,
                "reason": group.reason,
                # 分割信息
                "was_split": group.was_split,
                "split_files": group.split_files if group.was_split else []
            }
            metadata["merge_groups"].append(group_info)

        return metadata

    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        保存元数据到文件

        Args:
            metadata: 元数据字典

        Returns:
            str: 元数据文件路径
        """
        metadata_path = self.output_dir / "merge_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Metadata saved to: {metadata_path}")
        return str(metadata_path)

    def process(self) -> Dict[str, Any]:
        """
        执行完整的批处理流程

        Returns:
            Dict[str, Any]: 处理结果和元数据
        """
        import shutil

        temp_dir = None
        try:
            # 1. 扫描图片
            image_files = self.scan_images()
            if not image_files:
                logger.warning("No images found in source directory")
                return {"error": "No images found"}

            # 2. [新增] 过滤文字过少的图片
            original_image_files = image_files.copy()
            image_files, discarded = self._filter_low_text_images(image_files)
            if not image_files:
                logger.warning("All images discarded due to low text")
                return {"error": "All images discarded due to low text"}

            # 3. [新增] 裁剪空白区域
            working_files = image_files  # 默认使用过滤后的原图

            if self.crop_blank_regions:
                temp_dir = self.output_dir / "temp_cropped"
                temp_dir.mkdir(exist_ok=True)
                logger.info(f"开始裁剪空白区域，临时目录: {temp_dir}")

                cropped_files = []
                for img_path in image_files:
                    temp_path = temp_dir / Path(img_path).name
                    success, saved = self._crop_to_text_region(img_path, str(temp_path))
                    if success:
                        cropped_files.append(str(temp_path))
                        self.stats["images_cropped"] += 1
                        self.stats["crop_saved_height"] += saved
                    else:
                        cropped_files.append(img_path)  # 使用原图

                working_files = cropped_files
                logger.info(f"裁剪完成: {self.stats['images_cropped']} 张图片被裁剪, 节省 {self.stats['crop_saved_height']}px")

            # 4. 生成分组策略（使用原始图片进行文字检测，避免裁剪影响合并判断）
            merge_groups = self.generate_merge_groups(image_files)

            # 5. 执行合并（使用裁剪后的图片）
            output_files = self.execute_merge(working_files, merge_groups)

            # 6. [新增] 清理临时文件
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info(f"已清理临时目录: {temp_dir}")

            # 7. 生成元数据（使用原始文件名）
            metadata = self.generate_metadata(original_image_files, merge_groups)
            metadata["output_files"] = [Path(f).name for f in output_files]
            metadata["discarded_files"] = [Path(f).name for f in discarded]

            # 8. 保存元数据
            metadata_path = self.save_metadata(metadata)

            logger.info("Batch processing completed successfully")

            return {
                "success": True,
                "metadata_path": metadata_path,
                "statistics": self.stats,
                "output_files": output_files,
                "discarded_files": discarded
            }

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # 清理临时目录
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
            return {
                "success": False,
                "error": str(e)
            }


def create_batch_processor(source_dir: str, **kwargs) -> BatchMergeProcessor:
    """创建批处理管理器的工厂函数"""
    return BatchMergeProcessor(source_dir, **kwargs)


if __name__ == "__main__":
    # 简单测试
    import sys

    if len(sys.argv) < 2:
        print("Usage: python batch_merge_processor.py <source_directory>")
        sys.exit(1)

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建批处理器
    processor = create_batch_processor(sys.argv[1])

    # 执行处理
    result = processor.process()

    if result["success"]:
        print("Processing completed successfully!")
        print(f"Statistics: {result['statistics']}")
        print(f"Output files: {len(result['output_files'])}")
    else:
        print(f"Processing failed: {result['error']}")