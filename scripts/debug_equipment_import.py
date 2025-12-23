#!/usr/bin/env python
"""
调试脚本：测试 agent_equipment_import 从 OCR 文本提取装备信息

使用方法:
    PYTHONPATH=. uv run python scripts/debug_equipment_import.py

该脚本会：
1. 加载 OCR 文本
2. 使用文本压缩中间件压缩长文本
3. 批量提取所有型号的装备信息
4. 保存到待审核表
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_ocr_text(file_path: str) -> str:
    """加载 OCR 识别结果文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def test_compression(text: str):
    """测试文本压缩效果"""
    from packages.agents.equipment_import.middleware import TextCompressor

    print("\n" + "=" * 60)
    print("测试文本压缩效果")
    print("=" * 60)

    compressor = TextCompressor()
    result = compressor.compress(text)

    print(f"\n原始长度: {result.original_length} 字符")
    print(f"压缩后长度: {result.compressed_length} 字符")
    print(f"压缩率: {result.compression_ratio:.1%}")

    if result.metadata:
        print(f"\n检测到的元信息:")
        if result.metadata.get("brands"):
            print(f"  品牌: {result.metadata['brands']}")
        if result.metadata.get("series"):
            print(f"  系列: {result.metadata['series']}")
        if result.metadata.get("model_count"):
            print(f"  型号数量: {result.metadata['model_count']}")
        if result.metadata.get("models"):
            print(f"  型号列表: {result.metadata['models'][:10]}...")

    # 显示压缩后文本的前 1000 字符
    print(f"\n压缩后文本预览 (前 1000 字符):")
    print("-" * 40)
    print(result.content[:1000])
    print("-" * 40)

    return result


def test_batch_extraction(agent, text: str):
    """测试批量提取效果"""
    print("\n" + "=" * 60)
    print("测试批量提取 (从完整文本提取所有型号)")
    print("=" * 60)

    # 批量提取（不保存）
    extracted_list = agent.batch_extract_only(
        text=text,
        source_type="ecommerce"
    )

    print(f"\n提取到 {len(extracted_list)} 个型号:")
    print("-" * 40)

    for i, extracted in enumerate(extracted_list, 1):
        print(f"\n[{i}] {extracted.brand_name or '未知品牌'} - {extracted.model or '未知型号'}")
        print(f"    类型: {extracted.equipment_type}")
        if extracted.specs:
            specs_summary = []
            if extracted.specs.get("length"):
                specs_summary.append(f"长度:{extracted.specs['length']}m")
            if extracted.specs.get("power"):
                specs_summary.append(f"硬度:{extracted.specs['power']}")
            if extracted.specs.get("action"):
                specs_summary.append(f"调性:{extracted.specs['action']}")
            if specs_summary:
                print(f"    规格: {', '.join(specs_summary)}")
        print(f"    置信度: {extracted.confidence:.0%}")

    return extracted_list


def test_batch_save(agent, text: str, source_url: str):
    """测试批量提取并保存"""
    print("\n" + "=" * 60)
    print("测试批量提取并保存到待审核表")
    print("=" * 60)

    results = agent.batch_extract_and_save(
        text=text,
        source_type="ecommerce",
        source_url=source_url
    )

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    print(f"\n批量保存结果:")
    print(f"  成功: {success_count} 个")
    print(f"  失败: {fail_count} 个")

    if fail_count > 0:
        print(f"\n失败详情:")
        for r in results:
            if not r.success:
                model = r.extracted.model if r.extracted else "未知"
                print(f"  - {model}: {r.message}")

    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试装备导入 Agent")
    parser.add_argument("--save", action="store_true", help="自动保存到待审核表")
    parser.add_argument("--no-save", action="store_true", help="跳过保存确认")
    parser.add_argument("--file", type=str, default="debug_rs.md", help="OCR 文件路径")
    args = parser.parse_args()

    # 加载 OCR 文本
    ocr_file = Path(args.file)
    if not ocr_file.exists():
        logger.error(f"文件不存在: {ocr_file}")
        sys.exit(1)

    logger.info(f"加载 OCR 文件: {ocr_file}")
    ocr_text = load_ocr_text(str(ocr_file))
    logger.info(f"文本长度: {len(ocr_text)} 字符")

    # 测试文本压缩
    compressed = test_compression(ocr_text)

    # 初始化装备导入 Agent
    print("\n" + "=" * 60)
    print("初始化装备导入 Agent...")
    print("=" * 60)

    try:
        from packages.agents.equipment_import import EquipmentImportAgent

        # 使用 qwen 模型，启用压缩
        agent = EquipmentImportAgent(
            model_provider="qwen",
            enable_logging=True,
            enable_compression=True
        )
        logger.info("Agent 初始化成功")

    except Exception as e:
        logger.error(f"Agent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 测试批量提取
    extracted_list = test_batch_extraction(agent, ocr_text)

    # 处理保存逻辑
    if extracted_list:
        should_save = False
        if args.save:
            should_save = True
        elif args.no_save:
            should_save = False
        else:
            # 交互式询问
            print("\n" + "-" * 40)
            try:
                user_input = input("是否保存到待审核表? (y/n): ").strip().lower()
                should_save = user_input == "y"
            except EOFError:
                print("非交互模式，跳过保存 (使用 --save 自动保存)")
                should_save = False

        if should_save:
            test_batch_save(
                agent,
                ocr_text,
                source_url="https://item.taobao.com/item.htm?id=851749152448"
            )
        else:
            print("跳过保存")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
