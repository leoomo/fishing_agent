#!/usr/bin/env python
"""
图片切割合并测试脚本

测试 OCRMergeProcessor 的图片处理功能（不含OCR识别）：
- 文字区域检测与裁剪
- 智能图片合并
- 大图片分割

输入: shared/images/pending/1/
输出: shared/images/merge_output/
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"  步骤 {step_num}: {description}")
    print(f"{'='*60}")
    logger.info(f"步骤 {step_num}: {description}")


def print_subsection(title):
    """打印小节标题"""
    print(f"\n{'─'*40}")
    print(f"  {title}")
    print(f"{'─'*40}")


def format_size(bytes_size):
    """格式化文件大小"""
    if bytes_size < 1024:
        return f"{bytes_size}B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f}KB"
    else:
        return f"{bytes_size / 1024 / 1024:.2f}MB"


def main():
    step = 0

    # ===== 步骤 1: 配置检查 =====
    step += 1
    print_step(step, "配置检查")

    input_dir = Path("shared/images/pending/1")
    output_dir = Path("shared/images/merge_output")

    # 检查输入目录
    if not input_dir.exists():
        print(f"  ❌ 输入目录不存在: {input_dir.absolute()}")
        return
    print(f"  ✓ 输入目录: {input_dir.absolute()}")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 输出目录: {output_dir.absolute()}")

    # ===== 步骤 2: 扫描图片 =====
    step += 1
    print_step(step, "扫描图片文件")

    def extract_sort_key(filepath):
        """从文件名提取排序键值"""
        import re
        stem = Path(filepath).stem
        # 尝试提取文件名中的数字（支持 image_15.jpg, 15.jpg, 001.jpg 等格式）
        match = re.search(r'(\d+)', stem)
        if match:
            return int(match.group(1))
        # 如果没有数字，返回文件名本身作为后备
        return stem

    image_files = sorted(
        [str(f) for f in input_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']],
        key=extract_sort_key
    )

    print(f"\n找到 {len(image_files)} 张图片:")
    for i, path in enumerate(image_files[:5]):
        size = os.path.getsize(path)
        print(f"  {i+1}. {Path(path).name} ({format_size(size)})")
    if len(image_files) > 5:
        print(f"  ... 还有 {len(image_files)-5} 张")

    # ===== 步骤 3: 初始化处理器 =====
    step += 1
    print_step(step, "初始化 OCR 合并处理器")

    from packages.data_processing.ocr import OCRMergeProcessor

    # 配置参数
    config = {
        "source_dir": str(input_dir),
        "output_dir": str(output_dir),
        # 裁剪参数
        "padding": 15,
        "min_text_area": 100,
        # 合并参数
        "quality": 95,
        "spacing": 0,
        # 分割参数（使用优化后的新参数，避免过度切分）
        "enable_split": True,
        "min_segment_height": 800,   # 提高到 800，避免切得太碎
        "max_segment_height": 4000,  # 提高到 4000
        "min_blank_rows": 50,        # 只切割 >=50px 的空白区域
        # 其他参数
        "keep_empty_images": False,
        "skip_pure_images": True,
        "skip_sparse_regions": True,
        "min_chars_per_region": 5,
        "verbose": True
    }

    print(f"\n配置参数:")
    print(f"  padding: {config['padding']}px")
    print(f"  min_segment_height: {config['min_segment_height']}px")
    print(f"  max_segment_height: {config['max_segment_height']}px")
    print(f"  min_blank_rows: {config.get('min_blank_rows', 50)}px")
    print(f"  enable_split: {config['enable_split']}")
    print(f"  skip_sparse_regions: {config['skip_sparse_regions']}")

    try:
        processor = OCRMergeProcessor(**config)
        print(f"\n✓ 处理器初始化成功")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        logger.error(f"初始化失败", exc_info=True)
        return

    # ===== 步骤 4: 执行处理 =====
    step += 1
    print_step(step, "执行图片处理")

    import time
    start_time = time.time()

    try:
        result = processor.process()

        elapsed = time.time() - start_time

        print(f"\n✓ 处理完成，耗时: {elapsed:.2f} 秒")

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        logger.error(f"处理失败", exc_info=True)
        return

    # ===== 步骤 5: 显示结果 =====
    step += 1
    print_step(step, "处理结果")

    if not result.success:
        print(f"\n❌ 处理失败")
        print(f"  错误: {result.error}")
        return

    print(f"\n✅ 处理成功!")

    # 统计信息
    stats = result.statistics
    print_subsection("统计信息")
    print(f"  输入图片: {stats.get('total_images', 0)} 张")
    print(f"  有文字的图片: {stats.get('images_with_text', 0)} 张")
    print(f"  无文字的图片: {stats.get('images_without_text', 0)} 张")
    print(f"  跳过的稀疏区域: {stats.get('sparse_regions_skipped', 0)} 个")
    print(f"  跳过的空白图片: {stats.get('empty_images_skipped', 0)} 张")
    print(f"  输出文件: {stats.get('output_count', 0)} 个")
    print(f"  处理时间: {stats.get('processing_time_ms', 0) / 1000:.2f} 秒")

    # 输出文件详情
    print_subsection("输出文件列表")

    from PIL import Image

    total_size = 0
    for i, file_path in enumerate(result.output_files, 1):
        path = Path(file_path)
        size = os.path.getsize(file_path)
        total_size += size

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                print(f"  {i}. {path.name:30s} {width}x{height:4d}px  {format_size(size):>8s}")
        except Exception as e:
            print(f"  {i}. {path.name:30s} (无法读取: {e})")

    print(f"\n  总大小: {format_size(total_size)}")

    # 检查是否有超过阈值的文件
    print_subsection("文件高度检查")

    max_height = config['max_segment_height']
    over_threshold = []

    for file_path in result.output_files:
        try:
            with Image.open(file_path) as img:
                if img.height > max_height:
                    over_threshold.append((Path(file_path).name, img.height, img.width))
        except Exception:
            pass

    if over_threshold:
        print(f"  ⚠️  仍有 {len(over_threshold)} 个文件超过阈值 ({max_height}px):")
        for name, h, w in over_threshold:
            print(f"      {name}: {w}x{h}px")
    else:
        print(f"  ✅ 所有文件都符合阈值要求 (≤ {max_height}px)")

    # ===== 步骤 6: 后处理分割 =====
    step += 1
    print_step(step, "后处理：分割超大文件")

    from packages.data_processing.image.splitter import BlankRowDetector, ImageSplitter

    max_height = config['max_segment_height']
    min_height = config['min_segment_height']

    # 找出超过阈值的文件
    large_files = []
    for file_path in result.output_files:
        try:
            with Image.open(file_path) as img:
                if img.height > max_height:
                    large_files.append((file_path, img.width, img.height))
        except Exception:
            pass

    if large_files:
        print(f"\n发现 {len(large_files)} 个超大文件，开始分割...")

        split_results = []
        remaining_files = []

        for file_path, width, height in large_files:
            path = Path(file_path)
            print(f"\n  处理: {path.name} ({width}x{height}px)")

            try:
                with Image.open(file_path) as img:
                    # 检测空白区域
                    blank_detector = BlankRowDetector()
                    blank_regions = blank_detector.find_blank_regions(img)

                    print(f"    检测到 {len(blank_regions)} 个空白区域")

                    # 选择切割点
                    splitter = ImageSplitter(
                        min_segment_height=min_height,
                        max_segment_height=max_height
                    )
                    split_points = splitter.select_split_points(
                        blank_regions,
                        img.height
                    )

                    print(f"    选择 {len(split_points)} 个切割点")

                    if split_points:
                        # 执行切割
                        segments = splitter.split_image(img, split_points)
                        print(f"    分割成 {len(segments)} 个片段")

                        # 保存分割后的文件
                        segment_files = []
                        for i, segment in enumerate(segments):
                            seg_name = f"{path.stem}_seg{i+1:02d}{path.suffix}"
                            seg_path = output_dir / seg_name
                            segment.save(str(seg_path), 'JPEG', quality=config['quality'])
                            segment_size = os.path.getsize(seg_path)

                            sw, sh = segment.size
                            print(f"      片段 {i+1}: {sw}x{sh}px  {format_size(segment_size)}")
                            segment_files.append(str(seg_path))

                        split_results.append((file_path, segment_files))
                    else:
                        print(f"    未找到合适的切割点，保持原样")
                        remaining_files.append(file_path)

            except Exception as e:
                print(f"    ❌ 分割失败: {e}")
                remaining_files.append(file_path)

        # 更新输出文件列表
        if split_results:
            print(f"\n  分割完成:")
            final_files = []

            for original, segments in split_results:
                print(f"    {Path(original).name} → {len(segments)} 个片段")
                final_files.extend(segments)

            # 添加未分割的文件
            for f in result.output_files:
                if not any(f == orig for orig, _ in split_results):
                    final_files.append(f)

            # 删除原文件
            import shutil
            for original, segments in split_results:
                try:
                    os.unlink(original)
                    print(f"    删除原文件: {Path(original).name}")
                except Exception as e:
                    print(f"    删除失败: {e}")

            print(f"\n  最终文件数: {len(final_files)}")
            print(f"  分割了 {len(split_results)} 个文件")

            # 显示最终结果
            print_subsection("最终输出文件")

            final_files.sort()
            total_size = 0
            for i, file_path in enumerate(final_files, 1):
                path = Path(file_path)
                size = os.path.getsize(file_path)
                total_size += size

                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        status = "✓" if height <= max_height else "⚠️"
                        print(f"  {status} {i:2d}. {path.name:35s} {width}x{height:4d}px  {format_size(size):>8s}")
                except Exception as e:
                    print(f"  ✗ {i:2d}. {path.name:35s} (无法读取)")

            print(f"\n  总大小: {format_size(total_size)}")
    else:
        print("\n  ✅ 所有文件都符合阈值要求，无需分割")

    # ===== 步骤 7: 查看元数据 =====
    step += 1
    print_step(step, "处理元数据")

    metadata_path = output_dir / "processing_metadata.json"
    if metadata_path.exists():
        print(f"\n✓ 元数据已保存: {metadata_path.name}")
        print(f"  文件大小: {format_size(os.path.getsize(metadata_path))}")

        # 显示部分元数据
        import json
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        print(f"\n元数据摘要:")
        print(f"  时间戳: {metadata.get('timestamp')}")
        print(f"  版本: {metadata.get('version')}")

        config_info = metadata.get('configuration', {})
        print(f"  配置:")
        print(f"    padding: {config_info.get('padding')}px")
        print(f"    enable_split: {config_info.get('enable_split')}")
        print(f"    max_segment_height: {config_info.get('max_segment_height')}px")

        details = metadata.get('processing_details', [])
        print(f"\n处理详情 (前5张):")
        for detail in details[:5]:
            filename = detail.get('filename')
            has_text = detail.get('has_text')
            text_boxes = detail.get('text_boxes', 0)
            original = detail.get('original_size')
            cropped = detail.get('cropped_size')

            status = "✓" if has_text else "✗"
            crop_info = f" → {cropped}" if cropped else ""
            print(f"  {status} {filename}: {text_boxes}框 {original}{crop_info}")

    # ===== 步骤 8: 完成 =====
    step += 1
    print_step(step, "测试完成")

    print(f"\n✅ 全部步骤完成!")
    print(f"   输入目录: {input_dir}")
    print(f"   输出目录: {output_dir}")
    print(f"   输入文件: {len(image_files)} 张")
    print(f"   输出文件: {len(result.output_files)} 个")
    print(f"   总耗时: {elapsed:.2f} 秒")

    print(f"\n📁 查看输出文件:")
    print(f"   cd {output_dir}")
    print(f"   ls -lh")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 未预期的错误: {e}")
        logger.error(f"未预期的错误", exc_info=True)
