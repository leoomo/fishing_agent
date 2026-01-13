"""
Crawler node models for distributed crawling

分布式爬虫节点模型，用于管理Worker节点
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class NodeStatus(str, enum.Enum):
    """Node status enumeration"""
    ONLINE = "online"           # 在线，接受任务
    OFFLINE = "offline"         # 离线
    DRAINING = "draining"       # 排空中，不接受新任务
    MAINTENANCE = "maintenance" # 维护中


class CrawlerNode(Base, TimestampMixin):
    """
    分布式爬虫节点

    用于管理Worker节点的注册、状态、能力和性能指标
    """
    __tablename__ = 'crawler_nodes'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # === 节点标识 ===
    node_id = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment='节点唯一标识（UUID）'
    )
    node_name = Column(
        String(200),
        nullable=False,
        comment='节点名称'
    )
    node_secret_hash = Column(
        String(256),
        nullable=False,
        comment='节点密钥哈希（bcrypt）'
    )

    # === 网络信息 ===
    ip_address = Column(
        String(45),
        nullable=True,
        comment='节点IP地址'
    )
    location = Column(
        String(100),
        nullable=True,
        comment='地理位置标签'
    )

    # === 能力标签 ===
    capabilities = Column(
        Text,
        default='["all"]',
        comment='能力标签JSON数组（如 ["taobao", "jd", "forum"]）'
    )

    # === 状态与健康 ===
    status = Column(
        SQLEnum(NodeStatus, native_enum=False),
        default=NodeStatus.OFFLINE,
        nullable=False,
        index=True,
        comment='节点状态'
    )
    last_heartbeat = Column(
        DateTime,
        nullable=True,
        index=True,
        comment='最后心跳时间'
    )
    heartbeat_interval = Column(
        Integer,
        default=30,
        comment='心跳间隔（秒）'
    )

    # === 性能指标 ===
    max_concurrent_tasks = Column(
        Integer,
        default=1,
        comment='最大并发任务数（默认1，避免触发风控）'
    )
    current_tasks = Column(
        Integer,
        default=0,
        comment='当前运行任务数（通过心跳更新）'
    )
    total_completed = Column(
        Integer,
        default=0,
        comment='累计完成任务数'
    )
    total_failed = Column(
        Integer,
        default=0,
        comment='累计失败任务数'
    )
    avg_task_duration = Column(
        Float,
        default=0.0,
        comment='平均任务时长（秒）'
    )
    success_rate = Column(
        Float,
        default=100.0,
        comment='成功率（百分比）'
    )

    # === 系统指标（心跳上报） ===
    cpu_usage = Column(
        Float,
        nullable=True,
        comment='CPU使用率（百分比）'
    )
    memory_usage = Column(
        Float,
        nullable=True,
        comment='内存使用率（百分比）'
    )
    disk_usage = Column(
        Float,
        nullable=True,
        comment='磁盘使用率（百分比）'
    )
    running_task_ids = Column(
        Text,
        nullable=True,
        comment='当前运行任务ID列表JSON'
    )

    # === 版本兼容 ===
    worker_version = Column(
        String(50),
        nullable=True,
        comment='Worker版本号'
    )
    api_version = Column(
        String(20),
        default='v1',
        comment='API版本'
    )

    # === 元数据 ===
    tags = Column(
        Text,
        nullable=True,
        comment='自定义标签JSON'
    )
    config = Column(
        Text,
        nullable=True,
        comment='节点特定配置JSON'
    )

    # === Relationships ===
    assigned_tasks = relationship(
        "CrawlerTask",
        back_populates="assigned_node",
        foreign_keys="CrawlerTask.assigned_node_id"
    )
    task_assignments = relationship(
        "NodeTaskAssignment",
        back_populates="node",
        cascade="all, delete-orphan"
    )

    # === Indexes ===
    __table_args__ = (
        Index('idx_node_status_heartbeat', 'status', 'last_heartbeat'),
    )

    def __repr__(self):
        return f"<CrawlerNode(id={self.id}, node_id='{self.node_id}', status='{self.status}')>"

    def to_dict(self, include_stats=True):
        """Convert to dictionary representation"""
        import json

        result = {
            'id': self.id,
            'node_id': self.node_id,
            'node_name': self.node_name,
            'ip_address': self.ip_address,
            'location': self.location,
            'capabilities': json.loads(self.capabilities) if self.capabilities else ['all'],
            'status': self.status.value if isinstance(self.status, enum.Enum) else self.status,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'heartbeat_interval': self.heartbeat_interval,
            'worker_version': self.worker_version,
            'api_version': self.api_version,
            'tags': json.loads(self.tags) if self.tags else None,
            'config': json.loads(self.config) if self.config else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_stats:
            result.update({
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'current_tasks': self.current_tasks,
                'total_completed': self.total_completed,
                'total_failed': self.total_failed,
                'avg_task_duration': self.avg_task_duration,
                'success_rate': self.success_rate,
                'cpu_usage': self.cpu_usage,
                'memory_usage': self.memory_usage,
                'disk_usage': self.disk_usage,
                'running_task_ids': json.loads(self.running_task_ids) if self.running_task_ids else [],
            })

        return result

    def is_available(self) -> bool:
        """Check if node is available for new tasks"""
        return (
            self.status == NodeStatus.ONLINE and
            self.current_tasks < self.max_concurrent_tasks
        )

    def update_stats_on_complete(self, duration: float, success: bool):
        """Update statistics when a task completes"""
        if success:
            self.total_completed += 1
        else:
            self.total_failed += 1

        # Update average duration
        total_tasks = self.total_completed + self.total_failed
        if total_tasks > 0:
            # Moving average
            self.avg_task_duration = (
                (self.avg_task_duration * (total_tasks - 1) + duration) / total_tasks
            )

        # Update success rate
        if total_tasks > 0:
            self.success_rate = (self.total_completed / total_tasks) * 100


class NodeTaskAssignment(Base, TimestampMixin):
    """
    任务分配历史记录

    用于审计和故障恢复，记录任务的分配、认领、完成等事件
    """
    __tablename__ = 'crawler_node_task_assignments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(
        Integer,
        ForeignKey('crawler_tasks.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='任务ID'
    )
    node_id = Column(
        Integer,
        ForeignKey('crawler_nodes.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='节点ID'
    )

    # === 操作信息 ===
    action = Column(
        String(20),
        nullable=False,
        comment='操作类型（assigned/claimed/completed/failed/reassigned）'
    )
    action_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment='操作时间'
    )
    action_reason = Column(
        Text,
        nullable=True,
        comment='操作原因'
    )

    # === Relationships ===
    node = relationship("CrawlerNode", back_populates="task_assignments")
    task = relationship("CrawlerTask", back_populates="node_assignments")

    # === Indexes ===
    __table_args__ = (
        Index('idx_assignment_task_action', 'task_id', 'action'),
        Index('idx_assignment_node_action', 'node_id', 'action_at'),
    )

    def __repr__(self):
        return f"<NodeTaskAssignment(id={self.id}, task_id={self.task_id}, node_id={self.node_id}, action='{self.action}')>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'node_id': self.node_id,
            'action': self.action,
            'action_at': self.action_at.isoformat() if self.action_at else None,
            'action_reason': self.action_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
