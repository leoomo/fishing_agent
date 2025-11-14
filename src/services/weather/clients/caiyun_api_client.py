"""
彩云天气API客户端
提供对彩云天气v2.6 API的访问接口
"""
import asyncio
import logging
import sys
from typing import Dict, Any, Optional
import aiohttp


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
    """彩云天气API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.caiyunapp.com/v2.6"):
        self._logger = logging.getLogger(__name__)
        self._api_key = api_key
        self._base_url = base_url
        self._session = None
        
        # 配置参数
        self._timeout = aiohttp.ClientTimeout(total=10.0, connect=3.0)
        self._retry_attempts = 3
        
    async def _ensure_session(self):
        """确保aiohttp会话已创建"""
        if self._session is None or self._session.closed:
            # 创建连接池优化的会话
            connector = aiohttp.TCPConnector(
                limit=100,              # 总连接池大小
                limit_per_host=20,      # 每个主机连接数
                keepalive_timeout=30,   # 保持连接时间
                enable_cleanup_closed=True,
                use_dns_cache=True
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self._timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'WeatherService/1.0 (CaiyunApiClient)'
                }
            )
    
    async def close(self):
        """关闭客户端会话"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_hourly_forecast(self, lng: float, lat: float, **params) -> Dict[str, Any]:
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
        return await self._make_api_request("/weather", {
            'lng': lng,
            'lat': lat,
            'hourlysteps': params.get('hourlysteps', 72),
            'alert': params.get('alert', True)
        })
    
    async def get_daily_forecast(self, lng: float, lat: float, **params) -> Dict[str, Any]:
        """
        获取逐天天气预报
        
        Args:
            lng: 经度
            lat: 纬度
            **params: 其他参数
                - dailysteps: 预报步数 (默认7)
                - alert: 是否包含天气预警 (默认true)
        
        Returns:
            Dict[str, Any]: API响应数据
        
        Raises:
            WeatherApiException: API调用相关异常
        """
        return await self._make_api_request("/weather", {
            'lng': lng,
            'lat': lat,
            'dailysteps': params.get('dailysteps', 7),
            'alert': params.get('alert', True)
        })
    
    async def get_realtime_weather(self, lng: float, lat: float) -> Dict[str, Any]:
        """
        获取实时天气
        
        Args:
            lng: 经度
            lat: 纬度
        
        Returns:
            Dict[str, Any]: API响应数据
        
        Raises:
            WeatherApiException: API调用相关异常
        """
        return await self._make_api_request("/weather", {
            'lng': lng,
            'lat': lat,
            'alert': True
        })
    
    async def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
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
  
        await self._ensure_session()
        
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
        
        last_exception = None
        
        for attempt in range(self._retry_attempts):
            try:
                self._logger.debug(f"API请求尝试 {attempt + 1}/{self._retry_attempts}: {url}")
                
                async with self._session.get(url, params=query_params) as response:
                    response_data = await response.json()
                    
                    # 处理不同的HTTP状态码
                    if response.status == 200:
                        return response_data
                    elif response.status == 401:
                        raise AuthenticationException("API密钥无效或已过期")
                    elif response.status == 404:
                        raise LocationNotFoundException("指定的地理位置无效")
                    elif response.status == 429:
                        raise ApiQuotaExceededException("API调用频率超限")
                    elif response.status >= 500:
                        # 服务器错误，可以重试
                        raise NetworkTimeoutException(f"服务器错误: {response.status}")
                    else:
                        raise WeatherApiException(f"API请求失败: {response.status}")
                        
            except aiohttp.ClientError as e:
                last_exception = NetworkTimeoutException(f"网络请求失败: {e}")
                if attempt < self._retry_attempts - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    self._logger.warning(f"网络错误，{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise last_exception

            except asyncio.TimeoutError as e:
                last_exception = NetworkTimeoutException(f"网络请求超时: {e}")
                if attempt < self._retry_attempts - 1:
                    wait_time = 2 ** attempt
                    self._logger.warning(f"请求超时，{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise last_exception
                    
            except Exception as e:
                # 检查是否是已知的API异常
                if isinstance(e, WeatherApiException):
                    raise

                last_exception = WeatherApiException(f"未知错误: {e}")
                if attempt < self._retry_attempts - 1:
                    wait_time = 1 + attempt
                    self._logger.warning(f"未知错误，{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise last_exception
        
        # 所有重试都失败
        raise last_exception or WeatherApiException("API请求失败")
    
    def _get_api_key_from_env(self) -> str:
        """从环境变量获取API密钥"""
        import os
        return os.getenv('CAIYUN_API_KEY', '')
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            # 使用北京坐标测试连接
            result = await self.get_realtime_weather(116.4, 39.9)
            
            return {
                'status': 'success',
                'message': 'API连接正常',
                'api_version': result.get('lang', 'unknown'),
                'timestamp': result.get('server_time', 'unknown')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'API连接失败: {e}',
                'timestamp': None
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        try:
            # 安全获取时间戳
            try:
                timestamp = asyncio.get_event_loop().time()
            except (RuntimeError, AttributeError):
                # 如果没有事件循环或循环已关闭，使用系统时间
                import time
                timestamp = time.time()
        except Exception:
            timestamp = 0.0

        # 安全检查会话状态
        session_status = 'inactive'
        if self._session:
            try:
                session_status = 'active' if not self._session.closed else 'closed'
            except Exception:
                session_status = 'error'

        return {
            'client': 'CaiyunApiClient',
            'base_url': self._base_url,
            'timeout': self._timeout.total,
            'retry_attempts': self._retry_attempts,
            'session_status': session_status,
            'api_key_set': bool(self._api_key or self._get_api_key_from_env()),
            'timestamp': timestamp
        }
    
    def close(self):
        """显式关闭客户端会话"""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            # 简单同步关闭，不依赖现有事件循环
            try:
                import asyncio
                # 创建独立的事件循环来关闭会话
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(self._close_async())
                finally:
                    new_loop.close()
                    self._session = None
            except Exception as e:
                # 忽略关闭错误，记录日志
                self._logger.debug(f"Session cleanup error ignored: {e}")
                # 强制清理引用，让GC处理
                self._session = None

    async def _close_async(self):
        """异步关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    def __del__(self):
        """析构函数，尝试清理资源"""
        try:
            if hasattr(self, '_session') and self._session:
                # 简单清理，避免在析构函数中使用异步操作
                self._session = None
        except Exception:
            pass  # 完全忽略析构函数中的错误