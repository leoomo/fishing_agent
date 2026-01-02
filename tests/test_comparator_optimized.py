"""
装备对比功能优化测试

测试内容：
1. 常量一致性
2. 规格提取器
3. 搜索器
4. 差异分析器
5. 对比器综合功能
6. 格式化输出
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


# ========== 常量测试 ==========

class TestConstants:
    """常量一致性测试"""

    def test_power_order_complete(self):
        """硬度序列完整性"""
        from packages.agents.fishing.tools.lure.constants import POWER_ORDER

        assert "UUL" in POWER_ORDER
        assert "XXH" in POWER_ORDER
        assert POWER_ORDER.index("UL") < POWER_ORDER.index("XH")

    def test_action_order_complete(self):
        """调性序列完整性"""
        from packages.agents.fishing.tools.lure.constants import ACTION_ORDER

        assert "S" in ACTION_ORDER
        assert "XF" in ACTION_ORDER
        assert ACTION_ORDER.index("S") < ACTION_ORDER.index("XF")

    def test_action_name_map_consistency(self):
        """调性映射一致性"""
        from packages.agents.fishing.tools.lure.constants import (
            ACTION_ORDER, ACTION_NAME_MAP
        )

        # 所有映射值都应在 ACTION_ORDER 中
        for value in ACTION_NAME_MAP.values():
            assert value in ACTION_ORDER

    def test_compare_aspects_categories(self):
        """对比维度包含所有类别"""
        from packages.agents.fishing.tools.lure.constants import COMPARE_ASPECTS

        expected_categories = ["鱼竿", "路亚竿", "渔轮", "鱼线", "拟饵"]
        for cat in expected_categories:
            assert cat in COMPARE_ASPECTS


# ========== 规格提取器测试 ==========

class TestSpecsExtractor:
    """规格提取器测试"""

    def test_get_specs_rod(self):
        """鱼竿规格提取"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        mock_db = MagicMock()
        mock_db.execute.return_value = [{
            'length': 2.1,
            'power': 'ML',
            'action': 'F',
            'sections': 2,
            'weight': 98,
            'lure_weight_min': 3,
            'lure_weight_max': 15,
            'guide_type': '富士'
        }]

        extractor = SpecsExtractor(mock_db)
        specs = extractor.get_specs(1, "鱼竿")

        assert specs["长度"] == "2.1m"
        assert specs["硬度"] == "ML"
        assert specs["调性"] == "F"
        assert specs["自重"] == "98g"
        assert specs["适用饵范围"] == "3-15g"

    def test_get_specs_reel(self):
        """渔轮规格提取"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        mock_db = MagicMock()
        mock_db.execute.return_value = [{
            'reel_type': '纺车轮',
            'gear_ratio': '6.2:1',
            'bearings': '7+1',
            'weight': 200,
            'line_capacity': '0.6号/150m',
            'max_drag': 5.0,
            'retrieve_per_turn': 73
        }]

        extractor = SpecsExtractor(mock_db)
        specs = extractor.get_specs(1, "渔轮")

        assert specs["轮型"] == "纺车轮"
        assert specs["速比"] == "6.2:1"
        assert specs["最大刹车力"] == "5.0kg"

    def test_get_raw_specs(self):
        """原始规格获取"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        mock_db = MagicMock()
        mock_db.execute.return_value = [{'id': 1, 'power': 'ML'}]

        extractor = SpecsExtractor(mock_db)
        raw = extractor.get_raw_specs(1, "鱼竿")

        assert raw is not None
        assert raw['power'] == 'ML'


# ========== 搜索器测试 ==========

class TestEquipmentSearcher:
    """搜索器测试"""

    def test_exact_match_priority(self):
        """精确匹配优先"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        mock_db = MagicMock()
        mock_db.execute.return_value = [{'id': 1, 'name': '毒牙264ML', 'category': '鱼竿'}]

        searcher = EquipmentSearcher(mock_db)
        result = searcher.search_by_name("毒牙264ML")

        assert result is not None
        assert result['name'] == "毒牙264ML"

    def test_fuzzy_match_fallback(self):
        """模糊匹配回退"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        mock_db = MagicMock()
        # 精确匹配返回空
        mock_db.execute.side_effect = [
            [],  # 精确匹配
            [{'id': 1, 'name': '禧玛诺毒牙264ML', 'category': '鱼竿'}]  # 模糊匹配
        ]

        searcher = EquipmentSearcher(mock_db)
        result = searcher.search_by_name("毒牙")

        assert result is not None
        assert "毒牙" in result['name']

    def test_search_multiple(self):
        """批量搜索"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        mock_db = MagicMock()
        mock_db.execute.return_value = [{'id': 1, 'name': 'Test', 'category': '鱼竿'}]

        searcher = EquipmentSearcher(mock_db)
        results = searcher.search_multiple(["毒牙264ML", "月下美人76ML"])

        # 应该调用两次搜索
        assert len(results) == 2

    def test_similarity_calculation(self):
        """相似度计算"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        mock_db = MagicMock()
        searcher = EquipmentSearcher(mock_db)

        # 完全匹配
        eq1 = {'name': '毒牙264ML', 'model': None}
        score1 = searcher._similarity('毒牙264ML', eq1)

        # 部分匹配
        eq2 = {'name': '禧玛诺毒牙264', 'model': None}
        score2 = searcher._similarity('毒牙264ML', eq2)

        assert score1 > score2


# ========== 差异分析器测试 ==========

class TestDiffAnalyzer:
    """差异分析器测试"""

    @dataclass
    class MockItem:
        name: str
        specs: Dict[str, Any]
        price: Optional[float] = None

    def test_numeric_diff_analysis(self):
        """数值型差异分析"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"自重": "100g"}, 500),
            self.MockItem("装备B", {"自重": "150g"}, 800),
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

        items = [
            self.MockItem("装备A", {"硬度": "ML"}),
            self.MockItem("装备B", {"硬度": "H"}),
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

        items = [
            self.MockItem("装备A", {}, 300),
            self.MockItem("装备B", {}, 600),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        # 应检测到价格差异（100%差异）
        price_diff = next((d for d in all_diffs if d.spec_name == "价格"), None)
        assert price_diff is not None
        assert price_diff.diff_magnitude == "large"
        assert price_diff.best_item == "装备A"  # 更便宜
        assert "相差¥300" in price_diff.analysis

    def test_categorical_diff_analysis(self):
        """分类型差异分析"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"颜色": "红色"}),
            self.MockItem("装备B", {"颜色": "蓝色"}),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        # 应检测到颜色差异
        color_diff = next((d for d in all_diffs if d.spec_name == "颜色"), None)
        assert color_diff is not None
        assert color_diff.diff_type == "categorical"
        assert color_diff.diff_magnitude == "medium"

    def test_key_differences_limit(self):
        """关键差异限制为3个"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {
                "自重": "100g",
                "长度": "2.1m",
                "硬度": "ML",
                "调性": "F",
                "颜色": "红色"
            }, 500),
            self.MockItem("装备B", {
                "自重": "200g",
                "长度": "2.5m",
                "硬度": "H",
                "调性": "S",
                "颜色": "蓝色"
            }, 1000),
        ]

        all_diffs, key_diffs = analyzer.analyze_differences(items, "鱼竿")

        assert len(key_diffs) <= 3


# ========== 对比器测试 ==========

class TestEquipmentComparator:
    """对比器测试"""

    def test_compare_validation(self):
        """对比验证"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        mock_db = MagicMock()
        mock_db.execute.return_value = []

        comparator = EquipmentComparator(mock_db)

        with pytest.raises(ValueError, match="必须提供"):
            comparator.compare()

    def test_compare_min_items(self):
        """最少2个装备"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        mock_db = MagicMock()
        mock_db.execute.return_value = [{'id': 1, 'name': 'Test', 'category': '鱼竿'}]

        comparator = EquipmentComparator(mock_db)

        with pytest.raises(ValueError, match="至少需要2个"):
            comparator.compare(equipment_ids=[1])

    def test_compare_same_category(self):
        """同类型装备验证"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        mock_db = MagicMock()
        mock_db.execute.return_value = [
            {'id': 1, 'name': '鱼竿A', 'category': '鱼竿'},
            {'id': 2, 'name': '渔轮B', 'category': '渔轮'}
        ]

        comparator = EquipmentComparator(mock_db)

        with pytest.raises(ValueError, match="只能对比同类型"):
            comparator.compare(equipment_ids=[1, 2])

    def test_extract_weight(self):
        """重量提取"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        assert EquipmentComparator._extract_weight("100g") == 100.0
        assert EquipmentComparator._extract_weight("100") == 100.0
        assert EquipmentComparator._extract_weight(100) == 100.0
        assert EquipmentComparator._extract_weight(None) is None

    def test_extract_length(self):
        """长度提取"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        assert EquipmentComparator._extract_length("2.1m") == 2.1
        assert EquipmentComparator._extract_length("2.1") == 2.1
        assert EquipmentComparator._extract_length(2.1) == 2.1
        assert EquipmentComparator._extract_length(None) is None

    def test_get_brand_score(self):
        """品牌评分"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        assert comparator._get_brand_score("禧玛诺") == 95
        assert comparator._get_brand_score("SHIMANO") == 95
        assert comparator._get_brand_score("阿布") == 80
        assert comparator._get_brand_score("汉鼎") == 70
        assert comparator._get_brand_score("未知品牌") == 60
        assert comparator._get_brand_score(None) == 50


# ========== 格式化测试 ==========

class TestFormatters:
    """格式化测试"""

    def test_format_comparison_summary_table(self):
        """对比总结表格"""
        from packages.agents.fishing.tools.lure.formatters import format_comparison_summary_table
        from packages.agents.fishing.tools.lure.comparator import ComparisonResult, ComparisonItem
        from packages.agents.fishing.tools.lure.diff_analyzer import SpecDifference

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=899,
                specs={"长度": "2.1m", "硬度": "ML", "调性": "F"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="达亿瓦",
                price=1299,
                specs={"长度": "2.3m", "硬度": "M", "调性": "F"}
            )
        ]

        spec_differences = [
            SpecDifference(
                spec_name="价格",
                values={"装备A": "¥899", "装备B": "¥1299"},
                diff_type="numeric",
                diff_magnitude="large",
                diff_percent=44.5,
                best_item="装备A",
                worst_item="装备B",
                analysis="价格差异44%"
            )
        ]

        result = ComparisonResult(
            items=items,
            category="鱼竿",
            compare_aspects=["价格", "长度", "硬度"],
            recommendations={},
            spec_differences=spec_differences
        )

        output = format_comparison_summary_table(result)

        assert "对比总结" in output
        assert "差异项" in output
        assert "相同项" in output
        assert "装备A" in output
        assert "装备B" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
