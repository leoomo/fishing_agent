#!/usr/bin/env python3
"""
FastAPI 后端入口 - 智能钓鱼助手 API
"""
import os
import sys
import warnings
from dotenv import load_dotenv

# 抑制警告
warnings.filterwarnings("ignore", message="LangSmith now uses UUID v7")

# 加载环境变量
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
