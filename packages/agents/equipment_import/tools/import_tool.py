"""
装备导入工具

提供 LangChain @tool 装饰的工具方法，供 Agent 调用。
"""

import json
import logging
from typing import List

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def extract_equipment_from_text(
    text: str,
    source_type: str = "unknown",
    source_url: str = ""
) -> str:
    """
    从文本中提取装备信息并存入待审核表。

    这个工具会：
    1. 使用 LLM 分析文本，识别装备类型和规格参数
    2. 将提取的信息结构化
    3. 保存到待审核表，等待人工审核

    Args:
        text: 包含装备信息的文本内容
        source_type: 来源类型，可选值: ecommerce(电商)、official(官方)、forum(论坛)、unknown(未知)
        source_url: 来源 URL，可选

    Returns:
        JSON 字符串，包含提取结果：
        - success: 是否成功
        - pending_id: 待审核记录 ID
        - equipment_type: 识别的装备类型
        - brand: 品牌名称
        - model: 型号
        - confidence: 置信度
        - message: 结果消息
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

        # 使用 LLM 提取装备信息
        extractor = EquipmentExtractor()
        extracted = extractor.extract(text, source_type)

        # 检查提取结果
        if not extracted.equipment_type:
            return json.dumps({
                "success": False,
                "message": "无法识别装备类型，请检查输入文本",
                "confidence": extracted.confidence,
                "extraction_notes": extracted.extraction_notes
            }, ensure_ascii=False)

        # 存入待审核表
        pending_id = save_pending_equipment(
            extracted=extracted,
            ocr_text=text,  # 保持数据库字段名不变
            source_type=source_type,
            source_url=source_url if source_url else None
        )

        # 返回结果
        return json.dumps({
            "success": True,
            "pending_id": pending_id,
            "equipment_type": extracted.equipment_type,
            "brand": extracted.brand_name,
            "model": extracted.model,
            "name": extracted.name,
            "confidence": extracted.confidence,
            "message": f"成功提取 {extracted.equipment_type} 信息，已存入待审核表 (ID: {pending_id})"
        }, ensure_ascii=False)

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
