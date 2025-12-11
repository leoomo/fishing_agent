#!/usr/bin/env python3
"""
平台抽象层简单测试
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from packages.agent_fishing.tools.crawler.platform.registry import platform_registry
from packages.agent_fishing.tools.crawler.platform.base_platform import TaskConfig, TaskType

def main():
    """测试平台抽象层"""
    print("=== 平台抽象层测试 ===")

    # 1. 获取支持的平台
    platforms = platform_registry.get_supported_platforms()
    print(f"支持的平台: {platforms}")

    # 2. 测试URL检测
    test_urls = [
        "https://item.taobao.com/item.htm?id=123456789",
        "https://detail.tmall.com/item.htm?id=987654321",
        "https://item.jd.com/123456.html",
        "https://shop.jd.com/12345.html"
    ]

    print("\nURL检测测试:")
    for url in test_urls:
        platform = platform_registry.detect_platform_by_url(url)
        print(f"  {url} -> {platform}")

    # 3. 创建测试配置
    print("\n创建任务配置:")
    config = TaskConfig(
        task_type=TaskType.KEYWORD_SEARCH,
        keywords=["路亚竿", "渔轮"],
        max_pages=2
    )
    print(f"  配置: {config}")

    # 4. 获取平台实例
    print("\n获取平台实例:")
    taobao = platform_registry.get_platform("taobao")
    print(f"  淘宝平台: {taobao.__class__.__name__}")

    jd = platform_registry.get_platform("jd")
    print(f"  京东平台: {jd.__class__.__name__}")

    # 5. 验证配置
    print("\n验证配置:")
    is_valid = taobao.validate_config(config)
    print(f"  配置有效性: {is_valid}")

    # 6. 任务估算
    print("\n任务估算:")
    estimate = taobao.get_task_estimate(config)
    print(f"  估算信息: {estimate}")

    print("\n✅ 平台抽象层基础功能测试完成！")


if __name__ == "__main__":
    main()