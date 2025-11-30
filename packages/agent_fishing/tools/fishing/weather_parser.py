#!/usr/bin/env python3
"""
天气数据解析模块

职责:
- 解析天气API响应文本
- 提取温度、天气状态、湿度、风速、气压等字段
- 处理多种数据格式(数字、字符串、单位符号)
"""

from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


def parse_weather_response(weather_response: str, location: str) -> Dict[str, Any]:
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
                temp_value = parse_temperature_value(line)
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
                condition_value = parse_weather_condition(line)
                if condition_value:
                    weather_data['condition'] = condition_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 天气状况解析成功: {condition_value}")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"天气状况解析失败: {line}")

            # 智能湿度解析
            elif any(keyword in line for keyword in ['湿度:', '💧']):
                humidity_value = parse_humidity_value(line)
                if humidity_value is not None:
                    weather_data['humidity'] = humidity_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 湿度解析成功: {humidity_value}%")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"湿度解析失败: {line}")

            # 智能风速解析
            elif any(keyword in line for keyword in ['风速:', '风力:', '💨']):
                wind_value = parse_wind_speed_value(line)
                if wind_value is not None:
                    weather_data['wind_speed'] = wind_value
                    parse_stats['parsed_fields'] += 1
                    logger.debug(f"✅ 风速解析成功: {wind_value} m/s")
                else:
                    parse_stats['failed_fields'] += 1
                    parse_stats['errors'].append(f"风速解析失败: {line}")

            # 智能气压解析
            elif any(keyword in line for keyword in ['气压:', '🌀']):
                pressure_value = parse_pressure_value(line)
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


def parse_temperature_value(line: str) -> Optional[float]:
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


def parse_weather_condition(line: str) -> Optional[str]:
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


def parse_humidity_value(line: str) -> Optional[float]:
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


def parse_wind_speed_value(line: str) -> Optional[float]:
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


def parse_pressure_value(line: str) -> Optional[float]:
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
                if 500 <= pressure <= 1100:  # 合理的气压范围
                    logger.debug(f"🌀 解析气压: {pressure} hPa (原值: {match.group(1)} {unit})")
                    return pressure
                else:
                    logger.warning(f"🌀 气压值不合理: {pressure} hPa")

        logger.debug(f"🌀 气压解析失败: {line}")
        return None

    except Exception as e:
        logger.debug(f"🌀 气压解析异常: {line}, 错误: {e}")
        return None

