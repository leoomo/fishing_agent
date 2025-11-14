#!/usr/bin/env python3
"""
真实坐标服务 - 针对河桥镇问题的解决方案
结合高德API和现有本地数据的混合方案
"""

import os
import sqlite3
import requests
import time
import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class PlaceCoordinate:
    """地名坐标数据"""
    place_name: str
    full_address: str
    province: str
    city: str
    district: str
    longitude: float
    latitude: float
    level: str
    data_source: str  # 'local_db', 'amap_api', 'fallback'
    confidence: float
    is_approximation: bool = False
    approximation_reason: str = ""

class RealCoordinateService:
    """真实坐标服务 - 混合方案"""

    def __init__(self):
        """初始化服务"""
        # 数据库路径
        self.coords_db_path = Path("src/data/admin_divisions.db")
        self.cache_db_path = Path("src/data/coordinates_cache.db")

        # 确保目录存在
        self.coords_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)

        # 高德API配置
        self.api_key = os.getenv('AMAP_API_KEY')

        # API调用控制
        self.last_api_call = 0
        self.min_call_interval = 1.0  # 增加间隔避免QPS限制
        self.daily_call_count = 0
        self.last_reset_day = time.localtime().tm_yday

        # 初始化数据库
        self._init_cache_db()

        logger.info("真实坐标服务初始化完成")

    def _init_cache_db(self) -> None:
        """初始化缓存数据库"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS coordinate_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        place_name TEXT NOT NULL,
                        full_address TEXT,
                        province TEXT,
                        city TEXT,
                        district TEXT,
                        longitude REAL NOT NULL,
                        latitude REAL NOT NULL,
                        level TEXT,
                        data_source TEXT NOT NULL,
                        confidence REAL,
                        is_approximation BOOLEAN DEFAULT FALSE,
                        approximation_reason TEXT,
                        created_at REAL NOT NULL,
                        query_count INTEGER DEFAULT 0,
                        UNIQUE(place_name, full_address)
                    )
                """)

                # 创建索引
                conn.execute("CREATE INDEX IF NOT EXISTS idx_place_name ON coordinate_cache(place_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON coordinate_cache(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_data_source ON coordinate_cache(data_source)")

                conn.commit()
                logger.info("缓存数据库初始化完成")

        except Exception as e:
            logger.error(f"缓存数据库初始化失败: {e}")
            raise

    def get_coordinate(self, place_name: str,
                      city: Optional[str] = None,
                      province: Optional[str] = None) -> Optional[PlaceCoordinate]:
        """
        获取坐标 - 优先本地数据库和缓存

        Args:
            place_name: 地名
            city: 城市（可选）
            province: 省份（可选）

        Returns:
            坐标数据或None
        """
        logger.debug(f"查询坐标: {place_name}")

        # 1. 优先查询缓存
        cached_result = self._get_from_cache(place_name, city, province)
        if cached_result:
            logger.debug(f"缓存命中: {place_name}")
            return cached_result

        # 2. 查询本地行政区划数据库
        local_result = self._get_from_local_db(place_name, city, province)
        if local_result:
            logger.debug(f"本地数据库命中: {place_name}")
            # 缓存结果
            self._save_to_cache(local_result)
            return local_result

        # 3. 调用高德API（带QPS控制）
        api_result = self._call_amap_api_safely(place_name, city, province)
        if api_result:
            logger.info(f"高德API命中: {place_name}")
            # 缓存结果
            self._save_to_cache(api_result)
            return api_result

        # 4. 降级处理
        fallback_result = self._get_fallback_coordinate(place_name, city, province)
        if fallback_result:
            logger.info(f"降级匹配: {place_name} -> {fallback_result.full_address}")
            # 缓存结果
            self._save_to_cache(fallback_result)
            return fallback_result

        logger.warning(f"未找到坐标: {place_name}")
        return None

    def _get_from_cache(self, place_name: str,
                        city: Optional[str] = None,
                        province: Optional[str] = None) -> Optional[PlaceCoordinate]:
        """从缓存获取坐标"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                # 构建查询条件
                conditions = ["place_name = ?"]
                params = [place_name]

                if city:
                    conditions.append("city = ?")
                    params.append(city)
                if province:
                    conditions.append("province = ?")
                    params.append(province)

                where_clause = " AND ".join(conditions)

                cursor = conn.execute(f"""
                    SELECT place_name, full_address, province, city, district,
                           longitude, latitude, level, data_source, confidence,
                           is_approximation, approximation_reason, created_at, query_count
                    FROM coordinate_cache
                    WHERE {where_clause}
                    ORDER BY query_count DESC, confidence DESC
                    LIMIT 1
                """, params)

                row = cursor.fetchone()
                if row:
                    # 更新查询次数
                    conn.execute("""
                        UPDATE coordinate_cache
                        SET query_count = query_count + 1
                        WHERE place_name = ? AND full_address = ?
                    """, (place_name, row[1]))
                    conn.commit()

                    return PlaceCoordinate(
                        place_name=row[0],
                        full_address=row[1],
                        province=row[2],
                        city=row[3],
                        district=row[4],
                        longitude=row[5],
                        latitude=row[6],
                        level=row[7],
                        data_source=row[8],
                        confidence=row[9],
                        is_approximation=bool(row[10]),
                        approximation_reason=row[11] or ""
                    )

        except Exception as e:
            logger.error(f"查询缓存失败: {e}")

        return None

    def _get_from_local_db(self, place_name: str,
                           city: Optional[str] = None,
                           province: Optional[str] = None) -> Optional[PlaceCoordinate]:
        """从本地行政区划数据库获取坐标"""
        try:
            if not self.coords_db_path.exists():
                return None

            with sqlite3.connect(self.coords_db_path) as conn:
                # 构建查询条件
                conditions = ["name = ?"]
                params = [place_name]

                if city:
                    conditions.append("city = ?")
                    params.append(city)
                if province:
                    conditions.append("province = ?")
                    params.append(province)

                where_clause = " AND ".join(conditions)

                cursor = conn.execute(f"""
                    SELECT name, province, city, longitude, latitude, level
                    FROM regions
                    WHERE {where_clause}
                    AND longitude IS NOT NULL AND latitude IS NOT NULL
                    ORDER BY level
                    LIMIT 1
                """, params)

                row = cursor.fetchone()
                if row:
                    return PlaceCoordinate(
                        place_name=row[0],
                        full_address=row[0],  # 使用name作为full_address
                        province=row[1],
                        city=row[2],
                        district="",  # regions表没有district字段
                        longitude=row[3],
                        latitude=row[4],
                        level=row[5],
                        data_source="local_db",
                        confidence=1.0,
                        is_approximation=False
                    )

        except Exception as e:
            logger.error(f"查询本地数据库失败: {e}")

        return None

    def _call_amap_api_safely(self, place_name: str,
                              city: Optional[str] = None,
                              province: Optional[str] = None) -> Optional[PlaceCoordinate]:
        """安全调用高德API（带QPS控制）"""
        if not self.api_key:
            logger.warning("⚠️ 未配置高德API密钥")
            return None

        try:
            # 检查API调用限制
            self._check_api_limits()

            # 构建完整地址
            address_parts = []
            if province:
                address_parts.append(province)
            if city:
                address_parts.append(city)
            address_parts.append(place_name)
            full_address = "".join(address_parts)

            # API请求
            params = {
                'key': self.api_key,
                'address': full_address,
                'output': 'JSON'
            }

            # 记录请求日志
            logger.info(f"🌐 高德API安全调用开始: place_name='{place_name}', full_address='{full_address}'")
            logger.debug(f"🔍 请求参数: {params}")
            logger.debug(f"📍 请求URL: https://restapi.amap.com/v3/geocode/geo")

            # 发起请求
            start_time = time.time()
            response = requests.get(
                "https://restapi.amap.com/v3/geocode/geo",
                params=params,
                timeout=15
            )
            request_duration = time.time() - start_time

            self.last_api_call = time.time()
            self.daily_call_count += 1

            # 记录响应日志
            logger.info(f"📡 高德API安全响应: status_code={response.status_code}, duration={request_duration:.3f}s, daily_count={self.daily_call_count}")
            logger.debug(f"📋 响应头: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()

                # 记录响应数据日志
                logger.debug(f"📄 原始响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

                if data.get('status') == '1' and data.get('count', 0) > 0:
                    geocodes = data.get('geocodes', [])
                    logger.info(f"✅ 高德API安全匹配成功: count={len(geocodes)}, place_name='{place_name}'")

                    if geocodes:
                        geocode = geocodes[0]
                        logger.debug(f"🎯 选中安全匹配结果: {json.dumps(geocode, ensure_ascii=False, indent=2)}")
                        location = geocode.get('location', {})

                        if location.get('lng') and location.get('lat'):
                            address_component = geocode.get('addressComponent', {})

                            # 记录解析结果日志
                            longitude = float(location['lng'])
                            latitude = float(location['lat'])
                            confidence = float(geocode.get('confidence', '0')) / 100
                            level = geocode.get('level', '')

                            logger.info(f"📍 安全坐标解析结果: lng={longitude}, lat={latitude}, confidence={confidence:.2f}, level='{level}'")
                            logger.debug(f"🏛️ 安全地址组件: province='{address_component.get('province', '')}', city='{address_component.get('city', '')}', district='{address_component.get('district', '')}'")

                            return PlaceCoordinate(
                                place_name=place_name,
                                full_address=full_address,
                                province=address_component.get('province', ''),
                                city=address_component.get('city', ''),
                                district=address_component.get('district', ''),
                                longitude=longitude,
                                latitude=latitude,
                                level=level,
                                data_source='amap_api',
                                confidence=confidence,
                                is_approximation=False
                            )
                        else:
                            logger.warning(f"⚠️ 高德API安全调用返回无效坐标: (0, 0) for place_name='{place_name}'")
                else:
                    logger.warning(f"❌ 高德API安全调用无匹配: place_name='{place_name}', status='{data.get('status')}', count={data.get('count', 0)}")
                    logger.debug(f"📋 安全API完整响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
            else:
                logger.error(f"💥 高德API安全调用失败: HTTP {response.status_code}, place_name='{place_name}'")
                logger.error(f"📄 安全调用响应内容: {response.text}")

        except requests.exceptions.Timeout:
            logger.error(f"⏰ 高德API安全调用超时: place_name='{place_name}', timeout=15s")
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 高德API安全调用连接错误: place_name='{place_name}'")
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 高德API安全调用请求异常: place_name='{place_name}', error={e}")
        except json.JSONDecodeError as e:
            logger.error(f"📄 高德API安全调用响应解析失败: place_name='{place_name}', error={e}")
        except Exception as e:
            logger.error(f"❌ 高德API安全调用失败: place_name='{place_name}', error={e}")
            logger.exception("安全调用详细错误信息:")

        return None

    def _get_fallback_coordinate(self, place_name: str,
                               city: Optional[str] = None,
                               province: Optional[str] = None) -> Optional[PlaceCoordinate]:
        """降级处理 - 查找上级地名"""
        try:
            # 特殊处理河桥镇
            if "河桥" in place_name:
                # 已知河桥镇属于临安区
                return self._get_from_local_db("临安区", "杭州市", "浙江省")

            # 一般降级策略：移除最具体的部分
            if "镇" in place_name:
                base_name = place_name.replace("镇", "").replace("乡", "").replace("街道", "").strip()
                if base_name:
                    return self._get_from_local_db(base_name, city, province)

            # 如果没有匹配，返回None
            return None

        except Exception as e:
            logger.error(f"降级处理失败: {e}")
            return None

    def _check_api_limits(self) -> None:
        """检查API调用限制"""
        # 检查日限制
        current_day = time.localtime().tm_yday
        if current_day != self.last_reset_day:
            self.daily_call_count = 0
            self.last_reset_day = current_day
            logger.info("API日限制已重置")

        # 检查QPS限制
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_call_interval:
            sleep_time = self.min_call_interval - time_since_last_call
            logger.debug(f"QPS限制，等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)

        # 简单的日限制检查
        if self.daily_call_count >= 100:  # 保守限制
            logger.warning(f"接近API日限制，今日已调用 {self.daily_call_count} 次")
            raise Exception("API调用次数已达限制")

    def _save_to_cache(self, coordinate: PlaceCoordinate) -> None:
        """保存坐标到缓存"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO coordinate_cache
                    (place_name, full_address, province, city, district, longitude, latitude,
                     level, data_source, confidence, is_approximation, approximation_reason,
                     created_at, query_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    coordinate.place_name, coordinate.full_address,
                    coordinate.province, coordinate.city, coordinate.district,
                    coordinate.longitude, coordinate.latitude,
                    coordinate.level, coordinate.data_source,
                    coordinate.confidence, coordinate.is_approximation,
                    coordinate.approximation_reason,
                    time.time(), 1  # query_count
                ))
                conn.commit()

        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def get_statistics(self) -> Dict:
        """获取服务统计信息"""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                # 总缓存数
                total_result = conn.execute("SELECT COUNT(*) FROM coordinate_cache").fetchone()
                total_count = total_result[0] if total_result else 0

                # 按数据源统计
                source_result = conn.execute("""
                    SELECT data_source, COUNT(*) as count
                    FROM coordinate_cache
                    GROUP BY data_source
                """).fetchall()

                # 热门查询
                popular_result = conn.execute("""
                    SELECT place_name, query_count, data_source
                    FROM coordinate_cache
                    WHERE query_count > 0
                    ORDER BY query_count DESC
                    LIMIT 10
                """).fetchall()

                # API使用统计
                api_stats = {
                    'daily_count': self.daily_call_count,
                    'daily_limit': 100,  # 保守限制
                    'usage_percent': (self.daily_call_count / 100) * 100
                }

                return {
                    'total_cached': total_count,
                    'by_source': dict(source_result),
                    'popular_queries': popular_result,
                    'api_usage': api_stats
                }

        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}

def main():
    """测试真实坐标服务"""
    print("🗺️ 测试真实坐标服务")
    print("=" * 60)

    service = RealCoordinateService()

    # 测试河桥镇问题
    print("🎯 测试河桥镇问题解决:")
    test_cases = [
        ("河桥镇", None, None),
        ("河桥镇", "杭州市", "浙江省"),
        ("临安区", None, None),
        ("北京市", None, None)
    ]

    for place_name, city, province in test_cases:
        print(f"   查询: {place_name}")
        result = service.get_coordinate(place_name, city, province)
        if result:
            approx_info = " (近似)" if result.is_approximation else ""
            print(f"   ✅ 成功: ({result.longitude:.6f}, {result.latitude:.6f}){approx_info}")
            print(f"      数据源: {result.data_source}, 置信度: {result.confidence:.2f}")
            print(f"      完整地址: {result.full_address}")
        else:
            print(f"   ❌ 失败: 未找到坐标")
        print()

    # 显示统计信息
    print("📊 服务统计:")
    stats = service.get_statistics()
    print(f"   缓存总数: {stats['total_cached']}")
    print(f"   API使用: {stats['api_usage']['daily_count']}/{stats['api_usage']['daily_limit']} ({stats['api_usage']['usage_percent']:.1f}%)")

    if stats['by_source']:
        print(f"   按数据源:")
        for source, count in stats['by_source'].items():
            print(f"      {source}: {count}")

if __name__ == "__main__":
    main()