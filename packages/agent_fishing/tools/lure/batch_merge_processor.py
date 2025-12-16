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

from .image_merger import ImageMerger


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
        merge_batch_size: int = 2  # 每次合并的图片数量
    ):
        """
        初始化批处理管理器

        Args:
            source_dir: 源图片目录
            output_dir: 输出目录（默认为源目录下的merged子目录）
            quality: 输出图片质量
            merge_batch_size: 每次合并的图片数量
        """
        self.source_dir = Path(source_dir).resolve()
        if not self.source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")

        self.output_dir = Path(output_dir) if output_dir else self.source_dir / "merged"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.image_merger = ImageMerger(quality=quality)
        self.merge_batch_size = merge_batch_size

        # 处理统计
        self.stats = {
            "total_images": 0,
            "merge_groups": 0,
            "original_count": 0,
            "output_count": 0
        }

        logger.info(f"BatchMergeProcessor initialized")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Merge batch size: {self.merge_batch_size}")

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

    def generate_merge_groups(self, image_files: List[str]) -> List[MergeGroup]:
        """
        生成分组合并策略

        策略：
        - 按照指定的批次大小合并图片

        Args:
            image_files: 图片文件列表

        Returns:
            List[MergeGroup]: 合并组列表
        """
        groups = []

        # 按批次大小分组
        for i in range(0, len(image_files), self.merge_batch_size):
            start_idx = i
            end_idx = min(i + self.merge_batch_size, len(image_files))
            indices = list(range(start_idx, end_idx))

            group = MergeGroup(
                indices,
                reason=f"batch merge of {len(indices)} images"
            )
            groups.append(group)

        # 更新统计
        self.stats["merge_groups"] = len(groups)
        self.stats["original_count"] = len(image_files)

        logger.info(f"Generated {len(groups)} merge groups")
        for i, group in enumerate(groups):
            logger.debug(f"Group {i+1}: {group}")

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
                "merge_batch_size": self.merge_batch_size,
                "quality": self.image_merger.quality
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