"""
用户装备管理器

提供用户装备库的CRUD操作和统计分析功能。
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..lure.database import LureDatabase

logger = logging.getLogger(__name__)


@dataclass
class UserEquipment:
    """用户装备数据类"""

    id: int
    user_id: int
    equipment_id: int
    equipment_name: str
    category: str
    brand_name: Optional[str]
    model: Optional[str]
    purchase_date: Optional[str]
    purchase_price: Optional[float]
    purchase_source: Optional[str]
    condition: str
    usage_frequency: Optional[str]
    notes: Optional[str]
    is_favorite: bool
    tags: Optional[str]
    created_at: str


class UserEquipmentManager:
    """用户装备管理器"""

    def __init__(self, db: LureDatabase):
        """
        初始化用户装备管理器

        Args:
            db: 数据库实例
        """
        self.db = db
        logger.info("初始化用户装备管理器")

    # ========== 用户管理 ==========

    def create_user(
        self,
        username: str,
        nickname: Optional[str] = None,
        email: Optional[str] = None,
        user_level: str = "新手",
        fishing_experience_years: Optional[int] = None,
        preferred_fish: Optional[str] = None,
    ) -> int:
        """
        创建用户

        Args:
            username: 用户名（唯一）
            nickname: 昵称
            email: 邮箱
            user_level: 用户水平（新手/进阶/高手）
            fishing_experience_years: 钓龄（年）
            preferred_fish: 偏好鱼种

        Returns:
            用户ID

        Raises:
            ValueError: 如果用户名已存在
        """
        # 检查用户名是否已存在
        existing = self.db.execute(
            "SELECT user_id FROM users WHERE username = ?", (username,)
        )
        if existing:
            raise ValueError(f"用户名已存在: {username}")

        # 插入用户
        insert_query = """
        INSERT INTO users (
            username, nickname, email, user_level,
            fishing_experience_years, preferred_fish
        ) VALUES (?, ?, ?, ?, ?, ?)
        """

        user_id = self.db.execute_write(
            insert_query,
            (username, nickname, email, user_level, fishing_experience_years, preferred_fish),
        )

        logger.info(f"创建用户成功: {username} (ID:{user_id})")
        return user_id

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，不存在返回None
        """
        query = "SELECT * FROM users WHERE user_id = ?"
        rows = self.db.execute(query, (user_id,))
        return rows[0] if rows else None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户信息

        Args:
            username: 用户名

        Returns:
            用户信息字典，不存在返回None
        """
        query = "SELECT * FROM users WHERE username = ?"
        rows = self.db.execute(query, (username,))
        return rows[0] if rows else None

    def update_user(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        user_level: Optional[str] = None,
        fishing_experience_years: Optional[int] = None,
        preferred_fish: Optional[str] = None,
    ) -> bool:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            nickname: 昵称
            user_level: 用户水平
            fishing_experience_years: 钓龄
            preferred_fish: 偏好鱼种

        Returns:
            是否更新成功
        """
        # 构建动态更新语句
        updates = []
        params = []

        if nickname is not None:
            updates.append("nickname = ?")
            params.append(nickname)

        if user_level is not None:
            updates.append("user_level = ?")
            params.append(user_level)

        if fishing_experience_years is not None:
            updates.append("fishing_experience_years = ?")
            params.append(fishing_experience_years)

        if preferred_fish is not None:
            updates.append("preferred_fish = ?")
            params.append(preferred_fish)

        if not updates:
            logger.warning("没有字段需要更新")
            return False

        # 添加updated_at
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        # 添加user_id
        params.append(user_id)

        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        affected = self.db.execute_write(query, tuple(params))

        logger.info(f"更新用户信息: user_id={user_id}")
        return affected > 0

    # ========== 装备管理 ==========

    def add_equipment(
        self,
        user_id: int,
        equipment_id: int,
        purchase_price: Optional[float] = None,
        purchase_date: Optional[str] = None,
        purchase_source: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[int]:
        """
        添加装备到用户库

        Args:
            user_id: 用户ID
            equipment_id: 装备ID
            purchase_price: 购买价格
            purchase_date: 购买日期
            purchase_source: 购买渠道
            notes: 备注
            tags: 标签列表

        Returns:
            user_equipment表的记录ID

        Raises:
            ValueError: 如果装备不存在或已添加
        """
        # 1. 检查装备是否存在
        equipment = self.db.execute(
            "SELECT equipment_id FROM equipment WHERE equipment_id = ?",
            (equipment_id,),
        )
        if not equipment:
            raise ValueError(f"装备不存在: equipment_id={equipment_id}")

        # 2. 检查是否已添加（UNIQUE约束会自动检查，但这里提供更友好的错误信息）
        existing = self.db.execute(
            "SELECT id FROM user_equipment WHERE user_id = ? AND equipment_id = ?",
            (user_id, equipment_id),
        )
        if existing:
            raise ValueError(f"装备已在装备库中: equipment_id={equipment_id}")

        # 3. 插入user_equipment表
        insert_query = """
        INSERT INTO user_equipment (
            user_id, equipment_id, purchase_date, purchase_price,
            purchase_source, notes, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        # 标签转JSON字符串
        import json
        tags_json = json.dumps(tags, ensure_ascii=False) if tags else None

        record_id = self.db.execute_write(
            insert_query,
            (
                user_id,
                equipment_id,
                purchase_date,
                purchase_price,
                purchase_source,
                notes,
                tags_json,
            ),
        )

        logger.info(f"添加装备到用户库: user_id={user_id}, equipment_id={equipment_id}")
        return record_id

    def remove_equipment(self, user_id: int, equipment_id: int) -> bool:
        """
        从装备库删除装备

        Args:
            user_id: 用户ID
            equipment_id: 装备ID

        Returns:
            是否删除成功
        """
        query = "DELETE FROM user_equipment WHERE user_id = ? AND equipment_id = ?"
        affected = self.db.execute_write(query, (user_id, equipment_id))

        if affected > 0:
            logger.info(f"删除装备: user_id={user_id}, equipment_id={equipment_id}")
            return True
        else:
            logger.warning(
                f"装备不在用户库中: user_id={user_id}, equipment_id={equipment_id}"
            )
            return False

    def list_user_equipment(
        self,
        user_id: int,
        category: Optional[str] = None,
        only_favorites: bool = False,
    ) -> List[UserEquipment]:
        """
        查询用户装备列表

        Args:
            user_id: 用户ID
            category: 装备类别过滤（可选）
            only_favorites: 只显示收藏装备

        Returns:
            用户装备列表
        """
        # 构建查询（JOIN equipment和brands表获取完整信息）
        query = """
        SELECT
            ue.id,
            ue.user_id,
            ue.equipment_id,
            e.name AS equipment_name,
            e.category,
            b.name_cn AS brand_name,
            e.model,
            ue.purchase_date,
            ue.purchase_price,
            ue.purchase_source,
            ue.condition,
            ue.usage_frequency,
            ue.notes,
            ue.is_favorite,
            ue.tags,
            ue.created_at
        FROM user_equipment ue
        JOIN equipment e ON ue.equipment_id = e.equipment_id
        LEFT JOIN brands b ON e.brand_id = b.id
        WHERE ue.user_id = ?
        """

        params = [user_id]

        # 类别过滤
        if category:
            query += " AND e.category = ?"
            params.append(category)

        # 收藏过滤
        if only_favorites:
            query += " AND ue.is_favorite = 1"

        # 排序
        query += " ORDER BY ue.created_at DESC"

        rows = self.db.execute(query, tuple(params))

        # 转换为UserEquipment对象
        equipment_list = []
        for row in rows:
            equipment_list.append(
                UserEquipment(
                    id=row["id"],
                    user_id=row["user_id"],
                    equipment_id=row["equipment_id"],
                    equipment_name=row["equipment_name"],
                    category=row["category"],
                    brand_name=row.get("brand_name"),
                    model=row.get("model"),
                    purchase_date=row.get("purchase_date"),
                    purchase_price=row.get("purchase_price"),
                    purchase_source=row.get("purchase_source"),
                    condition=row.get("condition", "正常"),
                    usage_frequency=row.get("usage_frequency"),
                    notes=row.get("notes"),
                    is_favorite=bool(row.get("is_favorite", 0)),
                    tags=row.get("tags"),
                    created_at=row["created_at"],
                )
            )

        logger.info(f"查询用户装备: user_id={user_id}, 数量={len(equipment_list)}")
        return equipment_list

    def toggle_favorite(self, user_id: int, equipment_id: int) -> bool:
        """
        切换收藏状态

        Args:
            user_id: 用户ID
            equipment_id: 装备ID

        Returns:
            是否操作成功
        """
        query = """
        UPDATE user_equipment
        SET is_favorite = 1 - is_favorite,
            updated_at = ?
        WHERE user_id = ? AND equipment_id = ?
        """

        affected = self.db.execute_write(
            query, (datetime.now().isoformat(), user_id, equipment_id)
        )

        if affected > 0:
            logger.info(f"切换收藏状态: user_id={user_id}, equipment_id={equipment_id}")
            return True
        return False

    def update_equipment_notes(
        self, user_id: int, equipment_id: int, notes: str
    ) -> bool:
        """
        更新装备备注

        Args:
            user_id: 用户ID
            equipment_id: 装备ID
            notes: 备注内容

        Returns:
            是否更新成功
        """
        query = """
        UPDATE user_equipment
        SET notes = ?,
            updated_at = ?
        WHERE user_id = ? AND equipment_id = ?
        """

        affected = self.db.execute_write(
            query, (notes, datetime.now().isoformat(), user_id, equipment_id)
        )

        return affected > 0

    # ========== 统计分析 ==========

    def get_equipment_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户装备统计

        Args:
            user_id: 用户ID

        Returns:
            统计信息字典
        """
        # 按类别统计
        category_stats = self._get_category_stats(user_id)

        # 总花费
        total_spent = self._get_total_spent(user_id)

        # 装备总数
        total_count = sum(stat["count"] for stat in category_stats)

        # 收藏数
        favorite_count = self._get_favorite_count(user_id)

        stats = {
            "user_id": user_id,
            "total_count": total_count,
            "total_spent": total_spent,
            "favorite_count": favorite_count,
            "by_category": category_stats,
        }

        logger.info(f"装备统计: user_id={user_id}, 总数={total_count}")
        return stats

    def _get_category_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """按类别统计"""
        query = """
        SELECT
            e.category,
            COUNT(*) AS count,
            AVG(ue.purchase_price) AS avg_price,
            SUM(ue.purchase_price) AS total_price
        FROM user_equipment ue
        JOIN equipment e ON ue.equipment_id = e.equipment_id
        WHERE ue.user_id = ?
        GROUP BY e.category
        ORDER BY count DESC
        """

        rows = self.db.execute(query, (user_id,))
        return [dict(row) for row in rows]

    def _get_total_spent(self, user_id: int) -> float:
        """计算总花费"""
        query = """
        SELECT SUM(purchase_price) AS total
        FROM user_equipment
        WHERE user_id = ? AND purchase_price IS NOT NULL
        """

        rows = self.db.execute(query, (user_id,))
        total = rows[0]["total"] if rows and rows[0]["total"] else 0.0
        return float(total)

    def _get_favorite_count(self, user_id: int) -> int:
        """统计收藏数"""
        query = """
        SELECT COUNT(*) AS count
        FROM user_equipment
        WHERE user_id = ? AND is_favorite = 1
        """

        rows = self.db.execute(query, (user_id,))
        return rows[0]["count"] if rows else 0

    def get_missing_equipment_types(self, user_id: int) -> List[str]:
        """
        分析缺失的装备类型

        Args:
            user_id: 用户ID

        Returns:
            缺失的装备类别列表
        """
        # 获取用户已有装备类别
        query = """
        SELECT DISTINCT e.category
        FROM user_equipment ue
        JOIN equipment e ON ue.equipment_id = e.equipment_id
        WHERE ue.user_id = ?
        """

        rows = self.db.execute(query, (user_id,))
        owned_categories = {row["category"] for row in rows}

        # 基础装备类别
        required_categories = {"鱼竿", "渔轮", "鱼线"}

        # 计算缺失
        missing = list(required_categories - owned_categories)

        logger.info(f"缺失装备类型: user_id={user_id}, 缺失={missing}")
        return missing

    def get_equipment_brands(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户装备的品牌分布

        Args:
            user_id: 用户ID

        Returns:
            品牌统计列表
        """
        query = """
        SELECT
            b.name_cn AS brand_name,
            COUNT(*) AS count
        FROM user_equipment ue
        JOIN equipment e ON ue.equipment_id = e.equipment_id
        LEFT JOIN brands b ON e.brand_id = b.id
        WHERE ue.user_id = ?
        GROUP BY b.name_cn
        ORDER BY count DESC
        """

        rows = self.db.execute(query, (user_id,))
        return [dict(row) for row in rows]
