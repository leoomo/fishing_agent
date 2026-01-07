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

    def _apply_common_filters(self, query, kwargs: Dict[str, Any]):
        """
        Apply common filters to a query from kwargs

        Args:
            query: SQLAlchemy query object
            kwargs: Dictionary of filter parameters

        Returns:
            Query with filters applied
        """
        from datetime import datetime

        if kwargs.get('brand_id'):
            query = query.filter(Equipment.brand_id == kwargs['brand_id'])

        if kwargs.get('is_active', True):
            query = query.filter(Equipment.is_active == True)

        if kwargs.get('user_level'):
            query = query.filter(Equipment.user_level == kwargs['user_level'])

        if kwargs.get('keyword'):
            keyword = kwargs['keyword']
            query = query.filter(or_(
                Equipment.name.like(f"%{keyword}%"),
                Equipment.description.like(f"%{keyword}%"),
                Equipment.features.like(f"%{keyword}%"),
            ))

        if kwargs.get('price_min') is not None:
            query = query.filter(or_(
                Equipment.price_min >= kwargs['price_min'],
                Equipment.price_max >= kwargs['price_min']
            ))

        if kwargs.get('price_max') is not None:
            query = query.filter(or_(
                Equipment.price_min <= kwargs['price_max'],
                Equipment.price_max <= kwargs['price_max']
            ))

        # 通用扩展筛选
        if kwargs.get('source'):
            query = query.filter(Equipment.source == kwargs['source'])

        if kwargs.get('model'):
            query = query.filter(Equipment.model.like(f"%{kwargs['model']}%"))

        if kwargs.get('created_after'):
            try:
                dt = datetime.fromisoformat(kwargs['created_after'].replace('Z', '+00:00'))
                query = query.filter(Equipment.created_at >= dt)
            except ValueError:
                pass

        if kwargs.get('created_before'):
            try:
                dt = datetime.fromisoformat(kwargs['created_before'].replace('Z', '+00:00'))
                query = query.filter(Equipment.created_at <= dt)
            except ValueError:
                pass

        return query

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
        # 通用扩展筛选参数
        source: Optional[str] = None,
        model: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
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
            source: Data source filter (manual/crawler/import)
            model: Model name filter (partial match)
            created_after: Created after date (ISO format)
            created_before: Created before date (ISO format)
            limit: Maximum number of results
            offset: Pagination offset
            order_by: Field to order by (prefix with '-' for descending)
            preload: Whether to preload brand and spec relationships

        Returns:
            List of matching equipment
        """
        from datetime import datetime

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

        # 通用扩展筛选
        if source:
            filters.append(Equipment.source == source)

        if model:
            filters.append(Equipment.model.like(f"%{model}%"))

        if created_after:
            try:
                dt = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
                filters.append(Equipment.created_at >= dt)
            except ValueError:
                pass

        if created_before:
            try:
                dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
                filters.append(Equipment.created_at <= dt)
            except ValueError:
                pass

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
        sections: Optional[int] = None,
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
            sections: Number of rod sections
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

        if sections is not None:
            rod_filters.append(RodSpec.sections == sections)

        if rod_filters:
            query = query.filter(and_(*rod_filters))

        # Apply common filters from kwargs
        query = self._apply_common_filters(query, kwargs)

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

    def search_reels(
        self,
        reel_type: Optional[str] = None,
        max_drag_min: Optional[float] = None,
        max_drag_max: Optional[float] = None,
        weight_min: Optional[float] = None,
        weight_max: Optional[float] = None,
        **kwargs
    ) -> List[Equipment]:
        """
        Search for fishing reels with reel-specific filters

        Args:
            reel_type: Reel type (spinning/baitcasting/fly)
            max_drag_min: Minimum max drag (kg)
            max_drag_max: Maximum max drag (kg)
            weight_min: Minimum weight (g)
            weight_max: Maximum weight (g)
            **kwargs: Additional filters passed to search()

        Returns:
            List of matching reel equipment
        """
        query = self.session.query(Equipment).join(ReelSpec)

        # Force category to be reel
        kwargs['category'] = '渔轮'

        # Build reel-specific filters
        reel_filters = []

        if reel_type:
            reel_filters.append(ReelSpec.reel_type == reel_type)

        if max_drag_min is not None:
            reel_filters.append(ReelSpec.max_drag >= max_drag_min)

        if max_drag_max is not None:
            reel_filters.append(ReelSpec.max_drag <= max_drag_max)

        if weight_min is not None:
            reel_filters.append(ReelSpec.weight >= weight_min)

        if weight_max is not None:
            reel_filters.append(ReelSpec.weight <= weight_max)

        if reel_filters:
            query = query.filter(and_(*reel_filters))

        # Apply common filters from kwargs
        query = self._apply_common_filters(query, kwargs)

        # Preload relationships
        query = query.options(
            joinedload(Equipment.brand),
            joinedload(Equipment.reel_spec),
        )

        # Apply pagination
        limit = kwargs.get('limit', 50)
        offset = kwargs.get('offset', 0)
        query = query.offset(offset).limit(limit)

        return query.all()

    def search_lines(
        self,
        line_type: Optional[str] = None,
        diameter_min: Optional[float] = None,
        diameter_max: Optional[float] = None,
        strength_min: Optional[float] = None,
        strength_max: Optional[float] = None,
        **kwargs
    ) -> List[Equipment]:
        """
        Search for fishing lines with line-specific filters

        Args:
            line_type: Line type (PE/尼龙/碳线/钢丝)
            diameter_min: Minimum diameter (mm)
            diameter_max: Maximum diameter (mm)
            strength_min: Minimum strength (lb)
            strength_max: Maximum strength (lb)
            **kwargs: Additional filters passed to search()

        Returns:
            List of matching line equipment
        """
        query = self.session.query(Equipment).join(LineSpec)

        # Force category to be line
        kwargs['category'] = '鱼线'

        # Build line-specific filters
        line_filters = []

        if line_type:
            line_filters.append(LineSpec.line_type == line_type)

        if diameter_min is not None:
            line_filters.append(LineSpec.diameter >= diameter_min)

        if diameter_max is not None:
            line_filters.append(LineSpec.diameter <= diameter_max)

        if strength_min is not None:
            line_filters.append(LineSpec.strength_lb >= strength_min)

        if strength_max is not None:
            line_filters.append(LineSpec.strength_lb <= strength_max)

        if line_filters:
            query = query.filter(and_(*line_filters))

        # Apply common filters from kwargs
        query = self._apply_common_filters(query, kwargs)

        # Preload relationships
        query = query.options(
            joinedload(Equipment.brand),
            joinedload(Equipment.line_spec),
        )

        # Apply pagination
        limit = kwargs.get('limit', 50)
        offset = kwargs.get('offset', 0)
        query = query.offset(offset).limit(limit)

        return query.all()

    def search_lures(
        self,
        lure_category: Optional[str] = None,
        weight_min: Optional[float] = None,
        weight_max: Optional[float] = None,
        diving_depth_min: Optional[float] = None,
        diving_depth_max: Optional[float] = None,
        **kwargs
    ) -> List[Equipment]:
        """
        Search for lures with lure-specific filters

        Args:
            lure_category: Lure category (硬饵/软饵/金属饵/飞蝇)
            weight_min: Minimum weight (g)
            weight_max: Maximum weight (g)
            diving_depth_min: Minimum diving depth (m)
            diving_depth_max: Maximum diving depth (m)
            **kwargs: Additional filters passed to search()

        Returns:
            List of matching lure equipment
        """
        query = self.session.query(Equipment).join(LureSpec)

        # Force category to be lure
        kwargs['category'] = '拟饵'

        # Build lure-specific filters
        lure_filters = []

        if lure_category:
            lure_filters.append(LureSpec.lure_category == lure_category)

        if weight_min is not None:
            lure_filters.append(LureSpec.weight >= weight_min)

        if weight_max is not None:
            lure_filters.append(LureSpec.weight <= weight_max)

        if diving_depth_min is not None:
            lure_filters.append(
                or_(
                    LureSpec.diving_depth_min >= diving_depth_min,
                    LureSpec.diving_depth_max >= diving_depth_min
                )
            )

        if diving_depth_max is not None:
            lure_filters.append(
                or_(
                    LureSpec.diving_depth_min <= diving_depth_max,
                    LureSpec.diving_depth_max <= diving_depth_max
                )
            )

        if lure_filters:
            query = query.filter(and_(*lure_filters))

        # Apply common filters from kwargs
        query = self._apply_common_filters(query, kwargs)

        # Preload relationships
        query = query.options(
            joinedload(Equipment.brand),
            joinedload(Equipment.lure_spec),
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

    # === Agent Tools 专用方法 ===

    def search_by_name_exact(
        self,
        name: str,
        category: Optional[str] = None
    ) -> Optional[Equipment]:
        """
        精确匹配搜索 (name 或 model 完��匹配)

        Args:
            name: 搜索名称
            category: 装备类别（可选）

        Returns:
            匹配的装备或 None
        """
        query = self.session.query(Equipment).options(
            joinedload(Equipment.brand),
            joinedload(Equipment.rod_spec),
            joinedload(Equipment.reel_spec),
            joinedload(Equipment.line_spec),
            joinedload(Equipment.lure_spec),
        )

        # 精确匹配 name 或 model
        query = query.filter(
            or_(
                Equipment.name == name,
                Equipment.model == name
            )
        )

        if category:
            query = query.filter(Equipment.category == category)

        return query.first()

    def search_by_name_fuzzy(
        self,
        name: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Equipment]:
        """
        模糊匹配搜索 (name/model/brand_name 包含)

        Args:
            name: 搜索名称
            category: 装备类别（可选）
            limit: 返回数量限制

        Returns:
            匹配的装备列表
        """
        from ...models.brand import Brand

        query = self.session.query(Equipment).outerjoin(
            Brand, Equipment.brand_id == Brand.brand_id
        ).options(
            joinedload(Equipment.brand),
            joinedload(Equipment.rod_spec),
            joinedload(Equipment.reel_spec),
            joinedload(Equipment.line_spec),
            joinedload(Equipment.lure_spec),
        )

        # 模糊匹配 name, model 或 brand_name
        pattern = f"%{name}%"
        query = query.filter(
            or_(
                Equipment.name.like(pattern),
                Equipment.model.like(pattern),
                Brand.name_cn.like(pattern)
            )
        )

        if category:
            query = query.filter(Equipment.category == category)

        return query.limit(limit).all()

    def get_by_ids(
        self,
        equipment_ids: List[int],
        preload: bool = True
    ) -> List[Equipment]:
        """
        批量按ID查询 (保持输入顺序)

        Args:
            equipment_ids: 装备ID列表
            preload: 是否预加载关联数据

        Returns:
            装备列表（保持输入顺序）
        """
        if not equipment_ids:
            return []

        query = self.session.query(Equipment).filter(
            Equipment.equipment_id.in_(equipment_ids)
        )

        if preload:
            query = query.options(
                joinedload(Equipment.brand),
                joinedload(Equipment.rod_spec),
                joinedload(Equipment.reel_spec),
                joinedload(Equipment.line_spec),
                joinedload(Equipment.lure_spec),
            )

        results = query.all()

        # 按输入顺序排序
        id_to_equipment = {e.equipment_id: e for e in results}
        return [id_to_equipment[eid] for eid in equipment_ids if eid in id_to_equipment]

    def to_dict(self, equipment: Equipment) -> Dict[str, Any]:
        """
        将 Equipment 实例转为字典 (兼容原有格式)

        Args:
            equipment: Equipment 实例

        Returns:
            字典格式的装备数据
        """
        result = {
            'id': equipment.equipment_id,
            'equipment_id': equipment.equipment_id,
            'name': equipment.name,
            'category': equipment.category,
            'brand_id': equipment.brand_id,
            'brand_name': equipment.brand.name_cn if equipment.brand else None,
            'model': equipment.model,
            'price_min': equipment.price_min,
            'price_max': equipment.price_max,
            'description': equipment.description,
            'features': equipment.features,
            'user_level': equipment.user_level,
            'source': equipment.source,
            'is_active': equipment.is_active,
            'created_at': equipment.created_at.isoformat() if equipment.created_at else None,
            'updated_at': equipment.updated_at.isoformat() if equipment.updated_at else None,
        }

        # 添加规格数据
        if equipment.rod_spec:
            result['specs'] = {
                'length': equipment.rod_spec.length,
                'power': equipment.rod_spec.power,
                'action': equipment.rod_spec.action,
                'sections': equipment.rod_spec.sections,
                'weight': equipment.rod_spec.weight,
                'lure_weight_min': equipment.rod_spec.lure_weight_min,
                'lure_weight_max': equipment.rod_spec.lure_weight_max,
                'line_weight_min': equipment.rod_spec.line_weight_min,
                'line_weight_max': equipment.rod_spec.line_weight_max,
            }
        elif equipment.reel_spec:
            result['specs'] = {
                'reel_type': equipment.reel_spec.reel_type,
                'gear_ratio': equipment.reel_spec.gear_ratio,
                'max_drag': equipment.reel_spec.max_drag,
                'weight': equipment.reel_spec.weight,
                'line_capacity': equipment.reel_spec.line_capacity,
                'bearings': equipment.reel_spec.bearings,
            }
        elif equipment.line_spec:
            result['specs'] = {
                'line_type': equipment.line_spec.line_type,
                'diameter': equipment.line_spec.diameter,
                'strength_lb': equipment.line_spec.strength_lb,
                'length_m': equipment.line_spec.length_m,
                'color': equipment.line_spec.color,
            }
        elif equipment.lure_spec:
            result['specs'] = {
                'lure_category': equipment.lure_spec.lure_category,
                'lure_type': equipment.lure_spec.lure_type,
                'weight': equipment.lure_spec.weight,
                'length': equipment.lure_spec.length,
                'diving_depth_min': equipment.lure_spec.diving_depth_min,
                'diving_depth_max': equipment.lure_spec.diving_depth_max,
                'color': equipment.lure_spec.color,
            }
        else:
            result['specs'] = {}

        return result
