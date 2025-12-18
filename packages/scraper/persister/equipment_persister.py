"""
数据持久化器

负责将爬取的装备数据保存到数据库，包括：
- 数据去重检查
- 品牌确保存在
- 装备主表插入
- 规格表插入
- 图片下载和保存
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from packages.scraper.spider.base import CrawlItem as EquipmentData
# 注意：以下模块需要由调用方注入，不在此处导入
# deduplicator, downloader, LureDatabase, ImageManager 通过构造函数注入

logger = logging.getLogger(__name__)


class DataPersister:
    """数据持久化器"""

    def __init__(
        self,
        db,  # 数据库实例 (SQLAlchemy Session 或类似接口)
        image_manager=None,  # 图片管理器
        deduplicator=None,  # 去重器（可选，不提供则自动创建）
        image_downloader=None,  # 图片下载器（可选，不提供则自动创建）
    ):
        """
        初始化数据持久化器

        Args:
            db: 数据库实例
            image_manager: 图片管理器
            deduplicator: 去重器（可选，不提供则自动创建）
            image_downloader: 图片下载器（可选，不提供则自动创建）
        """
        self.db = db
        self.image_manager = image_manager
        self.deduplicator = deduplicator
        self.image_downloader = image_downloader

        # 统计信息
        self.stats = {
            "total_processed": 0,
            "inserted": 0,
            "updated": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

        logger.info("初始化数据持久化器")

    def save_equipment(
        self, equipment: EquipmentData, update_if_exists: bool = True
    ) -> Optional[int]:
        """
        保存装备数据

        Args:
            equipment: 装备数据
            update_if_exists: 如果已存在是否更新（默认True）

        Returns:
            装备ID，失败返回None
        """
        self.stats["total_processed"] += 1

        try:
            # ========== 步骤1: 检查去重 ==========
            existing_id = self.deduplicator.find_duplicates(equipment)

            if existing_id:
                if update_if_exists and equipment.source_url:
                    # 如果是爬虫数据且允许更新
                    logger.info(f"找到重复装备 (ID:{existing_id})，执行更新")
                    self._update_equipment(existing_id, equipment)
                    self.stats["updated"] += 1
                    return existing_id
                else:
                    # 跳过重复
                    logger.info(f"跳过重复装备 (ID:{existing_id})")
                    self.stats["duplicates_skipped"] += 1
                    return existing_id

            # ========== 步骤2: 确保品牌存在 ==========
            brand_id = self._ensure_brand_exists(equipment.brand_name)
            if not brand_id:
                logger.error(f"创建品牌失败: {equipment.brand_name}")
                self.stats["errors"] += 1
                return None

            # ========== 步骤3: 插入装备主表 ==========
            equipment_id = self._insert_equipment(equipment, brand_id)
            if not equipment_id:
                logger.error(f"插入装备主表失败: {equipment.name}")
                self.stats["errors"] += 1
                return None

            logger.info(f"成功插入装备: {equipment.name} (ID:{equipment_id})")
            self.stats["inserted"] += 1

            # ========== 步骤4: 插入规格表 ==========
            if equipment.specs:
                self._insert_specs(equipment_id, equipment)

            # ========== 步骤5: 下载并保存图片 ==========
            if equipment.images:
                self._save_images(equipment_id, equipment)

            return equipment_id

        except Exception as e:
            logger.error(f"保存装备数据失败: {e}", exc_info=True)
            self.stats["errors"] += 1
            return None

    def _ensure_brand_exists(self, brand_name: str) -> Optional[int]:
        """
        确保品牌存在，不存在则创建

        Args:
            brand_name: 品牌名称

        Returns:
            品牌ID
        """
        # 查询品牌是否存在
        query = "SELECT id FROM brands WHERE name_cn = ?"
        rows = self.db.execute(query, (brand_name,))

        if rows:
            return rows[0]["id"]

        # 创建新品牌
        insert_query = """
        INSERT INTO brands (name_cn, tier, description)
        VALUES (?, ?, ?)
        """
        brand_id = self.db.execute_write(
            insert_query, (brand_name, "未知", f"由爬虫自动创建的品牌：{brand_name}")
        )

        logger.info(f"创建新品牌: {brand_name} (ID:{brand_id})")
        return brand_id

    def _insert_equipment(self, equipment: EquipmentData, brand_id: int) -> Optional[int]:
        """
        插入装备主表

        Args:
            equipment: 装备数据
            brand_id: 品牌ID

        Returns:
            装备ID
        """
        insert_query = """
        INSERT INTO equipment (
            name, category, brand_id, model,
            price_min, price_max, description, features,
            target_fish, user_level, is_active,
            source, source_url, crawled_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # 准备数据
        features_json = equipment.features if equipment.features else None
        crawled_at = datetime.now().isoformat() if equipment.source_url else None

        params = (
            equipment.name,
            equipment.category,
            brand_id,
            equipment.model,
            equipment.price_min,
            equipment.price_max,
            equipment.description,
            features_json,
            equipment.target_fish,
            equipment.user_level,
            1,  # is_active
            "crawler" if equipment.source_url else "manual",  # source
            equipment.source_url,
            crawled_at,
        )

        equipment_id = self.db.execute_write(insert_query, params)
        return equipment_id

    def _update_equipment(self, equipment_id: int, equipment: EquipmentData):
        """
        更新装备数据

        Args:
            equipment_id: 装备ID
            equipment: 新装备数据
        """
        # 只更新价格、描述等动态字段
        update_query = """
        UPDATE equipment
        SET price_min = ?,
            price_max = ?,
            description = ?,
            last_synced_at = ?
        WHERE equipment_id = ?
        """

        params = (
            equipment.price_min,
            equipment.price_max,
            equipment.description,
            datetime.now().isoformat(),
            equipment_id,
        )

        self.db.execute_write(update_query, params)
        logger.debug(f"更新装备 (ID:{equipment_id})")

    def _insert_specs(self, equipment_id: int, equipment: EquipmentData):
        """
        插入规格表

        Args:
            equipment_id: 装备ID
            equipment: 装备数据
        """
        specs = equipment.specs
        category = equipment.category

        try:
            if category == "鱼竿":
                self._insert_rod_specs(equipment_id, specs)
            elif category == "渔轮":
                self._insert_reel_specs(equipment_id, specs)
            elif category == "鱼线":
                self._insert_line_specs(equipment_id, specs)
            elif category == "拟饵":
                self._insert_lure_specs(equipment_id, specs)

            logger.debug(f"插入规格表成功: {category} (ID:{equipment_id})")

        except Exception as e:
            logger.warning(f"插入规格表失败: {e}")

    def _insert_rod_specs(self, equipment_id: int, specs: Dict[str, Any]):
        """插入鱼竿规格"""
        insert_query = """
        INSERT INTO rod_specs (
            equipment_id, length, power, action, sections, weight
        ) VALUES (?, ?, ?, ?, ?, ?)
        """

        params = (
            equipment_id,
            specs.get("length") or specs.get("长度"),
            specs.get("power") or specs.get("硬度"),
            specs.get("action") or specs.get("调性"),
            specs.get("sections") or specs.get("节数"),
            specs.get("weight") or specs.get("自重"),
        )

        self.db.execute_write(insert_query, params)

    def _insert_reel_specs(self, equipment_id: int, specs: Dict[str, Any]):
        """插入渔轮规格"""
        insert_query = """
        INSERT INTO reel_specs (
            equipment_id, reel_type, gear_ratio, bearings, weight
        ) VALUES (?, ?, ?, ?, ?)
        """

        params = (
            equipment_id,
            specs.get("reel_type") or specs.get("轮型"),
            specs.get("gear_ratio") or specs.get("速比"),
            specs.get("bearings") or specs.get("轴承"),
            specs.get("weight") or specs.get("自重"),
        )

        self.db.execute_write(insert_query, params)

    def _insert_line_specs(self, equipment_id: int, specs: Dict[str, Any]):
        """插入鱼线规格"""
        insert_query = """
        INSERT INTO line_specs (
            equipment_id, line_type, diameter, strength_lb, length_m
        ) VALUES (?, ?, ?, ?, ?)
        """

        params = (
            equipment_id,
            specs.get("line_type") or specs.get("线型"),
            specs.get("diameter") or specs.get("线径"),
            specs.get("strength_lb") or specs.get("拉力"),
            specs.get("length_m") or specs.get("长度"),
        )

        self.db.execute_write(insert_query, params)

    def _insert_lure_specs(self, equipment_id: int, specs: Dict[str, Any]):
        """插入拟饵规格"""
        insert_query = """
        INSERT INTO lure_specs (
            equipment_id, lure_type, lure_category, length, weight
        ) VALUES (?, ?, ?, ?, ?)
        """

        params = (
            equipment_id,
            specs.get("lure_type") or specs.get("饵型"),
            specs.get("lure_category"),
            specs.get("length") or specs.get("长度"),
            specs.get("weight") or specs.get("重量"),
        )

        self.db.execute_write(insert_query, params)

    def _save_images(self, equipment_id: int, equipment: EquipmentData):
        """
        下载并保存图片

        Args:
            equipment_id: 装备ID
            equipment: 装备数据
        """
        if not equipment.images:
            return

        # 批量下载图片
        local_images = self.image_downloader.download_multiple(
            equipment.images, equipment.name
        )

        # 保存图片记录到数据库
        for i, img in enumerate(local_images):
            try:
                self._insert_image_record(equipment_id, img, i)
            except Exception as e:
                logger.warning(f"插入图片记录失败: {e}")

        logger.info(f"保存 {len(local_images)} 张图片 (ID:{equipment_id})")

    def _insert_image_record(
        self, equipment_id: int, image: Dict[str, str], order: int
    ):
        """插入图片记录"""
        insert_query = """
        INSERT INTO product_images (
            equipment_id, image_url, image_type, display_order
        ) VALUES (?, ?, ?, ?)
        """

        params = (
            equipment_id,
            image["url"],
            image.get("type", "main"),
            order,
        )

        self.db.execute_write(insert_query, params)

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_processed": 0,
            "inserted": 0,
            "updated": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }
        logger.info("统计信息已重置")
