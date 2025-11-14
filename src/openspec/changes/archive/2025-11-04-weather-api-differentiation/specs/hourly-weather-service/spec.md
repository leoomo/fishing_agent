# HourlyWeatherService 规范说明

## 组件概述

**组件名称**: HourlyWeatherService (逐小时天气预报服务)  
**版本**: 1.0.0  
**类型**: 天气服务组件  
**负责人**: AI Assistant  

## 功能描述

HourlyWeatherService专门负责处理3天内的逐小时天气预报查询。它使用彩云天气的逐小时预报API (`weather/hourly?hourlysteps=72`)，提供高精度的24小时详细天气数据。该服务针对0-3天时间范围进行了专门优化，具有数据精度高、缓存策略精细、响应速度快的特点。

## 接口规范

### 主要接口

#### `get_forecast(location_info: dict, date_str: str) -> WeatherResult`

获取指定日期的逐小时天气预报数据。

**参数**:
- `location_info: dict` - 地理位置信息
  - `name: str` - 地点名称
  - `lng: float` - 经度 (范围: -180 到 180)
  - `lat: float` - 纬度 (范围: -90 到 90)
  - `adcode: str` - 行政区划代码 (可选，中国标准)
  - `level: str` - 行政级别 (可选: province, city, district)

- `date_str: str` - 查询日期，格式为"YYYY-MM-DD"
  - 必须在当前日期的3天内 (包括今天)
  - 超出范围将抛出`DateOutOfRangeException`

**返回值**:
- `WeatherResult` - 统一格式的天气查询结果
  - `data_source: str` - 固定为"hourly_api"
  - `hourly_data: list` - 24小时详细数据数组
  - `confidence: float` - 置信度，通常为0.95 (API数据精度高)
  - `api_url: str` - API端点"weather/hourly?hourlysteps=72"
  - `cached: bool` - 是否来自缓存

**异常**:
- `DateOutOfRangeException` - 查询日期超出3天范围
- `LocationNotFoundException` - 地点信息无效或不存在
- `ApiQuotaExceededException` - API调用次数超限
- `NetworkException` - 网络连接异常
- `WeatherApiException` - 天气API服务异常

### 核心方法

#### `_process_hourly_data(api_data: dict, target_date: str) -> WeatherResult`

处理API返回的逐小时数据，提取目标日期的24小时数据。

**参数**:
- `api_data: dict` - 彩云天气API返回的原始数据
- `target_date: str` - 目标日期字符串

**处理流程**:
1. 解析API响应数据结构
2. 提取时间戳数组 `api_data['result']['hourly']['time']`
3. 计算目标日期的时间范围 (00:00:00 到 23:59:59)
4. 筛选时间范围内的小时数据
5. 提取对应的温度、天气、风速、湿度等数据
6. 构建标准化的`HourlyData`对象列表

#### `_extract_target_date_hours(timestamps: list, target_date: str) -> list`

从72小时时间戳中筛选出目标日期的24小时索引。

**参数**:
- `timestamps: list` - API返回的时间戳数组 (Unix时间戳)
- `target_date: str` - 目标日期

**返回值**:
- `list` - 目标日期24小时对应的时间戳索引数组

**算法逻辑**:
```python
def _extract_target_date_hours(timestamps, target_date):
    target_start = datetime.strptime(target_date, "%Y-%m-%d")
    target_end = target_start + timedelta(days=1)
    
    target_indices = []
    for i, timestamp in enumerate(timestamps):
        dt = datetime.fromtimestamp(timestamp)
        if target_start <= dt < target_end:
            target_indices.append(i)
    
    return target_indices
```

#### `_build_hourly_data_list(api_data: dict, target_indices: list) -> list`

根据索引列表构建24小时详细数据。

**参数**:
- `api_data: dict` - API原始数据
- `target_indices: list` - 目标小时索引数组

**返回值**:
- `list[HourlyData]` - 24小时详细数据对象列表

### 缓存接口

#### `_get_cache_key(location_name: str, date_str: str) -> str`

生成缓存键，格式为: `hourly_{location_name}_{date_str}`

**参数**:
- `location_name: str` - 地点名称
- `date_str: str` - 查询日期

**返回值**:
- `str` - 缓存键字符串

#### `_is_cache_valid(cached_data: WeatherResult) -> bool`

验证缓存数据是否仍然有效。

**参数**:
- `cached_data: WeatherResult` - 缓存的天气结果

**验证逻辑**:
- 检查缓存时间是否超过30分钟TTL
- 验证数据格式完整性
- 确认置信度不低于阈值

## 数据结构规范

### HourlyData 结构

```python
@dataclass
class HourlyData:
    """逐小时天气数据结构"""
    time: datetime              # 时间点 (精确到小时)
    temperature: float          # 温度 (摄氏度，范围: -50 到 60)
    weather: str               # 天气状况 (晴/多云/阴/雨/雪等)
    wind_speed: float          # 风速 (米/秒，范围: 0 到 50)
    wind_direction: float      # 风向 (度，范围: 0 到 360)
    humidity: float            # 湿度 (百分比，范围: 0 到 100)
    pressure: float            # 气压 (百帕，范围: 800 到 1200)
    visibility: float          # 能见度 (公里，范围: 0 到 50)
    precipitation: float       # 降水量 (毫米，范围: 0 到 100)
    ultraviolet: float         # 紫外线指数 (范围: 0 到 15)
    aqi: int                   # 空气质量指数 (范围: 0 到 500)
    
    def get_fishing_score(self) -> float:
        """计算钓鱼适宜性评分 (0-100)"""
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

### API响应数据结构

```python
# 彩云天气API响应结构示例
{
    "status": "ok",
    "lang": "zh_CN",
    "unit": "metric",
    "tzshift": 28800,
    "tzname": "Asia/Shanghai",
    "location": [
        120.2,  # 经度
        30.3    # 纬度
    ],
    "result": {
        "hourly": {
            "status": "ok",
            "temperature_2m": [15.2, 14.8, ...],     # 温度
            "weather": ["晴", "多云", ...],           # 天气状况
            "wind_speed": [2.1, 2.3, ...],           # 风速
            "wind_direction": [180, 185, ...],        # 风向
            "humidity_2m": [65, 68, ...],            # 湿度
            "pressure_surface": [1013, 1012, ...],    # 气压
            "visibility": [10, 8, ...],              # 能见度
            "precipitation": [0, 0, ...],            # 降水量
            "ultraviolet": [3, 2, ...],              # 紫外线指数
            "air_quality": {"aqi": [45, 48, ...]},   # 空气质量
            "time": [1698758400, 1698762000, ...]    # 时间戳
        }
    }
}
```

## 配置规范

### 必需配置

```python
HOURLY_WEATHER_CONFIG = {
    'api_endpoint': 'https://api.caiyunapp.com/v2.6',  # API基础地址
    'api_key': '${CAIYUN_API_KEY}',                    # API密钥
    'cache_ttl': 1800,                                 # 缓存TTL (30分钟)
    'request_timeout': 10.0,                           # 请求超时时间
    'max_retry_attempts': 3,                           # 最大重试次数
    'forecast_range_days': 3                           # 预报范围天数
}
```

### 性能优化配置

```python
PERFORMANCE_CONFIG = {
    'connection_pool_size': 20,        # 连接池大小
    'max_concurrent_requests': 50,     # 最大并发请求数
    'batch_request_enabled': True,     # 是否启用批量请求
    'compression_enabled': True,       # 是否启用压缩
    'keep_alive_enabled': True         # 是否启用长连接
}
```

### 缓存配置

```python
CACHE_CONFIG = {
    'enabled': True,                   # 是否启用缓存
    'ttl_seconds': 1800,              # 缓存TTL (30分钟)
    'max_size': 1000,                 # 最大缓存条目数
    'cleanup_interval': 300,          # 清理间隔 (5分钟)
    'compression': True               # 是否压缩缓存数据
}
```

## API调用规范

### 请求格式

```python
# HTTP GET请求
GET https://api.caiyunapp.com/v2.6/{API_KEY}/{lng},{lat}/weather?alert=true&hourlysteps=72

# 请求参数说明:
# - API_KEY: 彩云天气API密钥
# - lng, lat: 经纬度坐标
# - alert: 是否包含天气预警
# - hourlysteps: 小时预报步数 (最大72)

# 请求头
Headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'WeatherService/1.0'
}
```

### 响应处理

1. **成功响应 (200)**:
   ```python
   # 验证响应格式
   if response.status_code == 200:
       data = await response.json()
       if data.get('status') == 'ok':
           hourly_data = data['result']['hourly']
           if hourly_data.get('status') == 'ok':
               return self._process_hourly_data(data, target_date)
   ```

2. **错误响应处理**:
   ```python
   # API限流 (429)
   if response.status == 429:
       raise ApiQuotaExceededException("API调用频率超限")
   
   # 地理位置无效 (404)
   if response.status == 404:
       raise LocationNotFoundException("指定的地理位置无效")
   
   # API密钥无效 (401)
   if response.status == 401:
       raise AuthenticationException("API密钥无效或已过期")
   ```

### 重试策略

```python
async def _api_call_with_retry(self, url: str, params: dict) -> dict:
    """带重试机制的API调用"""
    for attempt in range(self.max_retry_attempts):
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status in [429, 502, 503, 504]:
                    # 可重试的错误码
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise WeatherApiException(f"API调用失败: {response.status}")
        except Exception as e:
            if attempt == self.max_retry_attempts - 1:
                raise
            await asyncio.sleep(1)
```

## 缓存策略

### 缓存键设计

```python
def _generate_cache_key(self, location_info: dict, date_str: str) -> str:
    """生成唯一的缓存键"""
    location_name = location_info.get('name', 'unknown')
    # 标准化地点名称，移除特殊字符
    normalized_name = re.sub(r'[^\w\u4e00-\u9fff]', '', location_name)
    return f"hourly_{normalized_name}_{date_str}"
```

### 缓存数据格式

```python
{
    "data_source": "hourly_api",
    "hourly_data": [
        {
            "time": "2025-11-05T00:00:00Z",
            "temperature": 15.2,
            "weather": "晴",
            "wind_speed": 2.1,
            "humidity": 65,
            # ... 其他字段
        },
        # ... 24小时数据
    ],
    "confidence": 0.95,
    "api_url": "weather/hourly?hourlysteps=72",
    "cached": True,
    "cache_timestamp": "2025-11-04T10:30:00Z"
}
```

### 缓存失效策略

1. **TTL失效**: 缓存30分钟后自动失效
2. **手动失效**: 数据更新时主动清除相关缓存
3. **容量管理**: LRU策略淘汰旧缓存
4. **定期清理**: 每5分钟清理过期缓存

## 错误处理规范

### 异常类型定义

```python
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
```

### 错误恢复机制

1. **API调用失败**:
   - 重试机制 (最多3次，指数退避)
   - 切换到备用API端点
   - 降级到模拟数据服务

2. **数据处理失败**:
   - 数据完整性验证
   - 异常值过滤和修正
   - 使用默认值填充缺失数据

3. **缓存失败**:
   - 绕过缓存直接调用API
   - 缓存服务降级处理
   - 异常情况下的直接查询

## 性能要求

### 响应时间要求

- **缓存命中**: < 50ms
- **API调用**: < 2000ms (P95)
- **数据处理**: < 100ms
- **总响应时间**: < 2500ms (P95)

### 并发处理能力

- **最大并发**: 50个并发请求
- **吞吐量**: 1000 QPS
- **连接池**: 20个持久连接
- **内存使用**: < 100MB

### 可靠性要求

- **服务可用性**: 99.9%+
- **API成功率**: 95%+ (包含重试)
- **数据准确性**: 99%+
- **缓存命中率**: 70%+

## 测试规范

### 单元测试

```python
class TestHourlyWeatherService:
    """逐小时天气服务单元测试"""
    
    @pytest.fixture
    def service(self):
        return HourlyWeatherService()
    
    @pytest.mark.asyncio
    async def test_get_forecast_success(self, service):
        """测试正常天气预报查询"""
        location_info = {'name': '杭州', 'lng': 120.2, 'lat': 30.3}
        date_str = '2025-11-05'
        
        result = await service.get_forecast(location_info, date_str)
        
        assert result.data_source == "hourly_api"
        assert len(result.hourly_data) == 24
        assert result.confidence >= 0.9
        assert all(0 <= hour.temperature <= 50 for hour in result.hourly_data)
    
    @pytest.mark.asyncio
    async def test_date_out_of_range(self, service):
        """测试超出日期范围的查询"""
        location_info = {'name': '杭州', 'lng': 120.2, 'lat': 30.3}
        future_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
        
        with pytest.raises(DateOutOfRangeException):
            await service.get_forecast(location_info, future_date)
    
    def test_extract_target_date_hours(self, service):
        """测试时间戳筛选逻辑"""
        base_time = datetime(2025, 11, 5, 0, 0, 0)
        timestamps = [base_time.timestamp() + i * 3600 for i in range(72)]
        
        indices = service._extract_target_date_hours(timestamps, '2025-11-05')
        
        assert len(indices) == 24
        assert all(0 <= idx < 72 for idx in indices)
```

### 集成测试

```python
class TestHourlyWeatherIntegration:
    """逐小时天气服务集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_forecast(self):
        """端到端天气预报测试"""
        service = HourlyWeatherService()
        location_info = {'name': '北京', 'lng': 116.4, 'lat': 39.9}
        
        # 测试今天、明天、后天的预报
        for days_ahead in range(3):
            date_str = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            result = await service.get_forecast(location_info, date_str)
            
            assert result.data_source == "hourly_api"
            assert len(result.hourly_data) == 24
            assert result.confidence >= 0.9
            
            # 验证数据合理性
            temps = [h.temperature for h in result.hourly_data]
            assert all(-50 <= t <= 60 for t in temps)  # 温度合理范围
            assert all(0 <= h.humidity <= 100 for h in result.hourly_data)  # 湿度合理范围
```

### 性能测试

```python
class TestHourlyWeatherPerformance:
    """逐小时天气服务性能测试"""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """测试缓存性能"""
        service = HourlyWeatherService()
        location_info = {'name': '上海', 'lng': 121.5, 'lat': 31.2}
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 首次调用 (无缓存)
        start_time = time.time()
        await service.get_forecast(location_info, date_str)
        first_call_time = time.time() - start_time
        
        # 二次调用 (有缓存)
        start_time = time.time()
        await service.get_forecast(location_info, date_str)
        second_call_time = time.time() - start_time
        
        # 缓存应该显著提升性能
        assert second_call_time < first_call_time * 0.1
        assert second_call_time < 0.1  # 缓存响应应 < 100ms
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        service = HourlyWeatherService()
        location_info = {'name': '广州', 'lng': 113.3, 'lat': 23.1}
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 并发执行10个相同请求
        tasks = [
            service.get_forecast(location_info, date_str)
            for _ in range(10)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 验证所有结果一致
        for result in results:
            assert result.data_source == "hourly_api"
            assert len(result.hourly_data) == 24
        
        # 并发请求应该合理快速完成
        assert total_time < 5.0  # 10个并发请求应在5秒内完成
```

---

**文档版本**: 1.0  
**最后更新**: 2025-11-04  
**审核状态**: 待审核  