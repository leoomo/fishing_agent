"""
装备导入工具

提供 LangChain @tool 装饰的工具方法，供 Agent 调用。
保持单一工具设计，通过可选参数扩展功能。
"""

import json
import logging
from typing import List, Optional

from langchain_core.tools import tool

from ..constants import (
    EQUIPMENT_TYPES,
    SOURCE_TYPES,
    CONFIDENCE_THRESHOLD_LOW,
    DEFAULT_MODEL_PROVIDER
)

logger = logging.getLogger(__name__)


def _check_duplicate_equipment(
    brand_name: Optional[str],
    model: Optional[str],
    equipment_type: Optional[str]
) -> Optional[dict]:
    """
    检查是否存在重复装备

    Args:
        brand_name: 品牌名称
        model: 型号
        equipment_type: 装备类型

    Returns:
        重复装备信息，或 None
    """
    if not brand_name and not model:
        return None

    try:
        from apps.api.database import get_db

        db = get_db()
        conditions = []
        params = []

        # 构建查询条件
        if model:
            conditions.append("(e.name LIKE ? OR e.model LIKE ?)")
            params.extend([f"%{model}%", f"%{model}%"])

        if brand_name:
            conditions.append("b.name_cn LIKE ?")
            params.append(f"%{brand_name}%")

        if equipment_type:
            conditions.append("e.category = ?")
            params.append(equipment_type)

        if not conditions:
            return None

        query = f"""
            SELECT e.id, e.name, e.category, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE {' AND '.join(conditions)}
            LIMIT 1
        """

        results = db.execute(query, tuple(params))
        if results:
            return results[0]

    except Exception as e:
        logger.warning(f"检查重复装备失败: {e}")

    return None


def _check_duplicate_pending(
    brand_name: Optional[str],
    model: Optional[str]
) -> Optional[dict]:
    """
    检查待审核表是否存在重复

    Args:
        brand_name: 品牌名称
        model: 型号

    Returns:
        重复待审核信息，或 None
    """
    if not brand_name and not model:
        return None

    try:
        from apps.api.orm.session import get_db_session
        from ..models.pending import PendingEquipment

        with get_db_session() as session:
            query = session.query(PendingEquipment).filter(
                PendingEquipment.status == "pending"
            )

            if model:
                query = query.filter(PendingEquipment.model_name.like(f"%{model}%"))

            if brand_name:
                query = query.filter(PendingEquipment.brand_name.like(f"%{brand_name}%"))

            existing = query.first()
            if existing:
                return {
                    "id": existing.id,
                    "brand_name": existing.brand_name,
                    "model_name": existing.model_name,
                    "equipment_type": existing.equipment_type,
                    "status": existing.status
                }

    except Exception as e:
        logger.warning(f"检查待审核重复失败: {e}")

    return None


@tool
def extract_equipment_from_text(
    text: str,
    source_type: str = "unknown",
    source_url: str = "",
    check_duplicates: bool = True,
    brand_hint: str = "",
    dry_run: bool = False
) -> str:
    """
    从文本中提取装备信息并存入待审核表。

    这个工具会：
    1. 使用 LLM 分析文本，识别装备类型和规格参数
    2. 将提取的信息结构化
    3. 可选地检查重复
    4. 保存到待审核表（除非 dry_run=True）

    Args:
        text: 包含装备信息的文本内容
        source_type: 来源类型，可选值: ecommerce(电商)、official(官方)、forum(论坛)、unknown(未知)
        source_url: 来源 URL，可选
        check_duplicates: 是否检查重复装备，默认 True
        brand_hint: 品牌提示，帮助 LLM 更准确识别品牌
        dry_run: 仅提取不保存，默认 False

    Returns:
        JSON 字符串，包含提取结果：
        - success: 是否成功
        - pending_id: 待审核记录 ID (dry_run=True 时为 None)
        - equipment_type: 识别的装备类型
        - brand: 品牌名称
        - model: 型号
        - confidence: 置信度
        - message: 结果消息
        - duplicate: 重复装备信息（如有）
        - dry_run: 是否为预览模式
    """
    from ..core.extractor import EquipmentExtractor
    from ..models.pending import save_pending_equipment

    try:
        # 验证输入
        if not text or not text.strip():
            return json.dumps({
                "success": False,
                "message": "文本内容为空",
                "pending_id": None
            }, ensure_ascii=False)

        # 验证来源类型
        if source_type not in SOURCE_TYPES:
            source_type = "unknown"

        # 如果有品牌提示，添加到文本开头
        processed_text = text
        if brand_hint:
            processed_text = f"[品牌提示: {brand_hint}]\n\n{text}"

        # 使用 LLM 提取装备信息
        extractor = EquipmentExtractor(model_provider=DEFAULT_MODEL_PROVIDER)
        extracted = extractor.extract(processed_text, source_type)

        # 检查提取结果
        if not extracted.equipment_type:
            return json.dumps({
                "success": False,
                "message": "无法识别装备类型，请检查输入文本",
                "confidence": extracted.confidence,
                "extraction_notes": extracted.extraction_notes
            }, ensure_ascii=False)

        # 验证装备类型
        if extracted.equipment_type not in EQUIPMENT_TYPES:
            return json.dumps({
                "success": False,
                "message": f"不支持的装备类型: {extracted.equipment_type}",
                "confidence": extracted.confidence
            }, ensure_ascii=False)

        # 检查置信度
        if extracted.confidence < CONFIDENCE_THRESHOLD_LOW:
            return json.dumps({
                "success": False,
                "message": f"提取置信度过低 ({extracted.confidence:.0%})，请提供更详细的信息",
                "confidence": extracted.confidence,
                "extraction_notes": extracted.extraction_notes
            }, ensure_ascii=False)

        # 检查重复
        duplicate_info = None
        if check_duplicates:
            # 检查正式装备表
            dup_equipment = _check_duplicate_equipment(
                extracted.brand_name,
                extracted.model,
                extracted.equipment_type
            )
            if dup_equipment:
                duplicate_info = {
                    "type": "equipment",
                    "id": dup_equipment.get("id"),
                    "name": dup_equipment.get("name"),
                    "message": f"已存在相似装备: {dup_equipment.get('name')}"
                }

            # 检查待审核表
            if not duplicate_info:
                dup_pending = _check_duplicate_pending(
                    extracted.brand_name,
                    extracted.model
                )
                if dup_pending:
                    duplicate_info = {
                        "type": "pending",
                        "id": dup_pending.get("id"),
                        "name": f"{dup_pending.get('brand_name')} {dup_pending.get('model_name')}",
                        "message": f"待审核表中已有相似记录 (ID: {dup_pending.get('id')})"
                    }

        # dry_run 模式：只返回提取结果，不保存
        if dry_run:
            result = {
                "success": True,
                "dry_run": True,
                "pending_id": None,
                "equipment_type": extracted.equipment_type,
                "brand": extracted.brand_name,
                "model": extracted.model,
                "name": extracted.name,
                "confidence": extracted.confidence,
                "specs": extracted.specs,
                "message": f"预览模式：成功提取 {extracted.equipment_type} 信息"
            }
            if duplicate_info:
                result["duplicate"] = duplicate_info
                result["message"] += f"（注意：{duplicate_info['message']}）"
            return json.dumps(result, ensure_ascii=False)

        # 如果有重复且不是 dry_run，仍然保存但返回提示
        pending_id = save_pending_equipment(
            extracted=extracted,
            ocr_text=text,
            source_type=source_type,
            source_url=source_url if source_url else None
        )

        # 返回结果
        result = {
            "success": True,
            "dry_run": False,
            "pending_id": pending_id,
            "equipment_type": extracted.equipment_type,
            "brand": extracted.brand_name,
            "model": extracted.model,
            "name": extracted.name,
            "confidence": extracted.confidence,
            "message": f"成功提取 {extracted.equipment_type} 信息，已存入待审核表 (ID: {pending_id})"
        }

        if duplicate_info:
            result["duplicate"] = duplicate_info
            result["message"] += f"（注意：{duplicate_info['message']}）"

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        logger.error(f"提取装备信息失败: {e}")
        return json.dumps({
            "success": False,
            "message": f"提取失败: {str(e)}",
            "pending_id": None
        }, ensure_ascii=False)


def get_import_tools() -> List:
    """
    获取所有导入工具

    Returns:
        List: 工具列表
    """
    return [extract_equipment_from_text]
