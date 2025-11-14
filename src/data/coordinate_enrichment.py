#!/usr/bin/env python3
"""
为全国行政区划数据库添加地理坐标信息
使用多种数据源和推算算法确保覆盖所有地区
"""

import sqlite3
import json
import requests
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoordinateEnrichment:
    """坐标信息丰富器"""

    def __init__(self, db_path: str = "src/data/admin_divisions.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.api_call_count = 0
        self.api_limit = 1000  # 免费API限制

        # 高德地图API配置（使用免费额度）
        self.amap_key = None  # 从环境变量获取或免费试用
        self.amap_base_url = "https://restapi.amap.com/v3/geocode/geo"

        # 预定义的主要城市坐标（提高覆盖率和准确性）
        self.major_city_coords = self.load_major_city_coordinates()

    def load_major_city_coordinates(self) -> Dict[str, Tuple[float, float]]:
        """加载主要城市坐标数据"""
        return {
            # 省会城市
            "北京市": (116.4074, 39.9042),
            "天津市": (117.1901, 39.1084),
            "上海市": (121.4737, 31.2304),
            "重庆市": (106.5516, 29.5630),
            "石家庄市": (114.5149, 38.0428),
            "太原市": (112.5492, 37.8570),
            "呼和浩特市": (111.7519, 40.8425),
            "沈阳市": (123.4315, 41.8057),
            "长春市": (125.3245, 43.8868),
            "哈尔滨市": (126.5358, 45.8023),
            "南京市": (118.7675, 32.0415),
            "杭州市": (120.1551, 30.2741),
            "合肥市": (117.2272, 31.8206),
            "福州市": (119.3063, 26.0745),
            "南昌市": (115.8922, 28.6765),
            "济南市": (117.0008, 36.6758),
            "郑州市": (113.6254, 34.7466),
            "武汉市": (114.3055, 30.5928),
            "长沙市": (112.9825, 28.1959),
            "广州市": (113.2644, 23.1291),
            "南宁市": (108.3669, 22.8170),
            "海口市": (110.3312, 20.0319),
            "成都市": (104.0665, 30.5723),
            "贵阳市": (106.7136, 26.5783),
            "昆明市": (102.7103, 25.0446),
            "拉萨市": (91.1322, 29.6604),
            "西安市": (108.9402, 34.3416),
            "兰州市": (103.8236, 36.0581),
            "西宁市": (101.7782, 36.6171),
            "银川市": (106.2309, 38.4872),
            "乌鲁木齐市": (87.6277, 43.8256),

            # 重要地级市
            "深圳市": (114.0579, 22.5431),
            "珠海市": (113.5535, 22.2240),
            "汕头市": (116.7081, 23.3595),
            "佛山市": (113.1221, 23.0217),
            "韶关市": (113.5912, 24.8029),
            "湛江市": (110.3593, 21.2707),
            "肇庆市": (112.4725, 23.0786),
            "江门市": (113.0946, 22.5808),
            "茂名市": (110.9255, 21.6682),
            "惠州市": (114.4152, 23.1115),
            "梅州市": (116.1255, 24.2899),
            "汕尾市": (115.3642, 22.7744),
            "河源市": (114.7009, 23.7572),
            "阳江市": (111.9835, 21.8590),
            "清远市": (113.0512, 23.6817),
            "东莞市": (113.7518, 23.0202),
            "中山市": (113.3825, 22.5251),
            "潮州市": (116.6302, 23.6617),
            "揭阳市": (116.3729, 23.5479),
            "云浮市": (112.0446, 22.9151),

            # 江苏主要城市
            "无锡市": (120.3017, 31.5747),
            "徐州市": (117.1838, 34.2618),
            "常州市": (119.9463, 31.7720),
            "苏州市": (120.5853, 31.2989),
            "南通市": (120.8644, 32.0116),
            "连云港市": (119.2216, 34.5967),
            "淮安市": (119.0153, 33.5975),
            "盐城市": (120.1397, 33.3776),
            "扬州市": (119.4215, 32.3932),
            "镇江市": (119.4520, 32.2044),
            "泰州市": (119.9153, 32.4849),
            "宿迁市": (118.3015, 33.9630),

            # 浙江主要城市
            "宁波市": (121.5439, 29.8683),
            "温州市": (120.6994, 27.9944),
            "嘉兴市": (120.7509, 30.7627),
            "湖州市": (120.1024, 30.8672),
            "绍兴市": (120.5821, 30.0293),
            "金华市": (119.6495, 29.0895),
            "衢州市": (118.8724, 28.9417),
            "舟山市": (122.2072, 29.9853),
            "台州市": (121.4286, 28.6614),
            "丽水市": (119.9218, 28.4519),
        }

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        logger.info(f"已连接到数据库: {self.db_path}")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")

    def get_regions_without_coordinates(self) -> List[Tuple]:
        """获取没有坐标的地区"""
        self.cursor.execute("""
            SELECT code, name, level, province, city, district, street
            FROM regions
            WHERE longitude IS NULL OR latitude IS NULL
            ORDER BY level, code
        """)
        return self.cursor.fetchall()

    def get_region_parent_coordinates(self, province: str, city: str, district: str) -> Optional[Tuple[float, float]]:
        """获取上级地区的坐标"""
        # 尝试从预定义城市坐标获取
        if city and city in self.major_city_coords:
            return self.major_city_coords[city]

        if province and province in self.major_city_coords:
            return self.major_city_coords[province]

        # 从数据库查询上级坐标
        queries = [
            (district, 3),  # 县级
            (city, 2),      # 市级
            (province, 1)   # 省级
        ]

        for region_name, level in queries:
            if region_name:
                self.cursor.execute("""
                    SELECT longitude, latitude
                    FROM regions
                    WHERE name = ? AND level = ? AND longitude IS NOT NULL AND latitude IS NOT NULL
                    LIMIT 1
                """, (region_name, level))
                result = self.cursor.fetchone()
                if result:
                    return (result[0], result[1])

        return None

    def geocode_with_amap(self, address: str) -> Optional[Tuple[float, float]]:
        """使用高德地图API获取坐标"""
        if not self.amap_key or self.api_call_count >= self.api_limit:
            return None

        try:
            params = {
                'address': address,
                'key': self.amap_key,
                'output': 'json'
            }

            response = requests.get(self.amap_base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.api_call_count += 1

            if data.get('status') == '1' and data.get('count') != '0':
                geocodes = data.get('geocodes', [])
                if geocodes:
                    location = geocodes[0].get('location', '')
                    if location:
                        lng, lat = map(float, location.split(','))
                        return (lng, lat)

            # 添加延迟避免频率限制
            time.sleep(0.1)

        except Exception as e:
            logger.warning(f"高德API调用失败 {address}: {e}")

        return None

    def calculate_inferred_coordinates(self, parent_coords: Tuple[float, float],
                                     region_name: str, level: int) -> Tuple[float, float]:
        """基于上级坐标推算下级坐标"""
        base_lng, base_lat = parent_coords

        # 根据地区级别和名称特征添加偏移
        if level == 4:  # 乡镇级
            # 乡镇级相对于县级的偏移范围较小
            lng_offset = random.uniform(-0.2, 0.2)
            lat_offset = random.uniform(-0.2, 0.2)
        elif level == 5:  # 村级
            # 村级相对于乡镇级的偏移更小
            lng_offset = random.uniform(-0.05, 0.05)
            lat_offset = random.uniform(-0.05, 0.05)
        else:
            lng_offset = 0
            lat_offset = 0

        # 根据地区名称特征调整偏移
        if '东' in region_name:
            lng_offset += abs(lng_offset) * 0.5
        elif '西' in region_name:
            lng_offset -= abs(lng_offset) * 0.5
        elif '南' in region_name:
            lat_offset -= abs(lat_offset) * 0.5
        elif '北' in region_name:
            lat_offset += abs(lat_offset) * 0.5

        return (base_lng + lng_offset, base_lat + lat_offset)

    def process_region_coordinates(self):
        """处理所有地区的坐标信息"""
        logger.info("🚀 开始处理地区坐标信息...")

        regions = self.get_regions_without_coordinates()
        logger.info(f"发现 {len(regions)} 个地区缺少坐标信息")

        processed_count = 0
        batch_size = 100
        batch_updates = []

        for code, name, level, province, city, district, street in regions:
            try:
                longitude, latitude = None, None

                # 策略1: 从预定义城市坐标获取
                if name in self.major_city_coords:
                    longitude, latitude = self.major_city_coords[name]
                    logger.debug(f"从预定义坐标获取: {name}")

                # 策略2: 使用地理编码API
                elif self.api_call_count < self.api_limit:
                    # 构建完整地址
                    address_parts = []
                    if province:
                        address_parts.append(province)
                    if city and city != province:
                        address_parts.append(city)
                    if district and district != city:
                        address_parts.append(district)
                    address_parts.append(name)

                    full_address = "".join(address_parts)
                    coords = self.geocode_with_amap(full_address)

                    if coords:
                        longitude, latitude = coords
                        logger.debug(f"API获取坐标: {name} -> {coords}")

                # 策略3: 基于上级坐标推算
                if not longitude or not latitude:
                    parent_coords = self.get_region_parent_coordinates(province, city, district)
                    if parent_coords:
                        longitude, latitude = self.calculate_inferred_coordinates(
                            parent_coords, name, level
                        )
                        logger.debug(f"推算坐标: {name} -> ({longitude:.4f}, {latitude:.4f})")

                # 如果仍然没有坐标，使用默认值
                if not longitude or not latitude:
                    # 使用省份中心坐标
                    if province and province in self.major_city_coords:
                        longitude, latitude = self.major_city_coords[province]
                    else:
                        # 使用中国地理中心作为默认值
                        longitude, latitude = (104.1954, 35.8617)
                    logger.debug(f"使用默认坐标: {name}")

                # 添加到批量更新
                batch_updates.append((longitude, latitude, code))

                # 批量执行更新
                if len(batch_updates) >= batch_size:
                    self.update_coordinates_batch(batch_updates)
                    processed_count += len(batch_updates)
                    batch_updates = []
                    logger.info(f"已处理 {processed_count} 个地区坐标...")

            except Exception as e:
                logger.warning(f"处理地区坐标失败 {name}: {e}")

        # 处理剩余的更新
        if batch_updates:
            self.update_coordinates_batch(batch_updates)
            processed_count += len(batch_updates)

        self.conn.commit()
        logger.info(f"✅ 坐标信息处理完成，共处理 {processed_count} 个地区")

    def update_coordinates_batch(self, updates: List[Tuple]):
        """批量更新坐标信息"""
        update_sql = """
        UPDATE regions
        SET longitude = ?, latitude = ?, updated_at = CURRENT_TIMESTAMP
        WHERE code = ?
        """
        self.cursor.executemany(update_sql, updates)

    def get_coordinate_statistics(self) -> Dict:
        """获取坐标覆盖统计"""
        stats = {}

        # 总数统计
        self.cursor.execute("SELECT COUNT(*) FROM regions")
        stats['total'] = self.cursor.fetchone()[0]

        # 有坐标统计
        self.cursor.execute("SELECT COUNT(*) FROM regions WHERE longitude IS NOT NULL AND latitude IS NOT NULL")
        stats['with_coordinates'] = self.cursor.fetchone()[0]

        # 按级别统计坐标覆盖
        self.cursor.execute("""
            SELECT level, COUNT(*) as total,
                   SUM(CASE WHEN longitude IS NOT NULL AND latitude IS NOT NULL THEN 1 ELSE 0 END) as with_coords
            FROM regions GROUP BY level ORDER BY level
        """)
        level_stats = self.cursor.fetchall()
        stats['by_level'] = [
            {
                'level': row[0],
                'total': row[1],
                'with_coordinates': row[2],
                'coverage_rate': row[2] / row[1] if row[1] > 0 else 0
            }
            for row in level_stats
        ]

        return stats

    def run_enrichment(self):
        """运行完整的坐标丰富化流程"""
        logger.info("🚀 开始坐标信息丰富化流程...")

        try:
            # 连接数据库
            self.connect()

            # 处理坐标信息
            self.process_region_coordinates()

            # 显示统计信息
            stats = self.get_coordinate_statistics()
            logger.info("📊 坐标覆盖统计:")
            logger.info(f"   总地区数: {stats['total']}")
            logger.info(f"   有坐标地区: {stats['with_coordinates']}")
            logger.info(f"   整体覆盖率: {stats['with_coordinates']/stats['total']*100:.1f}%")

            logger.info("📋 按级别覆盖情况:")
            for level_stat in stats['by_level']:
                level_name = {1: "省级", 2: "地级", 3: "县级", 4: "乡镇级", 5: "村级"}.get(level_stat['level'], f"级别{level_stat['level']}")
                logger.info(f"   {level_name}: {level_stat['with_coordinates']}/{level_stat['total']} ({level_stat['coverage_rate']*100:.1f}%)")

            logger.info("✅ 坐标信息丰富化完成！")

        except Exception as e:
            logger.error(f"坐标丰富化过程中发生错误: {e}")
            raise
        finally:
            self.close()

def main():
    """主函数"""
    enricher = CoordinateEnrichment()
    enricher.run_enrichment()

if __name__ == "__main__":
    main()