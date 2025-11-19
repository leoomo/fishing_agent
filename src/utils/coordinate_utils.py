#!/usr/bin/env python3
"""
坐标工具模块

简化坐标获取逻辑，集成高德地图API和本地缓存，
移除了过度复杂的匹配器和抽象层。
"""

import os
import requests
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv
from .cache import cache

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 高德地图API配置
AMAP_API_KEY = os.getenv('AMAP_API_KEY')
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"

# 缓存配置
COORDINATE_CACHE_TTL = 86400  # 24小时


def get_coordinates(location: str) -> Tuple[float, float]:
    """
    获取位置坐标

    Args:
        location: 位置名称（支持中文地名）

    Returns:
        (longitude, latitude) 坐标元组

    Raises:
        ValueError: 无法获取坐标时抛出
    """
    if not location or not location.strip():
        raise ValueError("位置名称不能为空")

    location = location.strip()
    cache_key = f"coords:{location}"

    # 1. 检查缓存
    cached_coords = cache.get(cache_key)
    if cached_coords:
        logger.debug(f"从缓存获取坐标: {location} -> {cached_coords}")
        return cached_coords

    # 2. 调用高德地图API
    coords = _fetch_coordinates_from_api(location)
    if not coords:
        raise ValueError(f"无法获取位置坐标: {location}")

    # 3. 缓存结果
    cache.set(cache_key, coords, ttl=COORDINATE_CACHE_TTL)
    logger.info(f"获取坐标成功: {location} -> {coords}")

    return coords


def _fetch_coordinates_from_api(location: str) -> Optional[Tuple[float, float]]:
    """
    从高德地图API获取坐标

    Args:
        location: 位置名称

    Returns:
        坐标元组或None
    """
    if not AMAP_API_KEY:
        logger.error("未配置高德地图API密钥 (AMAP_API_KEY)")
        return None

    try:
        params = {
            'address': location,
            'key': AMAP_API_KEY,
            'output': 'json'
        }

        response = requests.get(AMAP_GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('status') == '1' and data.get('geocodes'):
            geocode = data['geocodes'][0]
            if geocode.get('location'):
                # 解析坐标: "120.12345,30.67890"
                location_str = geocode['location']
                lon_str, lat_str = location_str.split(',')
                longitude = float(lon_str)
                latitude = float(lat_str)
                return (longitude, latitude)
        else:
            logger.warning(f"高德API返回无坐标: {data}")
            return None

    except requests.RequestException as e:
        logger.error(f"高德API请求失败: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"解析高德API响应失败: {e}")
        return None


def validate_coordinates(coords: Tuple[float, float]) -> bool:
    """
    验证坐标是否有效

    Args:
        coords: 坐标元组 (longitude, latitude)

    Returns:
        是否有效
    """
    if not isinstance(coords, tuple) or len(coords) != 2:
        return False

    longitude, latitude = coords

    # 经度范围: -180 到 180
    # 纬度范围: -90 到 90
    try:
        lon_float = float(longitude)
        lat_float = float(latitude)
        return (-180 <= lon_float <= 180) and (-90 <= lat_float <= 90)
    except (ValueError, TypeError):
        return False


def format_coordinates(coords: Tuple[float, float]) -> str:
    """
    格式化坐标为字符串

    Args:
        coords: 坐标元组

    Returns:
        格式化的坐标字符串 "longitude,latitude"
    """
    if not validate_coordinates(coords):
        raise ValueError(f"无效的坐标: {coords}")

    return f"{coords[0]},{coords[1]}"


def clear_coordinate_cache(location: Optional[str] = None) -> int:
    """
    清理坐标缓存

    Args:
        location: 特定位置名称，None表示清理所有坐标缓存

    Returns:
        清理的缓存项数量
    """
    if location:
        cache_key = f"coords:{location}"
        return 1 if cache.delete(cache_key) else 0
    else:
        # 清理所有坐标缓存
        removed_count = 0
        for key in list(cache._memory_cache.keys()):
            if key.startswith("coords:"):
                if cache.delete(key):
                    removed_count += 1
        return removed_count


def get_cache_stats() -> dict:
    """
    获取坐标缓存统计

    Returns:
        缓存统计信息
    """
    stats = cache.get_stats()

    # 统计坐标相关缓存
    coordinate_count = sum(1 for key in cache._memory_cache.keys()
                         if key.startswith("coords:"))

    return {
        **stats,
        'coordinate_items': coordinate_count
    }