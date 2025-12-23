"""
PendingEquipment - 待审核装备表模型

存储 Agent 从文本中提取的装备信息，等待人工审核。
"""

import json
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey

# 复用现有的 Base 和数据库会话
from apps.api.models.base import Base, TimestampMixin
from apps.api.orm.session import get_db_session

if TYPE_CHECKING:
    from ..schemas.extracted import ExtractedEquipment


class PendingEquipment(Base, TimestampMixin):
    """
    待审核装备表

    存储 Agent 提取的原始数据，等待人工审核后存入正式 equipment 表。
    """
    __tablename__ = "pending_equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 状态: pending(待审核) / approved(已通过) / rejected(已拒绝)
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="审核状态"
    )

    # === 原始输入 ===
    ocr_text = Column(
        Text,
        nullable=False,
        comment="OCR 识别的原始文本"
    )

    source_type = Column(
        String(50),
        default="unknown",
        nullable=False,
        comment="来源类型: ecommerce/official/forum/unknown"
    )

    source_url = Column(
        String(500),
        nullable=True,
        comment="来源 URL"
    )

    # === LLM 提取结果 ===
    extracted_data = Column(
        Text,
        nullable=False,
        comment="ExtractedEquipment 的 JSON 序列化"
    )

    confidence = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="整体提取置信度 (0-1)"
    )

    # 提取的关键字段（便于列表展示和搜索）
    equipment_type = Column(
        String(20),
        nullable=True,
        index=True,
        comment="装备类型: 鱼竿/渔轮/鱼线/拟饵"
    )

    brand_name = Column(
        String(100),
        nullable=True,
        index=True,
        comment="品牌名称"
    )

    model_name = Column(
        String(200),
        nullable=True,
        comment="型号"
    )

    product_name = Column(
        String(300),
        nullable=True,
        comment="产品名称"
    )

    # === 审核信息 ===
    # Note: admin_users table is created through migrations, not ORM
    # We store the ID as an integer without FK constraint
    reviewed_by = Column(
        Integer,
        nullable=True,
        comment="审核人 ID (admin_users.id)"
    )

    reviewed_at = Column(
        DateTime,
        nullable=True,
        comment="审核时间"
    )

    review_notes = Column(
        Text,
        nullable=True,
        comment="审核备注"
    )

    # 最终装备 ID（审核通过后关联到正式表）
    equipment_id = Column(
        Integer,
        ForeignKey("equipment.equipment_id"),
        nullable=True,
        comment="关联的正式装备 ID"
    )

    # === 图片和任务关联 ===
    images = Column(
        Text,
        nullable=True,
        comment="图片路径JSON数组，格式: ['pending/123/1.jpg', ...]"
    )

    task_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="关联的爬虫任务ID"
    )

    def __repr__(self):
        return (
            f"<PendingEquipment(id={self.id}, "
            f"status={self.status}, "
            f"type={self.equipment_type}, "
            f"brand={self.brand_name})>"
        )

    def get_extracted_data(self) -> dict:
        """获取解析后的提取数据"""
        if self.extracted_data:
            return json.loads(self.extracted_data)
        return {}

    def set_extracted_data(self, data: dict):
        """设置提取数据（自动序列化为 JSON）"""
        self.extracted_data = json.dumps(data, ensure_ascii=False)


def save_pending_equipment(
    extracted: "ExtractedEquipment",
    ocr_text: str,
    source_type: str = "unknown",
    source_url: Optional[str] = None
) -> int:
    """
    保存提取结果到待审核表

    Args:
        extracted: 提取的装备信息
        ocr_text: 原始 OCR 文本
        source_type: 来源类型
        source_url: 来源 URL

    Returns:
        int: 新创建记录的 ID
    """
    with get_db_session() as session:
        pending = PendingEquipment(
            ocr_text=ocr_text,
            source_type=source_type,
            source_url=source_url,
            extracted_data=json.dumps(extracted.to_dict(), ensure_ascii=False),
            confidence=extracted.confidence,
            equipment_type=extracted.equipment_type,
            brand_name=extracted.brand_name,
            model_name=extracted.model,
            product_name=extracted.name,
            status="pending"
        )

        session.add(pending)
        session.flush()  # 获取自增 ID

        return pending.id
