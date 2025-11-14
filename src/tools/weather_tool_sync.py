"""
LangChain Learning - Weather Tool (同步版本)

天气工具模块提供天气查询和预报功能，集成彩云天气API。
使用分层日志系统，支持Normal/Debug/Error三种模式。
"""

import os
import requests
import json
import time
from typing import Optional, Any, Dict, Union, List, Tuple
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import wraps

# 导入服务
from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService
from services.weather.datetime_weather_service import DateTimeWeatherService
from services.weather.hourly_weather_service_sync import HourlyWeatherService

# 导入分层日志系统
try:
    from services.logging.hierarchical_logger import HierarchicalLogger, hierarchical_log_function
    from services.logging.hierarchical_logger_config import LogMode, default_hierarchical_config
except ImportError:
    # 如果分层日志系统不可用，使用基础日志
    HierarchicalLogger = None
    hierarchical_log_function = None
    LogMode = None
    default_hierarchical_config = None

# 基础日志配置
logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class WeatherTool:
    """天气工具类 - 同步版本（分层日志）"""

    def __init__(self, name: str = "weather_tool"):
        """初始化天气工具"""
        self.name = name
        self._log_layer = "tool"

        # 初始化分层日志系统
        if HierarchicalLogger:
            self._logger = HierarchicalLogger(f"weather.{name}", self._log_layer)
            self._hierarchical_config = self._logger.get_config()
        else:
            # 回退到基础日志
            self._logger = logging.getLogger(f"{__name__}.{name}")
            self._hierarchical_config = None

        # 记录初始化开始
        init_start = time.time()
        self._logger.info(f"🔧 开始初始化 WeatherTool (同步版本): {name}")

        # 初始化服务
        self._logger.debug("🔧 开始初始化服务...")
        self.enhanced_service = EnhancedCaiyunWeatherService()
        self.datetime_service = DateTimeWeatherService()
        self.hourly_service = HourlyWeatherService()
        self._logger.info("✅ 所有服务初始化完成")

        # 缓存统计
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }

        init_time = time.time() - init_start
        self._logger.info(f"✅ WeatherTool (同步版本) 初始化完成 ({init_time:.3f}s)")

    def _apply_hierarchical_decorator(self, func):
        """应用分层日志装饰器"""
        if hierarchical_log_function and self._hierarchical_config:
            return hierarchical_log_function(func)
        else:
            # 回退到基础装饰器
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                start_time = time.time()
                self._logger.info(f"🚀 开始执行 {func.__name__}")
                try:
                    result = func(self, *args, **kwargs)
                    execution_time = time.time() - start_time
                    self._logger.info(f"✅ {func.__name__} 执行成功 ({execution_time:.3f}s)")
                    return result
                except Exception as e:
                    self._logger.error(f"❌ {func.__name__} 执行失败: {str(e)}")
                    raise
            return wrapper

    def execute(self, operation: str, **kwargs) -> ToolResult:
        """执行天气操作 - 同步版本（分层日志）"""
        # 记录操作开始
        self._logger.info(f"🎯 开始执行操作: {operation}")

        try:
            if operation == "current_weather":
                return self._current_weather(**kwargs)
            elif operation == "weather_by_date":
                return self._weather_by_date(**kwargs)
            elif operation == "weather_by_datetime":
                return self._weather_by_datetime(**kwargs)
            elif operation == "hourly_forecast":
                return self._hourly_forecast(**kwargs)
            elif operation == "time_period_weather":
                return self._time_period_weather(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {operation}"
                )

        except Exception as e:
            self._logger.error(f"天气工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"天气工具执行失败: {str(e)}"
            )

    def _current_weather(self, location: str, **kwargs) -> ToolResult:
        """获取当前天气（分层日志版本）"""
        # 更新统计
        self._cache_stats['total_requests'] += 1

        # 根据日志模式决定输出详细程度
        if self._hierarchical_config and self._hierarchical_config.should_show_details('tool', 'tool_details'):
            self._logger.info(f"🌤️ 开始获取 {location} 的当前天气 (同步版本)")
        else:
            # Normal模式下只显示简洁信息
            self._logger.info(f"查询 {location} 天气")

        try:
            # 使用增强版天气服务
            if self._hierarchical_config and self._hierarchical_config.mode == LogMode.DEBUG:
                self._logger.debug(f"🔧 调用增强版天气服务: {location}")

            service_start_time = time.time()
            weather_data, source = self.enhanced_service.get_weather(location)
            service_time = time.time() - service_start_time

            # 根据模式记录不同详细程度的信息
            if self._hierarchical_config and self._hierarchical_config.mode == LogMode.DEBUG:
                self._logger.info(f"✅ 增强版天气服务完成: {location} ({service_time:.3f}s)")
                self._logger.debug(f"📋 服务响应: {weather_data.condition}, {weather_data.temperature}°C")

                # 记录性能指标
                if self._hierarchical_config.should_show_details('tool', 'performance_metrics'):
                    self._logger.log_performance_metrics(
                        f"weather_query_{location}",
                        {
                            "service_time": service_time,
                            "temperature": weather_data.temperature,
                            "api_calls": 1
                        }
                    )

                # 记录缓存信息
                if hasattr(self.enhanced_service, 'get_cache_info'):
                    cache_info = self.enhanced_service.get_cache_info()
                    hit_rate = cache_info.get('hit_rate', 0)
                    self._logger.log_cache_info(f"weather_query_{location}", False, hit_rate)
            else:
                # Normal模式只显示简洁结果
                self._logger.info(f"✅ {location}: {weather_data.condition}, {weather_data.temperature}°C")

            # 转换为统一的返回格式
            result_data = {
                'temperature': weather_data.temperature,
                'apparent_temperature': weather_data.apparent_temperature,
                'humidity': weather_data.humidity,
                'pressure': weather_data.pressure,
                'wind_speed': weather_data.wind_speed,
                'wind_direction': weather_data.wind_direction,
                'condition': weather_data.condition,
                'description': weather_data.description,
                'source': source,
                'location': location
            }

            # 构建元数据
            metadata = {
                "operation": "current_weather",
                "source": source,
                "service_time_ms": service_time * 1000
            }

            if hasattr(self.enhanced_service, 'get_cache_info'):
                cache_info = self.enhanced_service.get_cache_info()
                metadata['cache_hit_rate'] = cache_info.get('hit_rate', 0)

            return ToolResult(
                success=True,
                data=result_data,
                metadata=metadata
            )

        except Exception as e:
            self._logger.error(f"获取当前天气失败: {str(e)}")
            # 使用模拟数据
            fallback_data = self._create_fallback_weather(location)
            return ToolResult(
                success=True,
                data=asdict(fallback_data),
                metadata={"operation": "current_weather", "source": "fallback", "error": str(e)}
            )

    def _weather_by_date(self, location: str, date: str = "today", **kwargs) -> ToolResult:
        """查询指定日期天气"""
        try:
            weather_data, source, status_code = self.datetime_service.get_weather_by_date(location, date)

            if weather_data and status_code == 0:  # 0 表示成功
                return ToolResult(
                    success=True,
                    data={
                        'temperature': weather_data.temperature,
                        'humidity': weather_data.humidity,
                        'condition': weather_data.condition,
                        'description': weather_data.description,
                        'date': date,
                        'source': source,
                        'location': location
                    },
                    metadata={
                        "operation": "weather_by_date",
                        "source": source,
                        "date": date,
                        "status_code": status_code
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"查询{location}{date}天气失败: status_code={status_code}"
                )

        except Exception as e:
            self._logger.error(f"查询指定日期天气失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"查询指定日期天气失败: {str(e)}"
            )

    def _weather_by_datetime(self, location: str, datetime_str: str, **kwargs) -> ToolResult:
        """查询指定时间段天气"""
        try:
            # 简化实现，直接返回模拟数据
            import random
            import re

            # 解析时间段
            time_period = "全天"
            if "上午" in datetime_str:
                time_period = "上午"
            elif "下午" in datetime_str:
                time_period = "下午"
            elif "晚上" in datetime_str:
                time_period = "晚上"
            elif "早上" in datetime_str:
                time_period = "早上"
            elif "中午" in datetime_str:
                time_period = "中午"

            base_temp = random.uniform(15, 25)
            conditions = ['晴', '多云', '阴', '小雨']

            return ToolResult(
                success=True,
                data={
                    'temperature': round(base_temp, 1),
                    'temperature_avg': round(base_temp, 1),
                    'temperature_min': round(base_temp - 3, 1),
                    'temperature_max': round(base_temp + 3, 1),
                    'humidity': random.uniform(50, 70),
                    'humidity_avg': random.uniform(50, 70),
                    'condition': random.choice(conditions),
                    'condition_primary': random.choice(conditions),
                    'wind_speed': random.uniform(5, 15),
                    'wind_speed_avg': random.uniform(5, 15),
                    'description': f"{location}{datetime_str}模拟天气：{random.choice(conditions)}",
                    'time_period': time_period,
                    'date': datetime_str,
                    'source': '模拟数据',
                    'location': location
                },
                metadata={
                    "operation": "weather_by_datetime",
                    "source": "simulation",
                    "datetime": datetime_str
                }
            )

        except Exception as e:
            self._logger.error(f"查询指定时间段天气失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"查询指定时间段天气失败: {str(e)}"
            )

    def _hourly_forecast(self, location: str, hours: int = 24, **kwargs) -> ToolResult:
        """查询小时级预报"""
        try:
            # 简化实现，生成模拟的小时级预报数据
            import random
            from datetime import datetime, timedelta

            hourly_data = []
            base_temp = random.uniform(15, 25)

            for i in range(min(hours, 24)):  # 最多24小时
                hour_time = datetime.now() + timedelta(hours=i)
                # 温度变化模式
                temp_variation = 0
                if 6 <= hour_time.hour <= 14:
                    temp_variation = (hour_time.hour - 6) * 1.5
                elif 14 < hour_time.hour <= 20:
                    temp_variation = (20 - hour_time.hour) * 0.8
                else:
                    temp_variation = -5

                hourly_temp = base_temp + temp_variation

                hourly_data.append({
                    'datetime': hour_time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
                    'hour': hour_time.hour,
                    'temperature': round(hourly_temp, 1),
                    'humidity': random.uniform(40, 80),
                    'condition': random.choice(['晴', '多云', '阴']),
                    'precipitation': 0.0
                })

            return ToolResult(
                success=True,
                data={
                    'hourly_data': hourly_data,
                    'forecast_hours': len(hourly_data),
                    'source': '模拟数据',
                    'location': location,
                    'confidence': 0.6
                },
                metadata={
                    "operation": "hourly_forecast",
                    "source": "simulation",
                    "hours": hours
                }
            )

        except Exception as e:
            self._logger.error(f"查询小时级预报失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"查询小时级预报失败: {str(e)}"
            )

    def _time_period_weather(self, location: str, date: str, time_period: str, **kwargs) -> ToolResult:
        """查询指定日期时间段天气"""
        try:
            # 简化实现，返回模拟数据
            import random

            base_temp = random.uniform(15, 25)
            conditions = ['晴', '多云', '阴', '小雨']

            return ToolResult(
                success=True,
                data={
                    'temperature': round(base_temp, 1),
                    'temperature_avg': round(base_temp, 1),
                    'temperature_min': round(base_temp - 3, 1),
                    'temperature_max': round(base_temp + 3, 1),
                    'humidity': random.uniform(50, 70),
                    'humidity_avg': random.uniform(50, 70),
                    'condition': random.choice(conditions),
                    'condition_primary': random.choice(conditions),
                    'wind_speed': random.uniform(5, 15),
                    'wind_speed_avg': random.uniform(5, 15),
                    'description': f"{location}{date}{time_period}模拟天气：{random.choice(conditions)}",
                    'time_period': time_period,
                    'date': date,
                    'source': '模拟数据',
                    'location': location
                },
                metadata={
                    "operation": "time_period_weather",
                    "source": "simulation",
                    "date": date,
                    "time_period": time_period
                }
            )

        except Exception as e:
            self._logger.error(f"查询时间段天气失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"查询时间段天气失败: {str(e)}"
            )

    def _create_fallback_weather(self, location: str):
        """创建模拟天气数据"""
        from services.weather.weather_service import WeatherData

        # 基于位置的简单模拟数据
        import random

        # 根据城市名称生成不同的温度范围
        city_temps = {
            '北京': (5, 15),
            '上海': (10, 20),
            '广州': (15, 25),
            '深圳': (18, 28),
            '杭州': (8, 18)
        }

        temp_range = city_temps.get(location, (10, 20))
        base_temp = random.uniform(*temp_range)

        conditions = ['晴', '多云', '阴', '小雨', '中雨']
        condition = random.choice(conditions)

        return WeatherData(
            temperature=round(base_temp, 1),
            apparent_temperature=round(base_temp - 2, 1),
            humidity=random.uniform(40, 80),
            pressure=random.uniform(1000, 1020),
            wind_speed=random.uniform(0, 15),
            wind_direction=random.uniform(0, 360),
            condition=condition,
            description=f"{location}模拟天气：{condition}，温度{base_temp:.1f}°C"
        )

    def close(self):
        """关闭工具，清理资源"""
        try:
            if hasattr(self, 'enhanced_service') and self.enhanced_service:
                if hasattr(self.enhanced_service, 'place_matcher') and self.enhanced_service.place_matcher:
                    self.enhanced_service.place_matcher.close()

            if hasattr(self, 'hourly_service') and self.hourly_service:
                self.hourly_service.close()

            self._logger.info(f"工具 {self.name} 已关闭")
        except Exception as e:
            self._logger.error(f"关闭工具时出错: {e}")