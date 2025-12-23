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

# 设置分类日志
if os.getenv("LOG_TO_FILE", "true").lower() == "true":
    # 导入轮转文件处理器
    from logging.handlers import RotatingFileHandler

    # 创建logs目录结构
    log_dir = "logs"
    os.makedirs(f"{log_dir}/api", exist_ok=True)
    os.makedirs(f"{log_dir}/agent", exist_ok=True)
    os.makedirs(f"{log_dir}/crawler", exist_ok=True)

    # 通用格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 1. API主应用日志
    api_app_handler = RotatingFileHandler(
        'logs/api/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    api_app_handler.setFormatter(formatter)
    logging.getLogger('apps.api').addHandler(api_app_handler)

    # 2. API认证日志
    api_auth_handler = RotatingFileHandler(
        'logs/api/auth.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    api_auth_handler.setFormatter(formatter)
    logging.getLogger('apps.api.auth').addHandler(api_auth_handler)
    logging.getLogger('apps.api.middleware').addHandler(api_auth_handler)

    # 3. OCR服务日志
    ocr_handler = RotatingFileHandler(
        'logs/api/ocr.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    ocr_handler.setFormatter(formatter)
    logging.getLogger('apps.api.services.ocr').addHandler(ocr_handler)

    # 4. Agent核心日志
    agent_fishing_handler = RotatingFileHandler(
        'logs/agent/fishing.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    agent_fishing_handler.setFormatter(formatter)
    logging.getLogger('packages.agent_fishing.core').addHandler(agent_fishing_handler)
    logging.getLogger('packages.agent_fishing.utils').addHandler(agent_fishing_handler)

    # 5. Agent工具日志
    agent_tools_handler = RotatingFileHandler(
        'logs/agent/tools.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    agent_tools_handler.setFormatter(formatter)
    logging.getLogger('packages.agent_fishing.tools').addHandler(agent_tools_handler)

    # 6. 数据采集RPA日志
    crawler_handler = RotatingFileHandler(
        'logs/crawler/rpa.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    crawler_handler.setFormatter(formatter)
    logging.getLogger('packages.agent_fishing.tools.crawler').addHandler(crawler_handler)

    # 7. 默认日志（其他未分类的日志）
    default_handler = RotatingFileHandler(
        'logs/api/app.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    default_handler.setFormatter(formatter)
    logging.getLogger().addHandler(default_handler)

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
        from packages.scraper.scheduler.workflow_scheduler import WorkflowScheduler
        from packages.scraper.executor.task_queue import configure_database, initialize_task_queue
        from packages.agent_fishing.tools.lure.database import get_db
        from packages.agent_fishing.tools.lure.orm.session import init_db
        from packages.agent_fishing.tools.lure.models.base import Base
        import threading

        # Import PendingEquipment model BEFORE init_db so its table gets created
        from packages.agent_equipment_import.models.pending import PendingEquipment

        # 初始化数据库并创建表
        logger.info("初始化数据库...")
        init_db(create_tables=True)
        logger.info("数据库表创建完成")

        # 配置 scraper 包的数据库连接（依赖注入）
        configure_database(get_db)

        # 初始化工作流调度器（传入 get_db 函数）
        workflow_scheduler = WorkflowScheduler(scheduler, get_db)
        workflow_scheduler.load_schedules_from_db()
        logger.info("工作流调度器初始化完成")

        # 初始化爬虫任务队列
        logger.info("初始化爬虫任务队列...")
        max_workers = int(os.getenv("CRAWLER_WORKERS", "3"))
        task_queue = initialize_task_queue(mode="thread", max_workers=max_workers)

        # 启动任务队列工作线程
        worker_thread = threading.Thread(
            target=task_queue.start_worker_loop,
            daemon=True,
            name="crawler-worker"
        )
        worker_thread.start()
        logger.info(f"爬虫任务队列已启动 (模式=thread, 工作器={max_workers})")

    except Exception as e:
        logger.error(f"工作流调度器初始化失败: {e}")

    yield

    # 关闭时清理
    logger.info("正在关闭应用...")

    # 关闭任务队列
    try:
        from packages.scraper.executor.task_queue import shutdown_task_queue
        logger.info("正在关闭爬虫任务队列...")
        shutdown_task_queue(wait=True, timeout=30)
        logger.info("爬虫任务队列已关闭")
    except Exception as e:
        logger.error(f"关闭爬虫任务队列失败: {e}")

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
from .routes.chat import router as chat_router
from .routes.equipment_admin import router as equipment_admin_router
from .routes.user_admin import router as user_admin_router
from .routes.import_export import router as import_export_router
from .routes.crawler import router as crawler_router
from .routes.monitor import router as monitor_router
from .routes.analytics import router as analytics_router
from .routes.config import router as config_router
from .routes.ocr import router as ocr_router
from .routes.worker import router as worker_router
from .middleware import install_api_logging_middleware

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
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])  # Mobile app chat adapter

# Phase 3 管理模块路由
app.include_router(equipment_admin_router, prefix="/api/v1/admin", tags=["equipment-admin"])
app.include_router(user_admin_router, prefix="/api/v1/admin", tags=["user-admin"])
app.include_router(import_export_router, prefix="/api/v1/admin/import-export", tags=["import-export"])

# Phase 4 数据采集和监控模块路由
app.include_router(crawler_router, prefix="/api/v1/admin/crawler", tags=["crawler"])
app.include_router(monitor_router, prefix="/api/v1/admin/monitor", tags=["monitor"])

# Phase 5 数据分析和配置管理模块路由
app.include_router(analytics_router, prefix="/api/v1/admin/analytics", tags=["analytics"])
app.include_router(config_router, prefix="/api/v1/admin/config", tags=["config"])

# OCR 图片表格识别路由
app.include_router(ocr_router, prefix="/api/v1/ocr", tags=["ocr"])

# 分布式 Worker API 路由
app.include_router(worker_router, prefix="/api/v1/worker", tags=["worker"])


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
