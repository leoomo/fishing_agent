"""
Dedup - 数据去重模块

注意：EquipmentDeduplicator 依赖业务层 (LureDatabase)，
需要在使用时手动导入：
    from packages.data_processing.dedup.deduplicator import EquipmentDeduplicator
"""

# 暂不在包级别导出，因为依赖业务层
# 使用时请直接导入: from .deduplicator import EquipmentDeduplicator

__all__ = []
