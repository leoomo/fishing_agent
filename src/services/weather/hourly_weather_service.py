"""
逐小时天气预报服务 (0-3天)
专门处理3天内的逐小时天气预报查询
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .weather_cache import WeatherCache
from .clients.caiyun_api_client import CaiyunApiClient
from .utils.datetime_utils import calculate_days_from_now
from .enums import WeatherErrorCode, WeatherDataSource
from .weather_api_router import WeatherResult


class DateOutOfRangeException(Exception):
    """查询日期超出服务范围"""
    pass


class LocationNotFoundException(Exception):
    """地理位置未找到"""
    pass


class ApiQuotaExceededException(Exception):
    """API调用配额超限"""
    pass


class WeatherDataCorruptionException(Exception):
    """天气数据损坏或格式错误"""
    pass


class NetworkTimeoutException(Exception):
    """网络请求超时"""
    pass


class HourlyWeatherService:
    """逐小时天气预报服务 (0-3天)"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._cache = WeatherCache(default_ttl=1800, file_path="data/cache/weather_hourly_cache.json")  # 30分钟TTL
        self._api_client = CaiyunApiClient()
        
        # 配置参数
        self.max_forecast_days = 3
        self.request_timeout = 10.0
        self.max_retry_attempts = 3
        
        # 统计信息
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0,
            'date_out_of_range': 0
        }
    
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """
        获取指定日期的逐小时天气预报数据。

        Args:
            location_info: 地理位置信息
                - name: 地点名称
                - lng: 经度
                - lat: 纬度
                - adcode: 行政区划代码 (可选)
            date_str: 查询日期，格式为"YYYY-MM-DD"
                必须在当前日期的3天内 (包括今天)

        Returns:
            WeatherResult: 统一格式的天气查询结果
        """
    
        self._stats['total_requests'] += 1
        start_time = datetime.now()
        
        try:
            # 1. 验证日期范围
            days_from_now = calculate_days_from_now(date_str)

            if days_from_now < 0:
                # 过去日期的错误提示
                self._stats['date_out_of_range'] += 1
                raise DateOutOfRangeException(f"查询日期{date_str}是过去日期，逐小时预报服务仅支持未来天气查询")
            elif days_from_now > self.max_forecast_days:
                # 未来日期超出范围的错误提示
                self._stats['date_out_of_range'] += 1
                raise DateOutOfRangeException(f"查询日期{date_str}超出逐小时预报范围({self.max_forecast_days}天)，当前仅支持未来{self.max_forecast_days}天内的天气预报")
            
            # 2. 生成缓存键
            cache_key = self._generate_cache_key(location_info, date_str)
            
            # 3. 检查缓存
            cached_result = self._cache.get(cache_key)
            if cached_result:
                self._stats['cache_hits'] += 1
                self._logger.debug(f"缓存命中: {cache_key}")
                cached_result.cached = True
                return cached_result
            
            # 4. 调用API
            self._stats['api_calls'] += 1
            api_data = await self._call_api_with_retry(location_info)
            
            # 5. 处理数据
            result = self._process_hourly_data(api_data, date_str)
            
            # 6. 缓存结果
            self._cache.set(cache_key, result)
            
            # 7. 记录性能日志
            duration = (datetime.now() - start_time).total_seconds()
            self._logger.info(f"逐小时预报查询完成: {location_info['name']} {date_str} 耗时{duration:.2f}s")
            
            return result
            
        except DateOutOfRangeException as e:
            # 日期范围错误特殊处理
            self._stats['date_out_of_range'] += 1
            self._logger.warning(f"逐小时预报日期范围错误: {location_info['name']} {date_str} - {e}")

            # 对于日期范围错误，直接返回历史日期模拟数据或提示
            return await self._handle_date_out_of_range(location_info, date_str, str(e))

        except Exception as e:
            self._stats['errors'] += 1
            self._logger.error(f"逐小时预报查询失败: {location_info['name']} {date_str} 错误: {e}")

            # 错误回退
            return await self._fallback_to_simulation(location_info, date_str, str(e))
    
    async def _call_api_with_retry(self, location_info: dict) -> Dict[str, Any]:
        """带重试机制的API调用"""
        last_exception = None

        for attempt in range(self.max_retry_attempts):
            try:
                api_data = await self._api_client.get_hourly_forecast(
                    lng=location_info['lng'],
                    lat=location_info['lat'],
                    hourlysteps=72
                )

                # 验证API响应
                if not self._validate_api_response(api_data):
                    raise WeatherDataCorruptionException("API响应数据格式错误")

                return api_data

            except NetworkTimeoutException as e:
                last_exception = e
                if attempt < self.max_retry_attempts - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    self._logger.warning(f"网络超时，{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
                    
            except ApiQuotaExceededException as e:
                # 配额超限不需要重试
                raise
                
            except Exception as e:
                # 检查是否是已知的API异常类型
                if isinstance(e, (WeatherDataCorruptionException, NetworkTimeoutException,
                                ApiQuotaExceededException, LocationNotFoundException)):
                    raise

                last_exception = e
                if attempt < self.max_retry_attempts - 1:
                    wait_time = 1 + attempt
                    self._logger.warning(f"API调用失败，{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        # 所有重试都失败
        raise last_exception or Exception("API调用失败")
    
    def _validate_api_response(self, api_data: Dict[str, Any]) -> bool:
        """验证API响应数据的完整性"""
        try:
            # 检查基本结构
            if not isinstance(api_data, dict):
                return False
            
            if api_data.get('status') != 'ok':
                return False
            
            result = api_data.get('result', {})
            if not isinstance(result, dict):
                return False
            
            hourly = result.get('hourly', {})
            if not isinstance(hourly, dict):
                return False
            
            if hourly.get('status') != 'ok':
                return False
            
            # 检查必要字段 (彩云API字段映射)
            required_fields = ['temperature', 'wind', 'humidity', 'skycon']
            for field in required_fields:
                if field not in hourly or not isinstance(hourly[field], list):
                    return False

            # 检查数据长度
            temp_count = len(hourly['temperature'])
            for field in required_fields:
                if len(hourly[field]) != temp_count:
                    return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"API响应验证失败: {e}")
            return False
    
    def _process_hourly_data(self, api_data: dict, target_date: str) -> WeatherResult:
        """
        处理API返回的逐小时数据，提取目标日期的24小时数据。
        
        Args:
            api_data: 彩云天气API返回的原始数据
            target_date: 目标日期字符串
        
        Returns:
            WeatherResult: 处理后的天气结果
        """
        try:
            hourly_data = api_data.get('result', {}).get('hourly', {})

            # 从温度数据中提取时间信息 (彩云API格式)
            temperature_data = hourly_data.get('temperature', [])
            if not temperature_data:
                raise WeatherDataCorruptionException("API响应中没有温度数据")

            # 筛选目标日期的时间索引
            target_indices = self._extract_target_date_hours_from_datetime(temperature_data, target_date)

            if not target_indices:
                raise WeatherDataCorruptionException(f"未找到目标日期{target_date}的小时数据")
            
            # 构建24小时数据
            hourly_result = self._build_hourly_data_list(api_data, target_indices, target_date)
            
            if len(hourly_result) != 24:
                self._logger.warning(f"小时数据不完整: 期望24小时，实际{len(hourly_result)}小时")
            
            return WeatherResult(
                data_source=WeatherDataSource.HOURLY_API.value,
                hourly_data=hourly_result,
                confidence=0.95,  # API数据精度高
                api_url="weather/hourly?hourlysteps=72",
                error_code=0,
                error_message="",
                cached=False,
                metadata={
                    'api_data_points': len(temperature_data),
                    'target_indices_count': len(target_indices),
                    'data_completeness': len(hourly_result) / 24.0,
                    'source_api': 'caiyun_v2.6'
                }
            )
            
        except Exception as e:
            self._logger.error(f"处理逐小时数据失败: {e}")
            raise WeatherDataCorruptionException(f"数据处理失败: {e}")

    def _extract_target_date_hours_from_datetime(self, datetime_data: list, target_date: str) -> List[int]:
        """
        从彩云API的datetime格式数据中筛选出目标日期的24小时索引。

        Args:
            datetime_data: API返回的包含datetime字段的数据数组
            target_date: 目标日期

        Returns:
            List[int]: 目标日期24小时对应的索引数组
        """
        try:
            target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
            target_date_str = target_datetime.strftime("%Y-%m-%d")

            target_indices = []

            for i, item in enumerate(datetime_data):
                if isinstance(item, dict) and 'datetime' in item:
                    item_datetime_str = item['datetime']
                    # 彩云API返回格式: "2025-11-04T23:00+08:00"
                    # 提取日期部分
                    item_date = item_datetime_str.split('T')[0]
                    if item_date == target_date_str:
                        target_indices.append(i)

            self._logger.debug(f"目标日期{target_date}找到{len(target_indices)}个小时数据")
            return target_indices

        except Exception as e:
            self._logger.error(f"提取目标日期时间索引失败: {e}")
            return []

    def _extract_target_date_hours(self, timestamps: list, target_date: str) -> List[int]:
        """
        从72小时时间戳中筛选出目标日期的24小时索引。
        
        Args:
            timestamps: API返回的时间戳数组 (Unix时间戳)
            target_date: 目标日期
        
        Returns:
            List[int]: 目标日期24小时对应的时间戳索引数组
        """
        try:
            target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
            target_start = target_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            target_end = target_start + timedelta(days=1)
            
            target_indices = []
            target_timestamp_start = target_start.timestamp()
            target_timestamp_end = target_end.timestamp()
            
            for i, timestamp in enumerate(timestamps):
                if target_timestamp_start <= timestamp < target_timestamp_end:
                    target_indices.append(i)
            
            self._logger.debug(f"目标日期{target_date}找到{len(target_indices)}个小时数据")
            return target_indices
            
        except Exception as e:
            self._logger.error(f"提取目标日期时间索引失败: {e}")
            return []
    
    def _build_hourly_data_list(self, api_data: dict, target_indices: List[int], target_date: str) -> List[Dict[str, Any]]:
        """
        根据索引列表构建24小时详细数据。
        
        Args:
            api_data: API原始数据
            target_indices: 目标小时索引数组
            target_date: 目标日期
        
        Returns:
            List[Dict[str, Any]]: 24小时详细数据对象列表
        """
        hourly_data = api_data.get('result', {}).get('hourly', {})
        
        # 提取所有数据数组 (彩云API字段)
        temperature_data = hourly_data.get('temperature', [])
        weather_conditions = hourly_data.get('skycon', [])
        wind_data = hourly_data.get('wind', [])
        humidity_data = hourly_data.get('humidity', [])
        pressure_data = hourly_data.get('pressure', [])
        visibility_data = hourly_data.get('visibility', [])
        precipitation_data = hourly_data.get('precipitation', [])

        # 空气质量数据 (可选)
        air_quality_data = hourly_data.get('air_quality', {})
        aqi_data = air_quality_data.get('aqi', {}).get('value', []) if isinstance(air_quality_data.get('aqi'), dict) else []
        pm25_data = air_quality_data.get('pm25', {}).get('value', []) if isinstance(air_quality_data.get('pm25'), dict) else []
        
        hourly_result = []
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        
        for i, idx in enumerate(target_indices):
            try:
                # 从彩云API数据中提取时间
                if idx < len(temperature_data):
                    temp_item = temperature_data[idx]
                    if isinstance(temp_item, dict) and 'datetime' in temp_item:
                        hour_dt = datetime.fromisoformat(temp_item['datetime'].replace('+08:00', '+00:00'))
                    else:
                        hour_dt = target_datetime.replace(hour=i, minute=0, second=0)
                else:
                    hour_dt = target_datetime.replace(hour=i, minute=0, second=0)

                # 获取各项数据 (彩云API格式)
                temp_val = temperature_data[idx].get('value', 20.0) if idx < len(temperature_data) and isinstance(temperature_data[idx], dict) else 20.0

                # 风速和风向
                wind_val = wind_data[idx].get('speed', 2.0) if idx < len(wind_data) and isinstance(wind_data[idx], dict) else {'speed': 2.0, 'direction': 0.0}
                wind_speed_val = wind_val.get('speed', 2.0) if isinstance(wind_val, dict) else wind_val
                wind_direction_val = wind_val.get('direction', 0.0) if isinstance(wind_val, dict) else 0.0

                # 天气状况
                weather_val = weather_conditions[idx].get('value', '多云') if idx < len(weather_conditions) and isinstance(weather_conditions[idx], dict) else '多云'

                # 湿度
                humidity_val = humidity_data[idx].get('value', 60.0) if idx < len(humidity_data) and isinstance(humidity_data[idx], dict) else 60.0

                # 气压
                pressure_val = pressure_data[idx].get('value', 1013.0) if idx < len(pressure_data) and isinstance(pressure_data[idx], dict) else 1013.0

                # 能见度
                visibility_val = visibility_data[idx].get('value', 10.0) if idx < len(visibility_data) and isinstance(visibility_data[idx], dict) else 10.0

                # 降水量
                precip_val = precipitation_data[idx].get('value', 0.0) if idx < len(precipitation_data) and isinstance(precipitation_data[idx], dict) else 0.0

                # 空气质量
                aqi_info = {}
                if idx < len(aqi_data):
                    aqi_info = {'aqi': aqi_data[idx]}
                if idx < len(pm25_data):
                    aqi_info['pm25'] = pm25_data[idx]

                hour_data = {
                    'time': hour_dt,
                    'temperature': float(temp_val),
                    'weather': str(weather_val),
                    'wind_speed': float(wind_speed_val),
                    'wind_direction': float(wind_direction_val),
                    'humidity': float(humidity_val),
                    'pressure': float(pressure_val),
                    'visibility': float(visibility_val),
                    'precipitation': float(precip_val),
                    'ultraviolet': 1.0,  # 彩云API可能不直接提供，使用默认值
                    'air_quality': aqi_info,
                    'hour_of_day': hour_dt.hour,
                    'data_source': WeatherDataSource.HOURLY_API.value,
                    'fishing_score': 0  # 将在后面计算
                }
                
                # 计算钓鱼适宜性评分
                hour_data['fishing_score'] = self._calculate_fishing_score(hour_data)
                
                hourly_result.append(hour_data)
                
            except Exception as e:
                self._logger.warning(f"构建小时数据失败，索引{idx}: {e}")
                # 添加默认数据以保证24小时完整性
                hour_dt = target_datetime.replace(hour=i, minute=0, second=0)
                hour_data = {
                    'time': hour_dt,
                    'temperature': 20.0,
                    'weather': '多云',
                    'wind_speed': 2.0,
                    'wind_direction': 0.0,
                    'humidity': 60.0,
                    'pressure': 1013.0,
                    'visibility': 10.0,
                    'precipitation': 0.0,
                    'ultraviolet': 1.0,
                    'air_quality': {},
                    'hour_of_day': i,
                    'data_source': WeatherDataSource.HOURLY_API.value,
                    'fishing_score': 50.0,
                    'error': f'数据构建失败: {e}'
                }
                hourly_result.append(hour_data)
        
        return hourly_result
    
    def _calculate_fishing_score(self, hour_data: Dict[str, Any]) -> float:
        """
        计算钓鱼适宜性评分 (0-100)
        
        Args:
            hour_data: 小时天气数据
        
        Returns:
            float: 钓鱼适宜性评分
        """
        score = 0
        
        try:
            temperature = hour_data.get('temperature', 20)
            weather = hour_data.get('weather', '多云')
            wind_speed = hour_data.get('wind_speed', 2)
            humidity = hour_data.get('humidity', 60)
            
            # 温度评分 (15-25°C最优)
            if 15 <= temperature <= 25:
                score += 30
            elif 10 <= temperature < 15 or 25 < temperature <= 30:
                score += 20
            elif 5 <= temperature < 10 or 30 < temperature <= 35:
                score += 10
            else:
                score += 5
            
            # 天气评分
            good_weather = ['晴', '多云', '阴']
            fair_weather = ['小雨', '雾']
            bad_weather = ['大雨', '暴雨', '雷阵雨', '大雪', '冰雹']
            
            if weather in good_weather:
                score += 30
            elif weather in fair_weather:
                score += 15
            elif weather in bad_weather:
                score += 5
            else:
                score += 10  # 未知天气情况
            
            # 风速评分 (1-3m/s最优)
            if 1 <= wind_speed <= 3:
                score += 25
            elif 0.5 <= wind_speed < 1 or 3 < wind_speed <= 5:
                score += 15
            elif 0.1 <= wind_speed < 0.5 or 5 < wind_speed <= 8:
                score += 10
            else:
                score += 5
            
            # 湿度评分 (40-70%最优)
            if 40 <= humidity <= 70:
                score += 15
            elif 30 <= humidity < 40 or 70 < humidity <= 80:
                score += 10
            elif 20 <= humidity < 30 or 80 < humidity <= 90:
                score += 5
            else:
                score += 2
            
            return min(100, score)
            
        except Exception as e:
            self._logger.error(f"计算钓鱼评分失败: {e}")
            return 50.0  # 默认评分
    
    def _generate_cache_key(self, location_info: dict, date_str: str) -> str:
        """生成唯一的缓存键"""
        location_name = location_info.get('name', 'unknown')
        # 标准化地点名称，移除特殊字符
        normalized_name = re.sub(r'[^\w\u4e00-\u9fff]', '', location_name)
        return f"hourly_{normalized_name}_{date_str}"
    
    async def _handle_date_out_of_range(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """
        专门处理日期超出范围的情况

        Args:
            location_info: 地理位置信息
            date_str: 查询日期
            error_msg: 错误信息

        Returns:
            WeatherResult: 包含错误信息的结果
        """
        from datetime import datetime
        from .enums import WeatherDataSource

        # 计算日期差值用于更详细的提示
        try:
            days_from_now = calculate_days_from_now(date_str)

            if days_from_now < 0:
                # 过去日期：提供历史天气的概念性数据
                suggestion = f"历史日期({abs(days_from_now)}天前)，无法提供准确的逐小时天气预报"
                data_source = WeatherDataSource.HISTORICAL.value
                confidence = 0.2  # 历史数据置信度很低
            else:
                # 未来日期超出范围
                suggestion = f"超出预报范围({days_from_now - self.max_forecast_days}天)，建议查询未来{self.max_forecast_days}天内天气"
                data_source = WeatherDataSource.SIMULATION.value
                confidence = 0.1  # 超出范围数据置信度极低

            # 生成基础的24小时数据（用于钓鱼推荐等下游服务）
            hourly_data = []
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                target_date = datetime.now()
                date_str = target_date.strftime("%Y-%m-%d")

            base_temp = 18.0 + (days_from_now * 0.1)  # 简单的温度变化模拟

            for hour in range(24):
                hour_dt = target_date.replace(hour=hour, minute=0, second=0)

                # 简单的24小时温度变化
                temp_variation = 8 * (1 - abs(hour - 14) / 10)
                temperature = base_temp + temp_variation

                hour_data = {
                    'time': hour_dt,
                    'temperature': round(temperature, 1),
                    'weather': '多云',
                    'wind_speed': 3.0,
                    'wind_direction': 180.0,
                    'humidity': 65.0,
                    'pressure': 1013.0,
                    'visibility': 10.0,
                    'precipitation': 0.0,
                    'ultraviolet': 3.0,
                    'air_quality': {},
                    'hour_of_day': hour,
                    'data_source': data_source,
                    'fishing_score': 60.0,  # 默认评分
                    'error': f'日期范围错误: {suggestion}'
                }
                hourly_data.append(hour_data)

            return WeatherResult(
                data_source=data_source,
                hourly_data=hourly_data,
                confidence=confidence,
                api_url="date_out_of_range",
                error_code=2,
                error_message=suggestion,
                cached=False,
                metadata={
                    'reason': 'date_out_of_range',
                    'days_from_now': days_from_now,
                    'max_forecast_days': self.max_forecast_days,
                    'suggestion': suggestion,
                    'historical_data': days_from_now < 0
                }
            )

        except Exception as e:
            # 如果连错误处理都失败了，返回最基础的错误结果
            return WeatherResult(
                data_source=WeatherDataSource.EMERGENCY.value,
                hourly_data=[],
                confidence=0.0,
                api_url="error_handling_failed",
                error_code=3,
                error_message=f"日期处理失败: {error_msg}，错误处理异常: {e}",
                cached=False,
                metadata={'error': True, 'date_processing_failed': True}
            )

    async def _fallback_to_simulation(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """错误回退到模拟数据"""
        self._logger.warning(f"逐小时服务回退到模拟数据: {error_msg}")

      
        try:
            # 尝试从模拟服务获取数据
            from .simulation_service import SimulationService
            simulation_service = SimulationService()
            return await simulation_service.get_forecast(location_info, date_str)
        except Exception as e:
            self._logger.error(f"模拟服务也无法获取数据: {e}")

            # 最后的紧急回退
            return self._emergency_fallback(location_info, date_str, error_msg)

        
    def _emergency_fallback(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """紧急回退数据"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            target_date = datetime.now() + timedelta(days=1)
        
        # 生成基础的24小时数据
        hourly_data = []
        base_temp = 18.0  # 基础温度
        
        for hour in range(24):
            hour_dt = target_date.replace(hour=hour, minute=0, second=0)
            
            # 简单的温度模拟
            temp_variation = 8 * (1 - abs(hour - 14) / 10)  # 下午2点最热
            temperature = base_temp + temp_variation
            
            hour_data = {
                'time': hour_dt,
                'temperature': round(temperature, 1),
                'weather': '多云',
                'wind_speed': 3.0,
                'wind_direction': 180.0,
                'humidity': 65.0,
                'pressure': 1013.0,
                'visibility': 10.0,
                'precipitation': 0.0,
                'ultraviolet': 3.0,
                'air_quality': {},
                'hour_of_day': hour,
                'data_source': WeatherDataSource.EMERGENCY.value,
                'fishing_score': 60.0,
                'error': f'紧急回退数据: {error_msg}'
            }
            hourly_data.append(hour_data)
        
        return WeatherResult(
            data_source=WeatherDataSource.EMERGENCY.value,
            hourly_data=hourly_data,
            confidence=0.3,  # 紧急数据置信度很低
            api_url="emergency_fallback",
            error_code=1,
            error_message=f"逐小时服务紧急回退: {error_msg}",
            cached=False,
            metadata={
                'fallback_reason': 'hourly_service_failed',
                'original_error': error_msg,
                'emergency_fallback': True
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        total = max(self._stats['total_requests'], 1)

        return {
            **self._stats,
            'cache_hit_rate': round(self._stats['cache_hits'] / total * 100, 1),
            'api_call_rate': round(self._stats['api_calls'] / total * 100, 1),
            'error_rate': round(self._stats['errors'] / total * 100, 1),
            'date_out_of_range_rate': round(self._stats['date_out_of_range'] / total * 100, 1),
            'timestamp': datetime.now().isoformat()
        }

    def __del__(self):
        """析构函数，确保API客户端被正确关闭"""
        try:
            if hasattr(self, '_api_client') and self._api_client:
                self._api_client.close()
        except Exception:
            pass
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        # 检查API客户端状态（异步对象的安全检查）
        api_client_status = 'unavailable'
        if self._api_client:
            try:
                # 检查客户端是否有基本属性和方法
                if hasattr(self._api_client, '_session') and hasattr(self._api_client, 'get_hourly_forecast'):
                    # 进一步检查会话状态（避免直接访问异步属性）
                    session = getattr(self._api_client, '_session', None)
                    if session and hasattr(session, 'closed'):
                        api_client_status = 'healthy' if not session.closed else 'session_closed'
                    else:
                        api_client_status = 'initialized'
                else:
                    api_client_status = 'malformed'
            except Exception:
                api_client_status = 'error'

        return {
            'service': 'HourlyWeatherService',
            'status': 'healthy',
            'max_forecast_days': self.max_forecast_days,
            'cache_ttl': 1800,
            'stats': self.get_stats(),
            'api_client_status': api_client_status,
            'timestamp': datetime.now().isoformat()
        }