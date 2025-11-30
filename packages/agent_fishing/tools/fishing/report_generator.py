#!/usr/bin/env python3
"""
报告生成器模块

职责:
- 生成完整的钓鱼推荐报告
- 添加钓鱼策略建议
- 添加装备建议
- 生成详细天气分析
"""

from typing import Dict, Any, List
import logging

from .time_optimizer import generate_score_trend, find_best_time_slots, filter_time_slots_by_period
from .weather_api import translate_weather_condition
from .scorer import calculate_hourly_scores

logger = logging.getLogger(__name__)


def generate_fishing_report(location: str, date: str, weather_data: Dict[str, Any], scores: Dict[str, float], time_period: str = None) -> str:
    """
    生成钓鱼推荐报告（支持24小时智能时段推荐和时间段过滤）

    Args:
        location: 地点名称
        date: 日期字符串
        weather_data: 天气数据字典
        scores: 钓鱼评分字典
        time_period: 时间段限制（"白天"/"晚上"/"上午"/"下午"/None）

    Returns:
        格式化的钓鱼推荐报告
    """
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
            hourly_scores = calculate_hourly_scores(weather_data)

            if hourly_scores:
                # 检测最佳时段
                best_time_slots = find_best_time_slots(hourly_scores, top_n=5)  # 先获取前5个时段

                # 🆕 根据 time_period 过滤时段
                if time_period and time_period != "全天":
                    hourly_datetimes = weather_data.get('hourly_datetimes', [])
                    best_time_slots = filter_time_slots_by_period(
                        time_slots=best_time_slots,
                        hourly_datetimes=hourly_datetimes,
                        time_period=time_period
                    )
                    logger.info(f"时间段过滤({time_period})后剩余{len(best_time_slots)}个时段")

                    # 如果过滤后没有时段，添加提示信息
                    if not best_time_slots:
                        logger.info(f"在时间段'{time_period}'内未找到推荐时段")

                # 统一限制显示前3个
                best_time_slots = best_time_slots[:3]

                # 生成评分趋势图
                score_trend = generate_score_trend(hourly_scores)

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

    # 🆕 处理时间段过滤后的情况
    if time_period and time_period != "全天" and has_hourly_data and not best_time_slots:
        # 有时间段限制但没有找到符合条件的时段
        report += f"\n⚠️ **提示**: 在指定的时间段（{time_period}）内未找到推荐时段。\n"
        report += f"💡 建议: 尝试查询其他时间段或全天推荐。\n\n"

    # 🆕 如果有智能时段推荐，优先展示
    if best_time_slots:
        # 🆕 添加时间段标识
        period_label = f"（{time_period}）" if time_period and time_period != "全天" else ""
        report += f"\n⏰ **智能推荐时段{period_label}** (基于24小时数据分析):\n\n"

        # 排名emoji
        rank_emojis = ['🥇', '🥈', '🥉']

        for i, slot in enumerate(best_time_slots):
            emoji = rank_emojis[i] if i < len(rank_emojis) else f"{i+1}."
            # 翻译时段天气条件为中文
            slot_condition_cn = translate_weather_condition(slot['condition'])
            report += f"{emoji} **第{i+1}推荐**: {slot['time_range']} (评分: {slot['avg_score']:.1f}分)\n"
            report += f"   • 温度: {slot['temp_min']:.1f}-{slot['temp_max']:.1f}°C | 天气: {slot_condition_cn} | 风速: {slot['wind_min']:.1f}-{slot['wind_max']:.1f}m/s\n"
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
    # 温度范围：从hourly_temps计算，如果没有则用平均温度
    hourly_temps = weather_data.get('hourly_temps', [])
    if hourly_temps:
        temp_min = min(hourly_temps)
        temp_max = max(hourly_temps)
        report += f"• 🌡️ 温度: {temp_min:.1f}-{temp_max:.1f}°C\n"
    else:
        report += f"• 🌡️ 温度: {weather_data['temperature']:.1f}°C\n"
    # 翻译天气条件为中文
    condition_cn = translate_weather_condition(weather_data['condition'])
    report += f"• ☁️ 天气: {condition_cn}\n"
    report += f"• 💨 风速: {float(weather_data['wind_speed']):.1f} m/s\n"
    report += f"• 💧 湿度: {float(weather_data['humidity']):.1f}%\n"
    report += f"• 🌀 气压: {weather_data['pressure']:.1f} hPa\n\n"

    # 趋势分析（如果有）
    if 'trend_analysis' in scores:
        trend = scores['trend_analysis']
        has_trend = False

        # 检查是否有显著趋势
        if trend.get('pressure_multiplier', 1.0) != 1.0 or \
           trend.get('temp_multiplier', 1.0) != 1.0 or \
           trend.get('wind_multiplier', 1.0) != 1.0:
            has_trend = True
            report += f"📈 **趋势分析** (动态调整):\n"

            # 气压趋势
            pressure_mult = trend.get('pressure_multiplier', 1.0)
            if pressure_mult > 1.0:
                bonus = int((pressure_mult - 1.0) * 100)
                if pressure_mult >= 1.15:
                    report += f"• ⚡ 气压快速下降 (+{bonus}%) - 钓鱼黄金期！\n"
                else:
                    report += f"• ✅ 气压缓慢下降 (+{bonus}%) - 鱼类活跃\n"
            elif pressure_mult < 1.0:
                penalty = int((1.0 - pressure_mult) * 100)
                report += f"• ⚠️ 气压上升中 (-{penalty}%) - 活跃度降低\n"

            # 温度趋势
            temp_mult = trend.get('temp_multiplier', 1.0)
            if temp_mult > 1.0:
                bonus = int((temp_mult - 1.0) * 100)
                report += f"• 🌡️ 温度上升中 (+{bonus}%) - 有利于鱼类活动\n"
            elif temp_mult < 1.0:
                penalty = int((1.0 - temp_mult) * 100)
                report += f"• ❄️ 温度下降中 (-{penalty}%) - 活跃度下降\n"

            # 风速稳定性
            wind_mult = trend.get('wind_multiplier', 1.0)
            if wind_mult > 1.0:
                report += f"• 💨 风速稳定 (+5%) - 利于作钓\n"
            elif wind_mult < 1.0:
                penalty = int((1.0 - wind_mult) * 100)
                report += f"• 🌪️ 风速不稳定 (-{penalty}%) - 建议避风钓位\n"

            report += "\n"

    # 钓鱼建议
    report += f"💡 **钓鱼建议**:\n"
    report += add_fishing_suggestions(scores)

    # 装备建议
    report += f"\n🎒 **装备建议**:\n"
    report += add_equipment_suggestions(weather_data)

    # 🆕 添加24小时评分趋势图（如果有）
    if score_trend:
        report += f"\n{score_trend}\n"

    return report


def add_fishing_suggestions(scores: Dict[str, float]) -> str:
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


def add_equipment_suggestions(weather_data: Dict[str, Any]) -> str:
    """添加装备建议"""
    suggestions = ""

    condition = weather_data.get('condition', '').upper()

    # 晴天条件：支持中文和英文代码
    if condition.startswith('晴') or 'CLEAR' in condition:
        suggestions += "• 建议携带防晒装备和遮阳帽\n"
    # 雨天条件
    elif '雨' in condition or 'RAIN' in condition:
        suggestions += "• 建议携带雨具，选择有遮挡的钓位\n"
    # 多云条件
    elif 'CLOUDY' in condition or '云' in condition:
        suggestions += "• 多云天气，光线柔和适合作钓\n"

    # 温度建议
    temp = weather_data.get('temperature', 20)
    if temp is not None:
        if temp < 10:
            suggestions += "• 气温较低，建议携带保暖衣物和热饮\n"
        elif temp < 15:
            suggestions += "• 建议携带外套保暖\n"
        elif temp > 30:
            suggestions += "• 高温天气，建议携带充足饮水和防晒\n"
        elif temp > 25:
            suggestions += "• 建议携带充足的饮水\n"

    # 风力建议
    wind_speed = weather_data.get('wind_speed', 0)
    if wind_speed and wind_speed > 5:
        suggestions += "• 风力较大，建议使用重铅或选择避风钓位\n"

    # 如果没有任何建议，添加默认建议
    if not suggestions:
        suggestions += "• 建议携带常规钓鱼装备\n"

    return suggestions


def generate_detailed_analysis(weather_data: Dict[str, Any], scores: Dict[str, float]) -> str:
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
    analysis += f"• 湿度{weather_data['humidity']:.1f}%，气压{weather_data['pressure']:.1f}hPa，"

    if scores['humidity'] >= 75 and scores['pressure'] >= 75:
        analysis += "空气湿润且气压稳定，有利于鱼类觅食\n"
    else:
        analysis += "需要注意天气变化对鱼类活动的影响\n"

    return analysis

