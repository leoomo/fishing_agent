#!/usr/bin/env python3
"""
淘宝店铺分类RPA爬虫

实现从店铺页面开始，点击"路亚竿"分类，滚动加载所有商品，
然后提取第一个商品的详细信息和下载图片。
"""

import time
import random
import logging
import re
from typing import List, Optional
from pathlib import Path

from playwright.sync_api import Page, Locator

from .playwright_spider import PlaywrightSpider
from .login_manager import LoginManager
from .config import RPAConfig
from ..base_spider import EquipmentData
import requests
import os

logger = logging.getLogger(__name__)


class TaobaoShopCategoryRPA(PlaywrightSpider):
    """淘宝店铺分类RPA爬虫"""

    def __init__(self, config: Optional[RPAConfig] = None):
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

        # 保存 RPA 配置
        self.config = config

        # 店铺配置
        self.shop_url = "https://shop437350870.taobao.com"
        self.category_name = "路亚竿"

        # 初始化组件
        self.login_manager = LoginManager(config)
        self.image_save_dir = Path("shared/images")

        logger.info("TaobaoShopCategoryRPA初始化完成")

    def crawl_shop_category(self) -> List[EquipmentData]:
        """
        爬取店铺分类商品的主要入口方法

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

                # 2. 进入店铺页面
                if not self._enter_shop_page(page):
                    logger.error("进入店铺页面失败，终止流程")
                    return products

                # 3. 点击路亚竿分类
                if not self._click_lure_rod_category(page):
                    logger.error("点击路亚竿分类失败，终止流程")
                    return products

                # 4. 等待分类页面加载完成
                if not self._wait_for_category_loaded(page):
                    logger.error("分类页面加载超时，终止流程")
                    return products

                # 5. 竖向滚动加载所有商品（测试期间暂时注释）
                # self._scroll_to_load_all_products(page)

                # 6. 点击第一个商品并提取详细信息
                product = self._click_first_product_and_extract(page)
                if product:
                    products.append(product)
                    logger.info(f"成功提取商品信息: {product.name}")
                else:
                    logger.warning("未能提取到商品信息")

                return products

        except Exception as e:
            logger.error(f"爬取过程中发生错误: {e}", exc_info=True)
            return products

    def _enter_shop_page(self, page: Page) -> bool:
        """
        进入店铺页面

        Returns:
            是否成功进入店铺页面
        """
        logger.info(f"正在进入店铺页面: {self.shop_url}")

        try:
            # 导航到店铺页面
            if not self.safe_goto(page, self.shop_url):
                logger.error(f"无法进入店铺页面: {self.shop_url}")
                return False

            # 等待页面加载
            time.sleep(3)

            # 检查是否成功进入店铺
            if "taobao.com" not in page.url:
                logger.error("页面跳转失败，未进入淘宝店铺")
                return False

            logger.info("✅ 成功进入店铺页面")
            return True

        except Exception as e:
            logger.error(f"进入店铺页面时发生错误: {e}", exc_info=True)
            return False

    def _click_lure_rod_category(self, page: Page) -> bool:
        """
        点击路亚竿分类

        Returns:
            是否成功点击路亚竿分类
        """
        logger.info("开始点击'路亚竿'分类...")

        # 路亚竿分类选择器（基于店铺页面结构）
        category_selectors = [
            "a:has-text('路亚竿')",
            "span:has-text('路亚竿')",
            "div:has-text('路亚竿')",
            ".shop-category a:has-text('路亚竿')",
            ".cat-tree a:has-text('路亚竿')",
            ".side-cate a:has-text('路亚竿')",
            ".category-list a:has-text('路亚竿')",
            ".nav a:has-text('路亚竿')",
            ".menu a:has-text('路亚竿')",
            "[data-category='路亚竿']",
            "*:has-text('路亚竿'):has(a)",
        ]

        for selector in category_selectors:
            try:
                elements = page.locator(selector).all()
                for elem in elements:
                    if elem.is_visible(timeout=2000):
                        elem.click()
                        logger.info(f"✅ 成功点击路亚竿分类: {selector}")
                        time.sleep(3)
                        return True
            except Exception as e:
                logger.debug(f"尝试选择器失败 ({selector}): {e}", exc_info=True)
                continue

        logger.error("❌ 未找到'路亚竿'分类")
        return False

    def _wait_for_category_loaded(self, page: Page) -> bool:
        """
        等待分类页面加载完成

        Returns:
            是否成功加载完成
        """
        logger.info("等待分类页面加载完成...")

        max_wait_time = 30
        wait_interval = 2
        elapsed_time = 0

        # 等待商品元素出现
        product_selectors = [
            "[data-spm='product_shelf']",
            "[data-spm-anchor-id*='product_shelf']",
            ".item",
            ".product",
            ".goods",
        ]

        while elapsed_time < max_wait_time:
            try:
                for selector in product_selectors:
                    elements = page.locator(selector).all()
                    if elements and len(elements) > 0:
                        logger.info(f"✅ 分类页面加载完成，检测到 {len(elements)} 个商品元素")
                        return True

                time.sleep(wait_interval)
                elapsed_time += wait_interval
                logger.debug(f"等待分类加载... ({elapsed_time}s)")

            except Exception as e:
                logger.debug(f"检查分类加载状态时发生错误: {e}", exc_info=True)
                time.sleep(wait_interval)
                elapsed_time += wait_interval

        logger.warning("分类页面加载超时，但继续执行")
        return True

    def _scroll_to_load_all_products(self, page: Page) -> bool:
        """
        竖向滚动页面，让所有商品条目加载完成
        使用渐进式滚动，模拟人类浏览行为

        Returns:
            是否成功加载所有商品
        """
        logger.info("开始竖向滚动加载所有商品...")

        # 使用配置参数
        max_scrolls = self.config.scroll_max_attempts
        scroll_count = 0
        last_height = 0
        no_change_count = 0
        scroll_completion_threshold = self.config.scroll_completion_threshold

        # 获取初始页面高度
        try:
            last_height = page.evaluate("document.body.scrollHeight")
            logger.debug(f"初始页面高度: {last_height}")
        except Exception as e:
            logger.warning(f"获取初始页面高度失败: {e}", exc_info=True)
            return False

        while scroll_count < max_scrolls:
            try:
                # 渐进式滚动：每次滚动一小段距离，而不是直接到底部
                viewport_height = page.evaluate("window.innerHeight")
                current_scroll_position = page.evaluate("window.pageYOffset")

                # 计算下一步滚动位置（使用配置的滚动步长范围）
                scroll_step = random.uniform(self.config.scroll_step_min, self.config.scroll_step_max) * viewport_height
                next_scroll_position = current_scroll_position + scroll_step

                # 执行平滑滚动
                page.evaluate(f"""
                window.scrollTo({{
                    top: {next_scroll_position},
                    behavior: 'smooth'
                }});
                """)

                # 等待滚动完成和内容加载
                wait_time = random.uniform(self.config.scroll_wait_min, self.config.scroll_wait_max)
                logger.debug(f"等待 {wait_time:.1f}s 让内容加载...")
                time.sleep(wait_time)

                # 检查是否到达页面底部
                at_bottom = page.evaluate("""
                () => {
                    const scrollTop = window.pageYOffset;
                    const windowHeight = window.innerHeight;
                    const documentHeight = document.documentElement.scrollHeight;
                    return scrollTop + windowHeight >= documentHeight - 100; // 100px容差
                }
                """)

                if at_bottom:
                    logger.debug("已到达页面底部")

                    # 到达底部后，继续检测是否有新内容加载
                    new_height = page.evaluate("document.body.scrollHeight")

                    if new_height == last_height:
                        no_change_count += 1
                        logger.debug(f"到底部后页面高度未变化，无变化计数: {no_change_count}")

                        if no_change_count >= scroll_completion_threshold:
                            logger.info("✅ 检测到页面内容加载完成")
                            break
                    else:
                        no_change_count = 0
                        last_height = new_height
                        logger.debug(f"到底部后页面高度增加: {new_height}")
                else:
                    # 检查页面高度变化
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height > last_height:
                        no_change_count = 0
                        last_height = new_height
                        logger.debug(f"页面高度更新: {last_height}")

                scroll_count += 1
                logger.debug(f"滚动进度: {scroll_count}/{max_scrolls}")

                # 如果连续多次滚动都没有变化，可能是真的完成了
                if scroll_count > 10 and no_change_count > 3:
                    logger.info("✅ 检测到页面滚动趋于稳定，可能已加载完成")
                    break

            except Exception as e:
                logger.warning(f"滚动操作失败 (第{scroll_count}次): {e}", exc_info=True)
                scroll_count += 1
                if scroll_count >= max_scrolls:
                    logger.error("滚动操作失败，已达最大重试次数")
                    break

            # 每10次滚动检查一次，避免无限滚动
            if scroll_count % 10 == 0:
                logger.info(f"已滚动 {scroll_count} 次，当前进度检查...")

        logger.info(f"滚动完成，总滚动次数: {scroll_count}")
        return True

    def _click_first_product_and_extract(self, page: Page) -> Optional[EquipmentData]:
        """
        点击第一个商品并提取详细信息

        Returns:
            商品详细信息，如果失败则返回None
        """
        logger.info("开始处理第一个商品...")

        # 使用XPath定位商品元素
        selector = "//div//div[@data-spm='product_shelf']/div[contains(@class, 'container--')]/div[contains(@class,'cardContainer--')]"

        try:
            elements = page.locator(f"xpath={selector}").all()
            if not elements:
                logger.warning("未找到商品元素")
                return None

            logger.info(f"找到 {len(elements)} 个商品元素，处理第一个")

            # 点击第一个商品并在新标签页中打开
            return self._open_product_and_extract(page, elements[0])

        except Exception as e:
            logger.error(f"处理商品失败: {e}", exc_info=True)
            return None

    def _open_product_and_extract(self, page: Page, product_element: Locator) -> Optional[EquipmentData]:
        """
        打开商品详情页并提取信息

        Args:
            page: 当前页面对象
            product_element: 商品元素定位器

        Returns:
            商品详细信息，如果失败则返回None
        """
        new_page = None
        try:
            # 监听新页面打开
            with page.expect_popup() as popup_info:
                product_element.click()

            # 获取新打开的页面
            new_page = popup_info.value
            logger.info("新标签页已打开，等待页面加载...")
            new_page.wait_for_load_state('domcontentloaded', timeout=10000)
            time.sleep(3)

            # 提取商品ID
            product_id = self._extract_product_id_from_url(new_page.url)
            if not product_id:
                logger.warning("无法提取商品ID")
                return None

            logger.info(f"商品ID: {product_id}")

            # 提取商品详细信息
            product_data = self._extract_product_details(new_page, product_id)
            if not product_data:
                logger.warning("商品详情提取失败")
                return None

            # 设置商品ID
            product_data.id = product_id

            # 竖向滚动商品详情页，确保所有图片加载完成
            logger.info("滚动商品详情页以加载所有图片...")
            self._scroll_to_load_all_products(new_page)

            # 滚动后重新提取图片列表，获取懒加载的图片
            logger.info("重新提取图片列表...")
            updated_images = self._extract_product_images(new_page)
            if updated_images:
                # 转换为字典格式
                image_list = [{"url": img_url, "type": "detail"} for img_url in updated_images]
                product_data.images = image_list
                logger.info(f"更新后的图片数量: {len(updated_images)}")

            # 下载商品图片
            downloaded_count = self._download_product_images(product_data, product_id)
            logger.info(f"下载了 {downloaded_count} 张图片")
            return product_data

        except Exception as e:
            logger.error(f"打开商品详情页失败: {e}", exc_info=True)
            return None
        finally:
            # 确保关闭新页面
            if new_page:
                try:
                    new_page.close()
                except Exception as e:
                    logger.warning(f"关闭新页面时出错: {e}", exc_info=True)

    def _get_product_url_from_element(self, element: Locator, page: Page) -> Optional[str]:
        """
        从商品元素中提取URL

        Args:
            element: 商品元素
            page: 页面对象

        Returns:
            商品URL，如果提取失败则返回None
        """
        try:
            # 策略1：检查元素是否直接包含链接
            href = element.get_attribute("href")
            if href and self._is_valid_product_url(href):
                return href

            # 策略2：查找最近的父链接
            parent_link = element.evaluate("el => el.closest('a')?.href")
            if parent_link and self._is_valid_product_url(parent_link):
                return parent_link

            # 策略3：检查子元素是否有链接
            child_link = element.evaluate("el => el.querySelector('a')?.href")
            if child_link and self._is_valid_product_url(child_link):
                return child_link

            # 策略4：通过 data-spm-anchor-id 查找相关链接
            data_spm_anchor_id = element.get_attribute("data-spm-anchor-id")
            if data_spm_anchor_id:
                # 查找具有相同 data-spm-anchor-id 的链接
                link_selector = f"[data-spm-anchor-id='{data_spm_anchor_id}'][href]"
                links = page.locator(link_selector).all()
                for link in links:
                    href = link.get_attribute("href")
                    if href and self._is_valid_product_url(href):
                        return href

            logger.debug("无法从商品元素中提取有效的URL")
            return None

        except Exception as e:
            logger.error(f"提取商品URL时发生错误: {e}", exc_info=True)
            return None

    def _is_valid_product_url(self, url: str) -> bool:
        """
        检查URL是否为有效的商品URL

        Args:
            url: 待检查的URL

        Returns:
            是否为有效商品URL
        """
        if not url:
            return False

        valid_patterns = [
            "item.taobao.com/item.htm",
            "detail.tmall.com/item.htm",
            "click.simba.taobao.com",
            "s.click.taobao.com",
        ]

        return any(pattern in url for pattern in valid_patterns)

    def _extract_product_id_from_url(self, url: str) -> Optional[str]:
        """
        从URL中提取商品ID

        Args:
            url: 商品详情页URL

        Returns:
            商品ID，如果提取失败则返回None
        """
        try:
            # 从URL中提取id参数: item.taobao.com/item.htm?id=123456789
            patterns = [
                r'id=(\d+)',  # 标准模式
                r'item\.htm\?id=(\d+)',  # 淘宝商品详情页
                r'detail\.tmall\.com/item\.htm\?id=(\d+)',  # 天猫详情页
            ]

            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

            return None

        except Exception as e:
            logger.error(f"从URL提取商品ID失败: {e}", exc_info=True)
            return None

    def _extract_product_details(self, page: Page, product_id: str) -> Optional[EquipmentData]:
        """
        提取商品详细信息

        Args:
            page: 详情页面对象
            product_id: 商品ID

        Returns:
            商品详细信息，如果提取失败则返回None
        """
        try:
            logger.info("开始提取商品详细信息...")

            # 等待页面加载
            time.sleep(2)

            # 提取商品基本信息
            name = self._extract_product_name(page)
            price = self._extract_product_price(page)
            brand = self._extract_product_brand(page)
            description = self._extract_product_description(page)
            images = self._extract_product_images(page)
            specs = self._extract_product_specs(page)

            # 如果没有提取到商品名称，尝试从页面标题获取
            if not name:
                title = page.title()
                if title:
                    # 移除淘宝相关的后缀
                    name = title.split('-淘宝')[0].split('-tmall.com')[0].strip()
                    logger.info(f"从页面标题获取商品名称: {name}")

            if not name:
                logger.warning("无法提取商品名称")
                return None

            # 记录提取结果
            logger.info(f"商品名称: {name}")
            logger.info(f"商品价格: {price or '未提取到'}")
            logger.info(f"商品品牌: {brand or '未提取到'}")
            logger.info(f"图片数量: {len(images)}")
            logger.info(f"规格参数数量: {len(specs or {})}")

            # 解析价格
            price_min = 0.0
            if price:
                try:
                    # 提取数字部分
                    price_match = re.search(r'[\d.]+', str(price))
                    if price_match:
                        price_min = float(price_match.group())
                except (ValueError, AttributeError) as e:
                    logger.warning(f"价格解析失败: {price}, 错误: {e}", exc_info=True)

            # 转换图片格式为字典列表
            image_list = [{"url": img_url, "type": "detail"} for img_url in (images or [])]

            # 创建商品数据对象
            product_data = EquipmentData(
                name=name,
                category="鱼竿",  # 路亚竿属于鱼竿类别
                brand_name=brand or "未知品牌",
                price_min=price_min,
                source_url=page.url,
                description=description,
                images=image_list,
                specs=specs or {},
            )

            logger.info(f"商品信息提取完成: {name}")
            return product_data

        except Exception as e:
            logger.error(f"提取商品详细信息时发生错误: {e}", exc_info=True)
            return None

    def _extract_product_name(self, page: Page) -> Optional[str]:
        """提取商品名称"""
        try:
            # 使用 XPath 提取 title 属性
            element = page.locator("xpath=//div[@id='tbpcDetail_SkuPanelBody']//span[contains(@class, 'mainTitle--')]").first
            name = element.get_attribute("title", timeout=5000)
            if name and len(name) > 5:
                logger.info(f"提取到商品名称: {name}")
                return name
        except Exception as e:
            logger.error(f"提取商品名称失败: {e}", exc_info=True)

        return None

    def _extract_product_price(self, page: Page) -> Optional[str]:
        """提取商品价格"""
        # TODO: 实现价格提取逻辑
        _ = page  # 未来会使用
        return None

    def _extract_product_brand(self, page: Page) -> Optional[str]:
        """提取商品品牌"""
        selectors = [
            "[data-spm='brand']",
            ".brand",
            "[class*='brand']",
            ".tb-property",
        ]

        for selector in selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    brand = element.text_content().strip()
                    if brand and len(brand) < 20:  # 品牌名通常不会太长
                        return brand
            except Exception as e:
                logger.debug(f"提取品牌失败 ({selector}): {e}", exc_info=True)
                continue

        return None

    def _extract_product_description(self, page: Page) -> Optional[str]:
        """提取商品描述"""
        selectors = [
            "[data-spm='description']",
            ".tb-description",
            ".description",
            "[class*='desc']",
            ".detail-desc",
        ]

        for selector in selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    desc = element.text_content().strip()
                    if desc and len(desc) > 10:
                        return desc[:500]  # 限制描述长度
            except Exception as e:
                logger.debug(f"提取描述失败 ({selector}): {e}", exc_info=True)
                continue

        return None

    def _extract_product_images(self, page: Page) -> List[str]:
        """提取商品图片URL"""
        images = []

        try:
            # 查找所有图片元素
            img_selectors = [
                "#J_ImgBooth img",
                ".tb-gallery img",
                ".gallery img",
                "[class*='image'] img",
                "[class*='photo'] img",
                "[class*='pic'] img",
                "img[src*='jpg']",
                "img[src*='jpeg']",
                "img[src*='png']",
                "img[data-src]",
            ]

            for selector in img_selectors:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        # 优先获取 data-src
                        src = element.get_attribute("data-src") or element.get_attribute("src")
                        if src and src.startswith(("http", "//")):
                            # 处理相对路径
                            if src.startswith("//"):
                                src = "https:" + src

                            # 过滤掉小图标和无用图片
                            if any(x in src for x in ['60x60', '40x40', 'logo', 'icon', 'avatar']):
                                continue

                            # 优先选择淘宝的图片
                            if ("alicdn.com" in src or "taobao.com" in src or "tmall.com" in src):
                                if src not in images:
                                    images.append(src)

                            # 限制图片数量
                            if len(images) >= 10:
                                break
                except Exception as e:
                    logger.debug(f"提取图片失败 ({selector}): {e}", exc_info=True)
                    continue

                if len(images) >= 10:
                    break

            # 如果没有找到图片，尝试通用方法
            if not images:
                all_imgs = page.locator("img").all()
                for img in all_imgs:
                    src = img.get_attribute("src") or img.get_attribute("data-src")
                    if src and ("alicdn.com" in src or "taobao.com" in src):
                        # 选择较大的图片
                        if any(size in src for size in ['400x400', '500x500', '600x600', '800x800']):
                            images.append(src)
                            if len(images) >= 5:
                                break

            logger.info(f"提取到 {len(images)} 张商品图片")

        except Exception as e:
            logger.error(f"提取商品图片时发生错误: {e}", exc_info=True)

        return images

    def _extract_product_specs(self, page: Page) -> Optional[dict]:
        """提取商品规格参数"""
        specs = {}

        try:
            # 查找规格参数表格
            spec_selectors = [
                "#J_AttrUL",
                ".tb-props",
                ".props",
                "[class*='spec']",
                "[class*='param']",
                "[class*='attr']",
                ".attributes",
                ".attributes-list",
            ]

            for selector in spec_selectors:
                try:
                    container = page.locator(selector).first
                    if container.is_visible(timeout=2000):
                        # 提取键值对形式的规格参数
                        rows = container.locator("li, tr, .item, dt, dd").all()
                        for row in rows:
                            try:
                                text = row.text_content().strip()
                                if '：' in text or ':' in text:
                                    if '：' in text:
                                        key, value = text.split('：', 1)
                                    else:
                                        key, value = text.split(':', 1)

                                    key = key.strip()
                                    value = value.strip()

                                    if key and value and len(key) < 30 and len(value) < 200:
                                        specs[key] = value
                            except Exception as e:
                                logger.debug(f"解析规格参数失败: {e}", exc_info=True)
                                continue

                        if specs:
                            logger.info(f"使用选择器 {selector} 提取到 {len(specs)} 个规格参数")
                            break
                except Exception as e:
                    logger.debug(f"提取规格参数失败 ({selector}): {e}", exc_info=True)
                    continue

            logger.info(f"提取到 {len(specs)} 个规格参数")

        except Exception as e:
            logger.error(f"提取商品规格参数时发生错误: {e}", exc_info=True)

        return specs if specs else None

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

    def search_equipment(
        self,
        keyword: str,
        category: str = "通用",
        max_results: int = 20,
    ) -> List[EquipmentData]:
        """
        搜索装备（店铺分类模式）

        注意：此方法为了兼容 BaseSpider 接口，实际使用店铺分类逻辑

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

                # 确保已登录
                if not self.login_manager.ensure_logged_in(page, context):
                    logger.error("❌ 登录失败")
                    return None

                # 访问详情页
                if not self.safe_goto(page, product_url):
                    logger.error("❌ 访问详情页失败")
                    return None

                # 等待页面加载
                time.sleep(3)

                # 提取商品ID
                product_id = self._extract_product_id_from_url(page.url)

                # 提取商品详细信息
                product_data = self._extract_product_details(page, product_id or "unknown")

                if product_data:
                    # 设置商品ID
                    product_data.id = product_id or "unknown"
                    logger.info(f"✅ 提取商品详情: {product_data.name}")
                    return product_data

                return None

        except Exception as e:
            logger.error(f"获取商品详情失败: {e}", exc_info=True)
            return None

    def _find_product_elements(self, page: Page) -> List:
        """
        查找商品元素，支持多种选择器策略

        Args:
            page: Page对象

        Returns:
            找到的商品元素列表
        """
        # 商品选择器配置
        product_selectors = [
            # 你提供的具体XPath（优先级最高）
            "//div//div[@data-spm='product_shelf']/div[contains(@class, 'container--')]/div[contains(@class,'cardContainer--')]",
            # CSS选择器版本
            "div[data-spm='product_shelf'] div[class*='container--'] div[class*='cardContainer--']",
            # 备用选择器
            "[data-spm-anchor-id*='product_shelf']",
            ".title--GExDBPUi[data-spm-anchor-id*='product_shelf']",
            "[data-spm='product_shelf']",
            "[class*='product_shelf']",
            ".item",
            ".Card--doubleCard",
        ]

        elements = []
        used_selector = None
        selector_type = None

        for selector in product_selectors:
            try:
                # 区分CSS选择器和XPath
                if selector.startswith("//"):
                    # XPath选择器
                    found_elements = page.locator(f"xpath={selector}").all()
                    current_type = "XPath"
                else:
                    # CSS选择器
                    found_elements = page.locator(selector).all()
                    current_type = "CSS"

                if found_elements:
                    elements = found_elements
                    used_selector = selector
                    selector_type = current_type
                    logger.info(f"使用 {selector_type} 选择器 '{selector}' 找到 {len(elements)} 个商品元素")
                    break
                else:
                    logger.debug(f"选择器 '{selector}' 未找到商品元素")

            except Exception as e:
                logger.debug(f"使用选择器 '{selector}' 失败: {e}", exc_info=True)
                continue

        if not elements:
            logger.warning("所有选择器都未找到商品元素")

        return elements, used_selector, selector_type

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