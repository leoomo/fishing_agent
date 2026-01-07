"""
EquipmentSearcher 全面测试

测试重构后的 EquipmentSearcher，验证其通过 EquipmentRepository 进行查询的功能。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from apps.api.models.base import Base
from apps.api.models import Equipment, Brand, RodSpec, ReelSpec, LineSpec, LureSpec
from packages.agents.fishing.tools.lure.equipment_searcher import (
    EquipmentSearcher,
    get_equipment_searcher,
)


# === Fixtures ===


@pytest.fixture(scope="function")
def db_engine():
    """创建内存数据库"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """创建测试会话"""
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_brand(db_session: Session):
    """创建测试品牌"""
    brand = Brand(
        name_cn="禧玛诺",
        name_en="Shimano",
        country="日本",
        is_active=True
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def sample_brand_2(db_session: Session):
    """创建第二个测试品牌"""
    brand = Brand(
        name_cn="达瓦",
        name_en="Daiwa",
        country="日本",
        is_active=True
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def sample_rod(db_session: Session, sample_brand: Brand):
    """创建测试鱼竿"""
    equipment = Equipment(
        name="禧玛诺毒牙264ML",
        category="鱼竿",
        brand_id=sample_brand.brand_id,
        model="264ML",
        price_min=800.0,
        price_max=1000.0,
        user_level="进阶",
        is_active=True
    )
    db_session.add(equipment)
    db_session.flush()

    rod_spec = RodSpec(
        equipment_id=equipment.equipment_id,
        length=1.98,
        sections=2,
        power="ML",
        action="Fast",
        lure_weight_min=5.0,
        lure_weight_max=18.0
    )
    db_session.add(rod_spec)
    db_session.commit()
    db_session.refresh(equipment)
    return equipment


@pytest.fixture
def sample_rod_2(db_session: Session, sample_brand_2: Brand):
    """创建第二个测试鱼竿"""
    equipment = Equipment(
        name="达瓦黑钢702M",
        category="鱼竿",
        brand_id=sample_brand_2.brand_id,
        model="702M",
        price_min=600.0,
        price_max=800.0,
        user_level="新手",
        is_active=True
    )
    db_session.add(equipment)
    db_session.flush()

    rod_spec = RodSpec(
        equipment_id=equipment.equipment_id,
        length=2.1,
        sections=2,
        power="M",
        action="Fast",
        lure_weight_min=7.0,
        lure_weight_max=28.0
    )
    db_session.add(rod_spec)
    db_session.commit()
    db_session.refresh(equipment)
    return equipment


@pytest.fixture
def sample_reel(db_session: Session, sample_brand: Brand):
    """创建测试渔轮"""
    equipment = Equipment(
        name="禧玛诺斯提拉2500",
        category="渔轮",
        brand_id=sample_brand.brand_id,
        model="2500",
        price_min=1500.0,
        price_max=2000.0,
        user_level="进阶",
        is_active=True
    )
    db_session.add(equipment)
    db_session.flush()

    reel_spec = ReelSpec(
        equipment_id=equipment.equipment_id,
        reel_type="spinning",
        gear_ratio="6.2:1",
        max_drag=5.0,
        weight=205,
        bearings=7
    )
    db_session.add(reel_spec)
    db_session.commit()
    db_session.refresh(equipment)
    return equipment


@pytest.fixture
def sample_line(db_session: Session, sample_brand_2: Brand):
    """创建测试鱼线"""
    equipment = Equipment(
        name="达瓦PE线1.0号",
        category="鱼线",
        brand_id=sample_brand_2.brand_id,
        model="PE1.0",
        price_min=100.0,
        price_max=150.0,
        user_level="新手",
        is_active=True
    )
    db_session.add(equipment)
    db_session.flush()

    line_spec = LineSpec(
        equipment_id=equipment.equipment_id,
        line_type="PE",
        diameter=0.16,
        strength_lb=20.0,
        length_m=150
    )
    db_session.add(line_spec)
    db_session.commit()
    db_session.refresh(equipment)
    return equipment


@pytest.fixture
def sample_lure(db_session: Session, sample_brand: Brand):
    """创建测试拟饵"""
    equipment = Equipment(
        name="禧玛诺米诺110F",
        category="拟饵",
        brand_id=sample_brand.brand_id,
        model="110F",
        price_min=80.0,
        price_max=120.0,
        user_level="进阶",
        is_active=True
    )
    db_session.add(equipment)
    db_session.flush()

    lure_spec = LureSpec(
        equipment_id=equipment.equipment_id,
        lure_category="硬饵",
        lure_type="米诺",
        weight=14.0,
        length=11.0,
        diving_depth_min=0.5,
        diving_depth_max=1.5
    )
    db_session.add(lure_spec)
    db_session.commit()
    db_session.refresh(equipment)
    return equipment


@pytest.fixture
def multiple_equipments(db_session: Session, sample_rod, sample_rod_2, sample_reel, sample_line, sample_lure):
    """创建多种装备用于综合测试"""
    return [sample_rod, sample_rod_2, sample_reel, sample_line, sample_lure]


# === 初始化测试 ===


class TestEquipmentSearcherInit:
    """初始化测试"""

    def test_init_with_session(self, db_session: Session):
        """使用提供的 session 初始化"""
        searcher = EquipmentSearcher(session=db_session)

        assert searcher.session is db_session
        assert searcher._owns_session is False
        assert searcher.repo is not None

    def test_init_creates_repo(self, db_session: Session):
        """验证 Repository 被正确创建"""
        searcher = EquipmentSearcher(session=db_session)

        from apps.api.orm.repositories import EquipmentRepository
        assert isinstance(searcher.repo, EquipmentRepository)


# === 名称搜索测试 ===


class TestEquipmentSearcherNameSearch:
    """名称搜索测试"""

    def test_search_by_name_exact_match(self, db_session: Session, sample_rod: Equipment):
        """精确匹配优先返回"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_name("禧玛诺毒牙264ML")

        assert result is not None
        assert result['name'] == "禧玛诺毒牙264ML"
        assert result['id'] == sample_rod.equipment_id

    def test_search_by_name_exact_match_model(self, db_session: Session, sample_rod: Equipment):
        """精确匹配型号"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_name("264ML")

        assert result is not None
        assert result['model'] == "264ML"

    def test_search_by_name_fuzzy_fallback(self, db_session: Session, sample_rod: Equipment):
        """精确失败时回退模糊匹配"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_name("毒牙")

        assert result is not None
        assert "毒牙" in result['name']

    def test_search_by_name_with_category(self, db_session: Session, sample_rod: Equipment):
        """带类别过滤的搜索"""
        searcher = EquipmentSearcher(session=db_session)

        # 正确类别
        result = searcher.search_by_name("毒牙", category="鱼竿")
        assert result is not None

        # 错误类别
        result = searcher.search_by_name("毒牙", category="渔轮")
        assert result is None

    def test_search_by_name_no_match(self, db_session: Session, sample_rod: Equipment):
        """无匹配返回 None"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_name("完全不存在的装备xyz")

        assert result is None

    def test_search_by_name_similarity_ranking(
        self, db_session: Session, sample_rod: Equipment, sample_rod_2: Equipment
    ):
        """模糊结果按相似度排序，返回最佳匹配"""
        searcher = EquipmentSearcher(session=db_session)

        # 搜索"禧玛诺"应返回禧玛诺品牌的装备
        result = searcher.search_by_name("禧玛诺")
        assert result is not None
        assert "禧玛诺" in result['name']


# === ID 搜索测试 ===


class TestEquipmentSearcherIdSearch:
    """ID 搜索测试"""

    def test_search_by_id_found(self, db_session: Session, sample_rod: Equipment):
        """存在的 ID 返回装备"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_id(sample_rod.equipment_id)

        assert result is not None
        assert result['id'] == sample_rod.equipment_id
        assert result['name'] == "禧玛诺毒牙264ML"

    def test_search_by_id_not_found(self, db_session: Session):
        """不存在的 ID 返回 None"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_id(99999)

        assert result is None

    def test_search_by_id_includes_specs(self, db_session: Session, sample_rod: Equipment):
        """ID 搜索包含规格信息"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_id(sample_rod.equipment_id)

        assert result is not None
        assert 'specs' in result
        assert result['specs']['power'] == "ML"
        assert result['specs']['length'] == 1.98

    def test_search_by_ids_batch(self, db_session: Session, sample_rod: Equipment, sample_rod_2: Equipment):
        """批量 ID 查询"""
        searcher = EquipmentSearcher(session=db_session)
        ids = [sample_rod.equipment_id, sample_rod_2.equipment_id]
        results = searcher.search_by_ids(ids)

        assert len(results) == 2

    def test_search_by_ids_order_preserved(self, db_session: Session, sample_rod: Equipment, sample_rod_2: Equipment):
        """批量查询保持顺序"""
        searcher = EquipmentSearcher(session=db_session)

        # 以特定顺序查询
        ids = [sample_rod_2.equipment_id, sample_rod.equipment_id]
        results = searcher.search_by_ids(ids)

        assert len(results) == 2
        assert results[0]['id'] == sample_rod_2.equipment_id
        assert results[1]['id'] == sample_rod.equipment_id

    def test_search_by_ids_empty_list(self, db_session: Session):
        """空列表返回空列表"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_by_ids([])

        assert results == []

    def test_search_by_ids_partial_missing(self, db_session: Session, sample_rod: Equipment):
        """部分 ID 不存在时正确处理"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_by_ids([sample_rod.equipment_id, 99999])

        assert len(results) == 1
        assert results[0]['id'] == sample_rod.equipment_id


# === 批量名称搜索测试 ===


class TestEquipmentSearcherMultiple:
    """批量名称搜索测试"""

    def test_search_multiple_all_found(self, db_session: Session, sample_rod: Equipment, sample_rod_2: Equipment):
        """全部找到"""
        searcher = EquipmentSearcher(session=db_session)
        names = ["禧玛诺毒牙264ML", "达瓦黑钢702M"]
        results = searcher.search_multiple(names)

        assert len(results) == 2

    def test_search_multiple_partial_found(self, db_session: Session, sample_rod: Equipment):
        """部分找到"""
        searcher = EquipmentSearcher(session=db_session)
        names = ["禧玛诺毒牙264ML", "不存在的装备"]
        results = searcher.search_multiple(names)

        assert len(results) == 1
        assert results[0]['name'] == "禧玛诺毒牙264ML"

    def test_search_multiple_empty_list(self, db_session: Session):
        """空列表返回空列表"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_multiple([])

        assert results == []

    def test_search_multiple_with_category(self, db_session: Session, sample_rod: Equipment, sample_reel: Equipment):
        """带类别过滤的批量搜索"""
        searcher = EquipmentSearcher(session=db_session)
        names = ["禧玛诺毒牙264ML", "禧玛诺斯提拉2500"]

        # 只搜索鱼竿
        results = searcher.search_multiple(names, category="鱼竿")
        assert len(results) == 1
        assert results[0]['category'] == "鱼竿"


# === 高级搜索测试 ===


class TestEquipmentSearcherAdvanced:
    """高级搜索测试"""

    def test_search_by_category(self, db_session: Session, multiple_equipments):
        """按类别搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search(category="鱼竿")

        assert len(results) == 2
        assert all(r['category'] == "鱼竿" for r in results)

    def test_search_by_price_range(self, db_session: Session, multiple_equipments):
        """按价格范围搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search(price_min=500.0, price_max=1000.0)

        assert len(results) >= 1
        for r in results:
            assert r['price_min'] >= 500.0 or r['price_max'] <= 1000.0

    def test_search_by_keyword(self, db_session: Session, multiple_equipments):
        """按关键词搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search(keyword="禧玛诺")

        assert len(results) >= 1
        for r in results:
            assert "禧玛诺" in r['name']

    def test_search_with_limit(self, db_session: Session, multiple_equipments):
        """搜索限制数量"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search(limit=2)

        assert len(results) <= 2

    def test_search_rods_by_power(self, db_session: Session, sample_rod: Equipment, sample_rod_2: Equipment):
        """鱼竿硬度搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_rods(power="ML")

        assert len(results) >= 1
        for r in results:
            assert r['specs']['power'] == "ML"

    def test_search_rods_by_length_range(self, db_session: Session, sample_rod: Equipment, sample_rod_2: Equipment):
        """鱼竿长度范围搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_rods(length_min=2.0, length_max=2.5)

        assert len(results) >= 1
        for r in results:
            assert 2.0 <= r['specs']['length'] <= 2.5

    def test_search_reels_by_type(self, db_session: Session, sample_reel: Equipment):
        """渔轮类型搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_reels(reel_type="spinning")

        assert len(results) >= 1
        for r in results:
            assert r['specs']['reel_type'] == "spinning"

    def test_search_reels_by_drag_range(self, db_session: Session, sample_reel: Equipment):
        """渔轮拽力范围搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_reels(max_drag_min=4.0, max_drag_max=6.0)

        assert len(results) >= 1

    def test_search_lines_by_type(self, db_session: Session, sample_line: Equipment):
        """鱼线类型搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_lines(line_type="PE")

        assert len(results) >= 1
        for r in results:
            assert r['specs']['line_type'] == "PE"

    def test_search_lines_by_diameter_range(self, db_session: Session, sample_line: Equipment):
        """鱼线线径范围搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_lines(diameter_min=0.1, diameter_max=0.2)

        assert len(results) >= 1

    def test_search_lures_by_category(self, db_session: Session, sample_lure: Equipment):
        """拟饵类别搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_lures(lure_category="硬饵")

        assert len(results) >= 1
        for r in results:
            assert r['specs']['lure_category'] == "硬饵"

    def test_search_lures_by_weight_range(self, db_session: Session, sample_lure: Equipment):
        """拟饵重量范围搜索"""
        searcher = EquipmentSearcher(session=db_session)
        results = searcher.search_lures(weight_min=10.0, weight_max=20.0)

        assert len(results) >= 1


# === 相似度计算测试 ===


class TestEquipmentSearcherSimilarity:
    """相似度计算测试"""

    def test_similarity_exact_name_match(self, db_session: Session):
        """完全匹配名称得分最高"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {
            'name': '禧玛诺毒牙264ML',
            'model': None,
            'brand_name': None
        }
        score = searcher._similarity('禧玛诺毒牙264ML', equipment)

        # 完全匹配，ratio=1.0，权重2，所以 score=2.0
        assert score == 2.0

    def test_similarity_name_weight(self, db_session: Session):
        """名称权重为 2"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {
            'name': '禧玛诺毒牙264ML',
            'model': None,
            'brand_name': None
        }
        score = searcher._similarity('禧玛诺毒牙264ML', equipment)

        # 名称完全匹配，权重 2
        assert score == 2.0

    def test_similarity_model_weight(self, db_session: Session):
        """型号权重为 1"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {
            'name': None,
            'model': '264ML',
            'brand_name': None
        }
        score = searcher._similarity('264ML', equipment)

        # 型号完全匹配，权重 1
        assert score == 1.0

    def test_similarity_brand_bonus(self, db_session: Session):
        """品牌包含加 0.5"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {
            'name': '毒牙',
            'model': None,
            'brand_name': '禧玛诺'
        }
        # 搜索词包含品牌名
        score = searcher._similarity('禧玛诺毒牙', equipment)

        # 名称部分匹配 + 品牌包含 0.5
        assert score > 0.5

    def test_similarity_missing_name(self, db_session: Session):
        """���称缺失时正确处理"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {
            'name': None,
            'model': '264ML',
            'brand_name': '禧玛诺'
        }
        score = searcher._similarity('264ML', equipment)

        # 只有 model 参与计算
        assert score > 0

    def test_similarity_missing_all_fields(self, db_session: Session):
        """所有字段缺失返回 0"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {
            'name': None,
            'model': None,
            'brand_name': None
        }
        score = searcher._similarity('test', equipment)

        assert score == 0

    def test_similarity_empty_equipment(self, db_session: Session):
        """空装备返�� 0"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {}
        score = searcher._similarity('test', equipment)

        assert score == 0

    def test_similarity_case_insensitive(self, db_session: Session):
        """大小写不敏感"""
        searcher = EquipmentSearcher(session=db_session)
        equipment = {
            'name': 'Shimano',
            'model': None,
            'brand_name': None
        }
        score1 = searcher._similarity('SHIMANO', equipment)
        score2 = searcher._similarity('shimano', equipment)

        assert score1 == score2
        assert score1 == 2.0  # 完全匹配


# === 返回格式测试 ===


class TestEquipmentSearcherReturnFormat:
    """返回格式测试"""

    def test_search_returns_dict(self, db_session: Session, sample_rod: Equipment):
        """搜索返回字典格式"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_id(sample_rod.equipment_id)

        assert isinstance(result, dict)

    def test_search_dict_has_required_fields(self, db_session: Session, sample_rod: Equipment):
        """返回的字典包含必要字段"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_id(sample_rod.equipment_id)

        required_fields = ['id', 'equipment_id', 'name', 'category', 'brand_id', 'brand_name', 'specs']
        for field in required_fields:
            assert field in result

    def test_search_dict_specs_structure(self, db_session: Session, sample_rod: Equipment):
        """specs 字段结构正确"""
        searcher = EquipmentSearcher(session=db_session)
        result = searcher.search_by_id(sample_rod.equipment_id)

        assert 'specs' in result
        specs = result['specs']
        assert 'power' in specs
        assert 'length' in specs
        assert 'action' in specs
