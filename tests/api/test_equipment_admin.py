"""
装备管理 API 集成测试
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


# ========== Fixtures ==========

@pytest.fixture
def admin_token():
    """获取管理员 token（需要先创建admin用户）"""
    # 注意：这需要先运行 scripts/create_admin.py 创建管理员用户
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        pytest.skip("需要先创建admin用户: uv run python scripts/create_admin.py")


@pytest.fixture
def test_brand_id(admin_token):
    """创建测试品牌"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 尝试创建品牌
    response = client.post(
        "/api/v1/admin/brands",
        headers=headers,
        json={
            "name_cn": "测试品牌",
            "name_en": "Test Brand",
            "country": "中国",
            "description": "测试用品牌"
        }
    )

    # 如果品牌已存在，获取现有品牌
    if response.status_code == 400:
        # 品牌已存在，查询品牌列表获取ID
        response = client.get("/api/v1/admin/brands", headers=headers)
        brands = response.json()
        for brand in brands:
            if brand["name_cn"] == "测试品牌":
                return brand["brand_id"]

    return response.json()["brand_id"]


# ========== 品牌管理测试 ==========

def test_create_brand(admin_token):
    """测试创建品牌"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    brand_data = {
        "name_cn": f"新品牌_{pytest.timestamp()}",
        "name_en": "New Brand",
        "country": "日本",
        "description": "高端钓具品牌"
    }

    response = client.post(
        "/api/v1/admin/brands",
        headers=headers,
        json=brand_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name_cn"] == brand_data["name_cn"]
    assert "brand_id" in data


def test_list_brands(admin_token):
    """测试查询品牌列表"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/brands?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_brand_with_equipment_count(admin_token, test_brand_id):
    """测试获取品牌详情（含装备数量）"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        f"/api/v1/admin/brands/{test_brand_id}?with_equipment_count=true",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "equipment_count" in data


# ========== 装备管理测试 ==========

def test_create_equipment(admin_token, test_brand_id):
    """测试创建装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    equipment_data = {
        "name": "测试鱼竿",
        "category": "鱼竿",
        "brand_id": test_brand_id,
        "model": "TEST-001",
        "price_min": 199,
        "price_max": 299,
        "description": "测试描述",
        "user_level": "新手",
        "specs": {
            "length": 2.1,
            "power": "ML",
            "action": "Fast",
            "lure_weight_min": 2,
            "lure_weight_max": 10
        }
    }

    response = client.post(
        "/api/v1/admin/equipment",
        headers=headers,
        json=equipment_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试鱼竿"
    assert data["category"] == "鱼竿"
    assert "equipment_id" in data
    assert data["specs"] is not None


def test_list_equipment(admin_token):
    """测试查询装备列表"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/equipment?page=1&page_size=10&category=鱼竿",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_equipment(admin_token, test_brand_id):
    """测试获取装备详情"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 先创建装备
    equipment_data = {
        "name": "详情测试鱼竿",
        "category": "鱼竿",
        "brand_id": test_brand_id,
        "model": "DETAIL-001",
        "price_min": 299,
        "price_max": 399,
        "user_level": "进阶",
        "specs": {
            "length": 2.4,
            "power": "M",
            "action": "Medium",
            "lure_weight_min": 5,
            "lure_weight_max": 15
        }
    }

    create_response = client.post(
        "/api/v1/admin/equipment",
        headers=headers,
        json=equipment_data
    )

    equipment_id = create_response.json()["equipment_id"]

    # 获取详情
    response = client.get(
        f"/api/v1/admin/equipment/{equipment_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["equipment_id"] == equipment_id
    assert "specs" in data  # 详情包含规格


def test_update_equipment(admin_token, test_brand_id):
    """测试更新装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 先创建装备
    equipment_data = {
        "name": "更新测试鱼竿",
        "category": "鱼竿",
        "brand_id": test_brand_id,
        "model": "UPDATE-001",
        "price_min": 199,
        "price_max": 299,
        "user_level": "新手"
    }

    create_response = client.post(
        "/api/v1/admin/equipment",
        headers=headers,
        json=equipment_data
    )

    equipment_id = create_response.json()["equipment_id"]

    # 更新装备
    update_data = {
        "price_min": 249,
        "price_max": 349,
        "description": "更新后的描述"
    }

    response = client.put(
        f"/api/v1/admin/equipment/{equipment_id}",
        headers=headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["price_min"] == 249
    assert data["description"] == "更新后的描述"


def test_delete_equipment(admin_token, test_brand_id):
    """测试删除装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 先创建装备
    equipment_data = {
        "name": "删除测试鱼竿",
        "category": "鱼竿",
        "brand_id": test_brand_id,
        "model": "DELETE-001",
        "price_min": 199,
        "price_max": 299,
        "user_level": "新手"
    }

    create_response = client.post(
        "/api/v1/admin/equipment",
        headers=headers,
        json=equipment_data
    )

    equipment_id = create_response.json()["equipment_id"]

    # 删除装备
    response = client.delete(
        f"/api/v1/admin/equipment/{equipment_id}",
        headers=headers
    )

    assert response.status_code == 204

    # 验证已软删除（is_active=False）
    response = client.get(
        f"/api/v1/admin/equipment/{equipment_id}",
        headers=headers
    )
    assert response.json()["is_active"] is False


# ========== 权限测试 ==========

def test_unauthorized_access():
    """测试未授权访问"""
    # 不提供 token
    response = client.get("/api/v1/admin/equipment")

    assert response.status_code == 401


def test_invalid_token():
    """测试无效 token"""
    headers = {"Authorization": "Bearer invalid_token"}

    response = client.get(
        "/api/v1/admin/equipment",
        headers=headers
    )

    assert response.status_code == 401


# ========== 导入导出测试 ==========

def test_export_csv(admin_token):
    """测试CSV导出"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/import-export/export/csv?category=鱼竿&limit=10",
        headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_export_json(admin_token):
    """测试JSON导出"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/import-export/export/json?category=鱼竿&limit=10",
        headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


# ========== 用户管理测试 ==========

def test_list_users(admin_token):
    """测试查询用户列表"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/users?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "users" in data


# ========== Pytest配置 ==========

@pytest.fixture(scope="session", autouse=True)
def add_timestamp_to_pytest():
    """为pytest添加时间戳属性"""
    import time
    pytest.timestamp = lambda: str(int(time.time() * 1000))
