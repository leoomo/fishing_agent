"""
淘宝平台爬虫实现

基于现有RPA系统的淘宝爬虫封装
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from urllib.parse import urlparse

from .base_platform import BasePlatform, TaskConfig, TaskType, CrawlResult

logger = logging.getLogger(__name__)


class TaobaoPlatform(BasePlatform):
    """淘宝平台爬虫"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.platform_name = "taobao"

        # 动态导入RPA模块（避免循环依赖）
        try:
            from packages.scraper.rpa.taobao_rpa import TaobaoRPA
            self.rpa = TaobaoRPA()
        except ImportError as e:
            logger.warning(f"无法导入TaobaoRPA模块: {e}")
            self.rpa = None

    def get_platform_domains(self) -> List[str]:
        """获取淘宝平台域名"""
        return [
            "taobao.com",
            "www.taobao.com",
            "shop.taobao.com",
            "item.taobao.com",
            "detail.taobao.com",
            "list.taobao.com",
            "search.taobao.com"
        ]

    def detect_platform(self, url: str) -> bool:
        """检测URL是否属于淘宝"""
        try:
            domain = urlparse(url).netloc.lower()
            return any(d in domain for d in self.get_platform_domains())
        except Exception:
            return False

    async def crawl(self,
                   task_config: TaskConfig,
                   on_progress: Optional[Callable[[str, int], None]] = None) -> CrawlResult:
        """
        执行淘宝爬虫任务

        Args:
            task_config: 任务配置
            on_progress: 进度回调函数

        Returns:
            爬虫结果
        """
        if not self.validate_config(task_config):
            raise ValueError("任务配置无效")

        if not self.rpa:
            raise RuntimeError("TaobaoRPA模块未正确初始化")

        items = []
        total_count = 0
        has_more = False
        metadata = {}

        try:
            # 根据任务类型执行不同的爬取逻辑
            if task_config.task_type == TaskType.KEYWORD_SEARCH:
                result = await self._crawl_by_keywords(task_config, on_progress)
            elif task_config.task_type == TaskType.SHOP_CRAWL:
                result = await self._crawl_shop(task_config, on_progress)
            elif task_config.task_type == TaskType.SHOP_ANALYZE:
                result = await self._analyze_shop(task_config, on_progress)
            elif task_config.task_type == TaskType.PRODUCT_DETAIL:
                result = await self._crawl_product_details(task_config, on_progress)
            else:
                raise ValueError(f"不支持的任务类型: {task_config.task_type}")

            items = result.get("items", [])
            total_count = result.get("total_count", len(items))
            has_more = result.get("has_more", False)
            metadata = result.get("metadata", {})

        except Exception as e:
            logger.error(f"淘宝爬虫执行失败: {e}")
            raise

        return CrawlResult(
            items=items,
            total_count=total_count,
            has_more=has_more,
            metadata=metadata
        )

    async def _crawl_by_keywords(self,
                               task_config: TaskConfig,
                               on_progress: Optional[Callable[[str, int], None]] = None) -> Dict[str, Any]:
        """关键词搜索爬取"""
        logger.info(f"开始关键词搜索: {task_config.keywords}")

        all_items = []
        total_pages = len(task_config.keywords or []) * task_config.max_pages
        current_page = 0

        for keyword in task_config.keywords or []:
            logger.info(f"搜索关键词: {keyword}")

            # 调用RPA爬虫
            try:
                # 在新线程中运行同步RPA代码
                loop = asyncio.get_event_loop()
                keyword_items = await loop.run_in_executor(
                    None,
                    self.rpa.crawl_by_keyword,
                    keyword,
                    task_config.max_pages
                )

                # 转换为统一格式
                formatted_items = self._format_items(keyword_items)
                all_items.extend(formatted_items)

                current_page += task_config.max_pages
                progress = int((current_page / total_pages) * 100) if total_pages > 0 else 100
                on_progress(f"完成关键词 '{keyword}' 搜索，获取 {len(formatted_items)} 条数据", progress)

            except Exception as e:
                logger.error(f"关键词 '{keyword}' 搜索失败: {e}")
                continue

        return {
            "items": all_items,
            "total_count": len(all_items),
            "has_more": False,
            "metadata": {
                "keywords": task_config.keywords,
                "pages_per_keyword": task_config.max_pages
            }
        }

    async def _crawl_shop(self,
                         task_config: TaskConfig,
                         on_progress: Optional[Callable[[str, int], None]] = None) -> Dict[str, Any]:
        """店铺爬取"""
        logger.info(f"开始店铺爬取: {task_config.shop_url}")

        try:
            loop = asyncio.get_event_loop()

            # 如果有分类信息，按分类爬取
            if task_config.custom_params and "categories" in task_config.custom_params:
                categories = task_config.custom_params["categories"]
                all_items = []

                for i, category in enumerate(categories):
                    on_progress(f"爬取分类 {category}...", int((i / len(categories)) * 100))

                    category_items = await loop.run_in_executor(
                        None,
                        self.rpa.crawl_shop_category,
                        task_config.shop_url,
                        category,
                        task_config.max_pages
                    )

                    formatted_items = self._format_items(category_items)
                    all_items.extend(formatted_items)

                return {
                    "items": all_items,
                    "total_count": len(all_items),
                    "has_more": False,
                    "metadata": {
                        "shop_url": task_config.shop_url,
                        "categories": categories
                    }
                }
            else:
                # 全店爬取
                items = await loop.run_in_executor(
                    None,
                    self.rpa.crawl_shop_all,
                    task_config.shop_url,
                    task_config.max_pages
                )

                formatted_items = self._format_items(items)
                on_progress("店铺爬取完成", 100)

                return {
                    "items": formatted_items,
                    "total_count": len(formatted_items),
                    "has_more": False,
                    "metadata": {
                        "shop_url": task_config.shop_url
                    }
                }

        except Exception as e:
            logger.error(f"店铺爬取失败: {e}")
            raise

    async def _analyze_shop(self,
                           task_config: TaskConfig,
                           on_progress: Optional[Callable[[str, int], None]] = None) -> Dict[str, Any]:
        """店铺分析"""
        logger.info(f"开始店铺分析: {task_config.shop_url}")

        try:
            loop = asyncio.get_event_loop()

            # 调用店铺分析功能
            analysis = await loop.run_in_executor(
                None,
                self.rpa.analyze_shop,
                task_config.shop_url
            )

            on_progress("店铺分析完成", 100)

            # 将分析结果转换为商品格式
            items = []
            if analysis and "categories" in analysis:
                for category in analysis["categories"]:
                    # 创建一个代表分类的虚拟商品项
                    items.append({
                        "name": category.get("name", ""),
                        "category": "分类",
                        "url": category.get("url", ""),
                        "item_count": category.get("item_count", 0),
                        "analysis_data": category
                    })

            return {
                "items": items,
                "total_count": len(items),
                "has_more": False,
                "metadata": {
                    "shop_url": task_config.shop_url,
                    "analysis_type": "shop_structure"
                }
            }

        except Exception as e:
            logger.error(f"店铺分析失败: {e}")
            raise

    async def _crawl_product_details(self,
                                   task_config: TaskConfig,
                                   on_progress: Optional[Callable[[str, int], None]] = None) -> Dict[str, Any]:
        """商品详情爬取"""
        logger.info(f"开始商品详情爬取，共 {len(task_config.product_urls or [])} 个商品")

        all_items = []
        product_urls = task_config.product_urls or []

        for i, url in enumerate(product_urls):
            try:
                loop = asyncio.get_event_loop()

                details = await loop.run_in_executor(
                    None,
                    self.rpa.get_product_details,
                    url
                )

                if details:
                    # 转换为统一格式
                    item = {
                        "name": details.get("name", ""),
                        "price": details.get("price", 0),
                        "brand": details.get("brand", ""),
                        "model": details.get("model", ""),
                        "description": details.get("description", ""),
                        "images": details.get("images", []),
                        "specs": details.get("specs", {}),
                        "source_url": url,
                        "details_data": details
                    }
                    all_items.append(item)

                progress = int(((i + 1) / len(product_urls)) * 100)
                on_progress(f"完成商品 {i + 1}/{len(product_urls)}", progress)

            except Exception as e:
                logger.error(f"商品详情爬取失败 {url}: {e}")
                continue

        return {
            "items": all_items,
            "total_count": len(all_items),
            "has_more": False,
            "metadata": {
                "product_count": len(product_urls),
                "success_count": len(all_items)
            }
        }

    def _format_items(self, items: List[Any]) -> List[Dict[str, Any]]:
        """
        将RPA返回的商品数据转换为统一格式

        Args:
            items: RPA返回的商品列表

        Returns:
            格式化后的商品列表
        """
        formatted_items = []

        for item in items:
            # 假设RPA返回的是EquipmentData对象或字典
            if hasattr(item, 'to_dict'):
                # EquipmentData对象
                item_dict = item.to_dict()
            elif isinstance(item, dict):
                # 字典格式
                item_dict = item.copy()
            else:
                # 其他格式，尝试转换
                item_dict = {
                    "name": str(getattr(item, 'name', '')),
                    "price": getattr(item, 'price_min', 0),
                    "brand": getattr(item, 'brand_name', ''),
                    "model": getattr(item, 'model', ''),
                    "description": getattr(item, 'description', ''),
                    "source_url": getattr(item, 'source_url', '')
                }

            # 确保必要字段存在
            formatted_item = {
                "name": item_dict.get("name", ""),
                "category": item_dict.get("category", ""),
                "brand": item_dict.get("brand_name", item_dict.get("brand", "")),
                "model": item_dict.get("model", ""),
                "price_min": float(item_dict.get("price_min", item_dict.get("price", 0))),
                "price_max": float(item_dict.get("price_max", item_dict.get("price", 0))),
                "description": item_dict.get("description", ""),
                "features": item_dict.get("features", "{}"),
                "source_url": item_dict.get("source_url", ""),
                "image_urls": item_dict.get("image_urls", []),
                "platform": "taobao",
                "raw_data": item_dict  # 保留原始数据
            }

            formatted_items.append(formatted_item)

        return formatted_items