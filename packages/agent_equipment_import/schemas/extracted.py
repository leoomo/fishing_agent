"""
提取结果数据模型

定义 LLM 从文本中提取的装备信息结构。
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class ExtractedEquipment:
    """
    LLM 提取的装备信息

    Attributes:
        equipment_type: 装备类型 (鱼竿/渔轮/鱼线/拟饵)
        brand_name: 品牌名称
        model: 型号
        name: 产品名称
        price_min: 最低价格
        price_max: 最高价格
        description: 产品描述
        features: 特点列表
        target_fish: 目标鱼种
        user_level: 推荐用户级别 (新手/进阶/高手)
        specs: 规格参数 (JSON 格式，根据装备类型不同结构不同)
        confidence: 整体提取置信度 (0-1)
        extraction_notes: LLM 的提取备注
    """
    equipment_type: str = ""  # 鱼竿/渔轮/鱼线/拟饵

    # 基础信息
    brand_name: Optional[str] = None
    model: Optional[str] = None
    name: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    description: Optional[str] = None
    features: List[str] = field(default_factory=list)
    target_fish: List[str] = field(default_factory=list)
    user_level: Optional[str] = None

    # 规格参数 (根据装备类型不同结构不同)
    # 鱼竿: length, power, action, sections, weight, lure_weight_min/max, line_weight_min/max
    # 渔轮: reel_type, gear_ratio, bearings, weight, max_drag, line_capacity
    # 鱼线: line_type, diameter, strength_lb, length_m, color
    # 拟饵: lure_type, length, weight, diving_depth_min/max, color, action_type
    specs: Dict[str, Any] = field(default_factory=dict)

    # 元信息
    confidence: float = 0.0
    extraction_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedEquipment":
        """从字典创建实例"""
        return cls(
            equipment_type=data.get("equipment_type", ""),
            brand_name=data.get("brand_name"),
            model=data.get("model"),
            name=data.get("name"),
            price_min=data.get("price_min"),
            price_max=data.get("price_max"),
            description=data.get("description"),
            features=data.get("features", []),
            target_fish=data.get("target_fish", []),
            user_level=data.get("user_level"),
            specs=data.get("specs", {}),
            confidence=data.get("confidence", 0.0),
            extraction_notes=data.get("extraction_notes", "")
        )

    def get_summary(self) -> str:
        """获取简要摘要"""
        parts = []

        if self.equipment_type:
            parts.append(f"类型: {self.equipment_type}")

        if self.brand_name:
            parts.append(f"品牌: {self.brand_name}")

        if self.model:
            parts.append(f"型号: {self.model}")

        if self.price_min:
            price_str = f"¥{self.price_min}"
            if self.price_max and self.price_max != self.price_min:
                price_str += f"-{self.price_max}"
            parts.append(f"价格: {price_str}")

        parts.append(f"置信度: {self.confidence:.0%}")

        return " | ".join(parts)


@dataclass
class ImportResult:
    """
    导入结果

    Attributes:
        success: 是否成功
        pending_id: 待审核记录 ID
        message: 结果消息
        extracted: 提取的装备信息
    """
    success: bool = False
    pending_id: Optional[int] = None
    message: str = ""
    extracted: Optional[ExtractedEquipment] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "pending_id": self.pending_id,
            "message": self.message,
            "extracted": self.extracted.to_dict() if self.extracted else None
        }
