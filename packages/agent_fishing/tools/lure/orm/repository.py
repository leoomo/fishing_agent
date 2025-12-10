"""
Base Repository Pattern for SQLAlchemy ORM

Provides generic CRUD operations with type hints.
"""

from typing import TypeVar, Generic, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic base repository for CRUD operations

    Usage:
        class EquipmentRepository(BaseRepository[Equipment]):
            def __init__(self, session: Session):
                super().__init__(session, Equipment)
    """

    def __init__(self, session: Session, model: Type[T]):
        """
        Initialize repository

        Args:
            session: SQLAlchemy session
            model: Model class (e.g., Equipment, Brand)
        """
        self.session = session
        self.model = model

    def get(self, id: int) -> Optional[T]:
        """
        Get a single record by primary key

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        return self.session.get(self.model, id)

    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
    ) -> List[T]:
        """
        Get all records with optional filtering and pagination

        Args:
            filters: Dictionary of field=value filters
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field name to order by (prefix with '-' for descending)

        Returns:
            List of model instances
        """
        query = self.session.query(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                # Descending order
                field = order_by[1:]
                if hasattr(self.model, field):
                    query = query.order_by(getattr(self.model, field).desc())
            else:
                # Ascending order
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))

        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def create(self, obj: T) -> T:
        """
        Create a new record

        Args:
            obj: Model instance to create

        Returns:
            Created model instance with ID populated
        """
        self.session.add(obj)
        self.session.flush()  # Flush to get the ID without committing
        return obj

    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update a record by ID

        Args:
            id: Primary key value
            data: Dictionary of fields to update

        Returns:
            Updated model instance or None if not found
        """
        obj = self.get(id)
        if obj is None:
            return None

        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)

        self.session.flush()
        return obj

    def delete(self, id: int) -> bool:
        """
        Delete a record by ID

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found
        """
        obj = self.get(id)
        if obj is None:
            return False

        self.session.delete(obj)
        self.session.flush()
        return True

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering

        Args:
            filters: Dictionary of field=value filters

        Returns:
            Number of matching records
        """
        query = self.session.query(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.scalar()

    def exists(self, id: int) -> bool:
        """
        Check if a record exists

        Args:
            id: Primary key value

        Returns:
            True if exists, False otherwise
        """
        return self.session.query(
            self.session.query(self.model).filter_by(**{self._get_pk_name(): id}).exists()
        ).scalar()

    def _get_pk_name(self) -> str:
        """
        Get the primary key column name

        Returns:
            Primary key field name
        """
        return self.model.__mapper__.primary_key[0].name
