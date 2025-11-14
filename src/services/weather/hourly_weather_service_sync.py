"""
逐小时天气预报服务 (0-3天) - 同步版本
专门处理3天内的逐小时天气预报查询
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .weather_cache import WeatherCache
from .clients.caiyun_api_client_sync import CaiyunApiClient
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
    """逐小时天气预报服务 (0-3天) - 同步版本"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._cache = WeatherCache(default_ttl=1800, file_path="data/cache/weather_hourly_cache.json")  # 30分钟TTL
        self._api_client = CaiyunApiClient()
        self.max_forecast_days = 3
        self.max_retry_attempts = 3

        # 统计信息
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0,
            'date_out_of_range': 0
        }

    def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """
        获取逐小时天气预报

        Args:
            location_info: 位置信息字典，包含经纬度等
            date_str: 日期字符串 (YYYY-MM-DD 格式)

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
                self._logger.info(f"逐小时预报缓存命中: {location_info['name']} {date_str}")
                cached_result.cached = True
                return cached_result

            # 4. 调用API
            self._stats['api_calls'] += 1
            api_data = self._call_api_with_retry(location_info)

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
            return self._handle_date_out_of_range(location_info, date_str, str(e))

        except Exception as e:
            self._stats['errors'] += 1
            self._logger.error(f"逐小时预报查询失败: {location_info['name']} {date_str} - {e}")
            # 错误回退
            return self._fallback_to_simulation(location_info, date_str, str(e))

    def _call_api_with_retry(self, location_info: dict) -> Dict[str, Any]:
        """带重试机制的API调用"""
        last_exception = None

        for attempt in range(self.max_retry_attempts):
            try:
                api_data = self._api_client.get_hourly_forecast(
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
                    import time
                    time.sleep(wait_time)
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
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    raise

        # 所有重试都失败
        raise last_exception or Exception("API调用失败")

    def _validate_api_response(self, api_data: Dict[str, Any]) -> bool:
        """验证API响应数据的完整性"""
        try:
            # 基本结构检查
            if not isinstance(api_data, dict):
                return False

            if 'status' not in api_data:
                return False

            if api_data.get('status') != 'ok':
                return False

            # 检查是否有实时数据
            if 'result' not in api_data:
                return False

            result = api_data['result']

            # 检查小时预报数据
            if 'hourly' not in result:
                return False

            hourly = result['hourly']
            if 'temperature' not in hourly or 'time' not in hourly:
                return False

            temperature_data = hourly['temperature']
            time_data = hourly['time']

            # 检查数据长度一致性
            if not isinstance(temperature_data, list) or not isinstance(time_data, list):
                return False

            if len(temperature_data) != len(time_data):
                return False

            # 检查是否有有效数据点
            if len(time_data) == 0:
                return False

            return True

        except Exception as e:
            self._logger.error(f"API响应验证失败: {e}")
            return False

    def _process_hourly_data(self, api_data: Dict[str, Any], target_date: str) -> WeatherResult:
        """处理API返回的逐小时数据"""
        try:
            result = api_data['result']
            hourly = result['hourly']

            # 提取时间序列
            time_series = hourly['time']
            temp_series = hourly.get('temperature', [])
            humidity_series = hourly.get('humidity', [])
            wind_speed_series = hourly.get('wind_speed', [])
            weather_series = hourly.get('skycon', [])
            precipitation_series = hourly.get('precipitation', [])

            # 解析目标日期
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            next_day = target_dt + timedelta(days=1)

            # 过滤目标日期的数据 (00:00 - 23:00)
            hourly_data = []
            for i, time_str in enumerate(time_series):
                try:
                    # 彩云API返回的时间格式: "2023-12-25T00:00+08:00"
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    if target_dt <= dt < next_day:
                        hourly_data.append({
                            'datetime': time_str,
                            'hour': dt.hour,
                            'temperature': temp_series[i] if i < len(temp_series) else None,
                            'humidity': humidity_series[i] if i < len(humidity_series) else None,
                            'wind_speed': wind_speed_series[i] if i < len(wind_speed_series) else None,
                            'condition': weather_series[i] if i < len(weather_series) else 'unknown',
                            'precipitation': precipitation_series[i] if i < len(precipitation_series) else 0.0
                        })
                except (ValueError, IndexError) as e:
                    self._logger.warning(f"跳过无效的时间点数据: {time_str} - {e}")
                    continue

            if not hourly_data:
                raise WeatherDataCorruptionException(f"没有找到{target_date}的有效逐小时数据")

            # 获取实时数据作为补充
            realtime = result.get('realtime', {})

            # 构建结果
            weather_result = WeatherResult(
                data_source=WeatherDataSource.CAIYUN_API.value,
                hourly_data=hourly_data,
                confidence=0.9,  # API数据具有较高置信度
                api_url=self._api_client._base_url,
                error_code=0,
                error_message="",
                cached=False,
                metadata={
                    'forecast_hours': len(hourly_data),
                    'source': 'api',
                    'realtime_temp': realtime.get('temperature'),
                    'target_date': target_date,
                    'original_forecast_hours': len(time_series)
                }
            )

            return weather_result

        except Exception as e:
            self._logger.error(f"处理逐小时数据失败: {e}")
            raise WeatherDataCorruptionException(f"逐小时数据处理失败: {e}")

    def _generate_cache_key(self, location_info: dict, date_str: str) -> str:
        """生成缓存键"""
        return f"hourly_{location_info['lng']}_{location_info['lat']}_{date_str}"

    def _handle_date_out_of_range(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """处理日期超出范围的情况"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now()
            days_diff = (target_date - today).days

            if days_diff < 0:
                # 历史日期 - 返回基于历史平均值的模拟数据
                return self._create_historical_estimate(location_info, date_str, error_msg)
            else:
                # 未来超出范围的日期 - 返回默认预报数据
                return self._create_extended_forecast(location_info, date_str, error_msg)

        except Exception as e:
            self._logger.error(f"处理日期范围错误失败: {e}")
            return self._emergency_fallback(location_info, date_str, error_msg)

    def _create_historical_estimate(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """创建历史日期的估算数据"""
        try:
            # 解析日期获取季节信息
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            month = target_date.month

            # 基于月份的季节性温度估算（中国北方城市基准）
            seasonal_temps = {
                1: -2, 2: 2, 12: 0,      # 冬季
                3: 8, 4: 15, 5: 21,      # 春季
                6: 26, 7: 28, 8: 27,     # 夏季
                9: 22, 10: 15, 11: 7     # 秋季
            }

            base_temp = seasonal_temps.get(month, 15)

            # 创建24小时的历史估算数据
            hourly_data = []
            for hour in range(24):
                # 日温差变化模式
                if 6 <= hour <= 14:  # 升温时段
                    temp_variation = (hour - 6) * 1.5
                elif 14 < hour <= 20:  # 降温时段
                    temp_variation = (20 - hour) * 0.8
                else:  # 夜间低温
                    temp_variation = -5

                hourly_temp = base_temp + temp_variation

                hourly_data.append({
                    'datetime': f"{date_str}T{hour:02d}:00:00+08:00",
                    'hour': hour,
                    'temperature': round(hourly_temp, 1),
                    'humidity': 65 if hour < 12 else 55,  # 上午湿度较高
                    'wind_speed': 5.0 + (hour % 4),  # 轻微变化的风速
                    'condition': 'CLOUDY' if 8 <= hour <= 18 else 'CLEAR_NIGHT',
                    'precipitation': 0.0
                })

            return WeatherResult(
                data_source=WeatherDataSource.HISTORICAL.value,
                hourly_data=hourly_data,
                confidence=0.3,  # 历史估算置信度较低
                api_url="historical_estimate",
                error_code=3,
                error_message=f"历史数据估算（{error_msg}）",
                cached=False,
                metadata={
                    'forecast_hours': len(hourly_data),
                    'source': 'historical_estimate',
                    'estimate_method': 'seasonal_average',
                    'target_date': date_str,
                    'season': self._get_season(month),
                    'base_temperature': base_temp
                }
            )

        except Exception as e:
            self._logger.error(f"创建历史估算数据失败: {e}")
            return self._emergency_fallback(location_info, date_str, error_msg)

    def _create_extended_forecast(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """创建超出范围的未来预报数据"""
        try:
            # 对于超出范围的未来日期，使用模式化的天气数据
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            month = target_date.month

            # 基于月份的典型天气模式
            monthly_patterns = {
                1: {'temp': -2, 'condition': 'SNOW', 'humidity': 80},
                2: {'temp': 2, 'condition': 'CLOUDY', 'humidity': 70},
                3: {'temp': 8, 'condition': 'RAIN', 'humidity': 75},
                4: {'temp': 15, 'condition': 'PARTLY_CLOUDY', 'humidity': 65},
                5: {'temp': 21, 'condition': 'SUNNY', 'humidity': 60},
                6: {'temp': 26, 'condition': 'PARTLY_CLOUDY', 'humidity': 65},
                7: {'temp': 28, 'condition': 'SUNNY', 'humidity': 70},
                8: {'temp': 27, 'condition': 'CLOUDY', 'humidity': 75},
                9: {'temp': 22, 'condition': 'PARTLY_CLOUDY', 'humidity': 65},
                10: {'temp': 15, 'condition': 'SUNNY', 'humidity': 60},
                11: {'temp': 7, 'condition': 'CLOUDY', 'humidity': 70},
                12: {'temp': 0, 'condition': 'SNOW', 'humidity': 85}
            }

            pattern = monthly_patterns.get(month, {'temp': 15, 'condition': 'CLOUDY', 'humidity': 70})

            # 创建24小时的扩展预报数据
            hourly_data = []
            for hour in range(24):
                # 温度日变化
                if 6 <= hour <= 14:
                    temp_variation = (hour - 6) * 2.0
                elif 14 < hour <= 20:
                    temp_variation = (20 - hour) * 1.2
                else:
                    temp_variation = -6

                hourly_temp = pattern['temp'] + temp_variation

                hourly_data.append({
                    'datetime': f"{date_str}T{hour:02d}:00:00+08:00",
                    'hour': hour,
                    'temperature': round(hourly_temp, 1),
                    'humidity': pattern['humidity'] + (hour % 10 - 5),
                    'wind_speed': 8.0 + (hour % 6),
                    'condition': pattern['condition'],
                    'precipitation': 0.1 if 'RAIN' in pattern['condition'] else 0.0
                })

            return WeatherResult(
                data_source=WeatherDataSource.EXTENDED_FORECAST.value,
                hourly_data=hourly_data,
                confidence=0.4,  # 扩展预报置信度较低
                api_url="extended_forecast",
                error_code=2,
                error_message=f"扩展预报数据（{error_msg}）",
                cached=False,
                metadata={
                    'forecast_hours': len(hourly_data),
                    'source': 'extended_forecast',
                    'pattern_month': month,
                    'target_date': date_str,
                    'base_pattern': pattern
                }
            )

        except Exception as e:
            self._logger.error(f"创建扩展预报数据失败: {e}")
            return self._emergency_fallback(location_info, date_str, error_msg)

    def _emergency_fallback(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """紧急回退数据"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")

            # 创建最基本的24小时数据
            hourly_data = []
            for hour in range(24):
                hourly_data.append({
                    'datetime': f"{date_str}T{hour:02d}:00:00+08:00",
                    'hour': hour,
                    'temperature': 20.0,  # 固定温度
                    'humidity': 60.0,    # 固定湿度
                    'wind_speed': 5.0,   # 固定风速
                    'condition': 'UNKNOWN',
                    'precipitation': 0.0
                })

            return WeatherResult(
                data_source=WeatherDataSource.EMERGENCY.value,
                hourly_data=hourly_data,
                confidence=0.1,  # 紧急数据置信度最低
                api_url="emergency_fallback",
                error_code=5,
                error_message=f"紧急回退数据（{error_msg}）",
                cached=False,
                metadata={
                    'forecast_hours': len(hourly_data),
                    'source': 'emergency_fallback',
                    'location': location_info.get('name', 'Unknown'),
                    'target_date': date_str,
                    'fallback_reason': error_msg
                }
            )

        except Exception as e:
            self._logger.error(f"创建紧急回退数据失败: {e}")
            # 最后的最后，返回空结果
            return WeatherResult(
                data_source=WeatherDataSource.EMERGENCY.value,
                hourly_data=[],
                confidence=0.0,
                api_url="emergency_fallback",
                error_code=9,
                error_message=f"数据生成失败: {error_msg}",
                cached=False,
                metadata={
                    'error': True,
                    'critical_failure': True,
                    'original_error': error_msg
                }
            )

    def _fallback_to_simulation(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """错误回退到模拟数据"""
        self._logger.warning(f"逐小时服务回退到模拟数据: {error_msg}")

        try:
            # 尝试从模拟服务获取数据
            from .simulation_service import SimulationService
            simulation_service = SimulationService()
            return simulation_service.get_forecast(location_info, date_str)
        except Exception as e:
            self._logger.error(f"模拟服务也无法获取数据: {e}")

            # 最后的紧急回退
            return self._emergency_fallback(location_info, date_str, error_msg)

    def _get_season(self, month: int) -> str:
        """获取季节"""
        if month in [12, 1, 2]:
            return "冬季"
        elif month in [3, 4, 5]:
            return "春季"
        elif month in [6, 7, 8]:
            return "夏季"
        else:
            return "秋季"

    def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        total = max(self._stats['total_requests'], 1)
        return {
            'total_requests': self._stats['total_requests'],
            'cache_hits': self._stats['cache_hits'],
            'api_calls': self._stats['api_calls'],
            'errors': self._stats['errors'],
            'date_out_of_range': self._stats['date_out_of_range'],
            'cache_hit_rate': round(self._stats['cache_hits'] / total, 3),
            'error_rate': round(self._stats['errors'] / total, 3)
        }

    def reset_statistics(self):
        """重置统计信息"""
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0,
            'date_out_of_range': 0
        }

    def close(self):
        """关闭服务"""
        if self._api_client:
            self._api_client.close()