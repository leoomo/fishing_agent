"""
鱼类知识采集服务

从 FishBase API 获取鱼类基础数据，使用 LLM 增强钓鱼相关知识。
支持断点续采、自动跳过已有数据。
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from apps.api.database import get_db

logger = logging.getLogger(__name__)

# 预设鱼种列表
FISH_SPECIES_LIST = [
    # 鲈形目 - 路亚主要目标
    "大嘴鲈", "小嘴鲈", "加州鲈",
    "鳜鱼", "斑鳜", "大眼鳜",

    # 鲤形目 - 鲌亚科
    "翘嘴鲌", "蒙古鲌", "拟尖头鲌", "红鳍鲌",

    # 鲤形目 - 其他掠食性
    "鳡鱼", "马口鱼", "宽鳍鱲",

    # 鳢科
    "黑鱼", "斑鳢", "七星鳢", "月鳢",

    # 鲶形目
    "鲶鱼", "大口鲶", "黄颡鱼", "长吻鮠",

    # 鲤形目 - 常见鱼种
    "鲤鱼", "草鱼", "鲫鱼", "青鱼", "鳊鱼", "鲢鱼", "鳙鱼",

    # 鲴类
    "红尾鲴", "青梢鲴", "银鲴",

    # 鳟鲑类
    "虹鳟", "金鳟", "褐鳟",

    # 海水/咸淡水
    "鲈鱼", "海鲈", "黄鳍鲷", "黑鲷", "真鲷",
    "石斑鱼", "青石斑", "红斑",
    "金枪鱼", "鲣鱼", "鲅鱼",

    # 其他
    "罗非鱼", "太阳鱼", "白条",
]

# 采集状态
class FetchStatus:
    PENDING = "pending"
    FETCHING = "fetching"
    ENRICHING = "enriching"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FishBaseFetcher:
    """FishBase API 客户端"""

    BASE_URL = "https://fishbase.ropensci.org"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FishingAgent/1.0",
            "Accept": "application/json"
        })

    def search_by_chinese_name(self, name_cn: str) -> Optional[Dict[str, Any]]:
        """通过中文名搜索鱼种"""
        try:
            # 搜索通用名称
            response = self.session.get(
                f"{self.BASE_URL}/comnames",
                params={"ComName": name_cn, "limit": 10},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("data"):
                logger.warning(f"FishBase 未找到: {name_cn}")
                return None

            # 获取第一个匹配的 SpecCode
            spec_code = data["data"][0].get("SpecCode")
            if not spec_code:
                return None

            # 获取物种详情
            return self.get_species_detail(spec_code)

        except requests.RequestException as e:
            logger.error(f"FishBase API 请求失败: {name_cn}, 错误: {e}")
            return None

    def get_species_detail(self, spec_code: int) -> Optional[Dict[str, Any]]:
        """获取物种详情"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/species",
                params={"SpecCode": spec_code},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get("data"):
                species_data = data["data"][0]

                # 尝试获取生态信息
                ecology = self._get_ecology(spec_code)
                if ecology:
                    species_data["ecology"] = ecology

                return species_data

            return None

        except requests.RequestException as e:
            logger.error(f"获取物种详情失败: SpecCode={spec_code}, 错误: {e}")
            return None

    def _get_ecology(self, spec_code: int) -> Optional[Dict[str, Any]]:
        """获取生态信息"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/ecology",
                params={"SpecCode": spec_code},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [{}])[0] if data.get("data") else None
        except Exception:
            return None


class LLMEnricher:
    """LLM 增强服务 - 生成钓鱼相关知识"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def enrich_fish_knowledge(self, name_cn: str, fishbase_data: Optional[Dict] = None) -> Dict[str, Any]:
        """使用 LLM 增强鱼类钓鱼知识"""
        if not self.api_key:
            logger.warning("未配置 DASHSCOPE_API_KEY，跳过 LLM 增强")
            return self._get_default_knowledge(name_cn)

        try:
            import requests

            # 构建提示词
            context = ""
            if fishbase_data:
                context = f"""
FishBase 数据参考：
- 学名: {fishbase_data.get('Genus', '')} {fishbase_data.get('Species', '')}
- 英文名: {fishbase_data.get('FBname', '')}
- 最大体长: {fishbase_data.get('Length', '')} cm
- 最大体重: {fishbase_data.get('Weight', '')} g
"""

            prompt = f"""你是一位专业的钓鱼专家。请为"{name_cn}"生成详细的钓鱼知识，返回 JSON 格式。

{context}

请返回以下 JSON 格式（不要包含 markdown 代码块标记）：
{{
    "name_en": "英文名",
    "scientific_name": "学名",
    "category": "freshwater/saltwater/brackish",
    "habitat": "栖息环境描述",
    "description": "物种简介（100字以内）",
    "min_weight": 最小常见体重(kg),
    "max_weight": 最大体重(kg),
    "min_length": 最小常见体长(cm),
    "max_length": 最大体长(cm),
    "recommended_lures": ["推荐拟饵1", "推荐拟饵2"],
    "recommended_rigs": ["推荐钓组1", "推荐钓组2"],
    "lure_difficulty": "简单/中等/困难",
    "fight_intensity": "弱/中等/强",
    "season_activity": [
        {{"season": "spring", "activity_level": "高/中/低", "best_time": "最佳时间", "tips": "钓鱼技巧"}},
        {{"season": "summer", "activity_level": "高/中/低", "best_time": "最佳时间", "tips": "钓鱼技巧"}},
        {{"season": "fall", "activity_level": "高/中/低", "best_time": "最佳时间", "tips": "钓鱼技巧"}},
        {{"season": "winter", "activity_level": "高/中/低", "best_time": "最佳时间", "tips": "钓鱼技巧"}}
    ],
    "knowledge": [
        {{"topic": "生活习性", "content": "详细描述"}},
        {{"topic": "钓法技巧", "content": "详细描述"}},
        {{"topic": "饵料选择", "content": "详细描述"}}
    ]
}}

只返回 JSON，不要其他内容。"""

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen-plus",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            # 清理可能的 markdown 代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"LLM 增强失败: {name_cn}, 错误: {e}")
            return self._get_default_knowledge(name_cn)

    def _get_default_knowledge(self, name_cn: str) -> Dict[str, Any]:
        """返回默认知识结构"""
        return {
            "name_en": "",
            "scientific_name": "",
            "category": "freshwater",
            "habitat": "",
            "description": f"{name_cn}是一种常见鱼类。",
            "min_weight": None,
            "max_weight": None,
            "min_length": None,
            "max_length": None,
            "recommended_lures": [],
            "recommended_rigs": [],
            "lure_difficulty": "中等",
            "fight_intensity": "中等",
            "season_activity": [],
            "knowledge": []
        }


class FishFetcherService:
    """鱼类知识采集服务"""

    def __init__(self):
        self.db = get_db()
        self.fishbase = FishBaseFetcher()
        self.llm = LLMEnricher()
        self._is_running = False
        self._should_stop = False
        self._current_task: Optional[threading.Thread] = None

    def get_progress(self) -> Dict[str, Any]:
        """获取采集进度"""
        # 确保进度表已初始化
        self._ensure_progress_initialized()

        rows = self.db.execute("""
            SELECT name_cn, status, species_id, error_message, updated_at
            FROM fish_fetch_progress
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
                "name": row["name_cn"],
                "status": status,
                "species_id": row["species_id"],
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
        # 检查是否已有数据
        count = self.db.execute("SELECT COUNT(*) as cnt FROM fish_fetch_progress")[0]["cnt"]
        if count > 0:
            return

        # 初始化进度表
        now = datetime.now().isoformat()
        for name in FISH_SPECIES_LIST:
            # 检查是否已存在于 fish_species 表
            existing = self.db.execute(
                "SELECT species_id FROM fish_species WHERE name_cn = ?",
                (name,)
            )

            if existing:
                # 已存在，标记为跳过
                self.db.execute_write("""
                    INSERT OR IGNORE INTO fish_fetch_progress
                    (name_cn, status, species_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, FetchStatus.SKIPPED, existing[0]["species_id"], now, now))
            else:
                # 不存在，标记为待采集
                self.db.execute_write("""
                    INSERT OR IGNORE INTO fish_fetch_progress
                    (name_cn, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (name, FetchStatus.PENDING, now, now))

    def start_fetch(self, use_llm: bool = True) -> Dict[str, Any]:
        """开始或继续采集"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        self._ensure_progress_initialized()
        self._should_stop = False
        self._is_running = True

        # 在后台线程中执行采集
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
            # 重试指定的项目
            for name in names:
                self.db.execute_write("""
                    UPDATE fish_fetch_progress
                    SET status = ?, error_message = NULL, updated_at = ?
                    WHERE name_cn = ? AND status = ?
                """, (FetchStatus.PENDING, now, name, FetchStatus.FAILED))
        else:
            # 重试所有失败的项目
            self.db.execute_write("""
                UPDATE fish_fetch_progress
                SET status = ?, error_message = NULL, updated_at = ?
                WHERE status = ?
            """, (FetchStatus.PENDING, now, FetchStatus.FAILED))

        return {"success": True, "message": "已重置失败项目"}

    def reset_all(self) -> Dict[str, Any]:
        """重置所有进度"""
        if self._is_running:
            return {"success": False, "message": "采集任务正在运行中"}

        self.db.execute_write("DELETE FROM fish_fetch_progress")
        self._ensure_progress_initialized()

        return {"success": True, "message": "已重置所有进度"}

    def _fetch_worker(self, use_llm: bool):
        """采集工作线程"""
        try:
            while not self._should_stop:
                # 获取下一个待采集的项目
                pending = self.db.execute("""
                    SELECT name_cn FROM fish_fetch_progress
                    WHERE status = ?
                    ORDER BY id
                    LIMIT 1
                """, (FetchStatus.PENDING,))

                if not pending:
                    logger.info("所有项目已采集完成")
                    break

                name_cn = pending[0]["name_cn"]
                self._fetch_single(name_cn, use_llm)

                # 短暂延迟，避免请求过快
                time.sleep(1)

        except Exception as e:
            logger.error(f"采集工作线程异常: {e}")
        finally:
            self._is_running = False
            self._should_stop = False

    def _fetch_single(self, name_cn: str, use_llm: bool):
        """采集单个鱼种"""
        now = datetime.now().isoformat()

        try:
            # 更新状态为采集中
            self.db.execute_write("""
                UPDATE fish_fetch_progress
                SET status = ?, updated_at = ?
                WHERE name_cn = ?
            """, (FetchStatus.FETCHING, now, name_cn))

            # 从 FishBase 获取数据
            fishbase_data = self.fishbase.search_by_chinese_name(name_cn)

            # 保存 FishBase 原始数据
            self.db.execute_write("""
                UPDATE fish_fetch_progress
                SET fishbase_data = ?, updated_at = ?
                WHERE name_cn = ?
            """, (json.dumps(fishbase_data, ensure_ascii=False) if fishbase_data else None, now, name_cn))

            # LLM 增强
            enriched_data = None
            if use_llm:
                self.db.execute_write("""
                    UPDATE fish_fetch_progress
                    SET status = ?, updated_at = ?
                    WHERE name_cn = ?
                """, (FetchStatus.ENRICHING, now, name_cn))

                enriched_data = self.llm.enrich_fish_knowledge(name_cn, fishbase_data)

            # 入库
            species_id = self._save_to_database(name_cn, fishbase_data, enriched_data)

            # 更新状态为完成
            self.db.execute_write("""
                UPDATE fish_fetch_progress
                SET status = ?, species_id = ?, updated_at = ?
                WHERE name_cn = ?
            """, (FetchStatus.COMPLETED, species_id, datetime.now().isoformat(), name_cn))

            logger.info(f"采集完成: {name_cn}, species_id={species_id}")

        except Exception as e:
            logger.error(f"采集失败: {name_cn}, 错误: {e}")
            self.db.execute_write("""
                UPDATE fish_fetch_progress
                SET status = ?, error_message = ?, updated_at = ?
                WHERE name_cn = ?
            """, (FetchStatus.FAILED, str(e), datetime.now().isoformat(), name_cn))

    def _save_to_database(self, name_cn: str, fishbase_data: Optional[Dict], enriched_data: Optional[Dict]) -> int:
        """保存数据到数据库"""
        now = datetime.now().isoformat()

        # 合并数据
        data = enriched_data or {}

        # 从 FishBase 数据补充
        if fishbase_data:
            if not data.get("name_en"):
                data["name_en"] = fishbase_data.get("FBname", "")
            if not data.get("scientific_name"):
                genus = fishbase_data.get("Genus", "")
                species = fishbase_data.get("Species", "")
                data["scientific_name"] = f"{genus} {species}".strip()
            if not data.get("max_length") and fishbase_data.get("Length"):
                data["max_length"] = fishbase_data.get("Length")
            if not data.get("max_weight") and fishbase_data.get("Weight"):
                # FishBase 返回的是克，转换为千克
                weight_g = fishbase_data.get("Weight")
                if weight_g:
                    data["max_weight"] = weight_g / 1000

        # 插入 fish_species 表（匹配实际表结构）
        species_id = self.db.execute_write("""
            INSERT INTO fish_species (
                name_cn, name_en, scientific_name, category, habitat,
                description, image_url,
                min_weight, max_weight, min_length, max_length,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name_cn,
            data.get("name_en", ""),
            data.get("scientific_name", ""),
            data.get("category", "freshwater"),
            data.get("habitat", ""),
            data.get("description", ""),
            data.get("image_url", ""),
            data.get("min_weight"),
            data.get("max_weight"),
            data.get("min_length"),
            data.get("max_length"),
            now, now
        ))

        # 插入季节活动（匹配实际表结构）
        for activity in data.get("season_activity", []):
            # 转换活跃度为英文枚举名称
            activity_level = activity.get("activity_level", "中")
            activity_level_map = {"高": "HIGH", "中": "MEDIUM", "低": "LOW"}
            activity_level_enum = activity_level_map.get(activity_level, "MEDIUM")

            self.db.execute_write("""
                INSERT INTO fish_season_activity (
                    species_id, season, activity_level, best_time,
                    recommended_lures, fishing_tips, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                species_id,
                activity.get("season", ""),
                activity_level_enum,
                activity.get("best_time", ""),
                activity.get("recommended_lures", ""),
                activity.get("fishing_tips", ""),
                now, now
            ))

        # 插入知识条目（匹配实际表结构）
        for knowledge in data.get("knowledge", []):
            self.db.execute_write("""
                INSERT INTO fish_knowledge (
                    species_id, topic, content, source, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                species_id,
                knowledge.get("topic", ""),
                knowledge.get("content", ""),
                knowledge.get("source", "FishBase + LLM"),
                knowledge.get("tags", ""),
                now, now
            ))

        return species_id

    def _activity_level_to_int(self, level: str) -> int:
        """活跃度转换为数字"""
        mapping = {"低": 1, "中": 2, "中等": 2, "高": 3}
        return mapping.get(level, 2)


# 全局服务实例
_fish_fetcher_service: Optional[FishFetcherService] = None


def get_fish_fetcher_service() -> FishFetcherService:
    """获取鱼类采集服务单例"""
    global _fish_fetcher_service
    if _fish_fetcher_service is None:
        _fish_fetcher_service = FishFetcherService()
    return _fish_fetcher_service
