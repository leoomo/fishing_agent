#!/usr/bin/env python3
"""
钓鱼分析器 - 同步版本
基于天气数据计算最佳钓鱼时间
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# 设置日志
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
        # 天气服务已禁用模拟数据生成，直接返回错误信息
        if not date:
            date = "明天"

        # 直接返回错误信息，不再生成任何模拟数据
        error_result = {
            "error": "天气服务查询失败，无法获取准确的天气数据进行钓鱼分析",
            "location": location,
            "date": date,
            "message": "为避免误导用户，模拟天气数据已被禁用。请稍后再试或检查天气服务配置。",
            "suggestion": "建议查询实时天气信息后再做钓鱼决定",
            "error_code": "WEATHER_SERVICE_UNAVAILABLE"
        }

        return json.dumps(error_result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"钓鱼分析失败: {e}")
        error_result = {
            "error": f"钓鱼分析失败: {str(e)}",
            "location": location,
            "date": date or "明天"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)