"""
Admin User Repository for backend user management
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..repository import BaseRepository
from ...models.admin_user import AdminUser


class AdminUserRepository(BaseRepository[AdminUser]):
    """Repository for AdminUser with specialized queries"""

    def __init__(self, session: Session):
        super().__init__(session, AdminUser)

    def get_by_username(self, username: str) -> Optional[AdminUser]:
        """
        Get admin user by username

        Args:
            username: Username

        Returns:
            AdminUser instance or None if not found
        """
        return (
            self.session.query(AdminUser)
            .filter(AdminUser.username == username)
            .first()
        )

    def get_by_email(self, email: str) -> Optional[AdminUser]:
        """
        Get admin user by email

        Args:
            email: Email address

        Returns:
            AdminUser instance or None if not found
        """
        return (
            self.session.query(AdminUser)
            .filter(AdminUser.email == email)
            .first()
        )

    def update_last_login(self, user_id: int) -> bool:
        """
        Update last login timestamp

        Args:
            user_id: User ID (admin_users.id)

        Returns:
            bool: True if updated, False if user not found
        """
        user = self.get(user_id)
        if user is None:
            return False

        user.last_login = datetime.utcnow().isoformat()
        self.session.flush()
        return True

    def create_admin_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "readonly",
        full_name: Optional[str] = None,
        is_active: bool = True
    ) -> AdminUser:
        """
        Create a new admin user

        Args:
            username: Username
            email: Email address
            password_hash: Bcrypt hashed password
            role: User role (admin/editor/readonly)
            full_name: Full name (optional)
            is_active: Whether user is active

        Returns:
            AdminUser: Created user instance
        """
        admin_user = AdminUser(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            full_name=full_name,
            is_active=is_active
        )

        self.session.add(admin_user)
        self.session.flush()

        return admin_user

    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate user account

        Args:
            user_id: User ID

        Returns:
            bool: True if deactivated, False if user not found
        """
        user = self.get(user_id)
        if user is None:
            return False

        user.is_active = False
        self.session.flush()
        return True

    def activate_user(self, user_id: int) -> bool:
        """
        Activate user account

        Args:
            user_id: User ID

        Returns:
            bool: True if activated, False if user not found
        """
        user = self.get(user_id)
        if user is None:
            return False

        user.is_active = True
        self.session.flush()
        return True

    def change_role(self, user_id: int, new_role: str) -> bool:
        """
        Change user role

        Args:
            user_id: User ID
            new_role: New role (admin/editor/readonly)

        Returns:
            bool: True if changed, False if user not found
        """
        user = self.get(user_id)
        if user is None:
            return False

        user.role = new_role
        self.session.flush()
        return True

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """
        Update user password

        Args:
            user_id: User ID
            new_password_hash: New bcrypt hashed password

        Returns:
            bool: True if updated, False if user not found
        """
        user = self.get(user_id)
        if user is None:
            return False

        user.password_hash = new_password_hash
        self.session.flush()
        return True
