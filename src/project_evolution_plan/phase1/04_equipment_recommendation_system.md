# 装备推荐系统开发指南

## 📋 模块概述

### 🎯 系统定位
装备推荐系统是智能钓鱼生态系统的核心模块之一，专注于为用户提供个性化的装备推荐和搭配建议。该系统基于用户需求、预算约束、钓鱼场景等多维度因素，运用智能推荐算法，为用户提供最适合的装备配置方案。

### 🔍 核心价值主张
- **个性化推荐**: 基于用户画像和需求特征的精准装备推荐
- **专业搭配**: 提供装备间的专业搭配建议和兼容性分析
- **预算优化**: 在预算约束下实现装备配置的最优化
- **场景适配**: 针对不同钓鱼场景提供专业化装备建议

### 🏗️ 系统依赖
- **基础设施层**: 共享数据库管理、缓存系统、配置管理
- **服务管理器**: 依赖注入容器和服务生命周期管理
- **鱼类知识系统**: 提供目标鱼种的相关装备需求信息
- **外部API**: 装备价格查询、规格参数获取

## 🎯 领域模型设计

### 核心实体模型

#### 1. 装备实体 (Equipment)
```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class EquipmentCategory(Enum):
    """装备类别枚举"""
    FISHING_ROD = "fishing_rod"      # 鱼竿
    FISHING_REEL = "fishing_reel"    # 鱼轮
    FISHING_LINE = "fishing_line"    # 鱼线
    FISHING_LURE = "fishing_lure"    # 拟饵
    FISHING_HOOK = "fishing_hook"    # 鱼钩
    ACCESSORIES = "accessories"      # 配件

class EquipmentLevel(Enum):
    """装备等级枚举"""
    BEGINNER = "beginner"            # 入门级
    INTERMEDIATE = "intermediate"    # 进阶级
    ADVANCED = "advanced"            # 高级
    PROFESSIONAL = "professional"    # 专业级

@dataclass
class EquipmentSpec:
    """装备规格"""
    brand: str                       # 品牌
    model: str                       # 型号
    category: EquipmentCategory      # 类别
    level: EquipmentLevel            # 等级
    price: float                     # 价格
    specifications: Dict[str, Any]   # 技术规格
    compatibility: List[str]         # 兼容性列表
    weight: Optional[float] = None   # 重量
    material: Optional[str] = None   # 材质
    warranty_period: Optional[int] = None  # 保修期(月)

@dataclass
class Equipment:
    """装备实体"""
    id: str                          # 唯一标识
    spec: EquipmentSpec              # 规格
    performance_score: float         # 性能评分(0-100)
    popularity_score: float          # 人气评分(0-100)
    user_rating: float               # 用户评分(0-5)
    review_count: int                # 评价数量
    availability: bool               # 是否有货
    last_updated: datetime = field(default_factory=datetime.now)

    def is_suitable_for_level(self, user_level: EquipmentLevel) -> bool:
        """判断装备是否适合用户水平"""
        level_hierarchy = {
            EquipmentLevel.BEGINNER: 1,
            EquipmentLevel.INTERMEDIATE: 2,
            EquipmentLevel.ADVANCED: 3,
            EquipmentLevel.PROFESSIONAL: 4
        }

        equipment_rank = level_hierarchy[self.spec.level]
        user_rank = level_hierarchy[user_level]

        # 装备等级最多比用户高一个级别
        return equipment_rank <= user_rank + 1
```

#### 2. 用户需求模型 (UserRequirement)
```python
@dataclass
class FishingScenario:
    """钓鱼场景"""
    location: str                    # 地点
    target_fish: List[str]           # 目标鱼种
    season: str                      # 季节
    weather_condition: str           # 天气条件
    water_type: str                  # 水域类型

@dataclass
class BudgetAllocation:
    """预算分配"""
    total_budget: float              # 总预算
    rod_budget: Optional[float] = None       # 鱼竿预算
    reel_budget: Optional[float] = None      # 鱼轮预算
    line_budget: Optional[float] = None      # 鱼线预算
    lure_budget: Optional[float] = None      # 拟饵预算
    accessory_budget: Optional[float] = None # 配件预算

    def get_category_budget(self, category: EquipmentCategory) -> float:
        """获取特定类别的预算"""
        budget_map = {
            EquipmentCategory.FISHING_ROD: self.rod_budget,
            EquipmentCategory.FISHING_REEL: self.reel_budget,
            EquipmentCategory.FISHING_LINE: self.line_budget,
            EquipmentCategory.FISHING_LURE: self.lure_budget,
            EquipmentCategory.FISHING_HOOK: self.accessory_budget,
            EquipmentCategory.ACCESSORIES: self.accessory_budget
        }
        return budget_map.get(category, 0) or 0

@dataclass
class UserRequirement:
    """用户需求"""
    user_id: str                     # 用户ID
    experience_level: EquipmentLevel # 经验水平
    primary_use: str                 # 主要用途
    fishing_scenarios: List[FishingScenario]  # 钓鱼场景
    budget_allocation: BudgetAllocation       # 预算分配
    preferred_brands: List[str] = field(default_factory=list)  # 偏好品牌
    avoided_brands: List[str] = field(default_factory=list)     # 避免品牌
    special_requirements: List[str] = field(default_factory=list)  # 特殊需求

    def matches_equipment(self, equipment: Equipment) -> bool:
        """判断装备是否符合用户需求"""
        # 检查品牌偏好
        if equipment.spec.brand in self.avoided_brands:
            return False
        if self.preferred_brands and equipment.spec.brand not in self.preferred_brands:
            return False

        # 检查经验水平适配
        if not equipment.is_suitable_for_level(self.experience_level):
            return False

        return True
```

#### 3. 推荐结果模型 (RecommendationResult)
```python
@dataclass
class EquipmentRecommendation:
    """装备推荐项"""
    equipment: Equipment             # 推荐装备
    score: float                     # 推荐评分(0-100)
    reasons: List[str]               # 推荐理由
    alternatives: List[Equipment]    # 替代方案
    price_analysis: Dict[str, float] # 价格分析

@dataclass
class EquipmentSet:
    """装备套装"""
    equipments: Dict[EquipmentCategory, EquipmentRecommendation]  # 装备组合
    total_price: float               # 总价格
    compatibility_score: float       # 兼容性评分
    synergy_score: float             # 协同效应评分
    overall_score: float             # 综合评分

    def get_equipment(self, category: EquipmentCategory) -> Optional[EquipmentRecommendation]:
        """获取特定类别的装备"""
        return self.equipments.get(category)

@dataclass
class RecommendationResult:
    """推荐结果"""
    user_requirement: UserRequirement  # 用户需求
    primary_set: EquipmentSet          # 主要推荐套装
    alternative_sets: List[EquipmentSet]  # 替代套装
    reasoning: str                     # 推荐理由说明
    confidence_score: float            # 置信度评分
    generated_at: datetime = field(default_factory=datetime.now)
```

### 领域服务模型

#### 1. 装备匹配服务 (EquipmentMatcher)
```python
class EquipmentMatcher:
    """装备匹配服务"""

    def __init__(self, equipment_repository: 'EquipmentRepository'):
        self.equipment_repository = equipment_repository
        self.scoring_weights = {
            'performance': 0.3,
            'price_fit': 0.25,
            'user_level': 0.2,
            'scenario_match': 0.15,
            'brand_preference': 0.1
        }

    def find_matching_equipment(self, requirement: UserRequirement,
                              category: EquipmentCategory,
                              budget: float) -> List[Equipment]:
        """查找匹配的装备"""
        # 获取候选装备
        candidates = self.equipment_repository.find_by_category_and_price(
            category, budget * 1.2  # 允许20%的预算浮动
        )

        # 应用用户需求过滤
        filtered_candidates = [
            equipment for equipment in candidates
            if requirement.matches_equipment(equipment)
        ]

        # 按匹配度评分排序
        scored_candidates = []
        for equipment in filtered_candidates:
            score = self._calculate_match_score(equipment, requirement, budget)
            scored_candidates.append((equipment, score))

        # 按评分排序并返回装备列表
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return [equipment for equipment, score in scored_candidates]

    def _calculate_match_score(self, equipment: Equipment,
                             requirement: UserRequirement,
                             budget: float) -> float:
        """计算装备匹配评分"""
        scores = {}

        # 性能评分
        scores['performance'] = equipment.performance_score / 100

        # 价格适配评分
        price_ratio = equipment.spec.price / budget
        if price_ratio <= 0.8:
            scores['price_fit'] = 1.0
        elif price_ratio <= 1.0:
            scores['price_fit'] = 0.8
        elif price_ratio <= 1.2:
            scores['price_fit'] = 0.5
        else:
            scores['price_fit'] = 0.0

        # 用户水平适配评分
        if equipment.is_suitable_for_level(requirement.experience_level):
            level_diff = self._get_level_difference(
                equipment.spec.level, requirement.experience_level
            )
            scores['user_level'] = 1.0 - (level_diff * 0.2)
        else:
            scores['user_level'] = 0.0

        # 场景匹配评分
        scores['scenario_match'] = self._calculate_scenario_match(
            equipment, requirement.fishing_scenarios
        )

        # 品牌偏好评分
        if equipment.spec.brand in requirement.preferred_brands:
            scores['brand_preference'] = 1.0
        elif equipment.spec.brand in requirement.avoided_brands:
            scores['brand_preference'] = 0.0
        else:
            scores['brand_preference'] = 0.5

        # 计算加权总分
        total_score = sum(
            score * weight
            for score, weight in zip(scores.values(), self.scoring_weights.values())
        )

        return total_score * 100

    def _get_level_difference(self, equipment_level: EquipmentLevel,
                            user_level: EquipmentLevel) -> int:
        """获取等级差异"""
        level_hierarchy = {
            EquipmentLevel.BEGINNER: 1,
            EquipmentLevel.INTERMEDIATE: 2,
            EquipmentLevel.ADVANCED: 3,
            EquipmentLevel.PROFESSIONAL: 4
        }

        return abs(
            level_hierarchy[equipment_level] - level_hierarchy[user_level]
        )

    def _calculate_scenario_match(self, equipment: Equipment,
                                scenarios: List[FishingScenario]) -> float:
        """计算场景匹配度"""
        if not scenarios:
            return 0.5  # 默认中等匹配

        total_match = 0.0
        for scenario in scenarios:
            # 基于装备规格和场景特征的匹配计算
            match_score = 0.5  # 基础匹配分

            # 这里可以添加更复杂的场景匹配逻辑
            # 例如：根据目标鱼种、水域类型等匹配装备特性

            total_match += match_score

        return total_match / len(scenarios)
```

#### 2. 搭配顾问服务 (ComboAdvisor)
```python
class ComboAdvisor:
    """装备搭配顾问"""

    def __init__(self):
        self.compatibility_rules = self._initialize_compatibility_rules()
        self.synergy_patterns = self._initialize_synergy_patterns()

    def analyze_equipment_compatibility(self, equipment_set: Dict[EquipmentCategory, Equipment]) -> float:
        """分析装备兼容性"""
        if len(equipment_set) < 2:
            return 1.0

        total_compatibility = 0.0
        comparison_count = 0

        categories = list(equipment_set.keys())

        for i in range(len(categories)):
            for j in range(i + 1, len(categories)):
                category1, category2 = categories[i], categories[j]
                equipment1, equipment2 = equipment_set[category1], equipment_set[category2]

                compatibility = self._calculate_pair_compatibility(equipment1, equipment2)
                total_compatibility += compatibility
                comparison_count += 1

        return total_compatibility / comparison_count if comparison_count > 0 else 1.0

    def calculate_synergy_score(self, equipment_set: Dict[EquipmentCategory, Equipment]) -> float:
        """计算协同效应评分"""
        synergy_score = 1.0  # 基础协同分

        # 检查品牌套装加成
        brands = [equipment.spec.brand for equipment in equipment_set.values()]
        if len(set(brands)) == 1:  # 同品牌套装
            synergy_score += 0.1

        # 检查装备等级一致性
        levels = [equipment.spec.level for equipment in equipment_set.values()]
        if len(set(levels)) == 1:  # 同等级套装
            synergy_score += 0.05

        # 检查特殊组合模式
        for pattern in self.synergy_patterns:
            if self._matches_synergy_pattern(equipment_set, pattern):
                synergy_score += pattern['bonus']

        return min(synergy_score, 1.0)  # 最高不超过1.0

    def _calculate_pair_compatibility(self, equipment1: Equipment, equipment2: Equipment) -> float:
        """计算两个装备间的兼容性"""
        category1 = equipment1.spec.category
        category2 = equipment2.spec.category

        # 获取兼容性规则
        rule_key = f"{category1.value}_{category2.value}"
        compatibility_rule = self.compatibility_rules.get(rule_key, {'base_score': 0.8})

        base_score = compatibility_rule['base_score']

        # 应用具体规格兼容性检查
        spec_compatibility = self._check_spec_compatibility(equipment1, equipment2)

        return base_score * spec_compatibility

    def _check_spec_compatibility(self, equipment1: Equipment, equipment2: Equipment) -> float:
        """检查规格兼容性"""
        compatibility = 1.0

        # 鱼竿和鱼轮兼容性检查
        if (equipment1.spec.category == EquipmentCategory.FISHING_ROD and
            equipment2.spec.category == EquipmentCategory.FISHING_REEL):

            # 检查鱼竿长度和鱼轮大小匹配
            rod_length = equipment1.spec.specifications.get('length', 0)
            reel_size = equipment2.spec.specifications.get('size', 0)

            if rod_length > 240 and reel_size < 2500:  # 长竿配小轮不合适
                compatibility *= 0.8
            elif rod_length < 180 and reel_size > 4000:  # 短竿配大轮不合适
                compatibility *= 0.8

        # 鱼线和鱼轮兼容性检查
        elif (equipment1.spec.category == EquipmentCategory.FISHING_LINE and
              equipment2.spec.category == EquipmentCategory.FISHING_REEL):

            line_capacity = equipment1.spec.specifications.get('capacity', '')
            reel_capacity = equipment2.spec.specifications.get('line_capacity', '')

            # 简化的容量匹配检查
            if not self._is_line_capacity_compatible(line_capacity, reel_capacity):
                compatibility *= 0.7

        return compatibility

    def _is_line_capacity_compatible(self, line_capacity: str, reel_capacity: str) -> bool:
        """检查鱼线容量兼容性"""
        # 简化的容量匹配逻辑，实际应用中需要更复杂的解析
        return True  # 占位实现

    def _initialize_compatibility_rules(self) -> Dict[str, Dict[str, float]]:
        """初始化兼容性规则"""
        return {
            'fishing_rod_fishing_reel': {'base_score': 0.9},
            'fishing_rod_fishing_line': {'base_score': 0.85},
            'fishing_reel_fishing_line': {'base_score': 0.95},
            'fishing_lure_fishing_line': {'base_score': 0.8},
            # 更多兼容性规则...
        }

    def _initialize_synergy_patterns(self) -> List[Dict[str, Any]]:
        """初始化协同模式"""
        return [
            {
                'name': 'brand_bonus',
                'description': '同品牌套装加成',
                'condition': 'same_brand',
                'bonus': 0.1
            },
            {
                'name': 'level_consistency',
                'description': '同等级套装加成',
                'condition': 'same_level',
                'bonus': 0.05
            },
            # 更多协同模式...
        ]

    def _matches_synergy_pattern(self, equipment_set: Dict[EquipmentCategory, Equipment],
                                pattern: Dict[str, Any]) -> bool:
        """检查是否匹配协同模式"""
        condition = pattern['condition']

        if condition == 'same_brand':
            brands = [equipment.spec.brand for equipment in equipment_set.values()]
            return len(set(brands)) == 1
        elif condition == 'same_level':
            levels = [equipment.spec.level for equipment in equipment_set.values()]
            return len(set(levels)) == 1

        return False
```

## 🔧 服务层实现

### 推荐引擎服务 (RecommendationEngine)
```python
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """推荐引擎"""

    def __init__(self, equipment_matcher: EquipmentMatcher,
                 combo_advisor: ComboAdvisor,
                 budget_optimizer: 'BudgetOptimizer',
                 personalization_engine: 'PersonalizationEngine'):
        self.equipment_matcher = equipment_matcher
        self.combo_advisor = combo_advisor
        self.budget_optimizer = budget_optimizer
        self.personalization_engine = personalization_engine

    def recommend_equipment_set(self, requirement: UserRequirement) -> RecommendationResult:
        """推荐装备套装"""
        try:
            logger.info(f"开始为用户 {requirement.user_id} 生成装备推荐")

            # 1. 预算分配优化
            optimized_budget = self.budget_optimizer.optimize_budget_allocation(
                requirement.budget_allocation, requirement.primary_use
            )

            # 2. 为每个装备类别生成推荐
            primary_recommendations = {}
            alternative_recommendations = {}

            for category in EquipmentCategory:
                if category == EquipmentCategory.ACCESSORIES:
                    continue  # 配件作为可选项处理

                category_budget = optimized_budget.get_category_budget(category)
                if category_budget <= 0:
                    continue

                # 获取主要推荐
                primary_candidates = self.equipment_matcher.find_matching_equipment(
                    requirement, category, category_budget
                )

                if primary_candidates:
                    primary_recommendations[category] = EquipmentRecommendation(
                        equipment=primary_candidates[0],
                        score=self._calculate_recommendation_score(primary_candidates[0], requirement),
                        reasons=self._generate_recommendation_reasons(primary_candidates[0], requirement),
                        alternatives=primary_candidates[1:3] if len(primary_candidates) > 1 else [],
                        price_analysis=self._analyze_price(primary_candidates[0], category_budget)
                    )

                # 获取替代推荐
                if len(primary_candidates) > 3:
                    alternative_recommendations[category] = [
                        EquipmentRecommendation(
                            equipment=candidate,
                            score=self._calculate_recommendation_score(candidate, requirement),
                            reasons=self._generate_recommendation_reasons(candidate, requirement),
                            alternatives=[],
                            price_analysis=self._analyze_price(candidate, category_budget)
                        )
                        for candidate in primary_candidates[3:6]
                    ]

            # 3. 生成主要套装
            primary_set = self._create_equipment_set(primary_recommendations, requirement)

            # 4. 生成替代套装
            alternative_sets = self._generate_alternative_sets(
                alternative_recommendations, requirement
            )

            # 5. 个性化调整
            if requirement.user_id:
                primary_set = self.personalization_engine.personalize_equipment_set(
                    primary_set, requirement.user_id
                )
                alternative_sets = [
                    self.personalization_engine.personalize_equipment_set(
                        alt_set, requirement.user_id
                    )
                    for alt_set in alternative_sets
                ]

            # 6. 生成推荐结果
            result = RecommendationResult(
                user_requirement=requirement,
                primary_set=primary_set,
                alternative_sets=alternative_sets,
                reasoning=self._generate_reasoning(primary_set, requirement),
                confidence_score=self._calculate_confidence_score(primary_set, requirement)
            )

            logger.info(f"成功为用户 {requirement.user_id} 生成装备推荐，置信度: {result.confidence_score:.2f}")
            return result

        except Exception as e:
            logger.error(f"装备推荐生成失败: {e}")
            raise RecommendationError(f"无法生成装备推荐: {e}")

    def recommend_single_equipment(self, requirement: UserRequirement,
                                 category: EquipmentCategory,
                                 budget: float) -> EquipmentRecommendation:
        """推荐单个装备"""
        try:
            candidates = self.equipment_matcher.find_matching_equipment(
                requirement, category, budget
            )

            if not candidates:
                raise RecommendationError(f"未找到符合条件的 {category.value} 装备")

            equipment = candidates[0]

            return EquipmentRecommendation(
                equipment=equipment,
                score=self._calculate_recommendation_score(equipment, requirement),
                reasons=self._generate_recommendation_reasons(equipment, requirement),
                alternatives=candidates[1:3] if len(candidates) > 1 else [],
                price_analysis=self._analyze_price(equipment, budget)
            )

        except Exception as e:
            logger.error(f"单个装备推荐失败: {e}")
            raise RecommendationError(f"无法推荐装备: {e}")

    def _calculate_recommendation_score(self, equipment: Equipment,
                                     requirement: UserRequirement) -> float:
        """计算推荐评分"""
        # 综合考虑性能、价格、用户匹配度等因素
        performance_weight = 0.4
        price_weight = 0.3
        match_weight = 0.2
        popularity_weight = 0.1

        performance_score = equipment.performance_score
        price_score = self._calculate_price_score(equipment, requirement)
        match_score = self._calculate_match_score(equipment, requirement)
        popularity_score = equipment.popularity_score

        total_score = (
            performance_score * performance_weight +
            price_score * price_weight +
            match_score * match_weight +
            popularity_score * popularity_weight
        )

        return min(total_score, 100)

    def _calculate_price_score(self, equipment: Equipment, requirement: UserRequirement) -> float:
        """计算价格评分"""
        # 简化的价格评分逻辑
        user_level_value = {
            EquipmentLevel.BEGINNER: 0.8,
            EquipmentLevel.INTERMEDIATE: 0.6,
            EquipmentLevel.ADVANCED: 0.4,
            EquipmentLevel.PROFESSIONAL: 0.2
        }

        price_ratio = equipment.spec.price / getattr(requirement.budget_allocation, 'total_budget', 1000)
        level_factor = user_level_value.get(requirement.experience_level, 0.5)

        if price_ratio <= 0.5:
            return 100 * (1 - level_factor * 0.3)
        elif price_ratio <= 0.8:
            return 90 * (1 - level_factor * 0.2)
        elif price_ratio <= 1.0:
            return 80 * (1 - level_factor * 0.1)
        else:
            return max(50, 80 - (price_ratio - 1.0) * 100)

    def _calculate_match_score(self, equipment: Equipment, requirement: UserRequirement) -> float:
        """计算匹配度评分"""
        match_score = 80  # 基础分

        # 品牌偏好
        if equipment.spec.brand in requirement.preferred_brands:
            match_score += 15
        elif equipment.spec.brand in requirement.avoided_brands:
            match_score -= 30

        # 经验水平匹配
        if equipment.is_suitable_for_level(requirement.experience_level):
            level_diff = self.combo_advisor._get_level_difference(
                equipment.spec.level, requirement.experience_level
            )
            match_score -= level_diff * 5

        return max(0, min(match_score, 100))

    def _generate_recommendation_reasons(self, equipment: Equipment,
                                      requirement: UserRequirement) -> List[str]:
        """生成推荐理由"""
        reasons = []

        # 性能优势
        if equipment.performance_score >= 90:
            reasons.append(f"性能卓越，评分 {equipment.performance_score}/100")
        elif equipment.performance_score >= 80:
            reasons.append(f"性能优秀，评分 {equipment.performance_score}/100")

        # 价格优势
        avg_price = self._get_category_average_price(equipment.spec.category)
        if equipment.spec.price < avg_price * 0.8:
            reasons.append("价格实惠，性价比高")
        elif equipment.spec.price < avg_price:
            reasons.append("价格合理")

        # 品牌优势
        if equipment.spec.brand in requirement.preferred_brands:
            reasons.append(f"符合品牌偏好 ({equipment.spec.brand})")

        # 用户水平适配
        if equipment.is_suitable_for_level(requirement.experience_level):
            reasons.append(f"适合 {requirement.experience_level.value} 水平使用")

        # 人气优势
        if equipment.popularity_score >= 90:
            reasons.append("广受用户好评")
        elif equipment.review_count >= 100:
            reasons.append(f"已有 {equipment.review_count}+ 用户评价")

        return reasons[:4]  # 最多返回4个理由

    def _analyze_price(self, equipment: Equipment, budget: float) -> Dict[str, float]:
        """分析价格情况"""
        price_ratio = equipment.spec.price / budget
        market_avg = self._get_category_average_price(equipment.spec.category)
        market_ratio = equipment.spec.price / market_avg

        return {
            'absolute_price': equipment.spec.price,
            'budget_ratio': price_ratio,
            'market_ratio': market_ratio,
            'budget_usage': price_ratio * 100,
            'price_position': 'below_market' if market_ratio < 0.9 else 'above_market' if market_ratio > 1.1 else 'market_average'
        }

    def _get_category_average_price(self, category: EquipmentCategory) -> float:
        """获取类别平均价格"""
        # 这里应该从数据库或缓存中获取
        price_ranges = {
            EquipmentCategory.FISHING_ROD: 500,
            EquipmentCategory.FISHING_REEL: 400,
            EquipmentCategory.FISHING_LINE: 50,
            EquipmentCategory.FISHING_LURE: 30,
            EquipmentCategory.FISHING_HOOK: 20,
            EquipmentCategory.ACCESSORIES: 100
        }
        return price_ranges.get(category, 200)

    def _create_equipment_set(self, recommendations: Dict[EquipmentCategory, EquipmentRecommendation],
                            requirement: UserRequirement) -> EquipmentSet:
        """创建装备套装"""
        equipment_dict = {category: rec.equipment for category, rec in recommendations.items()}

        # 计算兼容性
        compatibility_score = self.combo_advisor.analyze_equipment_compatibility(equipment_dict)

        # 计算协同效应
        synergy_score = self.combo_advisor.calculate_synergy_score(equipment_dict)

        # 计算总价格
        total_price = sum(equipment.spec.price for equipment in equipment_dict.values())

        # 计算综合评分
        overall_score = (
            sum(rec.score for rec in recommendations.values()) / len(recommendations) * 0.7 +
            compatibility_score * 100 * 0.2 +
            synergy_score * 100 * 0.1
        )

        return EquipmentSet(
            equipments=recommendations,
            total_price=total_price,
            compatibility_score=compatibility_score,
            synergy_score=synergy_score,
            overall_score=overall_score
        )

    def _generate_alternative_sets(self, alternative_recommendations: Dict[EquipmentCategory, List[EquipmentRecommendation]],
                                 requirement: UserRequirement) -> List[EquipmentSet]:
        """生成替代套装"""
        alternative_sets = []

        # 生成2-3个替代套装
        for i in range(2):
            set_recommendations = {}

            for category, alternatives in alternative_recommendations.items():
                if i < len(alternatives):
                    set_recommendations[category] = alternatives[i]
                else:
                    # 如果没有足够的替代选项，使用主要推荐
                    continue

            if set_recommendations:
                alternative_set = self._create_equipment_set(set_recommendations, requirement)
                alternative_sets.append(alternative_set)

        return alternative_sets

    def _generate_reasoning(self, equipment_set: EquipmentSet, requirement: UserRequirement) -> str:
        """生成推荐理由说明"""
        reasoning_parts = []

        # 总体说明
        reasoning_parts.append(f"基于您的 {requirement.experience_level.value} 水平和 {requirement.primary_use} 需求")

        # 预算说明
        total_budget = requirement.budget_allocation.total_budget
        actual_price = equipment_set.total_price

        if actual_price <= total_budget:
            reasoning_parts.append(f"推荐的装备总价 {actual_price:.0f} 元，在您的预算 {total_budget:.0f} 元范围内")
        else:
            reasoning_parts.append(f"推荐的装备总价 {actual_price:.0f} 元，略超预算 {(actual_price/total_budget-1)*100:.1f}%")

        # 兼容性说明
        if equipment_set.compatibility_score >= 0.9:
            reasoning_parts.append("装备间兼容性极佳，搭配合理")
        elif equipment_set.compatibility_score >= 0.8:
            reasoning_parts.append("装备间兼容性良好，可以正常使用")

        # 性能说明
        avg_performance = sum(rec.equipment.performance_score for rec in equipment_set.equipments.values()) / len(equipment_set.equipments)
        if avg_performance >= 90:
            reasoning_parts.append("整体性能表现卓越")
        elif avg_performance >= 80:
            reasoning_parts.append("整体性能表现优秀")

        return "。".join(reasoning_parts) + "。"

    def _calculate_confidence_score(self, equipment_set: EquipmentSet,
                                  requirement: UserRequirement) -> float:
        """计算推荐置信度"""
        confidence_factors = []

        # 装备覆盖度
        coverage_ratio = len(equipment_set.equipments) / 5  # 假设5个主要类别
        confidence_factors.append(('coverage', coverage_ratio))

        # 兼容性评分
        confidence_factors.append(('compatibility', equipment_set.compatibility_score))

        # 预算匹配度
        budget_ratio = equipment_set.total_price / requirement.budget_allocation.total_budget
        budget_score = 1.0 - abs(budget_ratio - 0.8)  # 理想是使用80%的预算
        confidence_factors.append(('budget', max(budget_score, 0)))

        # 综合评分
        confidence_factors.append(('overall_score', equipment_set.overall_score / 100))

        # 计算加权置信度
        weights = {'coverage': 0.2, 'compatibility': 0.3, 'budget': 0.2, 'overall_score': 0.3}

        confidence = sum(score * weights[factor] for factor, score in confidence_factors)
        return min(confidence * 100, 100)


class RecommendationError(Exception):
    """推荐异常"""
    pass
```

### 预算优化服务 (BudgetOptimizer)
```python
class BudgetOptimizer:
    """预算优化服务"""

    def __init__(self):
        self.allocation_templates = self._initialize_allocation_templates()
        self.min_price_thresholds = self._initialize_min_price_thresholds()

    def optimize_budget_allocation(self, budget_allocation: BudgetAllocation,
                                 primary_use: str) -> BudgetAllocation:
        """优化预算分配"""
        try:
            total_budget = budget_allocation.total_budget

            # 如果用户没有指定具体分配，使用模板
            if not any([budget_allocation.rod_budget, budget_allocation.reel_budget,
                       budget_allocation.line_budget, budget_allocation.lure_budget]):
                return self._apply_allocation_template(total_budget, primary_use)

            # 验证和调整用户指定的分配
            user_allocation = {
                EquipmentCategory.FISHING_ROD: budget_allocation.rod_budget or 0,
                EquipmentCategory.FISHING_REEL: budget_allocation.reel_budget or 0,
                EquipmentCategory.FISHING_LINE: budget_allocation.line_budget or 0,
                EquipmentCategory.FISHING_LURE: budget_allocation.lure_budget or 0,
                EquipmentCategory.ACCESSORIES: budget_allocation.accessory_budget or 0
            }

            # 应用最小价格约束
            adjusted_allocation = self._apply_min_price_constraints(user_allocation)

            # 检查总预算约束
            total_allocated = sum(adjusted_allocation.values())
            if total_allocated > total_budget:
                # 按比例缩减
                scale_factor = total_budget / total_allocated
                for category in adjusted_allocation:
                    adjusted_allocation[category] *= scale_factor

            # 将未分配的预算分配到配件
            remaining_budget = total_budget - sum(adjusted_allocation.values())
            if remaining_budget > 0:
                adjusted_allocation[EquipmentCategory.ACCESSORIES] += remaining_budget

            # 创建优化后的预算分配
            optimized_allocation = BudgetAllocation(
                total_budget=total_budget,
                rod_budget=adjusted_allocation[EquipmentCategory.FISHING_ROD],
                reel_budget=adjusted_allocation[EquipmentCategory.FISHING_REEL],
                line_budget=adjusted_allocation[EquipmentCategory.FISHING_LINE],
                lure_budget=adjusted_allocation[EquipmentCategory.FISHING_LURE],
                accessory_budget=adjusted_allocation[EquipmentCategory.ACCESSORIES]
            )

            return optimized_allocation

        except Exception as e:
            logger.error(f"预算分配优化失败: {e}")
            # 返回默认分配
            return self._apply_allocation_template(total_budget, primary_use)

    def _apply_allocation_template(self, total_budget: float, primary_use: str) -> BudgetAllocation:
        """应用预算分配模板"""
        template_name = self._get_template_name(primary_use)
        template = self.allocation_templates.get(template_name, self.allocation_templates['balanced'])

        return BudgetAllocation(
            total_budget=total_budget,
            rod_budget=total_budget * template['rod'],
            reel_budget=total_budget * template['reel'],
            line_budget=total_budget * template['line'],
            lure_budget=total_budget * template['lure'],
            accessory_budget=total_budget * template['accessories']
        )

    def _get_template_name(self, primary_use: str) -> str:
        """根据用途获取模板名称"""
        use_mapping = {
            '路亚': 'lure_fishing',
            '台钓': 'traditional_fishing',
            '海钓': 'sea_fishing',
            '溪流': 'stream_fishing',
            '黑坑': 'commercial_fishing'
        }
        return use_mapping.get(primary_use, 'balanced')

    def _apply_min_price_constraints(self, allocation: Dict[EquipmentCategory, float]) -> Dict[EquipmentCategory, float]:
        """应用最小价格约束"""
        adjusted_allocation = allocation.copy()

        for category, min_price in self.min_price_thresholds.items():
            if adjusted_allocation[category] > 0 and adjusted_allocation[category] < min_price:
                adjusted_allocation[category] = min_price

        return adjusted_allocation

    def _initialize_allocation_templates(self) -> Dict[str, Dict[str, float]]:
        """初始化分配模板"""
        return {
            'balanced': {
                'rod': 0.35,      # 鱼竿35%
                'reel': 0.30,     # 鱼轮30%
                'line': 0.10,     # 鱼线10%
                'lure': 0.15,     # 拟饵15%
                'accessories': 0.10  # 配件10%
            },
            'lure_fishing': {
                'rod': 0.30,      # 路亚竿
                'reel': 0.25,     # 路亚轮
                'line': 0.15,     # PE线
                'lure': 0.25,     # 路亚拟饵
                'accessories': 0.05
            },
            'traditional_fishing': {
                'rod': 0.25,      # 台钓竿
                'reel': 0.20,     # 渔轮
                'line': 0.15,     # 鱼线
                'lure': 0.10,     # 饵料
                'accessories': 0.30  # 浮漂、支架等
            },
            'sea_fishing': {
                'rod': 0.40,      # 海竿
                'reel': 0.35,     # 大型渔轮
                'line': 0.15,     # 大力马线
                'lure': 0.05,     # 铁板等
                'accessories': 0.05
            },
            'stream_fishing': {
                'rod': 0.35,      # 溪流竿
                'reel': 0.30,     # 小型渔轮
                'line': 0.20,     # 细线
                'lure': 0.10,     # 小拟饵
                'accessories': 0.05
            },
            'commercial_fishing': {
                'rod': 0.20,      # 黑坑竿
                'reel': 0.15,     # 渔轮
                'line': 0.25,     # 鱼线
                'lure': 0.25,     # 饵料
                'accessories': 0.15
            }
        }

    def _initialize_min_price_thresholds(self) -> Dict[EquipmentCategory, float]:
        """初始化最小价格阈值"""
        return {
            EquipmentCategory.FISHING_ROD: 100,     # 鱼竿最低100元
            EquipmentCategory.FISHING_REEL: 80,     # 鱼轮最低80元
            EquipmentCategory.FISHING_LINE: 20,     # 鱼线最低20元
            EquipmentCategory.FISHING_LURE: 10,     # 拟饵最低10元
            EquipmentCategory.ACCESSORIES: 30       # 配件最低30元
        }
```

### 个性化引擎服务 (PersonalizationEngine)
```python
class PersonalizationEngine:
    """个性化引擎"""

    def __init__(self, user_preference_repository: 'UserPreferenceRepository',
                 behavior_analyzer: 'BehaviorAnalyzer'):
        self.user_preference_repository = user_preference_repository
        self.behavior_analyzer = behavior_analyzer
        self.personalization_factors = self._initialize_personalization_factors()

    def personalize_equipment_set(self, equipment_set: EquipmentSet, user_id: str) -> EquipmentSet:
        """个性化装备套装"""
        try:
            # 获取用户偏好
            user_preferences = self.user_preference_repository.get_user_preferences(user_id)

            if not user_preferences:
                return equipment_set  # 没有偏好数据，返回原套装

            # 分析用户行为模式
            behavior_patterns = self.behavior_analyzer.analyze_user_behavior(user_id)

            # 应用个性化调整
            personalized_set = self._apply_personalization(
                equipment_set, user_preferences, behavior_patterns
            )

            return personalized_set

        except Exception as e:
            logger.error(f"装备套装个性化失败: {e}")
            return equipment_set

    def _apply_personalization(self, equipment_set: EquipmentSet,
                             user_preferences: Dict[str, Any],
                             behavior_patterns: Dict[str, Any]) -> EquipmentSet:
        """应用个性化调整"""
        personalized_recommendations = equipment_set.equipments.copy()

        for category, recommendation in equipment_set.equipments.items():
            # 品牌偏好调整
            if 'brand_preferences' in user_preferences:
                brand_adjustment = self._calculate_brand_adjustment(
                    recommendation.equipment, user_preferences['brand_preferences']
                )
                recommendation.score *= brand_adjustment

            # 价格敏感度调整
            if 'price_sensitivity' in user_preferences:
                price_adjustment = self._calculate_price_adjustment(
                    recommendation.equipment, user_preferences['price_sensitivity']
                )
                recommendation.score *= price_adjustment

            # 性能偏好调整
            if 'performance_preference' in user_preferences:
                performance_adjustment = self._calculate_performance_adjustment(
                    recommendation.equipment, user_preferences['performance_preference']
                )
                recommendation.score *= performance_adjustment

            # 更新推荐理由
            recommendation.reasons = self._update_recommendation_reasons(
                recommendation, user_preferences
            )

        # 重新计算套装评分
        total_score = sum(rec.score for rec in personalized_recommendations.values()) / len(personalized_recommendations)
        equipment_set.overall_score = total_score

        return equipment_set

    def _calculate_brand_adjustment(self, equipment: Equipment,
                                  brand_preferences: Dict[str, float]) -> float:
        """计算品牌调整系数"""
        brand = equipment.spec.brand
        base_adjustment = 1.0

        if brand in brand_preferences:
            preference_score = brand_preferences[brand]
            # 偏好评分 0-1，转换为调整系数 0.8-1.2
            adjustment = 0.8 + preference_score * 0.4
            base_adjustment *= adjustment

        return base_adjustment

    def _calculate_price_adjustment(self, equipment: Equipment,
                                  price_sensitivity: Dict[str, float]) -> float:
        """计算价格调整系数"""
        sensitivity_level = price_sensitivity.get('level', 'medium')  # low, medium, high
        preferred_price_range = price_sensitivity.get('preferred_range', {})

        base_adjustment = 1.0

        # 根据敏感度调整
        if sensitivity_level == 'high':
            # 高价格敏感度，便宜装备加分
            if equipment.spec.price < 300:
                base_adjustment *= 1.1
            elif equipment.spec.price > 1000:
                base_adjustment *= 0.9
        elif sensitivity_level == 'low':
            # 低价格敏感度，贵重装备加分
            if equipment.spec.price > 800:
                base_adjustment *= 1.1
            elif equipment.spec.price < 200:
                base_adjustment *= 0.9

        # 根据偏好价格范围调整
        if preferred_price_range:
            min_price = preferred_price_range.get('min', 0)
            max_price = preferred_price_range.get('max', float('inf'))

            if min_price <= equipment.spec.price <= max_price:
                base_adjustment *= 1.05

        return base_adjustment

    def _calculate_performance_adjustment(self, equipment: Equipment,
                                        performance_preference: Dict[str, Any]) -> float:
        """计算性能调整系数"""
        preference_type = performance_preference.get('type', 'balanced')  # performance, value, balanced

        base_adjustment = 1.0

        if preference_type == 'performance':
            # 性能优先，高性能装备加分
            if equipment.performance_score >= 90:
                base_adjustment *= 1.15
            elif equipment.performance_score >= 80:
                base_adjustment *= 1.05
        elif preference_type == 'value':
            # 性价比优先，中等性能装备加分
            if 70 <= equipment.performance_score <= 85:
                base_adjustment *= 1.1
            elif equipment.performance_score > 90:
                base_adjustment *= 0.95  # 过度高性能可能意味着不必要的高价

        return base_adjustment

    def _update_recommendation_reasons(self, recommendation: EquipmentRecommendation,
                                     user_preferences: Dict[str, Any]) -> List[str]:
        """更新推荐理由"""
        reasons = recommendation.reasons.copy()
        equipment = recommendation.equipment

        # 添加个性化理由
        if 'brand_preferences' in user_preferences:
            brand = equipment.spec.brand
            if brand in user_preferences['brand_preferences']:
                preference_score = user_preferences['brand_preferences'][brand]
                if preference_score > 0.8:
                    reasons.append(f"符合您对 {brand} 品牌的强烈偏好")

        if 'price_sensitivity' in user_preferences:
            sensitivity = user_preferences['price_sensitivity']
            if sensitivity.get('level') == 'high' and equipment.spec.price < 300:
                reasons.append("价格实惠，符合您的预算偏好")

        return reasons[:5]  # 最多保留5个理由

    def _initialize_personalization_factors(self) -> Dict[str, float]:
        """初始化个性化因子权重"""
        return {
            'brand_preference': 0.3,
            'price_sensitivity': 0.25,
            'performance_preference': 0.2,
            'behavior_pattern': 0.15,
            'historical_feedback': 0.1
        }
```

## 📊 数据访问层

### 装备数据访问接口 (EquipmentRepository)
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class EquipmentRepository(ABC):
    """装备数据访问接口"""

    @abstractmethod
    def find_by_id(self, equipment_id: str) -> Optional[Equipment]:
        """根据ID查找装备"""
        pass

    @abstractmethod
    def find_by_category(self, category: EquipmentCategory) -> List[Equipment]:
        """根据类别查找装备"""
        pass

    @abstractmethod
    def find_by_category_and_price(self, category: EquipmentCategory,
                                 max_price: float) -> List[Equipment]:
        """根据类别和价格范围查找装备"""
        pass

    @abstractmethod
    def find_by_brand(self, brand: str) -> List[Equipment]:
        """根据品牌查找装备"""
        pass

    @abstractmethod
    def search_equipment(self, keyword: str, filters: Dict[str, Any]) -> List[Equipment]:
        """搜索装备"""
        pass

    @abstractmethod
    def get_popular_equipment(self, category: EquipmentCategory,
                            limit: int = 10) -> List[Equipment]:
        """获取热门装备"""
        pass

    @abstractmethod
    def save_equipment(self, equipment: Equipment) -> bool:
        """保存装备"""
        pass

    @abstractmethod
    def update_equipment(self, equipment: Equipment) -> bool:
        """更新装备"""
        pass

class DatabaseEquipmentRepository(EquipmentRepository):
    """数据库装备访问实现"""

    def __init__(self, database_connection):
        self.db = database_connection

    def find_by_id(self, equipment_id: str) -> Optional[Equipment]:
        """根据ID查找装备"""
        query = "SELECT * FROM equipment WHERE id = ?"
        result = self.db.execute(query, (equipment_id,)).fetchone()

        if result:
            return self._map_row_to_equipment(result)
        return None

    def find_by_category(self, category: EquipmentCategory) -> List[Equipment]:
        """根据类别查找装备"""
        query = "SELECT * FROM equipment WHERE category = ? ORDER BY performance_score DESC"
        results = self.db.execute(query, (category.value,)).fetchall()

        return [self._map_row_to_equipment(row) for row in results]

    def find_by_category_and_price(self, category: EquipmentCategory,
                                 max_price: float) -> List[Equipment]:
        """根据类别和价格范围查找装备"""
        query = """
        SELECT * FROM equipment
        WHERE category = ? AND price <= ?
        ORDER BY performance_score DESC, popularity_score DESC
        """
        results = self.db.execute(query, (category.value, max_price)).fetchall()

        return [self._map_row_to_equipment(row) for row in results]

    def find_by_brand(self, brand: str) -> List[Equipment]:
        """根据品牌查找装备"""
        query = "SELECT * FROM equipment WHERE brand = ? ORDER BY popularity_score DESC"
        results = self.db.execute(query, (brand,)).fetchall()

        return [self._map_row_to_equipment(row) for row in results]

    def search_equipment(self, keyword: str, filters: Dict[str, Any]) -> List[Equipment]:
        """搜索装备"""
        base_query = """
        SELECT * FROM equipment
        WHERE (brand LIKE ? OR model LIKE ? OR specifications LIKE ?)
        """
        params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]

        # 添加过滤条件
        if 'category' in filters:
            base_query += " AND category = ?"
            params.append(filters['category'].value)

        if 'min_price' in filters:
            base_query += " AND price >= ?"
            params.append(filters['min_price'])

        if 'max_price' in filters:
            base_query += " AND price <= ?"
            params.append(filters['max_price'])

        if 'level' in filters:
            base_query += " AND level = ?"
            params.append(filters['level'].value)

        base_query += " ORDER BY performance_score DESC LIMIT 50"

        results = self.db.execute(base_query, params).fetchall()
        return [self._map_row_to_equipment(row) for row in results]

    def get_popular_equipment(self, category: EquipmentCategory,
                            limit: int = 10) -> List[Equipment]:
        """获取热门装备"""
        query = """
        SELECT * FROM equipment
        WHERE category = ? AND availability = 1
        ORDER BY popularity_score DESC, review_count DESC
        LIMIT ?
        """
        results = self.db.execute(query, (category.value, limit)).fetchall()

        return [self._map_row_to_equipment(row) for row in results]

    def save_equipment(self, equipment: Equipment) -> bool:
        """保存装备"""
        try:
            query = """
            INSERT INTO equipment (
                id, brand, model, category, level, price, specifications,
                compatibility, weight, material, warranty_period,
                performance_score, popularity_score, user_rating,
                review_count, availability
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                equipment.id,
                equipment.spec.brand,
                equipment.spec.model,
                equipment.spec.category.value,
                equipment.spec.level.value,
                equipment.spec.price,
                json.dumps(equipment.spec.specifications),
                json.dumps(equipment.spec.compatibility),
                equipment.spec.weight,
                equipment.spec.material,
                equipment.spec.warranty_period,
                equipment.performance_score,
                equipment.popularity_score,
                equipment.user_rating,
                equipment.review_count,
                equipment.availability
            )

            self.db.execute(query, params)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"保存装备失败: {e}")
            return False

    def update_equipment(self, equipment: Equipment) -> bool:
        """更新装备"""
        try:
            query = """
            UPDATE equipment SET
                brand = ?, model = ?, category = ?, level = ?, price = ?,
                specifications = ?, compatibility = ?, weight = ?, material = ?,
                warranty_period = ?, performance_score = ?, popularity_score = ?,
                user_rating = ?, review_count = ?, availability = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            """

            params = (
                equipment.spec.brand,
                equipment.spec.model,
                equipment.spec.category.value,
                equipment.spec.level.value,
                equipment.spec.price,
                json.dumps(equipment.spec.specifications),
                json.dumps(equipment.spec.compatibility),
                equipment.spec.weight,
                equipment.spec.material,
                equipment.spec.warranty_period,
                equipment.performance_score,
                equipment.popularity_score,
                equipment.user_rating,
                equipment.review_count,
                equipment.availability,
                equipment.id
            )

            self.db.execute(query, params)
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"更新装备失败: {e}")
            return False

    def _map_row_to_equipment(self, row) -> Equipment:
        """将数据库行映射为装备对象"""
        spec = EquipmentSpec(
            brand=row['brand'],
            model=row['model'],
            category=EquipmentCategory(row['category']),
            level=EquipmentLevel(row['level']),
            price=row['price'],
            specifications=json.loads(row['specifications']),
            compatibility=json.loads(row['compatibility']),
            weight=row['weight'],
            material=row['material'],
            warranty_period=row['warranty_period']
        )

        return Equipment(
            id=row['id'],
            spec=spec,
            performance_score=row['performance_score'],
            popularity_score=row['popularity_score'],
            user_rating=row['user_rating'],
            review_count=row['review_count'],
            availability=bool(row['availability']),
            last_updated=row['last_updated']
        )
```

### 用户偏好数据访问 (UserPreferenceRepository)
```python
class UserPreferenceRepository(ABC):
    """用户偏好数据访问接口"""

    @abstractmethod
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好"""
        pass

    @abstractmethod
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """保存用户偏好"""
        pass

    @abstractmethod
    def update_user_preferences(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新用户偏好"""
        pass

    @abstractmethod
    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户历史记录"""
        pass

class DatabaseUserPreferenceRepository(UserPreferenceRepository):
    """数据库用户偏好访问实现"""

    def __init__(self, database_connection):
        self.db = database_connection

    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户偏好"""
        query = "SELECT preferences FROM user_preferences WHERE user_id = ?"
        result = self.db.execute(query, (user_id,)).fetchone()

        if result:
            return json.loads(result['preferences'])
        return None

    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """保存用户偏好"""
        try:
            query = """
            INSERT OR REPLACE INTO user_preferences (user_id, preferences, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """

            self.db.execute(query, (user_id, json.dumps(preferences)))
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}")
            return False

    def update_user_preferences(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新用户偏好"""
        try:
            current_prefs = self.get_user_preferences(user_id) or {}
            current_prefs.update(updates)

            return self.save_user_preferences(user_id, current_prefs)

        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
            return False

    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户历史记录"""
        query = """
        SELECT action, details, created_at FROM user_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """

        results = self.db.execute(query, (user_id, limit)).fetchall()

        return [
            {
                'action': row['action'],
                'details': json.loads(row['details']),
                'created_at': row['created_at']
            }
            for row in results
        ]
```

## 🛠️ LangChain工具集成

### 装备推荐工具函数
```python
from langchain_core.tools import tool
from typing import Dict, Any, List, Optional

@tool
def recommend_equipment_set(
    experience_level: str,
    total_budget: float,
    primary_use: str,
    target_fish: Optional[List[str]] = None,
    preferred_brands: Optional[List[str]] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """
    推荐完整的钓鱼装备套装

    Args:
        experience_level: 经验水平 (beginner/intermediate/advanced/professional)
        total_budget: 总预算(元)
        primary_use: 主要用途 (路亚/台钓/海钓/溪流/黑坑)
        target_fish: 目标鱼种列表
        preferred_brands: 偏好品牌列表
        location: 钓鱼地点

    Returns:
        Dict: 包含推荐装备套装、价格分析、推荐理由等信息
    """
    try:
        # 构建用户需求
        requirement = UserRequirement(
            user_id="temp_user",
            experience_level=EquipmentLevel(experience_level),
            primary_use=primary_use,
            fishing_scenarios=[
                FishingScenario(
                    location=location or "未知地点",
                    target_fish=target_fish or [],
                    season="当前季节",
                    weather_condition="未知",
                    water_type="未知"
                )
            ],
            budget_allocation=BudgetAllocation(total_budget=total_budget),
            preferred_brands=preferred_brands or []
        )

        # 获取推荐服务
        service_container = get_service_container()
        recommendation_engine = service_container.get_service('recommendation_engine')

        # 生成推荐
        result = recommendation_engine.recommend_equipment_set(requirement)

        # 格式化返回结果
        return {
            "success": True,
            "total_budget": total_budget,
            "actual_price": result.primary_set.total_price,
            "budget_usage": f"{result.primary_set.total_price/total_budget*100:.1f}%",
            "confidence_score": f"{result.confidence_score:.1f}/100",
            "compatibility_score": f"{result.primary_set.compatibility_score*100:.1f}%",
            "overall_score": f"{result.primary_set.overall_score:.1f}/100",
            "equipment_recommendations": {
                category.value: {
                    "brand": rec.equipment.spec.brand,
                    "model": rec.equipment.spec.model,
                    "price": rec.equipment.spec.price,
                    "score": f"{rec.score:.1f}/100",
                    "reasons": rec.reasons,
                    "price_analysis": rec.price_analysis
                }
                for category, rec in result.primary_set.equipments.items()
            },
            "reasoning": result.reasoning,
            "alternative_count": len(result.alternative_sets)
        }

    except Exception as e:
        logger.error(f"装备套装推荐失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "很抱歉，无法生成装备推荐，请检查输入参数"
        }

@tool
def recommend_single_equipment(
    category: str,
    experience_level: str,
    budget: float,
    primary_use: str,
    preferred_brands: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    推荐单个钓鱼装备

    Args:
        category: 装备类别 (fishing_rod/fishing_reel/fishing_line/fishing_lure/fishing_hook/accessories)
        experience_level: 经验水平 (beginner/intermediate/advanced/professional)
        budget: 预算(元)
        primary_use: 主要用途
        preferred_brands: 偏好品牌列表

    Returns:
        Dict: 包含推荐装备详细信息
    """
    try:
        # 构建用户需求
        requirement = UserRequirement(
            user_id="temp_user",
            experience_level=EquipmentLevel(experience_level),
            primary_use=primary_use,
            fishing_scenarios=[],
            budget_allocation=BudgetAllocation(total_budget=budget * 5),  # 假设总预算
            preferred_brands=preferred_brands or []
        )

        # 获取推荐服务
        service_container = get_service_container()
        recommendation_engine = service_container.get_service('recommendation_engine')

        # 生成推荐
        result = recommendation_engine.recommend_single_equipment(
            requirement, EquipmentCategory(category), budget
        )

        return {
            "success": True,
            "category": category,
            "recommended_equipment": {
                "brand": result.equipment.spec.brand,
                "model": result.equipment.spec.model,
                "price": result.equipment.spec.price,
                "level": result.equipment.spec.level.value,
                "performance_score": f"{result.equipment.performance_score}/100",
                "user_rating": f"{result.equipment.user_rating}/5.0",
                "review_count": result.equipment.review_count,
                "recommendation_score": f"{result.score:.1f}/100",
                "reasons": result.reasons,
                "price_analysis": result.price_analysis,
                "specifications": result.equipment.spec.specifications
            },
            "alternatives": [
                {
                    "brand": alt.equipment.spec.brand,
                    "model": alt.equipment.spec.model,
                    "price": alt.equipment.spec.price,
                    "score": f"{alt.score:.1f}/100"
                }
                for alt in result.alternatives
            ]
        }

    except Exception as e:
        logger.error(f"单个装备推荐失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "很抱歉，无法推荐装备，请检查输入参数"
        }

@tool
def analyze_equipment_combo(
    equipment_list: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    分析装备搭配的兼容性和协同效应

    Args:
        equipment_list: 装备列表，每个装备包含brand和model

    Returns:
        Dict: 包含兼容性分析、协同效应、优化建议等
    """
    try:
        # 获取装备信息
        service_container = get_service_container()
        equipment_repository = service_container.get_service('equipment_repository')
        combo_advisor = service_container.get_service('combo_advisor')

        equipment_dict = {}
        for equipment_info in equipment_list:
            brand = equipment_info.get('brand')
            model = equipment_info.get('model')

            # 查找装备
            equipments = equipment_repository.search_equipment(
                f"{brand} {model}", {'limit': 1}
            )

            if equipments:
                equipment = equipments[0]
                equipment_dict[equipment.spec.category] = equipment

        if len(equipment_dict) < 2:
            return {
                "success": False,
                "message": "需要至少2个装备才能进行搭配分析"
            }

        # 分析兼容性
        compatibility_score = combo_advisor.analyze_equipment_compatibility(equipment_dict)

        # 计算协同效应
        synergy_score = combo_advisor.calculate_synergy_score(equipment_dict)

        # 生成优化建议
        suggestions = combo_advisor.generate_combo_suggestions(equipment_dict)

        return {
            "success": True,
            "equipment_count": len(equipment_dict),
            "compatibility_score": f"{compatibility_score*100:.1f}%",
            "synergy_score": f"{synergy_score*100:.1f}%",
            "overall_combo_score": f"{(compatibility_score + synergy_score) * 50:.1f}%",
            "compatibility_analysis": {
                "level": "excellent" if compatibility_score >= 0.9 else "good" if compatibility_score >= 0.8 else "fair",
                "description": combo_advisor._get_compatibility_description(compatibility_score)
            },
            "synergy_analysis": {
                "level": "high" if synergy_score >= 0.9 else "medium" if synergy_score >= 0.8 else "low",
                "description": combo_advisor._get_synergy_description(synergy_score)
            },
            "suggestions": suggestions,
            "equipments": {
                category.value: {
                    "brand": equipment.spec.brand,
                    "model": equipment.spec.model,
                    "level": equipment.spec.level.value
                }
                for category, equipment in equipment_dict.items()
            }
        }

    except Exception as e:
        logger.error(f"装备搭配分析失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "很抱歉，无法分析装备搭配"
        }

@tool
def optimize_budget_allocation(
    total_budget: float,
    primary_use: str,
    custom_allocation: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    优化装备预算分配

    Args:
        total_budget: 总预算(元)
        primary_use: 主要用途 (路亚/台钓/海钓/溪流/黑坑)
        custom_allocation: 自定义分配比例 (可选)

    Returns:
        Dict: 包含优化后的预算分配建议
    """
    try:
        # 获取预算优化服务
        service_container = get_service_container()
        budget_optimizer = service_container.get_service('budget_optimizer')

        if custom_allocation:
            # 使用自定义分配
            budget_allocation = BudgetAllocation(
                total_budget=total_budget,
                rod_budget=custom_allocation.get('fishing_rod', 0),
                reel_budget=custom_allocation.get('fishing_reel', 0),
                line_budget=custom_allocation.get('fishing_line', 0),
                lure_budget=custom_allocation.get('fishing_lure', 0),
                accessory_budget=custom_allocation.get('accessories', 0)
            )
        else:
            # 使用默认分配
            budget_allocation = BudgetAllocation(total_budget=total_budget)

        # 优化预算分配
        optimized_allocation = budget_optimizer.optimize_budget_allocation(
            budget_allocation, primary_use
        )

        # 计算分配比例
        allocations = {
            "鱼竿": {
                "amount": optimized_allocation.rod_budget,
                "percentage": f"{optimized_allocation.rod_budget/total_budget*100:.1f}%",
                "description": "钓竿核心装备"
            },
            "鱼轮": {
                "amount": optimized_allocation.reel_budget,
                "percentage": f"{optimized_allocation.reel_budget/total_budget*100:.1f}%",
                "description": "收线装置"
            },
            "鱼线": {
                "amount": optimized_allocation.line_budget,
                "percentage": f"{optimized_allocation.line_budget/total_budget*100:.1f}%",
                "description": "连接装备和鱼"
            },
            "拟饵/饵料": {
                "amount": optimized_allocation.lure_budget,
                "percentage": f"{optimized_allocation.lure_budget/total_budget*100:.1f}%",
                "description": "吸引鱼类的装备"
            },
            "配件": {
                "amount": optimized_allocation.accessory_budget,
                "percentage": f"{optimized_allocation.accessory_budget/total_budget*100:.1f}%",
                "description": "辅助装备和工具"
            }
        }

        return {
            "success": True,
            "total_budget": total_budget,
            "primary_use": primary_use,
            "allocation_template": "自定义" if custom_allocation else "系统推荐",
            "allocations": allocations,
            "total_allocated": sum([
                optimized_allocation.rod_budget,
                optimized_allocation.reel_budget,
                optimized_allocation.line_budget,
                optimized_allocation.lure_budget,
                optimized_allocation.accessory_budget
            ]),
            "optimization_notes": [
                "预算分配基于您的钓鱼用途进行优化",
                "考虑了装备间的重要性和平衡性",
                "确保核心装备获得足够预算支持"
            ]
        }

    except Exception as e:
        logger.error(f"预算分配优化失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "很抱歉，无法优化预算分配"
        }

def get_service_container():
    """获取服务容器"""
    # 这里应该从基础设施层获取服务容器
    # 简化实现
    from shared.infrastructure.service_manager import get_service_manager
    return get_service_manager()
```

## 🎯 开发实施指南

### 开发优先级和里程碑

#### 第一阶段：核心推荐引擎（2周）
**目标**：建立基础的装备推荐能力

**Week 1: 领域模型和数据访问**
- [ ] 实现Equipment、UserRequirement等核心领域模型
- [ ] 建立EquipmentRepository数据访问层
- [ ] 创建基础数据库表结构和测试数据
- [ ] 实现装备查询和过滤功能

**Week 2: 推荐算法实现**
- [ ] 实现EquipmentMatcher装备匹配服务
- [ ] 开发基础的推荐评分算法
- [ ] 实现单装备推荐功能
- [ ] 创建单元测试和集成测试

#### 第二阶段：套装推荐系统（2周）
**目标**：实现完整的装备套装推荐能力

**Week 3: 搭配分析系统**
- [ ] 实现ComboAdvisor搭配顾问服务
- [ ] 开发装备兼容性分析算法
- [ ] 实现协同效应评分系统
- [ ] 建立搭配规则库

**Week 4: 套装推荐引擎**
- [ ] 实现RecommendationEngine推荐引擎
- [ ] 开发套装生成和优化算法
- [ ] 实现预算优化服务
- [ ] 创建替代套装生成逻辑

#### 第三阶段：个性化和集成（1-2周）
**目标**：实现个性化推荐和LangChain集成

**Week 5: 个性化推荐**
- [ ] 实现PersonalizationEngine个性化引擎
- [ ] 开发用户偏好分析功能
- [ ] 实现行为模式识别
- [ ] 建立用户反馈学习机制

**Week 6: LangChain工具集成**
- [ ] 开发LangChain工具函数
- [ ] 实现工具函数的错误处理
- [ ] 创建API接口和文档
- [ ] 进行端到端测试

### 技术实施要点

#### 1. 数据模型设计
- **规范化设计**: 避免数据冗余，确保数据一致性
- **索引优化**: 为常用查询字段建立索引
- **JSON存储**: 适合存储规格参数等非结构化数据
- **版本控制**: 支持装备规格的历史版本管理

#### 2. 推荐算法优化
- **多因子评分**: 综合考虑性能、价格、适配性等因素
- **权重调优**: 根据用户反馈调整评分权重
- **缓存策略**: 缓存热门装备和推荐结果
- **性能监控**: 监控推荐算法的准确性和响应时间

#### 3. 个性化系统
- **用户画像**: 基于历史行为构建用户画像
- **偏好学习**: 从用户反馈中学习偏好模式
- **隐私保护**: 确保用户数据的隐私和安全
- **实时更新**: 支持用户偏好的实时更新

#### 4. 系统集成
- **依赖注入**: 使用依赖注入管理服务依赖
- **接口标准化**: 定义清晰的服务接口
- **错误处理**: 实现优雅的错误处理和恢复
- **监控日志**: 完善的日志记录和性能监控

### 测试策略

#### 单元测试
```python
import pytest
from unittest.mock import Mock, patch

class TestEquipmentMatcher:
    """装备匹配服务测试"""

    def setup_method(self):
        self.mock_repository = Mock(spec=EquipmentRepository)
        self.matcher = EquipmentMatcher(self.mock_repository)

    def test_find_matching_equipment_basic(self):
        """测试基础装备匹配"""
        # 准备测试数据
        requirement = UserRequirement(
            user_id="test_user",
            experience_level=EquipmentLevel.BEGINNER,
            primary_use="路亚",
            fishing_scenarios=[],
            budget_allocation=BudgetAllocation(total_budget=1000)
        )

        mock_equipment = Equipment(
            id="test_rod",
            spec=EquipmentSpec(
                brand="TestBrand",
                model="TestModel",
                category=EquipmentCategory.FISHING_ROD,
                level=EquipmentLevel.BEGINNER,
                price=500,
                specifications={},
                compatibility=[]
            ),
            performance_score=85,
            popularity_score=80,
            user_rating=4.2,
            review_count=100,
            availability=True
        )

        self.mock_repository.find_by_category_and_price.return_value = [mock_equipment]

        # 执行测试
        result = self.matcher.find_matching_equipment(
            requirement, EquipmentCategory.FISHING_ROD, 600
        )

        # 验证结果
        assert len(result) == 1
        assert result[0].id == "test_rod"
        self.mock_repository.find_by_category_and_price.assert_called_once()

    def test_calculate_match_score(self):
        """测试匹配评分计算"""
        equipment = Equipment(
            id="test_rod",
            spec=EquipmentSpec(
                brand="TestBrand",
                model="TestModel",
                category=EquipmentCategory.FISHING_ROD,
                level=EquipmentLevel.BEGINNER,
                price=500,
                specifications={},
                compatibility=[]
            ),
            performance_score=85,
            popularity_score=80,
            user_rating=4.2,
            review_count=100,
            availability=True
        )

        requirement = UserRequirement(
            user_id="test_user",
            experience_level=EquipmentLevel.BEGINNER,
            primary_use="路亚",
            fishing_scenarios=[],
            budget_allocation=BudgetAllocation(total_budget=1000),
            preferred_brands=["TestBrand"]
        )

        score = self.matcher._calculate_match_score(equipment, requirement, 600)

        assert 0 <= score <= 100
        assert score > 50  # 应该有不错的匹配度

class TestRecommendationEngine:
    """推荐引擎测试"""

    def setup_method(self):
        self.mock_matcher = Mock(spec=EquipmentMatcher)
        self.mock_advisor = Mock(spec=ComboAdvisor)
        self.mock_optimizer = Mock(spec=BudgetOptimizer)
        self.mock_personalization = Mock(spec=PersonalizationEngine)

        self.engine = RecommendationEngine(
            self.mock_matcher,
            self.mock_advisor,
            self.mock_optimizer,
            self.mock_personalization
        )

    @patch('equipment_recommendation_system.logger')
    def test_recommend_equipment_set_success(self, mock_logger):
        """测试成功推荐装备套装"""
        # 准备测试数据
        requirement = UserRequirement(
            user_id="test_user",
            experience_level=EquipmentLevel.BEGINNER,
            primary_use="路亚",
            fishing_scenarios=[],
            budget_allocation=BudgetAllocation(total_budget=1000)
        )

        # 设置mock返回值
        mock_equipment = Equipment(
            id="test_rod",
            spec=EquipmentSpec(
                brand="TestBrand",
                model="TestModel",
                category=EquipmentCategory.FISHING_ROD,
                level=EquipmentLevel.BEGINNER,
                price=500,
                specifications={},
                compatibility=[]
            ),
            performance_score=85,
            popularity_score=80,
            user_rating=4.2,
            review_count=100,
            availability=True
        )

        self.mock_optimizer.optimize_budget_allocation.return_value = requirement.budget_allocation
        self.mock_matcher.find_matching_equipment.return_value = [mock_equipment]
        self.mock_advisor.analyze_equipment_compatibility.return_value = 0.9
        self.mock_advisor.calculate_synergy_score.return_value = 0.85

        # 执行测试
        result = self.engine.recommend_equipment_set(requirement)

        # 验证结果
        assert result is not None
        assert result.user_requirement == requirement
        assert len(result.primary_set.equipments) > 0
        assert result.confidence_score > 0
```

#### 集成测试
```python
class TestEquipmentRecommendationIntegration:
    """装备推荐系统集成测试"""

    def setup_method(self):
        # 使用测试数据库
        self.test_db = create_test_database()
        self.setup_test_data()

        # 创建真实的服务实例
        self.equipment_repository = DatabaseEquipmentRepository(self.test_db)
        self.matcher = EquipmentMatcher(self.equipment_repository)
        self.advisor = ComboAdvisor()
        self.optimizer = BudgetOptimizer()
        self.personalization = PersonalizationEngine(
            Mock(), Mock()  # 简化个性化依赖
        )

        self.engine = RecommendationEngine(
            self.matcher, self.advisor, self.optimizer, self.personalization
        )

    def test_full_recommendation_workflow(self):
        """测试完整的推荐工作流"""
        # 创建真实用户需求
        requirement = UserRequirement(
            user_id="integration_test_user",
            experience_level=EquipmentLevel.INTERMEDIATE,
            primary_use="路亚",
            fishing_scenarios=[
                FishingScenario(
                    location="杭州",
                    target_fish=["鲈鱼"],
                    season="春季",
                    weather_condition="晴天",
                    water_type="湖泊"
                )
            ],
            budget_allocation=BudgetAllocation(total_budget=2000),
            preferred_brands=["达亿瓦", "禧玛诺"]
        )

        # 执行推荐
        result = self.engine.recommend_equipment_set(requirement)

        # 验证结果
        assert result is not None
        assert result.primary_set.total_price <= 2500  # 允许20%预算超支
        assert result.confidence_score >= 60
        assert len(result.primary_set.equipments) >= 3  # 至少竿、轮、线

        # 验证装备质量
        for category, recommendation in result.primary_set.equipments.items():
            assert recommendation.equipment.availability
            assert recommendation.equipment.performance_score >= 70
            assert recommendation.score >= 60
```

### 部署和运维

#### 1. 性能优化
- **数据库优化**: 建立合适的索引，优化查询语句
- **缓存策略**: Redis缓存热门装备和推荐结果
- **异步处理**: 非实时的推荐计算使用异步任务
- **负载均衡**: 多实例部署，分担推荐计算负载

#### 2. 监控和日志
- **性能监控**: 监控推荐响应时间和准确率
- **业务监控**: 监控推荐转化率和用户满意度
- **错误日志**: 详细的错误记录和告警机制
- **用户行为**: 记录用户对推荐结果的反馈

#### 3. 数据管理
- **数据更新**: 定期更新装备信息和价格数据
- **数据质量**: 建立数据质量检查和清洗机制
- **备份策略**: 定期备份推荐数据和用户偏好
- **数据隐私**: 保护用户数据，符合隐私法规

---

## 📝 开发总结

装备推荐系统是智能钓鱼生态系统的核心模块，通过智能化的推荐算法和个性化服务，为用户提供专业、精准的装备推荐。系统采用模块化设计，具备良好的扩展性和维护性。

### 核心能力
- **智能推荐**: 基于多维度分析的精准装备推荐
- **搭配分析**: 专业的装备兼容性和协同效应分析
- **预算优化**: 科学的预算分配和成本控制
- **个性化服务**: 基于用户行为的个性化推荐

### 技术特色
- **领域驱动设计**: 清晰的领域模型和业务逻辑
- **依赖注入**: 松耦合的服务架构
- **算法优化**: 多因子评分和权重调优机制
- **LangChain集成**: 无缝集成到智能体系统

该系统为钓鱼爱好者提供专业级的装备推荐服务，显著提升用户体验和购买决策质量。