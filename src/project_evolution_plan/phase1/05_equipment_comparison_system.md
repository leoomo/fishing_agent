# 装备对比分析系统开发指南

## 📋 模块概述

### 🎯 系统定位
装备对比分析系统是智能钓鱼生态系统的核心分析工具，专注于为用户提供专业、客观、详细的装备对比分析服务。该系统基于多维度的装备参数、性能数据、用户评价等信息，通过智能算法进行深度分析，帮助用户做出最优的装备选择决策。

### 🔍 核心价值主张
- **专业对比**: 基于技术规格和性能数据的客观对比分析
- **多维评估**: 从性能、价格、品牌、用户口碑等多个维度综合评估
- **决策支持**: 提供数据驱动的购买建议和升级指导
- **价值分析**: 深度分析装备的性价比和长期价值

### 🏗️ 系统依赖
- **基础设施层**: 共享数据库管理、缓存系统、配置管理
- **装备推荐系统**: 提供装备基础信息和推荐数据
- **外部数据源**: 装备规格数据、价格信息、用户评价等

## 🎯 领域模型设计

### 核心实体模型

#### 1. 对比分析实体 (ComparisonAnalysis)
```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime

class ComparisonType(Enum):
    """对比类型枚举"""
    HEAD_TO_HEAD = "head_to_head"              # 正面对比
    MULTI_COMPARISON = "multi_comparison"       # 多装备对比
    CATEGORY_ANALYSIS = "category_analysis"    # 类别分析
    PRICE_RANGE = "price_range"                # 价格区间对比
    BRAND_COMPARISON = "brand_comparison"      # 品牌对比

class AnalysisDimension(Enum):
    """分析维度枚举"""
    PERFORMANCE = "performance"                # 性能维度
    PRICE = "price"                          # 价格维度
    USABILITY = "usability"                   # 易用性维度
    DURABILITY = "durability"                 # 耐用性维度
    BRAND_VALUE = "brand_value"              # 品牌价值维度
    USER_SATISFACTION = "user_satisfaction"   # 用户满意度维度

@dataclass
class ComparisonMetric:
    """对比指标"""
    name: str                                # 指标名称
    category: AnalysisDimension              # 指标类别
    weight: float                           # 权重 (0-1)
    unit: Optional[str] = None              # 单位
    description: str = ""                   # 描述
    higher_is_better: bool = True           # 数值越大越好

@dataclass
class EquipmentComparison:
    """装备对比数据"""
    equipment_id: str                       # 装备ID
    metrics: Dict[str, float]               # 指标数值
    normalized_scores: Dict[str, float]     # 标准化评分
    strengths: List[str]                    # 优势项目
    weaknesses: List[str]                   # 劣势项目
    overall_score: float                    # 综合评分

@dataclass
class ComparisonResult:
    """对比结果"""
    comparison_id: str                      # 对比ID
    comparison_type: ComparisonType         # 对比类型
    equipment_comparisons: List[EquipmentComparison]  # 装备对比数据
    dimension_scores: Dict[AnalysisDimension, Dict[str, float]]  # 维度评分
    ranking: List[Tuple[str, float]]        # 排名结果
    recommendation: str                     # 推荐建议
    key_differences: List[Dict[str, Any]]   # 关键差异
    value_analysis: Dict[str, Any]          # 价值分析
    generated_at: datetime = field(default_factory=datetime.now)
```

#### 2. 性能评分模型 (PerformanceScore)
```python
@dataclass
class PerformanceBenchmark:
    """性能基准"""
    category: str                           # 装备类别
    level: str                             # 性能等级
    min_score: float                       # 最低分
    max_score: float                       # 最高分
    description: str                       # 描述

@dataclass
class DetailedPerformanceScore:
    """详细性能评分"""
    overall_score: float                    # 综合评分
    dimension_scores: Dict[AnalysisDimension, float]  # 维度评分
    sub_metrics: Dict[str, float]          # 子指标评分
    benchmark_comparison: Dict[str, str]   # 基准对比
    confidence_level: float                # 置信度
    last_updated: datetime = field(default_factory=datetime.now)

class PerformanceScorer:
    """性能评分器"""

    def __init__(self):
        self.benchmarks = self._initialize_benchmarks()
        self.scoring_weights = self._initialize_scoring_weights()
        self.normalization_methods = self._initialize_normalization_methods()

    def score_equipment(self, equipment: 'Equipment') -> DetailedPerformanceScore:
        """对装备进行性能评分"""
        try:
            # 提取装备指标
            raw_metrics = self._extract_metrics(equipment)

            # 标准化指标
            normalized_metrics = self._normalize_metrics(raw_metrics, equipment.spec.category)

            # 计算维度评分
            dimension_scores = self._calculate_dimension_scores(normalized_metrics)

            # 计算综合评分
            overall_score = self._calculate_overall_score(dimension_scores)

            # 基准对比
            benchmark_comparison = self._compare_to_benchmarks(
                overall_score, equipment.spec.category, equipment.spec.level
            )

            return DetailedPerformanceScore(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                sub_metrics=normalized_metrics,
                benchmark_comparison=benchmark_comparison,
                confidence_level=self._calculate_confidence_level(equipment)
            )

        except Exception as e:
            logger.error(f"装备性能评分失败: {e}")
            return DetailedPerformanceScore(
                overall_score=50.0,
                dimension_scores={},
                sub_metrics={},
                benchmark_comparison={},
                confidence_level=0.0
            )

    def _extract_metrics(self, equipment: 'Equipment') -> Dict[str, float]:
        """提取装备指标"""
        metrics = {}

        # 基础性能指标
        metrics['performance_score'] = equipment.performance_score
        metrics['popularity_score'] = equipment.popularity_score
        metrics['user_rating'] = equipment.user_rating * 20  # 转换为100分制

        # 价格相关指标
        avg_price = self._get_category_average_price(equipment.spec.category)
        metrics['price competitiveness'] = 1 - (equipment.spec.price / avg_price - 1) * 0.5
        metrics['price competitiveness'] = max(0, min(100, metrics['price competitiveness'] * 100))

        # 评价数量指标
        metrics['review_confidence'] = min(100, equipment.review_count / 10)  # 每10个评价加1分，最高100分

        # 从规格参数中提取具体指标
        specs = equipment.spec.specifications
        category = equipment.spec.category

        if category == EquipmentCategory.FISHING_ROD:
            metrics.update(self._extract_rod_metrics(specs))
        elif category == EquipmentCategory.FISHING_REEL:
            metrics.update(self._extract_reel_metrics(specs))
        elif category == EquipmentCategory.FISHING_LINE:
            metrics.update(self._extract_line_metrics(specs))
        elif category == EquipmentCategory.FISHING_LURE:
            metrics.update(self._extract_lure_metrics(specs))

        return metrics

    def _extract_rod_metrics(self, specs: Dict[str, Any]) -> Dict[str, float]:
        """提取鱼竿指标"""
        metrics = {}

        # 调性评分
        if 'action' in specs:
            action_scores = {
                'ultralight': 30, 'light': 50, 'medium_light': 70,
                'medium': 85, 'medium_heavy': 90, 'heavy': 75, 'extra_heavy': 60
            }
            metrics['action_score'] = action_scores.get(specs['action'].lower(), 50)

        # 长度评分
        if 'length' in specs:
            length = specs['length']
            # 理想长度范围2.1-2.7米
            if 210 <= length <= 270:
                metrics['length_score'] = 100
            elif 180 <= length < 210 or 270 < length <= 300:
                metrics['length_score'] = 85
            else:
                metrics['length_score'] = 70

        # 材质评分
        if 'material' in specs:
            material_scores = {
                'carbon': 95, 'carbon_fiber': 95, 'glass': 60, 'composite': 75,
                'bamboo': 40, 'fiberglass': 55
            }
            material = specs['material'].lower()
            metrics['material_score'] = max(30, material_scores.get(material, 50))

        # 重量评分
        if 'weight' in specs:
            weight = specs['weight']
            # 轻量化评分，越轻越好
            metrics['weight_score'] = max(30, 100 - (weight - 50) * 0.5)

        return metrics

    def _extract_reel_metrics(self, specs: Dict[str, Any]) -> Dict[str, float]:
        """提取鱼轮指标"""
        metrics = {}

        # 轴承数量评分
        if 'bearings' in specs:
            bearings = specs['bearings']
            if bearings >= 10:
                metrics['bearing_score'] = 100
            elif bearings >= 7:
                metrics['bearing_score'] = 85
            elif bearings >= 4:
                metrics['bearing_score'] = 70
            else:
                metrics['bearing_score'] = 50

        # 线容量评分
        if 'line_capacity' in specs:
            # 根据线容量范围评分
            metrics['capacity_score'] = 80  # 简化评分

        # 材质评分
        if 'body_material' in specs:
            material_scores = {
                'aluminum': 85, 'carbon': 95, 'graphite': 90,
                'plastic': 50, 'metal': 75, 'titanium': 100
            }
            material = specs['body_material'].lower()
            metrics['body_material_score'] = max(40, material_scores.get(material, 60))

        # 齿轮比评分
        if 'gear_ratio' in specs:
            gear_ratio = specs['gear_ratio']
            # 理想齿轮比范围5.0-6.0
            if 5.0 <= gear_ratio <= 6.0:
                metrics['gear_ratio_score'] = 100
            elif 4.5 <= gear_ratio < 5.0 or 6.0 < gear_ratio <= 7.0:
                metrics['gear_ratio_score'] = 85
            else:
                metrics['gear_ratio_score'] = 70

        return metrics

    def _extract_line_metrics(self, specs: Dict[str, Any]) -> Dict[str, float]:
        """提取鱼线指标"""
        metrics = {}

        # 强度评分
        if 'strength' in specs:
            strength = specs['strength']
            # 根据强度范围评分
            metrics['strength_score'] = min(100, strength / 10)  # 简化评分

        # 直径评分
        if 'diameter' in specs:
            diameter = specs['diameter']
            # 线径评分，越细越好（在同等强度下）
            metrics['diameter_score'] = max(50, 100 - (diameter - 0.2) * 100)

        # 材质评分
        if 'material' in specs:
            material_scores = {
                'pe': 95, 'nylon': 75, 'fluorocarbon': 85,
                'braided': 90, 'mono': 70, 'copolymer': 80
            }
            material = specs['material'].lower()
            metrics['material_score'] = max(50, material_scores.get(material, 60))

        return metrics

    def _extract_lure_metrics(self, specs: Dict[str, Any]) -> Dict[str, float]:
        """提取拟饵指标"""
        metrics = {}

        # 重量评分
        if 'weight' in specs:
            weight = specs['weight']
            # 根据重量范围评分
            if 3 <= weight <= 15:  # 理想重量范围
                metrics['weight_score'] = 100
            elif 1 <= weight < 3 or 15 < weight <= 25:
                metrics['weight_score'] = 80
            else:
                metrics['weight_score'] = 60

        # 类型评分
        if 'type' in specs:
            type_scores = {
                'minnow': 90, 'crankbait': 85, 'spinnerbait': 80,
                'jig': 85, 'soft_plastic': 75, 'topwater': 90,
                'vibrating': 80, 'spoon': 70
            }
            lure_type = specs['type'].lower()
            metrics['type_score'] = type_scores.get(lure_type, 70)

        return metrics

    def _normalize_metrics(self, metrics: Dict[str, float], category: str) -> Dict[str, float]:
        """标准化指标"""
        normalized = {}

        for metric_name, value in metrics.items():
            if metric_name in self.normalization_methods[category]:
                method = self.normalization_methods[category][metric_name]
                normalized[metric_name] = self._apply_normalization(value, method)
            else:
                # 默认标准化方法
                normalized[metric_name] = max(0, min(100, value))

        return normalized

    def _apply_normalization(self, value: float, method: Dict[str, Any]) -> float:
        """应用标准化方法"""
        normalization_type = method.get('type', 'linear')

        if normalization_type == 'linear':
            min_val = method.get('min', 0)
            max_val = method.get('max', 100)
            return ((value - min_val) / (max_val - min_val)) * 100
        elif normalization_type == 'logarithmic':
            return min(100, math.log(value + 1) * method.get('scale', 20))
        elif normalization_type == 'inverse':
            optimal = method.get('optimal', 50)
            deviation = abs(value - optimal)
            max_deviation = method.get('max_deviation', 50)
            return max(0, 100 - (deviation / max_deviation) * 100)

        return max(0, min(100, value))

    def _calculate_dimension_scores(self, metrics: Dict[str, float]) -> Dict[AnalysisDimension, float]:
        """计算维度评分"""
        dimension_scores = {}

        for dimension, weight in self.scoring_weights.items():
            # 获取该维度相关的指标
            dimension_metrics = self._get_dimension_metrics(dimension)

            if dimension_metrics:
                # 计算维度平均分
                relevant_scores = [
                    metrics[metric] for metric in dimension_metrics
                    if metric in metrics
                ]

                if relevant_scores:
                    dimension_scores[dimension] = sum(relevant_scores) / len(relevant_scores)
                else:
                    dimension_scores[dimension] = 50.0  # 默认分数
            else:
                dimension_scores[dimension] = 50.0

        return dimension_scores

    def _get_dimension_metrics(self, dimension: AnalysisDimension) -> List[str]:
        """获取维度相关指标"""
        dimension_mapping = {
            AnalysisDimension.PERFORMANCE: ['performance_score', 'action_score', 'bearing_score', 'strength_score'],
            AnalysisDimension.PRICE: ['price competitiveness'],
            AnalysisDimension.USABILITY: ['length_score', 'weight_score', 'gear_ratio_score'],
            AnalysisDimension.DURABILITY: ['material_score', 'body_material_score'],
            AnalysisDimension.BRAND_VALUE: ['popularity_score'],
            AnalysisDimension.USER_SATISFACTION: ['user_rating', 'review_confidence']
        }
        return dimension_mapping.get(dimension, [])

    def _calculate_overall_score(self, dimension_scores: Dict[AnalysisDimension, float]) -> float:
        """计算综合评分"""
        total_score = 0.0
        total_weight = 0.0

        for dimension, score in dimension_scores.items():
            weight = self.scoring_weights.get(dimension, 0.1)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 50.0

    def _compare_to_benchmarks(self, score: float, category: str, level: str) -> Dict[str, str]:
        """与基准对比"""
        benchmarks = self.benchmarks.get(category, [])

        for benchmark in benchmarks:
            if benchmark.level.lower() == level.lower():
                if score >= benchmark.max_score:
                    return {'level': 'excellent', 'description': '超越同级产品'}
                elif score >= (benchmark.min_score + benchmark.max_score) / 2:
                    return {'level': 'good', 'description': '优于同级产品'}
                elif score >= benchmark.min_score:
                    return {'level': 'average', 'description': '符合同级标准'}
                else:
                    return {'level': 'below_average', 'description': '低于同级标准'}

        return {'level': 'unknown', 'description': '无法进行基准对比'}

    def _calculate_confidence_level(self, equipment: 'Equipment') -> float:
        """计算置信度"""
        confidence_factors = []

        # 评价数量因子
        review_confidence = min(1.0, equipment.review_count / 100)
        confidence_factors.append(review_confidence)

        # 数据完整性因子
        spec_completeness = len(equipment.spec.specifications) / 10  # 假设10个关键规格
        confidence_factors.append(min(1.0, spec_completeness))

        # 用户评分一致性因子
        if equipment.user_rating > 0:
            # 简化的一致性计算
            rating_consistency = 0.8
        else:
            rating_consistency = 0.3
        confidence_factors.append(rating_consistency)

        return sum(confidence_factors) / len(confidence_factors)

    def _initialize_benchmarks(self) -> Dict[str, List[PerformanceBenchmark]]:
        """初始化性能基准"""
        return {
            'fishing_rod': [
                PerformanceBenchmark('fishing_rod', 'beginner', 60, 75, '入门级鱼竿'),
                PerformanceBenchmark('fishing_rod', 'intermediate', 75, 85, '进阶级鱼竿'),
                PerformanceBenchmark('fishing_rod', 'advanced', 85, 92, '高级鱼竿'),
                PerformanceBenchmark('fishing_rod', 'professional', 92, 98, '专业级鱼竿'),
            ],
            'fishing_reel': [
                PerformanceBenchmark('fishing_reel', 'beginner', 65, 78, '入门级鱼轮'),
                PerformanceBenchmark('fishing_reel', 'intermediate', 78, 88, '进阶级鱼轮'),
                PerformanceBenchmark('fishing_reel', 'advanced', 88, 94, '高级鱼轮'),
                PerformanceBenchmark('fishing_reel', 'professional', 94, 99, '专业级鱼轮'),
            ],
            # 其他类别基准...
        }

    def _initialize_scoring_weights(self) -> Dict[AnalysisDimension, float]:
        """初始化评分权重"""
        return {
            AnalysisDimension.PERFORMANCE: 0.30,
            AnalysisDimension.PRICE: 0.20,
            AnalysisDimension.USABILITY: 0.15,
            AnalysisDimension.DURABILITY: 0.15,
            AnalysisDimension.BRAND_VALUE: 0.10,
            AnalysisDimension.USER_SATISFACTION: 0.10
        }

    def _initialize_normalization_methods(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """初始化标准化方法"""
        return {
            'fishing_rod': {
                'action_score': {'type': 'linear', 'min': 0, 'max': 100},
                'length_score': {'type': 'linear', 'min': 0, 'max': 100},
                'material_score': {'type': 'linear', 'min': 0, 'max': 100},
                'weight_score': {'type': 'linear', 'min': 0, 'max': 100},
            },
            'fishing_reel': {
                'bearing_score': {'type': 'linear', 'min': 0, 'max': 100},
                'capacity_score': {'type': 'linear', 'min': 0, 'max': 100},
                'body_material_score': {'type': 'linear', 'min': 0, 'max': 100},
                'gear_ratio_score': {'type': 'linear', 'min': 0, 'max': 100},
            },
            # 其他类别标准化方法...
        }

    def _get_category_average_price(self, category: str) -> float:
        """获取类别平均价格"""
        price_ranges = {
            'fishing_rod': 500,
            'fishing_reel': 400,
            'fishing_line': 50,
            'fishing_lure': 30,
            'fishing_hook': 20,
            'accessories': 100
        }
        return price_ranges.get(category, 200)
```

## 🔧 服务层实现

### 对比分析引擎 (ComparisonEngine)
```python
class ComparisonEngine:
    """对比分析引擎"""

    def __init__(self, equipment_repository: 'EquipmentRepository',
                 performance_scorer: PerformanceScorer,
                 spec_analyzer: 'SpecificationAnalyzer',
                 upgrade_advisor: 'UpgradeAdvisor'):
        self.equipment_repository = equipment_repository
        self.performance_scorer = performance_scorer
        self.spec_analyzer = spec_analyzer
        self.upgrade_advisor = upgrade_advisor
        self.comparison_cache = ComparisonCache()

    def compare_equipment(self, equipment_ids: List[str],
                         comparison_type: ComparisonType = ComparisonType.HEAD_TO_HEAD) -> ComparisonResult:
        """对比装备"""
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(equipment_ids, comparison_type)
            cached_result = self.comparison_cache.get(cache_key)
            if cached_result:
                return cached_result

            # 获取装备信息
            equipments = []
            for equipment_id in equipment_ids:
                equipment = self.equipment_repository.find_by_id(equipment_id)
                if equipment:
                    equipments.append(equipment)
                else:
                    raise ValueError(f"装备 {equipment_id} 不存在")

            if len(equipments) < 2:
                raise ValueError("至少需要2个装备进行对比")

            # 生成对比ID
            comparison_id = self._generate_comparison_id(equipment_ids)

            # 计算性能评分
            equipment_comparisons = []
            for equipment in equipments:
                performance_score = self.performance_scorer.score_equipment(equipment)
                comparison_data = self._create_equipment_comparison(equipment, performance_score)
                equipment_comparisons.append(comparison_data)

            # 分析维度评分
            dimension_scores = self._analyze_dimension_scores(equipment_comparisons)

            # 生成排名
            ranking = self._generate_ranking(equipment_comparisons)

            # 分析关键差异
            key_differences = self._analyze_key_differences(equipments, equipment_comparisons)

            # 价值分析
            value_analysis = self._analyze_value(equipment_comparisons)

            # 生成推荐建议
            recommendation = self._generate_recommendation(
                equipment_comparisons, dimension_scores, comparison_type
            )

            # 创建对比结果
            result = ComparisonResult(
                comparison_id=comparison_id,
                comparison_type=comparison_type,
                equipment_comparisons=equipment_comparisons,
                dimension_scores=dimension_scores,
                ranking=ranking,
                recommendation=recommendation,
                key_differences=key_differences,
                value_analysis=value_analysis
            )

            # 缓存结果
            self.comparison_cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"装备对比分析失败: {e}")
            raise ComparisonError(f"无法完成装备对比: {e}")

    def compare_multiple_equipment(self, category: str,
                                 filters: Dict[str, Any] = None,
                                 limit: int = 10) -> ComparisonResult:
        """对比多款装备"""
        try:
            # 获取装备列表
            if filters:
                equipments = self.equipment_repository.search_equipment("", filters)
            else:
                equipments = self.equipment_repository.find_by_category(EquipmentCategory(category))

            # 限制数量
            equipments = equipments[:limit]

            if len(equipments) < 2:
                raise ValueError("找到的装备数量不足")

            equipment_ids = [equipment.id for equipment in equipments]
            return self.compare_equipment(
                equipment_ids, ComparisonType.MULTI_COMPARISON
            )

        except Exception as e:
            logger.error(f"多装备对比失败: {e}")
            raise ComparisonError(f"无法进行多装备对比: {e}")

    def analyze_upgrade_value(self, current_equipment_id: str,
                            target_equipment_id: str) -> Dict[str, Any]:
        """分析升级价值"""
        try:
            current_equipment = self.equipment_repository.find_by_id(current_equipment_id)
            target_equipment = self.equipment_repository.find_by_id(target_equipment_id)

            if not current_equipment or not target_equipment:
                raise ValueError("装备不存在")

            # 计算性能提升
            current_score = self.performance_scorer.score_equipment(current_equipment)
            target_score = self.performance_scorer.score_equipment(target_equipment)

            performance_improvement = target_score.overall_score - current_score.overall_score

            # 分析规格差异
            spec_differences = self.spec_analyzer.compare_specifications(
                current_equipment.spec, target_equipment.spec
            )

            # 计算性价比
            price_difference = target_equipment.spec.price - current_equipment.spec.price
            value_ratio = performance_improvement / (price_difference / 100) if price_difference > 0 else float('inf')

            # 生成升级建议
            upgrade_recommendation = self.upgrade_advisor.analyze_upgrade(
                current_equipment, target_equipment, performance_improvement, price_difference
            )

            return {
                'current_equipment': {
                    'id': current_equipment.id,
                    'name': f"{current_equipment.spec.brand} {current_equipment.spec.model}",
                    'overall_score': current_score.overall_score
                },
                'target_equipment': {
                    'id': target_equipment.id,
                    'name': f"{target_equipment.spec.brand} {target_equipment.spec.model}",
                    'overall_score': target_score.overall_score
                },
                'performance_improvement': performance_improvement,
                'price_difference': price_difference,
                'value_ratio': value_ratio,
                'spec_differences': spec_differences,
                'upgrade_recommendation': upgrade_recommendation,
                'is_recommended': performance_improvement > 10 and value_ratio > 0.5
            }

        except Exception as e:
            logger.error(f"升级价值分析失败: {e}")
            raise ComparisonError(f"无法分析升级价值: {e}")

    def _create_equipment_comparison(self, equipment: 'Equipment',
                                   performance_score: DetailedPerformanceScore) -> EquipmentComparison:
        """创建装备对比数据"""
        # 提取指标
        metrics = self.performance_scorer._extract_metrics(equipment)

        # 识别优势和劣势
        strengths, weaknesses = self._identify_strengths_weaknesses(
            metrics, performance_score.dimension_scores
        )

        return EquipmentComparison(
            equipment_id=equipment.id,
            metrics=metrics,
            normalized_scores=performance_score.sub_metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            overall_score=performance_score.overall_score
        )

    def _identify_strengths_weaknesses(self, metrics: Dict[str, float],
                                     dimension_scores: Dict[AnalysisDimension, float]) -> Tuple[List[str], List[str]]:
        """识别优势和劣势"""
        strengths = []
        weaknesses = []

        # 基于维度评分识别
        for dimension, score in dimension_scores.items():
            if score >= 85:
                strengths.append(f"{dimension.value}表现出色 (评分: {score:.1f})")
            elif score <= 60:
                weaknesses.append(f"{dimension.value}有待改进 (评分: {score:.1f})")

        # 基于具体指标识别
        for metric, value in metrics.items():
            if value >= 90:
                strengths.append(f"{metric}指标优秀 (数值: {value:.1f})")
            elif value <= 40:
                weaknesses.append(f"{metric}指标较低 (数值: {value:.1f})")

        return strengths[:3], weaknesses[:3]  # 最多返回3个

    def _analyze_dimension_scores(self, equipment_comparisons: List[EquipmentComparison]) -> Dict[AnalysisDimension, Dict[str, float]]:
        """分析维度评分"""
        dimension_scores = {}

        # 收集所有维度
        all_dimensions = set()
        for comparison in equipment_comparisons:
            # 这里需要从metrics中反推维度，简化处理
            for metric_name in comparison.metrics.keys():
                dimension = self._map_metric_to_dimension(metric_name)
                if dimension:
                    all_dimensions.add(dimension)

        # 为每个维度计算评分
        for dimension in all_dimensions:
            dimension_scores[dimension] = {}
            for comparison in equipment_comparisons:
                score = self._calculate_dimension_score_for_equipment(comparison, dimension)
                dimension_scores[dimension][comparison.equipment_id] = score

        return dimension_scores

    def _map_metric_to_dimension(self, metric_name: str) -> Optional[AnalysisDimension]:
        """将指标映射到维度"""
        metric_mapping = {
            'performance_score': AnalysisDimension.PERFORMANCE,
            'price competitiveness': AnalysisDimension.PRICE,
            'user_rating': AnalysisDimension.USER_SATISFACTION,
            'popularity_score': AnalysisDimension.BRAND_VALUE,
            'material_score': AnalysisDimension.DURABILITY,
            'action_score': AnalysisDimension.PERFORMANCE,
            'bearing_score': AnalysisDimension.PERFORMANCE,
            'weight_score': AnalysisDimension.USABILITY,
        }
        return metric_mapping.get(metric_name)

    def _calculate_dimension_score_for_equipment(self, comparison: EquipmentComparison,
                                               dimension: AnalysisDimension) -> float:
        """计算装备的特定维度评分"""
        # 获取该维度相关的指标
        dimension_metrics = self.performance_scorer._get_dimension_metrics(dimension)

        relevant_scores = []
        for metric in dimension_metrics:
            if metric in comparison.normalized_scores:
                relevant_scores.append(comparison.normalized_scores[metric])

        if relevant_scores:
            return sum(relevant_scores) / len(relevant_scores)
        else:
            return 50.0  # 默认分数

    def _generate_ranking(self, equipment_comparisons: List[EquipmentComparison]) -> List[Tuple[str, float]]:
        """生成排名"""
        sorted_comparisons = sorted(
            equipment_comparisons,
            key=lambda x: x.overall_score,
            reverse=True
        )

        return [(comp.equipment_id, comp.overall_score) for comp in sorted_comparisons]

    def _analyze_key_differences(self, equipments: List['Equipment'],
                               equipment_comparisons: List[EquipmentComparison]) -> List[Dict[str, Any]]:
        """分析关键差异"""
        key_differences = []

        if len(equipments) != 2:
            return key_differences

        eq1, eq2 = equipments[0], equipments[1]
        comp1, comp2 = equipment_comparisons[0], equipment_comparisons[1]

        # 价格差异
        price_diff = abs(eq1.spec.price - eq2.spec.price)
        if price_diff > 100:  # 价格差异超过100元
            key_differences.append({
                'type': 'price',
                'description': f"价格差异 {price_diff:.0f} 元",
                'impact': 'high' if price_diff > 500 else 'medium'
            })

        # 性能差异
        performance_diff = abs(comp1.overall_score - comp2.overall_score)
        if performance_diff > 10:  # 性能差异超过10分
            key_differences.append({
                'type': 'performance',
                'description': f"性能评分差异 {performance_diff:.1f} 分",
                'impact': 'high' if performance_diff > 20 else 'medium'
            })

        # 品牌差异
        if eq1.spec.brand != eq2.spec.brand:
            key_differences.append({
                'type': 'brand',
                'description': f"品牌差异：{eq1.spec.brand} vs {eq2.spec.brand}",
                'impact': 'medium'
            })

        # 规格差异
        spec_diffs = self.spec_analyzer.identify_key_spec_differences(
            eq1.spec.specifications, eq2.spec.specifications
        )
        for diff in spec_diffs[:3]:  # 最多显示3个关键规格差异
            key_differences.append({
                'type': 'specification',
                'description': diff,
                'impact': 'medium'
            })

        return key_differences

    def _analyze_value(self, equipment_comparisons: List[EquipmentComparison]) -> Dict[str, Any]:
        """分析价值"""
        total_scores = [comp.overall_score for comp in equipment_comparisons]
        avg_score = sum(total_scores) / len(total_scores)

        # 价值等级分析
        value_analysis = {}
        for comp in equipment_comparisons:
            equipment = self.equipment_repository.find_by_id(comp.equipment_id)
            if equipment:
                price = equipment.spec.price
                value_score = comp.overall_score / (price / 100)  # 每100元的性能评分

                value_analysis[comp.equipment_id] = {
                    'value_score': value_score,
                    'value_rank': 'high' if value_score > avg_score / (price / 100) * 1.2 else 'medium' if value_score > avg_score / (price / 100) * 0.8 else 'low',
                    'price_performance_ratio': f"{value_score:.2f}"
                }

        return {
            'individual_values': value_analysis,
            'best_value_equipment': max(value_analysis.keys(), key=lambda k: value_analysis[k]['value_score']),
            'value_range': {
                'min': min(v['value_score'] for v in value_analysis.values()),
                'max': max(v['value_score'] for v in value_analysis.values()),
                'average': sum(v['value_score'] for v in value_analysis.values()) / len(value_analysis)
            }
        }

    def _generate_recommendation(self, equipment_comparisons: List[EquipmentComparison],
                               dimension_scores: Dict[AnalysisDimension, Dict[str, float]],
                               comparison_type: ComparisonType) -> str:
        """生成推荐建议"""
        if not equipment_comparisons:
            return "无法生成推荐建议"

        # 找出最佳装备
        best_comparison = max(equipment_comparisons, key=lambda x: x.overall_score)
        best_equipment = self.equipment_repository.find_by_id(best_comparison.equipment_id)

        if not best_equipment:
            return "无法获取装备信息"

        # 分析推荐理由
        reasons = []

        # 综合性能优势
        if best_comparison.overall_score >= 90:
            reasons.append("综合性能表现卓越")
        elif best_comparison.overall_score >= 80:
            reasons.append("综合性能表现优秀")

        # 优势项目
        if best_comparison.strengths:
            reasons.append(f"在 {best_comparison.strengths[0].split('(')[0].strip()} 方面表现突出")

        # 性价比优势
        value_scores = [comp.overall_score / (self.equipment_repository.find_by_id(comp.equipment_id).spec.price / 100)
                       for comp in equipment_comparisons
                       if self.equipment_repository.find_by_id(comp.equipment_id)]

        if value_scores:
            best_value = max(value_scores)
            current_value = best_comparison.overall_score / (best_equipment.spec.price / 100)
            if current_value >= best_value * 0.95:
                reasons.append("具有良好的性价比")

        # 生成推荐文本
        recommendation = f"推荐选择 {best_equipment.spec.brand} {best_equipment.spec.model}"

        if reasons:
            recommendation += f"，因为{'，'.join(reasons[:2])}"  # 最多2个理由

        # 根据对比类型添加特定建议
        if comparison_type == ComparisonType.HEAD_TO_HEAD:
            recommendation += "。在直接对比中，这款装备展现出明显优势。"
        elif comparison_type == ComparisonType.MULTI_COMPARISON:
            recommendation += f"。在 {len(equipment_comparisons)} 款装备中脱颖而出。"

        return recommendation

    def _generate_cache_key(self, equipment_ids: List[str], comparison_type: ComparisonType) -> str:
        """生成缓存键"""
        sorted_ids = sorted(equipment_ids)
        return f"comparison:{'_'.join(sorted_ids)}:{comparison_type.value}"

    def _generate_comparison_id(self, equipment_ids: List[str]) -> str:
        """生成对比ID"""
        sorted_ids = sorted(equipment_ids)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"cmp_{timestamp}_{'_'.join(sorted_ids[:3])}"  # 最多3个ID

class ComparisonError(Exception):
    """对比分析异常"""
    pass
```

### 规格分析器 (SpecificationAnalyzer)
```python
class SpecificationAnalyzer:
    """规格分析器"""

    def __init__(self):
        self.comparison_rules = self._initialize_comparison_rules()
        self.spec_weights = self._initialize_spec_weights()

    def compare_specifications(self, spec1: EquipmentSpec, spec2: EquipmentSpec) -> Dict[str, Any]:
        """对比两个装备的规格"""
        if spec1.category != spec2.category:
            raise ValueError("只能对比同类别装备的规格")

        comparison_result = {
            'category': spec1.category.value,
            'differences': [],
            'similarities': [],
            'winner_metrics': {},
            'overall_similarity': 0.0
        }

        # 获取该类别的对比规则
        rules = self.comparison_rules.get(spec1.category.value, {})

        # 对比关键规格
        all_specs = set(spec1.specifications.keys()) | set(spec2.specifications.keys())

        similarity_scores = []

        for spec_key in all_specs:
            if spec_key in rules:
                spec_comparison = self._compare_spec_value(
                    spec_key,
                    spec1.specifications.get(spec_key),
                    spec2.specifications.get(spec_key),
                    rules[spec_key]
                )

                comparison_result['differences'].append(spec_comparison)

                if spec_comparison['similarity'] > 0.8:
                    comparison_result['similarities'].append(spec_key)

                if spec_comparison.get('winner'):
                    comparison_result['winner_metrics'][spec_key] = spec_comparison['winner']

                similarity_scores.append(spec_comparison['similarity'])

        # 计算总体相似度
        if similarity_scores:
            comparison_result['overall_similarity'] = sum(similarity_scores) / len(similarity_scores)

        # 添加基础信息对比
        comparison_result['basic_info'] = {
            'brand_comparison': self._compare_brands(spec1.brand, spec2.brand),
            'level_comparison': self._compare_levels(spec1.level, spec2.level),
            'price_difference': abs(spec1.price - spec2.price),
            'weight_difference': abs((spec1.weight or 0) - (spec2.weight or 0))
        }

        return comparison_result

    def identify_key_spec_differences(self, specs1: Dict[str, Any],
                                    specs2: Dict[str, Any]) -> List[str]:
        """识别关键规格差异"""
        differences = []

        # 定义关键规格
        key_specs = [
            'length', 'weight', 'material', 'action',  # 鱼竿
            'bearings', 'gear_ratio', 'line_capacity',  # 鱼轮
            'strength', 'diameter', 'material',         # 鱼线
            'weight', 'type', 'diving_depth'            # 拟饵
        ]

        for spec in key_specs:
            if spec in specs1 and spec in specs2:
                value1, value2 = specs1[spec], specs2[spec]
                if not self._are_spec_values_similar(spec, value1, value2):
                    differences.append(f"{spec}: {value1} vs {value2}")
            elif spec in specs1 or spec in specs2:
                value = specs1.get(spec, specs2.get(spec, 'N/A'))
                differences.append(f"{spec}: {value} vs N/A")

        return differences[:5]  # 最多返回5个关键差异

    def _compare_spec_value(self, spec_name: str, value1: Any, value2: Any,
                          rule: Dict[str, Any]) -> Dict[str, Any]:
        """对比规格值"""
        comparison = {
            'spec_name': spec_name,
            'value1': value1,
            'value2': value2,
            'similarity': 0.0,
            'significance': rule.get('significance', 'medium'),
            'description': ''
        }

        if value1 is None or value2 is None:
            comparison['similarity'] = 0.0
            comparison['description'] = "其中一个装备缺少此规格信息"
            return comparison

        comparison_type = rule.get('type', 'numeric')

        if comparison_type == 'numeric':
            comparison.update(self._compare_numeric_values(value1, value2, rule))
        elif comparison_type == 'categorical':
            comparison.update(self._compare_categorical_values(value1, value2, rule))
        elif comparison_type == 'range':
            comparison.update(self._compare_range_values(value1, value2, rule))

        return comparison

    def _compare_numeric_values(self, value1: float, value2: float,
                              rule: Dict[str, Any]) -> Dict[str, Any]:
        """对比数值型规格"""
        result = {}

        # 计算相似度
        max_val = max(value1, value2)
        min_val = min(value1, value2)

        if max_val > 0:
            similarity = min_val / max_val
        else:
            similarity = 1.0 if value1 == value2 else 0.0

        result['similarity'] = similarity

        # 确定优胜者
        higher_is_better = rule.get('higher_is_better', True)
        if higher_is_better:
            winner = 'equipment1' if value1 > value2 else 'equipment2' if value2 > value1 else 'equal'
        else:
            winner = 'equipment1' if value1 < value2 else 'equipment2' if value2 < value1 else 'equal'

        result['winner'] = winner

        # 生成描述
        diff_percentage = abs(value1 - value2) / max_val * 100 if max_val > 0 else 0

        if diff_percentage < 5:
            description = f"数值非常接近 ({value1} vs {value2})"
        elif diff_percentage < 15:
            description = f"数值相近 ({value1} vs {value2})"
        else:
            description = f"数值差异较大 ({value1} vs {value2})"

        result['description'] = description

        return result

    def _compare_categorical_values(self, value1: str, value2: str,
                                  rule: Dict[str, Any]) -> Dict[str, Any]:
        """对比类别型规格"""
        result = {}

        # 标准化值
        normalized_value1 = str(value1).lower().strip()
        normalized_value2 = str(value2).lower().strip()

        # 计算相似度
        if normalized_value1 == normalized_value2:
            similarity = 1.0
            winner = 'equal'
        else:
            # 检查是否为同义词或相似类别
            similarity = self._calculate_categorical_similarity(
                normalized_value1, normalized_value2, rule
            )
            winner = 'different'  # 类别型规格没有优胜者概念

        result['similarity'] = similarity
        result['winner'] = winner

        # 生成描述
        if similarity >= 0.9:
            description = f"相同类型 ({value1})"
        elif similarity >= 0.7:
            description = f"相似类型 ({value1} vs {value2})"
        else:
            description = f"不同类型 ({value1} vs {value2})"

        result['description'] = description

        return result

    def _compare_range_values(self, value1: str, value2: str,
                            rule: Dict[str, Any]) -> Dict[str, Any]:
        """对比范围型规格"""
        result = {}

        # 解析范围值 (例如 "2.1-2.4m")
        range1 = self._parse_range_value(value1)
        range2 = self._parse_range_value(value2)

        if range1 and range2:
            # 计算范围重叠度
            overlap = self._calculate_range_overlap(range1, range2)
            similarity = overlap

            # 确定优胜者（基于范围中点）
            midpoint1 = (range1[0] + range1[1]) / 2
            midpoint2 = (range2[0] + range2[1]) / 2
            higher_is_better = rule.get('higher_is_better', True)

            if higher_is_better:
                winner = 'equipment1' if midpoint1 > midpoint2 else 'equipment2' if midpoint2 > midpoint1 else 'equal'
            else:
                winner = 'equipment1' if midpoint1 < midpoint2 else 'equipment2' if midpoint2 < midpoint1 else 'equal'

            result['winner'] = winner
        else:
            similarity = 0.0
            winner = 'different'

        result['similarity'] = similarity

        # 生成描述
        if similarity >= 0.8:
            description = f"范围非常接近 ({value1} vs {value2})"
        elif similarity >= 0.5:
            description = f"范围部分重叠 ({value1} vs {value2})"
        else:
            description = f"范围差异较大 ({value1} vs {value2})"

        result['description'] = description

        return result

    def _parse_range_value(self, value: str) -> Optional[Tuple[float, float]]:
        """解析范围值"""
        import re

        # 匹配格式如 "2.1-2.4m" 或 "2.1~2.4"
        range_pattern = r'(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)'
        match = re.search(range_pattern, str(value))

        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            return (min_val, max_val)

        # 尝试匹配单个数值
        number_pattern = r'(\d+\.?\d*)'
        match = re.search(number_pattern, str(value))
        if match:
            single_val = float(match.group(1))
            return (single_val, single_val)

        return None

    def _calculate_range_overlap(self, range1: Tuple[float, float],
                               range2: Tuple[float, float]) -> float:
        """计算范围重叠度"""
        min1, max1 = range1
        min2, max2 = range2

        # 计算重叠区间
        overlap_min = max(min1, min2)
        overlap_max = min(max1, max2)

        if overlap_min > overlap_max:
            return 0.0  # 没有重叠

        # 计算重叠长度
        overlap_length = overlap_max - overlap_min

        # 计算总长度
        total_length = max(max1, max2) - min(min1, min2)

        if total_length == 0:
            return 1.0  # 两个范围都是点且相同

        return overlap_length / total_length

    def _calculate_categorical_similarity(self, value1: str, value2: str,
                                        rule: Dict[str, Any]) -> float:
        """计算类别相似度"""
        # 检查同义词映射
        synonyms = rule.get('synonyms', {})

        normalized_values = set()
        for value in [value1, value2]:
            if value in synonyms:
                normalized_values.add(synonyms[value])
            else:
                normalized_values.add(value)

        if len(normalized_values) == 1:
            return 1.0  # 同义词或相同值

        # 检查相似类别映射
        similarity_groups = rule.get('similarity_groups', [])
        for group in similarity_groups:
            if value1 in group and value2 in group:
                return 0.8  # 相似类别

        # 检查是否有共同的父类别
        parent_categories = rule.get('parent_categories', {})
        parent1 = parent_categories.get(value1)
        parent2 = parent_categories.get(value2)

        if parent1 and parent1 == parent2:
            return 0.6  # 相同父类别

        return 0.0  # 完全不同

    def _are_spec_values_similar(self, spec_name: str, value1: Any, value2: Any) -> bool:
        """判断规格值是否相似"""
        if value1 is None or value2 is None:
            return False

        try:
            # 数值型规格
            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                max_val = max(value1, value2)
                if max_val > 0:
                    similarity = min(value1, value2) / max_val
                    return similarity > 0.9
                else:
                    return value1 == value2

            # 字符串型规格
            value1_str = str(value1).lower().strip()
            value2_str = str(value2).lower().strip()
            return value1_str == value2_str

        except (ValueError, TypeError):
            return False

    def _compare_brands(self, brand1: str, brand2: str) -> Dict[str, Any]:
        """对比品牌"""
        brand_tiers = {
            'premium': ['禧玛诺', '达亿瓦', 'stella', 'exist'],
            'mid_range': ['光威', '化氏', '宝飞龙', '天元'],
            'budget': ['迪佳', '鱼王', '美人鱼']
        }

        tier1 = self._get_brand_tier(brand1, brand_tiers)
        tier2 = self._get_brand_tier(brand2, brand_tiers)

        return {
            'brands': [brand1, brand2],
            'tiers': [tier1, tier2],
            'similarity': 1.0 if tier1 == tier2 else 0.5,
            'premium_diff': abs(tier1 - tier2)
        }

    def _compare_levels(self, level1: EquipmentLevel, level2: EquipmentLevel) -> Dict[str, Any]:
        """对比等级"""
        level_hierarchy = {
            EquipmentLevel.BEGINNER: 1,
            EquipmentLevel.INTERMEDIATE: 2,
            EquipmentLevel.ADVANCED: 3,
            EquipmentLevel.PROFESSIONAL: 4
        }

        rank1 = level_hierarchy[level1]
        rank2 = level_hierarchy[level2]

        return {
            'levels': [level1.value, level2.value],
            'ranks': [rank1, rank2],
            'difference': abs(rank1 - rank2)
        }

    def _get_brand_tier(self, brand: str, brand_tiers: Dict[str, List[str]]) -> int:
        """获取品牌档次"""
        brand_lower = brand.lower()

        for tier, brands in brand_tiers.items():
            for b in brands:
                if b.lower() in brand_lower or brand_lower in b.lower():
                    return list(brand_tiers.keys()).index(tier) + 1

        return 2  # 默认中档

    def _initialize_comparison_rules(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """初始化对比规则"""
        return {
            'fishing_rod': {
                'length': {
                    'type': 'range',
                    'significance': 'high',
                    'higher_is_better': False  # 不是越高越好，而是适中
                },
                'weight': {
                    'type': 'numeric',
                    'significance': 'medium',
                    'higher_is_better': False  # 轻量化更好
                },
                'material': {
                    'type': 'categorical',
                    'significance': 'high',
                    'synonyms': {
                        'carbon': '碳纤维',
                        'carbon fiber': '碳纤维',
                        'graphite': '碳纤维'
                    },
                    'similarity_groups': [
                        ['carbon', 'carbon fiber', 'graphite'],
                        ['glass', 'fiberglass', '玻璃纤维']
                    ]
                },
                'action': {
                    'type': 'categorical',
                    'significance': 'medium',
                    'synonyms': {
                        'ml': 'medium light',
                        'mh': 'medium heavy'
                    }
                }
            },
            'fishing_reel': {
                'bearings': {
                    'type': 'numeric',
                    'significance': 'medium',
                    'higher_is_better': True
                },
                'gear_ratio': {
                    'type': 'numeric',
                    'significance': 'high',
                    'higher_is_better': True
                },
                'line_capacity': {
                    'type': 'categorical',
                    'significance': 'medium'
                }
            },
            # 其他类别规则...
        }

    def _initialize_spec_weights(self) -> Dict[str, Dict[str, float]]:
        """初始化规格权重"""
        return {
            'fishing_rod': {
                'length': 0.20,
                'weight': 0.15,
                'material': 0.25,
                'action': 0.20,
                'power': 0.20
            },
            'fishing_reel': {
                'bearings': 0.20,
                'gear_ratio': 0.25,
                'line_capacity': 0.20,
                'weight': 0.15,
                'material': 0.20
            },
            # 其他类别权重...
        }
```

## 🛠️ LangChain工具集成

### 装备对比分析工具函数
```python
from langchain_core.tools import tool
from typing import Dict, Any, List, Optional

@tool
def compare_multiple_equipment(
    equipment_list: List[Dict[str, str]],
    comparison_focus: Optional[str] = None
) -> Dict[str, Any]:
    """
    对比多款钓鱼装备的详细参数和性能

    Args:
        equipment_list: 装备列表，每个装备包含brand和model
        comparison_focus: 对比重点 (performance/price/value/overall)

    Returns:
        Dict: 包含详细对比分析、性能排名、优劣势分析等
    """
    try:
        if len(equipment_list) < 2:
            return {
                "success": False,
                "message": "至少需要2个装备进行对比"
            }

        # 获取装备信息
        service_container = get_service_container()
        equipment_repository = service_container.get_service('equipment_repository')
        comparison_engine = service_container.get_service('comparison_engine')

        equipment_ids = []
        equipment_details = []

        for equipment_info in equipment_list:
            brand = equipment_info.get('brand', '')
            model = equipment_info.get('model', '')

            # 搜索装备
            search_results = equipment_repository.search_equipment(
                f"{brand} {model}", {'limit': 1}
            )

            if search_results:
                equipment = search_results[0]
                equipment_ids.append(equipment.id)
                equipment_details.append({
                    "id": equipment.id,
                    "brand": equipment.spec.brand,
                    "model": equipment.spec.model,
                    "price": equipment.spec.price,
                    "level": equipment.spec.level.value
                })

        if len(equipment_ids) < 2:
            return {
                "success": False,
                "message": "无法找到足够的装备信息进行对比"
            }

        # 执行对比分析
        comparison_type = ComparisonType.MULTI_COMPARISON
        result = comparison_engine.compare_equipment(equipment_ids, comparison_type)

        # 格式化返回结果
        formatted_result = {
            "success": True,
            "comparison_id": result.comparison_id,
            "equipment_count": len(result.equipment_comparisons),
            "equipments": equipment_details,
            "ranking": [
                {
                    "rank": i + 1,
                    "equipment_id": equipment_id,
                    "overall_score": f"{score:.1f}/100"
                }
                for i, (equipment_id, score) in enumerate(result.ranking)
            ],
            "dimension_analysis": {
                dimension.value: {
                    equipment_id: f"{score:.1f}/100"
                    for equipment_id, score in scores.items()
                }
                for dimension, scores in result.dimension_scores.items()
            },
            "key_differences": result.key_differences,
            "value_analysis": {
                "best_value": result.value_analysis.get('best_value_equipment'),
                "value_range": {
                    "min": f"{result.value_analysis['value_range']['min']:.2f}",
                    "max": f"{result.value_analysis['value_range']['max']:.2f}",
                    "average": f"{result.value_analysis['value_range']['average']:.2f}"
                }
            },
            "recommendation": result.recommendation,
            "detailed_scores": {
                comp.equipment_id: {
                    "overall_score": f"{comp.overall_score:.1f}/100",
                    "strengths": comp.strengths,
                    "weaknesses": comp.weaknesses,
                    "key_metrics": {
                        metric: f"{value:.1f}"
                        for metric, value in list(comp.metrics.items())[:5]
                    }
                }
                for comp in result.equipment_comparisons
            }
        }

        # 根据对比重点调整结果
        if comparison_focus:
            formatted_result["focus_analysis"] = _generate_focus_analysis(
                result, comparison_focus
            )

        return formatted_result

    except Exception as e:
        logger.error(f"多装备对比失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "很抱歉，无法完成装备对比分析"
        }

@tool
def analyze_upgrade_value(
    current_equipment: Dict[str, str],
    target_equipment: Dict[str, str]
) -> Dict[str, Any]:
    """
    分析装备升级的价值和性价比

    Args:
        current_equipment: 当前装备 {brand, model}
        target_equipment: 目标装备 {brand, model}

    Returns:
        Dict: 包含升级价值分析、性能提升、性价比评估等
    """
    try:
        # 获取装备信息
        service_container = get_service_container()
        equipment_repository = service_container.get_service('equipment_repository')
        comparison_engine = service_container.get_service('comparison_engine')

        # 查找装备
        current_eq = _find_equipment_by_brand_model(
            equipment_repository, current_equipment['brand'], current_equipment['model']
        )
        target_eq = _find_equipment_by_brand_model(
            equipment_repository, target_equipment['brand'], target_equipment['model']
        )

        if not current_eq or not target_eq:
            return {
                "success": False,
                "message": "无法找到指定的装备信息"
            }

        # 执行升级价值分析
        upgrade_analysis = comparison_engine.analyze_upgrade_value(
            current_eq.id, target_eq.id
        )

        # 格式化结果
        return {
            "success": True,
            "current_equipment": {
                "name": f"{current_eq.spec.brand} {current_eq.spec.model}",
                "price": current_eq.spec.price,
                "level": current_eq.spec.level.value,
                "overall_score": f"{upgrade_analysis['current_equipment']['overall_score']:.1f}/100"
            },
            "target_equipment": {
                "name": f"{target_eq.spec.brand} {target_eq.spec.model}",
                "price": target_eq.spec.price,
                "level": target_eq.spec.level.value,
                "overall_score": f"{upgrade_analysis['target_equipment']['overall_score']:.1f}/100"
            },
            "upgrade_analysis": {
                "performance_improvement": f"{upgrade_analysis['performance_improvement']:.1f} 分",
                "price_difference": f"{upgrade_analysis['price_difference']:.0f} 元",
                "value_ratio": f"{upgrade_analysis['value_ratio']:.2f}",
                "is_recommended": upgrade_analysis['is_recommended']
            },
            "spec_improvements": upgrade_analysis['spec_differences'],
            "recommendation": upgrade_analysis['upgrade_recommendation'],
            "upgrade_suggestion": _generate_upgrade_suggestion(upgrade_analysis)
        }

    except Exception as e:
        logger.error(f"升级价值分析失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "很抱歉，无法分析升级价值"
        }

@tool
def get_equipment_performance_scores(
    category: str,
    brands: Optional[List[str]] = None,
    price_range: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    获取特定类别装备的性能评分排名

    Args:
        category: 装备类别
        brands: 筛选品牌列表 (可选)
        price_range: 价格范围 {min, max} (可选)

    Returns:
        Dict: 包含性能评分排名和详细分析
    """
    try:
        # 构建过滤条件
        filters = {'category': category}

        if brands:
            filters['brands'] = brands

        if price_range:
            filters['min_price'] = price_range.get('min', 0)
            filters['max_price'] = price_range.get('max', float('inf'))

        # 获取装备对比结果
        service_container = get_service_container()
        comparison_engine = service_container.get_service('comparison_engine')

        comparison_result = comparison_engine.compare_multiple_equipment(
            category, filters, limit=15
        )

        # 格式化性能排名
        performance_ranking = []
        for rank, (equipment_id, score) in enumerate(comparison_result.ranking, 1):
            equipment_info = None
            for comp in comparison_result.equipment_comparisons:
                if comp.equipment_id == equipment_id:
                    # 获取装备详细信息
                    equipment_repository = service_container.get_service('equipment_repository')
                    equipment = equipment_repository.find_by_id(equipment_id)
                    if equipment:
                        equipment_info = {
                            "brand": equipment.spec.brand,
                            "model": equipment.spec.model,
                            "price": equipment.spec.price,
                            "level": equipment.spec.level.value
                        }
                    break

            if equipment_info:
                performance_ranking.append({
                    "rank": rank,
                    "overall_score": f"{score:.1f}/100",
                    "performance_grade": _get_performance_grade(score),
                    **equipment_info
                })

        # 维度分析
        dimension_analysis = {}
        for dimension, scores in comparison_result.dimension_scores.items():
            # 按评分排序
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            dimension_analysis[dimension.value] = [
                {
                    "rank": i + 1,
                    "equipment_id": equipment_id,
                    "score": f"{score:.1f}/100"
                }
                for i, (equipment_id, score) in enumerate(sorted_scores[:5])
            ]

        return {
            "success": True,
            "category": category,
            "total_equipment": len(performance_ranking),
            "performance_ranking": performance_ranking,
            "dimension_analysis": dimension_analysis,
            "analysis_summary": _generate_performance_summary(comparison_result),
            "best_value_equipment": comparison_result.value_analysis.get('best_value_equipment')
        }

    except Exception as e:
        logger.error(f"性能评分获取失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "很抱歉，无法获取装备性能评分"
        }

# 辅助函数
def _find_equipment_by_brand_model(repository, brand: str, model: str):
    """根据品牌型号查找装备"""
    search_results = repository.search_equipment(f"{brand} {model}", {'limit': 1})
    return search_results[0] if search_results else None

def _generate_focus_analysis(result: ComparisonResult, focus: str) -> Dict[str, Any]:
    """生成重点分析"""
    focus_analysis = {}

    if focus == "performance":
        # 性能重点分析
        best_performance = max(result.equipment_comparisons, key=lambda x: x.overall_score)
        focus_analysis = {
            "focus_type": "performance",
            "best_performer": best_performance.equipment_id,
            "analysis": f"最佳性能装备评分为 {best_performance.overall_score:.1f} 分",
            "recommendation": "如果您优先考虑性能，建议选择这款装备"
        }
    elif focus == "price":
        # 价格重点分析
        service_container = get_service_container()
        equipment_repository = service_container.get_service('equipment_repository')

        prices = {}
        for comp in result.equipment_comparisons:
            equipment = equipment_repository.find_by_id(comp.equipment_id)
            if equipment:
                prices[comp.equipment_id] = equipment.spec.price

        if prices:
            cheapest_id = min(prices.keys(), key=lambda k: prices[k])
            focus_analysis = {
                "focus_type": "price",
                "cheapest_option": cheapest_id,
                "analysis": f"最经济选项价格为 {prices[cheapest_id]:.0f} 元",
                "recommendation": "如果您预算有限，建议选择这款经济型装备"
            }
    elif focus == "value":
        # 性价比重点分析
        best_value_id = result.value_analysis.get('best_value_equipment')
        if best_value_id:
            focus_analysis = {
                "focus_type": "value",
                "best_value": best_value_id,
                "analysis": "最佳性价比选择",
                "recommendation": "如果您追求性价比，这款装备是最佳选择"
            }

    return focus_analysis

def _generate_upgrade_suggestion(upgrade_analysis: Dict[str, Any]) -> str:
    """生成升级建议"""
    performance_improvement = upgrade_analysis['performance_improvement']
    price_difference = upgrade_analysis['price_difference']
    is_recommended = upgrade_analysis['is_recommended']

    if is_recommended:
        if performance_improvement > 20:
            return "强烈推荐升级！性能提升显著，性价比优秀。"
        elif performance_improvement > 10:
            return "推荐升级。性能有明显提升，值得投资。"
        else:
            return "可以考虑升级。性能略有提升，按需选择。"
    else:
        if price_difference > 1000:
            return "不推荐升级。价格过高，性能提升有限。"
        else:
            return "升级价值不高。建议继续使用当前装备或考虑其他选择。"

def _get_performance_grade(score: float) -> str:
    """获取性能等级"""
    if score >= 95:
        return "A+ (卓越)"
    elif score >= 90:
        return "A (优秀)"
    elif score >= 85:
        return "B+ (良好)"
    elif score >= 80:
        return "B (中等偏上)"
    elif score >= 75:
        return "C+ (中等)"
    elif score >= 70:
        return "C (中等偏下)"
    else:
        return "D (需要改进)"

def _generate_performance_summary(result: ComparisonResult) -> str:
    """生成性能总结"""
    if not result.equipment_comparisons:
        return "无数据"

    scores = [comp.overall_score for comp in result.equipment_comparisons]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)

    summary = f"共对比 {len(scores)} 款装备，平均评分 {avg_score:.1f} 分。"

    if max_score - min_score > 20:
        summary += "装备间性能差异较大，建议仔细对比选择。"
    else:
        summary += "装备间性能相近，可根据价格和品牌偏好选择。"

    return summary

def get_service_container():
    """获取服务容器"""
    from shared.infrastructure.service_manager import get_service_manager
    return get_service_manager()
```

## 🎯 开发实施指南

### 开发优先级和里程碑

#### 第一阶段：核心对比引擎（2周）
**目标**：建立基础的装备对比分析能力

**Week 1: 性能评分系统**
- [ ] 实现PerformanceScorer性能评分器
- [ ] 开发多维度评分算法
- [ ] 建立性能基准体系
- [ ] 实现装备指标提取和标准化

**Week 2: 对比分析引擎**
- [ ] 实现ComparisonEngine对比分析引擎
- [ ] 开发装备对比核心算法
- [ ] 实现排名和推荐生成
- [ ] 创建基础缓存机制

#### 第二阶段：规格分析系统（1-2周）
**目标**：实现详细的规格参数对比分析

**Week 3: 规格分析器**
- [ ] 实现SpecificationAnalyzer规格分析器
- [ ] 开发多类型规格对比算法
- [ ] 建立规格对比规则库
- [ ] 实现相似度计算方法

**Week 4: 升级价值分析**
- [ ] 实现UpgradeAdvisor升级顾问
- [ ] 开发升级价值评估算法
- [ ] 实现性价比分析功能
- [ ] 创建升级建议生成器

#### 第三阶段：工具集成和优化（1周）
**目标**：完成LangChain工具集成和系统优化

**Week 5: 工具集成**
- [ ] 开发LangChain工具函数
- [ ] 实现错误处理和异常管理
- [ ] 创建API接口和文档
- [ ] 进行端到端测试和性能优化

### 技术实施要点

#### 1. 性能评分算法
- **多维度评估**: 从性能、价格、易用性、耐用性等多维度评估
- **权重调优**: 根据用户反馈和市场需求调整评分权重
- **基准对比**: 与同级产品进行基准对比，提供相对性能评估
- **置信度计算**: 评估评分结果的可信度

#### 2. 规格对比分析
- **类型识别**: 区分数值型、类别型、范围型等不同规格类型
- **相似度计算**: 针对不同类型采用合适的相似度计算方法
- **关键差异识别**: 识别影响用户决策的关键规格差异
- **标准化处理**: 将不同规格标准化到统一的评分体系

#### 3. 对比结果展示
- **多层次展示**: 提供概览、详细分析、专业建议等多层次信息
- **可视化支持**: 支持图表、雷达图等可视化对比展示
- **个性化推荐**: 基于用户需求提供个性化的购买建议
- **决策支持**: 提供明确的决策依据和购买指导

#### 4. 系统性能优化
- **缓存策略**: 对常用对比结果进行缓存
- **异步处理**: 复杂分析计算使用异步任务
- **数据库优化**: 优化查询性能和索引设计
- **负载均衡**: 支持高并发对比请求

### 测试策略

#### 单元测试
```python
import pytest
from unittest.mock import Mock

class TestPerformanceScorer:
    """性能评分器测试"""

    def setup_method(self):
        self.scorer = PerformanceScorer()

    def test_score_fishing_rod(self):
        """测试鱼竿评分"""
        equipment = Equipment(
            id="test_rod",
            spec=EquipmentSpec(
                brand="TestBrand",
                model="TestModel",
                category=EquipmentCategory.FISHING_ROD,
                level=EquipmentLevel.INTERMEDIATE,
                price=500,
                specifications={
                    'length': 240,
                    'weight': 80,
                    'material': 'carbon',
                    'action': 'medium'
                },
                compatibility=[]
            ),
            performance_score=85,
            popularity_score=80,
            user_rating=4.2,
            review_count=150,
            availability=True
        )

        result = self.scorer.score_equipment(equipment)

        assert result.overall_score > 70
        assert len(result.dimension_scores) > 0
        assert result.confidence_level > 0.5

    def test_extract_rod_metrics(self):
        """测试鱼竿指标提取"""
        specs = {
            'length': 240,
            'weight': 80,
            'material': 'carbon',
            'action': 'medium'
        }

        metrics = self.scorer._extract_rod_metrics(specs)

        assert 'length_score' in metrics
        assert 'weight_score' in metrics
        assert 'material_score' in metrics
        assert 'action_score' in metrics
        assert all(0 <= score <= 100 for score in metrics.values())

class TestComparisonEngine:
    """对比分析引擎测试"""

    def setup_method(self):
        self.mock_repository = Mock(spec=EquipmentRepository)
        self.mock_scorer = Mock(spec=PerformanceScorer)
        self.mock_analyzer = Mock(spec=SpecificationAnalyzer)
        self.mock_advisor = Mock(spec=UpgradeAdvisor)

        self.engine = ComparisonEngine(
            self.mock_repository,
            self.mock_scorer,
            self.mock_analyzer,
            self.mock_advisor
        )

    def test_compare_two_equipment(self):
        """测试两款装备对比"""
        # 准备测试数据
        equipment1 = self._create_test_equipment("rod1", 500)
        equipment2 = self._create_test_equipment("rod2", 600)

        self.mock_repository.find_by_id.side_effect = [equipment1, equipment2]

        # 设置性能评分返回值
        mock_score = DetailedPerformanceScore(
            overall_score=85.0,
            dimension_scores={AnalysisDimension.PERFORMANCE: 90.0},
            sub_metrics={'performance_score': 85},
            benchmark_comparison={},
            confidence_level=0.8
        )
        self.mock_scorer.score_equipment.return_value = mock_score

        # 执行对比
        result = self.engine.compare_equipment(["rod1", "rod2"])

        # 验证结果
        assert result is not None
        assert len(result.equipment_comparisons) == 2
        assert len(result.ranking) == 2
        assert result.recommendation is not None

    def _create_test_equipment(self, equipment_id: str, price: float) -> Equipment:
        """创建测试装备"""
        return Equipment(
            id=equipment_id,
            spec=EquipmentSpec(
                brand="TestBrand",
                model=f"TestModel{equipment_id}",
                category=EquipmentCategory.FISHING_ROD,
                level=EquipmentLevel.INTERMEDIATE,
                price=price,
                specifications={},
                compatibility=[]
            ),
            performance_score=85,
            popularity_score=80,
            user_rating=4.2,
            review_count=100,
            availability=True
        )
```

#### 集成测试
```python
class TestComparisonIntegration:
    """对比系统集成测试"""

    def setup_method(self):
        # 使用测试数据库
        self.test_db = create_test_database()
        self.setup_test_data()

        # 创建真实的服务实例
        self.equipment_repository = DatabaseEquipmentRepository(self.test_db)
        self.performance_scorer = PerformanceScorer()
        self.spec_analyzer = SpecificationAnalyzer()
        self.upgrade_advisor = UpgradeAdvisor()

        self.comparison_engine = ComparisonEngine(
            self.equipment_repository,
            self.performance_scorer,
            self.spec_analyzer,
            self.upgrade_advisor
        )

    def test_full_comparison_workflow(self):
        """测试完整对比工作流"""
        # 获取测试装备
        equipments = self.equipment_repository.find_by_category(
            EquipmentCategory.FISHING_ROD
        )[:3]

        if len(equipments) < 2:
            pytest.skip("需要至少2个测试装备")

        equipment_ids = [equipment.id for equipment in equipments]

        # 执行对比
        result = self.comparison_engine.compare_equipment(
            equipment_ids, ComparisonType.MULTI_COMPARISON
        )

        # 验证结果
        assert result is not None
        assert len(result.equipment_comparisons) == len(equipments)
        assert len(result.ranking) == len(equipments)
        assert result.overall_score > 0

        # 验证排名合理性
        scores = [score for _, score in result.ranking]
        assert scores == sorted(scores, reverse=True)

        # 验证维度分析
        assert len(result.dimension_scores) > 0
        for dimension, scores in result.dimension_scores.items():
            assert len(scores) == len(equipments)
```

### 部署和运维

#### 1. 性能监控
- **响应时间**: 监控对比分析的响应时间
- **准确率**: 监控推荐结果的用户满意度
- **并发量**: 监控系统的并发处理能力
- **缓存命中率**: 监控缓存系统的效率

#### 2. 数据质量
- **数据完整性**: 确保装备规格数据的完整性
- **数据准确性**: 定期验证装备信息的准确性
- **数据更新**: 建立装备信息的定期更新机制
- **异常检测**: 监控和检测异常数据

#### 3. 用户体验
- **结果质量**: 持续优化对比分析结果的质量
- **响应速度**: 优化系统响应速度
- **界面友好**: 提供直观易用的对比结果展示
- **个性化**: 基于用户反馈优化个性化推荐

---

## 📝 开发总结

装备对比分析系统为钓鱼爱好者提供专业、客观、详细的装备对比分析服务。通过多维度的性能评估、详细的规格对比、智能的升级价值分析，帮助用户做出最优的装备选择决策。

### 核心能力
- **专业性能评分**: 基于多维度指标的科学评分体系
- **详细规格对比**: 深度分析装备规格参数的差异和影响
- **智能排名推荐**: 提供客观的排名和个性化推荐建议
- **升级价值分析**: 评估装备升级的价值和性价比

### 技术特色
- **科学评分算法**: 基于基准对比和多维度评估的评分体系
- **智能规格分析**: 支持多种规格类型的智能对比分析
- **高性能缓存**: 优化常用对比结果的缓存策略
- **LangChain集成**: 无缝集成到智能体对话系统

该系统为钓鱼装备选择提供专业级的数据支持，显著提升用户的购买决策质量和满意度。