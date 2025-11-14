"""
LangChain Learning - Base Tool

提供工具的基础实现，包含通用的工具功能和便利方法。
"""

from typing import Any, Dict, Optional
import logging
import asyncio
from .interfaces import ITool, ToolMetadata, ToolResult


class BaseTool(ITool):
    """工具基类，提供通用的工具功能"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._initialized = False

    @property
    def logger(self) -> logging.Logger:
        """获取日志器"""
        return self._logger

    async def initialize(self) -> None:
        """初始化工具（子类可重写）"""
        if not self._initialized:
            self._logger.info(f"Initializing tool: {self.metadata.name}")
            await self._on_initialize()
            self._initialized = True
            self._logger.info(f"Tool initialized: {self.metadata.name}")

    async def _on_initialize(self) -> None:
        """初始化钩子方法（子类可重写）"""
        pass

    async def cleanup(self) -> None:
        """清理工具资源（子类可重写）"""
        if self._initialized:
            self._logger.info(f"Cleaning up tool: {self.metadata.name}")
            await self._on_cleanup()
            self._initialized = False
            self._logger.info(f"Tool cleaned up: {self.metadata.name}")

    async def _on_cleanup(self) -> None:
        """清理钩子方法（子类可重写）"""
        pass

    def is_initialized(self) -> bool:
        """检查工具是否已初始化"""
        return self._initialized

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数（子类应重写）"""
        return True

    def _validate_required_params(self, required_params: list, **kwargs) -> bool:
        """验证必需参数"""
        for param in required_params:
            if param not in kwargs or kwargs[param] is None:
                self._logger.error(f"Missing required parameter: {param}")
                return False
        return True

    async def execute(self, **kwargs) -> ToolResult:
        """执行工具逻辑（子类必须重写）"""
        if not self._initialized:
            await self.initialize()

        try:
            self._logger.debug(f"Executing tool {self.metadata.name} with params: {kwargs}")
            result = await self._execute(**kwargs)
            self._logger.debug(f"Tool {self.metadata.name} execution completed")
            return result
        except Exception as e:
            self._logger.error(f"Tool {self.metadata.name} execution failed: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e)
            )

    async def _execute(self, **kwargs) -> ToolResult:
        """执行钩子方法（子类必须重写）"""
        raise NotImplementedError("Subclasses must implement _execute method")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


class ConfigurableTool(BaseTool):
    """可配置的工具基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self._config = config or {}
        self._validate_config()

    def _validate_config(self) -> None:
        """验证配置（子类可重写）"""
        pass

    @property
    def config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._config.copy()

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置"""
        self._config.update(new_config)
        self._validate_config()


class AsyncTool(BaseTool):
    """异步工具基类，专门用于处理I/O密集型操作"""

    def __init__(self, timeout: Optional[float] = None, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self._timeout = timeout

    async def execute_with_timeout(self, **kwargs) -> ToolResult:
        """带超时的执行"""
        try:
            if self._timeout:
                return await asyncio.wait_for(
                    self.execute(**kwargs),
                    timeout=self._timeout
                )
            else:
                return await self.execute(**kwargs)
        except asyncio.TimeoutError:
            self._logger.error(f"Tool {self.metadata.name} execution timed out")
            return ToolResult(
                success=False,
                error=f"Execution timed out after {self._timeout} seconds"
            )