"""
Tests for EquipmentRepository
"""

import pytest
from sqlalchemy.orm import Session

from packages.agent_fishing.tools.lure.orm.repositories import EquipmentRepository
from packages.agent_fishing.tools.lure.models import Equipment, Brand, RodSpec


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
