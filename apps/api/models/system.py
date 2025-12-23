"""
System models for crawler, monitoring, logging, and configuration
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship, backref
from datetime import datetime
import enum

from .base import Base, TimestampMixin


# Enumerations
class TaskStatus(str, enum.Enum):
    """Crawler task status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class LogLevel(str, enum.Enum):
    """Log level"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ErrorCategory(str, enum.Enum):
    """Error categorization for pattern detection"""
    LLM_API = "llm_api"           # OpenAI, Claude API failures
    EXTERNAL_SERVICE = "external"  # Weather, map APIs
    TOOL_EXECUTION = "tool"        # Fishing equipment analysis
    DATABASE = "database"          # Storage and connectivity
    TIMEOUT = "timeout"           # Request timeouts
    VALIDATION = "validation"      # Input validation failures
    AUTHENTICATION = "auth"       # Authentication/authorization
    RATE_LIMIT = "rate_limit"     # Rate limiting
    NETWORK = "network"           # Network connectivity issues
    SYSTEM_RESOURCE = "system"    # System resource constraints
    UNKNOWN = "unknown"           # Uncategorized errors


class ErrorSeverity(str, enum.Enum):
    """Error severity levels"""
    CRITICAL = "critical"         # System-down errors
    HIGH = "high"                 # Major functionality impacted
    MEDIUM = "medium"             # Partial functionality impacted
    LOW = "low"                   # Minor issues


class ConfigType(str, enum.Enum):
    """System configuration type"""
    AGENT = "agent"
    ALGORITHM = "algorithm"
    API = "api"
    SYSTEM = "system"


class ReportType(str, enum.Enum):
    """Analytics report type"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


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

    # === Relationships ===
    logs = relationship("CrawlerLog", back_populates="task", cascade="all, delete-orphan")
    children = relationship('CrawlerTask', backref=backref('parent', remote_side=[id]))

    def __repr__(self):
        return f"<CrawlerTask(id={self.id}, type='{self.task_type}', status='{self.status}')>"

    def to_dict(self, include_logs=False):
        """Convert to dictionary representation"""
        result = {
            'id': self.id,
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
    created_by = Column(Integer, ForeignKey('admin_users.id'), comment='创建人ID')
    usage_count = Column(Integer, default=0, comment='使用次数统计')

    # Relationships
    creator = relationship('AdminUser', back_populates='created_workflow_templates')
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
    config = Column(Text, comment='调度配置JSON（执行参数）')
    next_run_time = Column(DateTime, comment='下次执行时间')
    last_run_time = Column(DateTime, comment='最后执行时间')
    last_task_id = Column(Integer, ForeignKey('crawler_tasks.id'), comment='最后一次执行的任务ID')
    created_by = Column(Integer, ForeignKey('admin_users.id'))

    # Relationships
    template = relationship('CrawlerWorkflowTemplate', back_populates='schedules')
    creator = relationship('AdminUser', back_populates='created_schedules')
    last_task = relationship('CrawlerTask')

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
            'config': self.config,
            'next_run_time': self.next_run_time.isoformat() if self.next_run_time else None,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'last_task_id': self.last_task_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# Monitoring Models
class APILog(Base):
    """API call logging"""

    __tablename__ = 'api_logs'

    # 复合索引用于常见查询优化
    __table_args__ = (
        # 按时间范围和端点统计
        Index('ix_api_logs_timestamp_endpoint', 'timestamp', 'endpoint'),
        # 按状态码和时间统计错误
        Index('ix_api_logs_status_timestamp', 'status_code', 'timestamp'),
        # 按错误类别和时间统计
        Index('ix_api_logs_category_timestamp', 'error_category', 'timestamp'),
        # 按相关ID统计
        Index('ix_api_logs_correlation_id', 'correlation_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="Request timestamp")
    endpoint = Column(String(200), nullable=False, index=True, comment="API endpoint")
    method = Column(String(10), nullable=False, comment="HTTP method")
    status_code = Column(Integer, nullable=False, index=True, comment="HTTP status code")
    response_time = Column(Float, comment="Response time in milliseconds")
    user_id = Column(Integer, index=True, comment="User ID if authenticated")
    ip_address = Column(String(50), comment="Client IP address")
    user_agent = Column(String(500), comment="User agent string")
    error_message = Column(Text, comment="Error message if any")

    # Enhanced error tracking fields
    correlation_id = Column(String(100), index=True, comment="Correlation ID for cross-service tracing")
    error_category = Column(SQLEnum(ErrorCategory, native_enum=False), index=True, comment="Error category for pattern detection")
    error_severity = Column(SQLEnum(ErrorSeverity, native_enum=False), comment="Error severity level")
    error_context = Column(Text, comment="Additional error context (JSON)")
    stack_trace = Column(Text, comment="Stack trace for debugging")

    def __repr__(self):
        return f"<APILog(id={self.id}, endpoint='{self.endpoint}', status={self.status_code})>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'endpoint': self.endpoint,
            'method': self.method,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'error_message': self.error_message,
            'correlation_id': self.correlation_id,
            'error_category': self.error_category.value if isinstance(self.error_category, enum.Enum) else self.error_category,
            'error_severity': self.error_severity.value if isinstance(self.error_severity, enum.Enum) else self.error_severity,
            'error_context': self.error_context,
            'stack_trace': self.stack_trace,
        }


class AgentExecutionLog(Base):
    """Agent execution tracking - one record per agent.run() call"""

    __tablename__ = 'agent_execution_logs'

    __table_args__ = (
        Index('ix_agent_exec_timestamp_type', 'timestamp', 'agent_type'),
        Index('ix_agent_exec_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_agent_exec_session', 'session_id'),
        Index('ix_agent_exec_correlation_id', 'correlation_id'),
        Index('ix_agent_exec_error_category', 'error_category', 'timestamp'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True,
                       comment="Execution timestamp")

    # Agent identification
    agent_type = Column(String(50), nullable=False, index=True,
                        comment="Agent type (fishing/equipment_import/etc)")
    agent_version = Column(String(20), comment="Agent version if applicable")

    # Execution context
    session_id = Column(Integer, index=True, comment="Chat session ID if applicable")
    user_id = Column(Integer, index=True, comment="User ID")

    # Enhanced error tracking
    correlation_id = Column(String(100), index=True, comment="Correlation ID for cross-service tracing")
    failure_stage = Column(String(50), comment="Stage where failure occurred (INIT/PROCESSING/TOOL_CALL/FINAL_RESPONSE)")
    error_category = Column(SQLEnum(ErrorCategory, native_enum=False), index=True, comment="Error category for pattern detection")
    error_pattern_id = Column(String(100), index=True, comment="Link to detected failure patterns")
    recovery_attempted = Column(Boolean, default=False, comment="Whether recovery was attempted")
    recovery_successful = Column(Boolean, comment="Whether recovery was successful")
    failed_tool_name = Column(String(100), comment="Name of tool that caused failure")

    # Input/Output
    input_text = Column(Text, comment="User input (truncated to 1000 chars)")
    output_text = Column(Text, comment="Agent output (truncated to 2000 chars)")

    # LLM metrics
    model_provider = Column(String(50), comment="LLM provider used")
    model_name = Column(String(100), comment="Model name")
    llm_calls = Column(Integer, default=0, comment="Number of LLM calls in this execution")
    input_tokens = Column(Integer, default=0, comment="Total input tokens")
    output_tokens = Column(Integer, default=0, comment="Total output tokens")
    total_tokens = Column(Integer, default=0, comment="Total tokens")

    # Performance
    latency_ms = Column(Integer, comment="Total execution time in milliseconds")
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, comment="Error message if failed")

    # Cost
    estimated_cost = Column(Float, default=0.0, comment="Estimated cost in CNY")

    # Tool usage summary (JSON)
    tool_calls_summary = Column(Text, comment="JSON summary of tool calls")

    # Relationships
    tool_calls = relationship("ToolCallLog", back_populates="execution", cascade="all, delete-orphan")
    llm_logs = relationship("LLMLog", back_populates="execution")

    def __repr__(self):
        return f"<AgentExecutionLog(id={self.id}, agent='{self.agent_type}', tokens={self.total_tokens})>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'agent_type': self.agent_type,
            'agent_version': self.agent_version,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'correlation_id': self.correlation_id,
            'failure_stage': self.failure_stage,
            'error_category': self.error_category.value if isinstance(self.error_category, enum.Enum) else self.error_category,
            'error_pattern_id': self.error_pattern_id,
            'recovery_attempted': self.recovery_attempted,
            'recovery_successful': self.recovery_successful,
            'failed_tool_name': self.failed_tool_name,
            'input_text': self.input_text,
            'output_text': self.output_text,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'llm_calls': self.llm_calls,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'latency_ms': self.latency_ms,
            'success': self.success,
            'error_message': self.error_message,
            'estimated_cost': self.estimated_cost,
            'tool_calls_summary': self.tool_calls_summary,
        }


class ToolCallLog(Base):
    """Detailed tool call tracking"""

    __tablename__ = 'tool_call_logs'

    __table_args__ = (
        Index('ix_tool_call_timestamp_name', 'timestamp', 'tool_name'),
        Index('ix_tool_call_execution', 'execution_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Link to execution
    execution_id = Column(Integer, ForeignKey('agent_execution_logs.id', ondelete='CASCADE'),
                          nullable=False, index=True)

    # Tool info
    tool_name = Column(String(100), nullable=False, index=True, comment="Tool function name")
    tool_category = Column(String(50), comment="Tool category (weather/fishing/lure/etc)")

    # Execution details
    input_args = Column(Text, comment="Tool input arguments (JSON, truncated)")
    output_result = Column(Text, comment="Tool output (truncated to 1000 chars)")

    # Performance
    latency_ms = Column(Integer, comment="Tool execution time in milliseconds")
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, comment="Error message if failed")

    # Relationships
    execution = relationship("AgentExecutionLog", back_populates="tool_calls")

    def __repr__(self):
        return f"<ToolCallLog(id={self.id}, tool='{self.tool_name}', latency={self.latency_ms}ms)>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'execution_id': self.execution_id,
            'tool_name': self.tool_name,
            'tool_category': self.tool_category,
            'input_args': self.input_args,
            'output_result': self.output_result,
            'latency_ms': self.latency_ms,
            'success': self.success,
            'error_message': self.error_message,
        }


class LLMLog(Base):
    """LLM API call logging"""

    __tablename__ = 'llm_logs'

    # 复合索引用于常见查询优化
    __table_args__ = (
        # 按时间范围和提供商统计
        Index('ix_llm_logs_timestamp_provider', 'timestamp', 'model_provider'),
        # 按成功状态和时间统计
        Index('ix_llm_logs_success_timestamp', 'success', 'timestamp'),
        # 按 Agent 类型统计
        Index('ix_llm_logs_agent_type', 'agent_type'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="Call timestamp")
    model_provider = Column(String(50), nullable=False, index=True, comment="Model provider (qwen/zhipu/openai)")
    model_name = Column(String(100), comment="Model name")
    prompt_tokens = Column(Integer, comment="Input token count")
    completion_tokens = Column(Integer, comment="Output token count")
    total_tokens = Column(Integer, index=True, comment="Total token count")
    response_time = Column(Float, comment="Response time in seconds")
    success = Column(Boolean, nullable=False, index=True, comment="Whether call succeeded")
    error_message = Column(Text, comment="Error message if failed")
    cost = Column(Float, comment="Estimated cost in CNY")

    # New fields for agent monitoring
    agent_type = Column(String(50), index=True, comment="Agent type that made the call")
    session_id = Column(Integer, index=True, comment="Session ID if applicable")
    user_id = Column(Integer, index=True, comment="User ID if applicable")
    execution_id = Column(Integer, ForeignKey('agent_execution_logs.id', ondelete='SET NULL'),
                          comment="Parent execution ID")

    # Relationships
    execution = relationship("AgentExecutionLog", back_populates="llm_logs")

    def __repr__(self):
        return f"<LLMLog(id={self.id}, provider='{self.model_provider}', tokens={self.total_tokens})>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'response_time': self.response_time,
            'success': self.success,
            'error_message': self.error_message,
            'cost': self.cost,
        }


# Configuration Models
class SystemConfig(Base, TimestampMixin):
    """System configuration"""

    __tablename__ = 'system_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True, comment="Configuration key")
    config_value = Column(Text, nullable=False, comment="Configuration value (JSON)")
    config_type = Column(
        SQLEnum(ConfigType, native_enum=False),
        nullable=False,
        index=True,
        comment="Configuration type"
    )
    description = Column(Text, comment="Configuration description")
    is_encrypted = Column(Boolean, default=False, nullable=False, comment="Whether value is encrypted")
    last_modified_by = Column(Integer, ForeignKey('admin_users.id'), comment="Last modified by admin user ID")

    # Relationships
    modifier = relationship("AdminUser", back_populates="configs_modified")

    def __repr__(self):
        return f"<SystemConfig(id={self.id}, key='{self.config_key}', type='{self.config_type}')>"

    def to_dict(self, decrypt_value=False):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value if not self.is_encrypted or decrypt_value else '***encrypted***',
            'config_type': self.config_type.value if isinstance(self.config_type, enum.Enum) else self.config_type,
            'description': self.description,
            'is_encrypted': self.is_encrypted,
            'last_modified_by': self.last_modified_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Analytics Models
class AnalyticsReport(Base, TimestampMixin):
    """Analytics report"""

    __tablename__ = 'analytics_reports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(
        SQLEnum(ReportType, native_enum=False),
        nullable=False,
        index=True,
        comment="Report type"
    )
    start_date = Column(Date, nullable=False, index=True, comment="Report start date")
    end_date = Column(Date, nullable=False, index=True, comment="Report end date")
    report_data = Column(Text, nullable=False, comment="Report data (JSON)")
    generated_by = Column(Integer, ForeignKey('admin_users.id'), comment="Generated by admin user ID")
    is_published = Column(Boolean, default=False, nullable=False, comment="Whether report is published")

    # Relationships
    generator = relationship("AdminUser", back_populates="reports_generated")

    def __repr__(self):
        return f"<AnalyticsReport(id={self.id}, type='{self.report_type}', start={self.start_date})>"

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'report_type': self.report_type.value if isinstance(self.report_type, enum.Enum) else self.report_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'report_data': self.report_data,
            'generated_by': self.generated_by,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
