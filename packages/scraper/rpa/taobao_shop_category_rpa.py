#!/usr/bin/env python3
"""
淘宝店铺分类RPA爬虫（重构版）

从店铺页面点击分类，滚动加载商品，提取第一个商品的详细信息并下载图片。
使用页面对象模式和配置驱动的提取器，代码量减少50%。
"""

import logging
import requests
import re
from typing import List, Optional
from pathlib import Path

from .playwright_spider import PlaywrightSpider
from .login_manager import LoginManager
from .config import RPAConfig
from packages.scraper.spider.base import CrawlItem as EquipmentData

# 导入新的模块化组件
from .pages.taobao_shop_category_page import TaobaoShopCategoryPage
from .extractors.taobao_product_extractor import TaobaoProductExtractor

logger = logging.getLogger(__name__)


class TaobaoShopCategoryRPA(PlaywrightSpider):
    """淘宝店铺分类RPA爬虫（重构版 v2.0）"""

    def __init__(self, config: Optional[RPAConfig] = None):
        """
        初始化爬虫

        Args:
            config: RPA配置，如果为None则从环境变量加载
        """
        # 确保配置存在
        if config is None:
            config = RPAConfig.from_env()

        # 将 RPAConfig 转换为 BaseSpider 期望的字典格式
        base_config = {
            "request_delay": config.request_delay,
            "max_retries": config.max_retries,
            "timeout": config.page_timeout,
        }
        super().__init__(base_config)

        # 保存配置
        self.config = config

        # 店铺配置
        self.shop_url = "https://shop437350870.taobao.com"
        self.category_name = "路亚竿"

        # 初始化组件
        self.login_manager = LoginManager(config)
        self.image_save_dir = Path("shared/images")

        logger.info("TaobaoShopCategoryRPA v2.0 初始化完成")

    def crawl(self, **kwargs) -> List[EquipmentData]:
        """
        实现抽象方法 - 默认调用 crawl_shop_category

        Returns:
            商品数据列表
        """
        return self.crawl_shop_category()

    def search_equipment(
        self, keyword: str, category: Optional[str] = None, max_results: int = 50
    ) -> List[EquipmentData]:
        """
        实现抽象方法 - 店铺分类爬虫不支持关键词搜索

        Returns:
            空列表
        """
        logger.warning("TaobaoShopCategoryRPA 不支持关键词搜索功能")
        return []

    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        实现抽象方法 - 店铺分类爬虫不支持单独商品详情获取

        Returns:
            None
        """
        logger.warning("TaobaoShopCategoryRPA 不支持单独商品详情获取")
        return None

    def crawl_shop_category(self) -> List[EquipmentData]:
        """
        爬取店铺分类商品的主要入口方法

        流程编排：
        1. 登录
        2. 导航到店铺
        3. 点击分类
        4. 等待加载
        5. 滚动加载所有商品
        6. 打开第一个商品详情
        7. 提取商品信息
        8. 下载商品图片

        Returns:
            商品数据列表
        """
        products = []

        try:
            with self as spider:
                page = spider.page
                context = spider.context

                # 1. 登录（如果需要）
                if not self.login_manager.ensure_logged_in(page, context):
                    logger.error("登录失败，终止流程")
                    return products

                # 2. 创建页面对象
                category_page = TaobaoShopCategoryPage(page, self.config)

                # 3. 导航到店铺
                if not category_page.navigate_to_shop(self.shop_url):
                    logger.error("进入店铺页面失败，终止流程")
                    return products

                # 4. 点击分类
                if not category_page.click_category(self.category_name):
                    logger.error("点击分类失败，终止流程")
                    return products

                # 5. 等待分类页面加载完成
                if not category_page.wait_for_category_loaded():
                    logger.error("分类页面加载超时，终止流程")
                    return products

                # 6. 滚动加载所有商品（可选，根据需求启用）
                # category_page.scroll_to_load_products()

                # 7. 打开第一个商品详情页
                product_page = category_page.open_first_product_detail()
                if not product_page:
                    logger.error("打开商品详情页失败，终止流程")
                    return products

                # 8. 提取商品ID
                product_id = category_page.extract_product_id_from_url(product_page.url)
                if not product_id:
                    logger.warning("无法提取商品ID，使用默认值")
                    product_id = "unknown"

                logger.info(f"商品ID: {product_id}")

                # 9. 提取商品信息（使用新的提取器）
                extractor = TaobaoProductExtractor(product_page)
                product_data = extractor.extract_all(product_id, product_page.url)

                if not product_data:
                    logger.warning("商品详情提取失败")
                    product_page.close()
                    return products

                # 10. 滚动商品详情页，加载懒加载图片（可选）
                logger.info("滚动商品详情页以加载所有图片...")
                from .utils.scroll_helper import scroll_to_load_all
                scroll_to_load_all(product_page, self.config, logger)

                # 11. 重新提取图片列表（获取懒加载的图片）
                logger.info("重新提取图片列表...")
                extractor_recheck = TaobaoProductExtractor(product_page)
                updated_images = extractor_recheck._extract_field('images', extractor_recheck.FIELD_CONFIGS['images'])

                if updated_images:
                    product_data.images = [{"url": img_url, "type": "detail"} for img_url in updated_images]
                    logger.info(f"更新后的图片数量: {len(updated_images)}")

                # 12. 下载商品图片
                if product_data.images:
                    logger.info("开始下载商品图片...")
                    downloaded_count = self._download_product_images(product_data, product_id)
                    logger.info(f"下载了 {downloaded_count} 张图片")

                # 13. 添加到结果列表
                products.append(product_data)
                logger.info(f"✅ 成功提取商品信息: {product_data.name}")

                # 14. 关闭详情页
                product_page.close()

                return products

        except Exception as e:
            logger.error(f"爬取过程中发生错误: {e}", exc_info=True)
            return products

    def search_equipment(
        self,
        keyword: str,
        category: str = "通用",
        max_results: int = 20,
    ) -> List[EquipmentData]:
        """
        搜索装备（店铺分类模式）

        注意：此方法为了兼容 BaseSpider 接口，实际使用店铺分类逻辑。

        Args:
            keyword: 搜索关键词（在店铺分类模式下会被忽略）
            category: 装备类型
            max_results: 最大结果数

        Returns:
            装备数据列表
        """
        logger.info(f"店铺分类模式搜索: keyword={keyword}, category={category}, max_results={max_results}")

        # 实际执行店铺分类爬取
        return self.crawl_shop_category()

    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        获取商品详情（店铺分类模式）

        Args:
            product_url: 商品详情页URL

        Returns:
            装备数据或None
        """
        logger.info(f"获取商品详情: {product_url}")

        try:
            with self as spider:
                page = spider.page
                context = spider.context

                # 1. 确保已登录
                if not self.login_manager.ensure_logged_in(page, context):
                    logger.error("❌ 登录失败")
                    return None

                # 2. 访问详情页
                if not self.safe_goto(page, product_url):
                    logger.error("❌ 访问详情页失败")
                    return None

                # 3. 等待页面加载
                import time
                time.sleep(3)

                # 4. 提取商品ID
                from .pages.taobao_shop_category_page import TaobaoShopCategoryPage
                category_page = TaobaoShopCategoryPage(page, self.config)
                product_id = category_page.extract_product_id_from_url(page.url)

                # 5. 提取商品详细信息
                extractor = TaobaoProductExtractor(page)
                product_data = extractor.extract_all(product_id or "unknown", page.url)

                if product_data:
                    logger.info(f"✅ 提取商品详情: {product_data.name}")
                    return product_data

                return None

        except Exception as e:
            logger.error(f"获取商品详情失败: {e}", exc_info=True)
            return None

    def _download_product_images(self, product: EquipmentData, product_id: str) -> int:
        """
        下载商品所有图片到shared/images目录

        Args:
            product: 商品数据
            product_id: 商品ID

        Returns:
            下载的图片数量
        """
        downloaded_count = 0

        try:
            # 创建商品图片保存目录
            save_dir = self.image_save_dir / product_id
            save_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"开始下载商品图片，保存目录: {save_dir}")

            # 下载所有图片
            if hasattr(product, 'images') and product.images:
                for i, image_item in enumerate(product.images):
                    try:
                        # 从字典中提取URL
                        if isinstance(image_item, dict):
                            image_url = image_item.get('url')
                        else:
                            # 兼容旧格式（字符串列表）
                            image_url = image_item

                        if not image_url:
                            continue

                        # 构建文件名
                        file_ext = self._get_image_extension(image_url)
                        filename = f"image_{i+1}{file_ext}"
                        save_path = save_dir / filename

                        # 下载图片
                        success = self._download_single_image(image_url, str(save_path), product.source_url)

                        if success:
                            downloaded_count += 1
                            logger.debug(f"下载图片成功: {filename}")
                        else:
                            logger.warning(f"下载图片失败: {image_url}")

                    except Exception as e:
                        logger.warning(f"下载第{i+1}张图片失败: {e}", exc_info=True)

            logger.info(f"图片下载完成，成功下载 {downloaded_count} 张图片")

        except Exception as e:
            logger.error(f"下载商品图片失败: {e}", exc_info=True)

        return downloaded_count

    def _download_single_image(self, url: str, save_path: str, referer: str = None) -> bool:
        """
        下载单张图片

        Args:
            url: 图片URL
            save_path: 保存路径
            referer: 引用页面URL

        Returns:
            是否下载成功
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }

            if referer:
                headers['Referer'] = referer

            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL不是图片: {url}, content-type: {content_type}")
                return False

            # 保存图片
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            logger.error(f"下载图片失败: {url}, 错误: {e}", exc_info=True)
            return False

    def _get_image_extension(self, url: str) -> str:
        """从URL推断图片扩展名"""
        url_lower = url.lower()

        if url_lower.endswith('.jpg') or url_lower.endswith('.jpeg'):
            return '.jpg'
        elif url_lower.endswith('.png'):
            return '.png'
        elif url_lower.endswith('.webp'):
            return '.webp'
        elif url_lower.endswith('.gif'):
            return '.gif'
        else:
            return '.jpg'  # 默认扩展名
