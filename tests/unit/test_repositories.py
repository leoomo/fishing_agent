"""
Repository 单元测试
"""

import pytest


class TestEquipmentRepository:
    """EquipmentRepository 测试"""

    def test_create_equipment(self, db_session, sample_brand_data, sample_equipment_data):
        """测试创建装备"""
        from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand
        from packages.agent_fishing.tools.lure.models.equipment import Equipment

        equipment_repo = EquipmentRepository(db_session)

        # 创建品牌
        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        # 创建装备
        sample_equipment_data["brand_id"] = brand.brand_id
        equipment = Equipment(**sample_equipment_data)
        created = equipment_repo.create(equipment)
        db_session.commit()

        assert created.equipment_id is not None
        assert created.name == sample_equipment_data["name"]

    def test_search_by_category(self, db_session, sample_brand_data, sample_equipment_data):
        """测试按类别搜索"""
        from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand
        from packages.agent_fishing.tools.lure.models.equipment import Equipment

        equipment_repo = EquipmentRepository(db_session)

        # 准备数据
        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        for i in range(3):
            data = sample_equipment_data.copy()
            data["name"] = f"测试装备{i}"
            data["brand_id"] = brand.brand_id
            equipment = Equipment(**data)
            equipment_repo.create(equipment)

        db_session.commit()

        # 搜索
        results = equipment_repo.search(category="鱼竿", is_active=True)

        assert len(results) == 3
        assert all(eq.category == "鱼竿" for eq in results)

    def test_search_by_price_range(self, db_session, sample_brand_data, sample_equipment_data):
        """测试按价格范围搜索"""
        from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand
        from packages.agent_fishing.tools.lure.models.equipment import Equipment

        equipment_repo = EquipmentRepository(db_session)

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        # 创建不同价格的装备
        prices = [(100, 200), (300, 400), (500, 600)]
        for i, (price_min, price_max) in enumerate(prices):
            data = sample_equipment_data.copy()
            data["name"] = f"装备{i}"
            data["brand_id"] = brand.brand_id
            data["price_min"] = price_min
            data["price_max"] = price_max
            equipment = Equipment(**data)
            equipment_repo.create(equipment)

        db_session.commit()

        # 搜索价格 200-400 的装备
        results = equipment_repo.search(price_min=200, price_max=400, is_active=True)

        assert len(results) >= 1

    def test_search_by_keyword(self, db_session, sample_brand_data, sample_equipment_data):
        """测试关键词搜索"""
        from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand
        from packages.agent_fishing.tools.lure.models.equipment import Equipment

        equipment_repo = EquipmentRepository(db_session)

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        # 创建装备
        data1 = sample_equipment_data.copy()
        data1["name"] = "碳素路亚竿"
        data1["brand_id"] = brand.brand_id
        equipment1 = Equipment(**data1)
        equipment_repo.create(equipment1)

        data2 = sample_equipment_data.copy()
        data2["name"] = "玻璃纤维鱼竿"
        data2["brand_id"] = brand.brand_id
        equipment2 = Equipment(**data2)
        equipment_repo.create(equipment2)

        db_session.commit()

        # 搜索
        results = equipment_repo.search(keyword="碳素", is_active=True)

        assert len(results) == 1
        assert "碳素" in results[0].name

    def test_create_with_specs(self, db_session, sample_brand_data, sample_equipment_data, sample_rod_spec_data):
        """测试创建带规格的装备"""
        from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand

        equipment_repo = EquipmentRepository(db_session)

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        sample_equipment_data["brand_id"] = brand.brand_id
        equipment = equipment_repo.create_with_specs(
            equipment_data=sample_equipment_data,
            spec_data=sample_rod_spec_data
        )
        db_session.commit()
        db_session.refresh(equipment)

        assert equipment.equipment_id is not None
        assert equipment.rod_spec is not None
        assert equipment.rod_spec.length == sample_rod_spec_data["length"]

    def test_get_with_details(self, db_session, sample_brand_data, sample_equipment_data):
        """测试获取装备详情（含关联）"""
        from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand
        from packages.agent_fishing.tools.lure.models.equipment import Equipment

        equipment_repo = EquipmentRepository(db_session)

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        sample_equipment_data["brand_id"] = brand.brand_id
        equipment = Equipment(**sample_equipment_data)
        created = equipment_repo.create(equipment)
        db_session.commit()

        # 获取详情
        result = equipment_repo.get_with_details(created.equipment_id)

        assert result is not None
        assert result.brand is not None
        assert result.brand.name_cn == sample_brand_data["name_cn"]


class TestBrandRepository:
    """BrandRepository 测试"""

    def test_create_brand(self, db_session, sample_brand_data):
        """测试创建品牌"""
        from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand

        repo = BrandRepository(db_session)
        brand = Brand(**sample_brand_data)
        created = repo.create(brand)
        db_session.commit()

        assert created.brand_id is not None
        assert created.name_cn == sample_brand_data["name_cn"]

    def test_get_by_name(self, db_session, sample_brand_data):
        """测试按名称获取品牌"""
        from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand

        repo = BrandRepository(db_session)
        brand = Brand(**sample_brand_data)
        created = repo.create(brand)
        db_session.commit()

        result = repo.get_by_name(sample_brand_data["name_cn"])

        assert result is not None
        assert result.brand_id == created.brand_id

    def test_list_all_brands(self, db_session):
        """测试获取所有品牌"""
        from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository
        from packages.agent_fishing.tools.lure.models.brand import Brand

        repo = BrandRepository(db_session)

        # 创建多个品牌
        for i in range(5):
            brand = Brand(name_cn=f"品牌{i}", country="中国")
            repo.create(brand)

        db_session.commit()

        results = repo.get_all()

        assert len(results) >= 5


class TestUserRepository:
    """UserRepository 测试"""

    def test_create_user(self, db_session, sample_user_data):
        """测试创建用户"""
        from packages.agent_fishing.tools.lure.orm.repositories.user_repo import UserRepository
        from packages.agent_fishing.tools.lure.models.user import User

        repo = UserRepository(db_session)
        user = User(**sample_user_data)
        created = repo.create(user)
        db_session.commit()

        assert created.user_id is not None
        assert created.username == sample_user_data["username"]

    def test_get_user_by_username(self, db_session, sample_user_data):
        """测试按用户名获取用户"""
        from packages.agent_fishing.tools.lure.orm.repositories.user_repo import UserRepository
        from packages.agent_fishing.tools.lure.models.user import User

        repo = UserRepository(db_session)
        user = User(**sample_user_data)
        created = repo.create(user)
        db_session.commit()

        result = repo.get_by_username(sample_user_data["username"])

        assert result is not None
        assert result.user_id == created.user_id


class TestAdminUserRepository:
    """AdminUserRepository 测试"""

    def test_create_admin_user(self, db_session):
        """测试创建管理员"""
        import bcrypt
        from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository

        repo = AdminUserRepository(db_session)
        password_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()

        admin = repo.create_admin_user(
            username="test_admin",
            email="admin@test.com",
            password_hash=password_hash,
            role="admin"
        )
        db_session.commit()

        assert admin.id is not None
        assert admin.username == "test_admin"

    def test_get_admin_by_username(self, db_session):
        """测试按用户名获取管理员"""
        import bcrypt
        from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository

        repo = AdminUserRepository(db_session)
        password_hash = bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode()

        repo.create_admin_user(
            username="find_test_admin",
            email="find@test.com",
            password_hash=password_hash,
            role="editor"
        )
        db_session.commit()

        result = repo.get_by_username("find_test_admin")

        assert result is not None
        assert result.email == "find@test.com"

    def test_password_verification(self, db_session):
        """测试密码验证"""
        import bcrypt
        from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository

        repo = AdminUserRepository(db_session)
        raw_password = "correct_password"
        password_hash = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

        admin = repo.create_admin_user(
            username="auth_test",
            email="auth@test.com",
            password_hash=password_hash,
            role="admin"
        )
        db_session.commit()

        # 验证正确密码
        assert bcrypt.checkpw(raw_password.encode(), admin.password_hash.encode()) is True
        # 验证错误密码
        assert bcrypt.checkpw("wrong_password".encode(), admin.password_hash.encode()) is False

    def test_deactivate_user(self, db_session):
        """测试禁用用户"""
        import bcrypt
        from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository

        repo = AdminUserRepository(db_session)
        password_hash = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()

        admin = repo.create_admin_user(
            username="deactivate_test",
            email="deactivate@test.com",
            password_hash=password_hash,
            role="admin"
        )
        db_session.commit()

        # 禁用用户
        result = repo.deactivate_user(admin.id)
        db_session.commit()

        assert result is True

        # 获取用户验证状态
        updated_admin = repo.get(admin.id)
        assert updated_admin.is_active is False
