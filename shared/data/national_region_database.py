#!/usr/bin/env python3
"""
扩展行政区划数据库为支持全国4.5万乡镇级数据
包含五级区划：省->市->县->乡->村
"""

import sqlite3
import json
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NationalRegionDatabase:
    """全国行政区划数据库管理器"""

    def __init__(self, db_path: str = "src/data/admin_divisions.db"):
        self.db_path = db_path
        self.ensure_data_directory()
        self.conn = None
        self.cursor = None

    def ensure_data_directory(self):
        """确保数据目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

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

    def create_extended_schema(self):
        """创建扩展的数据库架构支持五级区划"""
        logger.info("开始创建扩展数据库架构...")

        # 备份现有数据
        self.backup_existing_data()

        # 重创建表结构
        self.cursor.execute('DROP TABLE IF EXISTS regions')

        create_table_sql = '''
        CREATE TABLE regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,          -- 12位区划代码
            name TEXT NOT NULL,                -- 标准名称
            parent_code TEXT,                   -- 上级区划代码
            level INTEGER NOT NULL,             -- 行政级别(1省 2市 3县 4乡 5村)
            longitude REAL,                     -- 经度
            latitude REAL,                      -- 纬度
            pinyin TEXT,                        -- 拼音
            aliases TEXT,                       -- 别名(JSON格式)
            province TEXT,                      -- 省份
            city TEXT,                          -- 市
            district TEXT,                      -- 区县
            street TEXT,                        -- 乡镇/街道
            community TEXT,                    -- 村/社区
            urban_rural_type TEXT,             -- 城乡分类代码
            data_source TEXT,                   -- 数据来源
            data_quality REAL DEFAULT 1.0,     -- 数据质量评分(0-1)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''

        self.cursor.execute(create_table_sql)

        # 创建优化索引
        indexes = [
            'CREATE INDEX idx_regions_name ON regions(name)',
            'CREATE INDEX idx_regions_pinyin ON regions(pinyin)',
            'CREATE INDEX idx_regions_parent_code ON regions(parent_code)',
            'CREATE INDEX idx_regions_level ON regions(level)',
            'CREATE INDEX idx_regions_coordinates ON regions(longitude, latitude)',
            'CREATE INDEX idx_regions_hierarchy ON regions(province, city, district, street)',
            'CREATE INDEX idx_regions_code ON regions(code)',
            'CREATE INDEX idx_regions_data_source ON regions(data_source)'
        ]

        for index_sql in indexes:
            self.cursor.execute(index_sql)

        # 恢复现有数据
        self.restore_existing_data()

        self.conn.commit()
        logger.info("✅ 扩展数据库架构创建完成")

    def backup_existing_data(self):
        """备份现有数据"""
        try:
            self.cursor.execute('SELECT * FROM regions')
            existing_data = self.cursor.fetchall()

            if existing_data:
                # 获取列名
                self.cursor.execute('PRAGMA table_info(regions)')
                columns = [col[1] for col in self.cursor.fetchall()]

                # 保存到临时表
                backup_df = pd.DataFrame(existing_data, columns=columns)
                backup_df.to_csv('data/backup_regions.csv', index=False, encoding='utf-8')
                logger.info(f"已备份 {len(existing_data)} 条现有数据")

                return backup_df
        except Exception as e:
            logger.warning(f"备份数据时出现问题: {e}")

        return None

    def restore_existing_data(self):
        """恢复现有数据到新表结构"""
        backup_file = Path('data/backup_regions.csv')
        if backup_file.exists():
            try:
                backup_df = pd.read_csv(backup_file, encoding='utf-8')

                # 转换数据到新结构
                for _, row in backup_df.iterrows():
                    # 填充新的层级字段
                    province = city = district = street = community = None

                    if row['level'] == 1:  # 省级
                        province = row['name']
                    elif row['level'] == 2:  # 市级
                        city = row['name']
                    elif row['level'] == 3:  # 县级
                        district = row['name']
                    elif row['level'] == 4:  # 乡镇级
                        street = row['name']

                    # 插入数据
                    insert_sql = '''
                    INSERT INTO regions (
                        code, name, parent_code, level, longitude, latitude,
                        pinyin, aliases, province, city, district, street,
                        community, data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''

                    self.cursor.execute(insert_sql, (
                        row['code'], row['name'], row['parent_code'], row['level'],
                        row['longitude'], row['latitude'], row['pinyin'], row['aliases'],
                        province, city, district, street, community, 'legacy'
                    ))

                logger.info(f"✅ 已恢复 {len(backup_df)} 条现有数据")

            except Exception as e:
                logger.error(f"恢复数据失败: {e}")

    def download_national_data(self):
        """下载全国行政区划数据"""
        logger.info("开始下载全国行政区划数据...")

        # 使用GitHub开源数据源（更易获取且格式规范）
        github_url = "https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist/areas.json"

        try:
            response = requests.get(github_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info(f"✅ 成功下载GitHub行政区划数据，共 {len(data)} 条记录")

            # 保存原始数据
            with open('data/national_areas_raw.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return data

        except Exception as e:
            logger.error(f"下载GitHub数据失败: {e}")
            return None

    def parse_and_insert_data(self, data: List[Dict]):
        """解析并插入行政区划数据"""
        logger.info("开始解析和插入行政区划数据...")

        inserted_count = 0
        batch_size = 1000
        batch_data = []

        for item in data:
            try:
                # 解析数据结构
                code = item.get('code', '')
                name = item.get('name', '')
                level = self.determine_level(code)
                parent_code = self.get_parent_code(code)

                # 生成拼音（简单处理）
                pinyin = self.generate_pinyin(name)

                # 构建层级信息
                province, city, district, street, community = self.build_hierarchy_info(code, name, level)

                batch_data.append((
                    code, name, parent_code, level, None, None, pinyin, None,
                    province, city, district, street, community, None, 'github', 1.0
                ))

                if len(batch_data) >= batch_size:
                    self.insert_batch(batch_data)
                    inserted_count += len(batch_data)
                    batch_data = []
                    logger.info(f"已插入 {inserted_count} 条记录...")

            except Exception as e:
                logger.warning(f"解析数据项失败 {item}: {e}")

        # 插入剩余数据
        if batch_data:
            self.insert_batch(batch_data)
            inserted_count += len(batch_data)

        self.conn.commit()
        logger.info(f"✅ 数据插入完成，共插入 {inserted_count} 条记录")

    def determine_level(self, code: str) -> int:
        """根据区划代码确定行政级别"""
        if not code or len(code) < 2:
            return 0

        # 12位代码的层级规则
        if len(code) >= 2:
            # 省级：前2位
            if code[2:] == '0000000000':
                return 1
            # 市级：前4位
            elif len(code) >= 4 and code[4:] == '00000000':
                return 2
            # 县级：前6位
            elif len(code) >= 6 and code[6:] == '000000':
                return 3
            # 乡级：前9位
            elif len(code) >= 9 and code[9:] == '000':
                return 4
            # 村级：12位完整代码
            elif len(code) >= 12:
                return 5
            else:
                return 3  # 默认为县级

        return 0

    def get_parent_code(self, code: str) -> Optional[str]:
        """获取上级区划代码"""
        if not code or len(code) < 2:
            return None

        level = self.determine_level(code)

        if level == 2:  # 市级，上级是省级
            return code[:2] + '0000000000'
        elif level == 3:  # 县级，上级是市级
            return code[:4] + '00000000'
        elif level == 4:  # 乡级，上级是县级
            return code[:6] + '000000'
        elif level == 5:  # 村级，上级是乡级
            return code[:9] + '000'
        else:
            return None

    def generate_pinyin(self, name: str) -> str:
        """生成拼音（简单处理，后续可优化）"""
        # 这里使用简单的拼音生成，实际项目中可以使用pypinyin等库
        pinyin_map = {
            '北京': 'beijing',
            '天津': 'tianjin',
            '上海': 'shanghai',
            '重庆': 'chongqing',
            '河北': 'hebei',
            '山西': 'shanxi',
            '辽宁': 'liaoning',
            '吉林': 'jilin',
            '黑龙江': 'heilongjiang',
            '江苏': 'jiangsu',
            '浙江': 'zhejiang',
            '安徽': 'anhui',
            '福建': 'fujian',
            '江西': 'jiangxi',
            '山东': 'shandong',
            '河南': 'henan',
            '湖北': 'hubei',
            '湖南': 'hunan',
            '广东': 'guangdong',
            '海南': 'hainan',
            '四川': 'sichuan',
            '贵州': 'guizhou',
            '云南': 'yunnan',
            '陕西': 'shaanxi',
            '甘肃': 'gansu',
            '青海': 'qinghai',
            '内蒙古': 'neimenggu',
            '广西': 'guangxi',
            '西藏': 'xizang',
            '宁夏': 'ningxia',
            '新疆': 'xinjiang',
            '台湾': 'taiwan',
            '香港': 'xianggang',
            '澳门': 'aomen'
        }

        return pinyin_map.get(name, name.lower())

    def build_hierarchy_info(self, code: str, name: str, level: int) -> Tuple:
        """构建层级信息"""
        province = city = district = street = community = None

        if level == 1:  # 省级
            province = name
        elif level == 2:  # 市级
            city = name
        elif level == 3:  # 县级
            district = name
        elif level == 4:  # 乡级
            street = name
        elif level == 5:  # 村级
            community = name

        return province, city, district, street, community

    def insert_batch(self, batch_data: List[Tuple]):
        """批量插入数据"""
        insert_sql = '''
        INSERT OR REPLACE INTO regions (
            code, name, parent_code, level, longitude, latitude, pinyin, aliases,
            province, city, district, street, community, urban_rural_type,
            data_source, data_quality
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        self.cursor.executemany(insert_sql, batch_data)

    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        stats = {}

        # 总数统计
        self.cursor.execute("SELECT COUNT(*) FROM regions")
        stats['total'] = self.cursor.fetchone()[0]

        # 按级别统计
        self.cursor.execute("SELECT level, COUNT(*) FROM regions GROUP BY level ORDER BY level")
        level_stats = dict(self.cursor.fetchall())
        stats['by_level'] = level_stats

        # 按数据源统计
        self.cursor.execute("SELECT data_source, COUNT(*) FROM regions GROUP BY data_source")
        source_stats = dict(self.cursor.fetchall())
        stats['by_source'] = source_stats

        # 有坐标的统计
        self.cursor.execute("SELECT COUNT(*) FROM regions WHERE longitude IS NOT NULL AND latitude IS NOT NULL")
        stats['with_coordinates'] = self.cursor.fetchone()[0]

        return stats

    def run_initialization(self):
        """运行完整的数据库初始化流程"""
        logger.info("🚀 开始初始化全国行政区划数据库...")

        try:
            # 连接数据库
            self.connect()

            # 创建扩展架构
            self.create_extended_schema()

            # 下载数据
            data = self.download_national_data()
            if data:
                # 解析并插入数据
                self.parse_and_insert_data(data)

                # 显示统计信息
                stats = self.get_statistics()
                logger.info("📊 数据库统计信息:")
                logger.info(f"   总记录数: {stats['total']}")
                logger.info(f"   按级别分布: {stats['by_level']}")
                logger.info(f"   按数据源分布: {stats['by_source']}")
                logger.info(f"   有坐标记录: {stats['with_coordinates']}")

                logger.info("✅ 全国行政区划数据库初始化完成！")
            else:
                logger.error("❌ 数据下载失败，初始化未完成")

        except Exception as e:
            logger.error(f"初始化过程中发生错误: {e}")
            raise
        finally:
            self.close()

def main():
    """主函数"""
    db = NationalRegionDatabase()
    db.run_initialization()

if __name__ == "__main__":
    main()