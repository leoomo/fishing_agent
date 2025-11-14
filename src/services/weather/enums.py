"""
天气API相关的枚举定义
"""
from enum import Enum


class ForecastRange(Enum):
    """天气预报范围枚举"""
    HOURLY = "hourly"        # 0-3天：逐小时预报
    DAILY = "daily"          # 3-7天：逐天预报
    SIMULATION = "simulation"  # 7天+：模拟数据


class WeatherErrorCode(Enum):
    """天气服务错误码"""
    SUCCESS = 0              # 成功
    CACHE_HIT = 1            # 缓存命中
    NETWORK_ERROR = 2        # 网络错误
    API_ERROR = 3            # API错误
    DATA_ERROR = 4           # 数据错误
    LOCATION_ERROR = 5       # 地理位置错误
    DATE_OUT_OF_RANGE = 6    # 日期超出范围
    QUOTA_EXCEEDED = 7       # API配额超限


class WeatherDataSource(Enum):
    """天气数据源枚举"""
    HOURLY_API = "hourly_api"           # 逐小时API
    DAILY_API = "daily_api"             # 逐天API
    SIMULATION = "simulation"           # 模拟数据
    CACHE = "cache"                     # 缓存数据
    FALLBACK = "fallback"               # 回退数据
    EMERGENCY = "emergency_fallback"    # 紧急回退
    HISTORICAL = "historical_estimate"  # 历史数据估算