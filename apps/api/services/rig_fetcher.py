"""
钓组知识采集服务

从 Wikipedia API 获取钓组基础定义，使用 LLM 增强生成完整的钓组知识。
支持断点续采、自动跳过已有数据。
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from apps.api.database import get_db

logger = logging.getLogger(__name__)

# 预设钓组列表
RIG_LIST = [
    # 路亚基础钓组
    {"name_en": "Texas Rig", "name_cn": "德州钓组", "wiki_page": "Texas_rig", "category": "lure"},
    {"name_en": "Carolina Rig", "name_cn": "卡罗莱纳钓组", "wiki_page": "Carolina_rig", "category": "lure"},
    {"name_en": "Drop Shot Rig", "name_cn": "倒吊钓组", "wiki_page": "Dropshotting", "category": "lure"},
    {"name_en": "Wacky Rig", "name_cn": "无铅钓组", "wiki_page": "Wacky_rig", "category": "lure"},
    {"name_en": "Ned Rig", "name_cn": "内德钓组", "wiki_page": None, "category": "lure"},
    {"name_en": "Neko Rig", "name_cn": "猫钓组", "wiki_page": None, "category": "lure"},
    {"name_en": "Shaky Head Rig", "name_cn": "摇头钓组", "wiki_page": None, "category": "lure"},
    {"name_en": "Jig Head Rig", "name_cn": "铅头钩钓组", "wiki_page": None, "category": "lure"},
    {"name_en": "Weightless Rig", "name_cn": "无铅自然落水钓组", "wiki_page": None, "category": "lure"},
    {"name_en": "Split Shot Rig", "name_cn": "咬铅钓组", "wiki_page": None, "category": "lure"},

    # 传统钓组
    {"name_en": "Hair Rig", "name_cn": "毛钩钓组", "wiki_page": "Hair_rig", "category": "bottom"},
    {"name_en": "Float Rig", "name_cn": "浮漂钓组", "wiki_page": None, "category": "float"},
    {"name_en": "Bottom Rig", "name_cn": "底钓钓组", "wiki_page": None, "category": "bottom"},

    # 海钓钓组
    {"name_en": "Sabiki Rig", "name_cn": "串钩钓组", "wiki_page": "Sabiki", "category": "surf"},
    {"name_en": "High-Low Rig", "name_cn": "双钩钓组", "wiki_page": None, "category": "surf"},
    {"name_en": "Fish Finder Rig", "name_cn": "探鱼钓组", "wiki_page": None, "category": "surf"},

    # 飞蝇钓组
    {"name_en": "Dry Fly Rig", "name_cn": "干蝇钓组", "wiki_page": None, "category": "fly"},
    {"name_en": "Nymph Rig", "name_cn": "若虫钓组", "wiki_page": None, "category": "fly"},
]

# 采集状态
class FetchStatus:
    PENDING = "pending"
    FETCHING = "fetching"
    ENRICHING = "enriching"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WikipediaFetcher:
    """Wikipedia API 客户端"""

    # 使用 Wikipedia REST API
    BASE_URL = "https://en.wikipedia.org/api/rest_v1"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FishingAgent/1.0 (https://github.com/fishing-agent; contact@example.com)",
            "Accept": "application/json"
        })

    def get_page_summary(self, title: str) -> Optional[Dict[str, Any]]:
        """获取页面摘要"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/page/summary/{title}",
                timeout=self.timeout
            )

            if response.status_code == 404:
                logger.warning(f"Wikipedia 页面不存在: {title}")
                return None

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Wikipedia API 请求失败: {title}, 错误: {e}")
            return None

    def get_page_extract(self, title: str) -> Optional[str]:
        """获取页面文本内容（使用 MediaWiki API）"""
        try:
            # 使用 MediaWiki Action API 获取更完整的内容
            response = self.session.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "extracts",
                    "exintro": False,  # 获取完整内容
                    "explaintext": True,  # 纯文本格式
                    "format": "json"
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":  # -1 表示页面不存在
                    extract = page_data.get("extract", "")
                    # 限制长度，避免 token 过多
                    if len(extract) > 3000:
                        extract = extract[:3000] + "..."
                    return extract

            return None

        except requests.RequestException as e:
            logger.error(f"获取 Wikipedia 内容失败: {title}, 错误: {e}")
            return None


class RigLLMEnricher:
    """LLM 增强服务 - 生成钓组知识"""

    def __init__(self):
        from apps.api.services.llm_service import LLMService
        self.llm = LLMService(
            provider="qwen",
            model="qwen-plus",
            caller="rig_fetcher"
        )

    def enrich_rig_knowledge(
        self,
        name_cn: str,
        name_en: str,
        category: str,
        wiki_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 LLM 增强钓组知识"""
        # 构建上下文
        context = ""
        if wiki_content:
            context = f"""
Wikipedia 参考资料（英文）:
{wiki_content}
"""

        prompt = f"""你是一位专业的钓鱼专家。请为"{name_cn}"({name_en})生成详细的钓组知识，返回 JSON 格式。

{context}

请返回以下 JSON 格式（不要包含 markdown 代码块标记）：
{{
    "description": "钓组简介（150字以内，包含起源、特点、适用场景）",
    "difficulty": "easy/medium/hard",
    "target_species": ["适用鱼种1", "适用鱼种2", "适用鱼种3"],
    "best_conditions": "最佳使用条件（水深、水流、季节等）",
    "components": [
        {{"name": "组件中文名", "type": "hook/sinker/swivel/leader/float/stopper/snap/bead", "spec": "推荐规格", "quantity": 1, "position": 1, "notes": "安装说明"}}
    ],
    "specs": [
        {{"name": "推荐主线", "value": "8-15", "unit": "lb"}},
        {{"name": "推荐前导线", "value": "6-12", "unit": "lb"}},
        {{"name": "适用水深", "value": "1-5", "unit": "m"}}
    ],
    "assembly_steps": [
        "步骤1：具体操作说明",
        "步骤2：具体操作说明",
        "步骤3：具体操作说明"
    ],
    "usage_tips": [
        "使用技巧1",
        "使用技巧2",
        "使用技巧3"
    ],
    "pros": ["优点1", "优点2"],
    "cons": ["缺点1", "缺点2"],
    "recommended_lures": ["推荐拟饵类型1", "推荐拟饵类型2"]
}}

注意：
1. components 中的 type 必须是以下之一：hook（钩）、sinker（铅坠）、swivel（转环）、leader（前导线）、float（浮漂）、stopper（挡豆）、snap（别针）、bead（珠子）
2. components 按照从主线端到钩端的顺序排列，position 从 1 开始递增
3. 所有内容使用中文
4. 只返回 JSON，不要其他内容"""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                timeout=90
            )

            if not response.success:
                logger.warning(f"LLM 调用失败: {name_cn}, 错误: {response.error}")
                return self._get_default_knowledge(name_cn, name_en, category)

            content = response.content
            # 清理可能的 markdown 代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {name_cn}, 错误: {e}")
            return self._get_default_knowledge(name_cn, name_en, category)
        except Exception as e:
            logger.error(f"LLM 增强失败: {name_cn}, 错误: {e}")
            return self._get_default_knowledge(name_cn, name_en, category)

    def _get_default_knowledge(self, name_cn: str, name_en: str, category: str) -> Dict[str, Any]:
        """返回默认知识结构"""
        return {
            "description": f"{name_cn}是一种常用的钓组配置。",
            "difficulty": "medium",
            "target_species": [],
            "best_conditions": "",
            "components": [],
            "specs": [],
            "assembly_steps": [],
            "usage_tips": [],
            "pros": [],
            "cons": [],
            "recommended_lures": []
        }


class RigFetcherService:
    """钓组知识采集服务"""

    def __init__(self):
        self.db = get_db()
        self.wiki = WikipediaFetcher()
        self.llm = RigLLMEnricher()
        self._is_running = False
        self._should_stop = False
        self._current_task: Optional[threading.Thread] = None

    def get_progress(self) -> Dict[str, Any]:
        """获取采集进度"""
        self._ensure_progress_initialized()

        rows = self.db.execute("""
            SELECT name_cn, name_en, status, rig_id, error_message, updated_at
            FROM rig_fetch_progress
            ORDER BY id
        """)

        items = []
        stats = {
            "total": len(rows),
            "pending": 0,
            "fetching": 0,
            "enriching": 0,
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }

        for row in rows:
            status = row["status"]
            stats[status] = stats.get(status, 0) + 1
            items.append({
                "name_cn": row["name_cn"],
                "name_en": row["name_en"],
                "status": status,
                "rig_id": row["rig_id"],
                "error": row["error_message"],
                "updated_at": row["updated_at"]
            })

        return {
            "is_running": self._is_running,
            "stats": stats,
            "items": items
        }

    def _ensure_progress_initialized(self):
        """确保进度表已初始化"""
        count = self.db.execute("SELECT COUNT(*) as cnt FROM rig_fetch_progress")[0]["cnt"]
        if count > 0:
            return

        now = datetime.now().isoformat()
        for rig in RIG_LIST:
            # 检查是否已存在于 rig_types 表
            existing = self.db.execute(
                "SELECT rig_id FROM rig_types WHERE name = ?",
                (rig["name_cn"],)
            )

            if existing:
                self.db.execute_write("""
                    INSERT OR IGNORE INTO rig_fetch_progress
                    (name_cn, name_en, wiki_page, category, status, rig_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rig["name_cn"], rig["name_en"], rig.get("wiki_page"),
                    rig["category"], FetchStatus.SKIPPED,
                    existing[0]["rig_id"], now, now
                ))
            else:
                self.db.execute_write("""
                    INSERT OR IGNORE INTO rig_fetch_progress
                    (name_cn, name_en, wiki_page, category, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    rig["name_cn"], rig["name_en"], rig.get("wiki_page"),
                    rig["category"], FetchStatus.PENDING, now, now
                ))

    def start_fetch(self, use_llm: bool = True) -> Dict[str, Any]:
        """开始或继续采集"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        self._ensure_progress_initialized()
        self._should_stop = False
        self._is_running = True

        self._current_task = threading.Thread(
            target=self._fetch_worker,
            args=(use_llm,),
            daemon=True
        )
        self._current_task.start()

        return {"success": True, "message": "采集任务已启动"}

    def pause_fetch(self) -> Dict[str, Any]:
        """暂停采集"""
        if not self._is_running:
            return {"success": False, "message": "没有正在运行的采集任务"}

        self._should_stop = True
        return {"success": True, "message": "正在暂停采集..."}

    def retry_failed(self, names: Optional[List[str]] = None) -> Dict[str, Any]:
        """重试失败的项目"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        now = datetime.now().isoformat()

        if names:
            for name in names:
                self.db.execute_write("""
                    UPDATE rig_fetch_progress
                    SET status = ?, error_message = NULL, updated_at = ?
                    WHERE name_cn = ? AND status = ?
                """, (FetchStatus.PENDING, now, name, FetchStatus.FAILED))
        else:
            self.db.execute_write("""
                UPDATE rig_fetch_progress
                SET status = ?, error_message = NULL, updated_at = ?
                WHERE status = ?
            """, (FetchStatus.PENDING, now, FetchStatus.FAILED))

        return {"success": True, "message": "已重置失败项目"}

    def reset_all(self) -> Dict[str, Any]:
        """重置所有进度"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        self.db.execute_write("DELETE FROM rig_fetch_progress")
        self._ensure_progress_initialized()

        return {"success": True, "message": "已重置所有进度"}

    def _fetch_worker(self, use_llm: bool):
        """采集工作线程"""
        try:
            while not self._should_stop:
                pending = self.db.execute("""
                    SELECT name_cn, name_en, wiki_page, category
                    FROM rig_fetch_progress
                    WHERE status = ?
                    ORDER BY id
                    LIMIT 1
                """, (FetchStatus.PENDING,))

                if not pending:
                    logger.info("所有钓组已采集完成")
                    break

                row = pending[0]
                self._fetch_single(
                    row["name_cn"],
                    row["name_en"],
                    row["wiki_page"],
                    row["category"],
                    use_llm
                )

                # 延迟避免请求过快
                time.sleep(2)

        except Exception as e:
            logger.error(f"采集工作线程异常: {e}")
        finally:
            self._is_running = False
            self._should_stop = False

    def _fetch_single(
        self,
        name_cn: str,
        name_en: str,
        wiki_page: Optional[str],
        category: str,
        use_llm: bool
    ):
        """采集单个钓组"""
        now = datetime.now().isoformat()

        try:
            # 更新状态为采集中
            self.db.execute_write("""
                UPDATE rig_fetch_progress
                SET status = ?, updated_at = ?
                WHERE name_cn = ?
            """, (FetchStatus.FETCHING, now, name_cn))

            # 从 Wikipedia 获取数据
            wiki_content = None
            if wiki_page:
                wiki_content = self.wiki.get_page_extract(wiki_page)
                if wiki_content:
                    logger.info(f"获取 Wikipedia 内容成功: {wiki_page}")

            # 保存 Wikipedia 原始数据
            self.db.execute_write("""
                UPDATE rig_fetch_progress
                SET wiki_data = ?, updated_at = ?
                WHERE name_cn = ?
            """, (wiki_content, datetime.now().isoformat(), name_cn))

            # LLM 增强
            enriched_data = None
            if use_llm:
                self.db.execute_write("""
                    UPDATE rig_fetch_progress
                    SET status = ?, updated_at = ?
                    WHERE name_cn = ?
                """, (FetchStatus.ENRICHING, datetime.now().isoformat(), name_cn))

                enriched_data = self.llm.enrich_rig_knowledge(
                    name_cn, name_en, category, wiki_content
                )

            # 入库
            rig_id = self._save_to_database(name_cn, name_en, category, enriched_data)

            # 更新状态为完成
            self.db.execute_write("""
                UPDATE rig_fetch_progress
                SET status = ?, rig_id = ?, updated_at = ?
                WHERE name_cn = ?
            """, (FetchStatus.COMPLETED, rig_id, datetime.now().isoformat(), name_cn))

            logger.info(f"采集完成: {name_cn}, rig_id={rig_id}")

        except Exception as e:
            logger.error(f"采集失败: {name_cn}, 错误: {e}")
            self.db.execute_write("""
                UPDATE rig_fetch_progress
                SET status = ?, error_message = ?, updated_at = ?
                WHERE name_cn = ?
            """, (FetchStatus.FAILED, str(e), datetime.now().isoformat(), name_cn))

    def _save_to_database(
        self,
        name_cn: str,
        name_en: str,
        category: str,
        enriched_data: Optional[Dict]
    ) -> int:
        """保存数据到数据库"""
        now = datetime.now().isoformat()
        data = enriched_data or {}

        # 插入 rig_types 表
        rig_id = self.db.execute_write("""
            INSERT INTO rig_types (
                name, category, description, difficulty,
                target_species, best_conditions, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name_cn,
            category,
            data.get("description", ""),
            data.get("difficulty", "medium"),
            json.dumps(data.get("target_species", []), ensure_ascii=False),
            data.get("best_conditions", ""),
            now, now
        ))

        # 插入组件
        for comp in data.get("components", []):
            self.db.execute_write("""
                INSERT INTO rig_components (
                    rig_id, component_name, component_type, quantity,
                    size, position, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rig_id,
                comp.get("name", ""),
                comp.get("type", ""),
                comp.get("quantity", 1),
                comp.get("spec", ""),
                comp.get("position", 0),
                comp.get("notes", ""),
                now, now
            ))

        # 插入规格
        for spec in data.get("specs", []):
            self.db.execute_write("""
                INSERT INTO rig_specs (
                    rig_id, spec_name, spec_value, unit, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rig_id,
                spec.get("name", ""),
                spec.get("value", ""),
                spec.get("unit", ""),
                spec.get("notes", ""),
                now, now
            ))

        # 额外信息存储到 rig_types 的 best_conditions 字段（JSON 格式扩展）
        extra_info = {
            "assembly_steps": data.get("assembly_steps", []),
            "usage_tips": data.get("usage_tips", []),
            "pros": data.get("pros", []),
            "cons": data.get("cons", []),
            "recommended_lures": data.get("recommended_lures", []),
            "name_en": name_en
        }
        self.db.execute_write("""
            UPDATE rig_types
            SET best_conditions = ?
            WHERE rig_id = ?
        """, (json.dumps(extra_info, ensure_ascii=False), rig_id))

        return rig_id


# 全局服务实例
_rig_fetcher_service: Optional[RigFetcherService] = None


def get_rig_fetcher_service() -> RigFetcherService:
    """获取钓组采集服务单例"""
    global _rig_fetcher_service
    if _rig_fetcher_service is None:
        _rig_fetcher_service = RigFetcherService()
    return _rig_fetcher_service
