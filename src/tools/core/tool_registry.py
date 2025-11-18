#!/usr/bin/env python3
"""
工具注册中心
统一管理和注册所有工具，提供工具发现和获取功能
"""

from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    category: str  # basic, weather, advice, equipment
    description: str
    function: Any
    enabled: bool = True

class ToolRegistry:
    """工具注册中心 - 单例模式"""

    _instance: Optional['ToolRegistry'] = None
    _initialized: bool = False

    def __new__(cls) -> 'ToolRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._tools: Dict[str, ToolInfo] = {}
            self._categories: Dict[str, List[str]] = {
                'basic': [],
                'weather': [],
                'advice': [],
                'equipment': []
            }
            self._initialized = True
            logger.info("🔧 工具注册中心初始化完成")

    def register_tool(self, name: str, function: Any, category: str, description: str = "") -> bool:
        """
        注册单个工具

        Args:
            name: 工具名称
            function: 工具函数
            category: 工具类别 (basic, weather, advice, equipment)
            description: 工具描述

        Returns:
            注册是否成功
        """
        try:
            if category not in self._categories:
                logger.warning(f"未知工具类别: {category}，将忽略")
                return False

            tool_info = ToolInfo(
                name=name,
                category=category,
                description=description,
                function=function
            )

            self._tools[name] = tool_info
            self._categories[category].append(name)

            logger.info(f"✅ 注册工具: {name} (类别: {category})")
            return True

        except Exception as e:
            logger.error(f"❌ 注册工具失败 {name}: {e}")
            return False

    def register_tools_by_category(self, tools_list: List[Any], category: str) -> int:
        """
        按类别批量注册工具

        Args:
            tools_list: 工具函数列表
            category: 工具类别

        Returns:
            成功注册的工具数量
        """
        success_count = 0
        for tool_func in tools_list:
            tool_name = getattr(tool_func, '__name__', str(tool_func))
            tool_desc = getattr(tool_func, '__doc__', '') or ''

            if self.register_tool(tool_name, tool_func, category, tool_desc):
                success_count += 1

        logger.info(f"📊 {category} 类别注册完成: {success_count}/{len(tools_list)} 个工具")
        return success_count

    def get_tool(self, name: str) -> Optional[Any]:
        """获取单个工具函数"""
        tool_info = self._tools.get(name)
        if tool_info and tool_info.enabled:
            return tool_info.function
        return None

    def get_tools_by_category(self, category: str) -> List[Any]:
        """获取指定类别的所有工具"""
        if category not in self._categories:
            return []

        tools = []
        for tool_name in self._categories[category]:
            tool_func = self.get_tool(tool_name)
            if tool_func:
                tools.append(tool_func)

        return tools

    def get_all_tools(self) -> List[Any]:
        """获取所有已注册的工具"""
        all_tools = []
        for category in self._categories.keys():
            all_tools.extend(self.get_tools_by_category(category))
        return all_tools

    def get_tool_info(self, name: str) -> Optional[ToolInfo]:
        """获取工具详细信息"""
        return self._tools.get(name)

    def list_tools_by_category(self) -> Dict[str, List[str]]:
        """列出所有工具名称（按类别）"""
        return {cat: names[:] for cat, names in self._categories.items()}

    def enable_tool(self, name: str) -> bool:
        """启用工具"""
        if name in self._tools:
            self._tools[name].enabled = True
            logger.info(f"✅ 启用工具: {name}")
            return True
        return False

    def disable_tool(self, name: str) -> bool:
        """禁用工具"""
        if name in self._tools:
            self._tools[name].enabled = False
            logger.info(f"❌ 禁用工具: {name}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取注册统计信息"""
        stats = {
            'total_tools': len(self._tools),
            'enabled_tools': sum(1 for t in self._tools.values() if t.enabled),
            'categories': {}
        }

        for category, tool_names in self._categories.items():
            enabled_count = sum(1 for name in tool_names
                               if name in self._tools and self._tools[name].enabled)
            stats['categories'][category] = {
                'total': len(tool_names),
                'enabled': enabled_count,
                'disabled': len(tool_names) - enabled_count
            }

        return stats

    def reset(self) -> None:
        """重置注册中心（清空所有工具）"""
        self._tools.clear()
        for category in self._categories:
            self._categories[category].clear()
        logger.info("🔄 工具注册中心已重置")

# 全局工具注册器实例
tool_registry = ToolRegistry()