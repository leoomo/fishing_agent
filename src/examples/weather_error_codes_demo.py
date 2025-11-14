#!/usr/bin/env python3
"""
天气服务错误码系统演示

这个脚本演示了如何使用天气服务的错误码系统，
包括基本用法、错误处理和最佳实践。
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入必要的模块
from tools.weather_tool import WeatherTool
from services.weather.datetime_weather_service import DateTimeWeatherService, WeatherServiceErrorCode


class WeatherErrorCodesDemo:
    """天气服务错误码系统演示类"""

    def __init__(self):
        self.weather_tool = WeatherTool()
        self.service = DateTimeWeatherService()

    async def demo_basic_usage(self):
        """演示基本用法"""
        print("\n" + "="*60)
        print("🌤️  基本用法演示")
        print("="*60)

        # 演示成功情况
        print("\n📍 1. 成功查询演示")
        await self._demo_successful_query()

        # 演示不同的错误情况
        error_cases = [
            ("", "2024-12-25", "空地区名"),
            ("北京", "", "空日期"),
            ("广州", "2024-13-25", "无效日期"),
            ("深圳", "1999-01-01", "超出历史范围"),
        ]

        for i, (place, date, desc) in enumerate(error_cases, 2):
            print(f"\n📍 {i}. {desc}演示")
            await self._demo_error_case("weather_by_date", location=place, date=date)

    async def _demo_successful_query(self):
        """演示成功查询"""
        result = await self.weather_tool.execute(
            operation="weather_by_date",
            location="北京",
            date="2024-12-25"
        )

        print(f"   ✅ 请求状态: {'成功' if result.success else '失败'}")

        if result.metadata:
            error_code = result.metadata.get("error_code")
            description = result.metadata.get("description")
            status_message = result.metadata.get("status_message")

            print(f"   🎯 错误码: {error_code}")
            print(f"   📝 描述: {description}")
            print(f"   💬 状态: {status_message}")

        if result.data:
            print(f"   🌡️ 温度: {result.data.get('temperature', 'N/A')}°C")
            print(f"   🌤️ 天气: {result.data.get('condition', 'N/A')}")

    async def _demo_error_case(self, operation: str, **kwargs):
        """演示错误情况"""
        result = await self.weather_tool.execute(operation=operation, **kwargs)

        print(f"   ❌ 请求状态: {'成功' if result.success else '失败'}")

        if result.metadata:
            error_code = result.metadata.get("error_code")
            description = result.metadata.get("description")
            status_message = result.metadata.get("status_message")

            print(f"   🎯 错误码: {error_code}")
            print(f"   📝 描述: {description}")
            print(f"   💬 状态: {status_message}")

            # 根据错误码给出建议
            suggestion = self._get_error_suggestion(error_code)
            if suggestion:
                print(f"   💡 建议: {suggestion}")

    def _get_error_suggestion(self, error_code: int) -> str:
        """根据错误码给出处理建议"""
        suggestions = {
            6: "检查输入参数，确保地区名和日期不为空",
            7: "检查日期格式，使用YYYY-MM-DD格式，确保日期有效",
            8: "检查时间段表达式，如'明天上午'、'今天下午3点'",
            9: "使用有效日期范围（过去1天到未来15天）",
            2: "检查API密钥配置或网络连接",
            4: "检查网络连接，稍后重试",
            3: "检查地区名称，使用标准地名",
            5: "稍后重试，或联系管理员",
        }
        return suggestions.get(error_code, "")

    async def demo_error_code_patterns(self):
        """演示错误码模式处理"""
        print("\n" + "="*60)
        print("🎯 错误码模式处理演示")
        print("="*60)

        # 定义测试场景
        test_scenarios = [
            ("成功场景", {"location": "北京", "date": "2024-12-25"}),
            ("参数错误", {"location": "", "date": "2024-12-25"}),
            ("日期错误", {"location": "上海", "date": "2024-13-25"}),
            ("范围错误", {"location": "深圳", "date": "2030-01-01"}),
        ]

        for scenario_name, params in test_scenarios:
            print(f"\n📋 场景: {scenario_name}")
            await self._process_with_error_handling(params)

    async def _process_with_error_handling(self, params: Dict[str, Any]):
        """使用错误处理逻辑处理请求"""
        result = await self.weather_tool.execute(
            operation="weather_by_date",
            **params
        )

        # 获取错误码信息
        error_code = result.metadata.get("error_code") if result.metadata else -1
        description = result.metadata.get("description", "") if result.metadata else ""

        # 根据错误码类别处理
        if error_code in [0, 1]:
            # 成功类
            print(f"   ✅ 成功获取数据: {description}")
            if result.data:
                print(f"   🌡️ 温度: {result.data.get('temperature', 'N/A')}°C")

        elif error_code in [6, 7, 8]:
            # 参数问题
            print(f"   ⚠️ 参数错误: {description}")
            suggestion = self._get_error_suggestion(error_code)
            print(f"   💡 {suggestion}")
            print("   🔄 请修正输入后重试")

        elif error_code in [2, 4]:
            # API问题
            print(f"   🔄 API问题: {description}")
            print("   📦 已使用模拟数据保证服务可用性")
            if result.data:
                print(f"   🌡️ 模拟数据温度: {result.data.get('temperature', 'N/A')}°C")

        elif error_code in [3, 5, 9]:
            # 数据问题
            print(f"   🌍 数据问题: {description}")
            print("   📦 已使用模拟数据")
            if result.data:
                print(f"   🌡️ 模拟数据温度: {result.data.get('temperature', 'N/A')}°C")

        else:
            # 未知错误
            print(f"   ❓ 未知错误: {description}")
            if result.data:
                print(f"   🌡️ 可用数据: {result.data.get('temperature', 'N/A')}°C")

    async def demo_advanced_usage(self):
        """演示高级用法"""
        print("\n" + "="*60)
        print("🚀 高级用法演示")
        print("="*60)

        # 批量查询演示
        await self._demo_batch_queries()

        # 错误码统计演示
        await self._demo_error_statistics()

        # 服务级别错误处理演示
        await self._demo_service_level_handling()

    async def _demo_batch_queries(self):
        """演示批量查询和错误处理"""
        print("\n📊 批量查询演示")

        batch_requests = [
            {"location": "北京", "date": "2024-12-25"},
            {"location": "", "date": "2024-12-25"},  # 错误：空地区名
            {"location": "上海", "date": "2024-13-25"},  # 错误：无效日期
            {"location": "广州", "date": "2024-12-26"},
        ]

        results = []
        for i, request in enumerate(batch_requests, 1):
            print(f"\n   处理请求 {i}: {request}")
            result = await self.weather_tool.execute(
                operation="weather_by_date",
                **request
            )

            results.append({
                "request": request,
                "success": result.success,
                "error_code": result.metadata.get("error_code") if result.metadata else -1,
                "data": result.data
            })

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        error_codes = [r["error_code"] for r in results if not r["success"]]

        print(f"\n📈 批量查询统计:")
        print(f"   成功: {success_count}/{len(results)}")
        print(f"   失败错误码: {set(error_codes)}")

    async def _demo_error_statistics(self):
        """演示错误码统计"""
        print("\n📈 错误码统计演示")

        # 故意制造各种错误来统计
        error_inducing_requests = [
            {"location": "", "date": "2024-12-25"},    # 错误码 6
            {"location": "北京", "date": ""},         # 错误码 6
            {"location": "上海", "date": "2024-13-25"}, # 错误码 7
            {"location": "广州", "date": "1999-01-01"}, # 错误码 9
            {"location": "深圳", "date": "2030-01-01"}, # 错误码 9
        ]

        error_stats = {}
        for request in error_inducing_requests:
            result = await self.weather_tool.execute(
                operation="weather_by_date",
                **request
            )

            if result.metadata:
                error_code = result.metadata.get("error_code")
                if error_code not in error_stats:
                    error_stats[error_code] = 0
                error_stats[error_code] += 1

        print("   错误码分布:")
        for error_code, count in error_stats.items():
            description = WeatherServiceErrorCode.get_description(error_code)
            print(f"   错误码 {error_code}: {count}次 ({description})")

    async def _demo_service_level_handling(self):
        """演示服务级别的错误处理"""
        print("\n🏢 服务级别错误处理演示")

        # 直接使用DateTimeWeatherService
        print("\n   直接使用DateTimeWeatherService:")
        weather_data, status_msg, error_code = self.service.get_weather_by_date("北京", "2024-12-25")

        print(f"   天气数据: {'有' if weather_data else '无'}")
        print(f"   状态消息: {status_msg}")
        print(f"   错误码: {error_code}")
        print(f"   错误描述: {WeatherServiceErrorCode.get_description(error_code)}")

        # 使用便利方法
        print("\n   使用便利方法检查:")
        is_successful = self.service.is_request_successful(error_code)
        is_api_success = self.service.is_hourly_forecast_successful(error_code)

        print(f"   是否成功(含缓存): {is_successful}")
        print(f"   是否API成功: {is_api_success}")

    async def demo_best_practices(self):
        """演示最佳实践"""
        print("\n" + "="*60)
        print("💡 最佳实践演示")
        print("="*60)

        # 演示日志记录
        await self._demo_logging_practices()

        # 演示重试机制
        await self._demo_retry_mechanism()

        # 演示用户友好消息
        await self._demo_user_friendly_messages()

    async def _demo_logging_practices(self):
        """演示日志记录最佳实践"""
        print("\n📝 日志记录实践")

        result = await self.weather_tool.execute(
            operation="weather_by_date",
            location="北京",
            date="2024-12-25"
        )

        if result.metadata:
            error_code = result.metadata.get("error_code")
            self._log_error_code(error_code, "北京", "演示查询")

    def _log_error_code(self, error_code: int, place_name: str, operation: str):
        """记录错误码到日志"""
        description = WeatherServiceErrorCode.get_description(error_code)

        if error_code in [0, 1]:
            logger.info(f"天气查询成功 - {place_name} ({operation}): {description}")
        elif error_code in [6, 7, 8]:
            logger.warning(f"天气查询参数错误 - {place_name} ({operation}): {description}")
        elif error_code in [2, 4]:
            logger.error(f"天气API问题 - {place_name} ({operation}): {description}")
        else:
            logger.error(f"天气查询失败 - {place_name} ({operation}): {description} (错误码: {error_code})")

    async def _demo_retry_mechanism(self):
        """演示重试机制"""
        print("\n🔄 重试机制实践")

        # 模拟网络错误场景
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            print(f"   尝试 {attempt}/{max_retries}:")

            # 使用一个可能失败的参数
            result = await self.weather_tool.execute(
                operation="weather_by_date",
                location="不存在的城市xyz",
                date="2024-12-25"
            )

            if result.success:
                print("   ✅ 请求成功!")
                break
            else:
                if result.metadata:
                    error_code = result.metadata.get("error_code")
                    if error_code in [2, 4]:  # API问题，可以重试
                        print(f"   ⚠️ 可重试错误: {result.metadata.get('description')}")
                        if attempt < max_retries:
                            print("   🔄 准备重试...")
                            await asyncio.sleep(0.5)  # 模拟延迟
                    else:
                        print(f"   ❌ 不可重试错误: {result.metadata.get('description')}")
                        break

    async def _demo_user_friendly_messages(self):
        """演示用户友好消息"""
        print("\n💬 用户友好消息实践")

        test_cases = [
            (6, "参数错误", "请检查输入参数，确保地区名和日期格式正确"),
            (7, "日期错误", "请使用YYYY-MM-DD格式，如2024-12-25"),
            (9, "日期范围错误", "请查询过去1天到未来15天内的天气"),
            (2, "API错误", "天气服务暂时不可用，请稍后重试"),
        ]

        for error_code, error_type, suggestion in test_cases:
            user_message = self._get_user_friendly_error_message(error_code, "北京")
            print(f"\n   {error_type} (错误码 {error_code}):")
            print(f"   用户消息: {user_message}")
            print(f"   建议: {suggestion}")

    def _get_user_friendly_error_message(self, error_code: int, place_name: str) -> str:
        """获取用户友好的错误消息"""
        messages = {
            0: f"成功获取{place_name}的天气信息",
            1: f"从缓存获取{place_name}的天气信息",
            6: f"查询{place_name}天气时输入参数有误",
            7: f"查询{place_name}天气时日期格式不正确",
            8: f"查询{place_name}天气时时间段表达式无效",
            9: f"查询{place_name}天气时日期超出有效范围",
            2: f"获取{place_name}天气时服务暂时不可用",
            3: f"无法找到{place_name}的天气信息",
            4: f"获取{place_name}天气时网络连接超时",
            5: f"获取{place_name}天气时数据解析失败",
        }
        return messages.get(error_code, f"查询{place_name}天气时遇到问题")

    async def run_all_demos(self):
        """运行所有演示"""
        print("🌤️  天气服务错误码系统完整演示")
        print("="*60)
        print("本演示将展示错误码系统的各种用法和最佳实践")

        try:
            await self.demo_basic_usage()
            await self.demo_error_code_patterns()
            await self.demo_advanced_usage()
            await self.demo_best_practices()

            print("\n" + "="*60)
            print("✅ 所有演示完成!")
            print("="*60)
            print("\n📚 相关文档:")
            print("   - 天气服务错误码系统指南: docs/WEATHER_ERROR_CODES_GUIDE.md")
            print("   - 工具使用指南: docs/TOOLS_GUIDE.md")
            print("   - API文档: docs/API.md")
            print("\n🎯 快速测试:")
            print("   uv run python demo_comprehensive_error_codes.py")
            print("   uv run python examples/weather_error_codes_demo.py")

        except Exception as e:
            logger.error(f"演示过程中发生错误: {str(e)}")
            raise


async def main():
    """主函数"""
    demo = WeatherErrorCodesDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    asyncio.run(main())