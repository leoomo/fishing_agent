#!/usr/bin/env python3
"""
天气数据获取模块

职责:
- 从彩云天气API获取天气数据
- 提取实时、小时级、日级预报数据
- 数据验证和完整性检查
- 天气状态翻译
"""

from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging

from ...utils.coordinate import get_coordinates
from ...utils.api_client import get_weather_client
from ...utils.cache import cache
from .weather_parser import parse_weather_response

logger = logging.getLogger(__name__)


def safe_convert_temperature(temp_value):
    """安全转换温度值

    Args:
        temp_value: 温度值，可能是数字或字符串

    Returns:
        转换后的浮点数温度值，如果无法转换则返回None
    """
    if temp_value is None:
        return None

    # 如果已经是数字，直接返回
    if isinstance(temp_value, (int, float)):
        return float(temp_value)

    # 如果是字符串，尝试转换
    if isinstance(temp_value, str):
        try:
            # 移除常见单位符号
            temp_str = temp_value.strip().replace('°C', '').replace('℃', '').replace('°F', '').replace('K', '')

            # 转换为浮点数
            temp_num = float(temp_str)

            # 如果可能的开尔文温度，转换为摄氏度
            if temp_num > 200:  # 假设超过200可能是开尔文
                temp_num = temp_num - 273.15
                logger.debug(f"开尔文转摄氏度: {temp_value} -> {temp_num:.1f}°C")

            return temp_num

        except (ValueError, TypeError) as e:
            logger.warning(f"温度转换失败: '{temp_value}' - {e}")
            return None

    # 其他类型无法转换
    return None


def get_weather_data(location: str, target_date: datetime) -> Optional[Dict[str, Any]]:
    """获取天气数据 - 使用统一API客户端，直接获取JSON数据"""
    try:
        logger.info(f"开始获取{location}在{target_date}的天气数据")

        # 获取坐标
        coords = get_coordinates(location)
        longitude, latitude = coords

        # 获取天气客户端
        weather_client = get_weather_client()

        # 计算日期差，确定获取多少小时的数据
        today = datetime.now().date()
        if isinstance(target_date, datetime):
            target_date = target_date.date()

        if target_date == today:
            # 今天：优先获取小时级预报数据（用于生成趋势图），回退到实时数据
            logger.info("获取今天的小时级预报数据")
            hourly_data = weather_client.get_hourly_forecast(longitude, latitude, 24)
            if hourly_data:
                result = _extract_hourly_weather(hourly_data, target_date)
                if result and result.get('has_hourly_data'):
                    return result

            # 回退到实时天气数据
            logger.info("回退到实时天气数据")
            weather_data = weather_client.get_realtime_weather(longitude, latitude)
            if weather_data:
                return _extract_realtime_weather(weather_data)
            else:
                return None
        else:
            # 未来日期：获取预报数据
            days_diff = (target_date - today).days
            if 1 <= days_diff <= 3:
                # 1-3天：使用小时级预报（精度最高）
                hours_needed = days_diff * 24
                logger.info(f"获取{hours_needed}小时预报数据（精度高）")

                hourly_data = weather_client.get_hourly_forecast(longitude, latitude, 72)
                if hourly_data:
                    return _extract_hourly_weather(hourly_data, target_date)
                else:
                    return None
            elif 4 <= days_diff <= 6:
                # 4-6天：使用日级预报（中等精度）
                # 注意：daily API返回今天(第0天)+未来6天，共7条数据
                logger.info(f"获取日级预报数据（第{days_diff}天，使用daily API）")

                daily_data = weather_client.get_daily_forecast(longitude, latitude, 7)
                if daily_data:
                    return _extract_daily_weather(daily_data, target_date)
                else:
                    return None
            else:
                logger.warning(f"不支持查询{days_diff}天后的天气数据（API限制：最多6天）")
                return None

    except Exception as e:
        logger.error(f"获取天气数据失败: {str(e)}")
        logger.error(f"详细错误信息: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return None



def _extract_realtime_weather(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """从彩云天气API实时数据中提取天气字段"""
    try:
        logger.info("开始提取实时天气数据")

        realtime = weather_data.get('result', {}).get('realtime', {})

        if not realtime:
            logger.error("API返回数据中没有realtime字段")
            return {}

        # 处理气压单位转换（Pa转hPa）
        pressure = realtime.get('pressure')
        if pressure and pressure > 10000:  # 检查是否为Pa（正常气压范围80000-110000 Pa）
            pressure = pressure / 100  # 转换为hPa
            logger.debug(f"气压单位转换: {realtime.get('pressure')} Pa → {pressure} hPa")

        # 使用安全温度转换
        raw_temp = realtime.get('temperature')
        safe_temp = safe_convert_temperature(raw_temp)

        # 直接使用正确的字段映射
        extracted_data = {
            'temperature': safe_temp,
            'condition': realtime.get('skycon'),
            'wind_speed': realtime.get('wind', {}).get('speed'),
            'humidity': realtime.get('humidity'),
            'pressure': pressure,
            'visibility': realtime.get('visibility'),
            'data_source': 'realtime',
            'data_quality': 'valid'
        }

        # 验证必需字段
        required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
        missing_fields = [field for field in required_fields if extracted_data.get(field) is None]

        # 数据合理性验证
        validation_errors = []

        # 温度范围检查（-60°C 到 70°C）
        if extracted_data.get('temperature') is not None:
            temp = extracted_data['temperature']
            if not (-60 <= temp <= 70):
                validation_errors.append(f"温度值异常: {temp}°C")
                extracted_data['data_quality'] = 'invalid'

        # 气压范围检查（500 hPa 到 1100 hPa，覆盖高海拔地区）
        if extracted_data.get('pressure') is not None:
            pressure = extracted_data['pressure']
            if not (500 <= pressure <= 1100):
                validation_errors.append(f"气压值异常: {pressure:.1f} hPa")
                extracted_data['data_quality'] = 'invalid'

        if missing_fields:
            logger.warning(f"实时天气数据不完整，缺少字段: {missing_fields}")
            extracted_data['data_quality'] = 'incomplete'
            # 根据伦理要求，不编造数据，让上层逻辑处理
        elif validation_errors:
            logger.warning(f"实时天气数据验证失败: {validation_errors}")
            # data_quality已在上面设置为invalid
        else:
            logger.info("实时天气数据提取成功，所有必需字段都存在且合理")

        return extracted_data

    except Exception as e:
        logger.error(f"提取实时天气数据失败: {e}")
        return {}



def _extract_hourly_weather(hourly_data: Dict[str, Any], target_date: date) -> Dict[str, Any]:
    """从彩云天气API小时级预报数据中提取指定日期的天气字段"""
    try:
        logger.info(f"开始提取{target_date}的小时级天气数据")

        hourly = hourly_data.get('result', {}).get('hourly', {})

        if not hourly:
            logger.error("API返回数据中没有hourly字段")
            return {}

        # 获取温度、天气状况、风速、湿度、气压数据
        temperatures = hourly.get('temperature', [])
        skycons = hourly.get('skycon', [])
        winds = hourly.get('wind', [])
        humidities = hourly.get('humidity', [])
        pressures = hourly.get('pressure', [])

        if not temperatures:
            logger.error("没有温度数据")
            return {}

        # 筛选目标日期的数据
        from dateutil import parser as dateparser

        target_temps = []
        target_conditions = []
        target_wind_speeds = []
        target_humidities = []
        target_pressures = []
        target_datetimes = []  # 新增：保存时间戳

        for i, temp_data in enumerate(temperatures):
            try:
                # 解析时间戳
                timestamp = temp_data['datetime']
                if isinstance(timestamp, str):
                    parsed_datetime = dateparser.parse(timestamp)
                    hour_date = parsed_datetime.date()
                else:
                    parsed_datetime = datetime.fromtimestamp(timestamp)
                    hour_date = parsed_datetime.date()

                if hour_date == target_date:
                    # 使用安全温度转换收集目标日期的数据
                    safe_temp = safe_convert_temperature(temp_data['value'])
                    if safe_temp is not None:
                        target_temps.append(safe_temp)
                    target_datetimes.append(parsed_datetime)  # 新增：保存完整时间戳

                    if i < len(skycons):
                        target_conditions.append(skycons[i]['value'])

                    if i < len(winds):
                        target_wind_speeds.append(winds[i]['speed'])

                    if i < len(humidities):
                        # 湿度数据可能需要转换（API返回0-1范围，我们期望0-100）
                        humidity_val = humidities[i]['value']
                        if humidity_val <= 1:
                            humidity_val = humidity_val * 100
                        target_humidities.append(humidity_val)

                    if i < len(pressures):
                        pressure_val = pressures[i]['value']
                        if pressure_val and pressure_val > 10000:  # 检查是否为Pa（正常气压范围80000-110000 Pa）
                            pressure_val = pressure_val / 100  # 转换为hPa
                        target_pressures.append(pressure_val)

            except Exception as e:
                logger.debug(f"处理小时数据失败: {e}")
                continue

        if not target_temps:
            logger.error(f"没有找到{target_date}的温度数据")
            return {}

        # 计算平均值/主要值（安全计算）
        avg_temp = sum(target_temps) / len(target_temps) if target_temps else None

        # 获取主要天气状况（出现频率最高的）
        main_condition = max(set(target_conditions), key=target_conditions.count) if target_conditions else None

        # 计算平均风速、湿度、气压
        avg_wind_speed = sum(target_wind_speeds) / len(target_wind_speeds) if target_wind_speeds else None
        avg_humidity = sum(target_humidities) / len(target_humidities) if target_humidities else None
        avg_pressure = sum(target_pressures) / len(target_pressures) if target_pressures else None

        # 🆕 构建历史数据序列（用于趋势分析）
        historical_data = []
        if len(target_temps) >= 6:
            # 取最近6个小时的数据作为历史序列
            for i in range(max(0, len(target_temps) - 6), len(target_temps)):
                historical_data.append({
                    'temperature': target_temps[i] if i < len(target_temps) else None,
                    'pressure': target_pressures[i] if i < len(target_pressures) else None,
                    'wind_speed': target_wind_speeds[i] if i < len(target_wind_speeds) else None,
                    'timestamp': target_datetimes[i] if i < len(target_datetimes) else None
                })

        extracted_data = {
            # 日平均值（向后兼容）
            'temperature': avg_temp,
            'condition': main_condition,
            'wind_speed': avg_wind_speed,
            'humidity': avg_humidity,
            'pressure': avg_pressure,
            # 新增：24小时数据数组
            'hourly_temps': target_temps,
            'hourly_conditions': target_conditions,
            'hourly_wind_speeds': target_wind_speeds,
            'hourly_humidities': target_humidities,
            'hourly_pressures': target_pressures,
            'hourly_datetimes': target_datetimes,
            'has_hourly_data': len(target_temps) > 0,  # 标记是否有小时数据
            # 🆕 历史数据（用于趋势分析）
            'historical_data': historical_data if len(historical_data) >= 3 else None,
            # 元数据
            'data_source': 'hourly_forecast',
            'data_quality': 'valid'
        }

        # 验证必需字段
        required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
        missing_fields = [field for field in required_fields if extracted_data.get(field) is None]

        # 数据合理性验证
        validation_errors = []

        # 温度范围检查（-60°C 到 70°C）
        if extracted_data.get('temperature') is not None:
            temp = extracted_data['temperature']
            if not (-60 <= temp <= 70):
                validation_errors.append(f"温度值异常: {temp:.1f}°C")

        # 气压范围检查（500 hPa 到 1100 hPa，覆盖高海拔地区）
        if extracted_data.get('pressure') is not None:
            pressure = extracted_data['pressure']
            if not (500 <= pressure <= 1100):
                validation_errors.append(f"气压值异常: {pressure:.1f} hPa")

        if missing_fields:
            logger.warning(f"小时级天气数据不完整，缺少字段: {missing_fields}")
            extracted_data['data_quality'] = 'incomplete'
            # 根据伦理要求，不编造数据，让上层逻辑处理
        elif validation_errors:
            logger.warning(f"小时级天气数据验证失败: {validation_errors}")
            extracted_data['data_quality'] = 'invalid'
        else:
            logger.info(f"小时级天气数据提取成功: 温度={avg_temp:.1f}°C, 天气={main_condition}")

        return extracted_data

    except Exception as e:
        logger.error(f"提取小时级天气数据失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return {}



def _extract_daily_weather(daily_data: Dict[str, Any], target_date: date) -> Dict[str, Any]:
    """从彩云天气API日级预报数据中提取指定日期的天气字段

    Args:
        daily_data: 彩云天气API返回的daily预报数据
        target_date: 目标日期

    Returns:
        提取的天气数据字典，包含温度、风速、湿度、气压、天气状况等字段

    Note:
        - 温度单位: °C (直接使用avg值)
        - 风速单位: m/s (直接使用avg.speed值)
        - 湿度: 0-1格式需转换为百分比
        - 气压: Pa需转换为hPa (除以100)
        - 天气状况: 使用skycon.value
    """
    try:
        logger.info(f"开始提取{target_date}的日级天气数据")

        daily = daily_data.get('result', {}).get('daily', {})

        if not daily:
            logger.error("API返回数据中没有daily字段")
            return {}

        # 获取各字段的数据数组
        temperatures = daily.get('temperature', [])
        skycons = daily.get('skycon', [])
        winds = daily.get('wind', [])
        humidities = daily.get('humidity', [])
        pressures = daily.get('pressure', [])

        if not temperatures:
            logger.error("没有温度数据")
            return {}

        # 查找目标日期的索引
        from dateutil import parser as dateparser

        target_index = None
        for i, temp_data in enumerate(temperatures):
            try:
                timestamp = temp_data['date']
                if isinstance(timestamp, str):
                    parsed_date = dateparser.parse(timestamp).date()
                else:
                    parsed_date = datetime.fromtimestamp(timestamp).date()

                if parsed_date == target_date:
                    target_index = i
                    break
            except Exception as e:
                logger.debug(f"解析日期失败: {e}")
                continue

        if target_index is None:
            logger.error(f"没有找到{target_date}的数据")
            return {}

        # 提取指定日期的数据
        temp_data = temperatures[target_index]
        temperature = temp_data.get('avg')  # 平均温度

        # 天气状况
        condition = None
        if target_index < len(skycons):
            condition = skycons[target_index].get('value')

        # 风速
        wind_speed = None
        if target_index < len(winds):
            wind_data = winds[target_index]
            avg_wind = wind_data.get('avg', {})
            if isinstance(avg_wind, dict):
                wind_speed = avg_wind.get('speed')
            elif isinstance(avg_wind, (int, float)):
                wind_speed = avg_wind

        # 湿度 (0-1格式转百分比)
        humidity = None
        if target_index < len(humidities):
            humidity_data = humidities[target_index]
            humidity_val = humidity_data.get('avg')
            if humidity_val is not None:
                # 如果是0-1范围，转换为百分比
                if humidity_val <= 1:
                    humidity = humidity_val * 100
                else:
                    humidity = humidity_val

        # 气压 (Pa转hPa)
        pressure = None
        if target_index < len(pressures):
            pressure_data = pressures[target_index]
            pressure_val = pressure_data.get('avg')
            if pressure_val is not None:
                # 如果是Pa单位（大于10000），转换为hPa
                if pressure_val > 10000:
                    pressure = pressure_val / 100
                else:
                    pressure = pressure_val

        extracted_data = {
            'temperature': temperature,
            'condition': condition,
            'wind_speed': wind_speed,
            'humidity': humidity,
            'pressure': pressure,
            'data_source': 'daily_forecast',
            'data_quality': 'valid'
        }

        # 验证必需字段
        required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
        missing_fields = [field for field in required_fields if extracted_data.get(field) is None]

        # 数据合理性验证
        validation_errors = []

        # 温度范围检查（-60°C 到 70°C）
        if extracted_data.get('temperature') is not None:
            temp = extracted_data['temperature']
            if not (-60 <= temp <= 70):
                validation_errors.append(f"温度值异常: {temp:.1f}°C")

        # 气压范围检查（500 hPa 到 1100 hPa，覆盖高海拔地区）
        if extracted_data.get('pressure') is not None:
            pressure = extracted_data['pressure']
            if not (500 <= pressure <= 1100):
                validation_errors.append(f"气压值异常: {pressure:.1f} hPa")

        if missing_fields:
            logger.warning(f"日级天气数据不完整，缺少字段: {missing_fields}")
            extracted_data['data_quality'] = 'incomplete'
        elif validation_errors:
            logger.warning(f"日级天气数据验证失败: {validation_errors}")
            extracted_data['data_quality'] = 'invalid'
        else:
            logger.info(f"日级天气数据提取成功: 温度={temperature:.1f}°C, 天气={condition}")

        return extracted_data

    except Exception as e:
        logger.error(f"提取日级天气数据失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return {}



def validate_weather_data(weather_data: Dict[str, Any], location: str) -> Dict[str, Any]:
    """验证天气数据的合理性"""
    validation_errors = []

    # 温度验证 - 扩展合理范围
    if weather_data.get('temperature') is not None:
        temp = weather_data['temperature']
        if not (-60 <= temp <= 70):  # 扩展到更现实的地球表面温度范围
            validation_errors.append(f"温度值超出合理范围: {temp}°C (期望: -60°C 到 70°C)")
            weather_data['temperature'] = None

    # 湿度验证
    if weather_data.get('humidity') is not None:
        humidity = weather_data['humidity']
        if not (0 <= humidity <= 100):
            validation_errors.append(f"湿度值不合理: {humidity}%")
            weather_data['humidity'] = None

    # 风速验证
    if weather_data.get('wind_speed') is not None:
        wind_speed = weather_data['wind_speed']
        if not (0 <= wind_speed <= 50):  # 最大50m/s
            validation_errors.append(f"风速值不合理: {wind_speed} m/s")
            weather_data['wind_speed'] = None

    # 气压验证
    if weather_data.get('pressure') is not None:
        pressure = weather_data['pressure']
        if not (500 <= pressure <= 1100):  # 合理的气压范围
            validation_errors.append(f"气压值不合理: {pressure} hPa")
            weather_data['pressure'] = None

    # 记录验证结果
    if validation_errors:
        logger.warning(f"⚠️ {location}天气数据验证失败: {'; '.join(validation_errors)}")
        weather_data['validation_errors'] = validation_errors
        if weather_data.get('parse_quality') == 'excellent':
            weather_data['parse_quality'] = 'good'
    else:
        logger.debug(f"✅ {location}天气数据验证通过")
        weather_data['validation_errors'] = []

    return weather_data


def translate_weather_condition(skycon: str) -> str:
    """将彩云天气代码转换为中文描述"""
    translations = {
        'CLEAR_DAY': '晴天',
        'CLEAR_NIGHT': '晴夜',
        'PARTLY_CLOUDY_DAY': '多云',
        'PARTLY_CLOUDY_NIGHT': '多云',
        'CLOUDY': '阴天',
        'RAIN': '雨',
        'SNOW': '雪',
        'WIND': '大风',
        'FOG': '雾',
        'HAZE': '霾'
    }
    return translations.get(skycon, skycon)


# 工具列表，用于agent创建
