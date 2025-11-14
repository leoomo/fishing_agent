"""
集成中间件系统

将LangChain意图识别中间件与现有的日志中间件集成，
提供统一的中间件管理接口。
"""

from typing import List, Optional, Any, Dict
import logging

from .logging_middleware import AgentLoggingMiddleware, MiddlewareConfig
from .langchain_intent_middleware import LangChainIntentMiddleware


class IntegratedMiddlewareManager:
    """
    集成中间件管理器

    功能：
    1. 统一管理多个中间件
    2. 提供简单的配置接口
    3. 协调不同中间件之间的交互
    4. 提供统一的性能统计
    """

    def __init__(self, config: Optional[MiddlewareConfig] = None,
                 enable_intent_enhancement: bool = True):
        """
        初始化集成中间件管理器

        Args:
            config: 中间件配置
            enable_intent_enhancement: 是否启用意图增强功能
        """
        self.config = config or MiddlewareConfig.from_env()
        self.enable_intent_enhancement = enable_intent_enhancement

        # 初始化日志中间件
        self.logging_middleware = None
        if self.config.enable_logging:
            try:
                self.logging_middleware = AgentLoggingMiddleware(config=self.config)
                self.logger = logging.getLogger('integrated.middleware')
                self.logger.info("集成中间件管理器初始化完成")
            except Exception as e:
                print(f"⚠️  日志中间件初始化失败: {e}")

        # 初始化意图增强中间件
        self.intent_middleware = None
        if self.enable_intent_enhancement and self.logging_middleware:
            try:
                self.intent_middleware = LangChainIntentMiddleware(self.logging_middleware)
                self.logger.info("意图增强中间件初始化完成")
            except Exception as e:
                print(f"⚠️  意图增强中间件初始化失败: {e}")

    def get_middleware_list(self) -> List[Any]:
        """
        获取中间件列表（用于LangChain Agent创建）

        Returns:
            中间件列表
        """
        middleware_list = []

        # 添加意图增强中间件（如果启用）
        if self.intent_middleware:
            middleware_list.append(self.intent_middleware)

        # 添加日志中间件
        if self.logging_middleware:
            # 注意：日志中间件可能需要特定的包装
            # 这里先直接添加，根据实际使用情况调整
            middleware_list.append(self.logging_middleware)

        return middleware_list

    def get_execution_summary(self) -> Optional[Dict[str, Any]]:
        """
        获取执行摘要

        Returns:
            包含所有中间件统计信息的字典
        """
        summary = {
            'middleware_status': {
                'logging_enabled': self.logging_middleware is not None,
                'intent_enhancement_enabled': self.intent_middleware is not None
            }
        }

        # 获取日志中间件统计
        if self.logging_middleware:
            logging_summary = self.logging_middleware.get_execution_summary()
            if logging_summary:
                summary['logging_stats'] = logging_summary

        # 获取意图增强统计
        if self.intent_middleware:
            intent_stats = self.intent_middleware.get_intent_stats()
            if intent_stats:
                summary['intent_stats'] = intent_stats

        return summary

    def reset_all_stats(self):
        """重置所有中间件的统计信息"""
        if self.logging_middleware:
            self.logging_middleware.reset_session_metrics()

        if self.intent_middleware:
            self.intent_middleware.reset_stats()

        self.logger.info("所有中间件统计信息已重置")

    def enable_performance_monitoring(self, enable: bool = True):
        """启用/禁用性能监控"""
        if self.config:
            self.config.enable_performance_monitoring = enable

        if self.logging_middleware:
            # 可能需要重新初始化或更新配置
            self.logging_middleware.config.enable_performance_monitoring = enable

        self.logger.info(f"性能监控已{'启用' if enable else '禁用'}")

    def enable_tool_tracking(self, enable: bool = True):
        """启用/禁用工具追踪"""
        if self.config:
            self.config.enable_tool_tracking = enable

        if self.logging_middleware:
            self.logging_middleware.config.enable_tool_tracking = enable

        self.logger.info(f"工具追踪已{'启用' if enable else '禁用'}")

    def set_log_level(self, level: str):
        """设置日志级别"""
        if self.config:
            self.config.log_level = level

        if self.logging_middleware:
            self.logging_middleware.config.log_level = level

        self.logger.info(f"日志级别已设置为: {level}")


# 便利函数：创建默认的集成中间件管理器
def create_integrated_middleware(enable_logging: bool = True,
                                enable_intent_enhancement: bool = True,
                                log_level: str = "INFO",
                                log_to_console: bool = True,
                                log_to_file: bool = False) -> IntegratedMiddlewareManager:
    """
    创建默认配置的集成中间件管理器

    Args:
        enable_logging: 是否启用日志记录
        enable_intent_enhancement: 是否启用意图增强
        log_level: 日志级别
        log_to_console: 是否输出到控制台
        log_to_file: 是否输出到文件

    Returns:
        配置好的集成中间件管理器
    """
    config = MiddlewareConfig(
        log_level=log_level,
        log_to_console=log_to_console,
        log_to_file=log_to_file,
        enable_performance_monitoring=True,
        enable_tool_tracking=True,
        enable_call_purpose_analysis=True
    )

    return IntegratedMiddlewareManager(
        config=config,
        enable_intent_enhancement=enable_intent_enhancement
    )


# 便利函数：为现有项目快速集成
def integrate_with_existing_agent(agent_class, middleware_manager: IntegratedMiddlewareManager):
    """
    将集成中间件管理器与现有的Agent类集成

    Args:
        agent_class: 现有的Agent类
        middleware_manager: 集成中间件管理器

    Returns:
        增强后的Agent类
    """
    class EnhancedAgent(agent_class):
        def __init__(self, *args, **kwargs):
            # 初始化原有Agent
            super().__init__(*args, **kwargs)

            # 集成中间件
            self.middleware_manager = middleware_manager
            self._setup_middleware()

        def _setup_middleware(self):
            """设置中间件"""
            # 如果Agent支持中间件设置，进行集成
            if hasattr(self, 'middleware'):
                # 获取现有中间件列表
                existing_middleware = getattr(self, 'middleware', [])
                new_middleware = self.middleware_manager.get_middleware_list()

                # 合并中间件列表
                combined_middleware = new_middleware + existing_middleware
                setattr(self, 'middleware', combined_middleware)

        def get_comprehensive_stats(self):
            """获取综合统计信息"""
            return self.middleware_manager.get_execution_summary()

        def reset_all_stats(self):
            """重置所有统计信息"""
            self.middleware_manager.reset_all_stats()

    return EnhancedAgent