#!/usr/bin/env python3
"""
高德地图坐标服务
优先查询本地缓存，缺失时调用API并存储结果
"""

import os
import sqlite3
import requests
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入专用日志类
from ..logging.business_logger import BusinessLogger

logger = logging.getLogger(__name__)

@dataclass
class CoordinateData:
    """坐标数据模型"""
    place_name: str           # 地名
    full_address: str         # 完整地址
    province: str            # 省份
    city: str                # 城市
    district: str            # 区县
    longitude: float         # 经度
    latitude: float          # 纬度
    level: str               # 行政级别
    confidence: int          # 匹配度
    data_source: str         # 数据来源
    created_at: float        # 创建时间
    updated_at: float        # 更新时间
    query_count: int = 0     # 查询次数

class AmapCoordinateService:
    """高德地图坐标服务 - 智能缓存版"""

    def __init__(self, db_path: str = "src/data/coordinates_cache.db"):
        """
        初始化坐标服务

        Args:
            db_path: 缓存数据库路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 高德API配置
        self.api_key = os.getenv('AMAP_API_KEY')
        if not self.api_key:
            raise ValueError("未找到高德地图API密钥，请在.env文件中配置AMAP_API_KEY")

        self.base_url = "https://restapi.amap.com/v3/geocode/geo"

        # API调用控制
        self.last_api_call = 0
        self.min_call_interval = 0.1  # 最小调用间隔（秒）
        self.daily_api_limit = 50000  # 日限制
        self.daily_api_count = 0
        self.last_reset_date = time.localtime().tm_yday

        # 初始化业务日志记录器
        self.biz_logger = BusinessLogger(__name__)

        # 初始化数据库
        self._init_database()

        self.biz_logger.log_service_initialized("高德地图坐标服务")

    def _init_database(self) -> None:
        """初始化缓存数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 创建坐标缓存表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS coordinate_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        place_name TEXT NOT NULL,
                        full_address TEXT NOT NULL,
                        province TEXT,
                        city TEXT,
                        district TEXT,
                        longitude REAL NOT NULL,
                        latitude REAL NOT NULL,
                        level TEXT,
                        confidence INTEGER,
                        data_source TEXT DEFAULT 'amap_api',
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        query_count INTEGER DEFAULT 0,
                        UNIQUE(place_name, full_address)
                    )
                """)

                # 创建索引
                conn.execute("CREATE INDEX IF NOT EXISTS idx_place_name ON coordinate_cache(place_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_full_address ON coordinate_cache(full_address)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_coordinates ON coordinate_cache(longitude, latitude)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_hierarchy ON coordinate_cache(province, city, district)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON coordinate_cache(updated_at)")

                conn.commit()
                self.biz_logger.log_database_initialized("坐标缓存数据库")

        except Exception as e:
            self.biz_logger.log_database_error("数据库初始化", e)
            raise

    def get_coordinate(self, place_name: str,
                      city: Optional[str] = None,
                      province: Optional[str] = None,
                      force_refresh: bool = False) -> Optional[CoordinateData]:
        """
        获取坐标 - 优先本地缓存

        Args:
            place_name: 地名
            city: 城市（可选，用于提高查询精度）
            province: 省份（可选，用于提高查询精度）
            force_refresh: 是否强制刷新（忽略缓存）

        Returns:
            坐标数据或None
        """
        # 1. 优先查询本地缓存
        if not force_refresh:
            cached_data = self._get_from_cache(place_name, city, province)
            if cached_data:
                self._update_query_count_by_place(place_name, city, province)
                self.biz_logger.log_cache_hit(place_name)
                return cached_data

        # 2. 缓存未命中，调用API
        self.biz_logger.log_cache_miss(place_name)
        api_data = self._call_amap_api(place_name, city, province)

        if api_data:
            # 3. 存储到本地缓存
            self._save_to_cache(api_data)
            return api_data

        return None

    def _get_from_cache(self, place_name: str,
                        city: Optional[str] = None,
                        province: Optional[str] = None) -> Optional[CoordinateData]:
        """从本地缓存获取坐标"""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                    SELECT id, place_name, full_address, province, city, district,
                           longitude, latitude, level, confidence, data_source,
                           created_at, updated_at, query_count
                    FROM coordinate_cache
                    WHERE {where_clause}
                    ORDER BY confidence DESC, updated_at DESC
                    LIMIT 1
                """, params)

                row = cursor.fetchone()
                if row:
                    return CoordinateData(
                        place_name=row[1],
                        full_address=row[2],
                        province=row[3],
                        city=row[4],
                        district=row[5],
                        longitude=row[6],
                        latitude=row[7],
                        level=row[8],
                        confidence=row[9],
                        data_source=row[10],
                        created_at=row[11],
                        updated_at=row[12],
                        query_count=row[13]
                    )
        except Exception as e:
            logger.error(f"查询缓存失败: {e}")

        return None

    def _call_amap_api(self, place_name: str,
                       city: Optional[str] = None,
                       province: Optional[str] = None) -> Optional[CoordinateData]:
        """调用高德地图API获取坐标"""
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

            # API请求参数
            params = {
                'key': self.api_key,
                'address': full_address,
                'output': 'JSON'
            }

            # 记录请求日志
            description = f"place_name='{place_name}', full_address='{full_address}'"
            self.biz_logger.log_api_request_start("高德API", description, params, self.base_url)

            # 发起请求
            start_time = time.time()
            response = requests.get(self.base_url, params=params, timeout=10)
            request_duration = time.time() - start_time

            self.last_api_call = time.time()
            self.daily_api_count += 1

            # 记录响应日志
            self.biz_logger.log_api_response("高德API", response.status_code, request_duration,
                                           dict(response.headers), daily_count=self.daily_api_count)

            if response.status_code == 200:
                data = response.json()

                # 记录响应数据日志
                self.biz_logger.log_api_response_data(data, "高德API原始响应")

                # 检查API响应
                if data.get('status') == '1' and int(data.get('count', 0)) > 0:
                    geocodes = data.get('geocodes', [])
                    self.biz_logger.log_api_success("高德API", f"匹配 count={len(geocodes)}, place_name='{place_name}'")

                    if geocodes:
                        geocode = geocodes[0]  # 取第一个匹配结果
                        self.biz_logger.log_data_details("选中匹配结果", geocode)

                        # 解析响应数据
                        location = geocode.get('location', '')
                        if isinstance(location, str):
                            # 高德API的location是"lng,lat"格式的字符串
                            lng_str, lat_str = location.split(',')
                            longitude = float(lng_str)
                            latitude = float(lat_str)
                        else:
                            # 兼容字典格式
                            longitude = float(location.get('lng', 0))
                            latitude = float(location.get('lat', 0))

                        # 解析地址组件
                        address_component = geocode.get('addressComponent', {})
                        province_api = address_component.get('province', '')
                        city_api = address_component.get('city', '')
                        district_api = address_component.get('district', '')
                        level = geocode.get('level', '')
                        confidence = int(geocode.get('confidence', 0))

                        # 记录解析结果日志
                        self.biz_logger.log_data_parsed("坐标", f"lng={longitude}, lat={latitude}",
                                                       confidence=confidence, level=level)
                        self.biz_logger.log_address_components(province_api, city_api, district_api)

                        if longitude != 0 and latitude != 0:
                            self.biz_logger.log_coordinate_success(place_name, longitude, latitude)
                            return CoordinateData(
                                place_name=place_name,
                                full_address=full_address,
                                province=province_api,
                                city=city_api,
                                district=district_api,
                                longitude=longitude,
                                latitude=latitude,
                                level=level,
                                confidence=confidence,
                                data_source='amap_api',
                                created_at=time.time(),
                                updated_at=time.time(),
                                query_count=1
                            )
                        else:
                            self.biz_logger.log_invalid_data("高德API坐标", f"(0, 0) for place_name='{place_name}'")
                else:
                    self.biz_logger.log_api_no_match("高德API",
                                                    f"place_name='{place_name}', status='{data.get('status')}', count={data.get('count', 0)}",
                                                    data)
            else:
                self.biz_logger.log_http_error("高德API", response.status_code,
                                              f"place_name='{place_name}'", response.text)

        except requests.exceptions.Timeout:
            self.biz_logger.log_timeout_error("高德API", f"place_name='{place_name}'", 10)
        except requests.exceptions.ConnectionError:
            self.biz_logger.log_connection_error("高德API", f"place_name='{place_name}'")
        except requests.exceptions.RequestException as e:
            self.biz_logger.log_request_error("高德API", f"place_name='{place_name}'", e)
        except json.JSONDecodeError as e:
            self.biz_logger.log_json_error("高德API", f"place_name='{place_name}'", e)
        except Exception as e:
            self.biz_logger.log_general_error("高德API", f"place_name='{place_name}'", e)

        return None

    def _save_to_cache(self, coordinate_data: CoordinateData) -> bool:
        """保存坐标数据到缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO coordinate_cache
                    (place_name, full_address, province, city, district, longitude, latitude,
                     level, confidence, data_source, created_at, updated_at, query_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    coordinate_data.place_name, coordinate_data.full_address,
                    coordinate_data.province, coordinate_data.city, coordinate_data.district,
                    coordinate_data.longitude, coordinate_data.latitude,
                    coordinate_data.level, coordinate_data.confidence,
                    coordinate_data.data_source, coordinate_data.created_at,
                    coordinate_data.updated_at, coordinate_data.query_count
                ))
                conn.commit()
                self.biz_logger.log_cache_saved(coordinate_data.place_name)
                return True

        except Exception as e:
            self.biz_logger.log_database_error("保存缓存", e)
            return False

    def _update_query_count_by_place(self, place_name: str, city: Optional[str] = None, province: Optional[str] = None) -> None:
        """通过地名更新查询次数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 构建更新条件
                conditions = ["place_name = ?"]
                params = [place_name, time.time()]

                if city:
                    conditions.append("city = ?")
                    params.insert(-1, city)
                if province:
                    conditions.append("province = ?")
                    params.insert(-1, province)

                where_clause = " AND ".join(conditions)

                conn.execute(f"""
                    UPDATE coordinate_cache
                    SET query_count = query_count + 1, updated_at = ?
                    WHERE {where_clause}
                """, params)
                conn.commit()
        except Exception as e:
            self.biz_logger.log_database_error("更新查询次数", e)

    def _check_api_limits(self) -> None:
        """检查API调用限制"""
        # 检查日限制
        current_day = time.localtime().tm_yday
        if current_day != self.last_reset_date:
            self.daily_api_count = 0
            self.last_reset_date = current_day
            self.biz_logger.log_limit_reset("API调用")

        if self.daily_api_count >= self.daily_api_limit:
            self.biz_logger.log_limit_reached("API调用", self.daily_api_count)
            raise Exception("API调用次数已达上限")

        # 检查调用频率
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_call_interval:
            sleep_time = self.min_call_interval - time_since_last_call
            self.biz_logger.log_limit_check("API调用频率限制", sleep_time)
            time.sleep(sleep_time)

    def batch_get_coordinates(self, place_list: List[Tuple[str, Optional[str], Optional[str]]],
                            skip_existing: bool = True) -> List[CoordinateData]:
        """
        批量获取坐标

        Args:
            place_list: [(地名, 城市, 省份), ...] 的列表
            skip_existing: 是否跳过已存在的缓存

        Returns:
            坐标数据列表
        """
        results = []

        for place_name, city, province in place_list:
            try:
                coordinate = self.get_coordinate(
                    place_name=place_name,
                    city=city,
                    province=province,
                    force_refresh=not skip_existing
                )
                if coordinate:
                    results.append(coordinate)

                # 控制调用频率
                time.sleep(0.1)

            except Exception as e:
                self.biz_logger.log_general_error("批量获取坐标", f"{place_name}", e)
                continue

        self.biz_logger.log_batch_complete("批量获取坐标", len(results), len(place_list))
        return results

    def get_cache_statistics(self) -> Dict:
        """获取缓存统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 总记录数
                total_result = conn.execute("SELECT COUNT(*) FROM coordinate_cache").fetchone()
                total_count = total_result[0] if total_result else 0

                # 按省份统计
                province_result = conn.execute("""
                    SELECT province, COUNT(*) as count
                    FROM coordinate_cache
                    WHERE province IS NOT NULL
                    GROUP BY province
                    ORDER BY count DESC
                """).fetchall()

                # 按城市统计
                city_result = conn.execute("""
                    SELECT city, COUNT(*) as count
                    FROM coordinate_cache
                    WHERE city IS NOT NULL
                    GROUP BY city
                    ORDER BY count DESC
                    LIMIT 10
                """).fetchall()

                # 按级别统计
                level_result = conn.execute("""
                    SELECT level, COUNT(*) as count
                    FROM coordinate_cache
                    WHERE level IS NOT NULL
                    GROUP BY level
                    ORDER BY count DESC
                """).fetchall()

                # 热门查询
                popular_result = conn.execute("""
                    SELECT place_name, full_address, query_count
                    FROM coordinate_cache
                    WHERE query_count > 0
                    ORDER BY query_count DESC
                    LIMIT 10
                """).fetchall()

                # API调用统计
                api_stats = {
                    'daily_count': self.daily_api_count,
                    'daily_limit': self.daily_api_limit,
                    'usage_percent': (self.daily_api_count / self.daily_api_limit) * 100
                }

                return {
                    'total_records': total_count,
                    'by_province': dict(province_result),
                    'by_city': dict(city_result),
                    'by_level': dict(level_result),
                    'popular_queries': popular_result,
                    'api_usage': api_stats
                }

        except Exception as e:
            self.biz_logger.log_database_error("获取缓存统计", e)
            return {}

    def cleanup_expired_cache(self, days: int = 30) -> int:
        """清理过期缓存"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM coordinate_cache
                    WHERE updated_at < ? AND query_count < 5
                """, (cutoff_time,))

                deleted_count = cursor.rowcount
                conn.commit()

            self.biz_logger.log_operation_success("清理过期缓存", f"删除 {deleted_count} 条记录")
            return deleted_count

        except Exception as e:
            self.biz_logger.log_database_error("清理缓存", e)
            return 0

def main():
    """测试高德地图坐标服务"""
    print("🗺️ 测试高德地图坐标服务（智能缓存版）")
    print("=" * 60)

    try:
        service = AmapCoordinateService()

        # 测试单个查询
        print("1️⃣ 测试单个坐标查询:")
        test_places = [
            ("河桥镇", "杭州市", "浙江省"),
            ("城关镇", "北京市", None),
            ("临安区", "杭州市", "浙江省"),
            ("朝阳区城关镇", "北京市", None)
        ]

        for place_name, city, province in test_places:
            print(f"   查询: {place_name}")
            coordinate = service.get_coordinate(place_name, city, province)
            if coordinate:
                print(f"   ✅ 成功: ({coordinate.longitude:.6f}, {coordinate.latitude:.6f})")
                print(f"      级别: {coordinate.level}, 置信度: {coordinate.confidence}")
                print(f"      地址: {coordinate.full_address}")
            else:
                print(f"   ❌ 失败: 未找到坐标")
            print()

        # 测试缓存命中
        print("2️⃣ 测试缓存命中:")
        print("   再次查询相同地名（应该命中缓存）:")
        coordinate = service.get_coordinate("河桥镇", "杭州市", "浙江省")
        if coordinate:
            print(f"   ✅ 缓存命中: ({coordinate.longitude:.6f}, {coordinate.latitude:.6f})")
            print(f"   查询次数: {coordinate.query_count}")
        print()

        # 测试批量查询
        print("3️⃣ 测试批量查询:")
        batch_places = [
            ("西湖镇", "杭州市", "浙江省"),
            ("建设镇", "天津市", None),
            ("中心镇", "上海市", None)
        ]
        batch_results = service.batch_get_coordinates(batch_places)
        print(f"   批量查询结果: {len(batch_results)} 个成功")
        for result in batch_results:
            print(f"   ✅ {result.place_name} -> ({result.longitude:.6f}, {result.latitude:.6f})")
        print()

        # 显示统计信息
        print("4️⃣ 缓存统计信息:")
        stats = service.get_cache_statistics()
        print(f"   总记录数: {stats['total_records']}")
        print(f"   API使用情况: {stats['api_usage']['daily_count']}/{stats['api_usage']['daily_limit']} ({stats['api_usage']['usage_percent']:.1f}%)")

        if stats['by_province']:
            print(f"   按省份分布:")
            for province, count in list(stats['by_province'].items())[:3]:
                print(f"      {province}: {count}")

        if stats['popular_queries']:
            print(f"   热门查询:")
            for query in stats['popular_queries'][:3]:
                print(f"      {query[0]} (查询{query[2]}次)")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()