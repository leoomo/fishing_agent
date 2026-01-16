"""
文章网络采集服务

从 Wikipedia API 获取钓鱼相关文章内容，使用 LLM 翻译和增强内容。
采集的文章进入草稿状态待审核。

参考实现：apps/api/services/rig_fetcher.py
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


# 预设钓鱼相关词条列表
WIKI_ARTICLES = [
    # 钓鱼基础
    {"title": "Fishing", "name_cn": "钓鱼概述", "type": "strategy"},
    {"title": "Angling", "name_cn": "垂钓", "type": "strategy"},
    {"title": "Sport_fishing", "name_cn": "运动钓鱼", "type": "strategy"},
    {"title": "Recreational_fishing", "name_cn": "休闲钓鱼", "type": "strategy"},

    # 钓法类型
    {"title": "Fly_fishing", "name_cn": "飞蝇钓", "type": "tips"},
    {"title": "Spin_fishing", "name_cn": "路亚钓", "type": "tips"},
    {"title": "Bait_fishing", "name_cn": "活饵钓", "type": "tips"},
    {"title": "Ice_fishing", "name_cn": "冰钓", "type": "tips"},
    {"title": "Surf_fishing", "name_cn": "海岸钓", "type": "tips"},
    {"title": "Trolling_(fishing)", "name_cn": "拖钓", "type": "tips"},
    {"title": "Jigging", "name_cn": "铁板钓", "type": "tips"},
    {"title": "Bottom_fishing", "name_cn": "底钓", "type": "tips"},

    # 对象鱼钓法
    {"title": "Bass_fishing", "name_cn": "鲈鱼钓法", "type": "strategy"},
    {"title": "Carp_fishing", "name_cn": "鲤鱼钓法", "type": "strategy"},
    {"title": "Trout_fishing", "name_cn": "鳟鱼钓法", "type": "strategy"},
    {"title": "Salmon_fishing", "name_cn": "三文鱼钓法", "type": "strategy"},
    {"title": "Catfish", "name_cn": "鲶鱼", "type": "strategy"},

    # 钓鱼理念与实践
    {"title": "Catch_and_release", "name_cn": "钓后放流", "type": "tips"},
    {"title": "Fish_hook", "name_cn": "鱼钩介绍", "type": "review"},
    {"title": "Fishing_bait", "name_cn": "鱼饵选择", "type": "tips"},

    # 装备类
    {"title": "Fishing_tackle", "name_cn": "钓具介绍", "type": "review"},
    {"title": "Fishing_rod", "name_cn": "鱼竿", "type": "review"},
    {"title": "Fishing_reel", "name_cn": "渔轮", "type": "review"},
    {"title": "Fishing_line", "name_cn": "鱼线", "type": "review"},
    {"title": "Fishing_lure", "name_cn": "拟饵", "type": "review"},
    {"title": "Fishing_float", "name_cn": "浮漂", "type": "review"},
    {"title": "Fishing_sinker", "name_cn": "铅坠", "type": "review"},
    {"title": "Fishing_net", "name_cn": "渔网", "type": "review"},

    # 钓点环境
    {"title": "Fishing_spot", "name_cn": "钓点选择", "type": "spot"},
    {"title": "Fishery", "name_cn": "渔场", "type": "spot"},
]


class FetchStatus:
    """采集状态常量"""
    PENDING = "pending"
    FETCHING = "fetching"
    ENRICHING = "enriching"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WikipediaFetcher:
    """Wikipedia API 客户端"""

    BASE_URL = "https://en.wikipedia.org/api/rest_v1"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FishingAgent/1.0 (https://github.com/fishing-agent; contact@example.com)",
            "Accept": "application/json"
        })

    def get_page_extract(self, title: str) -> Optional[str]:
        """获取页面文本内容（使用 MediaWiki API）"""
        try:
            response = self.session.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": title,
                    "prop": "extracts",
                    "exintro": False,
                    "explaintext": True,
                    "format": "json"
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":
                    extract = page_data.get("extract", "")
                    # 限制长度，避免 token 过多
                    if len(extract) > 5000:
                        extract = extract[:5000] + "..."
                    return extract

            return None

        except requests.RequestException as e:
            logger.error(f"获取 Wikipedia 内容失败: {title}, 错误: {e}")
            return None


class ArticleLLMEnricher:
    """LLM 增强服务 - 翻译和生成文章内容"""

    def __init__(self):
        from apps.api.services.llm_service import LLMService
        self.llm = LLMService(
            provider="qwen",
            model="qwen-plus",
            caller="article_fetcher"
        )

    def enrich_article(
        self,
        name_cn: str,
        wiki_title: str,
        article_type: str,
        wiki_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 LLM 翻译和增强文章内容"""
        context = ""
        if wiki_content:
            context = f"""
以下是 Wikipedia 英文原文内容:
{wiki_content}
"""

        prompt = f"""你是一位专业的钓鱼知识编辑。请基于以下 Wikipedia 内容，生成一篇高质量的中文钓鱼文章。

主题：{name_cn}（{wiki_title}）
文章类型：{article_type}
{context}

请返回以下 JSON 格式（不要包含 markdown 代码块标记）：
{{
    "title": "文章标题（吸引人且准确描述内容，不超过50字）",
    "content": "完整的 Markdown 格式文章内容（2000-4000字，包含标题、分段、要点等）",
    "summary": "文章摘要（100-200字，概括核心内容）",
    "tags": "标签1,标签2,标签3,标签4（4-6个相关标签，逗号分隔）"
}}

要求：
1. 内容必须是中文，翻译准确且流畅
2. 保持专业性，同时通俗易懂
3. content 使用 Markdown 格式，包含适当的标题层级(## ###)、列表、重点强调等
4. 根据文章类型调整写作风格：
   - strategy: 完整的攻略指南风格
   - tips: 实用技巧分享风格
   - review: 装备评测分析风格
   - spot: 钓点推荐介绍风格
5. 如果原文信息不足，可以根据你的钓鱼知识适当补充
6. 只返回 JSON，不要其他内容"""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                timeout=120
            )

            if not response.success:
                logger.warning(f"LLM 调用失败: {name_cn}, 错误: {response.error}")
                return self._get_default_article(name_cn, wiki_title, article_type)

            content = response.content.strip()
            # 清理可能的 markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {name_cn}, 错误: {e}")
            return self._get_default_article(name_cn, wiki_title, article_type)
        except Exception as e:
            logger.error(f"LLM 增强失败: {name_cn}, 错误: {e}")
            return self._get_default_article(name_cn, wiki_title, article_type)

    def _get_default_article(self, name_cn: str, wiki_title: str, article_type: str) -> Dict[str, Any]:
        """返回默认文章结构"""
        return {
            "title": name_cn,
            "content": f"# {name_cn}\n\n关于{name_cn}的详细介绍。",
            "summary": f"这是关于{name_cn}的文章。",
            "tags": f"钓鱼,{name_cn}"
        }


class ArticleFetcherService:
    """文章采集服务"""

    def __init__(self):
        self.db = get_db()
        self.wiki = WikipediaFetcher()
        self.llm = ArticleLLMEnricher()
        self._is_running = False
        self._should_stop = False
        self._current_task: Optional[threading.Thread] = None

    def get_sources(self) -> List[Dict[str, Any]]:
        """获取可用数据源列表"""
        return [
            {
                "id": "wikipedia",
                "name": "Wikipedia (钓鱼词条)",
                "description": "从维基百科获取钓鱼相关知识文章",
                "total_items": len(WIKI_ARTICLES),
                "enabled": True
            }
        ]

    def get_progress(self) -> Dict[str, Any]:
        """获取采集进度"""
        self._ensure_progress_initialized()

        rows = self.db.execute("""
            SELECT source_url, title, source_type, status, article_id, error_message, updated_at
            FROM article_fetch_progress
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
                "source_url": row["source_url"],
                "title": row["title"],
                "source_type": row["source_type"],
                "status": status,
                "article_id": row["article_id"],
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
        count = self.db.execute("SELECT COUNT(*) as cnt FROM article_fetch_progress")[0]["cnt"]
        if count > 0:
            return

        now = datetime.now().isoformat()
        for article in WIKI_ARTICLES:
            source_url = f"https://en.wikipedia.org/wiki/{article['title']}"
            self.db.execute_write("""
                INSERT OR IGNORE INTO article_fetch_progress
                (source_type, source_name, source_url, title, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "wikipedia",
                article["title"],
                source_url,
                article["name_cn"],
                FetchStatus.PENDING,
                now, now
            ))

    def start_fetch(self, source_id: str = "wikipedia", use_llm: bool = True) -> Dict[str, Any]:
        """开始或继续采集"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        if source_id != "wikipedia":
            return {"success": False, "message": f"不支持的数据源: {source_id}"}

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

    def retry_failed(self, urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """重试失败的项目"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        now = datetime.now().isoformat()

        if urls:
            for url in urls:
                self.db.execute_write("""
                    UPDATE article_fetch_progress
                    SET status = ?, error_message = NULL, updated_at = ?
                    WHERE source_url = ? AND status = ?
                """, (FetchStatus.PENDING, now, url, FetchStatus.FAILED))
        else:
            self.db.execute_write("""
                UPDATE article_fetch_progress
                SET status = ?, error_message = NULL, updated_at = ?
                WHERE status = ?
            """, (FetchStatus.PENDING, now, FetchStatus.FAILED))

        return {"success": True, "message": "已重置失败项目"}

    def reset_progress(self) -> Dict[str, Any]:
        """重置所有进度"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        self.db.execute_write("DELETE FROM article_fetch_progress")
        self._ensure_progress_initialized()

        return {"success": True, "message": "已重置所有进度"}

    def _fetch_worker(self, use_llm: bool):
        """采集工作线程"""
        try:
            while not self._should_stop:
                pending = self.db.execute("""
                    SELECT source_url, title, source_name
                    FROM article_fetch_progress
                    WHERE status = ?
                    ORDER BY id
                    LIMIT 1
                """, (FetchStatus.PENDING,))

                if not pending:
                    logger.info("所有文章已采集完成")
                    break

                row = pending[0]
                # 从 WIKI_ARTICLES 获取对应的类型
                article_type = "strategy"  # 默认类型
                for article in WIKI_ARTICLES:
                    if article["title"] == row["source_name"]:
                        article_type = article["type"]
                        break

                self._fetch_single(
                    row["source_url"],
                    row["title"],
                    row["source_name"],
                    article_type,
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
        source_url: str,
        name_cn: str,
        wiki_title: str,
        article_type: str,
        use_llm: bool
    ):
        """采集单个文章"""
        now = datetime.now().isoformat()

        try:
            # 更新状态为采集中
            self.db.execute_write("""
                UPDATE article_fetch_progress
                SET status = ?, updated_at = ?
                WHERE source_url = ?
            """, (FetchStatus.FETCHING, now, source_url))

            # 从 Wikipedia 获取数据
            wiki_content = self.wiki.get_page_extract(wiki_title)
            if wiki_content:
                logger.info(f"获取 Wikipedia 内容成功: {wiki_title}")
            else:
                logger.warning(f"Wikipedia 内容为空: {wiki_title}")

            # 保存 Wikipedia 原始数据
            self.db.execute_write("""
                UPDATE article_fetch_progress
                SET raw_data = ?, updated_at = ?
                WHERE source_url = ?
            """, (wiki_content, datetime.now().isoformat(), source_url))

            # LLM 增强
            enriched_data = None
            if use_llm:
                self.db.execute_write("""
                    UPDATE article_fetch_progress
                    SET status = ?, updated_at = ?
                    WHERE source_url = ?
                """, (FetchStatus.ENRICHING, datetime.now().isoformat(), source_url))

                enriched_data = self.llm.enrich_article(
                    name_cn, wiki_title, article_type, wiki_content
                )

            # 入库
            article_id = self._save_to_database(
                name_cn, wiki_title, article_type, source_url, enriched_data
            )

            # 更新状态为完成
            self.db.execute_write("""
                UPDATE article_fetch_progress
                SET status = ?, article_id = ?, updated_at = ?
                WHERE source_url = ?
            """, (FetchStatus.COMPLETED, article_id, datetime.now().isoformat(), source_url))

            logger.info(f"采集完成: {name_cn}, article_id={article_id}")

        except Exception as e:
            logger.error(f"采集失败: {name_cn}, 错误: {e}")
            self.db.execute_write("""
                UPDATE article_fetch_progress
                SET status = ?, error_message = ?, updated_at = ?
                WHERE source_url = ?
            """, (FetchStatus.FAILED, str(e), datetime.now().isoformat(), source_url))

    def _save_to_database(
        self,
        name_cn: str,
        wiki_title: str,
        article_type: str,
        source_url: str,
        enriched_data: Optional[Dict]
    ) -> int:
        """保存数据到数据库（插入 Article 表）"""
        from apps.api.orm.session import get_db_session
        from apps.api.models.article import Article, ArticleType, ArticleStatus

        data = enriched_data or {}

        # 转换文章类型
        type_mapping = {
            "strategy": ArticleType.STRATEGY,
            "tips": ArticleType.TIPS,
            "review": ArticleType.REVIEW,
            "spot": ArticleType.SPOT
        }
        article_type_enum = type_mapping.get(article_type, ArticleType.STRATEGY)

        # 扩展信息
        extensions = {
            "source": "wikipedia",
            "source_url": source_url,
            "wiki_title": wiki_title,
            "original_name": name_cn
        }

        with get_db_session() as session:
            article = Article(
                title=data.get("title", name_cn),
                content=data.get("content", ""),
                article_type=article_type_enum,
                status=ArticleStatus.DRAFT,  # 采集的文章进入草稿状态
                author_id=None,  # 网络采集无作者
                summary=data.get("summary", ""),
                tags=data.get("tags", ""),
                extensions=json.dumps(extensions, ensure_ascii=False)
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            return article.id


# 全局服务实例
_article_fetcher_service: Optional[ArticleFetcherService] = None


def get_article_fetcher_service() -> ArticleFetcherService:
    """获取文章采集服务单例"""
    global _article_fetcher_service
    if _article_fetcher_service is None:
        _article_fetcher_service = ArticleFetcherService()
    return _article_fetcher_service
