"""
Article API schemas

Minimalist validation - only essential fields required
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class ArticleTypeEnum(str, Enum):
    """Article type enumeration"""
    STRATEGY = "strategy"
    TIPS = "tips"
    REVIEW = "review"
    SPOT = "spot"


class ArticleStatusEnum(str, Enum):
    """Article status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ========== Create/Update Schemas ==========

class ArticleCreate(BaseModel):
    """
    Create article - Only 2 required fields

    Design: User only needs to provide title and select type
    """
    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    article_type: ArticleTypeEnum = Field(..., description="文章类型")
    content: str = Field(default="", max_length=50000, description="Markdown内容")

    # Optional fields - Progressive disclosure
    cover_image: Optional[str] = Field(None, max_length=500, description="封面图URL")
    summary: Optional[str] = Field(None, max_length=300, description="摘要")
    tags: Optional[str] = Field(None, max_length=200, description="标签(逗号分隔)")
    extensions: Optional[Dict[str, Any]] = Field(None, description="扩展字段")


class ArticleUpdate(BaseModel):
    """
    Update article - All fields optional for auto-save
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=50000)
    article_type: Optional[ArticleTypeEnum] = None
    cover_image: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = Field(None, max_length=300)
    tags: Optional[str] = Field(None, max_length=200)
    extensions: Optional[Dict[str, Any]] = None


class ArticlePublish(BaseModel):
    """
    Publish action - Can update fields at publish time
    """
    summary: Optional[str] = Field(None, max_length=300, description="发布时可更新摘要")
    tags: Optional[str] = Field(None, max_length=200, description="发布时可更新标签")


# ========== Response Schemas ==========

class ArticleResponse(BaseModel):
    """Article detail response"""
    id: int
    title: str
    content: str
    article_type: str
    status: str
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    cover_image: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []
    extensions: Optional[Dict[str, Any]] = None
    view_count: int = 0
    like_count: int = 0
    created_at: str
    updated_at: str
    published_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ArticleListItem(BaseModel):
    """Article list item - No content for faster loading"""
    id: int
    title: str
    article_type: str
    status: str
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    cover_image: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []
    view_count: int = 0
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class ArticleListResponse(BaseModel):
    """Paginated article list"""
    total: int
    page: int
    page_size: int
    items: List[ArticleListItem]


# ========== Search Schemas ==========

class ArticleSearchResult(BaseModel):
    """Semantic search result item"""
    id: int
    title: str
    article_type: str
    summary: Optional[str] = None
    score: float = Field(..., description="相似度分数")


class ArticleSearchResponse(BaseModel):
    """Semantic search response"""
    query: str
    results: List[ArticleSearchResult]
    total: int
