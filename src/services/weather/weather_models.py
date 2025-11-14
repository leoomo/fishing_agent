#!/usr/bin/env python3
"""
扩展天气数据模型
支持日期时间、时间粒度、历史数据和预报数据
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

# 导入基础模型
try:
    from .weather_service import WeatherData
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from weather_service import WeatherData


class WeatherDataType(Enum):
    """天气数据类型枚举"""
    CURRENT = "current"      # 当前天气
    HISTORICAL = "historical" # 历史天气
    HOURLY_FORECAST = "hourly_forecast"  # 小时预报
    DAILY_FORECAST = "daily_forecast"    # 日预报
    TIME_PERIOD = "time_period"  # 时间段聚合数据


@dataclass
class EnhancedWeatherData:
    """增强版天气数据类，包含基础WeatherData的所有字段"""

    # 基础天气数据字段
    temperature: float                          # 温度 (摄氏度)
    apparent_temperature: float                 # 体感温度 (摄氏度)
    humidity: float                             # 湿度 (百分比)
    pressure: float                             # 气压 (hPa)
    wind_speed: float                           # 风速 (km/h)
    wind_direction: float                       # 风向 (度)
    condition: str                              # 天气状况
    description: str                            # 天气描述
    location: str                               # 位置
    timestamp: float                            # 时间戳
    source: str                                 # 数据源

    # 新增字段
    datetime: Optional[datetime] = None          # 具体日期时间
    date_str: Optional[str] = None               # 日期字符串 (YYYY-MM-DD)
    time_period: Optional[str] = None            # 时间段（上午、下午等）
    data_type: str = WeatherDataType.CURRENT.value  # 数据类型

    # 时间相关字段
    forecast_hours: int = 0                      # 预报小时数（用于预报数据）
    is_aggregated: bool = False                  # 是否为聚合数据（时间段）

    # API相关字段
    api_source: str = "caiyun"                  # API数据源
    api_version: str = "v2.6"                    # API版本
    original_response: Optional[Dict] = None     # 原始API响应

    # 元数据
    created_at: 'datetime' = field(default_factory=lambda: datetime.now())
    updated_at: 'datetime' = field(default_factory=lambda: datetime.now())
    cache_key: Optional[str] = None             # 缓存键
    confidence: float = 1.0                     # 数据置信度 (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def __post_init__(self):
        """初始化后处理"""
        if self.datetime and not self.date_str:
            self.date_str = self.datetime.strftime('%Y-%m-%d')

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    @classmethod
    def from_base_weather_data(cls, base_data, **kwargs) -> 'EnhancedWeatherData':
        """从基础WeatherData创建增强版"""
        return cls(
            temperature=getattr(base_data, 'temperature', 0),
            apparent_temperature=getattr(base_data, 'apparent_temperature', 0),
            humidity=getattr(base_data, 'humidity', 0),
            pressure=getattr(base_data, 'pressure', 0),
            wind_speed=getattr(base_data, 'wind_speed', 0),
            wind_direction=getattr(base_data, 'wind_direction', 0),
            condition=getattr(base_data, 'condition', ''),
            description=getattr(base_data, 'description', ''),
            location=getattr(base_data, 'location', ''),
            timestamp=getattr(base_data, 'timestamp', 0),
            source=getattr(base_data, 'source', ''),
            **kwargs
        )


@dataclass
class HourlyWeatherData:
    """小时级天气数据"""

    datetime: datetime                           # 时间
    temperature: float                          # 温度
    apparent_temperature: float                 # 体感温度
    humidity: float                             # 湿度
    pressure: float                             # 气压
    wind_speed: float                           # 风速
    wind_direction: float                       # 风向
    condition: str                              # 天气状况
    precipitation_probability: float = 0.0      # 降水概率
    precipitation_value: float = 0.0            # 降水量
    cloud_rate: float = 0.0                     # 云量
    visibility: float = 0.0                     # 能见度
    aqi: Optional[Dict[str, int]] = None        # 空气质量指数
    pm25: Optional[float] = None                # PM2.5浓度

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


@dataclass
class TimePeriodWeatherData:
    """时间段天气数据（聚合后）"""

    location: str                               # 位置
    date: str                                   # 日期 (YYYY-MM-DD)
    time_period: str                            # 时间段
    start_time: datetime                        # 开始时间
    end_time: datetime                          # 结束时间

    # 温度数据
    temperature_avg: float                      # 平均温度
    temperature_min: float                      # 最低温度
    temperature_max: float                      # 最高温度

    # 降水数据
    precipitation_total: float = 0.0            # 总降水量
    precipitation_probability_max: float = 0.0  # 最大降水概率

    # 风数据
    wind_speed_avg: float = 0.0                 # 平均风速
    wind_direction_avg: float = 0.0             # 平均风向

    # 其他数据
    humidity_avg: float = 0.0                   # 平均湿度
    pressure_avg: float = 0.0                   # 平均气压
    condition_primary: str = ""                  # 主要天气状况

    # 元数据
    hours_count: int = 0                        # 聚合的小时数
    data_source: str = "aggregated"             # 数据源
    created_at: 'datetime' = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


@dataclass
class WeatherForecast:
    """天气预报数据"""

    location: str                               # 位置
    forecast_type: str                          # 预报类型 (hourly/daily)
    created_at: 'datetime' = field(default_factory=lambda: datetime.now())

    # 小时预报数据
    hourly_data: List[HourlyWeatherData] = field(default_factory=list)

    # 日预报数据（如果适用）
    daily_data: List[EnhancedWeatherData] = field(default_factory=list)

    # 预报元信息
    forecast_hours: int = 0                     # 预报小时总数
    source: str = "caiyun_api"                  # 数据源

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "location": self.location,
            "forecast_type": self.forecast_type,
            "created_at": self.created_at.isoformat(),
            "hourly_data": [data.to_dict() for data in self.hourly_data],
            "daily_data": [data.to_dict() for data in self.daily_data],
            "forecast_hours": self.forecast_hours,
            "source": self.source
        }

    def get_hourly_range(self, start_hour: int = 0, end_hour: Optional[int] = None) -> List[HourlyWeatherData]:
        """获取指定小时范围的预报数据"""
        if end_hour is None:
            end_hour = len(self.hourly_data)

        return self.hourly_data[start_hour:end_hour]

    def get_data_for_time_period(self, time_period: str, date: datetime) -> TimePeriodWeatherData:
        """获取指定时间段的数据"""
        try:
            from .datetime_utils import TimeGranularityParser
        except ImportError:
            from datetime_utils import TimeGranularityParser

        parser = TimeGranularityParser()
        hours = parser.get_covering_hours(time_period, date)

        # 筛选对应小时的数据
        period_data = []
        for hourly in self.hourly_data:
            if hourly.datetime.hour in hours and hourly.datetime.date() == date.date():
                period_data.append(hourly)

        if not period_data:
            raise ValueError(f"未找到 {date.strftime('%Y-%m-%d')} {time_period} 的数据")

        # 聚合数据
        return self._aggregate_period_data(period_data, time_period, date)

    def _aggregate_period_data(self, hourly_data: List[HourlyWeatherData],
                               time_period: str, date: datetime) -> TimePeriodWeatherData:
        """聚合时间段数据"""
        if not hourly_data:
            raise ValueError("没有数据可以聚合")

        try:
            from .datetime_utils import TimeGranularityParser
        except ImportError:
            from datetime_utils import TimeGranularityParser
        parser = TimeGranularityParser()
        start_time, end_time = parser.get_time_range(time_period, date)

        # 计算平均值
        temps = [d.temperature for d in hourly_data]
        apparent_temps = [d.apparent_temperature for d in hourly_data]
        humidities = [d.humidity for d in hourly_data]
        pressures = [d.pressure for d in hourly_data]
        wind_speeds = [d.wind_speed for d in hourly_data]
        precipitations = [d.precipitation_value for d in hourly_data]
        precip_probs = [d.precipitation_probability for d in hourly_data]

        # 统计天气状况
        conditions = [d.condition for d in hourly_data]
        condition_counts = {}
        for condition in conditions:
            condition_counts[condition] = condition_counts.get(condition, 0) + 1

        primary_condition = max(condition_counts, key=condition_counts.get)

        return TimePeriodWeatherData(
            location=hourly_data[0].location if hasattr(hourly_data[0], 'location') else "未知",
            date=date.strftime('%Y-%m-%d'),
            time_period=time_period,
            start_time=start_time,
            end_time=end_time,
            temperature_avg=sum(temps) / len(temps),
            temperature_min=min(temps),
            temperature_max=max(temps),
            precipitation_total=sum(precipitations),
            precipitation_probability_max=max(precip_probs),
            wind_speed_avg=sum(wind_speeds) / len(wind_speeds),
            wind_direction_avg=sum(d.wind_direction for d in hourly_data) / len(hourly_data),
            humidity_avg=sum(humidities) / len(humidities),
            pressure_avg=sum(pressures) / len(pressures),
            condition_primary=primary_condition,
            hours_count=len(hourly_data),
            data_source="aggregated_hourly"
        )


@dataclass
class WeatherQuery:
    """天气查询请求"""

    location: str                              # 位置
    date: Optional[str] = None                 # 日期 (YYYY-MM-DD)
    time_period: Optional[str] = None         # 时间段
    forecast_hours: int = 24                  # 预报小时数
    include_hourly: bool = True               # 是否包含小时数据
    data_type: str = WeatherDataType.CURRENT.value  # 数据类型

    # 查询参数
    language: str = "zh_CN"                    # 语言
    units: str = "metric"                      # 单位制

    def to_cache_key(self) -> str:
        """生成缓存键"""
        parts = [self.location]

        if self.date:
            parts.append(self.date)
        else:
            parts.append("current")

        if self.time_period:
            parts.append(self.time_period)

        parts.append(f"hours_{self.forecast_hours}")
        parts.append(self.data_type)

        return ":".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "location": self.location,
            "date": self.date,
            "time_period": self.time_period,
            "forecast_hours": self.forecast_hours,
            "include_hourly": self.include_hourly,
            "data_type": self.data_type,
            "language": self.language,
            "units": self.units
        }


# 工厂函数
def create_enhanced_weather_data(base_data: WeatherData, **kwargs) -> EnhancedWeatherData:
    """创建增强版天气数据"""
    return EnhancedWeatherData.from_base_weather_data(base_data, **kwargs)


def create_hourly_weather_data_from_api(api_data: Dict, location: str) -> HourlyWeatherData:
    """从API数据创建小时天气数据"""
    return HourlyWeatherData(
        datetime=datetime.fromisoformat(api_data["datetime"].replace('Z', '+00:00')),
        temperature=api_data.get("temperature", 0),
        apparent_temperature=api_data.get("apparent_temperature", 0),
        humidity=api_data.get("humidity", 0),
        pressure=api_data.get("pressure", 0),
        wind_speed=api_data.get("wind", {}).get("speed", 0),
        wind_direction=api_data.get("wind", {}).get("direction", 0),
        condition=api_data.get("skycon", ""),
        precipitation_probability=api_data.get("precipitation", {}).get("probability", 0),
        precipitation_value=api_data.get("precipitation", {}).get("value", 0),
        cloud_rate=api_data.get("cloudrate", 0),
        visibility=api_data.get("visibility", 0),
        aqi=api_data.get("air_quality", {}).get("aqi"),
        pm25=api_data.get("air_quality", {}).get("pm25")
    )


def create_time_period_weather_data(hourly_data: List[HourlyWeatherData],
                                   time_period: str, date: datetime) -> TimePeriodWeatherData:
    """从小时数据创建时间段天气数据"""
    if not hourly_data:
        raise ValueError("没有小时数据可以聚合")

    # 这里调用WeatherForecast类的聚合方法
    forecast = WeatherForecast(location="", forecast_type="hourly")
    forecast.hourly_data = hourly_data
    return forecast.get_data_for_time_period(time_period, date)