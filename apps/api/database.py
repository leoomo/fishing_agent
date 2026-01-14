"""
路亚装备数据库模块

提供SQLite数据库访问接口，包含：
- 线程安全的连接管理
- WAL模式支持并发读
- 事务管理
- 表初始化
"""

import sqlite3
import threading
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass

# 数据库路径
DB_PATH = Path(__file__).parents[2] / "shared" / "data" / "equipment.db"


class LureDatabase:
    """路亚装备数据库访问类

    特点：
    - 线程本地连接（每个线程独立连接）
    - WAL模式支持并发读
    - 自动重试机制
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._local = threading.local()
        self._init_lock = threading.Lock()
        self._initialized = False

        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._ensure_initialized()

    def _get_connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            # 启用WAL模式
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
        return self._local.conn

    def _ensure_initialized(self):
        """确保数据库已初始化"""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return
            self._init_tables()
            self._initialized = True

    def _init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # ========== 品牌表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_cn TEXT NOT NULL UNIQUE,
                name_en TEXT,
                country TEXT,
                tier TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== 装备主表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand_id INTEGER,
                model TEXT,
                price_min REAL,
                price_max REAL,
                description TEXT,
                features TEXT,
                target_fish TEXT,
                user_level TEXT,
                is_active INTEGER DEFAULT 1,
                is_vectorized INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (brand_id) REFERENCES brands(id)
            )
        """)

        # ========== 鱼竿规格表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rod_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL UNIQUE,
                length REAL,
                power TEXT,
                action TEXT,
                sections INTEGER,
                weight REAL,
                lure_weight_min REAL,
                lure_weight_max REAL,
                line_weight_min REAL,
                line_weight_max REAL,
                guide_type TEXT,
                handle_type TEXT,
                FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
            )
        """)

        # ========== 渔轮规格表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reel_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL UNIQUE,
                reel_type TEXT,
                gear_ratio TEXT,
                bearings TEXT,
                weight REAL,
                line_capacity TEXT,
                max_drag REAL,
                retrieve_per_turn REAL,
                FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
            )
        """)

        # ========== 鱼线规格表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS line_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL UNIQUE,
                line_type TEXT,
                diameter REAL,
                strength_lb REAL,
                length_m REAL,
                color TEXT,
                material TEXT,
                FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
            )
        """)

        # ========== 拟饵规格表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lure_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL UNIQUE,
                lure_type TEXT,
                lure_category TEXT,
                length REAL,
                weight REAL,
                diving_depth_min REAL,
                diving_depth_max REAL,
                color TEXT,
                action_type TEXT,
                FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id) ON DELETE CASCADE
            )
        """)

        # ========== 图片关联表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_images (
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

        # ========== 鱼类基础表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fish_species (
                species_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_cn TEXT NOT NULL UNIQUE,
                name_en TEXT,
                name_latin TEXT,
                aliases TEXT,
                category TEXT NOT NULL,
                family TEXT,
                order_name TEXT,
                habitat TEXT,
                habitat_description TEXT,
                active_temp_min REAL,
                active_temp_max REAL,
                optimal_temp_min REAL,
                optimal_temp_max REAL,
                active_seasons TEXT,
                feeding_habits TEXT,
                prey_types TEXT,
                max_length REAL,
                common_length_min REAL,
                common_length_max REAL,
                max_weight REAL,
                common_weight_min REAL,
                common_weight_max REAL,
                lure_difficulty TEXT,
                fight_intensity TEXT,
                recommended_lures TEXT,
                recommended_rigs TEXT,
                recommended_rod_power TEXT,
                recommended_line_lb_min REAL,
                recommended_line_lb_max REAL,
                native_region TEXT,
                distribution_cn TEXT,
                introduced_status TEXT,
                is_protected INTEGER DEFAULT 0,
                fishing_regulations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== 鱼类知识表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fish_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id INTEGER,
                knowledge_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                tags TEXT,
                keywords TEXT,
                embedding_id TEXT,
                is_vectorized INTEGER DEFAULT 0,
                source TEXT,
                author TEXT,
                reliability_score REAL DEFAULT 0.8,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (species_id) REFERENCES fish_species(species_id) ON DELETE CASCADE
            )
        """)

        # ========== 钓组类型表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rig_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_cn TEXT NOT NULL UNIQUE,
                name_en TEXT,
                category TEXT,
                description TEXT,
                difficulty TEXT,
                usage_scenario TEXT,
                target_fish TEXT,
                anti_snag_rating INTEGER,
                sensitivity_rating INTEGER,
                versatility_rating INTEGER,
                is_vectorized INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== 钓组规格表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rig_specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rig_type_id INTEGER NOT NULL,
                description TEXT,
                components TEXT,
                assembly_steps TEXT,
                operation_tips TEXT,
                suitable_scenarios TEXT,
                target_fish TEXT,
                is_vectorized INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rig_type_id) REFERENCES rig_types(id) ON DELETE CASCADE
            )
        """)

        # ========== 拟饵类型字典表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lure_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_cn TEXT NOT NULL UNIQUE,
                name_en TEXT,
                category TEXT,
                description TEXT,
                typical_action TEXT,
                typical_depth TEXT,
                best_season TEXT,
                target_fish TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== 鱼竿-拟饵/钓组兼容性矩阵 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rod_lure_fitness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rod_power TEXT NOT NULL,
                lure_type_id INTEGER,
                rig_type_id INTEGER,
                fitness_level TEXT NOT NULL,
                lure_weight_min REAL,
                lure_weight_max REAL,
                notes TEXT,
                FOREIGN KEY (lure_type_id) REFERENCES lure_types(id),
                FOREIGN KEY (rig_type_id) REFERENCES rig_types(id)
            )
        """)

        # ========== 鱼类季节活动规律表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fish_season_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                species_id INTEGER NOT NULL,
                season TEXT NOT NULL,
                activity_level INTEGER,
                best_time_of_day TEXT,
                preferred_depth TEXT,
                feeding_intensity TEXT,
                recommended_lure_types TEXT,
                notes TEXT,
                FOREIGN KEY (species_id) REFERENCES fish_species(species_id) ON DELETE CASCADE
            )
        """)

        # ========== 钓组配件组成表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rig_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rig_type_id INTEGER NOT NULL,
                component_name TEXT NOT NULL,
                component_type TEXT,
                quantity INTEGER DEFAULT 1,
                spec_requirement TEXT,
                is_required INTEGER DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (rig_type_id) REFERENCES rig_types(id) ON DELETE CASCADE
            )
        """)

        # ========== 鱼类采集进度表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fish_fetch_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_cn TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'pending',
                species_id INTEGER,
                fishbase_data TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== 创建索引 ==========
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_brand ON equipment(brand_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_price ON equipment(price_min, price_max)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_vectorized ON equipment(is_vectorized)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_equipment ON product_images(equipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_rig ON product_images(rig_type_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_fish ON product_images(species_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_type ON product_images(image_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_vectorized ON product_images(is_vectorized)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fish_name ON fish_species(name_cn)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fish_category ON fish_species(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_fish ON fish_knowledge(species_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_type ON fish_knowledge(knowledge_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_vectorized ON fish_knowledge(is_vectorized)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rig_types_vectorized ON rig_types(is_vectorized)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lure_types_category ON lure_types(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rod_lure_fitness_power ON rod_lure_fitness(rod_power)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fish_season_activity ON fish_season_activity(species_id, season)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rig_components ON rig_components(rig_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fish_fetch_progress_status ON fish_fetch_progress(status)")

        conn.commit()

        # 运行数据库迁移
        self._run_migrations()

    def _run_migrations(self):
        """运行数据库迁移"""
        try:
            from packages.agents.fishing.tools.lure.migrations import DatabaseMigrations
            conn = self._get_connection()
            migrations = DatabaseMigrations(conn)
            migrations.run_all_migrations()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"数据库迁移执行失败（可能已经执行过）: {e}")

    def execute(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询（只读）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """执行写入操作，返回受影响行数或lastrowid"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

        if query.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        return cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """批量执行写入"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close(self):
        """关闭当前线程的连接"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# 全局数据库实例
_db_instance: Optional[LureDatabase] = None
_db_lock = threading.Lock()


def get_db(db_path: Optional[str] = None) -> LureDatabase:
    """获取数据库单例实例"""
    global _db_instance

    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = LureDatabase(db_path)

    return _db_instance


def reset_db():
    """重置数据库实例（主要用于测试）"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
