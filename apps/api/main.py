#!/usr/bin/env python3
"""
FastAPI 后端入口 - 智能钓鱼助手 API
"""
import os
import sys
import warnings
import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 抑制警告
warnings.filterwarnings("ignore", message="LangSmith now uses UUID v7")

# 加载环境变量
load_dotenv()

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = None
workflow_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global scheduler, workflow_scheduler

    # 启动时初始化
    logger.info("正在启动应用...")

    # 创建并启动调度器
    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("APScheduler 已启动")

    # 初始化工作流调度器
    try:
        from packages.agent_fishing.tools.crawler.scheduler.workflow_scheduler import WorkflowScheduler
        workflow_scheduler = WorkflowScheduler(scheduler)
        workflow_scheduler.load_schedules_from_db()
        logger.info("工作流调度器初始化完成")
    except Exception as e:
        logger.error(f"工作流调度器初始化失败: {e}")

    yield

    # 关闭时清理
    logger.info("正在关闭应用...")

    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler 已关闭")


app = FastAPI(
    title="智能钓鱼助手 API",
    version="5.0.0",
    description="基于 LangChain 的智能钓鱼助手 REST API - 支持数据分析和配置管理",
    lifespan=lifespan
)
from .routes import fishing_router
from .routes.user_equipment import router as user_equipment_router
from .routes.auth import router as auth_router
from .routes.equipment_admin import router as equipment_admin_router
from .routes.user_admin import router as user_admin_router
from .routes.import_export import router as import_export_router
from .routes.crawler import router as crawler_router
from .routes.monitor import router as monitor_router
from .routes.analytics import router as analytics_router
from .routes.config import router as config_router
from .middleware import install_api_logging_middleware

app = FastAPI(
    title="智能钓鱼助手 API",
    version="5.0.0",
    description="基于 LangChain 的智能钓鱼助手 REST API - 支持数据分析和配置管理"
)

# GZip 压缩中间件（响应大于 500 字节时压缩）
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API logging middleware
install_api_logging_middleware(
    app,
    excluded_paths=["/health", "/", "/docs", "/redoc", "/openapi.json"]
)

# 注册路由
app.include_router(fishing_router, prefix="/api/v1/fishing", tags=["fishing"])
app.include_router(user_equipment_router, prefix="/api/v1/user-equipment", tags=["user-equipment"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# Phase 3 管理模块路由
app.include_router(equipment_admin_router, prefix="/api/v1/admin", tags=["equipment-admin"])
app.include_router(user_admin_router, prefix="/api/v1/admin", tags=["user-admin"])
app.include_router(import_export_router, prefix="/api/v1/admin/import-export", tags=["import-export"])

# Phase 4 爬虫和监控模块路由
app.include_router(crawler_router, prefix="/api/v1/admin/crawler", tags=["crawler"])
app.include_router(monitor_router, prefix="/api/v1/admin/monitor", tags=["monitor"])

# Phase 5 数据分析和配置管理模块路由
app.include_router(analytics_router, prefix="/api/v1/admin/analytics", tags=["analytics"])
app.include_router(config_router, prefix="/api/v1/admin/config", tags=["config"])


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "智能钓鱼助手 API",
        "version": "5.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


def main():
    """启动服务器"""
    import uvicorn
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
