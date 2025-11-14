"""
LangChain Learning - Tool Registry

工具注册器负责管理系统中所有工具的注册、发现和调用。
支持动态注册、延迟加载和热更新。
"""

import importlib
import pkgutil
from typing import Dict, List, Type, Optional, Any
import inspect
import asyncio
from .interfaces import ITool, IRegistry


class ToolRegistry(IRegistry):
    """工具注册器"""

    def __init__(self):
        self._tools: Dict[str, ITool] = {}
        self._tool_classes: Dict[str, Type[ITool]] = {}
        self._tool_instances: Dict[str, ITool] = {}
        self._discovery_cache: Dict[str, bool] = {}

    def register(self, name: str, tool: ITool) -> None:
        """注册工具实例"""
        if not isinstance(tool, ITool):
            raise ValueError(f"Tool must implement ITool interface: {type(tool)}")

        if name in self._tools:
            print(f"Warning: Tool '{name}' already registered, overwriting")

        self._tools[name] = tool
        print(f"Tool registered: {name}")

    def register_class(self, tool_class: Type[ITool], name: Optional[str] = None) -> None:
        """注册工具类（延迟实例化）"""
        if not (isinstance(tool_class, type) and issubclass(tool_class, ITool)):
            raise ValueError(f"Tool class must inherit from ITool: {tool_class}")

        # 创建临时实例获取元数据
        temp_instance = tool_class()
        tool_name = name or temp_instance.metadata.name

        if tool_name in self._tool_classes:
            print(f"Warning: Tool class '{tool_name}' already registered, overwriting")

        self._tool_classes[tool_name] = tool_class
        print(f"Tool class registered: {tool_name}")

    def get(self, name: str) -> Optional[ITool]:
        """获取工具实例"""
        # 优先返回已实例化的工具
        if name in self._tools:
            return self._tools[name]

        # 尝试从注册的类创建实例
        if name in self._tool_classes:
            tool = self._tool_classes[name]()
            self._tools[name] = tool
            return tool

        return None

    async def get_async(self, name: str) -> Optional[ITool]:
        """异步获取工具实例"""
        tool = self.get(name)
        if tool and hasattr(tool, 'initialize'):
            await tool.initialize()
        return tool

    def list_all(self) -> List[str]:
        """列出所有已注册的工具名称"""
        all_tools = set(self._tools.keys()) | set(self._tool_classes.keys())
        return sorted(list(all_tools))

    def list_metadata(self) -> List[Dict[str, Any]]:
        """列出所有工具的元数据"""
        metadata_list = []

        # 处理已实例化的工具
        for tool in self._tools.values():
            metadata_list.append(tool.metadata.dict())

        # 处理注册的工具类
        for tool_class in self._tool_classes.values():
            temp_instance = tool_class()
            metadata_list.append(temp_instance.metadata.dict())

        return metadata_list

    def unregister(self, name: str) -> bool:
        """注销工具"""
        removed = False

        if name in self._tools:
            tool = self._tools[name]
            if hasattr(tool, 'cleanup'):
                # 异步清理资源
                if asyncio.iscoroutinefunction(tool.cleanup):
                    asyncio.create_task(tool.cleanup())
                else:
                    tool.cleanup()
            del self._tools[name]
            removed = True

        if name in self._tool_classes:
            del self._tool_classes[name]
            removed = True

        if removed:
            print(f"Tool unregistered: {name}")

        return removed

    async def unregister_async(self, name: str) -> bool:
        """异步注销工具"""
        if name in self._tools:
            tool = self._tools[name]
            if hasattr(tool, 'cleanup'):
                await tool.cleanup()
            del self._tools[name]
            return True

        if name in self._tool_classes:
            del self._tool_classes[name]
            return True

        return False

    def discover_tools(self, package_name: str) -> List[str]:
        """自动发现指定包中的工具"""
        if package_name in self._discovery_cache:
            return []

        discovered_tools = []

        try:
            package = importlib.import_module(package_name)

            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                full_module_name = f"{package_name}.{module_name}"

                try:
                    module = importlib.import_module(full_module_name)

                    # 查找模块中的工具类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        if (isinstance(attr, type) and
                            issubclass(attr, ITool) and
                            attr != ITool):
                            
                            try:
                                self.register_class(attr)
                                discovered_tools.append(attr_name)
                            except Exception as e:
                                print(f"Failed to register tool {attr_name}: {e}")

                except ImportError as e:
                    print(f"Failed to import module {full_module_name}: {e}")

        except ImportError as e:
            print(f"Failed to discover tools in package {package_name}: {e}")

        self._discovery_cache[package_name] = True
        return discovered_tools

    def clear(self) -> None:
        """清空所有注册的工具"""
        # 清理资源
        for tool in self._tools.values():
            if hasattr(tool, 'cleanup'):
                if asyncio.iscoroutinefunction(tool.cleanup):
                    asyncio.create_task(tool.cleanup())
                else:
                    tool.cleanup()

        self._tools.clear()
        self._tool_classes.clear()
        self._tool_instances.clear()
        self._discovery_cache.clear()

    async def clear_async(self) -> None:
        """异步清空所有注册的工具"""
        for tool in self._tools.values():
            if hasattr(tool, 'cleanup'):
                await tool.cleanup()

        self._tools.clear()
        self._tool_classes.clear()
        self._tool_instances.clear()
        self._discovery_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取注册器统计信息"""
        return {
            "total_tools": len(self.list_all()),
            "instantiated_tools": len(self._tools),
            "registered_classes": len(self._tool_classes),
            "discovered_packages": len(self._discovery_cache)
        }


class ServiceRegistry(IRegistry):
    """服务注册器"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._service_classes: Dict[str, Type] = {}

    def register(self, name: str, service: Any) -> None:
        """注册服务实例"""
        self._services[name] = service

    def register_class(self, name: str, service_class: Type) -> None:
        """注册服务类"""
        self._service_classes[name] = service_class

    def get(self, name: str) -> Optional[Any]:
        """获取服务实例"""
        if name in self._services:
            return self._services[name]

        if name in self._service_classes:
            service = self._service_classes[name]()
            self._services[name] = service
            return service

        return None

    def list_all(self) -> List[str]:
        """列出所有已注册的服务名称"""
        return sorted(list(set(self._services.keys()) | set(self._service_classes.keys())))

    def unregister(self, name: str) -> bool:
        """注销服务"""
        removed = False

        if name in self._services:
            del self._services[name]
            removed = True

        if name in self._service_classes:
            del self._service_classes[name]
            removed = True

        return removed

    async def initialize_all(self) -> None:
        """初始化所有服务"""
        init_tasks = []

        for service in self._services.values():
            if hasattr(service, 'initialize'):
                init_tasks.append(service.initialize())

        for name in list(self._service_classes.keys()):
            service_class = self._service_classes[name]
            if name not in self._services:
                service = service_class()
                self._services[name] = service
                if hasattr(service, 'initialize'):
                    init_tasks.append(service.initialize())

        if init_tasks:
            await asyncio.gather(*init_tasks, return_exceptions=True)

    async def cleanup_all(self) -> None:
        """清理所有服务"""
        cleanup_tasks = []

        for service in self._services.values():
            if hasattr(service, 'cleanup'):
                cleanup_tasks.append(service.cleanup())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)