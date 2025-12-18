"""
路亚论坛爬虫实现

爬取路亚论坛的装备测评帖子，提取装备信息、用户评价和实拍图片。

支持的论坛：
- 路亚之家 (www.luya.com)
- 中国钓鱼论坛 (www.diaoyula.com)
- 钓鱼人论坛 (www.diaoyuren.com)
"""

import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from packages.scraper.spider.base import BaseSpider, CrawlItem as EquipmentData

logger = logging.getLogger(__name__)


class ForumSpider(BaseSpider):
    """论坛爬虫"""

    # 支持的论坛配置
    FORUMS = {
        "路亚之家": {
            "base_url": "http://www.luya.com",
            "search_url": "http://www.luya.com/search.php?mod=forum",
            "encoding": "utf-8",
        },
        "钓鱼人": {
            "base_url": "https://www.diaoyuren.com",
            "search_url": "https://www.diaoyuren.com/search.php?mod=forum",
            "encoding": "utf-8",
        },
    }

    def __init__(self, config: Optional[Dict] = None, forum_name: str = "路亚之家"):
        super().__init__(config)
        self.forum_name = forum_name
        self.forum_config = self.FORUMS.get(forum_name)

        if not self.forum_config:
            raise ValueError(
                f"不支持的论坛: {forum_name}, 支持的论坛: {list(self.FORUMS.keys())}"
            )

        logger.info(f"初始化论坛爬虫: {forum_name}")

    def search_equipment(
        self, keyword: str, category: Optional[str] = None, max_results: int = 50
    ) -> List[EquipmentData]:
        """
        搜索装备测评帖

        Args:
            keyword: 搜索关键词（如"禧玛诺毒牙"）
            category: 装备类别
            max_results: 最大结果数量

        Returns:
            装备数据列表
        """
        # 构建搜索关键词
        search_keyword = self._build_search_keyword(keyword, category)
        logger.info(f"论坛搜索: {search_keyword} (最大: {max_results})")

        results = []
        page = 1

        while len(results) < max_results:
            # 发起搜索请求
            posts = self._search_posts(search_keyword, page)

            if not posts:
                logger.info(f"第{page}页无结果，停止搜索")
                break

            logger.info(f"第{page}页找到 {len(posts)} 个帖子")

            # 遍历帖子，提取装备信息
            for post_url in posts:
                if len(results) >= max_results:
                    break

                equipment = self.get_product_detail(post_url)
                if equipment:
                    results.append(equipment)
                    logger.debug(f"从帖子提取装备: {equipment.name}")

            page += 1

            # 安全上限
            if page > 5:
                logger.warning("已达到5页上限，停止搜索")
                break

        # 更新统计
        self.stats["total_results"] = len(results)
        logger.info(f"论坛搜索完成: 共提取 {len(results)} 个装备")
        return results

    def get_product_detail(self, post_url: str) -> Optional[EquipmentData]:
        """
        从测评帖提取装备信息

        Args:
            post_url: 帖子URL

        Returns:
            装备数据
        """
        logger.info(f"解析测评帖: {post_url}")

        # 发起请求
        response = self.fetch_with_retry(
            post_url, referer=self.forum_config["base_url"]
        )

        if not response:
            logger.error(f"帖子请求失败: {post_url}")
            return None

        # 设置正确的编码
        response.encoding = self.forum_config["encoding"]

        # 解析帖子内容
        try:
            equipment = self._parse_review_post(response.text, post_url)
            return equipment
        except Exception as e:
            logger.error(f"解析帖子失败: {e}", exc_info=True)
            return None

    def _build_search_keyword(self, keyword: str, category: Optional[str]) -> str:
        """构建搜索关键词（添加"测评"、"开箱"等关键词）"""
        review_keywords = ["测评", "开箱", "使用感受", "体验"]
        # 随机选择一个测评关键词
        import random

        review_keyword = random.choice(review_keywords)

        if category:
            return f"{keyword} {category} {review_keyword}"
        return f"{keyword} {review_keyword}"

    def _search_posts(self, keyword: str, page: int) -> List[str]:
        """
        搜索帖子

        Args:
            keyword: 搜索关键词
            page: 页码

        Returns:
            帖子URL列表
        """
        # 构建搜索URL
        search_url = self.forum_config["search_url"]
        params = {
            "searchid": "",
            "orderby": "lastpost",  # 按最后回复排序
            "ascdesc": "desc",
            "searchsubmit": "yes",
            "kw": keyword,
            "page": page,
        }

        # 构建完整URL
        from urllib.parse import urlencode

        full_url = f"{search_url}&{urlencode(params)}"

        # 发起请求
        response = self.fetch_with_retry(full_url)

        if not response:
            logger.warning(f"搜索请求失败: 第{page}页")
            return []

        # 设置编码
        response.encoding = self.forum_config["encoding"]

        # 解析搜索结果
        soup = BeautifulSoup(response.text, "lxml")
        post_urls = []

        # 查找帖子列表（Discuz论坛通用结构）
        threads = soup.find_all("tbody", {"id": re.compile(r"normalthread_\d+")})

        for thread in threads:
            # 提取帖子链接
            link = thread.find("a", {"class": "s xst"})
            if link and link.get("href"):
                post_url = urljoin(self.forum_config["base_url"], link["href"])
                post_urls.append(post_url)

        logger.debug(f"搜索第{page}页找到 {len(post_urls)} 个帖子")
        return post_urls

    def _parse_review_post(self, html: str, post_url: str) -> Optional[EquipmentData]:
        """
        解析测评帖子

        Args:
            html: 帖子HTML
            post_url: 帖子URL

        Returns:
            装备数据
        """
        soup = BeautifulSoup(html, "lxml")

        # 提取帖子标题（作为装备名称）
        title_elem = soup.find("h1", {"class": "ts"}) or soup.find("span", {"id": "thread_subject"})
        if not title_elem:
            logger.warning("未找到帖子标题")
            return None

        title = title_elem.get_text(strip=True)

        # 从标题提取装备名称和品牌
        name = self._extract_equipment_name_from_title(title)
        brand_name = self._extract_brand_from_title(title)
        category = self._infer_category_from_title(title)

        # 提取帖子正文
        post_content = soup.find("td", {"class": "t_f"}) or soup.find("div", {"class": "pcb"})
        if not post_content:
            logger.warning("未找到帖子正文")
            description = None
        else:
            description = post_content.get_text(strip=True)[:500]  # 限制500字符

        # 提取图片
        images = self._extract_images_from_post(post_content) if post_content else []

        # 提取规格参数（从正文中）
        specs = self._extract_specs_from_content(post_content.get_text() if post_content else "")

        # 从正文推断价格
        price = self._extract_price_from_content(post_content.get_text() if post_content else "")

        # 构建EquipmentData
        try:
            equipment = EquipmentData(
                name=name,
                category=category,
                brand_name=brand_name or "未知品牌",
                price_min=price if price else 0.0,
                price_max=price if price else None,
                source_url=post_url,
                images=images,
                description=description,
                specs=specs,
                user_level=None,  # 论坛帖无法直接判断
                target_fish=self._extract_target_fish_from_content(
                    post_content.get_text() if post_content else ""
                ),
            )
            return equipment
        except ValueError as e:
            logger.warning(f"创建EquipmentData失败: {e}")
            return None

    def _extract_equipment_name_from_title(self, title: str) -> str:
        """从标题提取装备名称（去除"测评"、"开箱"等词）"""
        # 移除测评关键词
        title = re.sub(r"(测评|开箱|使用感受|体验|分享|简评)", "", title)
        # 移除特殊符号
        title = re.sub(r"[【】\[\]()（）]", " ", title)
        # 清理多余空格
        title = " ".join(title.split())
        return title.strip()

    def _extract_brand_from_title(self, title: str) -> Optional[str]:
        """从标题提取品牌"""
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

        title_upper = title.upper()
        for brand in common_brands:
            if brand.upper() in title_upper or brand in title:
                return brand

        return None

    def _infer_category_from_title(self, title: str) -> str:
        """从标题推断类别"""
        title_lower = title.lower()
        if "竿" in title or "rod" in title_lower:
            return "鱼竿"
        elif "轮" in title or "reel" in title_lower:
            return "渔轮"
        elif "线" in title or "line" in title_lower:
            return "鱼线"
        elif "饵" in title or "lure" in title_lower or "bait" in title_lower:
            return "拟饵"
        else:
            return "鱼竿"  # 默认

    def _extract_images_from_post(self, content) -> List[Dict[str, str]]:
        """从帖子提取图片"""
        images = []
        img_tags = content.find_all("img", limit=10)  # 最多10张

        for img in img_tags:
            img_url = img.get("file") or img.get("src") or img.get("zoomfile")
            if img_url:
                # 补全URL
                if not img_url.startswith("http"):
                    img_url = urljoin(self.forum_config["base_url"], img_url)
                images.append({"url": img_url, "type": "review"})

        logger.debug(f"从帖子提取 {len(images)} 张图片")
        return images

    def _extract_specs_from_content(self, content: str) -> Dict[str, Any]:
        """从内容提取规格参数"""
        specs = {}

        # 常见规格关键词
        spec_patterns = {
            "长度": r"长度[:：]?\s*(\d+\.?\d*)\s*(米|m|尺|ft)",
            "硬度": r"硬度[:：]?\s*([A-Z]{1,3})",
            "调性": r"调性[:：]?\s*(\d+H|快调|慢调|中调)",
            "节数": r"节数[:：]?\s*(\d+)\s*节",
            "自重": r"自重[:：]?\s*(\d+\.?\d*)\s*(克|g)",
            "轴承": r"轴承[:：]?\s*(\d+)\s*个",
            "速比": r"速比[:：]?\s*(\d+\.?\d*:\d+\.?\d*)",
            "线径": r"线径[:：]?\s*(\d+\.?\d*)\s*号",
        }

        for key, pattern in spec_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                specs[key] = match.group(1)

        return specs

    def _extract_price_from_content(self, content: str) -> Optional[float]:
        """从内容提取价格"""
        # 价格模式
        price_patterns = [
            r"价格[:：]?\s*(\d+\.?\d*)\s*元",
            r"[\uffe5$]\s*(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*块钱",
        ]

        for pattern in price_patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_target_fish_from_content(self, content: str) -> Optional[str]:
        """从内容提取目标鱼种"""
        common_fish = ["鲈鱼", "黑鱼", "鳜鱼", "鲶鱼", "翘嘴", "马口", "白条"]

        for fish in common_fish:
            if fish in content:
                return fish

        return None
