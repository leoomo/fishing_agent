#!/usr/bin/env python
"""
本地 OCR 测试脚本

读取 shared/images/pending/1 中的图片，使用远程 Ollama 服务进行 OCR 识别，
结果保存到 shared/images/output/ 目录
"""

import os
import sys
import glob
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from apps.api.services.ocr.ollama_provider import OllamaProvider


def main():
    # 配置
    input_dir = Path("shared/images/pending/1")
    output_dir = Path("shared/images/output")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取所有图片（按名称排序）
    image_paths = sorted(
        glob.glob(str(input_dir / "*.jpg")),
        key=lambda x: int(Path(x).stem)
    )

    print(f"=== 本地 OCR 测试 ===")
    print(f"输入目录: {input_dir.absolute()}")
    print(f"输出目录: {output_dir.absolute()}")
    print(f"图片数量: {len(image_paths)}")
    print()

    # 直接创建 OCR 提供商（绕过 factory 的可用性检查）
    print("正在初始化 OCR 提供商...")
    provider = OllamaProvider()
    print(f"✓ 提供商: {provider.__class__.__name__}")
    print(f"✓ 服务地址: {provider.base_url}")
    print(f"✓ 模型: {provider._model}")
    print()

    # 检查服务可用性
    print("检查服务可用性...")
    try:
        if not provider.is_available():
            print("❌ OCR 服务不可用，请检查:")
            print(f"  1. 远程服务 {provider.base_url} 是否运行")
            print("  2. 网络是否可达")
            return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("请检查:")
        print(f"  1. 远程服务 {provider.base_url} 是否运行")
        print("  2. 网络是否可达")
        return

    print("✓ OCR 服务可用")
    print()

    # 开始 OCR 识别
    print("开始 OCR 识别...")
    start_time = time.time()

    result = provider.recognize_table_from_paths(image_paths, verbose=True)

    elapsed = time.time() - start_time

    print()
    print(f"=== 识别完成，耗时: {elapsed:.1f} 秒 ===")
    print()

    if result.get("success"):
        # 保存结果到文件
        output_file = output_dir / "ocr_result.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# OCR 识别结果\n\n")
            f.write(f"**时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**输入图片**: {len(image_paths)} 张\n")
            f.write(f"**提供商**: {ocr_provider}\n")
            f.write(f"**模型**: {result.get('metadata', {}).get('model')}\n")
            f.write(f"**耗时**: {elapsed:.1f} 秒\n\n")
            f.write("---\n\n")
            f.write(result.get("markdown", ""))

        print(f"✅ OCR 识别成功!")
        print(f"   文本长度: {len(result.get('markdown', ''))} 字符")
        print(f"   结果已保存到: {output_file.absolute()}")

        # 显示前500字符预览
        print()
        print("--- 预览前500字符 ---")
        print(result.get("markdown", "")[:500])
        print("...")

    else:
        print(f"❌ OCR 识别失败")
        print(f"   错误: {result.get('error')}")
        print(f"   错误码: {result.get('error_code')}")

        # 保存错误信息
        error_file = output_dir / "ocr_error.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"OCR 识别失败\n\n")
            f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"错误: {result.get('error')}\n")
            f.write(f"错误码: {result.get('error_code')}\n")

        print(f"   错误信息已保存到: {error_file.absolute()}")


if __name__ == "__main__":
    main()
