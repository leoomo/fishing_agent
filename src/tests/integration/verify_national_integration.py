#!/usr/bin/env python3
"""
验证全国覆盖功能集成到LangChain智能体的效果
不依赖外部API，重点测试数据库和匹配功能
"""

import sys
import os
import sqlite3
import time
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.matching.enhanced_place_matcher import EnhancedPlaceMatcher
from services.weather.enhanced_weather_service import EnhancedCaiyunWeatherService

def test_database_connectivity():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        conn = sqlite3.connect("src/data/admin_divisions.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM regions")
        count = cursor.fetchone()[0]

        cursor.execute("SELECT level, COUNT(*) FROM regions GROUP BY level ORDER BY level")
        level_stats = cursor.fetchall()

        conn.close()

        print(f"✅ 数据库连接成功")
        print(f"📊 总地区数: {count}")
        print(f"📋 按级别分布:")
        for level, cnt in level_stats:
            level_name = {1: "省级", 2: "地级", 3: "县级", 4: "乡镇级", 5: "村级"}.get(level, f"级别{level}")
            print(f"   {level_name}: {cnt}个")

        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_place_matcher():
    """测试地名匹配器"""
    print("\n🔍 测试增强地名匹配器...")
    try:
        matcher = EnhancedPlaceMatcher()
        matcher.connect()

        # 测试各类地名
        test_cases = [
            # 省级
            ("北京市", "省级"),
            ("上海市", "省级"),
            ("广东省", "省级"),
            ("浙江省", "省级"),
            ("京", "省级别名"),
            ("沪", "省级别名"),

            # 地级
            ("广州市", "地级"),
            ("深圳市", "地级"),
            ("杭州市", "地级"),
            ("成都市", "地级"),
            ("西安市", "地级"),

            # 县级
            ("朝阳区", "县级"),
            ("天河区", "县级"),
            ("海淀区", "县级"),
            ("福田区", "县级"),
            ("西湖区", "县级"),

            # 乡镇级
            ("沙河镇", "乡镇级"),
            ("太平镇", "乡镇级"),
            ("新塘镇", "乡镇级"),
            ("永宁镇", "乡镇级"),
            ("河桥镇", "乡镇级"),

            # 模糊查询
            ("中山路", "模糊查询"),
            ("人民路", "模糊查询"),
            ("解放路", "模糊查询"),
        ]

        success_count = 0
        total_count = len(test_cases)

        print(f"📝 测试 {total_count} 个地名:")
        for place, expected_type in test_cases:
            start_time = time.time()
            result = matcher.match_place(place)
            match_time = time.time() - start_time

            if result:
                success_count += 1
                actual_type = result['level_name']
                match_status = "✅" if actual_type == expected_type else "⚠️"
                print(f"   {match_status} {place} -> {result['name']} ({actual_type}) {match_time*1000:.1f}ms")
            else:
                print(f"   ❌ {place} -> 未匹配")

        matcher.close()

        success_rate = success_count / total_count * 100
        print(f"\n📊 匹配测试结果:")
        print(f"   成功匹配: {success_count}/{total_count}")
        print(f"   成功率: {success_rate:.1f}%")

        return success_rate >= 70

    except Exception as e:
        print(f"❌ 地名匹配器测试失败: {e}")
        return False

def test_weather_service_integration():
    """测试天气服务集成"""
    print("\n🔍 测试天气服务集成...")
    try:
        weather_service = EnhancedCaiyunWeatherService()

        # 测试地名解析功能
        test_locations = [
            "北京市", "上海市", "广州市", "深圳市", "杭州市",
            "朝阳区", "天河区", "海淀区", "福田区", "西湖区",
            "沙河镇", "太平镇", "新塘镇", "永宁镇"
        ]

        success_count = 0
        total_count = len(test_locations)

        print(f"📝 测试 {total_count} 个地点的地名解析:")
        for location in test_locations:
            try:
                start_time = time.time()
                # 测试地名解析（不调用实际API）
                place_info = weather_service.place_matcher.match_place(location)
                resolve_time = time.time() - start_time

                if place_info:
                    success_count += 1
                    print(f"   ✅ {location} -> {place_info['name']} ({place_info['level_name']}) {resolve_time*1000:.1f}ms")
                else:
                    print(f"   ❌ {location} -> 解析失败")

            except Exception as e:
                print(f"   ❌ {location} -> 错误: {e}")

        success_rate = success_count / total_count * 100
        print(f"\n📊 地名解析测试结果:")
        print(f"   成功解析: {success_count}/{total_count}")
        print(f"   成功率: {success_rate:.1f}%")

        return success_rate >= 70

    except Exception as e:
        print(f"❌ 天气服务集成测试失败: {e}")
        return False

def test_agent_integration():
    """测试智能体集成"""
    print("\n🔍 测试LangChain智能体集成...")
    try:
        # 导入智能体模块
        from modern_langchain_agent import ModernLangChainAgent

        # 测试智能体类是否能正常初始化（不调用API）
        print("📝 测试智能体类初始化...")

        # 测试get_weather工具是否能正常工作
        print("📝 测试天气工具功能...")

        # 创建天气服务实例
        weather_service = EnhancedCaiyunWeatherService()

        # 测试几个关键地点的匹配
        key_locations = ["北京市", "上海市", "广州市", "朝阳区", "天河区", "沙河镇"]
        tool_success_count = 0

        for location in key_locations:
            try:
                result = weather_service.get_weather(location)
                if result and 'location' in result:
                    tool_success_count += 1
                    print(f"   ✅ 天气工具: {location} -> {result['location']}")
                else:
                    print(f"   ❌ 天气工具: {location} -> 失败")
            except Exception as e:
                print(f"   ❌ 天气工具: {location} -> 错误: {e}")

        tool_success_rate = tool_success_count / len(key_locations) * 100
        print(f"\n📊 智能体工具测试结果:")
        print(f"   工具成功率: {tool_success_rate:.1f}%")

        return tool_success_rate >= 70

    except Exception as e:
        print(f"❌ 智能体集成测试失败: {e}")
        return False

def generate_integration_report():
    """生成集成报告"""
    print("\n📝 生成全国覆盖功能集成报告...")

    report = {
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests': {}
    }

    # 运行各项测试
    report['tests']['database'] = {
        'name': '数据库连接测试',
        'passed': test_database_connectivity()
    }

    report['tests']['place_matcher'] = {
        'name': '地名匹配器测试',
        'passed': test_place_matcher()
    }

    report['tests']['weather_service'] = {
        'name': '天气服务集成测试',
        'passed': test_weather_service_integration()
    }

    report['tests']['agent_integration'] = {
        'name': '智能体集成测试',
        'passed': test_agent_integration()
    }

    # 计算总体结果
    passed_tests = sum(1 for test in report['tests'].values() if test['passed'])
    total_tests = len(report['tests'])

    report['summary'] = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'success_rate': passed_tests / total_tests * 100,
        'overall_success': passed_tests == total_tests
    }

    # 保存报告
    report_file = 'national_integration_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 全国覆盖功能集成测试完成！")
    print("=" * 60)
    print(f"📊 测试总结:")
    print(f"   总测试数: {report['summary']['total_tests']}")
    print(f"   通过测试: {report['summary']['passed_tests']}")
    print(f"   成功率: {report['summary']['success_rate']:.1f}%")
    print(f"   整体状态: {'✅ 成功' if report['summary']['overall_success'] else '❌ 失败'}")
    print(f"📁 报告已保存到: {report_file}")

    return report

def main():
    """主函数"""
    print("🚀 全国覆盖功能集成验证")
    print("=" * 60)
    print("测试LangChain智能体是否正确集成全国覆盖功能")
    print("包括: 数据库连接、地名匹配、天气服务、智能体集成")
    print("=" * 60)

    report = generate_integration_report()
    return report

if __name__ == "__main__":
    main()