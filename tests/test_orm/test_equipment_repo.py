"""
Tests for EquipmentRepository
"""

import pytest
from sqlalchemy.orm import Session

from apps.api.orm.repositories import EquipmentRepository
from apps.api.models import Equipment, Brand, RodSpec, ReelSpec, LineSpec, LureSpec


class TestEquipmentRepository:
    """Test cases for EquipmentRepository"""

    def test_get_equipment(self, db_session: Session, sample_equipment: Equipment):
        """Test getting equipment by ID"""
        repo = EquipmentRepository(db_session)
        equipment = repo.get(sample_equipment.equipment_id)

        assert equipment is not None
        assert equipment.equipment_id == sample_equipment.equipment_id
        assert equipment.name == "光威赤刃"

    def test_get_with_details(self, db_session: Session, sample_equipment: Equipment, sample_rod_spec: RodSpec):
        """Test getting equipment with all details preloaded"""
        repo = EquipmentRepository(db_session)
        equipment = repo.get_with_details(sample_equipment.equipment_id)

        assert equipment is not None
        assert equipment.brand is not None
        assert equipment.brand.name_cn == "光威"
        assert equipment.rod_spec is not None
        assert equipment.rod_spec.power == "M"

    def test_search_by_category(self, db_session: Session, sample_equipment: Equipment):
        """Test searching equipment by category"""
        repo = EquipmentRepository(db_session)
        results = repo.search(category="鱼竿")

        assert len(results) == 1
        assert results[0].category == "鱼竿"

    def test_search_by_price_range(self, db_session: Session, sample_equipment: Equipment):
        """Test searching equipment by price range"""
        repo = EquipmentRepository(db_session)

        # Should find equipment in range
        results = repo.search(price_min=100.0, price_max=400.0)
        assert len(results) == 1

        # Should not find equipment out of range
        results = repo.search(price_min=500.0, price_max=1000.0)
        assert len(results) == 0

    def test_search_by_keyword(self, db_session: Session, sample_equipment: Equipment):
        """Test searching equipment by keyword"""
        repo = EquipmentRepository(db_session)

        # Search in name
        results = repo.search(keyword="赤刃")
        assert len(results) == 1

        # Search with no match
        results = repo.search(keyword="不存在的关键词")
        assert len(results) == 0

    def test_search_rods(self, db_session: Session, sample_equipment: Equipment, sample_rod_spec: RodSpec):
        """Test searching rods with rod-specific filters"""
        repo = EquipmentRepository(db_session)

        # Search by power
        results = repo.search_rods(power="M")
        assert len(results) == 1
        assert results[0].rod_spec.power == "M"

        # Search by lure weight range
        results = repo.search_rods(lure_weight_min=5.0, lure_weight_max=15.0)
        assert len(results) == 1

        # Search with no match
        results = repo.search_rods(power="XH")
        assert len(results) == 0

    def test_create_with_specs(self, db_session: Session, sample_brand: Brand):
        """Test creating equipment with specifications"""
        repo = EquipmentRepository(db_session)

        equipment_data = {
            'name': '测试鱼竿',
            'category': '鱼竿',
            'brand_id': sample_brand.brand_id,
            'price_min': 300.0,
            'price_max': 400.0,
            'user_level': '进阶',
            'is_active': True
        }

        spec_data = {
            'length': 2.4,
            'power': 'MH',
            'action': 'Fast',
            'lure_weight_min': 7.0,
            'lure_weight_max': 28.0
        }

        equipment = repo.create_with_specs(equipment_data, spec_data)
        db_session.commit()

        assert equipment.equipment_id is not None
        assert equipment.name == '测试鱼竿'

        # Verify spec was created
        db_session.refresh(equipment)
        assert equipment.rod_spec is not None
        assert equipment.rod_spec.power == 'MH'

    def test_get_by_category(self, db_session: Session, sample_equipment: Equipment):
        """Test getting equipment by category"""
        repo = EquipmentRepository(db_session)
        results = repo.get_by_category("鱼竿")

        assert len(results) == 1
        assert results[0].category == "鱼竿"

    def test_get_by_brand(self, db_session: Session, sample_equipment: Equipment, sample_brand: Brand):
        """Test getting equipment by brand"""
        repo = EquipmentRepository(db_session)
        results = repo.get_by_brand(sample_brand.brand_id)

        assert len(results) == 1
        assert results[0].brand_id == sample_brand.brand_id

    def test_update_equipment(self, db_session: Session, sample_equipment: Equipment):
        """Test updating equipment"""
        repo = EquipmentRepository(db_session)

        updated = repo.update(
            sample_equipment.equipment_id,
            {'price_min': 250.0, 'price_max': 350.0}
        )
        db_session.commit()

        assert updated is not None
        assert updated.price_min == 250.0
        assert updated.price_max == 350.0

    def test_delete_equipment(self, db_session: Session, sample_equipment: Equipment):
        """Test deleting equipment"""
        repo = EquipmentRepository(db_session)
        equipment_id = sample_equipment.equipment_id

        result = repo.delete(equipment_id)
        db_session.commit()

        assert result is True

        # Verify deletion
        equipment = repo.get(equipment_id)
        assert equipment is None

    def test_count_equipment(self, db_session: Session, sample_equipment: Equipment):
        """Test counting equipment"""
        repo = EquipmentRepository(db_session)

        # Count all
        count = repo.count()
        assert count == 1

        # Count with filter
        count = repo.count({'category': '鱼竿'})
        assert count == 1

        count = repo.count({'category': '渔轮'})
        assert count == 0


class TestEquipmentRepositoryAgentMethods:
    """测试 Agent Tools 专用方法 (search_by_name_exact, search_by_name_fuzzy, get_by_ids, to_dict)"""

    # === search_by_name_exact 测试 ===

    def test_search_by_name_exact_match_name(self, db_session: Session, sample_equipment: Equipment):
        """精确匹配名称"""
        repo = EquipmentRepository(db_session)
        result = repo.search_by_name_exact("光威赤刃")

        assert result is not None
        assert result.name == "光威赤刃"
        assert result.equipment_id == sample_equipment.equipment_id

    def test_search_by_name_exact_match_model(self, db_session: Session, sample_equipment: Equipment):
        """精确匹配型号"""
        repo = EquipmentRepository(db_session)
        result = repo.search_by_name_exact("CRE001")

        assert result is not None
        assert result.model == "CRE001"
        assert result.equipment_id == sample_equipment.equipment_id

    def test_search_by_name_exact_with_category(self, db_session: Session, sample_equipment: Equipment):
        """带类别过滤的精确搜索"""
        repo = EquipmentRepository(db_session)

        # 正确类别应找到
        result = repo.search_by_name_exact("光威赤刃", category="鱼竿")
        assert result is not None

        # 错误类别不应找到
        result = repo.search_by_name_exact("光威赤刃", category="渔轮")
        assert result is None

    def test_search_by_name_exact_no_match(self, db_session: Session, sample_equipment: Equipment):
        """无匹配返回 None"""
        repo = EquipmentRepository(db_session)
        result = repo.search_by_name_exact("不存在的装备")

        assert result is None

    def test_search_by_name_exact_preloads_relations(
        self, db_session: Session, sample_equipment: Equipment, sample_rod_spec: RodSpec
    ):
        """验证预加载关联对象"""
        repo = EquipmentRepository(db_session)
        result = repo.search_by_name_exact("光威赤刃")

        assert result is not None
        assert result.brand is not None
        assert result.brand.name_cn == "光威"
        assert result.rod_spec is not None
        assert result.rod_spec.power == "M"

    # === search_by_name_fuzzy 测试 ===

    def test_search_by_name_fuzzy_name(self, db_session: Session, sample_equipment: Equipment):
        """模糊匹配名称"""
        repo = EquipmentRepository(db_session)
        results = repo.search_by_name_fuzzy("赤刃")

        assert len(results) >= 1
        assert any(e.name == "光威赤刃" for e in results)

    def test_search_by_name_fuzzy_model(self, db_session: Session, sample_equipment: Equipment):
        """模糊匹配型号"""
        repo = EquipmentRepository(db_session)
        results = repo.search_by_name_fuzzy("CRE")

        assert len(results) >= 1
        assert any(e.model == "CRE001" for e in results)

    def test_search_by_name_fuzzy_brand(self, db_session: Session, sample_brand: Brand, sample_equipment: Equipment):
        """模糊匹配品牌名"""
        repo = EquipmentRepository(db_session)
        results = repo.search_by_name_fuzzy("光威")

        assert len(results) >= 1
        assert any(e.equipment_id == sample_equipment.equipment_id for e in results)

    def test_search_by_name_fuzzy_with_category(self, db_session: Session, sample_equipment: Equipment):
        """带类别过滤的模糊搜索"""
        repo = EquipmentRepository(db_session)

        # 正确类别
        results = repo.search_by_name_fuzzy("赤刃", category="鱼竿")
        assert len(results) >= 1

        # 错误类别
        results = repo.search_by_name_fuzzy("赤刃", category="渔轮")
        assert len(results) == 0

    def test_search_by_name_fuzzy_limit(self, db_session: Session, sample_brand: Brand):
        """limit 参数限制结果数量"""
        repo = EquipmentRepository(db_session)

        # 创建多个装备
        for i in range(5):
            equipment = Equipment(
                name=f"测试装备{i}",
                category="鱼竿",
                brand_id=sample_brand.brand_id,
                user_level="新手",
                is_active=True
            )
            db_session.add(equipment)
        db_session.commit()

        # 测试 limit
        results = repo.search_by_name_fuzzy("测试装备", limit=3)
        assert len(results) == 3

        results = repo.search_by_name_fuzzy("测试装备", limit=10)
        assert len(results) == 5

    def test_search_by_name_fuzzy_no_match(self, db_session: Session, sample_equipment: Equipment):
        """无匹配返回空列表"""
        repo = EquipmentRepository(db_session)
        results = repo.search_by_name_fuzzy("完全不存在的装备名称xyz")

        assert results == []

    # === get_by_ids 测试 ===

    def test_get_by_ids_single(self, db_session: Session, sample_equipment: Equipment):
        """单个 ID 查询"""
        repo = EquipmentRepository(db_session)
        results = repo.get_by_ids([sample_equipment.equipment_id])

        assert len(results) == 1
        assert results[0].equipment_id == sample_equipment.equipment_id

    def test_get_by_ids_multiple(self, db_session: Session, sample_brand: Brand):
        """多个 ID 查询"""
        repo = EquipmentRepository(db_session)

        # 创建多个装备
        ids = []
        for i in range(3):
            equipment = Equipment(
                name=f"批量测试{i}",
                category="鱼竿",
                brand_id=sample_brand.brand_id,
                user_level="新手",
                is_active=True
            )
            db_session.add(equipment)
            db_session.flush()
            ids.append(equipment.equipment_id)
        db_session.commit()

        results = repo.get_by_ids(ids)
        assert len(results) == 3

    def test_get_by_ids_preserves_order(self, db_session: Session, sample_brand: Brand):
        """批量查询保持输入顺序"""
        repo = EquipmentRepository(db_session)

        # 创建多个装备
        ids = []
        for i in range(4):
            equipment = Equipment(
                name=f"顺序测试{i}",
                category="鱼竿",
                brand_id=sample_brand.brand_id,
                user_level="新手",
                is_active=True
            )
            db_session.add(equipment)
            db_session.flush()
            ids.append(equipment.equipment_id)
        db_session.commit()

        # 以不同顺序查询
        query_order = [ids[2], ids[0], ids[3], ids[1]]
        results = repo.get_by_ids(query_order)

        assert len(results) == 4
        for i, equipment in enumerate(results):
            assert equipment.equipment_id == query_order[i]

    def test_get_by_ids_partial_missing(self, db_session: Session, sample_equipment: Equipment):
        """部分 ID 不存在时正确处理"""
        repo = EquipmentRepository(db_session)
        results = repo.get_by_ids([sample_equipment.equipment_id, 99999, 88888])

        assert len(results) == 1
        assert results[0].equipment_id == sample_equipment.equipment_id

    def test_get_by_ids_empty_list(self, db_session: Session):
        """空列表返回空列表"""
        repo = EquipmentRepository(db_session)
        results = repo.get_by_ids([])

        assert results == []

    def test_get_by_ids_all_missing(self, db_session: Session):
        """所有 ID 都不存在时返回空列表"""
        repo = EquipmentRepository(db_session)
        results = repo.get_by_ids([99999, 88888, 77777])

        assert results == []

    # === to_dict 测试 ===

    def test_to_dict_basic_fields(self, db_session: Session, sample_equipment: Equipment):
        """基础字段正确映射"""
        repo = EquipmentRepository(db_session)
        result = repo.to_dict(sample_equipment)

        assert result['id'] == sample_equipment.equipment_id
        assert result['equipment_id'] == sample_equipment.equipment_id
        assert result['name'] == "光威赤刃"
        assert result['category'] == "鱼竿"
        assert result['model'] == "CRE001"
        assert result['price_min'] == 200.0
        assert result['price_max'] == 300.0
        assert result['description'] == "入门级路亚竿"
        assert result['user_level'] == "新手"
        assert result['is_active'] == True  # SQLite stores boolean as 1/0

    def test_to_dict_brand_info(self, db_session: Session, sample_equipment: Equipment, sample_brand: Brand):
        """品牌信息正确包含"""
        repo = EquipmentRepository(db_session)
        # 确保 brand 被加载
        db_session.refresh(sample_equipment)
        result = repo.to_dict(sample_equipment)

        assert result['brand_id'] == sample_brand.brand_id
        assert result['brand_name'] == "光威"

    def test_to_dict_with_rod_specs(
        self, db_session: Session, sample_equipment: Equipment, sample_rod_spec: RodSpec
    ):
        """鱼竿规格正确包含"""
        repo = EquipmentRepository(db_session)
        db_session.refresh(sample_equipment)
        result = repo.to_dict(sample_equipment)

        assert 'specs' in result
        specs = result['specs']
        assert specs['length'] == 2.1
        assert specs['power'] == "M"
        assert specs['action'] == "Fast"
        assert specs['sections'] == 2
        assert specs['lure_weight_min'] == 5.0
        assert specs['lure_weight_max'] == 20.0

    def test_to_dict_without_specs(self, db_session: Session, sample_equipment: Equipment):
        """无规格时 specs 为空字典"""
        repo = EquipmentRepository(db_session)
        result = repo.to_dict(sample_equipment)

        assert 'specs' in result
        assert result['specs'] == {}

    def test_to_dict_timestamp_format(self, db_session: Session, sample_equipment: Equipment):
        """时间戳为 ISO 8601 格式或 None"""
        repo = EquipmentRepository(db_session)
        result = repo.to_dict(sample_equipment)

        # created_at 应该存在
        if result.get('created_at'):
            # 验证是 ISO 格式字符串
            assert isinstance(result['created_at'], str)
            assert 'T' in result['created_at']  # ISO 格式包含 T

    def test_to_dict_with_reel_specs(self, db_session: Session, sample_brand: Brand):
        """渔轮规格正确包含"""
        repo = EquipmentRepository(db_session)

        # 创建渔轮装备
        equipment = Equipment(
            name="测试渔轮",
            category="渔轮",
            brand_id=sample_brand.brand_id,
            user_level="进阶",
            is_active=True
        )
        db_session.add(equipment)
        db_session.flush()

        reel_spec = ReelSpec(
            equipment_id=equipment.equipment_id,
            reel_type="spinning",
            gear_ratio="6.2:1",
            max_drag=5.0,
            weight=230,
            line_capacity="0.23/150m",
            bearings=7
        )
        db_session.add(reel_spec)
        db_session.commit()
        db_session.refresh(equipment)

        result = repo.to_dict(equipment)

        assert result['category'] == "渔轮"
        specs = result['specs']
        assert specs['reel_type'] == "spinning"
        assert specs['gear_ratio'] == "6.2:1"
        assert specs['max_drag'] == 5.0

    def test_to_dict_with_line_specs(self, db_session: Session, sample_brand: Brand):
        """鱼线规格正确包含"""
        repo = EquipmentRepository(db_session)

        equipment = Equipment(
            name="测试鱼线",
            category="鱼线",
            brand_id=sample_brand.brand_id,
            user_level="新手",
            is_active=True
        )
        db_session.add(equipment)
        db_session.flush()

        line_spec = LineSpec(
            equipment_id=equipment.equipment_id,
            line_type="PE",
            diameter=0.16,
            strength_lb=20.0,
            length_m=150,
            color="绿色"
        )
        db_session.add(line_spec)
        db_session.commit()
        db_session.refresh(equipment)

        result = repo.to_dict(equipment)

        assert result['category'] == "鱼线"
        specs = result['specs']
        assert specs['line_type'] == "PE"
        assert specs['diameter'] == 0.16
        assert specs['strength_lb'] == 20.0

    def test_to_dict_with_lure_specs(self, db_session: Session, sample_brand: Brand):
        """拟饵规格正确包含"""
        repo = EquipmentRepository(db_session)

        equipment = Equipment(
            name="测试拟饵",
            category="拟饵",
            brand_id=sample_brand.brand_id,
            user_level="进阶",
            is_active=True
        )
        db_session.add(equipment)
        db_session.flush()

        lure_spec = LureSpec(
            equipment_id=equipment.equipment_id,
            lure_category="硬饵",
            lure_type="米诺",
            weight=10.5,
            length=8.0,
            diving_depth_min=0.5,
            diving_depth_max=1.5,
            color="银色"
        )
        db_session.add(lure_spec)
        db_session.commit()
        db_session.refresh(equipment)

        result = repo.to_dict(equipment)

        assert result['category'] == "拟饵"
        specs = result['specs']
        assert specs['lure_category'] == "硬饵"
        assert specs['weight'] == 10.5
        assert specs['diving_depth_min'] == 0.5
