# DailyWeatherService 规范说明

## 组件概述

**组件名称**: DailyWeatherService (逐天天气预报服务)  
**版本**: 1.0.0  
**类型**: 天气服务组件  
**负责人**: AI Assistant  

## 功能描述

DailyWeatherService专门负责处理3-7天内的天气预报查询。它使用彩云天气的逐天预报API (`weather/daily?dailysteps=7`)，获取未来7天的天气概况，并通过智能插值算法将逐天数据转换为24小时详细数据。该服务在保证较高数据精度的同时，显著提升了API调用效率和响应速度。

## 接口规范

### 主要接口

#### `get_forecast(location_info: dict, date_str: str) -> WeatherResult`

获取指定日期的天气预报数据，使用逐天API并进行小时级插值。

**参数**:
- `location_info: dict` - 地理位置信息
  - `name: str` - 地点名称
  - `lng: float` - 经度 (范围: -180 到 180)
  - `lat: float` - 纬度 (范围: -90 到 90)
  - `adcode: str` - 行政区划代码 (可选)
  - `level: str` - 行政级别 (可选)

- `date_str: str` - 查询日期，格式为"YYYY-MM-DD"
  - 必须在当前日期的3-7天范围内
  - 超出范围将抛出`DateOutOfRangeException`

**返回值**:
- `WeatherResult` - 统一格式的天气查询结果
  - `data_source: str` - 固定为"daily_api"
  - `hourly_data: list` - 24小时插值数据数组
  - `confidence: float` - 置信度，通常为0.85 (插值数据精度适中)
  - `api_url: str` - API端点"weather/daily?dailysteps=7"
  - `cached: bool` - 是否来自缓存

**异常**:
- `DateOutOfRangeException` - 查询日期超出3-7天范围
- `LocationNotFoundException` - 地点信息无效或不存在
- `ApiQuotaExceededException` - API调用次数超限
- `NetworkException` - 网络连接异常
- `WeatherApiException` - 天气API服务异常
- `InterpolationException` - 数据插值处理异常

### 核心方法

#### `_process_daily_data(api_data: dict, target_date: str) -> WeatherResult`

处理API返回的逐天数据，提取目标日期信息并进行插值转换。

**参数**:
- `api_data: dict` - 彩云天气API返回的原始数据
- `target_date: str` - 目标日期字符串

**处理流程**:
1. 解析API响应数据结构
2. 提取日期数组 `api_data['result']['daily']['time']`
3. 找到目标日期在数组中的索引
4. 提取当日温度、天气、风速、湿度等逐天数据
5. 调用插值算法转换为24小时数据
6. 构建标准化的`WeatherResult`对象

#### `_find_date_index(dates: list, target_date: str) -> int`

在日期数组中查找目标日期的索引位置。

**参数**:
- `dates: list` - API返回的日期数组 (Unix时间戳)
- `target_date: str` - 目标日期字符串

**返回值**:
- `int` - 目标日期在数组中的索引，如果未找到返回-1

**算法逻辑**:
```python
def _find_date_index(self, dates: list, target_date: str) -> int:
    """查找目标日期在API数据中的索引"""
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
    target_timestamp = int(target_datetime.timestamp())
    
    for i, date_timestamp in enumerate(dates):
        # 考虑时区差异和日期精度
        api_date = datetime.fromtimestamp(date_timestamp).date()
        if api_date == target_datetime.date():
            return i
    
    return -1
```

#### `_interpolate_daily_to_hourly(day_data: dict, date_str: str) -> list`

将逐天数据插值为24小时数据的核心算法。

**参数**:
- `day_data: dict` - 单日的天气数据
  - `temperature_max: float` - 日最高温度
  - `temperature_min: float` - 日最低温度
  - `weather: str` - 天气状况
  - `wind_speed: float` - 日均风速
  - `humidity: float` - 日均湿度
- `date_str: str` - 日期字符串

**返回值**:
- `list[HourlyData]` - 24小时插值数据对象列表

**插值算法设计**:

1. **温度插值** - 基于正弦曲线模拟日内温度变化:
   ```python
   # 假设最低温出现在早上6点，最高温出现在下午14点
   def _interpolate_temperature(self, temp_min: float, temp_max: float, hour: int) -> float:
       if hour <= 6:
           # 0-6点：温度逐渐降至最低
           factor = hour / 6
           return temp_min + (temp_max - temp_min) * factor * 0.3
       elif hour <= 14:
           # 6-14点：温度逐渐升至最高
           factor = (hour - 6) / 8
           return temp_min + (temp_max - temp_min) * (0.3 + 0.7 * factor)
       else:
           # 14-24点：温度逐渐下降
           factor = (hour - 14) / 10
           return temp_max - (temp_max - temp_min) * 0.7 * factor
   ```

2. **风速插值** - 考虑日内风速变化规律:
   ```python
   def _interpolate_wind_speed(self, base_wind: float, hour: int) -> float:
       # 风速在午后通常较高，夜间较低
       wind_factor = 0.8 + 0.4 * math.sin(hour * math.pi / 12)
       return base_wind * wind_factor
   ```

3. **湿度插值** - 与温度变化的负相关关系:
   ```python
   def _interpolate_humidity(self, base_humidity: float, temperature: float, 
                           base_temp: float) -> float:
       # 温度升高时湿度相对下降
       humidity_variation = (temperature - base_temp) * 2
       return max(30, min(95, base_humidity - humidity_variation))
   ```

#### `_validate_interpolation_result(hourly_data: list) -> bool`

验证插值结果的合理性和完整性。

**参数**:
- `hourly_data: list` - 插值生成的24小时数据

**验证逻辑**:
1. 数据完整性检查 (确保24小时数据)
2. 数值范围合理性验证
3. 日变化趋势连续性检查
4. 极端值和异常值检测

## 数据结构规范

### DayData 结构 (逐天数据)

```python
@dataclass
class DayData:
    """逐天天气数据结构"""
    date: datetime                # 日期
    temperature_max: float        # 日最高温度 (°C)
    temperature_min: float        # 日最低温度 (°C)
    temperature_avg: float        # 日平均温度 (°C)
    weather: str                  # 主要天气状况
    weather_hours: dict           # 各时段天气状况分布
    wind_speed_max: float         # 最大风速 (m/s)
    wind_speed_avg: float         # 平均风速 (m/s)
    wind_direction: float         # 主要风向 (度)
    humidity_max: float           # 最大湿度 (%)
    humidity_min: float           # 最小湿度 (%)
    humidity_avg: float           # 平均湿度 (%)
    pressure_max: float           # 最高气压 (hPa)
    pressure_min: float           # 最低气压 (hPa)
    precipitation: float          # 降水量 (mm)
    ultraviolet_max: float        # 最大紫外线指数
    air_quality_aqi: int          # 空气质量指数
    
    def get_temperature_range(self) -> tuple:
        """获取当日温度范围"""
        return self.temperature_min, self.temperature_max
    
    def is_weather_good_for_outdoor(self) -> bool:
        """判断是否适合户外活动"""
        good_weather = ['晴', '多云', '阴']
        return (self.weather in good_weather and 
                10 <= self.temperature_avg <= 30 and
                self.wind_speed_avg <= 5)
```

### 插值参数配置

```python
INTERPOLATION_CONFIG = {
    'temperature': {
        'min_hour': 6,          # 最低温出现时间 (小时)
        'max_hour': 14,         # 最高温出现时间 (小时)
        'morning_factor': 0.3,  # 早晨温度变化因子
        'evening_drop': 0.7     # 晚间温度下降因子
    },
    'wind_speed': {
        'base_factor': 0.8,     # 基础风速因子
        'variation_range': 0.4, # 风速变化范围
        'peak_hour': 15         # 风速峰值时间
    },
    'humidity': {
        'temp_correlation': 2.0, # 温湿度相关系数
        'min_humidity': 30,      # 最小湿度限制
        'max_humidity': 95       # 最大湿度限制
    }
}
```

## API调用规范

### 请求格式

```python
# HTTP GET请求
GET https://api.caiyunapp.com/v2.6/{API_KEY}/{lng},{lat}/weather?alert=true&dailysteps=7

# 请求参数说明:
# - API_KEY: 彩云天气API密钥
# - lng, lat: 经纬度坐标
# - alert: 是否包含天气预警
# - dailysteps: 天预报步数 (固定为7)

# 请求头
Headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'WeatherService/1.0'
}
```

### 响应数据结构

```python
# 彩云天气逐天API响应结构示例
{
    "status": "ok",
    "lang": "zh_CN", 
    "unit": "metric",
    "tzshift": 28800,
    "location": [120.2, 30.3],
    "result": {
        "daily": {
            "status": "ok",
            "temperature_2m": [
                [15.2, 8.1, 11.6],      # 最高温, 最低温, 平均温度
                [18.5, 10.2, 14.3],     # 第二天数据
                # ... 7天数据
            ],
            "weather": [
                "晴",                    # 第一天天气
                "多云",                  # 第二天天气
                # ... 7天天气
            ],
            "wind_speed": [
                [5.2, 2.1, 3.6],        # 最大风速, 最小风速, 平均风速
                # ... 7天数据
            ],
            "wind_direction": [
                180,                     # 主要风向
                # ... 7天数据
            ],
            "humidity_2m": [
                [75, 45, 60],            # 最大湿度, 最小湿度, 平均湿度
                # ... 7天数据
            ],
            "precipitation": [0.0, 2.5, 0.0],  # 降水量
            "air_quality": {"aqi": [45, 68, 72]},  # 空气质量
            "ultraviolet": [6, 4, 3],     # 紫外线指数
            "time": [1698758400, 1698844800, ...]  # 时间戳
        }
    }
}
```

### 数据解析和转换

```python
def _parse_daily_response(self, api_data: dict, target_index: int) -> DayData:
    """解析API响应中的逐天数据"""
    daily = api_data['result']['daily']
    
    # 提取温度数据
    temp_data = daily['temperature_2m'][target_index]
    temperature_max = temp_data[0]
    temperature_min = temp_data[1] 
    temperature_avg = temp_data[2]
    
    # 提取天气和其他数据
    weather = daily['weather'][target_index]
    
    wind_data = daily['wind_speed'][target_index]
    wind_speed_max = wind_data[0]
    wind_speed_avg = wind_data[2]
    
    humidity_data = daily['humidity_2m'][target_index]
    humidity_max = humidity_data[0]
    humidity_min = humidity_data[1]
    humidity_avg = humidity_data[2]
    
    # 构建DayData对象
    return DayData(
        date=datetime.fromtimestamp(daily['time'][target_index]),
        temperature_max=temperature_max,
        temperature_min=temperature_min,
        temperature_avg=temperature_avg,
        weather=weather,
        wind_speed_max=wind_data[0],
        wind_speed_avg=wind_speed_avg,
        humidity_max=humidity_max,
        humidity_min=humidity_min,
        humidity_avg=humidity_avg,
        precipitation=daily['precipitation'][target_index],
        air_quality_aqi=daily['air_quality']['aqi'][target_index],
        ultraviolet_max=daily['ultraviolet'][target_index]
    )
```

## 插值算法详解

### 温度插值算法

```python
def _interpolate_temperature_profile(self, day_data: DayData) -> dict:
    """生成24小时温度变化曲线"""
    temp_min = day_data.temperature_min
    temp_max = day_data.temperature_max
    temp_avg = day_data.temperature_avg
    
    hourly_temps = {}
    
    for hour in range(24):
        if hour <= 6:
            # 夜间到清晨：温度下降至最低点
            progress = hour / 6
            temp = temp_avg - (temp_avg - temp_min) * progress
        elif hour <= 14:
            # 上午到下午：温度上升至最高点
            progress = (hour - 6) / 8
            temp = temp_min + (temp_max - temp_min) * progress
        else:
            # 下午到夜间：温度下降
            progress = (hour - 14) / 10
            temp = temp_max - (temp_max - temp_min) * progress
        
        # 添加随机扰动使数据更真实
        noise = random.gauss(0, 0.5)  # ±0.5°C的随机扰动
        hourly_temps[hour] = round(temp + noise, 1)
    
    return hourly_temps
```

### 风速插值算法

```python
def _interpolate_wind_profile(self, day_data: DayData) -> dict:
    """生成24小时风速变化曲线"""
    base_wind = day_data.wind_speed_avg
    wind_max = day_data.wind_speed_max
    
    hourly_winds = {}
    
    for hour in range(24):
        # 风速通常在下午2-4点达到峰值
        peak_factor = math.exp(-((hour - 15) ** 2) / 50)  # 高斯分布
        
        # 基础风速 + 日变化 + 随机扰动
        wind_speed = base_wind + (wind_max - base_wind) * peak_factor
        noise = random.gauss(0, 0.2)  # 风速随机扰动
        hourly_winds[hour] = max(0, round(wind_speed + noise, 1))
    
    return hourly_winds
```

### 湿度插值算法

```python
def _interpolate_humidity_profile(self, day_data: DayData, temp_profile: dict) -> dict:
    """基于温度变化生成24小时湿度曲线"""
    base_humidity = day_data.humidity_avg
    humidity_range = day_data.humidity_max - day_data.humidity_min
    
    hourly_humidity = {}
    
    for hour in range(24):
        # 湿度与温度呈负相关
        temp = temp_profile[hour]
        temp_deviation = temp - day_data.temperature_avg
        
        # 温度升高时湿度下降
        humidity_adjustment = -temp_deviation * 2.0
        humidity = base_humidity + humidity_adjustment
        
        # 添加日变化 (清晨湿度较高)
        daily_variation = 5 * math.cos((hour - 6) * math.pi / 12)
        humidity += daily_variation
        
        # 添加随机扰动
        noise = random.gauss(0, 2)
        final_humidity = humidity + noise
        
        # 限制在合理范围内
        hourly_humidity[hour] = max(30, min(95, round(final_humidity, 1)))
    
    return hourly_humidity
```

## 缓存策略

### 缓存配置

```python
DAILY_CACHE_CONFIG = {
    'ttl_seconds': 7200,        # 缓存TTL (2小时)
    'max_size': 500,           # 最大缓存条目数
    'cleanup_interval': 600,   # 清理间隔 (10分钟)
    'compression_enabled': True, # 启用数据压缩
    'key_prefix': 'daily_'      # 缓存键前缀
}
```

### 缓存键策略

```python
def _generate_cache_key(self, location_info: dict, date_str: str) -> str:
    """生成唯一的缓存键"""
    location_name = location_info.get('name', 'unknown')
    # 标准化处理：移除特殊字符，统一格式
    normalized_name = ''.join(c for c in location_name if c.isalnum() or c == '_')
    return f"daily_{normalized_name}_{date_str}"
```

### 缓存数据格式

```python
{
    "data_source": "daily_api",
    "day_data": {
        "date": "2025-11-06T00:00:00Z",
        "temperature_max": 18.5,
        "temperature_min": 10.2,
        "temperature_avg": 14.3,
        "weather": "多云",
        "wind_speed_avg": 3.2,
        "humidity_avg": 65,
        "precipitation": 0.0,
        "air_quality_aqi": 68
    },
    "hourly_data": [
        {
            "time": "2025-11-06T00:00:00Z",
            "temperature": 11.5,
            "weather": "多云",
            "wind_speed": 2.8,
            "humidity": 72,
            "interpolated": True  # 标记为插值数据
        },
        # ... 24小时数据
    ],
    "confidence": 0.85,
    "api_url": "weather/daily?dailysteps=7",
    "cached": True,
    "cache_timestamp": "2025-11-04T10:30:00Z"
}
```

## 配置规范

### 服务配置

```python
DAILY_WEATHER_CONFIG = {
    'api_endpoint': 'https://api.caiyunapp.com/v2.6',
    'api_key': '${CAIYUN_API_KEY}',
    'cache_ttl': 7200,                          # 2小时TTL
    'request_timeout': 15.0,                     # 请求超时时间
    'max_retry_attempts': 3,
    'forecast_range_min_days': 3,               # 最小预报天数
    'forecast_range_max_days': 7,               # 最大预报天数
    'interpolation_enabled': True,              # 启用插值算法
    'validation_enabled': True                  # 启用数据验证
}
```

### 插值算法配置

```python
INTERPOLATION_CONFIG = {
    'temperature': {
        'curve_type': 'sine',                   # 温度曲线类型
        'min_temp_hour': 6,                     # 最低温时间
        'max_temp_hour': 14,                    # 最高温时间
        'noise_factor': 0.5,                    # 随机扰动因子
        'smoothing_enabled': True               # 平滑处理
    },
    'wind_speed': {
        'distribution_type': 'gaussian',        # 风速分布类型
        'peak_hour': 15,                        # 峰值时间
        'std_deviation': 4.0,                   # 标准差
        'min_wind_speed': 0.1                   # 最小风速
    },
    'humidity': {
        'temp_correlation': -2.0,               # 温湿度相关系数
        'daily_variation_amplitude': 5,         # 日变化幅度
        'phase_shift': 6,                       # 相位偏移
        'range_limit': [30, 95]                 # 湿度范围限制
    }
}
```

## 错误处理规范

### 插值异常处理

```python
class InterpolationException(Exception):
    """数据插值处理异常"""
    pass

def _safe_interpolation(self, day_data: DayData, date_str: str) -> list:
    """安全的插值处理，包含异常恢复"""
    try:
        # 尝试执行插值算法
        hourly_data = self._interpolate_daily_to_hourly(day_data, date_str)
        
        # 验证插值结果
        if not self._validate_interpolation_result(hourly_data):
            raise InterpolationException("插值结果验证失败")
        
        return hourly_data
        
    except Exception as e:
        self.logger.warning(f"插值失败，使用简化算法: {e}")
        
        # 降级到简化的线性插值
        return self._fallback_linear_interpolation(day_data, date_str)

def _fallback_linear_interpolation(self, day_data: DayData, date_str: str) -> list:
    """简化的线性插值算法作为备用方案"""
    hourly_data = []
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # 简单的线性插值：温度从最低到最高再回到最低
    temp_range = day_data.temperature_max - day_data.temperature_min
    
    for hour in range(24):
        hour_datetime = target_date.replace(hour=hour, minute=0, second=0)
        
        if hour <= 12:
            # 上午：线性升温
            progress = hour / 12
            temperature = day_data.temperature_min + temp_range * progress
        else:
            # 下午：线性降温
            progress = (hour - 12) / 12
            temperature = day_data.temperature_max - temp_range * progress
        
        hour_data = {
            'time': hour_datetime,
            'temperature': round(temperature, 1),
            'weather': day_data.weather,
            'wind_speed': day_data.wind_speed_avg,
            'humidity': day_data.humidity_avg
        }
        hourly_data.append(hour_data)
    
    return hourly_data
```

## 性能要求

### 响应时间要求

- **缓存命中**: < 100ms
- **API调用**: < 3000ms (P95)
- **插值处理**: < 200ms
- **总响应时间**: < 3500ms (P95)

### 数据质量要求

- **温度精度**: ±1°C
- **插值连续性**: 相邻小时温度变化 < 5°C
- **数据合理性**: 95%的数据在合理范围内
- **置信度**: ≥ 0.85

### 可靠性要求

- **服务可用性**: 99.8%+
- **插值成功率**: 98%+
- **API成功率**: 90%+ (包含重试)
- **缓存命中率**: 60%+

## 测试规范

### 插值算法测试

```python
class TestInterpolationAlgorithm:
    """插值算法测试"""
    
    def test_temperature_interpolation(self):
        """测试温度插值算法"""
        day_data = DayData(
            date=datetime(2025, 11, 6),
            temperature_max=20.0,
            temperature_min=10.0,
            temperature_avg=15.0,
            weather="晴"
        )
        
        service = DailyWeatherService()
        hourly_data = service._interpolate_daily_to_hourly(day_data, "2025-11-06")
        
        # 验证24小时数据
        assert len(hourly_data) == 24
        
        # 验证温度范围
        temps = [h.temperature for h in hourly_data]
        assert min(temps) >= 9.0  # 允许小幅超出
        assert max(temps) <= 21.0
        
        # 验证温度变化趋势 (清晨低，下午高)
        assert hourly_data[6].temperature < hourly_data[14].temperature
        
        # 验证温度连续性
        for i in range(1, 24):
            temp_diff = abs(hourly_data[i].temperature - hourly_data[i-1].temperature)
            assert temp_diff <= 5.0  # 相邻小时温度变化不应过大
```

### 集成测试

```python
class TestDailyWeatherIntegration:
    """逐天天气服务集成测试"""
    
    @pytest.mark.asyncio
    async def test_4_day_forecast(self):
        """测试4天后的天气预报 (在服务范围内)"""
        service = DailyWeatherService()
        location_info = {'name': '杭州', 'lng': 120.2, 'lat': 30.3}
        
        # 查询4天后的天气
        future_date = (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d')
        result = await service.get_forecast(location_info, future_date)
        
        assert result.data_source == "daily_api"
        assert len(result.hourly_data) == 24
        assert result.confidence >= 0.8
        
        # 验证插值数据特征
        for hour_data in result.hourly_data:
            assert -50 <= hour_data.temperature <= 60
            assert 0 <= hour_data.humidity <= 100
            assert hour_data.wind_speed >= 0
    
    @pytest.mark.asyncio
    async def test_boundary_dates(self):
        """测试边界日期 (3天和7天)"""
        service = DailyWeatherService()
        location_info = {'name': '上海', 'lng': 121.5, 'lat': 31.2}
        
        # 测试3天边界 (应该包含在服务范围内)
        date_3_days = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        result_3_days = await service.get_forecast(location_info, date_3_days)
        assert result_3_days.data_source == "daily_api"
        
        # 测试7天边界 (应该包含在服务范围内)
        date_7_days = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        result_7_days = await service.get_forecast(location_info, date_7_days)
        assert result_7_days.data_source == "daily_api"
        
        # 测试8天 (应该超出服务范围)
        date_8_days = (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d')
        with pytest.raises(DateOutOfRangeException):
            await service.get_forecast(location_info, date_8_days)
```

---

**文档版本**: 1.0  
**最后更新**: 2025-11-04  
**审核状态**: 待审核  