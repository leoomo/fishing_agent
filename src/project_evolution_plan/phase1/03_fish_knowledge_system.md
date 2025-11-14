# 鱼类知识系统开发指南

## 📋 概述

鱼类知识系统是智能钓鱼生态系统的核心基础模块，提供专业的鱼类行为学知识和钓鱼策略指导。本文档详细描述鱼类知识系统的设计、实现和开发指南。

## 🎯 模块目标

### 核心功能
- **鱼种习性分析**: 提供20+主要淡水鱼种的详细习性信息
- **季节性策略**: 四季钓鱼策略和应对方案
- **天气应对指导**: 不同天气条件下的钓鱼策略
- **地域性模式**: 不同地区的钓鱼特点和建议

### 用户价值
- 解决"钓什么鱼"的核心问题
- 提供专业的钓鱼知识指导
- 帮助用户理解鱼类行为规律
- 建立系统性的钓鱼知识体系

## 🏗️ 系统架构

### 目录结构
```
fish_knowledge/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── fish_species.py          # 鱼种领域模型
│   ├── behavior_patterns.py     # 行为模式模型
│   ├── strategies.py            # 策略模型
│   └── weather_responses.py      # 天气响应模型
├── services/
│   ├── __init__.py
│   ├── fish_species_service.py  # 鱼种服务
│   ├── strategy_service.py      # 策略服务
│   ├── pattern_matching_service.py # 模式匹配服务
│   └── weather_analysis_service.py # 天气分析服务
├── repositories/
│   ├── __init__.py
│   ├── fish_repository.py       # 鱼种数据访问
│   ├── strategy_repository.py   # 策略数据访问
│   └── pattern_repository.py    # 模式数据访问
├── tools/
│   ├── __init__.py
│   ├── fish_species_analyzer.py # 鱼种分析工具
│   ├── strategy_advisor.py      # 策略建议工具
│   ├── seasonal_planner.py      # 季节规划工具
│   └── weather_advisor.py       # 天气建议工具
└── data/
    ├── fish_knowledge.json      # 鱼种知识数据
    ├── seasonal_patterns.json   # 季节模式数据
    ├── regional_data.json       # 地域数据
    └── weather_responses.json   # 天气应对数据
```

## 🔧 核心组件设计

### 1. 领域模型

#### 鱼种模型
```python
# fish_knowledge/domain/fish_species.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class HabitatType(Enum):
    """栖息地类型"""
    SHALLOW_WATER = "浅水区"
    DEEP_WATER = "深水区"
    SURFACE = "表层"
    MIDDLE_LAYER = "中层"
    BOTTOM = "底层"
    STRUCTURED_AREA = "结构区"

class FeedingHabits(Enum):
    """食性类型"""
    CARNIVOROUS = "肉食性"
    HERBIVOROUS = "草食性"
    OMNIVOROUS = "杂食性"
    PLANKTON_FEEDER = "浮游生物食性"

class ActivityPattern(Enum):
    """活动模式"""
    DIURNAL = "日间活动"
    NOCTURNAL = "夜行性"
    CREPUSCULAR = "晨昏活动"
    CONTINUOUS = "持续活动"

@dataclass
class TemperatureRange:
    """温度范围"""
    optimal_min: float
    optimal_max: float
    tolerance_min: float
    tolerance_max: float

@dataclass
class FishingTechnique:
    """钓鱼技术"""
    name: str
    description: str
    difficulty_level: int  # 1-5
    equipment_required: List[str]

@dataclass
class SeasonalPattern:
    """季节模式"""
    spring: Dict[str, Any]
    summer: Dict[str, Any]
    autumn: Dict[str, Any]
    winter: Dict[str, Any]

@dataclass
class BehaviorPatterns:
    """行为模式"""
    activity_pattern: ActivityPattern
    schooling_behavior: str  # 群游性
    territorial_behavior: str  # 领地性
    reproduction_behavior: str  # 繁殖行为

@dataclass
class FishSpecies:
    """鱼种信息模型"""
    # 基本信息
    name: str
    scientific_name: str
    family: str
    order: str
    common_names: List[str]

    # 栖息信息
    habitat_preference: HabitatType
    distribution: str
    water_type_preference: List[str]

    # 行为特征
    feeding_habits: FeedingHabits
    behavior_patterns: BehaviorPatterns
    seasonal_patterns: SeasonalPattern

    # 环境适应性
    temperature_range: TemperatureRange
    oxygen_requirement: Dict[str, float]
    ph_tolerance: Dict[str, float]

    # 钓鱼相关信息
    preferred_baits: List[str]
    fishing_techniques: List[FishingTechnique]
    best_fishing_times: List[str]
    fishing_difficulty: int  # 1-5

    # 保护状态
    conservation_status: str
    fishing_regulations: Dict[str, Any]

    # 元数据
    data_source: str
    last_updated: str
    reliability_score: float  # 0-1
```

#### 策略模型
```python
# fish_knowledge/domain/strategies.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class StrategyType(Enum):
    """策略类型"""
    SEASONAL = "季节策略"
    WEATHER = "天气策略"
    LOCATION = "地点策略"
    EQUIPMENT = "装备策略"
    TECHNIQUE = "技术策略"

class FishingTimeSlot(Enum):
    """钓鱼时段"""
    EARLY_MORNING = "清晨"
    MORNING = "上午"
    NOON = "中午"
    AFTERNOON = "下午"
    EVENING = "傍晚"
    NIGHT = "夜间"

@dataclass
class TimeSlot:
    """时间段"""
    start_hour: int
    end_hour: int
    description: str
    fishing_quality: int  # 1-10
    recommended_techniques: List[str]

@dataclass
class LocationStrategy:
    """地点策略"""
    location_type: str
    recommended_spots: List[str]
    avoiding_spots: List[str]
    environmental_factors: Dict[str, Any]

@dataclass
class EquipmentRecommendation:
    """装备建议"""
    rod_recommendations: List[Dict[str, Any]]
    lure_recommendations: List[Dict[str, Any]]
    essential_accessories: List[str]

@dataclass
class FishingStrategy:
    """钓鱼策略"""
    strategy_type: StrategyType
    target_fish: Optional[str]
    location: str
    time_slots: List[TimeSlot]
    location_strategy: LocationStrategy
    equipment_recommendations: EquipmentRecommendation
    weather_conditions: Dict[str, Any]
    success_tips: List[str]
    risk_factors: List[str]
    expected_catch_rate: float  # 0-1
```

#### 天气响应模型
```python
# fish_knowledge/domain/weather_responses.py
from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum

class WeatherFactor(Enum):
    """天气因子"""
    TEMPERATURE = "温度"
    PRESSURE = "气压"
    WIND = "风力"
    HUMIDITY = "湿度"
    RAINFALL = "降雨"
    CLOUD_COVER = "云量"

class ImpactLevel(Enum):
    """影响程度"""
    POSITIVE = "正面影响"
    NEGATIVE = "负面影响"
    NEUTRAL = "中性影响"
    CRITICAL_POSITIVE = "重大正面影响"
    CRITICAL_NEGATIVE = "重大负面影响"

@dataclass
class WeatherImpact:
    """天气影响"""
    factor: WeatherFactor
    impact_level: ImpactLevel
    score_change: float  # -10 到 +10
    description: str
    recommendations: List[str]

@dataclass
class WeatherResponse:
    """天气响应"""
    weather_condition: Dict[str, Any]
    overall_score: float  # 0-100
    fishing_quality: str  # 优秀、良好、一般、较差、差
    impacts: List[WeatherImpact]
    recommended_actions: List[str]
    risk_warnings: List[str]
    optimal_conditions: Dict[str, Any]
```

### 2. 服务层设计

#### 鱼种服务
```python
# fish_knowledge/services/fish_species_service.py
from typing import Optional, List, Dict, Any
from ..domain.fish_species import FishSpecies
from ..repositories.fish_repository import IFishRepository
from shared.infrastructure.service_manager import service_manager
from shared.utils.logging import logger

class FishSpeciesService:
    """鱼种服务"""

    def __init__(self,
                 fish_repository: IFishRepository,
                 cache,
                 logger):
        self.fish_repository = fish_repository
        self.cache = cache
        self.logger = logger

    def get_fish_species_info(self, fish_name: str) -> Optional[Dict[str, Any]]:
        """获取鱼种详细信息"""
        try:
            self.logger.info(f"查询鱼种信息: {fish_name}")

            # 缓存检查
            cache_key = f"fish_info:{fish_name}"
            cached_info = self.cache.get(cache_key)
            if cached_info:
                return cached_info

            # 数据库查询
            fish_species = self.fish_repository.get_by_name(fish_name)
            if not fish_species:
                self.logger.warning(f"未找到鱼种信息: {fish_name}")
                return None

            # 转换为字典格式
            result = self._convert_to_dict(fish_species)

            # 缓存结果
            self.cache.set(cache_key, result, ttl=3600)

            return result

        except Exception as e:
            self.logger.error(f"获取鱼种信息失败: {e}")
            return None

    def search_fish_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据条件搜索鱼种"""
        try:
            self.logger.info(f"根据条件搜索鱼种: {criteria}")

            # 检查缓存
            cache_key = f"fish_search:{hash(str(criteria))}"
            cached_results = self.cache.get(cache_key)
            if cached_results:
                return cached_results

            # 数据库搜索
            fish_list = self.fish_repository.search_by_criteria(criteria)

            # 转换为字典格式
            results = [self._convert_to_dict(fish) for fish in fish_list]

            # 缓存结果
            self.cache.set(cache_key, results, ttl=1800)

            return results

        except Exception as e:
            self.logger.error(f"搜索鱼种失败: {e}")
            return []

    def get_fish_by_family(self, family: str) -> List[Dict[str, Any]]:
        """根据科属获取鱼种"""
        return self.search_fish_by_criteria({"family": family})

    def get_fish_by_habitat(self, habitat: str) -> List[Dict[str, Any]]:
        """根据栖息地获取鱼种"""
        return self.search_fish_by_criteria({"habitat": habitat})

    def get_fish_by_feeding_habits(self, feeding_habits: str) -> List[Dict[str, Any]]:
        """根据食性获取鱼种"""
        return self.search_fish_by_criteria({"feeding_habits": feeding_habits})

    def _convert_to_dict(self, fish_species: FishSpecies) -> Dict[str, Any]:
        """转换为字典格式"""
        if not fish_species:
            return {}

        return {
            "基本信息": {
                "名称": fish_species.name,
                "学名": fish_species.scientific_name,
                "科属": fish_species.family,
                "目": fish_species.order,
                "别名": fish_species.common_names
            },
            "栖息信息": {
                "栖息地类型": fish_species.habitat_preference.value,
                "分布范围": fish_species.distribution,
                "水域偏好": fish_species.water_type_preference
            },
            "行为特征": {
                "食性": fish_species.feeding_habits.value,
                "活动模式": fish_species.behavior_patterns.activity_pattern.value,
                "群游性": fish_species.behavior_patterns.schooling_behavior,
                "领地性": fish_species.behavior_patterns.territorial_behavior,
                "繁殖行为": fish_species.behavior_patterns.reproduction_behavior
            },
            "环境适应性": {
                "最佳温度": f"{fish_species.temperature_range.optimal_min}°C - {fish_species.temperature_range.optimal_max}°C",
                "耐受温度": f"{fish_species.temperature_range.tolerance_min}°C - {fish_species.temperature_range.tolerance_max}°C",
                "氧气需求": fish_species.oxygen_requirement,
                "pH耐受度": fish_species.ph_tolerance
            },
            "钓鱼信息": {
                "偏好饵料": fish_species.preferred_baits,
                "钓鱼技术": [
                    {
                        "名称": tech.name,
                        "描述": tech.description,
                        "难度等级": tech.difficulty_level,
                        "所需装备": tech.equipment_required
                    }
                    for tech in fish_species.fishing_techniques
                ],
                "最佳作钓时间": fish_species.best_fishing_times,
                "钓鱼难度": fish_species.fishing_difficulty
            },
            "保护状态": {
                "保护等级": fish_species.conservation_status,
                "渔业规定": fish_species.fishing_regulations
            },
            "元数据": {
                "数据来源": fish_species.data_source,
                "最后更新": fish_species.last_updated,
                "可靠性评分": fish_species.reliability_score
            }
        }

    def get_all_fish_names(self) -> List[str]:
        """获取所有鱼种名称"""
        try:
            all_fish = self.fish_repository.get_all()
            return [fish.name for fish in all_fish if fish.is_active]
        except Exception as e:
            self.logger.error(f"获取鱼种名称列表失败: {e}")
            return []

# 注册服务
service_manager.register_service(
    'fish_species_service',
    FishSpeciesService,
    singleton=True
)
```

#### 策略服务
```python
# fish_knowledge/services/strategy_service.py
from typing import Optional, Dict, Any, List
from ..domain.strategies import FishingStrategy, StrategyType
from ..repositories.strategy_repository import IStrategyRepository
from shared.infrastructure.service_manager import service_manager
from shared.utils.logging import logger

class StrategyService:
    """策略服务"""

    def __init__(self,
                 strategy_repository: IStrategyRepository,
                 cache,
                 logger):
        self.strategy_repository = strategy_repository
        self.cache = cache
        self.logger = logger

    def get_seasonal_strategy(self,
                             season: str,
                             location: str,
                             target_fish: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取季节性钓鱼策略"""
        try:
            self.logger.info(f"获取季节策略: {season}, 地点: {location}, 目标鱼种: {target_fish}")

            # 构建缓存键
            cache_key = f"seasonal_strategy:{season}:{location}:{target_fish or 'all'}"
            cached_strategy = self.cache.get(cache_key)
            if cached_strategy:
                return cached_strategy

            # 生成策略
            strategy = self._generate_seasonal_strategy(season, location, target_fish)

            if not strategy:
                return None

            # 转换为字典格式
            result = self._convert_strategy_to_dict(strategy)

            # 缓存结果
            self.cache.set(cache_key, result, ttl=7200)  # 2小时缓存

            return result

        except Exception as e:
            self.logger.error(f"获取季节策略失败: {e}")
            return None

    def get_weather_strategy(self,
                              weather_data: Dict[str, Any],
                              target_fish: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取天气应对策略"""
        try:
            self.logger.info(f"获取天气策略: {weather_data.get('condition')}, 目标鱼种: {target_fish}")

            cache_key = f"weather_strategy:{hash(str(weather_data))}:{target_fish or 'all'}"
            cached_strategy = self.cache.get(cache_key)
            if cached_strategy:
                return cached_strategy

            strategy = self._generate_weather_strategy(weather_data, target_fish)

            if not strategy:
                return None

            result = self._convert_strategy_to_dict(strategy)
            self.cache.set(cache_key, result, ttl=1800)  # 30分钟缓存

            return result

        except Exception as e:
            self.logger.error(f"获取天气策略失败: {e}")
            return None

    def get_location_strategy(self,
                               location: str,
                               season: Optional[str] = None,
                               target_fish: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取地域性钓鱼策略"""
        try:
            self.logger.info(f"获取地点策略: {location}, 季节: {season}, 目标鱼种: {target_fish}")

            cache_key = f"location_strategy:{location}:{season or 'current'}:{target_fish or 'all'}"
            cached_strategy = self.cache.get(cache_key)
            if cached_strategy:
                return cached_strategy

            strategy = self._generate_location_strategy(location, season, target_fish)

            if not strategy:
                return None

            result = self._convert_strategy_to_dict(strategy)
            self.cache.set(cache_key, result, ttl=7200)

            return result

        except Exception as e:
            self.logger.error(f"获取地点策略失败: {e}")
            return None

    def _generate_seasonal_strategy(self,
                                   season: str,
                                   location: str,
                                   target_fish: Optional[str]) -> Optional[FishingStrategy]:
        """生成季节性策略"""
        # 季节性策略数据
        seasonal_data = self._load_seasonal_data()

        if season not in seasonal_data:
            self.logger.warning(f"未找到季节数据: {season}")
            return None

        # 基础策略信息
        base_strategy = seasonal_data[season]

        # 应用地域化调整
        location_adjustments = self._apply_location_adjustments(base_strategy, location)

        # 应用鱼种特化
        fish_specific_adjustments = self._apply_fish_specific_adjustments(
            location_adjustments, target_fish
        )

        return fish_specific_adjustments

    def _generate_weather_strategy(self,
                                 weather_data: Dict[str, Any],
                                 target_fish: Optional[str]) -> Optional[FishingStrategy]:
        """生成天气应对策略"""
        # 天气策略生成逻辑
        return None  # 实现细节

    def _generate_location_strategy(self,
                                 location: str,
                                 season: Optional[str],
                                 target_fish: Optional[str]) -> Optional[FishingStrategy]:
        """生成地域性策略"""
        # 地域策略生成逻辑
        return None  # 实现细节

    def _load_seasonal_data(self) -> Dict[str, Any]:
        """加载季节性数据"""
        # 从JSON文件或数据库加载
        return {}

    def _apply_location_adjustments(self, strategy: Dict[str, Any], location: str) -> Dict[str, Any]:
        """应用地域化调整"""
        return strategy  # 实现细节

    def _apply_fish_specific_adjustments(self,
                                         strategy: Dict[str, Any],
                                         target_fish: Optional[str]) -> Dict[str, Any]:
        """应用鱼种特化调整"""
        return strategy  # 实现细节

    def _convert_strategy_to_dict(self, strategy: FishingStrategy) -> Dict[str, Any]:
        """转换策略为字典格式"""
        if not strategy:
            return {}

        return {
            "策略类型": strategy.strategy_type.value,
            "目标鱼种": strategy.target_fish,
            "地点": strategy.location,
            "时间段": [
                {
                    "时间段": slot.description,
                    "开始时间": f"{slot.start_hour}:00",
                    "结束时间": f"{slot.end_hour}:00",
                    "钓鱼质量": slot.fishing_quality,
                    "推荐技术": slot.recommended_techniques
                }
                for slot in strategy.time_slots
            ],
            "地点策略": {
                "地点类型": strategy.location_strategy.location_type,
                "推荐钓点": strategy.location_strategy.recommended_spots,
                "避免钓点": strategy.location_strategy.avoiding_spots,
                "环境因素": strategy.location_strategy.environmental_factors
            },
            "装备建议": {
                "鱼竿推荐": strategy.equipment_recommendations.rod_recommendations,
                "饵料推荐": strategy.equipment_recommendations.lure_recommendations,
                "必备配件": strategy.equipment_recommendations.essential_accessories
            },
            "天气条件": strategy.weather_conditions,
            "成功技巧": strategy.success_tips,
            "风险因素": strategy.risk_warnings,
            "预期渔获率": f"{strategy.expected_catch_rate * 100:.1f}%"
        }

# 注册服务
service_manager.register_service(
    'strategy_service',
    StrategyService,
    singleton=True
)
```

### 3. LangChain工具集成

#### 鱼种分析工具
```python
# fish_knowledge/tools/fish_species_analyzer.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
from ..services.fish_species_service import FishSpeciesService
from shared.infrastructure.service_manager import service_manager
from shared.utils.logging import logger

class FishSpeciesInput(BaseModel):
    """鱼种分析输入参数"""
    fish_name: str = Field(..., description="鱼种名称，如'鲈鱼'、'翘嘴'、'黑鱼'")
    include_details: bool = Field(default=True, description="是否包含详细信息")

class FishSpeciesOutput(BaseModel):
    """鱼种分析输出结果"""
    success: bool = Field(..., description="查询是否成功")
    fish_name: str = Field(..., description="查询的鱼种名称")
    info: Optional[str] = Field(default=None, description="鱼种详细信息")
    message: str = Field(..., description="状态消息")

class FishSpeciesAnalyzer(BaseTool):
    """鱼种分析工具"""

    name: str = "fish_species_analyzer"
    description: str = "获取鱼种的详细信息，包括习性、觅食规律、栖息偏好等"
    args_schema: dict = {
        "type": "object",
        "properties": {
            "fish_name": {
                "type": "string",
                "description": "鱼种名称(如'鲈鱼'、'翘嘴'、'黑鱼')",
                "minLength": 1,
                "maxLength": 20
            },
            "include_details": {
                "type": "boolean",
                "description": "是否包含详细信息",
                "default": True
            }
        },
        "required": ["fish_name"]
    }

    def _run(self, fish_name: str, include_details: bool = True) -> str:
        """执行鱼种分析"""
        try:
            logger.info(f"执行鱼种分析: {fish_name}")

            # 获取鱼种服务
            fish_service = service_manager.get('fish_species_service')

            # 查询鱼种信息
            fish_info = fish_service.get_fish_species_info(fish_name)

            if fish_info:
                result = FishSpeciesOutput(
                    success=True,
                    fish_name=fish_name,
                    info=fish_info,
                    message="查询成功"
                )
            else:
                result = FishSpeciesOutput(
                    success=False,
                    fish_name=fish_name,
                    info=None,
                    message=f"未找到'{fish_name}'的相关信息，请检查鱼种名称是否正确"
                )

            return self._format_output(result)

        except Exception as e:
            logger.error(f"鱼种分析失败: {e}")
            return f"分析过程中出现错误: {str(e)}"

    def _format_output(self, result: FishSpeciesOutput) -> str:
        """格式化输出结果"""
        if not result.success:
            return f"❌ {result.message}"

        if not result.info:
            return f"❌ 未找到'{result.fish_name}'的相关信息"

        # 生成格式化的输出
        fish_data = result.info
        output_parts = []

        output_parts.append(f"🐟 **{result.fish_name} 详细信息**\n")

        # 基本信息
        if "基本信息" in fish_data:
            basic_info = fish_data["基本信息"]
            output_parts.append("📋 **基本信息:**")
            for key, value in basic_info.items():
                output_parts.append(f"• {key}: {value}")

        # 栖息信息
        if "栖息信息" in fish_data:
            habitat_info = fish_data["栖息信息"]
            output_parts.append("\n🏞️ **栖息信息:**")
            for key, value in habitat_info.items():
                output_parts.append(f"• {key}: {value}")

        # 行为特征
        if "行为特征" in fish_data:
            behavior_info = fish_data["行为特征"]
            output_parts.append("\n🎯 **行为特征:**")
            for key, value in behavior_info.items():
                output_parts.append(f"• {key}: {value}")

        # 环境适应性
        if "环境适应性" in fish_data:
            env_info = fish_data["环境适应性"]
            output_parts.append("\n🌡️ **环境适应性:**")
            for key, value in env_info.items():
                output_parts.append(f"• {key}: {value}")

        # 钓鱼信息
        if "钓鱼信息" in fish_data:
            fishing_info = fish_data["钓鱼信息"]
            output_parts.append("\n🎣 **钓鱼信息:**")

            # 最佳作钓时间
            if "最佳作钓时间" in fishing_info:
                output_parts.append(f"• **最佳时间**: {', '.join(fishing_info['最佳作钓时间'])}")

            # 钓鱼技术
            if "钓鱼技术" in fishing_info:
                output_parts.append("\n🎯 **推荐钓法:**")
                for tech in fishing_info["钓鱼技术"]:
                    output_parts.append(f"• {tech['名称']}: {tech['描述']}")

        # 元数据
        if "元数据" in fish_data:
            meta_info = fish_data["元数据"]
            output_parts.append(f"\n📊 **数据来源:** {meta_info.get('数据来源', '未知')}")
            output_parts.append(f"**可靠性评分:** {meta_info.get('可靠性评分', 0):.1f}/1.0")

        return "\n".join(output_parts)

# 注册工具
def get_fish_species_info(fish_name: str) -> str:
    """获取鱼种详细信息

    Args:
        fish_name: 鱼种名称(如"鲈鱼"、"翘嘴"、"黑鱼")

    Returns:
        详细的鱼种信息，包含习性、觅食规律、栖息偏好等
    """
    tool = FishSpeciesAnalyzer()
    return tool._run(fish_name)
```

#### 季节策略工具
```python
# fish_knowledge/tools/seasonal_planner.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
from ..services.strategy_service import StrategyService
from shared.infrastructure.service_manager import service_manager
from shared.utils.logging import logger

class SeasonalStrategyInput(BaseModel):
    """季节策略输入参数"""
    season: str = Field(..., description="季节('春'、'夏'、'秋'、'冬')")
    location: str = Field(..., description="地理位置")
    target_fish: Optional[str] = Field(default=None, description="目标鱼种(可选)")

class SeasonalStrategyOutput(BaseModel):
    """季节策略输出结果"""
    success: bool = Field(..., description="查询是否成功")
    season: str = Field(..., description="查询的季节")
    location: str = Field(..., description="查询的地点")
    strategy: Optional[str] = Field(default=None, description="季节性钓鱼策略")
    message: str = Field(..., description="状态消息")

class SeasonalPlanner(BaseTool):
    """季节规划工具"""

    name: str = "seasonal_planner"
    description: str = "获取特定季节和地点的钓鱼策略，包括目标鱼种、最佳时间、装备建议等"
    args_schema: dict = {
        "type": "object",
        "properties": {
            "season": {
                "type": "string",
                "description": "季节('春'、'夏'、'秋'、'冬')",
                "enum": ["春", "夏", "秋", "冬"]
            },
            "location": {
                "type": "string",
                "description": "地理位置(省市县)",
                "minLength": 2,
                "maxLength": 50
            },
            "target_fish": {
                "type": "string",
                "description": "目标鱼种(可选)",
                "maxLength": 20
            }
        },
        "required": ["season", "location"]
    }

    def _run(self, season: str, location: str, target_fish: Optional[str] = None) -> str:
        """执行季节规划"""
        try:
            logger.info(f"执行季节规划: {season}, 地点: {location}, 目标鱼种: {target_fish}")

            # 获取策略服务
            strategy_service = service_manager.get('strategy_service')

            # 查询季节策略
            strategy = strategy_service.get_seasonal_strategy(season, location, target_fish)

            if strategy:
                result = SeasonalStrategyOutput(
                    success=True,
                    season=season,
                    location=location,
                    strategy=strategy,
                    message="查询成功"
                )
            else:
                result = SeasonalStrategyOutput(
                    success=False,
                    season=season,
                    location=location,
                    strategy=None,
                    message=f"未找到{season}季节在{location}的钓鱼策略"
                )

            return self._format_output(result)

        except Exception as e:
            logger.error(f"季节规划失败: {e}")
            return f"规划过程中出现错误: {str(e)}"

    def _format_output(self, result: SeasonalStrategyOutput) -> str:
        """格式化输出结果"""
        if not result.success:
            return f"❌ {result.message}"

        if not result.strategy:
            return f"❌ 未找到{result.season}季节在{result.location}的钓鱼策略"

        strategy_data = result.strategy
        output_parts = []

        output_parts.append(f"🍃 **{result.season}季钓鱼策略** - {result.location}\n")

        # 解析策略数据
        # 这里需要根据实际的数据结构进行解析
        output_parts.append("📋 **总体特点:**")
        # 添加具体内容...

        output_parts.append("🐟 **主要目标鱼种及策略:**")
        # 添加具体内容...

        output_parts.append("⏰ **最佳作钓时间:**")
        # 添加具体内容...

        output_parts.append("🌡️ **天气应对:**")
        # 添加具体内容...

        output_parts.append("🎣 **装备建议:**")
        # 添加具体内容...

        return "\n".join(output_parts)

# 注册工具
def get_seasonal_strategy(season: str, location: str, target_fish: str = None) -> str:
    """获取季节性钓鱼策略

    Args:
        season: 季节("春"、"夏"、"秋"、"冬")
        location: 地理位置
        target_fish: 目标鱼种(可选)

    Returns:
        详细的季节性钓鱼策略建议
    """
    tool = SeasonalPlanner()
    return tool._run(season, location, target_fish)
```

## 📊 数据来源和质量管理

### 数据来源
1. **鱼类学资料**: 专业鱼类学教材和研究报告
2. **钓鱼专业书籍**: 钓鱼技巧和策略的专业书籍
3. **钓鱼社区经验**: 钓鱼爱好者的经验分享和总结
4. **科学研究数据**: 鱼类行为学的科学研究结果
5. **地域性资料**: 不同地区的钓鱼特点和模式

### 数据质量管理流程
```python
# fish_knowledge/data/data_manager.py
import json
import os
from typing import Dict, List, Any
from pathlib import Path
from shared.infrastructure.service_manager import service_manager
from shared.utils.logging import logger

class FishKnowledgeDataManager:
    """鱼类知识数据管理器"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_files = {
            "fish_knowledge": "fish_knowledge.json",
            "seasonal_patterns": "seasonal_patterns.json",
            "regional_data": "regional_data.json",
            "weather_responses": "weather_responses.json"
        }

    def load_fish_knowledge_data(self) -> Dict[str, Any]:
        """加载鱼类知识数据"""
        file_path = self.data_dir / self.data_files["fish_knowledge"]
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def load_seasonal_patterns_data(self) -> Dict[str, Any]:
        """加载季节模式数据"""
        file_path = self.data_dir / self.data_files["seasonal_patterns"]
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def validate_data_quality(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """验证数据质量"""
        validated_data = []
        invalid_data = []

        if data_type == "fish_knowledge":
            for item in data.get("fish_species", []):
                if self._validate_fish_species_data(item):
                    validated_data.append(item)
                else:
                    invalid_data.append(item)

        return {
            "valid_data": validated_data,
            "invalid_data": invalid_data,
            "validation_rate": len(validated_data) / (len(validated_data) + len(invalid_data)) if validated_data or invalid_data else 0
        }

    def _validate_fish_species_data(self, fish_data: Dict[str, Any]) -> bool:
        """验证鱼种数据"""
        required_fields = ["name", "scientific_name", "family"]
        return all(field in fish_data for field in required_fields)

    def update_data_from_sources(self):
        """从外部数据源更新数据"""
        # 实现从外部API或文件更新数据的逻辑
        pass
```

## 🎯 验收标准

### 功能验收标准
- [ ] 支持20+主要淡水鱼种的专业知识查询
- [ ] 涵盖四季钓鱼策略和地域性模式
- [ ] 天气应对指导覆盖主要天气情况
- [ ] 知识准确性>95%（基于专业钓鱼资料验证）
- [ ] 策略建议实用性评分>85%（用户测试）

### 性能验收标准
- [ ] 知识检索响应时间<2秒
- [ ] 策略生成时间<3秒
- [ ] 系统可用性>99.5%
- [ ] 数据更新频率：每月更新一次

### 数据质量标准
- [ ] 数据准确性>95%（多源验证）
- [ ] 信息完整性>90%（关键字段覆盖）
- [ ] 数据一致性>95%（避免冲突信息）
- [ ] 更新及时性：新数据在7天内录入

## 🚀 开发指南

### 开发环境准备
```bash
# 安装依赖
uv add sqlalchemy pydantic redis

# 创建目录结构
mkdir -p fish_knowledge/{domain,services,repositories,tools,data}
```

### 数据准备
```python
# 准备鱼种知识数据
python scripts/prepare_fish_data.py

# 初始化数据库
python scripts/init_database.py
```

### 服务开发流程
1. **定义领域模型** - 实现domain模块下的数据模型
2. **实现仓储层** - 实现repositories下的数据访问逻辑
3. **开发服务层** - 实现services下的业务逻辑
4. **创建工具函数** - 实现tools下的LangChain工具
5. **编写测试用例** - 确保功能正确性

### 集成测试
```python
# 测试鱼类知识系统功能
def test_fish_knowledge_system():
    # 1. 测试鱼种查询
    fish_service = service_manager.get('fish_species_service')
    result = fish_service.get_fish_species_info("鲈鱼")
    assert result is not None

    # 2. 测试策略生成
    strategy_service = service_manager.get('strategy_service')
    result = strategy_service.get_seasonal_strategy("秋", "杭州")
    assert result is not None

    # 3. 测试工具函数
    from fish_knowledge.tools.fish_species_analyzer import get_fish_species_info
    result = get_fish_species_info("鲈鱼")
    assert "鲈鱼" in result
```

## 📝 使用示例

### 基本查询
```python
from fish_knowledge.tools.fish_species_analyzer import get_fish_species_info
from fish_knowledge.tools.seasonal_planner import get_seasonal_strategy

# 查询鱼种信息
fish_info = get_fish_species_info("鲈鱼")

# 获取季节策略
seasonal_strategy = get_seasonal_strategy("秋", "杭州", "鲈鱼")
```

### 批量查询
```python
from fish_knowledge.services.fish_species_service import FishSpeciesService

fish_service = service_manager.get('fish_species_service')

# 获取所有鲈科鱼种
bass_fish = fish_service.get_fish_by_family("鲈科")

# 获取浅水区鱼种
shallow_water_fish = fish_service.get_fish_by_habitat("浅水区")
```

---

*本文档为鱼类知识系统的开发提供了完整的设计指南和实现参考，确保开发团队能够高效、正确地构建专业的鱼类知识库。*