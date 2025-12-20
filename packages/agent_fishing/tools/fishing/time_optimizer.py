#!/usr/bin/env python3
"""
时段优化器模块

职责:
- 查找24小时内最佳连续时段
- 按用户指定时间段过滤(白天/晚上/上午等)
- 时间范围判断和验证
- 评分趋势可视化
"""

from typing import Dict, Any, List
from datetime import datetime, date, time, timedelta
import logging

logger = logging.getLogger(__name__)


def filter_time_slots_by_period(
    time_slots: List[Dict[str, Any]],
    hourly_datetimes: List[datetime],
    time_period: str = None
) -> List[Dict[str, Any]]:
    """
    根据时间段过滤推荐时段

    Args:
        time_slots: 候选时段列表（由 find_best_time_slots 返回）
        hourly_datetimes: 小时级时间戳列表（与时段索引对应）
        time_period: 时间段限制（"白天"/"晚上"/"上午"/"下午"/None）

    Returns:
        过滤后的时段列表

    Implementation Notes:
        - 每个时段有 start_hour 和 end_hour，对应实际的小时数
        - 通过小时数判断时段是否在指定范围内
        - 时段过滤规则：时段的所有小时必须在指定范围内

    Examples:
        输入: time_slots=[{"start_hour": 10, "end_hour": 13, ...}]  # 10:00-13:00
              time_period="上午"  # 6:00-12:00
        输出: []  # 因为13:00超出上午范围

        输入: time_slots=[{"start_hour": 8, "end_hour": 11, ...}]   # 8:00-11:00
              time_period="上午"  # 6:00-12:00
        输出: [{"start_hour": 8, "end_hour": 11, ...}]  # 完全在上午范围内
    """
    # 标准化时间段名称
    normalized_period = normalize_time_period(time_period)

    # 全天模式，不过滤
    if normalized_period == "全天":
        return time_slots

    # 获取时间范围配置
    period_config = TIME_PERIOD_DEFINITIONS.get(normalized_period)
    if not period_config:
        return time_slots  # 未识别的时间段，返回全部

    start_hour = period_config["start"]
    end_hour = period_config["end"]
    cross_midnight = period_config.get("cross_midnight", False)

    filtered_slots = []

    for slot in time_slots:
        slot_start_hour = slot.get("start_hour")
        slot_end_hour = slot.get("end_hour")

        # 安全检查
        if slot_start_hour is None or slot_end_hour is None:
            continue

        # 判断时段是否在指定范围内
        if is_slot_in_time_range(
            slot_start_hour,
            slot_end_hour,
            start_hour,
            end_hour,
            cross_midnight
        ):
            filtered_slots.append(slot)

    return filtered_slots


def is_slot_in_time_range(
    slot_start: int,
    slot_end: int,
    range_start: int,
    range_end: int,
    cross_midnight: bool = False
) -> bool:
    """
    判断时段是否在指定时间范围内

    Args:
        slot_start: 时段起始小时（0-23）
        slot_end: 时段结束小时（0-23）
        range_start: 范围起始小时（0-23）
        range_end: 范围结束小时（0-23）
        cross_midnight: 范围是否跨越午夜（如晚上18:00-次日6:00）

    Returns:
        bool: 时段是否完全在范围内

    Logic:
        - 要求时段的**所有小时**都在范围内
        - 支持跨午夜范围（如18:00-6:00）

    Examples:
        >>> is_slot_in_time_range(8, 10, 6, 12, False)
        True  # 8:00-10:00 完全在 6:00-12:00 内

        >>> is_slot_in_time_range(11, 13, 6, 12, False)
        False  # 13:00 超出 12:00

        >>> is_slot_in_time_range(20, 22, 18, 6, True)
        True  # 20:00-22:00 在 18:00-次日6:00 内
    """
    if not cross_midnight:
        # 正常范围（不跨午夜）
        return slot_start >= range_start and slot_end <= range_end
    else:
        # 跨午夜范围（如18:00-6:00）
        # 拆分为两个范围：[range_start, 24) 和 [0, range_end)
        in_evening = slot_start >= range_start and slot_end >= range_start
        in_morning = slot_start < range_end and slot_end < range_end
        return in_evening or in_morning


def merge_adjacent_slots(
    slots: List[Dict[str, Any]],
    hourly_scores: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    合并相邻且评分相同的时段

    Args:
        slots: 已选时段列表
        hourly_scores: 原始24小时评分列表（用于重新计算合并后的数据）

    Returns:
        合并后的时段列表

    Examples:
        输入: [{6:00-10:00, 85分}, {10:00-12:00, 85分}]
        输出: [{6:00-12:00, 85分}]  # 评分相同，合并

        输入: [{6:00-10:00, 85分}, {10:00-12:00, 83分}]
        输出: [{6:00-10:00, 85分}, {10:00-12:00, 83分}]  # 评分不同，不合并
    """
    if len(slots) <= 1:
        return slots

    # 按起始时间排序
    sorted_slots = sorted(slots, key=lambda x: x['start_hour'])

    merged = []
    current = sorted_slots[0].copy()

    for slot in sorted_slots[1:]:
        # 判断是否可以合并：相邻且评分完全相同
        if (slot['start_hour'] == current['end_hour'] and
                slot['avg_score'] == current['avg_score']):
            # 合并时段：重新从 hourly_scores 计算
            new_start = current['start_hour']
            new_end = slot['end_hour']
            window_scores = hourly_scores[new_start:new_end]

            # 重新计算所有指标
            current = _build_slot_from_window(window_scores, new_start, new_end)
        else:
            merged.append(current)
            current = slot.copy()

    merged.append(current)
    return merged


def _build_slot_from_window(
    window_scores: List[Dict[str, Any]],
    start_idx: int,
    end_idx: int
) -> Dict[str, Any]:
    """
    从小时评分窗口构建时段数据

    Args:
        window_scores: 窗口内的小时评分列表
        start_idx: 起始索引
        end_idx: 结束索引

    Returns:
        时段字典
    """
    window_size = len(window_scores)

    # 计算平均评分
    avg_score = sum(h['score'] for h in window_scores) / window_size

    # 获取时间范围
    start_time = window_scores[0]['time_str']
    last_dt = window_scores[-1].get('datetime')
    if last_dt:
        end_dt = last_dt + timedelta(hours=1)
        end_time = end_dt.strftime('%H:%M')
    else:
        last_hour = int(window_scores[-1]['time_str'].split(':')[0])
        end_hour = (last_hour + 1) % 24
        end_time = f"{end_hour:02d}:00"

    # 计算平均天气数据
    avg_temp = sum(h['temperature'] for h in window_scores) / window_size
    avg_wind = sum(h['wind_speed'] for h in window_scores) / window_size
    avg_humidity = sum(h['humidity'] for h in window_scores) / window_size
    avg_pressure = sum(h['pressure'] for h in window_scores) / window_size

    # 获取温度和风速范围
    min_temp = min(h['temperature'] for h in window_scores)
    max_temp = max(h['temperature'] for h in window_scores)
    min_wind = min(h['wind_speed'] for h in window_scores)
    max_wind = max(h['wind_speed'] for h in window_scores)

    # 获取主要天气状况
    conditions = [h['condition'] for h in window_scores]
    main_condition = max(set(conditions), key=conditions.count)

    return {
        'start_hour': start_idx,
        'end_hour': end_idx,
        'start_time': start_time,
        'end_time': end_time,
        'time_range': f"{start_time}-{end_time}",
        'duration_hours': window_size,
        'avg_score': avg_score,
        'temperature': avg_temp,
        'temp_min': min_temp,
        'temp_max': max_temp,
        'condition': main_condition,
        'wind_speed': avg_wind,
        'wind_min': min_wind,
        'wind_max': max_wind,
        'humidity': avg_humidity,
        'pressure': avg_pressure
    }


def find_best_time_slots(hourly_scores: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
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
                # 从最后一个时间点的datetime计算结束时间
                last_dt = window_scores[-1].get('datetime')
                if last_dt:
                    end_dt = last_dt + timedelta(hours=1)
                    end_time = end_dt.strftime('%H:%M')
                else:
                    # 回退：从time_str解析
                    last_hour = int(window_scores[-1]['time_str'].split(':')[0])
                    end_hour = (last_hour + 1) % 24
                    end_time = f"{end_hour:02d}:00"

                # 获取窗口内的平均天气数据
                avg_temp = sum(h['temperature'] for h in window_scores) / len(window_scores)
                avg_wind = sum(h['wind_speed'] for h in window_scores) / len(window_scores)
                avg_humidity = sum(h['humidity'] for h in window_scores) / len(window_scores)
                avg_pressure = sum(h['pressure'] for h in window_scores) / len(window_scores)

                # 获取温度和风速范围
                min_temp = min(h['temperature'] for h in window_scores)
                max_temp = max(h['temperature'] for h in window_scores)
                min_wind = min(h['wind_speed'] for h in window_scores)
                max_wind = max(h['wind_speed'] for h in window_scores)

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
                    'temp_min': min_temp,
                    'temp_max': max_temp,
                    'condition': main_condition,
                    'wind_speed': avg_wind,
                    'wind_min': min_wind,
                    'wind_max': max_wind,
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

        # 合并相邻且评分接近的时段
        merged_slots = merge_adjacent_slots(selected_slots, hourly_scores)

        # 按评分降序排序，确保🥇对应最高分
        merged_slots.sort(key=lambda x: x['avg_score'], reverse=True)

        logger.info(f"成功检测{len(merged_slots)}个最佳钓鱼时段（合并前{len(selected_slots)}个）")
        return merged_slots

    except Exception as e:
        logger.error(f"智能时段检测失败: {e}")
        return []


def generate_score_trend(hourly_scores: List[Dict[str, Any]]) -> str:
    """
    生成24小时评分趋势（4时段+进度条，适配手机屏幕）

    Args:
        hourly_scores: 24小时评分列表

    Returns:
        4时段进度条格式的趋势图字符串
    """
    try:
        if not hourly_scores:
            return "无评分数据"

        # 时段定义
        periods = [
            ("🌅 凌晨", 0, 6),
            ("🌞 上午", 6, 12),
            ("☀️ 下午", 12, 18),
            ("🌙 晚上", 18, 24),
        ]

        def make_progress_bar(score: float, width: int = 10) -> str:
            """生成进度条"""
            filled = int((score / 100) * width)
            return "█" * filled + "░" * (width - filled)

        # 计算每个时段平均分
        period_scores = []
        for name, start, end in periods:
            # 确保不超出列表范围
            actual_end = min(end, len(hourly_scores))
            if start < actual_end:
                segment = hourly_scores[start:actual_end]
                avg = sum(s['score'] for s in segment) / len(segment)
                period_scores.append((name, start, end, avg))

        if not period_scores:
            return "无评分数据"

        # 找最佳时段
        best_idx = max(range(len(period_scores)), key=lambda i: period_scores[i][3])

        # 生成输出
        lines = ["📊 24小时评分概览", ""]
        for i, (name, start, end, avg) in enumerate(period_scores):
            bar = make_progress_bar(avg)
            best_mark = " ⬅️最佳" if i == best_idx else ""
            lines.append(f"{name} {start:02d}-{end:02d}  {bar} {avg:.0f}分{best_mark}")

        # 添加统计
        all_scores = [s['score'] for s in hourly_scores]
        max_score = max(all_scores)
        max_idx = all_scores.index(max_score)
        avg_score = sum(all_scores) / len(all_scores)
        max_time = hourly_scores[max_idx]['time_str']

        lines.append("")
        lines.append(f"📈 全天均分: {avg_score:.0f}分 | 峰值: {max_score:.0f}分({max_time})")
        lines.append("")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"生成评分趋势图失败: {e}")
        return f"评分趋势图生成失败: {str(e)}"


