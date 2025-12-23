"""
Agent Component - 共享组件

提供所有 Agent 通用的功能:
- monitoring: 统一监控回调
"""

from .monitoring import MonitoringCallback

__all__ = ["MonitoringCallback"]
