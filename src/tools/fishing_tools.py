#!/usr/bin/env python3
"""
钓鱼工具模块 - 简化架构版本

使用LangChain 1.0+最佳实践，整合钓鱼推荐、分析和建议功能。
替代原来的15+个文件，提供完整的钓鱼决策支持。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
import logging
from langchain.tools import tool

try:
    from ..utils.coordinate_utils import get_coordinates
    from ..utils.api_client import get_weather_client
    from ..utils.cache import cache
except ImportError:
    # 回退到绝对导入
    from utils.coordinate_utils import get_coordinates
    from utils.api_client import get_weather_client
    from utils.cache import cache

logger = logging.getLogger(__name__)


@tool
def query_fishing_recommendation(location: str, date: str = None) -> str:
    """
    查询钓鱼时间推荐，基于天气条件分析最佳的钓鱼时间

    Args:
        location: 地区名称，如"杭州"、"北京"、"余杭区"等
        date: 日期字符串，支持：
              - 相对日期: "明天"、"后天"、"今天"
              - 绝对日期: "2024-12-25"
              - 空值: 默认为明天

    Returns:
        详细的钓鱼推荐报告，包含天气分析和最佳钓鱼时间建议

    Examples:
        query_fishing_recommendation("杭州", "明天")
        query_fishing_recommendation("余杭区")
        query_fishing_recommendation("北京", "2024-12-25")
    """
    try:
        # 解析日期
        target_date = _parse_date_input(date)
        date_str = target_date.strftime('%Y-%m-%d')

        # 获取天气数据
        weather_data = _get_weather_data(location, target_date)
        if not weather_data:
            return f"❌ 抱歉，无法获取{location}在{date_str}的天气数据，请稍后重试。"

        # 计算钓鱼评分
        fishing_score = _calculate_fishing_score(weather_data)

        # 生成推荐报告
        return _generate_fishing_report(location, date_str, weather_data, fishing_score)

    except Exception as e:
        logger.error(f"钓鱼推荐分析失败: {str(e)}")
        return f"❌ 分析钓鱼推荐时发生错误: {str(e)}，请稍后重试。"




def _parse_date_input(date_input: str) -> datetime:
    """解析日期输入"""
    if not date_input:
        return datetime.now() + timedelta(days=1)  # 默认明天

    date_input = date_input.strip().lower()

    # 相对日期映射
    relative_dates = {
        'today': '今天', 'tomorrow': '明天', 'yesterday': '昨天',
        '今天': '今天', '明天': '明天', '昨天': '昨天', '后天': '后天'
    }

    if date_input in relative_dates:
        if date_input in ['today', '今天']:
            return datetime.now()
        elif date_input in ['tomorrow', '明天']:
            return datetime.now() + timedelta(days=1)
        elif date_input in ['yesterday', '昨天']:
            return datetime.now() - timedelta(days=1)
        elif date_input in ['后天']:
            return datetime.now() + timedelta(days=2)

    # 尝试解析绝对日期
    try:
        return datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        # 如果解析失败，默认明天
        return datetime.now() + timedelta(days=1)


def _get_weather_data(location: str, target_date: datetime) -> Optional[Dict[str, Any]]:
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
            # 今天：获取实时天气
            logger.info("获取实时天气数据")
            weather_data = weather_client.get_realtime_weather(longitude, latitude)
            if weather_data:
                return _extract_realtime_weather(weather_data)
            else:
                return None
        else:
            # 未来日期：获取预报数据
            days_diff = (target_date - today).days
            if 1 <= days_diff <= 3:
                # 获取72小时预报数据，确保覆盖未来3天
                hours_needed = days_diff * 24
                logger.info(f"获取{hours_needed}小时预报数据")

                hourly_data = weather_client.get_hourly_forecast(longitude, latitude, 72)
                if hourly_data:
                    return _extract_hourly_weather(hourly_data, target_date)
                else:
                    return None
            else:
                logger.warning(f"不支持查询{days_diff}天后的天气数据")
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

        # 直接使用正确的字段映射
        extracted_data = {
            'temperature': realtime.get('temperature'),
            'condition': realtime.get('skycon'),
            'wind_speed': realtime.get('wind', {}).get('speed'),
            'humidity': realtime.get('humidity'),
            'pressure': realtime.get('pressure'),
            'visibility': realtime.get('visibility'),
            'data_source': 'realtime',
            'data_quality': 'valid'
        }

        # 验证必需字段
        required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
        missing_fields = [field for field in required_fields if extracted_data.get(field) is None]

        if missing_fields:
            logger.warning(f"实时天气数据不完整，缺少字段: {missing_fields}")
            extracted_data['data_quality'] = 'incomplete'
            # 根据伦理要求，不编造数据，让上层逻辑处理
        else:
            logger.info("实时天气数据提取成功，所有必需字段都存在")

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
                    # 收集目标日期的数据
                    target_temps.append(temp_data['value'])
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
                        target_pressures.append(pressures[i]['value'])

            except Exception as e:
                logger.debug(f"处理小时数据失败: {e}")
                continue

        if not target_temps:
            logger.error(f"没有找到{target_date}的温度数据")
            return {}

        # 计算平均值/主要值
        avg_temp = sum(target_temps) / len(target_temps)

        # 获取主要天气状况（出现频率最高的）
        main_condition = max(set(target_conditions), key=target_conditions.count) if target_conditions else None

        # 计算平均风速、湿度、气压
        avg_wind_speed = sum(target_wind_speeds) / len(target_wind_speeds) if target_wind_speeds else None
        avg_humidity = sum(target_humidities) / len(target_humidities) if target_humidities else None
        avg_pressure = sum(target_pressures) / len(target_pressures) if target_pressures else None

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
            # 元数据
            'data_source': 'hourly_forecast',
            'data_quality': 'valid'
        }

        # 验证必需字段
        required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
        missing_fields = [field for field in required_fields if extracted_data.get(field) is None]

        if missing_fields:
            logger.warning(f"小时级天气数据不完整，缺少字段: {missing_fields}")
            extracted_data['data_quality'] = 'incomplete'
            # 根据伦理要求，不编造数据，让上层逻辑处理
        else:
            logger.info(f"小时级天气数据提取成功: 温度={avg_temp:.1f}°C, 天气={main_condition}")

        return extracted_data

    except Exception as e:
        logger.error(f"提取小时级天气数据失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return {}


def _parse_weather_response(weather_response: str, location: str) -> Dict[str, Any]:
    """解析天气响应为结构化数据 - 智能解析版本"""
    import re

    try:
        logger.debug(f"开始解析{location}的天气响应数据")

        # 数据质量跟踪
        parse_stats = {
            'total_lines': 0,
            'parsed_fields': 0,
            'failed_fields': 0,
            'errors': []
        }

        lines = weather_response.split('\n')
        parse_stats['total_lines'] = len(lines)

        # 初始化天气数据结构
        weather_data = {
            'temperature': None,
            'condition': None,
            'wind_speed': None,
            'humidity': None,
            'pressure': None,
            'visibility': None,
            'parse_quality': 'unknown'  # 数据质量标记
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 智能温度解析 - 支持多种格式
            if any(keyword in line for keyword in ['温度:', '气温:', '🌡️']):
                temp_value = _parse_temperature_value(line)
                if temp_value is not None:
                    weather_data['temperature'] = temp_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 温度解析成功: {temp_value}°C")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"温度解析失败: {line}")
                    logger.warning(f"⚠️ 温度解析失败: {line}")

            # 智能天气状况解析
            elif any(keyword in line for keyword in ['天气:', '天气状况:', '☁️']):
                condition_value = _parse_weather_condition(line)
                if condition_value:
                    weather_data['condition'] = condition_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 天气状况解析成功: {condition_value}")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"天气状况解析失败: {line}")

            # 智能湿度解析
            elif any(keyword in line for keyword in ['湿度:', '💧']):
                humidity_value = _parse_humidity_value(line)
                if humidity_value is not None:
                    weather_data['humidity'] = humidity_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 湿度解析成功: {humidity_value}%")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"湿度解析失败: {line}")

            # 智能风速解析
            elif any(keyword in line for keyword in ['风速:', '风力:', '💨']):
                wind_value = _parse_wind_speed_value(line)
                if wind_value is not None:
                    weather_data['wind_speed'] = wind_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 风速解析成功: {wind_value} m/s")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"风速解析失败: {line}")

            # 智能气压解析
            elif any(keyword in line for keyword in ['气压:', '🌀']):
                pressure_value = _parse_pressure_value(line)
                if pressure_value is not None:
                    weather_data['pressure'] = pressure_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 气压解析成功: {pressure_value} hPa")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"气压解析失败: {line}")

        # 数据验证和质量检查
        weather_data = _validate_weather_data(weather_data, location)
        weather_data['parse_stats'] = parse_stats

        # 记录解析质量
        success_rate = parse_stats['parsed_fields'] / max(1, parse_stats['parsed_fields'] + parse_stats['failed_fields'])
        if success_rate >= 0.8:
            weather_data['parse_quality'] = 'excellent'
        elif success_rate >= 0.6:
            weather_data['parse_quality'] = 'good'
        elif success_rate >= 0.4:
            weather_data['parse_quality'] = 'fair'
        else:
            weather_data['parse_quality'] = 'poor'

        logger.info(f"📊 {location}天气数据解析完成: 质量={weather_data['parse_quality']}, "
                   f"成功={parse_stats['parsed_fields']}, 失败={parse_stats['failed_fields']}")

        return weather_data

    except Exception as e:
        logger.error(f"💥 解析{location}天气响应时发生严重错误: {str(e)}")
        # 返回明确标记为失败的数据
        return {
            'temperature': None,
            'condition': None,
            'wind_speed': None,
            'humidity': None,
            'pressure': None,
            'visibility': None,
            'parse_quality': 'failed',
            'error': str(e),
            'location': location
        }


def _parse_temperature_value(line: str) -> Optional[float]:
    """智能解析温度值 - 支持多种格式"""
    import re

    try:
        # 正则表达式匹配各种温度格式 - 注意顺序很重要，范围模式必须在前面
        patterns = [
            r'温度范围[:：]\s*([-+]?\d*\.?\d+)\s*°?[CF]?\s*[~～至-]\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 温度范围: 18°C - 25°C
            r'温度[:：]\s*([-+]?\d*\.?\d+)\s*°?[CF]?\s*[~～至-]\s*([-+]?\d*\.?\d+)\s*°?[CF]?\s*\(.*?平均.*?([-+]?\d*\.?\d+).*?\)',  # 温度: 14.1°C ~ 3.4°C (平均8.0°C)
            r'温度[:：]\s*([-+]?\d*\.?\d+)\s*°?[CF]?\s*[~～至-]\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 温度: 18°C - 25°C
            r'气温[:：]\s*([-+]?\d*\.?\d+)\s*°?[CF]?\s*[~～至-]\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 气温: 18°C - 25°C
            r'([-+]?\d*\.?\d+)\s*°?[CF]?\s*[~～至-]\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 18°C - 25°C
            r'(最高|最低)[温度][:：]\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 最高温度: 25°C
            r'温度[:：]\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 温度: 25°C
            r'气温[:：]\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 气温: 25°C
            r'🌡️\s*([-+]?\d*\.?\d+)\s*°?[CF]?',  # 🌡️ 25°C
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    # 带平均值的温度范围: 温度: 14.1°C ~ 3.4°C (平均8.0°C)
                    temp1, temp2, avg_temp = float(groups[0]), float(groups[1]), float(groups[2])
                    logger.debug(f"🌡️ 解析温度范围(带平均值): {temp1}°C ~ {temp2}°C, 平均: {avg_temp}°C")
                    return avg_temp
                elif len(groups) == 2:
                    # 温度范围情况 - 取平均值
                    temp1, temp2 = float(groups[0]), float(groups[1])
                    avg_temp = (temp1 + temp2) / 2
                    logger.debug(f"🌡️ 解析温度范围: {temp1}°C ~ {temp2}°C, 平均: {avg_temp}°C")
                    return avg_temp
                elif len(groups) == 1:
                    # 单个温度值
                    temp = float(groups[0])
                    logger.debug(f"🌡️ 解析单点温度: {temp}°C")
                    return temp
                else:
                    # 检查是否是范围情况的第一个值
                    if groups and any(g is not None for g in groups):
                        temps = [float(g) for g in groups if g is not None]
                        if len(temps) == 2:
                            avg_temp = sum(temps) / len(temps)
                            logger.debug(f"🌡️ 解析温度范围(复杂): {temps[0]}°C ~ {temps[1]}°C, 平均: {avg_temp}°C")
                            return avg_temp
                        elif len(temps) == 1:
                            logger.debug(f"🌡️ 解析单点温度(复杂): {temps[0]}°C")
                            return temps[0]

        logger.debug(f"🌡️ 温度解析失败，无匹配模式: {line}")
        return None

    except Exception as e:
        logger.debug(f"🌡️ 温度解析异常: {line}, 错误: {e}")
        return None


def _parse_weather_condition(line: str) -> Optional[str]:
    """智能解析天气状况"""
    import re

    try:
        # 清理emoji和特殊字符
        clean_line = re.sub(r'[🌤️☁️🌧️⛈️❄️🌞]', '', line).strip()

        patterns = [
            r'天气[:：]\s*([^\n\r]+)',  # 天气: 多云
            r'天气状况[:：]\s*([^\n\r]+)',  # 天气状况: 多云转晴
            r'☁️\s*([^\n\r]+)',  # ☁️ 多云
            r'^(晴|多云|阴|小雨|中雨|大雨|暴雨|雷阵雨|雪|雾|霾)',  # 直接匹配天气状态
        ]

        for pattern in patterns:
            match = re.search(pattern, clean_line, re.IGNORECASE)
            if match:
                condition = match.group(1).strip()
                # 清理可能的多余信息
                condition = re.sub(r'\s*(,|，)\s*.*$', '', condition)  # 移除逗号后的内容
                condition = re.sub(r'\s*\(\s*[^)]*\s*\)\s*$', '', condition)  # 移除括号内容

                if condition and len(condition) > 0:
                    logger.debug(f"☁️ 解析天气状况: {condition}")
                    return condition

        logger.debug(f"☁️ 天气状况解析失败: {line}")
        return None

    except Exception as e:
        logger.debug(f"☁️ 天气状况解析异常: {line}, 错误: {e}")
        return None


def _parse_humidity_value(line: str) -> Optional[float]:
    """智能解析湿度值"""
    import re

    try:
        patterns = [
            r'湿度[:：]\s*([-+]?\d*\.?\d+)\s*%?',  # 湿度: 65%
            r'💧\s*([-+]?\d*\.?\d+)\s*%?',  # 💧 65%
            r'相对湿度[:：]\s*([-+]?\d*\.?\d+)\s*%?',  # 相对湿度: 65%
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                humidity = float(match.group(1))
                # 合理性检查
                if 0 <= humidity <= 100:
                    logger.debug(f"💧 解析湿度: {humidity}%")
                    return humidity
                else:
                    logger.warning(f"💧 湿度值不合理: {humidity}%")

        logger.debug(f"💧 湿度解析失败: {line}")
        return None

    except Exception as e:
        logger.debug(f"💧 湿度解析异常: {line}, 错误: {e}")
        return None


def _parse_wind_speed_value(line: str) -> Optional[float]:
    """智能解析风速值"""
    import re

    try:
        patterns = [
            r'风速[:：]\s*([-+]?\d*\.?\d+)\s*(m/s|km/h|mph|节|级)?',  # 风速: 5 m/s
            r'风力[:：]\s*([-+]?\d*\.?\d+)\s*(m/s|km/h|mph|节|级)?',  # 风力: 5 m/s
            r'💨\s*([-+]?\d*\.?\d+)\s*(m/s|km/h|mph|节|级)?',  # 💨 5 m/s
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                wind_speed = float(match.group(1))
                unit = match.group(2) or 'm/s'

                # 单位转换到m/s
                if unit == 'km/h':
                    wind_speed = wind_speed / 3.6
                elif unit == 'mph':
                    wind_speed = wind_speed * 0.44704
                elif unit == '节':
                    wind_speed = wind_speed * 0.514444
                elif unit == '级':
                    # 风级转换 (简化版)
                    wind_level_map = {
                        0: 0, 1: 0.3, 2: 1.6, 3: 3.4, 4: 5.5, 5: 8.0,
                        6: 10.8, 7: 13.9, 8: 17.2, 9: 20.8, 10: 24.5, 11: 28.5, 12: 32.7
                    }
                    wind_level = int(wind_speed)
                    wind_speed = wind_level_map.get(wind_level, wind_speed)

                # 合理性检查
                if 0 <= wind_speed <= 50:  # 最大50m/s
                    logger.debug(f"💨 解析风速: {wind_speed} m/s (原值: {match.group(1)} {unit})")
                    return wind_speed
                else:
                    logger.warning(f"💨 风速值不合理: {wind_speed} m/s")

        logger.debug(f"💨 风速解析失败: {line}")
        return None

    except Exception as e:
        logger.debug(f"💨 风速解析异常: {line}, 错误: {e}")
        return None


def _parse_pressure_value(line: str) -> Optional[float]:
    """智能解析气压值"""
    import re

    try:
        patterns = [
            r'气压[:：]\s*([-+]?\d*\.?\d+)\s*(hPa|mb|mmHg|kPa)?',  # 气压: 1013 hPa
            r'🌀\s*([-+]?\d*\.?\d+)\s*(hPa|mb|mmHg|kPa)?',  # 🌀 1013 hPa
            r'大气压(?:强)?[:：]\s*([-+]?\d*\.?\d+)\s*(hPa|mb|mmHg|kPa)?',  # 大气压强: 1013 hPa
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                pressure = float(match.group(1))
                unit = match.group(2) or 'hPa'

                # 单位转换到hPa
                if unit == 'mmHg':
                    pressure = pressure * 1.33322
                elif unit == 'kPa':
                    pressure = pressure * 10
                elif unit == 'mb':
                    pressure = pressure  # mb == hPa

                # 合理性检查
                if 800 <= pressure <= 1100:  # 合理的气压范围
                    logger.debug(f"🌀 解析气压: {pressure} hPa (原值: {match.group(1)} {unit})")
                    return pressure
                else:
                    logger.warning(f"🌀 气压值不合理: {pressure} hPa")

        logger.debug(f"🌀 气压解析失败: {line}")
        return None

    except Exception as e:
        logger.debug(f"🌀 气压解析异常: {line}, 错误: {e}")
        return None


def _validate_weather_data(weather_data: Dict[str, Any], location: str) -> Dict[str, Any]:
    """验证天气数据的合理性"""
    validation_errors = []

    # 温度验证
    if weather_data.get('temperature') is not None:
        temp = weather_data['temperature']
        if not (-50 <= temp <= 60):  # 地球表面合理温度范围
            validation_errors.append(f"温度值不合理: {temp}°C")
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
        if not (800 <= pressure <= 1100):  # 合理的气压范围
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


def _calculate_fishing_score(weather_data: Dict[str, Any]) -> Dict[str, float]:
    """计算钓鱼评分 - 严格模式，不使用虚假数据"""

    # 严格验证天气数据完整性
    required_fields = ['temperature', 'condition', 'wind_speed', 'humidity', 'pressure']
    missing_fields = [field for field in required_fields if weather_data.get(field) is None]

    if missing_fields:
        logger.error(f"天气数据不完整，缺少字段: {missing_fields}")
        logger.error(f"现有数据: {weather_data}")
        # 返回所有0分，表示无法计算
        return {
            'overall': 0.0,
            'temperature': 0.0,
            'condition': 0.0,
            'wind': 0.0,
            'humidity': 0.0,
            'pressure': 0.0,
            'data_quality': 'incomplete'
        }

    # 验证数据的合理性
    temp = weather_data['temperature']
    if not isinstance(temp, (int, float)) or temp < -50 or temp > 60:
        logger.error(f"温度数据异常: {temp}")
        return {
            'overall': 0.0, 'temperature': 0.0, 'condition': 0.0, 'wind': 0.0,
            'humidity': 0.0, 'pressure': 0.0, 'data_quality': 'invalid'
        }

    # 获取验证过的数据
    condition = weather_data['condition']
    wind = weather_data['wind_speed']
    humidity = weather_data['humidity']
    pressure = weather_data['pressure']

    logger.info(f"使用验证过的天气数据: 温度={temp}°C, 天气={condition}, 风速={wind}m/s")

    # 各维度评分
    temp_score = _calc_temp_score(temp)
    weather_score = _calc_weather_score(condition)
    wind_score = _calc_wind_score(wind)
    humidity_score = _calc_humidity_score(humidity)
    pressure_score = _calc_pressure_score(pressure)

    # 综合评分（权重分配）
    weights = {
        'temperature': 0.25,
        'weather': 0.30,
        'wind': 0.20,
        'humidity': 0.15,
        'pressure': 0.10
    }

    overall_score = (
        temp_score * weights['temperature'] +
        weather_score * weights['weather'] +
        wind_score * weights['wind'] +
        humidity_score * weights['humidity'] +
        pressure_score * weights['pressure']
    )

    return {
        'overall': overall_score,
        'temperature': temp_score,
        'weather': weather_score,
        'wind': wind_score,
        'humidity': humidity_score,
        'pressure': pressure_score
    }


def _calculate_hourly_scores(weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    按小时计算钓鱼评分

    Args:
        weather_data: 包含hourly数据数组的天气数据

    Returns:
        24小时评分列表，每项包含小时、时间、评分和天气详情
    """
    try:
        # 检查是否有小时数据
        if not weather_data.get('has_hourly_data', False):
            logger.warning("没有hourly数据，无法计算小时评分")
            return []

        hourly_temps = weather_data.get('hourly_temps', [])
        hourly_conditions = weather_data.get('hourly_conditions', [])
        hourly_wind_speeds = weather_data.get('hourly_wind_speeds', [])
        hourly_humidities = weather_data.get('hourly_humidities', [])
        hourly_pressures = weather_data.get('hourly_pressures', [])
        hourly_datetimes = weather_data.get('hourly_datetimes', [])

        # 验证数据完整性
        data_length = len(hourly_temps)
        if data_length == 0:
            logger.error("hourly_temps为空")
            return []

        hourly_scores = []

        # 权重配置（与日评分保持一致）
        weights = {
            'temperature': 0.25,
            'weather': 0.30,
            'wind': 0.20,
            'humidity': 0.15,
            'pressure': 0.10
        }

        # 遍历每个小时
        for i in range(data_length):
            try:
                # 获取该小时的天气数据
                temp = hourly_temps[i] if i < len(hourly_temps) else None
                condition = hourly_conditions[i] if i < len(hourly_conditions) else None
                wind_speed = hourly_wind_speeds[i] if i < len(hourly_wind_speeds) else None
                humidity = hourly_humidities[i] if i < len(hourly_humidities) else None
                pressure = hourly_pressures[i] if i < len(hourly_pressures) else None
                dt = hourly_datetimes[i] if i < len(hourly_datetimes) else None

                # 验证必需字段
                if None in [temp, condition, wind_speed, humidity, pressure]:
                    logger.debug(f"第{i}小时数据不完整，跳过")
                    continue

                # 计算各维度评分（复用现有函数）
                temp_score = _calc_temp_score(temp)
                weather_score = _calc_weather_score(condition)
                wind_score = _calc_wind_score(wind_speed)
                humidity_score = _calc_humidity_score(humidity)
                pressure_score = _calc_pressure_score(pressure)

                # 计算综合评分
                overall_score = (
                    temp_score * weights['temperature'] +
                    weather_score * weights['weather'] +
                    wind_score * weights['wind'] +
                    humidity_score * weights['humidity'] +
                    pressure_score * weights['pressure']
                )

                # 构建该小时的评分记录
                hour_score = {
                    'hour': i,
                    'datetime': dt,
                    'time_str': dt.strftime('%H:%M') if dt else f'{i}:00',
                    'score': overall_score,
                    'temperature': temp,
                    'condition': condition,
                    'wind_speed': wind_speed,
                    'humidity': humidity,
                    'pressure': pressure,
                    'scores': {
                        'temperature': temp_score,
                        'weather': weather_score,
                        'wind': wind_score,
                        'humidity': humidity_score,
                        'pressure': pressure_score
                    }
                }

                hourly_scores.append(hour_score)

            except Exception as e:
                logger.warning(f"计算第{i}小时评分失败: {e}")
                continue

        logger.info(f"成功计算{len(hourly_scores)}个小时的钓鱼评分")
        return hourly_scores

    except Exception as e:
        logger.error(f"按小时计算评分失败: {e}")
        return []


def _find_best_time_slots(hourly_scores: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    """
    智能检测最佳钓鱼时段（灵活时段长度）

    Args:
        hourly_scores: 24小时评分列表
        top_n: 返回top N个时段，默认3个

    Returns:
        最佳时段列表，每项包含时段范围、评分、天气摘要等
    """
    try:
        if not hourly_scores:
            logger.warning("hourly_scores为空，无法检测最佳时段")
            return []

        # 准备候选时段列表
        candidate_slots = []

        # 使用滑动窗口检测连续高分时段（窗口大小1-4小时）
        for window_size in range(1, 5):  # 1-4小时
            for start_idx in range(len(hourly_scores) - window_size + 1):
                end_idx = start_idx + window_size

                # 获取窗口内的评分
                window_scores = hourly_scores[start_idx:end_idx]

                # 计算窗口平均评分
                avg_score = sum(h['score'] for h in window_scores) / len(window_scores)

                # 获取时间范围
                start_time = window_scores[0]['time_str']
                end_hour = window_scores[-1]['hour'] + 1
                end_time = f"{end_hour:02d}:00" if end_hour < 24 else "24:00"

                # 获取窗口内的平均天气数据
                avg_temp = sum(h['temperature'] for h in window_scores) / len(window_scores)
                avg_wind = sum(h['wind_speed'] for h in window_scores) / len(window_scores)
                avg_humidity = sum(h['humidity'] for h in window_scores) / len(window_scores)
                avg_pressure = sum(h['pressure'] for h in window_scores) / len(window_scores)

                # 获取主要天气状况（出现频率最高的）
                conditions = [h['condition'] for h in window_scores]
                main_condition = max(set(conditions), key=conditions.count)

                # 构建候选时段
                slot = {
                    'start_hour': start_idx,
                    'end_hour': end_idx,
                    'start_time': start_time,
                    'end_time': end_time,
                    'time_range': f"{start_time}-{end_time}",
                    'duration_hours': window_size,
                    'avg_score': avg_score,
                    'temperature': avg_temp,
                    'condition': main_condition,
                    'wind_speed': avg_wind,
                    'humidity': avg_humidity,
                    'pressure': avg_pressure
                }

                candidate_slots.append(slot)

        # 按平均评分降序排序
        candidate_slots.sort(key=lambda x: x['avg_score'], reverse=True)

        # 选择top N个不重叠的时段
        selected_slots = []
        used_hours = set()

        for slot in candidate_slots:
            # 检查是否与已选时段重叠
            slot_hours = set(range(slot['start_hour'], slot['end_hour']))
            if not slot_hours.intersection(used_hours):
                selected_slots.append(slot)
                used_hours.update(slot_hours)

                if len(selected_slots) >= top_n:
                    break

        # 按时间顺序排序（早到晚）
        selected_slots.sort(key=lambda x: x['start_hour'])

        logger.info(f"成功检测{len(selected_slots)}个最佳钓鱼时段")
        return selected_slots

    except Exception as e:
        logger.error(f"智能时段检测失败: {e}")
        return []


def _generate_score_trend(hourly_scores: List[Dict[str, Any]]) -> str:
    """
    生成24小时评分趋势ASCII可视化图

    Args:
        hourly_scores: 24小时评分列表

    Returns:
        ASCII趋势图字符串
    """
    try:
        if not hourly_scores:
            return "无评分数据"

        # 提取评分
        scores = [h['score'] for h in hourly_scores]
        hours = [h['time_str'] for h in hourly_scores]

        # 计算统计信息
        max_score = max(scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)

        # 构建趋势图
        chart = []
        chart.append("📊 24小时钓鱼评分趋势")
        chart.append("=" * 50)
        chart.append("")

        # 评分刻度（10个等级，从0到100）
        height = 10  # 图表高度
        width = len(scores)  # 图表宽度

        # 绘制图表主体
        for level in range(height, 0, -1):
            score_threshold = (level / height) * 100
            line = f"{int(score_threshold):3d} ┃ "

            for score in scores:
                if score >= score_threshold:
                    line += "█"
                else:
                    line += " "

            chart.append(line)

        # 绘制底部分隔线
        chart.append("    ┗" + "━" * width)

        # 绘制时间轴（简化版：只显示关键时刻）
        time_axis = "      "
        for i, hour_str in enumerate(hours):
            if i % 4 == 0:  # 每4小时显示一次
                hour = hour_str.split(':')[0]
                time_axis += f"{hour:2s}  "

        chart.append(time_axis + " (时)")
        chart.append("")

        # 添加统计信息
        chart.append(f"📈 统计数据:")
        chart.append(f"   最高评分: {max_score:.1f}分")
        chart.append(f"   最低评分: {min_score:.1f}分")
        chart.append(f"   平均评分: {avg_score:.1f}分")
        chart.append("")

        return "\n".join(chart)

    except Exception as e:
        logger.error(f"生成评分趋势图失败: {e}")
        return f"评分趋势图生成失败: {str(e)}"


def _calc_temp_score(temp: float) -> float:
    """温度评分"""
    if 15 <= temp <= 25:
        return 95.0
    elif 12 <= temp < 15 or 25 < temp <= 28:
        return 80.0
    elif 8 <= temp < 12 or 28 < temp <= 32:
        return 60.0
    else:
        return 30.0


def _calc_weather_score(condition: str) -> float:
    """天气状况评分"""
    if condition in ['多云', '阴', '小雨']:
        return 95.0
    elif condition in ['晴', '雾']:
        return 80.0
    elif condition in ['中雨']:
        return 50.0
    elif condition in ['大雨', '暴雨']:
        return 20.0
    else:
        return 70.0


def _calc_wind_score(wind: float) -> float:
    """风力评分"""
    # 假设输入是m/s
    if wind < 3:  # < 11 km/h
        return 95.0
    elif wind < 6:  # < 22 km/h
        return 80.0
    elif wind < 8:  # < 29 km/h
        return 50.0
    else:
        return 25.0


def _calc_humidity_score(humidity: float) -> float:
    """湿度评分"""
    if 50 <= humidity <= 70:
        return 90.0
    elif 40 <= humidity < 50 or 70 < humidity <= 80:
        return 75.0
    elif 30 <= humidity < 40 or 80 < humidity <= 90:
        return 60.0
    else:
        return 40.0


def _calc_pressure_score(pressure: float) -> float:
    """气压评分"""
    if 1000 <= pressure <= 1020:
        return 90.0
    elif 990 <= pressure < 1000 or 1020 < pressure <= 1030:
        return 75.0
    else:
        return 55.0


def _generate_fishing_report(location: str, date: str, weather_data: Dict[str, Any], scores: Dict[str, float]) -> str:
    """生成钓鱼推荐报告（支持24小时智能时段推荐）"""
    overall_score = scores.get('overall', 0.0)
    data_quality = scores.get('data_quality', 'unknown')

    # 检查数据质量 - 如果数据无效或评分过低，返回错误信息
    if data_quality in ['incomplete', 'invalid'] or overall_score == 0.0:
        logger.error(f"无法生成钓鱼推荐报告 - 数据质量: {data_quality}, 评分: {overall_score}")
        return f"""❌ 抱歉，无法生成{location}在{date}的钓鱼推荐报告。

**原因**: 天气数据获取不完整或验证失败
- 详细错误: 数据质量为"{data_quality}"
- 系统状态: 无法提供可靠的钓鱼建议

**建议**:
- 请稍后重试，确保天气服务正常
- 如需帮助，请提供具体地点和时间
- 避免在不明确的天气条件下进行钓鱼活动

*出于数据准确性考虑，我们不提供基于虚假或推测信息的钓鱼建议。*"""

    # 🆕 检测是否有hourly数据，尝试生成智能时段推荐
    hourly_scores = []
    best_time_slots = []
    score_trend = ""
    has_hourly_data = weather_data.get('has_hourly_data', False)

    if has_hourly_data:
        try:
            logger.info("检测到hourly数据，开始生成智能时段推荐")

            # 计算24小时评分
            hourly_scores = _calculate_hourly_scores(weather_data)

            if hourly_scores:
                # 检测最佳时段
                best_time_slots = _find_best_time_slots(hourly_scores, top_n=3)

                # 生成评分趋势图
                score_trend = _generate_score_trend(hourly_scores)

                logger.info(f"智能时段推荐生成成功: {len(best_time_slots)}个时段")
            else:
                logger.warning("hourly评分计算失败，将使用默认推荐")

        except Exception as e:
            logger.error(f"智能时段推荐生成失败: {e}")
            # 失败时不影响基础报告生成

    # 确定推荐等级
    if overall_score >= 85:
        grade = "🌟 优秀"
        recommendation = "非常适合钓鱼，是出钓的好时机"
        time_advice = "清晨5-9点和傍晚18-21点是最佳时段"
    elif overall_score >= 70:
        grade = "👍 良好"
        recommendation = "适合钓鱼，条件较好"
        time_advice = "建议选择清晨或傍晚时段"
    elif overall_score >= 55:
        grade = "👌 一般"
        recommendation = "可以钓鱼，需选择合适时机和钓点"
        time_advice = "建议早晚时段，避开正午"
    else:
        grade = "👎 较差"
        recommendation = "不太适合钓鱼，建议改期"
        time_advice = "如需钓鱼，建议选择有遮蔽的钓位"

    # 生成报告
    report = f"🎣 {location} 钓鱼推荐报告 ({date})\n"
    report += "=" * 50 + "\n\n"

    # 🆕 低分天气警告提示（用户选择的"标注相对最佳"）
    if overall_score < 60:
        report += "⚠️ **天气条件提示**\n"
        report += f"整体天气评分较低 ({overall_score:.1f}分)，不太适合钓鱼。\n"
        if best_time_slots:
            report += "以下为相对最佳时段，仅供参考，建议谨慎出钓。\n\n"
        else:
            report += "建议改期或选择更合适的天气条件。\n\n"

    # 综合推荐
    report += f"🏆 **综合评分**: {overall_score:.1f}/100 {grade}\n"
    report += f"📝 **推荐建议**: {recommendation}\n"

    # 🆕 如果有智能时段推荐，优先展示
    if best_time_slots:
        report += f"\n⏰ **智能推荐时段** (基于24小时数据分析):\n\n"

        # 排名emoji
        rank_emojis = ['🥇', '🥈', '🥉']

        for i, slot in enumerate(best_time_slots):
            emoji = rank_emojis[i] if i < len(rank_emojis) else f"{i+1}."
            report += f"{emoji} **第{i+1}推荐**: {slot['time_range']} (评分: {slot['avg_score']:.1f}分)\n"
            report += f"   • 温度: {slot['temperature']:.1f}°C | 天气: {slot['condition']} | 风速: {slot['wind_speed']:.1f}m/s\n"
            report += f"   • 湿度: {slot['humidity']:.1f}% | 气压: {slot['pressure']:.1f} hPa\n"

            # 添加推荐理由
            reasons = []
            if slot['avg_score'] >= 80:
                if 15 <= slot['temperature'] <= 25:
                    reasons.append("温度适宜")
                if slot['wind_speed'] < 3:
                    reasons.append("风力较小")
                if 50 <= slot['humidity'] <= 70:
                    reasons.append("湿度理想")
            elif slot['avg_score'] >= 60:
                reasons.append("相对较好的时段")
            else:
                reasons.append("整体条件差，此为相对最佳")

            if reasons:
                report += f"   • 推荐理由: {', '.join(reasons)}\n"

            report += "\n"
    else:
        # 没有智能时段数据时，使用默认建议
        report += f"⏰ **最佳时段**: {time_advice}\n\n"

    # 天气条件
    report += f"🌤️ **天气条件**:\n"
    report += f"• 🌡️ 温度: {weather_data['temperature']}°C\n"
    report += f"• ☁️ 天气: {weather_data['condition']}\n"
    report += f"• 💨 风速: {weather_data['wind_speed']} m/s\n"
    report += f"• 💧 湿度: {weather_data['humidity']}%\n"
    report += f"• 🌀 气压: {weather_data['pressure']} hPa\n\n"

    # 各维度评分
    report += f"📊 **详细评分**:\n"
    report += f"• 🌡️ 温度评分: {scores['temperature']:.1f}/100\n"
    report += f"• ☁️ 天气评分: {scores['weather']:.1f}/100\n"
    report += f"• 💨 风力评分: {scores['wind']:.1f}/100\n"
    report += f"• 💧 湿度评分: {scores['humidity']:.1f}/100\n"
    report += f"• 🌀 气压评分: {scores['pressure']:.1f}/100\n\n"

    # 钓鱼建议
    report += f"💡 **钓鱼建议**:\n"
    report += _add_fishing_suggestions(scores)

    # 装备建议
    report += f"\n🎒 **装备建议**:\n"
    report += _add_equipment_suggestions(weather_data)

    # 🆕 添加24小时评分趋势图（如果有）
    if score_trend:
        report += f"\n{score_trend}\n"

    return report


def _add_fishing_suggestions(scores: Dict[str, float]) -> str:
    """添加钓鱼建议"""
    suggestions = ""

    if scores['temperature'] >= 80:
        suggestions += "• ✅ 温度适宜，鱼类活跃度较高\n"
    elif scores['temperature'] >= 60:
        suggestions += "• ⚠️ 温度一般，建议选择深水区或遮荫处\n"
    else:
        suggestions += "• ❌ 温度不佳，鱼类活动较少\n"

    if scores['weather'] >= 80:
        suggestions += "• ✅ 天气条件良好，适合钓鱼\n"
    else:
        suggestions += "• ⚠️ 天气一般，注意防护\n"

    if scores['wind'] >= 80:
        suggestions += "• ✅ 风平浪静，利于作钓\n"
    elif scores['wind'] >= 60:
        suggestions += "• ⚠️ 风力适中，注意抛竿技巧\n"
    else:
        suggestions += "• ❌ 风力较大，建议选择避风钓位\n"

    return suggestions


def _add_equipment_suggestions(weather_data: Dict[str, Any]) -> str:
    """添加装备建议"""
    suggestions = ""

    if weather_data.get('condition', '').startswith('晴'):
        suggestions += "• 建议携带防晒装备和遮阳帽\n"
    elif '雨' in weather_data.get('condition', ''):
        suggestions += "• 建议携带雨具，选择有遮挡的钓位\n"

    if weather_data.get('temperature', 20) < 15:
        suggestions += "• 建议携带保暖衣物\n"
    elif weather_data.get('temperature', 20) > 28:
        suggestions += "• 建议携带充足的饮水\n"

    return suggestions


def _generate_detailed_analysis(weather_data: Dict[str, Any], scores: Dict[str, float]) -> str:
    """生成详细分析"""
    analysis = ""

    # 温度分析
    temp = weather_data['temperature']
    if scores['temperature'] >= 80:
        analysis += f"• 温度{temp}°C处于鱼类活跃范围，新陈代谢旺盛，觅食积极\n"
    elif scores['temperature'] >= 60:
        analysis += f"• 温度{temp}°C一般，鱼类活跃度适中，需要选择合适钓点\n"
    else:
        analysis += f"• 温度{temp}°C偏低或偏高，鱼类活跃度下降，需要调整策略\n"

    # 天气分析
    analysis += f"• 天气{weather_data['condition']}，"

    # 风力分析
    wind_speed = weather_data['wind_speed']
    if scores['wind'] >= 80:
        analysis += f"风力{wind_speed}m/s较小，抛竿精准，观漂容易\n"
    elif scores['wind'] >= 60:
        analysis += f"风力{wind_speed}m/s适中，注意抛竿角度和钓组选择\n"
    else:
        analysis += f"风力{wind_speed}m/s较大，建议选择避风钓位或加重钓组\n"

    # 湿度和气压分析
    analysis += f"• 湿度{weather_data['humidity']}%，气压{weather_data['pressure']}hPa，"

    if scores['humidity'] >= 75 and scores['pressure'] >= 75:
        analysis += "空气湿润且气压稳定，有利于鱼类觅食\n"
    else:
        analysis += "需要注意天气变化对鱼类活动的影响\n"

    return analysis


# 工具列表，用于agent创建
FISHING_TOOLS = [
    query_fishing_recommendation
]