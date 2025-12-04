"""
京东爬虫实现

爬取京东商城的路亚装备信息。
京东API结构清晰，反爬虫相对宽松，适合作为首个实现。
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

from bs4 import BeautifulSoup

from .base_spider import BaseSpider, EquipmentData

logger = logging.getLogger(__name__)


class JDSpider(BaseSpider):
    """京东爬虫"""

    # 京东搜索API
    SEARCH_URL = "https://search.jd.com/Search"
    # 京东商品详情
    ITEM_URL = "https://item.jd.com/{}.html"
    # 京东价格API
    PRICE_API = "https://p.3.cn/prices/mgets"

    # 装备类别关键词映射
    CATEGORY_KEYWORDS = {
        "鱼竿": "路亚竿",
        "渔轮": "路亚轮",
        "鱼线": "路亚线",
        "拟饵": "路亚饵",
    }

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        logger.info("初始化京东爬虫")

    def search_equipment(
        self, keyword: str, category: Optional[str] = None, max_results: int = 50
    ) -> List[EquipmentData]:
        """
        搜索装备

        Args:
            keyword: 搜索关键词（如"禧玛诺"）
            category: 装备类别
            max_results: 最大结果数量

        Returns:
            装备数据列表
        """
        # 构建搜索关键词
        search_keyword = self._build_search_keyword(keyword, category)
        logger.info(f"京东搜索: {search_keyword}, 最大结果: {max_results}")

        results = []
        page = 1
        page_size = 30  # 每页显示30个商品

        while len(results) < max_results:
            # 构建搜索URL
            params = {
                "keyword": search_keyword,
                "page": page,
                "s": (page - 1) * page_size + 1,  # 起始位置
                "click": 0,
            }
            search_url = f"{self.SEARCH_URL}?{urlencode(params)}"

            # 发起请求
            response = self.fetch_with_retry(
                search_url, referer="https://www.jd.com"
            )

            if not response:
                logger.warning(f"搜索请求失败: 第{page}页")
                break

            # 解析搜索结果
            page_results = self._parse_search_results(
                response.text, category or "鱼竿"
            )

            if not page_results:
                logger.info(f"第{page}页无结果，停止搜索")
                break

            results.extend(page_results)
            logger.info(f"第{page}页获取 {len(page_results)} 个商品，累计 {len(results)} 个")

            # 检查是否达到目标数量
            if len(results) >= max_results:
                results = results[:max_results]
                break

            page += 1

            # 安全上限（防止无限循环）
            if page > 10:
                logger.warning("已达到10页上限，停止搜索")
                break

        # 更新统计
        self.stats["total_results"] = len(results)
        logger.info(f"京东搜索完成: 共获取 {len(results)} 个装备")
        return results

    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        获取商品详情

        Args:
            product_url: 商品URL

        Returns:
            装备数据
        """
        logger.info(f"获取商品详情: {product_url}")

        # 发起请求
        response = self.fetch_with_retry(product_url, referer="https://search.jd.com")

        if not response:
            logger.error(f"商品详情请求失败: {product_url}")
            return None

        # 解析商品详情
        try:
            equipment = self._parse_product_detail(response.text, product_url)
            return equipment
        except Exception as e:
            logger.error(f"解析商品详情失败: {e}", exc_info=True)
            return None

    def _build_search_keyword(self, keyword: str, category: Optional[str]) -> str:
        """
        构建搜索关键词

        Args:
            keyword: 用户关键词
            category: 装备类别

        Returns:
            组合后的关键词
        """
        if category and category in self.CATEGORY_KEYWORDS:
            category_keyword = self.CATEGORY_KEYWORDS[category]
            return f"{keyword} {category_keyword}"
        return keyword

    def _parse_search_results(
        self, html: str, category: str
    ) -> List[EquipmentData]:
        """
        解析搜索结果页面

        Args:
            html: 搜索结果HTML
            category: 装备类别

        Returns:
            装备数据列表
        """
        soup = BeautifulSoup(html, "lxml")
        results = []

        # 查找商品列表（京东搜索页的商品容器）
        item_list = soup.find("div", {"id": "J_goodsList"})
        if not item_list:
            logger.warning("未找到商品列表容器")
            return results

        # 遍历商品项
        items = item_list.find_all("li", {"class": "gl-item"})
        logger.debug(f"找到 {len(items)} 个商品项")

        for item in items:
            try:
                equipment = self._extract_equipment_from_item(item, category)
                if equipment:
                    results.append(equipment)
            except Exception as e:
                logger.warning(f"提取装备信息失败: {e}")
                continue

        return results

    def _extract_equipment_from_item(
        self, item, category: str
    ) -> Optional[EquipmentData]:
        """
        从商品项提取装备信息

        Args:
            item: BeautifulSoup商品项
            category: 装备类别

        Returns:
            装备数据
        """
        # 提取商品ID
        sku_id = item.get("data-sku")
        if not sku_id:
            logger.debug("未找到商品ID")
            return None

        # 提取商品名称
        name_elem = item.find("div", {"class": "p-name"})
        if not name_elem:
            logger.debug("未找到商品名称")
            return None

        name = name_elem.get_text(strip=True)

        # 提取品牌（从商品名称中推断）
        brand_name = self._extract_brand_from_name(name)
        if not brand_name:
            brand_name = "未知品牌"

        # 提取价格（从data-price属性或价格元素）
        price_elem = item.find("div", {"class": "p-price"})
        price = 0.0
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r"(\d+(?:\.\d+)?)", price_text)
            if price_match:
                price = float(price_match.group(1))

        # 提取图片
        img_elem = item.find("img", {"class": "err-product"})
        images = []
        if img_elem:
            img_url = img_elem.get("data-lazy-img") or img_elem.get("src")
            if img_url:
                # 补全协议
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                images.append({"url": img_url, "type": "main"})

        # 构建商品URL
        source_url = self.ITEM_URL.format(sku_id)

        # 构建EquipmentData
        try:
            equipment = EquipmentData(
                name=name,
                category=category,
                brand_name=brand_name,
                price_min=price,
                price_max=price,
                source_url=source_url,
                images=images,
                description=None,  # 需要详情页获取
                specs={},  # 需要详情页获取
            )
            return equipment
        except ValueError as e:
            logger.warning(f"创建EquipmentData失败: {e}")
            return None

    def _extract_brand_from_name(self, name: str) -> Optional[str]:
        """
        从商品名称提取品牌

        常见路亚品牌列表（优先匹配）
        """
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

        # 如果没匹配到，尝试提取第一个词作为品牌
        words = name.split()
        if words:
            return words[0]

        return None

    def _parse_product_detail(
        self, html: str, product_url: str
    ) -> Optional[EquipmentData]:
        """
        解析商品详情页

        Args:
            html: 商品详情HTML
            product_url: 商品URL

        Returns:
            装备数据
        """
        soup = BeautifulSoup(html, "lxml")

        # 提取商品名称
        name_elem = soup.find("div", {"class": "sku-name"})
        if not name_elem:
            logger.error("详情页未找到商品名称")
            return None
        name = name_elem.get_text(strip=True)

        # 提取品牌
        brand_name = self._extract_brand_from_detail_page(soup)

        # 提取价格（需要通过价格API）
        sku_id_match = re.search(r"/(\d+)\.html", product_url)
        price = 0.0
        if sku_id_match:
            sku_id = sku_id_match.group(1)
            price = self._fetch_price(sku_id)

        # 提取图片
        images = self._extract_images_from_detail(soup)

        # 提取描述
        description = self._extract_description(soup)

        # 提取规格参数
        specs = self._extract_specs(soup)

        # 推断类别
        category = self._infer_category_from_name(name)

        # 构建EquipmentData
        try:
            equipment = EquipmentData(
                name=name,
                category=category,
                brand_name=brand_name or "未知品牌",
                price_min=price,
                price_max=price,
                source_url=product_url,
                images=images,
                description=description,
                specs=specs,
            )
            return equipment
        except ValueError as e:
            logger.error(f"创建EquipmentData失败: {e}")
            return None

    def _extract_brand_from_detail_page(self, soup) -> Optional[str]:
        """从详情页提取品牌"""
        # 方法1: 从品牌栏提取
        brand_elem = soup.find("li", {"class": "brand-name"})
        if brand_elem:
            brand_link = brand_elem.find("a")
            if brand_link:
                return brand_link.get_text(strip=True)

        # 方法2: 从参数表提取
        params = soup.find("ul", {"class": "parameter2"})
        if params:
            for li in params.find_all("li"):
                text = li.get_text(strip=True)
                if "品牌：" in text or "品牌:" in text:
                    brand = text.split("：")[-1].split(":")[-1]
                    return brand

        return None

    def _fetch_price(self, sku_id: str) -> float:
        """
        通过价格API获取价格

        Args:
            sku_id: 商品ID

        Returns:
            价格
        """
        try:
            price_url = f"{self.PRICE_API}?skuIds=J_{sku_id}"
            response = self.fetch_with_retry(price_url)
            if response:
                data = response.json()
                if data and len(data) > 0:
                    price_str = data[0].get("p")
                    if price_str:
                        return float(price_str)
        except Exception as e:
            logger.warning(f"获取价格失败: {e}")

        return 0.0

    def _extract_images_from_detail(self, soup) -> List[Dict[str, str]]:
        """从详情页提取图片"""
        images = []

        # 主图
        main_img = soup.find("img", {"id": "spec-img"})
        if main_img:
            img_url = main_img.get("src") or main_img.get("data-origin")
            if img_url:
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                images.append({"url": img_url, "type": "main"})

        # 缩略图
        thumb_list = soup.find("ul", {"id": "spec-list"})
        if thumb_list:
            for img in thumb_list.find_all("img")[:5]:  # 最多5张
                img_url = img.get("src") or img.get("data-origin")
                if img_url:
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    images.append({"url": img_url, "type": "detail"})

        return images

    def _extract_description(self, soup) -> Optional[str]:
        """提取商品描述"""
        intro_elem = soup.find("div", {"class": "p-parameter"})
        if intro_elem:
            return intro_elem.get_text(strip=True)[:500]  # 限制500字符
        return None

    def _extract_specs(self, soup) -> Dict[str, Any]:
        """
        提取规格参数

        Returns:
            规格字典
        """
        specs = {}

        # 从参数表提取
        params = soup.find("ul", {"class": "parameter2"})
        if params:
            for li in params.find_all("li"):
                text = li.get_text(strip=True)
                if "：" in text or ":" in text:
                    parts = text.replace("：", ":").split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        specs[key] = value

        return specs

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
