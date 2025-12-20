"""
Master Service Application

分布式爬虫Master服务FastAPI应用
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..database import CrawlerDatabase
from .routes import node_router, task_router, image_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("Initializing crawler database...")
    db = CrawlerDatabase()
    db.create_tables()
    logger.info("Crawler database initialized")

    yield

    # 关闭时清理
    logger.info("Shutting down Master service...")


def create_app() -> FastAPI:
    """
    创建Master服务FastAPI应用

    Returns:
        FastAPI: 配置好的应用实例
    """
    app = FastAPI(
        title="Crawler Master Service",
        description="分布式爬虫Master服务 - 节点管理、任务调度、图片处理",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(node_router)
    app.include_router(task_router)
    app.include_router(image_router)

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "crawler-master"}

    @app.get("/")
    async def root():
        return {
            "service": "Crawler Master Service",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return app


# 创建默认应用实例
app = create_app()
