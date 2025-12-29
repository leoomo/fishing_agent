"""
参数差异分析器

自动识别对比装备之间的关键差异，量化差异程度
"""

from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import re

from .constants import POWER_ORDER, ACTION_ORDER

if TYPE_CHECKING:
    from .comparator import ComparisonItem


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
        "重量": {"lower_is_better": True, "unit": "g", "thresholds": (15, 35)},
        "强度": {"lower_is_better": False, "unit": "lb", "thresholds": (15, 30)},
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

        if min_price == 0:
            diff_percent = 100 if max_price > 0 else 0
        else:
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
            match = re.search(r'(\d+\.?\d*)', value)
            if match:
                return float(match.group(1))
        return None
