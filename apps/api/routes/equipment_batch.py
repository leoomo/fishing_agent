"""
装备批量添加 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, status
import logging

from apps.api.schemas.equipment_batch import (
    EquipmentCategory,
    BatchEquipmentCreateRequest,
    BatchRodCreateRequest,
    BatchReelCreateRequest,
    BatchLineCreateRequest,
    BatchLureCreateRequest,
    BatchEquipmentCreateResponse,
    TextParseRequest,
    TextParseResponse,
)
from apps.api.services.batch_equipment_service import batch_equipment_service
from apps.api.services.text_parser_service import text_parser_service
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 批量创建端点 ==========

@router.post(
    "/batch",
    response_model=BatchEquipmentCreateResponse,
    summary="批量创建装备",
    description="使用模板+变体模式批量创建同系列装备",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def batch_create_equipment(
    request: BatchEquipmentCreateRequest
) -> BatchEquipmentCreateResponse:
    """
    批量创建装备

    使用模板+变体模式，一次性创建多个同系列装备：
    - 模板包含共享字段（品牌、产品线、材质等）
    - 变体包含差异字段（型号、长度、调性等）
    - 自动生成装备名称：品牌 + 产品线 + 型号

    Args:
        request: 批量创建请求，包含类别、模板和变体列表

    Returns:
        BatchEquipmentCreateResponse: 创建结果，包含成功/跳过/失败数量
    """
    try:
        result = batch_equipment_service.batch_create(
            category=request.category,
            template=request.template,
            variants=request.variants,
            skip_duplicates=request.skip_duplicates
        )

        logger.info(
            f"批量创建装备完成: 成功={result.success_count}, "
            f"跳过={result.skip_count}, 失败={result.error_count}"
        )

        return result

    except Exception as e:
        logger.error(f"批量创建装备失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建失败: {str(e)}"
        )


@router.post(
    "/batch/rods",
    response_model=BatchEquipmentCreateResponse,
    summary="批量创建鱼竿",
    description="使用强类型模板批量创建鱼竿",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def batch_create_rods(
    request: BatchRodCreateRequest
) -> BatchEquipmentCreateResponse:
    """
    批量创建鱼竿（强类型版本）

    相比通用的 /batch 接口，此接口使用强类型验证：
    - BatchRodTemplate 验证模板字段
    - RodVariantSpec 验证变体规格
    """
    try:
        result = batch_equipment_service.batch_create_rods(
            template=request.template,
            variants=request.variants,
            skip_duplicates=request.skip_duplicates
        )

        logger.info(
            f"批量创建鱼竿完成: 成功={result.success_count}, "
            f"跳过={result.skip_count}, 失败={result.error_count}"
        )

        return result

    except Exception as e:
        logger.error(f"批量创建鱼竿失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建失败: {str(e)}"
        )


@router.post(
    "/batch/reels",
    response_model=BatchEquipmentCreateResponse,
    summary="批量创建渔轮",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def batch_create_reels(
    request: BatchReelCreateRequest
) -> BatchEquipmentCreateResponse:
    """批量创建渔轮"""
    try:
        result = batch_equipment_service.batch_create(
            category=EquipmentCategory.REEL,
            template=request.template.model_dump(),
            variants=[v.model_dump() for v in request.variants],
            skip_duplicates=request.skip_duplicates
        )
        return result
    except Exception as e:
        logger.error(f"批量创建渔轮失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建失败: {str(e)}"
        )


@router.post(
    "/batch/lines",
    response_model=BatchEquipmentCreateResponse,
    summary="批量创建鱼线",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def batch_create_lines(
    request: BatchLineCreateRequest
) -> BatchEquipmentCreateResponse:
    """批量创建鱼线"""
    try:
        result = batch_equipment_service.batch_create(
            category=EquipmentCategory.LINE,
            template=request.template.model_dump(),
            variants=[v.model_dump() for v in request.variants],
            skip_duplicates=request.skip_duplicates
        )
        return result
    except Exception as e:
        logger.error(f"批量创建鱼线失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建失败: {str(e)}"
        )


@router.post(
    "/batch/lures",
    response_model=BatchEquipmentCreateResponse,
    summary="批量创建拟饵",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def batch_create_lures(
    request: BatchLureCreateRequest
) -> BatchEquipmentCreateResponse:
    """批量创建拟饵"""
    try:
        result = batch_equipment_service.batch_create(
            category=EquipmentCategory.LURE,
            template=request.template.model_dump(),
            variants=[v.model_dump() for v in request.variants],
            skip_duplicates=request.skip_duplicates
        )
        return result
    except Exception as e:
        logger.error(f"批量创建拟饵失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建失败: {str(e)}"
        )


# ========== 文本解析端点 ==========

@router.post(
    "/parse-text",
    response_model=TextParseResponse,
    summary="解析规格表文本",
    description="解析粘贴的规格表文本，提取变体信息",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def parse_spec_text(
    request: TextParseRequest
) -> TextParseResponse:
    """
    解析规格表文本

    支持多种格式：
    - Tab 分隔的表格
    - 空格分隔的表格
    - 竖线分隔的表格
    - Markdown 表格

    自动识别表头并映射到标准字段。

    Args:
        request: 解析请求，包含文本和类别

    Returns:
        TextParseResponse: 解析结果，包含模板和变体列表
    """
    try:
        result = text_parser_service.parse(
            text=request.text,
            category=request.category,
            delimiter=request.delimiter
        )
        return result

    except Exception as e:
        logger.error(f"解析文本失败: {e}", exc_info=True)
        return TextParseResponse(
            success=False,
            warnings=[f"解析失败: {str(e)}"]
        )
