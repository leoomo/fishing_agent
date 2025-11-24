"""
装备对比服务模块

提供装备对比分析功能：
- 多产品参数对比
- 优劣势分析
- 选购建议生成
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ComparisonItem:
    """对比项目"""
    equipment_id: int
    name: str
    category: str
    brand: Optional[str]
    price: Optional[float]
    specs: Dict[str, Any]
    main_image: Optional[str] = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    """对比结果"""
    items: List[ComparisonItem]
    category: str
    compare_aspects: List[str]
    recommendations: Dict[str, str]  # 场景 -> 推荐产品


class EquipmentComparator:
    """装备对比服务"""

    # 各类装备的对比维度
    COMPARE_ASPECTS = {
        "鱼竿": ["价格", "长度", "硬度", "调性", "自重", "品牌"],
        "渔轮": ["价格", "轮型", "速比", "自重", "刹车力", "品牌"],
        "鱼线": ["价格", "类型", "号数", "强度", "长度"],
        "拟饵": ["价格", "类型", "长度", "重量", "潜深", "颜色"],
    }

    # 硬度排序（用于比较）
    POWER_ORDER = ["UL", "L", "ML", "M", "MH", "H", "XH"]

    # 调性排序
    ACTION_ORDER = ["S", "M", "MF", "F", "XF"]

    def __init__(self, db, image_manager=None):
        """
        初始化对比服务

        Args:
            db: 数据库实例
            image_manager: 图片管理器（可选）
        """
        self.db = db
        self.image_manager = image_manager

    def compare(
        self,
        equipment_ids: Optional[List[int]] = None,
        equipment_names: Optional[List[str]] = None,
        aspects: Optional[List[str]] = None
    ) -> ComparisonResult:
        """
        对比多款装备

        Args:
            equipment_ids: 装备ID列表
            equipment_names: 装备名称列表（二选一）
            aspects: 对比维度（可选，默认全面对比）

        Returns:
            ComparisonResult对象
        """
        # 获取装备列表
        if equipment_ids:
            equipments = self._get_equipments_by_ids(equipment_ids)
        elif equipment_names:
            equipments = self._get_equipments_by_names(equipment_names)
        else:
            raise ValueError("必须提供equipment_ids或equipment_names")

        if len(equipments) < 2:
            raise ValueError("对比至少需要2个装备")

        # 验证类型一致性
        categories = set(e['category'] for e in equipments)
        if len(categories) > 1:
            raise ValueError(f"只能对比同类型装备，当前包含: {', '.join(categories)}")

        category = equipments[0]['category']

        # 确定对比维度
        if aspects is None:
            aspects = self.COMPARE_ASPECTS.get(category, ["价格", "品牌"])

        # 获取详细规格
        items = []
        for eq in equipments:
            specs = self._get_equipment_specs(eq['equipment_id'], category)
            main_image = None
            if self.image_manager:
                main_image = self.image_manager.get_main_image(eq['equipment_id'])

            item = ComparisonItem(
                equipment_id=eq['equipment_id'],
                name=eq['name'],
                category=category,
                brand=eq.get('brand_name'),
                price=eq.get('price_min'),
                specs=specs,
                main_image=main_image
            )
            items.append(item)

        # 分析优劣势
        self._analyze_strengths_weaknesses(items, category)

        # 生成推荐建议
        recommendations = self._generate_recommendations(items, category)

        return ComparisonResult(
            items=items,
            category=category,
            compare_aspects=aspects,
            recommendations=recommendations
        )

    def search_equipment_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称搜索装备"""
        query = """
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.name LIKE ?
               OR e.model LIKE ?
            LIMIT 1
        """
        pattern = f"%{name}%"
        rows = self.db.execute(query, (pattern, pattern))
        return rows[0] if rows else None

    def search_equipments_by_keyword(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """关键词搜索装备"""
        query = """
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE (e.name LIKE ? OR e.model LIKE ? OR b.name_cn LIKE ?)
        """
        params = [f"%{keyword}%"] * 3

        if category:
            query += " AND e.category = ?"
            params.append(category)

        query += " LIMIT ?"
        params.append(limit)

        return self.db.execute(query, tuple(params))

    # ========== 私有方法 ==========

    def _get_equipments_by_ids(self, equipment_ids: List[int]) -> List[Dict[str, Any]]:
        """根据ID列表获取装备"""
        placeholders = ",".join(["?"] * len(equipment_ids))
        query = f"""
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.equipment_id IN ({placeholders})
        """
        return self.db.execute(query, tuple(equipment_ids))

    def _get_equipments_by_names(self, names: List[str]) -> List[Dict[str, Any]]:
        """根据名称列表获取装备"""
        equipments = []
        for name in names:
            eq = self.search_equipment_by_name(name)
            if eq:
                equipments.append(eq)
        return equipments

    def _get_equipment_specs(self, equipment_id: int, category: str) -> Dict[str, Any]:
        """获取装备详细规格"""
        specs = {}

        if category == "鱼竿":
            query = "SELECT * FROM rod_specs WHERE equipment_id = ?"
            rows = self.db.execute(query, (equipment_id,))
            if rows:
                row = rows[0]
                specs = {
                    "长度": f"{row.get('length')}m" if row.get('length') else None,
                    "硬度": row.get('power'),
                    "调性": row.get('action'),
                    "节数": row.get('sections'),
                    "自重": f"{row.get('weight')}g" if row.get('weight') else None,
                    "饵重范围": f"{row.get('lure_weight_min')}-{row.get('lure_weight_max')}g"
                        if row.get('lure_weight_min') else None,
                    "导环": row.get('guide_type'),
                }

        elif category == "渔轮":
            query = "SELECT * FROM reel_specs WHERE equipment_id = ?"
            rows = self.db.execute(query, (equipment_id,))
            if rows:
                row = rows[0]
                specs = {
                    "轮型": row.get('reel_type'),
                    "速比": row.get('gear_ratio'),
                    "轴承": row.get('bearings'),
                    "自重": f"{row.get('weight')}g" if row.get('weight') else None,
                    "线容量": row.get('line_capacity'),
                    "最大刹车力": f"{row.get('max_drag')}kg" if row.get('max_drag') else None,
                    "每转收线": f"{row.get('retrieve_per_turn')}cm"
                        if row.get('retrieve_per_turn') else None,
                }

        elif category == "鱼线":
            query = "SELECT * FROM line_specs WHERE equipment_id = ?"
            rows = self.db.execute(query, (equipment_id,))
            if rows:
                row = rows[0]
                specs = {
                    "类型": row.get('line_type'),
                    "线径": f"{row.get('diameter')}mm" if row.get('diameter') else None,
                    "强度": f"{row.get('strength_lb')}lb" if row.get('strength_lb') else None,
                    "长度": f"{row.get('length_m')}m" if row.get('length_m') else None,
                    "颜色": row.get('color'),
                    "材质": row.get('material'),
                }

        elif category == "拟饵":
            query = "SELECT * FROM lure_specs WHERE equipment_id = ?"
            rows = self.db.execute(query, (equipment_id,))
            if rows:
                row = rows[0]
                specs = {
                    "类型": row.get('lure_type'),
                    "分类": row.get('lure_category'),
                    "长度": f"{row.get('length')}mm" if row.get('length') else None,
                    "重量": f"{row.get('weight')}g" if row.get('weight') else None,
                    "潜深": f"{row.get('diving_depth_min')}-{row.get('diving_depth_max')}m"
                        if row.get('diving_depth_min') else None,
                    "颜色": row.get('color'),
                    "泳姿": row.get('action_type'),
                }

        # 过滤掉None值
        return {k: v for k, v in specs.items() if v is not None}

    def _analyze_strengths_weaknesses(
        self,
        items: List[ComparisonItem],
        category: str
    ) -> None:
        """分析各产品的优劣势"""
        if len(items) < 2:
            return

        # 收集所有数值用于比较
        prices = [(i, item.price) for i, item in enumerate(items) if item.price]
        weights = []

        for i, item in enumerate(items):
            if "自重" in item.specs:
                try:
                    w = float(item.specs["自重"].replace("g", ""))
                    weights.append((i, w))
                except (ValueError, AttributeError):
                    pass

        # 价格分析
        if prices:
            prices.sort(key=lambda x: x[1])
            cheapest_idx = prices[0][0]
            items[cheapest_idx].strengths.append("价格最低")
            if len(prices) > 1:
                most_expensive_idx = prices[-1][0]
                items[most_expensive_idx].weaknesses.append("价格最高")

        # 重量分析
        if weights:
            weights.sort(key=lambda x: x[1])
            lightest_idx = weights[0][0]
            items[lightest_idx].strengths.append("最轻便")
            if len(weights) > 1:
                heaviest_idx = weights[-1][0]
                items[heaviest_idx].weaknesses.append("相对较重")

        # 鱼竿特定分析
        if category == "鱼竿":
            self._analyze_rod_specs(items)

        # 渔轮特定分析
        elif category == "渔轮":
            self._analyze_reel_specs(items)

    def _analyze_rod_specs(self, items: List[ComparisonItem]) -> None:
        """分析鱼竿规格"""
        lengths = []
        for i, item in enumerate(items):
            if "长度" in item.specs:
                try:
                    l = float(item.specs["长度"].replace("m", ""))
                    lengths.append((i, l))
                except (ValueError, AttributeError):
                    pass

        if lengths:
            lengths.sort(key=lambda x: x[1])
            longest_idx = lengths[-1][0]
            shortest_idx = lengths[0][0]

            if lengths[-1][1] > lengths[0][1]:
                items[longest_idx].strengths.append("长度更长，远投能力强")
                items[shortest_idx].strengths.append("短竿操控灵活")
                items[shortest_idx].weaknesses.append("覆盖范围较小")

        # 调性分析
        for item in items:
            action = item.specs.get("调性")
            if action:
                if action in ["F", "XF"]:
                    item.strengths.append(f"{action}调性回弹快，适合快速作钓")
                elif action in ["MF", "M"]:
                    item.strengths.append(f"{action}调性手感细腻")

    def _analyze_reel_specs(self, items: List[ComparisonItem]) -> None:
        """分析渔轮规格"""
        for item in items:
            gear_ratio = item.specs.get("速比")
            if gear_ratio:
                try:
                    ratio = float(gear_ratio.split(":")[0])
                    if ratio >= 7.0:
                        item.strengths.append("高速比，收线快")
                    elif ratio <= 5.5:
                        item.strengths.append("低速比，力量大")
                except (ValueError, IndexError):
                    pass

    def _generate_recommendations(
        self,
        items: List[ComparisonItem],
        category: str
    ) -> Dict[str, str]:
        """生成选购建议"""
        recommendations = {}

        if not items:
            return recommendations

        # 找出各维度最优
        cheapest = min(items, key=lambda x: x.price or float('inf'))
        recommendations["预算有限"] = cheapest.name

        # 找最轻便的
        lightest = None
        min_weight = float('inf')
        for item in items:
            if "自重" in item.specs:
                try:
                    w = float(item.specs["自重"].replace("g", ""))
                    if w < min_weight:
                        min_weight = w
                        lightest = item
                except (ValueError, AttributeError):
                    pass

        if lightest:
            recommendations["长时间作钓"] = lightest.name

        # 鱼竿特定建议
        if category == "鱼竿":
            longest = None
            max_length = 0
            for item in items:
                if "长度" in item.specs:
                    try:
                        l = float(item.specs["长度"].replace("m", ""))
                        if l > max_length:
                            max_length = l
                            longest = item
                    except (ValueError, AttributeError):
                        pass

            if longest:
                recommendations["岸钓/远投"] = longest.name

            # 找短竿
            shortest = None
            min_length = float('inf')
            for item in items:
                if "长度" in item.specs:
                    try:
                        l = float(item.specs["长度"].replace("m", ""))
                        if l < min_length:
                            min_length = l
                            shortest = item
                    except (ValueError, AttributeError):
                        pass

            if shortest and shortest != longest:
                recommendations["船钓/精细作钓"] = shortest.name

        return recommendations
