"""
Image Upload Routes

图片上传API路由
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session

from ...database import get_db_session
from ...models import CrawlerNode, CrawlerTask, TaskStatus
from ..schemas.node import ImageUploadResponse, ImageBatchUploadResponse
from ..auth.node_auth import get_current_node

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nodes", tags=["images"])

# 图片存储根目录
IMAGE_STORAGE_ROOT = os.getenv(
    "CRAWLER_IMAGE_STORAGE",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "shared", "data", "images", "crawler")
)


def get_image_storage_path() -> Path:
    """获取图片存储路径"""
    path = Path(IMAGE_STORAGE_ROOT).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def compute_url_hash(url: str) -> str:
    """计算URL的MD5哈希"""
    return hashlib.md5(url.encode()).hexdigest()


def is_duplicate_image(storage_path: Path, url_hash: str) -> Optional[Path]:
    """检查图片是否已存在（基于URL哈希）"""
    # 检查所有可能的扩展名
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        existing = storage_path / f"{url_hash}{ext}"
        if existing.exists():
            return existing
    return None


@router.post("/{node_id}/tasks/{task_id}/images", response_model=ImageUploadResponse)
async def upload_image(
    node_id: str,
    task_id: int,
    file: UploadFile = File(...),
    image_type: str = Form("detail"),  # main/detail/spec
    original_url: str = Form(...),
    equipment_name: str = Form("unknown"),
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    上传单张图片

    Args:
        node_id: 节点ID
        task_id: 任务ID
        file: 图片文件
        image_type: 图片类型 (main/detail/spec)
        original_url: 原始图片URL (用于去重)
        equipment_name: 装备名称

    Returns:
        ImageUploadResponse: 上传结果
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 验证任务存在且属于该节点
    task = db.query(CrawlerTask).filter(
        CrawlerTask.id == task_id,
        CrawlerTask.assigned_node_id == current_node.id,
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not assigned to this node",
        )

    try:
        storage_path = get_image_storage_path()

        # 检查URL哈希去重
        url_hash = compute_url_hash(original_url)
        existing = is_duplicate_image(storage_path, url_hash)

        if existing:
            logger.debug(f"Duplicate image detected: {original_url}")
            return ImageUploadResponse(
                image_id=None,
                local_url=f"file://{existing}",
                status="duplicate",
                message="Image already exists",
            )

        # 读取文件内容
        content = await file.read()

        # 确定文件扩展名
        ext = ".jpg"
        if file.content_type:
            content_type_map = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/webp": ".webp",
            }
            ext = content_type_map.get(file.content_type, ".jpg")
        elif file.filename:
            ext = Path(file.filename).suffix or ".jpg"

        # 创建按日期和任务ID组织的子目录
        date_str = datetime.utcnow().strftime("%Y%m%d")
        task_dir = storage_path / date_str / str(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        filename = f"{url_hash}{ext}"
        file_path = task_dir / filename
        file_path.write_bytes(content)

        local_url = f"file://{file_path}"

        logger.info(f"Image saved: {file_path} ({len(content)} bytes)")

        # 更新任务的图片统计
        result_summary = json.loads(task.result_summary) if task.result_summary else {}
        image_stats = result_summary.get('image_stats', {'saved': 0, 'duplicates': 0, 'errors': 0})
        image_stats['saved'] = image_stats.get('saved', 0) + 1
        result_summary['image_stats'] = image_stats
        task.result_summary = json.dumps(result_summary)
        db.commit()

        return ImageUploadResponse(
            image_id=None,  # 暂不分配image_id，后续可以关联到装备图片表
            local_url=local_url,
            status="saved",
            message=f"Image saved to {file_path.name}",
        )

    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        return ImageUploadResponse(
            image_id=None,
            local_url=None,
            status="error",
            message=str(e),
        )


@router.post("/{node_id}/tasks/{task_id}/images/batch", response_model=ImageBatchUploadResponse)
async def upload_images_batch(
    node_id: str,
    task_id: int,
    files: List[UploadFile] = File(...),
    metadata: str = Form(...),  # JSON字符串，包含每张图片的元数据
    db: Session = Depends(get_db_session),
    current_node: CrawlerNode = Depends(get_current_node),
):
    """
    批量上传图片

    Args:
        node_id: 节点ID
        task_id: 任务ID
        files: 图片文件列表
        metadata: JSON字符串，格式: [{"image_type": "main", "original_url": "...", "equipment_name": "..."}]

    Returns:
        ImageBatchUploadResponse: 批量上传结果
    """
    # 验证node_id匹配
    if current_node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch",
        )

    # 验证任务存在且属于该节点
    task = db.query(CrawlerTask).filter(
        CrawlerTask.id == task_id,
        CrawlerTask.assigned_node_id == current_node.id,
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not assigned to this node",
        )

    # 解析元数据
    try:
        meta_list = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid metadata JSON",
        )

    if len(meta_list) != len(files):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metadata count ({len(meta_list)}) does not match file count ({len(files)})",
        )

    storage_path = get_image_storage_path()
    date_str = datetime.utcnow().strftime("%Y%m%d")
    task_dir = storage_path / date_str / str(task_id)
    task_dir.mkdir(parents=True, exist_ok=True)

    results = []
    saved_count = 0
    duplicate_count = 0
    error_count = 0

    for file, meta in zip(files, meta_list):
        original_url = meta.get('original_url', '')
        image_type = meta.get('image_type', 'detail')
        equipment_name = meta.get('equipment_name', 'unknown')

        try:
            # 检查URL哈希去重
            url_hash = compute_url_hash(original_url)
            existing = is_duplicate_image(storage_path, url_hash)

            if existing:
                results.append(ImageUploadResponse(
                    image_id=None,
                    local_url=f"file://{existing}",
                    status="duplicate",
                    message="Image already exists",
                ))
                duplicate_count += 1
                continue

            # 读取文件内容
            content = await file.read()

            # 确定文件扩展名
            ext = ".jpg"
            if file.content_type:
                content_type_map = {
                    "image/jpeg": ".jpg",
                    "image/png": ".png",
                    "image/gif": ".gif",
                    "image/webp": ".webp",
                }
                ext = content_type_map.get(file.content_type, ".jpg")
            elif file.filename:
                ext = Path(file.filename).suffix or ".jpg"

            # 保存文件
            filename = f"{url_hash}{ext}"
            file_path = task_dir / filename
            file_path.write_bytes(content)

            local_url = f"file://{file_path}"

            results.append(ImageUploadResponse(
                image_id=None,
                local_url=local_url,
                status="saved",
                message=f"Saved as {filename}",
            ))
            saved_count += 1

        except Exception as e:
            logger.error(f"Failed to save image {file.filename}: {e}")
            results.append(ImageUploadResponse(
                image_id=None,
                local_url=None,
                status="error",
                message=str(e),
            ))
            error_count += 1

    # 更新任务的图片统计
    result_summary = json.loads(task.result_summary) if task.result_summary else {}
    image_stats = result_summary.get('image_stats', {'saved': 0, 'duplicates': 0, 'errors': 0})
    image_stats['saved'] = image_stats.get('saved', 0) + saved_count
    image_stats['duplicates'] = image_stats.get('duplicates', 0) + duplicate_count
    image_stats['errors'] = image_stats.get('errors', 0) + error_count
    result_summary['image_stats'] = image_stats
    task.result_summary = json.dumps(result_summary)
    db.commit()

    logger.info(f"Batch image upload for task {task_id}: "
                f"saved={saved_count}, duplicates={duplicate_count}, errors={error_count}")

    return ImageBatchUploadResponse(
        total=len(files),
        saved=saved_count,
        duplicates=duplicate_count,
        errors=error_count,
        images=results,
    )
