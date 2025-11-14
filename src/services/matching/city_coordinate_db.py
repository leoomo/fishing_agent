#!/usr/bin/env python3
"""
中国行政区划坐标数据库查询类
提供省、市、县各级行政区划的坐标查询功能
"""

import sqlite3
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PlaceInfo:
    """地点信息数据类"""
    code: str
    name: str
    parent_code: Optional[str]
    level: int
    longitude: float
    latitude: float
    pinyin: Optional[str]
    aliases: List[str]
    full_path: str = ""  # 完整路径，如：广东省>广州市>天河区


class CityCoordinateDB:
    """中国行政区划坐标数据库查询类"""

    def __init__(self, db_path: str = "src/data/admin_divisions.db"):
        """
        初始化坐标数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._init_connection()
        self._cache: Dict[str, Any] = {}  # 简单的内存缓存

    def _init_connection(self) -> None:
        """初始化数据库连接"""
        try:
            if not self.db_path.exists():
                raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # 使结果可以按列名访问

            # 启用WAL模式以提高并发性能
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")

        except Exception as e:
            raise Exception(f"数据库连接失败: {e}")

    def _ensure_connection(self) -> sqlite3.Connection:
        """确保数据库连接可用"""
        if self.connection is None:
            raise RuntimeError("数据库连接未初始化")
        return self.connection

    def get_coordinates(self, place_name: str) -> Optional[Tuple[float, float]]:
        """
        获取地名对应的经纬度坐标

        Args:
            place_name: 地名（支持省、市、县各级）

        Returns:
            (经度, 纬度) 或 None
        """
        if not place_name or not place_name.strip():
            return None

        # 检查缓存
        cache_key = f"coords:{place_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # 1. 精确匹配
            coords = self._exact_match_coordinates(place_name)
            if coords:
                self._cache[cache_key] = coords
                return coords

            # 2. 模糊匹配
            coords = self._fuzzy_match_coordinates(place_name)
            if coords:
                self._cache[cache_key] = coords
                return coords

            # 3. 包含匹配
            coords = self._contains_match_coordinates(place_name)
            if coords:
                self._cache[cache_key] = coords
                return coords

            return None

        except Exception as e:
            print(f"查询坐标时出错: {e}")
            return None

    def _exact_match_coordinates(self, place_name: str) -> Optional[Tuple[float, float]]:
        """精确匹配坐标"""
        query = """
            SELECT longitude, latitude FROM regions
            WHERE name = ? OR pinyin = ?
            LIMIT 1
        """
        try:
            conn = self._ensure_connection()
            cursor = conn.execute(query, (place_name, place_name.lower()))
            result = cursor.fetchone()
            if result and result['longitude'] and result['latitude']:
                return (result['longitude'], result['latitude'])
        except Exception:
            pass
        return None

    def _fuzzy_match_coordinates(self, place_name: str) -> Optional[Tuple[float, float]]:
        """模糊匹配坐标"""
        # 移除常见的行政后缀
        clean_name = re.sub(r'(省|市|县|区|镇|乡|村|自治区|自治州|自治县)$', '', place_name)

        query = """
            SELECT longitude, latitude, name FROM regions
            WHERE name LIKE ? OR pinyin LIKE ?
            ORDER BY level DESC, length(name) ASC
            LIMIT 1
        """
        try:
            conn = self._ensure_connection()
            cursor = conn.execute(query, (f'%{clean_name}%', f'%{clean_name}%'))
            result = cursor.fetchone()
            if result and result['longitude'] and result['latitude']:
                return (result['longitude'], result['latitude'])
        except Exception:
            pass
        return None

    def _contains_match_coordinates(self, place_name: str) -> Optional[Tuple[float, float]]:
        """包含匹配坐标"""
        query = """
            SELECT longitude, latitude FROM regions
            WHERE ? LIKE '%' || name || '%'
            ORDER BY level DESC, length(name) DESC
            LIMIT 1
        """
        try:
            conn = self._ensure_connection()
            cursor = conn.execute(query, (place_name,))
            result = cursor.fetchone()
            if result and result['longitude'] and result['latitude']:
                return (result['longitude'], result['latitude'])
        except Exception:
            pass
        return None

    def search_place(self, place_name: str, limit: int = 10) -> List[PlaceInfo]:
        """
        搜索匹配的地名

        Args:
            place_name: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            匹配结果列表，包含坐标和行政区划信息
        """
        if not place_name or not place_name.strip():
            return []

        try:
            # 多策略搜索
            results = []

            # 1. 精确匹配
            exact_results = self._search_exact(place_name, limit // 2)
            results.extend(exact_results)

            # 2. 模糊匹配
            if len(results) < limit:
                fuzzy_results = self._search_fuzzy(place_name, limit - len(results))
                results.extend(fuzzy_results)

            # 3. 去重并限制数量
            unique_results = []
            seen_codes = set()
            for result in results:
                if result.code not in seen_codes:
                    unique_results.append(result)
                    seen_codes.add(result.code)
                    if len(unique_results) >= limit:
                        break

            return unique_results

        except Exception as e:
            print(f"搜索地名时出错: {e}")
            return []

    def _search_exact(self, place_name: str, limit: int) -> List[PlaceInfo]:
        """精确搜索"""
        query = """
            SELECT code, name, parent_code, level, longitude, latitude, pinyin, aliases
            FROM regions
            WHERE name = ? OR pinyin = ?
            ORDER BY level DESC, length(name) ASC
            LIMIT ?
        """
        try:
            conn = self._ensure_connection()
            cursor = conn.execute(query, (place_name, place_name.lower(), limit))
            return [self._row_to_place_info(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def _search_fuzzy(self, place_name: str, limit: int) -> List[PlaceInfo]:
        """模糊搜索"""
        query = """
            SELECT code, name, parent_code, level, longitude, latitude, pinyin, aliases
            FROM regions
            WHERE name LIKE ? OR pinyin LIKE ? OR aliases LIKE ?
            ORDER BY level DESC, length(name) ASC
            LIMIT ?
        """
        try:
            conn = self._ensure_connection()
            pattern = f'%{place_name}%'
            cursor = conn.execute(query, (pattern, pattern, pattern, limit))
            return [self._row_to_place_info(row) for row in cursor.fetchall()]
        except Exception:
            return []

    def get_administrative_info(self, place_name: str) -> Optional[PlaceInfo]:
        """
        获取行政区划详细信息

        Args:
            place_name: 地名

        Returns:
            包含省、市、县、乡层级信息的PlaceInfo对象
        """
        try:
            # 搜索匹配的地名
            places = self.search_place(place_name, limit=1)
            if not places:
                return None

            place_info = places[0]

            # 构建完整路径
            full_path = self._build_full_path(place_info)
            place_info.full_path = full_path

            return place_info

        except Exception as e:
            print(f"获取行政区划信息时出错: {e}")
            return None

    def _build_full_path(self, place_info: PlaceInfo) -> str:
        """构建完整的行政区划路径"""
        try:
            if not place_info.parent_code:
                return place_info.name

            # 递归查找父级
            path_parts = []
            current = place_info

            while current:
                path_parts.append(current.name)
                if current.parent_code:
                    parent_query = "SELECT * FROM regions WHERE code = ?"
                    conn = self._ensure_connection()
                    cursor = conn.execute(parent_query, (current.parent_code,))
                    parent_row = cursor.fetchone()
                    if parent_row:
                        current = self._row_to_place_info(parent_row)
                    else:
                        break
                else:
                    break

            # 反转路径（从顶级到当前级）
            path_parts.reverse()
            return " > ".join(path_parts)

        except Exception:
            return place_info.name

    def _row_to_place_info(self, row: sqlite3.Row) -> PlaceInfo:
        """将数据库行转换为PlaceInfo对象"""
        aliases = []
        if row['aliases']:
            try:
                aliases = json.loads(row['aliases'])
            except:
                aliases = []

        return PlaceInfo(
            code=row['code'],
            name=row['name'],
            parent_code=row['parent_code'],
            level=row['level'],
            longitude=row['longitude'] or 0.0,
            latitude=row['latitude'] or 0.0,
            pinyin=row['pinyin'],
            aliases=aliases
        )

    def get_children(self, parent_code: str) -> List[PlaceInfo]:
        """
        获取下级行政区划

        Args:
            parent_code: 上级行政区划代码

        Returns:
            下级行政区划列表
        """
        try:
            query = """
                SELECT code, name, parent_code, level, longitude, latitude, pinyin, aliases
                FROM regions
                WHERE parent_code = ?
                ORDER BY name
            """
            conn = self._ensure_connection()
            cursor = conn.execute(query, (parent_code,))
            return [self._row_to_place_info(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取下级行政区划时出错: {e}")
            return []

    def get_statistics(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        try:
            stats = {}
            conn = self._ensure_connection()
            cursor = conn.execute("SELECT level, COUNT(*) as count FROM regions GROUP BY level ORDER BY level")

            for row in cursor.fetchall():
                level_name = {1: "省级", 2: "地级", 3: "县级"}.get(row['level'], f"级别{row['level']}")
                stats[level_name] = row['count']

            # 总计
            cursor = conn.execute("SELECT COUNT(*) as total FROM regions")
            stats["总计"] = cursor.fetchone()['total']

            return stats

        except Exception as e:
            print(f"获取统计信息时出错: {e}")
            return {}

    def clear_cache(self) -> None:
        """清理内存缓存"""
        self._cache.clear()

    def close(self) -> None:
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        """析构函数，确保连接被关闭"""
        self.close()


# 便捷函数
def get_coordinates(place_name: str, db_path: str = "src/data/admin_divisions.db") -> Optional[Tuple[float, float]]:
    """
    便捷函数：获取地名坐标

    Args:
        place_name: 地名
        db_path: 数据库路径

    Returns:
        (经度, 纬度) 或 None
    """
    db = CityCoordinateDB(db_path)
    try:
        return db.get_coordinates(place_name)
    finally:
        db.close()


def search_place(place_name: str, limit: int = 10, db_path: str = "src/data/admin_divisions.db") -> List[PlaceInfo]:
    """
    便捷函数：搜索地名

    Args:
        place_name: 搜索关键词
        limit: 结果数量限制
        db_path: 数据库路径

    Returns:
        搜索结果列表
    """
    db = CityCoordinateDB(db_path)
    try:
        return db.search_place(place_name, limit)
    finally:
        db.close()


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 CityCoordinateDB")
    print("=" * 50)

    db = CityCoordinateDB()

    # 测试统计信息
    stats = db.get_statistics()
    print("📊 数据库统计:")
    for level, count in stats.items():
        print(f"   {level}: {count}个")

    print("\n🔍 测试坐标查询:")
    test_places = ["北京市", "上海市", "广州市", "深圳市", "天河区", "朝阳区", "西湖区"]

    for place in test_places:
        coords = db.get_coordinates(place)
        if coords:
            print(f"   ✅ {place}: ({coords[0]:.4f}, {coords[1]:.4f})")
        else:
            print(f"   ❌ {place}: 未找到")

    print("\n🔎 测试地名搜索:")
    search_results = db.search_place("湖", limit=5)
    for result in search_results:
        print(f"   📍 {result.name} (级别: {result.level}, 坐标: {result.longitude:.4f}, {result.latitude:.4f})")

    print("\n📋 测试行政区划信息:")
    admin_info = db.get_administrative_info("天河区")
    if admin_info:
        print(f"   🏛️ {admin_info.name}")
        print(f"   📍 坐标: ({admin_info.longitude:.4f}, {admin_info.latitude:.4f})")
        print(f"   🏷️ 代码: {admin_info.code}")
        print(f"   📊 级别: {admin_info.level}")
        print(f"   🗂️ 完整路径: {admin_info.full_path}")

    db.close()
    print("\n✅ 测试完成！")