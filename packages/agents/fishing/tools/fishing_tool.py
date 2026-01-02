#!/usr/bin/env python3
"""
钓鱼推荐工具 - 主入口

职责:
- 提供 @tool 装饰的钓鱼推荐接口
- 协调各子模块 (天气获取/评分计算/时段优化/报告生成)
- 处理单日和多日推荐逻辑
- 时间段标准化
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging
from langchain.tools import tool

from ..utils.date import parse_date_input, parse_dates_list, format_date, get_weekday_cn
from .fishing.weather_api import get_weather_data
from .fishing.scorer import calculate_fishing_score, calculate_hourly_scores
from .fishing.time_optimizer import find_best_time_slots, filter_time_slots_by_period
from .fishing.report_generator import generate_fishing_report

logger = logging.getLogger(__name__)


# ===== 时间段定义常量 =====
TIME_PERIOD_DEFINITIONS = {
    # 标准时间段（24小时制）
    "白天": {"start": 6, "end": 18, "alias": ["daytime", "白昼"]},
    "晚上": {"start": 18, "end": 6, "alias": ["night", "夜间", "夜晚"], "cross_midnight": True},
    "上午": {"start": 6, "end": 12, "alias": ["morning", "早上", "早晨"]},
    "下午": {"start": 12, "end": 18, "alias": ["afternoon"]},
    "傍晚": {"start": 16, "end": 19, "alias": ["evening", "黄昏"]},
    "深夜": {"start": 0, "end": 6, "alias": ["midnight", "凌晨"]},
    "全天": {"start": 0, "end": 24, "alias": ["all", "整天", "24小时"]},
}



def normalize_time_period(time_period: str) -> str:
    """
    标准化时间段字符串

    Args:
        time_period: 原始时间段字符串（可能包含别名）

    Returns:
        标准化后的时间段名称（如"白天"、"晚上"）

    Examples:
        >>> normalize_time_period("daytime")
        "白天"
        >>> normalize_time_period("早上")
        "上午"
    """
    if not time_period:
        return "全天"

    time_period_lower = time_period.lower().strip()

    # 直接匹配
    if time_period_lower in TIME_PERIOD_DEFINITIONS:
        return time_period_lower

    # 别名匹配
    for standard_name, config in TIME_PERIOD_DEFINITIONS.items():
        if time_period_lower in config.get("alias", []):
            return standard_name

    # 未识别的时间段，返回全天
    return "全天"




@tool
def query_fishing_recommendation(location: str, dates: list = None, time_period: str = None) -> str:
    """
    查询钓鱼时间推荐（已内置天气数据获取功能）

    ⚠️ 重要提示：
    - ✅ 本工具已自动获取所有必需的天气数据，无需额外调用 get_weather
    - ✅ 使用7因子科学评分系统（温度、天气、风力、气压、湿度、季节、月相）
    - ✅ 自动分析趋势并提供详细的钓鱼建议
    - ❌ 仅用于包含"钓鱼"关键词的查询
    - ❌ 纯天气查询请使用 get_weather 工具
    - ❌ 绝对禁止与 get_weather 同时调用

    Args:
        location: 地区名称，如"杭州"、"北京"、"余杭区"等
        dates: 日期列表，支持：
              - 单日: ["明天"] 或 ["2024-12-25"]
              - 多日: ["今天", "明天", "后天"]
              - 一周: 传入7个日期
              - 空值/None: 默认["明天"]
        time_period: 时间段限制（仅对单日查询生效），支持：
              - "白天" / "晚上" / "上午" / "下午" / "傍晚" / "深夜"
              - "全天" / None: 返回全天所有时段（默认）

    Returns:
        - 单日: 详细钓鱼推荐报告（包含完整天气分析和24小时时段推荐）
        - 多日: 多天钓鱼推荐表格，含最佳日期推荐

    ✅ 正确用法示例:
        "明天杭州钓鱼怎么样？" → query_fishing_recommendation("杭州", ["明天"])
        "今天余杭区钓鱼天气" → query_fishing_recommendation("余杭区", ["今天"])
        "后天白天佛山钓鱼" → query_fishing_recommendation("佛山", ["后天"], "白天")

    ❌ 错误用法（应使用 get_weather）:
        "杭州明天天气" → 不要调用此工具！
    """
    try:
        # 参数标准化
        if not dates:
            dates = ["明天"]

        # 限制最多7天
        if len(dates) > 7:
            return "❌ 最多支持查询7天的钓鱼推荐"

        # 根据日期数量分发逻辑
        if len(dates) == 1:
            return _single_day_recommendation(location, dates[0], time_period)
        else:
            return _multi_day_recommendation(location, dates)

    except Exception as e:
        logger.error(f"钓鱼推荐分析失败: {str(e)}")
        return f"❌ 分析钓鱼推荐时发生错误: {str(e)}，请稍后重试。"




def _single_day_recommendation(location: str, date_str: str, time_period: str = None) -> str:
    """
    单日详细钓鱼推荐

    Args:
        location: 地区名称
        date_str: 日期字符串
        time_period: 时间段限制

    Returns:
        详细的单日钓鱼推荐报告
    """
    # 解析日期
    target_date = parse_date_input(date_str)
    formatted_date = format_date(target_date)

    # 标准化时间段参数
    normalized_period = normalize_time_period(time_period)

    # 获取天气数据（包含历史数据用于趋势分析）
    weather_data = get_weather_data(location, target_date)
    if not weather_data:
        return f"❌ 抱歉，无法获取{location}在{formatted_date}的天气数据，请稍后重试。"

    # 计算钓鱼评分（传递日期和历史数据）
    # 如果weather_data中有historical_data，使用它；否则传None
    historical_data = weather_data.get('historical_data', None)

    # 构建target_date的datetime对象（包含小时信息）
    if isinstance(target_date, datetime):
        target_datetime = target_date
    else:
        # 如果是date对象，转换为datetime（默认中午12点）
        target_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=12))

    fishing_score = calculate_fishing_score(
        weather_data,
        target_date=target_datetime,
        historical_data=historical_data
    )

    # 生成推荐报告
    return generate_fishing_report(location, formatted_date, weather_data, fishing_score, normalized_period)




def _multi_day_recommendation(location: str, dates: list) -> str:
    """
    多日钓鱼推荐

    Args:
        location: 地区名称
        dates: 日期字符串列表

    Returns:
        多日钓鱼推荐表格报告
    """
    # 解析日期列表
    parsed_dates = parse_dates_list(dates)

    # 收集多天数据
    results = []
    for target_date in parsed_dates:
        date_obj = target_date.date() if isinstance(target_date, datetime) else target_date
        date_str = format_date(date_obj)
        weekday = get_weekday_cn(date_obj)

        # 获取天气数据
        weather_data = get_weather_data(location, target_date)

        if weather_data:
            # 构建target_date的datetime对象（默认中午12点）
            if isinstance(target_date, datetime):
                target_datetime = target_date
            else:
                target_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=12))

            # 计算评分（对于多日概览，不使用趋势分析，但使用季节和月相）
            fishing_score = calculate_fishing_score(
                weather_data,
                target_date=target_datetime,
                historical_data=None  # 多日概览不需要趋势分析
            )
            overall_score = fishing_score.get('overall', 0.0)
            data_quality = fishing_score.get('data_quality', 'unknown')

            # 只有当数据质量有效时才添加
            if data_quality == 'valid' and overall_score > 0:
                results.append({
                    'date': date_str,
                    'weekday': weekday,
                    'score': overall_score,
                    'temperature': weather_data.get('temperature'),
                    'condition': weather_data.get('condition'),
                    'wind_speed': weather_data.get('wind_speed'),
                    'data_source': weather_data.get('data_source', 'unknown')
                })

    if not results:
        return f"❌ 抱歉，无法获取{location}的天气数据，请稍后重试。"

    # 生成报告
    report = f"🎣 {location}钓鱼推荐（{len(results)}天）\n\n"

    # 找到最佳日期
    best_day = max(results, key=lambda x: x['score'])
    report += f"✨ **最佳钓鱼日期**: {best_day['date']} ({best_day['weekday']})，评分: {best_day['score']:.1f}\n\n"

    # 生成表格
    report += "| 日期 | 星期 | 评分 | 温度 | 天气 | 风速 |\n"
    report += "|------|------|------|------|------|------|\n"

    for result in results:
        # 转换天气代码为中文
        condition_cn = _translate_weather_condition(result['condition'])

        # 评分等级
        score = result['score']
        if score >= 80:
            score_emoji = "🟢"
        elif score >= 60:
            score_emoji = "🟡"
        else:
            score_emoji = "🔴"

        report += f"| {result['date']} | {result['weekday']} | {score_emoji} {score:.1f} | {result['temperature']:.1f}°C | {condition_cn} | {result['wind_speed']:.1f}m/s |\n"

    # 评分说明
    report += f"\n📈 **评分说明** (基于7因子科学评分体系):\n"
    report += f"- 🟢 80分以上: 优秀，非常适合钓鱼\n"
    report += f"- 🟡 60-80分: 良好，适合钓鱼\n"
    report += f"- 🔴 60分以下: 一般，需注意天气条件\n"
    report += f"\n*评分综合考虑：温度、天气、风力、气压、湿度、季节、月相*\n"

    return report






