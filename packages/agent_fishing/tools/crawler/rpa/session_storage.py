"""
Session 持久化管理
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionStorage:
    """Session 持久化存储"""

    def __init__(self, storage_path: str):
        """
        初始化

        Args:
            storage_path: Cookie 文件路径
        """
        self.storage_path = Path(storage_path)

        # 确保父目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"初始化 SessionStorage: {self.storage_path}")

    def exists(self) -> bool:
        """检查 Session 文件是否存在"""
        return self.storage_path.exists()

    def save(self, session_data: Dict):
        """
        保存 Session 数据

        Args:
            session_data: Session 数据字典
                {
                    "account": "user@example.com",
                    "cookies": [...],
                    "created_at": "2025-12-04T19:00:00",
                    "last_used": "2025-12-04T20:30:00",
                    "is_valid": true
                }
        """
        try:
            # 添加时间戳
            session_data["last_used"] = datetime.now().isoformat()

            if "created_at" not in session_data:
                session_data["created_at"] = datetime.now().isoformat()

            # 写入文件
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Session 已保存: {self.storage_path}")

        except Exception as e:
            logger.error(f"保存 Session 失败: {e}", exc_info=True)
            raise

    def load(self) -> Optional[Dict]:
        """
        加载 Session 数据

        Returns:
            Session 数据字典，如果文件不存在或损坏则返回 None
        """
        if not self.exists():
            logger.warning(f"Session 文件不存在: {self.storage_path}")
            return None

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            logger.info(f"Session 已加载: {self.storage_path}")
            return session_data

        except json.JSONDecodeError as e:
            logger.error(f"Session 文件格式错误: {e}")
            return None
        except Exception as e:
            logger.error(f"加载 Session 失败: {e}", exc_info=True)
            return None

    def delete(self):
        """删除 Session 文件"""
        try:
            if self.exists():
                self.storage_path.unlink()
                logger.info(f"Session 文件已删除: {self.storage_path}")
            else:
                logger.warning(f"Session 文件不存在，无法删除: {self.storage_path}")

        except Exception as e:
            logger.error(f"删除 Session 文件失败: {e}", exc_info=True)
            raise

    def mark_invalid(self):
        """标记 Session 为无效"""
        session_data = self.load()
        if session_data:
            session_data["is_valid"] = False
            self.save(session_data)
            logger.info("Session 已标记为无效")

    def get_cookies(self) -> Optional[List[Dict]]:
        """
        获取 Cookie 列表

        Returns:
            Cookie 列表或 None
        """
        session_data = self.load()
        if session_data and "cookies" in session_data:
            return session_data["cookies"]
        return None

    def is_valid(self) -> bool:
        """
        检查 Session 是否有效

        Returns:
            是否有效
        """
        session_data = self.load()
        if not session_data:
            return False

        return session_data.get("is_valid", False)
