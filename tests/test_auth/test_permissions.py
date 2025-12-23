"""
Tests for permission system
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.auth.permissions import (
    RoleEnum,
    PermissionEnum,
    has_permission,
    get_role_permissions
)
from apps.api.orm.session import get_db_session
from apps.api.orm.repositories.admin_user_repo import AdminUserRepository
from apps.api.auth.jwt import get_password_hash, create_access_token

client = TestClient(app)


class TestPermissionSystem:
    """Test cases for permission system"""

    def test_role_enum(self):
        """Test role enumeration"""
        assert RoleEnum.ADMIN.value == "admin"
        assert RoleEnum.EDITOR.value == "editor"
        assert RoleEnum.READONLY.value == "readonly"

    def test_permission_enum(self):
        """Test permission enumeration"""
        assert PermissionEnum.EQUIPMENT_CREATE.value == "equipment:create"
        assert PermissionEnum.EQUIPMENT_READ.value == "equipment:read"
        assert PermissionEnum.USER_MANAGE.value == "user:manage"

    def test_admin_has_all_permissions(self):
        """Test that admin has all permissions"""
        admin_permissions = get_role_permissions(RoleEnum.ADMIN)

        # Admin should have all permissions
        assert len(admin_permissions) == len(list(PermissionEnum))

        # Check specific permissions
        assert "equipment:create" in admin_permissions
        assert "equipment:delete" in admin_permissions
        assert "user:manage" in admin_permissions
        assert "config:update" in admin_permissions

    def test_editor_permissions(self):
        """Test editor role permissions"""
        editor_permissions = get_role_permissions(RoleEnum.EDITOR)

        # Editor can create/read/update
        assert "equipment:create" in editor_permissions
        assert "equipment:read" in editor_permissions
        assert "equipment:update" in editor_permissions

        # But cannot delete
        assert "equipment:delete" not in editor_permissions
        assert "user:manage" not in editor_permissions
        assert "config:update" not in editor_permissions

    def test_readonly_permissions(self):
        """Test readonly role permissions"""
        readonly_permissions = get_role_permissions(RoleEnum.READONLY)

        # Readonly can only read
        assert "equipment:read" in readonly_permissions
        assert "brand:read" in readonly_permissions
        assert "user:read" in readonly_permissions

        # Cannot create/update/delete
        assert "equipment:create" not in readonly_permissions
        assert "equipment:update" not in readonly_permissions
        assert "equipment:delete" not in readonly_permissions
        assert "user:manage" not in readonly_permissions

    def test_has_permission_function(self):
        """Test has_permission helper function"""
        # Admin has all permissions
        assert has_permission(RoleEnum.ADMIN, PermissionEnum.EQUIPMENT_DELETE) is True
        assert has_permission(RoleEnum.ADMIN, PermissionEnum.USER_MANAGE) is True

        # Editor has limited permissions
        assert has_permission(RoleEnum.EDITOR, PermissionEnum.EQUIPMENT_CREATE) is True
        assert has_permission(RoleEnum.EDITOR, PermissionEnum.EQUIPMENT_DELETE) is False

        # Readonly only has read permissions
        assert has_permission(RoleEnum.READONLY, PermissionEnum.EQUIPMENT_READ) is True
        assert has_permission(RoleEnum.READONLY, PermissionEnum.EQUIPMENT_CREATE) is False


class TestPermissionDependencies:
    """Test FastAPI permission dependencies"""

    @pytest.fixture(autouse=True)
    def setup_test_users(self):
        """Create test users with different roles"""
        with get_db_session() as session:
            repo = AdminUserRepository(session)

            # Clean up existing test users
            for username in ["test_admin", "test_editor", "test_readonly"]:
                existing = repo.get_by_username(username)
                if existing:
                    repo.delete(existing.id)

            session.commit()

            # Create admin user
            password_hash = get_password_hash("password123")
            self.admin_user = repo.create_admin_user(
                username="test_admin",
                email="admin@test.com",
                password_hash=password_hash,
                role="admin"
            )

            # Create editor user
            self.editor_user = repo.create_admin_user(
                username="test_editor",
                email="editor@test.com",
                password_hash=password_hash,
                role="editor"
            )

            # Create readonly user
            self.readonly_user = repo.create_admin_user(
                username="test_readonly",
                email="readonly@test.com",
                password_hash=password_hash,
                role="readonly"
            )

            session.commit()

            # Generate tokens
            self.admin_token = create_access_token({
                "user_id": self.admin_user.id,
                "username": self.admin_user.username,
                "role": self.admin_user.role
            })

            self.editor_token = create_access_token({
                "user_id": self.editor_user.id,
                "username": self.editor_user.username,
                "role": self.editor_user.role
            })

            self.readonly_token = create_access_token({
                "user_id": self.readonly_user.id,
                "username": self.readonly_user.username,
                "role": self.readonly_user.role
            })

            yield

            # Cleanup
            repo.delete(self.admin_user.id)
            repo.delete(self.editor_user.id)
            repo.delete(self.readonly_user.id)
            session.commit()

    def test_admin_can_access_profile(self):
        """Test admin can access their profile"""
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "test_admin"
        assert data["user"]["role"] == "admin"
        assert len(data["permissions"]) > 0

    def test_editor_can_access_profile(self):
        """Test editor can access their profile"""
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {self.editor_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "test_editor"
        assert data["user"]["role"] == "editor"

    def test_readonly_can_access_profile(self):
        """Test readonly user can access their profile"""
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {self.readonly_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "test_readonly"
        assert data["user"]["role"] == "readonly"

    def test_unauthenticated_cannot_access_profile(self):
        """Test unauthenticated user cannot access profile"""
        response = client.get("/api/v1/auth/profile")

        assert response.status_code == 403

    def test_invalid_token_cannot_access_profile(self):
        """Test invalid token cannot access profile"""
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401
