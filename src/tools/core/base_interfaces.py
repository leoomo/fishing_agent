#!/usr/bin/env python3
"""
基础工具接口定义
提供标准化的工具接口和数据结构
"""

from typing import Any, Dict, Optional, Union, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class ToolStatus(Enum):
    """工具执行状态"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"

@dataclass
class ToolResult:
    """工具执行结果"""
    status: ToolStatus
    data: Any = None
    message: str = ""
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    tool_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_success(self) -> bool:
        """判断执行是否成功"""
        return self.status == ToolStatus.SUCCESS

    def is_error(self) -> bool:
        """判断执行是否出错"""
        return self.status == ToolStatus.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'status': self.status.value,
            'data': self.data,
            'message': self.message,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
            'tool_id': self.tool_id
        }

class BaseTool:
    """基础工具抽象类"""

    def __init__(self, name: str, description: str = "", category: str = "general"):
        self.name = name
        self.description = description
        self.category = category
        self.enabled = True
        self._config: Dict[str, Any] = {}
        self._stats = {
            'call_count': 0,
            'success_count': 0,
            'error_count': 0,
            'total_time': 0.0
        }

    def configure(self, **kwargs) -> None:
        """配置工具参数"""
        self._config.update(kwargs)

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置参数"""
        return self._config.get(key, default)

    def enable(self) -> None:
        """启用工具"""
        self.enabled = True

    def disable(self) -> None:
        """禁用工具"""
        self.enabled = False

    def is_enabled(self) -> bool:
        """检查工具是否启用"""
        return self.enabled

    def validate_input(self, *args, **kwargs) -> bool:
        """验证输入参数"""
        return True

    def execute(self, *args, **kwargs) -> ToolResult:
        """
        执行工具功能（需要子类实现）

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            ToolResult: 执行结果
        """
        raise NotImplementedError("子类必须实现 execute 方法")

    def _execute_with_stats(self, *args, **kwargs) -> ToolResult:
        """带统计信息的执行"""
        start_time = datetime.now()

        try:
            self._stats['call_count'] += 1

            # 验证输入
            if not self.validate_input(*args, **kwargs):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    message=f"输入参数验证失败: {args}, {kwargs}"
                )

            # 执行工具
            result = self.execute(*args, **kwargs)

            # 更新统计
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            self._stats['total_time'] += execution_time

            if result.is_success():
                self._stats['success_count'] += 1
            else:
                self._stats['error_count'] += 1

            result.execution_time = execution_time
            return result

        except Exception as e:
            self._stats['error_count'] += 1
            return ToolResult(
                status=ToolStatus.ERROR,
                message=f"工具执行异常: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def get_stats(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        avg_time = 0.0
        if self._stats['call_count'] > 0:
            avg_time = self._stats['total_time'] / self._stats['call_count']

        success_rate = 0.0
        if self._stats['call_count'] > 0:
            success_rate = self._stats['success_count'] / self._stats['call_count']

        return {
            'name': self.name,
            'category': self.category,
            'enabled': self.enabled,
            'call_count': self._stats['call_count'],
            'success_count': self._stats['success_count'],
            'error_count': self._stats['error_count'],
            'success_rate': success_rate,
            'total_time': self._stats['total_time'],
            'average_time': avg_time
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            'call_count': 0,
            'success_count': 0,
            'error_count': 0,
            'total_time': 0.0
        }

    def __str__(self) -> str:
        return f"BaseTool(name='{self.name}', category='{self.category}', enabled={self.enabled})"

    def __repr__(self) -> str:
        return self.__str__()

# 便捷函数装饰器
def simple_tool(category: str = "general", description: str = ""):
    """
    简单工具装饰器
    将普通函数转换为工具
    """
    def decorator(func):
        class SimpleToolWrapper(BaseTool):
            def __init__(self, name, description, category):
                super().__init__(name, description, category)
                self._func = func

            def execute(self, *args, **kwargs) -> ToolResult:
                try:
                    result = self._func(*args, **kwargs)
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data=result,
                        message="执行成功"
                    )
                except Exception as e:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        message=f"执行失败: {str(e)}"
                    )

        wrapper = SimpleToolWrapper(
            name=func.__name__,
            description=description or func.__doc__ or "",
            category=category
        )

        # 保存原始函数
        wrapper._original_func = func

        return wrapper

    return decorator

# 工具上下文管理器
class ToolContext:
    """工具执行上下文"""

    def __init__(self):
        self._variables: Dict[str, Any] = {}
        self._history: List[ToolResult] = []

    def set_variable(self, name: str, value: Any) -> None:
        """设置上下文变量"""
        self._variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取上下文变量"""
        return self._variables.get(name, default)

    def add_result(self, result: ToolResult) -> None:
        """添加执行结果到历史"""
        self._history.append(result)

    def get_history(self, limit: int = 10) -> List[ToolResult]:
        """获取执行历史"""
        return self._history[-limit:] if limit > 0 else self._history

    def clear(self) -> None:
        """清空上下文"""
        self._variables.clear()
        self._history.clear()