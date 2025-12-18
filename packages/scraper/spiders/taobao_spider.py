"""
淘宝爬虫实现（简化版）

由于淘宝反爬虫机制严格，本实现采用简化策略：
1. 使用移动版API（反爬虫相对宽松）
2. 基础HTML解析（不处理JS动态渲染）
3. 预留Cookie管理和Selenium扩展接口

注意：淘宝可能需要登录态或滑块验证，建议配合手动录入使用。
"""

import json
import logging
import random
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

from bs4 import BeautifulSoup

from packages.scraper.spider.base import BaseSpider, CrawlItem as EquipmentData

logger = logging.getLogger(__name__)


class ScrollException(Exception):
    """滚动操作失败异常"""
    pass


class ContentLoadException(Exception):
    """内容加载失败异常"""
    pass


class TaobaoSpider(BaseSpider):
    """淘宝爬虫（简化版）"""

    # 淘宝移动版搜索（反爬虫相对宽松）
    MOBILE_SEARCH_URL = "https://s.m.taobao.com/h5"
    # PC版搜索（需要处理JS渲染）
    PC_SEARCH_URL = "https://s.taobao.com/search"

    # 装备类别关键词
    CATEGORY_KEYWORDS = {
        "鱼竿": "路亚竿",
        "渔轮": "路亚轮",
        "鱼线": "路亚线 PE线",
        "拟饵": "路亚饵 拟饵",
    }

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.use_mobile = config.get("use_mobile", True) if config else True
        self.use_rpa_for_dynamic = config.get("use_rpa_for_dynamic", True) if config else True

        # Scroll configuration
        self.max_scroll_attempts = config.get("max_scroll_attempts", 20) if config else 20
        self.scroll_wait_time_range = config.get("scroll_wait_time", (1.5, 3.0)) if config else (1.5, 3.0)
        self.scroll_completion_threshold = config.get("scroll_completion_threshold", 3) if config else 3

        # Lazy RPA initialization
        self._rpa_spider = None

        logger.info(f"初始化淘宝爬虫 (移动版: {self.use_mobile}, 动态内容: {self.use_rpa_for_dynamic})")
        logger.warning(
            "淘宝反爬虫严格，建议配合手动录入使用。"
            "如遇验证码/封禁，请增加延迟或使用代理池。"
        )

    @property
    def rpa_spider(self):
        """Lazy initialization of RPA spider"""
        if self._rpa_spider is None:
            from .rpa.taobao_rpa import TaobaoRPA
            from .rpa.config import RPAConfig
            self._rpa_spider = TaobaoRPA(RPAConfig.from_env())
            logger.info("初始化RPA爬虫用于动态内容处理")
        return self._rpa_spider

    def search_equipment(
        self, keyword: str, category: Optional[str] = None, max_results: int = 50
    ) -> List[EquipmentData]:
        """
        搜索装备

        Args:
            keyword: 搜索关键词
            category: 装备类别
            max_results: 最大结果数量

        Returns:
            装备数据列表
        """
        # 构建搜索关键词
        search_keyword = self._build_search_keyword(keyword, category)
        logger.info(f"淘宝搜索: {search_keyword}, 最大结果: {max_results}")

        if self.use_mobile:
            return self._search_mobile(search_keyword, category or "鱼竿", max_results)
        else:
            return self._search_pc(search_keyword, category or "鱼竿", max_results)

    def scroll_and_extract_all_links(self, url: str) -> List[str]:
        """
        滚动页面直到所有商品加载完毕，点击商品进入详情页面提取链接

        实现无限滚动检测和处理逻辑，确保获取到页面上所有动态加载的商品。
        新版本：基于 data-spm-anchor-id 识别商品，直接点击进入详情页面。

        Args:
            url: 目标页面URL，应为包含无限滚动商品的页面

        Returns:
            List[str]: 提取到的所有商品链接列表

        Raises:
            ScrollException: 当滚动检测失败时
            ContentLoadException: 当页面加载失败时

        Example:
            >>> spider = TaobaoSpider()
            >>> links = spider.scroll_and_extract_all_links("https://example.com/products")
            >>> print(f"提取到 {len(links)} 个商品链接")
        """
        logger.info(f"开始无限滚动提取商品链接（新版本：点击进入详情页）: {url}")
        all_links = []

        if not self.use_rpa_for_dynamic:
            logger.warning("RPA动态内容功能未启用，无法进行无限滚动")
            return all_links

        try:
            # 使用上下文管理器确保资源正确释放
            with self.rpa_spider as spider:
                page = spider.page
                context = spider.context

                # 确保已登录（如果需要）
                if not spider.login_manager.ensure_logged_in(page, context):
                    logger.warning("登录失败，继续尝试匿名访问")

                # 导航到目标页面
                if not spider.safe_goto(page, url):
                    raise ContentLoadException(f"页面导航失败: {url}")

                # 等待初始内容加载
                time.sleep(3)

                # 执行无限滚动，加载所有商品
                self._perform_infinite_scroll(page)

                # 提取所有商品链接（新方法：点击商品进入详情页）
                all_links = self._click_products_and_extract_links(page)
                logger.info(f"✅ 无限滚动完成，通过点击商品提取到 {len(all_links)} 个商品链接")

        except ScrollException as e:
            logger.error(f"无限滚动操作失败: {e}")
            raise
        except ContentLoadException as e:
            logger.error(f"内容加载失败: {e}")
            raise
        except Exception as e:
            logger.error(f"滚动提取过程中发生未预期错误: {e}", exc_info=True)
            raise ScrollException(f"滚动提取失败: {e}")

        return all_links

    def _click_products_and_extract_links(self, page) -> List[str]:
        """
        点击页面上的商品，进入详情页面提取商品链接

        Args:
            page: Playwright页面对象

        Returns:
            商品链接列表
        """
        links = []

        # 使用 data-spm-anchor-id 属性识别商品元素
        product_selectors = [
            "[data-spm-anchor-id*='product_shelf']",
            ".title--GExDBPUi[data-spm-anchor-id*='product_shelf']",
            "div[data-spm-anchor-id*='product_shelf']",
            "[class*='title--'][data-spm-anchor-id*='product_shelf']",
            "[data-spm='product_shelf'] [data-spm-anchor-id]",
        ]

        logger.info("开始识别页面商品元素...")

        # 收集所有商品元素
        all_product_elements = []
        for selector in product_selectors:
            try:
                elements = page.locator(selector).all()
                if elements:
                    all_product_elements.extend(elements)
                    logger.info(f"选择器 '{selector}' 找到 {len(elements)} 个商品元素")
            except Exception as e:
                logger.debug(f"使用选择器 '{selector}' 失败: {e}")

        # 如果没找到商品元素，尝试更广泛的搜索
        if not all_product_elements:
            logger.warning("未找到 data-spm-anchor-id 商品元素，尝试备用方法...")
            backup_selectors = [
                "[data-spm-anchor-id]",  # 任何有 data-spm-anchor-id 的元素
                "[class*='title']",     # 包含 title 的类
                "[class*='Title']",     # 包含 Title 的类
            ]

            for selector in backup_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        logger.info(f"备用选择器 '{selector}' 找到 {len(elements)} 个元素")
                        # 过滤掉明显不是商品的元素
                        filtered_elements = []
                        for elem in elements:
                            try:
                                text = elem.inner_text().strip()
                                if text and len(text) > 3:  # 过滤太短的文本
                                    filtered_elements.append(elem)
                            except:
                                continue
                        all_product_elements.extend(filtered_elements[:50])  # 限制数量
                        break
                except:
                    continue

        logger.info(f"总共找到 {len(all_product_elements)} 个潜在商品元素")

        # 逐个处理商品元素
        for i, element in enumerate(all_product_elements):
            try:
                if i >= 100:  # 限制处理数量，避免过度点击
                    logger.warning("已达到最大处理数量限制，停止处理更多商品")
                    break

                logger.debug(f"处理第 {i+1} 个商品元素...")

                # 保存当前页面URL，以便后续返回
                current_url = page.url

                # 尝试点击商品
                product_url = self._click_product_and_get_url(element, page)

                if product_url:
                    links.append(product_url)
                    logger.debug(f"✅ 商品 {i+1} 获取到URL: {product_url}")
                else:
                    logger.debug(f"❌ 商品 {i+1} 未能获取到URL")

                # 返回原页面继续处理其他商品
                try:
                    page.goto(current_url, timeout=10000)
                    time.sleep(1)
                except:
                    logger.debug(f"返回原页面失败，继续处理...")
                    pass

            except Exception as e:
                logger.debug(f"处理商品元素 {i+1} 失败: {e}")
                continue

        # 去重
        unique_links = list(set(links))
        logger.info(f"最终通过点击方式提取到 {len(unique_links)} 个唯一商品链接")
        return unique_links

    def _click_product_and_get_url(self, element, page) -> Optional[str]:
        """
        点击商品元素并获取商品详情页URL

        Args:
            element: 商品元素
            page: Playwright页面对象

        Returns:
            商品详情页URL，如果失败则返回None
        """
        try:
            # 首先检查元素是否直接包含链接
            href = element.get_attribute("href")
            if href and self._is_valid_product_url(href):
                return self._normalize_url(href)

            # 查找最近的父链接
            try:
                parent_link = element.evaluate("""el => {
                    const parent = el.closest('a');
                    return parent ? parent.href : null;
                }""")
                if parent_link and self._is_valid_product_url(parent_link):
                    return self._normalize_url(parent_link)
            except:
                pass

            # 检查元素是否可点击
            try:
                is_clickable = element.evaluate("""el => {
                    const style = window.getComputedStyle(el);
                    return style.cursor === 'pointer' ||
                           el.onclick !== null ||
                           el.getAttribute('onclick') !== null ||
                           el.tagName === 'A' ||
                           el.closest('a') !== null;
                }""")
            except:
                is_clickable = True  # 默认可点击

            if not is_clickable:
                logger.debug("元素不可点击，跳过")
                return None

            # 尝试多种点击方式
            click_strategies = [
                # 策略1：普通点击
                lambda: element.click(),
                # 策略2：Ctrl+点击（在新标签页打开）
                lambda: element.click(modifiers=['Control']),
                # 策略3：中键点击
                lambda: element.click(button='middle'),
                # 策略4：双击
                lambda: element.dblclick(),
            ]

            for strategy_idx, click_strategy in enumerate(click_strategies):
                try:
                    logger.debug(f"尝试点击策略 {strategy_idx + 1}")

                    # 记录点击前的标签页数量
                    page_count_before = len(page.context.pages)

                    # 执行点击
                    click_strategy()

                    # 等待页面响应
                    time.sleep(2 if strategy_idx == 0 else 1)

                    # 检查是否有新页面打开或当前页面跳转
                    if strategy_idx == 0:
                        # 普通点击，检查当前页面URL是否变化
                        current_url = page.url
                        if current_url != element.page.url:  # 这里需要检查原始URL
                            if self._is_valid_product_url(current_url):
                                return self._normalize_url(current_url)
                    else:
                        # 新标签页打开，检查新页面
                        pages_after = page.context.pages
                        if len(pages_after) > page_count_before:
                            new_page = pages_after[-1]  # 最新打开的页面
                            try:
                                new_page.wait_for_load_state(timeout=5000)
                                new_url = new_page.url
                                if self._is_valid_product_url(new_url):
                                    result_url = self._normalize_url(new_url)
                                    # 关闭新标签页
                                    new_page.close()
                                    return result_url
                                new_page.close()
                            except:
                                try:
                                    new_page.close()
                                except:
                                    pass

                except Exception as e:
                    logger.debug(f"点击策略 {strategy_idx + 1} 失败: {e}")
                    continue

            # 最后尝试：通过 data-spm-anchor-id 查找相关链接
            data_spm_anchor_id = element.get_attribute("data-spm-anchor-id")
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

        except Exception as e:
            logger.debug(f"点击商品并获取URL失败: {e}")

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

        # 检查是否包含商品页面关键词
        valid_patterns = [
            "item.taobao.com/item.htm",
            "detail.tmall.com/item.htm",
            "click.simba.taobao.com",
            "s.click.taobao.com",
        ]

        return any(pattern in url for pattern in valid_patterns)

    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        获取商品详情（支持无限滚动）

        优先使用RPA模式处理动态内容，回退到HTTP模式处理静态内容

        Args:
            product_url: 商品URL

        Returns:
            装备数据
        """
        logger.info(f"获取商品详情: {product_url}")

        # 检测是否需要无限滚动
        if self.use_rpa_for_dynamic and self._requires_infinite_scroll(product_url):
            logger.info("检测到动态内容，使用无限滚动模式")
            return self._extract_with_infinite_scroll(product_url)
        else:
            logger.info("使用静态内容提取模式")
            return self._extract_static_content(product_url)

    def _extract_static_content(self, product_url: str) -> Optional[EquipmentData]:
        """
        提取静态内容（原有逻辑）

        Args:
            product_url: 商品URL

        Returns:
            装备数据
        """
        logger.warning("淘宝详情页解析功能有限，建议使用搜索结果")

        # 发起请求
        response = self.fetch_with_retry(
            product_url, referer="https://s.taobao.com"
        )

        if not response:
            logger.error(f"商品详情请求失败: {product_url}")
            return None

        # 简化解析（提取基础信息）
        try:
            soup = BeautifulSoup(response.text, "lxml")
            # 提取标题
            title_elem = soup.find("h1") or soup.find("title")
            name = title_elem.get_text(strip=True) if title_elem else "未知商品"

            # 推断品牌和类别
            brand_name = self._extract_brand_from_name(name)
            category = self._infer_category_from_name(name)

            return EquipmentData(
                name=name,
                category=category,
                brand_name=brand_name or "未知品牌",
                source_url=product_url,
                description="淘宝商品（详情页解析受限）",
            )
        except Exception as e:
            logger.error(f"解析商品详情失败: {e}", exc_info=True)
            return None

    def _extract_with_infinite_scroll(self, product_url: str) -> Optional[EquipmentData]:
        """
        使用无限滚动模式提取商品详情

        Args:
            product_url: 商品URL

        Returns:
            装备数据
        """
        try:
            with self.rpa_spider as spider:
                page = spider.page
                context = spider.context

                # 确保已登录
                if not spider.login_manager.ensure_logged_in(page, context):
                    logger.error("登录失败，无法提取详情")
                    return None

                # 导航到详情页
                if not spider.safe_goto(page, product_url):
                    logger.error(f"详情页导航失败: {product_url}")
                    return None

                # 等待页面加载
                time.sleep(3)

                # 滚动触发内容加载
                self._perform_infinite_scroll(page, max_scrolls=5)  # 详情页滚动次数较少

                # 提取商品信息（复用RPA的逻辑）
                name = spider._extract_detail_name(page)
                if not name:
                    logger.warning("未提取到商品名称")
                    return None

                price = spider._extract_detail_price(page)
                specs = spider._extract_specs(page)
                images = spider._extract_images(page)
                description = spider._extract_description(page)

                # 推断品牌和类别
                brand_name = specs.get("品牌") or self._extract_brand_from_name(name)
                category = self._infer_category_from_name(name)

                # 标准化规格参数
                normalized_specs = spider._normalize_specs(specs, name)

                return EquipmentData(
                    name=name,
                    category=category,
                    brand_name=brand_name or "未知品牌",
                    source_url=product_url,
                    description=description,
                    images=images,
                    specs=normalized_specs,
                )

        except Exception as e:
            logger.error(f"无限滚动提取详情失败: {e}", exc_info=True)
            logger.warning("回退到静态内容提取")
            return self._extract_static_content(product_url)

    def _requires_infinite_scroll(self, url: str) -> bool:
        """
        检测页面是否需要无限滚动处理

        Args:
            url: 页面URL

        Returns:
            是否需要无限滚动
        """
        # 基于URL模式的简单检测
        infinite_scroll_patterns = [
            "search",
            "category",
            "shop",
            "list",
            "grid",
        ]

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in infinite_scroll_patterns)

    def _perform_infinite_scroll(self, page, max_scrolls: Optional[int] = None) -> None:
        """
        执行无限滚动策略

        Args:
            page: Playwright页面对象
            max_scrolls: 最大滚动次数，默认使用配置值
        """
        max_scrolls = max_scrolls or self.max_scroll_attempts
        scroll_count = 0
        last_height = 0
        no_change_count = 0

        logger.info(f"开始无限滚动，最大尝试次数: {max_scrolls}")

        while scroll_count < max_scrolls:
            try:
                # 滚动到底部
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                # 等待内容加载
                wait_time = random.uniform(*self.scroll_wait_time_range)
                time.sleep(wait_time)

                # 检查页面高度变化
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    logger.debug(f"页面高度未变化，无变化计数: {no_change_count}")
                    if no_change_count >= self.scroll_completion_threshold:
                        logger.info("检测到页面内容加载完成")
                        break
                else:
                    no_change_count = 0
                    last_height = new_height
                    logger.debug(f"页面高度更新: {new_height}")

                scroll_count += 1
                logger.debug(f"滚动进度: {scroll_count}/{max_scrolls}")

            except Exception as e:
                logger.warning(f"滚动操作失败 (第{scroll_count}次): {e}")
                scroll_count += 1
                if scroll_count >= max_scrolls:
                    raise ScrollException(f"滚动操作失败，已达最大重试次数: {max_scrolls}")

        logger.info(f"无限滚动完成，总滚动次数: {scroll_count}")

    def _build_search_keyword(self, keyword: str, category: Optional[str]) -> str:
        """构建搜索关键词"""
        if category and category in self.CATEGORY_KEYWORDS:
            category_keyword = self.CATEGORY_KEYWORDS[category]
            return f"{keyword} {category_keyword}"
        return keyword

    def _search_mobile(
        self, keyword: str, category: str, max_results: int
    ) -> List[EquipmentData]:
        """
        移动版搜索（推荐）

        Args:
            keyword: 搜索关键词
            category: 装备类别
            max_results: 最大结果数量

        Returns:
            装备数据列表
        """
        results = []
        page = 0

        while len(results) < max_results:
            # 构建请求参数
            params = {
                "q": keyword,
                "page": page,
            }
            search_url = f"{self.MOBILE_SEARCH_URL}?{urlencode(params)}"

            # 发起请求（使用移动版UA）
            headers = self.ua_rotator.get_headers(referer="https://m.taobao.com")
            # 覆盖为移动UA
            headers["User-Agent"] = (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.1 Mobile/15E148 Safari/604.1"
            )

            response = self.fetch_with_retry(search_url, headers=headers)

            if not response:
                logger.warning(f"移动版搜索请求失败: 第{page}页")
                break

            # 尝试解析JSON API响应
            page_results = self._parse_mobile_response(response.text, category)

            if not page_results:
                logger.info(f"移动版第{page}页无结果，停止搜索")
                break

            results.extend(page_results)
            logger.info(
                f"移动版第{page}页获取 {len(page_results)} 个商品，累计 {len(results)} 个"
            )

            # 检查是否达到目标
            if len(results) >= max_results:
                results = results[:max_results]
                break

            page += 1

            # 安全上限
            if page > 5:
                logger.warning("移动版已达到5页上限，停止搜索")
                break

        # 更新统计
        self.stats["total_results"] = len(results)
        logger.info(f"淘宝移动版搜索完成: 共获取 {len(results)} 个装备")
        return results

    def _search_pc(
        self, keyword: str, category: str, max_results: int
    ) -> List[EquipmentData]:
        """
        PC版搜索（需要处理JS渲染，当前简化实现）

        Args:
            keyword: 搜索关键词
            category: 装备类别
            max_results: 最大结果数量

        Returns:
            装备数据列表
        """
        logger.warning("PC版搜索受JS渲染限制，推荐使用移动版")
        results = []

        # 构建搜索URL
        params = {"q": keyword, "s": 0}
        search_url = f"{self.PC_SEARCH_URL}?{urlencode(params)}"

        # 发起请求
        response = self.fetch_with_retry(search_url, referer="https://www.taobao.com")

        if not response:
            logger.error("PC版搜索请求失败")
            return results

        # 简化解析（只能提取部分静态内容）
        soup = BeautifulSoup(response.text, "lxml")
        logger.warning("PC版解析功能受限，仅返回静态内容")

        # 尝试提取g_page_config中的数据
        script_tags = soup.find_all("script")
        for script in script_tags:
            if "g_page_config" in script.text:
                # 尝试提取JSON数据
                try:
                    json_match = re.search(
                        r"g_page_config\s*=\s*(\{.*?\});", script.text, re.DOTALL
                    )
                    if json_match:
                        data = json.loads(json_match.group(1))
                        # 进一步解析（需要根据实际结构调整）
                        logger.debug("找到g_page_config数据，但需要进一步解析")
                except Exception as e:
                    logger.debug(f"解析g_page_config失败: {e}")

        # 更新统计
        self.stats["total_results"] = len(results)
        return results

    def _parse_mobile_response(self, html: str, category: str) -> List[EquipmentData]:
        """
        解析移动版响应

        Args:
            html: 响应HTML
            category: 装备类别

        Returns:
            装备数据列表
        """
        results = []

        # 方法1: 尝试解析JSON API响应
        try:
            data = json.loads(html)
            if "data" in data and "itemsArray" in data["data"]:
                items = data["data"]["itemsArray"]
                for item in items:
                    equipment = self._extract_from_api_item(item, category)
                    if equipment:
                        results.append(equipment)
                return results
        except json.JSONDecodeError:
            logger.debug("响应不是JSON格式，尝试HTML解析")

        # 方法2: HTML解析
        soup = BeautifulSoup(html, "lxml")
        item_list = soup.find_all("div", {"class": re.compile(r"item.*")})

        for item in item_list[:20]:  # 限制20个
            try:
                equipment = self._extract_from_html_item(item, category)
                if equipment:
                    results.append(equipment)
            except Exception as e:
                logger.warning(f"提取装备信息失败: {e}")
                continue

        return results

    def _extract_from_api_item(
        self, item: Dict, category: str
    ) -> Optional[EquipmentData]:
        """从API响应项提取装备信息"""
        try:
            name = item.get("title", "未知商品")
            price = float(item.get("price", 0))
            item_url = item.get("url", "")

            # 提取图片
            pic_url = item.get("pic_url") or item.get("picUrl")
            images = []
            if pic_url:
                if not pic_url.startswith("http"):
                    pic_url = "https:" + pic_url
                images.append({"url": pic_url, "type": "main"})

            # 提取品牌
            brand_name = self._extract_brand_from_name(name)

            return EquipmentData(
                name=name,
                category=category,
                brand_name=brand_name or "未知品牌",
                price_min=price,
                price_max=price,
                source_url=item_url if item_url.startswith("http") else "",
                images=images,
            )
        except Exception as e:
            logger.warning(f"API项解析失败: {e}")
            return None

    def _extract_from_html_item(self, item, category: str) -> Optional[EquipmentData]:
        """从HTML项提取装备信息"""
        # 提取标题
        title_elem = item.find("a", {"class": re.compile(r"title.*")})
        if not title_elem:
            return None
        name = title_elem.get_text(strip=True)

        # 提取价格
        price_elem = item.find("span", {"class": re.compile(r"price.*")})
        price = 0.0
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r"(\d+(?:\.\d+)?)", price_text)
            if price_match:
                price = float(price_match.group(1))

        # 提取图片
        img_elem = item.find("img")
        images = []
        if img_elem:
            img_url = img_elem.get("src") or img_elem.get("data-src")
            if img_url:
                if not img_url.startswith("http"):
                    img_url = "https:" + img_url
                images.append({"url": img_url, "type": "main"})

        # 提取链接
        source_url = title_elem.get("href", "")
        if source_url and not source_url.startswith("http"):
            source_url = "https:" + source_url

        # 提取品牌
        brand_name = self._extract_brand_from_name(name)

        try:
            return EquipmentData(
                name=name,
                category=category,
                brand_name=brand_name or "未知品牌",
                price_min=price,
                price_max=price,
                source_url=source_url,
                images=images,
            )
        except ValueError as e:
            logger.warning(f"创建EquipmentData失败: {e}")
            return None

    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """从商品名称提取品牌"""
        common_brands = [
            "禧玛诺",
            "SHIMANO",
            "达亿瓦",
            "DAIWA",
            "阿布",
            "ABU",
            "猎鱼人",
            "光威",
            "迪佳",
            "佳钓尼",
            "钓之屋",
            "海伯",
            "双宝",
            "威海",
            "渔拓",
            "诺思曼",
            "凯普",
        ]

        name_upper = name.upper()
        for brand in common_brands:
            if brand.upper() in name_upper or brand in name:
                return brand

        # 提取第一个词
        words = name.split()
        if words:
            return words[0]

        return None

    def _infer_category_from_name(self, name: str) -> str:
        """从商品名称推断类别"""
        name_lower = name.lower()
        if "竿" in name or "rod" in name_lower:
            return "鱼竿"
        elif "轮" in name or "reel" in name_lower:
            return "渔轮"
        elif "线" in name or "line" in name_lower:
            return "鱼线"
        elif "饵" in name or "lure" in name_lower or "bait" in name_lower:
            return "拟饵"
        else:
            return "鱼竿"  # 默认
