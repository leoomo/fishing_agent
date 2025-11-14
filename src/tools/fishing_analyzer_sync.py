#!/usr/bin/env python3
"""
钓鱼分析工具 - 同步版本
基于天气数据分析最佳的钓鱼时间
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def parse_date_input(date_input: str) -> datetime:
    """
    解析日期输入，支持多种格式

    Args:
        date_input: 日期字符串，支持：
                    - YYYY-MM-DD 格式: "2024-12-25"
                    - 相对日期: "tomorrow", "yesterday", "today"
                    - 中文相对日期: "明天", "昨天", "今天"
                    - 数字+时间单位: "2天后", "3天前", "1 week后"

    Returns:
        datetime对象
    """
    # 处理空值
    if not date_input:
        return datetime.now() + timedelta(days=1)  # 默认明天

    date_input = date_input.strip().lower()

    # 相对日期映射
    relative_dates = {
        'today': '今天',
        'tomorrow': '明天',
        'yesterday': '昨天',
        '今天': '今天',
        '明天': '明天',
        '昨天': '昨天',
        '后天': '后天'
    }

    # 检查简单相对日期
    if date_input in relative_dates:
        if date_input in ['today', '今天']:
            return datetime.now()
        elif date_input in ['tomorrow', '明天']:
            return datetime.now() + timedelta(days=1)
        elif date_input in ['yesterday', '昨天']:
            return datetime.now() - timedelta(days=1)
        elif date_input in ['后天']:  # 新增
            return datetime.now() + timedelta(days=2)

    # 检查数字+时间单位格式
    import re

    # 匹配 "2天后", "3天前" 等格式
    day_pattern = r'(\d+)\s*天[后前]'
    day_match = re.search(day_pattern, date_input)
    if day_match:
        days = int(day_match.group(1))
        if '后' in date_input:
            return datetime.now() + timedelta(days=days)
        elif '前' in date_input:
            return datetime.now() - timedelta(days=days)

    # 尝试解析标准日期格式 YYYY-MM-DD
    try:
        return datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        pass

    # 尝试解析其他日期格式
    date_formats = [
        '%Y年%m月%d日',
        '%m/%d/%Y',
        '%d/%m/%Y'
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_input, fmt)
        except ValueError:
            continue

    # 如果所有格式都失败，默认返回明天
    logger.warning(f"无法解析日期 '{date_input}'，使用默认值（明天）")
    return datetime.now() + timedelta(days=1)

def find_best_fishing_time(location: str, date: str = None) -> str:
    """
    找出最佳钓鱼时间的工具函数 - 同步版本

    Args:
        location: 地点名称
        date: 日期 (可选，支持多种格式：YYYY-MM-DD、相对日期如"tomorrow"、"2天后"等，默认为明天)

    Returns:
        JSON格式的钓鱼推荐结果
    """
    try:
        # 简化实现，生成基于地理位置和日期的模拟钓鱼推荐
        if not date:
            # 默认为明天
            date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # 解析日期，支持多种格式
        target_date = parse_date_input(date)
        weekday = target_date.weekday()  # 0=周一, 6=周日

        # 生成标准日期字符串用于显示
        date_display = target_date.strftime('%Y-%m-%d')

        # 根据地理位置生成不同的天气模式
        location_patterns = {
            '北京': {'base_temp': 15, 'wind_base': 10, 'conditions': ['晴', '多云', '阴']},
            '上海': {'base_temp': 18, 'wind_base': 12, 'conditions': ['多云', '小雨', '阴']},
            '广州': {'base_temp': 22, 'wind_base': 8, 'conditions': ['晴', '多云', '阵雨']},
            '深圳': {'base_temp': 23, 'wind_base': 9, 'conditions': ['晴', '多云', '阴']},
            '杭州': {'base_temp': 17, 'wind_base': 11, 'conditions': ['多云', '小雨', '晴']}
        }

        # 获取地区特征，默认使用杭州的模式
        region_pattern = location_patterns.get('杭州', location_patterns['杭州'])
        if any(city in location for city in location_patterns.keys()):
            for city, pattern in location_patterns.items():
                if city in location:
                    region_pattern = pattern
                    break

        # 根据星期调整评分（周末通常更适合钓鱼）
        weekend_bonus = 5 if weekday >= 5 else 0

        # 生成4个推荐时间段
        time_slots = [
            ('早上', '05:00-08:00', 5, 8),
            ('上午', '09:00-11:00', 9, 11),
            ('下午', '14:00-17:00', 14, 17),
            ('傍晚', '18:00-21:00', 18, 21)
        ]

        best_time_slots = []
        weather_summaries = {}

        # 为每个时间段生成评分
        import random
        for period_name, time_range, start_hour, end_hour in time_slots:
            # 基础分数
            base_score = 60.0

            # 时间段评分（早上和傍晚通常更好）
            if period_name in ['早上', '傍晚']:
                base_score += 15
            elif period_name == '上午':
                base_score += 10

            # 温度评分（15-25°C 最佳）
            temp_variations = [-3, -1, 0, 1, 2, 3, -2, -1]
            for hour in range(start_hour, end_hour + 1):
                temp = region_pattern['base_temp'] + temp_variations[hour % len(temp_variations)]
                if 15 <= temp <= 25:
                    base_score += 5
                elif 10 <= temp < 15 or 25 < temp <= 30:
                    base_score += 2
                else:
                    base_score -= 5

            # 风力评分（<15km/h 最佳）
            wind_speed = region_pattern['wind_base'] + random.uniform(-3, 3)
            if wind_speed < 10:
                base_score += 10
            elif wind_speed < 15:
                base_score += 5
            else:
                base_score -= 10

            # 天气评分
            condition = random.choice(region_pattern['conditions'])
            if condition in ['晴', '多云']:
                base_score += 8
            elif condition in ['阴']:
                base_score += 5
            elif condition in ['小雨']:
                base_score += 3
            else:
                base_score -= 10

            # 添加周末奖励
            base_score += weekend_bonus

            # 限制分数范围
            final_score = max(0, min(100, base_score + random.uniform(-5, 5)))
            final_score = round(final_score, 1)

            best_time_slots.append((period_name, final_score))

            # 生成天气摘要
            temp_display = region_pattern['base_temp'] + random.uniform(-2, 2)
            weather_summaries[period_name] = f"{condition} {temp_display:.1f}°C 风速{wind_speed:.1f}km/h"

        # 按分数排序
        best_time_slots.sort(key=lambda x: x[1], reverse=True)

        # 生成详细分析
        detailed_analysis = f"{location} {date_display} ({date}) 钓鱼条件分析：\n\n"
        detailed_analysis += f"• 地理位置：{location}（{region_pattern['base_temp']}°C基准温度）\n"
        detailed_analysis += f"• 星期因素：{'周末' if weekday >= 5 else '工作日'}（{'+5分奖励' if weekday >= 5 else '无奖励'}）\n"
        detailed_analysis += f"• 天气模式：主要{', '.join(region_pattern['conditions'])}\n\n"
        detailed_analysis += "各时间段分析：\n"
        for period_name, score in best_time_slots:
            trend = "🌟" if score >= 80 else "👍" if score >= 60 else "👌"
            detailed_analysis += f"• {period_name}: {trend} {score:.1f}分 - {weather_summaries[period_name]}\n"

        # 生成总结建议
        if best_time_slots[0][1] >= 80:
            summary = f"非常适合钓鱼！推荐在{best_time_slots[0][0]}出行，{best_time_slots[0][1]:.1f}分。天气条件良好，温度适宜，风力适中。"
        elif best_time_slots[0][1] >= 60:
            summary = f"比较适合钓鱼。推荐在{best_time_slots[0][0]}出行，{best_time_slots[0][1]:.1f}分。条件基本满足钓鱼需求。"
        else:
            summary = f"钓鱼条件一般。建议{best_time_slots[0][0]}尝试，{best_time_slots[0][1]:.1f}分。可能需要注意保暖或选择更好的天气时机。"

        # 构建结果
        result = {
            "location": location,
            "date": date_display,  # 使用解析后的标准日期
            "date_input": date,     # 保留原始输入
            "best_time_slots": best_time_slots,
            "weather_summaries": weather_summaries,
            "detailed_analysis": detailed_analysis,
            "summary": summary,
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "analysis_method": "sync_simulation"
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"钓鱼分析失败: {e}")
        error_result = {
            "error": f"钓鱼分析失败: {str(e)}",
            "location": location,
            "date": date or "明天"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)