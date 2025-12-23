"""
模型单元测试
"""

import pytest
from datetime import datetime


class TestEquipmentModel:
    """Equipment 模型测试"""

    def test_equipment_creation(self, db_session, sample_brand_data, sample_equipment_data):
        """测试装备创建"""
        from apps.api.models.brand import Brand
        from apps.api.models.equipment import Equipment

        # 创建品牌
        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        # 创建装备
        sample_equipment_data["brand_id"] = brand.brand_id
        equipment = Equipment(**sample_equipment_data)
        db_session.add(equipment)
        db_session.commit()
        db_session.refresh(equipment)

        assert equipment.equipment_id is not None
        assert equipment.name == sample_equipment_data["name"]
        assert equipment.category == sample_equipment_data["category"]
        assert equipment.brand_id == brand.brand_id

    def test_equipment_to_dict(self, db_session, sample_brand_data, sample_equipment_data):
        """测试装备 to_dict 方法"""
        from apps.api.models.brand import Brand
        from apps.api.models.equipment import Equipment

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        sample_equipment_data["brand_id"] = brand.brand_id
        equipment = Equipment(**sample_equipment_data)
        db_session.add(equipment)
        db_session.commit()
        db_session.refresh(equipment)

        result = equipment.to_dict(include_brand=False, include_specs=False)

        assert result["equipment_id"] == equipment.equipment_id
        assert result["name"] == equipment.name
        assert result["category"] == equipment.category
        assert "brand" not in result

    def test_equipment_brand_relationship(self, db_session, sample_brand_data, sample_equipment_data):
        """测试装备和品牌的关系"""
        from apps.api.models.brand import Brand
        from apps.api.models.equipment import Equipment

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        sample_equipment_data["brand_id"] = brand.brand_id
        equipment = Equipment(**sample_equipment_data)
        db_session.add(equipment)
        db_session.commit()
        db_session.refresh(equipment)

        # 验证关系
        assert equipment.brand is not None
        assert equipment.brand.name_cn == sample_brand_data["name_cn"]


class TestBrandModel:
    """Brand 模型测试"""

    def test_brand_creation(self, db_session, sample_brand_data):
        """测试品牌创建"""
        from apps.api.models.brand import Brand

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.commit()
        db_session.refresh(brand)

        assert brand.brand_id is not None
        assert brand.name_cn == sample_brand_data["name_cn"]
        assert brand.name_en == sample_brand_data["name_en"]

    def test_brand_to_dict(self, db_session, sample_brand_data):
        """测试品牌 to_dict 方法"""
        from apps.api.models.brand import Brand

        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.commit()

        result = brand.to_dict()

        assert result["name_cn"] == sample_brand_data["name_cn"]
        assert result["country"] == sample_brand_data["country"]


class TestRodSpecModel:
    """RodSpec 模型测试"""

    def test_rod_spec_creation(self, db_session, sample_brand_data, sample_equipment_data, sample_rod_spec_data):
        """测试鱼竿规格创建"""
        from apps.api.models.brand import Brand
        from apps.api.models.equipment import Equipment, RodSpec

        # 创建品牌
        brand = Brand(**sample_brand_data)
        db_session.add(brand)
        db_session.flush()

        # 创建装备
        sample_equipment_data["brand_id"] = brand.brand_id
        equipment = Equipment(**sample_equipment_data)
        db_session.add(equipment)
        db_session.flush()

        # 创建规格
        sample_rod_spec_data["equipment_id"] = equipment.equipment_id
        rod_spec = RodSpec(**sample_rod_spec_data)
        db_session.add(rod_spec)
        db_session.commit()
        db_session.refresh(equipment)

        assert equipment.rod_spec is not None
        assert equipment.rod_spec.length == sample_rod_spec_data["length"]
        assert equipment.rod_spec.power == sample_rod_spec_data["power"]


class TestUserModel:
    """User 模型测试"""

    def test_user_creation(self, db_session, sample_user_data):
        """测试用户创建"""
        from apps.api.models.user import User

        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.user_id is not None
        assert user.username == sample_user_data["username"]
        assert user.experience_level == sample_user_data["experience_level"]


class TestAdminUserModel:
    """AdminUser 模型测试"""

    def test_admin_user_creation(self, db_session):
        """测试管理员用户创建"""
        import bcrypt
        from apps.api.models.admin_user import AdminUser

        # 使用 bcrypt 哈希密码
        password_hash = bcrypt.hashpw("test_password_123".encode(), bcrypt.gensalt()).decode()

        admin = AdminUser(
            username="test_admin",
            email="admin@test.com",
            password_hash=password_hash,
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

        assert admin.id is not None
        assert admin.username == "test_admin"
        assert admin.role == "admin"

    def test_admin_user_password_hash(self, db_session):
        """测试管理员密码哈希验证"""
        import bcrypt
        from apps.api.models.admin_user import AdminUser

        # 使用 bcrypt 哈希密码
        raw_password = "test_password_123"
        password_hash = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

        admin = AdminUser(
            username="test_admin_hash",
            email="admin_hash@test.com",
            password_hash=password_hash,
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()

        # 验证密码 (使用 bcrypt 直接验证)
        assert bcrypt.checkpw(raw_password.encode(), admin.password_hash.encode()) is True
        assert bcrypt.checkpw("wrong_password".encode(), admin.password_hash.encode()) is False

    def test_admin_user_password_not_plain(self, db_session):
        """测试密码不是明文存储"""
        import bcrypt
        from apps.api.models.admin_user import AdminUser

        raw_password = "my_secret_password"
        password_hash = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

        admin = AdminUser(
            username="test_admin2",
            email="admin2@test.com",
            password_hash=password_hash,
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()

        # 密码不应该是明文
        assert admin.password_hash != raw_password
        assert len(admin.password_hash) > 20  # 哈希值应该比明文长
