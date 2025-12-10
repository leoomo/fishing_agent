"""
Pytest configuration and fixtures for ORM tests
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from packages.agent_fishing.tools.lure.models.base import Base
from packages.agent_fishing.tools.lure.models import (
    Brand, Equipment, RodSpec, ReelSpec, LineSpec, LureSpec,
    User, UserEquipment, FishingLog,
    FishSpecies, FishKnowledge, FishSeasonActivity
)


@pytest.fixture(scope="function")
def db_engine():
    """
    Create an in-memory SQLite database for testing

    Yields:
        Engine: SQLAlchemy engine
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create a new database session for a test

    Args:
        db_engine: Database engine fixture

    Yields:
        Session: SQLAlchemy session
    """
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def sample_brand(db_session: Session):
    """
    Create a sample brand for testing

    Args:
        db_session: Database session

    Returns:
        Brand: Sample brand instance
    """
    brand = Brand(
        name_cn="光威",
        name_en="GW",
        country="中国",
        description="知名国产钓具品牌",
        is_active=True
    )
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def sample_equipment(db_session: Session, sample_brand: Brand):
    """
    Create sample equipment for testing

    Args:
        db_session: Database session
        sample_brand: Sample brand fixture

    Returns:
        Equipment: Sample equipment instance
    """
    equipment = Equipment(
        name="光威赤刃",
        category="鱼竿",
        brand_id=sample_brand.brand_id,
        model="CRE001",
        price_min=200.0,
        price_max=300.0,
        description="入门级路亚竿",
        user_level="新手",
        is_active=True
    )
    db_session.add(equipment)
    db_session.commit()
    db_session.refresh(equipment)
    return equipment


@pytest.fixture
def sample_rod_spec(db_session: Session, sample_equipment: Equipment):
    """
    Create sample rod spec for testing

    Args:
        db_session: Database session
        sample_equipment: Sample equipment fixture

    Returns:
        RodSpec: Sample rod spec instance
    """
    rod_spec = RodSpec(
        equipment_id=sample_equipment.equipment_id,
        length=2.1,
        sections=2,
        weight=120.0,
        power="M",
        action="Fast",
        lure_weight_min=5.0,
        lure_weight_max=20.0,
        line_weight_min=4.0,
        line_weight_max=12.0,
        material="碳素"
    )
    db_session.add(rod_spec)
    db_session.commit()
    db_session.refresh(rod_spec)
    return rod_spec


@pytest.fixture
def sample_user(db_session: Session):
    """
    Create a sample user for testing

    Args:
        db_session: Database session

    Returns:
        User: Sample user instance
    """
    user = User(
        username="test_user",
        nickname="测试钓友",
        email="test@example.com",
        experience_level="进阶",
        fishing_years=3,
        location="北京"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_fish_species(db_session: Session):
    """
    Create sample fish species for testing

    Args:
        db_session: Database session

    Returns:
        FishSpecies: Sample fish species instance
    """
    species = FishSpecies(
        name_cn="鲈鱼",
        name_en="Bass",
        scientific_name="Lateolabrax japonicus",
        category="肉食性鱼类",
        habitat="淡水、海水",
        min_weight=0.5,
        max_weight=10.0,
        min_length=20.0,
        max_length=80.0
    )
    db_session.add(species)
    db_session.commit()
    db_session.refresh(species)
    return species
