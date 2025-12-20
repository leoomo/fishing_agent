#!/usr/bin/env python3
"""
创建监控数据表
"""

import sqlite3
from datetime import datetime

# 数据库路径
DB_PATH = "packages/agent_fishing/tools/lure/data/equipment.db"

def create_monitoring_tables():
    """创建缺失的监控数据表"""

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建 agent_execution_logs 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            agent_type TEXT NOT NULL,
            agent_version TEXT,
            session_id INTEGER,
            user_id INTEGER,
            input_text TEXT,
            output_text TEXT,
            model_provider TEXT,
            model_name TEXT,
            llm_calls INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            latency_ms INTEGER,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            estimated_cost REAL DEFAULT 0.0,
            tool_calls_summary TEXT
        )
    """)

    # 创建 tool_call_logs 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            execution_id INTEGER,
            tool_name TEXT NOT NULL,
            tool_category TEXT,
            input_args TEXT,
            output_result TEXT,
            latency_ms INTEGER,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            FOREIGN KEY (execution_id) REFERENCES agent_execution_logs(id) ON DELETE CASCADE
        )
    """)

    # 创建 llm_logs 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            model_provider TEXT NOT NULL,
            model_name TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            response_time REAL,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            cost REAL,
            agent_type TEXT,
            session_id INTEGER,
            user_id INTEGER,
            execution_id INTEGER,
            FOREIGN KEY (execution_id) REFERENCES agent_execution_logs(id) ON DELETE SET NULL
        )
    """)

    # 创建索引以提高查询性能
    indexes = [
        "CREATE INDEX IF NOT EXISTS ix_agent_exec_timestamp_type ON agent_execution_logs(timestamp, agent_type)",
        "CREATE INDEX IF NOT EXISTS ix_agent_exec_user_timestamp ON agent_execution_logs(user_id, timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_agent_exec_session ON agent_execution_logs(session_id)",
        "CREATE INDEX IF NOT EXISTS ix_tool_call_timestamp_name ON tool_call_logs(timestamp, tool_name)",
        "CREATE INDEX IF NOT EXISTS ix_tool_call_execution ON tool_call_logs(execution_id)",
        "CREATE INDEX IF NOT EXISTS ix_llm_logs_timestamp_provider ON llm_logs(timestamp, model_provider)",
        "CREATE INDEX IF NOT EXISTS ix_llm_logs_success_timestamp ON llm_logs(success, timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_llm_logs_agent_type ON llm_logs(agent_type)"
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    # 提交事务
    conn.commit()

    # 验证表是否创建成功
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('agent_execution_logs', 'tool_call_logs', 'llm_logs')")
    created_tables = cursor.fetchall()

    print(f"成功创建监控数据表: {[table[0] for table in created_tables]}")

    # 关闭连接
    conn.close()

if __name__ == "__main__":
    create_monitoring_tables()
    print("监控数据表创建完成！")