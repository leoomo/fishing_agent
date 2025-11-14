#!/usr/bin/env python3
"""
彩云天气 API 服务模块
提供实时天气数据查询功能
"""

import os
import json
import requests
from typing import Dict, Optional, Union
import logging
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class CaiyunWeatherService:
    """彩云天气 API 服务"""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        初始化天气服务

        Args:
            api_key: 彩云天气 API 密钥，如果为 None 则从环境变量获取
            timeout: API 请求超时时间（秒）
        """
        self.api_key = api_key or os.getenv("CAIYUN_API_KEY")
        self.timeout = timeout
        self.base_url = "https://api.caiyunapp.com/v2.6"

        if not self.api_key:
            logger.warning("未设置彩云天气 API 密钥，将使用模拟数据")

    def get_coordinates(self, city: str) -> Optional[tuple]:
        """
        获取城市坐标（简化版本，支持主要城市）

        Args:
            city: 城市名称

        Returns:
            (longitude, latitude) 坐标元组，如果找不到则返回 None
        """
        # 主要城市坐标映射
        city_coordinates = {
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
            "厦门": (118.1119, 24.4899)
        }

        return city_coordinates.get(city.strip())

    def call_weather_api(self, longitude: float, latitude: float) -> Optional[Dict]:
        """
        调用彩云天气 API

        Args:
            longitude: 经度
            latitude: 纬度

        Returns:
            API 响应数据，失败时返回 None
        """
        if not self.api_key:
            logger.error("未配置 API 密钥")
            return None

        url = f"{self.base_url}/{self.api_key}/{longitude},{latitude}/realtime"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # 检查 API 响应状态
            if data.get("status") != "ok":
                logger.error(f"API 返回错误状态: {data.get('status')}")
                return None

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"API 响应解析失败: {str(e)}")
            return None

    def parse_weather_data(self, api_data: Dict) -> Optional[WeatherData]:
        """
        解析 API 返回的天气数据

        Args:
            api_data: API 返回的原始数据

        Returns:
            解析后的 WeatherData 对象，失败时返回 None
        """
        try:
            # 验证数据结构
            if not isinstance(api_data, dict) or "result" not in api_data:
                return None

            result = api_data.get("result", {})
            if not isinstance(result, dict) or "realtime" not in result:
                return None

            realtime = result.get("realtime", {})
            if not isinstance(realtime, dict):
                return None

            # 获取天气状况
            skycon = realtime.get("skycon", "")
            condition_map = {
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

            condition = condition_map.get(skycon, skycon)

            return WeatherData(
                temperature=realtime.get("temperature", 0),
                apparent_temperature=realtime.get("apparent_temperature", 0),
                humidity=realtime.get("humidity", 0),
                pressure=realtime.get("pressure", 0),
                wind_speed=realtime.get("wind", {}).get("speed", 0),
                wind_direction=realtime.get("wind", {}).get("direction", 0),
                condition=condition,
                description=f"{condition}，{realtime.get('temperature', 0)}°C"
            )

        except Exception as e:
            logger.error(f"天气数据解析失败: {str(e)}")
            return None

    def get_fallback_weather(self, city: str) -> WeatherData:
        """
        获取模拟天气数据（当 API 不可用时使用）

        Args:
            city: 城市名称

        Returns:
            模拟的天气数据
        """
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

        weather_info = fallback_weather.get(city.strip(), {
            "temp": random.randint(15, 30),
            "condition": random.choice(["晴天", "多云", "阴天"]),
            "humidity": random.randint(40, 80)
        })

        return WeatherData(
            temperature=weather_info["temp"],
            apparent_temperature=weather_info["temp"] + random.randint(-2, 2),
            humidity=weather_info["humidity"],
            pressure=random.randint(1000, 1020),
            wind_speed=random.uniform(0, 20),
            wind_direction=random.randint(0, 360),
            condition=weather_info["condition"],
            description=f"{weather_info['condition']}，{weather_info['temp']}°C"
        )

    def get_weather(self, city: str) -> tuple[WeatherData, str]:
        """
        获取指定城市的天气信息

        Args:
            city: 城市名称

        Returns:
            (WeatherData, status_message) 元组
            status_message 描述了数据来源（API 或模拟数据）
        """
        # 获取城市坐标
        coordinates = self.get_coordinates(city)
        if not coordinates:
            error_msg = f"未找到城市 '{city}' 的坐标信息，使用模拟数据"
            logger.warning(error_msg)
            return self.get_fallback_weather(city), "模拟数据（城市不存在）"

        longitude, latitude = coordinates

        # 尝试调用 API
        if self.api_key:
            api_data = self.call_weather_api(longitude, latitude)
            if api_data:
                weather_data = self.parse_weather_data(api_data)
                if weather_data:
                    return weather_data, "实时数据（彩云天气 API）"
                else:
                    logger.warning("API 数据解析失败，使用模拟数据")
            else:
                logger.warning("API 调用失败，使用模拟数据")
        else:
            logger.info("未配置 API 密钥，使用模拟数据")

        # 回退到模拟数据
        fallback_data = self.get_fallback_weather(city)
        return fallback_data, "模拟数据（API 不可用）"

# 全局天气服务实例
_weather_service = None

def get_weather_service() -> CaiyunWeatherService:
    """获取全局天气服务实例"""
    global _weather_service
    if _weather_service is None:
        _weather_service = CaiyunWeatherService()
    return _weather_service

def get_weather_info(city: str) -> str:
    """
    获取天气信息的便捷函数

    Args:
        city: 城市名称

    Returns:
        格式化的天气信息字符串
    """
    service = get_weather_service()
    weather_data, source = service.get_weather(city)

    weather_info = (
        f"{city}天气: {weather_data.condition}，"
        f"温度 {weather_data.temperature:.1f}°C "
        f"(体感 {weather_data.apparent_temperature:.1f}°C)，"
        f"湿度 {weather_data.humidity:.0f}%，"
        f"风速 {weather_data.wind_speed:.1f}km/h\n"
        f"数据来源: {source}"
    )

    return weather_info

if __name__ == "__main__":
    # 测试代码
    test_cities = ["北京", "上海", "广州", "不存在的城市"]

    for city in test_cities:
        print(f"测试 {city}:")
        print(get_weather_info(city))
        print("-" * 50)