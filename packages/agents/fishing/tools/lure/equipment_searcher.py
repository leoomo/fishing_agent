"""
装备搜索器

统一使用 EquipmentRepository 进行查询，支持精确匹配、模糊匹配、
相似度排序以及全部高级搜索功能。
"""

from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher


class EquipmentSearcher:
    """
    装备搜索器 - 统一使用 EquipmentRepository 进行查询

    提供两类搜索能力：
    1. 名称搜索：精确匹配 + 模糊匹配 + 相似度排序
    2. 高级搜索：支持全部筛选参数（品类、品牌、价格、规格等）
    """

    def __init__(self, session=None):
        """
        初始化搜索器

        Args:
            session: SQLAlchemy session（可选，默认自动获取）
        """
        from apps.api.orm.session import get_session_factory
        from apps.api.orm.repositories import EquipmentRepository

        if session is not None:
            self.session = session
            self._owns_session = False
        else:
            # 使用 scoped_session 获取 session
            session_factory = get_session_factory()
            self.session = session_factory()
            self._owns_session = True

        self.repo = EquipmentRepository(self.session)

    # === 原有方法（API 不变，内部改为调用 Repository）===

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
        result = self.repo.search_by_name_exact(name, category)
        if result:
            return self.repo.to_dict(result)

        # 2. 尝试模糊匹配 + 相似度排序
        candidates = self.repo.search_by_name_fuzzy(name, category, limit=10)
        if not candidates:
            return None

        # 3. 转为字典并按相似度排序，返回最佳匹配
        dicts = [self.repo.to_dict(e) for e in candidates]
        best = max(dicts, key=lambda x: self._similarity(name, x))
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
        result = self.repo.get_with_details(equipment_id)
        if result:
            return self.repo.to_dict(result)
        return None

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

        results = self.repo.get_by_ids(equipment_ids)
        return [self.repo.to_dict(e) for e in results]

    # === 新增：高级搜索方法（代理到 Repository）===

    def search(self, **filters) -> List[Dict[str, Any]]:
        """
        通用参数搜索

        支持的参数：
            category: 装备类别（鱼竿/渔轮/鱼线/拟饵/套装）
            brand_id: 品牌ID
            brand_name: 品牌名称（模糊匹配）
            price_min: 最低价格
            price_max: 最高价格
            user_level: 用户水平（新手/进阶/高手）
            is_active: 是否启用
            keyword: 关键词（搜索名称/描述/特性）
            source: 数据来源（manual/crawler/import）
            model: 型号（模糊匹配）
            created_after: 创建时间起始（ISO格式）
            created_before: 创建时间结束（ISO格式）
            limit: 返回数量限制（默认50）
            offset: 分页偏移量（默认0）

        Returns:
            装备列表
        """
        results = self.repo.search(**filters)
        return [self.repo.to_dict(e) for e in results]

    def search_rods(self, **filters) -> List[Dict[str, Any]]:
        """
        鱼竿专属搜索

        支持的参数（除通用参数外）：
            power: 硬度（UL/L/ML/M/MH/H/XH）
            action: 调性（Fast/Moderate/Slow）
            length_min: 最小长度（米）
            length_max: 最大长度（米）
            lure_weight_min: 最小饵重（克）
            lure_weight_max: 最大饵重（克）
            sections: 节数

        Returns:
            鱼竿列表
        """
        results = self.repo.search_rods(**filters)
        return [self.repo.to_dict(e) for e in results]

    def search_reels(self, **filters) -> List[Dict[str, Any]]:
        """
        渔轮专属搜索

        支持的参数（除通用参数外）：
            reel_type: 轮型（spinning/baitcasting/fly）
            max_drag_min: 最小拽力（kg）
            max_drag_max: 最大拽力（kg）
            weight_min: 最小重量（g）
            weight_max: 最大重量（g）

        Returns:
            渔轮列表
        """
        results = self.repo.search_reels(**filters)
        return [self.repo.to_dict(e) for e in results]

    def search_lines(self, **filters) -> List[Dict[str, Any]]:
        """
        鱼线专属搜索

        支持的参数（除通用参数外）：
            line_type: 线型（PE/尼龙/碳线/钢丝）
            diameter_min: 最小线径（mm）
            diameter_max: 最大线径（mm）
            strength_min: 最小拉力（lb）
            strength_max: 最大拉力（lb）

        Returns:
            鱼线列表
        """
        results = self.repo.search_lines(**filters)
        return [self.repo.to_dict(e) for e in results]

    def search_lures(self, **filters) -> List[Dict[str, Any]]:
        """
        拟饵专属搜索

        支持的参数（除通用参数外）：
            lure_category: 饵类别（硬饵/软饵/金属饵/飞蝇）
            weight_min: 最小重量（g）
            weight_max: 最大重量（g）
            diving_depth_min: 最小潜深（m）
            diving_depth_max: 最大潜深（m）

        Returns:
            拟饵列表
        """
        results = self.repo.search_lures(**filters)
        return [self.repo.to_dict(e) for e in results]

    # === 内部方法 ===

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


def get_equipment_searcher(session=None) -> EquipmentSearcher:
    """
    获取 EquipmentSearcher 实例的便捷方法

    Args:
        session: SQLAlchemy session（可选）

    Returns:
        EquipmentSearcher 实例
    """
    return EquipmentSearcher(session=session)
