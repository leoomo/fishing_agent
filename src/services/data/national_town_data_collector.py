#!/usr/bin/env python3
"""
全国城镇数据收集器
用于获取、处理和整合全国镇级行政区划数据
"""

import json
import sqlite3
import requests
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import time
import re
from urllib.parse import quote

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TownData:
    """城镇数据模型"""
    code: str                    # 行政区划代码
    name: str                    # 标准名称
    parent_code: str             # 上级区划代码
    parent_name: str             # 上级区划名称
    level: int                   # 行政级别 (4:镇级, 5:村级)
    longitude: Optional[float]   # 经度
    latitude: Optional[float]    # 纬度
    province: str                # 省份
    city: str                    # 城市
    district: str                # 区县
    town_type: str               # 镇类型 (镇、乡、街道等)
    population: Optional[int]   # 人口
    area_km2: Optional[float]    # 面积
    data_source: str             # 数据来源
    data_quality: float = 1.0    # 数据质量评分 (0-1)

class NationalTownDataCollector:
    """全国城镇数据收集器"""

    def __init__(self, db_path: str = "src/data/admin_divisions.db"):
        """
        初始化数据收集器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.conn = None

        # 数据源配置
        self.data_sources = {
            'gaode': {
                'name': '高德地图',
                'base_url': 'https://restapi.amap.com/v3/config/district',
                'key': None,  # 需要配置API密钥
                'rate_limit': 100  # 每分钟请求限制
            },
            'baidu': {
                'name': '百度地图',
                'base_url': 'https://api.map.baidu.com/place/v2/search',
                'key': None,  # 需要配置API密钥
                'rate_limit': 100
            }
        }

        # 镇类型分类
        self.town_types = {
            '镇': '镇',
            '乡': '乡',
            '街道': '街道',
            '苏木': '苏木',
            '民族乡': '民族乡',
            '民族苏木': '民族苏木'
        }

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

            # 启用WAL模式
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")

            logger.info(f"已连接到数据库: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")

    def create_towns_table(self):
        """创建城镇数据表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS towns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            parent_code TEXT NOT NULL,
            parent_name TEXT NOT NULL,
            level INTEGER NOT NULL,
            longitude REAL,
            latitude REAL,
            province TEXT,
            city TEXT,
            district TEXT,
            town_type TEXT,
            population INTEGER,
            area_km2 REAL,
            aliases TEXT,
            data_source TEXT,
            data_quality REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        try:
            self.conn.execute(create_table_sql)

            # 创建索引
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_towns_code ON towns(code)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_towns_parent_code ON towns(parent_code)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_towns_name ON towns(name)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_towns_coords ON towns(longitude, latitude)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_towns_province ON towns(province)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_towns_city ON towns(city)")

            self.conn.commit()
            logger.info("城镇数据表创建成功")
        except Exception as e:
            logger.error(f"创建城镇数据表失败: {e}")
            raise

    def get_existing_districts(self) -> List[Dict]:
        """获取现有的区县数据"""
        try:
            cursor = self.conn.execute("""
                SELECT code, name, province, city
                FROM regions
                WHERE level = 3
                ORDER BY code
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取区县数据失败: {e}")
            return []

    def collect_sample_towns(self) -> List[TownData]:
        """
        收集示例城镇数据
        基于现有的区县数据生成一些常见的镇级数据
        """
        logger.info("开始收集示例城镇数据...")

        districts = self.get_existing_districts()
        sample_towns = []

        # 常见镇名模式
        common_town_names = [
            '城关镇', '中心镇', '新城镇', '建设镇', '发展镇',
            '和平镇', '民主镇', '团结镇', '胜利镇', '红旗镇',
            '解放镇', '人民镇', '幸福镇', '友谊镇', '光明镇',
            '东风镇', '朝阳镇', '新华镇', '中华镇', '前进镇'
        ]

        for district in districts[:50]:  # 限制处理前50个区县
            district_code = district['code']
            district_name = district['name']
            province = district['province']
            city = district['city']

            # 为每个区县生成2-3个示例镇
            num_towns = min(3, len(common_town_names))
            selected_names = common_town_names[:num_towns]

            for i, town_name in enumerate(selected_names):
                # 生成镇编码（区县编码 + 3位数字）
                town_code = district_code + f"{i+1:03d}"

                # 生成近似坐标（区县坐标基础上稍有偏移）
                coords = self._get_district_coordinates(district_code)
                if coords:
                    longitude, latitude = coords
                    # 添加小的随机偏移
                    longitude += (i - 1) * 0.01
                    latitude += (i - 1) * 0.01
                else:
                    longitude = None
                    latitude = None

                town_data = TownData(
                    code=town_code,
                    name=town_name,
                    parent_code=district_code,
                    parent_name=district_name,
                    level=4,
                    longitude=longitude,
                    latitude=latitude,
                    province=province,
                    city=city,
                    district=district_name,
                    town_type='镇',
                    population=None,
                    area_km2=None,
                    data_source='generated_sample',
                    data_quality=0.7  # 示例数据质量较低
                )

                sample_towns.append(town_data)

        logger.info(f"生成了 {len(sample_towns)} 个示例城镇数据")
        return sample_towns

    def _get_district_coordinates(self, district_code: str) -> Optional[Tuple[float, float]]:
        """获取区县坐标"""
        try:
            cursor = self.conn.execute(
                "SELECT longitude, latitude FROM regions WHERE code = ?",
                (district_code,)
            )
            result = cursor.fetchone()
            if result and result['longitude'] and result['latitude']:
                return (result['longitude'], result['latitude'])
        except Exception:
            pass
        return None

    def save_towns_to_db(self, towns: List[TownData]) -> int:
        """保存城镇数据到数据库"""
        logger.info(f"开始保存 {len(towns)} 个城镇数据...")

        saved_count = 0
        for town in towns:
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO towns
                    (code, name, parent_code, parent_name, level, longitude, latitude,
                     province, city, district, town_type, population, area_km2,
                     data_source, data_quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    town.code, town.name, town.parent_code, town.parent_name,
                    town.level, town.longitude, town.latitude, town.province,
                    town.city, town.district, town.town_type, town.population,
                    town.area_km2, town.data_source, town.data_quality
                ))
                saved_count += 1
            except Exception as e:
                logger.warning(f"保存城镇数据失败 {town.name}: {e}")

        try:
            self.conn.commit()
            logger.info(f"成功保存 {saved_count} 个城镇数据")
        except Exception as e:
            logger.error(f"提交事务失败: {e}")
            return 0

        return saved_count

    def collect_from_open_source(self) -> List[TownData]:
        """
        从开源数据源收集城镇数据
        使用公开的行政区划数据
        """
        logger.info("开始从开源数据源收集城镇数据...")

        # 这里可以添加从国家统计局等公开数据源的数据收集逻辑
        # 目前先返回空列表，后续可以扩展
        open_source_towns = []

        # TODO: 实现从国家统计局API或数据文件的收集
        # 例如：http://www.stats.gov.cn/sj/tjbz/tjyqh/dhcaj/

        logger.info("开源数据收集完成")
        return open_source_towns

    def generate_town_hierarchy_data(self) -> Dict:
        """生成城镇层级结构数据"""
        try:
            cursor = self.conn.execute("""
                SELECT province, city, district, COUNT(*) as town_count
                FROM towns
                GROUP BY province, city, district
                ORDER BY province, city, district
            """)

            hierarchy = {}
            for row in cursor.fetchall():
                province = row['province']
                if province not in hierarchy:
                    hierarchy[province] = {}

                city = row['city']
                if city not in hierarchy[province]:
                    hierarchy[province][city] = {}

                hierarchy[province][city][row['district']] = row['town_count']

            return hierarchy
        except Exception as e:
            logger.error(f"生成层级数据失败: {e}")
            return {}

    def get_statistics(self) -> Dict:
        """获取数据统计信息"""
        try:
            stats = {}

            # 总城镇数
            cursor = self.conn.execute("SELECT COUNT(*) FROM towns")
            stats['total_towns'] = cursor.fetchone()[0]

            # 按省统计
            cursor = self.conn.execute("""
                SELECT province, COUNT(*) as count
                FROM towns
                GROUP BY province
                ORDER BY count DESC
            """)
            stats['by_province'] = dict(cursor.fetchall())

            # 按类型统计
            cursor = self.conn.execute("""
                SELECT town_type, COUNT(*) as count
                FROM towns
                GROUP BY town_type
                ORDER BY count DESC
            """)
            stats['by_type'] = dict(cursor.fetchall())

            # 有坐标的城镇数
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM towns
                WHERE longitude IS NOT NULL AND latitude IS NOT NULL
            """)
            stats['with_coordinates'] = cursor.fetchone()[0]

            # 数据质量统计
            cursor = self.conn.execute("""
                SELECT AVG(data_quality) as avg_quality
                FROM towns
            """)
            avg_quality = cursor.fetchone()[0]
            stats['average_quality'] = round(avg_quality, 2) if avg_quality else 0

            return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def export_towns_to_json(self, output_file: str = "src/data/towns_export.json"):
        """导出城镇数据到JSON文件"""
        try:
            cursor = self.conn.execute("""
                SELECT * FROM towns
                ORDER BY province, city, district, name
            """)

            towns_data = [dict(row) for row in cursor.fetchall()]

            # 移除内部字段
            for town in towns_data:
                town.pop('id', None)
                town.pop('created_at', None)
                town.pop('updated_at', None)

            # 添加统计信息
            towns_json = {
                'export_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_count': len(towns_data),
                'statistics': self.get_statistics(),
                'towns': towns_data
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(towns_json, f, ensure_ascii=False, indent=2)

            logger.info(f"城镇数据已导出到: {output_file}")
            return len(towns_data)
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return 0

    def run_data_collection(self):
        """运行完整的数据收集流程"""
        logger.info("开始全国城镇数据收集流程")
        logger.info("=" * 60)

        try:
            # 连接数据库
            self.connect()

            # 创建城镇数据表
            self.create_towns_table()

            # 收集示例数据
            sample_towns = self.collect_sample_towns()

            # 保存数据
            saved_count = self.save_towns_to_db(sample_towns)

            # 收集开源数据
            open_source_towns = self.collect_from_open_source()
            if open_source_towns:
                saved_count += self.save_towns_to_db(open_source_towns)

            # 获取统计信息
            stats = self.get_statistics()
            logger.info("数据收集统计:")
            for key, value in stats.items():
                if isinstance(value, dict):
                    logger.info(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        logger.info(f"    {sub_key}: {sub_value}")
                else:
                    logger.info(f"  {key}: {value}")

            # 导出数据
            export_count = self.export_towns_to_json()

            logger.info("=" * 60)
            logger.info(f"数据收集完成！")
            logger.info(f"总计城镇数: {stats.get('total_towns', 0)}")
            logger.info(f"成功保存: {saved_count} 个")
            logger.info(f"导出JSON: {export_count} 个")

            return stats

        except Exception as e:
            logger.error(f"数据收集失败: {e}")
            raise
        finally:
            self.close()

def main():
    """主函数"""
    collector = NationalTownDataCollector()
    try:
        stats = collector.run_data_collection()
        print(f"\n✅ 全国城镇数据收集完成！")
        print(f"📊 最终统计:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in list(value.items())[:5]:  # 只显示前5个
                    print(f"     {sub_key}: {sub_value}")
                if len(value) > 5:
                    print(f"     ... 还有 {len(value)-5} 个")
            else:
                print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ 数据收集失败: {e}")

if __name__ == "__main__":
    main()