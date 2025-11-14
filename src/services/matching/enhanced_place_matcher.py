#!/usr/bin/env python3
"""
增强的地名匹配系统
支持全国3000+县级行政区的智能匹配
包含五级区划匹配、模糊匹配、拼音匹配等高级功能
"""

import sqlite3
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from difflib import SequenceMatcher
import unicodedata

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedPlaceMatcher:
    """增强的地名匹配器"""

    def __init__(self, db_path: str = "src/data/admin_divisions.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

        # 地区类型映射
        self.level_names = {
            1: ["省", "自治区", "直辖市", "特别行政区"],
            2: ["市", "地区", "自治州", "盟"],
            3: ["县", "区", "市", "自治县", "旗", "自治旗", "林区", "特区"],
            4: ["镇", "乡", "街道", "苏木", "民族乡", "民族苏木"],
            5: ["村", "社区", "居委会", "嘎查", "管委会"]
        }

        # 常见别名映射
        self.alias_map = self._build_alias_map()

        # 地区后缀模式
        self.suffix_patterns = [
            r'省$', r'自治区$', r'直辖市$', r'特别行政区$',
            r'市$', r'地区$', r'自治州$', r'盟$',
            r'县$', r'区$', r'市$', r'自治县$', r'旗$', r'自治旗$', r'林区$', r'特区$',
            r'镇$', r'乡$', r'街道$', r'苏木$', r'民族乡$', r'民族苏木$',
            r'村$', r'社区$', r'居委会$', r'嘎查$', r'管委会$'
        ]

    def _build_alias_map(self) -> Dict[str, str]:
        """构建常见地区别名映射"""
        return {
            # 北京
            "京": "北京市", "燕京": "北京市", "北平": "北京市", "首都": "北京市",
            # 上海
            "沪": "上海市", "申": "上海市", "魔都": "上海市",
            # 天津
            "津": "天津市", "津门": "天津市",
            # 重庆
            "渝": "重庆市", "巴": "重庆市", "山城": "重庆市",
            # 广东
            "粤": "广东省", "羊城": "广州市", "花城": "广州市", "穗": "广州市",
            "鹏城": "深圳市", "深": "深圳市", "珠海": "珠海市", "佛山": "佛山市",
            # 江苏
            "苏": "江苏省", "宁": "南京市", "金陵": "南京市", "建康": "南京市",
            "苏": "苏州市", "姑苏": "苏州市", "平江": "苏州市", "锡": "无锡市",
            "常": "常州市", "龙城": "常州市", "通": "南通市", "北上海": "南通市",
            # 浙江
            "浙": "浙江省", "杭": "杭州市", "武林": "杭州市", "钱塘": "杭州市",
            "甬": "宁波市", "鹿城": "温州市", "禾城": "嘉兴市", "湖城": "湖州市",
            "越州": "绍兴市", "婺州": "金华市", "台州": "台州市",
            # 四川
            "川": "四川省", "蜀": "四川省", "蓉": "成都市", "锦城": "成都市", "天府": "成都市",
            # 陕西
            "陕": "陕西省", "秦": "陕西省", "长安": "西安市", "镐京": "西安市", "西京": "西安市",
            # 山东
            "鲁": "山东省", "齐鲁": "山东省", "泉城": "济南市", "齐州": "济南市", "历下": "济南市",
            "岛城": "青岛市", "琴岛": "青岛市", "胶澳": "青岛市",
            # 河南
            "豫": "河南省", "中原": "河南省", "商都": "郑州市", "绿城": "郑州市",
            # 湖北
            "鄂": "湖北省", "楚": "湖北省", "江城": "武汉市", "江夏": "武汉市",
            # 湖南
            "湘": "湖南省", "潇湘": "湖南省", "星城": "长沙市", "长沙": "长沙市", "潭州": "长沙市",
            # 其他重要城市
            "盛京": "沈阳市", "奉天": "沈阳市", "沈": "沈阳市",
            "滨城": "大连市", "星海": "大连市", "连": "大连市",
            "榕城": "福州市", "左海": "福州市", "三山": "福州市",
            "鹭岛": "厦门市", "厦": "厦门市", "门": "厦门市",
            "庐州": "合肥市", "合淝": "合肥市", "皖": "合肥市",
            "洪都": "南昌市", "南昌": "南昌市", "赣": "南昌市",
            "林城": "贵阳市", "筑城": "贵阳市", "金阳": "贵阳市",
            "春城": "昆明市", "昆": "昆明市", "滇": "昆明市",
            "日光城": "拉萨市", "逻些": "拉萨市",
            "金城": "兰州市",
            "夏都": "西宁市",
            "凤城": "银川市", "塞上江南": "银川市",
            "乌市": "乌鲁木齐市", "迪化": "乌鲁木齐市",
        }

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        logger.info(f"已连接到数据库: {self.db_path}")

    def _ensure_connection(self) -> sqlite3.Cursor:
        """确保数据库连接可用"""
        if self.cursor is None:
            self.connect()
        return self.cursor  # type: ignore

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")

    def normalize_text(self, text: str) -> str:
        """标准化文本"""
        if not text:
            return ""

        # 转换为简体
        text = unicodedata.normalize('NFKC', text)

        # 去除空格和特殊字符
        text = re.sub(r'\s+', '', text)
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)

        return text.strip()

    def extract_region_name(self, query: str) -> str:
        """从查询中提取地区名称"""
        if not query:
            return ""

        # 标准化查询
        query = self.normalize_text(query)

        # 移除常见的地区后缀
        for pattern in self.suffix_patterns:
            query = re.sub(pattern, '', query)

        return query

    def exact_match(self, name: str) -> Optional[Dict]:
        """精确匹配"""
        normalized_name = self.normalize_text(name)

        # 直接匹配
        cursor = self._ensure_connection()
        cursor.execute("""
            SELECT code, name, level, province, city, district, street, longitude, latitude
            FROM regions
            WHERE name = ? OR pinyin = ?
            LIMIT 1
        """, (name, normalized_name.lower()))

        result = cursor.fetchone()
        if result:
            return self._format_result(result)

        return None

    def alias_match(self, name: str) -> Optional[Dict]:
        """别名匹配"""
        normalized_name = self.normalize_text(name)

        # 检查别名映射
        if normalized_name in self.alias_map:
            alias_name = self.alias_map[normalized_name]
            return self.exact_match(alias_name)

        # 检查数据库中的别名
        cursor = self._ensure_connection()
        cursor.execute("""
            SELECT code, name, level, province, city, district, street, longitude, latitude
            FROM regions
            WHERE aliases LIKE ?
            LIMIT 1
        """, (f'%{name}%',))

        result = cursor.fetchone()
        if result:
            return self._format_result(result)

        return None

    def fuzzy_match(self, name: str, threshold: float = 0.7) -> Optional[Dict]:
        """模糊匹配"""
        normalized_name = self.normalize_text(name)

        if len(normalized_name) < 2:
            return None

        # 获取所有候选地区
        cursor = self._ensure_connection()
        cursor.execute("""
            SELECT code, name, level, province, city, district, street, longitude, latitude
            FROM regions
            WHERE LENGTH(name) >= ?
            ORDER BY level, LENGTH(name)
            LIMIT 100
        """, (len(normalized_name),))

        candidates = cursor.fetchall()
        best_match = None
        best_score = 0

        for candidate in candidates:
            candidate_name = candidate[1]

            # 计算相似度
            score1 = SequenceMatcher(None, normalized_name, candidate_name).ratio()

            # 计算包含相似度
            score2 = 0
            if normalized_name in candidate_name or candidate_name in normalized_name:
                score2 = 0.8

            # 综合评分
            total_score = max(score1, score2)

            # 级别权重（省级 > 市级 > 县级）
            level_weight = {1: 1.2, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.8}
            total_score *= level_weight.get(candidate[2], 1.0)

            if total_score > best_score and total_score >= threshold:
                best_score = total_score
                best_match = candidate

        if best_match:
            return self._format_result(best_match)

        return None

    def hierarchical_match(self, name: str, context: Optional[Dict] = None) -> Optional[Dict]:
        """层级匹配"""
        normalized_name = self.normalize_text(name)

        if context:
            # 在特定上下文中搜索
            province = context.get('province')
            city = context.get('city')
            district = context.get('district')

            conditions = []
            params = [normalized_name]

            if province:
                conditions.append("province = ?")
                params.append(province)
            if city:
                conditions.append("city = ?")
                params.append(city)
            if district:
                conditions.append("district = ?")
                params.append(district)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cursor = self._ensure_connection()
            cursor.execute(f"""
                SELECT code, name, level, province, city, district, street, longitude, latitude
                FROM regions
                WHERE (name LIKE ? OR pinyin LIKE ?) AND {where_clause}
                ORDER BY level DESC
                LIMIT 1
            """, [f'%{normalized_name}%', f'%{normalized_name.lower()}%'] + params)

            result = cursor.fetchone()
            if result:
                return self._format_result(result)

        return None

    def contains_match(self, name: str) -> Optional[Dict]:
        """包含匹配"""
        normalized_name = self.normalize_text(name)

        if len(normalized_name) < 2:
            return None

        cursor = self._ensure_connection()
        cursor.execute("""
            SELECT code, name, level, province, city, district, street, longitude, latitude
            FROM regions
            WHERE name LIKE ? OR pinyin LIKE ?
            ORDER BY level DESC, LENGTH(name)
            LIMIT 10
        """, (f'%{normalized_name}%', f'%{normalized_name.lower()}%'))

        results = cursor.fetchall()

        # 选择最匹配的结果
        for result in results:
            result_name = result[1]
            if normalized_name in result_name or result_name in normalized_name:
                return self._format_result(result)

        # 如果没有直接包含，选择第一个结果
        if results:
            return self._format_result(results[0])

        return None

    def _format_result(self, result: Tuple) -> Dict:
        """格式化查询结果"""
        return {
            'code': result[0],
            'name': result[1],
            'level': result[2],
            'level_name': self._get_level_name(result[2]),
            'province': result[3],
            'city': result[4],
            'district': result[5],
            'street': result[6],
            'longitude': float(result[7]) if result[7] is not None else None,
            'latitude': float(result[8]) if result[8] is not None else None,
            'full_address': self._build_full_address(result)
        }

    def _get_level_name(self, level: int) -> str:
        """获取级别名称"""
        level_names = {
            1: "省级",
            2: "地级",
            3: "县级",
            4: "乡镇级",
            5: "村级"
        }
        return level_names.get(level, f"级别{level}")

    def _build_full_address(self, result: Tuple) -> str:
        """构建完整地址"""
        parts = []
        if result[3]:  # province
            parts.append(result[3])
        if result[4] and result[4] != result[3]:  # city
            parts.append(result[4])
        if result[5] and result[5] != result[4]:  # district
            parts.append(result[5])
        if result[6] and result[6] != result[5]:  # street
            parts.append(result[6])

        return "".join(parts)

    def match_place(self, query: str, context: Optional[Dict] = None) -> Optional[Dict]:
        """主匹配方法"""
        if not query:
            return None

        logger.debug(f"开始匹配地名: {query}")

        # 1. 精确匹配
        result = self.exact_match(query)
        if result:
            logger.debug(f"精确匹配成功: {result['name']}")
            return result

        # 2. 别名匹配
        result = self.alias_match(query)
        if result:
            logger.debug(f"别名匹配成功: {result['name']}")
            return result

        # 3. 层级匹配
        result = self.hierarchical_match(query, context)
        if result:
            logger.debug(f"层级匹配成功: {result['name']}")
            return result

        # 4. 包含匹配
        result = self.contains_match(query)
        if result:
            logger.debug(f"包含匹配成功: {result['name']}")
            return result

        # 5. 模糊匹配
        result = self.fuzzy_match(query)
        if result:
            logger.debug(f"模糊匹配成功: {result['name']}")
            return result

        logger.debug(f"匹配失败: {query}")
        return None

    def batch_match(self, queries: List[str]) -> List[Optional[Dict]]:
        """批量匹配"""
        results = []
        for query in queries:
            result = self.match_place(query)
            results.append(result)
        return results

    def get_statistics(self) -> Dict:
        """获取匹配器统计信息"""
        stats = {}

        # 总数统计
        cursor = self._ensure_connection()
        cursor.execute("SELECT COUNT(*) FROM regions")
        stats['total_regions'] = cursor.fetchone()[0]

        # 按级别统计
        cursor = self._ensure_connection()
        cursor.execute("SELECT level, COUNT(*) FROM regions GROUP BY level ORDER BY level")
        stats['by_level'] = dict(cursor.fetchall())

        # 有坐标统计
        cursor = self._ensure_connection()
        cursor.execute("SELECT COUNT(*) FROM regions WHERE longitude IS NOT NULL AND latitude IS NOT NULL")
        stats['with_coordinates'] = cursor.fetchone()[0]

        # 别名统计
        stats['alias_count'] = len(self.alias_map)

        return stats

    def test_matching_performance(self, test_queries: List[str]) -> Dict:
        """测试匹配性能"""
        logger.info("开始测试匹配性能...")

        results = {
            'total_queries': len(test_queries),
            'successful_matches': 0,
            'failed_matches': 0,
            'match_details': []
        }

        import time
        start_time = time.time()

        for query in test_queries:
            match_start = time.time()
            result = self.match_place(query)
            match_time = time.time() - match_start

            if result:
                results['successful_matches'] += 1
                results['match_details'].append({
                    'query': query,
                    'matched': result['name'],
                    'level': result['level_name'],
                    'time': match_time,
                    'success': True
                })
            else:
                results['failed_matches'] += 1
                results['match_details'].append({
                    'query': query,
                    'matched': None,
                    'level': None,
                    'time': match_time,
                    'success': False
                })

        total_time = time.time() - start_time
        results['total_time'] = total_time
        results['average_time'] = total_time / len(test_queries)
        results['success_rate'] = results['successful_matches'] / len(test_queries)

        logger.info(f"匹配性能测试完成:")
        logger.info(f"   总查询数: {results['total_queries']}")
        logger.info(f"   成功匹配: {results['successful_matches']}")
        logger.info(f"   匹配失败: {results['failed_matches']}")
        logger.info(f"   成功率: {results['success_rate']*100:.1f}%")
        logger.info(f"   平均耗时: {results['average_time']*1000:.2f}ms")

        return results

def main():
    """主函数 - 测试增强匹配器"""
    matcher = EnhancedPlaceMatcher()

    try:
        matcher.connect()

        # 显示统计信息
        stats = matcher.get_statistics()
        logger.info("📊 增强地名匹配器统计:")
        logger.info(f"   总地区数: {stats['total_regions']}")
        logger.info(f"   按级别分布: {stats['by_level']}")
        logger.info(f"   有坐标地区: {stats['with_coordinates']}")
        logger.info(f"   别名映射数: {stats['alias_count']}")

        # 测试查询
        test_queries = [
            "北京", "上海", "广州", "深圳", "杭州", "成都", "西安",
            "朝阳区", "天河区", "海淀区", "福田区",
            "中山路", "人民路", "解放路", "建设路",
            "沙河镇", "太平镇", "新塘镇", "永宁镇",
            "京", "沪", "粤", "苏", "浙", "川", "鲁",
            "燕京", "金陵", "鹏城", "蓉城", "长安"
        ]

        # 运行性能测试
        performance_results = matcher.test_matching_performance(test_queries)

        # 显示部分匹配结果
        logger.info("\n🔍 匹配结果示例:")
        for detail in performance_results['match_details'][:10]:
            if detail['success']:
                logger.info(f"   {detail['query']} -> {detail['matched']} ({detail['level']})")
            else:
                logger.info(f"   {detail['query']} -> 未匹配")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        raise
    finally:
        matcher.close()

if __name__ == "__main__":
    main()