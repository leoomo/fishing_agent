"""
装备对比模块测试

测试EquipmentComparator类的核心功能:
- 装备查找
- 多维度对比
- 对比报告生成
"""

import pytest
import tempfile
from pathlib import Path

from ..database import LureDatabase
from ..comparator import EquipmentComparator, ComparisonResult


class TestEquipmentComparator:
    """装备对比测试"""

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
            (2, "达亿瓦", "日本", "高端")
        )

        # 插入装备
        db.execute_write(
            """INSERT INTO equipment
            (equipment_id, name, category, brand_id, price_min, price_max, user_level, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (1, "禧玛诺毒牙264ML", "鱼竿", 1, 800, 1000, "进阶", "经典泛用路亚竿")
        )
        db.execute_write(
            """INSERT INTO equipment
            (equipment_id, name, category, brand_id, price_min, price_max, user_level, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (2, "达亿瓦月下美人76ML", "鱼竿", 2, 900, 1100, "进阶", "轻量化设计路亚竿")
        )

        # 插入鱼竿规格
        db.execute_write(
            """INSERT INTO rod_specs
            (equipment_id, length, power, action, weight, sections)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (1, 2.64, "ML", "F", 120, 2)
        )
        db.execute_write(
            """INSERT INTO rod_specs
            (equipment_id, length, power, action, weight, sections)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (2, 2.28, "ML", "F", 95, 2)
        )

        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def comparator(self, db_with_equipment):
        """创建对比器实例"""
        from ..image_manager import ImageManager, LocalImageStorage
        storage = LocalImageStorage("/tmp/test_images")
        image_manager = ImageManager(db_with_equipment, storage)
        return EquipmentComparator(db_with_equipment, image_manager)

    def test_find_equipment_exact_match(self, comparator):
        """测试精确匹配装备名称"""
        equipment = comparator._find_equipment("禧玛诺毒牙264ML")
        assert equipment is not None
        assert equipment['name'] == "禧玛诺毒牙264ML"

    def test_find_equipment_fuzzy_match(self, comparator):
        """测试模糊匹配"""
        equipment = comparator._find_equipment("毒牙")
        assert equipment is not None
        assert "毒牙" in equipment['name']

    def test_find_equipment_not_found(self, comparator):
        """测试找不到装备"""
        equipment = comparator._find_equipment("不存在的装备")
        assert equipment is None

    def test_compare_two_rods(self, comparator):
        """测试对比两款鱼竿"""
        result = comparator.compare(
            equipment_names=["禧玛诺毒牙264ML", "达亿瓦月下美人76ML"]
        )

        assert isinstance(result, ComparisonResult)
        assert len(result.items) == 2
        assert result.category == "鱼竿"

    def test_compare_result_fields(self, comparator):
        """测试对比结果字段"""
        result = comparator.compare(
            equipment_names=["毒牙", "月下美人"]
        )

        # 检查对比项存在
        assert len(result.items) == 2

        # 检查第一项
        item1 = result.items[0]
        assert "name" in item1
        assert "brand" in item1
        assert "price" in item1

    def test_compare_with_aspects(self, comparator):
        """测试指定对比维度"""
        result = comparator.compare(
            equipment_names=["毒牙", "月下美人"],
            aspects=["价格", "性能"]
        )

        # 有指定维度的情况下仍应返回结果
        assert result is not None

    def test_compare_different_category_error(self, db_with_equipment, comparator):
        """测试不同类型装备对比"""
        # 先添加一个渔轮
        db_with_equipment.execute_write(
            """INSERT INTO equipment
            (equipment_id, name, category, brand_id, price_min)
            VALUES (?, ?, ?, ?, ?)""",
            (3, "禧玛诺红蝎2500", "渔轮", 1, 600)
        )

        with pytest.raises(ValueError, match="同类型"):
            comparator.compare(
                equipment_names=["毒牙", "红蝎2500"]
            )

    def test_compare_single_item_error(self, comparator):
        """测试单个装备报错"""
        with pytest.raises(ValueError, match="至少2个"):
            comparator.compare(equipment_names=["毒牙"])

    def test_compare_not_found_error(self, comparator):
        """测试装备不存在报错"""
        with pytest.raises(ValueError, match="未找到"):
            comparator.compare(
                equipment_names=["毒牙", "不存在的装备"]
            )


class TestComparisonDimensions:
    """对比维度测试"""

    @pytest.fixture
    def db_with_full_specs(self):
        """创建带完整规格的数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LureDatabase(db_path)

        # 品牌
        db.execute_write("INSERT INTO brands (id, name_cn, tier) VALUES (1, '品牌A', '高端')")
        db.execute_write("INSERT INTO brands (id, name_cn, tier) VALUES (2, '品牌B', '中端')")

        # 装备
        db.execute_write(
            """INSERT INTO equipment (equipment_id, name, category, brand_id, price_min, price_max, user_level)
            VALUES (1, '高端竿A', '鱼竿', 1, 1500, 2000, '高级')"""
        )
        db.execute_write(
            """INSERT INTO equipment (equipment_id, name, category, brand_id, price_min, price_max, user_level)
            VALUES (2, '中端竿B', '鱼竿', 2, 500, 700, '进阶')"""
        )

        # 规格
        db.execute_write(
            "INSERT INTO rod_specs (equipment_id, length, power, action, weight) VALUES (1, 2.7, 'MH', 'F', 130)"
        )
        db.execute_write(
            "INSERT INTO rod_specs (equipment_id, length, power, action, weight) VALUES (2, 2.1, 'ML', 'MF', 140)"
        )

        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def comparator(self, db_with_full_specs):
        from ..image_manager import ImageManager, LocalImageStorage
        storage = LocalImageStorage("/tmp/test_images")
        image_manager = ImageManager(db_with_full_specs, storage)
        return EquipmentComparator(db_with_full_specs, image_manager)

    def test_price_comparison(self, comparator):
        """测试价格对比"""
        result = comparator.compare(
            equipment_names=["高端竿A", "中端竿B"],
            aspects=["价格"]
        )

        item1 = result.items[0]
        item2 = result.items[1]

        # 高端竿价格更高
        assert item1['price']['min'] > item2['price']['min']

    def test_specs_comparison(self, comparator):
        """测试规格对比"""
        result = comparator.compare(
            equipment_names=["高端竿A", "中端竿B"],
            aspects=["性能"]
        )

        item1 = result.items[0]
        item2 = result.items[1]

        # 验证规格存在
        assert 'specs' in item1 or 'length' in item1.get('specs', {})

    def test_comparison_summary(self, comparator):
        """测试对比摘要"""
        result = comparator.compare(
            equipment_names=["高端竿A", "中端竿B"]
        )

        # 应该有对比摘要
        assert result.summary is not None or result.differences is not None


class TestComparisonResult:
    """对比结果数据类测试"""

    def test_comparison_result_creation(self):
        """测试创建对比结果"""
        result = ComparisonResult(
            category="鱼竿",
            items=[
                {"name": "竿A", "price": {"min": 500}},
                {"name": "竿B", "price": {"min": 600}}
            ],
            differences={"price": "竿B贵100元"},
            summary="两款竿各有特点",
            recommendation="预算有限选竿A"
        )

        assert result.category == "鱼竿"
        assert len(result.items) == 2
        assert result.summary == "两款竿各有特点"

    def test_comparison_result_to_dict(self):
        """测试结果转字典"""
        result = ComparisonResult(
            category="渔轮",
            items=[{"name": "轮A"}, {"name": "轮B"}],
            differences={},
            summary="对比摘要"
        )

        # 验证可序列化
        from dataclasses import asdict
        d = asdict(result)
        assert d['category'] == "渔轮"
        assert len(d['items']) == 2
