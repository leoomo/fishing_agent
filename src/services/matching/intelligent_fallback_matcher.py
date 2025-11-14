#!/usr/bin/env python3
"""
智能降级地名匹配器
当找不到目标地名时，智能查找上级地名作为近似位置
主要解决镇级、村级地名缺失的问题
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from services.matching.city_coordinate_db import CityCoordinateDB
from services.matching.enhanced_place_matcher import EnhancedPlaceMatcher

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FallbackResult:
    """降级匹配结果"""
    success: bool
    original_query: str
    matched_name: str
    coordinates: Tuple[float, float]
    level: int
    level_name: str
    approximation: bool = False
    approximation_reason: str = ""
    confidence: float = 1.0
    full_path: str = ""

class IntelligentFallbackMatcher:
    """智能降级地名匹配器"""

    def __init__(self, db_path: str = "src/data/admin_divisions.db"):
        """
        初始化智能降级匹配器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.city_db = CityCoordinateDB(db_path)
        self.enhanced_matcher = EnhancedPlaceMatcher(db_path)

        # 行政区划后缀模式
        self.admin_suffixes = [
            r'省$', r'自治区$', r'直辖市$', r'特别行政区$',
            r'市$', r'地区$', r'自治州$', r'盟$',
            r'县$', r'区$', r'市$', r'自治县$', r'旗$', r'自治旗$', r'林区$', r'特区$',
            r'镇$', r'乡$', r'街道$', r'苏木$', r'民族乡$', r'民族苏木$',
            r'村$', r'社区$', r'居委会$', r'嘎查$', r'管委会$'
        ]

        # 级别名称映射
        self.level_names = {
            1: "省级",
            2: "地级",
            3: "县级",
            4: "镇级",
            5: "村级"
        }

    def connect(self):
        """连接数据库"""
        self.enhanced_matcher.connect()

    def close(self):
        """关闭连接"""
        self.enhanced_matcher.close()
        self.city_db.close()

    def normalize_place_name(self, place_name: str) -> str:
        """标准化地名"""
        if not place_name:
            return ""

        # 去除空格和特殊字符
        place_name = re.sub(r'\s+', '', place_name)

        # 移除行政区划后缀，保留核心名称
        for suffix in self.admin_suffixes:
            place_name = re.sub(suffix, '', place_name)

        return place_name.strip()

    def extract_administrative_hierarchy(self, place_name: str) -> Dict[str, str]:
        """
        从地名中提取可能的行政区划层级

        Args:
            place_name: 原始地名

        Returns:
            包含可能行政区划信息的字典
        """
        hierarchy = {
            'province': '',
            'city': '',
            'district': '',
            'town': '',
            'village': ''
        }

        # 常见的行政区划标识词
        province_keywords = ['省', '自治区', '直辖市', '特别行政区']
        city_keywords = ['市', '地区', '自治州', '盟']
        district_keywords = ['县', '区', '市', '自治县', '旗', '自治旗', '林区', '特区']
        town_keywords = ['镇', '乡', '街道', '苏木', '民族乡', '民族苏木']
        village_keywords = ['村', '社区', '居委会', '嘎查', '管委会']

        # 简单的层级提取逻辑
        parts = []

        # 按行政区划关键词分割
        for keyword in province_keywords + city_keywords + district_keywords + town_keywords + village_keywords:
            if keyword in place_name:
                parts = place_name.split(keyword)
                break

        if not parts:
            # 如果没有找到明确的行政区划标识，尝试其他方法
            parts = [place_name]

        # 填充层级信息（简化版本）
        if len(parts) >= 1:
            hierarchy['village'] = parts[-1]  # 最具体的部分
        if len(parts) >= 2:
            hierarchy['town'] = parts[-2]
        if len(parts) >= 3:
            hierarchy['district'] = parts[-3]
        if len(parts) >= 4:
            hierarchy['city'] = parts[-4]
        if len(parts) >= 5:
            hierarchy['province'] = parts[-5]

        return hierarchy

    def try_exact_match(self, place_name: str) -> Optional[FallbackResult]:
        """尝试精确匹配"""
        # 使用增强匹配器
        result = self.enhanced_matcher.match_place(place_name)
        if result:
            return FallbackResult(
                success=True,
                original_query=place_name,
                matched_name=result['name'],
                coordinates=(result['longitude'], result['latitude']),
                level=result['level'],
                level_name=result['level_name'],
                approximation=False,
                confidence=1.0,
                full_path=result['full_address']
            )

        # 使用基础坐标数据库
        coords = self.city_db.get_coordinates(place_name)
        if coords:
            admin_info = self.city_db.get_administrative_info(place_name)
            level = admin_info.level if admin_info else 3
            level_name = self.level_names.get(level, f"级别{level}")

            return FallbackResult(
                success=True,
                original_query=place_name,
                matched_name=place_name,
                coordinates=coords,
                level=level,
                level_name=level_name,
                approximation=False,
                confidence=1.0,
                full_path=admin_info.full_path if admin_info else place_name
            )

        return None

    def try_parent_fallback(self, place_name: str) -> Optional[FallbackResult]:
        """尝试上级地名降级"""
        hierarchy = self.extract_administrative_hierarchy(place_name)

        # 逐级尝试上级地名
        fallback_attempts = [
            ('district', hierarchy['district'], '使用县级近似位置'),
            ('city', hierarchy['city'], '使用市级近似位置'),
            ('province', hierarchy['province'], '使用省级近似位置')
        ]

        # 针对常见的镇名模式进行特殊处理
        special_cases = {
            '河桥': [  # 使用去除后缀的名称作为键
                ('临安区', '使用临安区近似位置'),
                ('临安市', '使用临安市近似位置'),
                ('杭州市', '使用杭州市近似位置')
            ],
            '余杭': [  # 使用去除后缀的名称作为键
                ('余杭区', '使用余杭区近似位置'),
                ('杭州市', '使用杭州市近似位置')
            ],
            # 可以添加更多常见的镇名映射
        }

        # 检查特殊案例
        # 先尝试原始地名
        original_name = place_name.replace('镇', '').replace('乡', '').replace('街道', '').strip()

        # 确定使用哪个键来查找特殊案例
        key_to_use = None
        if original_name in special_cases:
            key_to_use = original_name
        else:
            # 尝试完全标准化后的名称
            clean_name = self.normalize_place_name(place_name)
            if clean_name in special_cases:
                key_to_use = clean_name

        if key_to_use:
            for special_place, reason in special_cases[key_to_use]:
                result = self.try_exact_match(special_place)
                if result:
                    result.original_query = place_name
                    result.approximation = True
                    result.approximation_reason = reason
                    result.confidence = 0.9  # 特殊映射给予较高置信度
                    return result

        # 常规降级处理
        for level_name, place_part, reason in fallback_attempts:
            if not place_part:
                continue

            # 尝试匹配上级地名
            result = self.try_exact_match(place_part)
            if result:
                result.original_query = place_name
                result.approximation = True
                result.approximation_reason = reason
                result.confidence = 0.8 - (len(fallback_attempts) - 1) * 0.1  # 逐级降低置信度
                return result

        return None

    def try_contextual_fallback(self, place_name: str) -> Optional[FallbackResult]:
        """尝试基于上下文的降级匹配"""
        # 移除"镇"、"乡"等后缀后尝试匹配
        clean_name = self.normalize_place_name(place_name)

        # 尝试不同的组合
        patterns = [
            clean_name,  # 直接使用清理后的名称
            f"{clean_name}区",  # 尝试加上区后缀
            f"{clean_name}县",  # 尝试加上县后缀
            f"{clean_name}市",  # 尝试加上市后缀
        ]

        for pattern in patterns:
            result = self.try_exact_match(pattern)
            if result:
                result.original_query = place_name
                result.approximation = True
                result.approximation_reason = f"使用'{pattern}'的近似位置"
                result.confidence = 0.7
                return result

        return None

    def try_fuzzy_fallback(self, place_name: str) -> Optional[FallbackResult]:
        """尝试模糊匹配降级"""
        # 使用增强匹配器的模糊匹配
        clean_name = self.normalize_place_name(place_name)

        if len(clean_name) < 2:
            return None

        # 尝试模糊匹配
        result = self.enhanced_matcher.fuzzy_match(clean_name, threshold=0.6)
        if result:
            return FallbackResult(
                success=True,
                original_query=place_name,
                matched_name=result['name'],
                coordinates=(result['longitude'], result['latitude']),
                level=result['level'],
                level_name=result['level_name'],
                approximation=True,
                approximation_reason=f"模糊匹配到'{result['name']}'",
                confidence=0.6,
                full_path=result['full_address']
            )

        return None

    def match_with_fallback(self, place_name: str) -> FallbackResult:
        """
        智能降级匹配主方法

        Args:
            place_name: 要匹配的地名

        Returns:
            FallbackResult: 匹配结果
        """
        logger.debug(f"开始智能降级匹配: {place_name}")

        if not place_name or not place_name.strip():
            return FallbackResult(
                success=False,
                original_query=place_name,
                matched_name="",
                coordinates=(0.0, 0.0),
                level=0,
                level_name="未知",
                approximation=False,
                confidence=0.0
            )

        # 1. 尝试精确匹配
        result = self.try_exact_match(place_name)
        if result:
            logger.debug(f"精确匹配成功: {result.matched_name}")
            return result

        # 2. 尝试上级地名降级
        result = self.try_parent_fallback(place_name)
        if result:
            logger.debug(f"上级地名降级成功: {result.matched_name} ({result.approximation_reason})")
            return result

        # 3. 尝试上下文降级
        result = self.try_contextual_fallback(place_name)
        if result:
            logger.debug(f"上下文降级成功: {result.matched_name} ({result.approximation_reason})")
            return result

        # 4. 尝试模糊匹配降级
        result = self.try_fuzzy_fallback(place_name)
        if result:
            logger.debug(f"模糊匹配降级成功: {result.matched_name} ({result.approximation_reason})")
            return result

        # 5. 完全失败
        logger.debug(f"匹配失败: {place_name}")
        return FallbackResult(
            success=False,
            original_query=place_name,
            matched_name="",
            coordinates=(0.0, 0.0),
            level=0,
            level_name="未找到",
            approximation=False,
            confidence=0.0
        )

    def batch_match_with_fallback(self, place_names: List[str]) -> List[FallbackResult]:
        """批量智能降级匹配"""
        results = []
        for place_name in place_names:
            result = self.match_with_fallback(place_name)
            results.append(result)
        return results

    def test_fallback_performance(self, test_queries: List[str]) -> Dict:
        """测试降级匹配性能"""
        logger.info("开始测试智能降级匹配性能...")

        results = {
            'total_queries': len(test_queries),
            'exact_matches': 0,
            'fallback_matches': 0,
            'failed_matches': 0,
            'match_details': []
        }

        import time
        start_time = time.time()

        for query in test_queries:
            match_start = time.time()
            result = self.match_with_fallback(query)
            match_time = time.time() - match_start

            if result.success:
                if result.approximation:
                    results['fallback_matches'] += 1
                    match_type = "降级匹配"
                else:
                    results['exact_matches'] += 1
                    match_type = "精确匹配"

                results['match_details'].append({
                    'query': query,
                    'matched': result.matched_name,
                    'level': result.level_name,
                    'approximation': result.approximation,
                    'approximation_reason': result.approximation_reason,
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
                    'approximation': False,
                    'approximation_reason': '',
                    'confidence': 0.0,
                    'time': match_time,
                    'success': False,
                    'match_type': "匹配失败"
                })

        total_time = time.time() - start_time
        results['total_time'] = total_time
        results['average_time'] = total_time / len(test_queries)
        results['success_rate'] = (results['exact_matches'] + results['fallback_matches']) / len(test_queries)
        results['fallback_rate'] = results['fallback_matches'] / len(test_queries)

        logger.info(f"智能降级匹配性能测试完成:")
        logger.info(f"   总查询数: {results['total_queries']}")
        logger.info(f"   精确匹配: {results['exact_matches']}")
        logger.info(f"   降级匹配: {results['fallback_matches']}")
        logger.info(f"   匹配失败: {results['failed_matches']}")
        logger.info(f"   成功率: {results['success_rate']*100:.1f}%")
        logger.info(f"   降级率: {results['fallback_rate']*100:.1f}%")
        logger.info(f"   平均耗时: {results['average_time']*1000:.2f}ms")

        return results

def main():
    """主函数 - 测试智能降级匹配器"""
    matcher = IntelligentFallbackMatcher()

    try:
        matcher.connect()

        print("🧪 测试智能降级地名匹配器")
        print("=" * 60)

        # 测试查询列表
        test_queries = [
            "河桥镇",           # 镇级，应该降级到临安区
            "临安河桥镇",       # 包含上级地名的镇级
            "杭州河桥镇",       # 包含更上级地名的镇级
            "余杭区河桥镇",     # 另一个区+镇的组合
            "西湖区河桥镇",     # 另一个区+镇的组合
            "临安区",           # 县级，应该精确匹配
            "杭州市",           # 地级，应该精确匹配
            "浙江省",           # 省级，应该精确匹配
            "不存在的镇",       # 完全不存在的地名
            "北京市朝阳区",     # 应该精确匹配
            "上海市浦东新区",   # 应该精确匹配
            "深圳市南山区",     # 应该精确匹配
        ]

        # 运行性能测试
        performance_results = matcher.test_fallback_performance(test_queries)

        # 显示详细结果
        print("\n📋 详细匹配结果:")
        for detail in performance_results['match_details']:
            if detail['success']:
                approx_info = ""
                if detail['approximation']:
                    approx_info = f" ({detail['approximation_reason']})"

                print(f"   ✅ {detail['query']} -> {detail['matched']} ({detail['level']}){approx_info}")
                print(f"      置信度: {detail['confidence']:.2f}, 类型: {detail['match_type']}")
            else:
                print(f"   ❌ {detail['query']} -> 未匹配")

        print(f"\n📊 性能统计:")
        print(f"   成功率: {performance_results['success_rate']*100:.1f}%")
        print(f"   降级率: {performance_results['fallback_rate']*100:.1f}%")
        print(f"   平均耗时: {performance_results['average_time']*1000:.2f}ms")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        raise
    finally:
        matcher.close()

if __name__ == "__main__":
    main()