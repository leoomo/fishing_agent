#!/usr/bin/env python3
"""
全国覆盖功能综合测试脚本
测试新的全国行政区划数据库和增强匹配系统的完整功能
"""

import sqlite3
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.matching.enhanced_place_matcher import EnhancedPlaceMatcher
from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NationalCoverageTester:
    """全国覆盖功能测试器"""

    def __init__(self, db_path: str = "src/data/admin_divisions.db"):
        self.db_path = db_path
        self.place_matcher = EnhancedPlaceMatcher(db_path)
        self.weather_service = None

    def test_database_connectivity(self) -> bool:
        """测试数据库连接性"""
        logger.info("🔍 测试数据库连接性...")
        try:
            self.place_matcher.connect()
            logger.info("✅ 数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def test_database_coverage(self) -> Dict:
        """测试数据库覆盖情况"""
        logger.info("🔍 测试数据库覆盖情况...")

        stats = self.place_matcher.get_statistics()

        coverage_report = {
            'total_regions': stats['total_regions'],
            'by_level': stats['by_level'],
            'with_coordinates': stats['with_coordinates'],
            'coordinate_coverage_rate': stats['with_coordinates'] / stats['total_regions'] * 100
        }

        logger.info("📊 数据库覆盖报告:")
        logger.info(f"   总地区数: {coverage_report['total_regions']}")
        logger.info(f"   坐标覆盖率: {coverage_report['coordinate_coverage_rate']:.1f}%")
        logger.info("   按级别分布:")
        for level, count in coverage_report['by_level'].items():
            level_name = {1: "省级", 2: "地级", 3: "县级", 4: "乡镇级", 5: "村级"}.get(level, f"级别{level}")
            logger.info(f"     {level_name}: {count}个")

        return coverage_report

    def test_place_matching(self) -> Dict:
        """测试地名匹配功能"""
        logger.info("🔍 测试地名匹配功能...")

        # 测试用例分类
        test_cases = {
            '省级地区': [
                "北京", "上海", "广州", "深圳", "杭州", "成都", "西安",
                "京", "沪", "粤", "苏", "浙", "川", "鲁",
                "燕京", "金陵", "鹏城", "蓉城", "长安"
            ],
            '地级市': [
                "苏州市", "无锡市", "常州市", "南京市", "武汉市", "长沙市",
                "珠海", "佛山", "东莞", "中山", "青岛", "宁波", "厦门"
            ],
            '县区级': [
                "朝阳区", "天河区", "海淀区", "福田区", "罗湖区",
                "西湖区", "上城区", "锦江区", "青羊区", "新城区"
            ],
            '乡镇级': [
                "沙河镇", "太平镇", "新塘镇", "永宁镇", "仙村镇",
                "河桥镇", "中新镇", "石楼镇"
            ],
            '模糊查询': [
                "中山路", "人民路", "解放路", "建设路", "和平路"
            ]
        }

        all_results = {}
        total_tests = 0
        total_successes = 0

        for category, queries in test_cases.items():
            logger.info(f"   测试{category}...")
            category_results = []

            for query in queries:
                start_time = time.time()
                result = self.place_matcher.match_place(query)
                match_time = time.time() - start_time

                success = result is not None
                total_tests += 1
                if success:
                    total_successes += 1

                category_results.append({
                    'query': query,
                    'success': success,
                    'result': result['name'] if result else None,
                    'level': result['level_name'] if result else None,
                    'time': match_time
                })

            all_results[category] = category_results

        # 计算总体统计
        overall_success_rate = total_successes / total_tests * 100 if total_tests > 0 else 0

        matching_report = {
            'total_tests': total_tests,
            'total_successes': total_successes,
            'success_rate': overall_success_rate,
            'category_results': all_results
        }

        logger.info(f"📊 地名匹配测试报告:")
        logger.info(f"   总测试数: {matching_report['total_tests']}")
        logger.info(f"   成功匹配: {matching_report['total_successes']}")
        logger.info(f"   成功率: {matching_report['success_rate']:.1f}%")

        return matching_report

    def test_weather_integration(self) -> Dict:
        """测试天气服务集成"""
        logger.info("🔍 测试天气服务集成...")

        try:
            # 初始化天气服务
            self.weather_service = EnhancedCaiyunWeatherService()

            # 测试查询列表
            test_locations = [
                "北京市", "上海市", "广州市", "深圳市", "杭州市",
                "朝阳区", "天河区", "海淀区",
                "沙河镇", "太平镇"
            ]

            weather_results = []
            total_tests = len(test_locations)
            total_successes = 0

            for location in test_locations:
                logger.info(f"   测试天气查询: {location}")
                start_time = time.time()

                try:
                    weather_data = self.weather_service.get_weather(location)
                    query_time = time.time() - start_time

                    if weather_data and 'temperature' in weather_data:
                        total_successes += 1
                        weather_results.append({
                            'location': location,
                            'success': True,
                            'temperature': weather_data.get('temperature'),
                            'description': weather_data.get('description', ''),
                            'query_time': query_time
                        })
                        logger.info(f"     ✅ {weather_data.get('temperature')}°C, {weather_data.get('description', '')}")
                    else:
                        weather_results.append({
                            'location': location,
                            'success': False,
                            'error': 'No weather data returned',
                            'query_time': query_time
                        })
                        logger.info(f"     ❌ 未获取到天气数据")

                except Exception as e:
                    query_time = time.time() - start_time
                    weather_results.append({
                        'location': location,
                        'success': False,
                        'error': str(e),
                        'query_time': query_time
                    })
                    logger.info(f"     ❌ 查询失败: {e}")

            success_rate = total_successes / total_tests * 100 if total_tests > 0 else 0

            weather_report = {
                'total_tests': total_tests,
                'total_successes': total_successes,
                'success_rate': success_rate,
                'results': weather_results
            }

            logger.info(f"📊 天气服务测试报告:")
            logger.info(f"   总测试数: {weather_report['total_tests']}")
            logger.info(f"   成功查询: {weather_report['total_successes']}")
            logger.info(f"   成功率: {weather_report['success_rate']:.1f}%")

            return weather_report

        except Exception as e:
            logger.error(f"❌ 天气服务测试失败: {e}")
            return {'error': str(e)}

    def test_performance(self) -> Dict:
        """测试系统性能"""
        logger.info("🔍 测试系统性能...")

        # 大量地名匹配性能测试
        large_query_list = []
        for level in [1, 2, 3]:
            self.place_matcher.cursor.execute(
                "SELECT name FROM regions WHERE level = ? ORDER BY RANDOM() LIMIT 100",
                (level,)
            )
            names = [row[0] for row in self.place_matcher.cursor.fetchall()]
            large_query_list.extend(names)

        logger.info(f"   执行 {len(large_query_list)} 个地名匹配查询...")

        start_time = time.time()
        successful_matches = 0

        for query in large_query_list:
            result = self.place_matcher.match_place(query)
            if result:
                successful_matches += 1

        total_time = time.time() - start_time
        average_time = total_time / len(large_query_list)

        performance_report = {
            'total_queries': len(large_query_list),
            'successful_matches': successful_matches,
            'total_time': total_time,
            'average_query_time': average_time,
            'queries_per_second': len(large_query_list) / total_time
        }

        logger.info(f"📊 性能测试报告:")
        logger.info(f"   总查询数: {performance_report['total_queries']}")
        logger.info(f"   成功匹配: {performance_report['successful_matches']}")
        logger.info(f"   总耗时: {performance_report['total_time']:.2f}s")
        logger.info(f"   平均耗时: {performance_report['average_query_time']*1000:.2f}ms")
        logger.info(f"   查询速度: {performance_report['queries_per_second']:.0f} queries/s")

        return performance_report

    def generate_test_report(self, coverage_report: Dict, matching_report: Dict,
                           weather_report: Dict, performance_report: Dict) -> Dict:
        """生成综合测试报告"""
        logger.info("📝 生成综合测试报告...")

        report = {
            'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'database_coverage': coverage_report,
            'place_matching': matching_report,
            'weather_integration': weather_report,
            'performance': performance_report,
            'summary': {
                'overall_success': True,
                'key_metrics': {
                    'database_coverage_rate': coverage_report['coordinate_coverage_rate'],
                    'place_matching_success_rate': matching_report['success_rate'],
                    'weather_service_success_rate': weather_report.get('success_rate', 0),
                    'average_query_time_ms': performance_report['average_query_time'] * 1000
                }
            }
        }

        # 评估整体成功标准
        metrics = report['summary']['key_metrics']
        if (metrics['database_coverage_rate'] >= 95 and
            metrics['place_matching_success_rate'] >= 70 and
            metrics['weather_service_success_rate'] >= 80 and
            metrics['average_query_time_ms'] <= 10):
            report['summary']['overall_success'] = True
            report['summary']['status'] = 'EXCELLENT'
        elif (metrics['database_coverage_rate'] >= 90 and
              metrics['place_matching_success_rate'] >= 60 and
              metrics['weather_service_success_rate'] >= 70 and
              metrics['average_query_time_ms'] <= 20):
            report['summary']['overall_success'] = True
            report['summary']['status'] = 'GOOD'
        else:
            report['summary']['overall_success'] = False
            report['summary']['status'] = 'NEEDS_IMPROVEMENT'

        # 保存报告到文件
        report_file = 'national_coverage_test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 测试报告已保存到: {report_file}")

        return report

    def run_comprehensive_test(self) -> Dict:
        """运行综合测试"""
        logger.info("🚀 开始全国覆盖功能综合测试...")
        logger.info("=" * 60)

        test_results = {}

        try:
            # 1. 数据库连接性测试
            if not self.test_database_connectivity():
                return {'error': '数据库连接失败'}

            # 2. 数据库覆盖测试
            test_results['coverage'] = self.test_database_coverage()

            # 3. 地名匹配测试
            test_results['matching'] = self.test_place_matching()

            # 4. 天气服务集成测试
            test_results['weather'] = self.test_weather_integration()

            # 5. 性能测试
            test_results['performance'] = self.test_performance()

            # 6. 生成综合报告
            comprehensive_report = self.generate_test_report(
                test_results['coverage'],
                test_results['matching'],
                test_results['weather'],
                test_results['performance']
            )

            # 显示最终结果
            logger.info("=" * 60)
            logger.info("🎉 全国覆盖功能综合测试完成！")
            logger.info(f"📋 整体状态: {comprehensive_report['summary']['status']}")
            logger.info(f"📊 关键指标:")
            metrics = comprehensive_report['summary']['key_metrics']
            logger.info(f"   数据库覆盖率: {metrics['database_coverage_rate']:.1f}%")
            logger.info(f"   地名匹配成功率: {metrics['place_matching_success_rate']:.1f}%")
            logger.info(f"   天气服务成功率: {metrics['weather_service_success_rate']:.1f}%")
            logger.info(f"   平均查询时间: {metrics['average_query_time_ms']:.2f}ms")

            return comprehensive_report

        except Exception as e:
            logger.error(f"❌ 综合测试过程中发生错误: {e}")
            return {'error': str(e)}

        finally:
            if self.place_matcher:
                self.place_matcher.close()

def main():
    """主函数"""
    tester = NationalCoverageTester()
    report = tester.run_comprehensive_test()
    return report

if __name__ == "__main__":
    main()