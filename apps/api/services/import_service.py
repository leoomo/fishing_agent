"""
CSV/JSON 导入服务
"""

import csv
import io
import json
from typing import Dict, List
import logging

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository

logger = logging.getLogger(__name__)


class ImportService:
    """导入服务"""

    def import_from_csv(self, csv_string: str) -> Dict:
        """
        从 CSV 导入装备

        Args:
            csv_string: CSV 文件内容

        Returns:
            dict: {
                "success_count": 成功数,
                "error_count": 失败数,
                "errors": [错误列表]
            }
        """
        success_count = 0
        error_count = 0
        errors = []

        # 解析 CSV
        csv_file = io.StringIO(csv_string)
        reader = csv.DictReader(csv_file)

        with get_db_session() as session:
            equipment_repo = EquipmentRepository(session)
            brand_repo = BrandRepository(session)

            for row_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是表头）
                try:
                    # 解析 brand_name → brand_id
                    brand_name = row.get('brand_name')
                    if not brand_name:
                        raise ValueError("缺少品牌名称")

                    # 获取或创建品牌
                    brand, created = brand_repo.get_or_create_by_name(brand_name)
                    if created:
                        session.flush()
                        logger.info(f"自动创建品牌: {brand_name}")

                    # 构造装备数据
                    equipment_data = {
                        "name": row.get('name'),
                        "category": row.get('category'),
                        "brand_id": brand.brand_id,
                        "model": row.get('model'),
                        "price_min": float(row['price_min']) if row.get('price_min') else None,
                        "price_max": float(row['price_max']) if row.get('price_max') else None,
                        "description": row.get('description'),
                        "features": row.get('features'),
                        "user_level": row.get('user_level', '新手'),
                        "source": "csv_import"
                    }

                    # 验证必需字段
                    if not equipment_data.get('name'):
                        raise ValueError("缺少装备名称")
                    if not equipment_data.get('category'):
                        raise ValueError("缺少装备类别")

                    # 创建装备
                    equipment_repo.create(equipment_data)
                    session.flush()
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": row_num,
                        "data": row,
                        "error": str(e)
                    })
                    logger.error(f"CSV 导入错误（行 {row_num}）: {e}")

            # 提交所有成功的导入
            if success_count > 0:
                session.commit()
                logger.info(f"CSV 导入成功: {success_count} 条记录")

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }

    def import_from_json(self, json_string: str) -> Dict:
        """
        从 JSON 导入装备

        Args:
            json_string: JSON 文件内容

        Returns:
            dict: {
                "success_count": 成功数,
                "error_count": 失败数,
                "errors": [错误列表]
            }
        """
        success_count = 0
        error_count = 0
        errors = []

        try:
            data = json.loads(json_string)

            # 确保数据是列表
            if not isinstance(data, list):
                data = [data]

        except json.JSONDecodeError as e:
            return {
                "success_count": 0,
                "error_count": 1,
                "errors": [{"row": 0, "error": f"JSON 解析失败: {str(e)}"}]
            }

        with get_db_session() as session:
            equipment_repo = EquipmentRepository(session)
            brand_repo = BrandRepository(session)

            for idx, item in enumerate(data):
                try:
                    # 解析品牌
                    brand_name = item.get('brand_name')
                    if not brand_name:
                        raise ValueError("缺少品牌名称")

                    # 获取或创建品牌
                    brand, created = brand_repo.get_or_create_by_name(brand_name)
                    if created:
                        session.flush()
                        logger.info(f"自动创建品牌: {brand_name}")

                    # 构造装备数据
                    equipment_data = {
                        "name": item.get('name'),
                        "category": item.get('category'),
                        "brand_id": brand.brand_id,
                        "model": item.get('model'),
                        "price_min": item.get('price_min'),
                        "price_max": item.get('price_max'),
                        "description": item.get('description'),
                        "features": item.get('features'),
                        "user_level": item.get('user_level', '新手'),
                        "source": "json_import"
                    }

                    # 验证必需字段
                    if not equipment_data.get('name'):
                        raise ValueError("缺少装备名称")
                    if not equipment_data.get('category'):
                        raise ValueError("缺少装备类别")

                    # 提取规格数据
                    specs = item.get('specs')

                    # 创建装备（包含规格）
                    equipment_repo.create_with_specs(
                        equipment_data=equipment_data,
                        spec_data=specs
                    )
                    session.flush()
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append({
                        "row": idx + 1,
                        "data": item,
                        "error": str(e)
                    })
                    logger.error(f"JSON 导入错误（记录 {idx + 1}）: {e}")

            # 提交所有成功的导入
            if success_count > 0:
                session.commit()
                logger.info(f"JSON 导入成功: {success_count} 条记录")

        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
