"""
装备对比服务模块（优化版）

提供装备对比分析功能：
- 多产品参数对比
- 优劣势分析
- 综合评分
- 参数差异分析
- 选购建议生成
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .constants import (
    POWER_ORDER, ACTION_ORDER, COMPARE_ASPECTS,
    BRAND_TIER_SCORES, RECOMMENDATION_WEIGHTS
)
from .specs_extractor import SpecsExtractor
from .equipment_searcher import EquipmentSearcher
from .diff_analyzer import DiffAnalyzer, SpecDifference


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
    # 新增：综合评分
    overall_score: float = 0.0
    score_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """对比结果"""
    items: List[ComparisonItem]
    category: str
    compare_aspects: List[str]
    recommendations: Dict[str, str]  # 场景 -> 推荐产品
    # 新增：最佳综合选择
    best_overall: Optional[str] = None
    # 新增：对比总结
    summary: Optional[str] = None
    # 新增：参数差异分析
    spec_differences: List[SpecDifference] = field(default_factory=list)
    # 新增：关键差异（差异最大的前3个参数）
    key_differences: List[SpecDifference] = field(default_factory=list)


class EquipmentComparator:
    """装备对比服务（优化版）"""

    # 对比维度权重
    ASPECT_WEIGHTS = {
        "价格": 0.25,
        "自重": 0.15,
        "品牌": 0.15,
        "硬度": 0.10,
        "调性": 0.10,
        "长度": 0.10,
        "速比": 0.10,
        "刹车力": 0.05,
    }

    def __init__(self, db, image_manager=None):
        """
        初始化对比服务

        Args:
            db: 数据库实例
            image_manager: 图片管理器（可选）
        """
        self.db = db
        self.image_manager = image_manager
        self.specs_extractor = SpecsExtractor(db)
        self.searcher = EquipmentSearcher(db)
        self.diff_analyzer = DiffAnalyzer()

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
        # 1. 获取装备（使用优化后的搜索器）
        if equipment_ids:
            equipments = self.searcher.search_by_ids(equipment_ids)
        elif equipment_names:
            equipments = self.searcher.search_multiple(equipment_names)
        else:
            raise ValueError("必须提供equipment_ids或equipment_names")

        # 2. 数量验证
        if len(equipments) < 2:
            raise ValueError("对比至少需要2个装备")
        if len(equipments) > 5:
            raise ValueError("对比装备数量不能超过5个")

        # 3. 类型一致性验证
        categories = set(e['category'] for e in equipments)
        if len(categories) > 1:
            raise ValueError(f"只能对比同类型装备，当前包含: {', '.join(categories)}")

        category = equipments[0]['category']

        # 4. 确定对比维度
        if aspects is None:
            aspects = COMPARE_ASPECTS.get(category, ["价格", "品牌"])

        # 5. 构建对比项（使用统一的规格提取器）
        items = []
        for eq in equipments:
            # 兼容不同的ID字段名
            eq_id = eq.get('equipment_id') or eq.get('id')
            specs = self.specs_extractor.get_specs(eq_id, category)
            main_image = None
            if self.image_manager:
                main_image = self.image_manager.get_main_image(eq_id)

            item = ComparisonItem(
                equipment_id=eq_id,
                name=eq['name'],
                category=category,
                brand=eq.get('brand_name'),
                price=eq.get('price_min'),
                specs=specs,
                main_image=main_image
            )
            items.append(item)

        # 6. 计算综合评分（新增）
        self._calculate_overall_scores(items, category)

        # 7. 分析优劣势
        self._analyze_strengths_weaknesses(items, category)

        # 8. 分析参数差异（核心新增）
        all_diffs, key_diffs = self.diff_analyzer.analyze_differences(items, category)

        # 9. 生成推荐建议（增强版）
        recommendations = self._generate_recommendations(items, category)

        # 10. 确定最佳综合选择
        best_overall = max(items, key=lambda x: x.overall_score).name if items else None

        # 11. 生成对比总结
        summary = self._generate_summary(items, category)

        return ComparisonResult(
            items=items,
            category=category,
            compare_aspects=aspects,
            recommendations=recommendations,
            best_overall=best_overall,
            summary=summary,
            spec_differences=all_diffs,
            key_differences=key_diffs
        )

    def search_equipment_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称搜索装备（兼容旧API）"""
        return self.searcher.search_by_name(name)

    def search_equipments_by_keyword(
        self,
        keyword: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """关键词搜索装备（兼容旧API）"""
        return self.searcher._fuzzy_match(keyword, category, limit)

    # ========== 评分计算 ==========

    def _calculate_overall_scores(
        self,
        items: List[ComparisonItem],
        category: str
    ) -> None:
        """
        计算各装备的综合评分

        评分维度：
        - 性价比（价格越低越好）
        - 轻量化（自重越轻越好）
        - 品牌声誉
        - 规格匹配度（针对不同品类）
        """
        if len(items) < 2:
            return

        # 收集数值用于归一化
        prices = [item.price for item in items if item.price]
        weights = []
        for item in items:
            w = self._extract_weight(item.specs.get("自重"))
            if w:
                weights.append(w)

        for item in items:
            scores = {}

            # 1. 价格分数（越低越好，归一化到0-100）
            if item.price and prices:
                min_price, max_price = min(prices), max(prices)
                if max_price > min_price:
                    # 反向归一化：最低价得100分
                    scores["价格"] = 100 - ((item.price - min_price) / (max_price - min_price)) * 60
                else:
                    scores["价格"] = 80
            else:
                scores["价格"] = 70

            # 2. 自重分数（越轻越好）
            w = self._extract_weight(item.specs.get("自重"))
            if w and weights:
                min_w, max_w = min(weights), max(weights)
                if max_w > min_w:
                    scores["自重"] = 100 - ((w - min_w) / (max_w - min_w)) * 40
                else:
                    scores["自重"] = 80
            else:
                scores["自重"] = 70

            # 3. 品牌分数
            scores["品牌"] = self._get_brand_score(item.brand)

            # 4. 品类特定分数
            if category in ("鱼竿", "路亚竿"):
                scores.update(self._calculate_rod_scores(item))
            elif category == "渔轮":
                scores.update(self._calculate_reel_scores(item))

            # 5. 计算加权总分
            total = 0
            weight_sum = 0
            for aspect, score in scores.items():
                weight = self.ASPECT_WEIGHTS.get(aspect, 0.05)
                total += score * weight
                weight_sum += weight

            item.overall_score = round(total / weight_sum if weight_sum > 0 else 50, 1)
            item.score_breakdown = scores

    def _calculate_rod_scores(self, item: ComparisonItem) -> Dict[str, float]:
        """计算鱼竿特定分数"""
        scores = {}

        # 调性分数（快调更受欢迎）
        action = item.specs.get("调性")
        if action:
            try:
                idx = ACTION_ORDER.index(action.upper().replace("+", ""))
                # F/XF 更高分
                scores["调性"] = 60 + idx * 10
            except ValueError:
                scores["调性"] = 70

        return scores

    def _calculate_reel_scores(self, item: ComparisonItem) -> Dict[str, float]:
        """计算渔轮特定分数"""
        scores = {}

        # 速比分数
        gear_ratio = item.specs.get("速比")
        if gear_ratio:
            try:
                ratio = float(gear_ratio.split(":")[0])
                # 高速比（>7.0）更灵活
                if ratio >= 7.0:
                    scores["速比"] = 90
                elif ratio >= 6.0:
                    scores["速比"] = 80
                else:
                    scores["速比"] = 70
            except (ValueError, IndexError):
                scores["速比"] = 70

        return scores

    def _get_brand_score(self, brand_name: Optional[str]) -> float:
        """获取品牌分数"""
        if not brand_name:
            return 50

        # 一线日系品牌
        tier1 = ["禧玛诺", "达亿瓦", "SHIMANO", "DAIWA"]
        # 二线品牌
        tier2 = ["阿布", "ABU", "宝熊", "光威", "狼王"]
        # 知名国产
        tier3 = ["汉鼎", "佳钓尼", "化氏"]

        for brand in tier1:
            if brand.lower() in brand_name.lower():
                return 95
        for brand in tier2:
            if brand.lower() in brand_name.lower():
                return 80
        for brand in tier3:
            if brand.lower() in brand_name.lower():
                return 70

        return 60

    # ========== 优劣势分析 ==========

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
            w = self._extract_weight(item.specs.get("自重"))
            if w:
                weights.append((i, w))

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
        if category in ("鱼竿", "路亚竿"):
            self._analyze_rod_specs(items)

        # 渔轮特定分析
        elif category == "渔轮":
            self._analyze_reel_specs(items)

    def _analyze_rod_specs(self, items: List[ComparisonItem]) -> None:
        """分析鱼竿规格"""
        lengths = []
        for i, item in enumerate(items):
            l = self._extract_length(item.specs.get("长度"))
            if l:
                lengths.append((i, l))

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
                if action.upper() in ["F", "XF"]:
                    item.strengths.append(f"{action}调性回弹快，适合快速作钓")
                elif action.upper() in ["MF", "M"]:
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

    # ========== 总结和推荐 ==========

    def _generate_summary(
        self,
        items: List[ComparisonItem],
        category: str
    ) -> str:
        """生成对比总结"""
        if not items:
            return ""

        # 按综合评分排序
        sorted_items = sorted(items, key=lambda x: x.overall_score, reverse=True)
        best = sorted_items[0]

        summary_parts = [
            f"综合评分最高的是 **{best.name}**（{best.overall_score:.1f}分）"
        ]

        # 找出各维度最优
        cheapest = min(items, key=lambda x: x.price or float('inf'))
        if cheapest.name != best.name and cheapest.price:
            summary_parts.append(f"性价比最高的是 **{cheapest.name}**（¥{cheapest.price:.0f}）")

        # 最轻便
        lightest = None
        min_weight = float('inf')
        for item in items:
            w = self._extract_weight(item.specs.get("自重"))
            if w and w < min_weight:
                min_weight = w
                lightest = item

        if lightest and lightest.name != best.name:
            summary_parts.append(f"最轻便的是 **{lightest.name}**（{min_weight:.0f}g）")

        return "。".join(summary_parts) + "。"

    def _generate_recommendations(
        self,
        items: List[ComparisonItem],
        category: str
    ) -> Dict[str, str]:
        """生成选购建议（增强版）"""
        recommendations = {}

        if not items:
            return recommendations

        # 1. 综合最优
        best = max(items, key=lambda x: x.overall_score)
        recommendations["综合最优"] = best.name

        # 2. 预算有限
        cheapest = min(items, key=lambda x: x.price or float('inf'))
        if cheapest.price:
            recommendations["预算有限"] = cheapest.name

        # 3. 最轻便（长时间作钓）
        lightest = None
        min_weight = float('inf')
        for item in items:
            w = self._extract_weight(item.specs.get("自重"))
            if w and w < min_weight:
                min_weight = w
                lightest = item
        if lightest:
            recommendations["长时间作钓"] = lightest.name

        # 4. 品类特定建议
        if category in ("鱼竿", "路亚竿"):
            recommendations.update(self._rod_recommendations(items))
        elif category == "渔轮":
            recommendations.update(self._reel_recommendations(items))

        return recommendations

    def _rod_recommendations(self, items: List[ComparisonItem]) -> Dict[str, str]:
        """鱼竿特定推荐"""
        recommendations = {}

        # 远投能力（最长）
        lengths = []
        for item in items:
            l = self._extract_length(item.specs.get("长度"))
            if l:
                lengths.append((item, l))

        if lengths:
            longest = max(lengths, key=lambda x: x[1])
            shortest = min(lengths, key=lambda x: x[1])

            if longest[1] > shortest[1]:
                recommendations["岸钓/远投"] = longest[0].name
                recommendations["船钓/精细作钓"] = shortest[0].name

        return recommendations

    def _reel_recommendations(self, items: List[ComparisonItem]) -> Dict[str, str]:
        """渔轮特定推荐"""
        recommendations = {}

        for item in items:
            gear_ratio = item.specs.get("速比")
            if gear_ratio:
                try:
                    ratio = float(gear_ratio.split(":")[0])
                    if ratio >= 7.0 and "快速收线" not in recommendations:
                        recommendations["快速收线"] = item.name
                    elif ratio <= 5.5 and "力量型作钓" not in recommendations:
                        recommendations["力量型作钓"] = item.name
                except (ValueError, IndexError):
                    pass

        return recommendations

    # ========== 辅助方法 ==========

    @staticmethod
    def _extract_weight(weight_str) -> Optional[float]:
        """提取重量数值"""
        if not weight_str:
            return None
        if isinstance(weight_str, (int, float)):
            return float(weight_str)
        try:
            return float(str(weight_str).replace("g", "").strip())
        except ValueError:
            return None

    @staticmethod
    def _extract_length(length_str) -> Optional[float]:
        """提取长度数值"""
        if not length_str:
            return None
        if isinstance(length_str, (int, float)):
            return float(length_str)
        try:
            return float(str(length_str).replace("m", "").strip())
        except ValueError:
            return None
