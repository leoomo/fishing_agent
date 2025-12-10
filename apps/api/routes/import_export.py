"""
导入导出 API 路由
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, status
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import io

from apps.api.services.import_service import ImportService
from apps.api.services.export_service import ExportService
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== 导入端点 ==========

@router.post(
    "/import/csv",
    summary="CSV 导入装备",
    dependencies=[Depends(require_permission(PermissionEnum.DATA_IMPORT))]
)
async def import_csv(file: UploadFile = File(...)):
    """
    CSV 导入装备

    Args:
        file: CSV 文件

    Returns:
        dict: 导入结果（成功数、失败数、错误列表）
    """
    # 验证文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 CSV 文件"
        )

    try:
        # 读取文件内容
        content = await file.read()
        csv_string = content.decode('utf-8')

        # 导入
        import_service = ImportService()
        result = import_service.import_from_csv(csv_string)

        logger.info(
            f"CSV 导入完成: 成功={result['success_count']}, "
            f"失败={result['error_count']}"
        )

        return result

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件编码错误，请使用 UTF-8 编码"
        )
    except Exception as e:
        logger.error(f"CSV 导入失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post(
    "/import/json",
    summary="JSON 导入装备",
    dependencies=[Depends(require_permission(PermissionEnum.DATA_IMPORT))]
)
async def import_json(file: UploadFile = File(...)):
    """
    JSON 导入装备

    Args:
        file: JSON 文件

    Returns:
        dict: 导入结果（成功数、失败数、错误列表）
    """
    # 验证文件类型
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 JSON 文件"
        )

    try:
        # 读取文件内容
        content = await file.read()
        json_string = content.decode('utf-8')

        # 导入
        import_service = ImportService()
        result = import_service.import_from_json(json_string)

        logger.info(
            f"JSON 导入完成: 成功={result['success_count']}, "
            f"失败={result['error_count']}"
        )

        return result

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件编码错误，请使用 UTF-8 编码"
        )
    except Exception as e:
        logger.error(f"JSON 导入失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


# ========== 导出端点 ==========

@router.get(
    "/export/csv",
    summary="CSV 导出装备",
    dependencies=[Depends(require_permission(PermissionEnum.DATA_EXPORT))]
)
async def export_csv(
    category: Optional[str] = Query(None, description="类别过滤"),
    brand_id: Optional[int] = Query(None, description="品牌过滤"),
    is_active: Optional[bool] = Query(None, description="是否启用过滤"),
    limit: int = Query(1000, ge=1, le=10000, description="最大导出数量")
):
    """
    CSV 导出装备

    Returns:
        StreamingResponse: CSV 文件流
    """
    try:
        export_service = ExportService()

        filters = {}
        if category:
            filters['category'] = category
        if brand_id:
            filters['brand_id'] = brand_id
        if is_active is not None:
            filters['is_active'] = is_active

        csv_string = export_service.export_to_csv(filters=filters, limit=limit)

        # 转换为字节流（添加 BOM 以便 Excel 正确识别）
        output = io.BytesIO(csv_string.encode('utf-8-sig'))

        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=equipment_export.csv"
            }
        )

    except Exception as e:
        logger.error(f"CSV 导出失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


@router.get(
    "/export/json",
    summary="JSON 导出装备",
    dependencies=[Depends(require_permission(PermissionEnum.DATA_EXPORT))]
)
async def export_json(
    category: Optional[str] = Query(None, description="类别过滤"),
    brand_id: Optional[int] = Query(None, description="品牌过滤"),
    is_active: Optional[bool] = Query(None, description="是否启用过滤"),
    include_specs: bool = Query(True, description="包含详细规格"),
    limit: int = Query(1000, ge=1, le=10000, description="最大导出数量")
):
    """
    JSON 导出装备（包含完整规格和关联数据）

    Returns:
        StreamingResponse: JSON 文件流
    """
    try:
        export_service = ExportService()

        filters = {}
        if category:
            filters['category'] = category
        if brand_id:
            filters['brand_id'] = brand_id
        if is_active is not None:
            filters['is_active'] = is_active

        json_string = export_service.export_to_json(
            filters=filters,
            limit=limit,
            include_specs=include_specs
        )

        output = io.BytesIO(json_string.encode('utf-8'))

        return StreamingResponse(
            output,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=equipment_export.json"
            }
        )

    except Exception as e:
        logger.error(f"JSON 导出失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )
