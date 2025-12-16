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

    def __len__(self):
        return len(self.indices)

    def __str__(self):
        return f"MergeGroup({self.indices}, reason='{self.reason}')"


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
        max_workers: int = 4  # 并行检测的最大线程数
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
            "cache_hits": 0
        }

        logger.info(f"BatchMergeProcessor initialized")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Smart grouping: ENABLED")
        logger.info(f"Bottom detection ratio: {self.bottom_detection_ratio}")
        logger.info(f"OCR confidence threshold: {self.ocr_confidence_threshold}")

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

    def _detect_text_by_image_features(self, image_path: str) -> dict:
        """
        基于图像特征检测底部是否有文字
        """
        if not HAS_PIL:
            return {
                "has_text": False,
                "confidence": 0.0,
                "text": "",
                "error": "PIL not available"
            }

        try:
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                width, height = img.size

                # 裁剪底部20%区域
                bottom_height = int(height * self.bottom_detection_ratio)
                bottom_region = img.crop((0, height - bottom_height, width, height))

                # 转换为灰度
                gray = bottom_region.convert('L')

                # 计算统计信息
                stat = ImageStat.Stat(gray)

                # 计算暗像素比例
                pixels = np.array(gray)
                dark_pixels = np.sum(pixels < 180)  # 180以下的认为是暗像素
                dark_ratio = dark_pixels / pixels.size

                # 计算标准差
                std_dev = stat.stddev[0]

                # 判断规则（更宽松）
                # 1. 如果暗像素比例超过5%
                # 2. 或者标准差较大（表示有变化）
                has_text = dark_ratio > 0.05 or std_dev > 25

                # 计算置信度
                if has_text:
                    confidence = min(0.8, dark_ratio * 8 + std_dev / 40)
                else:
                    confidence = max(0.2, 1.0 - (dark_ratio * 5 + std_dev / 50))

                return {
                    "has_text": has_text,
                    "confidence": confidence,
                    "text": f"暗像素: {dark_ratio:.2%}, 标准差: {std_dev:.1f}",
                    "error": None
                }

        except Exception as e:
            return {
                "has_text": False,
                "confidence": 0.0,
                "text": "",
                "error": str(e)
            }

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

    def _detect_text_below_image(self, image_path: str) -> dict:
        """
        检测图片下方是否有文字

        Args:
            image_path: 图片路径

        Returns:
            dict: {"has_text": bool, "confidence": float, "text": str, "error": str}
        """
        # 检查缓存
        try:
            mtime = Path(image_path).stat().st_mtime
            cache_key = f"{image_path}_{mtime}"
            if cache_key in self._text_detection_cache:
                self.stats["cache_hits"] += 1
                logger.debug(f"Using cached detection result for {Path(image_path).name}")
                return self._text_detection_cache[cache_key]
        except:
            pass

        try:
            logger.debug(f"Detecting text below image {Path(image_path).name}")

            # 方法1: 基于图像特征检测
            result = self._detect_text_by_image_features(image_path)

            # 如果特征检测失败或置信度低，回退到文件名规则
            if not result["has_text"] and result["confidence"] < 0.3:
                filename_result = self._detect_text_by_filename(image_path)
                if filename_result["has_text"]:
                    result = filename_result

            # 应用置信度阈值
            if result["has_text"] and result["confidence"] >= self.ocr_confidence_threshold:
                self.stats["text_detections"] += 1
                if result.get("text"):
                    logger.info(f"Text detected below image {Path(image_path).name}: '{result['text'][:50]}...'")
                else:
                    logger.info(f"Text detected below image {Path(image_path).name}")
            elif result["has_text"]:
                result["has_text"] = False
                logger.debug(f"Low confidence text detection in {Path(image_path).name}: {result['confidence']}")

            # 缓存结果
            try:
                self._text_detection_cache[cache_key] = result
            except:
                pass

            return result

        except Exception as e:
            logger.error(f"Failed to detect text below image {image_path}: {e}")
            # 发生错误时返回默认值，不中断流程
            return {"has_text": False, "confidence": 0.0, "text": "", "error": str(e)}

    def _should_merge_with_next(self, image_files: List[str], index: int) -> bool:
        """
        判断当前图片是否应该与下一张合并

        Args:
            image_files: 图片文件列表
            index: 当前图片索引

        Returns:
            bool: 是否应该与下一张合并
        """
        # 如果是最后一张，不能合并
        if index >= len(image_files) - 1:
            return False

        # 智能分组：检测当前图片下方是否有文字
        current_image = image_files[index]
        detection_result = self._detect_text_below_image(current_image)

        if detection_result.get("error"):
            logger.warning(f"Text detection failed for {Path(current_image).name}, keeping separate")
            # 检测失败时保持独立
            return False

        # 如果下方有文字，与下一张合并
        if detection_result["has_text"]:
            logger.info(f"Image {index + 1} has text below, will merge with next image")
            return True

        return False

    def generate_merge_groups(self, image_files: List[str]) -> List[MergeGroup]:
        """
        生成分组合并策略

        策略：
        - 检测图片下方是否有文字，有则与下一张合并

        Args:
            image_files: 图片文件列表

        Returns:
            List[MergeGroup]: 合并组列表
        """
        return self._generate_smart_merge_groups(image_files)

    def _generate_smart_merge_groups(self, image_files: List[str]) -> List[MergeGroup]:
        """
        基于内容检测的智能分组

        Args:
            image_files: 图片文件列表

        Returns:
            List[MergeGroup]: 合并组列表
        """
        groups = []
        i = 0
        n = len(image_files)

        # 如果启用并行检测，先检测所有图片
        text_results = []
        if self.parallel_detection and n > 1:
            logger.info(f"Parallel text detection for {n} images using {self.max_workers} workers")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有检测任务
                future_to_index = {
                    executor.submit(self._detect_text_below_image, image_files[i]): i
                    for i in range(n)
                }

                # 初始化结果列表
                text_results = [None] * n

                # 收集结果
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        text_results[index] = future.result()
                    except Exception as e:
                        logger.error(f"Parallel detection failed for image {index}: {e}")
                        text_results[index] = {"has_text": False, "error": str(e)}
        else:
            # 串行检测
            logger.info(f"Serial text detection for {n} images")
            text_results = [self._detect_text_below_image(img) for img in image_files]

        # 根据检测结果生成分组
        while i < n:
            group_start = i
            group_end = i + 1  # 至少包含当前图片

            # 检查当前图片是否需要与下一张合并
            current_has_text = (text_results[i] and
                               text_results[i].get("has_text", False) and
                               not text_results[i].get("error"))

            if current_has_text and i < n - 1:
                # 当前图片有文字，与下一张合并
                group_end = i + 2
                reason = f"smart merge: image {i+1} has text below, merging with image {i+2}"
                logger.info(reason)
            else:
                reason = f"single image: {Path(image_files[i]).name}"
                if text_results[i] and text_results[i].get("error"):
                    reason += " (detection error)"
                elif not current_has_text and self.smart_grouping_enabled:
                    reason += " (no text detected)"

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

    def execute_merge(
        self,
        image_files: List[str],
        merge_groups: List[MergeGroup]
    ) -> List[str]:
        """
        执行图片合并

        Args:
            image_files: 图片文件列表
            merge_groups: 合并组列表

        Returns:
            List[str]: 输出文件路径列表
        """
        output_files = []

        logger.info(f"Executing merge for {len(merge_groups)} groups")

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

            output_files.append(str(output_path))
            logger.debug(f"Created: {output_name}")

        self.stats["output_count"] = len(output_files)
        reduction_ratio = (len(image_files) - len(output_files)) / len(image_files) if len(image_files) > 0 else 0
        self.stats["reduction_ratio"] = reduction_ratio

        logger.info(f"Merge completed: {len(image_files)} -> {len(output_files)} files (reduced by {reduction_ratio:.1%})")

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
                "max_workers": self.max_workers
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
                "reason": group.reason
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
        try:
            # 1. 扫描图片
            image_files = self.scan_images()
            if not image_files:
                logger.warning("No images found in source directory")
                return {"error": "No images found"}

            # 2. 生成分组策略
            merge_groups = self.generate_merge_groups(image_files)

            # 3. 执行合并
            output_files = self.execute_merge(image_files, merge_groups)

            # 4. 生成元数据
            metadata = self.generate_metadata(image_files, merge_groups)
            metadata["output_files"] = [Path(f).name for f in output_files]

            # 5. 保存元数据
            metadata_path = self.save_metadata(metadata)

            logger.info("Batch processing completed successfully")

            return {
                "success": True,
                "metadata_path": metadata_path,
                "statistics": self.stats,
                "output_files": output_files
            }

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
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