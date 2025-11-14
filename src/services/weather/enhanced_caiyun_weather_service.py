#!/usr/bin/env python3
"""
增强版彩云天气 API 服务模块

实现 IWeatherService 接口，集成智能地名匹配、坐标数据库查询、缓存机制等功能
支持全国所有行政区划的天气查询，通过服务管理器获取坐标服务。
"""

import os
import json
import requests
from typing import Dict, Optional, Union, Tuple, List, Any
import logging
from dataclasses import dataclass
from datetime import datetime, date
import time

# 导入接口和配置
try:
    from ...interfaces.weather_service import (
        IWeatherService, WeatherCondition, WeatherForecast
    )
    from ...interfaces.coordinate_service import ICoordinateService
    from ...config.service_config import get_service_config
except ImportError:
    # 处理相对导入失败的情况
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    from interfaces.weather_service import (
        IWeatherService, WeatherCondition, WeatherForecast
    )
    from interfaces.coordinate_service import ICoordinateService
    from config.service_config import get_service_config

# 导入现有服务
from .weather_service import WeatherData, CaiyunWeatherService
from ..matching.city_coordinate_db import CityCoordinateDB, PlaceInfo
from ..matching.enhanced_place_matcher import EnhancedPlaceMatcher
from .weather_cache import WeatherCache, get_weather_cache

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedCaiyunWeatherService(IWeatherService):
    """增强版彩云天气 API 服务 - 实现IWeatherService接口"""

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[int] = None):
        """
        初始化增强版天气服务

        Args:
            api_key: 彩云天气 API 密钥，如果为None则从环境变量获取
            timeout: API 请求超时时间（秒），如果为None则使用配置值
        """
        # 获取配置
        self._config = get_service_config()
        self._initialized = False
        self._coordinate_service: Optional[ICoordinateService] = None

        # 初始化天气服务基础配置
        if api_key is None:
            api_key = self._config.weather_service.api_key or os.getenv('CAIYUN_API_KEY')

        if timeout is None:
            timeout = self._config.weather_service.timeout

        # IWeatherService 接口不需要调用父类初始化

        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.caiyunapi.com/v2.6"

        if not self.api_key:
            raise ValueError("未找到彩云天气API密钥，请在.env文件中配置CAIYUN_API_KEY")

        # 初始化增强组件
        self.coordinate_db = CityCoordinateDB()
        self.place_matcher = EnhancedPlaceMatcher()
        self.cache = get_weather_cache()

        # 连接数据库
        try:
            self.place_matcher.connect()
        except Exception as e:
            logger.warning(f"地名匹配器连接失败，将使用降级模式: {e}")

        logger.info("增强版天气服务初始化完成")
        logger.info(f"数据库统计: {self.coordinate_db.get_statistics()}")
        logger.info(f"匹配器统计: {self.place_matcher.get_statistics()}")

    def _ensure_coordinate_service(self) -> ICoordinateService:
        """确保坐标服务已获取"""
        if self._coordinate_service is None:
            from ..service_manager import get_coordinate_service
            self._coordinate_service = get_coordinate_service()
        return self._coordinate_service

    def get_current_weather(self, location: str) -> Optional[WeatherCondition]:
        """
        获取指定位置的当前天气（实现接口方法）

        Args:
            location: 位置名称或坐标

        Returns:
            当前天气条件，如果获取失败返回 None
        """
        try:
            # 获取坐标
            coords = self._get_coordinates_for_location(location)
            if not coords:
                logger.warning(f"无法获取位置坐标: {location}")
                return None

            # 调用彩云天气API
            weather_data = self._call_caiyun_api(coords[0], coords[1])
            if not weather_data:
                return None

            # 转换为接口定义的格式
            return self._convert_to_weather_condition(weather_data)

        except Exception as e:
            logger.error(f"获取天气失败 {location}: {e}")
            return None

    def get_weather_forecast(self, location: str, days: int = 3) -> Optional[List[WeatherForecast]]:
        """
        获取指定位置的天气预报（实现接口方法）

        Args:
            location: 位置名称或坐标
            days: 预报天数

        Returns:
            天气预报列表，如果获取失败返回 None
        """
        try:
            # 获取坐标
            coords = self._get_coordinates_for_location(location)
            if not coords:
                logger.warning(f"无法获取位置坐标: {location}")
                return None

            # 调用彩云天气API（获取实时和预报数据）
            weather_data = self._call_caiyun_api_forecast(coords[0], coords[1])
            if not weather_data:
                return None

            # 转换为接口定义的格式
            return self._convert_to_weather_forecast(weather_data, days)

        except Exception as e:
            logger.error(f"获取天气预报失败 {location}: {e}")
            return None

    def get_weather_by_coordinate(self, coordinate: ICoordinateService) -> Optional[WeatherCondition]:
        """
        根据坐标获取天气（实现接口方法）

        Args:
            coordinate: 坐标信息

        Returns:
            天气条件，如果获取失败返回 None
        """
        try:
            # 从接口对象中提取坐标
            longitude = coordinate.longitude
            latitude = coordinate.latitude

            # 调用彩云天气API
            weather_data = self._call_caiyun_api(longitude, latitude)
            if not weather_data:
                return None

            # 转换为接口定义的格式
            return self._convert_to_weather_condition(weather_data)

        except Exception as e:
            logger.error(f"根据坐标获取天气失败 ({coordinate.longitude}, {coordinate.latitude}): {e}")
            return None

    def is_available(self) -> bool:
        """检查服务是否可用（实现接口方法）"""
        try:
            # 检查API密钥
            if not self.api_key:
                return False

            # 检查配置
            if not self._config.weather_service.enabled:
                return False

            # 检查坐标服务
            try:
                self._ensure_coordinate_service()
                return self._coordinate_service.is_initialized()
            except Exception:
                return False

        except Exception:
            return False

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息（实现接口方法）"""
        return {
            'service_name': 'EnhancedCaiyunWeatherService',
            'initialized': True,
            'api_key_configured': bool(self.api_key),
            'coordinate_service_connected': self._coordinate_service is not None,
            'coordinate_service_initialized': (
                self._coordinate_service.is_initialized()
                if self._coordinate_service else False
            ),
            'config': {
                'enabled': self._config.weather_service.enabled,
                'timeout': self._config.weather_service.timeout,
                'max_retries': self._config.weather_service.max_retries,
                'cache_enabled': self._config.weather_service.cache_enabled,
                'cache_ttl': self._config.weather_service.cache_ttl,
            },
            'database_stats': self.coordinate_db.get_statistics(),
            'matcher_stats': self.place_matcher.get_statistics(),
        }

    def health_check(self) -> bool:
        """执行健康检查（实现接口方法）"""
        try:
            # 基础检查
            if not self.is_available():
                return False

            # 测试坐标服务健康检查
            coordinate_service = self._ensure_coordinate_service()
            if not coordinate_service.health_check():
                return False

            # 可以添加简单的API测试（但不实际调用以避免消耗配额）
            return True

        except Exception:
            return False

    # 保持向后兼容的现有方法
    def _get_coordinates_for_location(self, place_name: str) -> Optional[Tuple[float, float]]:
        """
        获取地名坐标（增强版本，支持全国地区）
        查询优先级: 1.本地数据库 -> 2.服务管理器坐标服务 -> 3.原有逻辑降级

        Args:
            place_name: 地名（支持省、市、县、乡各级）

        Returns:
            (longitude, latitude) 坐标元组，如果找不到则返回 None
        """
        if not place_name or not place_name.strip():
            return None

        # 1. 检查缓存
        if self._config.weather_service.cache_enabled:
            cached_coords = self.cache.get(place_name, extra_params={"type": "coordinates"})
            if cached_coords:
                logger.info(f"从缓存获取坐标: {place_name} -> {cached_coords}")
                return cached_coords

        # 2. 优先查询本地数据库（智能地名匹配）
        match_result = self.place_matcher.match_place(place_name)
        if match_result:
            coords = (match_result['longitude'], match_result['latitude'])

            # 缓存结果
            if self._config.weather_service.cache_enabled:
                self.cache.set(place_name, coords, ttl=self._config.weather_service.cache_ttl,
                             extra_params={"type": "coordinates"})

            logger.info(f"本地数据库匹配成功: {place_name} -> {match_result['name']} "
                       f"({coords[0]:.4f}, {coords[1]:.4f}) "
                       f"级别: {match_result['level_name']}")

            return coords

        # 3. 使用服务管理器获取坐标服务
        try:
            coordinate_service = self._ensure_coordinate_service()
            coordinate_result = coordinate_service.get_coordinate(place_name)
            if coordinate_result:
                coords = (coordinate_result.longitude, coordinate_result.latitude)

                # 缓存结果
                if self._config.weather_service.cache_enabled:
                    self.cache.set(place_name, coords, ttl=self._config.weather_service.cache_ttl,
                                 extra_params={"type": "coordinates"})

                logger.info(f"坐标服务匹配成功: {place_name} -> ({coords[0]:.4f}, {coords[1]:.4f})")
                return coords

        except Exception as e:
            logger.warning(f"坐标服务查询失败: {place_name}, 错误: {e}")

        logger.warning(f"无法获取坐标: {place_name}")
        return None

    def _call_caiyun_api(self, longitude: float, latitude: float) -> Optional[Dict]:
        """调用彩云天气API获取实时天气"""
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'alert': 'true',
                'dailysteps': '1',
                'hourlysteps': '24'
            }

            headers = {
                'X-Caiyun-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    return data
                else:
                    logger.error(f"彩云API返回错误: {data}")
                    return None
            else:
                logger.error(f"彩云API请求失败: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"调用彩云天气API失败: {e}")
            return None

    def _call_caiyun_api_forecast(self, longitude: float, latitude: float) -> Optional[Dict]:
        """调用彩云天气API获取预报数据"""
        try:
            params = {
                'lat': latitude,
                'lon': latitude,
                'alert': 'true',
                'dailysteps': '7',  # 获取7天预报
                'hourlysteps': '168'  # 获取168小时预报
            }

            headers = {
                'X-Caiyun-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    return data
                else:
                    logger.error(f"彩云API返回错误: {data}")
                    return None
            else:
                logger.error(f"彩云API请求失败: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"调用彩云天气API失败: {e}")
            return None

    def _convert_to_weather_condition(self, weather_data: Dict) -> WeatherCondition:
        """将彩云天气API数据转换为WeatherCondition对象"""
        realtime = weather_data.get('result', {}).get('realtime', {})

        return WeatherCondition(
            temperature=realtime.get('temperature', 0.0),
            humidity=realtime.get('humidity', 0.0),
            pressure=realtime.get('pressure', 1013.0),
            wind_speed=realtime.get('wind', {}).get('speed', 0.0),
            wind_direction=realtime.get('wind', {}).get('direction', 0.0),
            weather=realtime.get('skycon', 'unknown'),
            visibility=realtime.get('visibility', 10.0),
            timestamp=datetime.now()
        )

    def _convert_to_weather_forecast(self, weather_data: Dict, days: int) -> List[WeatherForecast]:
        """将彩云天气API数据转换为WeatherForecast列表"""
        forecasts = []
        daily = weather_data.get('result', {}).get('daily', {})

        if not daily or not daily.get('temperature'):
            return forecasts

        # 获取每日数据
        temperatures = daily.get('temperature', [])
        skycon = daily.get('skycon', [])

        for i in range(min(days, len(temperatures) - 1)):
            try:
                forecast_date = date.fromtimestamp(temperatures[i]['date'])

                # 获取当天的温度范围
                daily_temp = temperatures[i]
                daily_weather = skycon[i] if i < len(skycon) else {'value': 'unknown'}

                # 创建简化的天气条件（这里可以进一步扩展）
                condition = WeatherCondition(
                    temperature=(daily_temp['max'] + daily_temp['min']) / 2,
                    humidity=50.0,  # 彩云API可能不提供湿度预报
                    pressure=1013.0,
                    wind_speed=0.0,
                    wind_direction=0.0,
                    weather=daily_weather.get('value', 'unknown'),
                    visibility=10.0,
                    timestamp=datetime.combine(forecast_date, datetime.min.time())
                )

                forecast = WeatherForecast(
                    date=forecast_date,
                    conditions=[condition],
                    daily_high=daily_temp['max'],
                    daily_low=daily_temp['min'],
                    weather_summary=daily_weather.get('value', 'unknown')
                )

                forecasts.append(forecast)

            except Exception as e:
                logger.error(f"转换预报数据失败: {e}")
                continue

        return forecasts

    def cleanup(self) -> None:
        """清理资源"""
        try:
            if hasattr(self.place_matcher, 'close'):
                self.place_matcher.close()
        except Exception as e:
            logger.error(f"清理天气服务资源失败: {e}")