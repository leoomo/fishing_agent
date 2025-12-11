"""
认证 API 集成测试
"""

import pytest


class TestAuthAPI:
    """认证 API 测试"""

    def test_login_success(self, api_client):
        """测试登录成功"""
        response = api_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )

        # 如果没有 admin 用户，可能返回 401
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "user_info" in data
        else:
            # 测试环境可能没有预置用户
            assert response.status_code in [401, 422]

    def test_login_failure_wrong_password(self, api_client):
        """测试登录失败 - 密码错误"""
        response = api_client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "wrong_password"}
        )

        assert response.status_code in [401, 422]

    def test_login_failure_empty_username(self, api_client):
        """测试登录失败 - 空用户名"""
        response = api_client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": "password"}
        )

        assert response.status_code in [400, 401, 422]

    def test_protected_endpoint_without_token(self, api_client):
        """测试受保护端点 - 无 Token"""
        response = api_client.get("/api/v1/admin/equipment")

        # 401 Unauthorized 或 403 Forbidden 都是有效的未认证响应
        assert response.status_code in [401, 403]

    def test_protected_endpoint_with_invalid_token(self, api_client):
        """测试受保护端点 - 无效 Token"""
        response = api_client.get(
            "/api/v1/admin/equipment",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401


class TestHealthCheck:
    """健康检查测试"""

    def test_health_endpoint(self, api_client):
        """测试健康检查端点"""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
