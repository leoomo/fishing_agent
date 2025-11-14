"""
天气API智能路由器
根据时间范围自动选择最优的天气服务API
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .enums import ForecastRange, WeatherDataSource
from .utils.datetime_utils import calculate_days_from_now


class WeatherResult:
    """统一的天气查询结果"""
    
    def __init__(self, 
                 data_source: str,
                 hourly_data: list,
                 confidence: float,
                 api_url: str,
                 error_code: int = 0,
                 error_message: str = "",
                 cached: bool = False,
                 metadata: Optional[Dict[str, Any]] = None):
        self.data_source = data_source
        self.hourly_data = hourly_data
        self.confidence = confidence
        self.api_url = api_url
        self.error_code = error_code
        self.error_message = error_message
        self.cached = cached
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def get_temperature_range(self) -> tuple:
        """获取温度范围"""
        if not self.hourly_data:
            return (0, 0)
        temps = [h.get('temperature', 0) for h in self.hourly_data if h.get('temperature') is not None]
        return (min(temps), max(temps)) if temps else (0, 0)
    
    def get_weather_summary(self) -> str:
        """获取天气概况"""
        if not self.hourly_data:
            return "无数据"
        
        weather_counts = {}
        for hour in self.hourly_data:
            weather = hour.get('weather', '未知')
            weather_counts[weather] = weather_counts.get(weather, 0) + 1
        
        # 返回最主要的天气状况
        main_weather = max(weather_counts.items(), key=lambda x: x[1])[0]
        percentage = weather_counts[main_weather] / len(self.hourly_data) * 100
        return f"{main_weather}(占比{percentage:.0f}%)"
    
    def is_successful(self) -> bool:
        """检查查询是否成功"""
        return self.error_code in [0, 1] and len(self.hourly_data) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'data_source': self.data_source,
            'hourly_data': self.hourly_data,
            'confidence': self.confidence,
            'api_url': self.api_url,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'cached': self.cached,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'temperature_range': self.get_temperature_range(),
            'weather_summary': self.get_weather_summary()
        }


class WeatherApiRouter:
    """天气API智能路由器"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
        # 服务实例 (稍后初始化)
        self._hourly_service = None
        self._daily_service = None
        self._simulation_service = None
        
        # 性能统计
        self._stats = {
            'total_requests': 0,
            'hourly_requests': 0,
            'daily_requests': 0,
            'simulation_requests': 0,
            'cache_hits': 0,
            'errors': 0
        }
    
    def set_services(self, hourly_service=None, daily_service=None, simulation_service=None):
        """设置服务实例"""
        self._hourly_service = hourly_service
        self._daily_service = daily_service
        self._simulation_service = simulation_service
        self._logger.info("WeatherApiRouter services initialized")
    
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """
        获取天气预报数据的主要接口，根据时间范围自动路由到对应的服务。
        
        Args:
            location_info: 地理位置信息
                - name: 地点名称
                - lng: 经度
                - lat: 纬度
                - adcode: 行政区划代码 (可选)
            date_str: 查询日期，格式为"YYYY-MM-DD"
        
        Returns:
            WeatherResult: 统一格式的天气查询结果
        """
        start_time = datetime.now()
        self._stats['total_requests'] += 1
        
        try:
            # 1. 计算时间范围
            days_from_now = calculate_days_from_now(date_str)
            forecast_range = self._determine_forecast_range(days_from_now)

            self._logger.debug(f"路由决策: {date_str} (距今{days_from_now}天) -> {forecast_range.value}")

            # 2. 将相对日期转换为绝对日期（各个服务期望标准格式）
            from .utils.datetime_utils import get_absolute_date
            absolute_date = get_absolute_date(days_from_now)

            # 3. 选择对应服务
            service = self._get_service_by_range(forecast_range)
            if not service:
                raise ValueError(f"未找到对应的服务: {forecast_range}")

            # 4. 更新统计
            self._update_service_stats(forecast_range)

            # 5. 执行查询（使用绝对日期）
            result = await service.get_forecast(location_info, absolute_date)
            
            # 5. 标准化结果
            normalized_result = self._normalize_result(result, forecast_range)
            
            # 6. 记录性能日志
            duration = (datetime.now() - start_time).total_seconds()
            self._log_api_call(forecast_range, location_info.get('name', 'unknown'), duration, True)
            
            return normalized_result
            
        except Exception as e:
            # 错误处理
            duration = (datetime.now() - start_time).total_seconds()
            self._stats['errors'] += 1
            self._log_api_call(None, location_info.get('name', 'unknown'), duration, False, str(e))
            
            # 尝试紧急回退
            return await self._emergency_fallback(location_info, date_str, str(e))
    
    def _determine_forecast_range(self, days_from_now: int) -> ForecastRange:
        """
        根据距离今天的天数确定使用哪种预报服务。
        
        Args:
            days_from_now: 距离今天的天数
        
        Returns:
            ForecastRange: 预报范围枚举
        """
        if days_from_now <= 3:
            return ForecastRange.HOURLY
        elif days_from_now <= 7:
            return ForecastRange.DAILY
        else:
            return ForecastRange.SIMULATION
    
    def _get_service_by_range(self, forecast_range: ForecastRange):
        """根据预报范围获取对应的服务实例。"""
        if forecast_range == ForecastRange.HOURLY:
            return self._hourly_service
        elif forecast_range == ForecastRange.DAILY:
            return self._daily_service
        elif forecast_range == ForecastRange.SIMULATION:
            return self._simulation_service
        else:
            return None
    
    def _update_service_stats(self, forecast_range: ForecastRange):
        """更新服务统计信息"""
        if forecast_range == ForecastRange.HOURLY:
            self._stats['hourly_requests'] += 1
        elif forecast_range == ForecastRange.DAILY:
            self._stats['daily_requests'] += 1
        elif forecast_range == ForecastRange.SIMULATION:
            self._stats['simulation_requests'] += 1
    
    def _normalize_result(self, result: WeatherResult, forecast_range: ForecastRange) -> WeatherResult:
        """
        标准化不同服务返回的结果格式，确保数据格式一致性。
        
        Args:
            result: 服务返回的原始结果
            forecast_range: 预报范围
        
        Returns:
            WeatherResult: 标准化后的结果
        """
        # 根据数据源调整置信度
        confidence_mapping = {
            WeatherDataSource.HOURLY_API.value: 0.95,
            WeatherDataSource.DAILY_API.value: 0.85,
            WeatherDataSource.SIMULATION.value: 0.60,
            WeatherDataSource.CACHE.value: 0.90,
        }
        
        # 如果置信度未设置或需要调整，根据数据源重新设置
        if result.data_source in confidence_mapping:
            result.confidence = min(result.confidence, confidence_mapping[result.data_source])
        
        # 添加路由元数据
        result.metadata.update({
            'forecast_range': forecast_range.value,
            'routing_timestamp': datetime.now().isoformat(),
            'router_version': '1.0.0'
        })
        
        return result
    
    def _log_api_call(self, forecast_range: Optional[ForecastRange], location: str, 
                     duration: float, success: bool, error_msg: str = ""):
        """记录API调用信息，用于监控和调试"""
        log_data = {
            'operation': 'weather_router_call',
            'location': location,
            'forecast_range': forecast_range.value if forecast_range else 'none',
            'duration_seconds': round(duration, 3),
            'success': success,
            'error_message': error_msg,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self._logger.info(f"API调用成功: {log_data}")
        else:
            self._logger.error(f"API调用失败: {log_data}")
    
    async def _emergency_fallback(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """
        紧急回退机制，当所有服务都不可用时使用基础模拟数据
        
        Args:
            location_info: 地理位置信息
            date_str: 查询日期
            error_msg: 原始错误信息
        
        Returns:
            WeatherResult: 紧急回退结果
        """
        self._logger.warning(f"所有天气服务不可用，使用紧急回退: {error_msg}")
        
        # 生成基础模拟数据
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            target_date = datetime.now() + timedelta(days=1)
        
        # 简单的24小时模拟数据
        hourly_data = []
        base_temp = 20.0  # 基础温度
        
        for hour in range(24):
            hour_dt = target_date.replace(hour=hour, minute=0, second=0)
            
            # 简单的温度变化模拟
            temp_variation = 5 * (1 - abs(hour - 14) / 10)  # 下午2点最热
            temperature = base_temp + temp_variation
            
            hour_data = {
                'time': hour_dt,
                'temperature': round(temperature, 1),
                'weather': '多云',
                'wind_speed': 3.0,
                'humidity': 60.0,
                'pressure': 1013.0,
                'data_source': 'emergency_fallback'
            }
            hourly_data.append(hour_data)
        
        return WeatherResult(
            data_source=WeatherDataSource.EMERGENCY.value,
            hourly_data=hourly_data,
            confidence=0.3,  # 紧急数据置信度很低
            api_url="emergency_fallback",
            error_code=1,
            error_message=f"所有服务不可用，使用紧急回退数据: {error_msg}",
            cached=False,
            metadata={
                'fallback_reason': 'all_services_failed',
                'original_error': error_msg,
                'emergency_fallback': True
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取路由器统计信息"""
        total = max(self._stats['total_requests'], 1)  # 避免除零
        
        return {
            **self._stats,
            'hourly_percentage': round(self._stats['hourly_requests'] / total * 100, 1),
            'daily_percentage': round(self._stats['daily_requests'] / total * 100, 1),
            'simulation_percentage': round(self._stats['simulation_requests'] / total * 100, 1),
            'cache_hit_rate': round(self._stats['cache_hits'] / total * 100, 1),
            'error_rate': round(self._stats['errors'] / total * 100, 1),
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            'total_requests': 0,
            'hourly_requests': 0,
            'daily_requests': 0,
            'simulation_requests': 0,
            'cache_hits': 0,
            'errors': 0
        }
        self._logger.info("路由器统计信息已重置")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        services_status = {}
        
        if self._hourly_service:
            services_status['hourly'] = {'available': True, 'type': 'HourlyWeatherService'}
        else:
            services_status['hourly'] = {'available': False, 'type': None}
            
        if self._daily_service:
            services_status['daily'] = {'available': True, 'type': 'DailyWeatherService'}
        else:
            services_status['daily'] = {'available': False, 'type': None}
            
        if self._simulation_service:
            services_status['simulation'] = {'available': True, 'type': 'SimulationService'}
        else:
            services_status['simulation'] = {'available': False, 'type': None}
        
        available_services = sum(1 for s in services_status.values() if s['available'])
        
        return {
            'status': 'healthy' if available_services >= 2 else 'degraded',
            'services': services_status,
            'available_services_count': available_services,
            'total_services_count': 3,
            'stats': self.get_stats(),
            'timestamp': datetime.now().isoformat()
        }

    def __del__(self):
        """析构函数，确保服务被正确清理"""
        try:
            # 清理服务实例
            if hasattr(self, '_hourly_service') and self._hourly_service:
                if hasattr(self._hourly_service, '_api_client'):
                    self._hourly_service._api_client.close()

            if hasattr(self, '_daily_service') and self._daily_service:
                if hasattr(self._daily_service, '_api_client'):
                    self._daily_service._api_client.close()

            if hasattr(self, '_simulation_service') and self._simulation_service:
                # Simulation service may not have API client, but检查一下
                if hasattr(self._simulation_service, '_api_client'):
                    self._simulation_service._api_client.close()

        except Exception:
            pass