"""
Article content model for fishing knowledge management

Supports:
- Fishing strategies (攻略)
- Tips & tricks (技巧)
- Equipment reviews (评测)
- Spot recommendations (钓点)
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey,
    Enum as SQLEnum, DateTime, Index
)
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class ArticleType(str, enum.Enum):
    """Article type enumeration"""
    STRATEGY = "strategy"   # 钓鱼攻略
    TIPS = "tips"           # 技巧分享
    REVIEW = "review"       # 装备评测
    SPOT = "spot"           # 钓点推荐


class ArticleStatus(str, enum.Enum):
    """Article status enumeration"""
    DRAFT = "draft"           # 草稿
    PUBLISHED = "published"   # 已发布
    ARCHIVED = "archived"     # 已归档


class Article(Base, TimestampMixin):
    """
    Article content model

    Design principle: Less is More
    - Only essential fields, no redundant metadata
    - Rich content through JSON extensions
    """

    __tablename__ = 'articles'

    __table_args__ = (
        Index('ix_article_type_status', 'article_type', 'status'),
        Index('ix_article_author_created', 'author_id', 'created_at'),
    )

    # === Core Fields (Required) ===
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True, comment="文章标题")
    content = Column(Text, nullable=False, default="", comment="Markdown内容")
    article_type = Column(
        SQLEnum(ArticleType, native_enum=False),
        nullable=False,
        index=True,
        comment="文章类型"
    )

    # === Status Management ===
    status = Column(
        SQLEnum(ArticleStatus, native_enum=False),
        default=ArticleStatus.DRAFT,
        nullable=False,
        index=True,
        comment="发布状态"
    )

    # === Author Info ===
    author_id = Column(
        Integer,
        ForeignKey('admin_users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="作者ID"
    )

    # === Optional Enhancements ===
    cover_image = Column(String(500), nullable=True, comment="封面图URL")
    summary = Column(String(300), nullable=True, comment="摘要")

    # === Type-Specific Extensions (JSON) ===
    # Strategy: {"target_fish": ["bass"], "seasons": ["spring"], "difficulty": "beginner"}
    # Tips: {"category": "casting", "read_time": 2}
    # Review: {"equipment_ids": [1,2], "rating": 4.5, "pros": [], "cons": []}
    # Spot: {"location": {"lat": 0, "lng": 0}, "water_type": "lake", "facilities": []}
    extensions = Column(Text, nullable=True, comment="扩展字段(JSON)")

    # === SEO & Discovery ===
    tags = Column(String(200), nullable=True, comment="标签(逗号分隔)")

    # === Metrics (Read-only) ===
    view_count = Column(Integer, default=0, comment="浏览次数")
    like_count = Column(Integer, default=0, comment="点赞次数")

    # === Timestamps ===
    published_at = Column(DateTime, nullable=True, comment="首次发布时间")

    # === Relationships ===
    author = relationship("AdminUser", backref="articles")

    def __repr__(self):
        title_preview = self.title[:20] + "..." if len(self.title) > 20 else self.title
        return f"<Article(id={self.id}, title='{title_preview}', type={self.article_type.value if self.article_type else None})>"

    def to_dict(self, include_content: bool = True) -> dict:
        """Convert to dictionary"""
        result = {
            'id': self.id,
            'title': self.title,
            'article_type': self.article_type.value if self.article_type else None,
            'status': self.status.value if self.status else None,
            'author_id': self.author_id,
            'author_name': self.author.username if self.author else None,
            'cover_image': self.cover_image,
            'summary': self.summary,
            'tags': self.tags.split(',') if self.tags else [],
            'view_count': self.view_count,
            'like_count': self.like_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }

        if include_content:
            result['content'] = self.content
            result['extensions'] = self.extensions

        return result
