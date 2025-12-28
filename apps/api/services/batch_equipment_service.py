"""
批量装备创建服务

支持模板 + 变体模式批量创建装备
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from apps.api.orm.session import get_db_session
from apps.api.orm.repositories.equipment_repo import EquipmentRepository
from apps.api.orm.repositories.brand_repo import BrandRepository
from apps.api.models.equipment import Equipment, RodSpec, ReelSpec, LineSpec, LureSpec
from apps.api.schemas.equipment_batch import (
    EquipmentCategory,
    BatchRodTemplate,
    RodVariantSpec,
    BatchReelTemplate,
    ReelVariantSpec,
    BatchLineTemplate,
    LineVariantSpec,
    BatchLureTemplate,
    LureVariantSpec,
    BatchEquipmentCreateResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class CreateResult:
    """单个装备创建结果"""
    success: bool
    equipment_id: Optional[int] = None
    model: str = ""
    error: Optional[str] = None
    skipped: bool = False


class BatchEquipmentService:
    """批量装备创建服务"""

    def __init__(self):
        self.category_handlers = {
            EquipmentCategory.ROD: self._create_rod,
            EquipmentCategory.REEL: self._create_reel,
            EquipmentCategory.LINE: self._create_line,
            EquipmentCategory.LURE: self._create_lure,
        }

    def batch_create(
        self,
        category: EquipmentCategory,
        template: Dict[str, Any],
        variants: List[Dict[str, Any]],
        skip_duplicates: bool = True
    ) -> BatchEquipmentCreateResponse:
        """
        批量创建装备

        Args:
            category: 装备类别
            template: 共享模板字段
            variants: 变体列表
            skip_duplicates: 是否跳过重复项

        Returns:
            BatchEquipmentCreateResponse: 批量创建结果
        """
        results: List[CreateResult] = []

        with get_db_session() as session:
            equipment_repo = EquipmentRepository(session)
            brand_repo = BrandRepository(session)

            # 验证品牌存在
            brand_id = template.get('brand_id')
            brand = brand_repo.get(brand_id)
            if not brand:
                return BatchEquipmentCreateResponse(
                    success_count=0,
                    skip_count=0,
                    error_count=len(variants),
                    errors=[{
                        "model": "all",
                        "error": f"品牌不存在: brand_id={brand_id}"
                    }]
                )

            brand_name = brand.name_cn

            # 逐个创建变体
            for variant in variants:
                model = variant.get('model', '')
                try:
                    # 检查重复
                    if skip_duplicates:
                        existing = self._check_duplicate(
                            session, brand_id, model, category.value
                        )
                        if existing:
                            results.append(CreateResult(
                                success=True,
                                model=model,
                                skipped=True
                            ))
                            continue

                    # 创建装备
                    handler = self.category_handlers.get(category)
                    if not handler:
                        results.append(CreateResult(
                            success=False,
                            model=model,
                            error=f"不支持的类别: {category}"
                        ))
                        continue

                    equipment = handler(
                        session,
                        equipment_repo,
                        brand_name,
                        template,
                        variant
                    )

                    results.append(CreateResult(
                        success=True,
                        equipment_id=equipment.equipment_id,
                        model=model
                    ))

                except Exception as e:
                    logger.error(f"创建装备失败: {model}, 错误: {e}", exc_info=True)
                    results.append(CreateResult(
                        success=False,
                        model=model,
                        error=str(e)
                    ))

            # 提交事务
            session.commit()

        # 汇总结果
        return self._summarize_results(results)

    def batch_create_rods(
        self,
        template: BatchRodTemplate,
        variants: List[RodVariantSpec],
        skip_duplicates: bool = True
    ) -> BatchEquipmentCreateResponse:
        """
        批量创建鱼竿（强类型版本）

        Args:
            template: 鱼竿模板
            variants: 变体规格列表
            skip_duplicates: 是否跳过重复项

        Returns:
            BatchEquipmentCreateResponse
        """
        return self.batch_create(
            category=EquipmentCategory.ROD,
            template=template.model_dump(),
            variants=[v.model_dump() for v in variants],
            skip_duplicates=skip_duplicates
        )

    def _check_duplicate(
        self,
        session,
        brand_id: int,
        model: str,
        category: str
    ) -> Optional[Equipment]:
        """检查是否存在重复装备"""
        return (
            session.query(Equipment)
            .filter(
                Equipment.brand_id == brand_id,
                Equipment.model == model,
                Equipment.category == category
            )
            .first()
        )

    def _generate_equipment_name(
        self,
        brand_name: str,
        product_line: str,
        model: str
    ) -> str:
        """生成装备名称: 品牌 产品线 型号"""
        return f"{brand_name} {product_line} {model}"

    def _create_rod(
        self,
        session,
        repo: EquipmentRepository,
        brand_name: str,
        template: Dict[str, Any],
        variant: Dict[str, Any]
    ) -> Equipment:
        """创建单个鱼竿"""
        model = variant['model']
        product_line = template['product_line']

        # 合并价格（变体覆盖模板）
        price_min = variant.get('price_min') or template.get('price_min')
        price_max = variant.get('price_max') or template.get('price_max')

        # 构建装备数据
        equipment_data = {
            'name': self._generate_equipment_name(brand_name, product_line, model),
            'category': '鱼竿',
            'brand_id': template['brand_id'],
            'model': model,
            'price_min': price_min,
            'price_max': price_max,
            'description': template.get('description'),
            'features': self._build_rod_features(template, variant),
            'user_level': template.get('user_level', '进阶'),
            'is_active': True,
            'source': 'batch_import',
        }

        # 构建规格数据
        spec_data = {
            'length': variant['length'],
            'power': variant['power'],
            'action': variant.get('action', 'Fast'),
            'lure_weight_min': variant.get('lure_weight_min', 0),
            'lure_weight_max': variant.get('lure_weight_max', 0),
            'sections': template.get('sections'),
            'closed_length': variant.get('closed_length'),
            'weight': variant.get('weight'),
        }

        return repo.create_with_specs(equipment_data, spec_data)

    def _create_reel(
        self,
        session,
        repo: EquipmentRepository,
        brand_name: str,
        template: Dict[str, Any],
        variant: Dict[str, Any]
    ) -> Equipment:
        """创建单个渔轮"""
        model = variant['model']
        product_line = template['product_line']

        price_min = variant.get('price_min') or template.get('price_min')
        price_max = variant.get('price_max') or template.get('price_max')

        equipment_data = {
            'name': self._generate_equipment_name(brand_name, product_line, model),
            'category': '渔轮',
            'brand_id': template['brand_id'],
            'model': model,
            'price_min': price_min,
            'price_max': price_max,
            'description': template.get('description'),
            'features': template.get('features'),
            'user_level': template.get('user_level', '进阶'),
            'is_active': True,
            'source': 'batch_import',
        }

        spec_data = {
            'gear_ratio': variant.get('gear_ratio'),
            'bearings': variant.get('bearings'),
            'max_drag': variant.get('max_drag'),
            'line_capacity': variant.get('line_capacity'),
            'weight': variant.get('weight'),
            'spool_type': template.get('spool_type'),
        }

        return repo.create_with_specs(equipment_data, spec_data)

    def _create_line(
        self,
        session,
        repo: EquipmentRepository,
        brand_name: str,
        template: Dict[str, Any],
        variant: Dict[str, Any]
    ) -> Equipment:
        """创建单个鱼线"""
        model = variant['model']
        product_line = template['product_line']

        price_min = variant.get('price_min') or template.get('price_min')
        price_max = variant.get('price_max') or template.get('price_max')

        equipment_data = {
            'name': self._generate_equipment_name(brand_name, product_line, model),
            'category': '鱼线',
            'brand_id': template['brand_id'],
            'model': model,
            'price_min': price_min,
            'price_max': price_max,
                        'description': template.get('description'),
            'features': template.get('features'),
            'user_level': template.get('user_level', '进阶'),
            'is_active': True,
            'source': 'batch_import',
        }

        spec_data = {
            'line_type': template.get('line_type'),
            'diameter': variant.get('diameter'),
            'breaking_strength': variant.get('breaking_strength'),
            'length': variant.get('length'),
            'material': template.get('material'),
        }

        return repo.create_with_specs(equipment_data, spec_data)

    def _create_lure(
        self,
        session,
        repo: EquipmentRepository,
        brand_name: str,
        template: Dict[str, Any],
        variant: Dict[str, Any]
    ) -> Equipment:
        """创建单个拟饵"""
        model = variant['model']
        product_line = template['product_line']

        price_min = variant.get('price_min') or template.get('price_min')
        price_max = variant.get('price_max') or template.get('price_max')

        equipment_data = {
            'name': self._generate_equipment_name(brand_name, product_line, model),
            'category': '拟饵',
            'brand_id': template['brand_id'],
            'model': model,
            'price_min': price_min,
            'price_max': price_max,
                        'description': template.get('description'),
            'features': template.get('features'),
            'user_level': template.get('user_level', '进阶'),
            'is_active': True,
            'source': 'batch_import',
        }

        spec_data = {
            'lure_type': template.get('lure_type'),
            'weight': variant.get('weight'),
            'length': variant.get('length'),
            'diving_depth': variant.get('diving_depth'),
            'action_type': template.get('action_type'),
        }

        return repo.create_with_specs(equipment_data, spec_data)

    def _build_rod_features(
        self,
        template: Dict[str, Any],
        variant: Dict[str, Any]
    ) -> str:
        """构建鱼竿特点描述"""
        features = []

        if template.get('sections'):
            features.append(f"{template['sections']}节设计")

        if template.get('guide_type'):
            features.append(template['guide_type'])

        if template.get('handle_type'):
            features.append(template['handle_type'])

        if template.get('material'):
            features.append(template['material'])

        if template.get('features'):
            features.append(template['features'])

        return ', '.join(features) if features else ''

    def _summarize_results(
        self,
        results: List[CreateResult]
    ) -> BatchEquipmentCreateResponse:
        """汇总创建结果"""
        success_count = 0
        skip_count = 0
        error_count = 0
        created_ids = []
        skipped_models = []
        errors = []

        for result in results:
            if result.skipped:
                skip_count += 1
                skipped_models.append(result.model)
            elif result.success:
                success_count += 1
                if result.equipment_id:
                    created_ids.append(result.equipment_id)
            else:
                error_count += 1
                errors.append({
                    "model": result.model,
                    "error": result.error
                })

        return BatchEquipmentCreateResponse(
            success_count=success_count,
            skip_count=skip_count,
            error_count=error_count,
            created_ids=created_ids,
            skipped_models=skipped_models,
            errors=errors
        )


# 单例服务实例
batch_equipment_service = BatchEquipmentService()
