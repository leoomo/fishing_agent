#!/usr/bin/env python3
"""
工具辅助函数
提供工具开发过程中的通用辅助功能
"""

import time
import functools
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
try:
    from .core.base_interfaces import ToolResult, ToolStatus
except ImportError:
    # 如果无法导入，定义简单的替代类
    class ToolStatus:
        SUCCESS = "success"
        ERROR = "error"

    class ToolResult:
        def __init__(self, status, data=None, message="", execution_time=0.0):
            self.status = status
            self.data = data
            self.message = message
            self.execution_time = execution_time

        def is_success(self):
            return self.status == ToolStatus.SUCCESS

        def is_error(self):
            return self.status == ToolStatus.ERROR

logger = logging.getLogger(__name__)

def tool_timer(func: Callable) -> Callable:
    """
    工具执行时间装饰器
    自动记录工具执行时间
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # 如果返回的是 ToolResult，更新执行时间
            if isinstance(result, ToolResult):
                result.execution_time = execution_time
                return result
            else:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=result,
                    execution_time=execution_time
                )
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                status=ToolStatus.ERROR,
                message=f"执行失败: {str(e)}",
                execution_time=execution_time
            )

    return wrapper

def tool_logger(log_level: int = logging.INFO) -> Callable:
    """
    工具日志装饰器
    自动记录工具调用日志
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(log_level, f"🔧 调用工具: {func.__name__} args={args} kwargs={kwargs}")

            try:
                result = func(*args, **kwargs)
                if isinstance(result, ToolResult):
                    if result.is_success():
                        logger.log(log_level, f"✅ 工具执行成功: {func.__name__}")
                    else:
                        logger.error(f"❌ 工具执行失败: {func.__name__} - {result.message}")
                else:
                    logger.log(log_level, f"✅ 工具执行成功: {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"💥 工具执行异常: {func.__name__} - {str(e)}")
                raise

        return wrapper
    return decorator

def input_validator(*validators: Callable) -> Callable:
    """
    输入验证装饰器
    支持多个验证函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for validator in validators:
                if not validator(*args, **kwargs):
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        message=f"输入参数验证失败: {validator.__name__}"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    失败重试装饰器
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # 如果是 ToolResult 且失败，进行重试
                    if isinstance(result, ToolResult) and result.is_error():
                        last_exception = Exception(result.message)
                        if attempt < max_retries:
                            logger.warning(f"⚠️ 工具执行失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {func.__name__}")
                            time.sleep(delay)
                            continue

                    return result

                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"⚠️ 工具执行异常，{delay}秒后重试 ({attempt + 1}/{max_retries}): {func.__name__} - {str(e)}")
                        time.sleep(delay)
                        continue

            # 所有重试都失败了
            return ToolResult(
                status=ToolStatus.ERROR,
                message=f"工具执行失败，已重试{max_retries}次: {str(last_exception)}"
            )

        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default_value: Any = None, **kwargs) -> ToolResult:
    """
    安全执行工具函数
    捕获异常并返回 ToolResult
    """
    try:
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        if isinstance(result, ToolResult):
            return result
        else:
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                execution_time=execution_time
            )

    except Exception as e:
        return ToolResult(
            status=ToolStatus.ERROR,
            message=f"执行异常: {str(e)}",
            data=default_value
        )

def cache_result(max_size: int = 100, ttl: Optional[float] = None) -> Callable:
    """
    结果缓存装饰器
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_timestamps = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 创建缓存键
            cache_key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()

            # 检查缓存
            if cache_key in cache:
                if ttl is None or (current_time - cache_timestamps[cache_key]) < ttl:
                    logger.debug(f"📋 使用缓存结果: {func.__name__}")
                    return cache[cache_key]
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
                    del cache_timestamps[cache_key]

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            if len(cache) >= max_size:
                # 删除最旧的缓存项
                oldest_key = min(cache_timestamps.keys(), key=cache_timestamps.get)
                del cache[oldest_key]
                del cache_timestamps[oldest_key]

            cache[cache_key] = result
            cache_timestamps[cache_key] = current_time

            return result

        return wrapper
    return decorator

def format_tool_output(data: Any, format_type: str = "str") -> str:
    """
    格式化工具输出
    """
    if format_type == "str":
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return "\n".join([f"{k}: {v}" for k, v in data.items()])
        elif isinstance(data, (list, tuple)):
            return "\n".join([str(item) for item in data])
        else:
            return str(data)
    elif format_type == "json":
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
    else:
        return str(data)

def validate_non_empty(*args) -> bool:
    """验证参数非空"""
    return all(arg is not None and arg != "" for arg in args)

def validate_positive_numbers(*args) -> bool:
    """验证参数为正数"""
    return all(isinstance(arg, (int, float)) and arg > 0 for arg in args)

def validate_string_length(min_length: int = 0, max_length: int = float('inf')):
    """验证字符串长度"""
    def validator(value: str) -> bool:
        return isinstance(value, str) and min_length <= len(value) <= max_length
    return validator

def validate_in_list(valid_values: List[Any]):
    """验证值在指定列表中"""
    def validator(value: Any) -> bool:
        return value in valid_values
    return validator

def batch_process(items: List[Any], processor: Callable, batch_size: int = 10) -> List[Any]:
    """
    批量处理工具
    将大量数据分批处理，避免内存溢出
    """
    results = []
    total_items = len(items)

    for i in range(0, total_items, batch_size):
        batch = items[i:i + batch_size]
        try:
            batch_results = processor(batch)
            results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
            logger.info(f"📦 批量处理进度: {min(i + batch_size, total_items)}/{total_items}")
        except Exception as e:
            logger.error(f"❌ 批量处理失败 (批次 {i//batch_size + 1}): {e}")
            # 继续处理下一批
            continue

    return results

def measure_performance(func: Callable, *args, num_runs: int = 100, **kwargs) -> Dict[str, float]:
    """
    性能测量工具
    """
    times = []
    success_count = 0

    for _ in range(num_runs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time

            times.append(execution_time)

            if isinstance(result, ToolResult) and result.is_success():
                success_count += 1
            else:
                success_count += 1  # 对于非 ToolResult，假设成功

        except Exception:
            # 失败的运行不计入时间统计
            continue

    if times:
        return {
            'average_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'success_rate': success_count / num_runs,
            'total_runs': num_runs
        }
    else:
        return {
            'average_time': 0.0,
            'min_time': 0.0,
            'max_time': 0.0,
            'success_rate': 0.0,
            'total_runs': num_runs
        }