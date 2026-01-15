"""
拟饵类型数据采集爬虫

从维基百科 Fishing Lure 页面采集拟饵类型数据。
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)


class LureTypeSpider:
    """从维基百科采集拟饵类型数据"""

    URL = "https://en.wikipedia.org/wiki/Fishing_lure"

    # 拟饵类型映射（英文名 -> 中文名和分类）
    LURE_TYPE_MAPPING = {
        "artificial flies": {
            "name_cn": "飞蝇",
            "category": "fly",
            "keywords": ["fly", "flies", "artificial fly"]
        },
        "plugs": {
            "name_cn": "米诺",
            "category": "hard",
            "keywords": ["plug", "crankbait", "minnow", "jerkbait"]
        },
        "soft plastic baits": {
            "name_cn": "软饵",
            "category": "soft",
            "keywords": ["soft plastic", "worm", "grub", "creature"]
        },
        "spinnerbait": {
            "name_cn": "复合亮片",
            "category": "metal",
            "keywords": ["spinnerbait", "spinner bait"]
        },
        "spoon lures": {
            "name_cn": "亮片",
            "category": "metal",
            "keywords": ["spoon", "spoon lure"]
        },
        "surface lures": {
            "name_cn": "水面系",
            "category": "hard",
            "keywords": ["surface", "topwater", "popper", "stickbait", "pencil"]
        },
        "swimbait": {
            "name_cn": "泳饵",
            "category": "soft",
            "keywords": ["swimbait", "swim bait"]
        },
        "jigs": {
            "name_cn": "铅头钩",
            "category": "other",
            "keywords": ["jig", "jighead"]
        },
        "chatterbait": {
            "name_cn": "颤泳饵",
            "category": "metal",
            "keywords": ["chatterbait", "bladed jig", "vibrating jig"]
        },
        "squid lures": {
            "name_cn": "木虾",
            "category": "hard",
            "keywords": ["squid", "egi", "squid jig"]
        },
    }

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser = None
        self._page = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def crawl(self) -> List[Dict[str, Any]]:
        """采集拟饵类型数据"""
        logger.info(f"开始采集维基百科拟饵数据: {self.URL}")

        await self._page.goto(self.URL, wait_until="domcontentloaded")
        await self._page.wait_for_timeout(2000)

        # 提取 Types 部分的列表项
        lure_types = await self._extract_lure_types()

        logger.info(f"采集完成，共获取 {len(lure_types)} 种拟饵类型")
        return lure_types

    async def _extract_lure_types(self) -> List[Dict[str, Any]]:
        """提取拟饵类型列表"""
        results = []

        # 找到 Types 标题后的列表
        types_section = await self._page.query_selector("#Types")
        if not types_section:
            logger.warning("未找到 Types 部分")
            return results

        # 获取 Types 部分后的第一个 ul 列表
        # 使用 JavaScript 来获取
        lure_items = await self._page.evaluate("""
            () => {
                const typesHeading = document.getElementById('Types');
                if (!typesHeading) return [];

                // 找到标题后的列表
                let element = typesHeading.parentElement.nextElementSibling;
                while (element && element.tagName !== 'UL') {
                    element = element.nextElementSibling;
                }

                if (!element || element.tagName !== 'UL') return [];

                const items = [];
                const listItems = element.querySelectorAll(':scope > li');

                for (const li of listItems) {
                    // 获取第一个链接作为名称
                    const link = li.querySelector('a');
                    const name = link ? link.textContent.trim() : '';
                    const url = link ? link.href : '';

                    // 获取完整文本作为描述
                    const fullText = li.textContent.trim();

                    items.push({
                        name: name,
                        url: url,
                        description: fullText
                    });
                }

                return items;
            }
        """)

        for item in lure_items:
            name_en = item.get("name", "").lower()
            description_en = item.get("description", "")

            # 跳过空项
            if not name_en:
                continue

            # 匹配到中文名和分类
            mapping = self._find_mapping(name_en, description_en)

            result = {
                "name_en": item.get("name", ""),
                "name_cn": mapping.get("name_cn", ""),
                "category": mapping.get("category", "other"),
                "description_en": description_en,
                "wiki_url": item.get("url", ""),
                "source": "Wikipedia",
            }

            results.append(result)
            logger.debug(f"提取拟饵: {result['name_en']} -> {result['name_cn']}")

        return results

    def _find_mapping(self, name_en: str, description: str) -> Dict[str, str]:
        """根据英文名找到对应的中文名和分类"""
        name_lower = name_en.lower()
        desc_lower = description.lower()

        for key, mapping in self.LURE_TYPE_MAPPING.items():
            # 检查名称匹配
            if key in name_lower:
                return mapping

            # 检查关键词匹配
            for keyword in mapping.get("keywords", []):
                if keyword in name_lower or keyword in desc_lower:
                    return mapping

        # 默认返回
        return {"name_cn": "", "category": "other"}


async def crawl_lure_types(headless: bool = True) -> List[Dict[str, Any]]:
    """采集拟饵类型数据的便捷函数"""
    async with LureTypeSpider(headless=headless) as spider:
        return await spider.crawl()


# 同步版本
def crawl_lure_types_sync(headless: bool = True) -> List[Dict[str, Any]]:
    """同步版本的采集函数"""
    return asyncio.run(crawl_lure_types(headless=headless))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = crawl_lure_types_sync(headless=False)
    for r in results:
        print(f"{r['name_en']}: {r['name_cn']} ({r['category']})")
        print(f"  {r['description_en'][:100]}...")
        print()
