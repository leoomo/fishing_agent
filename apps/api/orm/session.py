"""
Database session management with multi-database support

Supports SQLite (development), PostgreSQL (production), and MySQL.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from ..models.base import Base


# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite, postgresql, mysql

# SQLite configuration
SQLITE_DB_PATH = os.getenv(
    "DB_PATH",
    "shared/data/equipment.db"
)

# PostgreSQL configuration
POSTGRES_USER = os.getenv("DB_USER", "fishing_admin")
POSTGRES_PASSWORD = os.getenv("DB_PASSWORD", "")
POSTGRES_HOST = os.getenv("DB_HOST", "localhost")
POSTGRES_PORT = os.getenv("DB_PORT", "5432")
POSTGRES_DB = os.getenv("DB_NAME", "fishing_agent")

# MySQL configuration
MYSQL_USER = os.getenv("DB_USER", "fishing_admin")
MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "")
MYSQL_HOST = os.getenv("DB_HOST", "localhost")
MYSQL_PORT = os.getenv("DB_PORT", "3306")
MYSQL_DB = os.getenv("DB_NAME", "fishing_agent")

# SQL Echo (for debugging)
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"


def get_database_url():
    """
    Get database URL based on DB_TYPE environment variable

    Returns:
        str: Database connection URL
    """
    if DB_TYPE == "postgresql":
        return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    elif DB_TYPE == "mysql":
        return f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    else:  # sqlite (default)
        return f"sqlite:///{SQLITE_DB_PATH}"


def get_engine(url=None, **kwargs):
    """
    Create SQLAlchemy engine

    Args:
        url: Database URL (if None, uses get_database_url())
        **kwargs: Additional engine arguments

    Returns:
        Engine: SQLAlchemy engine instance
    """
    if url is None:
        url = get_database_url()

    # Default engine kwargs
    engine_kwargs = {
        "echo": SQL_ECHO,
    }

    # SQLite-specific configuration
    if url.startswith("sqlite"):
        engine_kwargs.update({
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,  # Use static pool for SQLite
        })

    # Override with custom kwargs
    engine_kwargs.update(kwargs)

    return create_engine(url, **engine_kwargs)


# Global engine and session factory
_engine = None
_session_factory = None


def init_db(url=None, create_tables=False):
    """
    Initialize database engine and session factory

    Args:
        url: Database URL (if None, uses get_database_url())
        create_tables: Whether to create all tables (default: False)

    Returns:
        Engine: Initialized engine
    """
    global _engine, _session_factory

    _engine = get_engine(url)
    _session_factory = scoped_session(
        sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # Prevent expired instances
        )
    )

    # Create tables if requested
    if create_tables:
        Base.metadata.create_all(_engine)

    return _engine


def get_session_factory():
    """
    Get the session factory (initializes if not already done)

    Returns:
        scoped_session: Thread-local session factory
    """
    global _session_factory

    if _session_factory is None:
        init_db()

    return _session_factory


@contextmanager
def get_db_session():
    """
    Context manager for database sessions

    Usage:
        with get_db_session() as session:
            # Use session
            session.query(Equipment).all()

    Yields:
        Session: SQLAlchemy session
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def close_db():
    """
    Close database connections and cleanup

    Call this when shutting down the application
    """
    global _session_factory, _engine

    if _session_factory is not None:
        _session_factory.remove()
        _session_factory = None

    if _engine is not None:
        _engine.dispose()
        _engine = None
