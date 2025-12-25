#!/usr/bin/env python
"""
本地 OCR 测试脚本（带详细进度显示）

读取 shared/images/pending/1 中的图片，使用远程 Ollama 服务进行 OCR 识别，
结果保存到 shared/images/output/ 目录
"""

import os
import sys
import glob
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

from apps.api.services.ocr.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"  步骤 {step_num}: {description}")
    print(f"{'='*60}")
    logger.info(f"步骤 {step_num}: {description}")


def main():
    step = 0

    # ===== 步骤 1: 配置检查 =====
    step += 1
    print_step(step, "配置检查")

    input_dir = Path("shared/images/pending/1")
    output_dir = Path("shared/images/output")

    # 检查环境变量
    print(f"\n环境变量:")
    print(f"  OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL', '未设置')}")
    print(f"  OCR_PROVIDER: {os.getenv('OCR_PROVIDER', '未设置')}")

    # 检查输入目录
    if not input_dir.exists():
        print(f"  ❌ 输入目录不存在: {input_dir.absolute()}")
        return
    print(f"  ✓ 输入目录存在: {input_dir.absolute()}")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 输出目录: {output_dir.absolute()}")

    # ===== 步骤 2: 扫描图片 =====
    step += 1
    print_step(step, "扫描图片文件")

    image_paths = sorted(
        glob.glob(str(input_dir / "*.jpg")),
        key=lambda x: int(Path(x).stem)
    )

    print(f"\n找到 {len(image_paths)} 张图片:")
    for i, path in enumerate(image_paths[:5]):
        size = os.path.getsize(path)
        print(f"  {i+1}. {Path(path).name} ({size/1024:.1f}KB)")
    if len(image_paths) > 5:
        print(f"  ... 还有 {len(image_paths)-5} 张")

    # ===== 步骤 3: 初始化 OCR 提供商 =====
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

    # ===== 步骤 4: 测试远程服务连接 =====
    step += 1
    print_step(step, "测试远程服务连接")

    try:
        print(f"\n正在连接 {provider.base_url} ...")
        logger.info(f"尝试连接 Ollama 服务: {provider.base_url}")

        client = provider._get_client()
        print(f"  ✓ 客户端创建成功")

        # 测试 list API
        print(f"\n正在调用 list() API...")
        result = client.list()
        print(f"  ✓ API 调用成功")
        print(f"  返回类型: {type(result)}")
        print(f"  返回内容: {result}")

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

    # ===== 步骤 5: 检查模型可用性 =====
    step += 1
    print_step(step, "检查 OCR 模型")

    try:
        print(f"\n正在检查模型 {provider._model}...")
        logger.info(f"检查模型: {provider._model}")

        model_info = client.show(provider._model)
        print(f"  ✓ 模型已存在")
        print(f"  模型信息: {model_info}")

    except Exception as e:
        print(f"\n⚠️  模型检查失败: {e}")
        print(f"  尝试拉取模型...")

        try:
            print(f"\n正在拉取模型 {provider._model}...")
            import sys
            for digest in client.pull(provider._model, stream=True):
                if 'status' in digest:
                    print(f"  {digest['status']}")
            print(f"  ✓ 模型拉取完成")

        except Exception as pull_error:
            print(f"\n❌ 模型拉取失败: {pull_error}")
            logger.error(f"模型拉取失败", exc_info=True)
            return

    # ===== 步骤 6: 图片处理 =====
    step += 1
    print_step(step, "图片预处理")

    try:
        print(f"\n正在处理 {len(image_paths)} 张图片...")
        logger.info(f"开始图片处理，共 {len(image_paths)} 张")

        merged_paths, images_merged = provider._merge_images(image_paths)

        print(f"  ✓ 处理完成")
        print(f"  输入: {images_merged} 张")
        print(f"  输出: {len(merged_paths)} 个文件")

        # 显示输出文件信息
        from PIL import Image
        total_size = 0
        for i, path in enumerate(merged_paths):
            with Image.open(path) as img:
                size = os.path.getsize(path)
                total_size += size
                print(f"    文件 {i+1}: {img.width}x{img.height}, {size/1024:.1f}KB")

        print(f"  总大小: {total_size/1024/1024:.2f}MB")

    except Exception as e:
        print(f"\n❌ 图片处理失败: {e}")
        logger.error(f"图片处理失败", exc_info=True)
        return

    # ===== 步骤 7: OCR 识别 =====
    step += 1
    print_step(step, "OCR 文字识别")

    try:
        print(f"\n开始 OCR 识别...")
        logger.info("开始 OCR 识别")

        start_time = time.time()
        all_markdown = []

        for i, target_path in enumerate(merged_paths):
            print(f"\n  处理文件 {i+1}/{len(merged_paths)}: {Path(target_path).name}")

            # 编码图片
            print(f"    - 编码图片...")
            import base64
            with open(target_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            file_size = os.path.getsize(target_path)
            print(f"    - 图片大小: {file_size/1024:.1f}KB")

            # 调用 OCR
            print(f"    - 调用 OCR API (模型: {provider._model})...")
            logger.info(f"调用 OCR API: {provider._model}")

            api_start = time.time()
            response = client.generate(
                model=provider._model,
                prompt="Extract all text from this image and return it in a structured markdown format.",
                images=[img_data],
                options={'temperature': 0.1}
            )
            api_elapsed = time.time() - api_start

            markdown = response['response'].strip()
            all_markdown.append(markdown)

            print(f"    - ✓ 完成 (耗时: {api_elapsed:.1f}s, 文本长度: {len(markdown)} 字符)")

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
        error_file = output_dir / f"ocr_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"OCR 识别失败\n\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"错误: {e}\n")
            f.write(f"错误类型: {type(e).__name__}\n")
        print(f"  错误信息已保存到: {error_file}")
        return

    # ===== 步骤 8: 保存结果 =====
    step += 1
    print_step(step, "保存结果")

    output_file = output_dir / "ocr_result.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# OCR 识别结果\n\n")
        f.write(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**输入图片**: {len(image_paths)} 张\n")
        f.write(f"**提供商**: ollama\n")
        f.write(f"**模型**: {provider._model}\n")
        f.write(f"**耗时**: {elapsed:.1f} 秒\n")
        f.write(f"**服务地址**: {provider.base_url}\n\n")
        f.write(f"**文本长度**: {len(final_markdown)} 字符\n\n")
        f.write("---\n\n")
        f.write(final_markdown)

    print(f"\n✓ 结果已保存到: {output_file.absolute()}")

    # ===== 步骤 9: 完成 =====
    step += 1
    print_step(step, "测试完成")

    print(f"\n✅ 全部步骤完成!")
    print(f"   输入图片: {len(image_paths)} 张")
    print(f"   输出文件: {output_file.name}")
    print(f"   文本长度: {len(final_markdown)} 字符")
    print(f"   总耗时: {elapsed:.1f} 秒")

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
