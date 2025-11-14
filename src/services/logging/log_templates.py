"""
日志预设模板配置

提供生产、开发、调试等预设模板，包含详细的层级配置和输出控制。
"""

import logging
from typing import Dict
from .hierarchical_logger_config import LogMode, LayerLogConfig


class LogTemplates:
    """日志预设模板"""

    @staticmethod
    def get_production_template() -> Dict[LogMode, LayerLogConfig]:
        """生产环境模板 - 简洁输出，适合日常使用"""
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
                agent_level=logging.INFO,
                tool_level=logging.DEBUG,
                service_level=logging.INFO,
                enable_agent_details=True,
                enable_tool_details=True,
                enable_service_details=False,
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

    @staticmethod
    def get_development_template() -> Dict[LogMode, LayerLogConfig]:
        """开发环境模板 - 平衡输出，适合开发调试"""
        return {
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

    @staticmethod
    def get_debugging_template() -> Dict[LogMode, LayerLogConfig]:
        """调试环境模板 - 详细输出，适合深度调试"""
        return {
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

    @staticmethod
    def get_minimal_template() -> Dict[LogMode, LayerLogConfig]:
        """最小输出模板 - 只显示错误和关键信息"""
        return {
            LogMode.NORMAL: LayerLogConfig(
                agent_level=logging.ERROR,
                tool_level=logging.ERROR,
                service_level=logging.ERROR,
                enable_agent_details=False,
                enable_tool_details=False,
                enable_service_details=False,
                show_performance_metrics=False,
                show_cache_info=False,
                show_transaction_ids=False
            ),
            LogMode.DEBUG: LayerLogConfig(
                agent_level=logging.INFO,
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


class LogTemplateManager:
    """日志模板管理器"""

    TEMPLATES = {
        "production": LogTemplates.get_production_template,
        "development": LogTemplates.get_development_template,
        "debugging": LogTemplates.get_debugging_template,
        "minimal": LogTemplates.get_minimal_template
    }

    @classmethod
    def get_template(cls, template_name: str):
        """获取指定模板"""
        if template_name in cls.TEMPLATES:
            return cls.TEMPLATES[template_name]()
        else:
            # 默认返回生产模板
            return cls.TEMPLATES["production"]()

    @classmethod
    def list_templates(cls) -> list:
        """列出所有可用模板"""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def describe_template(cls, template_name: str) -> str:
        """描述模板特点"""
        descriptions = {
            "production": "生产环境模板 - 简洁输出，适合日常使用，只显示关键结果",
            "development": "开发环境模板 - 平衡输出，显示工具执行过程和性能指标",
            "debugging": "调试环境模板 - 详细输出，显示完整的执行过程和调试信息",
            "minimal": "最小输出模板 - 只显示错误信息，适合静默运行"
        }
        return descriptions.get(template_name, "未知模板")

    @classmethod
    def get_recommended_template(cls, use_case: str) -> str:
        """根据使用场景推荐模板"""
        recommendations = {
            "production": "production",
            "日常使用": "production",
            "开发调试": "development",
            "问题排查": "debugging",
            "静默运行": "minimal",
            "性能测试": "development",
            "API测试": "minimal",
            "CI/CD": "minimal"
        }
        return recommendations.get(use_case, "production")