"""
彩云天气API客户端 - 同步版本
提供对彩云天气v2.6 API的同步访问接口
"""
import logging
import sys
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class WeatherApiException(Exception):
    """天气API异常基类"""
    pass


class NetworkTimeoutException(WeatherApiException):
    """网络超时异常"""
    pass


class ApiQuotaExceededException(WeatherApiException):
    """API配额超限异常"""
    pass


class AuthenticationException(WeatherApiException):
    """认证异常"""
    pass


class LocationNotFoundException(WeatherApiException):
    """地理位置未找到异常"""
    pass


class CaiyunApiClient:
    """彩云天气API客户端 - 同步版本"""

    def __init__(self, api_key: str = None, base_url: str = "https://api.caiyunapp.com/v2.6"):
        self._logger = logging.getLogger(__name__)
        self._api_key = api_key
        self._base_url = base_url
        self._session = None

        # 配置参数
        self._timeout = 10.0  # 总超时时间（秒）
        self._connect_timeout = 3.0  # 连接超时时间（秒）
        self._retry_attempts = 3

    def _ensure_session(self):
        """确保requests会话已创建"""
        if self._session is None:
            # 创建带重试机制的会话
            self._session = requests.Session()

            # 配置重试策略
            retry_strategy = Retry(
                total=self._retry_attempts,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

    def close(self):
        """关闭客户端会话"""
        if self._session:
            self._session.close()
            self._session = None

    def get_hourly_forecast(self, lng: float, lat: float, **params) -> Dict[str, Any]:
        """
        获取逐小时天气预报

        Args:
            lng: 经度
            lat: 纬度
            **params: 其他参数
                - hourlysteps: 预报步数 (默认72)
                - alert: 是否包含天气预警 (默认true)

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            WeatherApiException: API调用相关异常
        """
        return self._make_api_request("/weather", {
            'lng': lng,
            'lat': lat,
            'hourlysteps': params.get('hourlysteps', 72),
            'alert': params.get('alert', True)
        })

    def get_daily_forecast(self, lng: float, lat: float, **params) -> Dict[str, Any]:
        """
        获取每日天气预报

        Args:
            lng: 经度
            lat: 纬度
            **params: 其他参数
                - dailysteps: 预报步数 (默认15)
                - alert: 是否包含天气预警 (默认true)

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            WeatherApiException: API调用相关异常
        """
        return self._make_api_request("/weather", {
            'lng': lng,
            'lat': lat,
            'dailysteps': params.get('dailysteps', 15),
            'alert': params.get('alert', True)
        })

    def get_realtime_weather(self, lng: float, lat: float, **params) -> Dict[str, Any]:
        """
        获取实时天气

        Args:
            lng: 经度
            lat: 纬度
            **params: 其他参数

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            WeatherApiException: API调用相关异常
        """
        return self._make_api_request("/weather", {
            'lng': lng,
            'lat': lat,
            'alert': params.get('alert', True)
        })

    def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发起API请求

        Args:
            endpoint: API端点
            params: 请求参数

        Returns:
            Dict[str, Any]: API响应数据

        Raises:
            WeatherApiException: API调用相关异常
        """
        self._ensure_session()

        # 获取API密钥
        api_key = self._api_key or self._get_api_key_from_env()
        if not api_key:
            raise AuthenticationException("未设置彩云天气API密钥")

        # 构建URL
        lng = params.pop('lng')
        lat = params.pop('lat')
        url = f"{self._base_url}/{api_key}/{lng},{lat}{endpoint}"

        # 构建查询参数
        query_params = {}
        for key, value in params.items():
            if value is not None:
                if isinstance(value, bool):
                    query_params[key] = str(value).lower()
                else:
                    query_params[key] = value

        try:
            self._logger.debug(f"API请求: {url}")

            response = self._session.get(
                url,
                params=query_params,
                timeout=(self._connect_timeout, self._timeout)
            )
            response.raise_for_status()  # 检查HTTP状态码

            response_data = response.json()

            # 处理不同的HTTP状态码
            if response.status_code == 200:
                return response_data
            elif response.status_code == 401:
                raise AuthenticationException("API密钥无效或已过期")
            elif response.status_code == 404:
                raise LocationNotFoundException("指定的地理位置无效")
            elif response.status_code == 429:
                raise ApiQuotaExceededException("API调用频率超限")
            elif response.status_code >= 500:
                raise NetworkTimeoutException(f"服务器错误: {response.status_code}")
            else:
                raise WeatherApiException(f"API请求失败: {response.status_code}")

        except requests.exceptions.Timeout as e:
            raise NetworkTimeoutException(f"网络请求超时: {e}")
        except requests.exceptions.ConnectionError as e:
            raise NetworkTimeoutException(f"网络连接失败: {e}")
        except requests.exceptions.HTTPError as e:
            if "401" in str(e):
                raise AuthenticationException("API密钥无效或已过期")
            elif "404" in str(e):
                raise LocationNotFoundException("指定的地理位置无效")
            elif "429" in str(e):
                raise ApiQuotaExceededException("API调用频率超限")
            elif response.status_code >= 500:
                raise NetworkTimeoutException(f"服务器错误: {response.status_code}")
            else:
                raise WeatherApiException(f"HTTP错误: {e}")
        except ValueError as e:
            raise WeatherApiException(f"响应数据解析失败: {e}")
        except Exception as e:
            # 检查是否是已知的API异常
            if isinstance(e, WeatherApiException):
                raise
            raise WeatherApiException(f"未知错误: {e}")

    def _get_api_key_from_env(self) -> str:
        """从环境变量获取API密钥"""
        import os
        return os.getenv('CAIYUN_API_KEY', '')

    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接

        Returns:
            Dict[str, Any]: 连接状态信息
        """
        try:
            # 使用北京天安门坐标测试
            result = self.get_realtime_weather(116.397128, 39.916527)
            return {
                'status': 'success',
                'message': 'API连接正常',
                'result_sample': {
                    'status': result.get('status'),
                    'lang': result.get('lang'),
                    'location': result.get('location')
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'API连接失败: {e}',
                'error_type': type(e).__name__
            }

    def get_status(self) -> Dict[str, Any]:
        """
        获取客户端状态

        Returns:
            Dict[str, Any]: 客户端状态信息
        """
        import time

        session_status = 'active' if self._session else 'inactive'

        return {
            'client': 'CaiyunApiClient (Sync)',
            'base_url': self._base_url,
            'timeout': self._timeout,
            'connect_timeout': self._connect_timeout,
            'retry_attempts': self._retry_attempts,
            'session_status': session_status,
            'api_key_set': bool(self._api_key or self._get_api_key_from_env()),
            'timestamp': time.time()
        }