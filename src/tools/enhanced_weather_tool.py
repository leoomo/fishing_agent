#!/usr/bin/env python3
"""
Enhanced Weather Tool with Detailed Function Process Logging

天气工具模块提供天气查询和预报功能，集成彩云天气API。
增强版本包含详细的函数过程日志记录，便于调试和监控。
"""

import os
import requests
import json
import time
import uuid
from typing import Optional, Any, Dict, Union, List, Tuple
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import wraps

# 导入核心工具基类
try:
    from core.base_tool import BaseTool, ConfigurableTool
    from core.interfaces import ToolMetadata, ToolResult
except ImportError:
    # 兼容性导入
    class BaseTool:
        pass
    class ConfigurableTool:
        def __init__(self, config=None, logger=None):
            self.config = config or {}
            self._logger = logger or logging.getLogger(self.__class__.__name__)

        def get_config_value(self, key, default=None):
            return self.config.get(key, default)

    class ToolMetadata:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class ToolResult:
        def __init__(self, success=True, data=None, error=None, metadata=None):
            self.success = success
            self.data = data
            self.error = error
            self.metadata = metadata or {}

# 导入错误码类
try:
    from services.weather.datetime_weather_service import WeatherServiceErrorCode, HourlyForecastErrorCode
except ImportError:
    # 如果导入失败，创建一个简单的替代
    class WeatherServiceErrorCode:
        SUCCESS = 0
        CACHE_HIT = 1
        API_ERROR = 2
        COORDINATE_NOT_FOUND = 3
        NETWORK_TIMEOUT = 4
        DATA_PARSE_ERROR = 5
        PARAMETER_ERROR = 6
        DATE_PARSE_ERROR = 7
        TIME_PERIOD_ERROR = 8
        DATA_OUT_OF_RANGE = 9

        @classmethod
        def get_description(cls, error_code: int) -> str:
            descriptions = {
                0: "成功",
                1: "缓存命中",
                2: "API错误",
                3: "坐标未找到",
                4: "网络超时",
                5: "数据解析失败",
                6: "参数错误",
                7: "日期解析错误",
                8: "时间段错误",
                9: "数据超出范围"
            }
            return descriptions.get(error_code, "未知错误码")

    class HourlyForecastErrorCode:
        SUCCESS = 0
        CACHE_HIT = 1
        API_ERROR = 2
        COORDINATE_NOT_FOUND = 3
        NETWORK_TIMEOUT = 4
        DATA_PARSE_ERROR = 5
        PARAMETER_ERROR = 6

        @classmethod
        def get_description(cls, error_code: int) -> str:
            descriptions = {
                0: "成功",
                1: "缓存命中",
                2: "API错误",
                3: "坐标未找到",
                4: "网络超时",
                5: "数据解析失败",
                6: "参数错误"
            }
            return descriptions.get(error_code, "未知错误码")


def log_function_process(func):
    """
    装饰器：记录函数执行过程的详细信息
    """
    @wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        # 生成唯一的事务ID
        transaction_id = str(uuid.uuid4())[:8]
        function_name = f"{self.__class__.__name__}.{func.__name__}"
        logger = getattr(self, '_logger', logging.getLogger(function_name))

        # 记录函数开始
        start_time = time.time()
        logger.info(f"[{transaction_id}] 🚀 开始执行 {function_name}")
        logger.debug(f"[{transaction_id}] 📥 输入参数: args={args}, kwargs={kwargs}")

        try:
            # 执行函数
            result = await func(self, *args, **kwargs)

            # 计算执行时间
            execution_time = time.time() - start_time

            # 记录成功结果
            if hasattr(result, 'success'):
                if result.success:
                    logger.info(f"[{transaction_id}] ✅ {function_name} 执行成功 ({execution_time:.3f}s)")
                    if result.data:
                        logger.debug(f"[{transaction_id}] 📤 返回数据: {type(result.data).__name__}")
                else:
                    logger.warning(f"[{transaction_id}] ❌ {function_name} 执行失败 ({execution_time:.3f}s): {result.error}")
            else:
                logger.info(f"[{transaction_id}] ✅ {function_name} 执行成功 ({execution_time:.3f}s)")
                logger.debug(f"[{transaction_id}] 📤 返回结果: {type(result).__name__}")

            # 为结果添加事务ID
            if hasattr(result, 'metadata'):
                result.metadata['transaction_id'] = transaction_id
                result.metadata['execution_time'] = execution_time

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"[{transaction_id}] 💥 {function_name} 执行异常 ({execution_time:.3f}s): {str(e)}")
            logger.debug(f"[{transaction_id}] 📋 异常堆栈: {e.__class__.__name__}: {str(e)}")
            raise

    return async_wrapper


@dataclass
class WeatherData:
    """天气数据类"""
    temperature: float  # 温度 (摄氏度)
    apparent_temperature: float  # 体感温度 (摄氏度)
    humidity: float  # 湿度 (百分比)
    pressure: float  # 气压 (hPa)
    wind_speed: float  # 风速 (km/h)
    wind_direction: float  # 风向 (度)
    condition: str  # 天气状况
    description: str  # 天气描述
    location: str  # 位置
    timestamp: float  # 时间戳
    source: str  # 数据源


class EnhancedWeatherTool(ConfigurableTool):
    """增强版天气工具类 - 包含详细的函数过程日志"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)

        # 设置详细的日志格式
        self._setup_detailed_logging()

        # 记录初始化开始
        init_start = time.time()
        self._logger.info("🔧 开始初始化 EnhancedWeatherTool")

        # 配置参数
        self._api_key = self.get_config_value("api_key") or os.getenv("CAIYUN_API_KEY")
        self._timeout = self.get_config_value("timeout", 10)
        self._base_url = self.get_config_value("base_url", "https://api.caiyunapp.com/v2.6")
        self._cache = {}  # 简单缓存
        self._cache_ttl = self.get_config_value("cache_ttl", 1800)  # 30分钟缓存

        # 记录配置信息
        self._logger.info(f"⚙️ 配置参数: timeout={self._timeout}, base_url={self._base_url}")
        self._logger.info(f"🔑 API密钥状态: {'已配置' if self._api_key else '未配置'}")

        # 城市坐标映射
        self._city_coordinates = {
            "北京": (116.4074, 39.9042),
            "上海": (121.4737, 31.2304),
            "广州": (113.2644, 23.1291),
            "深圳": (114.0579, 22.5431),
            "杭州": (120.1551, 30.2741),
            "成都": (104.0668, 30.5728),
            "西安": (108.9402, 34.3416),
            "武汉": (114.3055, 30.5928),
            "南京": (118.7674, 32.0416),
            "重庆": (106.5516, 29.5630),
            "天津": (117.1901, 39.0842),
            "苏州": (120.5853, 31.2989),
            "青岛": (120.3826, 36.0671),
            "大连": (121.6147, 38.9140),
            "厦门": (118.1119, 24.4899),
            "朝阳": (116.4436, 39.9214),  # 北京朝阳区
            "海淀": (116.2982, 39.9596),  # 北京海淀区
            "浦东": (121.5440, 31.2212),  # 上海浦东新区
            "黄浦": (121.4903, 31.2364),  # 上海黄浦区
        }
        self._logger.info(f"📍 预定义城市坐标数量: {len(self._city_coordinates)}")

        # 天气状况映射
        self._condition_map = {
            "CLEAR_DAY": "晴天",
            "CLEAR_NIGHT": "晴夜",
            "PARTLY_CLOUDY_DAY": "多云",
            "PARTLY_CLOUDY_NIGHT": "多云",
            "CLOUDY": "阴天",
            "LIGHT_HAZE": "轻雾",
            "MODERATE_HAZE": "中雾",
            "HEAVY_HAZE": "重雾",
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

        # 缓存统计
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        }

        init_time = time.time() - init_start
        self._logger.info(f"✅ EnhancedWeatherTool 初始化完成 ({init_time:.3f}s)")

    def _setup_detailed_logging(self):
        """设置详细的日志配置"""
        # 创建详细的日志格式
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 如果logger没有handler，添加一个
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.DEBUG)

    @property
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        return ToolMetadata(
            name="enhanced_weather_tool",
            description="提供天气查询和预报功能（增强版，含详细日志）",
            version="2.0.0",
            author="langchain-learning",
            tags=["weather", "api", "climate", "enhanced", "logging"],
            dependencies=["requests"]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        operation = kwargs.get("operation")
        self._logger.debug(f"🔍 验证输入参数: operation={operation}")

        valid_operations = [
            "current_weather", "get_coordinates", "get_weather",
            "batch_weather", "search_locations", "weather_forecast",
            "weather_by_date", "weather_by_datetime", "hourly_forecast",
            "time_period_weather"
        ]

        is_valid = operation in valid_operations
        self._logger.debug(f"📋 参数验证结果: {is_valid}")
        return is_valid

    @log_function_process
    async def _execute(self, **kwargs) -> ToolResult:
        """执行天气操作"""
        operation = kwargs.get("operation")
        self._logger.info(f"🎯 开始执行操作: {operation}")

        try:
            if operation == "current_weather":
                return await self._current_weather(**kwargs)
            elif operation == "get_coordinates":
                return await self._get_coordinates(**kwargs)
            elif operation == "get_weather":
                return await self._get_weather(**kwargs)
            elif operation == "batch_weather":
                return await self._batch_weather(**kwargs)
            elif operation == "search_locations":
                return await self._search_locations(**kwargs)
            elif operation == "weather_forecast":
                return await self._weather_forecast(**kwargs)
            elif operation == "weather_by_date":
                return await self._weather_by_date(**kwargs)
            elif operation == "weather_by_datetime":
                return await self._weather_by_datetime(**kwargs)
            elif operation == "hourly_forecast":
                return await self._hourly_forecast(**kwargs)
            elif operation == "time_period_weather":
                return await self._time_period_weather(**kwargs)
            else:
                error_msg = f"不支持的操作: {operation}"
                self._logger.error(f"❌ {error_msg}")
                return ToolResult(
                    success=False,
                    error=error_msg
                )

        except Exception as e:
            error_msg = f"天气工具执行失败: {str(e)}"
            self._logger.error(f"💥 {error_msg}")
            self._logger.debug(f"📋 异常详情: {type(e).__name__}: {str(e)}")
            return ToolResult(
                success=False,
                error=error_msg
            )

    @log_function_process
    async def _current_weather(self, location: str, **kwargs) -> ToolResult:
        """获取当前天气"""
        self._logger.info(f"🌤️ 开始获取 {location} 的当前天气")

        # 更新统计
        self._cache_stats['total_requests'] += 1

        try:
            # 检查缓存
            cache_key = f"weather:{location}"
            self._logger.debug(f"💾 检查缓存: key={cache_key}")

            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                self._cache_stats['hits'] += 1
                hit_rate = self._cache_stats['hits'] / self._cache_stats['total_requests'] * 100
                self._logger.info(f"✅ 缓存命中: {location} (命中率: {hit_rate:.1f}%)")
                return ToolResult(
                    success=True,
                    data=cached_data,
                    metadata={
                        "operation": "current_weather",
                        "source": "cache",
                        "cache_hit_rate": hit_rate
                    }
                )
            else:
                self._cache_stats['misses'] += 1
                self._logger.debug(f"❌ 缓存未命中: {location}")

            # 获取坐标
            self._logger.info(f"📍 开始获取 {location} 的坐标")
            coordinates = self._get_location_coordinates(location)

            if not coordinates:
                self._logger.warning(f"⚠️ 未找到 {location} 的坐标，使用模拟数据")
                weather_data = self._create_fallback_weather(location)
                return ToolResult(
                    success=True,
                    data=asdict(weather_data),
                    metadata={
                        "operation": "current_weather",
                        "source": "fallback",
                        "reason": "coordinates_not_found"
                    }
                )

            longitude, latitude = coordinates
            self._logger.info(f"📐 坐标获取成功: {location} -> ({longitude:.6f}, {latitude:.6f})")

            # 调用 API
            self._logger.info(f"🌐 开始调用天气API: {location}")
            weather_data = await self._call_weather_api(longitude, latitude, location)

            # 缓存结果
            self._logger.debug(f"💾 缓存结果: {cache_key}")
            self._set_cache(cache_key, asdict(weather_data))

            self._logger.info(f"✅ {location} 天气数据获取成功: {weather_data.condition}, {weather_data.temperature}°C")
            return ToolResult(
                success=True,
                data=asdict(weather_data),
                metadata={
                    "operation": "current_weather",
                    "source": "api",
                    "coordinates": coordinates,
                    "cache_hit_rate": self._cache_stats['hits'] / max(1, self._cache_stats['total_requests']) * 100
                }
            )

        except Exception as e:
            self._logger.error(f"💥 获取 {location} 天气失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"获取当前天气失败: {str(e)}"
            )

    def _get_location_coordinates(self, location: str) -> Optional[Tuple[float, float]]:
        """获取位置坐标（使用增强版服务）"""
        self._logger.debug(f"🔍 开始获取坐标: {location}")

        # 首先尝试从预定义城市坐标中查找
        coords = self._city_coordinates.get(location.strip())
        if coords:
            self._logger.info(f"✅ 从预定义坐标获取: {location} -> {coords}")
            return coords

        # 如果预定义中没有，使用服务管理器获取坐标服务（支持高德API）
        try:
            self._logger.debug(f"🔍 尝试使用增强版坐标服务: {location}")

            # 使用绝对导入
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))

            from services.service_manager import get_coordinate_service
            if not hasattr(self, '_coordinate_service'):
                self._coordinate_service = get_coordinate_service()
                self._logger.info("🔧 增强版坐标服务已通过服务管理器初始化")

            # 使用坐标服务获取坐标
            coordinate_obj = self._coordinate_service.get_coordinate(location.strip())
            if coordinate_obj:
                coords = (coordinate_obj.longitude, coordinate_obj.latitude)
            else:
                coords = None

            if coords:
                # 将结果缓存到城市坐标字典中（内存缓存）
                self._city_coordinates[location.strip()] = coords
                self._logger.info(f"✅ 增强版坐标服务成功: {location.strip()} -> {coords}")
                self._logger.debug(f"💾 坐标已缓存到内存: {location.strip()} -> {coords}")
                return coords
            else:
                self._logger.warning(f"⚠️ 增强版坐标服务未能获取坐标: {location.strip()}")

        except Exception as e:
            self._logger.error(f"💥 增强版坐标查询失败: {e}")
            import traceback
            self._logger.debug(f"📋 异常堆栈: {traceback.format_exc()}")
        finally:
            # 清理sys.path
            if 'project_root' in locals() and str(project_root) in sys.path:
                sys.path.remove(str(project_root))

        return None

    async def _call_weather_api(self, longitude: float, latitude: float, location: str) -> WeatherData:
        """调用天气API"""
        self._logger.info(f"🌐 开始调用天气API: {location} ({longitude}, {latitude})")

        if not self._api_key:
            self._logger.warning("⚠️ 未配置API密钥，使用模拟数据")
            return self._create_fallback_weather(location)

        url = f"{self._base_url}/{self._api_key}/{longitude},{latitude}/realtime"
        self._logger.debug(f"📡 API请求URL: {url[:50]}...")

        try:
            # 发起请求
            self._logger.debug(f"📤 发起API请求...")
            request_start = time.time()

            response = requests.get(url, timeout=self._timeout)
            request_time = time.time() - request_start

            self._logger.info(f"📡 API响应: status={response.status_code}, time={request_time:.3f}s")

            response.raise_for_status()
            data = response.json()

            self._logger.debug(f"📋 API响应数据: status={data.get('status')}")

            if data.get("status") != "ok":
                error_status = data.get("status")
                self._logger.error(f"❌ API返回错误状态: {error_status}")
                return self._create_fallback_weather(location)

            # 解析天气数据
            self._logger.debug(f"🔄 开始解析天气数据...")
            weather_data = self._parse_weather_data(data, location)

            self._logger.info(f"✅ 天气数据解析成功: {weather_data.condition}, {weather_data.temperature}°C")
            return weather_data

        except requests.exceptions.RequestException as e:
            self._logger.error(f"💥 API请求失败: {str(e)}")
            return self._create_fallback_weather(location)
        except json.JSONDecodeError as e:
            self._logger.error(f"💥 API响应解析失败: {str(e)}")
            return self._create_fallback_weather(location)

    def _parse_weather_data(self, api_data: Dict, location: str) -> WeatherData:
        """解析API返回的天气数据"""
        self._logger.debug(f"🔄 解析天气数据: {location}")

        try:
            result = api_data.get("result", {})
            realtime = result.get("realtime", {})

            self._logger.debug(f"📋 原始数据: temperature={realtime.get('temperature')}, skycon={realtime.get('skycon')}")

            skycon = realtime.get("skycon", "")
            condition = self._condition_map.get(skycon, skycon)

            weather_data = WeatherData(
                temperature=realtime.get("temperature", 0),
                apparent_temperature=realtime.get("apparent_temperature", 0),
                humidity=realtime.get("humidity", 0),
                pressure=realtime.get("pressure", 0),
                wind_speed=realtime.get("wind", {}).get("speed", 0),
                wind_direction=realtime.get("wind", {}).get("direction", 0),
                condition=condition,
                description=f"{condition}，{realtime.get('temperature', 0)}°C",
                location=location,
                timestamp=time.time(),
                source="彩云天气API"
            )

            self._logger.debug(f"✅ 天气数据解析完成: {weather_data.description}")
            return weather_data

        except Exception as e:
            self._logger.error(f"💥 天气数据解析失败: {str(e)}")
            return self._create_fallback_weather(location)

    def _create_fallback_weather(self, location: str) -> WeatherData:
        """创建模拟天气数据"""
        self._logger.info(f"🎭 创建模拟天气数据: {location}")

        import random

        fallback_weather = {
            "北京": {"temp": 25, "condition": "晴天", "humidity": 60},
            "上海": {"temp": 28, "condition": "多云", "humidity": 70},
            "广州": {"temp": 30, "condition": "阴天", "humidity": 80},
            "深圳": {"temp": 29, "condition": "晴天", "humidity": 75},
            "杭州": {"temp": 22, "condition": "小雨", "humidity": 85},
            "成都": {"temp": 20, "condition": "雾", "humidity": 90},
            "西安": {"temp": 18, "condition": "晴", "humidity": 50}
        }

        weather_info = fallback_weather.get(location.strip(), {
            "temp": random.randint(15, 30),
            "condition": random.choice(["晴天", "多云", "阴天"]),
            "humidity": random.randint(40, 80)
        })

        weather_data = WeatherData(
            temperature=weather_info["temp"],
            apparent_temperature=weather_info["temp"] + random.randint(-2, 2),
            humidity=weather_info["humidity"],
            pressure=random.randint(1000, 1020),
            wind_speed=random.uniform(0, 20),
            wind_direction=random.randint(0, 360),
            condition=weather_info["condition"],
            description=f"{weather_info['condition']}，{weather_info['temp']}°C",
            location=location,
            timestamp=time.time(),
            source="模拟数据"
        )

        self._logger.debug(f"🎭 模拟数据创建完成: {weather_data.description}")
        return weather_data

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        self._logger.debug(f"💾 检查缓存: {key}")

        if key in self._cache:
            data, timestamp = self._cache[key]
            age = time.time() - timestamp

            if age < self._cache_ttl:
                self._logger.debug(f"✅ 缓存命中: {key} (age: {age:.1f}s)")
                return data
            else:
                self._logger.debug(f"❌ 缓存过期: {key} (age: {age:.1f}s > {self._cache_ttl}s)")
                del self._cache[key]

        self._logger.debug(f"❌ 缓存未命中: {key}")
        return None

    def _set_cache(self, key: str, data: Dict) -> None:
        """设置缓存数据"""
        self._logger.debug(f"💾 设置缓存: {key}")
        self._cache[key] = (data, time.time())

    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        total_requests = max(1, self._cache_stats['total_requests'])
        hit_rate = self._cache_stats['hits'] / total_requests * 100

        cache_info = {
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl,
            "api_configured": bool(self._api_key),
            "supported_locations": len(self._city_coordinates),
            "cache_stats": self._cache_stats.copy(),
            "hit_rate": hit_rate
        }

        self._logger.info(f"📊 缓存统计: 命中率={hit_rate:.1f}%, 大小={len(self._cache)}")
        return cache_info

    # 其他方法的实现保持不变，但都添加 @log_function_process 装饰器
    @log_function_process
    async def _get_coordinates(self, location: str, **kwargs) -> ToolResult:
        """获取位置坐标"""
        try:
            coordinates = self._get_location_coordinates(location)
            if coordinates:
                return ToolResult(
                    success=True,
                    data={
                        "location": location,
                        "longitude": coordinates[0],
                        "latitude": coordinates[1],
                        "coordinates": coordinates
                    },
                    metadata={"operation": "get_coordinates"}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"未找到位置 '{location}' 的坐标信息"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取坐标失败: {str(e)}"
            )

    @log_function_process
    async def _get_weather(self, location: str, detailed: bool = False, **kwargs) -> ToolResult:
        """获取天气信息（兼容方法）"""
        self._logger.debug(f"🔄 兼容方法调用: _get_weather -> _current_weather")
        return await self._current_weather(location, **kwargs)


if __name__ == "__main__":
    # 测试增强版日志功能
    import asyncio

    # 设置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    async def test_enhanced_logging():
        print("=" * 80)
        print("🧪 测试增强版天气工具日志功能")
        print("=" * 80)

        tool = EnhancedWeatherTool()

        # 测试多个查询
        test_locations = ["北京", "上海", "不存在的城市", "朝阳区"]

        for location in test_locations:
            print(f"\n{'=' * 60}")
            print(f"🌍 测试位置: {location}")
            print(f"{'=' * 60}")

            result = await tool._current_weather(location)

            if result.success:
                print(f"✅ 成功: {result.data.get('description')}")
                print(f"📍 来源: {result.metadata.get('source')}")
            else:
                print(f"❌ 失败: {result.error}")

        # 显示缓存统计
        print(f"\n{'=' * 60}")
        print("📊 缓存统计信息")
        print(f"{'=' * 60}")
        cache_info = tool.get_cache_info()
        for key, value in cache_info.items():
            print(f"{key}: {value}")

    # 运行测试
    asyncio.run(test_enhanced_logging())