#!/usr/bin/env python3
"""
日期时间处理工具模块
支持多种日期格式的解析和时间粒度处理
"""

import re
import time
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional, Dict, List
import calendar
import logging

logger = logging.getLogger(__name__)


class DateTimeParser:
    """日期时间解析器"""

    # 相对日期映射
    RELATIVE_DATES = {
        'today': 0,
        '今天': 0,
        'tomorrow': 1,
        '明天': 1,
        'yesterday': -1,
        '昨天': -1,
        'the day after tomorrow': 2,
        '后天': 2,
        'the day before yesterday': -2,
        '前天': -2,
    }

    # 星期映射
    WEEKDAYS = {
        'monday': 0, 'mon': 0, '周一': 0, '星期一': 0,
        'tuesday': 1, 'tue': 1, '周二': 1, '星期二': 1,
        'wednesday': 2, 'wed': 2, '周三': 2, '星期三': 2,
        'thursday': 3, 'thu': 3, '周四': 3, '星期四': 3,
        'friday': 4, 'fri': 4, '周五': 4, '星期五': 4,
        'saturday': 5, 'sat': 5, '周六': 5, '星期六': 5,
        'sunday': 6, 'sun': 6, '周日': 6, '星期日': 6,
    }

    # 月份映射
    MONTHS = {
        'january': 1, 'jan': 1, '一月': 1,
        'february': 2, 'feb': 2, '二月': 2,
        'march': 3, 'mar': 3, '三月': 3,
        'april': 4, 'apr': 4, '四月': 4,
        'may': 5, '五月': 5,
        'june': 6, 'jun': 6, '六月': 6,
        'july': 7, 'jul': 7, '七月': 7,
        'august': 8, 'aug': 8, '八月': 8,
        'september': 9, 'sep': 9, 'sept': 9, '九月': 9,
        'october': 10, 'oct': 10, '十月': 10,
        'november': 11, 'nov': 11, '十一月': 11,
        'december': 12, 'dec': 12, '十二月': 12,
    }

    def __init__(self):
        """初始化日期解析器"""
        self.now = datetime.now()

    def parse_date_string(self, date_str: str) -> Optional[datetime]:
        """
        解析日期字符串

        Args:
            date_str: 日期字符串，支持多种格式

        Returns:
            datetime对象，解析失败返回None
        """
        if not date_str or not date_str.strip():
            return None

        date_str = date_str.strip().lower()

        try:
            # 1. 处理相对日期
            if date_str in self.RELATIVE_DATES:
                days_offset = self.RELATIVE_DATES[date_str]
                return self.now + timedelta(days=days_offset)

            # 2. 处理"X天后"、"X天前"格式
            days_match = re.match(r'(\d+)[天日]后', date_str)
            if days_match:
                days = int(days_match.group(1))
                return self.now + timedelta(days=days)

            days_before_match = re.match(r'(\d+)[天日]前', date_str)
            if days_before_match:
                days = int(days_before_match.group(1))
                return self.now - timedelta(days=days)

            # 3. 处理星期格式
            for weekday_name, weekday_num in self.WEEKDAYS.items():
                if weekday_name in date_str:
                    current_weekday = self.now.weekday()
                    target_weekday = weekday_num

                    if target_weekday >= current_weekday:
                        days_ahead = target_weekday - current_weekday
                    else:
                        days_ahead = 7 - (current_weekday - target_weekday)

                    # 如果是"下周"，加7天
                    if '下周' in date_str or 'next week' in date_str:
                        days_ahead += 7

                    return self.now + timedelta(days=days_ahead)

            # 4. 处理"YYYY-MM-DD"格式
            iso_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
            if iso_match:
                year, month, day = map(int, iso_match.groups())
                return datetime(year, month, day)

            # 5. 处理"YYYY年MM月DD日"格式
            chinese_match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
            if chinese_match:
                year, month, day = map(int, chinese_match.groups())
                return datetime(year, month, day)

            # 6. 处理"MM月DD日"格式（当年）
            month_day_match = re.match(r'(\d{1,2})月(\d{1,2})日', date_str)
            if month_day_match:
                month, day = map(int, month_day_match.groups())
                year = self.now.year
                return datetime(year, month, day)

            # 7. 处理英文月份格式
            # "December 25, 2024" 或 "25 December 2024"
            for month_name, month_num in self.MONTHS.items():
                if month_name in date_str:
                    # 尝试匹配 "December 25, 2024"
                    month_match = re.search(rf'{month_name}\s+(\d{{1,2}}),?\s*(\d{{4}})?', date_str, re.IGNORECASE)
                    if month_match:
                        day = int(month_match.group(1))
                        year = int(month_match.group(2)) if month_match.group(2) else self.now.year
                        return datetime(year, month_num, day)

                    # 尝试匹配 "25 December 2024"
                    day_month_match = re.search(rf'(\d{{1,2}})\s+{month_name}\s*(\d{{4}})?', date_str, re.IGNORECASE)
                    if day_month_match:
                        day = int(day_month_match.group(1))
                        year = int(day_month_match.group(2)) if day_month_match.group(2) else self.now.year
                        return datetime(year, month_num, day)

            logger.warning(f"无法解析日期字符串: {date_str}")
            return None

        except Exception as e:
            logger.error(f"解析日期字符串失败: {date_str}, 错误: {e}")
            return None

    def parse_datetime_expression(self, datetime_str: str) -> Tuple[Optional[datetime], Optional[str]]:
        """
        解析包含时间粒度的日期时间表达式

        Args:
            datetime_str: 日期时间表达式，如"明天上午"、"2024-12-25晚上"等

        Returns:
            (datetime, time_period) 元组
        """
        if not datetime_str or not datetime_str.strip():
            return None, None

        datetime_str = datetime_str.strip()

        # 1. 尝试提取时间粒度关键词
        time_period = None
        remaining_str = datetime_str

        # 检查是否包含时间段关键词
        for period in TimeGranularityParser.TIME_PERIODS.keys():
            if period in datetime_str:
                time_period = period
                remaining_str = datetime_str.replace(period, '').strip()
                break

        # 2. 解析剩余的日期部分
        if remaining_str:
            date_obj = self.parse_date_string(remaining_str)
        else:
            # 如果没有日期部分，默认为今天
            date_obj = self.now

        return date_obj, time_period

    def format_date(self, dt: datetime, format_type: str = 'iso') -> str:
        """
        格式化日期

        Args:
            dt: datetime对象
            format_type: 格式类型 ('iso', 'chinese', 'readable')

        Returns:
            格式化后的日期字符串
        """
        if format_type == 'iso':
            return dt.strftime('%Y-%m-%d')
        elif format_type == 'chinese':
            return dt.strftime('%Y年%m月%d日')
        elif format_type == 'readable':
            return dt.strftime('%Y年%m月%d日 %A')
        else:
            return dt.strftime('%Y-%m-%d')

    def get_relative_description(self, dt: datetime) -> str:
        """
        获取相对日期描述

        Args:
            dt: datetime对象

        Returns:
            相对日期描述，如"今天"、"明天"、"3天后"等
        """
        delta = dt.date() - self.now.date()
        days_diff = delta.days

        if days_diff == 0:
            return "今天"
        elif days_diff == 1:
            return "明天"
        elif days_diff == -1:
            return "昨天"
        elif days_diff == 2:
            return "后天"
        elif days_diff == -2:
            return "前天"
        elif days_diff > 0:
            return f"{days_diff}天后"
        else:
            return f"{abs(days_diff)}天前"


class TimeGranularityParser:
    """时间粒度解析器"""

    # 时间段定义 (开始小时, 结束小时)
    TIME_PERIODS = {
        '早上': (5, 9),      # 05:00-08:59
        '上午': (9, 12),     # 09:00-11:59
        '中午': (12, 14),    # 12:00-13:59
        '下午': (14, 18),    # 14:00-17:59
        '晚上': (18, 22),    # 18:00-21:59
        '夜间': (22, 29),    # 22:00-04:59 (跨天处理)
        '凌晨': (0, 5),      # 00:00-04:59
        '清晨': (5, 8),      # 05:00-07:59 (与早上类似)
        '傍晚': (17, 19),    # 17:00-18:59
    }

    # 英文时间粒度
    EN_TIME_PERIODS = {
        'morning': (5, 9),   # 早上
        'forenoon': (9, 12), # 上午
        'noon': (12, 14),    # 中午
        'afternoon': (14, 18), # 下午
        'evening': (18, 22), # 晚上
        'night': (22, 29),   # 夜间
        'dawn': (5, 8),      # 黎明
        'dusk': (17, 19),    # 黄昏
    }

    # 合并所有时间段
    ALL_TIME_PERIODS = {**TIME_PERIODS, **EN_TIME_PERIODS}

    def __init__(self):
        """初始化时间粒度解析器"""
        pass

    def parse_time_period(self, time_str: str) -> Optional[str]:
        """
        解析时间粒度字符串

        Args:
            time_str: 时间粒度字符串

        Returns:
            标准化的时间粒度关键词
        """
        if not time_str:
            return None

        time_str = time_str.strip().lower()

        # 直接匹配
        if time_str in self.ALL_TIME_PERIODS:
            return time_str

        # 模糊匹配
        for period in self.ALL_TIME_PERIODS.keys():
            if period in time_str or time_str in period:
                return period

        return None

    def get_time_range(self, time_period: str, date: datetime) -> Tuple[datetime, datetime]:
        """
        获取指定时间段的时间范围

        Args:
            time_period: 时间粒度关键词
            date: 日期

        Returns:
            (start_time, end_time) 元组
        """
        if time_period not in self.ALL_TIME_PERIODS:
            raise ValueError(f"不支持的时间粒度: {time_period}")

        start_hour, end_hour = self.ALL_TIME_PERIODS[time_period]

        # 处理跨天的情况（如夜间）
        if end_hour > 24:
            start_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            end_time = (date + timedelta(days=1)).replace(hour=end_hour-24, minute=0, second=0, microsecond=0)
        else:
            start_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)

        return start_time, end_time

    def get_covering_hours(self, time_period: str, date: datetime) -> List[int]:
        """
        获取时间段覆盖的小时列表

        Args:
            time_period: 时间粒度关键词
            date: 日期

        Returns:
            小时列表 [start_hour, start_hour+1, ..., end_hour-1]
        """
        start_time, end_time = self.get_time_range(time_period, date)
        start_hour = start_time.hour
        end_hour = end_time.hour

        hours = []
        current_time = start_time

        while current_time < end_time:
            hours.append(current_time.hour)
            current_time += timedelta(hours=1)

            # 处理跨天
            if current_time.hour == 0 and len(hours) > 12:
                break

        return hours

    def get_period_description(self, time_period: str) -> str:
        """
        获取时间段描述

        Args:
            time_period: 时间粒度关键词

        Returns:
            时间段描述
        """
        if time_period not in self.ALL_TIME_PERIODS:
            return f"未知时间段: {time_period}"

        start_hour, end_hour = self.ALL_TIME_PERIODS[time_period]

        if end_hour > 24:
            return f"{start_hour:02d}:00 - {end_hour-24:02d}:00 (次日)"
        else:
            return f"{start_hour:02d}:00 - {end_hour:02d}:00"


def create_datetime_parser() -> DateTimeParser:
    """创建日期解析器实例"""
    return DateTimeParser()


def create_time_granularity_parser() -> TimeGranularityParser:
    """创建时间粒度解析器实例"""
    return TimeGranularityParser()


# 测试函数
def test_datetime_parsing():
    """测试日期时间解析功能"""
    parser = DateTimeParser()
    time_parser = TimeGranularityParser()

    test_cases = [
        "今天",
        "明天",
        "昨天",
        "后天",
        "3天后",
        "下周三",
        "2024-12-25",
        "2024年12月25日",
        "12月25日",
        "December 25, 2024",
        "明天上午",
        "2024-12-25晚上",
        "周五下午",
    ]

    print("=== 日期时间解析测试 ===")
    for test_case in test_cases:
        date_obj, time_period = parser.parse_datetime_expression(test_case)
        if date_obj:
            date_str = parser.format_date(date_obj, 'readable')
            period_desc = time_parser.get_period_description(time_period) if time_period else "无时间段"
            print(f"'{test_case}' -> {date_str} {period_desc}")
        else:
            print(f"'{test_case}' -> 解析失败")


if __name__ == "__main__":
    test_datetime_parsing()