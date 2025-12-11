"""
CSV/JSON 导出服务
"""

import csv
import io
import json
from typing import Dict, List, Optional
import logging

from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository

logger = logging.getLogger(__name__)


class ExportService:
    """导出服务"""

    def export_to_csv(
        self,
        filters: Optional[Dict] = None,
        limit: int = 1000
    ) -> str:
        """
        导出装备为 CSV

        Args:
            filters: 筛选条件
            limit: 最大导出数量

        Returns:
            str: CSV 格式的装备数据
        """
        filters = filters or {}

        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 查询装备
            equipment_list = repo.search(
                category=filters.get('category'),
                brand_id=filters.get('brand_id'),
                user_level=filters.get('user_level'),
                is_active=filters.get('is_active', True),
                limit=limit,
                offset=0,
                preload=True
            )

            # 创建 CSV
            output = io.StringIO()
            fieldnames = [
                'equipment_id',
                'name',
                'category',
                'brand_name',
                'model',
                'price_min',
                'price_max',
                'price_currency',
                'description',
                'features',
                'user_level',
                'is_active',
                'source',
                'created_at'
            ]

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for eq in equipment_list:
                writer.writerow({
                    'equipment_id': eq.equipment_id,
                    'name': eq.name,
                    'category': eq.category,
                    'brand_name': eq.brand.name_cn if eq.brand else '',
                    'model': eq.model or '',
                    'price_min': eq.price_min or '',
                    'price_max': eq.price_max or '',
                    'price_currency': 'CNY',  # 默认使用人民币
                    'description': eq.description or '',
                    'features': eq.features or '',
                    'user_level': eq.user_level,
                    'is_active': eq.is_active,
                    'source': eq.source,
                    'created_at': eq.created_at.isoformat()
                })

            logger.info(f"CSV 导出完成: {len(equipment_list)} 条记录")
            return output.getvalue()

    def export_to_json(
        self,
        filters: Optional[Dict] = None,
        limit: int = 1000,
        include_specs: bool = True
    ) -> str:
        """
        导出装备为 JSON（包含完整规格和关联数据）

        Args:
            filters: 筛选条件
            limit: 最大导出数量
            include_specs: 是否包含详细规格

        Returns:
            str: JSON 格式的装备数据
        """
        filters = filters or {}

        with get_db_session() as session:
            repo = EquipmentRepository(session)

            # 查询装备
            equipment_list = repo.search(
                category=filters.get('category'),
                brand_id=filters.get('brand_id'),
                user_level=filters.get('user_level'),
                is_active=filters.get('is_active', True),
                limit=limit,
                offset=0,
                preload=True
            )

            # 转换为字典列表
            result = []
            for eq in equipment_list:
                equipment_dict = {
                    'equipment_id': eq.equipment_id,
                    'name': eq.name,
                    'category': eq.category,
                    'brand_id': eq.brand_id,
                    'brand_name': eq.brand.name_cn if eq.brand else None,
                    'model': eq.model,
                    'price_min': eq.price_min,
                    'price_max': eq.price_max,
                    'price_currency': 'CNY',  # 默认使用人民币
                    'description': eq.description,
                    'features': eq.features,
                    'user_level': eq.user_level,
                    'is_active': eq.is_active,
                    'source': eq.source,
                    'source_url': eq.source_url,
                    'created_at': eq.created_at.isoformat(),
                    'updated_at': eq.updated_at.isoformat()
                }

                # 添加规格（如果请求）
                if include_specs:
                    specs = None

                    if eq.category == "鱼竿" and eq.rod_spec:
                        specs = {
                            "length": eq.rod_spec.length,
                            "power": eq.rod_spec.power,
                            "action": eq.rod_spec.action,
                            "lure_weight_min": eq.rod_spec.lure_weight_min,
                            "lure_weight_max": eq.rod_spec.lure_weight_max,
                            "sections": eq.rod_spec.sections,
                            "closed_length": eq.rod_spec.closed_length,
                            "weight": eq.rod_spec.weight
                        }
                    elif eq.category == "渔轮" and eq.reel_spec:
                        specs = {
                            "gear_ratio": eq.reel_spec.gear_ratio,
                            "bearings": eq.reel_spec.bearings,
                            "max_drag": eq.reel_spec.max_drag,
                            "line_capacity": eq.reel_spec.line_capacity,
                            "weight": eq.reel_spec.weight,
                            "spool_type": eq.reel_spec.spool_type
                        }
                    elif eq.category == "鱼线" and eq.line_spec:
                        specs = {
                            "line_type": eq.line_spec.line_type,
                            "diameter": eq.line_spec.diameter,
                            "breaking_strength": eq.line_spec.breaking_strength,
                            "length": eq.line_spec.length,
                            "material": eq.line_spec.material
                        }
                    elif eq.category == "拟饵" and eq.lure_spec:
                        specs = {
                            "lure_type": eq.lure_spec.lure_type,
                            "weight": eq.lure_spec.weight,
                            "length": eq.lure_spec.length,
                            "diving_depth": eq.lure_spec.diving_depth,
                            "action_type": eq.lure_spec.action_type
                        }

                    equipment_dict['specs'] = specs

                result.append(equipment_dict)

            logger.info(f"JSON 导出完成: {len(equipment_list)} 条记录")
            return json.dumps(result, ensure_ascii=False, indent=2)
