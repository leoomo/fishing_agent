"""
agent_equipment_import - 装备导入 Agent

从文本中提取装备信息并存储到待审核表。
支持对话式交互和直接 API 调用两种方式。
"""

from .core.agent import EquipmentImportAgent
from .schemas.extracted import ExtractedEquipment, ImportResult

__all__ = [
    "EquipmentImportAgent",
    "ExtractedEquipment",
    "ImportResult",
]

__version__ = "1.0.0"
