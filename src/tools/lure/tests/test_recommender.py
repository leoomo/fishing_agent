"""
推荐算法测试

测试LureRecommender类的核心功能:
- 四因子评分算法
- 价格匹配评分
- 规格匹配评分
- 品牌声誉评分
- 用户水平匹配
- 套装推荐
"""

import pytest
import tempfile
from pathlib import Path

from ..database import LureDatabase
from ..recommender import (
    LureRecommender,
    RecommendationResult,
    RECOMMENDATION_CONFIG,
    POWER_ORDER,
    USER_LEVEL_MAP
)


class TestRecommenderScoring:
    """评分算法测试"""

    @pytest.fixture
    def db_with_equipment(self):
        """创建带装备数据的临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LureDatabase(db_path)

        # 插入品牌
        db.execute_write(
            "INSERT INTO brands (id, name_cn, country, tier) VALUES (?, ?, ?, ?)",
            (1, "禧玛诺", "日本", "高端")
        )
        db.execute_write(
            "INSERT INTO brands (id, name_cn, country, tier) VALUES (?, ?, ?, ?)",
            (2, "狼王", "中国", "入门")
        )

        # 插入装备
        db.execute_write(
            """INSERT INTO equipment
            (equipment_id, name, category, brand_id, price_min, price_max, user_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (1, "禧玛诺毒牙264ML", "鱼竿", 1, 800, 1000, "进阶")
        )
        db.execute_write(
            """INSERT INTO equipment
            (equipment_id, name, category, brand_id, price_min, price_max, user_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (2, "狼王入门竿", "鱼竿", 2, 150, 200, "入门")
        )
        db.execute_write(
            """INSERT INTO equipment
            (equipment_id, name, category, brand_id, price_min, price_max, user_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (3, "禧玛诺红蝎2500", "渔轮", 1, 600, 700, "进阶")
        )

        # 插入鱼竿规格
        db.execute_write(
            """INSERT INTO rod_specs
            (equipment_id, length, power, action, weight)
            VALUES (?, ?, ?, ?, ?)""",
            (1, 2.64, "ML", "F", 120)
        )
        db.execute_write(
            """INSERT INTO rod_specs
            (equipment_id, length, power, action, weight)
            VALUES (?, ?, ?, ?, ?)""",
            (2, 2.1, "M", "MF", 150)
        )

        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def recommender(self, db_with_equipment):
        """创建推荐器实例"""
        return LureRecommender(db_with_equipment)

    # ========== 价格评分测试 ==========

    def test_price_score_within_budget(self, recommender):
        """测试预算内价格评分"""
        equipment = {"price_min": 800}
        score = recommender._calculate_price_score(equipment, budget=1000)
        assert score >= 80, "预算内应得高分"

    def test_price_score_exact_budget(self, recommender):
        """测试价格等于预算"""
        equipment = {"price_min": 500}
        score = recommender._calculate_price_score(equipment, budget=500)
        assert score == 100, "价格等于预算应得满分"

    def test_price_score_over_budget(self, recommender):
        """测试价格略超预算"""
        equipment = {"price_min": 1100}
        score = recommender._calculate_price_score(equipment, budget=1000)
        # 超10%，应在60-100之间
        assert 60 <= score <= 100, f"略超预算分数异常: {score}"

    def test_price_score_far_over_budget(self, recommender):
        """测试价格严重超预算"""
        equipment = {"price_min": 1500}
        score = recommender._calculate_price_score(equipment, budget=1000)
        assert score == 0, "严重超预算应为0分"

    def test_price_score_no_budget(self, recommender):
        """测试无预算限制"""
        equipment = {"price_min": 500}
        score = recommender._calculate_price_score(equipment, budget=None)
        assert score == 80, "无预算应给默认分80"

    def test_price_score_no_price(self, recommender):
        """测试装备无价格信息"""
        equipment = {}
        score = recommender._calculate_price_score(equipment, budget=1000)
        assert score == 70, "无价格信息应给70分"

    # ========== 规格评分测试 ==========

    def test_spec_score_exact_match(self, recommender):
        """测试规格完全匹配"""
        equipment = {"category": "鱼竿", "equipment_id": 1}
        specifications = {"硬度": "ML"}
        score = recommender._calculate_spec_score(equipment, specifications)
        assert score == 100, "硬度完全匹配应得满分"

    def test_spec_score_adjacent_power(self, recommender):
        """测试相邻硬度"""
        equipment = {"category": "鱼竿", "equipment_id": 1}
        specifications = {"硬度": "L"}  # ML的相邻硬度
        score = recommender._calculate_spec_score(equipment, specifications)
        assert score == 80, "相邻硬度应得80分"

    def test_spec_score_no_specs(self, recommender):
        """测试无规格要求"""
        equipment = {"category": "鱼竿", "equipment_id": 1}
        score = recommender._calculate_spec_score(equipment, {})
        assert score == 80, "无规格要求应给默认分80"

    # ========== 品牌评分测试 ==========

    def test_brand_score_high_tier(self, recommender):
        """测试高端品牌"""
        equipment = {"brand_id": 1}  # 禧玛诺
        score = recommender._calculate_brand_score(equipment)
        assert score >= 90, f"高端品牌应得高分，实际: {score}"

    def test_brand_score_entry_tier(self, recommender):
        """测试入门品牌"""
        equipment = {"brand_id": 2}  # 狼王
        score = recommender._calculate_brand_score(equipment)
        assert 60 <= score <= 70, f"入门品牌应得中低分，实际: {score}"

    def test_brand_score_unknown(self, recommender):
        """测试未知品牌"""
        equipment = {"brand_id": None}
        score = recommender._calculate_brand_score(equipment)
        assert score == 50, "未知品牌应得50分"

    # ========== 用户水平评分测试 ==========

    def test_user_level_exact_match(self, recommender):
        """测试水平完全匹配"""
        equipment = {"user_level": "入门"}
        score = recommender._calculate_user_level_score(equipment, "新手")
        assert score == 100, "水平匹配应得满分"

    def test_user_level_one_above(self, recommender):
        """测试装备水平高一级"""
        equipment = {"user_level": "进阶"}
        score = recommender._calculate_user_level_score(equipment, "新手")
        assert score == 70, "高一级应得70分"

    def test_user_level_one_below(self, recommender):
        """测试装备水平低一级"""
        equipment = {"user_level": "入门"}
        score = recommender._calculate_user_level_score(equipment, "进阶")
        assert score == 50, "低一级应得50分"

    # ========== 加权总分测试 ==========

    def test_weighted_sum(self, recommender):
        """测试加权求和"""
        scores = {
            "price_match": 100,
            "spec_match": 100,
            "brand_reputation": 100,
            "user_level": 100
        }
        total = recommender._weighted_sum(scores)
        assert total == 100, "全满分应为100"

    def test_weighted_sum_mixed(self, recommender):
        """测试混合分数加权"""
        scores = {
            "price_match": 80,  # 35%
            "spec_match": 70,   # 35%
            "brand_reputation": 90,  # 15%
            "user_level": 100   # 15%
        }
        # 80*0.35 + 70*0.35 + 90*0.15 + 100*0.15 = 28 + 24.5 + 13.5 + 15 = 81
        total = recommender._weighted_sum(scores)
        assert total == 81.0, f"加权总分应为81，实际: {total}"


class TestRecommend:
    """推荐功能测试"""

    @pytest.fixture
    def db_with_equipment(self):
        """创建带装备数据的临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LureDatabase(db_path)

        # 插入品牌
        db.execute_write(
            "INSERT INTO brands (id, name_cn, tier) VALUES (?, ?, ?)",
            (1, "禧玛诺", "高端")
        )
        db.execute_write(
            "INSERT INTO brands (id, name_cn, tier) VALUES (?, ?, ?)",
            (2, "狼王", "入门")
        )

        # 插入多款鱼竿
        rods = [
            (1, "禧玛诺毒牙264ML", "鱼竿", 1, 800, "进阶"),
            (2, "狼王入门竿210M", "鱼竿", 2, 150, "入门"),
            (3, "禧玛诺超越300MH", "鱼竿", 1, 1200, "高级"),
        ]
        for rod in rods:
            db.execute_write(
                """INSERT INTO equipment
                (equipment_id, name, category, brand_id, price_min, user_level)
                VALUES (?, ?, ?, ?, ?, ?)""",
                rod
            )

        # 鱼竿规格
        specs = [
            (1, 2.64, "ML", "F"),
            (2, 2.1, "M", "MF"),
            (3, 3.0, "MH", "F"),
        ]
        for spec in specs:
            db.execute_write(
                "INSERT INTO rod_specs (equipment_id, length, power, action) VALUES (?, ?, ?, ?)",
                spec
            )

        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def recommender(self, db_with_equipment):
        return LureRecommender(db_with_equipment)

    def test_recommend_basic(self, recommender):
        """测试基础推荐"""
        results = recommender.recommend(
            "鱼竿",
            {"budget": 1000, "user_level": "新手"},
            top_k=3
        )

        assert len(results) > 0
        assert all(isinstance(r, RecommendationResult) for r in results)

    def test_recommend_sorted_by_score(self, recommender):
        """测试结果按分数排序"""
        results = recommender.recommend(
            "鱼竿",
            {"budget": 1000, "user_level": "进阶"},
            top_k=3
        )

        scores = [r.total_score for r in results]
        assert scores == sorted(scores, reverse=True), "结果应按分数降序排列"

    def test_recommend_with_specs(self, recommender):
        """测试带规格要求的推荐"""
        results = recommender.recommend(
            "鱼竿",
            {
                "budget": 1000,
                "specifications": {"硬度": "ML"},
                "user_level": "进阶"
            },
            top_k=1
        )

        assert len(results) >= 1
        # ML竿应该排在前面
        if results:
            assert "毒牙" in results[0].name or results[0].specs.get("硬度") == "ML"

    def test_recommend_empty_result(self, recommender):
        """测试无匹配结果"""
        results = recommender.recommend(
            "鱼竿",
            {"budget": 50, "user_level": "新手"},  # 预算太低
            top_k=3
        )

        # 可能返回空或低分结果
        assert isinstance(results, list)

    def test_recommendation_result_fields(self, recommender):
        """测试推荐结果字段完整性"""
        results = recommender.recommend(
            "鱼竿",
            {"budget": 1000},
            top_k=1
        )

        if results:
            r = results[0]
            assert r.equipment_id > 0
            assert r.name
            assert r.category == "鱼竿"
            assert 0 <= r.total_score <= 100
            assert "price_match" in r.score_breakdown
            assert isinstance(r.match_reasons, list)


class TestPackageRecommend:
    """套装推荐测试"""

    @pytest.fixture
    def db_with_full_equipment(self):
        """创建包含各类装备的数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LureDatabase(db_path)

        # 品牌
        db.execute_write("INSERT INTO brands (id, name_cn, tier) VALUES (1, '禧玛诺', '高端')")
        db.execute_write("INSERT INTO brands (id, name_cn, tier) VALUES (2, '狼王', '入门')")

        # 鱼竿
        db.execute_write(
            """INSERT INTO equipment (equipment_id, name, category, brand_id, price_min, user_level)
            VALUES (1, '狼王入门竿', '鱼竿', 2, 150, '入门')"""
        )
        db.execute_write("INSERT INTO rod_specs (equipment_id, length, power) VALUES (1, 2.1, 'M')")

        # 渔轮
        db.execute_write(
            """INSERT INTO equipment (equipment_id, name, category, brand_id, price_min, user_level)
            VALUES (2, '狼王入门轮', '渔轮', 2, 100, '入门')"""
        )
        db.execute_write("INSERT INTO reel_specs (equipment_id, reel_type, gear_ratio) VALUES (2, '纺车轮', '5.2:1')")

        # 鱼线
        db.execute_write(
            """INSERT INTO equipment (equipment_id, name, category, brand_id, price_min, user_level)
            VALUES (3, '入门PE线', '鱼线', 2, 50, '入门')"""
        )
        db.execute_write("INSERT INTO line_specs (equipment_id, line_type, strength_lb) VALUES (3, 'PE线', 15)")

        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def recommender(self, db_with_full_equipment):
        return LureRecommender(db_with_full_equipment)

    def test_package_recommend(self, recommender):
        """测试套装推荐"""
        result = recommender.recommend_package(
            budget=500,
            user_level="新手",
            target_fish="鲈鱼"
        )

        assert "budget" in result
        assert "total_price" in result
        assert "items" in result
        assert "compatibility" in result

    def test_package_budget_allocation(self, recommender):
        """测试预算分配"""
        budget = 1000
        result = recommender.recommend_package(budget=budget, user_level="新手")

        # 验证总价不超过预算太多
        if result['total_price'] > 0:
            assert result['total_price'] <= budget * 1.2, "总价不应严重超预算"

    def test_package_compatibility_check(self, recommender):
        """测试兼容性检查"""
        result = recommender.recommend_package(budget=500, user_level="新手")

        compatibility = result.get('compatibility', {})
        assert 'is_compatible' in compatibility
        assert 'notes' in compatibility


class TestHelperMethods:
    """辅助方法测试"""

    @pytest.fixture
    def recommender(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = LureDatabase(db_path)
        recommender = LureRecommender(db)
        yield recommender
        db.close()
        Path(db_path).unlink(missing_ok=True)

    def test_match_power_exact(self, recommender):
        """测试硬度精确匹配"""
        score = recommender._match_power("ML", "ML")
        assert score == 100

    def test_match_power_adjacent(self, recommender):
        """测试硬度相邻匹配"""
        score = recommender._match_power("ML", "M")
        assert score == 80

    def test_match_power_two_levels(self, recommender):
        """测试硬度差两级"""
        score = recommender._match_power("ML", "MH")
        assert score == 50

    def test_match_length_exact(self, recommender):
        """测试长度精确匹配"""
        score = recommender._match_length(2.1, 2.1)
        assert score == 100

    def test_match_length_within_tolerance(self, recommender):
        """测试长度在容差内"""
        score = recommender._match_length(2.1, 2.3)  # 差0.2，在0.3容差内
        assert score == 100

    def test_parse_length_float(self, recommender):
        """测试解析数字长度"""
        assert recommender._parse_length(2.1) == 2.1

    def test_parse_length_string(self, recommender):
        """测试解析字符串长度"""
        assert recommender._parse_length("2.1m") == 2.1
        assert recommender._parse_length("2.1") == 2.1

    def test_generate_match_reasons(self, recommender):
        """测试生成匹配理由"""
        equipment = {"name": "测试竿"}
        scores = {
            "price_match": 95,
            "brand_reputation": 92,
            "user_level": 100,
            "spec_match": 80
        }
        user_specs = {"budget": 500}

        reasons = recommender._generate_match_reasons(equipment, scores, user_specs)

        assert isinstance(reasons, list)
        assert any("价格" in r for r in reasons)
        assert any("品牌" in r for r in reasons)
