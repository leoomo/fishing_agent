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
    """搜索器测试（使用 Repository mock）"""

    def test_exact_match_priority(self):
        """精确匹配优先"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        # Mock session 和 Repository
        mock_session = MagicMock()

        with patch('apps.api.orm.session.get_session_factory') as mock_factory, \
             patch('apps.api.orm.repositories.EquipmentRepository') as mock_repo_class:

            mock_factory.return_value = MagicMock(return_value=mock_session)
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            # 模拟精确匹配返回结果
            mock_equipment = MagicMock()
            mock_repo.search_by_name_exact.return_value = mock_equipment
            mock_repo.to_dict.return_value = {'id': 1, 'name': '毒牙264ML', 'category': '鱼竿'}

            searcher = EquipmentSearcher()
            result = searcher.search_by_name("毒牙264ML")

            assert result is not None
            assert result['name'] == "毒牙264ML"
            mock_repo.search_by_name_exact.assert_called_once_with("毒牙264ML", None)

    def test_fuzzy_match_fallback(self):
        """模糊匹配回退"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        mock_session = MagicMock()

        with patch('apps.api.orm.session.get_session_factory') as mock_factory, \
             patch('apps.api.orm.repositories.EquipmentRepository') as mock_repo_class:

            mock_factory.return_value = MagicMock(return_value=mock_session)
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            # 精确匹配返回空，模糊匹配返回结果
            mock_repo.search_by_name_exact.return_value = None
            mock_equipment = MagicMock()
            mock_repo.search_by_name_fuzzy.return_value = [mock_equipment]
            mock_repo.to_dict.return_value = {'id': 1, 'name': '禧玛诺毒牙264ML', 'category': '鱼竿'}

            searcher = EquipmentSearcher()
            result = searcher.search_by_name("毒牙")

            assert result is not None
            assert "毒牙" in result['name']
            mock_repo.search_by_name_fuzzy.assert_called_once()

    def test_search_multiple(self):
        """批量搜索"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        mock_session = MagicMock()

        with patch('apps.api.orm.session.get_session_factory') as mock_factory, \
             patch('apps.api.orm.repositories.EquipmentRepository') as mock_repo_class:

            mock_factory.return_value = MagicMock(return_value=mock_session)
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            # 模拟每次搜索都返回结果
            mock_equipment = MagicMock()
            mock_repo.search_by_name_exact.return_value = mock_equipment
            mock_repo.to_dict.return_value = {'id': 1, 'name': 'Test', 'category': '鱼竿'}

            searcher = EquipmentSearcher()
            results = searcher.search_multiple(["毒牙264ML", "月下美人76ML"])

            # 应该返回两个结果
            assert len(results) == 2

    def test_similarity_calculation(self):
        """相似度计算"""
        from packages.agents.fishing.tools.lure.equipment_searcher import EquipmentSearcher

        mock_session = MagicMock()

        with patch('apps.api.orm.session.get_session_factory') as mock_factory, \
             patch('apps.api.orm.repositories.EquipmentRepository') as mock_repo_class:

            mock_factory.return_value = MagicMock(return_value=mock_session)
            mock_repo = MagicMock()
            mock_repo_class.return_value = mock_repo

            searcher = EquipmentSearcher()

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

        with patch('packages.agents.fishing.tools.lure.comparator.EquipmentSearcher') as mock_searcher_class:
            mock_searcher = MagicMock()
            mock_searcher_class.return_value = mock_searcher
            mock_searcher.search_by_ids.return_value = []

            comparator = EquipmentComparator(mock_db)

            with pytest.raises(ValueError, match="必须提供"):
                comparator.compare()

    def test_compare_min_items(self):
        """最少2个装备"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        mock_db = MagicMock()

        with patch('packages.agents.fishing.tools.lure.comparator.EquipmentSearcher') as mock_searcher_class:
            mock_searcher = MagicMock()
            mock_searcher_class.return_value = mock_searcher
            # 只返回一个装备
            mock_searcher.search_by_ids.return_value = [
                {'id': 1, 'name': 'Test', 'category': '鱼竿'}
            ]

            comparator = EquipmentComparator(mock_db)

            with pytest.raises(ValueError, match="至少需要2个"):
                comparator.compare(equipment_ids=[1])

    def test_compare_same_category(self):
        """同类型装备验证"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        mock_db = MagicMock()

        with patch('packages.agents.fishing.tools.lure.comparator.EquipmentSearcher') as mock_searcher_class:
            mock_searcher = MagicMock()
            mock_searcher_class.return_value = mock_searcher
            # 返回两个不同类型的装备
            mock_searcher.search_by_ids.return_value = [
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


# ========== EquipmentComparator 完整测试 ==========

class TestEquipmentComparatorComplete:
    """EquipmentComparator 完整测试"""

    @dataclass
    class MockItem:
        name: str
        specs: Dict[str, Any]
        price: Optional[float] = None
        brand: Optional[str] = None
        category: str = "鱼竿"

    def test_calculate_overall_scores_rods(self):
        """鱼竿综合评分计算"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=500,
                specs={"自重": "100g", "调性": "F"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="汉鼎",
                price=1000,
                specs={"自重": "150g", "调性": "S"}
            )
        ]

        comparator._calculate_overall_scores(items, "鱼竿")

        # 装备A 应该评分更高（��便宜、更轻、品牌更好）
        assert items[0].overall_score > items[1].overall_score
        assert items[0].overall_score > 0
        assert items[1].overall_score > 0
        # 评分分解应该存在
        assert "价格" in items[0].score_breakdown
        assert "品牌" in items[0].score_breakdown

    def test_calculate_overall_scores_reels(self):
        """渔轮综合评分计算"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="渔轮A",
                category="渔轮",
                brand="达亿瓦",
                price=800,
                specs={"自重": "200g", "速比": "7.2:1"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="渔轮B",
                category="渔轮",
                brand="光威",
                price=300,
                specs={"自重": "250g", "速比": "5.2:1"}
            )
        ]

        comparator._calculate_overall_scores(items, "渔轮")

        # 两者都应有评分
        assert items[0].overall_score > 0
        assert items[1].overall_score > 0
        # 速比分数应被计算
        assert "速比" in items[0].score_breakdown

    def test_calculate_rod_scores(self):
        """鱼竿特定评分"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        item = ComparisonItem(
            equipment_id=1,
            name="测试竿",
            category="鱼竿",
            brand="禧玛诺",
            price=500,
            specs={"调性": "XF"}  # 最快调性
        )

        scores = comparator._calculate_rod_scores(item)

        assert "调性" in scores
        # XF 应该得到较高分数
        assert scores["调性"] >= 80

    def test_calculate_reel_scores(self):
        """渔轮特定评分"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        # 高速比渔轮
        item1 = ComparisonItem(
            equipment_id=1,
            name="高速轮",
            category="渔轮",
            brand="禧玛诺",
            price=500,
            specs={"速比": "7.5:1"}
        )

        scores1 = comparator._calculate_reel_scores(item1)
        assert "速比" in scores1
        assert scores1["速比"] == 90  # 高速比得90分

        # 低速比渔轮
        item2 = ComparisonItem(
            equipment_id=2,
            name="低速轮",
            category="渔轮",
            brand="禧玛诺",
            price=500,
            specs={"速比": "5.0:1"}
        )

        scores2 = comparator._calculate_reel_scores(item2)
        assert scores2["速比"] == 70  # 低速比得70分

    def test_analyze_strengths_weaknesses(self):
        """优劣势分析"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=300,
                specs={"自重": "80g", "长度": "2.4m", "调性": "F"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="汉鼎",
                price=800,
                specs={"自重": "120g", "长度": "2.1m", "调性": "MF"}
            )
        ]

        comparator._analyze_strengths_weaknesses(items, "鱼竿")

        # 装备A 应该有 "价格最低" 和 "最轻便" 优势
        assert "价格最低" in items[0].strengths
        assert "最轻便" in items[0].strengths
        # 装备A 有更长的竿
        assert any("长度更长" in s or "远投" in s for s in items[0].strengths)
        # 装备B 应该有价格最高的劣势
        assert "价格最高" in items[1].weaknesses

    def test_generate_summary(self):
        """总结生成"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="最佳装备",
                category="鱼竿",
                brand="禧玛诺",
                price=500,
                specs={"自重": "100g"},
                overall_score=85.0
            ),
            ComparisonItem(
                equipment_id=2,
                name="经济装备",
                category="鱼竿",
                brand="汉鼎",
                price=200,
                specs={"自重": "150g"},
                overall_score=70.0
            )
        ]

        summary = comparator._generate_summary(items, "鱼竿")

        assert "最佳装备" in summary
        assert "85.0" in summary  # 评分
        assert "经济装备" in summary  # 性价比最高

    def test_generate_recommendations(self):
        """推荐生成"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="高端装备",
                category="鱼竿",
                brand="禧玛诺",
                price=1000,
                specs={"自重": "90g", "长度": "2.4m"},
                overall_score=90.0
            ),
            ComparisonItem(
                equipment_id=2,
                name="入门装备",
                category="鱼竿",
                brand="汉鼎",
                price=200,
                specs={"自重": "130g", "长度": "2.1m"},
                overall_score=65.0
            )
        ]

        recommendations = comparator._generate_recommendations(items, "鱼竿")

        assert "综合最优" in recommendations
        assert recommendations["综合最优"] == "高端装备"
        assert "预算有限" in recommendations
        assert recommendations["预算有限"] == "入门装备"
        assert "长时间作钓" in recommendations
        assert recommendations["长时间作钓"] == "高端装备"  # 更轻

    def test_rod_recommendations(self):
        """鱼竿特定推荐"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="远投竿",
                category="鱼竿",
                brand="禧玛诺",
                price=800,
                specs={"长度": "2.7m"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="短竿",
                category="鱼竿",
                brand="达亿瓦",
                price=600,
                specs={"长度": "1.8m"}
            )
        ]

        recommendations = comparator._rod_recommendations(items)

        assert "岸钓/远投" in recommendations
        assert recommendations["岸钓/远投"] == "远投竿"
        assert "船钓/精细作钓" in recommendations
        assert recommendations["船钓/精细作钓"] == "短竿"

    def test_reel_recommendations(self):
        """渔轮特定推荐"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="高速轮",
                category="渔轮",
                brand="禧玛诺",
                price=800,
                specs={"速比": "7.5:1"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="力量轮",
                category="渔轮",
                brand="达亿瓦",
                price=600,
                specs={"速比": "5.2:1"}
            )
        ]

        recommendations = comparator._reel_recommendations(items)

        assert "快速收线" in recommendations
        assert recommendations["快速收线"] == "高速轮"
        assert "力量型作钓" in recommendations
        assert recommendations["力量型作钓"] == "力量轮"

    def test_compare_max_items(self):
        """最大5个装备限制"""
        from packages.agents.fishing.tools.lure.comparator import EquipmentComparator

        mock_db = MagicMock()

        with patch('packages.agents.fishing.tools.lure.comparator.EquipmentSearcher') as mock_searcher_class:
            mock_searcher = MagicMock()
            mock_searcher_class.return_value = mock_searcher
            # 返回6个装备
            mock_searcher.search_by_ids.return_value = [
                {'id': i, 'name': f'装备{i}', 'category': '鱼竿'}
                for i in range(6)
            ]

            comparator = EquipmentComparator(mock_db)

            with pytest.raises(ValueError, match="不能超过5个"):
                comparator.compare(equipment_ids=[1, 2, 3, 4, 5, 6])

    def test_compare_with_missing_specs(self):
        """缺失规格处理"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=500,
                specs={"自重": "100g"}  # 有自重
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="汉鼎",
                price=300,
                specs={}  # 无规格
            )
        ]

        # 不应抛出异常
        comparator._calculate_overall_scores(items, "鱼竿")
        comparator._analyze_strengths_weaknesses(items, "鱼竿")

        assert items[0].overall_score > 0
        assert items[1].overall_score > 0

    def test_compare_with_missing_price(self):
        """缺失价格处理"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=None,  # 无价格
                specs={"自重": "100g"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="汉鼎",
                price=300,
                specs={"自重": "150g"}
            )
        ]

        # 不应抛出异常
        comparator._calculate_overall_scores(items, "鱼竿")
        recommendations = comparator._generate_recommendations(items, "鱼竿")

        assert items[0].overall_score > 0
        # 预算有限推荐应该选有价格的
        assert "预算有限" in recommendations
        assert recommendations["预算有限"] == "装备B"

    def test_calculate_scores_single_item(self):
        """单个装备不计算评分"""
        from packages.agents.fishing.tools.lure.comparator import (
            EquipmentComparator, ComparisonItem
        )

        mock_db = MagicMock()
        comparator = EquipmentComparator(mock_db)

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=500,
                specs={"自重": "100g"}
            )
        ]

        comparator._calculate_overall_scores(items, "鱼竿")

        # 单个装备不应被修改
        assert items[0].overall_score == 0.0


# ========== DiffAnalyzer 完整测试 ==========

class TestDiffAnalyzerComplete:
    """DiffAnalyzer 完整测试"""

    @dataclass
    class MockItem:
        name: str
        specs: Dict[str, Any]
        price: Optional[float] = None

    def test_analyze_differences_full(self):
        """完整差异分析流程"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"自重": "100g", "硬度": "ML", "颜色": "红色"}, 500),
            self.MockItem("装备B", {"自重": "150g", "硬度": "H", "颜色": "蓝色"}, 800),
        ]

        all_diffs, key_diffs = analyzer.analyze_differences(items, "鱼竿")

        # 应包含自重、硬度、颜色、价格的差异
        spec_names = [d.spec_name for d in all_diffs]
        assert "自重" in spec_names
        assert "硬度" in spec_names
        assert "颜色" in spec_names
        assert "价格" in spec_names

        # 关键差异最多3个
        assert len(key_diffs) <= 3

    def test_numeric_diff_same_values(self):
        """数值相同时返回 none"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"自重": "100g"}),
            self.MockItem("装备B", {"自重": "100g"}),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        weight_diff = next((d for d in all_diffs if d.spec_name == "自重"), None)
        # 相同值时差异程度为 none，不应出现在结果中
        assert weight_diff is None or weight_diff.diff_magnitude == "none"

    def test_numeric_diff_zero_value(self):
        """零值处理 - 价格为0被视为无价格信息"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        # 价格为0被视为无效/未知价格，会被过滤
        items = [
            self.MockItem("装备A", {}, 0),  # 零价格 - 会被过滤
            self.MockItem("装备B", {}, 500),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        # 由于只有一个有效价格，不会产生价格差异
        price_diff = next((d for d in all_diffs if d.spec_name == "价格"), None)
        assert price_diff is None  # 无法比较

    def test_numeric_diff_low_vs_high_price(self):
        """低价与高价对比"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {}, 100),  # 低价
            self.MockItem("装备B", {}, 500),  # 高价
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        price_diff = next((d for d in all_diffs if d.spec_name == "价格"), None)
        assert price_diff is not None
        assert price_diff.diff_percent == 400  # (500-100)/100 * 100 = 400%
        assert price_diff.best_item == "装备A"  # 最便宜

    def test_numeric_diff_missing_unit(self):
        """缺失单位处理"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"自重": "100"}),  # 无单位
            self.MockItem("装备B", {"自重": "150g"}),  # 有单位
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        weight_diff = next((d for d in all_diffs if d.spec_name == "自重"), None)
        assert weight_diff is not None
        assert weight_diff.diff_type == "numeric"

    def test_ordinal_diff_same_values(self):
        """顺序型相同值"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"硬度": "M"}),
            self.MockItem("装备B", {"硬度": "M"}),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        power_diff = next((d for d in all_diffs if d.spec_name == "硬度"), None)
        # 相同硬度，差异程度应为 none
        assert power_diff is None or power_diff.diff_magnitude == "none"

    def test_ordinal_diff_invalid_value(self):
        """无效顺序值处理"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"硬度": "INVALID"}),  # 无效值
            self.MockItem("装备B", {"硬度": "M"}),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        power_diff = next((d for d in all_diffs if d.spec_name == "硬度"), None)
        # 无效值时应返回 "无法比较"
        if power_diff:
            assert power_diff.diff_magnitude == "none" or "无法比较" in power_diff.analysis

    def test_categorical_diff_same(self):
        """分类型相同值"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"颜色": "红色"}),
            self.MockItem("装备B", {"颜色": "红色"}),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        color_diff = next((d for d in all_diffs if d.spec_name == "颜色"), None)
        # 相同颜色，差异程度应为 none
        if color_diff:
            assert color_diff.diff_magnitude == "none"
            assert "相同" in color_diff.analysis

    def test_price_diff_one_missing(self):
        """部分价格缺失"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {}, None),  # 无价格
            self.MockItem("装备B", {}, 500),
        ]

        all_diffs, _ = analyzer.analyze_differences(items, "鱼竿")

        price_diff = next((d for d in all_diffs if d.spec_name == "价格"), None)
        # 只有一个价格，应返回 None
        assert price_diff is None

    def test_key_differences_sorting(self):
        """关键差异排序正确性"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {
                "自重": "100g",  # 100% 差异 - large
                "长度": "2.1m",  # 19% 差异 - medium
            }, 300),  # 233% 差异 - large
            self.MockItem("装备B", {
                "自重": "200g",
                "长度": "2.5m",
            }, 1000),
        ]

        all_diffs, key_diffs = analyzer.analyze_differences(items, "鱼竿")

        # 关键差异应该优先显示 large 级别的
        if key_diffs:
            first_diff = key_diffs[0]
            assert first_diff.diff_magnitude in ("large", "medium")

    def test_extract_number_various_formats(self):
        """各种格式数字提取"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        # 整数
        assert DiffAnalyzer._extract_number(100) == 100.0
        # 浮点数
        assert DiffAnalyzer._extract_number(2.5) == 2.5
        # 带单位字符串
        assert DiffAnalyzer._extract_number("100g") == 100.0
        assert DiffAnalyzer._extract_number("2.1m") == 2.1
        assert DiffAnalyzer._extract_number("5.5kg") == 5.5
        # 无数字字符串
        assert DiffAnalyzer._extract_number("无") is None
        # None
        assert DiffAnalyzer._extract_number(None) is None

    def test_three_item_comparison(self):
        """3个装备对比"""
        from packages.agents.fishing.tools.lure.diff_analyzer import DiffAnalyzer

        analyzer = DiffAnalyzer()

        items = [
            self.MockItem("装备A", {"自重": "100g"}, 300),
            self.MockItem("装备B", {"自重": "150g"}, 500),
            self.MockItem("装备C", {"自重": "200g"}, 800),
        ]

        all_diffs, key_diffs = analyzer.analyze_differences(items, "鱼竿")

        # 应正确识别最轻和最重
        weight_diff = next((d for d in all_diffs if d.spec_name == "自重"), None)
        assert weight_diff is not None
        assert weight_diff.best_item == "装备A"  # 最轻
        assert weight_diff.worst_item == "装备C"  # 最重

        # 价格差异
        price_diff = next((d for d in all_diffs if d.spec_name == "价格"), None)
        assert price_diff is not None
        assert price_diff.best_item == "装备A"  # 最便宜


# ========== SpecsExtractor 完整测试 ==========

class TestSpecsExtractorComplete:
    """SpecsExtractor 完整测试"""

    def test_get_specs_line(self):
        """鱼线规格提取"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        mock_db = MagicMock()
        mock_db.execute.return_value = [{
            'line_type': 'PE',
            'diameter': 0.165,
            'strength_lb': 20,
            'length_m': 150,
            'color': '荧光黄',
            'material': '高分子聚乙烯'
        }]

        extractor = SpecsExtractor(mock_db)
        specs = extractor.get_specs(1, "鱼线")

        assert specs["类型"] == "PE"
        assert specs["线径"] == "0.165mm"
        assert specs["强度"] == "20lb"
        assert specs["长度"] == "150m"
        assert specs["颜色"] == "荧光黄"
        assert specs["材质"] == "高分子聚乙烯"

    def test_get_specs_lure(self):
        """拟饵规格提取"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        mock_db = MagicMock()
        mock_db.execute.return_value = [{
            'lure_type': '硬饵',
            'lure_category': '米诺',
            'length': 70,
            'weight': 7.5,
            'diving_depth_min': 0.5,
            'diving_depth_max': 1.5,
            'color': '红头白身',
            'action_type': 'S形摆动'
        }]

        extractor = SpecsExtractor(mock_db)
        specs = extractor.get_specs(1, "拟饵")

        assert specs["类型"] == "硬饵"
        assert specs["分类"] == "米诺"
        assert specs["长度"] == "70mm"
        assert specs["重量"] == "7.5g"
        assert specs["潜深"] == "0.5-1.5m"
        assert specs["颜色"] == "红头白身"
        assert specs["泳姿"] == "S形摆动"

    def test_get_specs_unknown_category(self):
        """未知类别处理"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        mock_db = MagicMock()
        extractor = SpecsExtractor(mock_db)

        specs = extractor.get_specs(1, "未知类别")

        assert specs == {}
        # 不应调用数据库
        mock_db.execute.assert_not_called()

    def test_get_specs_no_data(self):
        """无数据返回空字典"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        mock_db = MagicMock()
        mock_db.execute.return_value = []  # 无数据

        extractor = SpecsExtractor(mock_db)
        specs = extractor.get_specs(1, "鱼竿")

        assert specs == {}

    def test_format_lure_range_partial(self):
        """部分饵重范围"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        # 只有 min
        result = SpecsExtractor._format_lure_range({'lure_weight_min': 5, 'lure_weight_max': None})
        assert result is None

        # 只有 max
        result = SpecsExtractor._format_lure_range({'lure_weight_min': None, 'lure_weight_max': 20})
        assert result is None

        # 都有
        result = SpecsExtractor._format_lure_range({'lure_weight_min': 5, 'lure_weight_max': 20})
        assert result == "5-20g"

    def test_format_depth_range_partial(self):
        """部分潜深范围"""
        from packages.agents.fishing.tools.lure.specs_extractor import SpecsExtractor

        # 只有 min
        result = SpecsExtractor._format_depth_range({'diving_depth_min': 0.5, 'diving_depth_max': None})
        assert result is None

        # 都有
        result = SpecsExtractor._format_depth_range({'diving_depth_min': 0.5, 'diving_depth_max': 1.5})
        assert result == "0.5-1.5m"


# ========== Formatters 完整测试 ==========

class TestFormattersComplete:
    """Formatters 完整测试"""

    def test_format_comparison_full(self):
        """完整对比报告格式化"""
        from packages.agents.fishing.tools.lure.formatters import format_comparison
        from packages.agents.fishing.tools.lure.comparator import ComparisonResult, ComparisonItem
        from packages.agents.fishing.tools.lure.diff_analyzer import SpecDifference

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=899,
                specs={"长度": "2.1m", "硬度": "ML", "调性": "F", "自重": "98g"},
                strengths=["价格最低", "最轻便"],
                weaknesses=[],
                overall_score=85.0
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="达亿瓦",
                price=1299,
                specs={"长度": "2.3m", "硬度": "M", "调性": "F", "自重": "110g"},
                strengths=["长度更长"],
                weaknesses=["价格最高"],
                overall_score=78.0
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
                analysis="价格差异44.5%"
            )
        ]

        result = ComparisonResult(
            items=items,
            category="鱼竿",
            compare_aspects=["价格", "长度", "硬度"],
            recommendations={"综合最优": "装备A", "预算有限": "装备A"},
            best_overall="装备A",
            summary="综合评分最高的是装备A（85.0分）",
            spec_differences=spec_differences,
            key_differences=spec_differences
        )

        output = format_comparison(result)

        # 验证各部分存在
        assert "# 装备对比报告" in output
        assert "快速结论" in output
        assert "关键差异" in output
        assert "综合评分" in output
        assert "详细参数对比" in output
        assert "优劣势分析" in output
        assert "选购建议" in output
        assert "装备A" in output
        assert "装备B" in output
        assert "85.0" in output

    def test_format_comparison_no_summary(self):
        """无总结时的格式化"""
        from packages.agents.fishing.tools.lure.formatters import format_comparison
        from packages.agents.fishing.tools.lure.comparator import ComparisonResult, ComparisonItem

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=899,
                specs={"长度": "2.1m"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="达亿瓦",
                price=1299,
                specs={"长度": "2.3m"}
            )
        ]

        result = ComparisonResult(
            items=items,
            category="鱼竿",
            compare_aspects=["价格", "长度"],
            recommendations={},
            summary=None,  # 无总结
            spec_differences=[]
        )

        output = format_comparison(result)

        # 应该仍然生成报告，只是没有快速结论部分
        assert "# 装备对比报告" in output
        assert "装备A" in output

    def test_format_comparison_no_differences(self):
        """无差异时的格式化"""
        from packages.agents.fishing.tools.lure.formatters import format_comparison
        from packages.agents.fishing.tools.lure.comparator import ComparisonResult, ComparisonItem

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=899,
                specs={"长度": "2.1m", "硬度": "M"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="禧玛诺",
                price=899,
                specs={"长度": "2.1m", "硬度": "M"}
            )
        ]

        result = ComparisonResult(
            items=items,
            category="鱼竿",
            compare_aspects=["价格", "长度", "硬度"],
            recommendations={},
            key_differences=[],  # 无差异
            spec_differences=[]
        )

        output = format_comparison(result)

        # 报告应该正常生成
        assert "# 装备对比报告" in output
        assert "详细参数对比" in output

    def test_format_recommendation(self):
        """推荐报告格式化"""
        from packages.agents.fishing.tools.lure.formatters import format_recommendation

        results = [
            {
                'name': '禧玛诺毒牙264ML',
                'price': 899,
                'brand': '禧玛诺',
                'score': 95,
                'specs': {'长度': '1.98m', '硬度': 'ML', '调性': 'F'},
                'reasons': ['品牌可靠', '适合新手'],
                'tips': '建议搭配2000型纺车轮'
            },
            {
                'name': '达亿瓦月下美人76ML',
                'price': 1299,
                'brand': '达亿瓦',
                'score': 90,
                'specs': {'长度': '2.29m', '硬度': 'ML', '调性': 'MF'},
                'reasons': ['手感细腻'],
                'tips': None
            }
        ]

        user_specs = {
            'equipment_type': '鱼竿',
            'budget': 1500,
            'user_level': '新手',
            'target_fish': '鲈鱼'
        }

        output = format_recommendation(results, user_specs)

        assert "# 路亚装备推荐报告" in output
        assert "需求分析" in output
        assert "鱼竿" in output
        assert "1500" in output
        assert "新手" in output
        assert "推荐产品" in output
        assert "禧玛诺毒牙264ML" in output
        assert "95%" in output  # 匹配度
        assert "推荐理由" in output
        assert "选购建议" in output

    def test_format_comparison_summary_table_same_specs(self):
        """全部相同规格"""
        from packages.agents.fishing.tools.lure.formatters import format_comparison_summary_table
        from packages.agents.fishing.tools.lure.comparator import ComparisonResult, ComparisonItem

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=899,
                specs={"长度": "2.1m", "硬度": "M"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="禧玛诺",
                price=899,
                specs={"长度": "2.1m", "硬度": "M"}
            )
        ]

        result = ComparisonResult(
            items=items,
            category="鱼竿",
            compare_aspects=["价格", "长度", "硬度"],
            recommendations={},
            spec_differences=[]
        )

        output = format_comparison_summary_table(result)

        assert "对比总结" in output
        assert "相同项" in output

    def test_format_comparison_summary_table_all_diff(self):
        """全部不同规格"""
        from packages.agents.fishing.tools.lure.formatters import format_comparison_summary_table
        from packages.agents.fishing.tools.lure.comparator import ComparisonResult, ComparisonItem
        from packages.agents.fishing.tools.lure.diff_analyzer import SpecDifference

        items = [
            ComparisonItem(
                equipment_id=1,
                name="装备A",
                category="鱼竿",
                brand="禧玛诺",
                price=500,
                specs={"长度": "2.1m", "硬度": "ML"}
            ),
            ComparisonItem(
                equipment_id=2,
                name="装备B",
                category="鱼竿",
                brand="达亿瓦",
                price=1000,
                specs={"长度": "2.4m", "硬度": "H"}
            )
        ]

        spec_differences = [
            SpecDifference(
                spec_name="价格",
                values={"装备A": "¥500", "装备B": "¥1000"},
                diff_type="numeric",
                diff_magnitude="large",
                diff_percent=100,
                best_item="装备A",
                worst_item="装备B",
                analysis="价格差异100%"
            ),
            SpecDifference(
                spec_name="硬度",
                values={"装备A": "ML", "装备B": "H"},
                diff_type="ordinal",
                diff_magnitude="large",
                diff_percent=33,
                best_item=None,
                worst_item=None,
                analysis="硬度跨越3个等级"
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
        assert "[显著]" in output or "显著" in output.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
