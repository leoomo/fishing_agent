#!/usr/bin/env python3
"""
钓鱼推荐工具模块
独立的钓鱼时间推荐功能，不依赖core层，使用正确的LangChain @tool模式
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)


@tool
def query_fishing_recommendation(
    location: str,
    date: str = None
) -> str:
    """查询钓鱼时间推荐，基于天气条件分析最佳的钓鱼时间

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

        # 获取真实天气数据
        weather_data = _get_weather_data(location, target_date)

        # 计算钓鱼评分
        fishing_score = _calculate_fishing_score(weather_data)

        # 生成推荐报告
        return _generate_fishing_report(location, date_str, weather_data, fishing_score)

    except Exception as e:
        logger.error(f"钓鱼推荐分析失败: {str(e)}")
        # 诚实地告知用户无法获取天气数据
        return f"""
❌ 抱歉，无法获取{location}在{date_str}的天气数据。

**具体原因**: {str(e)}

**建议**:
1. 请检查网络连接是否正常
2. 稍后重试
3. 尝试查询其他主要城市的天气情况
4. 使用其他天气应用确认当地天气状况后，再进行钓鱼决策

⚠️ 我们不会提供模拟或虚假的天气数据来误导您的钓鱼决策。真实准确的天气信息对安全的钓鱼活动至关重要。

请稍后重试以获取基于真实天气数据的专业钓鱼建议。
        """.strip()


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


def _get_weather_data(location: str, date: datetime) -> Dict[str, Any]:
    """获取真实的天气数据"""
    try:
        # 导入服务管理器获取天气服务
        from src.services.service_manager import get_weather_service
        weather_service = get_weather_service()

        # 使用天气服务获取真实数据
        date_str = date.strftime('%Y-%m-%d')
        result, message, status = weather_service.get_weather_by_date(location, date_str)

        if result and status in [0, 1]:  # 成功获取数据（0=API成功，1=缓存命中）
            # 转换EnhancedWeatherData到标准格式
            weather_data = {
                'temperature': result.temperature,  # °C
                'condition': _extract_weather_condition(result),  # 天气状况
                'wind_speed': _convert_wind_speed(result.wind_speed),  # 转换为km/h
                'humidity': _convert_humidity(result.humidity),  # 转换为百分比
                'pressure': _convert_pressure(result.pressure),  # 转换为hPa
                'visibility': getattr(result, 'visibility', 10.0)  # 能见度 km
            }

            logger.info(f"✅ 成功获取{location}的天气数据: {weather_data['temperature']:.1f}°C, {weather_data['condition']}")
            return weather_data
        else:
            error_msg = f"无法获取{location}的天气数据: {message} (状态码: {status})"
            logger.warning(f"⚠️ {error_msg}")
            raise ValueError(error_msg)

    except Exception as e:
        error_msg = f"获取天气数据失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)


def _extract_weather_condition(weather_data) -> str:
    """从天气数据中提取天气状况"""
    # 尝试多种可能的字段
    if hasattr(weather_data, 'description'):
        # 描述可能包含更多信息，提取前面的天气状况
        desc = weather_data.description
        if '，' in desc:
            return desc.split('，')[0]  # 取逗号前的部分
        return desc
    elif hasattr(weather_data, 'condition'):
        return weather_data.condition
    elif hasattr(weather_data, 'skycon'):
        return weather_data.skycon
    else:
        return '未知'  # 默认值


def _convert_wind_speed(wind_speed: float) -> float:
    """转换风速单位为km/h"""
    # API返回的可能是m/s，转换为km/h
    if wind_speed < 50:  # 假设是m/s，转换为km/h
        return wind_speed * 3.6
    else:  # 假设已经是km/h
        return wind_speed


def _convert_humidity(humidity: float) -> float:
    """转换湿度为百分比"""
    # API返回的可能是0-1的小数，转换为百分比
    if humidity <= 1.0:
        return humidity * 100
    else:
        return humidity


def _convert_pressure(pressure: float) -> float:
    """转换气压为hPa"""
    # API返回的可能是Pa，转换为hPa
    if pressure > 2000:  # 假设是Pa
        return pressure / 100
    else:  # 假设已经是hPa
        return pressure


# 注意：我们不再提供模拟或虚假的天气数据
# 诚实告知用户无法获取数据，而不是欺骗用户


def _calculate_fishing_score(weather_data: Dict[str, Any]) -> Dict[str, float]:
    """计算钓鱼评分"""
    temp = weather_data['temperature']
    condition = weather_data['condition']
    wind = weather_data['wind_speed']
    humidity = weather_data['humidity']
    pressure = weather_data['pressure']

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
    if wind < 8:
        return 95.0
    elif 8 <= wind < 15:
        return 80.0
    elif 15 <= wind < 20:
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


def _generate_fishing_report(
    location: str,
    date: str,
    weather_data: Dict[str, Any],
    scores: Dict[str, float]
) -> str:
    """生成钓鱼推荐报告"""
    overall_score = scores['overall']

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
        time_advice = "如需钓鱼，建议选择有遮蔽的钓点"

    # 生成报告
    report = f"🎣 {location} 钓鱼推荐报告 ({date})\n"
    report += "=" * 50 + "\n\n"

    # 综合推荐
    report += f"🏆 **综合评分**: {overall_score:.1f}/100 {grade}\n"
    report += f"📝 **推荐建议**: {recommendation}\n"
    report += f"⏰ **最佳时段**: {time_advice}\n\n"

    # 天气条件
    report += f"🌤️ **天气条件**:\n"
    report += f"• 🌡️ 温度: {weather_data['temperature']}°C\n"
    report += f"• ☁️ 天气: {weather_data['condition']}\n"
    report += f"• 💨 风速: {weather_data['wind_speed']} km/h\n"
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

    if scores['temperature'] >= 80:
        report += "• ✅ 温度适宜，鱼类活跃度较高\n"
    elif scores['temperature'] >= 60:
        report += "• ⚠️ 温度一般，建议选择深水区或遮荫处\n"
    else:
        report += "• ❌ 温度不佳，鱼类活动较少\n"

    if scores['weather'] >= 80:
        report += "• ✅ 天气条件良好，适合钓鱼\n"
    else:
        report += "• ⚠️ 天气一般，注意防护\n"

    if scores['wind'] >= 80:
        report += "• ✅ 风平浪静，利于作钓\n"
    elif scores['wind'] >= 60:
        report += "• ⚠️ 风力适中，注意抛竿技巧\n"
    else:
        report += "• ❌ 风力较大，建议选择避风钓位\n"

    # 装备建议
    report += f"\n🎒 **装备建议**:\n"
    if weather_data['condition'] in ['晴']:
        report += "• 建议携带防晒装备和遮阳帽\n"
    elif weather_data['condition'] in ['小雨', '中雨']:
        report += "• 建议携带雨具，选择有遮挡的钓位\n"

    if weather_data['temperature'] < 15:
        report += "• 建议携带保暖衣物\n"
    elif weather_data['temperature'] > 28:
        report += "• 建议携带充足的饮水\n"

    return report