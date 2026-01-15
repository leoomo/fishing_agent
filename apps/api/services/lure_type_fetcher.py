"""
拟饵类型网络采集服务

从维基百科采集拟饵类型数据，使用 LLM 翻译英文内容为中文。
"""

import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from apps.api.database import get_db

logger = logging.getLogger(__name__)


class WikipediaCrawlerService:
    """维基百科拟饵数据采集服务"""

    def __init__(self):
        self.db = get_db()
        self._is_running = False
        self._should_stop = False
        self._current_task: Optional[threading.Thread] = None
        self._progress = {
            "status": "idle",  # idle, crawling, translating, completed, failed
            "message": "",
            "crawled_count": 0,
            "translated_count": 0,
            "total_count": 0,
            "error": None,
        }

    def get_progress(self) -> Dict[str, Any]:
        """获取采集进度"""
        return {
            "is_running": self._is_running,
            **self._progress
        }

    def start_crawl(self) -> Dict[str, Any]:
        """开始网页采集"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        self._should_stop = False
        self._is_running = True
        self._progress = {
            "status": "crawling",
            "message": "正在从维基百科采集数据...",
            "crawled_count": 0,
            "translated_count": 0,
            "total_count": 0,
            "error": None,
        }

        # 在后台线程中执行采集
        self._current_task = threading.Thread(
            target=self._crawl_worker,
            daemon=True
        )
        self._current_task.start()

        return {"success": True, "message": "网页采集任务已启动"}

    def stop_crawl(self) -> Dict[str, Any]:
        """停止采集"""
        if not self._is_running:
            return {"success": False, "message": "没有正在运行的采集任务"}

        self._should_stop = True
        return {"success": True, "message": "正在停止采集..."}

    def _crawl_worker(self):
        """采集工作线程"""
        try:
            # 运行异步采集
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._async_crawl())
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"网页采集异常: {e}")
            self._progress["status"] = "failed"
            self._progress["error"] = str(e)
            self._progress["message"] = f"采集失败: {e}"
        finally:
            self._is_running = False
            self._should_stop = False

    async def _async_crawl(self):
        """异步采集流程"""
        from packages.scraper.spiders.lure_type_spider import LureTypeSpider

        # 1. 采集维基百科数据
        self._progress["status"] = "crawling"
        self._progress["message"] = "正在从维基百科采集拟饵类型数据..."

        async with LureTypeSpider(headless=True) as spider:
            crawled_data = await spider.crawl()

        if self._should_stop:
            self._progress["status"] = "idle"
            self._progress["message"] = "采集已停止"
            return

        self._progress["crawled_count"] = len(crawled_data)
        self._progress["total_count"] = len(crawled_data)
        logger.info(f"维基百科采集完成，共 {len(crawled_data)} 条数据")

        # 2. 使用 LLM 翻译和增强数据
        self._progress["status"] = "translating"
        self._progress["message"] = "正在使用 LLM 翻译和增强数据..."

        for i, item in enumerate(crawled_data):
            if self._should_stop:
                self._progress["status"] = "idle"
                self._progress["message"] = "采集已停止"
                return

            try:
                await self._process_crawled_item(item)
                self._progress["translated_count"] = i + 1
                self._progress["message"] = f"正在处理: {item.get('name_en', '')} ({i + 1}/{len(crawled_data)})"
            except Exception as e:
                logger.error(f"处理采集数据失败: {item.get('name_en', '')}, 错误: {e}")

            # 短暂延迟，避免请求过快
            await asyncio.sleep(0.5)

        self._progress["status"] = "completed"
        self._progress["message"] = f"采集完成，共处理 {len(crawled_data)} 条数据"
        logger.info(f"网页采集任务完成")

    async def _process_crawled_item(self, item: Dict[str, Any]):
        """处理单条采集数据"""
        name_en = item.get("name_en", "")
        name_cn = item.get("name_cn", "")
        category = item.get("category", "other")
        description_en = item.get("description_en", "")
        wiki_url = item.get("wiki_url", "")

        if not name_en:
            return

        # 检查是否已存在（按英文名或中文名匹配）
        existing = None
        if name_cn:
            existing = self.db.execute(
                "SELECT * FROM lure_types WHERE name = ? OR name_en = ?",
                (name_cn, name_en)
            )
        else:
            existing = self.db.execute(
                "SELECT * FROM lure_types WHERE name_en = ?",
                (name_en,)
            )

        # 使用 LLM 翻译描述并生成中文名（如果没有）
        translated = await self._translate_with_llm(name_en, description_en, name_cn)

        now = datetime.now().isoformat()

        if existing:
            # 更新现有记录
            lure_type_id = existing[0]["lure_type_id"]
            update_fields = []
            update_values = []

            if not existing[0].get("name_en") and name_en:
                update_fields.append("name_en = ?")
                update_values.append(name_en)

            if translated.get("description") and not existing[0].get("description"):
                update_fields.append("description = ?")
                update_values.append(translated["description"])

            if wiki_url:
                # 存储 wiki_url 到 best_conditions JSON 中
                best_conditions = existing[0].get("best_conditions", "{}")
                try:
                    bc_data = json.loads(best_conditions) if best_conditions else {}
                except (json.JSONDecodeError, TypeError):
                    bc_data = {}
                bc_data["wiki_url"] = wiki_url
                bc_data["source"] = "Wikipedia"
                if translated.get("usage_tips"):
                    bc_data["usage_tips"] = translated["usage_tips"]
                update_fields.append("best_conditions = ?")
                update_values.append(json.dumps(bc_data, ensure_ascii=False))

            if update_fields:
                update_fields.append("updated_at = ?")
                update_values.append(now)
                update_values.append(lure_type_id)

                self.db.execute_write(
                    f"UPDATE lure_types SET {', '.join(update_fields)} WHERE lure_type_id = ?",
                    tuple(update_values)
                )
                logger.debug(f"更新拟饵类型: {name_en} -> {existing[0]['name']}")
        else:
            # 创建新记录
            final_name = translated.get("name_cn") or name_cn or name_en

            # 准备 best_conditions JSON
            bc_data = {
                "wiki_url": wiki_url,
                "source": "Wikipedia",
            }
            if translated.get("usage_tips"):
                bc_data["usage_tips"] = translated["usage_tips"]

            self.db.execute_write("""
                INSERT INTO lure_types (name, name_en, category, description, best_conditions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                final_name,
                name_en,
                category,
                translated.get("description", ""),
                json.dumps(bc_data, ensure_ascii=False),
                now,
                now
            ))
            logger.debug(f"创建拟饵类型: {name_en} -> {final_name}")

    async def _translate_with_llm(self, name_en: str, description_en: str, existing_name_cn: str = "") -> Dict[str, Any]:
        """使用 LLM 翻译英文内容"""
        from apps.api.services.llm_service import LLMService

        llm = LLMService(
            provider="qwen",
            model="qwen-plus",
            caller="wikipedia_crawler"
        )

        prompt = f"""你是一位专业的路亚钓鱼翻译专家。请将以下英文拟饵信息翻译成中文。

英文名称: {name_en}
英文描述: {description_en}
已有中文名: {existing_name_cn or '无'}

请返回 JSON 格式（不要包含 markdown 代码块标记）：
{{
    "name_cn": "中文名称（如果已有中文名则保持不变，否则翻译）",
    "description": "中文描述（简洁专业，50-100字）",
    "usage_tips": ["使用技巧1", "使用技巧2"]
}}

只返回 JSON，不要其他内容。"""

        try:
            response = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=30
            )

            if not response.success:
                logger.warning(f"LLM 翻译失败: {name_en}")
                return {"name_cn": existing_name_cn, "description": "", "usage_tips": []}

            content = response.content.strip()
            # 清理可能的 markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"LLM 翻译异常: {name_en}, 错误: {e}")
            return {"name_cn": existing_name_cn, "description": "", "usage_tips": []}


# 全局网页采集服务实例
_wikipedia_crawler_service: Optional[WikipediaCrawlerService] = None


def get_wikipedia_crawler_service() -> WikipediaCrawlerService:
    """获取维基百科采集服务单例"""
    global _wikipedia_crawler_service
    if _wikipedia_crawler_service is None:
        _wikipedia_crawler_service = WikipediaCrawlerService()
    return _wikipedia_crawler_service
