"""
OCR API 路由

提供图片表格识别功能的 API 端点。
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends

from apps.api.schemas.ocr import OCRRecognizeResponse, OCRMetadata
from apps.api.services.ocr_service import get_ocr_service, OCRService
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/recognize-table",
    response_model=OCRRecognizeResponse,
    summary="识别图片中的表格",
    description="""
    上传装备规格表图片，返回 Markdown 格式的表格内容。

    **支持功能**:
    - 单张图片识别
    - 多张图片自动合并后识别
    - 通过 URL 识别图片

    **支持格式**: PNG, JPG, JPEG, WebP

    **最大文件大小**: 10MB
    """,
    dependencies=[Depends(require_permission(PermissionEnum.OCR_USE))]
)
async def recognize_table(
    files: Optional[List[UploadFile]] = File(None, description="图片文件列表（支持多张）"),
    image_url: Optional[str] = Form(None, description="图片URL（与files二选一，仅支持单张）"),
    ocr_service: OCRService = Depends(get_ocr_service)
) -> OCRRecognizeResponse:
    """
    识别装备规格表图片

    支持两种方式：
    1. 上传图片文件（推荐，支持多张自动合并）
    2. 提供图片URL（仅支持单张）
    """
    # 验证输入
    if not files and not image_url:
        return OCRRecognizeResponse(
            success=False,
            error="请提供图片文件或图片URL",
            error_code="OCR_NO_INPUT"
        )

    if files and image_url:
        return OCRRecognizeResponse(
            success=False,
            error="files 和 image_url 不能同时提供",
            error_code="OCR_INVALID_INPUT"
        )

    try:
        if files:
            # 文件上传方式
            valid_files = [f for f in files if f.filename and f.size > 0]

            if not valid_files:
                return OCRRecognizeResponse(
                    success=False,
                    error="未上传有效的图片文件",
                    error_code="OCR_NO_INPUT"
                )

            logger.info(f"收到 {len(valid_files)} 个图片文件")

            # 读取所有文件内容
            image_data_list = []
            for file in valid_files:
                content = await file.read()
                image_data_list.append((content, file.filename))
                logger.debug(f"读取文件: {file.filename}, 大小: {len(content)} bytes")

            # 调用 OCR 服务
            result = ocr_service.recognize_table_from_bytes(image_data_list)

        else:
            # URL 方式
            import requests
            import tempfile
            from pathlib import Path

            logger.info(f"从 URL 获取图片: {image_url}")

            try:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()

                # 从 URL 或 Content-Type 推断扩展名
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'

                # 保存到临时文件
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                    f.write(response.content)
                    temp_path = f.name

                try:
                    result = ocr_service.recognize_table(temp_path)
                finally:
                    # 清理临时文件
                    import os
                    os.unlink(temp_path)

            except requests.RequestException as e:
                return OCRRecognizeResponse(
                    success=False,
                    error=f"获取图片失败: {str(e)}",
                    error_code="OCR_URL_ERROR"
                )

        # 构建响应
        if result["success"]:
            return OCRRecognizeResponse(
                success=True,
                markdown=result["markdown"],
                metadata=OCRMetadata(
                    model=result["metadata"]["model"],
                    processing_time_ms=result["metadata"]["processing_time_ms"],
                    images_merged=result["metadata"].get("images_merged", 1),
                    image_size_bytes=result["metadata"].get("image_size_bytes")
                )
            )
        else:
            return OCRRecognizeResponse(
                success=False,
                error=result.get("error"),
                error_code=result.get("error_code"),
                metadata=OCRMetadata(
                    model=result["metadata"]["model"],
                    processing_time_ms=result["metadata"]["processing_time_ms"],
                    images_merged=result["metadata"].get("images_merged", 1)
                ) if result.get("metadata") else None
            )

    except Exception as e:
        logger.exception(f"OCR 处理异常: {e}")
        return OCRRecognizeResponse(
            success=False,
            error=f"处理异常: {str(e)}",
            error_code="OCR_UNKNOWN_ERROR"
        )


@router.get(
    "/status",
    summary="检查 OCR 服务状态",
    description="检查 OCR 服务是否正常配置"
)
async def ocr_status(
    ocr_service: OCRService = Depends(get_ocr_service)
) -> dict:
    """检查 OCR 服务状态"""
    import os

    api_key_configured = bool(os.getenv("SILICONFLOW_API_KEY"))

    return {
        "service": "ocr",
        "model": ocr_service.MODEL,
        "api_key_configured": api_key_configured,
        "timeout": ocr_service.timeout,
        "max_size_mb": ocr_service.max_size / 1024 / 1024,
        "supported_formats": list(ocr_service.SUPPORTED_FORMATS)
    }
