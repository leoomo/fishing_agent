"""
Equipment Repository with advanced search capabilities
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from ..repository import BaseRepository
from ...models.equipment import Equipment, RodSpec, ReelSpec, LineSpec, LureSpec


class EquipmentRepository(BaseRepository[Equipment]):
    """Repository for Equipment with specialized queries"""

    def __init__(self, session: Session):
        super().__init__(session, Equipment)

    def get_with_details(self, equipment_id: int) -> Optional[Equipment]:
        """
        Get equipment with all related data preloaded (brand and specs)

        Args:
            equipment_id: Equipment ID

        Returns:
            Equipment instance with preloaded relationships or None
        """
        return (
            self.session.query(Equipment)
            .options(
                joinedload(Equipment.brand),
                joinedload(Equipment.rod_spec),
                joinedload(Equipment.reel_spec),
                joinedload(Equipment.line_spec),
                joinedload(Equipment.lure_spec),
            )
            .filter(Equipment.equipment_id == equipment_id)
            .first()
        )

    def search(
        self,
        category: Optional[str] = None,
        brand_id: Optional[int] = None,
        brand_name: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        user_level: Optional[str] = None,
        is_active: bool = True,
        keyword: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "equipment_id",
        preload: bool = True,
    ) -> List[Equipment]:
        """
        Advanced equipment search with multiple filters

        Args:
            category: Equipment category (鱼竿/渔轮/鱼线/拟饵/套装)
            brand_id: Brand ID filter
            brand_name: Brand name filter (partial match)
            price_min: Minimum price filter
            price_max: Maximum price filter
            user_level: User level filter (新手/进阶/高手)
            is_active: Only return active equipment
            keyword: Keyword search in name/description/features
            limit: Maximum number of results
            offset: Pagination offset
            order_by: Field to order by (prefix with '-' for descending)
            preload: Whether to preload brand and spec relationships

        Returns:
            List of matching equipment
        """
        query = self.session.query(Equipment)

        # Apply filters
        filters = []

        if category:
            filters.append(Equipment.category == category)

        if brand_id:
            filters.append(Equipment.brand_id == brand_id)

        if brand_name:
            # Join with Brand table for brand name filtering
            from ...models.brand import Brand
            query = query.join(Brand, Equipment.brand_id == Brand.brand_id)
            filters.append(Brand.name_cn.like(f"%{brand_name}%"))

        if price_min is not None:
            filters.append(
                or_(
                    Equipment.price_min >= price_min,
                    Equipment.price_max >= price_min
                )
            )

        if price_max is not None:
            filters.append(
                or_(
                    Equipment.price_min <= price_max,
                    Equipment.price_max <= price_max
                )
            )

        if user_level:
            filters.append(Equipment.user_level == user_level)

        if is_active:
            filters.append(Equipment.is_active == True)

        if keyword:
            # Search in name, description, and features
            keyword_filter = or_(
                Equipment.name.like(f"%{keyword}%"),
                Equipment.description.like(f"%{keyword}%"),
                Equipment.features.like(f"%{keyword}%"),
            )
            filters.append(keyword_filter)

        # Combine all filters
        if filters:
            query = query.filter(and_(*filters))

        # Preload relationships to avoid N+1 queries
        if preload:
            query = query.options(
                joinedload(Equipment.brand),
                joinedload(Equipment.rod_spec),
                joinedload(Equipment.reel_spec),
                joinedload(Equipment.line_spec),
                joinedload(Equipment.lure_spec),
            )

        # Apply ordering
        if order_by.startswith('-'):
            field = order_by[1:]
            if hasattr(Equipment, field):
                query = query.order_by(getattr(Equipment, field).desc())
        else:
            if hasattr(Equipment, order_by):
                query = query.order_by(getattr(Equipment, order_by))

        # Apply pagination
        query = query.offset(offset).limit(limit)

        return query.all()

    def search_rods(
        self,
        power: Optional[str] = None,
        action: Optional[str] = None,
        length_min: Optional[float] = None,
        length_max: Optional[float] = None,
        lure_weight_min: Optional[float] = None,
        lure_weight_max: Optional[float] = None,
        **kwargs
    ) -> List[Equipment]:
        """
        Search for fishing rods with rod-specific filters

        Args:
            power: Rod power (UL/L/ML/M/MH/H/XH)
            action: Rod action (Fast/Moderate/Slow)
            length_min: Minimum rod length in meters
            length_max: Maximum rod length in meters
            lure_weight_min: Minimum lure weight range
            lure_weight_max: Maximum lure weight range
            **kwargs: Additional filters passed to search()

        Returns:
            List of matching rod equipment
        """
        query = self.session.query(Equipment).join(RodSpec)

        # Force category to be rod
        kwargs['category'] = '鱼竿'

        # Build rod-specific filters
        rod_filters = []

        if power:
            rod_filters.append(RodSpec.power == power)

        if action:
            rod_filters.append(RodSpec.action == action)

        if length_min is not None:
            rod_filters.append(RodSpec.length >= length_min)

        if length_max is not None:
            rod_filters.append(RodSpec.length <= length_max)

        if lure_weight_min is not None:
            rod_filters.append(
                or_(
                    RodSpec.lure_weight_min >= lure_weight_min,
                    RodSpec.lure_weight_max >= lure_weight_min
                )
            )

        if lure_weight_max is not None:
            rod_filters.append(
                or_(
                    RodSpec.lure_weight_min <= lure_weight_max,
                    RodSpec.lure_weight_max <= lure_weight_max
                )
            )

        if rod_filters:
            query = query.filter(and_(*rod_filters))

        # Apply common filters from kwargs
        if kwargs.get('brand_id'):
            query = query.filter(Equipment.brand_id == kwargs['brand_id'])

        if kwargs.get('is_active', True):
            query = query.filter(Equipment.is_active == True)

        # Preload relationships
        query = query.options(
            joinedload(Equipment.brand),
            joinedload(Equipment.rod_spec),
        )

        # Apply pagination
        limit = kwargs.get('limit', 50)
        offset = kwargs.get('offset', 0)
        query = query.offset(offset).limit(limit)

        return query.all()

    def create_with_specs(
        self,
        equipment_data: Dict[str, Any],
        spec_data: Optional[Dict[str, Any]] = None
    ) -> Equipment:
        """
        Create equipment with specifications in one transaction

        Args:
            equipment_data: Equipment fields
            spec_data: Specification fields (rod/reel/line/lure spec)

        Returns:
            Created Equipment instance with specs
        """
        # Create equipment
        equipment = Equipment(**equipment_data)
        self.session.add(equipment)
        self.session.flush()  # Get equipment_id

        # Create spec if provided
        if spec_data:
            category = equipment_data.get('category')
            spec_data['equipment_id'] = equipment.equipment_id

            # 根据类别选择模型并过滤有效字段
            spec = None
            if category == '鱼竿':
                valid_fields = {c.name for c in RodSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields and v is not None}
                spec = RodSpec(**filtered_data)
            elif category == '渔轮':
                valid_fields = {c.name for c in ReelSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields and v is not None}
                spec = ReelSpec(**filtered_data)
            elif category == '鱼线':
                valid_fields = {c.name for c in LineSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields and v is not None}
                spec = LineSpec(**filtered_data)
            elif category == '拟饵':
                valid_fields = {c.name for c in LureSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields and v is not None}
                spec = LureSpec(**filtered_data)

            if spec:
                self.session.add(spec)
                self.session.flush()

        return equipment

    def update_with_specs(
        self,
        equipment_id: int,
        equipment_data: Dict[str, Any],
        spec_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Equipment]:
        """
        Update equipment and its specifications in one transaction

        Args:
            equipment_id: Equipment ID to update
            equipment_data: Equipment fields to update
            spec_data: Specification fields to update

        Returns:
            Updated Equipment instance or None if not found
        """
        equipment = self.get_with_details(equipment_id)
        if not equipment:
            return None

        # Update equipment fields
        for key, value in equipment_data.items():
            if hasattr(equipment, key) and value is not None:
                setattr(equipment, key, value)

        # Update or create specs
        if spec_data:
            category = equipment.category

            if category == '鱼竿':
                valid_fields = {c.name for c in RodSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields}
                if equipment.rod_spec:
                    for key, value in filtered_data.items():
                        if key != 'equipment_id':
                            setattr(equipment.rod_spec, key, value)
                else:
                    filtered_data['equipment_id'] = equipment_id
                    filtered_data = {k: v for k, v in filtered_data.items() if v is not None}
                    equipment.rod_spec = RodSpec(**filtered_data)

            elif category == '渔轮':
                valid_fields = {c.name for c in ReelSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields}
                if equipment.reel_spec:
                    for key, value in filtered_data.items():
                        if key != 'equipment_id':
                            setattr(equipment.reel_spec, key, value)
                else:
                    filtered_data['equipment_id'] = equipment_id
                    filtered_data = {k: v for k, v in filtered_data.items() if v is not None}
                    equipment.reel_spec = ReelSpec(**filtered_data)

            elif category == '鱼线':
                valid_fields = {c.name for c in LineSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields}
                if equipment.line_spec:
                    for key, value in filtered_data.items():
                        if key != 'equipment_id':
                            setattr(equipment.line_spec, key, value)
                else:
                    filtered_data['equipment_id'] = equipment_id
                    filtered_data = {k: v for k, v in filtered_data.items() if v is not None}
                    equipment.line_spec = LineSpec(**filtered_data)

            elif category == '拟饵':
                valid_fields = {c.name for c in LureSpec.__table__.columns}
                filtered_data = {k: v for k, v in spec_data.items() if k in valid_fields}
                if equipment.lure_spec:
                    for key, value in filtered_data.items():
                        if key != 'equipment_id':
                            setattr(equipment.lure_spec, key, value)
                else:
                    filtered_data['equipment_id'] = equipment_id
                    filtered_data = {k: v for k, v in filtered_data.items() if v is not None}
                    equipment.lure_spec = LureSpec(**filtered_data)

            self.session.flush()

        return equipment

    def get_by_category(
        self,
        category: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Equipment]:
        """
        Get equipment by category with preloaded relationships

        Args:
            category: Equipment category
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of equipment
        """
        return self.search(
            category=category,
            limit=limit,
            offset=offset,
            preload=True
        )

    def get_by_brand(
        self,
        brand_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Equipment]:
        """
        Get all equipment for a specific brand

        Args:
            brand_id: Brand ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of equipment
        """
        return self.search(
            brand_id=brand_id,
            limit=limit,
            offset=offset,
            preload=True
        )
