"""
数据库迁移模块

提供数据库schema升级功能，安全地添加新字段和表。
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseMigrations:
    """数据库迁移管理器"""

    def __init__(self, conn: sqlite3.Connection):
        """
        初始化迁移管理器

        Args:
            conn: 数据库连接
        """
        self.conn = conn
        self.cursor = conn.cursor()

    def run_all_migrations(self):
        """运行所有迁移"""
        logger.info("开始执行数据库迁移...")

        migrations = [
            self._migration_001_add_crawler_fields,
            self._migration_002_add_user_tables,
            self._migration_003_add_admin_users_table,
        ]

        for i, migration in enumerate(migrations, 1):
            try:
                migration()
                logger.info(f"迁移 {i} 完成: {migration.__name__}")
            except Exception as e:
                logger.error(f"迁移 {i} 失败: {e}", exc_info=True)
                raise

        self.conn.commit()
        logger.info("所有数据库迁移完成")

    def _migration_001_add_crawler_fields(self):
        """
        迁移001: 为equipment表添加爬虫相关字段

        添加字段：
        - source: 数据来源（crawler/manual/import）
        - source_url: 原始商品URL
        - crawled_at: 爬取时间
        - last_synced_at: 最后同步时间
        """
        logger.info("执行迁移001: 添加爬虫字段到equipment表")

        # 检查字段是否已存在
        columns = self._get_table_columns("equipment")
        column_names = [col[1] for col in columns]

        # 添加source字段
        if "source" not in column_names:
            self.cursor.execute(
                "ALTER TABLE equipment ADD COLUMN source TEXT DEFAULT 'manual'"
            )
            logger.info("  添加字段: source")

        # 添加source_url字段
        if "source_url" not in column_names:
            self.cursor.execute("ALTER TABLE equipment ADD COLUMN source_url TEXT")
            logger.info("  添加字段: source_url")

        # 添加crawled_at字段
        if "crawled_at" not in column_names:
            self.cursor.execute("ALTER TABLE equipment ADD COLUMN crawled_at TIMESTAMP")
            logger.info("  添加字段: crawled_at")

        # 添加last_synced_at字段
        if "last_synced_at" not in column_names:
            self.cursor.execute(
                "ALTER TABLE equipment ADD COLUMN last_synced_at TIMESTAMP"
            )
            logger.info("  添加字段: last_synced_at")

        # 创建索引（提升查询性能）
        try:
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_equipment_source ON equipment(source)"
            )
            logger.info("  创建索引: idx_equipment_source")
        except sqlite3.OperationalError:
            pass  # 索引已存在

    def _migration_002_add_user_tables(self):
        """
        迁移002: 创建用户装备管理相关表

        创建表：
        - users: 用户信息表
        - user_equipment: 用户装备关联表
        """
        logger.info("执行迁移002: 创建用户装备管理表")

        # ========== users表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                nickname TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                user_level TEXT DEFAULT '新手',
                fishing_experience_years INTEGER,
                preferred_fish TEXT,
                preferred_scenarios TEXT,
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("  创建表: users")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
        )
        logger.info("  创建索引: idx_users_username, idx_users_email")

        # ========== user_equipment表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                equipment_id INTEGER NOT NULL,
                purchase_date TEXT,
                purchase_price REAL,
                purchase_source TEXT,
                condition TEXT DEFAULT '正常',
                usage_frequency TEXT,
                notes TEXT,
                is_favorite INTEGER DEFAULT 0,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE,
                UNIQUE(user_id, equipment_id)
            )
        """)
        logger.info("  创建表: user_equipment")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_equipment_user ON user_equipment(user_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_equipment_equipment ON user_equipment(equipment_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_equipment_favorite ON user_equipment(is_favorite)"
        )
        logger.info("  创建索引: idx_user_equipment_*")

    def _migration_003_add_admin_users_table(self):
        """
        迁移003: 创建后端管理员用户表

        创建表:
        - admin_users: 后端管理员用户表
        - system_configs: 系统配置表 (依赖admin_users)
        - analytics_reports: 数据分析报告表 (依赖admin_users)
        """
        logger.info("执行迁移003: 创建后端管理员用户表")

        # ========== admin_users表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT NOT NULL DEFAULT 'readonly',
                is_active INTEGER NOT NULL DEFAULT 1,
                last_login TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("  创建表: admin_users")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_admin_users_is_active ON admin_users(is_active)"
        )
        logger.info("  创建索引: idx_admin_users_*")

        # ========== system_config表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                config_type TEXT NOT NULL,
                description TEXT,
                is_encrypted INTEGER DEFAULT 0,
                last_modified_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (last_modified_by) REFERENCES admin_users(id)
            )
        """)
        logger.info("  创建表: system_config")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_system_config_type ON system_config(config_type)"
        )
        logger.info("  创建索引: idx_system_config_*")

        # ========== analytics_reports表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                report_data TEXT NOT NULL,
                generated_by INTEGER,
                is_published INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generated_by) REFERENCES admin_users(id)
            )
        """)
        logger.info("  创建表: analytics_reports")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analytics_reports_type ON analytics_reports(report_type)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analytics_reports_start ON analytics_reports(start_date)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analytics_reports_end ON analytics_reports(end_date)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analytics_reports_generated ON analytics_reports(generated_by)"
        )
        logger.info("  创建索引: idx_analytics_reports_*")

    def _get_table_columns(self, table_name: str) -> list:
        """
        获取表的所有列信息

        Args:
            table_name: 表名

        Returns:
            列信息列表
        """
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return self.cursor.fetchall()


def run_migrations(db_path: Optional[Path] = None):
    """
    运行数据库迁移的便捷函数

    Args:
        db_path: 数据库路径
    """
    from .database import DB_PATH

    db_file = db_path or DB_PATH

    logger.info(f"连接数据库: {db_file}")
    conn = sqlite3.connect(str(db_file))

    try:
        migrations = DatabaseMigrations(conn)
        migrations.run_all_migrations()
        logger.info("数据库迁移成功")
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 运行迁移
    run_migrations()
