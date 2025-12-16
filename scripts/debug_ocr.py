#!/usr/bin/env python3
"""
OCR 调试脚本

独立运行的调试工具，用于测试图片表格识别功能。
无需启动完整 API 服务即可测试 OCR 功能。

用法:
    # 单张图片
    uv run python scripts/debug_ocr.py image.png

    # 多张图片（自动合并）
    uv run python scripts/debug_ocr.py image1.png image2.png image3.png

    # 保存结果到文件
    uv run python scripts/debug_ocr.py image.png --output result.md

    # 详细日志模式
    uv run python scripts/debug_ocr.py image.png --verbose

    # 检查服务状态
    uv run python scripts/debug_ocr.py --status

    # 批量处理目录（每N张合并后识别）
    uv run python scripts/debug_ocr.py --batch /path/to/images --batch-size 5 --output result.md
"""

import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from colorama import Fore, Style, init

# 初始化 colorama
init(autoreset=True)


def setup_logging(verbose: bool = False):
    """配置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_status():
    """打印 OCR 服务状态"""
    print(f"\n{Fore.CYAN}========== OCR 服务状态 =========={Style.RESET_ALL}\n")

    api_key = os.getenv("SILICONFLOW_API_KEY")
    timeout = os.getenv("SILICONFLOW_OCR_TIMEOUT", "30")
    max_size = os.getenv("SILICONFLOW_OCR_MAX_SIZE", str(10 * 1024 * 1024))

    if api_key:
        # 隐藏部分密钥
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"{Fore.GREEN}API 密钥: {masked_key}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}API 密钥: 未配置{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  请在 .env 中设置 SILICONFLOW_API_KEY{Style.RESET_ALL}")

    print(f"超时时间: {timeout}秒")
    print(f"最大文件大小: {int(max_size) / 1024 / 1024:.1f}MB")
    print(f"支持格式: PNG, JPG, JPEG, WebP")
    print(f"模型: deepseek-ai/DeepSeek-OCR")
    print()


def batch_recognize(
    image_dir: str,
    batch_size: int = 5,
    output_file: str = None,
    verbose: bool = False
):
    """
    批量处理目录中的图片

    流程:
    1. 使用 BatchMergeProcessor 合并图片到 merged/ 子目录
    2. 扫描 merged/ 目录
    3. 逐个识别合并后的图片（间隔2秒）
    4. 汇总结果输出到 Markdown

    Args:
        image_dir: 源图片目录
        batch_size: 每组合并的图片数量
        output_file: 输出文件路径
        verbose: 详细日志
    """
    from apps.api.services.ocr_service import OCRService
    from packages.agent_fishing.tools.lure.batch_merge_processor import BatchMergeProcessor

    print(f"\n{Fore.CYAN}========== OCR 批量处理 =========={Style.RESET_ALL}\n")

    image_dir = Path(image_dir)
    if not image_dir.exists():
        print(f"{Fore.RED}错误: 目录不存在 {image_dir}{Style.RESET_ALL}")
        return

    # Step 1: 合并阶段
    print(f"{Fore.YELLOW}Step 1: 合并图片{Style.RESET_ALL}")
    print(f"  源目录: {image_dir}")
    print(f"  每组合并: {batch_size} 张")

    try:
        processor = BatchMergeProcessor(
            source_dir=str(image_dir),
            merge_batch_size=batch_size
        )
        result = processor.process()

        if not result.get("success"):
            print(f"{Fore.RED}合并失败: {result.get('error')}{Style.RESET_ALL}")
            return

        merged_dir = processor.output_dir
        merged_files = sorted(merged_dir.glob("*.jpg"))
        print(f"{Fore.GREEN}  合并完成: {result['statistics']['original_count']} 张 → {len(merged_files)} 张{Style.RESET_ALL}")
        print(f"  输出目录: {merged_dir}")

    except Exception as e:
        print(f"{Fore.RED}合并异常: {e}{Style.RESET_ALL}")
        return

    # Step 2: 识别阶段
    print(f"\n{Fore.YELLOW}Step 2: OCR 识别{Style.RESET_ALL}")
    print(f"  待识别: {len(merged_files)} 张合并图片")
    print(f"  请求间隔: 2 秒")
    print()

    service = OCRService()
    all_results = []

    for i, img_path in enumerate(merged_files, 1):
        print(f"  [{i}/{len(merged_files)}] {img_path.name}...", end=" ", flush=True)

        ocr_result = service.recognize_table(str(img_path), verbose=verbose)

        if ocr_result["success"]:
            text = ocr_result["markdown"]
            all_results.append({
                "file": img_path.name,
                "success": True,
                "markdown": text,
                "time_ms": ocr_result["metadata"]["processing_time_ms"]
            })
            print(f"{Fore.GREEN}OK{Style.RESET_ALL} ({ocr_result['metadata']['processing_time_ms']}ms)")
        else:
            all_results.append({
                "file": img_path.name,
                "success": False,
                "error": ocr_result.get("error")
            })
            print(f"{Fore.RED}失败{Style.RESET_ALL}: {ocr_result.get('error')}")

        # 请求间隔 2 秒
        if i < len(merged_files):
            time.sleep(2)

    # Step 3: 汇总结果
    success_count = sum(1 for r in all_results if r["success"])
    print(f"\n{Fore.CYAN}========== 处理完成 =========={Style.RESET_ALL}")
    print(f"  成功: {success_count}/{len(all_results)}")

    # 保存结果
    if output_file:
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# OCR 批量识别结果\n\n")
            f.write(f"- 源目录: `{image_dir}`\n")
            f.write(f"- 原始图片数: {result['statistics']['original_count']}\n")
            f.write(f"- 合并后图片数: {len(merged_files)}\n")
            f.write(f"- 每组合并: {batch_size} 张\n")
            f.write(f"- 识别成功: {success_count}/{len(all_results)}\n\n")
            f.write("---\n\n")

            for r in all_results:
                f.write(f"## {r['file']}\n\n")
                if r["success"]:
                    f.write(r["markdown"])
                else:
                    f.write(f"*识别失败: {r.get('error')}*")
                f.write("\n\n---\n\n")

        print(f"\n{Fore.GREEN}结果已保存到: {output_path}{Style.RESET_ALL}")

    print()


def recognize_images(image_paths: list, output_file: str = None, verbose: bool = False):
    """
    执行图片识别

    Args:
        image_paths: 图片路径列表
        output_file: 输出文件路径（可选）
        verbose: 是否输出详细日志
    """
    from apps.api.services.ocr_service import OCRService, OCRError

    print(f"\n{Fore.CYAN}========== OCR 图片表格识别 =========={Style.RESET_ALL}\n")

    # 验证文件存在
    valid_paths = []
    for path in image_paths:
        if os.path.exists(path):
            valid_paths.append(path)
            print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {path}")
        else:
            print(f"{Fore.RED}[NOT FOUND]{Style.RESET_ALL} {path}")

    if not valid_paths:
        print(f"\n{Fore.RED}错误: 没有有效的图片文件{Style.RESET_ALL}")
        return

    print(f"\n共 {len(valid_paths)} 个有效图片文件")

    # 创建服务实例
    print(f"\n{Fore.YELLOW}正在初始化 OCR 服务...{Style.RESET_ALL}")
    service = OCRService()

    # 执行识别
    print(f"{Fore.YELLOW}正在识别图片...{Style.RESET_ALL}\n")

    result = service.recognize_table_from_paths(valid_paths, verbose=verbose)

    # 输出结果
    if result["success"]:
        print(f"{Fore.GREEN}识别成功!{Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}---------- 识别结果 ----------{Style.RESET_ALL}\n")
        print(result["markdown"])
        print(f"\n{Fore.CYAN}---------- 元数据 ----------{Style.RESET_ALL}\n")
        metadata = result["metadata"]
        print(f"模型: {metadata['model']}")
        print(f"处理时间: {metadata['processing_time_ms']}ms")
        print(f"合并图片数: {metadata['images_merged']}")
        if metadata.get('image_size_bytes'):
            print(f"图片大小: {metadata['image_size_bytes'] / 1024:.1f}KB")

        # 保存到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# OCR 识别结果\n\n")
                f.write(f"## 元数据\n")
                f.write(f"- 模型: {metadata['model']}\n")
                f.write(f"- 处理时间: {metadata['processing_time_ms']}ms\n")
                f.write(f"- 合并图片数: {metadata['images_merged']}\n")
                f.write(f"- 源文件: {', '.join([Path(p).name for p in valid_paths])}\n\n")
                f.write(f"## 识别内容\n\n")
                f.write(result["markdown"])
            print(f"\n{Fore.GREEN}结果已保存到: {output_file}{Style.RESET_ALL}")

    else:
        print(f"{Fore.RED}识别失败!{Style.RESET_ALL}\n")
        print(f"错误: {result.get('error')}")
        print(f"错误码: {result.get('error_code')}")

    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="OCR 图片表格识别调试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单张图片
  uv run python scripts/debug_ocr.py image.png

  # 多张图片（自动合并）
  uv run python scripts/debug_ocr.py image1.png image2.png

  # 保存结果到文件
  uv run python scripts/debug_ocr.py image.png --output result.md

  # 详细日志模式
  uv run python scripts/debug_ocr.py image.png --verbose

  # 检查服务状态
  uv run python scripts/debug_ocr.py --status

  # 批量处理目录（先合并后识别）
  uv run python scripts/debug_ocr.py --batch shared/images/851749152448 --output result.md

  # 自定义每组合并数量
  uv run python scripts/debug_ocr.py --batch shared/images/851749152448 --batch-size 3 --output result.md
        """
    )

    parser.add_argument(
        "images",
        nargs="*",
        help="图片文件路径（支持多个）"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径（保存识别结果）"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="输出详细日志"
    )
    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="检查 OCR 服务状态"
    )
    parser.add_argument(
        "-b", "--batch",
        help="批量处理目录（先合并后识别）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="每组合并的图片数量（默认5）"
    )

    args = parser.parse_args()

    # 配置日志
    setup_logging(args.verbose)

    # 检查状态
    if args.status:
        print_status()
        return

    # 批量处理模式
    if args.batch:
        batch_recognize(
            image_dir=args.batch,
            batch_size=args.batch_size,
            output_file=args.output,
            verbose=args.verbose
        )
        return

    # 检查图片参数
    if not args.images:
        parser.print_help()
        print(f"\n{Fore.YELLOW}提示: 请提供图片路径或使用 --batch 指定目录{Style.RESET_ALL}")
        return

    # 执行识别
    recognize_images(
        image_paths=args.images,
        output_file=args.output,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
