"""
日期时间工具函数
"""
from datetime import datetime, timedelta
from typing import Optional


def calculate_days_from_now(date_str: str) -> int:
    """
    计算指定日期距离今天的天数

    Args:
        date_str: 日期字符串，支持：
                 - "YYYY-MM-DD" 绝对日期格式
                 - "今天", "明天", "后天" 等相对日期

    Returns:
        int: 距离今天的天数

    Raises:
        ValueError: 日期格式错误
    """
    # 相对日期映射 - 支持中英文
    relative_dates = {
        # 中文相对日期
        '今天': 0,
        '明天': 1,
        '后天': 2,
        '昨天': -1,
        '前天': -2,
        '大前天': -3,
        '大后天': 3,
        # 英文相对日期
        'today': 0,
        'tomorrow': 1,
        'day after tomorrow': 2,
        'yesterday': -1,
        'day before yesterday': -2,
        'three days ago': -3,
        'three days later': 3,
        # 简化英文
        'tmrw': 1,
        'yst': -1,
        'tmw': 1,
    }

    # 标准化输入（去除多余空格，转换为小写）
    normalized_date_str = date_str.strip().lower()

    # 首先检查是否为相对日期
    if normalized_date_str in relative_dates:
        return relative_dates[normalized_date_str]

    # 检查中文"X天后"格式
    if date_str.endswith('天后'):
        try:
            days = int(date_str[:-2])
            return days
        except ValueError:
            pass

    # 检查中文"X天前"格式
    if date_str.endswith('天前'):
        try:
            days = int(date_str[:-2])
            return -days
        except ValueError:
            pass

    # 检查英文"X days later"格式
    if normalized_date_str.endswith(' days later'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return days
        except (ValueError, IndexError):
            pass

    # 检查英文"X day later"格式（单数）
    if normalized_date_str.endswith(' day later'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return days
        except (ValueError, IndexError):
            pass

    # 检查英文"X days after"格式
    if normalized_date_str.endswith(' days after'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return days
        except (ValueError, IndexError):
            pass

    # 检查英文"X day after"格式（单数）
    if normalized_date_str.endswith(' day after'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return days
        except (ValueError, IndexError):
            pass

    # 检查英文"X days ago"格式
    if normalized_date_str.endswith(' days ago'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return -days
        except (ValueError, IndexError):
            pass

    # 检查英文"X day ago"格式（单数）
    if normalized_date_str.endswith(' day ago'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return -days
        except (ValueError, IndexError):
            pass

    # 检查英文"X days before"格式
    if normalized_date_str.endswith(' days before'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return -days
        except (ValueError, IndexError):
            pass

    # 检查英文"X day before"格式（单数）
    if normalized_date_str.endswith(' day before'):
        try:
            parts = normalized_date_str.split(' ')
            days = int(parts[0])
            return -days
        except (ValueError, IndexError):
            pass

    # 尝试解析为绝对日期
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)

        delta = target_date_start - today
        return delta.days
    except ValueError as e:
        raise ValueError(f"日期格式错误，支持YYYY-MM-DD格式或相对日期（如：今天、明天、后天）: {e}")


def get_absolute_date(days_from_now: int) -> str:
    """
    根据距离今天的天数获取绝对日期

    Args:
        days_from_now: 距离今天的天数（0=今天，1=明天，-1=昨天）

    Returns:
        str: YYYY-MM-DD格式的日期字符串
    """
    target_date = datetime.now() + timedelta(days=days_from_now)
    return target_date.strftime("%Y-%m-%d")


def is_date_in_future(date_str: str) -> bool:
    """
    检查日期是否在未来
    
    Args:
        date_str: 日期字符串，格式为"YYYY-MM-DD"
    
    Returns:
        bool: 是否为未来日期
    """
    return calculate_days_from_now(date_str) >= 0


def get_date_range(date_str: str, days_before: int = 0, days_after: int = 0) -> list:
    """
    获取指定日期周围的日期范围
    
    Args:
        date_str: 中心日期，格式为"YYYY-MM-DD"
        days_before: 前推天数
        days_after: 后推天数
    
    Returns:
        list: 日期字符串列表
    """
    try:
        center_date = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = center_date - timedelta(days=days_before)
        
        dates = []
        for i in range(days_before + days_after + 1):
            date = start_date + timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        
        return dates
    except ValueError as e:
        raise ValueError(f"日期格式错误，应为YYYY-MM-DD格式: {e}")


def get_time_period_range(period_name: str) -> str:
    """
    根据时间段名称获取具体的时间范围

    Args:
        period_name: 时间段名称

    Returns:
        str: 时间范围描述
    """
    time_ranges = {
        "夜间": "22:00-05:00",
        "早上": "05:00-08:00",
        "上午": "08:00-11:00",
        "中午": "11:00-13:00",
        "下午": "13:00-17:00",
        "傍晚": "17:00-19:00",
        "晚上": "19:00-22:00",
        "全天": "00:00-24:00"
    }

    return time_ranges.get(period_name, "未知时间段")


def get_time_period_hours(period_name: str) -> list:
    """
    根据时间段名称获取包含的小时列表

    Args:
        period_name: 时间段名称

    Returns:
        list: 小时列表
    """
    period_hours = {
        "夜间": [22, 23, 0, 1, 2, 3, 4],
        "早上": [5, 6, 7],
        "上午": [8, 9, 10],
        "中午": [11, 12],
        "下午": [13, 14, 15, 16],
        "傍晚": [17, 18],
        "晚上": [19, 20, 21],
        "全天": list(range(24))
    }

    return period_hours.get(period_name, [])


def get_time_period_name(hour: int) -> str:
    """
    根据小时数获取时间段名称
    
    Args:
        hour: 小时数 (0-23)
    
    Returns:
        str: 时间段名称
    """
    if 5 <= hour < 8:
        return "早上"
    elif 8 <= hour < 11:
        return "上午"
    elif 11 <= hour < 13:
        return "中午"
    elif 13 <= hour < 17:
        return "下午"
    elif 17 <= hour < 19:
        return "傍晚"
    elif 19 <= hour < 22:
        return "晚上"
    elif 22 <= hour < 24 or 0 <= hour < 5:
        return "夜间"
    else:
        return "全天"


def format_duration(seconds: float) -> str:
    """
    格式化持续时间
    
    Args:
        seconds: 持续时间（秒）
    
    Returns:
        str: 格式化的时间字符串
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m{remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h{remaining_minutes}m"


def is_business_hours(hour: int) -> bool:
    """
    判断是否为工作时间 (9:00-18:00)
    
    Args:
        hour: 小时数 (0-23)
    
    Returns:
        bool: 是否为工作时间
    """
    return 9 <= hour < 18


def get_season_name(date_str: str) -> str:
    """
    根据日期获取季节名称
    
    Args:
        date_str: 日期字符串，格式为"YYYY-MM-DD"
    
    Returns:
        str: 季节名称
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        month = date.month
        
        if month in [12, 1, 2]:
            return "冬季"
        elif month in [3, 4, 5]:
            return "春季"
        elif month in [6, 7, 8]:
            return "夏季"
        elif month in [9, 10, 11]:
            return "秋季"
        else:
            return "未知"
    except ValueError:
        return "未知"


def get_current_timezone_offset() -> int:
    """
    获取当前时区的偏移小时数
    
    Returns:
        int: 时区偏移小时数
    """
    import time
    return time.timezone // -3600 if time.daylight == 0 else time.altzone // -3600


def parse_iso_datetime(datetime_str: str) -> Optional[datetime]:
    """
    解析ISO格式的日期时间字符串
    
    Args:
        datetime_str: ISO格式的日期时间字符串
    
    Returns:
        Optional[datetime]: 解析后的datetime对象，失败返回None
    """
    try:
        # 尝试不同的ISO格式
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None


def get_relative_time_description(date_str: str) -> str:
    """
    获取相对时间描述
    
    Args:
        date_str: 日期字符串，格式为"YYYY-MM-DD"
    
    Returns:
        str: 相对时间描述
    """
    days = calculate_days_from_now(date_str)
    
    if days == 0:
        return "今天"
    elif days == 1:
        return "明天"
    elif days == 2:
        return "后天"
    elif days == -1:
        return "昨天"
    elif days == -2:
        return "前天"
    elif days > 0 and days <= 7:
        return f"{days}天后"
    elif days < 0 and days >= -7:
        return f"{abs(days)}天前"
    else:
        return f"{days}天"


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    验证日期范围是否有效
    
    Args:
        start_date: 开始日期，格式为"YYYY-MM-DD"
        end_date: 结束日期，格式为"YYYY-MM-DD"
    
    Returns:
        bool: 日期范围是否有效
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return start <= end
    except ValueError:
        return False