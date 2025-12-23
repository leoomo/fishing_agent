#!/usr/bin/env python3
"""地理编码歧义测试"""

import pytest
from packages.agents.fishing.utils.coordinate import (
    get_coordinates,
    select_best_geocode,
    is_within_bounds,
    GEOCODE_PRIORITY_BOUNDS
)


def test_heqiao_town_disambiguation():
    """测试河桥镇能正确定位到浙江省临安区"""
    coords = get_coordinates("河桥镇")
    longitude, latitude = coords

    # 验证在浙江省范围内
    assert is_within_bounds(longitude, latitude, GEOCODE_PRIORITY_BOUNDS), \
        f"河桥镇坐标不在浙江省范围内: ({longitude}, {latitude})"

    # 验证接近临安河桥镇（允许0.1°偏差）
    assert abs(longitude - 119.247232) < 0.1, "经度偏差过大"
    assert abs(latitude - 30.122528) < 0.1, "纬度偏差过大"


def test_explicit_context():
    """测试显式上下文查询仍正常"""
    coords1 = get_coordinates("临安区河桥镇")
    coords2 = get_coordinates("杭州市临安区河桥镇")

    # 应返回相近坐标
    assert abs(coords1[0] - coords2[0]) < 0.01, "临安区河桥镇坐标不一致"
    assert abs(coords1[1] - coords2[1]) < 0.01, "临安区河桥镇坐标不一致"


def test_bounds_check():
    """测试地理边界判断"""
    bounds = GEOCODE_PRIORITY_BOUNDS

    # 浙江省内
    assert is_within_bounds(119.247232, 30.122528, bounds) is True, \
        "临安河桥镇应在浙江省边界内"

    # 甘肃省
    assert is_within_bounds(102.886134, 36.49996, bounds) is False, \
        "甘肃河桥镇不应在浙江省边界内"


def test_select_best_geocode_province_match():
    """测试优先选择匹配省份的结果"""
    geocodes = [
        {
            'location': '102.886134,36.49996',
            'province': '甘肃省',
            'city': '白银市',
            'district': '景泰县'
        },
        {
            'location': '119.247232,30.122528',
            'province': '浙江省',
            'city': '杭州市',
            'district': '临安区'
        }
    ]

    bounds = GEOCODE_PRIORITY_BOUNDS
    best = select_best_geocode(geocodes, '浙江省', bounds)

    assert best is not None
    assert '浙江省' in best['province']
    assert '119.247232,30.122528' == best['location']


def test_select_best_geocode_bounds_match():
    """测试优先选择边界内的结果（无省份匹配时）"""
    geocodes = [
        {
            'location': '102.886134,36.49996',
            'province': '甘肃省',
            'city': '白银市',
            'district': '景泰县'
        },
        {
            'location': '119.247232,30.122528',
            'province': '江苏省',  # 假设省份不匹配
            'city': '某市',
            'district': '某区'
        }
    ]

    bounds = GEOCODE_PRIORITY_BOUNDS
    best = select_best_geocode(geocodes, '浙江省', bounds)

    assert best is not None
    # 应选择边界内的结果
    assert '119.247232,30.122528' == best['location']


def test_select_best_geocode_fallback():
    """测试回退到第一个结果（无匹配时）"""
    geocodes = [
        {
            'location': '102.886134,36.49996',
            'province': '甘肃省',
            'city': '白银市',
            'district': '景泰县'
        }
    ]

    bounds = GEOCODE_PRIORITY_BOUNDS
    best = select_best_geocode(geocodes, '浙江省', bounds)

    assert best is not None
    # 应回退到第一个结果
    assert '102.886134,36.49996' == best['location']
