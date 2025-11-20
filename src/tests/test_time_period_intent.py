#!/usr/bin/env python3
"""
时间段意图理解测试套件

测试目标:
1. 验证 time_period 参数正确传递
2. 验证时段过滤逻辑准确性
3. 验证边界情况处理
"""

import pytest
from datetime import datetime
try:
    from src.tools.fishing_tools import (
        query_fishing_recommendation,
        _filter_time_slots_by_period,
        _is_slot_in_time_range,
        normalize_time_period
    )
except ImportError:
    # 从tests目录运行时的相对导入
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.tools.fishing_tools import (
        query_fishing_recommendation,
        _filter_time_slots_by_period,
        _is_slot_in_time_range,
        normalize_time_period
    )


class TestTimePeriodNormalization:
    """测试时间段标准化功能"""

    def test_normalize_standard_names(self):
        """测试标准名称"""
        assert normalize_time_period("白天") == "白天"
        assert normalize_time_period("晚上") == "晚上"
        assert normalize_time_period("上午") == "上午"
        assert normalize_time_period("下午") == "下午"

    def test_normalize_aliases(self):
        """测试别名映射"""
        assert normalize_time_period("daytime") == "白天"
        assert normalize_time_period("早上") == "上午"
        assert normalize_time_period("夜间") == "晚上"
        assert normalize_time_period("afternoon") == "下午"

    def test_normalize_invalid(self):
        """测试无效输入"""
        assert normalize_time_period("invalid") == "全天"
        assert normalize_time_period("") == "全天"
        assert normalize_time_period(None) == "全天"


class TestTimeRangeCheck:
    """测试时间范围判断逻辑"""

    def test_normal_range_within(self):
        """测试正常范围内的时段"""
        # 8:00-10:00 在 6:00-12:00 内
        assert _is_slot_in_time_range(8, 10, 6, 12, False) is True

    def test_normal_range_outside(self):
        """测试超出正常范围的时段"""
        # 11:00-13:00 超出 6:00-12:00
        assert _is_slot_in_time_range(11, 13, 6, 12, False) is False

    def test_cross_midnight_evening(self):
        """测试跨午夜范围（晚上时段）"""
        # 20:00-22:00 在 18:00-次日6:00 内
        assert _is_slot_in_time_range(20, 22, 18, 6, True) is True

    def test_cross_midnight_morning(self):
        """测试跨午夜范围（凌晨时段）"""
        # 2:00-4:00 在 18:00-次日6:00 内
        assert _is_slot_in_time_range(2, 4, 18, 6, True) is True

    def test_cross_midnight_outside(self):
        """测试不在跨午夜范围内的时段"""
        # 10:00-12:00 不在 18:00-次日6:00 内
        assert _is_slot_in_time_range(10, 12, 18, 6, True) is False


class TestTimeSlotFiltering:
    """测试时段过滤功能"""

    @pytest.fixture
    def mock_hourly_datetimes(self):
        """模拟24小时时间戳"""
        base_date = datetime(2024, 12, 25, 0, 0, 0)
        return [base_date.replace(hour=h) for h in range(24)]

    @pytest.fixture
    def mock_time_slots(self):
        """模拟候选时段"""
        return [
            {"start_hour": 8, "end_hour": 10, "time_range": "08:00-10:00", "avg_score": 85.0},   # 上午
            {"start_hour": 14, "end_hour": 16, "time_range": "14:00-16:00", "avg_score": 80.0},  # 下午
            {"start_hour": 20, "end_hour": 22, "time_range": "20:00-22:00", "avg_score": 75.0},  # 晚上
        ]

    def test_filter_daytime(self, mock_time_slots, mock_hourly_datetimes):
        """测试过滤白天时段"""
        filtered = _filter_time_slots_by_period(
            mock_time_slots,
            mock_hourly_datetimes,
            "白天"
        )
        # 白天(6-18h): 应保留08:00-10:00和14:00-16:00，排除20:00-22:00
        assert len(filtered) == 2
        assert filtered[0]["time_range"] == "08:00-10:00"
        assert filtered[1]["time_range"] == "14:00-16:00"

    def test_filter_morning(self, mock_time_slots, mock_hourly_datetimes):
        """测试过滤上午时段"""
        filtered = _filter_time_slots_by_period(
            mock_time_slots,
            mock_hourly_datetimes,
            "上午"
        )
        # 上午(6-12h): 应只保留08:00-10:00
        assert len(filtered) == 1
        assert filtered[0]["time_range"] == "08:00-10:00"

    def test_filter_afternoon(self, mock_time_slots, mock_hourly_datetimes):
        """测试过滤下午时段"""
        filtered = _filter_time_slots_by_period(
            mock_time_slots,
            mock_hourly_datetimes,
            "下午"
        )
        # 下午(12-18h): 应只保留14:00-16:00
        assert len(filtered) == 1
        assert filtered[0]["time_range"] == "14:00-16:00"

    def test_filter_night(self, mock_time_slots, mock_hourly_datetimes):
        """测试过滤晚上时段"""
        filtered = _filter_time_slots_by_period(
            mock_time_slots,
            mock_hourly_datetimes,
            "晚上"
        )
        # 晚上(18-6h): 应只保留20:00-22:00
        assert len(filtered) == 1
        assert filtered[0]["time_range"] == "20:00-22:00"

    def test_filter_all_day(self, mock_time_slots, mock_hourly_datetimes):
        """测试全天模式（不过滤）"""
        filtered = _filter_time_slots_by_period(
            mock_time_slots,
            mock_hourly_datetimes,
            "全天"
        )
        # 全天: 应保留所有时段
        assert len(filtered) == 3

    def test_filter_none_period(self, mock_time_slots, mock_hourly_datetimes):
        """测试无时间段限制"""
        filtered = _filter_time_slots_by_period(
            mock_time_slots,
            mock_hourly_datetimes,
            None
        )
        # None: 应保留所有时段
        assert len(filtered) == 3


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_time_slots(self):
        """测试空时段列表"""
        filtered = _filter_time_slots_by_period([], [], "白天")
        assert filtered == []

    def test_invalid_indices(self):
        """测试无效索引"""
        slots = [{"start_hour": None, "end_hour": None}]
        datetimes = [datetime.now()]
        filtered = _filter_time_slots_by_period(slots, datetimes, "白天")
        assert len(filtered) == 0  # 应跳过无效时段

    def test_missing_indices(self):
        """测试缺少索引字段"""
        slots = [{"time_range": "08:00-10:00"}]  # 缺少 start_hour/end_hour
        datetimes = [datetime.now() for _ in range(24)]
        filtered = _filter_time_slots_by_period(slots, datetimes, "白天")
        assert len(filtered) == 0  # 应跳过缺少索引的时段


class TestToolIntegration:
    """工具集成测试"""

    def test_tool_signature_accepts_time_period(self):
        """测试工具签名接受time_period参数"""
        # 检查工具的描述是否包含time_period参数说明
        tool_description = query_fishing_recommendation.description

        # 验证工具描述中包含新的time_period参数
        assert "time_period:" in tool_description
        assert "时间段限制" in tool_description
        assert "白天" in tool_description
        assert "晚上" in tool_description

    def test_time_period_standardization_in_tool(self):
        """测试工具内部时间段标准化"""
        # 由于需要真实API密钥，这里只测试参数标准化逻辑
        try:
            from src.tools.fishing_tools import normalize_time_period
        except ImportError:
            # 从tests目录运行时的相对导入
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            from src.tools.fishing_tools import normalize_time_period

        # 测试各种输入都能正确标准化
        test_cases = [
            ("白天", "白天"),
            ("daytime", "白天"),
            ("早上", "上午"),
            ("MORNING", "上午"),  # 大小写不敏感
            ("晚上", "晚上"),
            ("invalid", "全天"),
            ("", "全天"),
            (None, "全天"),
        ]

        for input_val, expected in test_cases:
            result = normalize_time_period(input_val)
            assert result == expected, f"输入 '{input_val}' 应返回 '{expected}'，实际返回 '{result}'"


# ===== 运行测试 =====
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])