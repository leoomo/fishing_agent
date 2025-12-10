"""
爬虫和监控 API 集成测试
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


# ========== 爬虫管理测试 ==========

def test_list_crawler_tasks(admin_token):
    """测试查询爬虫任务列表"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/crawler/tasks?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "tasks" in data
    assert isinstance(data["tasks"], list)


def test_trigger_crawler_task(admin_token):
    """测试触发爬虫任务"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    task_data = {
        "task_type": "taobao",
        "keywords": ["测试关键词"],
        "max_pages": 3,
        "proxy": None
    }

    response = client.post(
        "/api/v1/admin/crawler/tasks/trigger",
        headers=headers,
        json=task_data
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["task_type"] == "taobao"
    assert data["status"] in ["pending", "running"]
    return data["id"]  # 返回task_id供其他测试使用


def test_get_crawler_task(admin_token):
    """测试获取爬虫任务详情"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 先创建一个任务
    task_data = {
        "task_type": "jd",
        "keywords": ["路亚竿"],
        "max_pages": 2
    }

    create_response = client.post(
        "/api/v1/admin/crawler/tasks/trigger",
        headers=headers,
        json=task_data
    )

    task_id = create_response.json()["id"]

    # 获取详情
    response = client.get(
        f"/api/v1/admin/crawler/tasks/{task_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["task_type"] == "jd"


def test_get_task_logs(admin_token):
    """测试获取任务日志"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 先创建一个任务
    task_data = {
        "task_type": "forum",
        "keywords": ["钓鱼"],
        "max_pages": 1
    }

    create_response = client.post(
        "/api/v1/admin/crawler/tasks/trigger",
        headers=headers,
        json=task_data
    )

    task_id = create_response.json()["id"]

    # 获取日志
    response = client.get(
        f"/api/v1/admin/crawler/tasks/{task_id}/logs",
        headers=headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_sync_status(admin_token):
    """测试获取数据同步状态"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/crawler/sync-status",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_synced" in data
    assert "pending_sync" in data
    assert "sync_errors" in data


def test_retry_task_invalid_status(admin_token):
    """测试重试非失败任务（应该失败）"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 创建一个pending任务
    task_data = {
        "task_type": "taobao",
        "keywords": ["测试"],
        "max_pages": 1
    }

    create_response = client.post(
        "/api/v1/admin/crawler/tasks/trigger",
        headers=headers,
        json=task_data
    )

    task_id = create_response.json()["id"]

    # 尝试重试（应该失败，因为状态不是failed）
    response = client.post(
        f"/api/v1/admin/crawler/tasks/{task_id}/retry",
        headers=headers
    )

    # 期望返回400，因为只能重试失败任务
    assert response.status_code == 400
    assert "只能重试失败任务" in response.json()["detail"]


# ========== 监控统计测试 ==========

def test_get_api_stats(admin_token):
    """测试获取API统计"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/monitor/api-stats",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "avg_response_time" in data
    assert "error_rate" in data
    assert "top_endpoints" in data
    assert isinstance(data["top_endpoints"], list)


def test_get_llm_stats(admin_token):
    """测试获取LLM统计"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/monitor/llm-stats",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data
    assert "total_tokens" in data
    assert "total_cost" in data
    assert "avg_response_time" in data
    assert "success_rate" in data
    assert "by_provider" in data
    assert isinstance(data["by_provider"], dict)


def test_get_db_performance(admin_token):
    """测试获取数据库性能指标"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/monitor/db-performance",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "avg_query_time" in data
    assert "slow_queries_count" in data
    assert "connection_pool_size" in data
    assert "active_connections" in data
    assert "table_sizes" in data


def test_health_check_no_auth():
    """测试健康检查（无需认证）"""
    response = client.get("/api/v1/admin/monitor/health-check")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "api_status" in data
    assert "db_status" in data
    assert "llm_status" in data
    assert "uptime_seconds" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


# ========== 权限测试 ==========

def test_crawler_unauthorized_access():
    """测试未授权访问爬虫端点"""
    # 不提供 token
    response = client.get("/api/v1/admin/crawler/tasks")

    assert response.status_code == 401


def test_monitor_unauthorized_access():
    """测试未授权访问监控端点"""
    # 不提供 token
    response = client.get("/api/v1/admin/monitor/api-stats")

    assert response.status_code == 401


def test_invalid_token_crawler():
    """测试无效 token 访问爬虫端点"""
    headers = {"Authorization": "Bearer invalid_token"}

    response = client.get(
        "/api/v1/admin/crawler/tasks",
        headers=headers
    )

    assert response.status_code == 401


def test_invalid_token_monitor():
    """测试无效 token 访问监控端点"""
    headers = {"Authorization": "Bearer invalid_token"}

    response = client.get(
        "/api/v1/admin/monitor/api-stats",
        headers=headers
    )

    assert response.status_code == 401


# ========== 边界测试 ==========

def test_get_nonexistent_task(admin_token):
    """测试获取不存在的任务"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/crawler/tasks/999999",
        headers=headers
    )

    assert response.status_code == 404


def test_delete_nonexistent_task(admin_token):
    """测试删除不存在的任务"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.delete(
        "/api/v1/admin/crawler/tasks/999999",
        headers=headers
    )

    assert response.status_code == 404


def test_trigger_crawler_invalid_type(admin_token):
    """测试触发无效类型的爬虫任务"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    task_data = {
        "task_type": "invalid_type",  # 无效类型
        "keywords": ["测试"],
        "max_pages": 1
    }

    response = client.post(
        "/api/v1/admin/crawler/tasks/trigger",
        headers=headers,
        json=task_data
    )

    assert response.status_code == 422  # Validation error


def test_api_stats_with_date_range(admin_token):
    """测试带日期范围的API统计"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/monitor/api-stats?start_date=2025-12-01&end_date=2025-12-10",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data


def test_llm_stats_with_date_range(admin_token):
    """测试带日期范围的LLM统计"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/monitor/llm-stats?start_date=2025-12-01&end_date=2025-12-10",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_calls" in data


# ========== Pytest配置 ==========

@pytest.fixture(scope="session", autouse=True)
def add_timestamp_to_pytest():
    """为pytest添加时间戳属性"""
    import time
    pytest.timestamp = lambda: str(int(time.time() * 1000))
