"""
LangChain Learning - Weather Tool (同步版本)

天气工具模块提供天气查询和预报功能，集成彩云天气API。
使用分层日志系统，支持Normal/Debug/Error三种模式。
"""

import os
import sys
import requests
import json
import time
import argparse
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
        """查询指定时间段天气，基于缓存的hourly_forecast数据"""
        try:
            # 首先尝试从缓存的hourly_forecast数据中获取
            hourly_result = self._hourly_forecast(location, hours=24, **kwargs)

            if hourly_result.success and hourly_result.data:
                hourly_data = hourly_result.data.get('hourly_forecast', [])

                if hourly_data:
                    # 解析日期时间表达式
                    from datetime import datetime, timedelta
                    import re

                    target_datetime = None
                    time_period = None

                    # 简单的日期时间解析
                    if datetime_str:
                        # 处理相对时间表达
                        if "今天" in datetime_str:
                            target_datetime = datetime.now()
                        elif "明天" in datetime_str:
                            target_datetime = datetime.now() + timedelta(days=1)
                        elif "后天" in datetime_str:
                            target_datetime = datetime.now() + timedelta(days=2)
                        else:
                            # 尝试解析具体日期时间
                            try:
                                # 简单格式解析
                                if re.match(r'\d{4}-\d{2}-\d{2}', datetime_str):
                                    target_datetime = datetime.strptime(datetime_str[:10], '%Y-%m-%d')
                            except ValueError:
                                pass

                        # 解析时间段
                        if "上午" in datetime_str:
                            time_period = "morning"
                        elif "下午" in datetime_str:
                            time_period = "afternoon"
                        elif "晚上" in datetime_str or "夜间" in datetime_str:
                            time_period = "evening"
                        elif "凌晨" in datetime_str:
                            time_period = "early_morning"

                    if target_datetime:
                        # 从小时数据中筛选匹配的时间段
                        filtered_data = []
                        target_date = target_datetime.date()

                        for hour_info in hourly_data:
                            hour_dt = datetime.fromisoformat(hour_info.get('datetime', '').replace('Z', '+00:00'))
                            if hour_dt.date() == target_date:
                                # 根据时间段筛选
                                hour = hour_dt.hour
                                if time_period == "early_morning" and 0 <= hour < 6:
                                    filtered_data.append(hour_info)
                                elif time_period == "morning" and 6 <= hour < 12:
                                    filtered_data.append(hour_info)
                                elif time_period == "afternoon" and 12 <= hour < 18:
                                    filtered_data.append(hour_info)
                                elif time_period == "evening" and 18 <= hour < 24:
                                    filtered_data.append(hour_info)
                                elif time_period is None:
                                    # 如果没有指定时间段，返回当天所有数据
                                    filtered_data.append(hour_info)

                        if filtered_data:
                            # 计算聚合数据
                            temps = [h.get('temperature', 0) for h in filtered_data if h.get('temperature') is not None]
                            humidities = [h.get('humidity', 0) for h in filtered_data if h.get('humidity') is not None]
                            wind_speeds = [h.get('wind_speed', 0) for h in filtered_data if h.get('wind_speed') is not None]
                            conditions = [h.get('condition', '未知') for h in filtered_data]

                            avg_temp = sum(temps) / len(temps) if temps else 0
                            avg_humidity = sum(humidities) / len(humidities) if humidities else 0
                            avg_wind_speed = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0
                            primary_condition = max(set(conditions), key=conditions.count) if conditions else "未知"

                            return ToolResult(
                                success=True,
                                data={
                                    'location': location,
                                    'datetime': datetime_str,
                                    'date': target_datetime.strftime('%Y-%m-%d'),
                                    'time_period': time_period or '全天',
                                    'temperature': round(avg_temp, 1),
                                    'humidity': round(avg_humidity, 1),
                                    'wind_speed': round(avg_wind_speed, 1),
                                    'condition': primary_condition,
                                    'description': f"{primary_condition}，平均温度{avg_temp:.1f}°C",
                                    'hourly_count': len(filtered_data),
                                    'data_points': filtered_data[:3],  # 返回前3个数据点作为示例
                                    'source': hourly_result.data.get('source', 'hourly_api'),
                                    'confidence': hourly_result.data.get('confidence', 0.9)
                                },
                                metadata={
                                    "operation": "weather_by_datetime",
                                    "source": "cached_hourly_forecast",
                                    "datetime": datetime_str,
                                    "location": location,
                                    "original_hours": len(hourly_data),
                                    "filtered_hours": len(filtered_data)
                                }
                            )

            # 如果没有找到数据，返回友好错误
            self._logger.warning(f"无法从缓存数据中获取指定时间段天气: {location} {datetime_str}")
            return ToolResult(
                success=False,
                error=f"无法获取 {location} {datetime_str} 的天气信息，请先查询小时级预报或检查日期时间格式",
                metadata={
                    "operation": "weather_by_datetime",
                    "source": "error",
                    "datetime": datetime_str,
                    "location": location,
                    "reason": "no_cached_data",
                    "suggestion": "请先使用 hourly_forecast 查询该地区的小时级天气预报"
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
            # 使用小时级天气预报服务
            from src.services.weather.enhanced_weather_service import get_enhanced_weather_service
            enhanced_service = get_enhanced_weather_service()

            # 获取坐标
            coordinates = enhanced_service.get_coordinates(location)
            if not coordinates:
                return ToolResult(
                    success=False,
                    error=f"未找到地区 '{location}' 的坐标信息",
                    metadata={"operation": "hourly_forecast", "location": location}
                )

            longitude, latitude = coordinates

            # 调用小时级天气预报服务
            from src.services.weather.hourly_weather_service_sync import HourlyWeatherService
            hourly_service = HourlyWeatherService()

            # 使用明天作为默认查询日期
            from datetime import datetime, timedelta
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            location_info = {
                'name': location,
                'lng': longitude,
                'lat': latitude
            }

            weather_result = hourly_service.get_forecast(location_info, tomorrow)

            if weather_result.error_code == 0 and weather_result.hourly_data:
                # 成功获取数据
                hourly_data = weather_result.hourly_data[:hours]  # 限制返回的小时数

                return ToolResult(
                    success=True,
                    data={
                        'location': location,
                        'date': tomorrow,
                        'hourly_forecast': hourly_data,
                        'source': weather_result.data_source,
                        'confidence': weather_result.confidence,
                        'description': weather_result.metadata.get('description', ''),
                        'forecast_keypoint': weather_result.metadata.get('forecast_keypoint', '')
                    },
                    metadata={
                        "operation": "hourly_forecast",
                        "source": weather_result.data_source,
                        "confidence": weather_result.confidence,
                        "forecast_hours": len(hourly_data)
                    }
                )
            else:
                # API查询失败
                return ToolResult(
                    success=False,
                    error=weather_result.error_message or "小时级预报查询失败",
                    metadata={
                        "operation": "hourly_forecast",
                        "source": "api_error",
                        "location": location,
                        "error_code": weather_result.error_code
                    }
                )

        except Exception as e:
            self._logger.error(f"查询小时级预报失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"查询小时级预报失败: {str(e)}"
            )

    def _time_period_weather(self, location: str, date: str, time_period: str, **kwargs) -> ToolResult:
        """查询指定日期时间段天气，基于缓存的hourly_forecast数据"""
        try:
            # 首先尝试从缓存的hourly_forecast数据中获取
            hourly_result = self._hourly_forecast(location, hours=48, **kwargs)
            if hourly_result.success and hourly_result.data:
                hourly_data = hourly_result.data.get('hourly_forecast', [])
                if hourly_data:
                    self._logger.info(f"✅ 从缓存获取到 {len(hourly_data)} 小时预报数据，用于时间段查询")
                    return self._filter_hourly_data_for_time_period(location, date, time_period, hourly_data)

            self._logger.warning(f"时间段天气服务查询失败，没有可用的缓存数据: {location} {date} {time_period}")
            return ToolResult(
                success=False,
                error="天气服务查询失败，没有可用的缓存数据，请先查询小时级预报",
                metadata={
                    "operation": "time_period_weather",
                    "source": "error",
                    "location": location,
                    "date": date,
                    "time_period": time_period,
                    "reason": "no_cached_hourly_data"
                }
            )

        except Exception as e:
            self._logger.error(f"查询时间段天气失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"查询时间段天气失败: {str(e)}"
            )

    def _create_fallback_weather(self, location: str):
        """创建错误天气数据，不再生成模拟数据"""
        from services.weather.weather_service import WeatherData

        self._logger.warning(f"天气工具同步版本服务失败，不再生成模拟数据: {location}")

        # 返回错误状态的数据，不再生成任何模拟天气信息
        return WeatherData(
            temperature=0.0,
            apparent_temperature=0.0,
            humidity=0.0,
            pressure=0.0,
            wind_speed=0.0,
            wind_direction=0.0,
            condition="天气服务查询失败",
            description="天气服务查询失败，请稍后再试"
        )

    def _filter_hourly_data_for_time_period(self, location: str, date: str, time_period: str, hourly_data: list) -> ToolResult:
        """从小时级数据中筛选指定日期和时间段的天气数据"""
        try:
            from datetime import datetime, timedelta
            import re

            # 解析日期
            target_datetime = None
            if date:
                if date.lower() == "today" or date == "今天":
                    target_datetime = datetime.now()
                elif date.lower() == "tomorrow" or date == "明天":
                    target_datetime = datetime.now() + timedelta(days=1)
                elif date.lower() == "yesterday" or date == "昨天":
                    target_datetime = datetime.now() - timedelta(days=1)
                else:
                    # 尝试解析具体日期
                    try:
                        if re.match(r'\d{4}-\d{2}-\d{2}', date):
                            target_datetime = datetime.strptime(date[:10], '%Y-%m-%d')
                        elif re.match(r'\d{1,2}-\d{1,2}', date):
                            # 假设是月-日格式，使用当前年份
                            current_year = datetime.now().year
                            target_datetime = datetime.strptime(f"{current_year}-{date[:5]}", '%Y-%m-%d')
                    except ValueError:
                        pass

            if not target_datetime:
                return ToolResult(
                    success=False,
                    error=f"无法解析日期: {date}",
                    metadata={"operation": "filter_time_period", "date": date}
                )

            # 解析时间段
            time_period_code = None
            if "早上" in time_period or "清晨" in time_period or "凌晨" in time_period:
                time_period_code = "early_morning"
            elif "上午" in time_period:
                time_period_code = "morning"
            elif "中午" in time_period:
                time_period_code = "noon"
            elif "下午" in time_period:
                time_period_code = "afternoon"
            elif "晚上" in time_period or "夜间" in time_period or "夜晚" in time_period:
                time_period_code = "evening"
            elif "全天" in time_period or time_period == "":
                time_period_code = None

            # 从小时数据中筛选匹配的时间段
            filtered_data = []
            target_date = target_datetime.date()

            for hour_info in hourly_data:
                try:
                    hour_dt = datetime.fromisoformat(hour_info.get('datetime', '').replace('Z', '+00:00'))
                    if hour_dt.date() == target_date:
                        # 根据时间段筛选
                        hour = hour_dt.hour
                        if time_period_code == "early_morning" and 0 <= hour < 6:
                            filtered_data.append(hour_info)
                        elif time_period_code == "morning" and 6 <= hour < 12:
                            filtered_data.append(hour_info)
                        elif time_period_code == "noon" and 12 <= hour < 14:
                            filtered_data.append(hour_info)
                        elif time_period_code == "afternoon" and 14 <= hour < 18:
                            filtered_data.append(hour_info)
                        elif time_period_code == "evening" and 18 <= hour < 24:
                            filtered_data.append(hour_info)
                        elif time_period_code is None:
                            # 如果没有指定时间段，返回当天所有数据
                            filtered_data.append(hour_info)
                except Exception as e:
                    self._logger.debug(f"解析小时数据失败: {e}")
                    continue

            if filtered_data:
                # 计算聚合数据
                temps = [h.get('temperature', 0) for h in filtered_data if h.get('temperature') is not None]
                humidities = [h.get('humidity', 0) for h in filtered_data if h.get('humidity') is not None]
                wind_speeds = [h.get('wind_speed', 0) for h in filtered_data if h.get('wind_speed') is not None]
                conditions = [h.get('condition', '未知') for h in filtered_data]

                avg_temp = sum(temps) / len(temps) if temps else 0
                avg_humidity = sum(humidities) / len(humidities) if humidities else 0
                avg_wind_speed = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0
                primary_condition = max(set(conditions), key=conditions.count) if conditions else "未知"

                return ToolResult(
                    success=True,
                    data={
                        'location': location,
                        'date': target_datetime.strftime('%Y-%m-%d'),
                        'time_period': time_period or '全天',
                        'temperature': round(avg_temp, 1),
                        'humidity': round(avg_humidity, 1),
                        'wind_speed': round(avg_wind_speed, 1),
                        'condition': primary_condition,
                        'description': f"{primary_condition}，平均温度{avg_temp:.1f}°C",
                        'hourly_count': len(filtered_data),
                        'data_points': filtered_data[:3],  # 返回前3个数据点作为示例
                        'source': 'cached_hourly_forecast',
                        'confidence': 0.9
                    },
                    metadata={
                        "operation": "time_period_weather",
                        "source": "cached_hourly_forecast",
                        "location": location,
                        "date": date,
                        "time_period": time_period,
                        "original_hours": len(hourly_data),
                        "filtered_hours": len(filtered_data)
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"没有找到 {location} {date} {time_period} 的天气数据",
                    metadata={
                        "operation": "filter_time_period",
                        "location": location,
                        "date": date,
                        "time_period": time_period,
                        "reason": "no_matching_data"
                    }
                )

        except Exception as e:
            self._logger.error(f"筛选时间段天气数据失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"筛选时间段天气数据失败: {str(e)}"
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


def format_weather_output(result: ToolResult, city: str, operation: str, debug: bool = False) -> None:
    """格式化天气输出"""
    if not result.success:
        print(f"❌ 查询 {city} 天气失败: {result.error}")
        if result.metadata:
            print(f"   元数据: {result.metadata}")
        return

    data = result.data or {}
    metadata = result.metadata or {}

    print(f"\n🌤️  {city} 天气信息")
    print("=" * 50)

    if operation == "current_weather":
        # 当前天气信息
        print(f"📍 地点: {data.get('location', city)}")
        print(f"🌡️  温度: {data.get('temperature', 'N/A')}°C (体感: {data.get('apparent_temperature', 'N/A')}°C)")
        print(f"💧 湿度: {data.get('humidity', 'N/A')}%")
        print(f"🌪️  风速: {data.get('wind_speed', 'N/A')} km/h")
        print(f"🧭 风向: {data.get('wind_direction', 'N/A')}")
        print(f"📊 气压: {data.get('pressure', 'N/A')} hPa")
        print(f"☁️  天气: {data.get('condition', 'N/A')}")
        print(f"📝 描述: {data.get('description', 'N/A')}")

        if debug:
            print(f"\n🔍 调试信息:")
            print(f"   数据源: {data.get('source', 'N/A')}")
            print(f"   服务耗时: {metadata.get('service_time_ms', 'N/A')}ms")
            cache_hit_rate = metadata.get('cache_hit_rate')
            if cache_hit_rate is not None:
                print(f"   缓存命中率: {cache_hit_rate:.1%}")

    elif operation == "weather_by_date":
        # 指定日期天气
        print(f"📍 地点: {data.get('location', city)}")
        print(f"📅 日期: {data.get('date', 'N/A')}")
        print(f"🌡️  温度: {data.get('temperature', 'N/A')}°C")
        print(f"💧 湿度: {data.get('humidity', 'N/A')}%")
        print(f"☁️  天气: {data.get('condition', 'N/A')}")
        print(f"📝 描述: {data.get('description', 'N/A')}")

        if debug:
            print(f"\n🔍 调试信息:")
            print(f"   数据源: {data.get('source', 'N/A')}")
            print(f"   状态码: {metadata.get('status_code', 'N/A')}")

    elif operation == "hourly_forecast":
        # 小时级预报
        print(f"📍 地点: {data.get('location', city)}")
        print(f"📅 日期: {data.get('date', 'N/A')}")
        print(f"📊 预报小时数: {len(data.get('hourly_forecast', []))}")
        print(f"🎯 置信度: {data.get('confidence', 'N/A')}")

        hourly_data = data.get('hourly_forecast', [])[:6]  # 显示前6小时
        if hourly_data:
            print(f"\n⏰ 小时预报 (前6小时):")
            for i, hour in enumerate(hourly_data):
                time_str = hour.get('datetime', '')[-8:-3] if hour.get('datetime') else 'N/A'
                temp = hour.get('temperature', 'N/A')
                condition = hour.get('condition', 'N/A')
                print(f"   {time_str} | {temp}°C | {condition}")

        if debug:
            print(f"\n🔍 调试信息:")
            print(f"   数据源: {data.get('source', 'N/A')}")
            print(f"   预报要点: {data.get('forecast_keypoint', 'N/A')}")
            print(f"   总描述: {data.get('description', 'N/A')}")

    elif operation == "weather_by_datetime":
        # 指定时间段天气
        print(f"📍 地点: {data.get('location', city)}")
        print(f"📅 日期: {data.get('date', 'N/A')}")
        print(f"⏰ 时间段: {data.get('time_period', 'N/A')}")
        print(f"🌡️  平均温度: {data.get('temperature', 'N/A')}°C")
        print(f"💧 湿度: {data.get('humidity', 'N/A')}%")
        print(f"🌪️  风速: {data.get('wind_speed', 'N/A')} km/h")
        print(f"☁️  主要天气: {data.get('condition', 'N/A')}")
        print(f"📝 描述: {data.get('description', 'N/A')}")

        if debug:
            print(f"\n🔍 调试信息:")
            print(f"   数据源: {data.get('source', 'N/A')}")
            print(f"   置信度: {data.get('confidence', 'N/A')}")
            print(f"   数据点数量: {data.get('hourly_count', 'N/A')}")

    print(f"\n⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def check_environment():
    """检查环境变量"""
    missing_vars = []
    if not os.getenv("CAIYUN_API_KEY"):
        missing_vars.append("CAIYUN_API_KEY")
    if not os.getenv("AMAP_API_KEY"):
        missing_vars.append("AMAP_API_KEY")

    if missing_vars:
        print("⚠️  警告: 以下环境变量未设置:")
        for var in missing_vars:
            print(f"   - {var}")
        print("   某些功能可能无法正常工作")
        print("   请在 .env 文件中设置这些环境变量")
        return False
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="天气工具测试程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python weather_tool_sync.py                           # 查询北京当前天气
  python weather_tool_sync.py --city 上海               # 查询上海当前天气
  python weather_tool_sync.py --city 广州 --debug        # 查询广州天气(调试模式)
  python weather_tool_sync.py --city 深圳 --date tomorrow  # 查询深圳明天天气
  python weather_tool_sync.py --operation hourly_forecast  # 查询小时级预报
  python weather_tool_sync.py --operation weather_by_datetime --datetime "明天上午"  # 查询明天上午天气
        """
    )

    parser.add_argument(
        "--city",
        type=str,
        default="北京",
        help="城市名称 (默认: 北京)"
    )

    parser.add_argument(
        "--operation",
        type=str,
        default="current_weather",
        choices=["current_weather", "weather_by_date", "hourly_forecast", "weather_by_datetime"],
        help="操作类型 (默认: current_weather)"
    )

    parser.add_argument(
        "--date",
        type=str,
        help="日期参数 (如: today, tomorrow, 2024-12-25)"
    )

    parser.add_argument(
        "--datetime",
        type=str,
        help="日期时间参数 (如: 明天上午, 今天下午)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )

    args = parser.parse_args()

    print("🚀 天气工具测试程序")
    print("=" * 50)

    # 检查环境变量
    if not check_environment():
        print()

    # 设置日志级别
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        print("🐛 调试模式已启用")
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        # 初始化天气工具
        print(f"🔧 正在初始化天气工具...")
        tool = WeatherTool("test_tool")

        print(f"🎯 开始执行操作: {args.operation}")
        print(f"📍 目标城市: {args.city}")

        # 执行相应的操作
        if args.operation == "current_weather":
            result = tool.execute("current_weather", location=args.city)

        elif args.operation == "weather_by_date":
            date = args.date if args.date else "today"
            result = tool.execute("weather_by_date", location=args.city, date=date)

        elif args.operation == "hourly_forecast":
            result = tool.execute("hourly_forecast", location=args.city, hours=24)

        elif args.operation == "weather_by_datetime":
            datetime_str = args.datetime if args.datetime else "今天"
            result = tool.execute("weather_by_datetime", location=args.city, datetime_str=datetime_str)

        else:
            print(f"❌ 不支持的操作: {args.operation}")
            return

        # 格式化输出结果
        format_weather_output(result, args.city, args.operation, args.debug)

        # 清理资源
        tool.close()

    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
    finally:
        print("\n✨ 程序执行完毕")


if __name__ == "__main__":
    main()