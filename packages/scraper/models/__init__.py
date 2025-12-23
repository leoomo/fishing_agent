"""
Models - 爬虫相关模型

独立的模型定义，不依赖 agent_fishing
"""

from .base import Base, TimestampMixin
from .task import (
    TaskStatus,
    LogLevel,
    CrawlerTask,
    CrawlerLog,
    CrawlerWorkflowTemplate,
    CrawlerSchedule
)
from .node import (
    NodeStatus,
    CrawlerNode,
    NodeTaskAssignment
)

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Enums
    "TaskStatus",
    "LogLevel",
    "NodeStatus",
    # Models
    "CrawlerTask",
    "CrawlerLog",
    "CrawlerWorkflowTemplate",
    "CrawlerSchedule",
    # Node Models
    "CrawlerNode",
    "NodeTaskAssignment",
]
