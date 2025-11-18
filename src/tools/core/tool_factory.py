#!/usr/bin/env python3
"""
工具工厂
提供工具创建、配置和管理的工厂模式实现
"""

from typing import Type, Dict, Any, List, Optional, Callable
import logging
from .base_interfaces import BaseTool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)

class ToolFactory:
    """工具工厂类 - 支持工具的创建和配置"""

    def __init__(self):
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
        self._default_config: Dict[str, Dict[str, Any]] = {}

    def register_tool_class(self, tool_class: Type[BaseTool], name: Optional[str] = None) -> bool:
        """
        注册工具类

        Args:
            tool_class: 工具类
            name: 工具名称（可选，默认使用类名）

        Returns:
            注册是否成功
        """
        try:
            tool_name = name or tool_class.__name__
            self._tool_classes[tool_name] = tool_class

            # 设置默认配置
            if tool_name not in self._default_config:
                self._default_config[tool_name] = {}

            logger.info(f"✅ 注册工具类: {tool_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 注册工具类失败: {e}")
            return False

    def create_tool(self, tool_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseTool]:
        """
        创建工具实例

        Args:
            tool_name: 工具名称
            config: 工具配置（可选）

        Returns:
            工具实例或 None
        """
        try:
            if tool_name not in self._tool_classes:
                logger.error(f"❌ 未找到工具类: {tool_name}")
                return None

            # 合并默认配置和用户配置
            final_config = self._default_config[tool_name].copy()
            if config:
                final_config.update(config)

            # 创建实例
            tool_class = self._tool_classes[tool_name]
            instance = tool_class()

            # 配置工具
            if final_config:
                instance.configure(**final_config)

            logger.info(f"✅ 创建工具实例: {tool_name}")
            return instance

        except Exception as e:
            logger.error(f"❌ 创建工具实例失败 {tool_name}: {e}")
            return None

    def get_tool_instance(self, tool_name: str, config: Optional[Dict[str, Any]] = None) -> BaseTool:
        """
        获取工具实例（单例模式）

        Args:
            tool_name: 工具名称
            config: 工具配置（可选）

        Returns:
            工具实例
        """
        if tool_name not in self._instances:
            instance = self.create_tool(tool_name, config)
            if instance:
                self._instances[tool_name] = instance
            else:
                raise RuntimeError(f"无法创建工具实例: {tool_name}")

        return self._instances[tool_name]

    def set_default_config(self, tool_name: str, config: Dict[str, Any]) -> None:
        """
        设置工具默认配置

        Args:
            tool_name: 工具名称
            config: 默认配置
        """
        if tool_name not in self._default_config:
            self._default_config[tool_name] = {}
        self._default_config[tool_name].update(config)
        logger.info(f"⚙️ 设置工具默认配置: {tool_name}")

    def list_registered_tools(self) -> List[str]:
        """列出所有已注册的工具类"""
        return list(self._tool_classes.keys())

    def list_tool_instances(self) -> List[str]:
        """列出所有已创建的工具实例"""
        return list(self._instances.keys())

    def create_tool_from_function(self, func: Callable, name: Optional[str] = None,
                                 category: str = "general", description: str = "") -> BaseTool:
        """
        从函数创建工具

        Args:
            func: 工具函数
            name: 工具名称（可选）
            category: 工具类别
            description: 工具描述

        Returns:
            工具实例
        """
        from .base_interfaces import simple_tool

        # 创建装饰器
        decorator = simple_tool(category=category, description=description)
        return decorator(func)

    def batch_create_tools(self, tool_configs: List[Dict[str, Any]]) -> List[BaseTool]:
        """
        批量创建工具

        Args:
            tool_configs: 工具配置列表，每个配置包含:
                - name: 工具名称
                - config: 工具配置（可选）

        Returns:
            工具实例列表
        """
        tools = []
        for tool_config in tool_configs:
            tool_name = tool_config.get('name')
            config = tool_config.get('config')

            if tool_name:
                tool = self.create_tool(tool_name, config)
                if tool:
                    tools.append(tool)

        logger.info(f"📦 批量创建工具完成: {len(tools)}/{len(tool_configs)} 个")
        return tools

    def validate_tool(self, tool: BaseTool) -> bool:
        """
        验证工具是否有效

        Args:
            tool: 工具实例

        Returns:
            验证结果
        """
        try:
            # 检查基本属性
            if not hasattr(tool, 'name') or not tool.name:
                logger.error("❌ 工具缺少名称属性")
                return False

            if not hasattr(tool, 'execute'):
                logger.error("❌ 工具缺少 execute 方法")
                return False

            # 检查是否可调用
            if not callable(tool.execute):
                logger.error("❌ execute 方法不可调用")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ 工具验证失败: {e}")
            return False

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息

        Args:
            tool_name: 工具名称

        Returns:
            工具信息字典
        """
        if tool_name in self._tool_classes:
            tool_class = self._tool_classes[tool_name]
            info = {
                'name': tool_name,
                'class': tool_class.__name__,
                'module': tool_class.__module__,
                'default_config': self._default_config.get(tool_name, {}),
                'has_instance': tool_name in self._instances
            }
            return info
        return None

    def clear_instances(self) -> None:
        """清空所有工具实例"""
        self._instances.clear()
        logger.info("🔄 已清空所有工具实例")

    def reset(self) -> None:
        """重置工厂"""
        self._tool_classes.clear()
        self._instances.clear()
        self._default_config.clear()
        logger.info("🔄 工具工厂已重置")

# 全局工具工厂实例
tool_factory = ToolFactory()