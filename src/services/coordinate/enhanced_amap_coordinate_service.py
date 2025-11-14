#!/usr/bin/env python3
"""
增强版高德地图坐标服务

实现 ICoordinateService 接口，支持懒加载单例模式。
优先查询本地缓存，缺失时调用API并存储结果。
"""

import os
import sqlite3
import requests
import json
import logging
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# 导入接口和配置
try:
    from ...interfaces.coordinate_service import ICoordinateService, Coordinate, LocationInfo
    from ...config.service_config import get_service_config
except ImportError:
    # 处理相对导入失败的情况
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    from interfaces.coordinate_service import ICoordinateService, Coordinate, LocationInfo
    from config.service_config import get_service_config

# 加载环境变量
load_dotenv()

# 导入专用日志类
from ..logging.business_logger import BusinessLogger

logger = logging.getLogger(__name__)


@dataclass
class CoordinateData:
    """坐标数据模型（保持向后兼容）"""
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

    def to_coordinate(self) -> Coordinate:
        """转换为接口定义的Coordinate对象"""
        return Coordinate(
            longitude=self.longitude,
            latitude=self.latitude,
            confidence=self.confidence / 100.0,  # 转换为0-1范围
            source=self.data_source
        )

    def to_location_info(self) -> LocationInfo:
        """转换为接口定义的LocationInfo对象"""
        return LocationInfo(
            name=self.place_name,
            adcode="",  # 需要从API获取或数据库查询
            province=self.province,
            city=self.city,
            district=self.district,
            coordinate=self.to_coordinate(),
            level=self.level
        )


class EnhancedAmapCoordinateService(ICoordinateService):
    """增强版高德地图坐标服务 - 实现ICoordinateService接口"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化坐标服务（懒加载模式）

        Args:
            db_path: 缓存数据库路径，如果为None则使用配置文件中的路径
        """
        self._initialized = False
        self._init_lock = threading.Lock()
        self._config = get_service_config()

        # 数据库路径配置
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path(self._config.coordinate_service.database.path)

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

        # 业务日志记录器（延迟初始化）
        self._biz_logger = None

        # 只在配置允许时自动初始化
        if self._config.coordinate_service.auto_init:
            self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """确保服务已初始化（线程安全）"""
        if not self._initialized:
            with self._init_lock:
                if not self._initialized:
                    self._init_database()
                    self._initialized = True
                    if self._biz_logger:
                        self._biz_logger.log_service_initialized("增强版高德地图坐标服务")

    @property
    def biz_logger(self) -> BusinessLogger:
        """获取业务日志记录器（延迟初始化）"""
        if self._biz_logger is None:
            self._biz_logger = BusinessLogger(__name__)
        return self._biz_logger

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

                # 只在DEBUG模式下显示初始化日志，避免重复日志
                if self._config.logging.debug_logging:
                    self.biz_logger.log_database_initialized("坐标缓存数据库")

        except Exception as e:
            if self._biz_logger:
                self._biz_logger.log_database_error("数据库初始化", e)
            raise

    def get_coordinate(self, location_name: str) -> Optional[Coordinate]:
        """
        根据位置名称获取坐标（实现接口方法）

        Args:
            location_name: 位置名称

        Returns:
            坐标信息，如果未找到返回 None
        """
        self._ensure_initialized()

        # 使用现有的get_coordinate方法，但简化参数
        coordinate_data = self.get_coordinate_data(location_name)

        if coordinate_data:
            return coordinate_data.to_coordinate()

        return None

    def get_location_info(self, location_name: str) -> Optional[LocationInfo]:
        """
        根据位置名称获取详细位置信息（实现接口方法）

        Args:
            location_name: 位置名称

        Returns:
            位置信息，如果未找到返回 None
        """
        self._ensure_initialized()

        # 使用现有的get_coordinate方法获取完整信息
        coordinate_data = self.get_coordinate_data(location_name)

        if coordinate_data:
            return coordinate_data.to_location_info()

        return None

    def is_initialized(self) -> bool:
        """检查服务是否已初始化（实现接口方法）"""
        return self._initialized

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态信息（实现接口方法）"""
        return {
            'service_name': 'EnhancedAmapCoordinateService',
            'initialized': self._initialized,
            'database_path': str(self.db_path),
            'api_key_configured': bool(self.api_key),
            'daily_api_count': self.daily_api_count,
            'daily_api_limit': self.daily_api_limit,
            'config': {
                'auto_init': self._config.coordinate_service.auto_init,
                'cache_enabled': self._config.coordinate_service.database.cache_enabled,
                'cache_ttl': self._config.coordinate_service.database.cache_ttl,
                'timeout': self._config.coordinate_service.timeout,
                'max_retries': self._config.coordinate_service.max_retries,
            }
        }

    def health_check(self) -> bool:
        """执行健康检查（实现接口方法）"""
        try:
            if not self._initialized:
                return False

            # 检查数据库连接
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1").fetchone()

            # 检查API密钥
            if not self.api_key:
                return False

            # 检查配置
            if not self._config.coordinate_service.enabled:
                return False

            return True
        except Exception:
            return False

    # 向后兼容的现有方法
    def get_coordinate_data(self, place_name: str,
                           city: Optional[str] = None,
                           province: Optional[str] = None,
                           force_refresh: bool = False) -> Optional[CoordinateData]:
        """
        获取坐标 - 优先本地缓存（保持向后兼容）

        Args:
            place_name: 地名
            city: 城市（可选，用于提高查询精度）
            province: 省份（可选，用于提高查询精度）
            force_refresh: 是否强制刷新（忽略缓存）

        Returns:
            坐标数据或None
        """
        self._ensure_initialized()

        # 1. 优先查询本地缓存
        if not force_refresh and self._config.coordinate_service.database.cache_enabled:
            cached_data = self._get_from_cache(place_name, city, province)
            if cached_data:
                self._update_query_count_by_place(place_name, city, province)
                self.biz_logger.log_cache_hit(place_name)
                return cached_data

        # 2. 缓存未命中，调用API
        if self._biz_logger:
            self.biz_logger.log_cache_miss(place_name)
        api_data = self._call_amap_api(place_name, city, province)

        if api_data:
            # 3. 存储到本地缓存
            if self._config.coordinate_service.database.cache_enabled:
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
            if self._biz_logger:
                description = f"place_name='{place_name}', full_address='{full_address}'"
                self.biz_logger.log_api_request_start("高德API", description, params, self.base_url)

            # 发起请求
            start_time = time.time()
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self._config.coordinate_service.timeout
            )
            request_duration = time.time() - start_time

            self.last_api_call = time.time()
            self.daily_api_count += 1

            # 记录响应日志
            if self._biz_logger:
                self.biz_logger.log_api_response("高德API", response.status_code, request_duration,
                                               dict(response.headers), daily_count=self.daily_api_count)

            if response.status_code == 200:
                data = response.json()

                # 记录响应数据日志
                if self._biz_logger:
                    self.biz_logger.log_api_response_data(data, "高德API原始响应")

                # 检查API响应
                if data.get('status') == '1' and int(data.get('count', 0)) > 0:
                    geocodes = data.get('geocodes', [])
                    if self._biz_logger:
                        self.biz_logger.log_api_success("高德API", f"匹配 count={len(geocodes)}, place_name='{place_name}'")

                    if geocodes:
                        geocode = geocodes[0]  # 取第一个匹配结果
                        if self._biz_logger:
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
                        if self._biz_logger:
                            self.biz_logger.log_data_parsed("坐标", f"lng={longitude}, lat={latitude}",
                                                           confidence=confidence, level=level)
                            self.biz_logger.log_address_components(province_api, city_api, district_api)

                        if longitude != 0 and latitude != 0:
                            if self._biz_logger:
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
                            if self._biz_logger:
                                self.biz_logger.log_invalid_data("高德API坐标", f"(0, 0) for place_name='{place_name}'")
                else:
                    if self._biz_logger:
                        self.biz_logger.log_api_no_match("高德API",
                                                        f"place_name='{place_name}', status='{data.get('status')}', count={data.get('count', 0)}",
                                                        data)
            else:
                if self._biz_logger:
                    self.biz_logger.log_http_error("高德API", response.status_code,
                                                  f"place_name='{place_name}'", response.text)

        except requests.exceptions.Timeout:
            if self._biz_logger:
                self.biz_logger.log_timeout_error("高德API", f"place_name='{place_name}'", self._config.coordinate_service.timeout)
        except requests.exceptions.ConnectionError:
            if self._biz_logger:
                self.biz_logger.log_connection_error("高德API", f"place_name='{place_name}'")
        except requests.exceptions.RequestException as e:
            if self._biz_logger:
                self.biz_logger.log_request_error("高德API", f"place_name='{place_name}'", e)
        except json.JSONDecodeError as e:
            if self._biz_logger:
                self.biz_logger.log_json_error("高德API", f"place_name='{place_name}'", e)
        except Exception as e:
            if self._biz_logger:
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
                if self._biz_logger:
                    self.biz_logger.log_cache_saved(coordinate_data.place_name)
                return True

        except Exception as e:
            if self._biz_logger:
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
            if self._biz_logger:
                self.biz_logger.log_database_error("更新查询次数", e)

    def _check_api_limits(self) -> None:
        """检查API调用限制"""
        # 检查日限制
        current_day = time.localtime().tm_yday
        if current_day != self.last_reset_date:
            self.daily_api_count = 0
            self.last_reset_date = current_day
            if self._biz_logger:
                self.biz_logger.log_limit_reset("API调用")

        if self.daily_api_count >= self.daily_api_limit:
            if self._biz_logger:
                self.biz_logger.log_limit_reached("API调用", self.daily_api_count)
            raise Exception("API调用次数已达上限")

        # 检查调用频率
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.min_call_interval:
            sleep_time = self.min_call_interval - time_since_last_call
            if self._biz_logger:
                self.biz_logger.log_limit_check("API调用频率限制", sleep_time)
            time.sleep(sleep_time)

    def cleanup(self) -> None:
        """清理资源"""
        # 关闭数据库连接等清理工作
        pass