"""
User Repository for user management and equipment tracking
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload

from ..repository import BaseRepository
from ...models.user import User, UserEquipment, FishingLog


class UserRepository(BaseRepository[User]):
    """Repository for User with specialized queries"""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username

        Args:
            username: Username

        Returns:
            User instance or None if not found
        """
        return (
            self.session.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            email: Email address

        Returns:
            User instance or None if not found
        """
        return (
            self.session.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_with_equipment(self, user_id: int) -> Optional[User]:
        """
        Get user with all equipment preloaded

        Args:
            user_id: User ID

        Returns:
            User instance with equipment relationships loaded
        """
        return (
            self.session.query(User)
            .options(
                joinedload(User.equipment).joinedload(UserEquipment.equipment)
            )
            .filter(User.user_id == user_id)
            .first()
        )

    def get_with_fishing_logs(self, user_id: int) -> Optional[User]:
        """
        Get user with all fishing logs preloaded

        Args:
            user_id: User ID

        Returns:
            User instance with fishing logs loaded
        """
        return (
            self.session.query(User)
            .options(joinedload(User.fishing_logs))
            .filter(User.user_id == user_id)
            .first()
        )


class UserEquipmentRepository(BaseRepository[UserEquipment]):
    """Repository for UserEquipment (user's equipment inventory)"""

    def __init__(self, session: Session):
        super().__init__(session, UserEquipment)

    def get_user_equipment(
        self,
        user_id: int,
        category: Optional[str] = None,
        is_favorite: Optional[bool] = None
    ) -> List[UserEquipment]:
        """
        Get all equipment for a user with filters

        Args:
            user_id: User ID
            category: Optional equipment category filter
            is_favorite: Optional favorite filter

        Returns:
            List of user equipment
        """
        from ...models.equipment import Equipment

        query = (
            self.session.query(UserEquipment)
            .join(Equipment)
            .options(
                joinedload(UserEquipment.equipment)
                .joinedload(Equipment.brand)
            )
            .filter(UserEquipment.user_id == user_id)
        )

        if category:
            query = query.filter(Equipment.category == category)

        if is_favorite is not None:
            query = query.filter(UserEquipment.is_favorite == (1 if is_favorite else 0))

        return query.all()

    def add_equipment(
        self,
        user_id: int,
        equipment_id: int,
        purchase_date: Optional[date] = None,
        purchase_price: Optional[float] = None,
        condition: str = "new",
        notes: Optional[str] = None
    ) -> UserEquipment:
        """
        Add equipment to user's inventory

        Args:
            user_id: User ID
            equipment_id: Equipment ID
            purchase_date: Date of purchase
            purchase_price: Purchase price
            condition: Equipment condition
            notes: User notes

        Returns:
            Created UserEquipment instance
        """
        user_equipment = UserEquipment(
            user_id=user_id,
            equipment_id=equipment_id,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            condition=condition,
            notes=notes
        )

        self.session.add(user_equipment)
        self.session.flush()

        return user_equipment

    def toggle_favorite(self, id: int) -> Optional[UserEquipment]:
        """
        Toggle favorite status for user equipment

        Args:
            id: UserEquipment ID

        Returns:
            Updated UserEquipment instance or None
        """
        user_equipment = self.get(id)
        if user_equipment is None:
            return None

        user_equipment.is_favorite = 1 if user_equipment.is_favorite == 0 else 0
        self.session.flush()

        return user_equipment


class FishingLogRepository(BaseRepository[FishingLog]):
    """Repository for FishingLog (user's fishing diary)"""

    def __init__(self, session: Session):
        super().__init__(session, FishingLog)

    def get_user_logs(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[FishingLog]:
        """
        Get fishing logs for a user with optional date range

        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of fishing logs
        """
        query = (
            self.session.query(FishingLog)
            .filter(FishingLog.user_id == user_id)
            .order_by(FishingLog.date.desc())
        )

        if start_date:
            query = query.filter(FishingLog.date >= start_date)

        if end_date:
            query = query.filter(FishingLog.date <= end_date)

        return query.offset(offset).limit(limit).all()

    def create_log(
        self,
        user_id: int,
        location: str,
        date: date,
        weather_condition: Optional[str] = None,
        temperature: Optional[float] = None,
        fish_caught: Optional[str] = None,
        total_count: Optional[int] = None,
        total_weight: Optional[float] = None,
        equipment_used: Optional[str] = None,
        notes: Optional[str] = None,
        images: Optional[str] = None
    ) -> FishingLog:
        """
        Create a new fishing log entry

        Args:
            user_id: User ID
            location: Fishing location
            date: Fishing date
            weather_condition: Weather conditions
            temperature: Temperature in Celsius
            fish_caught: Fish species caught
            total_count: Total number of fish
            total_weight: Total weight in kg
            equipment_used: Equipment used (JSON format)
            notes: Notes and observations
            images: Image URLs (JSON array)

        Returns:
            Created FishingLog instance
        """
        fishing_log = FishingLog(
            user_id=user_id,
            location=location,
            date=date,
            weather_condition=weather_condition,
            temperature=temperature,
            fish_caught=fish_caught,
            total_count=total_count,
            total_weight=total_weight,
            equipment_used=equipment_used,
            notes=notes,
            images=images
        )

        self.session.add(fishing_log)
        self.session.flush()

        return fishing_log

    def get_statistics(self, user_id: int) -> dict:
        """
        Get fishing statistics for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func

        stats = (
            self.session.query(
                func.count(FishingLog.id).label('total_trips'),
                func.sum(FishingLog.total_count).label('total_fish'),
                func.sum(FishingLog.total_weight).label('total_weight'),
                func.avg(FishingLog.total_count).label('avg_fish_per_trip')
            )
            .filter(FishingLog.user_id == user_id)
            .first()
        )

        return {
            'total_trips': stats.total_trips or 0,
            'total_fish': stats.total_fish or 0,
            'total_weight': float(stats.total_weight or 0),
            'avg_fish_per_trip': float(stats.avg_fish_per_trip or 0)
        }
