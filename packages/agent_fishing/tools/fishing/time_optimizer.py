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

        # 保持按评分降序排序，确保🥇对应最高分

        logger.info(f"成功检测{len(selected_slots)}个最佳钓鱼时段")
        return selected_slots

    except Exception as e:
        logger.error(f"智能时段检测失败: {e}")
        return []


def generate_score_trend(hourly_scores: List[Dict[str, Any]]) -> str:
    """
    生成24小时评分趋势ASCII可视化图

    Args:
        hourly_scores: 24小时评分列表

    Returns:
        ASCII趋势图字符串
    """
    try:
        if not hourly_scores:
            return "无评分数据"

        # 提取评分
        scores = [h['score'] for h in hourly_scores]
        hours = [h['time_str'] for h in hourly_scores]

        # 计算统计信息
        max_score = max(scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)

        # 构建趋势图
        chart = []
        chart.append("📊 24小时钓鱼评分趋势")
        chart.append("=" * 50)
        chart.append("")

        # 评分刻度（10个等级，从0到100）
        height = 10  # 图表高度
        width = len(scores)  # 图表宽度

        # 绘制图表主体
        for level in range(height, 0, -1):
            score_threshold = (level / height) * 100
            line = f"{int(score_threshold):3d} ┃ "

            for score in scores:
                if score >= score_threshold:
                    line += "█"
                else:
                    line += " "

            chart.append(line)

        # 绘制底部分隔线
        chart.append("    ┗" + "━" * width)

        # 绘制时间轴（简化版：只显示关键时刻）
        time_axis = "      "
        for i, hour_str in enumerate(hours):
            if i % 4 == 0:  # 每4小时显示一次
                hour = hour_str.split(':')[0]
                time_axis += f"{hour:2s}  "

        chart.append(time_axis + " (时)")
        chart.append("")

        # 添加统计信息
        chart.append(f"📈 统计数据:")
        chart.append(f"   最高评分: {max_score:.1f}分")
        chart.append(f"   最低评分: {min_score:.1f}分")
        chart.append(f"   平均评分: {avg_score:.1f}分")
        chart.append("")

        return "\n".join(chart)

    except Exception as e:
        logger.error(f"生成评分趋势图失败: {e}")
        return f"评分趋势图生成失败: {str(e)}"


