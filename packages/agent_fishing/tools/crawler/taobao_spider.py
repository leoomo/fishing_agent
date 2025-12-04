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
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote

from bs4 import BeautifulSoup

from .base_spider import BaseSpider, EquipmentData

logger = logging.getLogger(__name__)


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
        logger.info(f"初始化淘宝爬虫 (移动版: {self.use_mobile})")
        logger.warning(
            "淘宝反爬虫严格，建议配合手动录入使用。"
            "如遇验证码/封禁，请增加延迟或使用代理池。"
        )

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

    def get_product_detail(self, product_url: str) -> Optional[EquipmentData]:
        """
        获取商品详情

        注意：淘宝商品详情页JS渲染严重，简化版仅提取基础信息

        Args:
            product_url: 商品URL

        Returns:
            装备数据
        """
        logger.info(f"获取商品详情: {product_url}")
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
