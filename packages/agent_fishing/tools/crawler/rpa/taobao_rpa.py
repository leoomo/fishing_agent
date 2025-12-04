"""
淘宝RPA爬虫实现 - 关键词搜索模式
"""

import time
import logging
import re
from typing import List, Optional
from urllib.parse import quote

from playwright.sync_api import Page

from ..base_spider import BaseSpider, EquipmentData
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

            # 2. 访问搜索页
            search_url = f"https://s.taobao.com/search?q={quote(keyword)}"
            logger.info(f"访问搜索页: {search_url}")

            if not self.safe_goto(page, search_url):
                logger.error("❌ 访问搜索页失败")
                return results

            # 3. 等待商品列表加载
            if not self._wait_for_products(page):
                logger.error("❌ 商品列表加载失败")
                return results

            # 4. 爬取商品（支持分页）
            page_num = 1
            max_pages = 10  # 最多爬取10页

            while len(results) < max_results and page_num <= max_pages:
                logger.info(f"正在爬取第 {page_num} 页...")

                # 模拟人类浏览
                self._simulate_scroll(page)

                # 提取当前页商品
                page_results = self._extract_products(page, keyword, category)
                results.extend(page_results)

                logger.info(f"第 {page_num} 页提取 {len(page_results)} 条商品，累计 {len(results)} 条")

                # 检查是否达到目标数量
                if len(results) >= max_results:
                    break

                # 检查是否有下一页
                if not self._has_next_page(page):
                    logger.info("已到达最后一页")
                    break

                # 翻页
                if not self._goto_next_page(page):
                    logger.warning("翻页失败，停止爬取")
                    break

                page_num += 1

                # 翻页后延迟
                delay = self.config.request_delay + self.throttler._random_jitter()
                logger.debug(f"翻页延迟: {delay:.2f}秒")
                time.sleep(delay)

        # 截断到目标数量
        results = results[:max_results]
        logger.info(f"✅ 搜索完成，共获取 {len(results)} 条商品")

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
        提取当前页商品列表

        Args:
            page: Page对象
            keyword: 搜索关键词
            category: 装备类型

        Returns:
            装备列表
        """
        results = []

        # 多种选择器兼容
        item_selectors = [
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
                    logger.debug(f"使用选择器: {selector}，找到 {len(items)} 个商品")
                    break
            except:
                continue

        if not items:
            logger.warning("未找到商品列表")
            return results

        # 逐个提取
        for idx, item in enumerate(items):
            try:
                # 提取商品信息
                name = self._extract_item_name(item)
                price = self._extract_item_price(item)
                url = self._extract_item_url(item)

                if not name or not url:
                    logger.debug(f"商品 {idx+1} 缺少必要字段，跳过")
                    continue

                # 提取品牌
                brand = self._extract_brand_from_name(name)

                # 构建数据
                equipment = EquipmentData(
                    name=name,
                    brand=brand,
                    price=price,
                    url=url,
                    category=category,
                    source="taobao_rpa",
                )

                results.append(equipment)
                logger.debug(f"提取商品 {idx+1}: {name}")

            except Exception as e:
                logger.debug(f"提取商品 {idx+1} 失败: {e}")
                continue

        return results

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
