# 工作流系统开发方案 - 阶段2：工作流管理API

**目标**: 实现工作流模板CRUD、定时调度、执行状态查询API

**预估工作量**: 3-4天

**前置条件**:
- 阶段1完成（工作流引擎可用）
- API服务器正常运行
- JWT认证系统就绪

---

## 一、API Schema设计

### 1.1 工作流模板Schema

**文件**: `apps/api/schemas/crawler.py`（在现有文件中扩展）

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ===== 工作流模板相关 Schema =====

class WorkflowTemplateCreate(BaseModel):
    """创建工作流模板请求"""
    name: str = Field(..., max_length=200, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_json: str = Field(..., description="工作流定义JSON字符串")
    category: Optional[str] = Field(None, max_length=50, description="模板分类（shop/keyword/sync）")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "淘宝店铺商品抓取",
                "description": "从店铺URL抓取所有商品",
                "template_json": '{"steps": [...]}',
                "category": "shop"
            }
        }

class WorkflowTemplateUpdate(BaseModel):
    """更新工作流模板请求"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    template_json: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)

class WorkflowTemplateResponse(BaseModel):
    """工作流模板响应"""
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    is_system: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    usage_count: int

    class Config:
        from_attributes = True

class WorkflowTemplateDetail(WorkflowTemplateResponse):
    """工作流模板详情（含JSON）"""
    template_json: str

class WorkflowTemplateListResponse(BaseModel):
    """工作流模板列表响应"""
    total: int
    items: List[WorkflowTemplateResponse]

# ===== 工作流执行相关 Schema =====

class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    template_id: int = Field(..., description="工作流模板ID")
    params: Dict[str, Any] = Field(..., description="执行参数（替换模板中的{{变量}}）")

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": 1,
                "params": {
                    "shop_url": "https://shop.taobao.com/xxxxx",
                    "max_pages": 10
                }
            }
        }

class WorkflowExecutionResponse(BaseModel):
    """工作流执行状态响应"""
    workflow_id: str
    workflow_name: str
    status: str  # PENDING/RUNNING/SUCCESS/FAILED
    total_steps: int
    completed_steps: int
    progress_percent: int
    created_at: datetime
    tasks: Optional[List[Dict]] = None  # 步骤任务列表（可选）

class WorkflowTaskInfo(BaseModel):
    """工作流步骤任务信息"""
    id: int
    step_order: int
    task_name: str
    task_type: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    success_items: int
    failed_items: int
    error_message: Optional[str]

# ===== 定时调度相关 Schema =====

class ScheduleCreate(BaseModel):
    """创建定时调度请求"""
    name: str = Field(..., max_length=200, description="调度名称")
    template_id: int = Field(..., description="工作流模板ID")
    cron_expression: str = Field(..., max_length=100, description="Cron表达式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    config: Optional[Dict[str, Any]] = Field(None, description="执行参数（JSON）")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "每日凌晨2点抓取",
                "template_id": 1,
                "cron_expression": "0 2 * * *",
                "timezone": "Asia/Shanghai",
                "config": {
                    "shop_url": "https://shop.taobao.com/xxxxx",
                    "max_pages": 10
                }
            }
        }

class ScheduleUpdate(BaseModel):
    """更新定时调度请求"""
    name: Optional[str] = Field(None, max_length=200)
    cron_expression: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = None
    is_enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None

class ScheduleResponse(BaseModel):
    """定时调度响应"""
    id: int
    name: str
    template_id: int
    template_name: Optional[str]  # 关联的模板名称
    cron_expression: str
    timezone: str
    is_enabled: bool
    config: Optional[str]
    next_run_time: Optional[datetime]
    last_run_time: Optional[datetime]
    last_task_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class ScheduleListResponse(BaseModel):
    """定时调度列表响应"""
    total: int
    items: List[ScheduleResponse]
```

---

## 二、工作流模板API

### 2.1 扩展路由端点

**修改文件**: `apps/api/routes/crawler.py`（在现有路由中扩展）

```python
from apps.api.schemas.crawler import (
    WorkflowTemplateCreate, WorkflowTemplateUpdate, WorkflowTemplateResponse,
    WorkflowTemplateDetail, WorkflowTemplateListResponse,
    WorkflowExecuteRequest, WorkflowExecutionResponse, WorkflowTaskInfo,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse
)
from packages.agent_fishing.tools.lure.models.system import CrawlerWorkflowTemplate, CrawlerSchedule
from sqlalchemy import func

# ===== 工作流模板管理端点 =====

@router.post("/templates", response_model=WorkflowTemplateResponse)
async def create_workflow_template(
    request: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_EXECUTE"))
):
    """
    创建工作流模板

    Permissions: CRAWLER_EXECUTE
    """
    # 验证JSON格式
    try:
        workflow_def = json.loads(request.template_json)
        if 'steps' not in workflow_def:
            raise HTTPException(400, "工作流定义必须包含steps字段")
        if not isinstance(workflow_def['steps'], list):
            raise HTTPException(400, "steps字段必须是数组")
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"无效的JSON格式: {str(e)}")

    # 检查名称是否重复
    existing = db.query(CrawlerWorkflowTemplate).filter(
        CrawlerWorkflowTemplate.name == request.name
    ).first()
    if existing:
        raise HTTPException(400, f"模板名称 '{request.name}' 已存在")

    # 创建模板
    template = CrawlerWorkflowTemplate(
        name=request.name,
        description=request.description,
        template_json=request.template_json,
        category=request.category,
        created_by=current_user.user_id
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    logger.info(f"用户 {current_user.user_id} 创建工作流模板: {template.name} (ID={template.id})")

    return template

@router.get("/templates", response_model=WorkflowTemplateListResponse)
async def list_workflow_templates(
    category: Optional[str] = Query(None, description="按分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词（匹配名称或描述）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_READ"))
):
    """
    查询工作流模板列表

    Permissions: CRAWLER_READ
    """
    query = db.query(CrawlerWorkflowTemplate)

    # 筛选条件
    if category:
        query = query.filter(CrawlerWorkflowTemplate.category == category)
    if search:
        query = query.filter(
            (CrawlerWorkflowTemplate.name.like(f"%{search}%")) |
            (CrawlerWorkflowTemplate.description.like(f"%{search}%"))
        )

    # 总数
    total = query.count()

    # 分页
    items = query.order_by(CrawlerWorkflowTemplate.created_at.desc()) \
                 .offset((page - 1) * page_size) \
                 .limit(page_size) \
                 .all()

    return WorkflowTemplateListResponse(total=total, items=items)

@router.get("/templates/{template_id}", response_model=WorkflowTemplateDetail)
async def get_workflow_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_READ"))
):
    """
    获取工作流模板详情（含JSON）

    Permissions: CRAWLER_READ
    """
    template = db.query(CrawlerWorkflowTemplate).filter(
        CrawlerWorkflowTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(404, f"工作流模板 {template_id} 不存在")

    return template

@router.put("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def update_workflow_template(
    template_id: int,
    request: WorkflowTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_EXECUTE"))
):
    """
    更新工作流模板

    Permissions: CRAWLER_EXECUTE
    """
    template = db.query(CrawlerWorkflowTemplate).filter(
        CrawlerWorkflowTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(404, f"工作流模板 {template_id} 不存在")

    # 系统模板不允许修改
    if template.is_system:
        raise HTTPException(403, "系统内置模板不允许修改")

    # 更新字段
    if request.name is not None:
        # 检查名称是否重复
        existing = db.query(CrawlerWorkflowTemplate).filter(
            CrawlerWorkflowTemplate.name == request.name,
            CrawlerWorkflowTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(400, f"模板名称 '{request.name}' 已存在")
        template.name = request.name

    if request.description is not None:
        template.description = request.description

    if request.template_json is not None:
        # 验证JSON
        try:
            workflow_def = json.loads(request.template_json)
            if 'steps' not in workflow_def:
                raise HTTPException(400, "工作流定义必须包含steps字段")
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"无效的JSON格式: {str(e)}")
        template.template_json = request.template_json

    if request.category is not None:
        template.category = request.category

    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)

    logger.info(f"用户 {current_user.user_id} 更新工作流模板: {template.name} (ID={template.id})")

    return template

@router.delete("/templates/{template_id}", status_code=204)
async def delete_workflow_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_DELETE"))
):
    """
    删除工作流模板

    Permissions: CRAWLER_DELETE
    """
    template = db.query(CrawlerWorkflowTemplate).filter(
        CrawlerWorkflowTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(404, f"工作流模板 {template_id} 不存在")

    # 系统模板不允许删除
    if template.is_system:
        raise HTTPException(403, "系统内置模板不允许删除")

    # 检查是否有关联的调度
    schedule_count = db.query(CrawlerSchedule).filter(
        CrawlerSchedule.template_id == template_id
    ).count()
    if schedule_count > 0:
        raise HTTPException(400, f"模板被 {schedule_count} 个定时调度使用，无法删除")

    db.delete(template)
    db.commit()

    logger.info(f"用户 {current_user.user_id} 删除工作流模板: {template.name} (ID={template.id})")

# ===== 工作流执行管理端点 =====

@router.post("/workflows/execute", response_model=dict)
async def execute_workflow(
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_EXECUTE"))
):
    """
    执行工作流

    Permissions: CRAWLER_EXECUTE

    Returns:
        {"workflow_id": "uuid-string", "status": "submitted"}
    """
    service = CrawlerService(db)

    try:
        workflow_id = service.trigger_workflow(
            template_id=request.template_id,
            params=request.params,
            current_user=current_user
        )

        return {
            "workflow_id": workflow_id,
            "status": "submitted",
            "message": "工作流已提交执行"
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"执行工作流失败: {e}", exc_info=True)
        raise HTTPException(500, f"执行工作流失败: {str(e)}")

@router.get("/workflows/{workflow_id}", response_model=WorkflowExecutionResponse)
async def get_workflow_status(
    workflow_id: str,
    include_tasks: bool = Query(False, description="是否包含步骤任务列表"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_READ"))
):
    """
    查询工作流执行状态

    Permissions: CRAWLER_READ
    """
    # 查询该workflow_id下的所有任务
    tasks = db.query(CrawlerTask).filter(
        CrawlerTask.workflow_id == workflow_id
    ).order_by(CrawlerTask.step_order).all()

    if not tasks:
        raise HTTPException(404, f"工作流 {workflow_id} 不存在")

    # 排除根任务（step_order=-1）
    step_tasks = [t for t in tasks if t.step_order >= 0]
    root_task = next((t for t in tasks if t.step_order == -1), None)

    total_steps = len(step_tasks)
    completed_steps = len([t for t in step_tasks if t.status == 'SUCCESS'])
    failed_steps = len([t for t in step_tasks if t.status == 'FAILED'])

    # 工作流整体状态
    if failed_steps > 0:
        workflow_status = 'FAILED'
    elif completed_steps == total_steps:
        workflow_status = 'SUCCESS'
    elif any(t.status == 'RUNNING' for t in step_tasks):
        workflow_status = 'RUNNING'
    else:
        workflow_status = 'PENDING'

    response = WorkflowExecutionResponse(
        workflow_id=workflow_id,
        workflow_name=root_task.workflow_name if root_task else "Unknown Workflow",
        status=workflow_status,
        total_steps=total_steps,
        completed_steps=completed_steps,
        progress_percent=int((completed_steps / total_steps) * 100) if total_steps > 0 else 0,
        created_at=root_task.created_at if root_task else tasks[0].created_at
    )

    # 可选: 包含步骤任务列表
    if include_tasks:
        response.tasks = [
            {
                "id": t.id,
                "step_order": t.step_order,
                "task_name": t.task_name,
                "task_type": t.task_type,
                "status": t.status,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "success_items": t.success_items,
                "failed_items": t.failed_items,
                "error_message": t.error_message
            }
            for t in step_tasks
        ]

    return response
```

---

## 三、定时调度服务

### 3.1 调度服务实现

**新建文件**: `apps/api/services/scheduler_service.py`

```python
import json
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from packages.agent_fishing.tools.lure.models.system import CrawlerSchedule
from apps.api.services.crawler_service import CrawlerService

logger = logging.getLogger(__name__)

class WorkflowSchedulerService:
    """
    工作流定时调度服务

    Features:
    - 基于APScheduler实现Cron定时任务
    - 应用启动时自动加载所有启用的调度
    - 支持动态添加/移除调度
    - 调度执行失败自动记录日志
    """

    def __init__(self):
        """初始化调度器"""
        # 配置APScheduler
        jobstores = {
            'default': MemoryJobStore()  # 使用内存存储（重启后丢失，可升级为数据库存储）
        }
        executors = {
            'default': ThreadPoolExecutor(max_workers=5)
        }
        job_defaults = {
            'coalesce': True,  # 合并堆积的任务
            'max_instances': 1,  # 同一任务同时只能有一个实例
            'misfire_grace_time': 300  # 错过执行的任务在5分钟内仍可补执行
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )

        self.scheduler.start()
        logger.info("工作流定时调度器已启动")

    def load_all_schedules(self, db_session_factory):
        """
        加载所有启用的调度（应用启动时调用）

        Args:
            db_session_factory: 数据库会话工厂
        """
        db = db_session_factory()

        try:
            # 查询所有启用的调度
            schedules = db.query(CrawlerSchedule).filter(
                CrawlerSchedule.is_enabled == True
            ).all()

            logger.info(f"加载 {len(schedules)} 个定时调度...")

            for schedule in schedules:
                try:
                    self.add_workflow_schedule(schedule.id, db)
                    logger.info(f"调度 {schedule.id} ({schedule.name}) 已加载")
                except Exception as e:
                    logger.error(f"加载调度 {schedule.id} 失败: {e}")

            logger.info("所有定时调度加载完成")

        finally:
            db.close()

    def add_workflow_schedule(self, schedule_id: int, db_session=None):
        """
        添加定时任务

        Args:
            schedule_id: CrawlerSchedule的ID
            db_session: 数据库会话（可选，如果未提供则创建新会话）
        """
        from shared.database import SessionLocal

        if db_session is None:
            db = SessionLocal()
            should_close = True
        else:
            db = db_session
            should_close = False

        try:
            schedule = db.query(CrawlerSchedule).filter(
                CrawlerSchedule.id == schedule_id
            ).first()

            if not schedule:
                logger.error(f"调度 {schedule_id} 不存在")
                return

            # 解析Cron表达式
            try:
                trigger = CronTrigger.from_crontab(
                    schedule.cron_expression,
                    timezone=schedule.timezone
                )
            except Exception as e:
                logger.error(f"无效的Cron表达式 '{schedule.cron_expression}': {e}")
                return

            # 添加任务到APScheduler
            self.scheduler.add_job(
                func=self._execute_scheduled_workflow,
                trigger=trigger,
                args=[schedule_id],
                id=f"schedule_{schedule_id}",
                name=schedule.name,
                replace_existing=True
            )

            # 更新下次执行时间
            next_run = trigger.get_next_fire_time(None, datetime.now())
            schedule.next_run_time = next_run
            db.commit()

            logger.info(f"调度 {schedule_id} ({schedule.name}) 已添加，下次执行: {next_run}")

        finally:
            if should_close:
                db.close()

    def _execute_scheduled_workflow(self, schedule_id: int):
        """
        执行定时工作流（APScheduler回调函数）

        Args:
            schedule_id: CrawlerSchedule的ID
        """
        from shared.database import SessionLocal

        db = SessionLocal()

        try:
            schedule = db.query(CrawlerSchedule).filter(
                CrawlerSchedule.id == schedule_id
            ).first()

            if not schedule:
                logger.error(f"调度 {schedule_id} 不存在，跳过执行")
                return

            if not schedule.is_enabled:
                logger.info(f"调度 {schedule_id} 已禁用，跳过执行")
                return

            logger.info(f"开始执行定时工作流: {schedule.name} (调度ID={schedule_id})")

            # 解析执行参数
            config = json.loads(schedule.config) if schedule.config else {}

            # 触发工作流
            service = CrawlerService(db)
            workflow_id = service.trigger_workflow(
                template_id=schedule.template_id,
                params=config,
                current_user=None  # 定时触发无current_user
            )

            # 更新调度记录
            schedule.last_run_time = datetime.utcnow()
            schedule.last_task_id = workflow_id  # TODO: 这里应该记录workflow_id或根任务ID
            db.commit()

            logger.info(f"定时工作流 {workflow_id} 已提交执行 (调度ID={schedule_id})")

        except Exception as e:
            logger.error(f"执行定时工作流失败 (调度ID={schedule_id}): {e}", exc_info=True)

        finally:
            db.close()

    def remove_workflow_schedule(self, schedule_id: int):
        """
        移除定时任务

        Args:
            schedule_id: CrawlerSchedule的ID
        """
        job_id = f"schedule_{schedule_id}"

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"调度 {schedule_id} 已移除")
        except Exception as e:
            logger.warning(f"移除调度 {schedule_id} 失败: {e}")

    def pause_workflow_schedule(self, schedule_id: int):
        """暂停定时任务"""
        job_id = f"schedule_{schedule_id}"
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"调度 {schedule_id} 已暂停")
        except Exception as e:
            logger.warning(f"暂停调度 {schedule_id} 失败: {e}")

    def resume_workflow_schedule(self, schedule_id: int):
        """恢复定时任务"""
        job_id = f"schedule_{schedule_id}"
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"调度 {schedule_id} 已恢复")
        except Exception as e:
            logger.warning(f"恢复调度 {schedule_id} 失败: {e}")

    def shutdown(self, wait=True):
        """关闭调度器"""
        logger.info("关闭工作流定时调度器...")
        self.scheduler.shutdown(wait=wait)
        logger.info("工作流定时调度器已关闭")

# 全局单例
scheduler = WorkflowSchedulerService()
```

### 3.2 定时调度API端点

**修改文件**: `apps/api/routes/crawler.py`（继续扩展）

```python
from apps.api.services.scheduler_service import scheduler as workflow_scheduler
from croniter import croniter

# ===== 定时调度管理端点 =====

@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_EXECUTE"))
):
    """
    创建定时调度

    Permissions: CRAWLER_EXECUTE
    """
    # 验证Cron表达式
    try:
        cron = croniter(request.cron_expression, datetime.now())
        next_run = cron.get_next(datetime)
    except Exception as e:
        raise HTTPException(400, f"无效的Cron表达式: {str(e)}")

    # 验证模板存在
    template = db.query(CrawlerWorkflowTemplate).filter(
        CrawlerWorkflowTemplate.id == request.template_id
    ).first()
    if not template:
        raise HTTPException(404, f"工作流模板 {request.template_id} 不存在")

    # 创建调度
    schedule = CrawlerSchedule(
        name=request.name,
        template_id=request.template_id,
        cron_expression=request.cron_expression,
        timezone=request.timezone,
        config=json.dumps(request.config) if request.config else None,
        next_run_time=next_run,
        created_by=current_user.user_id
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # 注册到APScheduler
    workflow_scheduler.add_workflow_schedule(schedule.id, db)

    logger.info(f"用户 {current_user.user_id} 创建定时调度: {schedule.name} (ID={schedule.id})")

    # 构造响应（包含模板名称）
    response_dict = {
        **schedule.__dict__,
        "template_name": template.name
    }

    return ScheduleResponse(**response_dict)

@router.get("/schedules", response_model=ScheduleListResponse)
async def list_schedules(
    is_enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_READ"))
):
    """
    查询定时调度列表

    Permissions: CRAWLER_READ
    """
    query = db.query(CrawlerSchedule).join(CrawlerWorkflowTemplate)

    if is_enabled is not None:
        query = query.filter(CrawlerSchedule.is_enabled == is_enabled)

    total = query.count()

    items_orm = query.order_by(CrawlerSchedule.created_at.desc()) \
                     .offset((page - 1) * page_size) \
                     .limit(page_size) \
                     .all()

    # 构造响应（包含模板名称）
    items = [
        ScheduleResponse(
            **{
                **item.__dict__,
                "template_name": item.template.name if item.template else None
            }
        )
        for item in items_orm
    ]

    return ScheduleListResponse(total=total, items=items)

@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_EXECUTE"))
):
    """
    更新定时调度

    Permissions: CRAWLER_EXECUTE
    """
    schedule = db.query(CrawlerSchedule).filter(
        CrawlerSchedule.id == schedule_id
    ).first()

    if not schedule:
        raise HTTPException(404, f"调度 {schedule_id} 不存在")

    # 更新字段
    if request.name is not None:
        schedule.name = request.name
    if request.cron_expression is not None:
        # 验证新的Cron表达式
        try:
            croniter(request.cron_expression, datetime.now())
        except Exception as e:
            raise HTTPException(400, f"无效的Cron表达式: {str(e)}")
        schedule.cron_expression = request.cron_expression
    if request.timezone is not None:
        schedule.timezone = request.timezone
    if request.is_enabled is not None:
        old_enabled = schedule.is_enabled
        schedule.is_enabled = request.is_enabled

        # 处理启用/禁用状态变化
        if old_enabled and not request.is_enabled:
            workflow_scheduler.pause_workflow_schedule(schedule_id)
        elif not old_enabled and request.is_enabled:
            workflow_scheduler.resume_workflow_schedule(schedule_id)

    if request.config is not None:
        schedule.config = json.dumps(request.config)

    db.commit()
    db.refresh(schedule)

    # 重新注册到APScheduler（更新Cron表达式等）
    if request.cron_expression is not None or request.timezone is not None:
        workflow_scheduler.add_workflow_schedule(schedule_id, db)

    logger.info(f"用户 {current_user.user_id} 更新定时调度: {schedule.name} (ID={schedule.id})")

    # 构造响应
    response_dict = {
        **schedule.__dict__,
        "template_name": schedule.template.name if schedule.template else None
    }

    return ScheduleResponse(**response_dict)

@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("CRAWLER_DELETE"))
):
    """
    删除定时调度

    Permissions: CRAWLER_DELETE
    """
    schedule = db.query(CrawlerSchedule).filter(
        CrawlerSchedule.id == schedule_id
    ).first()

    if not schedule:
        raise HTTPException(404, f"调度 {schedule_id} 不存在")

    # 从APScheduler移除
    workflow_scheduler.remove_workflow_schedule(schedule_id)

    # 从数据库删除
    db.delete(schedule)
    db.commit()

    logger.info(f"用户 {current_user.user_id} 删除定时调度: {schedule.name} (ID={schedule.id})")
```

### 3.3 应用启动时加载调度

**修改文件**: `apps/api/main.py`

```python
from apps.api.services.scheduler_service import scheduler as workflow_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化任务队列
    logger.info("初始化任务队列...")
    initialize_task_queue(SessionLocal, num_workers=3)

    # 启动时加载所有定时调度
    logger.info("加载定时调度...")
    workflow_scheduler.load_all_schedules(SessionLocal)

    yield

    # 关闭时清理资源
    logger.info("关闭任务队列...")
    shutdown_task_queue(wait=True, timeout=30)

    logger.info("关闭定时调度器...")
    workflow_scheduler.shutdown(wait=True)

app = FastAPI(
    title="智能钓鱼助手 API",
    version="5.0.0",
    lifespan=lifespan
)
```

---

## 四、依赖安装

**修改文件**: `pyproject.toml`（或requirements.txt）

```toml
[tool.uv.dependencies]
# ... 现有依赖 ...

# 定时调度
apscheduler = "^3.10.4"

# Cron表达式解析
croniter = "^1.4.1"
```

**安装依赖**:
```bash
uv sync
```

---

## 五、API文档更新

### 5.1 Swagger文档

启动API服务器后，访问 `http://localhost:8000/docs` 查看自动生成的Swagger文档，确认新增端点:

- `POST /api/v1/admin/crawler/templates` - 创建模板
- `GET /api/v1/admin/crawler/templates` - 模板列表
- `GET /api/v1/admin/crawler/templates/{id}` - 模板详情
- `PUT /api/v1/admin/crawler/templates/{id}` - 更新模板
- `DELETE /api/v1/admin/crawler/templates/{id}` - 删除模板
- `POST /api/v1/admin/crawler/workflows/execute` - 执行工作流
- `GET /api/v1/admin/crawler/workflows/{workflow_id}` - 工作流状态
- `POST /api/v1/admin/crawler/schedules` - 创建调度
- `GET /api/v1/admin/crawler/schedules` - 调度列表
- `PUT /api/v1/admin/crawler/schedules/{id}` - 更新调度
- `DELETE /api/v1/admin/crawler/schedules/{id}` - 删除调度

---

## 六、测试验证

### 6.1 API测试用例

**文件**: `tests/test_workflow_api.py`

```python
import pytest
from fastapi.testclient import TestClient

def test_create_workflow_template(client, admin_token):
    """测试创建工作流模板"""
    response = client.post(
        "/api/v1/admin/crawler/templates",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "测试模板",
            "description": "测试描述",
            "template_json": '{"steps": []}',
            "category": "test"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试模板"

def test_execute_workflow(client, admin_token, template_id):
    """测试执行工作流"""
    response = client.post(
        "/api/v1/admin/crawler/workflows/execute",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "template_id": template_id,
            "params": {"keyword": "测试"}
        }
    )
    assert response.status_code == 200
    assert "workflow_id" in response.json()

def test_create_schedule(client, admin_token, template_id):
    """测试创建定时调度"""
    response = client.post(
        "/api/v1/admin/crawler/schedules",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "每日凌晨2点",
            "template_id": template_id,
            "cron_expression": "0 2 * * *",
            "timezone": "Asia/Shanghai",
            "config": {"keyword": "测试"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "每日凌晨2点"
```

---

## 七、验收标准

### 7.1 功能验收

- [ ] 工作流模板CRUD API正常
- [ ] 工作流执行API可提交工作流
- [ ] 工作流状态查询API返回正确状态
- [ ] 定时调度CRUD API正常
- [ ] 定时调度可按Cron表达式执行
- [ ] APScheduler正常启动和关闭
- [ ] 应用重启后调度自动恢复

### 7.2 安全验收

- [ ] 所有API端点都有JWT认证
- [ ] CRUD权限校验正常（CRAWLER_READ/EXECUTE/DELETE）
- [ ] 系统模板不能被修改/删除
- [ ] Cron表达式验证防止注入

### 7.3 性能验收

- [ ] API响应时间 < 200ms
- [ ] APScheduler调度延迟 < 5秒
- [ ] 并发创建100个模板无异常

---

## 八、交付清单

### 代码文件
- [x] API Schema定义（crawler.py扩展）
- [x] 工作流模板API（crawler.py扩展）
- [x] 工作流执行API（crawler.py扩展）
- [x] 定时调度服务（scheduler_service.py）
- [x] 定时调度API（crawler.py扩展）
- [x] 应用启动集成（main.py）
- [x] 依赖安装（pyproject.toml）

### 文档
- [ ] API使用文档
- [ ] Cron表达式示例
- [ ] 工作流模板JSON格式文档

### 测试
- [ ] 单元测试
- [ ] API集成测试
- [ ] 定时调度测试

---

**下一阶段**: [阶段3 - 工作流前端界面](./workflow-phase3-frontend.md)
