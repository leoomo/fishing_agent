# Phase 4: 爬虫 + 监控模块开发详细方案

**目标**: 实现爬虫管理和系统监控功能
**周期**: 第 6 周（5 个工作日）
**优先级**: P1（核心功能）

---

## 目标概述

构建爬虫任务管理和实时系统监控功能，提供数据采集能力和运营洞察。

**核心功能**:
- 爬虫任务管理（淘宝、京东、论坛）
- 实时任务监控（WebSocket）
- API 调用统计
- LLM Token 使用分析
- 数据库性能监控
- 错误日志查看

---

## Step 1: 爬虫管理 API（Day 1-3）

### 1.1 创建爬虫 Schema

**文件**: `apps/api/schemas/crawler.py`

**步骤**:
1. 定义爬虫相关 Schema:

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CrawlerTaskCreate(BaseModel):
    """创建爬虫任务请求"""
    task_type: str = Field(..., pattern="^(taobao|jd|forum)$", description="任务类型")
    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置（JSON）")


class CrawlerTaskResponse(BaseModel):
    """爬虫任务响应"""
    id: int
    task_type: str
    task_name: str
    status: str  # pending, running, success, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_items: int
    success_items: int
    failed_items: int
    error_message: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    result_summary: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


class CrawlerTaskListResponse(BaseModel):
    """爬虫任务列表响应"""
    total: int
    page: int
    page_size: int
    tasks: List[CrawlerTaskResponse]


class CrawlerLogResponse(BaseModel):
    """爬虫日志响应"""
    id: int
    task_id: int
    level: str  # info, warning, error
    message: str
    details: Optional[Dict[str, Any]] = None
    created_at: str


class TriggerCrawlerRequest(BaseModel):
    """触发爬虫任务请求"""
    task_type: str = Field(..., pattern="^(taobao|jd|forum)$")
    keywords: Optional[List[str]] = Field(None, description="搜索关键词列表")
    max_pages: Optional[int] = Field(5, ge=1, le=50, description="最大爬取页数")
    proxy: Optional[str] = Field(None, description="代理服务器")


class SyncStatusResponse(BaseModel):
    """数据同步状态响应"""
    last_sync_time: Optional[str] = None
    total_synced: int
    pending_sync: int
    duplicate_removed: int
    sync_errors: int
```

### 1.2 实现爬虫管理路由

**文件**: `apps/api/routes/crawler.py`

**步骤**:
1. 实现爬虫任务管理端点:

```python
from fastapi import APIRouter, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect
import asyncio
import logging
from typing import Optional
from datetime import datetime

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.crawler_repo import CrawlerRepository
from packages.agent_fishing.tools.lure.models.system import CrawlerTask

from apps.api.schemas.crawler import (
    CrawlerTaskCreate,
    CrawlerTaskResponse,
    CrawlerTaskListResponse,
    CrawlerLogResponse,
    TriggerCrawlerRequest,
    SyncStatusResponse
)
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.crawler_service import CrawlerService

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 爬虫任务管理 ==========

@router.get(
    "/tasks",
    response_model=CrawlerTaskListResponse,
    summary="查询爬虫任务列表",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤")
):
    """
    查询爬虫任务列表（分页 + 筛选）

    Returns:
        CrawlerTaskListResponse: 任务列表
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)

            filters = {}
            if task_type:
                filters['task_type'] = task_type
            if status:
                filters['status'] = status

            tasks = repo.get_all(
                filters=filters,
                limit=page_size,
                offset=(page - 1) * page_size,
                order_by='created_at DESC'
            )

            total = repo.count(filters=filters)

            return CrawlerTaskListResponse(
                total=total,
                page=page,
                page_size=page_size,
                tasks=[_build_task_response(task) for task in tasks]
            )

    except Exception as e:
        logger.error(f"查询爬虫任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get(
    "/tasks/{task_id}",
    response_model=CrawlerTaskResponse,
    summary="获取爬虫任务详情",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def get_task(task_id: int):
    """
    获取爬虫任务详情

    Args:
        task_id: 任务ID

    Returns:
        CrawlerTaskResponse: 任务详情

    Raises:
        HTTPException: 任务不存在
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(
                    status_code=404,
                    detail=f"任务不存在: task_id={task_id}"
                )

            return _build_task_response(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post(
    "/tasks/trigger",
    response_model=CrawlerTaskResponse,
    summary="手动触发爬虫任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))]
)
async def trigger_crawler(request: TriggerCrawlerRequest):
    """
    手动触发爬虫任务

    Args:
        request: 触发请求（包含任务类型、关键词、配置）

    Returns:
        CrawlerTaskResponse: 创建的任务信息
    """
    try:
        crawler_service = CrawlerService()

        # 创建任务
        task = crawler_service.trigger_crawler(
            task_type=request.task_type,
            keywords=request.keywords,
            max_pages=request.max_pages,
            proxy=request.proxy
        )

        logger.info(
            f"爬虫任务已触发: task_id={task.id}, "
            f"type={request.task_type}"
        )

        return _build_task_response(task)

    except Exception as e:
        logger.error(f"触发爬虫任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")


@router.post(
    "/tasks/{task_id}/retry",
    response_model=CrawlerTaskResponse,
    summary="重试失败任务",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_EXECUTE))]
)
async def retry_task(task_id: int):
    """
    重试失败的爬虫任务

    Args:
        task_id: 任务ID

    Returns:
        CrawlerTaskResponse: 新任务信息

    Raises:
        HTTPException: 任务不存在或状态不是 failed
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status != 'failed':
                raise HTTPException(
                    status_code=400,
                    detail=f"只能重试失败任务，当前状态: {task.status}"
                )

            # 重试任务
            crawler_service = CrawlerService()
            new_task = crawler_service.retry_task(task)

            logger.info(f"任务重试: 原task_id={task_id}, 新task_id={new_task.id}")

            return _build_task_response(new_task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重试失败: {str(e)}")


@router.get(
    "/tasks/{task_id}/logs",
    response_model=List[CrawlerLogResponse],
    summary="获取任务日志",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def get_task_logs(
    task_id: int,
    level: Optional[str] = Query(None, description="日志级别过滤")
):
    """
    获取爬虫任务日志

    Args:
        task_id: 任务ID
        level: 日志级别（info/warning/error）

    Returns:
        List[CrawlerLogResponse]: 日志列表
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)

            filters = {'task_id': task_id}
            if level:
                filters['level'] = level

            logs = repo.get_task_logs(task_id, level=level)

            return [
                CrawlerLogResponse(
                    id=log.id,
                    task_id=log.task_id,
                    level=log.level,
                    message=log.message,
                    details=log.details,
                    created_at=log.created_at.isoformat()
                )
                for log in logs
            ]

    except Exception as e:
        logger.error(f"获取任务日志失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="删除任务记录",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_DELETE))]
)
async def delete_task(task_id: int):
    """
    删除爬虫任务记录

    Args:
        task_id: 任务ID

    Raises:
        HTTPException: 任务不存在或正在运行
    """
    try:
        with get_db_session() as session:
            repo = CrawlerRepository(session)
            task = repo.get(task_id)

            if not task:
                raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

            if task.status == 'running':
                raise HTTPException(
                    status_code=400,
                    detail="无法删除正在运行的任务"
                )

            repo.delete(task_id)

            logger.info(f"任务记录已删除: task_id={task_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get(
    "/sync-status",
    response_model=SyncStatusResponse,
    summary="获取数据同步状态",
    dependencies=[Depends(require_permission(PermissionEnum.CRAWLER_READ))]
)
async def get_sync_status():
    """
    获取数据同步状态

    Returns:
        SyncStatusResponse: 同步状态统计
    """
    try:
        crawler_service = CrawlerService()
        status = crawler_service.get_sync_status()

        return SyncStatusResponse(**status)

    except Exception as e:
        logger.error(f"获取同步状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ========== WebSocket 实时监控 ==========

@router.websocket("/ws/crawler/{task_id}")
async def websocket_crawler_progress(websocket: WebSocket, task_id: int):
    """
    WebSocket 实时推送爬虫任务进度

    Args:
        websocket: WebSocket 连接
        task_id: 任务ID
    """
    await websocket.accept()

    try:
        logger.info(f"WebSocket 连接建立: task_id={task_id}")

        while True:
            # 查询任务状态
            with get_db_session() as session:
                repo = CrawlerRepository(session)
                task = repo.get(task_id)

                if not task:
                    await websocket.send_json({
                        "error": f"任务不存在: {task_id}"
                    })
                    break

                # 推送进度
                await websocket.send_json({
                    "task_id": task_id,
                    "status": task.status,
                    "progress": f"{task.success_items}/{task.total_items}",
                    "success_items": task.success_items,
                    "failed_items": task.failed_items,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # 任务结束时断开连接
                if task.status in ['success', 'failed']:
                    logger.info(
                        f"任务已完成，关闭 WebSocket: task_id={task_id}, "
                        f"status={task.status}"
                    )
                    break

            # 每秒推送一次
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"WebSocket 客户端断开连接: task_id={task_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# ========== 辅助函数 ==========

def _build_task_response(task: CrawlerTask) -> CrawlerTaskResponse:
    """构造任务响应对象"""
    import json

    return CrawlerTaskResponse(
        id=task.id,
        task_type=task.task_type,
        task_name=task.task_name,
        status=task.status,
        start_time=task.start_time.isoformat() if task.start_time else None,
        end_time=task.end_time.isoformat() if task.end_time else None,
        total_items=task.total_items,
        success_items=task.success_items,
        failed_items=task.failed_items,
        error_message=task.error_message,
        config=json.loads(task.config) if task.config else None,
        result_summary=json.loads(task.result_summary) if task.result_summary else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )
```

### 1.3 实现爬虫服务

**文件**: `apps/api/services/crawler_service.py`

**步骤**:
1. 实现爬虫任务管理逻辑:

```python
import subprocess
import json
import logging
from typing import List, Optional, Dict
from datetime import datetime

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.crawler_repo import CrawlerRepository
from packages.agent_fishing.tools.lure.models.system import CrawlerTask, CrawlerLog

logger = logging.getLogger(__name__)


class CrawlerService:
    """爬虫服务"""

    def trigger_crawler(
        self,
        task_type: str,
        keywords: Optional[List[str]] = None,
        max_pages: int = 5,
        proxy: Optional[str] = None
    ) -> CrawlerTask:
        """
        触发爬虫任务

        Args:
            task_type: 任务类型（taobao/jd/forum）
            keywords: 搜索关键词
            max_pages: 最大爬取页数
            proxy: 代理服务器

        Returns:
            CrawlerTask: 创建的任务对象
        """
        with get_db_session() as session:
            repo = CrawlerRepository(session)

            # 构造任务配置
            config = {
                "keywords": keywords or ["路亚竿", "渔轮"],
                "max_pages": max_pages,
                "proxy": proxy
            }

            # 创建任务
            task = CrawlerTask(
                task_type=task_type,
                task_name=f"{task_type}爬虫 - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                status='pending',
                config=json.dumps(config, ensure_ascii=False),
                total_items=0,
                success_items=0,
                failed_items=0
            )

            session.add(task)
            session.commit()
            session.refresh(task)

            logger.info(f"爬虫任务已创建: task_id={task.id}, type={task_type}")

            # 异步启动爬虫（后台运行）
            self._start_crawler_process(task.id, task_type, config)

            return task

    def _start_crawler_process(
        self,
        task_id: int,
        task_type: str,
        config: Dict
    ):
        """
        启动爬虫进程（后台运行）

        Args:
            task_id: 任务ID
            task_type: 任务类型
            config: 任务配置
        """
        try:
            # 构造爬虫命令
            cmd = [
                "python",
                "run_crawler.py",
                "--type", task_type,
                "--task-id", str(task_id),
                "--keywords", ",".join(config.get("keywords", [])),
                "--max-pages", str(config.get("max_pages", 5))
            ]

            if config.get("proxy"):
                cmd.extend(["--proxy", config["proxy"]])

            # 后台启动爬虫进程
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # 独立会话，不受父进程影响
            )

            logger.info(f"爬虫进程已启动: task_id={task_id}, cmd={' '.join(cmd)}")

        except Exception as e:
            logger.error(f"启动爬虫进程失败: {e}", exc_info=True)

            # 更新任务状态为失败
            with get_db_session() as session:
                repo = CrawlerRepository(session)
                repo.update(task_id, {
                    "status": "failed",
                    "error_message": f"启动失败: {str(e)}"
                })

    def retry_task(self, task: CrawlerTask) -> CrawlerTask:
        """
        重试失败任务

        Args:
            task: 失败的任务

        Returns:
            CrawlerTask: 新创建的任务
        """
        # 提取原任务配置
        config = json.loads(task.config) if task.config else {}

        # 创建新任务
        return self.trigger_crawler(
            task_type=task.task_type,
            keywords=config.get("keywords"),
            max_pages=config.get("max_pages", 5),
            proxy=config.get("proxy")
        )

    def get_sync_status(self) -> Dict:
        """
        获取数据同步状态

        Returns:
            dict: 同步状态统计
        """
        with get_db_session() as session:
            repo = CrawlerRepository(session)

            # 统计最近成功任务
            recent_success_tasks = repo.get_all(
                filters={"status": "success"},
                limit=10,
                order_by="end_time DESC"
            )

            last_sync_time = None
            if recent_success_tasks:
                last_sync_time = recent_success_tasks[0].end_time.isoformat()

            # 统计数据
            total_synced = sum(task.success_items for task in recent_success_tasks)
            sync_errors = sum(task.failed_items for task in recent_success_tasks)

            # TODO: 实现去重统计和待同步统计
            duplicate_removed = 0
            pending_sync = 0

            return {
                "last_sync_time": last_sync_time,
                "total_synced": total_synced,
                "pending_sync": pending_sync,
                "duplicate_removed": duplicate_removed,
                "sync_errors": sync_errors
            }
```

---

## Step 2: 系统监控 API（Day 4-5）

### 2.1 创建监控 Schema

**文件**: `apps/api/schemas/monitor.py`

**步骤**:
1. 定义监控相关 Schema:

```python
from typing import List, Dict, Optional
from pydantic import BaseModel


class APIStatsResponse(BaseModel):
    """API 统计响应"""
    total_calls: int
    avg_response_time: float
    error_rate: float
    top_endpoints: List[Dict[str, any]]  # [{endpoint, count, avg_time}]


class LLMStatsResponse(BaseModel):
    """LLM 统计响应"""
    total_calls: int
    total_tokens: int
    total_cost: float
    avg_response_time: float
    success_rate: float
    by_provider: Dict[str, Dict]  # {provider: {calls, tokens, cost}}


class DBPerformanceResponse(BaseModel):
    """数据库性能响应"""
    avg_query_time: float
    slow_queries_count: int
    connection_pool_size: int
    active_connections: int
    table_sizes: Dict[str, int]  # {table_name: size_mb}


class SystemHealthResponse(BaseModel):
    """系统健康检查响应"""
    status: str  # healthy, degraded, unhealthy
    api_status: str
    db_status: str
    llm_status: str
    uptime_seconds: float
```

### 2.2 实现监控路由

**文件**: `apps/api/routes/monitor.py`

**步骤**:
1. 实现监控统计端点:

```python
from fastapi import APIRouter, HTTPException, Query, Depends, WebSocket
import logging
from typing import Optional
from datetime import datetime, timedelta

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from sqlalchemy import func

from apps.api.schemas.monitor import (
    APIStatsResponse,
    LLMStatsResponse,
    DBPerformanceResponse,
    SystemHealthResponse
)
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum
from apps.api.services.monitor_service import MonitorService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/api-stats",
    response_model=APIStatsResponse,
    summary="API 调用统计",
    dependencies=[Depends(require_permission(PermissionEnum.MONITOR_READ))]
)
async def get_api_stats(
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）")
):
    """
    获取 API 调用统计

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        APIStatsResponse: API 统计数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_api_stats(
            start_date=start_date,
            end_date=end_date
        )

        return APIStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取 API 统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/llm-stats",
    response_model=LLMStatsResponse,
    summary="LLM 使用统计",
    dependencies=[Depends(require_permission(PermissionEnum.MONITOR_READ))]
)
async def get_llm_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    获取 LLM 使用统计

    Returns:
        LLMStatsResponse: LLM 统计数据
    """
    try:
        monitor_service = MonitorService()

        stats = monitor_service.get_llm_stats(
            start_date=start_date,
            end_date=end_date
        )

        return LLMStatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取 LLM 统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/db-performance",
    response_model=DBPerformanceResponse,
    summary="数据库性能监控",
    dependencies=[Depends(require_permission(PermissionEnum.MONITOR_READ))]
)
async def get_db_performance():
    """
    获取数据库性能指标

    Returns:
        DBPerformanceResponse: 数据库性能数据
    """
    try:
        monitor_service = MonitorService()
        performance = monitor_service.get_db_performance()

        return DBPerformanceResponse(**performance)

    except Exception as e:
        logger.error(f"获取数据库性能失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get(
    "/health-check",
    response_model=SystemHealthResponse,
    summary="系统健康检查"
)
async def health_check():
    """
    系统健康检查（无需认证）

    Returns:
        SystemHealthResponse: 健康状态
    """
    try:
        monitor_service = MonitorService()
        health = monitor_service.check_system_health()

        return SystemHealthResponse(**health)

    except Exception as e:
        logger.error(f"健康检查失败: {e}", exc_info=True)
        return SystemHealthResponse(
            status="unhealthy",
            api_status="unknown",
            db_status="unknown",
            llm_status="unknown",
            uptime_seconds=0
        )


@router.websocket("/ws/realtime-stats")
async def websocket_realtime_stats(websocket: WebSocket):
    """
    WebSocket 实时统计推送

    推送数据:
    - API 调用量（每秒）
    - LLM Token 使用（每分钟）
    - 错误率
    """
    await websocket.accept()

    try:
        logger.info("实时监控 WebSocket 连接建立")

        monitor_service = MonitorService()

        while True:
            # 获取实时统计
            stats = monitor_service.get_realtime_stats()

            # 推送数据
            await websocket.send_json({
                "timestamp": datetime.utcnow().isoformat(),
                **stats
            })

            # 每5秒推送一次
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("实时监控 WebSocket 客户端断开")
    except Exception as e:
        logger.error(f"实时监控 WebSocket 错误: {e}", exc_info=True)
    finally:
        try:
            await websocket.close()
        except:
            pass
```

### 2.3 实现监控服务

**文件**: `apps/api/services/monitor_service.py`

**步骤**:
1. 实现监控统计逻辑:

```python
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import APILog, LLMLog

logger = logging.getLogger(__name__)


class MonitorService:
    """监控服务"""

    def get_api_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取 API 调用统计

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            dict: API 统计数据
        """
        with get_db_session() as session:
            query = session.query(APILog)

            # 日期过滤
            if start_date:
                query = query.filter(APILog.timestamp >= start_date)
            if end_date:
                query = query.filter(APILog.timestamp <= end_date)

            # 总调用数
            total_calls = query.count()

            # 平均响应时间
            avg_response_time = session.query(
                func.avg(APILog.response_time)
            ).filter(
                APILog.timestamp >= (start_date or datetime.now() - timedelta(days=7))
            ).scalar() or 0

            # 错误率
            error_count = query.filter(APILog.status_code >= 400).count()
            error_rate = (error_count / total_calls * 100) if total_calls > 0 else 0

            # Top 端点
            top_endpoints = session.query(
                APILog.endpoint,
                func.count(APILog.id).label('count'),
                func.avg(APILog.response_time).label('avg_time')
            ).filter(
                APILog.timestamp >= (start_date or datetime.now() - timedelta(days=7))
            ).group_by(
                APILog.endpoint
            ).order_by(
                func.count(APILog.id).desc()
            ).limit(10).all()

            return {
                "total_calls": total_calls,
                "avg_response_time": round(avg_response_time, 2),
                "error_rate": round(error_rate, 2),
                "top_endpoints": [
                    {
                        "endpoint": ep.endpoint,
                        "count": ep.count,
                        "avg_time": round(ep.avg_time, 2)
                    }
                    for ep in top_endpoints
                ]
            }

    def get_llm_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        获取 LLM 使用统计

        Returns:
            dict: LLM 统计数据
        """
        with get_db_session() as session:
            query = session.query(LLMLog)

            # 日期过滤
            if start_date:
                query = query.filter(LLMLog.timestamp >= start_date)
            if end_date:
                query = query.filter(LLMLog.timestamp <= end_date)

            # 总调用数
            total_calls = query.count()

            # 总 Token 数
            total_tokens = session.query(
                func.sum(LLMLog.total_tokens)
            ).filter(
                LLMLog.timestamp >= (start_date or datetime.now() - timedelta(days=7))
            ).scalar() or 0

            # 总成本
            total_cost = session.query(
                func.sum(LLMLog.cost)
            ).filter(
                LLMLog.timestamp >= (start_date or datetime.now() - timedelta(days=7))
            ).scalar() or 0

            # 平均响应时间
            avg_response_time = session.query(
                func.avg(LLMLog.response_time)
            ).filter(
                LLMLog.timestamp >= (start_date or datetime.now() - timedelta(days=7))
            ).scalar() or 0

            # 成功率
            success_count = query.filter(LLMLog.success == True).count()
            success_rate = (success_count / total_calls * 100) if total_calls > 0 else 0

            # 按提供商统计
            by_provider = {}
            providers = session.query(LLMLog.model_provider).distinct().all()

            for (provider,) in providers:
                provider_logs = query.filter(LLMLog.model_provider == provider)

                by_provider[provider] = {
                    "calls": provider_logs.count(),
                    "tokens": session.query(
                        func.sum(LLMLog.total_tokens)
                    ).filter(
                        LLMLog.model_provider == provider,
                        LLMLog.timestamp >= (start_date or datetime.now() - timedelta(days=7))
                    ).scalar() or 0,
                    "cost": session.query(
                        func.sum(LLMLog.cost)
                    ).filter(
                        LLMLog.model_provider == provider,
                        LLMLog.timestamp >= (start_date or datetime.now() - timedelta(days=7))
                    ).scalar() or 0
                }

            return {
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 2),
                "avg_response_time": round(avg_response_time, 2),
                "success_rate": round(success_rate, 2),
                "by_provider": by_provider
            }

    def get_db_performance(self) -> Dict:
        """
        获取数据库性能指标

        Returns:
            dict: 数据库性能数据
        """
        # TODO: 实现数据库性能监控
        # - 查询执行时间统计
        # - 慢查询检测
        # - 连接池状态
        # - 表大小统计

        return {
            "avg_query_time": 0.0,
            "slow_queries_count": 0,
            "connection_pool_size": 10,
            "active_connections": 1,
            "table_sizes": {}
        }

    def check_system_health(self) -> Dict:
        """
        系统健康检查

        Returns:
            dict: 健康状态
        """
        import time

        # TODO: 实现完整的健康检查
        # - API 响应正常
        # - 数据库连接正常
        # - LLM 调用正常

        return {
            "status": "healthy",
            "api_status": "healthy",
            "db_status": "healthy",
            "llm_status": "healthy",
            "uptime_seconds": time.time()
        }

    def get_realtime_stats(self) -> Dict:
        """
        获取实时统计数据（最近1分钟）

        Returns:
            dict: 实时统计
        """
        one_minute_ago = datetime.now() - timedelta(minutes=1)

        with get_db_session() as session:
            # 最近1分钟 API 调用量
            api_calls = session.query(APILog).filter(
                APILog.timestamp >= one_minute_ago
            ).count()

            # 最近1分钟错误数
            api_errors = session.query(APILog).filter(
                APILog.timestamp >= one_minute_ago,
                APILog.status_code >= 400
            ).count()

            # 最近1分钟 LLM 调用
            llm_calls = session.query(LLMLog).filter(
                LLMLog.timestamp >= one_minute_ago
            ).count()

            # 最近1分钟 Token 消耗
            llm_tokens = session.query(
                func.sum(LLMLog.total_tokens)
            ).filter(
                LLMLog.timestamp >= one_minute_ago
            ).scalar() or 0

            return {
                "api_calls_per_minute": api_calls,
                "api_errors_per_minute": api_errors,
                "llm_calls_per_minute": llm_calls,
                "llm_tokens_per_minute": llm_tokens
            }
```

---

## 测试用例

### 爬虫管理测试

```bash
# 测试触发爬虫
curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/trigger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "taobao",
    "keywords": ["路亚竿"],
    "max_pages": 3
  }'

# 测试 WebSocket 监控
websocat ws://localhost:8000/api/v1/admin/crawler/ws/crawler/1
```

### 监控测试

```bash
# 测试 API 统计
curl "http://localhost:8000/api/v1/admin/monitor/api-stats" \
  -H "Authorization: Bearer $TOKEN"

# 测试健康检查
curl "http://localhost:8000/api/v1/admin/monitor/health-check"
```

---

## 注意事项

### 1. WebSocket 连接管理

⚠️ **避免连接泄漏**:
```python
# ✅ 正确处理 WebSocket
try:
    await websocket.accept()
    # ... 业务逻辑
finally:
    try:
        await websocket.close()
    except:
        pass
```

### 2. 爬虫进程管理

⚠️ **后台进程独立会话**:
```python
# ✅ 使用 start_new_session 避免父进程退出时杀死子进程
subprocess.Popen(
    cmd,
    start_new_session=True
)

# ❌ 默认会话
subprocess.Popen(cmd)  # 父进程退出时子进程也会被杀死
```

### 3. 实时统计性能

🚀 **缓存热数据**:
```python
# 可选：使用 Redis 缓存最近1分钟统计
# 避免每次 WebSocket 推送都查询数据库
```

---

## 验收标准

### 必须完成

- ✅ 爬虫任务 CRUD 端点
- ✅ 任务触发和重试功能
- ✅ WebSocket 实时进度推送
- ✅ API 统计端点
- ✅ LLM 统计端点
- ✅ 健康检查端点
- ✅ 实时监控 WebSocket

### 可选优化

- 🔧 慢查询日志记录
- 🔧 告警通知（钉钉/企业微信）
- 🔧 数据导出（监控报表）

---

## 下一步

完成 Phase 4 后，进入 **Phase 5: 数据分析 + 配置管理**
