"""
微信登录功能的数据库迁移
"""

import logging
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)


def run_wechat_migrations(conn: sqlite3.Connection):
    """
    运行微信登录相关的数据库迁移

    Args:
        conn: 数据库连接
    """
    cursor = conn.cursor()

    # 添加到现有的迁移列表
    migrations = [
        _migration_007_add_wechat_users_table,
        _migration_008_add_wechat_unionid_to_admin_users,
    ]

    for i, migration in enumerate(migrations, 7):
        try:
            migration(cursor)
            conn.commit()
            logger.info(f"微信登录迁移 {i} 完成: {migration.__name__}")
        except Exception as e:
            logger.error(f"微信登录迁移 {i} 失败: {e}", exc_info=True)
            raise


def _migration_007_add_wechat_users_table(cursor: sqlite3.Cursor):
    """
    迁移007: 创建微信用户表

    创建表：
    - wechat_users: 微信用户信息表
    """
    logger.info("执行迁移007: 创建微信用户表")

    # ========== wechat_users表 ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wechat_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openid TEXT NOT NULL UNIQUE,
            unionid TEXT,
            nickname TEXT,
            avatar_url TEXT,
            gender INTEGER DEFAULT 0,
            city TEXT,
            province TEXT,
            country TEXT,
            language TEXT DEFAULT 'zh_CN',
            session_key TEXT,
            session_expires_at TIMESTAMP,
            admin_user_id INTEGER,
            is_active INTEGER DEFAULT 1,
            last_login_at TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            extra_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_user_id) REFERENCES admin_users(id)
        )
    """)
    logger.info("  创建表: wechat_users")

    # 创建索引
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wechat_users_openid ON wechat_users(openid)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wechat_users_unionid ON wechat_users(unionid)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wechat_users_admin_user_id ON wechat_users(admin_user_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_wechat_users_is_active ON wechat_users(is_active)"
    )
    logger.info("  创建索引: idx_wechat_users_*")


def _migration_008_add_wechat_unionid_to_admin_users(cursor: sqlite3.Cursor):
    """
    迁移008: 为admin_users表添加微信unionid字段
    """
    logger.info("执行迁移008: 添加微信unionid字段到admin_users表")

    # 检查字段是否已存在
    columns = _get_table_columns(cursor, "admin_users")
    column_names = [col[1] for col in columns]

    # 添加wechat_unionid字段
    if "wechat_unionid" not in column_names:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN wechat_unionid TEXT UNIQUE")
        logger.info("  添加字段: wechat_unionid")

        # 创建索引
        try:
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_admin_users_wechat_unionid ON admin_users(wechat_unionid)"
            )
            logger.info("  创建索引: idx_admin_users_wechat_unionid")
        except sqlite3.OperationalError:
            pass  # 索引已存在


def _get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> list:
    """获取表的列信息"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()