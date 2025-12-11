#!/usr/bin/env python3
"""
Example usage of the refactored Taobao RPA crawler

This script demonstrates how to use the improved RPA crawler with proper
error handling, logging, and best practices.
"""

import logging
import sys
from pathlib import Path

# Add the parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from tools.crawler.rpa.improved.taobao_rpa_v2 import TaobaoRPAV2
from tools.crawler.rpa.core.config_validator import RPAConfigV2
from tools.crawler.rpa.core.spider_manager import SpiderManager, BrowserConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rpa_crawler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def example_basic_crawl():
    """Basic example: crawl a shop for products"""
    logger.info("=== Basic Shop Crawling Example ===")

    # Load configuration from environment
    config = RPAConfigV2.from_env()

    # Validate configuration
    errors = config.validate_all()
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return

    # Create crawler instance
    crawler = TaobaoRPAV2(config)

    # Crawl shop products
    shop_url = "https://shop437350870.taobao.com"
    category = "路亚竿"  # Optional: crawl specific category
    max_items = 50

    try:
        result = crawler.crawl_shop_products(
            shop_url=shop_url,
            category=category,
            max_items=max_items
        )

        logger.info(f"Crawling completed!")
        logger.info(f"  Total items: {len(result.items)}")
        logger.info(f"  Total pages: {result.total_pages}")
        logger.info(f"  Screenshots: {len(result.screenshots)}")

        if result.errors:
            logger.warning(f"Errors encountered: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")

        # Display first few items
        logger.info("\nSample items:")
        for i, item in enumerate(result.items[:3]):
            logger.info(f"  {i+1}. {item.name[:50]}... - ¥{item.price}")

    except Exception as e:
        logger.error(f"Crawling failed: {e}", exc_info=True)


def example_product_detail():
    """Example: Get detailed product information"""
    logger.info("\n=== Product Detail Example ===")

    config = RPAConfigV2.from_env()
    crawler = TaobaoRPAV2(config)

    # Example product URL (replace with actual URL)
    product_url = "https://item.taobao.com/item.htm?id=123456789"

    try:
        product = crawler.get_product_detail(product_url)

        if product:
            logger.info("Product details retrieved:")
            logger.info(f"  Name: {product.name}")
            logger.info(f"  Brand: {product.brand}")
            logger.info(f"  Price: ¥{product.price}")
            logger.info(f"  Category: {product.category}")
            logger.info(f"  Images: {len(product.images)}")
            logger.info(f"  Specs: {len(product.specs)} keys")
        else:
            logger.warning("Failed to retrieve product details")

    except Exception as e:
        logger.error(f"Product detail retrieval failed: {e}", exc_info=True)


def example_custom_configuration():
    """Example: Use custom configuration"""
    logger.info("\n=== Custom Configuration Example ===")

    # Create custom configuration
    browser_config = BrowserConfig(
        headless=False,  # Show browser for debugging
        timeout=60000,   # Longer timeout
        enable_stealth=True
    )

    config = RPAConfigV2()
    config.browser = browser_config
    config.crawl.max_items_per_page = 50
    config.anti_detection.random_delays = True

    # Save configuration to file
    config.save_to_file("custom_rpa_config.json")
    logger.info("Custom configuration saved")

    # Load configuration from file
    loaded_config = RPAConfigV2.load_from_file("custom_rpa_config.json")
    logger.info("Configuration loaded from file")

    # Use the configuration
    crawler = TaobaoRPAV2(loaded_config)


def example_monitoring_and_metrics():
    """Example: Monitor crawler performance"""
    logger.info("\n=== Monitoring Example ===")

    config = RPAConfigV2.from_env()
    crawler = TaobaoRPAV2(config)

    # Get initial statistics
    stats = crawler.get_crawl_statistics()
    logger.info(f"Initial stats: {stats}")

    # Perform crawling
    shop_url = "https://shop437350870.taobao.com"
    result = crawler.crawl_shop_products(
        shop_url=shop_url,
        max_items=10
    )

    # Get updated statistics
    stats = crawler.get_crawl_statistics()
    logger.info(f"Updated stats: {stats}")
    logger.info(f"Success rate: {stats.get('success_rate', 0):.2%}")
    logger.info(f"Average duration: {stats.get('average_duration', 0):.2f}s")


def example_error_handling():
    """Example: Robust error handling"""
    logger.info("\n=== Error Handling Example ===")

    config = RPAConfigV2.from_env()
    config.crawl.max_retries = 5  # More retries for reliability
    config.crawl.retry_delay = 3.0

    crawler = TaobaoRPAV2(config)

    # Try crawling with error handling
    try:
        result = crawler.crawl_shop_products(
            shop_url="https://invalid-shop-url.taobao.com",  # Invalid URL
            max_items=10
        )
    except Exception as e:
        logger.error(f"Expected error caught: {e}")

    # Check statistics for error tracking
    stats = crawler.get_crawl_statistics()
    logger.info(f"Operations tracked: {stats.get('total_operations', 0)}")
    logger.info(f"Failed operations: {stats.get('failed_operations', 0)}")


def main():
    """Run all examples"""
    logger.info("Starting RPA Crawler Examples")

    # Note: These examples require valid Taobao login and network access
    # Uncomment the examples you want to run:

    # example_basic_crawl()
    # example_product_detail()
    example_custom_configuration()
    example_monitoring_and_metrics()
    example_error_handling()

    logger.info("\nExamples completed!")


if __name__ == "__main__":
    main()