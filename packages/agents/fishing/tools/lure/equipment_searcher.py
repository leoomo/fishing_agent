"""
装备搜索器

提供精确匹配、模糊匹配、相似度排序等搜索能力
"""

from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher


class EquipmentSearcher:
    """装备搜索器"""

    def __init__(self, db):
        self.db = db

    def search_by_name(
        self,
        name: str,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        按名称搜索装备（优先精确匹配）

        Args:
            name: 搜索名称
            category: 装备类别（可选）

        Returns:
            最匹配的装备，或None
        """
        # 1. 尝试精确匹配
        result = self._exact_match(name, category)
        if result:
            return result

        # 2. 尝试模糊匹配 + 相似度排序
        candidates = self._fuzzy_match(name, category, limit=10)
        if not candidates:
            return None

        # 3. 按相似度排序，返回最佳匹配
        best = max(candidates, key=lambda x: self._similarity(name, x))
        return best

    def search_multiple(
        self,
        names: List[str],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量搜索装备

        Args:
            names: 名称列表
            category: 装备类别（可选）

        Returns:
            装备列表（保持输入顺序，未找到的跳过）
        """
        results = []
        for name in names:
            eq = self.search_by_name(name.strip(), category)
            if eq:
                results.append(eq)
        return results

    def search_by_id(self, equipment_id: int) -> Optional[Dict[str, Any]]:
        """
        按ID搜索装备

        Args:
            equipment_id: 装备ID

        Returns:
            装备信息，或None
        """
        query = """
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.id = ?
            LIMIT 1
        """
        rows = self.db.execute(query, (equipment_id,))
        return rows[0] if rows else None

    def search_by_ids(self, equipment_ids: List[int]) -> List[Dict[str, Any]]:
        """
        批量按ID搜索装备

        Args:
            equipment_ids: 装备ID列表

        Returns:
            装备列表（保持输入顺序）
        """
        if not equipment_ids:
            return []

        placeholders = ",".join("?" * len(equipment_ids))
        query = f"""
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.id IN ({placeholders})
        """
        rows = self.db.execute(query, tuple(equipment_ids))

        # 按输入顺序排序
        id_to_row = {row['id']: row for row in rows}
        return [id_to_row[eid] for eid in equipment_ids if eid in id_to_row]

    def _exact_match(
        self,
        name: str,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """精确匹配"""
        query = """
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE (e.name = ? OR e.model = ?)
        """
        params = [name, name]

        if category:
            query += " AND e.category = ?"
            params.append(category)

        query += " LIMIT 1"
        rows = self.db.execute(query, tuple(params))
        return rows[0] if rows else None

    def _fuzzy_match(
        self,
        name: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """模糊匹配"""
        query = """
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE (e.name LIKE ? OR e.model LIKE ? OR b.name_cn LIKE ?)
        """
        pattern = f"%{name}%"
        params = [pattern, pattern, pattern]

        if category:
            query += " AND e.category = ?"
            params.append(category)

        query += f" LIMIT {limit}"
        return self.db.execute(query, tuple(params))

    def _similarity(self, search_name: str, equipment: Dict) -> float:
        """
        计算相似度分数

        综合考虑：名称、型号、品牌
        """
        scores = []

        # 名称相似度（权重最高）
        if equipment.get('name'):
            scores.append(SequenceMatcher(
                None, search_name.lower(), equipment['name'].lower()
            ).ratio() * 2)

        # 型号相似度
        if equipment.get('model'):
            scores.append(SequenceMatcher(
                None, search_name.lower(), equipment['model'].lower()
            ).ratio())

        # 品牌名包含检查
        if equipment.get('brand_name') and equipment['brand_name'] in search_name:
            scores.append(0.5)

        return sum(scores) / len(scores) if scores else 0
