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
            self._migration_004_add_crawler_task_tables,
            self._migration_005_add_workflow_support,
            self._migration_006_add_pending_equipment_table,
            self._migration_007_rename_fish_species_id_to_species_id,
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

    def _migration_004_add_crawler_task_tables(self):
        """
        迁移004: 创建爬虫任务相关表

        创建表：
        - crawler_tasks: 爬虫任务表
        - crawler_logs: 爬虫任务日志表
        """
        logger.info("执行迁移004: 创建爬虫任务相关表")

        # ========== crawler_tasks表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawler_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                task_name TEXT,
                status TEXT DEFAULT 'pending',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_items INTEGER DEFAULT 0,
                success_items INTEGER DEFAULT 0,
                failed_items INTEGER DEFAULT 0,
                error_message TEXT,
                config TEXT,
                result_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("  创建表: crawler_tasks")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_crawler_tasks_type ON crawler_tasks(task_type)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_crawler_tasks_status ON crawler_tasks(status)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_crawler_tasks_created ON crawler_tasks(created_at)"
        )
        logger.info("  创建索引: idx_crawler_tasks_*")

        # ========== crawler_logs表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawler_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES crawler_tasks(id) ON DELETE CASCADE
            )
        """)
        logger.info("  创建表: crawler_logs")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_crawler_logs_task ON crawler_logs(task_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_crawler_logs_level ON crawler_logs(level)"
        )
        logger.info("  创建索引: idx_crawler_logs_*")

    def _migration_005_add_workflow_support(self):
        """
        迁移005: 为crawler_tasks表添加工作流支持字段

        添加字段：
        - workflow_id: 工作流ID
        - workflow_name: 工作流名称
        - parent_task_id: 父任务ID
        - step_order: 步骤顺序
        - step_config: 步骤配置
        - platform: 平台标识
        - shop_url: 店铺URL
        - retry_count: 重试次数
        - max_retries: 最大重试次数
        - timeout_seconds: 超时时间
        - requires_intervention: 是否需要人工干预
        - duplicate_items: 去重数量
        - invalid_items: 无效数据量
        """
        logger.info("执行迁移005: 添加工作流支持字段到crawler_tasks表")

        # 检查字段是否已存在
        columns = self._get_table_columns("crawler_tasks")
        column_names = [col[1] for col in columns]

        # 工作流相关字段
        workflow_fields = [
            ("workflow_id", "TEXT"),
            ("workflow_name", "TEXT"),
            ("parent_task_id", "INTEGER"),
            ("step_order", "INTEGER DEFAULT 0"),
            ("step_config", "TEXT"),
        ]

        # 执行控制字段
        control_fields = [
            ("platform", "TEXT"),
            ("shop_url", "TEXT"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("max_retries", "INTEGER DEFAULT 3"),
            ("timeout_seconds", "INTEGER DEFAULT 3600"),
            ("requires_intervention", "INTEGER DEFAULT 0"),
        ]

        # 数据质量字段
        quality_fields = [
            ("duplicate_items", "INTEGER DEFAULT 0"),
            ("invalid_items", "INTEGER DEFAULT 0"),
        ]

        # 添加所有字段
        all_fields = workflow_fields + control_fields + quality_fields

        for field_name, field_type in all_fields:
            if field_name not in column_names:
                self.cursor.execute(
                    f"ALTER TABLE crawler_tasks ADD COLUMN {field_name} {field_type}"
                )
                logger.info(f"  添加字段: {field_name}")

        # 添加外键约束
        try:
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_crawler_task_parent ON crawler_tasks(parent_task_id)"
            )
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_crawler_task_workflow ON crawler_tasks(workflow_id)"
            )
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_crawler_task_platform ON crawler_tasks(platform)"
            )
            logger.info("  创建索引: idx_crawler_task_*")
        except sqlite3.OperationalError:
            pass  # 索引已存在

        # ========== 创建工作流模板表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawler_workflow_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                template_json TEXT NOT NULL,
                category TEXT,
                is_system INTEGER DEFAULT 0,
                created_by INTEGER,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("  创建表: crawler_workflow_templates")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_templates_category ON crawler_workflow_templates(category)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_templates_system ON crawler_workflow_templates(is_system)"
        )

        # ========== 创建定时调度表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawler_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                template_id INTEGER NOT NULL,
                cron_expression TEXT NOT NULL,
                timezone TEXT DEFAULT 'Asia/Shanghai',
                is_enabled INTEGER DEFAULT 1,
                config TEXT,
                next_run_time TIMESTAMP,
                last_run_time TIMESTAMP,
                last_task_id INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES crawler_workflow_templates(id)
            )
        """)
        logger.info("  创建表: crawler_schedules")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_schedules_template ON crawler_schedules(template_id)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_schedules_enabled ON crawler_schedules(is_enabled)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON crawler_schedules(next_run_time, is_enabled)"
        )
        logger.info("  创建索引: idx_schedules_*")

    def _migration_006_add_pending_equipment_table(self):
        """
        迁移006: 创建待审核装备表

        用于存储 Agent 从 OCR 文本中提取的装备信息，等待人工审核。
        """
        logger.info("执行迁移006: 创建待审核装备表")

        # ========== pending_equipment表 ==========
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL DEFAULT 'pending',

                -- 原始输入
                ocr_text TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'unknown',
                source_url TEXT,

                -- LLM 提取结果
                extracted_data TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.0,

                -- 提取的关键字段（便于列表展示和搜索）
                equipment_type TEXT,
                brand_name TEXT,
                model_name TEXT,
                product_name TEXT,

                -- 审核信息
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                review_notes TEXT,

                -- 最终装备 ID
                equipment_id INTEGER,

                -- 时间戳
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (reviewed_by) REFERENCES admin_users(id),
                FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
            )
        """)
        logger.info("  创建表: pending_equipment")

        # 创建索引
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pending_equipment_status ON pending_equipment(status)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pending_equipment_type ON pending_equipment(equipment_type)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pending_equipment_brand ON pending_equipment(brand_name)"
        )
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pending_equipment_created ON pending_equipment(created_at)"
        )
        logger.info("  创建索引: idx_pending_equipment_*")

    def _migration_007_rename_fish_species_id_to_species_id(self):
        """
        迁移007: 统一字段命名 fish_species_id -> species_id

        SQLite 不支持直接 RENAME COLUMN，需要通过重建表实现。
        涉及表：
        - product_images: fish_species_id -> species_id
        """
        logger.info("执行迁移007: 统一 fish_species_id -> species_id")

        # 检查 product_images 表是否需要迁移
        columns = self._get_table_columns("product_images")
        column_names = [col[1] for col in columns]

        # 如果已经是 species_id，跳过
        if "species_id" in column_names and "fish_species_id" not in column_names:
            logger.info("  product_images 表已迁移，跳过")
            return

        # 如果还是 fish_species_id，需要迁移
        if "fish_species_id" in column_names:
            logger.info("  开始迁移 product_images 表...")

            # 1. 创建新表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_images_new (
                    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER,
                    rig_type_id INTEGER,
                    species_id INTEGER,
                    image_url TEXT NOT NULL,
                    image_type TEXT NOT NULL,
                    description TEXT,
                    display_order INTEGER DEFAULT 0,
                    embedding_id TEXT,
                    is_vectorized INTEGER DEFAULT 0,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE,
                    FOREIGN KEY (rig_type_id) REFERENCES rig_types(id) ON DELETE CASCADE,
                    FOREIGN KEY (species_id) REFERENCES fish_species(species_id) ON DELETE CASCADE
                )
            """)

            # 2. 复制数据
            self.cursor.execute("""
                INSERT INTO product_images_new (
                    image_id, equipment_id, rig_type_id, species_id,
                    image_url, image_type, description, display_order,
                    embedding_id, is_vectorized, file_size, width, height, format,
                    created_at, updated_at
                )
                SELECT
                    image_id, equipment_id, rig_type_id, fish_species_id,
                    image_url, image_type, description, display_order,
                    embedding_id, is_vectorized, file_size, width, height, format,
                    created_at, updated_at
                FROM product_images
            """)

            # 3. 删除旧表
            self.cursor.execute("DROP TABLE product_images")

            # 4. 重命名新表
            self.cursor.execute("ALTER TABLE product_images_new RENAME TO product_images")

            # 5. 重建索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_equipment ON product_images(equipment_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_rig ON product_images(rig_type_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_fish ON product_images(species_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_type ON product_images(image_type)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_vectorized ON product_images(is_vectorized)")

            logger.info("  product_images 表迁移完成")
        else:
            logger.info("  product_images 表没有 fish_species_id 字段，跳过")

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
