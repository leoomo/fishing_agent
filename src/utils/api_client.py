#!/usr/bin/env python3
"""
API客户端模块

简化API调用逻辑，提供统一的HTTP请求接口，
移除了过度的中间件和抽象层。
"""

import os
import requests
import logging
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv
from .cache import cache

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class APIClient:
    """简化的API客户端，提供基本的HTTP请求功能"""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        """
        初始化API客户端

        Args:
            base_url: 基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/') if base_url else None
        self.timeout = timeout
        self.session = requests.Session()

        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Fishing-Agent/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            use_cache: bool = True, cache_ttl: int = 300) -> Optional[Dict[str, Any]]:
        """
        发送GET请求

        Args:
            endpoint: API端点
            params: 请求参数
            use_cache: 是否使用缓存
            cache_ttl: 缓存TTL（秒）

        Returns:
            响应数据或None
        """
        url = self._build_url(endpoint)

        # 缓存逻辑
        if use_cache:
            cache_key = f"api:{url}:{str(params)}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"从缓存获取API响应: {url}")
                return cached_result

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
            else:
                data = {'text': response.text}

            # 缓存响应
            if use_cache:
                cache.set(cache_key, data, ttl=cache_ttl)

            logger.debug(f"API请求成功: {url}")
            return data

        except requests.Timeout:
            logger.error(f"API请求超时: {url}")
            return None
        except requests.ConnectionError:
            logger.error(f"API连接失败: {url}")
            return None
        except requests.HTTPError as e:
            logger.error(f"API HTTP错误 {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"API请求异常: {url}, 错误: {e}")
            return None

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
             json_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        发送POST请求

        Args:
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据

        Returns:
            响应数据或None
        """
        url = self._build_url(endpoint)

        try:
            if json_data:
                response = self.session.post(url, json=json_data, timeout=self.timeout)
            else:
                response = self.session.post(url, data=data, timeout=self.timeout)

            response.raise_for_status()

            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return {'text': response.text}

        except requests.RequestException as e:
            logger.error(f"POST请求失败: {url}, 错误: {e}")
            return None

    def _build_url(self, endpoint: str) -> str:
        """构建完整URL"""
        if self.base_url:
            if endpoint.startswith('/'):
                return f"{self.base_url}{endpoint}"
            else:
                return f"{self.base_url}/{endpoint}"
        return endpoint

    def close(self):
        """关闭会话"""
        self.session.close()


# 彩云天气API客户端
class CaiyunWeatherClient(APIClient):
    """彩云天气API专用客户端"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化彩云天气客户端

        Args:
            api_key: 彩云天气API密钥
        """
        self.api_key = api_key or os.getenv('CAIYUN_API_KEY')
        if not self.api_key:
            raise ValueError("未配置彩云天气API密钥 (CAIYUN_API_KEY)")

        super().__init__(base_url="https://api.caiyunapp.com/v2.6", timeout=15)

    def get_realtime_weather(self, longitude: float, latitude: float) -> Optional[Dict[str, Any]]:
        """
        获取实时天气

        Args:
            longitude: 经度
            latitude: 纬度

        Returns:
            天气数据或None
        """
        endpoint = f"/{self.api_key}/{longitude},{latitude}/realtime"
        params = {'alert': 'true'}

        return self.get(endpoint, params, use_cache=True, cache_ttl=600)  # 10分钟缓存

    def get_hourly_forecast(self, longitude: float, latitude: float, hours: int = 72) -> Optional[Dict[str, Any]]:
        """
        获取小时级预报

        Args:
            longitude: 经度
            latitude: 纬度
            hours: 预报小时数

        Returns:
            预报数据或None
        """
        endpoint = f"/{self.api_key}/{longitude},{latitude}/hourly"
        params = {'alert': 'true', 'hourlysteps': str(hours)}

        return self.get(endpoint, params, use_cache=True, cache_ttl=1800)  # 30分钟缓存

    def get_daily_forecast(self, longitude: float, latitude: float, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        获取日级预报

        Args:
            longitude: 经度
            latitude: 纬度
            days: 预报天数

        Returns:
            预报数据或None
        """
        endpoint = f"/{self.api_key}/{longitude},{latitude}/daily"
        params = {'alert': 'true', 'dailysteps': str(days)}

        return self.get(endpoint, params, use_cache=True, cache_ttl=3600)  # 1小时缓存


# 高德地图API客户端
class AmapGeocodingClient(APIClient):
    """高德地图地理编码API客户端"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化高德地图客户端

        Args:
            api_key: 高德地图API密钥
        """
        self.api_key = api_key or os.getenv('AMAP_API_KEY')
        if not self.api_key:
            raise ValueError("未配置高德地图API密钥 (AMAP_API_KEY)")

        super().__init__(base_url="https://restapi.amap.com/v3", timeout=10)

    def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """
        地理编码：地址转坐标

        Args:
            address: 地址

        Returns:
            地理编码结果或None
        """
        return self.get("/geocode/geo", params={
            'address': address,
            'key': self.api_key,
            'output': 'json'
        }, use_cache=True, cache_ttl=86400)  # 24小时缓存


# 全局客户端实例
_weather_client = None
_geocoding_client = None


def get_weather_client() -> CaiyunWeatherClient:
    """获取全局天气客户端实例"""
    global _weather_client
    if _weather_client is None:
        _weather_client = CaiyunWeatherClient()
    return _weather_client


def get_geocoding_client() -> AmapGeocodingClient:
    """获取全局地理编码客户端实例"""
    global _geocoding_client
    if _geocoding_client is None:
        _geocoding_client = AmapGeocodingClient()
    return _geocoding_client


def close_clients():
    """关闭所有客户端连接"""
    global _weather_client, _geocoding_client
    if _weather_client:
        _weather_client.close()
        _weather_client = None
    if _geocoding_client:
        _geocoding_client.close()
        _geocoding_client = None