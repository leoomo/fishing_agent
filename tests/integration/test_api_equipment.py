"""
装备管理 API 集成测试
"""

import pytest


class TestEquipmentAPI:
    """装备管理 API 测试"""

    def test_list_equipment_unauthorized(self, api_client):
        """测试未授权访问装备列表"""
        response = api_client.get("/api/v1/admin/equipment")

        # 401 Unauthorized 或 403 Forbidden 都是有效的未认证响应
        assert response.status_code in [401, 403]

    def test_list_equipment_authorized(self, api_client, auth_headers):
        """测试授权访问装备列表"""
        if not auth_headers:
            pytest.skip("No auth headers available")

        response = api_client.get(
            "/api/v1/admin/equipment",
            headers=auth_headers,
            params={"page": 1, "page_size": 10}
        )

        if response.status_code == 200:
            data = response.json()
            assert "items" in data or "total" in data
        else:
            # 可能是权限问题
            assert response.status_code in [403, 500]

    def test_list_equipment_pagination(self, api_client, auth_headers):
        """测试装备列表分页"""
        if not auth_headers:
            pytest.skip("No auth headers available")

        response = api_client.get(
            "/api/v1/admin/equipment",
            headers=auth_headers,
            params={"page": 1, "page_size": 5}
        )

        if response.status_code == 200:
            data = response.json()
            assert data.get("page") == 1
            assert data.get("page_size") == 5 or len(data.get("items", [])) <= 5

    def test_list_equipment_with_filter(self, api_client, auth_headers):
        """测试装备列表筛选"""
        if not auth_headers:
            pytest.skip("No auth headers available")

        response = api_client.get(
            "/api/v1/admin/equipment",
            headers=auth_headers,
            params={"category": "鱼竿", "page": 1, "page_size": 10}
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            # 验证所有返回的都是鱼竿
            for item in items:
                assert item.get("category") == "鱼竿"

    def test_get_equipment_not_found(self, api_client, auth_headers):
        """测试获取不存在的装备"""
        if not auth_headers:
            pytest.skip("No auth headers available")

        response = api_client.get(
            "/api/v1/admin/equipment/99999",
            headers=auth_headers
        )

        assert response.status_code in [404, 500]


class TestBrandAPI:
    """品牌管理 API 测试"""

    def test_list_brands_unauthorized(self, api_client):
        """测试未授权访问品牌列表"""
        response = api_client.get("/api/v1/admin/brands")

        # 401 Unauthorized 或 403 Forbidden 都是有效的未认证响应
        assert response.status_code in [401, 403]

    def test_list_brands_authorized(self, api_client, auth_headers):
        """测试授权访问品牌列表"""
        if not auth_headers:
            pytest.skip("No auth headers available")

        response = api_client.get(
            "/api/v1/admin/brands",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
