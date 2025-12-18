"""
淘宝RPA爬虫实现 - 关键词搜索模式
"""

import time
import logging
import re
from typing import List, Optional
from urllib.parse import quote

from playwright.sync_api import Page

from packages.scraper.spider.base import BaseSpider, CrawlItem as EquipmentData
from .playwright_spider import PlaywrightSpider
from .config import RPAConfig
from .login_manager import LoginManager

logger = logging.getLogger(__name__)


class TaobaoRPA(PlaywrightSpider):
    """淘宝RPA爬虫（关键词搜索）"""

    def __init__(self, config: Optional[RPAConfig] = None):
        """
        初始化

        Args:
            config: RPA配置，如果不提供则从环境变量加载
        """
        if config is None:
            config = RPAConfig.from_env()

        # 将 RPAConfig 转换为 BaseSpider 期望的字典格式
        base_config = {
            "request_delay": config.request_delay,
            "max_retries": config.max_retries,
            "timeout": config.page_timeout,
        }
        super().__init__(base_config)

        # 保存 RPA 配置（会被 PlaywrightSpider 再次加载，但这样保持一致性）
        self.config = config
        self.login_manager = LoginManager(config)

        logger.info("初始化 TaobaoRPA（关键词搜索模式）")

    def search_equipment(
        self,
        keyword: str,
        category: str = "通用",
        max_results: int = 20,
    ) -> List[EquipmentData]:
        """
        搜索装备（RPA模式）

        Args:
            keyword: 搜索关键词
            category: 装备类型
            max_results: 最大结果数

        Returns:
            装备数据列表
        """
        logger.info(f"开始RPA搜索: keyword={keyword}, category={category}, max_results={max_results}")

        results = []

        with self as spider:
            page = spider.page
            context = spider.context

            # 1. 确保已登录
            if not self.login_manager.ensure_logged_in(page, context):
                logger.error("❌ 登录失败，无法继续爬取")
                return results

            # 2. 访问店铺地址
            shop_url = "https://shop437350870.taobao.com"
            logger.info(f"📍 正在访问店铺: {shop_url}")

            if not self.safe_goto(page, shop_url):
                logger.error(f"❌ 无法访问店铺页面: {shop_url}")
                return results

            # 等待店铺页面加载
            time.sleep(3)

            # 3. 点击"路亚竿"分类
            if not self._click_lure_rod_category(page):
                logger.error("❌ 点击路亚竿分类失败")
                return results

            # 等待分类页面加载
            time.sleep(3)

            # 4. 等待商品列表加载
            if not self._wait_for_products(page):
                logger.error("❌ 商品列表加载失败")
                return results

            # 5. 提取商品信息
            page_results = self._extract_products(page, keyword, category)
            if page_results:
                results.extend(page_results)
                logger.info(f"📦 成功提取 {len(page_results)} 个商品信息")

            # 6. 翻页处理（如果需要）
            page_count = 1
            while len(results) < max_results and self._has_next_page(page):
                page_count += 1
                logger.info(f"📄 翻到第 {page_count} 页")

                if not self._goto_next_page(page):
                    logger.warning("⚠️ 翻页失败，停止翻页")
                    break

                # 等待新页面加载
                time.sleep(2)

                # 提取当前页商品
                current_page_results = self._extract_products(page, keyword, category)
                if current_page_results:
                    results.extend(current_page_results)
                    logger.info(f"📦 第 {page_count} 页提取到 {len(current_page_results)} 个商品")
                else:
                    logger.warning(f"⚠️ 第 {page_count} 页未提取到商品信息")

                # 避免过度翻页
                if page_count >= 10:
                    logger.warning("⚠️ 已达到最大翻页数限制，停止翻页")
                    break

        logger.info(f"🎉 搜索完成，共获取 {len(results)} 个商品信息")
        return results

    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        获取商品详情（RPA模式 - 完整版）

        Args:
            product_url: 商品详情页URL

        Returns:
            装备数据或None
        """
        logger.info(f"获取商品详情: {product_url}")

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

            # 模拟滚动（触发延迟加载）
            self._simulate_scroll(page)

            # 提取数据
            try:
                # 1. 提取基础信息
                name = self._extract_detail_name(page)
                if not name:
                    logger.warning("未提取到商品名称")
                    return None

                price = self._extract_detail_price(page)

                # 2. 提取规格参数
                specs = self._extract_specs(page)
                logger.debug(f"提取规格: {specs}")

                # 3. 提取品牌（优先规格表，回退到标题）
                brand = specs.get("品牌") or self._extract_brand_from_name(name)

                # 4. 提取图片
                images = self._extract_images(page)
                logger.debug(f"提取图片: {len(images)} 张")

                # 5. 提取描述
                description = self._extract_description(page)

                # 6. 标准化规格参数
                normalized_specs = self._normalize_specs(specs, name)

                # 7. 推断类别
                category = self._infer_category(name, specs)

                # 8. 构建数据
                equipment = EquipmentData(
                    name=name,
                    brand=brand,
                    price=price,
                    url=product_url,
                    category=category,
                    source="taobao_rpa",
                    description=description,
                    images=images,
                    specs=normalized_specs,
                )

                logger.info(f"✅ 提取商品详情: {name} ({brand})")
                return equipment

            except Exception as e:
                logger.error(f"提取详情失败: {e}", exc_info=True)
                return None

    def _click_lure_rod_category(self, page: Page) -> bool:
        """
        点击"路亚竿"分类

        Args:
            page: Page对象

        Returns:
            是否成功点击分类
        """
        logger.info("🔍 开始查找并点击'路亚竿'分类...")

        # 路亚竿分类的选择器策略
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
            # 更精确的选择器
            "a[href*='luya']",
            "a[href*='路亚']",
            ".category-item:has-text('路亚竿')",
            ".shop-cat-item:has-text('路亚竿')",
        ]

        for selector in category_selectors:
            try:
                elements = page.locator(selector).all()
                logger.debug(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")

                for elem in elements:
                    try:
                        # 检查元素是否可见
                        if elem.is_visible(timeout=1000):
                            # 获取元素文本确认是路亚竿
                            text = elem.text_content() or ""
                            if "路亚竿" in text:
                                # 点击元素
                                elem.click()
                                logger.info(f"✅ 成功点击路亚竿分类: {selector}")
                                time.sleep(2)
                                return True
                    except Exception as e:
                        logger.debug(f"点击元素失败: {e}")
                        continue

            except Exception as e:
                logger.debug(f"使用选择器 {selector} 失败: {e}")
                continue

        # 如果直接点击失败，尝试通过JavaScript查找
        logger.warning("⚠️ 直接查找失败，尝试JavaScript查找...")
        try:
            js_code = """
            // 查找包含"路亚竿"文本的所有可点击元素
            const elements = document.querySelectorAll('a, span, div, li, button');
            for (let elem of elements) {
                const text = elem.textContent || '';
                if (text.includes('路亚竿') && elem.offsetParent !== null) {
                    // 尝试点击或找到父链接
                    const link = elem.closest('a') || elem.querySelector('a');
                    if (link) {
                        link.click();
                        return true;
                    } else if (elem.click) {
                        elem.click();
                        return true;
                    }
                }
            }
            return false;
            """

            result = page.evaluate(js_code)
            if result:
                logger.info("✅ JavaScript成功点击路亚竿分类")
                time.sleep(2)
                return True

        except Exception as e:
            logger.error(f"JavaScript点击失败: {e}")

        logger.error("❌ 未找到或无法点击'路亚竿'分类")
        return False

    # ==================== 内部方法 ====================

    def _wait_for_products(self, page: Page) -> bool:
        """
        等待商品列表加载

        Args:
            page: Page对象

        Returns:
            是否成功
        """
        # 多种选择器兼容
        selectors = [
            ".item",  # 旧版
            ".Card--doubleCard",  # 新版
            ".m-itemlist .items .item",  # 另一种旧版
            "[class*='Item--item']",  # 模糊匹配
        ]

        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=10000)
                logger.debug(f"商品列表加载成功: {selector}")
                return True
            except:
                continue

        logger.error("商品列表加载超时")
        return False

    def _extract_products(
        self, page: Page, keyword: str, category: str
    ) -> List[EquipmentData]:
        """
        提取当前页商品列表（新版本：点击进入详情页获取完整信息）

        Args:
            page: Page对象
            keyword: 搜索关键词
            category: 装备类型

        Returns:
            装备列表
        """
        results = []

        # 使用 data-spm-anchor-id 属性来识别商品元素
        item_selectors = [
            "[data-spm-anchor-id*='product_shelf']",  # 基于 data-spm-anchor-id
            ".title--GExDBPUi[data-spm-anchor-id*='product_shelf']",  # 你提供的HTML结构
            # 备用选择器
            "[class*='product_shelf']",
            ".item",
            ".Card--doubleCard",
            ".m-itemlist .items .item",
            "[class*='Item--item']",
        ]

        items = []
        for selector in item_selectors:
            try:
                items = page.locator(selector).all()
                if items:
                    logger.info(f"使用选择器: {selector}，找到 {len(items)} 个商品元素")
                    break
            except Exception as e:
                logger.debug(f"使用选择器 {selector} 失败: {e}")
                continue

        if not items:
            logger.warning("未找到商品列表")
            return results

        logger.info(f"开始逐个点击商品进入详情页面提取信息，共 {len(items)} 个商品")

        # 保存当前页面URL
        current_url = page.url

        # 逐个点击商品进入详情页面
        for idx, item in enumerate(items):
            try:
                if idx >= 30:  # 限制处理数量，避免过度操作
                    logger.warning("已达到最大处理数量限制，停止处理更多商品")
                    break

                logger.info(f"处理第 {idx+1} 个商品...")

                # 尝试获取商品URL并进入详情页面
                product_url = self._get_product_url_from_element(item, page)

                if product_url:
                    # 保存当前页面状态
                    try:
                        # 进入商品详情页面
                        if not self.safe_goto(page, product_url):
                            logger.warning(f"无法进入商品详情页面: {product_url}")
                            continue

                        # 等待页面加载
                        time.sleep(3)

                        # 提取商品详细信息
                        product_data = self._extract_product_detail_from_page(page, category)

                        if product_data:
                            results.append(product_data)
                            logger.info(f"✅ 成功提取商品 {idx+1}: {product_data.name}")
                        else:
                            logger.warning(f"❌ 商品 {idx+1} 提取失败")

                    except Exception as e:
                        logger.error(f"处理商品 {idx+1} 时发生错误: {e}")

                    finally:
                        # 返回原页面继续处理其他商品
                        try:
                            page.goto(current_url, timeout=10000, wait_until="domcontentloaded")
                            time.sleep(1)
                        except Exception as e:
                            logger.warning(f"返回原页面失败，跳过剩余商品: {e}")
                            break
                else:
                    logger.warning(f"❌ 商品 {idx+1} 无法获取URL")

            except Exception as e:
                logger.error(f"处理商品 {idx+1} 时发生未预期错误: {e}")
                continue

        logger.info(f"商品提取完成，成功获取 {len(results)} 个商品的详细信息")
        return results

    def _get_product_url_from_element(self, item_element, page: Page) -> Optional[str]:
        """
        从商品元素中提取商品URL

        Args:
            item_element: 商品元素
            page: Playwright页面对象

        Returns:
            商品URL，如果失败则返回None
        """
        try:
            # 检查元素是否直接包含链接
            href = item_element.get_attribute("href")
            if href and self._is_valid_product_url(href):
                return self._normalize_url(href)

            # 查找最近的父链接
            try:
                parent_link = item_element.evaluate("""el => {
                    const parent = el.closest('a');
                    return parent ? parent.href : null;
                }""")
                if parent_link and self._is_valid_product_url(parent_link):
                    return self._normalize_url(parent_link)
            except:
                pass

            # 检查子元素是否有链接
            try:
                child_link = item_element.evaluate("""el => {
                    const link = el.querySelector('a');
                    return link ? link.href : null;
                }""")
                if child_link and self._is_valid_product_url(child_link):
                    return self._normalize_url(child_link)
            except:
                pass

            # 通过 data-spm-anchor-id 查找相关链接
            data_spm_anchor_id = item_element.get_attribute("data-spm-anchor-id")
            if data_spm_anchor_id:
                try:
                    related_links = page.evaluate(f"""() => {{
                        const elements = document.querySelectorAll('[data-spm-anchor-id="{data_spm_anchor_id}"]');
                        for (let el of elements) {{
                            const link = el.closest('a') || el.querySelector('a');
                            if (link && link.href) {{
                                return link.href;
                            }}
                        }}
                        return null;
                    }}""")
                    if related_links and self._is_valid_product_url(related_links):
                        return self._normalize_url(related_links)
                except:
                    pass

            return None

        except Exception as e:
            logger.error(f"从商品元素提取URL失败: {e}")
            return None

    def _extract_product_detail_from_page(self, page: Page, category: str) -> Optional[EquipmentData]:
        """
        从商品详情页面提取完整商品信息

        Args:
            page: 商品详情页面对象
            category: 商品类别

        Returns:
            完整的商品信息
        """
        try:
            # 使用现有的详情页提取方法
            name = self._extract_detail_name(page)
            if not name:
                logger.warning("未提取到商品名称")
                raise ValueError("商品名称为空")

            price = self._extract_detail_price(page)
            specs = self._extract_specs(page)
            images = self._extract_images(page)
            description = self._extract_description(page)

            # 提取品牌（优先规格表，回退到标题）
            brand = specs.get("品牌") or self._extract_brand_from_name(name)

            # 标准化规格参数
            normalized_specs = self._normalize_specs(specs, name)

            # 推断类别
            inferred_category = category or self._infer_category(name, specs)

            # 构建完整商品数据
            equipment = EquipmentData(
                name=name,
                brand=brand or "未知品牌",
                price=price,
                url=page.url,
                category=inferred_category,
                source="taobao_rpa_detail",
                description=description,
                images=images,
                specs=normalized_specs,
            )

            logger.debug(f"成功提取商品详情: {name}")
            return equipment

        except Exception as e:
            logger.error(f"从详情页提取商品信息失败: {e}")
            return None

    def _is_valid_product_url(self, url: str) -> bool:
        """
        检查URL是否为有效的商品详情页链接

        Args:
            url: 待检查的URL

        Returns:
            是否为有效的商品URL
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

    def _normalize_url(self, url: str) -> str:
        """
        标准化URL格式

        Args:
            url: 原始URL

        Returns:
            标准化后的URL
        """
        if url.startswith("//"):
            return "https:" + url
        elif not url.startswith("http"):
            return "https:" + url
        return url

    def _extract_item_name(self, item) -> Optional[str]:
        """提取商品名称"""
        selectors = [
            ".title",
            ".Title--title",
            "a[class*='title']",
            "div[class*='title']",
        ]

        for selector in selectors:
            try:
                elem = item.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text:
                        return text
            except:
                continue

        return None

    def _extract_item_price(self, item) -> Optional[str]:
        """提取商品价格"""
        selectors = [
            ".price",
            ".Price--priceInt",
            "span[class*='price']",
            "strong[class*='price']",
        ]

        for selector in selectors:
            try:
                elem = item.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    # 清理价格文本
                    text = re.sub(r"[^\d.]", "", text)
                    if text:
                        return text
            except:
                continue

        return None

    def _extract_item_url(self, item) -> Optional[str]:
        """提取商品链接"""
        selectors = [
            "a[href*='item.taobao.com']",
            "a[href*='detail.tmall.com']",
            "a.item",
            "a",
        ]

        for selector in selectors:
            try:
                elem = item.locator(selector).first
                if elem.count() > 0:
                    href = elem.get_attribute("href")
                    if href:
                        # 修复协议
                        if href.startswith("//"):
                            href = "https:" + href
                        elif not href.startswith("http"):
                            href = "https:" + href

                        # 只返回淘宝/天猫链接
                        if "item.taobao.com" in href or "detail.tmall.com" in href:
                            return href
            except:
                continue

        return None

    def _extract_brand_from_name(self, name: str) -> str:
        """
        从商品名称推断品牌

        Args:
            name: 商品名称

        Returns:
            品牌名称
        """
        # 常见渔具品牌（中英文）
        brands = [
            # 国际品牌
            "禧玛诺", "shimano", "SHIMANO",
            "达亿瓦", "daiwa", "DAIWA",
            "Abu Garcia", "阿布", "abu",
            "Penn", "宾威", "penn",
            # 国产品牌
            "光威", "汉鼎", "迪佳", "钓鱼王",
            "化氏", "龙王恨", "天元", "老鬼",
            "佳钓尼", "法莱", "宝飞龙", "狼王",
        ]

        name_lower = name.lower()

        for brand in brands:
            if brand.lower() in name_lower:
                # 返回规范化的品牌名（首字母大写）
                return brand.capitalize()

        return "未知品牌"

    def _has_next_page(self, page: Page) -> bool:
        """
        检查是否有下一页

        Args:
            page: Page对象

        Returns:
            是否有下一页
        """
        # 下一页按钮选择器
        next_selectors = [
            ".next:not(.disabled)",
            ".PageSelector--next:not([disabled])",
            "button.next:not([disabled])",
            "a.next:not(.disabled)",
        ]

        for selector in next_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0 and elem.is_visible(timeout=2000):
                    logger.debug(f"找到下一页按钮: {selector}")
                    return True
            except:
                continue

        return False

    def _goto_next_page(self, page: Page) -> bool:
        """
        翻到下一页

        Args:
            page: Page对象

        Returns:
            是否成功
        """
        # 下一页按钮选择器
        next_selectors = [
            ".next",
            ".PageSelector--next",
            "button.next",
            "a.next",
        ]

        for selector in next_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0 and elem.is_visible(timeout=2000):
                    # 点击下一页
                    elem.click()
                    logger.debug(f"点击下一页: {selector}")

                    # 等待页面加载
                    time.sleep(2)

                    # 等待商品列表重新加载
                    if self._wait_for_products(page):
                        return True
            except Exception as e:
                logger.debug(f"翻页失败 ({selector}): {e}")
                continue

        return False

    def _extract_detail_name(self, page: Page) -> Optional[str]:
        """提取详情页商品名称"""
        selectors = [
            ".tb-detail-hd h1",
            ".ItemHeader--mainTitle",
            "h1[class*='title']",
            ".tb-main-title",
        ]

        for selector in selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    if text:
                        return text
            except:
                continue

        return None

    def _extract_detail_price(self, page: Page) -> Optional[str]:
        """提取详情页价格"""
        selectors = [
            ".tb-rmb-num",
            ".Price--priceText",
            "span[class*='price']",
            ".tm-price",
        ]

        for selector in selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    # 清理价格
                    text = re.sub(r"[^\d.]", "", text)
                    if text:
                        return text
            except:
                continue

        return None

    def _extract_specs(self, page: Page) -> dict:
        """
        提取规格参数表

        Args:
            page: Page对象

        Returns:
            规格字典 {"参数名": "参数值"}
        """
        specs = {}

        # 规格表选择器
        spec_selectors = [
            ".attributes-list",  # 旧版淘宝
            ".Specs--attributes",  # 新版淘宝
            ".tm-tableAttr",  # 天猫
            "#J_AttrUL",  # 另一种格式
        ]

        for selector in spec_selectors:
            try:
                # 找到规格列表容器
                container = page.locator(selector).first
                if container.count() == 0:
                    continue

                # 提取 li 元素（通常是 <li>品牌：禧玛诺</li>）
                items = container.locator("li").all()
                for item in items:
                    try:
                        text = item.inner_text().strip()
                        # 分割参数名和值（支持多种分隔符）
                        if "：" in text:
                            key, value = text.split("：", 1)
                        elif ":" in text:
                            key, value = text.split(":", 1)
                        else:
                            continue

                        key = key.strip()
                        value = value.strip()

                        if key and value:
                            specs[key] = value

                    except:
                        continue

                # 如果提取到规格，返回
                if specs:
                    logger.debug(f"使用选择器 {selector} 提取规格: {len(specs)} 项")
                    return specs

            except Exception as e:
                logger.debug(f"规格提取失败 ({selector}): {e}")
                continue

        return specs

    def _extract_images(self, page: Page) -> List[str]:
        """
        提取商品图片

        Args:
            page: Page对象

        Returns:
            图片URL列表
        """
        images = []

        # 1. 提取主图（缩略图列表，最多5张）
        main_image_selectors = [
            "#J_UlThumb img",  # 旧版
            ".tb-thumb img",  # 另一种格式
            "ul[class*='pic-thumb'] img",  # 新版
        ]

        for selector in main_image_selectors:
            try:
                imgs = page.locator(selector).all()
                for img in imgs[:5]:  # 最多5张
                    src = img.get_attribute("src") or img.get_attribute("data-src")
                    if src:
                        src = self._normalize_image_url(src)
                        if src and src not in images:
                            images.append(src)

                if images:
                    break
            except:
                continue

        # 2. 提取详情图（描述区域，最多10张）
        detail_image_selectors = [
            "#description img",  # 旧版
            ".detail-content img",  # 新版
            "div[class*='detail'] img",  # 模糊匹配
        ]

        detail_images = []
        for selector in detail_image_selectors:
            try:
                imgs = page.locator(selector).all()
                for img in imgs[:10]:  # 最多10张
                    src = img.get_attribute("src") or img.get_attribute("data-src")
                    if src:
                        src = self._normalize_image_url(src)
                        if src and src not in images and src not in detail_images:
                            detail_images.append(src)

                if detail_images:
                    break
            except:
                continue

        # 合并主图和详情图
        images.extend(detail_images)

        logger.debug(f"提取图片: 主图 {len(images) - len(detail_images)} 张, 详情图 {len(detail_images)} 张")
        return images

    def _normalize_image_url(self, url: str) -> Optional[str]:
        """
        标准化图片URL（替换为高清版本）

        Args:
            url: 原始URL

        Returns:
            标准化后的URL
        """
        if not url:
            return None

        # 修复协议
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith("http"):
            url = "https:" + url

        # 替换为高清版本（去除尺寸后缀）
        # 例如: xxx_300x300.jpg -> xxx.jpg
        url = re.sub(r"_\d+x\d+.*?\.(jpg|jpeg|png|webp)", r".\1", url, flags=re.IGNORECASE)

        # 验证URL格式
        if not re.match(r"https?://", url):
            return None

        return url

    def _extract_description(self, page: Page) -> Optional[str]:
        """
        提取商品描述文本

        Args:
            page: Page对象

        Returns:
            描述文本
        """
        desc_selectors = [
            "#description",
            ".detail-content",
            "div[class*='detail']",
            ".tb-detail",
        ]

        for selector in desc_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    # 截断到合理长度
                    if len(text) > 1000:
                        text = text[:1000] + "..."
                    if text:
                        return text
            except:
                continue

        return None

    def _normalize_specs(self, specs: dict, name: str) -> dict:
        """
        标准化规格参数（映射到 EquipmentData 字段）

        Args:
            specs: 原始规格字典
            name: 商品名称

        Returns:
            标准化后的规格字典
        """
        normalized = {}

        # 1. 鱼竿规格
        if "长度" in specs or "调性" in specs or "硬度" in specs:
            # 长度（米）
            if "长度" in specs:
                length_str = specs["长度"]
                # 提取数字（支持: "3.6米", "3.6m", "3.6"）
                match = re.search(r"(\d+\.?\d*)", length_str)
                if match:
                    normalized["length"] = match.group(1)

            # 硬度/调性
            if "硬度" in specs:
                normalized["power"] = specs["硬度"]
            if "调性" in specs:
                normalized["action"] = specs["调性"]

            # 节数
            if "节数" in specs or "收缩节数" in specs:
                sections_str = specs.get("节数") or specs.get("收缩节数")
                match = re.search(r"(\d+)", sections_str)
                if match:
                    normalized["sections"] = match.group(1)

            # 重量
            if "重量" in specs or "净重" in specs:
                weight_str = specs.get("重量") or specs.get("净重")
                match = re.search(r"(\d+\.?\d*)", weight_str)
                if match:
                    normalized["weight"] = match.group(1)

        # 2. 渔轮规格
        elif "型号" in specs and ("速比" in specs or "轴承" in specs):
            # 轮型
            if "轮型" in specs or "类型" in specs:
                reel_type = specs.get("轮型") or specs.get("类型")
                normalized["reel_type"] = reel_type

            # 速比
            if "速比" in specs:
                normalized["gear_ratio"] = specs["速比"]

            # 轴承数
            if "轴承" in specs or "轴承数" in specs:
                bearings_str = specs.get("轴承") or specs.get("轴承数")
                match = re.search(r"(\d+)", bearings_str)
                if match:
                    normalized["bearings"] = match.group(1)

            # 重量
            if "重量" in specs:
                weight_str = specs["重量"]
                match = re.search(r"(\d+\.?\d*)", weight_str)
                if match:
                    normalized["weight"] = match.group(1)

        # 3. 鱼线规格
        elif "线径" in specs or "拉力" in specs or "线长" in specs:
            # 线型
            if "类型" in specs or "材质" in specs:
                line_type = specs.get("类型") or specs.get("材质")
                normalized["line_type"] = line_type

            # 线径（毫米）
            if "线径" in specs:
                diameter_str = specs["线径"]
                match = re.search(r"(\d+\.?\d*)", diameter_str)
                if match:
                    normalized["diameter"] = match.group(1)

            # 拉力（磅）
            if "拉力" in specs or "强度" in specs:
                strength_str = specs.get("拉力") or specs.get("强度")
                match = re.search(r"(\d+\.?\d*)", strength_str)
                if match:
                    normalized["strength_lb"] = match.group(1)

            # 长度（米）
            if "线长" in specs or "长度" in specs:
                length_str = specs.get("线长") or specs.get("长度")
                match = re.search(r"(\d+\.?\d*)", length_str)
                if match:
                    normalized["length_m"] = match.group(1)

        # 4. 拟饵规格
        elif "饵型" in specs or "重量" in specs or name.find("路亚") != -1:
            # 饵型
            if "饵型" in specs or "类型" in specs:
                lure_type = specs.get("饵型") or specs.get("类型")
                normalized["lure_type"] = lure_type

            # 分类
            if "分类" in specs:
                normalized["lure_category"] = specs["分类"]

            # 长度（cm）
            if "长度" in specs or "尺寸" in specs:
                length_str = specs.get("长度") or specs.get("尺寸")
                match = re.search(r"(\d+\.?\d*)", length_str)
                if match:
                    normalized["length"] = match.group(1)

            # 重量（克）
            if "重量" in specs:
                weight_str = specs["重量"]
                match = re.search(r"(\d+\.?\d*)", weight_str)
                if match:
                    normalized["weight"] = match.group(1)

        return normalized

    def _infer_category(self, name: str, specs: dict) -> str:
        """
        推断装备类别

        Args:
            name: 商品名称
            specs: 规格参数

        Returns:
            类别名称
        """
        name_lower = name.lower()

        # 根据规格参数推断
        if "调性" in specs or "硬度" in specs:
            return "鱼竿"
        elif "速比" in specs or "轴承" in specs:
            return "渔轮"
        elif "线径" in specs or "拉力" in specs:
            return "鱼线"
        elif "饵型" in specs:
            return "拟饵"

        # 根据名称关键词推断
        if any(kw in name_lower for kw in ["鱼竿", "钓竿", "竿", "rod"]):
            return "鱼竿"
        elif any(kw in name_lower for kw in ["渔轮", "轮", "reel"]):
            return "渔轮"
        elif any(kw in name_lower for kw in ["鱼线", "线", "line"]):
            return "鱼线"
        elif any(kw in name_lower for kw in ["拟饵", "路亚", "饵", "lure", "bait"]):
            return "拟饵"
        elif any(kw in name_lower for kw in ["鱼钩", "钩", "hook"]):
            return "鱼钩"
        elif any(kw in name_lower for kw in ["浮漂", "漂", "float"]):
            return "浮漂"
        elif any(kw in name_lower for kw in ["渔具包", "包", "bag"]):
            return "渔具包"

        return "通用"
