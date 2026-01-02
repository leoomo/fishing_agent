"""
Brand Repository for equipment manufacturers
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from ..repository import BaseRepository
from ...models.brand import Brand


class BrandRepository(BaseRepository[Brand]):
    """Repository for Brand with specialized queries"""

    def __init__(self, session: Session):
        super().__init__(session, Brand)

    def get_by_name(self, name_cn: str) -> Optional[Brand]:
        """
        Get brand by Chinese name

        Args:
            name_cn: Brand name in Chinese

        Returns:
            Brand instance or None if not found
        """
        return (
            self.session.query(Brand)
            .filter(Brand.name_cn == name_cn)
            .first()
        )

    def search_by_name(self, keyword: str, limit: int = 20) -> List[Brand]:
        """
        Search brands by name (partial match)

        Args:
            keyword: Keyword to search for
            limit: Maximum number of results

        Returns:
            List of matching brands
        """
        return (
            self.session.query(Brand)
            .filter(
                (Brand.name_cn.like(f"%{keyword}%")) |
                (Brand.name_en.like(f"%{keyword}%"))
            )
            .limit(limit)
            .all()
        )

    def get_active_brands(
        self,
        country: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Brand]:
        """
        Get all brands with optional country filter

        Args:
            country: Filter by country of origin
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of brands
        """
        query = self.session.query(Brand)

        if country:
            query = query.filter(Brand.country == country)

        return query.offset(offset).limit(limit).all()

    def get_with_equipment_count(self, brand_id: int) -> Optional[dict]:
        """
        Get brand with equipment count

        Args:
            brand_id: Brand ID

        Returns:
            Dictionary with brand data and equipment count
        """
        from ...models.equipment import Equipment
        from sqlalchemy import func

        result = (
            self.session.query(
                Brand,
                func.count(Equipment.equipment_id).label('equipment_count')
            )
            .outerjoin(Equipment, Brand.brand_id == Equipment.brand_id)
            .filter(Brand.brand_id == brand_id)
            .group_by(Brand.brand_id)
            .first()
        )

        if result is None:
            return None

        brand, equipment_count = result
        brand_dict = brand.to_dict()
        brand_dict['equipment_count'] = equipment_count

        return brand_dict

    def get_brands_with_equipment_counts(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """
        Get all brands with their equipment counts

        Args:
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of brand dictionaries with equipment counts
        """
        from ...models.equipment import Equipment
        from sqlalchemy import func

        results = (
            self.session.query(
                Brand,
                func.count(Equipment.equipment_id).label('equipment_count')
            )
            .outerjoin(Equipment, Brand.brand_id == Equipment.brand_id)
            .group_by(Brand.brand_id)
            .order_by(func.count(Equipment.equipment_id).desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        brands_with_counts = []
        for brand, equipment_count in results:
            brand_dict = brand.to_dict()
            brand_dict['equipment_count'] = equipment_count
            brands_with_counts.append(brand_dict)

        return brands_with_counts

    def create_brand(
        self,
        name_cn: str,
        name_en: Optional[str] = None,
        country: Optional[str] = None,
        website: Optional[str] = None,
        description: Optional[str] = None,
        logo_url: Optional[str] = None
    ) -> Brand:
        """
        Create a new brand

        Args:
            name_cn: Brand name in Chinese (required)
            name_en: Brand name in English
            country: Country of origin
            website: Official website URL
            description: Brand description
            logo_url: Brand logo image URL

        Returns:
            Created Brand instance
        """
        brand = Brand(
            name_cn=name_cn,
            name_en=name_en,
            country=country,
            description=description
        )

        self.session.add(brand)
        self.session.flush()

        return brand

    def get_or_create_by_name(self, name_cn: str) -> tuple[Brand, bool]:
        """
        Get existing brand by name or create new one

        Args:
            name_cn: Brand name in Chinese

        Returns:
            Tuple of (Brand instance, created: bool)
        """
        brand = self.get_by_name(name_cn)

        if brand is not None:
            return brand, False

        brand = self.create_brand(name_cn=name_cn)
        return brand, True
