"""
LangChain Learning - Core Interfaces

定义了系统中所有核心接口，确保模块间的标准通信和互操作性。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class ToolMetadata(BaseModel):
    """工具元数据"""
    name: str
    description: str
    version: str
    author: str
    tags: List[str] = []
    dependencies: List[str] = []


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    execution_time: Optional[float] = None
    timestamp: datetime = datetime.now()


class ITool(ABC):
    """工具接口基类"""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具逻辑"""
        pass

    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        pass

    async def __call__(self, **kwargs) -> ToolResult:
        """调用工具的便捷方法"""
        import time
        start_time = time.time()

        try:
            if not self.validate_input(**kwargs):
                return ToolResult(
                    success=False,
                    error="Invalid input parameters"
                )

            result = await self.execute(**kwargs)
            result.execution_time = time.time() - start_time
            return result

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )


class AgentConfig(BaseModel):
    """智能体配置"""
    name: str
    model: str
    system_prompt: str
    tools: List[str] = []
    max_iterations: int = 10
    verbose: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30


class IAgent(ABC):
    """智能体接口基类"""

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """智能体配置"""
        pass

    @abstractmethod
    async def run(self, query: str) -> str:
        """运行智能体"""
        pass

    @abstractmethod
    def add_tool(self, tool: ITool) -> None:
        """添加工具"""
        pass

    @abstractmethod
    def remove_tool(self, tool_name: str) -> None:
        """移除工具"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """初始化智能体"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass


class ServiceConfig(BaseModel):
    """服务配置"""
    name: str
    version: str
    enabled: bool = True
    config: Dict[str, Any] = {}


class IService(ABC):
    """服务接口基类"""

    @property
    @abstractmethod
    def config(self) -> ServiceConfig:
        """服务配置"""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理服务"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass


class IRegistry(ABC):
    """注册器接口"""

    @abstractmethod
    def register(self, name: str, item: Any) -> None:
        """注册项"""
        pass

    @abstractmethod
    def get(self, name: str) -> Optional[Any]:
        """获取项"""
        pass

    @abstractmethod
    def list_all(self) -> List[str]:
        """列出所有项"""
        pass

    @abstractmethod
    def unregister(self, name: str) -> bool:
        """注销项"""
        pass