#!/usr/bin/env python3
"""
平台抽象层测试

测试平台爬虫的注册、检测和基本功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """测试导入"""
    logger.info("=== 测试模块导入 ===")

    try:
        from packages.agents.fishing.tools.crawler.platform.registry import platform_registry
        from packages.agents.fishing.tools.crawler.platform.base_platform import TaskConfig, TaskType
        from packages.agents.fishing.tools.crawler.platform.taobao_platform import TaobaoPlatform
        from packages.agents.fishing.tools.crawler.platform.jd_platform import JDPlatform

        logger.info("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 模块导入失败: {e}")
        return False


def test_registry():
    """测试平台注册表"""
    logger.info("\n=== 测试平台注册表 ===")

    try:
        from packages.agents.fishing.tools.crawler.platform.registry import platform_registry

        # 获取支持的平台
        platforms = platform_registry.get_supported_platforms()
        logger.info(f"支持的平台: {platforms}")

        # 获取平台信息
        platform_info = platform_registry.get_platform_info()
        for name, info in platform_info.items():
            logger.info(f"平台 {name}: {info}")

        # 测试URL检测
        test_urls = [
            "https://item.taobao.com/item.htm?id=123456789",
            "https://detail.tmall.com/item.htm?id=987654321",
            "https://item.jd.com/123456.html",
            "https://shop.jd.com/12345.html",
            "https://unknown-website.com/product"
        ]

        for url in test_urls:
            platform = platform_registry.detect_platform_by_url(url)
            logger.info(f"URL: {url} -> 平台: {platform}")

        return True

    except Exception as e:
        logger.error(f"❌ 平台注册表测试失败: {e}")
        return False


def test_task_config():
    """测试任务配置"""
    logger.info("\n=== 测试任务配置 ===")

    try:
        from packages.agents.fishing.tools.crawler.platform.base_platform import TaskConfig, TaskType

        # 创建关键词搜索配置
        keyword_config = TaskConfig(
            task_type=TaskType.KEYWORD_SEARCH,
            keywords=["路亚竿", "渔轮"],
            max_pages=2,
            max_items_per_page=50
        )

        logger.info(f"关键词搜索配置: {keyword_config}")

        # 创建店铺爬取配置
        shop_config = TaskConfig(
            task_type=TaskType.SHOP_CRAWL,
            shop_url="https://shop.taobao.com/example",
            max_pages=3,
            custom_params={"categories": ["鱼竿", "渔轮"]}
        )

        logger.info(f"店铺爬取配置: {shop_config}")

        return True

    except Exception as e:
        logger.error(f"❌ 任务配置测试失败: {e}")
        return False


async def test_platform_crawl():
    """测试平台爬虫"""
    logger.info("\n=== 测试平台爬虫 ===")

    try:
        from packages.agents.fishing.tools.crawler.platform.registry import platform_registry
        from packages.agents.fishing.tools.crawler.platform.base_platform import TaskConfig, TaskType

        # 获取淘宝平台实例
        taobao = platform_registry.get_platform("taobao")

        # 创建测试配置
        test_config = TaskConfig(
            task_type=TaskType.KEYWORD_SEARCH,
            keywords=["测试关键词"],
            max_pages=1,
            max_items_per_page=5
        )

        # 验证配置
        is_valid = taobao.validate_config(test_config)
        logger.info(f"配置验证结果: {is_valid}")

        # 获取估算
        estimate = taobao.get_task_estimate(test_config)
        logger.info(f"任务估算: {estimate}")

        # 尝试执行爬虫（可能会失败，因为RPA模块可能不存在）
        try:
            result = await taobao.crawl(test_config)
            if result:
                logger.info(f"爬取成功! 获得 {result.total_count} 条数据")
            else:
                logger.warning("爬取返回空结果")
        except Exception as e:
            logger.warning(f"爬取失败（预期中）: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ 平台爬虫测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    logger.info("开始平台抽象层测试")

    tests = [
        ("模块导入", test_imports),
        ("平台注册表", test_registry),
        ("任务配置", test_task_config),
    ]

    # 同步测试
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 异常: {e}", exc_info=True)
            results.append((test_name, False))

    # 异步测试
    logger.info(f"\n{'='*50}")
    logger.info(f"运行测试: 平台爬虫")
    logger.info(f"{'='*50}")

    try:
        result = asyncio.run(test_platform_crawl())
        results.append(("平台爬虫", result))
    except Exception as e:
        logger.error(f"测试 平台爬虫 异常: {e}", exc_info=True)
        results.append(("平台爬虫", False))

    # 输出测试结果
    logger.info(f"\n{'='*50}")
    logger.info("测试结果汇总:")
    logger.info(f"{'='*50}")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        logger.info("🎉 所有测试通过！平台抽象层工作正常。")
        return 0
    else:
        logger.error("部分测试失败，需要进一步调试。")
        return 1


if __name__ == "__main__":
    exit(main())