"""
天气模拟数据服务 (7天+)
专门处理7天以上的天气预报查询，基于历史统计数据生成模拟数据
"""
import asyncio
import logging
import math
import random
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .weather_cache import WeatherCache
from .utils.datetime_utils import calculate_days_from_now, get_season_name
from .enums import WeatherDataSource, WeatherErrorCode
from .weather_api_router import WeatherResult


class HistoricalWeatherDatabase:
    """历史天气统计数据模拟器"""
    
    def __init__(self):
        # 模拟的历史天气统计数据
        # 按季节和地区分类的基准数据
        self.seasonal_baselines = {
            '春季': {  # 3-5月
                'avg_temperature': 18.0,
                'temp_range': 12.0,
                'avg_wind_speed': 3.5,
                'avg_humidity': 65,
                'common_weather': ['晴', '多云', '阴', '小雨'],
                'weather_weights': [0.3, 0.35, 0.2, 0.15]
            },
            '夏季': {  # 6-8月
                'avg_temperature': 28.0,
                'temp_range': 10.0,
                'avg_wind_speed': 2.8,
                'avg_humidity': 75,
                'common_weather': ['晴', '多云', '阴', '雷阵雨', '小雨'],
                'weather_weights': [0.25, 0.3, 0.15, 0.2, 0.1]
            },
            '秋季': {  # 9-11月
                'avg_temperature': 15.0,
                'temp_range': 15.0,
                'avg_wind_speed': 4.2,
                'avg_humidity': 60,
                'common_weather': ['晴', '多云', '阴', '小雨'],
                'weather_weights': [0.35, 0.3, 0.2, 0.15]
            },
            '冬季': {  # 12-2月
                'avg_temperature': 2.0,
                'temp_range': 18.0,
                'avg_wind_speed': 5.5,
                'avg_humidity': 55,
                'common_weather': ['晴', '多云', '阴', '小雨', '雪'],
                'weather_weights': [0.4, 0.25, 0.15, 0.1, 0.1]
            }
        }
        
        # 地区调整因子
        self.location_adjustments = {
            '北方': {
                'temp_offset': -8.0,
                'wind_multiplier': 1.3,
                'humidity_offset': -10
            },
            '南方': {
                'temp_offset': 5.0,
                'wind_multiplier': 0.8,
                'humidity_offset': 10
            },
            '沿海': {
                'temp_offset': 2.0,
                'wind_multiplier': 1.2,
                'humidity_offset': 15
            },
            '内陆': {
                'temp_offset': 0.0,
                'wind_multiplier': 1.0,
                'humidity_offset': 0
            }
        }
        
        # 地点类型映射 (简单规则)
        self._location_type_mapping = {
            '北京': '北方内陆', '天津': '北方沿海', '河北': '北方内陆',
            '山西': '北方内陆', '内蒙古': '北方内陆', '辽宁': '北方沿海',
            '吉林': '北方内陆', '黑龙江': '北方内陆', '上海': '南方沿海',
            '江苏': '南方沿海', '浙江': '南方沿海', '安徽': '南方内陆',
            '福建': '南方沿海', '江西': '南方内陆', '山东': '北方沿海',
            '河南': '北方内陆', '湖北': '南方内陆', '湖南': '南方内陆',
            '广东': '南方沿海', '广西': '南方内陆', '海南': '南方沿海',
            '重庆': '南方内陆', '四川': '南方内陆', '贵州': '南方内陆',
            '云南': '南方内陆', '西藏': '高原', '陕西': '北方内陆',
            '甘肃': '北方内陆', '青海': '高原', '宁夏': '北方内陆',
            '新疆': '北方内陆'
        }
    
    def get_monthly_stats(self, location_name: str, month: int) -> Dict[str, Any]:
        """
        获取指定地点和月份的天气统计信息
        
        Args:
            location_name: 地点名称
            month: 月份 (1-12)
        
        Returns:
            Dict[str, Any]: 天气统计信息
        """
        # 确定季节
        if month in [3, 4, 5]:
            season = '春季'
        elif month in [6, 7, 8]:
            season = '夏季'
        elif month in [9, 10, 11]:
            season = '秋季'
        else:
            season = '冬季'
        
        # 获取季节基准数据
        baseline = self.seasonal_baselines[season].copy()
        
        # 应用地区调整
        location_type = self._determine_location_type(location_name)
        adjustment = self._get_location_adjustment(location_type)
        
        # 调整基准数据
        adjusted_stats = {
            'avg_temperature': baseline['avg_temperature'] + adjustment['temp_offset'],
            'temp_range': baseline['temp_range'] * 1.1,  # 温差稍微增大
            'avg_wind_speed': baseline['avg_wind_speed'] * adjustment['wind_multiplier'],
            'avg_humidity': baseline['avg_humidity'] + adjustment['humidity_offset'],
            'common_weather': baseline['common_weather'],
            'weather_weights': baseline['weather_weights'],
            'season': season,
            'location_type': location_type,
            'month': month
        }
        
        # 添加一些随机变化
        random_factor = 0.8 + random.random() * 0.4  # 0.8-1.2的随机因子
        adjusted_stats['avg_temperature'] += random.gauss(0, 3)
        adjusted_stats['avg_wind_speed'] *= random_factor
        adjusted_stats['avg_humidity'] += random.gauss(0, 8)
        
        # 限制在合理范围内
        adjusted_stats['avg_humidity'] = max(20, min(95, adjusted_stats['avg_humidity']))
        adjusted_stats['avg_wind_speed'] = max(0.5, adjusted_stats['avg_wind_speed'])
        
        return adjusted_stats
    
    def _determine_location_type(self, location_name: str) -> str:
        """确定地点类型"""
        # 检查是否包含关键词
        if any(keyword in location_name for keyword in ['沿海', '海边', '港', '湾']):
            return '沿海'
        elif any(keyword in location_name for keyword in ['北', '东北', '西北']):
            return '北方'
        elif any(keyword in location_name for keyword in ['南', '东南', '西南']):
            return '南方'
        else:
            # 基于省份映射
            for province, loc_type in self._location_type_mapping.items():
                if province in location_name:
                    if '沿海' in loc_type:
                        return '沿海'
                    elif '北方' in loc_type:
                        return '北方'
                    else:
                        return '南方'
        
        # 默认为内陆
        return '内陆'
    
    def _get_location_adjustment(self, location_type: str) -> Dict[str, Any]:
        """获取地区调整因子"""
        if '北方' in location_type:
            return self.location_adjustments['北方']
        elif '南方' in location_type:
            return self.location_adjustments['南方']
        elif '沿海' in location_type:
            return self.location_adjustments['沿海']
        else:
            return self.location_adjustments['内陆']


class SimulationService:
    """天气模拟数据服务 (7天+)"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._cache = WeatherCache(default_ttl=86400, file_path="data/cache/weather_simulation_cache.json")  # 24小时TTL
        self._historical_db = HistoricalWeatherDatabase()
        
        # 配置参数
        self.min_days_for_simulation = 7
        
        # 统计信息
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'simulations': 0,
            'errors': 0,
            'historical_db_queries': 0
        }
    
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """
        获取指定日期的模拟天气数据
        
        Args:
            location_info: 地理位置信息
                - name: 地点名称
                - lng: 经度
                - lat: 纬度
                - adcode: 行政区划代码 (可选)
            date_str: 查询日期，格式为"YYYY-MM-DD"
                通常为7天以上的日期
        
        Returns:
            WeatherResult: 统一格式的天气查询结果
        """
        self._stats['total_requests'] += 1
        start_time = datetime.now()
        
        try:
            # 1. 验证日期范围 (模拟服务应该可以处理任何日期)
            days_from_now = calculate_days_from_now(date_str)
            
            # 2. 生成缓存键
            cache_key = self._generate_cache_key(location_info, date_str)
            
            # 3. 检查缓存
            cached_result = self._cache.get(cache_key)
            if cached_result:
                self._stats['cache_hits'] += 1
                self._logger.debug(f"模拟数据缓存命中: {cache_key}")
                cached_result.cached = True
                return cached_result
            
            # 4. 生成模拟数据
            self._stats['simulations'] += 1
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            month = target_date.month
            
            # 5. 查询历史统计数据
            self._stats['historical_db_queries'] += 1
            historical_data = self._historical_db.get_monthly_stats(
                location_info['name'], month
            )
            
            # 6. 生成24小时模拟数据
            hourly_data = self._generate_simulation_hourly(
                target_date, historical_data, days_from_now
            )
            
            result = WeatherResult(
                data_source=WeatherDataSource.SIMULATION.value,
                hourly_data=hourly_data,
                confidence=0.6,  # 模拟数据置信度较低
                api_url="simulation",
                error_code=0,
                error_message="",
                cached=False,
                metadata={
                    'simulation_method': 'historical_statistical',
                    'historical_data': historical_data,
                    'days_from_now': days_from_now,
                    'season': historical_data['season'],
                    'location_type': historical_data['location_type'],
                    'simulation_quality': 'medium'
                }
            )
            
            # 7. 缓存结果
            self._cache.set(cache_key, result)
            
            # 8. 记录性能日志
            duration = (datetime.now() - start_time).total_seconds()
            self._logger.info(f"模拟数据生成完成: {location_info['name']} {date_str} 耗时{duration:.2f}s")
            
            return result
            
        except Exception as e:
            self._stats['errors'] += 1
            self._logger.error(f"模拟数据生成失败: {location_info['name']} {date_str} 错误: {e}")
            
            # 紧急回退
            return self._emergency_fallback(location_info, date_str, str(e))
    
    def _generate_simulation_hourly(self, target_date: datetime, historical_data: Dict[str, Any], days_from_now: int) -> List[Dict[str, Any]]:
        """
        基于历史统计数据生成24小时模拟数据
        
        Args:
            target_date: 目标日期
            historical_data: 历史统计数据
            days_from_now: 距今天数
        
        Returns:
            List[Dict[str, Any]]: 24小时模拟数据
        """
        try:
            hourly_data = []
            
            # 基础参数
            base_temp = historical_data['avg_temperature']
            temp_range = historical_data['temp_range']
            base_wind = historical_data['avg_wind_speed']
            base_humidity = historical_data['avg_humidity']
            
            # 根据预测远度调整置信度 (越远的日期变化越大)
            distance_factor = min(1.0 + (days_from_now - 7) * 0.1, 2.0)
            
            # 添加随机变化
            random_factor = 0.1 + random.random() * 0.2  # 10%-30%随机变化
            
            for hour in range(24):
                hour_datetime = target_date.replace(hour=hour, minute=0, second=0)
                
                # 温度模拟：正弦曲线 + 随机扰动
                temp_variation = math.sin((hour - 6) * math.pi / 12)  # 6点最低，14点最高
                temperature = base_temp + temp_range * temp_variation * random_factor
                
                # 添加更多随机性
                noise = random.gauss(0, 2 * distance_factor)
                temperature += noise
                
                # 天气状况模拟：基于历史概率分布
                weather = self._simulate_weather_condition(historical_data, hour, days_from_now)
                
                # 风速模拟：日内变化 + 随机扰动
                wind_factor = 0.5 + 0.5 * math.sin(hour * math.pi / 12)
                wind_speed = base_wind * wind_factor * (0.8 + random.random() * 0.4) * distance_factor
                
                # 湿度模拟：与温度负相关
                humidity_variation = - (temperature - base_temp) * 2
                humidity = base_humidity + humidity_variation + random.random() * 10
                
                # 其他参数
                pressure = 1013 + random.gauss(0, 5)  # 气压小幅变化
                visibility = self._simulate_visibility(weather, base_humidity)
                precipitation = self._simulate_precipitation(weather, days_from_now)
                
                # 空气质量 (基于天气和季节)
                aqi = self._simulate_aqi(weather, historical_data['season'], days_from_now)
                
                hour_data = {
                    'time': hour_datetime,
                    'temperature': round(temperature, 1),
                    'weather': weather,
                    'wind_speed': round(max(0, wind_speed), 1),
                    'wind_direction': random.uniform(0, 360),
                    'humidity': round(max(20, min(95, humidity)), 1),
                    'pressure': round(pressure, 1),
                    'visibility': round(visibility, 1),
                    'precipitation': round(precipitation, 1),
                    'ultraviolet': self._simulate_uv_index(hour, historical_data['season']),
                    'air_quality': {'aqi': aqi},
                    'hour_of_day': hour,
                    'data_source': WeatherDataSource.SIMULATION.value,
                    'simulated': True,
                    'days_from_now': days_from_now,
                    'fishing_score': 0  # 将在后面计算
                }
                
                # 计算钓鱼适宜性评分
                hour_data['fishing_score'] = self._calculate_fishing_score(hour_data, distance_factor)
                
                hourly_data.append(hour_data)
            
            return hourly_data
            
        except Exception as e:
            self._logger.error(f"生成模拟小时数据失败: {e}")
            raise Exception(f"模拟数据生成失败: {e}")
    
    def _simulate_weather_condition(self, historical_data: Dict[str, Any], hour: int, days_from_now: int) -> str:
        """
        模拟天气状况
        
        Args:
            historical_data: 历史统计数据
            hour: 小时数
            days_from_now: 距今天数
        
        Returns:
            str: 天气状况
        """
        common_weather = historical_data['common_weather']
        weights = historical_data['weather_weights']
        
        # 根据时间调整权重
        adjusted_weights = weights.copy()
        
        # 夜间更容易出现多云和阴天
        if hour >= 20 or hour <= 6:
            weather_idx = common_weather.index('多云') if '多云' in common_weather else 1
            if weather_idx < len(adjusted_weights):
                adjusted_weights[weather_idx] *= 1.2
        
        # 根据预测远度调整 (越远天气变化越大)
        distance_factor = 1 + (days_from_now - 7) * 0.05
        
        # 归一化权重
        total_weight = sum(adjusted_weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in adjusted_weights]
        else:
            normalized_weights = [1.0 / len(common_weather)] * len(common_weather)
        
        # 随机选择天气
        weather = random.choices(common_weather, weights=normalized_weights)[0]
        
        return weather
    
    def _simulate_visibility(self, weather: str, humidity: float) -> float:
        """模拟能见度"""
        base_visibility = {
            '晴': 15.0,
            '多云': 12.0,
            '阴': 8.0,
            '小雨': 6.0,
            '中雨': 4.0,
            '大雨': 2.0,
            '暴雨': 1.0,
            '雪': 5.0,
            '雾': 1.0
        }
        
        visibility = base_visibility.get(weather, 10.0)
        
        # 湿度影响能见度
        if humidity > 80:
            visibility *= 0.8
        
        # 添加随机变化
        visibility *= random.uniform(0.8, 1.2)
        
        return max(0.5, min(20.0, visibility))
    
    def _simulate_precipitation(self, weather: str, days_from_now: int) -> float:
        """模拟降水量"""
        precipitation_ranges = {
            '晴': (0, 0),
            '多云': (0, 0),
            '阴': (0, 0.1),
            '小雨': (0.1, 2.0),
            '中雨': (2.0, 8.0),
            '大雨': (8.0, 20.0),
            '暴雨': (20.0, 50.0),
            '雪': (0.1, 5.0),
            '雾': (0, 0.1)
        }
        
        min_prec, max_prec = precipitation_ranges.get(weather, (0, 0))
        
        if max_prec == 0:
            return 0.0
        
        # 根据预测远度调整不确定性
        uncertainty_factor = 1 + (days_from_now - 7) * 0.02
        
        precipitation = random.uniform(min_prec, max_prec) * uncertainty_factor
        
        return round(precipitation, 1)
    
    def _simulate_uv_index(self, hour: int, season: str) -> float:
        """模拟紫外线指数"""
        # 基础UV强度
        season_base = {
            '春季': 6.0,
            '夏季': 9.0,
            '秋季': 4.0,
            '冬季': 2.0
        }
        
        base_uv = season_base.get(season, 4.0)
        
        # 只有白天有紫外线
        if 6 <= hour <= 18:
            # 使用正弦函数模拟紫外线变化
            hour_angle = (hour - 6) * math.pi / 12
            uv_factor = math.sin(hour_angle)
            uv = base_uv * uv_factor
            
            # 添加随机变化
            uv *= random.uniform(0.7, 1.3)
            
            return round(max(0, uv), 1)
        else:
            return 0.0
    
    def _simulate_aqi(self, weather: str, season: str, days_from_now: int) -> int:
        """模拟空气质量指数"""
        # 基础AQI
        season_base = {
            '春季': 80,   # 春季可能有花粉和沙尘
            '夏季': 60,   # 夏季雨水较多，空气质量较好
            '秋季': 90,   # 秋季干燥，可能有雾霾
            '冬季': 120   # 冬季取暖，空气质量较差
        }
        
        base_aqi = season_base.get(season, 80)
        
        # 天气影响
        weather_adjustment = {
            '晴': 0,
            '多云': -5,
            '阴': -10,
            '小雨': -20,
            '中雨': -30,
            '大雨': -40,
            '雾': 30,
            '雪': -10
        }
        
        aqi = base_aqi + weather_adjustment.get(weather, 0)
        
        # 添加随机变化
        aqi += int(random.gauss(0, 15))
        
        # 预测越远不确定性越大
        aqi *= (1 + (days_from_now - 7) * 0.02)
        
        return max(20, min(300, int(aqi)))
    
    def _calculate_fishing_score(self, hour_data: Dict[str, Any], distance_factor: float) -> float:
        """
        计算钓鱼适宜性评分 (考虑模拟数据的不确定性)
        
        Args:
            hour_data: 小时天气数据
            distance_factor: 距离因子
        
        Returns:
            float: 钓鱼适宜性评分
        """
        score = 0
        
        try:
            temperature = hour_data.get('temperature', 20)
            weather = hour_data.get('weather', '多云')
            wind_speed = hour_data.get('wind_speed', 2)
            humidity = hour_data.get('humidity', 60)
            
            # 模拟数据的评分需要考虑不确定性
            uncertainty_penalty = 0.7  # 30%的惩罚
            
            # 温度评分 (15-25°C最优)
            if 15 <= temperature <= 25:
                score += 21  # 30 * 0.7
            elif 10 <= temperature < 15 or 25 < temperature <= 30:
                score += 14  # 20 * 0.7
            elif 5 <= temperature < 10 or 30 < temperature <= 35:
                score += 7   # 10 * 0.7
            else:
                score += 3   # 5 * 0.7
            
            # 天气评分
            good_weather = ['晴', '多云', '阴']
            fair_weather = ['小雨', '雾']
            bad_weather = ['大雨', '暴雨', '雷阵雨', '大雪', '冰雹']
            
            if weather in good_weather:
                score += 21  # 30 * 0.7
            elif weather in fair_weather:
                score += 10  # 15 * 0.7
            elif weather in bad_weather:
                score += 3   # 5 * 0.7
            else:
                score += 7   # 10 * 0.7
            
            # 风速评分 (1-3m/s最优)
            if 1 <= wind_speed <= 3:
                score += 17  # 25 * 0.7
            elif 0.5 <= wind_speed < 1 or 3 < wind_speed <= 5:
                score += 10  # 15 * 0.7
            elif 0.1 <= wind_speed < 0.5 or 5 < wind_speed <= 8:
                score += 7   # 10 * 0.7
            else:
                score += 3   # 5 * 0.7
            
            # 湿度评分 (40-70%最优)
            if 40 <= humidity <= 70:
                score += 10  # 15 * 0.7
            elif 30 <= humidity < 40 or 70 < humidity <= 80:
                score += 7   # 10 * 0.7
            elif 20 <= humidity < 30 or 80 < humidity <= 90:
                score += 3   # 5 * 0.7
            else:
                score += 1   # 2 * 0.7
            
            # 距离越远，评分越保守
            distance_penalty = max(0.5, 1 - (distance_factor - 1) * 0.1)
            score *= distance_penalty
            
            return min(100, score)
            
        except Exception as e:
            self._logger.error(f"计算钓鱼评分失败: {e}")
            return 42.0  # 默认评分 (60 * 0.7)
    
    def _generate_cache_key(self, location_info: dict, date_str: str) -> str:
        """生成唯一的缓存键"""
        location_name = location_info.get('name', 'unknown')
        # 标准化处理：移除特殊字符，统一格式
        normalized_name = re.sub(r'[^\w\u4e00-\u9fff]', '', location_name)
        return f"simulation_{normalized_name}_{date_str}"
    
    def _emergency_fallback(self, location_info: dict, date_str: str, error_msg: str) -> WeatherResult:
        """紧急回退数据"""
        self._logger.error(f"模拟服务紧急回退: {error_msg}")
        
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            target_date = datetime.now() + timedelta(days=10)
        
        # 生成最基础的24小时数据
        hourly_data = []
        base_temp = 20.0
        
        for hour in range(24):
            hour_dt = target_date.replace(hour=hour, minute=0, second=0)
            
            # 最简单的温度模拟
            temp_variation = 5 * (1 - abs(hour - 14) / 10)
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
                'air_quality': {'aqi': 70},
                'hour_of_day': hour,
                'data_source': WeatherDataSource.EMERGENCY.value,
                'simulated': True,
                'emergency_fallback': True,
                'fishing_score': 42.0,
                'error': f'模拟服务紧急回退: {error_msg}'
            }
            hourly_data.append(hour_data)
        
        return WeatherResult(
            data_source=WeatherDataSource.EMERGENCY.value,
            hourly_data=hourly_data,
            confidence=0.2,  # 紧急数据置信度极低
            api_url="emergency_fallback",
            error_code=2,
            error_message=f"模拟服务紧急回退: {error_msg}",
            cached=False,
            metadata={
                'fallback_reason': 'simulation_service_failed',
                'original_error': error_msg,
                'emergency_fallback': True,
                'minimal_data': True
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        total = max(self._stats['total_requests'], 1)
        
        return {
            **self._stats,
            'cache_hit_rate': round(self._stats['cache_hits'] / total * 100, 1),
            'simulation_rate': round(self._stats['simulations'] / total * 100, 1),
            'historical_db_hit_rate': round(self._stats['historical_db_queries'] / total * 100, 1),
            'error_rate': round(self._stats['errors'] / total * 100, 1),
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'service': 'SimulationService',
            'status': 'healthy',
            'min_days_for_simulation': self.min_days_for_simulation,
            'cache_ttl': 86400,
            'historical_db_status': 'active',
            'stats': self.get_stats(),
            'timestamp': datetime.now().isoformat()
        }