#!/usr/bin/env python3
"""
数据库迁移脚本: 添加 OCR 优先级字段到 pending_equipment 表

运行方式:
    uv run python scripts/migrate_add_ocr_priority.py
"""

import sys
import os

# 添加项目根目录到 path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import text
from apps.api.orm.session import get_db_session


def migrate():
    """执行迁移"""
    print("=" * 50)
    print("  数据库迁移: 添加 ocr_priority 字段")
    print("=" * 50)

    with get_db_session() as session:
        # 检查字段是否已存在
        check_sql = text("""
            SELECT COUNT(*) as cnt
            FROM pragma_table_info('pending_equipment')
            WHERE name = 'ocr_priority'
        """)
        result = session.execute(check_sql).fetchone()

        if result[0] > 0:
            print("ocr_priority 字段已存在，无需迁移")
            return

        # 添加 ocr_priority 字段
        migrations = [
            "ALTER TABLE pending_equipment ADD COLUMN ocr_priority INTEGER DEFAULT 0 NOT NULL",
            # 创建索引
            "CREATE INDEX IF NOT EXISTS idx_pending_equipment_ocr_priority ON pending_equipment(ocr_priority)",
        ]

        for i, sql in enumerate(migrations, 1):
            try:
                print(f"[{i}/{len(migrations)}] {sql[:60]}...")
                session.execute(text(sql))
                session.commit()
                print(f"    ✓ 成功")
            except Exception as e:
                print(f"    ✗ 失败: {e}")
                session.rollback()

        # 验证迁移
        verify_sql = text("""
            SELECT ocr_priority, COUNT(*) as cnt
            FROM pending_equipment
            GROUP BY ocr_priority
        """)
        results = session.execute(verify_sql).fetchall()

        print("\n迁移完成！当前优先级分布:")
        for priority, count in results:
            print(f"  优先级 {priority}: {count}")


if __name__ == "__main__":
    migrate()
