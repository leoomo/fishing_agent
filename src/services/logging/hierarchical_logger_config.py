"""
分层日志配置管理器

支持三种日志模式（Normal/Debug/Error）和预设模板配置，
提供灵活的日志级别控制和输出管理。
"""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class LogMode(Enum):
    """日志模式枚举"""
    NORMAL = "normal"   # 简洁模式，适合日常使用
    DEBUG = "debug"     # 调试模式，显示详细过程
    ERROR = "error"     # 错误模式，只显示异常信息


class LogTemplate(Enum):
    """日志模板枚举"""
    PRODUCTION = "production"       # 生产环境模板
    DEVELOPMENT = "development"     # 开发环境模板
    DEBUGGING = "debugging"         # 调试环境模板


@dataclass
class LayerLogConfig:
    """层级日志配置"""
    agent_level: int = logging.INFO
    tool_level: int = logging.INFO
    service_level: int = logging.WARNING
    enable_agent_details: bool = False
    enable_tool_details: bool = False
    enable_service_details: bool = False
    show_performance_metrics: bool = False
    show_cache_info: bool = False
    show_transaction_ids: bool = False


@dataclass
class HierarchicalLoggerConfig:
    """分层日志配置管理器"""

    # 默认配置
    mode: LogMode = LogMode.NORMAL
    template: LogTemplate = LogTemplate.PRODUCTION
    layer_configs: Dict[LogMode, LayerLogConfig] = field(default_factory=dict)

    # 环境变量映射
    env_mappings = {
        'LOG_MODE': 'mode',
        'LOG_TEMPLATE': 'template',
        'DEBUG_LOGGING': 'debug_mode',
        'AGENT_LOG_LEVEL': 'agent_level',
        'LOG_AGENT_DETAILS': 'enable_agent_details',
        'LOG_TOOL_DETAILS': 'enable_tool_details',
        'LOG_SERVICE_DETAILS': 'enable_service_details',
        'LOG_PERFORMANCE_METRICS': 'show_performance_metrics',
        'LOG_CACHE_INFO': 'show_cache_info',
        'LOG_TRANSACTION_IDS': 'show_transaction_ids'
    }

    def __post_init__(self):
        """初始化后处理"""
        if not self.layer_configs:
            self.layer_configs = self._generate_default_configs()

        # 从环境变量加载配置
        self._load_from_env()

        # 应用模板配置
        self._apply_template()

    def _generate_default_configs(self) -> Dict[LogMode, LayerLogConfig]:
        """生成默认的层级配置"""
        return {
            LogMode.NORMAL: LayerLogConfig(
                agent_level=logging.INFO,
                tool_level=logging.INFO,
                service_level=logging.WARNING,
                enable_agent_details=False,
                enable_tool_details=False,
                enable_service_details=False,
                show_performance_metrics=False,
                show_cache_info=False,
                show_transaction_ids=False
            ),
            LogMode.DEBUG: LayerLogConfig(
                agent_level=logging.DEBUG,
                tool_level=logging.DEBUG,
                service_level=logging.INFO,
                enable_agent_details=True,
                enable_tool_details=True,
                enable_service_details=True,
                show_performance_metrics=True,
                show_cache_info=True,
                show_transaction_ids=True
            ),
            LogMode.ERROR: LayerLogConfig(
                agent_level=logging.ERROR,
                tool_level=logging.ERROR,
                service_level=logging.ERROR,
                enable_agent_details=True,
                enable_tool_details=True,
                enable_service_details=True,
                show_performance_metrics=True,
                show_cache_info=True,
                show_transaction_ids=True
            )
        }

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 处理LOG_MODE
        log_mode_env = os.getenv('LOG_MODE', '').lower()
        if log_mode_env:
            try:
                self.mode = LogMode(log_mode_env)
            except ValueError:
                print(f"⚠️ 无效的LOG_MODE值: {log_mode_env}，使用默认值: {self.mode.value}")

        # 处理DEBUG_LOGGING（向后兼容）
        if os.getenv('DEBUG_LOGGING', '').lower() == 'true' and self.mode == LogMode.NORMAL:
            self.mode = LogMode.DEBUG

        # 处理LOG_TEMPLATE
        log_template_env = os.getenv('LOG_TEMPLATE', '').lower()
        if log_template_env:
            try:
                self.template = LogTemplate(log_template_env)
            except ValueError:
                print(f"⚠️ 无效的LOG_TEMPLATE值: {log_template_env}，使用默认值: {self.template.value}")

        # 处理其他环境变量
        current_config = self.layer_configs[self.mode]

        # AGENT_LOG_LEVEL
        agent_level_env = os.getenv('AGENT_LOG_LEVEL', '').upper()
        if agent_level_env:
            try:
                level = getattr(logging, agent_level_env)
                current_config.agent_level = level
            except AttributeError:
                print(f"⚠️ 无效的AGENT_LOG_LEVEL值: {agent_level_env}")

        # 布尔值配置
        bool_configs = {
            'LOG_AGENT_DETAILS': 'enable_agent_details',
            'LOG_TOOL_DETAILS': 'enable_tool_details',
            'LOG_SERVICE_DETAILS': 'enable_service_details',
            'LOG_PERFORMANCE_METRICS': 'show_performance_metrics',
            'LOG_CACHE_INFO': 'show_cache_info',
            'LOG_TRANSACTION_IDS': 'show_transaction_ids'
        }

        for env_var, config_attr in bool_configs.items():
            env_value = os.getenv(env_var, '').lower()
            if env_value:
                setattr(current_config, config_attr, env_value == 'true')

    def _apply_template(self):
        """应用模板配置"""
        template_overrides = {
            LogTemplate.PRODUCTION: {
                LogMode.NORMAL: LayerLogConfig(
                    agent_level=logging.INFO,
                    tool_level=logging.INFO,
                    service_level=logging.WARNING,
                    enable_agent_details=False,
                    enable_tool_details=False,
                    enable_service_details=False,
                    show_performance_metrics=False,
                    show_cache_info=False,
                    show_transaction_ids=False
                )
            },
            LogTemplate.DEVELOPMENT: {
                LogMode.NORMAL: LayerLogConfig(
                    agent_level=logging.INFO,
                    tool_level=logging.DEBUG,
                    service_level=logging.INFO,
                    enable_agent_details=True,
                    enable_tool_details=True,
                    enable_service_details=False,
                    show_performance_metrics=True,
                    show_cache_info=True,
                    show_transaction_ids=False
                ),
                LogMode.DEBUG: LayerLogConfig(
                    agent_level=logging.DEBUG,
                    tool_level=logging.DEBUG,
                    service_level=logging.DEBUG,
                    enable_agent_details=True,
                    enable_tool_details=True,
                    enable_service_details=True,
                    show_performance_metrics=True,
                    show_cache_info=True,
                    show_transaction_ids=True
                )
            },
            LogTemplate.DEBUGGING: {
                LogMode.NORMAL: LayerLogConfig(
                    agent_level=logging.DEBUG,
                    tool_level=logging.DEBUG,
                    service_level=logging.DEBUG,
                    enable_agent_details=True,
                    enable_tool_details=True,
                    enable_service_details=True,
                    show_performance_metrics=True,
                    show_cache_info=True,
                    show_transaction_ids=True
                ),
                LogMode.DEBUG: LayerLogConfig(
                    agent_level=logging.DEBUG,
                    tool_level=logging.DEBUG,
                    service_level=logging.DEBUG,
                    enable_agent_details=True,
                    enable_tool_details=True,
                    enable_service_details=True,
                    show_performance_metrics=True,
                    show_cache_info=True,
                    show_transaction_ids=True
                )
            }
        }

        # 应用模板覆盖
        if self.template in template_overrides:
            overrides = template_overrides[self.template]
            if self.mode in overrides:
                # 合并配置，保留环境变量设置
                template_config = overrides[self.mode]
                current_config = self.layer_configs[self.mode]

                # 只覆盖未通过环境变量设置的值
                for attr_name in template_config.__dict__:
                    if attr_name not in ['agent_level'] or not os.getenv('AGENT_LOG_LEVEL'):
                        if not hasattr(self, '_env_overrides'):
                            self._env_overrides = set()
                        if attr_name not in self._env_overrides:
                            setattr(current_config, attr_name, getattr(template_config, attr_name))

    def get_layer_config(self, layer: str, mode: Optional[LogMode] = None) -> LayerLogConfig:
        """获取指定层级的配置"""
        target_mode = mode or self.mode
        return self.layer_configs[target_mode]

    def should_log(self, layer: str, level: int, mode: Optional[LogMode] = None) -> bool:
        """判断是否应该记录日志"""
        config = self.get_layer_config(layer, mode)

        if layer == 'agent':
            return level >= config.agent_level
        elif layer == 'tool':
            return level >= config.tool_level
        elif layer == 'service':
            return level >= config.service_level
        else:
            return level >= logging.INFO

    def should_show_details(self, layer: str, detail_type: str, mode: Optional[LogMode] = None) -> bool:
        """判断是否应该显示详细信息"""
        config = self.get_layer_config(layer, mode)

        detail_mapping = {
            'agent_details': config.enable_agent_details,
            'tool_details': config.enable_tool_details,
            'service_details': config.enable_service_details,
            'performance_metrics': config.show_performance_metrics,
            'cache_info': config.show_cache_info,
            'transaction_ids': config.show_transaction_ids
        }

        return detail_mapping.get(detail_type, False)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'mode': self.mode.value,
            'template': self.template.value,
            'layer_configs': {
                mode.value: {
                    'agent_level': config.agent_level,
                    'tool_level': config.tool_level,
                    'service_level': config.service_level,
                    'enable_agent_details': config.enable_agent_details,
                    'enable_tool_details': config.enable_tool_details,
                    'enable_service_details': config.enable_service_details,
                    'show_performance_metrics': config.show_performance_metrics,
                    'show_cache_info': config.show_cache_info,
                    'show_transaction_ids': config.show_transaction_ids
                }
                for mode, config in self.layer_configs.items()
            }
        }

    @classmethod
    def from_env(cls) -> 'HierarchicalLoggerConfig':
        """从环境变量创建配置"""
        return cls()


# 全局配置实例
default_hierarchical_config = HierarchicalLoggerConfig.from_env()