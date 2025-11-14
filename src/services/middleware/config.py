"""
中间件配置管理

提供统一的配置管理功能，支持环境变量和默认值。
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class MiddlewareConfig:
    """中间件配置类"""

    # 日志级别
    log_level: str = field(default_factory=lambda: os.getenv("AGENT_LOG_LEVEL", "INFO"))

    # 日志输出方式
    log_to_console: bool = field(default_factory=lambda: os.getenv("AGENT_LOG_CONSOLE", "true").lower() == "true")
    log_to_file: bool = field(default_factory=lambda: os.getenv("AGENT_LOG_FILE", "false").lower() == "true")

    # 日志文件路径
    log_file_path: str = field(default_factory=lambda: os.getenv("AGENT_LOG_FILE_PATH", "logs/agent.log"))

    # 性能监控
    enable_performance_monitoring: bool = field(default_factory=lambda: os.getenv("AGENT_PERF_MONITOR", "true").lower() == "true")

    # 工具调用监控
    enable_tool_tracking: bool = field(default_factory=lambda: os.getenv("AGENT_TOOL_TRACKING", "true").lower() == "true")

    # 敏感信息过滤
    enable_sensitive_filter: bool = field(default_factory=lambda: os.getenv("AGENT_SENSITIVE_FILTER", "true").lower() == "true")

    # 日志格式
    log_format: str = field(
        default_factory=lambda: os.getenv(
            "AGENT_LOG_FORMAT",
            "[{timestamp}] {level} | {session_id} | {component}: {message}"
        )
    )

    # 最大日志长度（防止日志过长）
    max_log_length: int = field(default_factory=lambda: int(os.getenv("AGENT_MAX_LOG_LENGTH", "2000")))

    # 会话ID生成方式
    session_id_generator: str = field(default_factory=lambda: os.getenv("AGENT_SESSION_ID_GEN", "uuid"))

    # 模型调用详细程度配置
    model_call_detail_level: str = field(
        default_factory=lambda: os.getenv("AGENT_MODEL_CALL_DETAIL", "enhanced")
    )

    # 是否启用调用目的分析
    enable_call_purpose_analysis: bool = field(
        default_factory=lambda: os.getenv("AGENT_CALL_PURPOSE_ANALYSIS", "true").lower() == "true"
    )

    # 是否在控制台显示增强信息
    show_enhanced_console_output: bool = field(
        default_factory=lambda: os.getenv("AGENT_ENHANCED_CONSOLE", "true").lower() == "true"
    )

    # 文件日志格式（json/structured/text）
    file_log_format: str = field(
        default_factory=lambda: os.getenv("AGENT_FILE_LOG_FORMAT", "json")
    )

    # 是否启用日志记录
    enable_logging: bool = field(
        default_factory=lambda: os.getenv("AGENT_ENABLE_LOGGING", "true").lower() == "true"
    )

    # 分层日志配置
    log_mode: str = field(default_factory=lambda: os.getenv("LOG_MODE", "normal"))  # normal/debug/error
    log_template: str = field(default_factory=lambda: os.getenv("LOG_TEMPLATE", "production"))  # production/development/debugging/minimal

    @classmethod
    def from_env(cls) -> 'MiddlewareConfig':
        """从环境变量创建配置"""
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'log_level': self.log_level,
            'log_to_console': self.log_to_console,
            'log_to_file': self.log_to_file,
            'log_file_path': self.log_file_path,
            'enable_performance_monitoring': self.enable_performance_monitoring,
            'enable_tool_tracking': self.enable_tool_tracking,
            'enable_sensitive_filter': self.enable_sensitive_filter,
            'log_format': self.log_format,
            'max_log_length': self.max_log_length,
            'session_id_generator': self.session_id_generator,
            'model_call_detail_level': self.model_call_detail_level,
            'enable_call_purpose_analysis': self.enable_call_purpose_analysis,
            'show_enhanced_console_output': self.show_enhanced_console_output,
            'file_log_format': self.file_log_format,
            'enable_logging': self.enable_logging,
            'log_mode': self.log_mode,
            'log_template': self.log_template
        }

    def validate(self) -> bool:
        """验证配置有效性"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_levels}")

        if self.max_log_length <= 0:
            raise ValueError("max_log_length must be positive")

        # 验证模型调用详细程度
        valid_detail_levels = ['basic', 'enhanced', 'detailed']
        if self.model_call_detail_level not in valid_detail_levels:
            raise ValueError(f"Invalid model_call_detail_level: {self.model_call_detail_level}. Must be one of {valid_detail_levels}")

        # 验证文件日志格式
        valid_file_formats = ['json', 'structured', 'text']
        if self.file_log_format not in valid_file_formats:
            raise ValueError(f"Invalid file_log_format: {self.file_log_format}. Must be one of {valid_file_formats}")

        # 验证分层日志模式
        valid_log_modes = ['normal', 'debug', 'error']
        if self.log_mode not in valid_log_modes:
            raise ValueError(f"Invalid log_mode: {self.log_mode}. Must be one of {valid_log_modes}")

        # 验证日志模板
        valid_templates = ['production', 'development', 'debugging', 'minimal']
        if self.log_template not in valid_templates:
            raise ValueError(f"Invalid log_template: {self.log_template}. Must be one of {valid_templates}")

        return True


# 全局配置实例
default_config = MiddlewareConfig.from_env()