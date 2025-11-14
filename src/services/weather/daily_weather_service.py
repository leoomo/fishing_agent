"""
逐天天气预报服务 (3-7天)
专门处理3-7天内的天气预报查询，通过插值算法生成小时级数据
"""
import asyncio
import logging
import math
import random
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .weather_cache import WeatherCache
from .clients.caiyun_api_client import CaiyunApiClient
from .utils.datetime_utils import calculate_days_from_now
from .enums import WeatherErrorCode, WeatherDataSource
from .weather_api_router import WeatherResult


class InterpolationException(Exception):
    """数据插值处理异常"""
    pass


class DailyWeatherService:
    """逐天天气预报服务 (3-7天)"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._cache = WeatherCache(default_ttl=7200, file_path="data/cache/weather_daily_cache.json")  # 2小时TTL
        self._api_client = CaiyunApiClient()
        
        # 配置参数
        self.min_forecast_days = 3
        self.max_forecast_days = 7
        self.request_timeout = 15.0
        self.max_retry_attempts = 3
        
        # 插值配置
        self.interpolation_config = {
            'temperature': {
                'min_hour': 6,          # 最低温出现时间
                'max_hour': 14,         # 最高温出现时间
                'morning_factor': 0.3,  # 早晨温度变化因子
                'evening_drop': 0.7     # 晚间温度下降因子
            },
            'wind_speed': {
                'base_factor': 0.8,     # 基础风速因子
                'variation_range': 0.4, # 风速变化范围
                'peak_hour': 15         # 风速峰值时间
            },
            'humidity': {
                'temp_correlation': -2.0, # 温湿度相关系数
                'min_humidity': 30,      # 最小湿度限制
                'max_humidity': 95       # 最大湿度限制
            }
        }
        
        # 统计信息
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'interpolations': 0,
            'errors': 0,
            'date_out_of_range': 0
        }
    
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """
        获取指定日期的天气预报数据，使用逐天API并进行小时级插值。
        
        Args:
            location_info: 地理位置信息
                - name: 地点名称
                - lng: 经度
                - lat: 纬度
                - adcode: 行政区划代码 (可选)
            date_str: 查询日期，格式为"YYYY-MM-DD"
                必须在当前日期的3-7天范围内
        
        Returns:
            WeatherResult: 统一格式的天气查询结果
        """
        self._stats['total_requests'] += 1
        start_time = datetime.now()
        
        try:
            # 1. 验证日期范围
            days_from_now = calculate_days_from_now(date_str)
            if days_from_now < self.min_forecast_days or days_from_now > self.max_forecast_days:
                self._stats['date_out_of_range'] += 1
                raise ValueError(f"查询日期{date_str}超出逐天预报范围({self.min_forecast_days}-{self.max_forecast_days}天)")
            
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
            self._stats['interpolations'] += 1
            result = self._process_daily_data(api_data, date_str)
            
            # 6. 缓存结果
            self._cache.set(cache_key, result)
            
            # 7. 记录性能日志
            duration = (datetime.now() - start_time).total_seconds()
            self._logger.info(f"逐天预报查询完成: {location_info['name']} {date_str} 耗时{duration:.2f}s (包含插值)")
            
            return result
            
        except Exception as e:
            self._stats['errors'] += 1
            self._logger.error(f"逐天预报查询失败: {location_info['name']} {date_str} 错误: {e}")
            
            # 错误回退
            return await self._fallback_to_simulation(location_info, date_str, str(e))
    
    async def _call_api_with_retry(self, location_info: dict) -> Dict[str, Any]:
        """带重试机制的API调用"""
        last_exception = None
        
        for attempt in range(self.max_retry_attempts):
            try:
                self._logger.debug(f"逐天API调用尝试 {attempt + 1}/{self.max_retry_attempts}")
                
                api_data = await self._api_client.get_daily_forecast(
                    lng=location_info['lng'],
                    lat=location_info['lat'],
                    dailysteps=7
                )
                
                # 验证API响应
                if not self._validate_daily_api_response(api_data):
                    raise Exception("API响应数据格式错误")
                
                return api_data
                
            except Exception as e:
                last_exception = e
                if attempt < self.max_retry_attempts - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    self._logger.warning(f"逐天API调用失败，{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        # 所有重试都失败
        raise last_exception or Exception("逐天API调用失败")
    
    def _validate_daily_api_response(self, api_data: Dict[str, Any]) -> bool:
        """验证逐天API响应数据的完整性"""
        try:
            # 检查基本结构
            if not isinstance(api_data, dict):
                return False
            
            if api_data.get('status') != 'ok':
                return False
            
            result = api_data.get('result', {})
            if not isinstance(result, dict):
                return False
            
            daily = result.get('daily', {})
            if not isinstance(daily, dict):
                return False
            
            if daily.get('status') != 'ok':
                return False
            
            # 检查必要字段
            required_fields = ['time', 'temperature_2m', 'weather', 'wind_speed', 'humidity_2m']
            for field in required_fields:
                if field not in daily or not isinstance(daily[field], list):
                    return False
            
            # 检查数据长度
            time_count = len(daily['time'])
            for field in required_fields:
                if len(daily[field]) != time_count:
                    return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"逐天API响应验证失败: {e}")
            return False
    
    def _process_daily_data(self, api_data: dict, target_date: str) -> WeatherResult:
        """
        处理API返回的逐天数据，提取目标日期信息并进行插值转换。
        
        Args:
            api_data: 彩云天气API返回的原始数据
            target_date: 目标日期字符串
        
        Returns:
            WeatherResult: 处理后的天气结果
        """
        try:
            daily_data = api_data.get('result', {}).get('daily', {})
            
            # 提取日期数组
            dates = daily_data.get('time', [])
            
            # 找到目标日期在数组中的索引
            target_index = self._find_date_index(dates, target_date)
            
            if target_index == -1:
                raise ValueError(f"目标日期 {target_date} 不在逐天预报范围内")
            
            # 提取当日数据
            day_data = self._extract_day_data(daily_data, target_index, target_date)
            
            # 转换为24小时数据 (使用日内插值算法)
            hourly_data = self._interpolate_daily_to_hourly(day_data, target_date)
            
            # 验证插值结果
            if not self._validate_interpolation_result(hourly_data):
                self._logger.warning("插值结果验证失败，使用简化算法")
                hourly_data = self._fallback_linear_interpolation(day_data, target_date)
            
            return WeatherResult(
                data_source=WeatherDataSource.DAILY_API.value,
                hourly_data=hourly_data,
                confidence=0.85,  # 逐天预报置信度稍低
                api_url="weather/daily?dailysteps=7",
                error_code=0,
                error_message="",
                cached=False,
                metadata={
                    'api_data_points': len(dates),
                    'target_index': target_index,
                    'interpolation_method': 'advanced',
                    'data_completeness': len(hourly_data) / 24.0,
                    'source_api': 'caiyun_v2.6',
                    'original_daily_data': day_data
                }
            )
            
        except Exception as e:
            self._logger.error(f"处理逐天数据失败: {e}")
            raise InterpolationException(f"逐天数据处理失败: {e}")
    
    def _find_date_index(self, dates: list, target_date: str) -> int:
        """
        在日期数组中查找目标日期的索引位置。
        
        Args:
            dates: API返回的日期数组 (Unix时间戳)
            target_date: 目标日期字符串
        
        Returns:
            int: 目标日期在数组中的索引，如果未找到返回-1
        """
        try:
            target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
            target_date_only = target_datetime.date()
            
            for i, date_timestamp in enumerate(dates):
                api_date = datetime.fromtimestamp(date_timestamp).date()
                if api_date == target_date_only:
                    return i
            
            return -1
            
        except Exception as e:
            self._logger.error(f"查找日期索引失败: {e}")
            return -1
    
    def _extract_day_data(self, daily_data: dict, target_index: int, target_date: str) -> Dict[str, Any]:
        """
        提取指定日期的逐天数据
        
        Args:
            daily_data: 逐天数据
            target_index: 目标索引
            target_date: 目标日期
        
        Returns:
            Dict[str, Any]: 日数据
        """
        try:
            # 提取温度数据
            temp_data = daily_data.get('temperature_2m', [])[target_index]
            if isinstance(temp_data, list) and len(temp_data) >= 3:
                temperature_max = float(temp_data[0])
                temperature_min = float(temp_data[1])
                temperature_avg = float(temp_data[2])
            else:
                # 回退到单一温度值
                temperature_avg = float(temp_data) if temp_data else 20.0
                temperature_max = temperature_avg + 5
                temperature_min = temperature_avg - 5
            
            # 提取天气状况
            weather = str(daily_data.get('weather', [])[target_index]) if target_index < len(daily_data.get('weather', [])) else '多云'
            
            # 提取风速数据
            wind_data = daily_data.get('wind_speed', [])[target_index]
            if isinstance(wind_data, list) and len(wind_data) >= 3:
                wind_speed_max = float(wind_data[0])
                wind_speed_avg = float(wind_data[2])
            else:
                wind_speed_avg = float(wind_data) if wind_data else 3.0
                wind_speed_max = wind_speed_avg + 2
            
            # 提取湿度数据
            humidity_data = daily_data.get('humidity_2m', [])[target_index]
            if isinstance(humidity_data, list) and len(humidity_data) >= 3:
                humidity_max = float(humidity_data[0])
                humidity_min = float(humidity_data[1])
                humidity_avg = float(humidity_data[2])
            else:
                humidity_avg = float(humidity_data) if humidity_data else 65.0
                humidity_max = min(95, humidity_avg + 10)
                humidity_min = max(30, humidity_avg - 10)
            
            # 提取其他数据
            precipitation = float(daily_data.get('precipitation', [])[target_index]) if target_index < len(daily_data.get('precipitation', [])) else 0.0
            
            # 空气质量数据
            aqi_data = daily_data.get('air_quality', {})
            air_quality_aqi = int(aqi_data.get('aqi', [])[target_index]) if target_index < len(aqi_data.get('aqi', [])) else 50
            
            ultraviolet = float(daily_data.get('ultraviolet', [])[target_index]) if target_index < len(daily_data.get('ultraviolet', [])) else 3.0
            
            # 风向数据
            wind_direction = float(daily_data.get('wind_direction', [])[target_index]) if target_index < len(daily_data.get('wind_direction', [])) else 180.0
            
            return {
                'date': datetime.strptime(target_date, "%Y-%m-%d"),
                'temperature_max': temperature_max,
                'temperature_min': temperature_min,
                'temperature_avg': temperature_avg,
                'weather': weather,
                'wind_speed_max': wind_speed_max,
                'wind_speed_avg': wind_speed_avg,
                'wind_direction': wind_direction,
                'humidity_max': humidity_max,
                'humidity_min': humidity_min,
                'humidity_avg': humidity_avg,
                'precipitation': precipitation,
                'air_quality_aqi': air_quality_aqi,
                'ultraviolet': ultraviolet
            }
            
        except Exception as e:
            self._logger.error(f"提取日数据失败: {e}")
            # 返回默认数据
            return {
                'date': datetime.strptime(target_date, "%Y-%m-%d"),
                'temperature_max': 25.0,
                'temperature_min': 15.0,
                'temperature_avg': 20.0,
                'weather': '多云',
                'wind_speed_max': 5.0,
                'wind_speed_avg': 3.0,
                'wind_direction': 180.0,
                'humidity_max': 75.0,
                'humidity_min': 55.0,
                'humidity_avg': 65.0,
                'precipitation': 0.0,
                'air_quality_aqi': 50,
                'ultraviolet': 3.0
            }
    
    def _interpolate_daily_to_hourly(self, day_data: Dict[str, Any], date_str: str) -> List[Dict[str, Any]]:
        """
        将逐天数据插值为24小时数据的核心算法
        
        Args:
            day_data: 单日的天气数据
            date_str: 日期字符串
        
        Returns:
            List[Dict[str, Any]]: 24小时插值数据对象列表
        """
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 生成温度变化曲线
            temp_profile = self._interpolate_temperature_profile(day_data)
            
            # 生成风速变化曲线
            wind_profile = self._interpolate_wind_profile(day_data)
            
            # 生成湿度变化曲线
            humidity_profile = self._interpolate_humidity_profile(day_data, temp_profile)
            
            # 构建24小时数据
            hourly_data = []
            
            for hour in range(24):
                hour_datetime = target_date.replace(hour=hour, minute=0, second=0)
                
                hour_data = {
                    'time': hour_datetime,
                    'temperature': round(temp_profile[hour], 1),
                    'weather': day_data['weather'],
                    'wind_speed': round(wind_profile[hour], 1),
                    'wind_direction': day_data['wind_direction'],
                    'humidity': round(humidity_profile[hour], 1),
                    'pressure': 1013.0,  # 逐天API不提供气压数据，使用默认值
                    'visibility': 10.0,   # 使用默认值
                    'precipitation': day_data['precipitation'] / 24 if day_data['precipitation'] > 0 else 0.0,
                    'ultraviolet': self._calculate_hourly_uv(day_data['ultraviolet'], hour),
                    'air_quality': {'aqi': day_data['air_quality_aqi']},
                    'hour_of_day': hour,
                    'data_source': WeatherDataSource.DAILY_API.value,
                    'interpolated': True,
                    'fishing_score': 0  # 将在后面计算
                }
                
                # 计算钓鱼适宜性评分
                hour_data['fishing_score'] = self._calculate_fishing_score(hour_data)
                
                hourly_data.append(hour_data)
            
            return hourly_data
            
        except Exception as e:
            self._logger.error(f"插值算法失败: {e}")
            raise InterpolationException(f"插值算法失败: {e}")
    
    def _interpolate_temperature_profile(self, day_data: Dict[str, Any]) -> Dict[int, float]:
        """
        生成24小时温度变化曲线
        
        Args:
            day_data: 日数据
        
        Returns:
            Dict[int, float]: 小时温度映射
        """
        temp_min = day_data['temperature_min']
        temp_max = day_data['temperature_max']
        temp_avg = day_data['temperature_avg']
        
        config = self.interpolation_config['temperature']
        
        hourly_temps = {}
        
        for hour in range(24):
            if hour <= config['min_hour']:
                # 0-6点：温度逐渐降至最低点
                progress = hour / config['min_hour']
                temp = temp_avg - (temp_avg - temp_min) * progress * config['morning_factor']
            elif hour <= config['max_hour']:
                # 6-14点：温度逐渐升至最高点
                progress = (hour - config['min_hour']) / (config['max_hour'] - config['min_hour'])
                temp = temp_min + (temp_max - temp_min) * (config['morning_factor'] + (1 - config['morning_factor']) * progress)
            else:
                # 14-24点：温度下降
                progress = (hour - config['max_hour']) / (24 - config['max_hour'])
                temp = temp_max - (temp_max - temp_min) * config['evening_drop'] * progress
            
            # 添加随机扰动使数据更真实
            noise = random.gauss(0, 0.5)  # ±0.5°C的随机扰动
            hourly_temps[hour] = round(temp + noise, 1)
        
        return hourly_temps
    
    def _interpolate_wind_profile(self, day_data: Dict[str, Any]) -> Dict[int, float]:
        """
        生成24小时风速变化曲线
        
        Args:
            day_data: 日数据
        
        Returns:
            Dict[int, float]: 小时风速映射
        """
        base_wind = day_data['wind_speed_avg']
        wind_max = day_data['wind_speed_max']
        
        config = self.interpolation_config['wind_speed']
        
        hourly_winds = {}
        
        for hour in range(24):
            # 风速通常在下午2-4点达到峰值，使用高斯分布模拟
            peak_factor = math.exp(-((hour - config['peak_hour']) ** 2) / 50)
            
            # 基础风速 + 日变化 + 随机扰动
            wind_speed = base_wind + (wind_max - base_wind) * peak_factor * config['variation_range']
            noise = random.gauss(0, 0.2)  # 风速随机扰动
            
            hourly_winds[hour] = max(0, round(wind_speed + noise, 1))
        
        return hourly_winds
    
    def _interpolate_humidity_profile(self, day_data: Dict[str, Any], temp_profile: Dict[int, float]) -> Dict[int, float]:
        """
        基于温度变化生成24小时湿度曲线
        
        Args:
            day_data: 日数据
            temp_profile: 温度曲线
        
        Returns:
            Dict[int, float]: 小时湿度映射
        """
        base_humidity = day_data['humidity_avg']
        config = self.interpolation_config['humidity']
        
        hourly_humidity = {}
        
        for hour in range(24):
            # 湿度与温度呈负相关
            temp = temp_profile[hour]
            temp_deviation = temp - day_data['temperature_avg']
            
            # 温度升高时湿度下降
            humidity_adjustment = temp_deviation * config['temp_correlation']
            
            # 添加日变化 (清晨湿度较高)
            daily_variation = 5 * math.cos((hour - 6) * math.pi / 12)
            
            humidity = base_humidity + humidity_adjustment + daily_variation
            
            # 添加随机扰动
            noise = random.gauss(0, 2)
            final_humidity = humidity + noise
            
            # 限制在合理范围内
            hourly_humidity[hour] = max(config['min_humidity'], min(config['max_humidity'], round(final_humidity, 1)))
        
        return hourly_humidity
    
    def _calculate_hourly_uv(self, daily_uv_max: float, hour: int) -> float:
        """
        计算小时的紫外线指数
        
        Args:
            daily_uv_max: 日最大紫外线指数
            hour: 小时数
        
        Returns:
            float: 小时紫外线指数
        """
        # 紫外线在中午12点左右最强
        if 6 <= hour <= 18:
            # 使用正弦函数模拟紫外线变化
            hour_angle = (hour - 6) * math.pi / 12
            uv_factor = math.sin(hour_angle)
            return round(daily_uv_max * uv_factor, 1)
        else:
            return 0.0
    
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
            
            # 插值数据的评分稍微调低，因为准确性不如实时数据
            interpolation_penalty = 0.9  # 10%的惩罚
            
            # 温度评分 (15-25°C最优)
            if 15 <= temperature <= 25:
                score += 27  # 30 * 0.9
            elif 10 <= temperature < 15 or 25 < temperature <= 30:
                score += 18  # 20 * 0.9
            elif 5 <= temperature < 10 or 30 < temperature <= 35:
                score += 9   # 10 * 0.9
            else:
                score += 4   # 5 * 0.9
            
            # 天气评分
            good_weather = ['晴', '多云', '阴']
            fair_weather = ['小雨', '雾']
            bad_weather = ['大雨', '暴雨', '雷阵雨', '大雪', '冰雹']
            
            if weather in good_weather:
                score += 27  # 30 * 0.9
            elif weather in fair_weather:
                score += 13  # 15 * 0.9
            elif weather in bad_weather:
                score += 4   # 5 * 0.9
            else:
                score += 9   # 10 * 0.9
            
            # 风速评分 (1-3m/s最优)
            if 1 <= wind_speed <= 3:
                score += 22  # 25 * 0.9
            elif 0.5 <= wind_speed < 1 or 3 < wind_speed <= 5:
                score += 13  # 15 * 0.9
            elif 0.1 <= wind_speed < 0.5 or 5 < wind_speed <= 8:
                score += 9   # 10 * 0.9
            else:
                score += 4   # 5 * 0.9
            
            # 湿度评分 (40-70%最优)
            if 40 <= humidity <= 70:
                score += 13  # 15 * 0.9
            elif 30 <= humidity < 40 or 70 < humidity <= 80:
                score += 9   # 10 * 0.9
            elif 20 <= humidity < 30 or 80 < humidity <= 90:
                score += 4   # 5 * 0.9
            else:
                score += 2   # 2 * 0.9
            
            return min(100, score)
            
        except Exception as e:
            self._logger.error(f"计算钓鱼评分失败: {e}")
            return 54.0  # 默认评分 (60 * 0.9)
    
    def _validate_interpolation_result(self, hourly_data: List[Dict[str, Any]]) -> bool:
        """
        验证插值结果的合理性和完整性
        
        Args:
            hourly_data: 插值生成的24小时数据
        
        Returns:
            bool: 验证是否通过
        """
        try:
            # 检查数据完整性
            if len(hourly_data) != 24:
                return False
            
            # 检查必要字段
            for hour_data in hourly_data:
                required_fields = ['time', 'temperature', 'weather', 'wind_speed', 'humidity']
                for field in required_fields:
                    if field not in hour_data:
                        return False
                
                # 检查数值合理性
                temp = hour_data.get('temperature', 0)
                humidity = hour_data.get('humidity', 0)
                wind_speed = hour_data.get('wind_speed', 0)
                
                if not (-50 <= temp <= 60):  # 温度合理范围
                    return False
                if not (0 <= humidity <= 100):  # 湿度合理范围
                    return False
                if wind_speed < 0:  # 风速不能为负
                    return False
            
            return True
            
        except Exception as e:
            self._logger.error(f"插值结果验证失败: {e}")
            return False
    
    def _fallback_linear_interpolation(self, day_data: Dict[str, Any], date_str: str) -> List[Dict[str, Any]]:
        """
        简化的线性插值算法作为备用方案
        
        Args:
            day_data: 日数据
            date_str: 日期字符串
        
        Returns:
            List[Dict[str, Any]]: 24小时数据
        """
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            temp_min = day_data['temperature_min']
            temp_max = day_data['temperature_max']
            temp_range = temp_max - temp_min
            
            hourly_data = []
            
            for hour in range(24):
                hour_datetime = target_date.replace(hour=hour, minute=0, second=0)
                
                # 简单的线性插值：温度从最低到最高再回到最低
                if hour <= 12:
                    # 上午：线性升温
                    progress = hour / 12
                    temperature = temp_min + temp_range * progress
                else:
                    # 下午：线性降温
                    progress = (hour - 12) / 12
                    temperature = temp_max - temp_range * progress
                
                hour_data = {
                    'time': hour_datetime,
                    'temperature': round(temperature, 1),
                    'weather': day_data['weather'],
                    'wind_speed': day_data['wind_speed_avg'],
                    'wind_direction': day_data['wind_direction'],
                    'humidity': day_data['humidity_avg'],
                    'pressure': 1013.0,
                    'visibility': 10.0,
                    'precipitation': day_data['precipitation'] / 24 if day_data['precipitation'] > 0 else 0.0,
                    'ultraviolet': self._calculate_hourly_uv(day_data['ultraviolet'], hour),
                    'air_quality': {'aqi': day_data['air_quality_aqi']},
                    'hour_of_day': hour,
                    'data_source': WeatherDataSource.DAILY_API.value,
                    'interpolated': True,
                    'interpolation_method': 'linear_fallback',
                    'fishing_score': 54.0
                }
                hourly_data.append(hour_data)
            
            return hourly_data
            
        except Exception as e:
            self._logger.error(f"线性插值失败: {e}")
            raise InterpolationException(f"线性插值失败: {e}")
    
    def _generate_cache_key(self, location_info: dict, date_str: str) -> str:
        """生成唯一的缓存键"""
        location_name = location_info.get('name', 'unknown')
        # 标准化处理：移除特殊字符，统一格式
        normalized_name = re.sub(r'[^\w\u4e00-\u9fff]', '', location_name)
        return f"daily_{normalized_name}_{date_str}"
    
    async def _fallback_to_simulation(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """错误回退到模拟数据"""
        self._logger.warning(f"逐天服务回退到模拟数据: {error_msg}")
        
        try:
            # 尝试从模拟服务获取数据
            from simulation_service import SimulationService
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
            target_date = datetime.now() + timedelta(days=5)
        
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
                'wind_speed': 3.5,
                'wind_direction': 180.0,
                'humidity': 65.0,
                'pressure': 1013.0,
                'visibility': 10.0,
                'precipitation': 0.0,
                'ultraviolet': 3.0,
                'air_quality': {'aqi': 60},
                'hour_of_day': hour,
                'data_source': WeatherDataSource.EMERGENCY.value,
                'interpolated': True,
                'fishing_score': 54.0,
                'error': f'逐天服务紧急回退数据: {error_msg}'
            }
            hourly_data.append(hour_data)
        
        return WeatherResult(
            data_source=WeatherDataSource.EMERGENCY.value,
            hourly_data=hourly_data,
            confidence=0.3,  # 紧急数据置信度很低
            api_url="emergency_fallback",
            error_code=1,
            error_message=f"逐天服务紧急回退: {error_msg}",
            cached=False,
            metadata={
                'fallback_reason': 'daily_service_failed',
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
            'interpolation_rate': round(self._stats['interpolations'] / total * 100, 1),
            'error_rate': round(self._stats['errors'] / total * 100, 1),
            'date_out_of_range_rate': round(self._stats['date_out_of_range'] / total * 100, 1),
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        # 检查API客户端状态（异步对象的安全检查）
        api_client_status = 'unavailable'
        if self._api_client:
            try:
                # 检查客户端是否有基本属性和方法
                if hasattr(self._api_client, '_session') and hasattr(self._api_client, 'get_daily_forecast'):
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
            'service': 'DailyWeatherService',
            'status': 'healthy',
            'forecast_range': f"{self.min_forecast_days}-{self.max_forecast_days}天",
            'cache_ttl': 7200,
            'interpolation_config': self.interpolation_config,
            'stats': self.get_stats(),
            'api_client_status': api_client_status,
            'timestamp': datetime.now().isoformat()
        }

    def __del__(self):
        """析构函数，确保API客户端被正确关闭"""
        try:
            if hasattr(self, '_api_client') and self._api_client:
                self._api_client.close()
        except Exception:
            pass