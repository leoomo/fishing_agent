# 彩云天气 API 文档

本文档描述了智能钓鱼助手项目中使用的彩云天气API v2.6版本，包括实时天气、72小时预报和API字段映射。

## 📋 概述

彩云天气API提供高精度的天气数据服务，支持实时天气查询、小时级预报和日级预报。

- **API版本**: v2.6
- **基础URL**: `https://api.caiyunapp.com/v2.6`
- **支持范围**: 全球覆盖，中国境内精度最高
- **更新频率**: 实时天气每5-10分钟更新，预报数据每小时更新

## 🔑 API认证

### API密钥配置

```bash
# 环境变量配置
CAIYUN_API_KEY=your-caiyun-api-key-here
```

### API URL格式

```
https://api.caiyunapp.com/v2.6/{API_KEY}/{longitude},{latitude}/{endpoint}
```

**参数说明**:
- `{API_KEY}`: 彩云天气API密钥
- `{longitude},{latitude}`: 经度,纬度（注意顺序）
- `{endpoint}`: API端点类型

## 🌤️ 实时天气 API

### 请求格式

```bash
GET https://api.caiyunapp.com/v2.6/{API_KEY}/{longitude},{latitude}/realtime
```

### 响应示例

```json
{
  "status": "ok",
  "api_version": "v2.6",
  "api_status": "active",
  "lang": "zh_CN",
  "unit": "metric",
  "tzshift": 28800,
  "timezone": "Asia/Shanghai",
  "server_time": 1703001234,
  "location": [39.9042, 116.4074],
  "result": {
    "realtime": {
      "status": "ok",
      "temperature": 15.2,
      "apparent_temperature": 13.8,
      "humidity": 0.65,
      "pressure": 1018.25,
      "wind": {
        "speed": 3.2,
        "direction": 180
      },
      "skycon": "CLEAR_DAY",
      "cloudrate": 0.1,
      "visibility": 25.0,
      "dswrf": 450.2,
      "precipitation": {
        "nearest": {
          "status": "ok",
          "distance": 1000,
          "intensity": 0.0
        }
      },
      "air_quality": {
        "aqi": {
          "chn": 45,
          "usa": 32
        },
        "pm25": 25
      },
      "life_index": {
        "ultraviolet": {
          "index": "3",
          "desc": "中等"
        },
        "comfort": {
          "index": "3",
          "desc": "较舒适"
        }
      }
    }
  }
}
```

### 字段映射说明

#### 核心天气字段

| JSONPath | 字段名称 | 数据类型 | 说明 | 项目使用 |
|----------|----------|----------|------|----------|
| `result.realtime.temperature` | 温度 | float | 地表2米气温(°C) | ✅ 钓鱼评分 |
| `result.realtime.apparent_temperature` | 体感温度 | float | 体感温度(°C) | ✅ 显示 |
| `result.realtime.humidity` | 湿度 | float | 相对湿度(0-1) | ✅ 钓鱼评分 |
| `result.realtime.pressure` | 气压 | float | 地面气压(hPa) | ✅ 钓鱼评分 |
| `result.realtime.wind.speed` | 风速 | float | 地表10米风速(m/s) | ✅ 钓鱼评分 |
| `result.realtime.wind.direction` | 风向 | float | 地表10米风向(度) | 📊 扩展功能 |
| `result.realtime.skycon` | 天气状况 | string | 天气现象代码 | ✅ 钓鱼评分 |
| `result.realtime.cloudrate` | 云量 | float | 云量(0-1) | 📊 扩展功能 |
| `result.realtime.visibility` | 能见度 | float | 能见度(km) | 📊 扩展功能 |
| `result.realtime.dswrf` | 短波辐射 | float | 向下短波辐射(W/m²) | 📊 扩展功能 |

#### 空气质量字段

| JSONPath | 字段名称 | 数据类型 | 说明 | 项目使用 |
|----------|----------|----------|------|----------|
| `result.realtime.air_quality.aqi.chn` | 国标AQI | int | 中国国标AQI | 📊 扩展功能 |
| `result.realtime.air_quality.pm25` | PM2.5 | float | PM2.5浓度(μg/m³) | 📊 扩展功能 |

#### 生活指数字段

| JSONPath | 字段名称 | 数据类型 | 说明 | 项目使用 |
|----------|----------|----------|------|----------|
| `result.realtime.life_index.ultraviolet.desc` | 紫外线 | string | 紫外线指数描述 | 📊 扩展功能 |
| `result.realtime.life_index.comfort.desc` | 舒适度 | string | 舒适度指数描述 | 📊 扩展功能 |

### 天气现象代码 (skycon)

| 代码 | 中文描述 | 英文描述 | 钓鱼适用性 |
|------|----------|----------|------------|
| `CLEAR_DAY` | 晴天 | Clear day | ⭐⭐⭐⭐⭐ |
| `CLEAR_NIGHT` | 晴夜 | Clear night | ⭐⭐⭐⭐⭐ |
| `PARTLY_CLOUDY_DAY` | 多云 | Partly cloudy day | ⭐⭐⭐⭐ |
| `PARTLY_CLOUDY_NIGHT` | 多云 | Partly cloudy night | ⭐⭐⭐⭐ |
| `CLOUDY` | 阴天 | Cloudy | ⭐⭐⭐ |
| `RAIN` | 雨 | Rain | ⭐⭐ |
| `SNOW` | 雪 | Snow | ⭐ |
| `WIND` | 大风 | Windy | ⭐ |
| `FOG` | 雾 | Fog | ⭐ |
| `HAZE` | 霾 | Haze | ⭐⭐ |

## ⏰ 小时级预报 API (72小时)

### 请求格式

```bash
GET https://api.caiyunapp.com/v2.6/{API_KEY}/{longitude},{latitude}/hourly?hourlysteps=72
```

**参数说明**:
- `hourlysteps`: 预报小时数，范围[1, 360]，项目使用72小时

### 响应示例

```json
{
  "status": "ok",
  "api_version": "v2.6",
  "lang": "zh_CN",
  "unit": "metric",
  "tzshift": 28800,
  "timezone": "Asia/Shanghai",
  "server_time": 1703001234,
  "location": [39.9042, 116.4074],
  "result": {
    "hourly": {
      "status": "ok",
      "description": "未来72小时多云转晴",
      "precipitation": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 0.0,
          "probability": 0
        }
      ],
      "temperature": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 15.2
        }
      ],
      "apparent_temperature": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 13.8
        }
      ],
      "wind": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "speed": 3.2,
          "direction": 180
        }
      ],
      "humidity": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 0.65
        }
      ],
      "cloudrate": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 0.3
        }
      ],
      "skycon": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": "CLEAR_NIGHT"
        }
      ],
      "pressure": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 1018.25
        }
      ],
      "visibility": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 25.0
        }
      ],
      "dswrf": [
        {
          "datetime": "2023-12-20T00:00+08:00",
          "value": 0.0
        }
      ],
      "air_quality": {
        "aqi": [
          {
            "datetime": "2023-12-20T00:00+08:00",
            "value": {
              "chn": 45,
              "usa": 32
            }
          }
        ],
        "pm25": [
          {
            "datetime": "2023-12-20T00:00+08:00",
            "value": 25
          }
        ]
      }
    },
    "primary": 0
  }
}
```

### 小时预报字段映射

| JSONPath | 字段名称 | 数据类型 | 说明 | 项目使用 |
|----------|----------|----------|------|----------|
| `result.hourly.temperature` | 温度数组 | array[object] | 每小时温度 | ✅ 72小时预报 |
| `result.hourly.apparent_temperature` | 体感温度数组 | array[object] | 每小时体感温度 | ✅ 72小时预报 |
| `result.hourly.humidity` | 湿度数组 | array[object] | 每小时湿度 | ✅ 72小时预报 |
| `result.hourly.wind.speed` | 风速数组 | array[object] | 每小时风速 | ✅ 72小时预报 |
| `result.hourly.wind.direction` | 风向数组 | array[object] | 每小时风向 | 📊 扩展功能 |
| `result.hourly.skycon` | 天气现象数组 | array[object] | 每小时天气状况 | ✅ 72小时预报 |
| `result.hourly.pressure` | 气压数组 | array[object] | 每小时气压 | ✅ 72小时预报 |
| `result.hourly.precipitation.probability` | 降水概率数组 | array[object] | 每小时降水概率 | 📊 扩展功能 |

## 📅 日级预报 API

### 请求格式

```bash
GET https://api.caiyunapp.com/v2.6/{API_KEY}/{longitude},{latitude}/daily?dailysteps=7
```

**参数说明**:
- `dailysteps`: 预报天数，范围[1, 15]，项目使用7天

### 日级预报字段映射

| JSONPath | 字段名称 | 数据类型 | 说明 | 项目使用 |
|----------|----------|----------|------|----------|
| `result.daily.temperature` | 温度范围 | array[object] | 每日最高/最低/平均温度 | 📊 扩展功能 |
| `result.daily.skycon` | 天气现象 | array[object] | 每日主要天气状况 | 📊 扩展功能 |
| `result.daily.precipitation` | 降水数据 | array[object] | 每日降水量和概率 | 📊 扩展功能 |
| `result.daily.wind` | 风速风向 | array[object] | 每日风速风向范围 | 📊 扩展功能 |
| `result.daily.life_index` | 生活指数 | object | 生活指数数据 | 📊 扩展功能 |

## 🔧 项目实现

### API客户端实现

```python
# utils/api_client.py
class WeatherAPIClient:
    def __init__(self):
        self.api_key = os.getenv("CAIYUN_API_KEY")
        self.base_url = "https://api.caiyunapp.com/v2.6"
        self.timeout = 30

    def get_realtime_weather(self, lat: float, lon: float) -> dict:
        """获取实时天气"""
        url = f"{self.base_url}/{self.api_key}/{lon},{lat}/realtime"

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "ok":
                # 项目简化数据提取
                weather_data = {
                    "temperature": data["result"]["realtime"]["temperature"],
                    "condition": data["result"]["realtime"]["skycon"],
                    "humidity": data["result"]["realtime"]["humidity"] * 100,  # 转换为百分比
                    "wind_speed": data["result"]["realtime"]["wind"]["speed"],
                    "pressure": data["result"]["realtime"]["pressure"],
                    "data_quality": "valid"
                }
                return weather_data
            else:
                raise Exception(f"API错误: {data.get('description', '未知错误')}")

        except Exception as e:
            raise Exception(f"获取天气数据失败: {str(e)}")

    def get_hourly_forecast(self, lat: float, lon: float, hours: int = 72) -> dict:
        """获取72小时天气预报"""
        url = f"{self.base_url}/{self.api_key}/{lon},{lat}/hourly"
        params = {
            'hourlysteps': str(hours),
            'alert': 'true'
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "ok":
                hourly_data = data["result"]["hourly"]

                forecast_data = {
                    "hourly_temperature": [item["value"] for item in hourly_data["temperature"]],
                    "hourly_condition": [item["value"] for item in hourly_data["skycon"]],
                    "hourly_humidity": [item["value"] * 100 for item in hourly_data["humidity"]],
                    "forecast_hours": hours,
                    "data_quality": "valid"
                }
                return forecast_data
            else:
                raise Exception(f"API错误: {data.get('description', '未知错误')}")

        except Exception as e:
            raise Exception(f"获取天气预报失败: {str(e)}")
```

### 数据验证和错误处理

```python
def _validate_weather_data(weather_data: dict) -> bool:
    """验证天气数据的完整性和合理性"""
    required_fields = ['temperature', 'condition', 'humidity', 'wind_speed', 'pressure']

    # 检查必需字段
    if not all(field in weather_data for field in required_fields):
        return False

    # 检查温度合理性 (-50°C 到 60°C)
    temp = weather_data.get('temperature')
    if temp is None or temp < -50 or temp > 60:
        return False

    # 检查湿度合理性 (0% 到 100%)
    humidity = weather_data.get('humidity')
    if humidity is None or humidity < 0 or humidity > 100:
        return False

    # 检查风速合理性 (0 到 50 m/s)
    wind_speed = weather_data.get('wind_speed')
    if wind_speed is None or wind_speed < 0 or wind_speed > 50:
        return False

    # 检查气压合理性 (900 到 1100 hPa)
    pressure = weather_data.get('pressure')
    if pressure is None or pressure < 900 or pressure > 1100:
        return False

    return True
```

## 📊 钓鱼评分算法应用

### 7因子评分数据映射

```python
def _calculate_fishing_score(weather_data: dict) -> dict:
    """基于彩云天气数据的钓鱼评分算法"""

    # 数据质量验证
    if not _validate_weather_data(weather_data):
        return {
            'overall': 0.0,
            'data_quality': 'incomplete'
        }

    # 7因子评分计算
    scores = {}

    # 1. 温度因子 (10-25°C最佳)
    temp = weather_data['temperature']
    if 10 <= temp <= 25:
        scores['temperature'] = 90 + (temp - 10) * 2  # 90-110分
    elif 5 <= temp < 10:
        scores['temperature'] = 60 + (temp - 5) * 6   # 60-90分
    elif 25 < temp <= 30:
        scores['temperature'] = 110 - (temp - 25) * 4  # 90-110分
    else:
        scores['temperature'] = max(20, 60 - abs(temp - 17.5) * 2)

    # 2. 天气因子 (根据skycon)
    condition = weather_data['condition']
    weather_scores = {
        'CLEAR_DAY': 95, 'CLEAR_NIGHT': 100,
        'PARTLY_CLOUDY_DAY': 85, 'PARTLY_CLOUDY_NIGHT': 90,
        'CLOUDY': 70, 'RAIN': 40, 'SNOW': 20,
        'WIND': 30, 'FOG': 25, 'HAZE': 60
    }
    scores['weather'] = weather_scores.get(condition, 50)

    # 3. 风力因子 (1-3级最佳)
    wind_speed = weather_data['wind_speed']
    if 1 <= wind_speed <= 3:
        scores['wind'] = 100
    elif 3 < wind_speed <= 5:
        scores['wind'] = 85 - (wind_speed - 3) * 10
    elif wind_speed < 1:
        scores['wind'] = 80 + wind_speed * 20
    else:
        scores['wind'] = max(20, 65 - wind_speed * 8)

    # 4. 湿度因子 (60-80%最佳)
    humidity = weather_data['humidity']
    if 60 <= humidity <= 80:
        scores['humidity'] = 95
    elif 50 <= humidity < 60:
        scores['humidity'] = 75 + (humidity - 50) * 2
    elif 80 < humidity <= 90:
        scores['humidity'] = 95 - (humidity - 80) * 2
    else:
        scores['humidity'] = max(30, 70 - abs(humidity - 70) * 0.5)

    # 5. 气压因子 (稳定高压最佳)
    pressure = weather_data['pressure']
    if 1010 <= pressure <= 1025:
        scores['pressure'] = 90 + (pressure - 1010) * 0.5
    elif 1000 <= pressure < 1010:
        scores['pressure'] = 75 + (pressure - 1000) * 1.5
    else:
        scores['pressure'] = max(40, 85 - abs(pressure - 1017.5) * 0.8)

    # 6. 季节因子 (根据当前日期)
    current_month = datetime.now().month
    if 3 <= current_month <= 5:  # 春季
        scores['seasonal'] = 95
    elif 9 <= current_month <= 11:  # 秋季
        scores['seasonal'] = 100
    elif 6 <= current_month <= 8:  # 夏季
        scores['seasonal'] = 80
    else:  # 冬季
        scores['seasonal'] = 60

    # 7. 时间因子 (根据当前小时)
    current_hour = datetime.now().hour
    if 6 <= current_hour <= 8 or 18 <= current_hour <= 20:
        scores['time'] = 100  # 黄金时段
    elif 9 <= current_hour <= 11 or 15 <= current_hour <= 17:
        scores['time'] = 85   # 较好时段
    elif 12 <= current_hour <= 14:
        scores['time'] = 70   # 一般时段
    else:
        scores['time'] = 50   # 较差时段

    # 计算综合评分
    overall = sum(scores.values()) / len(scores)
    scores['overall'] = round(overall, 1)
    scores['data_quality'] = 'valid'

    return scores
```

## 🔍 错误处理和降级策略

### API错误类型

| 错误类型 | HTTP状态码 | 处理策略 | 项目应用 |
|----------|------------|----------|----------|
| API密钥无效 | 401 | 返回配置错误，不提供天气数据 | ❌ 拒绝服务 |
| 超出配额 | 429 | 等待后重试，最多3次 | ⏱️ 重试机制 |
| 网络超时 | 408/504 | 返回网络错误，不提供模拟数据 | ❌ 诚实报告 |
| 位置无效 | 400 | 返回位置错误，不提供模拟数据 | ❌ 诚实报告 |
| 数据解析失败 | 200 | 返回数据错误，不提供模拟数据 | ❌ 诚实报告 |

### 伦理约束实施

```python
def ethical_weather_response(location: str, error_type: str) -> str:
    """伦理约束下的天气响应"""

    responses = {
        'api_key_invalid': f"天气服务配置错误，无法获取{location}的天气数据。请联系管理员检查API配置。",
        'network_error': f"网络连接失败，无法获取{location}的天气数据。请检查网络连接后重试。",
        'location_invalid': f"无法找到位置：'{location}'。请检查位置名称是否正确。",
        'data_invalid': f"获取{location}天气数据时发生错误，无法提供准确的天气信息。",
        'quota_exceeded': "天气服务调用次数已达上限，请稍后再试。"
    }

    return responses.get(error_type, "天气服务暂时不可用，请稍后重试。")

def ethical_fishing_response(location: str, date: str) -> str:
    """伦理约束下的钓鱼响应"""

    return f"""
🎣 {location}钓鱼建议 ({date})

⚠️ 由于无法获取准确的天气数据，暂无法提供专业的钓鱼评分分析。

💡 **通用钓鱼建议：**
- 建议选择天气条件较好的时候出行
- 早晨6-8点和傍晚18-20点通常是较好的钓鱼时段
- 请关注当地实时天气预报，做好相应准备

📋 **安全提醒：**
- 钓鱼前请检查天气状况
- 确保装备齐全，注意安全
- 遵守当地钓鱼规定

如需准确的钓鱼分析，请稍后重试或检查网络连接。
"""
```

## 📈 性能优化

### 缓存策略

```python
# 缓存时间设置
CACHE_CONFIG = {
    'realtime_weather': 600,      # 10分钟
    'hourly_forecast': 1800,      # 30分钟
    'daily_forecast': 3600,       # 1小时
    'coordinates': 86400,         # 24小时
}

# 缓存键格式
CACHE_KEYS = {
    'realtime': 'weather_realtime_{lat}_{lon}',
    'hourly': 'weather_hourly_{lat}_{lon}_{hours}',
    'coordinates': 'coords_{location_hash}'
}
```

### API调用优化

```python
class OptimizedWeatherClient:
    """优化的天气客户端"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FishingAgent/2.2.0',
            'Accept': 'application/json'
        })

    def get_realtime_weather_with_cache(self, lat: float, lon: float) -> dict:
        """带缓存的实时天气获取"""
        cache_key = f"weather_realtime_{lat}_{lon}"

        # 尝试从缓存获取
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        # API调用
        weather_data = self.get_realtime_weather(lat, lon)

        # 缓存结果
        cache.set(cache_key, weather_data, ttl=600)

        return weather_data
```

## 📝 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v2.2.0 | 2025-11-19 | 与简化架构保持一致，确认字段映射 |
| v2.1.0 | 2025-11-14 | 添加72小时预报支持，修复字段映射 |
| v2.0.0 | 2025-11-01 | 添加伦理约束，移除模拟数据 |
| v1.0.0 | 2025-10-15 | 初始版本，基础API文档 |

---

**最后更新**: 2025-11-19
**API版本**: v2.6
**维护者**: 智能钓鱼助手项目