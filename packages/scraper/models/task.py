"""
Crawler task models

独立的爬虫任务模型，不依赖 agent_fishing
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship, backref
from datetime import datetime
import enum

from .base import Base, TimestampMixin


# Enumerations
class TaskStatus(str, enum.Enum):
    """Crawler task status"""
    PENDING = "PENDING"      # 待启动（未点击启动）
    QUEUED = "QUEUED"        # 已启动，等待Worker领取
    RUNNING = "RUNNING"      # Worker已领取，执行中
    SUCCESS = "SUCCESS"      # 执行成功
    FAILED = "FAILED"        # 执行失败
    CANCELLED = "CANCELLED"  # 用户手动停止


class LogLevel(str, enum.Enum):
    """Log level"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# Crawler Models
class CrawlerTask(Base, TimestampMixin):
    """Crawler task tracking"""

    __tablename__ = 'crawler_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False, index=True, comment="Task type (taobao/jd/forum)")
    task_name = Column(String(200), comment="Task name")
    status = Column(
        SQLEnum(TaskStatus, native_enum=False),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
        comment="Task status"
    )
    start_time = Column(DateTime, index=True, comment="Task start time")
    end_time = Column(DateTime, comment="Task end time")
    total_items = Column(Integer, default=0, comment="Total items to process")
    success_items = Column(Integer, default=0, comment="Successfully processed items")
    failed_items = Column(Integer, default=0, comment="Failed items")
    error_message = Column(Text, comment="Error message if failed")
    config = Column(Text, comment="Task configuration (JSON)")
    result_summary = Column(Text, comment="Result summary (JSON)")

    # === 工作流相关字段 ===
    workflow_id = Column(String(36), index=True, nullable=True, comment='工作流分组ID（UUID）')
    workflow_name = Column(String(200), nullable=True, comment='工作流名称（冗余字段，便于查询）')
    parent_task_id = Column(Integer, ForeignKey('crawler_tasks.id'), nullable=True, comment='父任务ID（DAG依赖）')
    step_order = Column(Integer, default=0, comment='工作流中的步骤顺序')
    step_config = Column(Text, nullable=True, comment='步骤配置JSON（含depends_on）')

    # === 执行控制字段 ===
    platform = Column(String(50), index=True, nullable=True, comment='平台标识（taobao/jd/tmall）')
    shop_url = Column(String(500), nullable=True, comment='店铺URL（用于店铺级工作流）')
    retry_count = Column(Integer, default=0, comment='已重试次数')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    timeout_seconds = Column(Integer, default=3600, comment='超时时间（秒）')
    requires_intervention = Column(Boolean, default=False, comment='是否需要人工干预')

    # === 数据质量字段 ===
    duplicate_items = Column(Integer, default=0, comment='去重数量')
    invalid_items = Column(Integer, default=0, comment='无效数据量')

    # === 已下载产品标识 ===
    downloaded_products = Column(
        Text,
        nullable=True,
        comment="已下载产品标识JSON数组，格式: ['品牌_产品名', ...]"
    )

    # === 分布式执行字段 ===
    execution_mode = Column(
        String(20),
        default='local',
        comment='执行模式: local/distributed'
    )
    assigned_node_id = Column(
        Integer,
        ForeignKey('crawler_nodes.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment='分配的节点ID'
    )
    assigned_at = Column(
        DateTime,
        nullable=True,
        comment='任务分配时间'
    )
    claimed_at = Column(
        DateTime,
        nullable=True,
        comment='Worker认领时间'
    )

    # === Relationships ===
    logs = relationship("CrawlerLog", back_populates="task", cascade="all, delete-orphan")
    children = relationship('CrawlerTask', backref=backref('parent', remote_side=[id]))
    assigned_node = relationship(
        "CrawlerNode",
        back_populates="assigned_tasks",
        foreign_keys=[assigned_node_id]
    )
    node_assignments = relationship(
        "NodeTaskAssignment",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CrawlerTask(id={self.id}, type='{self.task_type}', status='{self.status}')>"

    def to_dict(self, include_logs=False):
        """Convert to dictionary representation"""
        result = {
            'task_id': self.id,  # 前端期望 task_id 而不是 id
            'task_type': self.task_type,
            'task_name': self.task_name,
            'status': self.status.value if isinstance(self.status, enum.Enum) else self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_items': self.total_items,
            'success_items': self.success_items,
            'failed_items': self.failed_items,
            'error_message': self.error_message,
            'config': self.config,
            'result_summary': self.result_summary,
            'downloaded_products': self.downloaded_products,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_logs:
            result['logs'] = [log.to_dict() for log in self.logs]

        return result


class CrawlerLog(Base, TimestampMixin):
    """Crawler task logs"""

    __tablename__ = 'crawler_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('crawler_tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    level = Column(
        SQLEnum(LogLevel, native_enum=False),
        nullable=False,
        index=True,
        comment="Log level"
    )
    message = Column(Text, nullable=False, comment="Log message")
    details = Column(Text, comment="Detailed information (JSON)")

    # Relationships
    task = relationship("CrawlerTask", back_populates="logs")

    def __repr__(self):
        return f"<CrawlerLog(id={self.id}, task_id={self.task_id}, level='{self.level}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'level': self.level.value if isinstance(self.level, enum.Enum) else self.level,
            'message': self.message,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# Workflow Models
class CrawlerWorkflowTemplate(Base, TimestampMixin):
    """工作流模板表"""
    __tablename__ = "crawler_workflow_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True, comment='模板名称')
    description = Column(Text, comment='模板描述')
    template_json = Column(Text, nullable=False, comment='工作流定义JSON')
    category = Column(String(50), comment='模板分类（shop/keyword/sync）')
    is_system = Column(Boolean, default=False, comment='是否系统内置模板')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    created_by = Column(Integer, nullable=True, comment='创建人ID')
    usage_count = Column(Integer, default=0, comment='使用次数统计')

    # Relationships
    schedules = relationship('CrawlerSchedule', back_populates='template')

    def __repr__(self):
        return f"<CrawlerWorkflowTemplate(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CrawlerSchedule(Base, TimestampMixin):
    """定时调度表"""
    __tablename__ = "crawler_schedules"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, comment='调度名称')
    template_id = Column(Integer, ForeignKey('crawler_workflow_templates.id'), nullable=False)
    cron_expression = Column(String(100), nullable=False, comment='Cron表达式')
    timezone = Column(String(50), default='Asia/Shanghai', comment='时区')
    is_enabled = Column(Boolean, default=True, comment='是否启用')
    params = Column(Text, comment='调度参数JSON')
    description = Column(Text, comment='调度描述')
    max_instances = Column(Integer, default=1, comment='最大并发实例数')
    timeout_seconds = Column(Integer, default=3600, comment='超时时间（秒）')
    next_run_at = Column(DateTime, comment='下次执行时间')
    last_run_at = Column(DateTime, comment='最后执行时间')
    run_count = Column(Integer, default=0, comment='运行次数')
    success_count = Column(Integer, default=0, comment='成功次数')
    failure_count = Column(Integer, default=0, comment='失败次数')
    created_by = Column(String(100), nullable=True, comment='创建人')

    # Relationships
    template = relationship('CrawlerWorkflowTemplate', back_populates='schedules')

    def __repr__(self):
        return f"<CrawlerSchedule(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'name': self.name,
            'template_id': self.template_id,
            'cron_expression': self.cron_expression,
            'timezone': self.timezone,
            'is_enabled': self.is_enabled,
            'params': self.params,
            'description': self.description,
            'max_instances': self.max_instances,
            'timeout_seconds': self.timeout_seconds,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'run_count': self.run_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
