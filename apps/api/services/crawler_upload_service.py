"""
爬虫图片上传服务 - 处理爬虫任务图片上传和去重
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile

from packages.scraper.database import get_crawler_db
from packages.scraper.models import CrawlerTask
from packages.agents.equipment_import.models.pending import PendingEquipment
from apps.api.orm.session import get_db_session
from apps.api.schemas.crawler import (
    CrawlerProductUpload,
    CrawlerUploadResponse,
    DownloadedProductsResponse,
    CheckDuplicatesResponse,
)

logger = logging.getLogger(__name__)

# 图片存储基础路径
IMAGES_BASE_PATH = Path(__file__).parents[3] / "shared" / "images"


def generate_product_id(brand_name: str, product_name: str) -> str:
    """
    生成产品标识

    Args:
        brand_name: 品牌名称
        product_name: 产品名称

    Returns:
        str: 品牌_产品名 格式的标识
    """
    brand = brand_name.strip().lower()
    product = product_name.strip().lower()

    # 替换特殊字符为下划线
    brand = re.sub(r'[^\w\-]', '_', brand)
    product = re.sub(r'[^\w\-]', '_', product)

    # 合并连续下划线
    brand = re.sub(r'_+', '_', brand).strip('_')
    product = re.sub(r'_+', '_', product).strip('_')

    return f"{brand}_{product}"


class CrawlerUploadService:
    """爬虫上传服务"""

    def __init__(self):
        self.images_base_path = IMAGES_BASE_PATH

    def upload_products(
        self,
        task_id: int,
        products: List[CrawlerProductUpload],
        files: List[UploadFile]
    ) -> CrawlerUploadResponse:
        """
        批量上传产品并创建待审核记录

        Args:
            task_id: 爬虫任务ID
            products: 产品列表（元数据）
            files: 上传的图片文件列表

        Returns:
            CrawlerUploadResponse: 上传结果
        """
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0
        pending_ids: List[int] = []
        skipped_products: List[str] = []
        errors: List[str] = []

        # 获取任务已下载的产品列表
        downloaded = self._get_downloaded_products_set(task_id)

        # 构建文件索引：{product_index}_{image_index} -> file
        file_map = {}
        for f in files:
            # 文件名格式: {product_index}_{image_index}.{ext}
            # 例如: 0_0.jpg, 0_1.jpg, 1_0.jpg
            name_without_ext = Path(f.filename).stem if f.filename else ""
            file_map[name_without_ext] = f

        # 处理每个产品
        for idx, product in enumerate(products):
            product_id = product.product_id

            # 检查是否已下载
            if product_id in downloaded:
                skipped_count += 1
                skipped_products.append(product_id)
                logger.debug(f"跳过已下载产品: {product_id}")
                continue

            try:
                # 收集该产品的图片文件
                product_files = []
                for img_idx in range(product.image_count):
                    key = f"{idx}_{img_idx}"
                    if key in file_map:
                        product_files.append(file_map[key])
                    else:
                        logger.warning(f"未找到产品 {product_id} 的图片: {key}")

                if not product_files:
                    errors.append(f"产品 {product_id} 没有有效图片")
                    failed_count += 1
                    continue

                # 创建 PendingEquipment 记录
                pending_id = self._create_pending_equipment(
                    task_id=task_id,
                    product=product
                )

                # 保存图片
                image_paths = self._save_images(pending_id, product_files)

                # 更新 PendingEquipment 的 images 字段
                self._update_pending_images(pending_id, image_paths)

                # 更新任务的已下载列表
                downloaded.add(product_id)

                pending_ids.append(pending_id)
                uploaded_count += 1
                logger.info(f"产品上传成功: {product_id}, pending_id={pending_id}")

            except Exception as e:
                logger.error(f"处理产品 {product_id} 失败: {e}", exc_info=True)
                errors.append(f"产品 {product_id} 处理失败: {str(e)}")
                failed_count += 1

        # 更新任务的 downloaded_products 字段
        self._update_task_downloaded_products(task_id, list(downloaded))

        return CrawlerUploadResponse(
            success=uploaded_count > 0 or skipped_count > 0,
            task_id=task_id,
            uploaded_count=uploaded_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            pending_ids=pending_ids,
            skipped_products=skipped_products,
            errors=errors
        )

    def get_downloaded_products(self, task_id: int) -> DownloadedProductsResponse:
        """
        获取任务已下载产品列表

        Args:
            task_id: 爬虫任务ID

        Returns:
            DownloadedProductsResponse: 已下载产品列表
        """
        products = list(self._get_downloaded_products_set(task_id))
        return DownloadedProductsResponse(
            task_id=task_id,
            products=products,
            count=len(products)
        )

    def check_duplicates(
        self,
        product_ids: List[str],
        task_id: Optional[int] = None
    ) -> CheckDuplicatesResponse:
        """
        检查产品是否已存在

        Args:
            product_ids: 产品标识列表
            task_id: 任务ID（可选）

        Returns:
            CheckDuplicatesResponse: 检查结果
        """
        exists: List[str] = []
        new: List[str] = []

        # 获取已存在的产品标识
        existing_set = set()

        # 1. 如果指定了任务ID，检查该任务的已下载列表
        if task_id:
            existing_set.update(self._get_downloaded_products_set(task_id))

        # 2. 检查 pending_equipment 表
        existing_set.update(self._get_pending_product_ids())

        # 分类
        for pid in product_ids:
            if pid in existing_set:
                exists.append(pid)
            else:
                new.append(pid)

        return CheckDuplicatesResponse(
            exists=exists,
            new=new
        )

    def _get_downloaded_products_set(self, task_id: int) -> set:
        """获取任务已下载产品集合"""
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).get(task_id)
            if task and task.downloaded_products:
                try:
                    return set(json.loads(task.downloaded_products))
                except json.JSONDecodeError:
                    logger.warning(f"解析任务 {task_id} 的 downloaded_products 失败")
        return set()

    def _get_pending_product_ids(self) -> set:
        """获取所有待审核产品的标识"""
        result = set()
        with get_db_session() as session:
            pending_items = session.query(
                PendingEquipment.brand_name,
                PendingEquipment.product_name
            ).filter(
                PendingEquipment.status == "pending"
            ).all()

            for brand, product in pending_items:
                if brand and product:
                    result.add(generate_product_id(brand, product))

        return result

    def _create_pending_equipment(
        self,
        task_id: int,
        product: CrawlerProductUpload
    ) -> int:
        """
        创建待审核装备记录

        Args:
            task_id: 爬虫任务ID
            product: 产品信息

        Returns:
            int: 新创建的 pending_equipment ID
        """
        with get_db_session() as session:
            pending = PendingEquipment(
                ocr_text="",  # OCR 文本待后续识别
                source_type="ecommerce",
                source_url=product.source_url,
                extracted_data="{}",  # 待后续 LLM 提取
                confidence=0.0,
                equipment_type=product.equipment_type,
                brand_name=product.brand_name,
                product_name=product.product_name,
                status="pending",
                task_id=task_id,
                images=None  # 稍后更新
            )

            session.add(pending)
            session.flush()
            pending_id = pending.id

        return pending_id

    def _save_images(
        self,
        pending_id: int,
        files: List[UploadFile]
    ) -> List[str]:
        """
        保存图片文件

        Args:
            pending_id: 待审核记录ID
            files: 上传的文件列表

        Returns:
            List[str]: 保存的图片相对路径列表
        """
        # 创建目录
        save_dir = self.images_base_path / "pending" / str(pending_id)
        save_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        for idx, file in enumerate(files, 1):
            # 确定扩展名
            ext = "jpg"
            if file.content_type:
                if "png" in file.content_type:
                    ext = "png"
                elif "webp" in file.content_type:
                    ext = "webp"

            # 保存文件
            filename = f"{idx}.{ext}"
            file_path = save_dir / filename
            with open(file_path, "wb") as f:
                content = file.file.read()
                f.write(content)
                file.file.seek(0)  # 重置文件指针

            # 记录相对路径
            relative_path = f"pending/{pending_id}/{filename}"
            image_paths.append(relative_path)
            logger.debug(f"图片已保存: {relative_path}")

        return image_paths

    def _update_pending_images(self, pending_id: int, image_paths: List[str]):
        """更新待审核记录的图片路径"""
        with get_db_session() as session:
            pending = session.query(PendingEquipment).get(pending_id)
            if pending:
                pending.images = json.dumps(image_paths, ensure_ascii=False)

    def _update_task_downloaded_products(self, task_id: int, products: List[str]):
        """更新任务的已下载产品列表"""
        db = get_crawler_db()
        with db.session_scope() as session:
            task = session.query(CrawlerTask).get(task_id)
            if task:
                task.downloaded_products = json.dumps(products, ensure_ascii=False)
