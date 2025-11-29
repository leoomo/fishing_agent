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

app = FastAPI(
    title="智能钓鱼助手 API",
    version="3.1.0",
    description="基于 LangChain 的智能钓鱼助手 REST API"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(fishing_router, prefix="/api/v1/fishing", tags=["fishing"])


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "智能钓鱼助手 API",
        "version": "3.1.0",
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
