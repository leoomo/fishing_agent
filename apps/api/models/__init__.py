"""
SQLAlchemy ORM Models for Fishing Agent

This package contains all database models using SQLAlchemy ORM.
"""

from .base import Base, TimestampMixin
from .brand import Brand
from .equipment import Equipment, RodSpec, ReelSpec, LineSpec, LureSpec
from .user import User, UserEquipment, FishingLog
from .fish import FishSpecies, FishKnowledge, FishSeasonActivity
from .rig import RigType, RigSpec, RigComponent
from .lure import LureType, RodLureFitness
from .accessory import Accessory
from .admin_user import AdminUser
from .system import (
    CrawlerTask, CrawlerLog, APILog, LLMLog, SystemConfig, AnalyticsReport,
    AgentExecutionLog, ToolCallLog
)
from .chat import ChatSession, ChatMessage
from .article import Article, ArticleType, ArticleStatus

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
    "Accessory",

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

    # Article
    "Article",
    "ArticleType",
    "ArticleStatus",
]
