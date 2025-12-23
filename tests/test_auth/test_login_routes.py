"""
Tests for authentication routes

Note: These are integration tests that require a running database.
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.orm.session import get_db_session
from apps.api.orm.repositories.admin_user_repo import AdminUserRepository
from apps.api.auth.jwt import get_password_hash

client = TestClient(app)


class TestLoginRoutes:
    """Test cases for login routes"""

    @pytest.fixture(autouse=True)
    def setup_test_user(self):
        """Create a test user before each test"""
        with get_db_session() as session:
            repo = AdminUserRepository(session)

            # Clean up any existing test user
            existing_user = repo.get_by_username("testuser")
            if existing_user:
                repo.delete(existing_user.id)
                session.commit()

            # Create test user
            password_hash = get_password_hash("testpass123")
            self.test_user = repo.create_admin_user(
                username="testuser",
                email="testuser@example.com",
                password_hash=password_hash,
                role="admin",
                full_name="Test User",
                is_active=True
            )
            session.commit()

            yield

            # Cleanup after test
            repo.delete(self.test_user.id)
            session.commit()

    def test_login_success(self):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "testuser@example.com"
        assert data["user"]["role"] == "admin"
        assert data["user"]["is_active"] is True
        assert len(data["permissions"]) > 0

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login with non-existent username"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "anypassword"
            }
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_inactive_user(self):
        """Test login with inactive user"""
        # Deactivate the test user
        with get_db_session() as session:
            repo = AdminUserRepository(session)
            repo.deactivate_user(self.test_user.id)
            session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )

        assert response.status_code == 403
        assert "账户已被禁用" in response.json()["detail"]

    def test_get_profile(self):
        """Test get profile endpoint"""
        # First login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]

        # Get profile
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user"]["username"] == "testuser"
        assert data["user"]["role"] == "admin"
        assert len(data["permissions"]) > 0

    def test_get_profile_without_token(self):
        """Test get profile without authentication"""
        response = client.get("/api/v1/auth/profile")

        assert response.status_code == 403

    def test_get_profile_with_invalid_token(self):
        """Test get profile with invalid token"""
        response = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    def test_logout(self):
        """Test logout endpoint"""
        # First login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert "登出成功" in response.json()["message"]

    def test_login_validation(self):
        """Test request validation"""
        # Username too short
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "ab",
                "password": "testpass123"
            }
        )
        assert response.status_code == 422

        # Password too short
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "12345"
            }
        )
        assert response.status_code == 422
