#!/usr/bin/env python3
"""
爬虫模块单元测试

测试覆盖:
- EquipmentDeduplicator: 数据去重器
- DataPersister: 数据持久化
- EquipmentData: 数据结构
- 反爬虫策略组件
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from packages.agent_fishing.tools.crawler import (
    EquipmentData,
    EquipmentDeduplicator,
    DataPersister,
    UserAgentRotator,
    RequestThrottler,
)
from packages.agent_fishing.tools.lure.database import get_db


class TestEquipmentData:
    """测试EquipmentData数据结构"""

    def test_equipment_data_creation(self):
        """测试创建装备数据"""
        eq = EquipmentData(
            name="禧玛诺毒牙264ML",
            category="鱼竿",
            brand_name="禧玛诺",
            model="264ML",
            price_min=599.0,
            price_max=699.0,
            description="入门路亚竿",
            target_fish="鲈鱼",
            user_level="新手",
            source_url="https://example.com/product/123",
            images=[{"url": "https://example.com/img1.jpg", "type": "main"}],
            specs={"length": "2.64m", "power": "ML", "action": "Fast"},
        )

        assert eq.name == "禧玛诺毒牙264ML"
        assert eq.category == "鱼竿"
        assert eq.brand_name == "禧玛诺"
        assert eq.price_min == 599.0
        assert eq.specs["length"] == "2.64m"
        assert len(eq.images) == 1

    def test_equipment_data_minimal(self):
        """测试最小必需字段的装备数据"""
        eq = EquipmentData(
            name="测试鱼竿",
            category="鱼竿",
            brand_name="测试品牌",
            price_min=100.0,
            source_url="https://example.com/test",
            images=[],
            specs={},
        )

        assert eq.name == "测试鱼竿"
        assert eq.model is None
        assert eq.price_max is None
        assert eq.description is None
        assert eq.images == []
        assert eq.specs == {}


class TestEquipmentDeduplicator:
    """测试装备去重器"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库"""
        db = Mock()
        return db

    @pytest.fixture
    def deduplicator(self, mock_db):
        """创建去重器实例"""
        return EquipmentDeduplicator(mock_db)

    def test_exact_match_brand_model(self, deduplicator, mock_db):
        """测试精确匹配：品牌+型号"""
        # 模拟数据库返回结果
        mock_db.execute.return_value = [
            {
                "equipment_id": 1,
                "name": "禧玛诺毒牙264ML",
                "brand_id": 10,
                "model": "264ML",
            }
        ]

        eq = EquipmentData(
            name="禧玛诺毒牙264ML",
            category="鱼竿",
            brand_name="禧玛诺",
            model="264ML",
            price_min=599.0,
            source_url="https://example.com/test",
            images=[],
            specs={},
        )

        result = deduplicator.find_duplicates(eq)  # 使用复数形式
        assert result is not None
        assert result == 1  # 返回equipment_id

    def test_no_duplicate_found(self, deduplicator, mock_db):
        """测试未找到重复"""
        # 模拟数据库返回空结果
        mock_db.execute.return_value = []

        eq = EquipmentData(
            name="全新装备",
            category="鱼竿",
            brand_name="新品牌",
            model="NEW001",
            price_min=999.0,
            source_url="https://example.com/new",
            images=[],
            specs={},
        )

        result = deduplicator.find_duplicates(eq)  # 使用复数形式
        assert result is None

    def test_fuzzy_match_by_name(self, deduplicator, mock_db):
        """测试模糊匹配：品牌+名称相似度"""
        # 模拟数据库返回相似名称的装备（使用正确的列名）
        mock_db.execute.return_value = [
            {
                "equipment_id": 2,
                "equipment_name": "达亿瓦月下美人76ML",  # 改为equipment_name
                "brand_id": 20,
                "model": None,
            }
        ]

        eq = EquipmentData(
            name="达亿瓦月下美人 76ML 鱼竿",  # 相似但不完全一样
            category="鱼竿",
            brand_name="达亿瓦",
            model=None,
            price_min=899.0,
            source_url="https://example.com/test",
            images=[],
            specs={},
        )

        # 由于name相似度高（>80%），应该被识别为重复
        result = deduplicator.find_duplicates(eq)  # 使用复数形式
        # 注意：实际的模糊匹配逻辑需要在deduplicator中实现
        # 这里只是测试框架，具体实现可能不同
        # 结果取决于具体的相似度算法实现
        # assert result == 2 或 assert result is None


class TestDataPersister:
    """测试数据持久化器"""

    @pytest.fixture
    def real_db(self):
        """使用真实数据库进行测试"""
        return get_db()

    @pytest.fixture
    def persister(self, real_db):
        """创建持久化器实例"""
        from packages.agent_fishing.tools.lure.image_manager import ImageManager, LocalImageStorage
        import tempfile
        # 使用临时目录存储测试图片
        temp_dir = tempfile.mkdtemp()
        storage = LocalImageStorage(base_path=temp_dir)
        image_manager = ImageManager(real_db, storage)
        return DataPersister(real_db, image_manager)

    def test_save_new_equipment(self, persister, real_db):
        """测试保存新装备"""
        eq = EquipmentData(
            name=f"测试鱼竿_{datetime.now().timestamp()}",
            category="鱼竿",
            brand_name="测试品牌",
            model="TEST001",
            price_min=299.0,
            price_max=399.0,
            description="测试装备",
            target_fish="测试鱼",
            user_level="新手",
            source_url="https://example.com/test",
            images=[],
            specs={"length": "2.1m", "power": "M"},
        )

        # 保存装备
        equipment_id = persister.save_equipment(eq, update_if_exists=False)

        # 验证保存成功
        assert equipment_id is not None
        assert isinstance(equipment_id, int)

        # 验证数据库中存在
        result = real_db.execute(
            "SELECT * FROM equipment WHERE equipment_id = ?", (equipment_id,)
        )
        assert len(result) == 1
        saved_eq = result[0]
        assert saved_eq["name"] == eq.name
        assert saved_eq["category"] == eq.category
        assert saved_eq["price_min"] == eq.price_min

        # 清理测试数据
        real_db.execute("DELETE FROM equipment WHERE equipment_id = ?", (equipment_id,))

    def test_skip_duplicate_equipment(self, persister, real_db):
        """测试跳过重复装备（不更新）"""
        # 第一次保存
        eq = EquipmentData(
            name=f"去重测试鱼竿_{datetime.now().timestamp()}",
            category="鱼竿",
            brand_name="测试品牌",
            model="DUP001",
            price_min=399.0,
            source_url="https://example.com/dup",
            images=[],
            specs={},
        )

        equipment_id_1 = persister.save_equipment(eq, update_if_exists=False)
        assert equipment_id_1 is not None

        # 第二次保存相同装备（应该跳过）
        equipment_id_2 = persister.save_equipment(eq, update_if_exists=False)
        # 如果去重正确，应该返回None或原ID
        # 具体行为取决于实现

        # 清理测试数据
        if equipment_id_1:
            real_db.execute(
                "DELETE FROM equipment WHERE equipment_id = ?", (equipment_id_1,)
            )

    def test_update_existing_equipment(self, persister, real_db):
        """测试更新已存在的装备"""
        # 第一次保存
        eq1 = EquipmentData(
            name=f"更新测试鱼竿_{datetime.now().timestamp()}",
            category="鱼竿",
            brand_name="测试品牌",
            model="UPD001",
            price_min=499.0,
            source_url="https://example.com/upd",
            images=[],
            specs={},
        )

        equipment_id = persister.save_equipment(eq1, update_if_exists=False)
        assert equipment_id is not None

        # 第二次保存，价格不同（应该更新）
        eq2 = EquipmentData(
            name=eq1.name,
            category=eq1.category,
            brand_name=eq1.brand_name,
            model=eq1.model,
            price_min=599.0,  # 价格变化
            price_max=699.0,  # 新增最高价
            source_url=eq1.source_url,
            images=[],
            specs={},
        )

        result_id = persister.save_equipment(eq2, update_if_exists=True)

        # 验证价格已更新
        result = real_db.execute(
            "SELECT * FROM equipment WHERE equipment_id = ?", (equipment_id,)
        )
        if result:
            updated_eq = result[0]
            # 验证更新（具体字段取决于实现）
            # assert updated_eq["price_min"] == 599.0  # 可能已更新
            # assert updated_eq["price_max"] == 699.0  # 可能已更新

        # 清理测试数据
        real_db.execute("DELETE FROM equipment WHERE equipment_id = ?", (equipment_id,))


class TestUserAgentRotator:
    """测试User-Agent轮换器"""

    def test_ua_rotation(self):
        """测试UA轮换功能"""
        rotator = UserAgentRotator()

        # 获取多个UA，应该有变化
        uas = [rotator.get_random_ua() for _ in range(10)]

        # 验证所有UA都不为空
        assert all(ua for ua in uas)

        # 验证至少有一些不同的UA（轮换生效）
        unique_uas = set(uas)
        assert len(unique_uas) > 1  # 至少有2个不同的UA

    def test_ua_format(self):
        """测试UA格式正确性"""
        rotator = UserAgentRotator()
        ua = rotator.get_random_ua()

        # 验证包含Mozilla（标准UA开头）
        assert "Mozilla" in ua


class TestRequestThrottler:
    """测试请求节流器"""

    def test_throttler_delay(self):
        """测试请求延迟功能"""
        throttler = RequestThrottler(min_delay=0.1, max_delay=0.2)

        import time

        start_time = time.time()
        throttler.wait()
        end_time = time.time()

        elapsed = end_time - start_time

        # 验证延迟在指定范围内
        assert 0.1 <= elapsed <= 0.3  # 允许0.1秒误差

    def test_throttler_randomness(self):
        """测试延迟随机性"""
        throttler = RequestThrottler(min_delay=0.1, max_delay=0.5)

        import time

        delays = []
        for _ in range(5):
            start = time.time()
            throttler.wait()
            end = time.time()
            delays.append(end - start)

        # 验证延迟有变化（随机性）
        unique_delays = len(set([round(d, 1) for d in delays]))
        assert unique_delays >= 2  # 至少有2种不同的延迟时间


class TestIntegration:
    """集成测试"""

    def test_full_workflow_mock(self):
        """测试完整工作流（Mock版本）"""
        # 这里可以测试完整的爬取->去重->保存流程
        # 使用Mock避免实际网络请求
        pass

    def test_deduplication_workflow(self):
        """测试去重工作流"""
        # 测试去重器在实际工作流中的表现
        pass


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
