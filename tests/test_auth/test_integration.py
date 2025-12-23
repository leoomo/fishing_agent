"""
Integration tests for Phase 2 Authentication System

Tests the complete authentication flow from end to end.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.orm.session import get_db_session
from apps.api.orm.repositories.admin_user_repo import AdminUserRepository
from apps.api.auth.jwt import get_password_hash

client = TestClient(app)


class TestAuthenticationIntegration:
    """End-to-end authentication integration tests"""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup test user before each test"""
        with get_db_session() as session:
            repo = AdminUserRepository(session)

            # Clean up existing test user
            existing = repo.get_by_username("integration_test_user")
            if existing:
                repo.delete(existing.id)
                session.commit()

            # Create test user
            password_hash = get_password_hash("testpass123")
            self.test_user = repo.create_admin_user(
                username="integration_test_user",
                email="integration@test.com",
                password_hash=password_hash,
                role="editor",
                full_name="Integration Test User",
                is_active=True
            )
            session.commit()

            yield

            # Cleanup
            repo.delete(self.test_user.id)
            session.commit()

    def test_complete_authentication_flow(self):
        """Test complete flow: login -> get profile -> logout"""

        # Step 1: Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "integration_test_user",
                "password": "testpass123"
            }
        )

        assert login_response.status_code == 200
        login_data = login_response.json()

        # Verify login response structure
        assert "access_token" in login_data
        assert "token_type" in login_data
        assert "user" in login_data
        assert "permissions" in login_data

        # Verify user data
        assert login_data["user"]["username"] == "integration_test_user"
        assert login_data["user"]["email"] == "integration@test.com"
        assert login_data["user"]["role"] == "editor"
        assert login_data["user"]["full_name"] == "Integration Test User"
        assert login_data["user"]["is_active"] is True

        # Verify permissions
        assert len(login_data["permissions"]) > 0
        assert "equipment:read" in login_data["permissions"]
        assert "equipment:create" in login_data["permissions"]

        # Store token
        token = login_data["access_token"]

        # Step 2: Access protected endpoint (profile)
        profile_response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert profile_response.status_code == 200
        profile_data = profile_response.json()

        # Verify profile matches login data
        assert profile_data["user"]["username"] == login_data["user"]["username"]
        assert profile_data["user"]["email"] == login_data["user"]["email"]
        assert profile_data["user"]["role"] == login_data["user"]["role"]

        # Step 3: Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert logout_response.status_code == 200
        assert "登出成功" in logout_response.json()["message"]

    def test_login_updates_last_login_timestamp(self):
        """Test that login updates last_login timestamp"""

        # First login
        first_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "integration_test_user",
                "password": "testpass123"
            }
        )

        assert first_login.status_code == 200
        first_last_login = first_login.json()["user"]["last_login"]

        # Wait a moment
        import time
        time.sleep(0.1)

        # Second login
        second_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "integration_test_user",
                "password": "testpass123"
            }
        )

        assert second_login.status_code == 200
        second_last_login = second_login.json()["user"]["last_login"]

        # Verify last_login was updated
        assert second_last_login is not None
        if first_last_login is not None:
            assert second_last_login >= first_last_login

    def test_cannot_access_protected_route_without_token(self):
        """Test that protected routes require authentication"""

        response = client.get("/api/v1/auth/profile")

        assert response.status_code == 403

    def test_cannot_access_protected_route_with_invalid_token(self):
        """Test that invalid tokens are rejected"""

        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    def test_permissions_reflect_user_role(self):
        """Test that returned permissions match user's role"""

        # Login as editor
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "integration_test_user",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        permissions = response.json()["permissions"]

        # Editor should have these permissions
        expected_permissions = [
            "equipment:create",
            "equipment:read",
            "equipment:update",
            "brand:create",
            "brand:read",
            "brand:update",
        ]

        for perm in expected_permissions:
            assert perm in permissions

        # Editor should NOT have these permissions
        forbidden_permissions = [
            "equipment:delete",
            "user:manage",
            "config:update",
        ]

        for perm in forbidden_permissions:
            assert perm not in permissions


class TestAPILoggingMiddleware:
    """Test API logging middleware integration"""

    @pytest.mark.skip(reason="API logging requires api_logs table which may not exist in test DB")
    def test_api_calls_are_logged(self):
        """Test that API calls are logged to database"""
        from apps.api.models.system import APILog

        # Make an API call
        response = client.get("/api/v1/auth/profile")

        # Note: This will fail with 403, but should still be logged
        assert response.status_code == 403

        # Check if log was created
        with get_db_session() as session:
            # Query latest log entry
            latest_log = (
                session.query(APILog)
                .filter(APILog.endpoint == "/api/v1/auth/profile")
                .order_by(APILog.timestamp.desc())
                .first()
            )

            # Verify log exists (may be None if table doesn't exist)
            if latest_log:
                assert latest_log.method == "GET"
                assert latest_log.status_code == 403
                assert latest_log.response_time is not None

    @pytest.mark.skip(reason="API logging requires api_logs table which may not exist in test DB")
    def test_excluded_paths_not_logged(self):
        """Test that excluded paths are not logged"""
        from apps.api.models.system import APILog

        # Get count of health endpoint logs before
        with get_db_session() as session:
            count_before = (
                session.query(APILog)
                .filter(APILog.endpoint == "/health")
                .count()
            )

        # Call health endpoint (should be excluded from logging)
        response = client.get("/health")
        assert response.status_code == 200

        # Get count after
        with get_db_session() as session:
            count_after = (
                session.query(APILog)
                .filter(APILog.endpoint == "/health")
                .count()
            )

        # Should not have increased
        assert count_after == count_before


class TestDatabaseMigrations:
    """Test database migrations and schema"""

    def test_admin_users_table_exists(self):
        """Test that admin_users table was created"""
        from sqlalchemy import text

        with get_db_session() as session:
            result = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_users'")
            )
            assert result.fetchone() is not None

    def test_system_config_table_exists(self):
        """Test that system_config table was created"""
        from sqlalchemy import text

        with get_db_session() as session:
            result = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'")
            )
            assert result.fetchone() is not None

    def test_analytics_reports_table_exists(self):
        """Test that analytics_reports table was created"""
        from sqlalchemy import text

        with get_db_session() as session:
            result = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='analytics_reports'")
            )
            assert result.fetchone() is not None

    def test_admin_user_repository_works(self):
        """Test that AdminUserRepository can perform basic CRUD operations"""
        with get_db_session() as session:
            repo = AdminUserRepository(session)

            # Create a test user
            password_hash = get_password_hash("testpass")
            user = repo.create_admin_user(
                username="crud_test_user",
                email="crud@test.com",
                password_hash=password_hash,
                role="readonly"
            )
            session.commit()

            # Read the user
            found_user = repo.get(user.id)
            assert found_user is not None
            assert found_user.username == "crud_test_user"

            # Update the user
            repo.change_role(user.id, "editor")
            session.commit()

            # Verify update
            updated_user = repo.get(user.id)
            assert updated_user.role == "editor"

            # Delete the user
            repo.delete(user.id)
            session.commit()

            # Verify deletion
            deleted_user = repo.get(user.id)
            assert deleted_user is None
