"""
Agents Package - 统一 Agent 存放目录

包含:
- fishing: 钓鱼助手 Agent
- equipment_import: 装备导入 Agent
- agent_component: 共享组件 (监控回调等)
"""

# 延迟导入，避免循环依赖
def get_fishing_agent():
    from .fishing import FishingAgent, create_agent
    return FishingAgent, create_agent

def get_equipment_import_agent():
    from .equipment_import import EquipmentImportAgent
    return EquipmentImportAgent
