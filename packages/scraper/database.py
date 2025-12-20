"""
Database connection for distributed crawler

独立的数据库连接，使用 crawler.db，与业务数据库 fishing.db 隔离
"""

import os
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# Database path configuration
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "shared" / "data" / "crawler.db"


class CrawlerDatabase:
    """
    爬虫专用数据库管理器

    Features:
    - 独立的 SQLite 数据库 (crawler.db)
    - 线程安全的会话管理
    - 自动创建表结构
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，默认为 shared/data/crawler.db
        """
        if db_path is None:
            db_path = os.getenv("CRAWLER_DB_PATH", str(DEFAULT_DB_PATH))

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engine with SQLite-specific settings
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=os.getenv("CRAWLER_DB_ECHO", "").lower() == "true",
            connect_args={
                "check_same_thread": False,  # Allow multi-threading
                "timeout": 30,  # Connection timeout
            },
            poolclass=StaticPool,  # Use static pool for SQLite
        )

        # Enable WAL mode for better concurrent access
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Crawler database initialized: {self.db_path}")

    def create_tables(self):
        """Create all tables if not exist"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Crawler database tables created/verified")

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("Crawler database tables dropped!")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions

        Usage:
            with db.session_scope() as session:
                session.query(CrawlerNode).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database instance
_db_instance: Optional[CrawlerDatabase] = None


def get_crawler_db() -> CrawlerDatabase:
    """
    Get or create the global crawler database instance

    Returns:
        CrawlerDatabase instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = CrawlerDatabase()
        _db_instance.create_tables()
    return _db_instance


def init_crawler_db(db_path: Optional[str] = None) -> CrawlerDatabase:
    """
    Initialize the crawler database with custom path

    Args:
        db_path: Custom database path

    Returns:
        CrawlerDatabase instance
    """
    global _db_instance
    _db_instance = CrawlerDatabase(db_path)
    _db_instance.create_tables()
    return _db_instance


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions

    Usage:
        @router.get("/nodes")
        def get_nodes(db: Session = Depends(get_db_session)):
            return db.query(CrawlerNode).all()
    """
    db = get_crawler_db()
    session = db.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
