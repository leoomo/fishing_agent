"""
Tests for BrandRepository
"""

import pytest
from sqlalchemy.orm import Session

from packages.agent_fishing.tools.lure.orm.repositories import BrandRepository
from packages.agent_fishing.tools.lure.models import Brand, Equipment


class TestBrandRepository:
    """Test cases for BrandRepository"""

    def test_get_brand(self, db_session: Session, sample_brand: Brand):
        """Test getting brand by ID"""
        repo = BrandRepository(db_session)
        brand = repo.get(sample_brand.brand_id)

        assert brand is not None
        assert brand.brand_id == sample_brand.brand_id
        assert brand.name_cn == "光威"

    def test_get_by_name(self, db_session: Session, sample_brand: Brand):
        """Test getting brand by Chinese name"""
        repo = BrandRepository(db_session)
        brand = repo.get_by_name("光威")

        assert brand is not None
        assert brand.name_cn == "光威"
        assert brand.name_en == "GW"

    def test_search_by_name(self, db_session: Session, sample_brand: Brand):
        """Test searching brands by name"""
        repo = BrandRepository(db_session)

        # Search Chinese name
        results = repo.search_by_name("光")
        assert len(results) == 1
        assert results[0].name_cn == "光威"

        # Search English name
        results = repo.search_by_name("GW")
        assert len(results) == 1

        # No match
        results = repo.search_by_name("不存在的品牌")
        assert len(results) == 0

    def test_get_active_brands(self, db_session: Session, sample_brand: Brand):
        """Test getting active brands"""
        repo = BrandRepository(db_session)
        results = repo.get_active_brands()

        assert len(results) == 1
        assert results[0].is_active is True

    def test_get_active_brands_by_country(self, db_session: Session, sample_brand: Brand):
        """Test getting active brands filtered by country"""
        repo = BrandRepository(db_session)

        # Match country
        results = repo.get_active_brands(country="中国")
        assert len(results) == 1

        # No match
        results = repo.get_active_brands(country="日本")
        assert len(results) == 0

    def test_get_with_equipment_count(self, db_session: Session, sample_brand: Brand, sample_equipment: Equipment):
        """Test getting brand with equipment count"""
        repo = BrandRepository(db_session)
        result = repo.get_with_equipment_count(sample_brand.brand_id)

        assert result is not None
        assert result['name_cn'] == "光威"
        assert result['equipment_count'] == 1

    def test_get_brands_with_equipment_counts(self, db_session: Session, sample_brand: Brand, sample_equipment: Equipment):
        """Test getting all brands with equipment counts"""
        repo = BrandRepository(db_session)
        results = repo.get_brands_with_equipment_counts()

        assert len(results) == 1
        assert results[0]['name_cn'] == "光威"
        assert results[0]['equipment_count'] == 1

    def test_create_brand(self, db_session: Session):
        """Test creating a brand"""
        repo = BrandRepository(db_session)

        brand = repo.create_brand(
            name_cn="达瓦",
            name_en="DAIWA",
            country="日本",
            description="全球知名钓具品牌"
        )
        db_session.commit()

        assert brand.brand_id is not None
        assert brand.name_cn == "达瓦"
        assert brand.country == "日本"
        assert brand.is_active is True

    def test_get_or_create_by_name_existing(self, db_session: Session, sample_brand: Brand):
        """Test get_or_create with existing brand"""
        repo = BrandRepository(db_session)

        brand, created = repo.get_or_create_by_name("光威")

        assert created is False
        assert brand.brand_id == sample_brand.brand_id

    def test_get_or_create_by_name_new(self, db_session: Session):
        """Test get_or_create with new brand"""
        repo = BrandRepository(db_session)

        brand, created = repo.get_or_create_by_name("新品牌")
        db_session.commit()

        assert created is True
        assert brand.brand_id is not None
        assert brand.name_cn == "新品牌"

    def test_update_brand(self, db_session: Session, sample_brand: Brand):
        """Test updating brand"""
        repo = BrandRepository(db_session)

        updated = repo.update(
            sample_brand.brand_id,
            {'website': 'https://www.guangwei.com', 'description': '更新的描述'}
        )
        db_session.commit()

        assert updated is not None
        assert updated.website == 'https://www.guangwei.com'
        assert updated.description == '更新的描述'

    def test_delete_brand(self, db_session: Session):
        """Test deleting brand"""
        repo = BrandRepository(db_session)

        # Create a brand without equipment
        brand = repo.create_brand(name_cn="测试品牌")
        db_session.commit()
        brand_id = brand.brand_id

        result = repo.delete(brand_id)
        db_session.commit()

        assert result is True

        # Verify deletion
        brand = repo.get(brand_id)
        assert brand is None
