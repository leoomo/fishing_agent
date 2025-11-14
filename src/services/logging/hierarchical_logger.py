"""
分层日志记录器

扩展现有的EnhancedBusinessLogger，支持模式化输出控制和层级管理。
根据配置动态调整日志输出的详细程度。
"""

import logging
import time
import uuid
import os
from typing import Optional, Dict, Any, Union
from functools import wraps

from .hierarchical_logger_config import HierarchicalLoggerConfig, LogMode, default_hierarchical_config


def hierarchical_log_function(func):
    """
    分层函数日志装饰器
    根据当前配置决定日志输出的详细程度
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # 获取logger和配置
        logger = getattr(self, '_logger', logging.getLogger(self.__class__.__name__))
        config = getattr(self, '_hierarchical_config', default_hierarchical_config)

        # 确定层级
        layer = getattr(self, '_log_layer', 'tool')

        # 检查是否应该记录此函数
        if not config.should_log(layer, logging.INFO):
            return func(self, *args, **kwargs)

        # 生成事务ID（如果需要）
        transaction_id = None
        if config.should_show_details(layer, 'transaction_ids'):
            transaction_id = str(uuid.uuid4())[:8]

        function_name = f"{self.__class__.__name__}.{func.__name__}"
        start_time = time.time()

        # 记录函数开始
        if config.should_show_details(layer, 'tool_details'):
            start_msg = f"[{transaction_id}] 🚀 开始执行 {function_name}" if transaction_id else f"🚀 开始执行 {function_name}"
            logger.info(start_msg)

            if config.should_show_details(layer, 'tool_details'):
                # 只在DEBUG模式下显示参数
                if config.mode == LogMode.DEBUG:
                    logger.debug(f"[{transaction_id}] 📥 输入参数: args={args}, kwargs={kwargs}" if transaction_id else f"📥 输入参数: args={args}, kwargs={kwargs}")

        try:
            # 执行函数
            result = func(self, *args, **kwargs)

            # 计算执行时间
            execution_time = time.time() - start_time

            # 记录成功结果
            if config.should_show_details(layer, 'tool_details'):
                success_msg = f"[{transaction_id}] ✅ {function_name} 执行成功 ({execution_time:.3f}s)" if transaction_id else f"✅ {function_name} 执行成功 ({execution_time:.3f}s)"
                logger.info(success_msg)

                if config.mode == LogMode.DEBUG and hasattr(result, 'data') and result.data:
                    logger.debug(f"[{transaction_id}] 📤 返回数据: {type(result.data).__name__}" if transaction_id else f"📤 返回数据: {type(result.data).__name__}")

            # 为结果添加事务ID和执行时间
            if hasattr(result, 'metadata') and transaction_id:
                result.metadata['transaction_id'] = transaction_id
                result.metadata['execution_time'] = execution_time
                if config.should_show_details(layer, 'performance_metrics'):
                    result.metadata['layer'] = layer
                    result.metadata['log_mode'] = config.mode.value

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            # 错误模式下记录完整异常信息
            if config.mode == LogMode.ERROR or config.should_show_details(layer, 'tool_details'):
                error_msg = f"[{transaction_id}] 💥 {function_name} 执行异常 ({execution_time:.3f}s): {str(e)}" if transaction_id else f"💥 {function_name} 执行异常 ({execution_time:.3f}s): {str(e)}"
                logger.error(error_msg)

                if config.mode == LogMode.ERROR:
                    logger.debug(f"[{transaction_id}] 📋 异常堆栈: {e.__class__.__name__}: {str(e)}" if transaction_id else f"📋 异常堆栈: {e.__class__.__name__}: {str(e)}")
            raise

    return wrapper


class HierarchicalLogger:
    """
    分层日志记录器

    提供统一的日志接口，根据配置动态调整输出详细程度。
    支持Agent、Tool、Service三个层级的独立配置。
    """

    def __init__(self, name: str, layer: str = "tool",
                 config: Optional[HierarchicalLoggerConfig] = None):
        """
        初始化分层日志记录器

        Args:
            name: logger名称
            layer: 日志层级 (agent/tool/service)
            config: 分层日志配置
        """
        self.name = name
        self.layer = layer
        self._config = config or default_hierarchical_config
        self._logger = logging.getLogger(f"hierarchical.{layer}.{name}")

        # 设置logger级别
        layer_config = self._config.get_layer_config(layer)
        self._logger.setLevel(min(layer_config.agent_level, layer_config.tool_level, layer_config.service_level))

        # 如果logger没有handler，添加默认handler
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.propagate = True

    def should_log(self, level: int) -> bool:
        """判断是否应该记录指定级别的日志"""
        return self._config.should_log(self.layer, level)

    def should_show_details(self, detail_type: str) -> bool:
        """判断是否应该显示详细信息"""
        return self._config.should_show_details(self.layer, detail_type)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        if self.should_log(logging.INFO):
            self._logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        if self.should_log(logging.DEBUG):
            self._logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        if self.should_log(logging.WARNING):
            self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        if self.should_log(logging.ERROR):
            self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        if self.should_log(logging.CRITICAL):
            self._logger.critical(message, **kwargs)

    def log_with_mode(self, level: str, message: str, mode: Optional[LogMode] = None, **kwargs):
        """根据指定模式记录日志"""
        target_mode = mode or self._config.mode
        original_mode = self._config.mode

        # 临时切换模式
        self._config.mode = target_mode

        try:
            getattr(self, level.lower())(message, **kwargs)
        finally:
            # 恢复原模式
            self._config.mode = original_mode

    def log_function_start(self, function_name: str, args: tuple = (), kwargs: dict = None,
                          transaction_id: Optional[str] = None):
        """记录函数开始"""
        if not self.should_show_details('tool_details'):
            return

        kwargs = kwargs or {}

        if transaction_id and self.should_show_details('transaction_ids'):
            start_msg = f"[{transaction_id}] 🚀 开始执行 {function_name}"
        else:
            start_msg = f"🚀 开始执行 {function_name}"

        self.info(start_msg)

        if self._config.mode == LogMode.DEBUG:
            if transaction_id and self.should_show_details('transaction_ids'):
                self.debug(f"[{transaction_id}] 📥 输入参数: args={args}, kwargs={kwargs}")
            else:
                self.debug(f"📥 输入参数: args={args}, kwargs={kwargs}")

    def log_function_success(self, function_name: str, execution_time: float,
                           transaction_id: Optional[str] = None, result_info: Optional[str] = None):
        """记录函数成功完成"""
        if not self.should_show_details('tool_details'):
            return

        if transaction_id and self.should_show_details('transaction_ids'):
            success_msg = f"[{transaction_id}] ✅ {function_name} 执行成功 ({execution_time:.3f}s)"
        else:
            success_msg = f"✅ {function_name} 执行成功 ({execution_time:.3f}s)"

        self.info(success_msg)

        if result_info and self._config.mode == LogMode.DEBUG:
            if transaction_id and self.should_show_details('transaction_ids'):
                self.debug(f"[{transaction_id}] 📋 结果信息: {result_info}")
            else:
                self.debug(f"📋 结果信息: {result_info}")

    def log_function_error(self, function_name: str, execution_time: float,
                          error: Exception, transaction_id: Optional[str] = None):
        """记录函数执行错误"""
        if self._config.mode == LogMode.ERROR or self.should_show_details('tool_details'):
            if transaction_id and self.should_show_details('transaction_ids'):
                error_msg = f"[{transaction_id}] 💥 {function_name} 执行异常 ({execution_time:.3f}s): {str(error)}"
            else:
                error_msg = f"💥 {function_name} 执行异常 ({execution_time:.3f}s): {str(error)}"

            self.error(error_msg)

            if self._config.mode == LogMode.ERROR:
                if transaction_id and self.should_show_details('transaction_ids'):
                    self.debug(f"[{transaction_id}] 📋 异常堆栈: {error.__class__.__name__}: {str(error)}")
                else:
                    self.debug(f"📋 异常堆栈: {error.__class__.__name__}: {str(error)}")

    def log_performance_metrics(self, operation: str, metrics: Dict[str, Any]):
        """记录性能指标"""
        if not self.should_show_details('performance_metrics'):
            return

        metrics_parts = []
        for key, value in metrics.items():
            if isinstance(value, float):
                metrics_parts.append(f"{key}={value:.3f}")
            else:
                metrics_parts.append(f"{key}={value}")

        metrics_str = ", ".join(metrics_parts)
        self.info(f"📊 {operation} 性能指标: {metrics_str}")

    def log_cache_info(self, operation: str, cache_hit: bool, hit_rate: Optional[float] = None):
        """记录缓存信息"""
        if not self.should_show_details('cache_info'):
            return

        if cache_hit:
            self.info(f"💾 {operation} 缓存命中")
        else:
            self.info(f"❌ {operation} 缓存未命中")

        if hit_rate is not None:
            self.info(f"📊 缓存命中率: {hit_rate:.1f}%")

    def get_config(self) -> HierarchicalLoggerConfig:
        """获取当前配置"""
        return self._config

    def set_mode(self, mode: LogMode):
        """动态设置日志模式"""
        self._config.mode = mode

        # 重新设置logger级别
        layer_config = self._config.get_layer_config(self.layer)
        self._logger.setLevel(min(layer_config.agent_level, layer_config.tool_level, layer_config.service_level))

    def create_child_logger(self, name: str, layer: Optional[str] = None) -> 'HierarchicalLogger':
        """创建子logger"""
        child_layer = layer or self.layer
        child_name = f"{self.name}.{name}"
        return HierarchicalLogger(child_name, child_layer, self._config)


# 便捷函数
def get_hierarchical_logger(name: str, layer: str = "tool",
                           config: Optional[HierarchicalLoggerConfig] = None) -> HierarchicalLogger:
    """获取分层日志记录器实例"""
    return HierarchicalLogger(name, layer, config)


def create_logger_with_mode(name: str, layer: str = "tool", mode: LogMode = LogMode.NORMAL) -> HierarchicalLogger:
    """创建指定模式的分层日志记录器"""
    config = HierarchicalLoggerConfig(mode=mode)
    return HierarchicalLogger(name, layer, config)