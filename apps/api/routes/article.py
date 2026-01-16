"""
Article API routes

Endpoints:
  POST   /articles              - Create article (auto-save draft)
  GET    /articles              - List articles (with filters)
  GET    /articles/{id}         - Get article detail
  PUT    /articles/{id}         - Update article (auto-save)
  DELETE /articles/{id}         - Delete article
  POST   /articles/{id}/publish - Publish article
  POST   /articles/{id}/archive - Archive article
  GET    /articles/search       - Semantic search
  GET    /articles/{id}/similar - Similar articles
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional
from datetime import datetime
import logging
import json

from apps.api.orm.session import get_db_session
from apps.api.models.article import Article, ArticleType, ArticleStatus
from apps.api.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticlePublish,
    ArticleResponse,
    ArticleListResponse,
    ArticleListItem,
    ArticleTypeEnum,
    ArticleStatusEnum,
    ArticleSearchResponse,
    ArticleSearchResult,
    ArticleFetchSource,
    ArticleFetchProgress,
    ArticleFetchProgressItem,
    ArticleFetchProgressStats,
    ArticleFetchStartRequest,
    ArticleFetchRetryRequest,
)
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


def article_to_response(article: Article) -> ArticleResponse:
    """Convert Article model to response schema"""
    extensions = None
    if article.extensions:
        try:
            extensions = json.loads(article.extensions)
        except (json.JSONDecodeError, TypeError):
            extensions = None

    return ArticleResponse(
        id=article.id,
        title=article.title,
        content=article.content or "",
        article_type=article.article_type.value if article.article_type else "",
        status=article.status.value if article.status else "",
        author_id=article.author_id,
        author_name=article.author.username if article.author else None,
        cover_image=article.cover_image,
        summary=article.summary,
        tags=article.tags.split(',') if article.tags else [],
        extensions=extensions,
        view_count=article.view_count or 0,
        like_count=article.like_count or 0,
        created_at=article.created_at.isoformat() if article.created_at else "",
        updated_at=article.updated_at.isoformat() if article.updated_at else "",
        published_at=article.published_at.isoformat() if article.published_at else None,
    )


def article_to_list_item(article: Article) -> ArticleListItem:
    """Convert Article model to list item schema"""
    return ArticleListItem(
        id=article.id,
        title=article.title,
        article_type=article.article_type.value if article.article_type else "",
        status=article.status.value if article.status else "",
        author_id=article.author_id,
        author_name=article.author.username if article.author else None,
        cover_image=article.cover_image,
        summary=article.summary,
        tags=article.tags.split(',') if article.tags else [],
        view_count=article.view_count or 0,
        created_at=article.created_at.isoformat() if article.created_at else "",
        updated_at=article.updated_at.isoformat() if article.updated_at else "",
    )


# ========== CRUD Endpoints ==========

@router.post(
    "/articles",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建文章(草稿)",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def create_article(
    data: ArticleCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """
    Create new article as draft

    Auto-save enabled - Frontend sends periodic updates
    """
    try:
        with get_db_session() as session:
            # Prepare extensions as JSON string
            extensions_str = None
            if data.extensions:
                extensions_str = json.dumps(data.extensions, ensure_ascii=False)

            article = Article(
                title=data.title,
                content=data.content or "",
                article_type=ArticleType(data.article_type.value),
                status=ArticleStatus.DRAFT,
                author_id=current_user.user_id,
                cover_image=data.cover_image,
                summary=data.summary,
                tags=data.tags,
                extensions=extensions_str,
            )

            session.add(article)
            session.commit()
            session.refresh(article)

            logger.info(f"Article created: id={article.id}, title={article.title[:30]}, user={current_user.username}")

            return article_to_response(article)

    except Exception as e:
        logger.error(f"Failed to create article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建文章失败: {str(e)}"
        )


@router.get(
    "/articles",
    response_model=ArticleListResponse,
    summary="获取文章列表",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_READ))]
)
async def list_articles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    article_type: Optional[ArticleTypeEnum] = Query(None, description="文章类型"),
    article_status: Optional[ArticleStatusEnum] = Query(None, alias="status", description="状态"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    author_id: Optional[int] = Query(None, description="作者ID"),
):
    """List articles with filters"""
    try:
        with get_db_session() as session:
            query = session.query(Article)

            # Apply filters
            if article_type:
                query = query.filter(Article.article_type == ArticleType(article_type.value))
            if article_status:
                query = query.filter(Article.status == ArticleStatus(article_status.value))
            if author_id:
                query = query.filter(Article.author_id == author_id)
            if keyword:
                query = query.filter(Article.title.contains(keyword))

            # Get total count
            total = query.count()

            # Pagination
            offset = (page - 1) * page_size
            articles = query.order_by(Article.updated_at.desc()).offset(offset).limit(page_size).all()

            return ArticleListResponse(
                total=total,
                page=page,
                page_size=page_size,
                items=[article_to_list_item(a) for a in articles]
            )

    except Exception as e:
        logger.error(f"Failed to list articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文章列表失败: {str(e)}"
        )


@router.get(
    "/articles/{article_id}",
    response_model=ArticleResponse,
    summary="获取文章详情",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_READ))]
)
async def get_article(article_id: int):
    """Get article by ID with full content"""
    try:
        with get_db_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()

            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文章不存在: id={article_id}"
                )

            return article_to_response(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文章失败: {str(e)}"
        )


@router.put(
    "/articles/{article_id}",
    response_model=ArticleResponse,
    summary="更新文章",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """
    Update article - Used for auto-save

    Only updates provided fields
    """
    try:
        with get_db_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()

            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文章不存在: id={article_id}"
                )

            # Update only provided fields
            update_data = data.model_dump(exclude_unset=True)

            if 'article_type' in update_data and update_data['article_type']:
                update_data['article_type'] = ArticleType(update_data['article_type'].value)

            if 'extensions' in update_data and update_data['extensions'] is not None:
                update_data['extensions'] = json.dumps(update_data['extensions'], ensure_ascii=False)

            for key, value in update_data.items():
                if hasattr(article, key):
                    setattr(article, key, value)

            session.commit()
            session.refresh(article)

            logger.debug(f"Article updated: id={article.id}, user={current_user.username}")

            return article_to_response(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文章失败: {str(e)}"
        )


@router.delete(
    "/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文章",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_DELETE))]
)
async def delete_article(
    article_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_DELETE))
):
    """Delete article"""
    try:
        with get_db_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()

            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文章不存在: id={article_id}"
                )

            session.delete(article)
            session.commit()

            logger.info(f"Article deleted: id={article_id}, user={current_user.username}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文章失败: {str(e)}"
        )


# ========== Status Actions ==========

@router.post(
    "/articles/{article_id}/publish",
    response_model=ArticleResponse,
    summary="发布文章",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def publish_article(
    article_id: int,
    data: Optional[ArticlePublish] = None,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """
    Publish article

    - Changes status to 'published'
    - Sets published_at timestamp
    - Optionally updates summary/tags
    """
    try:
        with get_db_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()

            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文章不存在: id={article_id}"
                )

            # Validate content before publishing
            if not article.content or len(article.content.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="文章内容不能为空"
                )

            # Update status
            article.status = ArticleStatus.PUBLISHED

            # Set published_at only on first publish
            if not article.published_at:
                article.published_at = datetime.utcnow()

            # Update optional fields if provided
            if data:
                if data.summary is not None:
                    article.summary = data.summary
                if data.tags is not None:
                    article.tags = data.tags

            session.commit()
            session.refresh(article)

            logger.info(f"Article published: id={article.id}, user={current_user.username}")

            # TODO: Sync to vector store after publishing
            # vector_store.upsert(article.id, article.content, {...})

            return article_to_response(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发布文章失败: {str(e)}"
        )


@router.post(
    "/articles/{article_id}/archive",
    response_model=ArticleResponse,
    summary="归档文章",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_UPDATE))]
)
async def archive_article(
    article_id: int,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_UPDATE))
):
    """Archive article - Removes from public view"""
    try:
        with get_db_session() as session:
            article = session.query(Article).filter(Article.id == article_id).first()

            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文章不存在: id={article_id}"
                )

            article.status = ArticleStatus.ARCHIVED
            session.commit()
            session.refresh(article)

            logger.info(f"Article archived: id={article.id}, user={current_user.username}")

            # TODO: Remove from vector store
            # vector_store.delete(article.id)

            return article_to_response(article)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to archive article: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归档文章失败: {str(e)}"
        )


# ========== Semantic Search ==========

@router.get(
    "/articles/search",
    response_model=ArticleSearchResponse,
    summary="语义搜索文章",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_READ))]
)
async def search_articles(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    article_type: Optional[ArticleTypeEnum] = Query(None, description="文章类型"),
    limit: int = Query(5, ge=1, le=20, description="返回数量"),
):
    """
    Semantic search using vector store

    TODO: Integrate with ChromaDB vector store
    Currently falls back to keyword search
    """
    try:
        with get_db_session() as session:
            # Fallback to keyword search for now
            query = session.query(Article).filter(
                Article.status == ArticleStatus.PUBLISHED
            )

            if article_type:
                query = query.filter(Article.article_type == ArticleType(article_type.value))

            # Simple keyword match (to be replaced with vector search)
            query = query.filter(
                (Article.title.contains(q)) |
                (Article.content.contains(q)) |
                (Article.summary.contains(q))
            )

            articles = query.limit(limit).all()

            results = [
                ArticleSearchResult(
                    id=a.id,
                    title=a.title,
                    article_type=a.article_type.value if a.article_type else "",
                    summary=a.summary,
                    score=1.0  # Placeholder score
                )
                for a in articles
            ]

            return ArticleSearchResponse(
                query=q,
                results=results,
                total=len(results)
            )

    except Exception as e:
        logger.error(f"Failed to search articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索文章失败: {str(e)}"
        )


@router.get(
    "/articles/{article_id}/similar",
    response_model=ArticleSearchResponse,
    summary="获取相似文章",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_READ))]
)
async def get_similar_articles(
    article_id: int,
    limit: int = Query(5, ge=1, le=10, description="返回数量"),
):
    """
    Get similar articles based on content

    TODO: Integrate with ChromaDB vector store
    Currently returns articles of same type
    """
    try:
        with get_db_session() as session:
            # Get the source article
            article = session.query(Article).filter(Article.id == article_id).first()

            if not article:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文章不存在: id={article_id}"
                )

            # Fallback: get articles of same type
            similar = session.query(Article).filter(
                Article.id != article_id,
                Article.status == ArticleStatus.PUBLISHED,
                Article.article_type == article.article_type
            ).limit(limit).all()

            results = [
                ArticleSearchResult(
                    id=a.id,
                    title=a.title,
                    article_type=a.article_type.value if a.article_type else "",
                    summary=a.summary,
                    score=0.8  # Placeholder score
                )
                for a in similar
            ]

            return ArticleSearchResponse(
                query=article.title,
                results=results,
                total=len(results)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get similar articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取相似文章失败: {str(e)}"
        )


# ========== Fetch Endpoints (网络采集) ==========

@router.get(
    "/articles/fetch/sources",
    response_model=list[ArticleFetchSource],
    summary="获取可用数据源",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def get_fetch_sources():
    """Get available fetch sources"""
    from apps.api.services.article_fetcher import get_article_fetcher_service

    try:
        service = get_article_fetcher_service()
        sources = service.get_sources()
        return [ArticleFetchSource(**s) for s in sources]
    except Exception as e:
        logger.error(f"Failed to get fetch sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据源失败: {str(e)}"
        )


@router.get(
    "/articles/fetch/progress",
    response_model=ArticleFetchProgress,
    summary="获取采集进度",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_READ))]
)
async def get_fetch_progress():
    """Get current fetch progress"""
    from apps.api.services.article_fetcher import get_article_fetcher_service

    try:
        service = get_article_fetcher_service()
        progress = service.get_progress()
        return ArticleFetchProgress(
            is_running=progress["is_running"],
            stats=ArticleFetchProgressStats(**progress["stats"]),
            items=[ArticleFetchProgressItem(**item) for item in progress["items"]]
        )
    except Exception as e:
        logger.error(f"Failed to get fetch progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取采集进度失败: {str(e)}"
        )


@router.post(
    "/articles/fetch/start",
    summary="开始采集",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def start_fetch(
    data: ArticleFetchStartRequest = ArticleFetchStartRequest(),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """Start fetching articles from external sources"""
    from apps.api.services.article_fetcher import get_article_fetcher_service

    try:
        service = get_article_fetcher_service()
        result = service.start_fetch(source_id=data.source_id, use_llm=data.use_llm)

        if result["success"]:
            logger.info(f"Article fetch started by user={current_user.username}")
            return {"message": result["message"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start fetch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动采集失败: {str(e)}"
        )


@router.post(
    "/articles/fetch/pause",
    summary="暂停采集",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def pause_fetch(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """Pause the current fetch task"""
    from apps.api.services.article_fetcher import get_article_fetcher_service

    try:
        service = get_article_fetcher_service()
        result = service.pause_fetch()

        if result["success"]:
            logger.info(f"Article fetch paused by user={current_user.username}")
            return {"message": result["message"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause fetch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"暂停采集失败: {str(e)}"
        )


@router.post(
    "/articles/fetch/retry",
    summary="重试失败项",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_CREATE))]
)
async def retry_failed(
    data: ArticleFetchRetryRequest = ArticleFetchRetryRequest(),
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_CREATE))
):
    """Retry failed fetch items"""
    from apps.api.services.article_fetcher import get_article_fetcher_service

    try:
        service = get_article_fetcher_service()
        result = service.retry_failed(urls=data.urls)

        if result["success"]:
            logger.info(f"Article fetch retry by user={current_user.username}")
            return {"message": result["message"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry fetch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重试采集失败: {str(e)}"
        )


@router.post(
    "/articles/fetch/reset",
    summary="重置进度",
    dependencies=[Depends(require_permission(PermissionEnum.CONTENT_DELETE))]
)
async def reset_progress(
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.CONTENT_DELETE))
):
    """Reset all fetch progress"""
    from apps.api.services.article_fetcher import get_article_fetcher_service

    try:
        service = get_article_fetcher_service()
        result = service.reset_progress()

        if result["success"]:
            logger.info(f"Article fetch progress reset by user={current_user.username}")
            return {"message": result["message"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset fetch progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置进度失败: {str(e)}"
        )
