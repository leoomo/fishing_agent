# 天气API接口差异化技术设计

## 设计概述

本设计文档详细描述了天气预报接口按时间范围差异化的技术实现方案，包括架构设计、接口规范、数据流程和实现细节。

## 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  FishingAnalyzer│  │   WeatherTool   │  │ Other Client │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                  WeatherApiRouter                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Range Calculator│  │  Service Selector│  │Load Balancer │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│HourlyWeatherSvc │  │DailyWeatherSvc  │  │SimulationService│
│   (0-3 days)    │  │   (3-7 days)    │  │   (7+ days)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Caiyun Weather API                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  hourly endpoint│  │  daily endpoint │  │  Simulator   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件设计

#### 1. WeatherApiRouter (智能路由器)

```python
from enum import Enum
from typing import Optional
from datetime import datetime, date

class ForecastRange(Enum):
    HOURLY = "hourly"    # 0-3天：逐小时预报
    DAILY = "daily"      # 3-7天：逐天预报
    SIMULATION = "simulation"  # 7天+：模拟数据

class WeatherApiRouter:
    """天气API智能路由器"""
    
    def __init__(self):
        self._hourly_service = HourlyWeatherService()
        self._daily_service = DailyWeatherService()
        self._simulation_service = SimulationService()
        self._datetime_utils = DateTimeUtils()
        
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """智能路由获取预报数据"""
        # 1. 计算时间范围
        days_from_now = self._datetime_utils.calculate_days_from_now(date_str)
        forecast_range = self._determine_forecast_range(days_from_now)
        
        # 2. 选择对应服务
        service = self._get_service_by_range(forecast_range)
        
        # 3. 执行预报查询
        result = await service.get_forecast(location_info, date_str)
        
        # 4. 统一数据格式
        return self._normalize_result(result, forecast_range)
    
    def _determine_forecast_range(self, days_from_now: int) -> ForecastRange:
        """根据天数确定预报范围"""
        if days_from_now <= 3:
            return ForecastRange.HOURLY
        elif days_from_now <= 7:
            return ForecastRange.DAILY
        else:
            return ForecastRange.SIMULATION
```

#### 2. HourlyWeatherService (逐小时服务)

```python
class HourlyWeatherService:
    """逐小时天气预报服务 (0-3天)"""
    
    def __init__(self):
        self._cache = WeatherCache(ttl=1800)  # 30分钟TTL
        self._api_client = CaiyunApiClient()
        
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """获取逐小时预报数据"""
        # 1. 检查缓存
        cache_key = f"hourly_{location_info['name']}_{date_str}"
        cached_data = await self._cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # 2. 调用API
        try:
            api_data = await self._api_client.get_hourly_forecast(
                location_info['lng'], 
                location_info['lat'],
                hourlysteps=72
            )
            
            # 3. 处理数据
            result = self._process_hourly_data(api_data, date_str)
            
            # 4. 缓存结果
            await self._cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            # 5. 错误回退
            return await self._fallback_to_simulation(location_info, date_str)
    
    def _process_hourly_data(self, api_data: dict, target_date: str) -> WeatherResult:
        """处理逐小时API数据"""
        hourly_data = api_data.get('result', {}).get('hourly', {})
        
        # 提取目标日期的24小时数据
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        date_start = target_datetime.replace(hour=0, minute=0, second=0)
        date_end = date_start + timedelta(days=1)
        
        # 筛选时间范围内的小时数据
        filtered_hours = []
        timestamps = hourly_data.get('time', [])
        
        for i, timestamp in enumerate(timestamps):
            if date_start.timestamp() <= timestamp < date_end.timestamp():
                hour_data = {
                    'time': datetime.fromtimestamp(timestamp),
                    'temperature': hourly_data.get('temperature_2m', [])[i],
                    'weather': hourly_data.get('weather', [])[i],
                    'wind_speed': hourly_data.get('wind_speed', [])[i],
                    'humidity': hourly_data.get('humidity_2m', [])[i],
                }
                filtered_hours.append(hour_data)
        
        return WeatherResult(
            data_source="hourly_api",
            hourly_data=filtered_hours,
            confidence=0.95,
            api_url=f"weather/hourly?hourlysteps=72"
        )
```

#### 3. DailyWeatherService (逐天服务)

```python
class DailyWeatherService:
    """逐天天气预报服务 (3-7天)"""
    
    def __init__(self):
        self._cache = WeatherCache(ttl=7200)  # 2小时TTL
        self._api_client = CaiyunApiClient()
        
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """获取逐天预报数据"""
        # 1. 检查缓存
        cache_key = f"daily_{location_info['name']}_{date_str}"
        cached_data = await self._cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # 2. 调用API
        try:
            api_data = await self._api_client.get_daily_forecast(
                location_info['lng'], 
                location_info['lat'],
                dailysteps=7
            )
            
            # 3. 处理数据
            result = self._process_daily_data(api_data, date_str)
            
            # 4. 缓存结果
            await self._cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            # 5. 错误回退
            return await self._fallback_to_simulation(location_info, date_str)
    
    def _process_daily_data(self, api_data: dict, target_date: str) -> WeatherResult:
        """处理逐天API数据并转换为小时格式"""
        daily_data = api_data.get('result', {}).get('daily', {})
        
        # 找到目标日期的索引
        dates = daily_data.get('time', [])
        target_index = self._find_date_index(dates, target_date)
        
        if target_index == -1:
            raise ValueError(f"目标日期 {target_date} 不在预报范围内")
        
        # 提取当日数据
        day_data = {
            'temperature_max': daily_data.get('temperature_max', [])[target_index],
            'temperature_min': daily_data.get('temperature_min', [])[target_index],
            'weather': daily_data.get('weather', [])[target_index],
            'wind_speed': daily_data.get('wind_speed', [])[target_index],
            'humidity': daily_data.get('humidity_2m', [])[target_index],
        }
        
        # 转换为24小时数据 (使用日内插值算法)
        hourly_data = self._interpolate_daily_to_hourly(day_data, target_date)
        
        return WeatherResult(
            data_source="daily_api",
            hourly_data=hourly_data,
            confidence=0.85,  # 逐天预报置信度稍低
            api_url=f"weather/daily?dailysteps=7"
        )
    
    def _interpolate_daily_to_hourly(self, day_data: dict, date_str: str) -> list:
        """将逐天数据插值为24小时数据"""
        hourly_data = []
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # 温度插值：基于正弦曲线模拟日内变化
        temp_max = day_data['temperature_max']
        temp_min = day_data['temperature_min']
        temp_range = temp_max - temp_min
        
        for hour in range(24):
            hour_datetime = target_date.replace(hour=hour, minute=0, second=0)
            
            # 温度插值：假设最低温在6点，最高温在14点
            if hour <= 6:
                temp_factor = hour / 6
                temperature = temp_min + (temp_max - temp_min) * temp_factor * 0.3
            elif hour <= 14:
                temp_factor = (hour - 6) / 8
                temperature = temp_min + temp_range * (0.3 + 0.7 * temp_factor)
            else:
                temp_factor = (hour - 14) / 10
                temperature = temp_max - temp_range * 0.7 * temp_factor
            
            # 风速和湿度保持日内变化
            wind_variation = 0.8 + 0.4 * math.sin(hour * math.pi / 12)
            humidity_variation = 1.0 - 0.2 * math.sin(hour * math.pi / 12)
            
            hour_data = {
                'time': hour_datetime,
                'temperature': round(temperature, 1),
                'weather': day_data['weather'],  # 保持天气状况
                'wind_speed': round(day_data['wind_speed'] * wind_variation, 1),
                'humidity': round(min(100, day_data['humidity'] * humidity_variation), 1),
            }
            hourly_data.append(hour_data)
        
        return hourly_data
```

#### 4. SimulationService (模拟数据服务)

```python
class SimulationService:
    """天气模拟数据服务 (7天+)"""
    
    def __init__(self):
        self._cache = WeatherCache(ttl=86400)  # 24小时TTL
        self._historical_db = HistoricalWeatherDatabase()
        
    async def get_forecast(self, location_info: dict, date_str: str) -> WeatherResult:
        """获取模拟天气数据"""
        # 1. 检查缓存
        cache_key = f"simulation_{location_info['name']}_{date_str}"
        cached_data = await self._cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # 2. 生成模拟数据
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        month = target_date.month
        
        # 3. 基于历史数据生成
        historical_data = await self._historical_db.get_monthly_stats(
            location_info['name'], month
        )
        
        # 4. 生成24小时模拟数据
        hourly_data = self._generate_simulation_hourly(
            target_date, historical_data
        )
        
        result = WeatherResult(
            data_source="simulation",
            hourly_data=hourly_data,
            confidence=0.6,  # 模拟数据置信度较低
            api_url="simulation"
        )
        
        # 5. 缓存结果
        await self._cache.set(cache_key, result)
        
        return result
    
    def _generate_simulation_hourly(self, target_date: datetime, hist_data: dict) -> list:
        """基于历史统计数据生成24小时模拟数据"""
        hourly_data = []
        
        # 基础参数
        base_temp = hist_data.get('avg_temperature', 20.0)
        temp_range = hist_data.get('temp_range', 10.0)
        base_wind = hist_data.get('avg_wind_speed', 3.0)
        base_humidity = hist_data.get('avg_humidity', 65.0)
        
        # 添加随机变化
        random_factor = 0.1 + random.random() * 0.2  # 10%-30%随机变化
        
        for hour in range(24):
            hour_datetime = target_date.replace(hour=hour, minute=0, second=0)
            
            # 温度模拟：正弦曲线 + 随机扰动
            temp_variation = math.sin((hour - 6) * math.pi / 12)
            temperature = base_temp + temp_range * temp_variation * random_factor
            
            # 天气状况模拟：基于历史概率分布
            weather = self._simulate_weather_condition(hist_data, hour)
            
            # 风速模拟：日内变化 + 随机扰动
            wind_factor = 0.5 + 0.5 * math.sin(hour * math.pi / 12)
            wind_speed = base_wind * wind_factor * (0.8 + random.random() * 0.4)
            
            # 湿度模拟：与温度负相关
            humidity = base_humidity - (temperature - base_temp) * 2 + random.random() * 10
            humidity = max(30, min(95, humidity))
            
            hour_data = {
                'time': hour_datetime,
                'temperature': round(temperature, 1),
                'weather': weather,
                'wind_speed': round(wind_speed, 1),
                'humidity': round(humidity, 1),
            }
            hourly_data.append(hour_data)
        
        return hourly_data
```

## 数据结构设计

### WeatherResult (统一结果格式)

```python
@dataclass
class WeatherResult:
    """统一的天气查询结果"""
    data_source: str        # 数据源：hourly_api, daily_api, simulation
    hourly_data: list       # 24小时详细数据
    confidence: float       # 置信度 0.0-1.0
    api_url: str           # API端点或标识
    error_code: int = 0    # 错误码
    error_message: str = "" # 错误信息
    cached: bool = False   # 是否来自缓存
    
    def get_temperature_range(self) -> tuple:
        """获取温度范围"""
        temps = [h['temperature'] for h in self.hourly_data]
        return min(temps), max(temps)
    
    def get_weather_summary(self) -> str:
        """获取天气概况"""
        weather_counts = {}
        for hour in self.hourly_data:
            weather = hour['weather']
            weather_counts[weather] = weather_counts.get(weather, 0) + 1
        
        # 返回最主要的天气状况
        main_weather = max(weather_counts.items(), key=lambda x: x[1])[0]
        return f"{main_weather}(占比{weather_counts[main_weather]/24*100:.0f}%)"
```

### HourlyData (小时数据结构)

```python
@dataclass
class HourlyData:
    """小时天气数据"""
    time: datetime
    temperature: float      # 温度(°C)
    weather: str           # 天气状况
    wind_speed: float      # 风速(m/s)
    humidity: float        # 湿度(%)
    pressure: float = 0    # 气压(hPa)，可选
    
    def get_fishing_score(self) -> float:
        """计算钓鱼适宜性评分"""
        score = 0
        
        # 温度评分 (15-25°C最优)
        if 15 <= self.temperature <= 25:
            score += 30
        elif 10 <= self.temperature < 15 or 25 < self.temperature <= 30:
            score += 20
        else:
            score += 10
        
        # 天气评分
        good_weather = ['晴', '多云', '阴']
        if self.weather in good_weather:
            score += 30
        elif self.weather in ['小雨', '雾']:
            score += 15
        else:
            score += 5
        
        # 风速评分 (1-3m/s最优)
        if 1 <= self.wind_speed <= 3:
            score += 25
        elif 0.5 <= self.wind_speed < 1 or 3 < self.wind_speed <= 5:
            score += 15
        else:
            score += 5
        
        # 湿度评分 (40-70%最优)
        if 40 <= self.humidity <= 70:
            score += 15
        elif 30 <= self.humidity < 40 or 70 < self.humidity <= 80:
            score += 10
        else:
            score += 5
        
        return min(100, score)
```

## 缓存策略设计

### 分层缓存架构

```python
class WeatherCacheManager:
    """天气缓存管理器"""
    
    def __init__(self):
        self._hourly_cache = TTLCache(maxsize=1000, ttl=1800)   # 30分钟
        self._daily_cache = TTLCache(maxsize=500, ttl=7200)     # 2小时
        self._simulation_cache = TTLCache(maxsize=200, ttl=86400) # 24小时
        
    async def get(self, cache_key: str, cache_type: str) -> Optional[WeatherResult]:
        """获取缓存数据"""
        cache = self._get_cache_by_type(cache_type)
        return cache.get(cache_key)
    
    async def set(self, cache_key: str, data: WeatherResult, cache_type: str):
        """设置缓存数据"""
        cache = self._get_cache_by_type(cache_type)
        cache[cache_key] = data
    
    def _get_cache_by_type(self, cache_type: str):
        """根据类型获取缓存实例"""
        cache_map = {
            'hourly': self._hourly_cache,
            'daily': self._daily_cache,
            'simulation': self._simulation_cache
        }
        return cache_map.get(cache_type, self._hourly_cache)
    
    async def invalidate_location(self, location_name: str):
        """清除指定地点的所有缓存"""
        patterns = [
            f"hourly_{location_name}_*",
            f"daily_{location_name}_*", 
            f"simulation_{location_name}_*"
        ]
        
        for pattern in patterns:
            keys_to_remove = [k for k in self._hourly_cache.keys() if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_remove:
                self._hourly_cache.pop(key, None)
```

## 错误处理和回退机制

### 多层回退策略

```python
class WeatherServiceFallback:
    """天气服务回退机制"""
    
    def __init__(self):
        self._services = [
            HourlyWeatherService(),
            DailyWeatherService(), 
            SimulationService()
        ]
    
    async def get_forecast_with_fallback(self, location_info: dict, date_str: str) -> WeatherResult:
        """带回退机制的预报查询"""
        days_from_now = calculate_days_from_now(date_str)
        
        # 确定服务优先级
        if days_from_now <= 3:
            services = [self._services[0], self._services[2]]  # hourly -> simulation
        elif days_from_now <= 7:
            services = [self._services[1], self._services[2]]  # daily -> simulation  
        else:
            services = [self._services[2]]  # simulation only
        
        # 依次尝试服务
        for service in services:
            try:
                result = await service.get_forecast(location_info, date_str)
                if result and result.confidence > 0.5:
                    return result
            except Exception as e:
                logger.warning(f"Service {service.__class__.__name__} failed: {e}")
                continue
        
        # 所有服务都失败，返回基础模拟数据
        return self._get_emergency_fallback(location_info, date_str)
    
    def _get_emergency_fallback(self, location_info: dict, date_str: str) -> WeatherResult:
        """紧急回退数据"""
        return WeatherResult(
            data_source="emergency_fallback",
            hourly_data=self._generate_basic_hourly(date_str),
            confidence=0.3,
            api_url="fallback",
            error_message="所有天气服务不可用，使用基础模拟数据"
        )
```

## 性能优化策略

### 1. 连接池优化

```python
class OptimizedCaiyunApiClient:
    """优化的彩云天气API客户端"""
    
    def __init__(self):
        # 使用连接池优化网络请求
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=100,              # 总连接池大小
                limit_per_host=20,      # 每个主机连接数
                keepalive_timeout=30,   # 保持连接时间
                enable_cleanup_closed=True
            ),
            timeout=aiohttp.ClientTimeout(total=10, connect=3)
        )
    
    async def get_hourly_forecast(self, lng: float, lat: float, **params) -> dict:
        """优化的逐小时预报请求"""
        url = f"{self.base_url}/weather/hourly"
        params.update({
            'lng': lng,
            'lat': lat,
            'hourlysteps': 72,
            'alert': True
        })
        
        async with self._session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise WeatherApiError(f"API request failed: {response.status}")
```

### 2. 批量查询优化

```python
class BatchWeatherQuery:
    """批量天气查询优化"""
    
    async def query_multiple_locations(self, location_date_pairs: list) -> dict:
        """批量查询多个地点的天气"""
        # 按服务类型分组
        hourly_queries = []
        daily_queries = []
        simulation_queries = []
        
        for location_info, date_str in location_date_pairs:
            days = calculate_days_from_now(date_str)
            if days <= 3:
                hourly_queries.append((location_info, date_str))
            elif days <= 7:
                daily_queries.append((location_info, date_str))
            else:
                simulation_queries.append((location_info, date_str))
        
        # 并发执行不同类型的查询
        results = await asyncio.gather(
            self._batch_hourly_query(hourly_queries),
            self._batch_daily_query(daily_queries), 
            self._batch_simulation_query(simulation_queries),
            return_exceptions=True
        )
        
        return self._merge_batch_results(results, location_date_pairs)
```

## 监控和指标

### 性能指标收集

```python
class WeatherServiceMetrics:
    """天气服务性能指标"""
    
    def __init__(self):
        self._api_calls = Counter('weather_api_calls_total', ['service', 'status'])
        self._response_time = Histogram('weather_response_time_seconds', ['service'])
        self._cache_hits = Counter('weather_cache_hits_total', ['cache_type'])
        self._confidence_scores = Histogram('weather_confidence_scores', ['data_source'])
    
    def record_api_call(self, service: str, status: str, duration: float):
        """记录API调用"""
        self._api_calls.labels(service=service, status=status).inc()
        self._response_time.labels(service=service).observe(duration)
    
    def record_cache_hit(self, cache_type: str):
        """记录缓存命中"""
        self._cache_hits.labels(cache_type=cache_type).inc()
    
    def record_confidence(self, data_source: str, confidence: float):
        """记录置信度"""
        self._confidence_scores.labels(data_source=data_source).observe(confidence)
```

## 测试策略

### 单元测试覆盖

```python
class TestWeatherApiRouter:
    """天气API路由器测试"""
    
    @pytest.mark.asyncio
    async def test_range_determination(self):
        """测试时间范围判断"""
        router = WeatherApiRouter()
        
        # 测试边界条件
        assert router._determine_forecast_range(0) == ForecastRange.HOURLY
        assert router._determine_forecast_range(3) == ForecastRange.HOURLY
        assert router._determine_forecast_range(4) == ForecastRange.DAILY
        assert router._determine_forecast_range(7) == ForecastRange.DAILY
        assert router._determine_forecast_range(8) == ForecastRange.SIMULATION
    
    @pytest.mark.asyncio
    async def test_service_routing(self):
        """测试服务路由逻辑"""
        router = WeatherApiRouter()
        
        # Mock服务
        with patch.object(router._hourly_service, 'get_forecast') as mock_hourly:
            mock_hourly.return_value = MockWeatherResult()
            
            result = await router.get_forecast(
                {'name': '杭州', 'lng': 120.2, 'lat': 30.3}, 
                datetime.now().strftime('%Y-%m-%d')
            )
            
            # 验证调用了正确的服务
            mock_hourly.assert_called_once()
            assert result.data_source == "hourly_api"
```

### 集成测试

```python
class TestWeatherIntegration:
    """天气系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_forecast(self):
        """端到端预报测试"""
        # 测试完整流程：用户查询 -> 路由 -> API -> 结果
        location_info = {'name': '杭州', 'lng': 120.2, 'lat': 30.3}
        
        # 测试不同时间范围的查询
        test_cases = [
            (datetime.now().strftime('%Y-%m-%d'), 'hourly_api'),      # 今天
            ((datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'), 'hourly_api'),  # 2天后
            ((datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'), 'daily_api'),   # 5天后
            ((datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'), 'simulation') # 10天后
        ]
        
        router = WeatherApiRouter()
        
        for date_str, expected_source in test_cases:
            result = await router.get_forecast(location_info, date_str)
            assert result.data_source == expected_source
            assert len(result.hourly_data) == 24
            assert all(0 <= hour['temperature'] <= 40 for hour in result.hourly_data)
```

---

这个设计为天气API接口差异化提供了完整的技术实现方案，确保系统性能优化和功能稳定性。