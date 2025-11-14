#!/usr/bin/env python3
"""
层级地名匹配器
支持省-市-县-镇四级地名智能匹配
整合了城镇数据，提供完整的地名匹配能力
"""

import sqlite3
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from services.matching.city_coordinate_db import CityCoordinateDB
from services.matching.intelligent_fallback_matcher import IntelligentFallbackMatcher

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """匹配结果"""
    success: bool
    original_query: str
    matched_name: str
    coordinates: Tuple[float, float]
    level: int
    level_name: str
    full_path: str
    approximation: bool = False
    approximation_reason: str = ""
    confidence: float = 1.0
    data_source: str = ""

class HierarchicalPlaceMatcher:
    """层级地名匹配器"""

    def __init__(self, db_path: str = "data/admin_divisions.db"):
        """
        初始化层级地名匹配器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.city_db = CityCoordinateDB(db_path)
        self.fallback_matcher = IntelligentFallbackMatcher(db_path)

        # 级别映射
        self.level_map = {
            1: "省级",
            2: "地级",
            3: "县级",
            4: "镇级",
            5: "村级"
        }

        # 级别权重（用于排序）
        self.level_weights = {
            5: 1.0,  # 村级优先级最高（最具体）
            4: 0.9,  # 镇级次之
            3: 0.8,  # 县级
            2: 0.7,  # 地级
            1: 0.6   # 省级（最泛化）
        }

    def connect(self):
        """连接数据库"""
        # CityCoordinateDB 在初始化时自动连接，无需手动连接
        self.fallback_matcher.connect()

    def close(self):
        """关闭连接"""
        if self.city_db.connection:
            self.city_db.connection.close()
        self.fallback_matcher.close()

    def match_place(self, place_name: str) -> MatchResult:
        """
        主要匹配方法 - 支持四级地名匹配

        Args:
            place_name: 要匹配的地名

        Returns:
            MatchResult: 匹配结果
        """
        logger.debug(f"开始层级地名匹配: {place_name}")

        if not place_name or not place_name.strip():
            return self._create_empty_result(place_name)

        # 1. 尝试从towns表匹配（镇级数据）
        town_result = self._match_town(place_name)
        if town_result and town_result.success:
            logger.debug(f"镇级匹配成功: {town_result.matched_name}")
            return town_result

        # 2. 尝试从regions表匹配（省市县数据）
        region_result = self._match_region(place_name)
        if region_result and region_result.success:
            logger.debug(f"区划匹配成功: {region_result.matched_name}")
            return region_result

        # 3. 使用智能降级匹配器
        fallback_result = self.fallback_matcher.match_with_fallback(place_name)
        if fallback_result.success:
            return MatchResult(
                success=True,
                original_query=fallback_result.original_query,
                matched_name=fallback_result.matched_name,
                coordinates=fallback_result.coordinates,
                level=fallback_result.level,
                level_name=fallback_result.level_name,
                full_path=fallback_result.full_path,
                approximation=fallback_result.approximation,
                approximation_reason=fallback_result.approximation_reason,
                confidence=fallback_result.confidence * 0.8,  # 降级匹配的置信度稍低
                data_source="fallback"
            )

        # 4. 完全失败
        logger.debug(f"匹配失败: {place_name}")
        return self._create_empty_result(place_name)

    def _match_town(self, place_name: str) -> Optional[MatchResult]:
        """从城镇数据表匹配"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 精确匹配
            cursor.execute("""
                SELECT code, name, parent_code, parent_name, level, longitude, latitude,
                       province, city, district, town_type, data_source, data_quality
                FROM towns
                WHERE name = ? OR aliases LIKE ?
                LIMIT 1
            """, (place_name, f'%{place_name}%'))

            result = cursor.fetchone()
            if result:
                full_path = self._build_town_full_path(result)
                return MatchResult(
                    success=True,
                    original_query=place_name,
                    matched_name=result[1],
                    coordinates=(result[5] or 0.0, result[6] or 0.0),
                    level=result[3],
                    level_name=self.level_map.get(result[3], f"级别{result[3]}"),
                    full_path=full_path,
                    approximation=False,
                    confidence=result[13] or 1.0,
                    data_source=result[12] or "database"
                )

            # 模糊匹配
            cursor.execute("""
                SELECT code, name, parent_code, parent_name, level, longitude, latitude,
                       province, city, district, town_type, data_source, data_quality
                FROM towns
                WHERE name LIKE ? OR aliases LIKE ?
                ORDER BY data_quality DESC, LENGTH(name) ASC
                LIMIT 1
            """, (f'%{place_name}%', f'%{place_name}%'))

            result = cursor.fetchone()
            if result:
                full_path = self._build_town_full_path(result)
                return MatchResult(
                    success=True,
                    original_query=place_name,
                    matched_name=result[1],
                    coordinates=(result[5] or 0.0, result[6] or 0.0),
                    level=result[3],
                    level_name=self.level_map.get(result[3], f"级别{result[3]}"),
                    full_path=full_path,
                    approximation=True,
                    approximation_reason="模糊匹配城镇数据",
                    confidence=(result[13] or 1.0) * 0.9,
                    data_source=result[12] or "database"
                )

        except Exception as e:
            logger.error(f"城镇匹配失败: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

        return None

    def _match_region(self, place_name: str) -> Optional[MatchResult]:
        """从区划数据表匹配"""
        try:
            # 使用现有的坐标数据库
            coords = self.city_db.get_coordinates(place_name)
            if coords:
                admin_info = self.city_db.get_administrative_info(place_name)
                if admin_info:
                    return MatchResult(
                        success=True,
                        original_query=place_name,
                        matched_name=admin_info.name,
                        coordinates=coords,
                        level=admin_info.level,
                        level_name=self.level_map.get(admin_info.level, f"级别{admin_info.level}"),
                        full_path=admin_info.full_path,
                        approximation=False,
                        confidence=1.0,
                        data_source="regions_database"
                    )
        except Exception as e:
            logger.error(f"区划匹配失败: {e}")

        return None

    def _build_town_full_path(self, town_row) -> str:
        """构建城镇的完整路径"""
        try:
            if not town_row or len(town_row) < 14:
                return town_row[1] if town_row and len(town_row) > 1 else ""

            parts = []
            if len(town_row) > 7 and town_row[7]:  # province
                parts.append(town_row[7])
            if len(town_row) > 8 and town_row[8]:  # city
                city_name = town_row[8]
                if len(town_row) > 7 and city_name != town_row[7]:  # 避免重复省份名称
                    parts.append(city_name)
            if len(town_row) > 9 and town_row[9]:  # district
                district_name = town_row[9]
                if len(town_row) > 8 and district_name != town_row[8]:  # 避免重复城市名称
                    parts.append(district_name)
            if len(town_row) > 1 and town_row[1]:  # town name
                parts.append(town_row[1])

            return "".join(parts)
        except Exception as e:
            logger.warning(f"构建城镇完整路径失败: {e}")
            return town_row[1] if town_row and len(town_row) > 1 else ""

    def _create_empty_result(self, place_name: str) -> MatchResult:
        """创建空结果"""
        return MatchResult(
            success=False,
            original_query=place_name,
            matched_name="",
            coordinates=(0.0, 0.0),
            level=0,
            level_name="未找到",
            full_path="",
            approximation=False,
            confidence=0.0,
            data_source=""
        )

    def batch_match(self, place_names: List[str]) -> List[MatchResult]:
        """批量匹配地名"""
        results = []
        for place_name in place_names:
            result = self.match_place(place_name)
            results.append(result)
        return results

    def search_by_hierarchy(self, province: str = None, city: str = None,
                           district: str = None, town: str = None) -> List[MatchResult]:
        """
        按层级搜索地名

        Args:
            province: 省份名称
            city: 城市名称
            district: 区县名称
            town: 城镇名称

        Returns:
            匹配结果列表
        """
        results = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 构建查询条件
            conditions = []
            params = []

            if province:
                conditions.append("province LIKE ?")
                params.append(f"%{province}%")
            if city:
                conditions.append("city LIKE ?")
                params.append(f"%{city}%")
            if district:
                conditions.append("district LIKE ?")
                params.append(f"%{district}%")
            if town:
                conditions.append("name LIKE ? OR aliases LIKE ?")
                params.extend([f"%{town}%", f"%{town}%"])

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # 查询区划数据
            cursor.execute(f"""
                SELECT code, name, parent_code, level, longitude, latitude
                FROM regions
                WHERE {where_clause}
                ORDER BY level, name
            """, params)

            region_rows = cursor.fetchall()
            for row in region_rows:
                results.append(MatchResult(
                    success=True,
                    original_query="hierarchy_search",
                    matched_name=row[1],
                    coordinates=(row[4] or 0.0, row[5] or 0.0),
                    level=row[2],
                    level_name=self.level_map.get(row[2], f"级别{row[2]}"),
                    full_path=self._build_region_full_path(row),
                    approximation=False,
                    confidence=1.0,
                    data_source="regions_database"
                ))

            # 查询城镇数据
            if town or district:
                cursor.execute(f"""
                    SELECT code, name, parent_code, parent_name, level, longitude, latitude,
                           province, city, district, town_type, data_source, data_quality
                    FROM towns
                    WHERE {where_clause}
                    ORDER BY data_quality DESC, name
                """, params)

                town_rows = cursor.fetchall()
                for row in town_rows:
                    full_path = self._build_town_full_path(row)
                    results.append(MatchResult(
                        success=True,
                        original_query="hierarchy_search",
                        matched_name=row[1],
                        coordinates=(row[5] or 0.0, row[6] or 0.0),
                        level=row[3],
                        level_name=self.level_map.get(row[3], f"级别{row[3]}"),
                        full_path=full_path,
                        approximation=False,
                        confidence=row[13] or 1.0,
                        data_source=row[12] or "database"
                    ))

        except Exception as e:
            logger.error(f"层级搜索失败: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

        return results

    def _build_region_full_path(self, region_row) -> str:
        """构建区划的完整路径"""
        try:
            return region_row[1] if region_row else ""
        except Exception:
            return ""

    def get_statistics(self) -> Dict:
        """获取匹配器统计信息"""
        try:
            stats = {}

            # 从towns表获取统计
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM towns")
            stats['total_towns'] = cursor.fetchone()[0]

            cursor.execute("SELECT level, COUNT(*) FROM towns GROUP BY level")
            stats['towns_by_level'] = dict(cursor.fetchall())

            cursor.execute("SELECT province, COUNT(*) FROM towns GROUP BY province")
            stats['towns_by_province'] = dict(cursor.fetchall())

            # 从regions表获取统计
            cursor.execute("SELECT COUNT(*) FROM regions")
            stats['total_regions'] = cursor.fetchone()[0]

            cursor.execute("SELECT level, COUNT(*) FROM regions GROUP BY level")
            stats['regions_by_level'] = dict(cursor.fetchall())

            # 总计
            stats['total_places'] = stats['total_towns'] + stats['total_regions']
            stats['town_coverage'] = stats['total_towns'] / stats['total_places'] if stats['total_places'] > 0 else 0

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def test_matching_performance(self, test_queries: List[str]) -> Dict:
        """测试匹配性能"""
        logger.info("开始测试层级匹配性能...")

        results = {
            'total_queries': len(test_queries),
            'town_matches': 0,
            'region_matches': 0,
            'fallback_matches': 0,
            'failed_matches': 0,
            'match_details': []
        }

        import time
        start_time = time.time()

        for query in test_queries:
            match_start = time.time()
            result = self.match_place(query)
            match_time = time.time() - match_start

            if result.success:
                if result.data_source == "database":
                    if result.level >= 4:  # 镇级或村级
                        results['town_matches'] += 1
                        match_type = "城镇匹配"
                    else:  # 省市县
                        results['region_matches'] += 1
                        match_type = "区划匹配"
                else:  # fallback
                    results['fallback_matches'] += 1
                    match_type = "降级匹配"

                results['match_details'].append({
                    'query': query,
                    'matched': result.matched_name,
                    'level': result.level_name,
                    'data_source': result.data_source,
                    'approximation': result.approximation,
                    'confidence': result.confidence,
                    'time': match_time,
                    'success': True,
                    'match_type': match_type
                })
            else:
                results['failed_matches'] += 1
                results['match_details'].append({
                    'query': query,
                    'matched': None,
                    'level': None,
                    'data_source': '',
                    'approximation': False,
                    'confidence': 0.0,
                    'time': match_time,
                    'success': False,
                    'match_type': "匹配失败"
                })

        total_time = time.time() - start_time
        results['total_time'] = total_time
        results['average_time'] = total_time / len(test_queries)
        results['success_rate'] = (results['town_matches'] + results['region_matches'] + results['fallback_matches']) / len(test_queries)
        results['town_match_rate'] = results['town_matches'] / len(test_queries)

        logger.info(f"层级匹配性能测试完成:")
        logger.info(f"   总查询数: {results['total_queries']}")
        logger.info(f"   城镇匹配: {results['town_matches']}")
        logger.info(f"   区划匹配: {results['region_matches']}")
        logger.info(f"   降级匹配: {results['fallback_matches']}")
        logger.info(f"   匹配失败: {results['failed_matches']}")
        logger.info(f"   成功率: {results['success_rate']*100:.1f}%")
        logger.info(f"   城镇匹配率: {results['town_match_rate']*100:.1f}%")
        logger.info(f"   平均耗时: {results['average_time']*1000:.2f}ms")

        return results

def main():
    """主函数 - 测试层级地名匹配器"""
    matcher = HierarchicalPlaceMatcher()

    try:
        matcher.connect()

        print("🧪 测试层级地名匹配器")
        print("=" * 60)

        # 显示统计信息
        stats = matcher.get_statistics()
        print("📊 层级地名匹配器统计:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"      {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")

        # 测试查询
        test_queries = [
            "河桥镇",           # 镇级，应该使用智能降级
            "中心镇",           # 镇级，应该匹配到数据库中的镇
            "北京市朝阳区",     # 区县级，应该精确匹配
            "临安区",           # 县级，应该精确匹配
            "杭州市",           # 地级，应该精确匹配
            "浙江省",           # 省级，应该精确匹配
            "不存在的镇",       # 完全不存在的地名
            "朝阳区城关镇",     # 区县+镇的组合
            "海淀区中关村",     # 区县+地点的组合
        ]

        # 运行性能测试
        performance_results = matcher.test_matching_performance(test_queries)

        # 显示部分匹配结果
        print("\n📋 详细匹配结果:")
        for detail in performance_results['match_details'][:15]:
            if detail['success']:
                approx_info = ""
                if detail['approximation']:
                    approx_info = f" ({detail['approximation_reason']})"
                print(f"   ✅ {detail['query']} -> {detail['matched']} ({detail['level']}){approx_info}")
                print(f"      数据源: {detail['data_source']}, 置信度: {detail['confidence']:.2f}, 类型: {detail['match_type']}")
            else:
                print(f"   ❌ {detail['query']} -> 未匹配")

        print(f"\n📊 性能统计:")
        print(f"   成功率: {performance_results['success_rate']*100:.1f}%")
        print(f"   城镇匹配率: {performance_results['town_match_rate']*100:.1f}%")
        print(f"   平均耗时: {performance_results['average_time']*1000:.2f}ms")

        # 测试层级搜索
        print(f"\n🔍 测试层级搜索:")
        hierarchy_results = matcher.search_by_hierarchy(
            province="北京市",
            district="朝阳区"
        )
        print(f"   找到 {len(hierarchy_results)} 个结果")
        for result in hierarchy_results[:5]:
            print(f"   ✅ {result.matched_name} ({result.level_name}) - {result.full_path}")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        raise
    finally:
        matcher.close()

if __name__ == "__main__":
    main()