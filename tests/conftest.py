"""
测试配置和 fixtures
"""

import os
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ["TESTING"] = "true"


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """创建临时测试数据库路径"""
    db_dir = tmp_path_factory.mktemp("data")
    db_path = db_dir / "test_equipment.db"
    os.environ["DB_PATH"] = str(db_path)
    return str(db_path)


@pytest.fixture(scope="function")
def db_session(test_db_path):
    """提供数据库会话 fixture，每个测试使用独立的内存数据库"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from packages.agent_fishing.tools.lure.models.base import Base

    # 创建内存数据库引擎（每个测试独立）
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # 创建所有表
    Base.metadata.create_all(engine)

    # 创建会话
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    try:
        yield session
        session.rollback()  # 回滚而不是提交，确保测试隔离
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def sample_brand_data():
    """示例品牌数据"""
    return {
        "name_cn": "测试品牌",
        "name_en": "Test Brand",
        "country": "中国",
        "tier": "中端",
    }


@pytest.fixture
def sample_equipment_data():
    """示例装备数据"""
    return {
        "name": "测试鱼竿",
        "category": "鱼竿",
        "model": "TEST-001",
        "price_min": 199,
        "price_max": 299,
        "description": "测试用鱼竿",
        "features": "轻量化设计",
        "user_level": "新手",
        "is_active": 1,
        "source": "test",
    }


@pytest.fixture
def sample_rod_spec_data():
    """示例鱼竿规格数据"""
    return {
        "length": 2.1,
        "power": "ML",
        "action": "Fast",
        "lure_weight_min": 2,
        "lure_weight_max": 10,
        "line_weight_min": 4,
        "line_weight_max": 12,
        "sections": 2,
    }


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "phone": "13800138000",
        "experience_level": "新手",
        "fishing_years": 1,
        "preferred_species": "鲈鱼",
        "location": "浙江杭州",
    }


@pytest.fixture
def sample_admin_user_data():
    """示例管理员用户数据"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "is_active": True,
    }


# FastAPI 测试客户端 fixture
@pytest.fixture
def api_client(test_db_path):
    """FastAPI 测试客户端"""
    # 确保数据库初始化
    from packages.agent_fishing.tools.lure.orm.session import init_db, close_db
    close_db()
    init_db(create_tables=True)

    from fastapi.testclient import TestClient
    from apps.api.main import app

    with TestClient(app) as client:
        yield client

    close_db()


@pytest.fixture
def auth_headers(api_client):
    """获取认证 headers"""
    import bcrypt

    # 首先创建管理员用户
    try:
        from packages.agent_fishing.tools.lure.orm.session import get_db_session
        from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository

        with get_db_session() as session:
            repo = AdminUserRepository(session)
            # 检查是否已存在
            existing = repo.get_by_username("admin")
            if not existing:
                # 使用 bcrypt 哈希密码
                password_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
                repo.create_admin_user(
                    username="admin",
                    email="admin@test.com",
                    password_hash=password_hash,
                    role="admin"
                )
    except Exception as e:
        print(f"Error creating admin user: {e}")

    # 尝试登录获取 token
    response = api_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    # 如果登录失败，返回空 headers（用于测试未认证场景）
    return {}
