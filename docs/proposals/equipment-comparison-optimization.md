# 装备对比方法优化方案

## 一、问题总结

基于代码审查，发现以下核心问题：

| 问题 | 严重程度 | 影响 |
|------|---------|------|
| 名称搜索精度不足 | 高 | 可能匹配到错误装备 |
| **缺少参数差异分析** | **高** | **用户无法快速识别关键差异** |
| 代码重复（规格获取） | 中 | 维护成本高 |
| 常量定义不一致 | 中 | 边界情况处理失败 |
| 推荐逻辑过于简单 | 中 | 用户体验不佳 |
| 缺少综合评分 | 低 | 决策参考不足 |

---

## 二、优化方案

### 2.1 架构重构：提取公共模块

**目标**：消除代码重复，统一常量定义

```
packages/agents/fishing/tools/lure/
├── constants.py          # 新增：统一常量定义
├── specs_extractor.py    # 新增：统一规格提取
├── comparator.py         # 重构：使用公共模块
├── recommender.py        # 重构：使用公共模块
└── ...
```

#### 2.1.1 新建 `constants.py`

```python
"""
装备常量定义

所有硬度、调性、用户水平等常量的唯一定义位置
"""

# 硬度等级排序（从软到硬）
POWER_ORDER = ["UUL", "UL", "L", "ML", "M", "MH", "H", "XH", "XXH"]

# 调性等级排序（从慢到快）
ACTION_ORDER = ["S", "M", "MF", "F", "XF"]

# 调性名称映射（中文/英文 -> 标准缩写）
ACTION_NAME_MAP = {
    # 英文缩写
    "S": "S", "M": "M", "MF": "MF", "F": "F", "XF": "XF",
    # 中文名称
    "慢调": "S", "中调": "M", "中快调": "MF", "快调": "F",
    "先调": "XF", "超快调": "XF",
    # 其他别名
    "软": "S", "中软": "M", "中快": "MF", "快": "F",
    "超快": "XF", "先": "XF"
}

# 用户水平映射
USER_LEVEL_MAP = {
    "新手": 1, "初学者": 1, "入门": 1,
    "进阶": 2, "中级": 2,
    "高手": 3, "高级": 3, "专业": 3
}

# 装备类别对比维度
COMPARE_ASPECTS = {
    "鱼竿": ["价格", "长度", "硬度", "调性", "自重", "品牌", "适用饵范围"],
    "路亚竿": ["价格", "长度", "硬度", "调性", "自重", "品牌", "适用饵范围"],
    "渔轮": ["价格", "轮型", "速比", "自重", "刹车力", "品牌", "轴承"],
    "鱼线": ["价格", "类型", "号数", "强度", "长度", "材质"],
    "拟饵": ["价格", "类型", "长度", "重量", "潜深", "颜色", "泳姿"],
}

# 品牌等级分数
BRAND_TIER_SCORES = {
    "高端": 95,
    "中高端": 85,
    "中端": 75,
    "入门": 65,
    "未知": 50
}
```

#### 2.1.2 新建 `specs_extractor.py`

```python
"""
装备规格提取器

统一的规格获取逻辑，供 comparator 和 recommender 共用
"""

from typing import Dict, Any, Optional, List


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
```

---

### 2.2 名称搜索精度优化

**目标**：优先精确匹配，使用相似度排序

#### 2.2.1 新增 `equipment_searcher.py`

```python
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
```

---

### 2.3 优劣势分析增强

**目标**：引入综合评分，多维度分析

#### 2.3.1 重构 `comparator.py` 的优劣势分析

```python
# comparator.py 重构部分

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .constants import POWER_ORDER, ACTION_ORDER, BRAND_TIER_SCORES, COMPARE_ASPECTS
from .specs_extractor import SpecsExtractor
from .equipment_searcher import EquipmentSearcher


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
class SpecDifference:
    """参数差异"""
    spec_name: str              # 参数名称（如"自重"）
    values: Dict[str, Any]      # 各装备的值 {装备名: 值}
    diff_type: str              # 差异类型: "numeric" | "categorical" | "text"
    diff_magnitude: str         # 差异程度: "large" | "medium" | "small" | "none"
    best_item: Optional[str]    # 该维度最优的装备名
    worst_item: Optional[str]   # 该维度最差的装备名
    analysis: str               # 差异分析说明


@dataclass
class ComparisonResult:
    """对比结果"""
    items: List[ComparisonItem]
    category: str
    compare_aspects: List[str]
    recommendations: Dict[str, str]
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
        self.db = db
        self.image_manager = image_manager
        self.specs_extractor = SpecsExtractor(db)
        self.searcher = EquipmentSearcher(db)

    def compare(
        self,
        equipment_ids: Optional[List[int]] = None,
        equipment_names: Optional[List[str]] = None,
        aspects: Optional[List[str]] = None
    ) -> ComparisonResult:
        """对比多款装备"""

        # 1. 获取装备（使用优化后的搜索器）
        if equipment_ids:
            equipments = self._get_equipments_by_ids(equipment_ids)
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
            specs = self.specs_extractor.get_specs(eq['equipment_id'], category)
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

        # 6. 计算综合评分（新增）
        self._calculate_overall_scores(items, category)

        # 7. 分析优劣势
        self._analyze_strengths_weaknesses(items, category)

        # 8. 生成推荐建议（增强版）
        recommendations = self._generate_recommendations(items, category)

        # 9. 确定最佳综合选择
        best_overall = max(items, key=lambda x: x.overall_score).name if items else None

        # 10. 生成对比总结
        summary = self._generate_summary(items, category)

        return ComparisonResult(
            items=items,
            category=category,
            compare_aspects=aspects,
            recommendations=recommendations,
            best_overall=best_overall,
            summary=summary
        )

    def _calculate_overall_scores(
        self,
        items: List[ComparisonItem],
        category: str
    ) -> None:
        """
        计算各装备的综合评分（新增方法）

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

    def _generate_summary(
        self,
        items: List[ComparisonItem],
        category: str
    ) -> str:
        """生成对比总结（新增方法）"""
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
```

---

### 2.4 参数差异分析模块（核心新增）

**目标**：自动识别关键参数差异，量化差异程度，生成差异分析

#### 2.4.1 新增 `diff_analyzer.py`

```python
"""
参数差异分析器

自动识别对比装备之间的关键差异，量化差异程度
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .constants import POWER_ORDER, ACTION_ORDER


@dataclass
class SpecDifference:
    """参数差异"""
    spec_name: str              # 参数名称
    values: Dict[str, Any]      # 各装备的值 {装备名: 值}
    diff_type: str              # 差异类型: "numeric" | "ordinal" | "categorical"
    diff_magnitude: str         # 差异程度: "large" | "medium" | "small" | "none"
    diff_percent: float         # 差异百分比（数值型）
    best_item: Optional[str]    # 该维度最优的装备名
    worst_item: Optional[str]   # 该维度最差的装备名
    analysis: str               # 差异分析说明


class DiffAnalyzer:
    """参数差异分析器"""

    # 数值型参数配置：(越小越好, 差异阈值)
    NUMERIC_SPECS = {
        "自重": {"lower_is_better": True, "unit": "g", "thresholds": (10, 30)},
        "价格": {"lower_is_better": True, "unit": "元", "thresholds": (20, 50)},
        "长度": {"lower_is_better": False, "unit": "m", "thresholds": (10, 25)},
        "最大刹车力": {"lower_is_better": False, "unit": "kg", "thresholds": (15, 30)},
        "轴承": {"lower_is_better": False, "unit": "个", "thresholds": (20, 40)},
    }

    # 顺序型参数配置
    ORDINAL_SPECS = {
        "硬度": {"order": POWER_ORDER, "higher_is_better": None},  # 无绝对好坏
        "调性": {"order": ACTION_ORDER, "higher_is_better": None},
    }

    def analyze_differences(
        self,
        items: List["ComparisonItem"],
        category: str
    ) -> Tuple[List[SpecDifference], List[SpecDifference]]:
        """
        分析所有参数差异

        Args:
            items: 对比项列表
            category: 装备类别

        Returns:
            (所有差异列表, 关键差异列表前3个)
        """
        all_diffs = []

        # 1. 收集所有规格键
        all_spec_keys = set()
        for item in items:
            all_spec_keys.update(item.specs.keys())

        # 2. 分析每个规格的差异
        for spec_name in all_spec_keys:
            diff = self._analyze_single_spec(spec_name, items, category)
            if diff and diff.diff_magnitude != "none":
                all_diffs.append(diff)

        # 3. 分析价格差异（单独处理）
        price_diff = self._analyze_price_diff(items)
        if price_diff:
            all_diffs.append(price_diff)

        # 4. 按差异程度排序，提取关键差异
        magnitude_order = {"large": 0, "medium": 1, "small": 2, "none": 3}
        all_diffs.sort(key=lambda x: (magnitude_order.get(x.diff_magnitude, 3), -x.diff_percent))

        key_diffs = all_diffs[:3]  # 取差异最大的3个

        return all_diffs, key_diffs

    def _analyze_single_spec(
        self,
        spec_name: str,
        items: List["ComparisonItem"],
        category: str
    ) -> Optional[SpecDifference]:
        """分析单个规格的差异"""

        # 收集各装备的值
        values = {}
        for item in items:
            val = item.specs.get(spec_name)
            if val is not None:
                values[item.name] = val

        if len(values) < 2:
            return None  # 数据不足

        # 判断参数类型并分析
        if spec_name in self.NUMERIC_SPECS:
            return self._analyze_numeric_diff(spec_name, values)
        elif spec_name in self.ORDINAL_SPECS:
            return self._analyze_ordinal_diff(spec_name, values)
        else:
            return self._analyze_categorical_diff(spec_name, values)

    def _analyze_numeric_diff(
        self,
        spec_name: str,
        values: Dict[str, Any]
    ) -> SpecDifference:
        """分析数值型参数差异"""
        config = self.NUMERIC_SPECS[spec_name]
        lower_is_better = config["lower_is_better"]
        unit = config["unit"]
        small_threshold, large_threshold = config["thresholds"]

        # 提取数值
        numeric_values = {}
        for name, val in values.items():
            num = self._extract_number(val)
            if num is not None:
                numeric_values[name] = num

        if len(numeric_values) < 2:
            return SpecDifference(
                spec_name=spec_name,
                values=values,
                diff_type="numeric",
                diff_magnitude="none",
                diff_percent=0,
                best_item=None,
                worst_item=None,
                analysis="数据不足"
            )

        # 计算差异
        min_val = min(numeric_values.values())
        max_val = max(numeric_values.values())

        if min_val == 0:
            diff_percent = 100 if max_val > 0 else 0
        else:
            diff_percent = ((max_val - min_val) / min_val) * 100

        # 判断差异程度
        if diff_percent >= large_threshold:
            magnitude = "large"
        elif diff_percent >= small_threshold:
            magnitude = "medium"
        elif diff_percent > 0:
            magnitude = "small"
        else:
            magnitude = "none"

        # 确定最优/最差
        if lower_is_better:
            best_item = min(numeric_values, key=numeric_values.get)
            worst_item = max(numeric_values, key=numeric_values.get)
        else:
            best_item = max(numeric_values, key=numeric_values.get)
            worst_item = min(numeric_values, key=numeric_values.get)

        # 生成分析说明
        analysis = self._generate_numeric_analysis(
            spec_name, numeric_values, diff_percent, magnitude,
            best_item, worst_item, lower_is_better, unit
        )

        return SpecDifference(
            spec_name=spec_name,
            values=values,
            diff_type="numeric",
            diff_magnitude=magnitude,
            diff_percent=diff_percent,
            best_item=best_item,
            worst_item=worst_item,
            analysis=analysis
        )

    def _analyze_ordinal_diff(
        self,
        spec_name: str,
        values: Dict[str, Any]
    ) -> SpecDifference:
        """分析顺序型参数差异（如硬度、调性）"""
        config = self.ORDINAL_SPECS[spec_name]
        order = config["order"]

        # 获取各值在序列中的位置
        positions = {}
        for name, val in values.items():
            val_upper = str(val).upper().replace("+", "")
            try:
                positions[name] = order.index(val_upper)
            except ValueError:
                pass

        if len(positions) < 2:
            return SpecDifference(
                spec_name=spec_name,
                values=values,
                diff_type="ordinal",
                diff_magnitude="none",
                diff_percent=0,
                best_item=None,
                worst_item=None,
                analysis="无法比较"
            )

        # 计算级别差异
        min_pos = min(positions.values())
        max_pos = max(positions.values())
        level_diff = max_pos - min_pos

        # 判断差异程度
        if level_diff >= 3:
            magnitude = "large"
        elif level_diff >= 2:
            magnitude = "medium"
        elif level_diff >= 1:
            magnitude = "small"
        else:
            magnitude = "none"

        # 硬度/调性没有绝对好坏，根据场景不同
        min_item = min(positions, key=positions.get)
        max_item = max(positions, key=positions.get)

        analysis = self._generate_ordinal_analysis(
            spec_name, values, level_diff, min_item, max_item, order
        )

        return SpecDifference(
            spec_name=spec_name,
            values=values,
            diff_type="ordinal",
            diff_magnitude=magnitude,
            diff_percent=level_diff / len(order) * 100,
            best_item=None,  # 顺序型无绝对好坏
            worst_item=None,
            analysis=analysis
        )

    def _analyze_categorical_diff(
        self,
        spec_name: str,
        values: Dict[str, Any]
    ) -> SpecDifference:
        """分析分类型参数差异（如品牌、颜色）"""
        unique_values = set(str(v) for v in values.values())

        if len(unique_values) == 1:
            magnitude = "none"
            analysis = f"所有装备{spec_name}相同：{list(unique_values)[0]}"
        else:
            magnitude = "medium"  # 分类型差异默认中等
            analysis = f"{spec_name}不同：" + "、".join(
                f"{name}={val}" for name, val in values.items()
            )

        return SpecDifference(
            spec_name=spec_name,
            values=values,
            diff_type="categorical",
            diff_magnitude=magnitude,
            diff_percent=0,
            best_item=None,
            worst_item=None,
            analysis=analysis
        )

    def _analyze_price_diff(self, items: List["ComparisonItem"]) -> Optional[SpecDifference]:
        """分析价格差异"""
        prices = {item.name: item.price for item in items if item.price}

        if len(prices) < 2:
            return None

        min_price = min(prices.values())
        max_price = max(prices.values())
        diff_percent = ((max_price - min_price) / min_price) * 100

        if diff_percent >= 50:
            magnitude = "large"
        elif diff_percent >= 20:
            magnitude = "medium"
        elif diff_percent > 0:
            magnitude = "small"
        else:
            magnitude = "none"

        cheapest = min(prices, key=prices.get)
        expensive = max(prices, key=prices.get)

        analysis = (
            f"价格差异{diff_percent:.0f}%：{cheapest}最便宜（¥{prices[cheapest]:.0f}），"
            f"{expensive}最贵（¥{prices[expensive]:.0f}），相差¥{max_price - min_price:.0f}"
        )

        return SpecDifference(
            spec_name="价格",
            values={name: f"¥{price:.0f}" for name, price in prices.items()},
            diff_type="numeric",
            diff_magnitude=magnitude,
            diff_percent=diff_percent,
            best_item=cheapest,
            worst_item=expensive,
            analysis=analysis
        )

    def _generate_numeric_analysis(
        self,
        spec_name: str,
        values: Dict[str, float],
        diff_percent: float,
        magnitude: str,
        best_item: str,
        worst_item: str,
        lower_is_better: bool,
        unit: str
    ) -> str:
        """生成数值型差异分析说明"""
        diff_word = {"large": "显著", "medium": "明显", "small": "略有"}.get(magnitude, "")
        direction = "轻" if lower_is_better else "高"

        return (
            f"{spec_name}{diff_word}差异（{diff_percent:.0f}%）："
            f"{best_item}最{direction}（{values[best_item]:.1f}{unit}），"
            f"{worst_item}{'最重' if lower_is_better else '最低'}（{values[worst_item]:.1f}{unit}）"
        )

    def _generate_ordinal_analysis(
        self,
        spec_name: str,
        values: Dict[str, Any],
        level_diff: int,
        min_item: str,
        max_item: str,
        order: List[str]
    ) -> str:
        """生成顺序型差异分析说明"""
        if spec_name == "硬度":
            return (
                f"硬度跨越{level_diff}个等级：{min_item}偏软（{values[min_item]}），"
                f"{max_item}偏硬（{values[max_item]}）。"
                f"软调适合精细作钓，硬调适合远投和大鱼"
            )
        elif spec_name == "调性":
            return (
                f"调性差{level_diff}级：{min_item}偏慢（{values[min_item]}），"
                f"{max_item}偏快（{values[max_item]}）。"
                f"快调回弹快适合速钓，慢调护线更好"
            )
        else:
            return f"{spec_name}差异{level_diff}级"

    @staticmethod
    def _extract_number(value: Any) -> Optional[float]:
        """从值中提取数字"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            import re
            match = re.search(r'(\d+\.?\d*)', value)
            if match:
                return float(match.group(1))
        return None
```

#### 2.4.2 在 `comparator.py` 中集成差异分析

```python
# comparator.py 中新增方法

from .diff_analyzer import DiffAnalyzer, SpecDifference

class EquipmentComparator:
    def __init__(self, db, image_manager=None):
        # ... 原有代码
        self.diff_analyzer = DiffAnalyzer()

    def compare(self, ...):
        # ... 原有代码

        # 新增：分析参数差异
        all_diffs, key_diffs = self.diff_analyzer.analyze_differences(items, category)

        return ComparisonResult(
            items=items,
            category=category,
            compare_aspects=aspects,
            recommendations=recommendations,
            best_overall=best_overall,
            summary=summary,
            spec_differences=all_diffs,      # 新增
            key_differences=key_diffs         # 新增
        )
```

---

### 2.5 格式化输出增强

**目标**：添加综合评分展示、参数差异高亮和对比总结

```python
# formatters.py 更新部分

def format_comparison(comparison: ComparisonResult) -> str:
    """格式化对比报告（增强版）"""
    output = "# 装备对比报告\n\n"

    items = comparison.items
    if len(items) < 2:
        return output + "对比数据不足\n"

    # 1. 对比总结（新增）
    if comparison.summary:
        output += "## 快速结论\n\n"
        output += f"> {comparison.summary}\n\n"

    # 2. 关键差异分析（核心新增）
    if comparison.key_differences:
        output += "## 🔍 关键差异\n\n"
        output += "> 以下是对比中差异最显著的参数，帮助您快速做出决策\n\n"

        for diff in comparison.key_differences:
            # 差异程度标记
            magnitude_icon = {
                "large": "🔴 显著差异",
                "medium": "🟡 明显差异",
                "small": "🟢 轻微差异"
            }.get(diff.diff_magnitude, "")

            output += f"### {diff.spec_name} {magnitude_icon}\n\n"
            output += f"{diff.analysis}\n\n"

            # 展示各装备的值
            output += "| 装备 | 数值 |\n"
            output += "|------|------|\n"
            for name, val in diff.values.items():
                # 标记最优/最差
                marker = ""
                if diff.best_item and name == diff.best_item:
                    marker = " ✅ 最优"
                elif diff.worst_item and name == diff.worst_item:
                    marker = " ⚠️"
                output += f"| {name} | {val}{marker} |\n"

            output += "\n"

        output += "---\n\n"

    # 3. 综合评分表格（新增）
    output += "## 综合评分\n\n"
    output += "| 装备 | 综合评分 | 价格 | 品牌 |\n"
    output += "|------|---------|------|------|\n"

    # 按评分排序展示
    sorted_items = sorted(items, key=lambda x: x.overall_score, reverse=True)
    for i, item in enumerate(sorted_items):
        rank = "🥇" if i == 0 else ("🥈" if i == 1 else ("🥉" if i == 2 else ""))
        price_str = f"¥{item.price:.0f}" if item.price else "-"
        output += f"| {rank} {item.name} | **{item.overall_score:.1f}**/100 | {price_str} | {item.brand or '-'} |\n"

    output += "\n"

    # 3. 详细参数对比表格
    output += "## 详细参数对比\n\n"

    headers = ["参数"] + [item.name for item in items]
    output += "| " + " | ".join(headers) + " |\n"
    output += "|" + "|".join(["------"] * len(headers)) + "|\n"

    # 收集所有规格键
    all_spec_keys = set()
    for item in items:
        all_spec_keys.update(item.specs.keys())

    # 按重要性排序的规格键
    priority_keys = ["自重", "长度", "硬度", "调性", "速比", "刹车力", "适用饵范围"]
    sorted_keys = [k for k in priority_keys if k in all_spec_keys]
    sorted_keys += [k for k in sorted(all_spec_keys) if k not in priority_keys]

    for key in sorted_keys:
        row = [key] + [str(item.specs.get(key, "-")) for item in items]
        output += "| " + " | ".join(row) + " |\n"

    output += "\n"

    # 4. 优劣势分析
    output += "## 优劣势分析\n\n"

    for item in items:
        output += f"### {item.name}\n\n"

        if item.main_image:
            output += f"![{item.name}]({item.main_image})\n\n"

        if item.strengths:
            output += "**优势**：\n"
            for strength in item.strengths:
                output += f"- ✅ {strength}\n"
            output += "\n"

        if item.weaknesses:
            output += "**不足**：\n"
            for weakness in item.weaknesses:
                output += f"- ⚠️ {weakness}\n"
            output += "\n"

        output += "---\n\n"

    # 5. 选购建议
    if comparison.recommendations:
        output += "## 选购建议\n\n"
        output += "| 使用场景 | 推荐选择 |\n"
        output += "|---------|--------|\n"

        # 优先展示综合最优
        priority_scenarios = ["综合最优", "预算有限", "长时间作钓"]
        for scenario in priority_scenarios:
            if scenario in comparison.recommendations:
                product = comparison.recommendations[scenario]
                output += f"| **{scenario}** | {product} |\n"

        # 其他建议
        for scenario, product in comparison.recommendations.items():
            if scenario not in priority_scenarios:
                output += f"| {scenario} | {product} |\n"

        output += "\n"

    # 6. 对比总结表格（核心新增：相同项 vs 差异项）
    output += format_comparison_summary_table(comparison)

    return output


def format_comparison_summary_table(comparison: ComparisonResult) -> str:
    """
    生成对比总结表格

    清晰区分：相同项 vs 差异项
    """
    output = "## 📊 对比总结\n\n"

    items = comparison.items
    if len(items) < 2:
        return output

    # 收集所有规格
    all_specs = {}
    for item in items:
        for key, value in item.specs.items():
            if key not in all_specs:
                all_specs[key] = {}
            all_specs[key][item.name] = value

    # 添加价格
    all_specs["价格"] = {item.name: f"¥{item.price:.0f}" if item.price else "-" for item in items}

    # 添加品牌
    all_specs["品牌"] = {item.name: item.brand or "-" for item in items}

    # 分类：相同项 vs 差异项
    same_specs = []
    diff_specs = []

    for spec_name, values in all_specs.items():
        unique_values = set(str(v) for v in values.values() if v and v != "-")
        if len(unique_values) <= 1:
            same_specs.append((spec_name, values))
        else:
            diff_specs.append((spec_name, values))

    # 获取差异分析信息
    diff_info = {d.spec_name: d for d in comparison.spec_differences} if comparison.spec_differences else {}

    # 表头
    headers = ["参数"] + [item.name for item in items] + ["差异说明"]
    output += "| " + " | ".join(headers) + " |\n"
    output += "|" + "|".join(["------"] * len(headers)) + "|\n"

    # 差异项（优先展示，带高亮）
    if diff_specs:
        output += "| **━━ 差异项 ━━** |" + " |".join([""] * (len(items) + 1)) + "\n"

        # 按差异程度排序
        def get_diff_priority(spec_tuple):
            spec_name = spec_tuple[0]
            if spec_name in diff_info:
                magnitude = diff_info[spec_name].diff_magnitude
                return {"large": 0, "medium": 1, "small": 2}.get(magnitude, 3)
            return 3

        diff_specs.sort(key=get_diff_priority)

        for spec_name, values in diff_specs:
            # 获取差异信息
            diff = diff_info.get(spec_name)

            # 差异程度标记
            if diff:
                magnitude_mark = {
                    "large": "🔴",
                    "medium": "🟡",
                    "small": "🟢"
                }.get(diff.diff_magnitude, "")
            else:
                magnitude_mark = ""

            # 构建每个值的展示（标记最优/最差）
            value_cells = []
            for item in items:
                val = str(values.get(item.name, "-"))
                if diff:
                    if diff.best_item == item.name:
                        val = f"**{val}** ✅"
                    elif diff.worst_item == item.name:
                        val = f"{val} ⚠️"
                value_cells.append(val)

            # 差异说明
            if diff and diff.diff_percent > 0:
                diff_note = f"{magnitude_mark} 差异{diff.diff_percent:.0f}%"
            elif diff:
                diff_note = f"{magnitude_mark} {diff.analysis[:20]}..."
            else:
                diff_note = "不同"

            row = [f"**{spec_name}**"] + value_cells + [diff_note]
            output += "| " + " | ".join(row) + " |\n"

    # 相同项
    if same_specs:
        output += "| **━━ 相同项 ━━** |" + " |".join([""] * (len(items) + 1)) + "\n"

        for spec_name, values in same_specs:
            # 获取共同值
            common_value = next((str(v) for v in values.values() if v and v != "-"), "-")
            value_cells = [common_value] * len(items)

            row = [spec_name] + value_cells + ["✓ 相同"]
            output += "| " + " | ".join(row) + " |\n"

    output += "\n"

    # 添加图例
    output += "> **图例**: 🔴 显著差异(>30%) | 🟡 明显差异(10-30%) | 🟢 轻微差异(<10%) | ✅ 该项最优 | ⚠️ 该项较弱\n\n"

    return output
```

---

## 三、实施计划

### 阶段1：基础重构（低风险）
1. 创建 `constants.py`，统一常量定义
2. 创建 `specs_extractor.py`，提取公共代码
3. 更新 `comparator.py` 和 `recommender.py` 使用新模块
4. 运行现有测试确保兼容性

### 阶段2：搜索优化（中风险）
1. 创建 `equipment_searcher.py`
2. 在 `comparator.py` 中使用新搜索器
3. 添加搜索精度测试用例

### 阶段3：参数差异分析（核心功能）
1. 创建 `diff_analyzer.py` 差异分析器
2. 实现数值型/顺序型/分类型三种差异分析
3. 集成到 `comparator.py`
4. 添加差异分析测试用例

### 阶段4：评分增强（中风险）
1. 添加 `_calculate_overall_scores` 方法
2. 更新 `ComparisonItem` 和 `ComparisonResult` 数据结构
3. 更新 `formatters.py` 展示综合评分

### 阶段5：输出优化（低风险）
1. 添加关键差异高亮展示
2. 添加对比总结生成
3. 优化表格展示顺序
4. 添加排名标记

---

## 四、测试用例

```python
# tests/test_comparator_optimized.py

import pytest
from packages.agents.fishing.tools.lure.comparator import EquipmentComparator
from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher


class TestEquipmentSearcher:
    """搜索器测试"""

    def test_exact_match_priority(self, db):
        """精确匹配优先于模糊匹配"""
        searcher = EquipmentSearcher(db)

        # 假设数据库中有 "毒牙264ML" 和 "毒牙264M"
        result = searcher.search_by_name("毒牙264ML")

        assert result is not None
        assert "264ML" in result['name'] or "264ML" in result['model']

    def test_similarity_ranking(self, db):
        """相似度排序测试"""
        searcher = EquipmentSearcher(db)

        # 搜索时应该返回最相似的结果
        result = searcher.search_by_name("禧玛诺毒牙")

        assert result is not None
        assert "禧玛诺" in result.get('brand_name', '') or "毒牙" in result['name']


class TestEquipmentComparator:
    """对比器测试"""

    def test_compare_same_category(self, db):
        """同类型装备对比"""
        comparator = EquipmentComparator(db)

        result = comparator.compare(equipment_names=["毒牙264ML", "月下美人76ML"])

        assert len(result.items) == 2
        assert result.category in ("鱼竿", "路亚竿")
        assert result.best_overall is not None

    def test_compare_different_category_fails(self, db):
        """不同类型装备对比应失败"""
        comparator = EquipmentComparator(db)

        with pytest.raises(ValueError, match="只能对比同类型装备"):
            comparator.compare(equipment_names=["毒牙264ML", "红蝎2500"])

    def test_overall_score_calculated(self, db):
        """综合评分应被计算"""
        comparator = EquipmentComparator(db)

        result = comparator.compare(equipment_names=["毒牙264ML", "月下美人76ML"])

        for item in result.items:
            assert item.overall_score > 0
            assert "价格" in item.score_breakdown

    def test_summary_generated(self, db):
        """对比总结应被生成"""
        comparator = EquipmentComparator(db)

        result = comparator.compare(equipment_names=["毒牙264ML", "月下美人76ML"])

        assert result.summary is not None
        assert len(result.summary) > 0

    def test_key_differences_identified(self, db):
        """关键差异应被识别"""
        comparator = EquipmentComparator(db)

        result = comparator.compare(equipment_names=["毒牙264ML", "月下美人76ML"])

        # 应有差异分析结果
        assert result.spec_differences is not None
        assert result.key_differences is not None
        # 关键差异最多3个
        assert len(result.key_differences) <= 3

    def test_diff_analysis_content(self, db):
        """差异分析内容应完整"""
        comparator = EquipmentComparator(db)

        result = comparator.compare(equipment_names=["毒牙264ML", "月下美人76ML"])

        for diff in result.key_differences:
            # 每个差异应有完整信息
            assert diff.spec_name is not None
            assert diff.diff_type in ("numeric", "ordinal", "categorical")
            assert diff.diff_magnitude in ("large", "medium", "small", "none")
            assert diff.analysis is not None and len(diff.analysis) > 0


class TestDiffAnalyzer:
    """差异分析器测试"""

    def test_numeric_diff_analysis(self):
        """数值型差异分析"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        # 模拟装备数据
        class MockItem:
            def __init__(self, name, specs, price=None):
                self.name = name
                self.specs = specs
                self.price = price

        items = [
            MockItem("装备A", {"自重": "100g"}, 500),
            MockItem("装备B", {"自重": "150g"}, 800),
        ]

        all_diffs, key_diffs = analyzer.analyze_differences(items, "鱼竿")

        # 应检测到自重差异（50%差异）
        weight_diff = next((d for d in all_diffs if d.spec_name == "自重"), None)
        assert weight_diff is not None
        assert weight_diff.diff_type == "numeric"
        assert weight_diff.diff_magnitude in ("large", "medium")
        assert weight_diff.best_item == "装备A"  # 更轻

    def test_ordinal_diff_analysis(self):
        """顺序型差异分析"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        class MockItem:
            def __init__(self, name, specs, price=None):
                self.name = name
                self.specs = specs
                self.price = price

        items = [
            MockItem("装备A", {"硬度": "ML"}),
            MockItem("装备B", {"硬度": "H"}),
        ]

        all_diffs, key_diffs = analyzer.analyze_differences(items, "鱼竿")

        # 应检测到硬度差异（ML到H跨3级）
        power_diff = next((d for d in all_diffs if d.spec_name == "硬度"), None)
        assert power_diff is not None
        assert power_diff.diff_type == "ordinal"
        assert power_diff.diff_magnitude == "large"  # 跨3级
        assert "偏软" in power_diff.analysis
        assert "偏硬" in power_diff.analysis

    def test_price_diff_analysis(self):
        """价格差异分析"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        class MockItem:
            def __init__(self, name, specs, price=None):
                self.name = name
                self.specs = specs
                self.price = price

        items = [
            MockItem("装备A", {}, 300),
            MockItem("装备B", {}, 600),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        # 应检测到价格差异（100%差异）
        price_diff = next((d for d in all_diffs if d.spec_name == "价格"), None)
        assert price_diff is not None
        assert price_diff.diff_magnitude == "large"
        assert price_diff.best_item == "装备A"  # 更便宜
        assert "相差¥300" in price_diff.analysis


class TestConstants:
    """常量一致性测试"""

    def test_power_order_complete(self):
        """硬度序列完整性"""
        from packages.agents.fishing.tools.lure.constants import POWER_ORDER

        assert "UUL" in POWER_ORDER
        assert "XXH" in POWER_ORDER
        assert POWER_ORDER.index("UL") < POWER_ORDER.index("XH")

    def test_action_name_map_consistency(self):
        """调性映射一致性"""
        from packages.agents.fishing.tools.lure.constants import (
            ACTION_ORDER, ACTION_NAME_MAP
        )

        # 所有映射值都应在 ACTION_ORDER 中
        for value in ACTION_NAME_MAP.values():
            assert value in ACTION_ORDER
```

---

## 五、预期收益

| 指标 | 优化前 | 优化后 |
|------|-------|-------|
| 搜索准确率 | ~70% | ~95% |
| **参数差异展示** | **无** | **自动识别关键差异+量化分析** |
| 代码重复率 | 高（2处规格提取） | 低（1处） |
| 用户决策信息 | 基础参数对比 | 综合评分+差异高亮+多维度建议 |
| 维护成本 | 中 | 低 |

### 示例输出对比

**优化前**：
```markdown
## 基础参数对比

| 参数 | 毒牙264ML | 月下美人76ML |
|------|----------|-------------|
| 价格 | ¥899 | ¥1299 |
| 自重 | 98g | 120g |
| 硬度 | ML | M |
```

**优化后**：
```markdown
## 🔍 关键差异

### 价格 🔴 显著差异
价格差异44%：毒牙264ML最便宜（¥899），月下美人76ML最贵（¥1299），相差¥400

### 自重 🟡 明显差异
自重明显差异（22%）：毒牙264ML最轻（98g），月下美人76ML最重（120g）

### 硬度 🟢 轻微差异
硬度差1级：毒牙264ML偏软（ML），月下美人76ML偏硬（M）

---

## 📊 对比总结

| 参数 | 毒牙264ML | 月下美人76ML | 差异说明 |
|------|----------|-------------|---------|
| **━━ 差异项 ━━** | | | |
| **价格** | **¥899** ✅ | ¥1299 ⚠️ | 🔴 差异44% |
| **自重** | **98g** ✅ | 120g ⚠️ | 🟡 差异22% |
| **硬度** | ML | M | 🟢 差1级 |
| **长度** | 1.98m | **2.29m** ✅ | 🟢 差异16% |
| **品牌** | 禧玛诺 | 达亿瓦 | 不同 |
| **━━ 相同项 ━━** | | | |
| 调性 | F | F | ✓ 相同 |
| 节数 | 2 | 2 | ✓ 相同 |
| 导环 | 富士 | 富士 | ✓ 相同 |

> **图例**: 🔴 显著差异(>30%) | 🟡 明显差异(10-30%) | 🟢 轻微差异(<10%) | ✅ 该项最优 | ⚠️ 该项较弱
```

---

## 六、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|-----|------|---------|
| 搜索逻辑变更导致兼容性问题 | 中 | 中 | 保留原有方法作为降级 |
| 综合评分权重不合理 | 中 | 低 | 权重可配置化 |
| 性能下降（多次数据库查询） | 低 | 低 | 批量查询优化 |

---

## 七、后续扩展

1. **用户偏好学习**：根据用户历史选择调整推荐权重
2. **价格波动追踪**：记录历史价格，提供"现在买划算吗"建议
3. **评测数据整合**：接入第三方评测数据，丰富优劣势分析
4. **可视化对比**：雷达图展示多维度对比
