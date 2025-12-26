#!/usr/bin/env python
"""
本地 OCR 测试脚本（带详细进度显示）

使用 OCRMergeProcessor 处理图片，然后使用远程 Ollama 服务进行 OCR 识别。
- 文字区域检测与裁剪
- 智能图片合并（spacing=0）
- 支持纯色区域检测的分割功能

输入: shared/images/pending/1
输出: shared/images/output/
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from packages.data_processing.ocr import OCRMergeProcessor
from apps.api.services.ocr.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"  步骤 {step_num}: {description}")
    print(f"{'='*60}")
    logger.info(f"步骤 {step_num}: {description}")


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
    ocr_output_dir = Path("shared/images/output")

    # 检查环境变量
    print(f"\n环境变量:")
    print(f"  OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL', '未设置')}")
    print(f"  OCR_PROVIDER: {os.getenv('OCR_PROVIDER', '未设置')}")

    # 检查输入目录
    if not input_dir.exists():
        print(f"  ❌ 输入目录不存在: {input_dir.absolute()}")
        return
    print(f"  ✓ 输入目录: {input_dir.absolute()}")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    ocr_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 合并输出: {output_dir.absolute()}")
    print(f"  ✓ OCR输出: {ocr_output_dir.absolute()}")

    # ===== 步骤 2: 初始化 OCRMergeProcessor =====
    step += 1
    print_step(step, "初始化 OCR 合并处理器")

    # 使用优化后的默认配置
    processor_config = {
        "source_dir": str(input_dir),
        "output_dir": str(output_dir),
        # 分割参数：降低阈值以测试分割功能（默认 max_segment_height=4000）
        "max_segment_height": 2000,
    }

    try:
        processor = OCRMergeProcessor(**processor_config)
        print(f"\n✓ 处理器初始化成功")
        print(f"  裁剪边距: {processor.padding}px")
        print(f"  合并间距: {processor.spacing}px")
        print(f"  分割启用: {processor.enable_split}")
        print(f"  最小片段: {processor.min_segment_height}px")
        print(f"  最大片段: {processor.max_segment_height}px")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        logger.error(f"初始化失败", exc_info=True)
        return

    # ===== 步骤 3: 执行图片处理 =====
    step += 1
    print_step(step, "执行图片处理（裁剪+合并+分割）")

    try:
        start_time = time.time()
        result = processor.process()
        elapsed = time.time() - start_time

        print(f"\n✓ 处理完成，耗时: {elapsed:.2f} 秒")

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        logger.error(f"处理失败", exc_info=True)
        return

    if not result.success:
        print(f"\n❌ 处理失败")
        print(f"  错误: {result.error}")
        return

    # 统计信息
    stats = result.statistics
    print(f"\n统计信息:")
    print(f"  输入图片: {stats.get('total_images', 0)} 张")
    print(f"  有文字的图片: {stats.get('images_with_text', 0)} 张")
    print(f"  跳过的稀疏区域: {stats.get('sparse_regions_skipped', 0)} 个")
    print(f"  跳过的空白图片: {stats.get('empty_images_skipped', 0)} 张")
    print(f"  输出文件: {stats.get('output_count', 0)} 个")
    print(f"  合并组数: {stats.get('merge_groups', 0)} 个")

    # 输出文件列表
    print(f"\n输出文件:")
    from PIL import Image
    total_size = 0
    for i, file_path in enumerate(result.output_files, 1):
        path = Path(file_path)
        size = os.path.getsize(file_path)
        total_size += size

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                print(f"  {i:2d}. {path.name:35s} {width}x{height:4d}px  {format_size(size):>8s}")
        except Exception as e:
            print(f"  {i:2d}. {path.name:35s} (无法读取: {e})")

    print(f"  总大小: {format_size(total_size)}")

    # ===== 步骤 4: 初始化 OCR 提供商 =====
    step += 1
    print_step(step, "初始化 OCR 提供商")

    try:
        provider = OllamaProvider()
        print(f"\nOCR 提供商信息:")
        print(f"  类型: {provider.__class__.__name__}")
        print(f"  服务地址: {provider.base_url}")
        print(f"  模型: {provider._model}")
        print(f"  超时: {provider.timeout}s")
        print(f"  最大文件大小: {provider.max_size/1024/1024:.1f}MB")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        logger.error(f"初始化 OCR 提供商失败: {e}", exc_info=True)
        return

    # ===== 步骤 5: 测试远程服务连接 =====
    step += 1
    print_step(step, "测试远程服务连接")

    try:
        print(f"\n正在连接 {provider.base_url} ...")
        logger.info(f"尝试连接 Ollama 服务: {provider.base_url}")

        client = provider._get_client()
        print(f"  ✓ 客户端创建成功")

        # 测试 list API
        print(f"\n正在调用 list() API...")
        api_result = client.list()
        print(f"  ✓ API 调用成功")
        print(f"  可用模型数: {len(api_result.get('models', []))}")

    except Exception as e:
        print(f"\n❌ 连接失败")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误信息: {e}")
        logger.error(f"连接 Ollama 服务失败", exc_info=True)
        print(f"\n可能的原因:")
        print(f"  1. 远程服务 {provider.base_url} 未运行")
        print(f"  2. 网络不可达")
        print(f"  3. 防火墙阻止连接")
        return

    # ===== 步骤 6: OCR 识别 =====
    step += 1
    print_step(step, "OCR 文字识别")

    try:
        print(f"\n开始 OCR 识别 {len(result.output_files)} 个文件...")
        logger.info("开始 OCR 识别")

        import base64
        start_time = time.time()
        all_markdown = []

        for i, image_path in enumerate(result.output_files):
            path = Path(image_path)
            print(f"\n  [{i+1}/{len(result.output_files)}] {path.name}")
            logger.info(f"处理文件 {i+1}/{len(result.output_files)}: {path.name}")

            # 编码图片
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            file_size = os.path.getsize(image_path)
            print(f"    大小: {format_size(file_size)}")

            # 调用 OCR
            print(f"    调用 OCR API...")
            api_start = time.time()

            try:
                response = client.generate(
                    model=provider._model,
                    prompt="Extract all text from this image and return it in a structured markdown format.",
                    images=[img_data],
                    options={'temperature': 0.1}
                )
                markdown = response['response'].strip()
                all_markdown.append(f"## {path.name}\n\n{markdown}")

                api_elapsed = time.time() - api_start
                print(f"    ✓ 完成 (耗时: {api_elapsed:.1f}s, 文本: {len(markdown)} 字符)")

            except Exception as e:
                logger.error(f"文件 {path.name} OCR 失败: {e}")
                all_markdown.append(f"## {path.name}\n\n*[OCR 失败: {e}]*")
                print(f"    ✗ 失败: {e}")

        # 合并结果
        final_markdown = "\n\n".join(all_markdown)
        elapsed = time.time() - start_time

        print(f"\n  ✓ OCR 识别完成")
        print(f"  总耗时: {elapsed:.1f} 秒")
        print(f"  文本总长度: {len(final_markdown)} 字符")

    except Exception as e:
        print(f"\n❌ OCR 识别失败")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误信息: {e}")
        logger.error(f"OCR 识别失败", exc_info=True)

        # 保存错误信息
        error_file = ocr_output_dir / f"ocr_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"OCR 识别失败\n\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"错误: {e}\n")
            f.write(f"错误类型: {type(e).__name__}\n")
        print(f"  错误信息已保存到: {error_file}")
        return

    # ===== 步骤 7: 保存结果 =====
    step += 1
    print_step(step, "保存结果")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = ocr_output_dir / f"ocr_result_{timestamp}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# OCR 识别结果\n\n")
        f.write(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**输入图片**: {stats.get('total_images', 0)} 张\n")
        f.write(f"**有文字图片**: {stats.get('images_with_text', 0)} 张\n")
        f.write(f"**输出文件**: {stats.get('output_count', 0)} 个\n")
        f.write(f"**合并组数**: {stats.get('merge_groups', 0)} 个\n")
        f.write(f"**提供商**: ollama\n")
        f.write(f"**模型**: {provider._model}\n")
        f.write(f"**OCR耗时**: {elapsed:.1f} 秒\n")
        f.write(f"**处理耗时**: {stats.get('processing_time_ms', 0) / 1000:.1f} 秒\n")
        f.write(f"**服务地址**: {provider.base_url}\n\n")
        f.write(f"**文本长度**: {len(final_markdown)} 字符\n\n")
        f.write("---\n\n")
        f.write(final_markdown)

    print(f"\n✓ 结果已保存到: {output_file.absolute()}")

    # ===== 步骤 8: 完成 =====
    step += 1
    print_step(step, "测试完成")

    print(f"\n✅ 全部步骤完成!")
    print(f"   输入图片: {stats.get('total_images', 0)} 张")
    print(f"   输出文件: {stats.get('output_count', 0)} 个")
    print(f"   OCR文本: {len(final_markdown)} 字符")
    print(f"   总耗时: {stats.get('processing_time_ms', 0) / 1000 + elapsed:.1f} 秒")

    # 显示前500字符预览
    print(f"\n--- 文本预览 (前500字符) ---")
    print(final_markdown[:500])
    if len(final_markdown) > 500:
        print("...")
    print(f"{'-'*60}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 未预期的错误: {e}")
        logger.error(f"未预期的错误", exc_info=True)
