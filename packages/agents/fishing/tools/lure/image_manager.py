"""
图片管理模块

提供图片存储和管理功能：
- ImageStorageAdapter: 存储适配器抽象接口
- LocalImageStorage: 本地文件系统存储实现
- ImageManager: 图片管理器（关联数据库操作）
"""

import os
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO
from dataclasses import dataclass
from datetime import datetime

# 尝试导入PIL，如果不存在则标记
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


@dataclass
class ImageMetadata:
    """图片元数据"""
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None


@dataclass
class ImageInfo:
    """图片信息"""
    image_id: int
    image_url: str
    image_type: str
    description: Optional[str]
    display_order: int
    metadata: Optional[ImageMetadata] = None


class ImageStorageAdapter(ABC):
    """图片存储适配器抽象基类"""

    @abstractmethod
    def save(self, image_data: bytes, relative_path: str) -> str:
        """保存图片，返回访问URL"""
        pass

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """删除图片"""
        pass

    @abstractmethod
    def get_url(self, relative_path: str) -> str:
        """获取图片访问URL"""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """检查图片是否存在"""
        pass

    @abstractmethod
    def get_metadata(self, relative_path: str) -> Optional[ImageMetadata]:
        """获取图片元数据"""
        pass

    @abstractmethod
    def get_full_path(self, relative_path: str) -> str:
        """获取图片完整路径"""
        pass


class LocalImageStorage(ImageStorageAdapter):
    """本地文件系统存储实现"""

    def __init__(self, base_path: str):
        """
        初始化本地存储

        Args:
            base_path: 图片存储的基础路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, image_data: bytes, relative_path: str) -> str:
        """保存图片到本地文件系统"""
        full_path = self.base_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(image_data)

        return self.get_url(relative_path)

    def save_from_file(self, source_path: str, relative_path: str) -> str:
        """从文件复制图片"""
        with open(source_path, 'rb') as f:
            image_data = f.read()
        return self.save(image_data, relative_path)

    def delete(self, relative_path: str) -> bool:
        """删除图片"""
        full_path = self.base_path / relative_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def get_url(self, relative_path: str) -> str:
        """获取本地文件URL"""
        full_path = self.base_path / relative_path
        return f"file://{full_path.absolute()}"

    def get_relative_url(self, relative_path: str) -> str:
        """获取相对路径URL（用于Web展示）"""
        return f"images/{relative_path}"

    def exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        return (self.base_path / relative_path).exists()

    def get_full_path(self, relative_path: str) -> str:
        """获取完整文件路径"""
        return str(self.base_path / relative_path)

    def get_metadata(self, relative_path: str) -> Optional[ImageMetadata]:
        """获取图片元数据"""
        full_path = self.base_path / relative_path
        if not full_path.exists():
            return None

        file_size = full_path.stat().st_size
        width, height, fmt = None, None, None

        if HAS_PIL:
            try:
                with Image.open(full_path) as img:
                    width, height = img.size
                    fmt = img.format.lower() if img.format else None
            except Exception:
                pass

        if fmt is None:
            # 从扩展名推断格式
            fmt = full_path.suffix.lower().lstrip('.')

        return ImageMetadata(
            file_size=file_size,
            width=width,
            height=height,
            format=fmt
        )


class OSSImageStorage(ImageStorageAdapter):
    """阿里云OSS存储实现（预留）"""

    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key: str,
        secret_key: str
    ):
        self.endpoint = endpoint
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        # self.client = oss2.Bucket(...)  # 未来实现

    def save(self, image_data: bytes, relative_path: str) -> str:
        raise NotImplementedError("OSS storage not implemented yet")

    def delete(self, relative_path: str) -> bool:
        raise NotImplementedError("OSS storage not implemented yet")

    def get_url(self, relative_path: str) -> str:
        return f"https://{self.bucket}.{self.endpoint}/{relative_path}"

    def exists(self, relative_path: str) -> bool:
        raise NotImplementedError("OSS storage not implemented yet")

    def get_metadata(self, relative_path: str) -> Optional[ImageMetadata]:
        raise NotImplementedError("OSS storage not implemented yet")

    def get_full_path(self, relative_path: str) -> str:
        return self.get_url(relative_path)


class ImageManager:
    """图片管理器

    整合存储适配器和数据库操作，提供完整的图片管理功能。
    """

    def __init__(self, db, storage: ImageStorageAdapter):
        """
        初始化图片管理器

        Args:
            db: 数据库实例 (LureDatabase)
            storage: 存储适配器实例
        """
        self.db = db
        self.storage = storage

    # ========== 查询方法 ==========

    def get_equipment_images(
        self,
        equipment_id: int,
        image_type: Optional[str] = None
    ) -> List[ImageInfo]:
        """获取装备的图片列表"""
        query = """
            SELECT image_id, image_url, image_type, description, display_order,
                   file_size, width, height, format
            FROM product_images
            WHERE equipment_id = ?
        """
        params = [equipment_id]

        if image_type:
            query += " AND image_type = ?"
            params.append(image_type)

        query += " ORDER BY display_order, image_id"

        rows = self.db.execute(query, tuple(params))
        return [self._row_to_image_info(row) for row in rows]

    def get_rig_images(
        self,
        rig_type_id: int,
        image_type: Optional[str] = None
    ) -> List[ImageInfo]:
        """获取钓组的图片列表"""
        query = """
            SELECT image_id, image_url, image_type, description, display_order,
                   file_size, width, height, format
            FROM product_images
            WHERE rig_type_id = ?
        """
        params = [rig_type_id]

        if image_type:
            query += " AND image_type = ?"
            params.append(image_type)

        query += " ORDER BY display_order, image_id"

        rows = self.db.execute(query, tuple(params))
        return [self._row_to_image_info(row) for row in rows]

    def get_fish_images(
        self,
        species_id: int,
        image_type: Optional[str] = None
    ) -> List[ImageInfo]:
        """获取鱼类的图片列表"""
        query = """
            SELECT image_id, image_url, image_type, description, display_order,
                   file_size, width, height, format
            FROM product_images
            WHERE species_id = ?
        """
        params = [species_id]

        if image_type:
            query += " AND image_type = ?"
            params.append(image_type)

        query += " ORDER BY display_order, image_id"

        rows = self.db.execute(query, tuple(params))
        return [self._row_to_image_info(row) for row in rows]

    def get_main_image(self, equipment_id: int) -> Optional[str]:
        """获取装备主图URL"""
        images = self.get_equipment_images(equipment_id, image_type='main')
        return images[0].image_url if images else None

    def get_image_by_id(self, image_id: int) -> Optional[ImageInfo]:
        """根据ID获取图片信息"""
        query = """
            SELECT image_id, image_url, image_type, description, display_order,
                   file_size, width, height, format
            FROM product_images
            WHERE image_id = ?
        """
        rows = self.db.execute(query, (image_id,))
        return self._row_to_image_info(rows[0]) if rows else None

    # ========== 写入方法 ==========

    def add_image(
        self,
        image_data: bytes,
        relative_path: str,
        image_type: str,
        equipment_id: Optional[int] = None,
        rig_type_id: Optional[int] = None,
        species_id: Optional[int] = None,
        description: Optional[str] = None,
        display_order: int = 0
    ) -> int:
        """
        添加图片

        Args:
            image_data: 图片二进制数据
            relative_path: 相对存储路径
            image_type: 图片类型 (main/detail/infographic/action/color等)
            equipment_id: 关联装备ID
            rig_type_id: 关联钓组ID
            species_id: 关联鱼类ID
            description: 图片描述
            display_order: 展示顺序

        Returns:
            新创建的图片ID
        """
        # 验证：必须关联一个实体
        entity_count = sum([
            equipment_id is not None,
            rig_type_id is not None,
            species_id is not None
        ])
        if entity_count != 1:
            raise ValueError("必须且只能关联一个实体（equipment/rig/fish）")

        # 保存文件
        image_url = self.storage.save(image_data, relative_path)

        # 获取元数据
        metadata = self.storage.get_metadata(relative_path)

        # 写入数据库
        query = """
            INSERT INTO product_images (
                equipment_id, rig_type_id, species_id,
                image_url, image_type, description, display_order,
                file_size, width, height, format
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            equipment_id, rig_type_id, species_id,
            image_url, image_type, description, display_order,
            metadata.file_size if metadata else None,
            metadata.width if metadata else None,
            metadata.height if metadata else None,
            metadata.format if metadata else None
        )

        return self.db.execute_write(query, params)

    def add_image_from_file(
        self,
        source_path: str,
        relative_path: str,
        image_type: str,
        equipment_id: Optional[int] = None,
        rig_type_id: Optional[int] = None,
        species_id: Optional[int] = None,
        description: Optional[str] = None,
        display_order: int = 0
    ) -> int:
        """从文件添加图片"""
        with open(source_path, 'rb') as f:
            image_data = f.read()

        return self.add_image(
            image_data=image_data,
            relative_path=relative_path,
            image_type=image_type,
            equipment_id=equipment_id,
            rig_type_id=rig_type_id,
            species_id=species_id,
            description=description,
            display_order=display_order
        )

    def add_image_url(
        self,
        image_url: str,
        image_type: str,
        equipment_id: Optional[int] = None,
        rig_type_id: Optional[int] = None,
        species_id: Optional[int] = None,
        description: Optional[str] = None,
        display_order: int = 0
    ) -> int:
        """直接添加图片URL（不经过存储适配器）"""
        # 验证：必须关联一个实体
        entity_count = sum([
            equipment_id is not None,
            rig_type_id is not None,
            species_id is not None
        ])
        if entity_count != 1:
            raise ValueError("必须且只能关联一个实体（equipment/rig/fish）")

        query = """
            INSERT INTO product_images (
                equipment_id, rig_type_id, species_id,
                image_url, image_type, description, display_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            equipment_id, rig_type_id, species_id,
            image_url, image_type, description, display_order
        )

        return self.db.execute_write(query, params)

    def delete_image(self, image_id: int) -> bool:
        """
        删除图片（含物理文件和数据库记录）

        Args:
            image_id: 图片ID

        Returns:
            是否删除成功
        """
        # 查询图片信息
        query = "SELECT image_url, embedding_id FROM product_images WHERE image_id = ?"
        rows = self.db.execute(query, (image_id,))

        if not rows:
            return False

        image_url = rows[0]['image_url']
        embedding_id = rows[0].get('embedding_id')

        # 1. 删除物理文件（如果是本地文件）
        if image_url.startswith('file://'):
            relative_path = self._url_to_relative_path(image_url)
            if relative_path:
                self.storage.delete(relative_path)

        # 2. TODO: 删除向量（如果存在）
        # if embedding_id:
        #     vector_store.delete(embedding_id)

        # 3. 删除数据库记录
        delete_query = "DELETE FROM product_images WHERE image_id = ?"
        self.db.execute_write(delete_query, (image_id,))

        return True

    def update_image_order(self, image_id: int, display_order: int) -> bool:
        """更新图片展示顺序"""
        query = """
            UPDATE product_images
            SET display_order = ?, updated_at = CURRENT_TIMESTAMP
            WHERE image_id = ?
        """
        affected = self.db.execute_write(query, (display_order, image_id))
        return affected > 0

    # ========== 向量化相关 ==========

    def mark_vectorized(self, image_id: int, embedding_id: str) -> None:
        """标记图片已向量化"""
        query = """
            UPDATE product_images
            SET embedding_id = ?, is_vectorized = 1, updated_at = CURRENT_TIMESTAMP
            WHERE image_id = ?
        """
        self.db.execute_write(query, (embedding_id, image_id))

    def get_unvectorized_images(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取未向量化的图片列表"""
        query = """
            SELECT image_id, image_url, description,
                   equipment_id, rig_type_id, species_id
            FROM product_images
            WHERE is_vectorized = 0
            LIMIT ?
        """
        return self.db.execute(query, (limit,))

    # ========== 工具方法 ==========

    def generate_relative_path(
        self,
        entity_type: str,
        entity_name: str,
        image_type: str,
        suffix: str = 'jpg'
    ) -> str:
        """
        生成标准化的相对路径

        Args:
            entity_type: 实体类型 (products/rods/reels/lures/rigs/fish)
            entity_name: 实体名称
            image_type: 图片类型 (main/detail/infographic等)
            suffix: 文件后缀

        Returns:
            相对路径，如 products/rods/shimano_zodias_264ml_main.jpg
        """
        # 规范化名称
        safe_name = self._sanitize_filename(entity_name)
        filename = f"{safe_name}_{image_type}.{suffix}"

        if entity_type in ['rods', 'reels', 'lines', 'lures']:
            return f"products/{entity_type}/{filename}"
        else:
            return f"{entity_type}/{filename}"

    # ========== 私有方法 ==========

    def _row_to_image_info(self, row: Dict) -> ImageInfo:
        """将数据库行转换为ImageInfo对象"""
        metadata = None
        if row.get('file_size'):
            metadata = ImageMetadata(
                file_size=row['file_size'],
                width=row.get('width'),
                height=row.get('height'),
                format=row.get('format')
            )

        return ImageInfo(
            image_id=row['image_id'],
            image_url=row['image_url'],
            image_type=row['image_type'],
            description=row.get('description'),
            display_order=row.get('display_order', 0),
            metadata=metadata
        )

    def _url_to_relative_path(self, image_url: str) -> Optional[str]:
        """从URL提取相对路径"""
        if image_url.startswith('file://'):
            full_path = image_url[7:]  # 去掉 file://
            base_str = str(self.storage.base_path.absolute())
            if full_path.startswith(base_str):
                return full_path[len(base_str):].lstrip('/')
        return None

    def _sanitize_filename(self, name: str) -> str:
        """规范化文件名"""
        # 替换空格和特殊字符
        import re
        safe = re.sub(r'[^\w\-]', '_', name.lower())
        # 移除连续下划线
        safe = re.sub(r'_+', '_', safe)
        # 移除首尾下划线
        return safe.strip('_')
