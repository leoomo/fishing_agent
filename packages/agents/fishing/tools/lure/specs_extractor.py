"""
装备规格提取器

统一的规格获取逻辑，供 comparator 和 recommender 共用
"""

from typing import Dict, Any, Optional


class SpecsExtractor:
    """装备规格提取器"""

    def __init__(self, db):
        self.db = db

    def get_specs(self, equipment_id: int, category: str) -> Dict[str, Any]:
        """
        获取装备详细规格

        Args:
            equipment_id: 装备ID
            category: 装备类别

        Returns:
            规格字典（已过滤None值）
        """
        specs = {}

        if category in ("鱼竿", "路亚竿"):
            specs = self._get_rod_specs(equipment_id)
        elif category == "渔轮":
            specs = self._get_reel_specs(equipment_id)
        elif category == "鱼线":
            specs = self._get_line_specs(equipment_id)
        elif category == "拟饵":
            specs = self._get_lure_specs(equipment_id)

        return {k: v for k, v in specs.items() if v is not None}

    def get_raw_specs(self, equipment_id: int, category: str) -> Optional[Dict]:
        """获取原始规格数据（用于计算）"""
        table_map = {
            "鱼竿": "rod_specs",
            "路亚竿": "rod_specs",
            "渔轮": "reel_specs",
            "鱼线": "line_specs",
            "拟饵": "lure_specs"
        }

        table = table_map.get(category)
        if not table:
            return None

        query = f"SELECT * FROM {table} WHERE equipment_id = ?"
        rows = self.db.execute(query, (equipment_id,))
        return rows[0] if rows else None

    def _get_rod_specs(self, equipment_id: int) -> Dict[str, Any]:
        """获取鱼竿规格"""
        row = self.get_raw_specs(equipment_id, "鱼竿")
        if not row:
            return {}

        return {
            "长度": f"{row.get('length')}m" if row.get('length') else None,
            "硬度": row.get('power'),
            "调性": row.get('action'),
            "节数": row.get('sections'),
            "自重": f"{row.get('weight')}g" if row.get('weight') else None,
            "适用饵范围": self._format_lure_range(row),
            "导环": row.get('guide_type'),
        }

    def _get_reel_specs(self, equipment_id: int) -> Dict[str, Any]:
        """获取渔轮规格"""
        row = self.get_raw_specs(equipment_id, "渔轮")
        if not row:
            return {}

        return {
            "轮型": row.get('reel_type'),
            "速比": row.get('gear_ratio'),
            "轴承": row.get('bearings'),
            "自重": f"{row.get('weight')}g" if row.get('weight') else None,
            "线容量": row.get('line_capacity'),
            "最大刹车力": f"{row.get('max_drag')}kg" if row.get('max_drag') else None,
            "每转收线": f"{row.get('retrieve_per_turn')}cm" if row.get('retrieve_per_turn') else None,
        }

    def _get_line_specs(self, equipment_id: int) -> Dict[str, Any]:
        """获取鱼线规格"""
        row = self.get_raw_specs(equipment_id, "鱼线")
        if not row:
            return {}

        return {
            "类型": row.get('line_type'),
            "线径": f"{row.get('diameter')}mm" if row.get('diameter') else None,
            "强度": f"{row.get('strength_lb')}lb" if row.get('strength_lb') else None,
            "长度": f"{row.get('length_m')}m" if row.get('length_m') else None,
            "颜色": row.get('color'),
            "材质": row.get('material'),
        }

    def _get_lure_specs(self, equipment_id: int) -> Dict[str, Any]:
        """获取拟饵规格"""
        row = self.get_raw_specs(equipment_id, "拟饵")
        if not row:
            return {}

        return {
            "类型": row.get('lure_type'),
            "分类": row.get('lure_category'),
            "长度": f"{row.get('length')}mm" if row.get('length') else None,
            "重量": f"{row.get('weight')}g" if row.get('weight') else None,
            "潜深": self._format_depth_range(row),
            "颜色": row.get('color'),
            "泳姿": row.get('action_type'),
        }

    @staticmethod
    def _format_lure_range(row: Dict) -> Optional[str]:
        """格式化适用饵范围"""
        min_val = row.get('lure_weight_min')
        max_val = row.get('lure_weight_max')
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}g"
        return None

    @staticmethod
    def _format_depth_range(row: Dict) -> Optional[str]:
        """格式化潜深范围"""
        min_val = row.get('diving_depth_min')
        max_val = row.get('diving_depth_max')
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}m"
        return None
