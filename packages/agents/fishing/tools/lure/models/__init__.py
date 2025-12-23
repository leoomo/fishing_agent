"""
ORM Models 兼容层

此模块已迁移到 apps.api.models，本文件仅作为兼容层保留。
所有新代码应直接从 apps.api.models 导入。
"""

# 重导出所有 models
from apps.api.models import (
    # Base
    Base,
    TimestampMixin,
    # Equipment
    Brand,
    Equipment,
    RodSpec,
    ReelSpec,
    LineSpec,
    LureSpec,
    # User
    User,
    UserEquipment,
    FishingLog,
    # Content
    FishSpecies,
    FishKnowledge,
    FishSeasonActivity,
    RigType,
    RigSpec,
    RigComponent,
    LureType,
    RodLureFitness,
    # Admin
    AdminUser,
    # System
    CrawlerTask,
    CrawlerLog,
    APILog,
    LLMLog,
    SystemConfig,
    AnalyticsReport,
    AgentExecutionLog,
    ToolCallLog,
    # Chat
    ChatSession,
    ChatMessage,
)

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Equipment
    "Brand",
    "Equipment",
    "RodSpec",
    "ReelSpec",
    "LineSpec",
    "LureSpec",
    # User
    "User",
    "UserEquipment",
    "FishingLog",
    # Content
    "FishSpecies",
    "FishKnowledge",
    "FishSeasonActivity",
    "RigType",
    "RigSpec",
    "RigComponent",
    "LureType",
    "RodLureFitness",
    # Admin
    "AdminUser",
    # System
    "CrawlerTask",
    "CrawlerLog",
    "APILog",
    "LLMLog",
    "SystemConfig",
    "AnalyticsReport",
    "AgentExecutionLog",
    "ToolCallLog",
    # Chat
    "ChatSession",
    "ChatMessage",
]
