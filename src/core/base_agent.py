"""
LangChain Learning - Base Agent

提供智能体的基础实现，包含通用的智能体功能和工具管理。
"""

from typing import List, Dict, Any, Optional
import logging
import asyncio
from .interfaces import IAgent, ITool, AgentConfig


class BaseAgent(IAgent):
    """智能体基类，提供通用的智能体功能"""

    def __init__(self, config: AgentConfig, logger: Optional[logging.Logger] = None):
        self._config = config
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._tools: Dict[str, ITool] = {}
        self._initialized = False
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }

    @property
    def config(self) -> AgentConfig:
        """获取智能体配置"""
        return self._config

    @property
    def logger(self) -> logging.Logger:
        """获取日志器"""
        return self._logger

    @property
    def tools(self) -> Dict[str, ITool]:
        """获取工具字典"""
        return self._tools.copy()

    def is_initialized(self) -> bool:
        """检查智能体是否已初始化"""
        return self._initialized

    async def initialize(self) -> None:
        """初始化智能体"""
        if not self._initialized:
            self._logger.info(f"Initializing agent: {self._config.name}")
            await self._on_initialize()
            
            # 初始化所有工具
            for tool_name, tool in self._tools.items():
                if hasattr(tool, 'initialize'):
                    await tool.initialize()
            
            self._initialized = True
            self._logger.info(f"Agent initialized: {self._config.name}")

    async def _on_initialize(self) -> None:
        """初始化钩子方法（子类可重写）"""
        pass

    async def cleanup(self) -> None:
        """清理智能体资源"""
        if self._initialized:
            self._logger.info(f"Cleaning up agent: {self._config.name}")
            await self._on_cleanup()
            
            # 清理所有工具
            for tool_name, tool in self._tools.items():
                if hasattr(tool, 'cleanup'):
                    await tool.cleanup()
            
            self._initialized = False
            self._logger.info(f"Agent cleaned up: {self._config.name}")

    async def _on_cleanup(self) -> None:
        """清理钩子方法（子类可重写）"""
        pass

    def add_tool(self, tool: ITool) -> None:
        """添加工具"""
        if not isinstance(tool, ITool):
            raise ValueError(f"Tool must implement ITool interface: {type(tool)}")

        tool_name = tool.metadata.name
        if tool_name in self._tools:
            self._logger.warning(f"Tool '{tool_name}' already exists, overwriting")

        self._tools[tool_name] = tool
        self._logger.info(f"Tool added to agent: {tool_name}")

    def remove_tool(self, tool_name: str) -> None:
        """移除工具"""
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            if hasattr(tool, 'cleanup'):
                if asyncio.iscoroutinefunction(tool.cleanup):
                    asyncio.create_task(tool.cleanup())
                else:
                    tool.cleanup()
            del self._tools[tool_name]
            self._logger.info(f"Tool removed from agent: {tool_name}")
        else:
            self._logger.warning(f"Tool '{tool_name}' not found in agent")

    def has_tool(self, tool_name: str) -> bool:
        """检查是否包含指定工具"""
        return tool_name in self._tools

    def get_tool(self, tool_name: str) -> Optional[ITool]:
        """获取工具"""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行指定工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        self._logger.debug(f"Executing tool: {tool_name}")
        result = await tool(**kwargs)
        self._logger.debug(f"Tool execution completed: {tool_name}")
        return result

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        stats = self._execution_stats.copy()
        if stats["total_executions"] > 0:
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
            stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
        else:
            stats["average_execution_time"] = 0.0
            stats["success_rate"] = 0.0
        return stats

    def reset_execution_stats(self) -> None:
        """重置执行统计"""
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }

    async def run(self, query: str) -> str:
        """运行智能体（子类必须重写）"""
        if not self._initialized:
            await self.initialize()

        import time
        start_time = time.time()

        try:
            self._logger.info(f"Running agent: {self._config.name} with query: {query[:100]}...")
            result = await self._run(query)
            
            self._execution_stats["successful_executions"] += 1
            self._logger.info(f"Agent execution completed successfully")
            
            return result

        except Exception as e:
            self._execution_stats["failed_executions"] += 1
            self._logger.error(f"Agent execution failed: {str(e)}")
            raise e

        finally:
            execution_time = time.time() - start_time
            self._execution_stats["total_executions"] += 1
            self._execution_stats["total_execution_time"] += execution_time

    async def _run(self, query: str) -> str:
        """运行钩子方法（子类必须重写）"""
        raise NotImplementedError("Subclasses must implement _run method")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(name='{self._config.name}', tools={len(self._tools)})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (f"{self.__class__.__name__}(name='{self._config.name}', "
                f"model='{self._config.model}', tools={list(self._tools.keys())})")


class ConfigurableAgent(BaseAgent):
    """可配置的智能体基类"""

    def __init__(self, config: AgentConfig, additional_config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._additional_config = additional_config or {}

    def get_additional_config(self, key: str, default: Any = None) -> Any:
        """获取额外配置"""
        return self._additional_config.get(key, default)

    def set_additional_config(self, key: str, value: Any) -> None:
        """设置额外配置"""
        self._additional_config[key] = value

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新额外配置"""
        self._additional_config.update(new_config)