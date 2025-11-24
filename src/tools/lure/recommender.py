"""
路亚装备推荐算法模块

实现四因子加权评分系统：
- 价格匹配 (35%)
- 规格匹配 (35%)
- 品牌声誉 (15%)
- 用户水平 (15%)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


# ========== 配置 ==========

RECOMMENDATION_CONFIG = {
    # 评分权重
    "weights": {
        "price_match": 0.35,
        "spec_match": 0.35,
        "brand_reputation": 0.15,
        "user_level": 0.15
    },
    # 过滤条件
    "filters": {
        "max_price_deviation": 0.2,  # 最大价格偏离20%
        "min_score": 50,  # 最低推荐分数
    },
    # 规格容差
    "spec_tolerance": {
        "length": 0.3,  # 长度容差0.3m
        "power": 1,  # 硬度容差±1级
        "action": 0  # 调性需完全匹配
    },
    # 套装预算分配
    "package_budget_allocation": {
        "鱼竿": 0.40,
        "渔轮": 0.35,
        "鱼线": 0.25
    }
}

# 硬度等级排序
POWER_ORDER = ["UUL", "UL", "L", "ML", "M", "MH", "H", "XH", "XXH"]

# 调性等级排序
ACTION_ORDER = ["S", "M", "MF", "F", "XF"]

# 用户水平映射
USER_LEVEL_MAP = {
    "新手": 1, "初学者": 1, "入门": 1,
    "进阶": 2, "中级": 2,
    "高手": 3, "高级": 3, "专业": 3
}


@dataclass
class RecommendationResult:
    """推荐结果"""
    equipment_id: int
    name: str
    category: str
    brand: Optional[str]
    price: Optional[float]
    total_score: float
    score_breakdown: Dict[str, float]
    match_reasons: List[str] = field(default_factory=list)
    specs: Dict[str, Any] = field(default_factory=dict)
    main_image: Optional[str] = None


class LureRecommender:
    """路亚装备推荐引擎"""

    def __init__(self, db, config: Optional[Dict] = None):
        """
        初始化推荐器

        Args:
            db: 数据库实例
            config: 配置覆盖（可选）
        """
        self.db = db
        self.config = {**RECOMMENDATION_CONFIG, **(config or {})}
        self._brand_scores = None  # 品牌分数缓存

    # ========== 主推荐方法 ==========

    def recommend(
        self,
        equipment_type: str,
        user_specs: Dict[str, Any],
        top_k: int = 3
    ) -> List[RecommendationResult]:
        """
        推荐装备

        Args:
            equipment_type: 装备类型（鱼竿/渔轮/鱼线/拟饵）
            user_specs: 用户需求规格
                - budget: 预算
                - specifications: 规格要求（硬度/长度等）
                - target_fish: 目标鱼种
                - scenario: 使用场景
                - user_level: 用户水平
            top_k: 返回数量

        Returns:
            推荐结果列表
        """
        budget = user_specs.get("budget")
        user_level = user_specs.get("user_level", "新手")
        specifications = user_specs.get("specifications", {})

        # 1. 获取候选装备
        candidates = self._get_candidates(equipment_type, budget)

        if not candidates:
            return []

        # 2. 计算每个装备的得分
        results = []
        for eq in candidates:
            scores = self._calculate_scores(eq, user_specs)
            total_score = self._weighted_sum(scores)

            # 过滤低分
            if total_score < self.config["filters"]["min_score"]:
                continue

            # 生成匹配理由
            reasons = self._generate_match_reasons(eq, scores, user_specs)

            results.append(RecommendationResult(
                equipment_id=eq['equipment_id'],
                name=eq['name'],
                category=eq['category'],
                brand=eq.get('brand_name'),
                price=eq.get('price_min'),
                total_score=total_score,
                score_breakdown=scores,
                match_reasons=reasons,
                specs=self._get_equipment_specs(eq)
            ))

        # 3. 排序并返回top_k
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results[:top_k]

    def recommend_package(
        self,
        budget: float,
        user_level: str = "新手",
        target_fish: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        推荐套装组合

        Args:
            budget: 总预算
            user_level: 用户水平
            target_fish: 目标鱼种

        Returns:
            套装推荐结果
        """
        allocation = self.config["package_budget_allocation"]

        # 按比例分配预算
        rod_budget = budget * allocation["鱼竿"]
        reel_budget = budget * allocation["渔轮"]
        line_budget = budget * allocation["鱼线"]

        user_specs_base = {
            "user_level": user_level,
            "target_fish": target_fish
        }

        # 分别推荐
        rod_rec = self.recommend("鱼竿", {**user_specs_base, "budget": rod_budget}, top_k=1)
        reel_rec = self.recommend("渔轮", {**user_specs_base, "budget": reel_budget}, top_k=1)
        line_rec = self.recommend("鱼线", {**user_specs_base, "budget": line_budget}, top_k=1)

        # 计算实际总价
        total_price = 0
        items = {}

        if rod_rec:
            items["rod"] = rod_rec[0]
            total_price += rod_rec[0].price or 0
        if reel_rec:
            items["reel"] = reel_rec[0]
            total_price += reel_rec[0].price or 0
        if line_rec:
            items["line"] = line_rec[0]
            total_price += line_rec[0].price or 0

        # 兼容性检查
        compatibility = self._check_package_compatibility(items)

        return {
            "budget": budget,
            "total_price": total_price,
            "savings": budget - total_price,
            "items": items,
            "compatibility": compatibility,
            "user_level": user_level
        }

    # ========== 评分方法 ==========

    def _calculate_scores(
        self,
        equipment: Dict,
        user_specs: Dict
    ) -> Dict[str, float]:
        """计算四项评分"""
        return {
            "price_match": self._calculate_price_score(
                equipment, user_specs.get("budget")
            ),
            "spec_match": self._calculate_spec_score(
                equipment, user_specs.get("specifications", {})
            ),
            "brand_reputation": self._calculate_brand_score(equipment),
            "user_level": self._calculate_user_level_score(
                equipment, user_specs.get("user_level", "新手")
            )
        }

    def _calculate_price_score(
        self,
        equipment: Dict,
        budget: Optional[float]
    ) -> float:
        """
        计算价格匹配分数

        规则：
        - 价格 <= 预算: 100分（精确匹配最佳，过低递减）
        - 预算 < 价格 <= 预算*1.2: 线性衰减60-100
        - 价格 > 预算*1.2: 0分
        """
        if not budget:
            return 80  # 无预算限制时给默认分

        price = equipment.get('price_min')
        if not price:
            return 70  # 无价格信息给中等分

        max_deviation = self.config["filters"]["max_price_deviation"]
        max_price = budget * (1 + max_deviation)

        if price <= budget:
            # 预算内：越接近预算分数越高
            ratio = price / budget
            if ratio >= 0.7:
                return 100
            elif ratio >= 0.5:
                return 80 + (ratio - 0.5) * 100  # 80-100
            else:
                return 60 + ratio * 40  # 60-80

        elif price <= max_price:
            # 略超预算：线性衰减
            over_ratio = (price - budget) / (max_price - budget)
            return 100 - over_ratio * 40  # 60-100

        else:
            # 超出太多
            return 0

    def _calculate_spec_score(
        self,
        equipment: Dict,
        specifications: Dict
    ) -> float:
        """
        计算规格匹配分数

        多维度匹配：硬度、长度、调性等
        """
        if not specifications:
            return 80  # 无规格要求给默认分

        scores = []
        category = equipment.get('category')

        # 获取装备详细规格
        eq_specs = self._get_equipment_specs(equipment)

        # 硬度匹配（鱼竿）
        if "硬度" in specifications and category == "鱼竿":
            target_power = specifications["硬度"]
            actual_power = eq_specs.get("硬度")
            if actual_power:
                scores.append(self._match_power(target_power, actual_power))

        # 长度匹配（鱼竿）
        if "长度" in specifications and category == "鱼竿":
            target_length = self._parse_length(specifications["长度"])
            actual_length = eq_specs.get("长度")
            if target_length and actual_length:
                scores.append(self._match_length(target_length, actual_length))

        # 调性匹配（鱼竿）
        if "调性" in specifications and category == "鱼竿":
            target_action = specifications["调性"]
            actual_action = eq_specs.get("调性")
            if actual_action:
                scores.append(100 if target_action == actual_action else 50)

        # 速比匹配（渔轮）
        if "速比" in specifications and category == "渔轮":
            # 简化处理
            scores.append(80)

        # 线号匹配（鱼线）
        if "线号" in specifications and category == "鱼线":
            scores.append(80)

        if scores:
            return sum(scores) / len(scores)
        return 80

    def _calculate_brand_score(self, equipment: Dict) -> float:
        """
        计算品牌声誉分数

        一线品牌: 90-100
        二线品牌: 70-85
        国产品牌: 60-75
        未知品牌: 50
        """
        if self._brand_scores is None:
            self._load_brand_scores()

        brand_id = equipment.get('brand_id')
        if not brand_id:
            return 50

        return self._brand_scores.get(brand_id, 50)

    def _calculate_user_level_score(
        self,
        equipment: Dict,
        user_level: str
    ) -> float:
        """
        计算用户水平匹配分数

        完全匹配或通用: 100
        高1级: 70（有成长空间）
        低1级: 50（不推荐）
        差距>1级: 30
        """
        eq_level = equipment.get('user_level', '入门')
        user_num = USER_LEVEL_MAP.get(user_level, 1)
        eq_num = USER_LEVEL_MAP.get(eq_level, 1)

        diff = eq_num - user_num

        if diff == 0:
            return 100
        elif diff == 1:
            return 70  # 装备略高于用户水平，有成长空间
        elif diff == -1:
            return 50  # 装备略低于用户水平
        else:
            return 30

    def _weighted_sum(self, scores: Dict[str, float]) -> float:
        """计算加权总分"""
        weights = self.config["weights"]
        total = 0
        for key, score in scores.items():
            weight = weights.get(key, 0)
            total += score * weight
        return round(total, 1)

    # ========== 辅助方法 ==========

    def _get_candidates(
        self,
        equipment_type: str,
        budget: Optional[float]
    ) -> List[Dict]:
        """获取候选装备列表"""
        query = """
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.category = ? AND e.is_active = 1
        """
        params = [equipment_type]

        # 价格过滤（允许20%超预算）
        if budget:
            max_price = budget * (1 + self.config["filters"]["max_price_deviation"])
            query += " AND (e.price_min <= ? OR e.price_min IS NULL)"
            params.append(max_price)

        query += " ORDER BY e.price_min ASC"

        return self.db.execute(query, tuple(params))

    def _get_equipment_specs(self, equipment: Dict) -> Dict[str, Any]:
        """获取装备详细规格"""
        category = equipment.get('category')
        eq_id = equipment.get('equipment_id')

        if not eq_id:
            return {}

        specs = {}

        if category == "鱼竿":
            query = "SELECT * FROM rod_specs WHERE equipment_id = ?"
            rows = self.db.execute(query, (eq_id,))
            if rows:
                row = rows[0]
                specs = {
                    "长度": row.get('length'),
                    "硬度": row.get('power'),
                    "调性": row.get('action'),
                    "自重": row.get('weight'),
                    "节数": row.get('sections')
                }

        elif category == "渔轮":
            query = "SELECT * FROM reel_specs WHERE equipment_id = ?"
            rows = self.db.execute(query, (eq_id,))
            if rows:
                row = rows[0]
                specs = {
                    "轮型": row.get('reel_type'),
                    "速比": row.get('gear_ratio'),
                    "自重": row.get('weight'),
                    "刹车力": row.get('max_drag')
                }

        elif category == "鱼线":
            query = "SELECT * FROM line_specs WHERE equipment_id = ?"
            rows = self.db.execute(query, (eq_id,))
            if rows:
                row = rows[0]
                specs = {
                    "类型": row.get('line_type'),
                    "线径": row.get('diameter'),
                    "强度": row.get('strength_lb'),
                    "长度": row.get('length_m')
                }

        return {k: v for k, v in specs.items() if v is not None}

    def _load_brand_scores(self):
        """加载品牌分数"""
        self._brand_scores = {}

        # 品牌等级分数映射
        tier_scores = {
            "高端": 95,
            "中高端": 85,
            "中端": 75,
            "入门": 65
        }

        query = "SELECT id, tier FROM brands"
        rows = self.db.execute(query)

        for row in rows:
            tier = row.get('tier', '入门')
            self._brand_scores[row['id']] = tier_scores.get(tier, 60)

    def _match_power(self, target: str, actual: str) -> float:
        """匹配硬度等级"""
        try:
            target_idx = POWER_ORDER.index(target.upper())
            actual_idx = POWER_ORDER.index(actual.upper())
            diff = abs(target_idx - actual_idx)

            if diff == 0:
                return 100
            elif diff == 1:
                return 80
            elif diff == 2:
                return 50
            else:
                return 20
        except ValueError:
            return 60

    def _match_length(self, target: float, actual: float) -> float:
        """匹配长度"""
        tolerance = self.config["spec_tolerance"]["length"]
        diff = abs(target - actual)

        if diff <= tolerance:
            return 100
        elif diff <= tolerance * 2:
            return 70
        else:
            return 40

    def _parse_length(self, length_str) -> Optional[float]:
        """解析长度字符串"""
        if isinstance(length_str, (int, float)):
            return float(length_str)

        if isinstance(length_str, str):
            # 处理 "2.1m" 或 "2.1" 格式
            import re
            match = re.search(r'(\d+\.?\d*)', length_str)
            if match:
                return float(match.group(1))
        return None

    def _generate_match_reasons(
        self,
        equipment: Dict,
        scores: Dict[str, float],
        user_specs: Dict
    ) -> List[str]:
        """生成匹配理由"""
        reasons = []

        if scores["price_match"] >= 90:
            reasons.append("价格在预算范围内")
        elif scores["price_match"] >= 70:
            reasons.append("价格略超预算但性价比高")

        if scores["brand_reputation"] >= 90:
            reasons.append("一线品牌，质量有保障")
        elif scores["brand_reputation"] >= 75:
            reasons.append("知名品牌，口碑良好")

        if scores["user_level"] >= 90:
            reasons.append("适合当前水平使用")
        elif scores["user_level"] >= 70:
            reasons.append("略有挑战，有成长空间")

        if scores["spec_match"] >= 90:
            reasons.append("规格完全符合需求")

        return reasons

    def _check_package_compatibility(self, items: Dict) -> Dict[str, Any]:
        """检查套装兼容性"""
        compatibility = {
            "is_compatible": True,
            "notes": []
        }

        rod = items.get("rod")
        reel = items.get("reel")
        line = items.get("line")

        # 简化的兼容性检查
        if rod and reel:
            compatibility["notes"].append("鱼竿渔轮搭配合理")

        if rod and line:
            compatibility["notes"].append("鱼竿鱼线搭配合理")

        return compatibility


# ========== 便捷函数 ==========

def create_recommender(db=None, config=None) -> LureRecommender:
    """创建推荐器的便捷函数"""
    if db is None:
        from .database import get_db
        db = get_db()

    return LureRecommender(db, config)
