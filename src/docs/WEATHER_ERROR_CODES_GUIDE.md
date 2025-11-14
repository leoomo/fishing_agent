# 天气服务错误码系统指南

本文档详细介绍了天气服务中实现的综合错误码系统，包括错误码定义、使用方法和最佳实践。

## 目录

- [概述](#概述)
- [错误码定义](#错误码定义)
- [支持的方法](#支持的方法)
- [使用指南](#使用指南)
- [错误处理示例](#错误处理示例)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 概述

天气服务错误码系统提供了详细的请求状态反馈，帮助开发者准确判断请求成功或失败的原因，并制定相应的处理策略。

### 主要特性

- **🎯 精确错误分类**: 10个不同的错误码覆盖所有可能的错误场景
- **📊 详细状态信息**: 每个错误码都配有详细的状态消息和描述
- **🔄 降级机制**: 即使失败也会提供可用的模拟数据
- **⚡ 高性能**: 错误码处理不影响服务性能
- **🛡️ 向后兼容**: 不影响现有代码的正常运行

### 错误码分类

| 类别 | 错误码 | 描述 |
|------|--------|------|
| **成功类** | 0, 1 | 请求成功或缓存命中 |
| **API问题** | 2, 4 | API调用失败或网络超时 |
| **数据问题** | 3, 5, 9 | 坐标未找到、解析失败、数据超出范围 |
| **参数问题** | 6, 7, 8 | 参数错误、日期错误、时间段错误 |

## 错误码定义

### WeatherServiceErrorCode 类

```python
class WeatherServiceErrorCode:
    SUCCESS = 0           # 成功
    CACHE_HIT = 1         # 缓存命中
    API_ERROR = 2         # API错误
    COORDINATE_NOT_FOUND = 3  # 坐标未找到
    NETWORK_TIMEOUT = 4   # 网络超时
    DATA_PARSE_ERROR = 5  # 数据解析失败
    PARAMETER_ERROR = 6   # 参数错误
    DATE_PARSE_ERROR = 7  # 日期解析错误
    TIME_PERIOD_ERROR = 8 # 时间段错误
    DATA_OUT_OF_RANGE = 9 # 数据超出范围
```

### 详细错误码说明

| 错误码 | 名称 | 描述 | 常见场景 | 处理建议 |
|--------|------|------|----------|----------|
| **0** | SUCCESS | 成功 | API调用成功获取数据 | 正常使用数据 |
| **1** | CACHE_HIT | 缓存命中 | 从缓存获取数据 | 正常使用数据 |
| **2** | API_ERROR | API错误 | API密钥无效、API服务异常 | 使用模拟数据 |
| **3** | COORDINATE_NOT_FOUND | 坐标未找到 | 地名无法匹配到坐标 | 使用模拟数据 |
| **4** | NETWORK_TIMEOUT | 网络超时 | 网络连接超时 | 使用模拟数据 |
| **5** | DATA_PARSE_ERROR | 数据解析失败 | API响应格式异常 | 使用模拟数据 |
| **6** | PARAMETER_ERROR | 参数错误 | 地区名为空、小时数超限 | 检查输入参数 |
| **7** | DATE_PARSE_ERROR | 日期解析错误 | 日期格式无效、日期不存在 | 检查日期格式 |
| **8** | TIME_PERIOD_ERROR | 时间段错误 | 时间段表达式无效 | 检查时间表达式 |
| **9** | DATA_OUT_OF_RANGE | 数据超出范围 | 日期超出历史/预报范围 | 使用模拟数据 |

## 支持的方法

### 1. get_weather_by_date()

根据指定日期查询天气信息。

**方法签名**:
```python
def get_weather_by_date(place_name: str, date: str) -> tuple[WeatherData, str, int]
```

**参数**:
- `place_name` (str): 地区名称
- `date` (str): 日期字符串 (格式: YYYY-MM-DD)

**返回**:
- `tuple[WeatherData, str, int]`: (天气数据, 状态消息, 错误码)

**可能返回的错误码**:
- `0`: 成功获取指定日期天气
- `1`: 从缓存获取数据
- `2`: API调用失败，使用模拟数据
- `3`: 地区坐标未找到，使用模拟数据
- `4`: 网络超时，使用模拟数据
- `5`: 数据解析失败，使用模拟数据
- `6`: 参数错误（空地区名或空日期）
- `7`: 日期解析错误（格式无效或日期不存在）
- `9`: 日期超出查询范围（历史1天或未来15天）

### 2. get_weather_by_datetime()

根据时间段查询天气信息。

**方法签名**:
```python
def get_weather_by_datetime(place_name: str, datetime_str: str) -> tuple[WeatherData, str, int]
```

**参数**:
- `place_name` (str): 地区名称
- `datetime_str` (str): 时间段表达式（如"明天上午"、"今天下午3点"）

**返回**:
- `tuple[WeatherData, str, int]`: (天气数据, 状态消息, 错误码)

**可能返回的错误码**:
- `0`: 成功获取时间段天气
- `1`: 从缓存获取数据
- `2`: API调用失败，使用模拟数据
- `3`: 地区坐标未找到，使用模拟数据
- `4`: 网络超时，使用模拟数据
- `5`: 数据解析失败，使用模拟数据
- `6`: 参数错误（空地区名或空时间表达式）
- `7`: 日期解析错误（时间表达式无法解析）
- `8`: 时间段错误（时间段格式无效）

### 3. get_hourly_forecast()

获取指定小时数的小时级天气预报。

**方法签名**:
```python
def get_hourly_forecast(place_name: str, hours: int) -> tuple[HourlyForecastData, str, int]
```

**参数**:
- `place_name` (str): 地区名称
- `hours` (int): 预报小时数 (1-360)

**返回**:
- `tuple[HourlyForecastData, str, int]`: (小时预报数据, 状态消息, 错误码)

**可能返回的错误码**:
- `0`: 成功获取小时预报
- `1`: 从缓存获取数据
- `2`: API调用失败，使用模拟数据
- `3`: 地区坐标未找到，使用模拟数据
- `4`: 网络超时，使用模拟数据
- `5`: 数据解析失败，使用模拟数据
- `6`: 参数错误（空地区名或小时数超出1-360范围）

## 使用指南

### 基本使用方法

```python
from services.weather.datetime_weather_service import DateTimeWeatherService, WeatherServiceErrorCode

# 创建服务实例
service = DateTimeWeatherService()

# 调用方法并获取错误码
weather_data, status_msg, error_code = service.get_weather_by_date("北京", "2024-12-25")

# 检查请求是否成功
if service.is_weather_query_successful(error_code):
    print(f"✅ 请求成功: {status_msg}")
    print(f"温度: {weather_data.temperature}°C")
else:
    print(f"⚠️ 请求失败: {status_msg}")
    print(f"错误码: {error_code} ({WeatherServiceErrorCode.get_description(error_code)})")

    # 即使失败也可能有模拟数据可用
    if weather_data:
        print(f"模拟数据: {weather_data.temperature}°C")
```

### 便利方法

```python
# 检查是否成功（包括缓存命中）
is_successful = service.is_weather_query_successful(error_code)

# 检查是否为实时API数据成功
is_api_success = service.is_weather_query_api_success(error_code)

# 获取错误码描述
description = WeatherServiceErrorCode.get_description(error_code)
```

### 在WeatherTool中使用

```python
from tools.weather_tool import WeatherTool

# 创建工具实例
tool = WeatherTool()

# 执行操作
result = await tool.execute(
    operation="weather_by_date",
    location="北京",
    date="2024-12-25"
)

# 检查结果和错误码
if result.success:
    print("✅ 请求成功")
else:
    print(f"❌ 请求失败: {result.error}")

# 获取错误码信息
if result.metadata:
    error_code = result.metadata.get("error_code")
    status_message = result.metadata.get("status_message")
    description = result.metadata.get("description")

    print(f"错误码: {error_code}")
    print(f"状态: {status_message}")
    print(f"描述: {description}")
```

## 错误处理示例

### 完整错误处理示例

```python
import asyncio
from services.weather.datetime_weather_service import DateTimeWeatherService, WeatherServiceErrorCode

async def comprehensive_error_handling_demo():
    """综合错误处理演示"""
    service = DateTimeWeatherService()

    # 测试各种场景
    test_cases = [
        ("北京", "2024-12-25", "正常查询"),
        ("", "2024-12-25", "空地区名"),
        ("上海", "", "空日期"),
        ("广州", "2024-13-25", "无效日期"),
        ("深圳", "1999-01-01", "超出历史范围"),
        ("杭州", "2030-01-01", "超出预报范围"),
    ]

    for place, date, description in test_cases:
        print(f"\n📍 测试: {description}")
        print(f"   参数: place='{place}', date='{date}'")

        try:
            weather_data, status_msg, error_code = service.get_weather_by_date(place, date)

            # 错误码分析
            print(f"   🎯 错误码: {error_code}")
            print(f"   📝 描述: {WeatherServiceErrorCode.get_description(error_code)}")
            print(f"   💬 状态: {status_msg}")

            # 成功判定
            if service.is_weather_query_successful(error_code):
                print(f"   ✅ 请求成功!")
                if weather_data:
                    print(f"   🌡️ 温度: {weather_data.temperature}°C")
            else:
                print(f"   ⚠️ 请求失败，但有模拟数据")
                if weather_data:
                    print(f"   🔄 模拟数据温度: {weather_data.temperature}°C")

            # 具体错误处理策略
            if error_code == WeatherServiceErrorCode.PARAMETER_ERROR:
                print(f"   💡 建议: 检查输入参数")
            elif error_code == WeatherServiceErrorCode.DATE_PARSE_ERROR:
                print(f"   💡 建议: 检查日期格式")
            elif error_code == WeatherServiceErrorCode.DATA_OUT_OF_RANGE:
                print(f"   💡 建议: 使用有效日期范围")
            elif error_code in [WeatherServiceErrorCode.API_ERROR,
                              WeatherServiceErrorCode.NETWORK_TIMEOUT]:
                print(f"   💡 建议: 检查网络连接和API配置")

        except Exception as e:
            print(f"   ❌ 系统异常: {str(e)}")

# 运行演示
asyncio.run(comprehensive_error_handling_demo())
```

### 错误码分类处理

```python
def handle_error_by_category(error_code: int, weather_data, status_msg: str):
    """根据错误码类别进行不同处理"""

    # 成功类
    if error_code in [0, 1]:
        print(f"✅ 成功获取数据: {status_msg}")
        return weather_data

    # 参数问题
    elif error_code in [6, 7, 8]:
        print(f"⚠️ 输入参数错误: {status_msg}")
        print("💡 请检查输入参数并重试")
        # 不返回模拟数据，要求用户修正输入
        return None

    # API问题
    elif error_code in [2, 4]:
        print(f"🔄 API服务问题: {status_msg}")
        print("💡 使用缓存数据，稍后重试")
        return weather_data  # 返回模拟数据

    # 数据问题
    elif error_code in [3, 5, 9]:
        print(f"🌍 数据获取问题: {status_msg}")
        print("💡 使用模拟数据，建议检查地名或日期")
        return weather_data  # 返回模拟数据

    # 未知错误
    else:
        print(f"❓ 未知错误: {status_msg}")
        return weather_data
```

## 最佳实践

### 1. 错误码检查优先级

```python
# ✅ 推荐：先检查错误码，再处理数据
weather_data, status_msg, error_code = service.get_weather_by_date("北京", "2024-12-25")

if service.is_weather_query_successful(error_code):
    # 处理成功情况
    process_weather_data(weather_data)
else:
    # 根据错误码采取不同策略
    handle_error_scenario(error_code, weather_data)
```

### 2. 分层错误处理

```python
# 第一层：基础成功检查
if not service.is_weather_query_successful(error_code):
    return None  # 或返回错误响应

# 第二层：数据质量检查
if not service.is_weather_query_api_success(error_code):
    logger.warning(f"使用了非实时数据: {status_msg}")

# 第三层：业务逻辑处理
return process_weather_data(weather_data)
```

### 3. 错误码日志记录

```python
import logging

logger = logging.getLogger(__name__)

def log_error_code(error_code: int, place_name: str, additional_info: str = ""):
    """记录错误码信息"""
    description = WeatherServiceErrorCode.get_description(error_code)

    if error_code in [0, 1]:
        logger.info(f"天气查询成功 - {place_name}: {description}")
    elif error_code in [6, 7, 8]:
        logger.warning(f"天气查询参数错误 - {place_name}: {description} - {additional_info}")
    else:
        logger.error(f"天气查询失败 - {place_name}: {description} ({error_code}) - {additional_info}")
```

### 4. 用户友好的错误消息

```python
def get_user_friendly_error_message(error_code: int, place_name: str) -> str:
    """获取用户友好的错误消息"""

    messages = {
        0: f"成功获取{place_name}的天气信息",
        1: f"从缓存获取{place_name}的天气信息",
        6: f"输入参数有误，请检查地区名称或日期格式",
        7: f"日期格式不正确，请使用YYYY-MM-DD格式",
        9: f"查询的日期超出范围，请查询近1天到未来15天的天气",
        2: f"天气服务暂时不可用，请稍后重试",
        4: f"网络连接超时，请检查网络连接",
    }

    return messages.get(error_code, f"查询{place_name}天气时遇到问题")
```

### 5. 批量查询错误处理

```python
async def batch_weather_query_with_error_handling(queries: list[tuple[str, str]]):
    """批量查询天气并处理错误"""
    service = DateTimeWeatherService()
    results = []

    for place_name, date in queries:
        try:
            weather_data, status_msg, error_code = service.get_weather_by_date(place_name, date)

            result = {
                'place': place_name,
                'date': date,
                'success': service.is_weather_query_successful(error_code),
                'error_code': error_code,
                'error_description': WeatherServiceErrorCode.get_description(error_code),
                'status_message': status_msg,
                'data': weather_data if weather_data else None
            }

            results.append(result)

        except Exception as e:
            results.append({
                'place': place_name,
                'date': date,
                'success': False,
                'error_code': -1,
                'error_description': '系统异常',
                'status_message': str(e),
                'data': None
            })

    return results
```

## 故障排除

### 常见问题

1. **错误码6频繁出现**
   - 检查输入参数是否为空
   - 验证日期格式是否正确
   - 确认小时数在1-360范围内

2. **错误码2持续出现**
   - 检查API密钥配置
   - 验证网络连接
   - 查看API服务状态

3. **错误码7无法解决**
   - 确认日期字符串格式为YYYY-MM-DD
   - 检查日期是否有效（如2月30日）
   - 验证时间表达式格式

4. **模拟数据质量问题**
   - 这是正常的降级机制
   - API恢复后会自动使用真实数据
   - 可以检查错误码了解具体原因

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **检查错误码描述**
   ```python
   description = WeatherServiceErrorCode.get_description(error_code)
   print(f"错误描述: {description}")
   ```

3. **验证输入参数**
   ```python
   # 验证日期格式
   import datetime
   try:
       datetime.datetime.strptime(date_str, '%Y-%m-%d')
   except ValueError:
       print(f"无效日期格式: {date_str}")
   ```

4. **测试不同场景**
   ```bash
   # 运行错误码演示
   uv run python demo_comprehensive_error_codes.py
   ```

---

**更新时间**: 2025-11-04
**版本**: 1.0.0
**维护者**: LangChain 学习项目