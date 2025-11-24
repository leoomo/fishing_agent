"""
数据库模块测试

测试LureDatabase类的核心功能:
- 表结构初始化
- CRUD操作
- 事务管理
- 线程安全
"""

import pytest
import tempfile
import threading
from pathlib import Path

from ..database import LureDatabase, get_db, reset_db


class TestLureDatabase:
    """数据库基础功能测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LureDatabase(db_path)
        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    def test_init_tables(self, temp_db):
        """测试表结构初始化"""
        # 检查核心表是否存在
        tables = temp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [t['name'] for t in tables]

        expected_tables = [
            'brands', 'equipment', 'rod_specs', 'reel_specs',
            'line_specs', 'lure_specs', 'product_images',
            'fish_species', 'fish_knowledge', 'rig_types', 'rig_specs',
            'lure_types', 'rod_lure_fitness', 'fish_season_activity', 'rig_components'
        ]

        for table in expected_tables:
            assert table in table_names, f"表 {table} 不存在"

    def test_execute_read(self, temp_db):
        """测试只读查询"""
        # 插入测试数据
        temp_db.execute_write(
            "INSERT INTO brands (name_cn, country, tier) VALUES (?, ?, ?)",
            ("测试品牌", "中国", "入门")
        )

        # 查询
        result = temp_db.execute("SELECT * FROM brands WHERE name_cn = ?", ("测试品牌",))

        assert len(result) == 1
        assert result[0]['name_cn'] == "测试品牌"
        assert result[0]['tier'] == "入门"

    def test_execute_write(self, temp_db):
        """测试写入操作"""
        # INSERT
        brand_id = temp_db.execute_write(
            "INSERT INTO brands (name_cn, tier) VALUES (?, ?)",
            ("禧玛诺", "高端")
        )
        assert brand_id > 0

        # UPDATE
        affected = temp_db.execute_write(
            "UPDATE brands SET tier = ? WHERE id = ?",
            ("中高端", brand_id)
        )
        assert affected == 1

        # 验证更新
        result = temp_db.execute("SELECT tier FROM brands WHERE id = ?", (brand_id,))
        assert result[0]['tier'] == "中高端"

    def test_execute_many(self, temp_db):
        """测试批量写入"""
        brands = [
            ("品牌A", "中国", "入门"),
            ("品牌B", "日本", "高端"),
            ("品牌C", "美国", "中端"),
        ]

        affected = temp_db.execute_many(
            "INSERT INTO brands (name_cn, country, tier) VALUES (?, ?, ?)",
            brands
        )

        assert affected == 3

        result = temp_db.execute("SELECT COUNT(*) as cnt FROM brands")
        assert result[0]['cnt'] == 3

    def test_transaction_commit(self, temp_db):
        """测试事务提交"""
        with temp_db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO brands (name_cn, tier) VALUES (?, ?)",
                ("事务测试", "入门")
            )

        result = temp_db.execute("SELECT * FROM brands WHERE name_cn = ?", ("事务测试",))
        assert len(result) == 1

    def test_transaction_rollback(self, temp_db):
        """测试事务回滚"""
        try:
            with temp_db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO brands (name_cn, tier) VALUES (?, ?)",
                    ("回滚测试", "入门")
                )
                raise ValueError("模拟错误")
        except ValueError:
            pass

        result = temp_db.execute("SELECT * FROM brands WHERE name_cn = ?", ("回滚测试",))
        assert len(result) == 0

    def test_thread_safety(self, temp_db):
        """测试线程安全"""
        results = []
        errors = []

        def insert_brand(name):
            try:
                temp_db.execute_write(
                    "INSERT INTO brands (name_cn, tier) VALUES (?, ?)",
                    (name, "入门")
                )
                results.append(name)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=insert_brand, args=(f"线程品牌{i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5


class TestEquipmentCRUD:
    """装备数据CRUD测试"""

    @pytest.fixture
    def db_with_brand(self):
        """创建带品牌数据的临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LureDatabase(db_path)

        # 插入品牌
        db.execute_write(
            "INSERT INTO brands (name_cn, country, tier) VALUES (?, ?, ?)",
            ("禧玛诺", "日本", "高端")
        )

        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    def test_insert_equipment(self, db_with_brand):
        """测试插入装备"""
        eq_id = db_with_brand.execute_write(
            """INSERT INTO equipment
            (name, category, brand_id, price_min, price_max, user_level)
            VALUES (?, ?, ?, ?, ?, ?)""",
            ("禧玛诺毒牙264ML", "鱼竿", 1, 800, 1000, "进阶")
        )

        assert eq_id > 0

        # 验证
        result = db_with_brand.execute(
            "SELECT * FROM equipment WHERE equipment_id = ?", (eq_id,)
        )
        assert result[0]['name'] == "禧玛诺毒牙264ML"
        assert result[0]['category'] == "鱼竿"

    def test_insert_rod_specs(self, db_with_brand):
        """测试插入鱼竿规格"""
        # 先插入装备
        eq_id = db_with_brand.execute_write(
            "INSERT INTO equipment (name, category) VALUES (?, ?)",
            ("测试竿", "鱼竿")
        )

        # 插入规格
        spec_id = db_with_brand.execute_write(
            """INSERT INTO rod_specs
            (equipment_id, length, power, action, weight)
            VALUES (?, ?, ?, ?, ?)""",
            (eq_id, 2.1, "ML", "F", 120)
        )

        assert spec_id > 0

        # 联合查询
        result = db_with_brand.execute(
            """SELECT e.name, r.length, r.power
            FROM equipment e
            JOIN rod_specs r ON e.equipment_id = r.equipment_id
            WHERE e.equipment_id = ?""",
            (eq_id,)
        )

        assert result[0]['length'] == 2.1
        assert result[0]['power'] == "ML"

    def test_cascade_delete(self, db_with_brand):
        """测试级联删除"""
        # 插入装备和规格
        eq_id = db_with_brand.execute_write(
            "INSERT INTO equipment (name, category) VALUES (?, ?)",
            ("级联测试竿", "鱼竿")
        )
        db_with_brand.execute_write(
            "INSERT INTO rod_specs (equipment_id, length, power) VALUES (?, ?, ?)",
            (eq_id, 2.1, "ML")
        )

        # 删除装备
        db_with_brand.execute_write(
            "DELETE FROM equipment WHERE equipment_id = ?", (eq_id,)
        )

        # 验证规格也被删除
        result = db_with_brand.execute(
            "SELECT * FROM rod_specs WHERE equipment_id = ?", (eq_id,)
        )
        assert len(result) == 0


class TestExtendedTables:
    """扩展表测试"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        db = LureDatabase(db_path)
        yield db

        db.close()
        Path(db_path).unlink(missing_ok=True)

    def test_lure_types_table(self, temp_db):
        """测试拟饵类型表"""
        lure_id = temp_db.execute_write(
            """INSERT INTO lure_types
            (name_cn, name_en, category, description, typical_action, target_fish)
            VALUES (?, ?, ?, ?, ?, ?)""",
            ("米诺", "Minnow", "硬饵", "模拟小鱼的硬饵", "摇摆", "鲈鱼,翘嘴")
        )

        assert lure_id > 0

        result = temp_db.execute("SELECT * FROM lure_types WHERE id = ?", (lure_id,))
        assert result[0]['name_cn'] == "米诺"
        assert result[0]['typical_action'] == "摇摆"

    def test_rod_lure_fitness_table(self, temp_db):
        """测试鱼竿-拟饵兼容性表"""
        # 先插入拟饵类型
        lure_id = temp_db.execute_write(
            "INSERT INTO lure_types (name_cn, category) VALUES (?, ?)",
            ("德州软饵", "软饵")
        )

        # 插入兼容性数据
        fitness_id = temp_db.execute_write(
            """INSERT INTO rod_lure_fitness
            (rod_power, lure_type_id, fitness_level, lure_weight_min, lure_weight_max, notes)
            VALUES (?, ?, ?, ?, ?, ?)""",
            ("MH", lure_id, "最佳", 7, 21, "MH竿适合7-21g软饵作钓")
        )

        assert fitness_id > 0

        result = temp_db.execute(
            "SELECT * FROM rod_lure_fitness WHERE rod_power = ?", ("MH",)
        )
        assert result[0]['fitness_level'] == "最佳"

    def test_fish_season_activity_table(self, temp_db):
        """测试鱼类季节活动表"""
        # 先插入鱼种
        fish_id = temp_db.execute_write(
            "INSERT INTO fish_species (name_cn, category) VALUES (?, ?)",
            ("大口黑鲈", "鲈形目")
        )

        # 插入季节活动
        activity_id = temp_db.execute_write(
            """INSERT INTO fish_season_activity
            (fish_species_id, season, activity_level, best_time_of_day,
             preferred_depth, feeding_intensity, recommended_lure_types)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (fish_id, "春季", 8, "清晨,傍晚", "浅水区", "高", "软饵,米诺")
        )

        assert activity_id > 0

        result = temp_db.execute(
            "SELECT * FROM fish_season_activity WHERE fish_species_id = ? AND season = ?",
            (fish_id, "春季")
        )
        assert result[0]['activity_level'] == 8
        assert result[0]['feeding_intensity'] == "高"

    def test_rig_components_table(self, temp_db):
        """测试钓组配件表"""
        # 先插入钓组类型
        rig_id = temp_db.execute_write(
            "INSERT INTO rig_types (name_cn, category) VALUES (?, ?)",
            ("德州钓组", "软饵钓组")
        )

        # 插入配件
        components = [
            (rig_id, "子弹铅", "铅坠", 1, "7-14g", 1, 1, "重量根据水深调整"),
            (rig_id, "曲柄钩", "鱼钩", 1, "2/0-4/0", 1, 2, "钩型选择影响刺鱼效果"),
            (rig_id, "软饵", "拟饵", 1, "3-4寸", 1, 3, "颜色根据水色选择"),
        ]

        affected = temp_db.execute_many(
            """INSERT INTO rig_components
            (rig_type_id, component_name, component_type, quantity,
             spec_requirement, is_required, display_order, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            components
        )

        assert affected == 3

        result = temp_db.execute(
            "SELECT * FROM rig_components WHERE rig_type_id = ? ORDER BY display_order",
            (rig_id,)
        )
        assert len(result) == 3
        assert result[0]['component_name'] == "子弹铅"


class TestSingleton:
    """单例模式测试"""

    def test_get_db_singleton(self):
        """测试数据库单例"""
        reset_db()

        db1 = get_db()
        db2 = get_db()

        assert db1 is db2

        reset_db()

    def test_reset_db(self):
        """测试重置单例"""
        db1 = get_db()
        reset_db()
        db2 = get_db()

        # 重置后应该是新实例
        assert db1 is not db2

        reset_db()
