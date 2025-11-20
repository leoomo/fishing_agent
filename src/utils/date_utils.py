#!/usr/bin/env python3
"""
日期解析工具模块 - 统一日期处理逻辑
"""

from datetime import datetime, date, timedelta
from typing import Union, List
import logging

logger = logging.getLogger(__name__)


def parse_date_input(date_input: str) -> datetime:
    """
    解析日期输入字符串为 datetime 对象

    Args:
        date_input: 日期字符串，支持：
                   - 相对日期: "今天"、"明天"、"后天"、"昨天"
                   - 绝对日期: "2024-12-25"、"12-25"
                   - 空值: 返回明天

    Returns:
        解析后的 datetime 对象

    Examples:
        >>> parse_date_input("明天")
        datetime(2024, 12, 26, ...)
        >>> parse_date_input("2024-12-25")
        datetime(2024, 12, 25, 0, 0)
    """
    if not date_input:
        return datetime.now() + timedelta(days=1)  # 默认明天

    date_input = date_input.strip().lower()

    # 相对日期映射
    relative_dates = {
        'today': 0, '今天': 0,
        'tomorrow': 1, '明天': 1,
        'yesterday': -1, '昨天': -1,
        '后天': 2, '大后天': 3
    }

    if date_input in relative_dates:
        return datetime.now() + timedelta(days=relative_dates[date_input])

    # 尝试解析绝对日期
    try:
        return datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        try:
            # 尝试 MM-DD 格式，使用当前年份
            parsed = datetime.strptime(date_input, '%m-%d')
            return parsed.replace(year=datetime.now().year)
        except ValueError:
            # 解析失败，默认明天
            logger.warning(f"无法解析日期: {date_input}，使用默认值（明天）")
            return datetime.now() + timedelta(days=1)


def parse_dates_list(dates: List[str]) -> List[datetime]:
    """
    解析日期列表

    Args:
        dates: 日期字符串列表

    Returns:
        datetime 对象列表
    """
    if not dates:
        return [datetime.now() + timedelta(days=1)]

    return [parse_date_input(d) for d in dates]


def format_date(dt: Union[datetime, date], fmt: str = '%Y-%m-%d') -> str:
    """
    格式化日期为字符串

    Args:
        dt: datetime 或 date 对象
        fmt: 格式字符串

    Returns:
        格式化后的日期字符串
    """
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    return dt.strftime(fmt)


def get_weekday_cn(dt: Union[datetime, date]) -> str:
    """
    获取中文星期名称

    Args:
        dt: datetime 或 date 对象

    Returns:
        中文星期名称
    """
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    if isinstance(dt, datetime):
        return weekdays[dt.weekday()]
    return weekdays[dt.weekday()]
