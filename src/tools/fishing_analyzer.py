#!/usr/bin/env python3
"""
钓鱼分析工具
基于天气数据分析最佳的钓鱼时间
支持3因子传统评分和7因子增强评分
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
import math
import random
import os

# 导入现有的天气工具
try:
    from .weather_tool import WeatherTool, ToolResult
    from ..services.service_manager import get_weather_service
    from .enhanced_fishing_scorer import EnhancedFishingScorer, FishingScore
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from weather_tool import WeatherTool, ToolResult
    sys.path.append(str(Path(__file__).parent.parent))
    from services.service_manager import get_weather_service
    from enhanced_fishing_scorer import EnhancedFishingScorer, FishingScore


@dataclass
class FishingCondition:
    """钓鱼条件数据"""
    hour: int                    # 小时 (0-23)
    temperature: float           # 温度 (°C)
    condition: str              # 天气状况
    wind_speed: float           # 风速 (km/h)
    humidity: float             # 湿度 (%)
    pressure: float             # 气压 (hPa)

    # 传统3因子评分 (0-100)
    temperature_score: float    # 温度评分
    weather_score: float        # 天气评分
    wind_score: float          # 风力评分
    overall_score: float       # 综合评分

    # 时间段名称
    period_name: str           # 时间段名称（如"早上"、"上午"等）

    # 增强7因子评分 (可选)
    enhanced_score: Optional[FishingScore] = None  # 增强评分结果

    # 评分模式标识
    is_enhanced: bool = False  # 是否使用增强评分


@dataclass
class FishingRecommendation:
    """钓鱼推荐结果"""
    location: str                              # 地点
    date: str                                  # 日期
    best_time_slots: List[Tuple[str, float]]   # 最佳时间段 (时间段名称, 评分)
    detailed_analysis: str                     # 详细分析
    hourly_conditions: List[FishingCondition] # 每小时条件
    summary: str                               # 总结建议
    weather_overview: Optional[str] = None     # 天气概况
    temperature_range: Optional[str] = None     # 温度范围
    weather_summaries: Optional[Dict[str, str]] = None  # 各时间段天气摘要

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "location": self.location,
            "date": self.date,
            "best_time_slots": [(period, score) for period, score in self.best_time_slots],
            "detailed_analysis": self.detailed_analysis,
            "hourly_conditions": [
                {
                    "hour": cond.hour,
                    "period_name": cond.period_name,
                    "temperature": cond.temperature,
                    "condition": cond.condition,
                    "overall_score": cond.overall_score
                } for cond in self.hourly_conditions
            ],
            "summary": self.summary,
            "weather_overview": self.weather_overview,
            "temperature_range": self.temperature_range,
            "weather_summaries": self.weather_summaries
        }


class FishingAnalyzer:
    """钓鱼条件分析器"""

    def __init__(self):
        """初始化钓鱼分析器"""
        # 初始化日志
        self._logger = logging.getLogger(__name__)

        # 使用天气工具
        self.weather_tool = WeatherTool()
        # 延迟初始化：使用服务管理器获取天气服务
        self._enhanced_weather_service = None

        # 初始化增强评分器
        self._enhanced_scorer = None

        # 初始化其他参数
        self._init_parameters()

    @property
    def enhanced_scorer(self):
        """获取增强评分器实例（懒加载）"""
        if self._enhanced_scorer is None:
            self._enhanced_scorer = EnhancedFishingScorer()
        return self._enhanced_scorer

    @property
    def use_enhanced_scoring(self) -> bool:
        """是否使用增强评分"""
        return os.getenv('ENABLE_ENHANCED_FISHING_SCORING', 'true').lower() == 'true'

    @property
    def enhanced_weather_service(self):
        """获取增强版天气服务实例（懒加载）"""
        if self._enhanced_weather_service is None:
            self._enhanced_weather_service = get_weather_service()
        return self._enhanced_weather_service

    def _init_parameters(self):
        """初始化后的设置"""
        # 钓鱼最佳条件参数
        self.optimal_temp_range = (15, 25)        # 最佳温度范围
        self.optimal_wind_speed = (0, 15)         # 最佳风速范围
        self.preferred_weather = ["晴", "多云", "阴", "小雨"]  # 偏好天气

        # 时间段定义 - 使用datetime_utils中的统一定义
        # 不再需要self.time_periods，直接使用get_time_period_name函数

    def get_time_period(self, hour: int) -> str:
        """获取小时对应的时间段"""
        from services.weather.utils.datetime_utils import get_time_period_name
        return get_time_period_name(hour)

    def calculate_temperature_score(self, temperature: float) -> float:
        """
        计算温度评分

        Args:
            temperature: 温度 (°C)

        Returns:
            温度评分 (0-100)
        """
        min_temp, max_temp = self.optimal_temp_range

        if min_temp <= temperature <= max_temp:
            # 在最佳范围内，给满分
            return 100.0
        elif temperature < min_temp:
            # 低于最佳范围，线性递减
            if temperature < 0:
                return 0.0
            ratio = temperature / min_temp
            return max(0.0, ratio * 80)  # 最低0分，最高80分
        else:
            # 高于最佳范围，线性递减
            if temperature > 35:
                return 0.0
            excess = temperature - max_temp
            ratio = max(0, 1 - excess / 10)  # 超过10度给0分
            return ratio * 80  # 最低0分，最高80分

    def calculate_weather_score(self, condition: str) -> float:
        """
        计算天气评分

        Args:
            condition: 天气状况

        Returns:
            天气评分 (0-100)
        """
        condition = condition.lower()

        # 最佳天气
        best_weather = ["多云", "阴"]
        for weather in best_weather:
            if weather in condition:
                return 100.0

        # 良好天气
        good_weather = ["晴", "小雨"]
        for weather in good_weather:
            if weather in condition:
                return 85.0

        # 一般天气
        fair_weather = ["中雨"]
        for weather in fair_weather:
            if weather in condition:
                return 50.0

        # 较差天气
        poor_weather = ["大雨", "暴雨", "雷阵雨"]
        for weather in poor_weather:
            if weather in condition:
                return 20.0

        # 极差天气
        terrible_weather = ["雪", "冰雹", "雾", "霾"]
        for weather in terrible_weather:
            if weather in condition:
                return 10.0

        # 未知天气，给中等分数
        return 60.0

    def calculate_wind_score(self, wind_speed: float) -> float:
        """
        计算风力评分

        Args:
            wind_speed: 风速 (km/h)

        Returns:
            风力评分 (0-100)
        """
        min_wind, max_wind = self.optimal_wind_speed

        if min_wind <= wind_speed <= max_wind:
            # 在最佳范围内
            return 100.0
        elif wind_speed < min_wind:
            # 风太小，影响钓饵传播
            return 85.0
        else:
            # 风太大，影响钓鱼
            if wind_speed > 30:
                return 10.0
            excess = wind_speed - max_wind
            ratio = max(0, 1 - excess / 15)  # 超过15km/h开始快速递减
            return ratio * 80

    def _generate_hourly_data_from_datetime(self, weather_data: Dict, date: str) -> List[Dict]:
        """
        从weather_by_datetime的数据生成24小时数据

        Args:
            weather_data: weather_by_datetime返回的数据
            date: 日期字符串

        Returns:
            24小时数据列表
        """
        hourly_data = []

        # 提取基础天气信息
        temp_avg = weather_data.get("temperature_avg", 20)
        temp_min = weather_data.get("temperature_min", temp_avg - 5)
        temp_max = weather_data.get("temperature_max", temp_avg + 5)
        condition = weather_data.get("condition", "多云")
        humidity_avg = weather_data.get("humidity_avg", 60)
        wind_speed = weather_data.get("wind_speed_avg", 5)

        # 生成24小时的数据
        import random
        for hour in range(24):
            # 模拟温度变化（早晚低，中午高）
            if 6 <= hour <= 8:  # 早上
                temp_variation = -3
            elif 12 <= hour <= 14:  # 中午
                temp_variation = 3
            elif 18 <= hour <= 20:  # 傍晚
                temp_variation = -1
            else:
                temp_variation = random.uniform(-2, 2)

            temperature = temp_avg + temp_variation
            temperature = max(temp_min, min(temp_max, temperature))  # 限制在最小最大值之间

            # 创建小时数据
            hourly_entry = {
                "datetime": f"{date}T{hour:02d}:00:00",
                "temperature": round(temperature, 1),
                "condition": condition,
                "wind_speed": round(wind_speed + random.uniform(-2, 2), 1),
                "humidity": max(30, min(95, humidity_avg + random.randint(-10, 10))),
                "pressure": 1013 + random.randint(-5, 5)
            }

            hourly_data.append(hourly_entry)

        return hourly_data

    def _generate_hourly_data_from_daily(self, weather_data: Dict, date: str) -> List[Dict]:
        """
        从daily_forecast数据生成24小时数据

        Args:
            weather_data: daily_forecast返回的数据
            date: 日期字符串

        Returns:
            24小时数据列表
        """
        hourly_data = []

        # 提取基础天气信息
        temperature = weather_data.get("temperature", 20)
        temp_min = weather_data.get("temperature_min", 15)
        temp_max = weather_data.get("temperature_max", 25)
        condition = weather_data.get("condition", "多云")
        humidity = weather_data.get("humidity", 60)
        wind_speed = weather_data.get("wind_speed", 5)

        # 确保温度数据是数字类型
        if isinstance(temp_min, (list, dict)):
            temp_min = float(temp_min) if isinstance(temp_min, (int, float)) else 15.0
        if isinstance(temp_max, (list, dict)):
            temp_max = float(temp_max) if isinstance(temp_max, (int, float)) else 25.0
        if isinstance(temperature, (list, dict)):
            temperature = float(temperature) if isinstance(temperature, (int, float)) else 20.0

        # 生成24小时的数据
        import random
        for hour in range(24):
            # 模拟温度变化
            if 6 <= hour <= 8:  # 早上
                temp_variation = -3
            elif 12 <= hour <= 14:  # 中午
                temp_variation = 3
            elif 18 <= hour <= 20:  # 傍晚
                temp_variation = -1
            else:
                temp_variation = random.uniform(-2, 2)

            hour_temperature = temp_min + (temp_max - temp_min) * ((hour + temp_variation + 3) / 27)
            hour_temperature = max(temp_min, min(temp_max, hour_temperature))

            hourly_entry = {
                "datetime": f"{date}T{hour:02d}:00:00",
                "temperature": round(hour_temperature, 1),
                "condition": condition,
                "wind_speed": round(wind_speed + random.uniform(-2, 2), 1),
                "humidity": max(30, min(95, humidity + random.randint(-10, 10))),
                "pressure": 1013 + random.randint(-5, 5)
            }

            hourly_data.append(hourly_entry)

        return hourly_data

    def _generate_hourly_data_from_date(self, weather_data: Dict, date: str) -> List[Dict]:
        """
        从weather_by_date的数据生成24小时数据

        Args:
            weather_data: weather_by_date返回的数据
            date: 日期字符串

        Returns:
            24小时数据列表
        """
        hourly_data = []

        # 提取基础天气信息
        temperature = weather_data.get("temperature", 20)
        condition = weather_data.get("condition", "多云")
        humidity = weather_data.get("humidity", 60)
        wind_speed = weather_data.get("wind_speed", 5)

        # 生成24小时的数据
        import random
        for hour in range(24):
            # 模拟温度变化
            if 6 <= hour <= 8:  # 早上
                temp_variation = -3
            elif 12 <= hour <= 14:  # 中午
                temp_variation = 3
            elif 18 <= hour <= 20:  # 傍晚
                temp_variation = -1
            else:
                temp_variation = random.uniform(-2, 2)

            hourly_temperature = temperature + temp_variation

            hourly_entry = {
                "datetime": f"{date}T{hour:02d}:00:00",
                "temperature": round(hourly_temperature, 1),
                "condition": condition,
                "wind_speed": round(wind_speed + random.uniform(-2, 2), 1),
                "humidity": max(30, min(95, humidity + random.randint(-10, 10))),
                "pressure": 1013 + random.randint(-5, 5)
            }

            hourly_data.append(hourly_entry)

        return hourly_data

    def _generate_fallback_hourly_data(self, date: str) -> List[Dict]:
        """
        生成备用的小时数据（当所有天气查询都失败时）

        Args:
            date: 日期字符串

        Returns:
            24小时模拟数据列表
        """
        hourly_data = []

        # 使用一般的天气参数
        base_temperature = 20
        base_condition = "多云"
        base_humidity = 60
        base_wind_speed = 5

        import random
        for hour in range(24):
            # 模拟温度变化
            if 6 <= hour <= 8:  # 早上
                temp_variation = -3
            elif 12 <= hour <= 14:  # 中午
                temp_variation = 3
            elif 18 <= hour <= 20:  # 傍晚
                temp_variation = -1
            else:
                temp_variation = random.uniform(-2, 2)

            temperature = base_temperature + temp_variation

            hourly_entry = {
                "datetime": f"{date}T{hour:02d}:00:00",
                "temperature": round(temperature, 1),
                "condition": base_condition,
                "wind_speed": round(base_wind_speed + random.uniform(-2, 2), 1),
                "humidity": max(30, min(95, base_humidity + random.randint(-10, 10))),
                "pressure": 1013 + random.randint(-5, 5)
            }

            hourly_data.append(hourly_entry)

        return hourly_data

    def _extract_daily_forecast_data(self, daily_data: Dict, day_offset: int) -> Optional[Dict]:
        """
        从7天预报数据中提取指定日期的天气数据

        Args:
            daily_data: 7天预报API返回的数据
            day_offset: 天数偏移 (0=今天, 1=明天, ...)

        Returns:
            格式化的天气数据字典
        """
        try:
            # 提取温度数据
            temperature = daily_data.get("temperature", [])
            if not temperature or len(temperature) <= day_offset:
                return None

            day_temps = temperature[day_offset]
            temp_min = day_temps.get("min", 15)
            temp_max = day_temps.get("max", 25)
            temp_avg = (temp_min + temp_max) / 2

            # 提取天气状况
            skycon = daily_data.get("skycon", [])
            if not skycon or len(skycon) <= day_offset:
                condition = "多云"
            else:
                condition_value = skycon[day_offset].get("value", "partly_cloudy_day")
                condition_map = {
                    "CLEAR_DAY": "晴天",
                    "CLEAR_NIGHT": "晴夜",
                    "PARTLY_CLOUDY_DAY": "多云",
                    "PARTLY_CLOUDY_NIGHT": "多云",
                    "CLOUDY": "阴天",
                    "LIGHT_HAZE": "轻度雾霾",
                    "MODERATE_HAZE": "中度雾霾",
                    "HEAVY_HAZE": "重度雾霾",
                    "LIGHT_RAIN": "小雨",
                    "MODERATE_RAIN": "中雨",
                    "HEAVY_RAIN": "大雨",
                    "STORM_RAIN": "暴雨",
                    "LIGHT_SNOW": "小雪",
                    "MODERATE_SNOW": "中雪",
                    "HEAVY_SNOW": "大雪",
                    "STORM_SNOW": "暴雪",
                    "DUST": "浮尘",
                    "SAND": "沙尘",
                    "WIND": "大风"
                }
                condition = condition_map.get(condition_value, "多云")

            # 提取湿度数据
            humidity = daily_data.get("humidity", [])
            if humidity and len(humidity) > day_offset:
                humidity_avg = humidity[day_offset]
            else:
                humidity_avg = 60

            # 提取风力数据
            wind = daily_data.get("wind", [])
            if wind and len(wind) > day_offset:
                day_wind = wind[day_offset]
                wind_speed = day_wind.get("avg", 5) if isinstance(day_wind, dict) else 5
            else:
                wind_speed = 5

            # 返回标准格式的数据
            return {
                "temperature": temp_avg,
                "temperature_min": temp_min,
                "temperature_max": temp_max,
                "condition": condition,
                "humidity": humidity_avg,
                "wind_speed": wind_speed,
                "source": "7天预报API",
                "data_type": "daily_forecast"
            }

        except Exception as e:
            self._logger.warning(f"解析7天预报数据失败: {e}")
            return None

    def analyze_hourly_condition(self, hourly_data: Dict, historical_data: List[Dict] = None, date: datetime = None) -> FishingCondition:
        """
        分析单小时的钓鱼条件

        Args:
            hourly_data: 小时天气数据
            historical_data: 历史数据序列 (用于增强评分)
            date: 目标日期 (用于增强评分)

        Returns:
            钓鱼条件评分
        """
        # 提取天气数据
        hour = datetime.fromisoformat(hourly_data.get("datetime", "").replace("Z", "+00:00")).hour
        temperature = hourly_data.get("temperature", 0)
        condition = hourly_data.get("condition", "")
        wind_speed = hourly_data.get("wind_speed", 0)
        humidity = hourly_data.get("humidity", 0)
        pressure = hourly_data.get("pressure", 0)

        # 计算传统3因子评分
        temp_score = self.calculate_temperature_score(temperature)
        weather_score = self.calculate_weather_score(condition)
        wind_score = self.calculate_wind_score(wind_speed)

        # 综合评分 (加权平均)
        traditional_overall_score = (
            temp_score * 0.4 +      # 温度权重40%
            weather_score * 0.35 +  # 天气权重35%
            wind_score * 0.25       # 风力权重25%
        )

        period_name = self.get_time_period(hour)

        # 决定使用的评分系统
        if self.use_enhanced_scoring and historical_data and date:
            try:
                # 使用增强7因子评分
                enhanced_score = self.enhanced_scorer.calculate_comprehensive_score(
                    hourly_data, historical_data, date
                )
                overall_score = enhanced_score.overall
                is_enhanced = True
                self._logger.debug(f"使用增强评分: {hour}时, 评分{overall_score:.1f}")
            except Exception as e:
                self._logger.warning(f"增强评分失败，回退到传统评分: {e}")
                overall_score = traditional_overall_score
                enhanced_score = None
                is_enhanced = False
        else:
            # 使用传统3因子评分
            overall_score = traditional_overall_score
            enhanced_score = None
            is_enhanced = False

        return FishingCondition(
            hour=hour,
            temperature=temperature,
            condition=condition,
            wind_speed=wind_speed,
            humidity=humidity,
            pressure=pressure,
            temperature_score=temp_score,
            weather_score=weather_score,
            wind_score=wind_score,
            overall_score=overall_score,
            enhanced_score=enhanced_score,
            period_name=period_name,
            is_enhanced=is_enhanced
        )

    async def find_best_fishing_time(self, location: str, date: str = None) -> FishingRecommendation:
        """
        找出最佳的钓鱼时间

        Args:
            location: 地点
            date: 日期 (YYYY-MM-DD格式，如果为None则查询明天)

        Returns:
            钓鱼推荐结果
        """
        try:
            # 如果没有指定日期，默认查询明天
            if date is None:
                tomorrow = datetime.now() + timedelta(days=1)
                date = tomorrow.strftime("%Y-%m-%d")

            # 使用新的智能路由获取天气预报
            try:
                self._logger.debug(f"使用智能路由查询天气: {location}, {date}")

                # 获取地理位置信息
                from services.service_manager import get_coordinate_service
                coordinate_service = get_coordinate_service()
                coordinate_result = coordinate_service.get_coordinate(location)

                if not coordinate_result:
                    self._logger.error(f"无法获取地理位置信息: {location}")
                    return FishingRecommendation(
                        location=location,
                        date=date,
                        best_time_slots=[],
                        detailed_analysis=f"无法获取地理位置信息: {location}",
                        hourly_conditions=[],
                        summary="建议检查地点名称是否正确"
                    )

                # 提取坐标信息
                if hasattr(coordinate_result, 'longitude'):
                    lng = coordinate_result.longitude
                    lat = coordinate_result.latitude
                else:
                    # 如果是字典格式
                    lng = coordinate_result.get('lng', 0)
                    lat = coordinate_result.get('lat', 0)

                location_info = {
                    'name': location,
                    'lng': lng,
                    'lat': lat,
                    'adcode': getattr(coordinate_result, 'adcode', '')
                }

                # 使用智能路由获取天气
                weather_data, status_message, error_code = await self.enhanced_weather_service.get_forecast_by_range(
                    location_info, date
                )

                if weather_data and error_code in [0, 1]:  # 0=成功, 1=缓存命中
                    result = ToolResult(
                        success=True,
                        data=weather_data,
                        metadata={
                            "operation": "intelligent_router",
                            "source": "智能路由系统",
                            "status_message": status_message,
                            "error_code": error_code
                        }
                    )
                    self._logger.info(f"智能路由查询成功: {location}, {date} - {status_message}")
                else:
                    self._logger.error(f"智能路由查询失败: {location}, {date} - {status_message}")
                    return FishingRecommendation(
                        location=location,
                        date=date,
                        best_time_slots=[],
                        detailed_analysis=f"天气查询失败: {status_message}",
                        hourly_conditions=[],
                        summary="建议查询其他日期或地点"
                    )

            except Exception as e:
                self._logger.error(f"智能路由查询异常: {location}, {date} - {e}")
                return FishingRecommendation(
                    location=location,
                    date=date,
                    best_time_slots=[],
                    detailed_analysis=f"天气服务异常: {str(e)}",
                    hourly_conditions=[],
                    summary="建议稍后重试或联系技术支持"
                )

            # 分析每小时的条件
            hourly_conditions = []

            # 根据智能路由的数据处理数据
            operation = result.metadata.get("operation", "intelligent_router")
            weather_data = result.data

            if not weather_data:
                hourly_data = []
            elif operation == "intelligent_router":
                # 智能路由返回的是EnhancedWeatherData格式，需要转换为小时数据
                hourly_data = self._generate_hourly_data_from_intelligent_router(weather_data, date)
            elif operation == "daily_forecast":
                # daily_forecast 返回的是7天预报数据，需要转换为小时数据
                hourly_data = self._generate_hourly_data_from_daily(weather_data, date)
            elif operation == "weather_by_datetime":
                # weather_by_datetime 返回的是单日时间段数据，需要转换为小时数据
                hourly_data = self._generate_hourly_data_from_datetime(weather_data, date)
            elif operation == "weather_by_date":
                # weather_by_date 返回的是单日天气数据，需要转换为小时数据
                hourly_data = self._generate_hourly_data_from_date(weather_data, date)
            elif operation == "hourly_forecast":
                # hourly_forecast 返回的是标准小时数据
                hourly_data = weather_data.get("hourly_data", [])
            else:
                # 未知格式，尝试从hourly_data获取，如果失败则生成模拟数据
                hourly_data = weather_data.get("hourly_data", [])
                if not hourly_data:
                    self._logger.warning(f"未知数据格式，生成模拟数据: operation={operation}")
                    hourly_data = self._generate_fallback_hourly_data(date)

            # 解析目标日期
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                # 处理相对日期
                from services.weather.utils.datetime_utils import calculate_days_from_now
                days_from_now = calculate_days_from_now(date)
                target_date = datetime.now() + timedelta(days=days_from_now)

            # 准备历史数据用于增强评分
            if len(hourly_data) > 0:
                # 使用已有数据作为历史数据（前面的小时数据）
                historical_data_for_enhanced = hourly_data[:max(0, len(hourly_data)-6)]
            else:
                historical_data_for_enhanced = []

            for i, data in enumerate(hourly_data):
                # 为每个小时提供历史数据（排除当前及之后的数据）
                historical_for_this_hour = hourly_data[:i] if i > 0 else []
                if len(historical_for_this_hour) == 0 and len(historical_data_for_enhanced) > 0:
                    historical_for_this_hour = historical_data_for_enhanced[-6:]

                condition = self.analyze_hourly_condition(
                    data,
                    historical_for_this_hour,
                    target_date
                )
                hourly_conditions.append(condition)

            # 按时间段分组并找出最佳时间
            period_scores = {}
            for condition in hourly_conditions:
                period = condition.period_name
                if period not in period_scores:
                    period_scores[period] = []
                period_scores[period].append(condition.overall_score)

            # 计算每个时间段的平均评分
            period_avg_scores = {}
            for period, scores in period_scores.items():
                avg_score = sum(scores) / len(scores)
                period_avg_scores[period] = avg_score

            # 排序找出最佳时间段
            sorted_periods = sorted(
                period_avg_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # 为时间段添加时间范围信息
            enhanced_time_slots = []
            for period_name, score in sorted_periods[:3]:  # 取前3个最佳时间段
                # 导入时间工具函数
                from services.weather.utils.datetime_utils import get_time_period_range
                time_range = get_time_period_range(period_name)
                enhanced_time_slots.append((f"{period_name} ({time_range})", score))

            best_time_slots = enhanced_time_slots

            # 生成详细分析
            detailed_analysis = self._generate_detailed_analysis(
                hourly_conditions, sorted_periods
            )

            # 生成总结建议
            summary = self._generate_summary(best_time_slots, hourly_conditions)

            # 生成天气概况和温度范围
            weather_overview = self._generate_weather_overview(hourly_conditions)
            temperature_range = self._generate_temperature_range(hourly_conditions)

            # 生成各时间段的天气摘要
            weather_summaries = {}
            for period_with_range, score in best_time_slots:
                # 提取纯时间段名称（去掉时间范围）
                period_name = period_with_range.split(' ')[0]
                weather_summaries[period_with_range] = self._get_period_weather_summary(period_name, hourly_conditions)

            return FishingRecommendation(
                location=location,
                date=date,
                best_time_slots=best_time_slots,
                detailed_analysis=detailed_analysis,
                hourly_conditions=hourly_conditions,
                summary=summary,
                weather_overview=weather_overview,
                temperature_range=temperature_range,
                weather_summaries=weather_summaries
            )

        except Exception as e:
            import traceback
            error_details = f"分析过程中出现错误: {str(e)}\n详细错误: {traceback.format_exc()}"
            self._logger.error(f"钓鱼分析异常: {error_details}")
            return FishingRecommendation(
                location=location,
                date=date or "未知",
                best_time_slots=[],
                detailed_analysis=f"分析过程中出现错误: {str(e)}",
                hourly_conditions=[],
                summary="建议稍后重试或咨询其他信息源"
            )

    def _generate_detailed_analysis(self, hourly_conditions: List[FishingCondition],
                                  sorted_periods: List[Tuple[str, float]]) -> str:
        """生成详细分析"""
        if not hourly_conditions:
            return "无天气数据可供分析"

        analysis_parts = []

        # 总体评价
        avg_score = sum(c.overall_score for c in hourly_conditions) / len(hourly_conditions)
        if avg_score >= 80:
            overall = "非常适合钓鱼"
        elif avg_score >= 60:
            overall = "比较适合钓鱼"
        elif avg_score >= 40:
            overall = "一般适合钓鱼"
        else:
            overall = "不太适合钓鱼"

        analysis_parts.append(f"**总体评价**: {overall} (综合评分: {avg_score:.1f}/100)")

        # 最佳时间段
        if sorted_periods:
            best_period, best_score = sorted_periods[0]
            analysis_parts.append(f"**最佳时间段**: {best_period} (评分: {best_score:.1f}/100)")

        # 温度分析
        temps = [c.temperature for c in hourly_conditions]
        min_temp, max_temp = min(temps), max(temps)
        analysis_parts.append(f"**温度范围**: {min_temp:.1f}°C - {max_temp:.1f}°C")

        # 天气状况
        conditions = [c.condition for c in hourly_conditions]
        condition_count = {}
        for condition in conditions:
            condition_count[condition] = condition_count.get(condition, 0) + 1
        main_condition = max(condition_count, key=condition_count.get)
        analysis_parts.append(f"**主要天气**: {main_condition}")

        return "\n".join(analysis_parts)

    def _generate_summary(self, best_time_slots: List[Tuple[str, float]],
                         hourly_conditions: List[FishingCondition]) -> str:
        """生成总结建议"""
        if not best_time_slots:
            return "今日天气条件不适宜钓鱼，建议改日进行。"

        summary_parts = []

        # 推荐最佳时间
        if best_time_slots:
            best_period_with_range, best_score = best_time_slots[0]
            # 提取纯时间段名称（去掉时间范围）
            best_period = best_period_with_range.split(' ')[0]
            if best_score >= 80:
                summary_parts.append(f"**强烈推荐**在{best_period}钓鱼，条件极佳！")
            elif best_score >= 60:
                summary_parts.append(f"**推荐**在{best_period}钓鱼，条件良好。")
            else:
                summary_parts.append(f"可以考虑在{best_period}钓鱼，但条件一般。")

        # 次佳选择
        if len(best_time_slots) >= 2:
            second_period_with_range, second_score = best_time_slots[1]
            # 提取纯时间段名称（去掉时间范围）
            second_period = second_period_with_range.split(' ')[0]
            if second_score >= 60:
                summary_parts.append(f"次佳选择是{second_period}。")

        # 注意事项
        # 找出条件最差的因素
        temp_scores = [c.temperature_score for c in hourly_conditions]
        weather_scores = [c.weather_score for c in hourly_conditions]
        wind_scores = [c.wind_score for c in hourly_conditions]

        avg_temp_score = sum(temp_scores) / len(temp_scores)
        avg_weather_score = sum(weather_scores) / len(weather_scores)
        avg_wind_score = sum(wind_scores) / len(wind_scores)

        min_score = min(avg_temp_score, avg_weather_score, avg_wind_score)

        if min_score < 50:
            if avg_temp_score == min_score:
                summary_parts.append("**注意**: 温度条件不太理想，请做好保暖或防暑准备。")
            elif avg_weather_score == min_score:
                summary_parts.append("**注意**: 天气条件较差，请做好防护措施。")
            else:
                summary_parts.append("**注意**: 风力较大，请注意安全并调整钓法。")

        return "\n".join(summary_parts)

    def _get_period_weather_summary(self, period_name: str, hourly_conditions: List[FishingCondition]) -> str:
        """
        生成指定时间段的天气摘要

        Args:
            period_name: 时间段名称（如"早上"、"上午"等）
            hourly_conditions: 每小时条件列表

        Returns:
            天气摘要字符串（如"18.2°C 多云 风力3.5km/h 湿度65%"）
        """
        # 筛选指定时间段的小时条件
        period_conditions = [
            cond for cond in hourly_conditions
            if cond.period_name == period_name
        ]

        if not period_conditions:
            return "无数据"

        # 计算平均值
        avg_temp = sum(cond.temperature for cond in period_conditions) / len(period_conditions)
        avg_wind = sum(cond.wind_speed for cond in period_conditions) / len(period_conditions)
        avg_humidity = sum(cond.humidity for cond in period_conditions) / len(period_conditions)

        # 获取最常见的天气状况
        weather_counts = {}
        for cond in period_conditions:
            weather = cond.condition
            weather_counts[weather] = weather_counts.get(weather, 0) + 1

        most_common_weather = max(weather_counts.items(), key=lambda x: x[1])[0]

        # 翻译天气代码为中文
        weather_translation = {
            'CLEAR_DAY': '晴天',
            'CLEAR_NIGHT': '晴夜',
            'PARTLY_CLOUDY_DAY': '多云',
            'PARTLY_CLOUDY_NIGHT': '多云',
            'CLOUDY': '阴天',
            'LIGHT_HAZE': '轻度雾霾',
            'MODERATE_HAZE': '中度雾霾',
            'HEAVY_HAZE': '重度雾霾',
            'LIGHT_RAIN': '小雨',
            'MODERATE_RAIN': '中雨',
            'HEAVY_RAIN': '大雨',
            'STORM_RAIN': '暴雨',
            'LIGHT_SNOW': '小雪',
            'MODERATE_SNOW': '中雪',
            'HEAVY_SNOW': '大雪',
            'STORM_SNOW': '暴雪',
            'DUST': '浮尘',
            'SAND': '沙尘',
            'WIND': '大风'
        }

        chinese_weather = weather_translation.get(most_common_weather, most_common_weather)

        # 格式化天气摘要
        return f"{avg_temp:.1f}°C {chinese_weather} 风力{avg_wind:.1f}km/h 湿度{avg_humidity:.0f}%"

    def _generate_weather_overview(self, hourly_conditions: List[FishingCondition]) -> str:
        """生成天气概况"""
        if not hourly_conditions:
            return "无天气数据"

        # 统计各种天气条件
        weather_counts = {}
        for condition in hourly_conditions:
            weather = condition.condition
            weather_counts[weather] = weather_counts.get(weather, 0) + 1

        # 找出最主要的天气状况
        main_weather = max(weather_counts.items(), key=lambda x: x[1])[0]
        percentage = weather_counts[main_weather] / len(hourly_conditions) * 100

        # 转换天气代码为中文
        weather_translation = {
            'CLEAR_DAY': '晴',
            'CLEAR_NIGHT': '晴',
            'PARTLY_CLOUDY_DAY': '多云',
            'PARTLY_CLOUDY_NIGHT': '多云',
            'CLOUDY': '阴',
            'LIGHT_RAIN': '小雨',
            'MODERATE_RAIN': '中雨',
            'HEAVY_RAIN': '大雨',
            'STORM': '暴雨',
            'LIGHT_SNOW': '小雪',
            'MODERATE_SNOW': '中雪',
            'HEAVY_SNOW': '大雪',
            'FOGGY': '雾'
        }

        chinese_weather = weather_translation.get(main_weather, main_weather)
        return f"{chinese_weather}(占比{percentage:.0f}%)"

    def _generate_temperature_range(self, hourly_conditions: List[FishingCondition]) -> str:
        """生成温度范围"""
        if not hourly_conditions:
            return "无温度数据"

        temperatures = [condition.temperature for condition in hourly_conditions]
        min_temp = min(temperatures)
        max_temp = max(temperatures)

        return f"{min_temp:.1f}°C - {max_temp:.1f}°C"

    def _generate_hourly_data_from_intelligent_router(self, weather_data, date: str) -> List[Dict]:
        """
        从智能路由的EnhancedWeatherData生成24小时数据

        Args:
            weather_data: 智能路由返回的EnhancedWeatherData
            date: 日期字符串

        Returns:
            24小时数据列表
        """
        hourly_data = []

        # 从EnhancedWeatherData中提取基础天气信息
        temp_avg = getattr(weather_data, 'temperature', 20.0)
        condition = getattr(weather_data, 'condition', '多云')
        wind_speed = getattr(weather_data, 'wind_speed', 3.0)
        humidity = getattr(weather_data, 'humidity', 60.0)
        pressure = getattr(weather_data, 'pressure', 1013.0)

        # 获取置信度
        confidence = getattr(weather_data, 'confidence', 1.0)

        # 获取元数据中的额外信息
        metadata = getattr(weather_data, 'metadata', {})
        data_source = metadata.get('data_source', 'unknown')

        # 根据日期计算days_from_now，而不是从元数据获取
        from services.weather.utils.datetime_utils import calculate_days_from_now
        try:
            days_from_now = calculate_days_from_now(date)
        except:
            days_from_now = 0

        # 根据数据源调整数据质量
        if data_source == 'hourly_api':
            data_quality = 1.0
            temp_variation = 5.0
        elif data_source == 'daily_api':
            data_quality = 0.85
            temp_variation = 8.0
        elif data_source == 'simulation':
            data_quality = 0.6
            temp_variation = 12.0
        else:
            data_quality = 0.7
            temp_variation = 10.0

        # 获取温度范围
        temp_min = temp_avg - temp_variation / 2
        temp_max = temp_avg + temp_variation / 2

        # 生成24小时数据，支持相对日期
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            # 处理相对日期
            from services.weather.utils.datetime_utils import calculate_days_from_now
            days_from_now = calculate_days_from_now(date)
            target_date = datetime.now() + timedelta(days=days_from_now)

        for hour in range(24):
            # 计算小时的温度变化
            if 6 <= hour <= 14:
                # 上午到下午，温度上升
                progress = (hour - 6) / 8
                temp = temp_min + (temp_max - temp_min) * progress
            else:
                # 下午到次日早晨，温度下降
                if hour > 14:
                    progress = (24 - hour) / 10
                else:  # 0-6点
                    progress = (hour + 10) / 10
                temp = temp_min + (temp_max - temp_min) * progress

            # 添加随机变化
            temp += random.gauss(0, temp_variation * 0.1)

            # 计算风速和湿度的变化
            hour_wind = wind_speed * (0.7 + 0.6 * math.sin(hour * math.pi / 12))
            hour_humidity = humidity - (temp - temp_avg) * 2 + random.gauss(0, 5)
            hour_humidity = max(20, min(95, hour_humidity))

            # 根据时间和天气状况调整
            hour_data = {
                'datetime': target_date.replace(hour=hour, minute=0, second=0).isoformat(),
                'temperature': round(temp, 1),
                'condition': condition,
                'wind_speed': round(max(0, hour_wind), 1),
                'humidity': round(hour_humidity, 1),
                'pressure': round(pressure + random.gauss(0, 5), 1),
                'hour': hour,
                'data_source': data_source,
                'confidence': confidence * data_quality,
                'days_from_now': days_from_now
            }

            hourly_data.append(hour_data)

        self._logger.debug(f"从智能路由数据生成了{len(hourly_data)}小时数据: {data_source}")
        return hourly_data


# 全局分析器实例
_fishing_analyzer = FishingAnalyzer()


async def find_best_fishing_time(location: str, date: str = None) -> str:
    """
    找出最佳钓鱼时间的工具函数

    Args:
        location: 地点名称
        date: 日期 (可选，默认为明天)

    Returns:
        JSON格式的钓鱼推荐结果
    """
    try:
        recommendation = await _fishing_analyzer.find_best_fishing_time(location, date)
        result_dict = recommendation.to_dict()

        return json.dumps(result_dict, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "error": f"钓鱼时间分析失败: {str(e)}",
            "location": location,
            "date": date or "明天"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)