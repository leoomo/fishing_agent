#!/usr/bin/env python
"""
调试脚本：测试 agent_equipment_import 从 OCR 文本提取装备信息

使用方法:
    PYTHONPATH=. uv run python scripts/debug_equipment_import.py
"""

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


def extract_product_sections(text: str) -> list[dict]:
    """
    从 OCR 文本中提取各个产品区块

    根据 markdown 结构，每个 merge_xxx.jpg 开始一个新区块
    """
    sections = []
    current_section = None
    current_lines = []

    for line in text.split("\n"):
        # 检测新的图片区块
        if line.startswith("## merge_") and line.endswith(".jpg"):
            # 保存上一个区块
            if current_section and current_lines:
                sections.append({
                    "image": current_section,
                    "content": "\n".join(current_lines).strip()
                })
            current_section = line.replace("## ", "").strip()
            current_lines = []
        elif current_section:
            current_lines.append(line)

    # 保存最后一个区块
    if current_section and current_lines:
        sections.append({
            "image": current_section,
            "content": "\n".join(current_lines).strip()
        })

    return sections


def find_spec_tables(sections: list[dict]) -> list[dict]:
    """
    找出包含规格参数表的区块

    这些区块通常包含具体的产品参数，是我们需要提取的主要内容
    """
    spec_sections = []

    for section in sections:
        content = section["content"]
        # 检测是否包含规格表（markdown 表格）
        if "| 规格" in content or "| 型号" in content:
            spec_sections.append(section)
        # 检测是否包含详细参数
        elif "详细参数" in content or "产品参数" in content:
            spec_sections.append(section)

    return spec_sections


def main():
    """主函数"""
    # 加载 OCR 文本
    ocr_file = Path("debug_rs.md")
    if not ocr_file.exists():
        logger.error(f"文件不存在: {ocr_file}")
        sys.exit(1)

    logger.info(f"加载 OCR 文件: {ocr_file}")
    ocr_text = load_ocr_text(str(ocr_file))
    logger.info(f"文本长度: {len(ocr_text)} 字符")

    # 提取产品区块
    sections = extract_product_sections(ocr_text)
    logger.info(f"提取到 {len(sections)} 个图片区块")

    # 找出包含规格表的区块
    spec_sections = find_spec_tables(sections)
    logger.info(f"其中 {len(spec_sections)} 个包含规格参数表")

    # 显示找到的规格区块
    print("\n" + "=" * 60)
    print("包含规格参数的区块:")
    print("=" * 60)
    for i, section in enumerate(spec_sections, 1):
        print(f"\n[{i}] {section['image']}")
        print("-" * 40)
        # 只显示前 500 字符
        content = section["content"]
        if len(content) > 500:
            print(content[:500] + "...")
        else:
            print(content)

    # 初始化装备导入 Agent
    print("\n" + "=" * 60)
    print("初始化装备导入 Agent...")
    print("=" * 60)

    try:
        from packages.agent_equipment_import import EquipmentImportAgent

        # 使用 qwen 模型（更稳定）
        agent = EquipmentImportAgent(model_provider="qwen", enable_logging=True)
        logger.info("Agent 初始化成功")

    except Exception as e:
        logger.error(f"Agent 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 选择一个包含完整规格的区块进行测试
    # merge_011_012 包含详细参数表
    test_section = None
    for section in spec_sections:
        if "详细参数" in section["content"] or "C631ML" in section["content"]:
            test_section = section
            break

    if not test_section:
        # 使用第一个规格区块
        test_section = spec_sections[0] if spec_sections else sections[0]

    print("\n" + "=" * 60)
    print(f"测试提取: {test_section['image']}")
    print("=" * 60)
    print(test_section["content"][:1000])

    # 使用 extract_only 仅提取不保存
    print("\n" + "=" * 60)
    print("开始提取装备信息...")
    print("=" * 60)

    try:
        extracted = agent.extract_only(
            text=test_section["content"],
            source_type="ecommerce"
        )

        print("\n提取结果:")
        print("-" * 40)
        print(f"装备类型: {extracted.equipment_type}")
        print(f"品牌: {extracted.brand_name}")
        print(f"型号: {extracted.model}")
        print(f"名称: {extracted.name}")
        print(f"价格: {extracted.price_min} - {extracted.price_max}")
        print(f"置信度: {extracted.confidence:.0%}")
        print(f"提取备注: {extracted.extraction_notes}")

        print("\n规格参数:")
        print(json.dumps(extracted.specs, ensure_ascii=False, indent=2))

        print("\n特点:")
        for feature in extracted.features:
            print(f"  - {feature}")

        print("\n目标鱼种:")
        for fish in extracted.target_fish:
            print(f"  - {fish}")

        # 保存到待审核表
        print("\n" + "=" * 60)
        print("保存到待审核表...")
        print("=" * 60)

        result = agent.extract_and_save(
            text=test_section["content"],
            source_type="ecommerce",
            source_url="https://item.taobao.com/item.htm?id=851749152448"
        )

        print(f"保存结果: {'成功' if result.success else '失败'}")
        print(f"消息: {result.message}")
        if result.pending_id:
            print(f"待审核 ID: {result.pending_id}")

    except Exception as e:
        logger.error(f"提取失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 批量测试多个区块
    print("\n" + "=" * 60)
    print("批量测试其他规格区块...")
    print("=" * 60)

    for i, section in enumerate(spec_sections[:5], 1):  # 最多测试 5 个
        if section == test_section:
            continue

        print(f"\n[{i}] {section['image']}")
        try:
            extracted = agent.extract_only(
                text=section["content"],
                source_type="ecommerce"
            )
            print(f"   类型: {extracted.equipment_type}")
            print(f"   品牌: {extracted.brand_name}")
            print(f"   型号: {extracted.model}")
            print(f"   置信度: {extracted.confidence:.0%}")
        except Exception as e:
            print(f"   提取失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
