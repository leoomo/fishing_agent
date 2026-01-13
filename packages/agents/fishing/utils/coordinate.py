#!/usr/bin/env python3
"""
坐标工具模块

简化坐标获取逻辑，集成高德地图API和本地缓存，
支持本地数据库优先查询和API结果回写。
"""

import os
import time
import sqlite3
import requests
import logging
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv
from .cache import cache

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 高德地图API配置
AMAP_API_KEY = os.getenv('AMAP_API_KEY')
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"

# 百度地图API配置（备用）
BAIDU_MAP_AK = os.getenv('BAIDU_MAP_AK')
BAIDU_GEOCODE_URL = "https://api.map.baidu.com/geocoding/v3/"

# 缓存配置
COORDINATE_CACHE_TTL = 86400  # 24小时

# 本地数据库路径
DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "shared" / "data"
TOWN_COORDS_DB = DATA_DIR / "town_coordinates.db"
ADMIN_DIVISIONS_DB = DATA_DIR / "admin_divisions.db"

# 地理编码优先区域配置
GEOCODE_PRIORITY_PROVINCE = os.getenv('GEOCODE_PRIORITY_PROVINCE', '浙江省')

# 浙江省经纬度范围（用于地理围栏）
GEOCODE_PRIORITY_BOUNDS = {
    'lon_min': float(os.getenv('GEOCODE_LON_MIN', '118.0')),
    'lon_max': float(os.getenv('GEOCODE_LON_MAX', '123.0')),
    'lat_min': float(os.getenv('GEOCODE_LAT_MIN', '27.0')),
    'lat_max': float(os.getenv('GEOCODE_LAT_MAX', '31.0'))
}


def get_coordinates(location: str) -> Tuple[float, float]:
    """
    获取位置坐标

    查询优先级：
    1. 内存缓存
    2. 本地数据库（coordinate_cache -> town_coordinates -> regions）
    3. 高德地图API
    4. 百度地图API（备用，如已配置）

    API查询成功后会回写到本地数据库，避免重复调用。

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

    # 1. 检查内存缓存
    cached_coords = cache.get(cache_key)
    if cached_coords:
        logger.debug(f"从内存缓存获取坐标: {location} -> {cached_coords}")
        return cached_coords

    # 2. 查询本地数据库
    coords = _query_local_database(location)
    if coords:
        cache.set(cache_key, coords, ttl=COORDINATE_CACHE_TTL)
        logger.info(f"从本地数据库获取坐标: {location} -> {coords}")
        return coords

    # 3. 调用API（带备用）
    coords, source = _fetch_coordinates_with_fallback(location)
    if coords:
        # 4. 回写到本地数据库
        _save_to_local_database(location, coords, source)
        cache.set(cache_key, coords, ttl=COORDINATE_CACHE_TTL)
        logger.info(f"从{source}获取坐标: {location} -> {coords}")
        return coords

    raise ValueError(f"无法获取位置坐标: {location}")


def _fetch_coordinates_from_api(location: str) -> Optional[Tuple[float, float]]:
    """
    从高德地图API获取坐标（支持多结果智能选择）

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
            geocodes = data['geocodes']

            # 记录多结果情况
            if len(geocodes) > 1:
                logger.info(f"地名 '{location}' 有 {len(geocodes)} 个匹配结果，执行智能选择")

            # 使用智能选择逻辑
            best_geocode = select_best_geocode(
                geocodes,
                GEOCODE_PRIORITY_PROVINCE,
                GEOCODE_PRIORITY_BOUNDS
            )

            if best_geocode and best_geocode.get('location'):
                location_str = best_geocode['location']
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


def _query_local_database(location: str) -> Optional[Tuple[float, float]]:
    """
    从本地数据库查询坐标

    查询顺序：
    1. coordinate_cache（API查询结果缓存）
    2. town_coordinates（乡镇坐标）
    3. regions（行政区划）

    Args:
        location: 位置名称

    Returns:
        坐标元组或None
    """
    # 1. 优先查询 coordinate_cache（API查询结果缓存）
    coords = _query_coordinate_cache(location)
    if coords:
        return coords

    # 2. 查询 town_coordinates（乡镇坐标）
    coords = _query_town_coordinates(location)
    if coords:
        return coords

    # 3. 查询 regions（行政区划）
    coords = _query_admin_divisions(location)
    if coords:
        return coords

    return None


def _query_coordinate_cache(location: str) -> Optional[Tuple[float, float]]:
    """查询坐标缓存表（存储API查询结果）"""
    if not ADMIN_DIVISIONS_DB.exists():
        return None

    try:
        conn = sqlite3.connect(str(ADMIN_DIVISIONS_DB))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT longitude, latitude FROM coordinate_cache
            WHERE place_name = ?
            LIMIT 1
        """, (location,))
        row = cursor.fetchone()

        if row:
            # 更新查询计数
            cursor.execute("""
                UPDATE coordinate_cache SET query_count = query_count + 1, updated_at = ?
                WHERE place_name = ?
            """, (time.time(), location))
            conn.commit()

        conn.close()
        if row and row[0] and row[1]:
            logger.debug(f"从coordinate_cache获取坐标: {location}")
            return (float(row[0]), float(row[1]))
    except Exception as e:
        logger.debug(f"查询coordinate_cache失败: {e}")

    return None


def _query_town_coordinates(location: str) -> Optional[Tuple[float, float]]:
    """查询乡镇坐标库"""
    if not TOWN_COORDS_DB.exists():
        return None

    try:
        conn = sqlite3.connect(str(TOWN_COORDS_DB))
        cursor = conn.cursor()

        # 优先精确匹配 name 字段
        cursor.execute("""
            SELECT longitude, latitude FROM town_coordinates
            WHERE name = ?
            ORDER BY accuracy_level DESC LIMIT 1
        """, (location,))
        row = cursor.fetchone()

        if not row:
            # 模糊匹配 full_name
            cursor.execute("""
                SELECT longitude, latitude FROM town_coordinates
                WHERE full_name LIKE ?
                ORDER BY accuracy_level DESC LIMIT 1
            """, (f"%{location}%",))
            row = cursor.fetchone()

        conn.close()
        if row and row[0] and row[1]:
            logger.debug(f"从town_coordinates获取坐标: {location}")
            return (float(row[0]), float(row[1]))
    except Exception as e:
        logger.debug(f"查询town_coordinates失败: {e}")

    return None


def _query_admin_divisions(location: str) -> Optional[Tuple[float, float]]:
    """查询行政区划库"""
    if not ADMIN_DIVISIONS_DB.exists():
        return None

    try:
        conn = sqlite3.connect(str(ADMIN_DIVISIONS_DB))
        cursor = conn.cursor()

        # 精确匹配
        cursor.execute("""
            SELECT longitude, latitude FROM regions
            WHERE name = ? AND longitude IS NOT NULL AND latitude IS NOT NULL
            ORDER BY level ASC LIMIT 1
        """, (location,))
        row = cursor.fetchone()

        if not row:
            # 模糊匹配
            cursor.execute("""
                SELECT longitude, latitude FROM regions
                WHERE name LIKE ? AND longitude IS NOT NULL AND latitude IS NOT NULL
                ORDER BY level ASC LIMIT 1
            """, (f"%{location}%",))
            row = cursor.fetchone()

        conn.close()
        if row and row[0] and row[1]:
            logger.debug(f"从regions获取坐标: {location}")
            return (float(row[0]), float(row[1]))
    except Exception as e:
        logger.debug(f"查询admin_divisions失败: {e}")

    return None


def _save_to_local_database(location: str, coords: Tuple[float, float], source: str) -> None:
    """
    将API查询结果保存到本地数据库

    Args:
        location: 位置名称
        coords: 坐标元组 (longitude, latitude)
        source: 数据来源（如 amap_api, baidu_api）
    """
    if not ADMIN_DIVISIONS_DB.exists():
        return

    try:
        conn = sqlite3.connect(str(ADMIN_DIVISIONS_DB))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO coordinate_cache
            (place_name, full_address, longitude, latitude, data_source, created_at, updated_at, query_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            location,
            location,
            coords[0],
            coords[1],
            source,
            time.time(),
            time.time()
        ))

        conn.commit()
        conn.close()
        logger.info(f"坐标已保存到本地数据库: {location} -> {coords}")
    except Exception as e:
        logger.debug(f"保存坐标到本地数据库失败: {e}")


def _fetch_coordinates_with_fallback(location: str) -> Tuple[Optional[Tuple[float, float]], str]:
    """
    带备用的API查询

    Args:
        location: 位置名称

    Returns:
        (坐标元组, 数据来源) 或 (None, "")
    """
    # 1. 尝试高德API
    coords = _fetch_coordinates_from_api(location)
    if coords:
        return coords, "amap_api"

    # 2. 尝试百度API（如已配置）
    if BAIDU_MAP_AK:
        coords = _fetch_from_baidu(location)
        if coords:
            return coords, "baidu_api"

    return None, ""


def _fetch_from_baidu(location: str) -> Optional[Tuple[float, float]]:
    """
    从百度地图API获取坐标（备用）

    Args:
        location: 位置名称

    Returns:
        坐标元组或None
    """
    try:
        params = {
            'address': location,
            'ak': BAIDU_MAP_AK,
            'output': 'json'
        }
        response = requests.get(BAIDU_GEOCODE_URL, params=params, timeout=10)
        data = response.json()

        if data.get('status') == 0 and data.get('result'):
            loc = data['result']['location']
            return (loc['lng'], loc['lat'])
    except Exception as e:
        logger.error(f"百度API请求失败: {e}")

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


def is_within_bounds(longitude: float, latitude: float, bounds: dict) -> bool:
    """
    检查坐标是否在指定边界内

    Args:
        longitude: 经度
        latitude: 纬度
        bounds: 边界字典 {lon_min, lon_max, lat_min, lat_max}

    Returns:
        是否在边界内
    """
    return (bounds['lon_min'] <= longitude <= bounds['lon_max'] and
            bounds['lat_min'] <= latitude <= bounds['lat_max'])


def select_best_geocode(geocodes: list, priority_province: str, priority_bounds: dict) -> Optional[dict]:
    """
    从多个地理编码结果中选择最佳匹配

    优先级：
    1. 优先选择指定省份内的结果
    2. 其次选择优先区域边界内的结果
    3. 最后回退到第一个结果

    Args:
        geocodes: 高德API返回的geocodes数组
        priority_province: 优先省份名称
        priority_bounds: 优先区域边界

    Returns:
        选中的geocode字典，或None
    """
    if not geocodes:
        return None

    # 解析所有有效的geocode
    candidates = []
    for geocode in geocodes:
        location_str = geocode.get('location')
        if not location_str:
            continue

        try:
            lon_str, lat_str = location_str.split(',')
            longitude = float(lon_str)
            latitude = float(lat_str)

            province = geocode.get('province', '')
            city = geocode.get('city', '')
            district = geocode.get('district', '')

            candidates.append({
                'longitude': longitude,
                'latitude': latitude,
                'province': province,
                'city': city,
                'district': district,
                'raw': geocode
            })
        except (ValueError, AttributeError) as e:
            logger.debug(f"解析geocode失败: {e}")
            continue

    if not candidates:
        return None

    # 策略1: 优先选择指定省份
    province_matches = [c for c in candidates if priority_province in c['province']]
    if province_matches:
        best = province_matches[0]
        logger.info(f"✅ 地名匹配: {best['province']}{best['city']}{best['district']} "
                   f"[{best['longitude']:.6f}, {best['latitude']:.6f}]")
        return best['raw']

    # 策略2: 选择地理边界内的结果
    bounds_matches = [c for c in candidates
                     if is_within_bounds(c['longitude'], c['latitude'], priority_bounds)]
    if bounds_matches:
        best = bounds_matches[0]
        logger.info(f"⚠️ 边界匹配: {best['province']}{best['city']}{best['district']} "
                   f"[{best['longitude']:.6f}, {best['latitude']:.6f}]")
        return best['raw']

    # 策略3: 回退到第一个结果
    fallback = candidates[0]
    logger.warning(f"⚠️ 使用首个结果: {fallback['province']}{fallback['city']}{fallback['district']} "
                  f"[{fallback['longitude']:.6f}, {fallback['latitude']:.6f}]")
    return fallback['raw']


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