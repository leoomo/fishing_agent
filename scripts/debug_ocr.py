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

    # 获取当前配置的提供商
    provider = os.getenv("OCR_PROVIDER", "ollama")
    print(f"{Fore.YELLOW}当前提供商: {provider.upper()}{Style.RESET_ALL}")

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "deepseek-ocr")
        timeout = os.getenv("OLLAMA_TIMEOUT", "120")
        max_size = os.getenv("OLLAMA_MAX_SIZE", str(20 * 1024 * 1024))

        print(f"服务地址: {base_url}")
        print(f"模型: {model}")
        print(f"超时时间: {timeout}秒")
        print(f"最大文件大小: {int(max_size) / 1024 / 1024:.1f}MB")
        print(f"类型: 本地OCR")

        # 检查服务可用性
        try:
            from apps.api.services.ocr import OCRProviderFactory
            ollama_provider = OCRProviderFactory.create_provider("ollama")
            if ollama_provider.is_available():
                print(f"{Fore.GREEN}状态: 可用 ✓{Style.RESET_ALL}")
                model_info = ollama_provider.get_model_info()
                print(f"模型详情: {model_info}")
            else:
                print(f"{Fore.RED}状态: 不可用 ✗{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}状态: 检查失败 - {e}{Style.RESET_ALL}")

    elif provider == "siliconflow":
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

        print(f"模型: deepseek-ai/DeepSeek-OCR")
        print(f"超时时间: {timeout}秒")
        print(f"最大文件大小: {int(max_size) / 1024 / 1024:.1f}MB")
        print(f"类型: 云端OCR")

        # 检查API密钥有效性
        try:
            from apps.api.services.ocr import OCRProviderFactory
            siliconflow_provider = OCRProviderFactory.create_provider("siliconflow")
            if siliconflow_provider.is_available():
                print(f"{Fore.GREEN}状态: 可用 ✓{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}状态: 不可用 ✗{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}状态: 检查失败 - {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}错误: 未知的提供商 '{provider}'{Style.RESET_ALL}")
        print(f"支持的提供商: ollama, siliconflow")

    print(f"\n{Fore.CYAN}通用信息:{Style.RESET_ALL}")
    print(f"支持格式: PNG, JPG, JPEG, WebP")
    print()

    # 显示所有提供商的可用性
    try:
        from apps.api.services.ocr import OCRProviderFactory
        availability = OCRProviderFactory.get_available_providers()
        print(f"{Fore.CYAN}所有提供商可用性:{Style.RESET_ALL}")
        for provider_name, available in availability.items():
            status = f"{Fore.GREEN}✓ 可用{Style.RESET_ALL}" if available else f"{Fore.RED}✗ 不可用{Style.RESET_ALL}"
            print(f"  {provider_name}: {status}")
    except Exception as e:
        print(f"获取提供商状态失败: {e}")

    print()


def batch_recognize(
    image_dir: str,
    batch_size: int = 2,
    output_file: str = None,
    verbose: bool = False
):
    """
    批量处理目录中的图片

    流程:
    1. 使用 BatchMergeProcessor 智能合并图片
    2. 扫描合并后的图片
    3. 逐个识别合并后的图片（间隔2秒）
    4. 汇总结果输出到 Markdown

    Args:
        image_dir: 源图片目录
        batch_size: 传统分组的大小（备用）
        output_file: 输出文件路径
        verbose: 详细日志
    """
    from apps.api.services.ocr_service import OCRService
    from packages.agent_fishing.tools.lure.batch_merge_processor import BatchMergeProcessor

    print(f"\n{Fore.CYAN}========== OCR 批量处理（智能合并） =========={Style.RESET_ALL}\n")

    image_dir = Path(image_dir)
    if not image_dir.exists():
        print(f"{Fore.RED}错误: 目录不存在 {image_dir}{Style.RESET_ALL}")
        return

    # Step 1: 智能合并阶段
    print(f"{Fore.YELLOW}Step 1: 智能合并图片{Style.RESET_ALL}")
    print(f"  源目录: {image_dir}")
    print(f"  检测策略: 自动检测图片下方是否有文字")
    print(f"  检测区域: 底部20%")
    print(f"  置信度阈值: 0.2")

    try:
        # 使用智能分组
        processor = BatchMergeProcessor(
            source_dir=str(image_dir),
            bottom_detection_ratio=0.2,
            ocr_confidence_threshold=0.2,
            min_text_length=1,
            parallel_detection=True,
            max_workers=4,
            quality=95
        )
        result = processor.process()

        if not result.get("success"):
            print(f"{Fore.RED}合并失败: {result.get('error')}{Style.RESET_ALL}")
            return

        merged_dir = processor.output_dir
        merged_files = sorted(merged_dir.glob("*.jpg"))
        stats = result['statistics']

        print(f"{Fore.GREEN}  智能合并完成:{Style.RESET_ALL}")
        print(f"    原始图片: {stats.get('original_count', 0)} 张")
        print(f"    合并后: {len(merged_files)} 张")
        print(f"    检测到文字的图片: {stats.get('text_detections', 0)} 张")
        print(f"    减少比例: {stats.get('reduction_ratio', 0):.1%}")
        print(f"  输出目录: {merged_dir}")

        # 显示合并策略详情
        print(f"\n{Fore.CYAN}合并策略详情:{Style.RESET_ALL}")
        if 'metadata_path' in result and result['metadata_path']:
            import json
            with open(result['metadata_path'], 'r') as f:
                metadata = json.load(f)

            groups = metadata.get('merge_groups', [])
            for i, group in enumerate(groups[:10]):  # 显示前10个
                source_files = group.get('source_files', [])
                reason = group.get('reason', '')
                if len(source_files) > 1:
                    print(f"  组{i+1}: {' + '.join(source_files)}")
                    print(f"       {reason}")
                else:
                    print(f"  组{i+1}: {source_files[0]}")

            if len(groups) > 10:
                print(f"  ... 还有 {len(groups) - 10} 个组")

    except Exception as e:
        print(f"{Fore.RED}合并异常: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: 识别阶段
    print(f"\n{Fore.YELLOW}Step 2: OCR 识别{Style.RESET_ALL}")
    print(f"  待识别: {len(merged_files)} 张合并图片")

    # 检查OCR提供商类型
    provider_type = os.getenv("OCR_PROVIDER", "ollama")
    is_api_mode = provider_type == "siliconflow"

    if is_api_mode:
        print(f"  模式: API模式 (SiliconFlow)")
        print(f"  请求间隔: 3 秒（防止请求过快）")
    else:
        print(f"  模式: 本地模式 (Ollama)")
        print(f"  请求间隔: 无延迟")
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

        # 仅在API模式下添加请求间隔
        if is_api_mode and i < len(merged_files):
            time.sleep(3)

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

  # 默认模式（合并并识别，输出到 debug_rs.md）
  uv run python scripts/debug_ocr.py
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

    # 默认模式：如果没有提供任何参数，使用默认图片目录并输出到 debug_rs.md
    if not args.images and not args.batch:
        default_dir = "shared/images/851749152448"
        output_file = "debug_rs.md"

        # 检查默认目录是否存在
        if Path(default_dir).exists():
            print(f"{Fore.CYAN}使用默认配置:{Style.RESET_ALL}")
            print(f"  图片目录: {default_dir}")
            print(f"  输出文件: {output_file}")
            print()

            batch_recognize(
                image_dir=default_dir,
                batch_size=2,  # 默认两张合并
                output_file=output_file,
                verbose=args.verbose
            )
        else:
            print(f"{Fore.RED}默认图片目录不存在: {default_dir}{Style.RESET_ALL}")
            print(f"请指定图片路径或使用 --batch 指定目录")
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
