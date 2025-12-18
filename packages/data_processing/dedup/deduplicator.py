"""
装备数据去重器

提供多策略去重检测，避免重复入库。
"""

import logging
from difflib import SequenceMatcher
from typing import Optional

from .base_spider import EquipmentData
from ..lure.database import LureDatabase

logger = logging.getLogger(__name__)


class EquipmentDeduplicator:
    """装备去重器"""

    def __init__(self, db: LureDatabase):
        """
        初始化去重器

        Args:
            db: 数据库实例
        """
        self.db = db
        logger.info("初始化装备去重器")

    def find_duplicates(self, equipment: EquipmentData) -> Optional[int]:
        """
        查找重复装备

        去重规则（按优先级）：
        1. 精确匹配：brand_name + model
        2. 模糊匹配：brand_name + name（相似度>80%）
        3. 规格匹配：category + 关键规格

        Args:
            equipment: 装备数据

        Returns:
            如果找到重复，返回existing equipment_id；否则返回None
        """
        # ========== 策略1: 精确匹配（brand + model） ==========
        if equipment.model:
            exact_match = self._find_exact_match(equipment)
            if exact_match:
                logger.info(
                    f"精确匹配找到重复: {equipment.brand_name} {equipment.model} "
                    f"(ID: {exact_match})"
                )
                return exact_match

        # ========== 策略2: 模糊匹配（brand + name） ==========
        fuzzy_match = self._find_fuzzy_match(equipment)
        if fuzzy_match:
            logger.info(
                f"模糊匹配找到重复: {equipment.brand_name} {equipment.name} "
                f"(ID: {fuzzy_match})"
            )
            return fuzzy_match

        # ========== 策略3: 规格匹配（category + specs） ==========
        spec_match = self._find_spec_match(equipment)
        if spec_match:
            logger.info(
                f"规格匹配找到重复: {equipment.category} (ID: {spec_match})"
            )
            return spec_match

        # 未找到重复
        logger.debug(f"未找到重复装备: {equipment.brand_name} {equipment.name}")
        return None

    def _find_exact_match(self, equipment: EquipmentData) -> Optional[int]:
        """
        精确匹配：brand_name + model

        Args:
            equipment: 装备数据

        Returns:
            匹配的equipment_id或None
        """
        if not equipment.model:
            return None

        query = """
        SELECT e.equipment_id
        FROM equipment e
        JOIN brands b ON e.brand_id = b.id
        WHERE b.name_cn = ? AND e.model = ?
        LIMIT 1
        """

        rows = self.db.execute(query, (equipment.brand_name, equipment.model))
        if rows:
            return rows[0]["equipment_id"]
        return None

    def _find_fuzzy_match(
        self, equipment: EquipmentData, similarity_threshold: float = 0.80
    ) -> Optional[int]:
        """
        模糊匹配：brand_name + name（相似度阈值）

        Args:
            equipment: 装备数据
            similarity_threshold: 相似度阈值（0-1），默认0.80

        Returns:
            匹配的equipment_id或None
        """
        query = """
        SELECT e.equipment_id, e.name AS equipment_name
        FROM equipment e
        JOIN brands b ON e.brand_id = b.id
        WHERE b.name_cn = ? AND e.category = ?
        """

        rows = self.db.execute(query, (equipment.brand_name, equipment.category))

        # 计算每个候选装备的相似度
        best_match = None
        best_similarity = 0.0

        for row in rows:
            existing_name = row["equipment_name"]
            similarity = SequenceMatcher(
                None, equipment.name.lower(), existing_name.lower()
            ).ratio()

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = row["equipment_id"]

        # 检查是否超过阈值
        if best_similarity >= similarity_threshold:
            logger.debug(
                f"模糊匹配相似度: {best_similarity:.2%} "
                f"(阈值: {similarity_threshold:.2%})"
            )
            return best_match

        return None

    def _find_spec_match(self, equipment: EquipmentData) -> Optional[int]:
        """
        规格匹配：根据装备类别匹配关键规格

        Args:
            equipment: 装备数据

        Returns:
            匹配的equipment_id或None
        """
        if not equipment.specs:
            return None

        # 根据装备类别选择匹配策略
        if equipment.category == "鱼竿":
            return self._match_rod_specs(equipment)
        elif equipment.category == "渔轮":
            return self._match_reel_specs(equipment)
        elif equipment.category == "鱼线":
            return self._match_line_specs(equipment)
        elif equipment.category == "拟饵":
            return self._match_lure_specs(equipment)

        return None

    def _match_rod_specs(self, equipment: EquipmentData) -> Optional[int]:
        """
        鱼竿规格匹配：长度 + 硬度 + 调性

        Args:
            equipment: 装备数据

        Returns:
            匹配的equipment_id或None
        """
        specs = equipment.specs
        length = specs.get("length")
        hardness = specs.get("hardness")
        action = specs.get("action")

        if not (length and hardness):
            return None

        # 查询相同规格的鱼竿
        query = """
        SELECT rs.equipment_id
        FROM rod_specs rs
        JOIN equipment e ON rs.equipment_id = e.equipment_id
        JOIN brands b ON e.brand_id = b.id
        WHERE b.name_cn = ?
          AND rs.length = ?
          AND rs.hardness = ?
        """

        params = [equipment.brand_name, length, hardness]

        # 如果有调性，加入条件
        if action:
            query += " AND rs.action = ?"
            params.append(action)

        query += " LIMIT 1"

        rows = self.db.execute(query, params)
        if rows:
            return rows[0]["equipment_id"]
        return None

    def _match_reel_specs(self, equipment: EquipmentData) -> Optional[int]:
        """
        渔轮规格匹配：轮型 + 轴承数 + 速比

        Args:
            equipment: 装备数据

        Returns:
            匹配的equipment_id或None
        """
        specs = equipment.specs
        reel_type = specs.get("reel_type")
        bearings = specs.get("bearings")

        if not reel_type:
            return None

        query = """
        SELECT rl.equipment_id
        FROM reel_specs rl
        JOIN equipment e ON rl.equipment_id = e.equipment_id
        JOIN brands b ON e.brand_id = b.id
        WHERE b.name_cn = ?
          AND rl.reel_type = ?
        """

        params = [equipment.brand_name, reel_type]

        # 如果有轴承数，加入条件
        if bearings:
            query += " AND rl.bearings = ?"
            params.append(bearings)

        query += " LIMIT 1"

        rows = self.db.execute(query, params)
        if rows:
            return rows[0]["equipment_id"]
        return None

    def _match_line_specs(self, equipment: EquipmentData) -> Optional[int]:
        """
        鱼线规格匹配：类型 + 线径 + 强度

        Args:
            equipment: 装备数据

        Returns:
            匹配的equipment_id或None
        """
        specs = equipment.specs
        line_type = specs.get("line_type")
        diameter = specs.get("diameter")

        if not (line_type and diameter):
            return None

        query = """
        SELECT ls.equipment_id
        FROM line_specs ls
        JOIN equipment e ON ls.equipment_id = e.equipment_id
        JOIN brands b ON e.brand_id = b.id
        WHERE b.name_cn = ?
          AND ls.line_type = ?
          AND ls.diameter = ?
        LIMIT 1
        """

        rows = self.db.execute(query, (equipment.brand_name, line_type, diameter))
        if rows:
            return rows[0]["equipment_id"]
        return None

    def _match_lure_specs(self, equipment: EquipmentData) -> Optional[int]:
        """
        拟饵规格匹配：类型 + 重量 + 潜深

        Args:
            equipment: 装备数据

        Returns:
            匹配的equipment_id或None
        """
        specs = equipment.specs
        lure_type = specs.get("lure_type")
        weight = specs.get("weight")

        if not lure_type:
            return None

        query = """
        SELECT lu.equipment_id
        FROM lure_specs lu
        JOIN equipment e ON lu.equipment_id = e.equipment_id
        JOIN brands b ON e.brand_id = b.id
        WHERE b.name_cn = ?
          AND lu.lure_type = ?
        """

        params = [equipment.brand_name, lure_type]

        # 如果有重量，加入条件（允许±0.5g误差）
        if weight:
            query += " AND ABS(lu.weight - ?) <= 0.5"
            params.append(weight)

        query += " LIMIT 1"

        rows = self.db.execute(query, params)
        if rows:
            return rows[0]["equipment_id"]
        return None
