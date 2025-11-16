#!/usr/bin/env python3
"""
增强版彩云天气 API 服务模块
集成智能地名匹配、坐标数据库查询、缓存机制等功能
支持全国所有行政区划的天气查询
"""

import os
import json
import requests
from typing import Dict, Optional, Union, Tuple
import logging
from dataclasses import dataclass, asdict

# 导入自定义组件
from .weather_service import WeatherData, CaiyunWeatherService
from ..matching.city_coordinate_db import CityCoordinateDB, PlaceInfo
from ..matching.enhanced_place_matcher import EnhancedPlaceMatcher
from .weather_cache import WeatherCache, get_weather_cache
from ..coordinate.amap_coordinate_service import AmapCoordinateService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedCaiyunWeatherService(CaiyunWeatherService):
    """增强版彩云天气 API 服务，支持全国地区查询"""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        初始化增强版天气服务

        Args:
            api_key: 彩云天气 API 密钥
            timeout: API 请求超时时间（秒）
        """
        super().__init__(api_key, timeout)

        # 初始化增强组件 - 使用绝对路径确保在不同工作目录下都能找到数据库
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent  # 从 src/services/weather/ 回到项目根目录
        db_path = project_root / "src" / "data" / "admin_divisions.db"
        self.db_path = str(db_path)

        # 延迟初始化，避免线程问题
        self.coordinate_db = None
        self.place_matcher = None
        self._db_initialized = False

        self.cache = get_weather_cache()
        self.amap_service = AmapCoordinateService()

        logger.info("增强版天气服务初始化完成（延迟数据库连接）")

    def _ensure_db_initialized(self):
        """确保数据库连接已初始化（线程安全）"""
        if not self._db_initialized:
            from ..matching.city_coordinate_db import CityCoordinateDB
            from ..matching.enhanced_place_matcher import EnhancedPlaceMatcher

            self.coordinate_db = CityCoordinateDB(self.db_path)
            self.place_matcher = EnhancedPlaceMatcher(self.db_path)
            self.place_matcher.connect()
            self._db_initialized = True

            logger.info("数据库连接已建立（线程安全）")

    def get_coordinates(self, place_name: str) -> Optional[Tuple[float, float]]:
        """
        获取地名坐标（增强版本，支持全国地区）
        查询优先级: 1.本地数据库 -> 2.高德API -> 3.原有逻辑降级

        Args:
            place_name: 地名（支持省、市、县、乡各级）

        Returns:
            (longitude, latitude) 坐标元组，如果找不到则返回 None
        """
        if not place_name or not place_name.strip():
            return None

        # 确保数据库已初始化（线程安全）
        try:
            self._ensure_db_initialized()
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            # 如果数据库初始化失败，跳过数据库查询，直接使用高德API
            return self._fallback_to_amap(place_name)

        # 1. 检查缓存
        cache_key = self.cache._generate_key(place_name, {"type": "coordinates"})
        cached_coords = self.cache.get(place_name, extra_params={"type": "coordinates"})

        logger.debug(f"缓存查询: place={place_name}, key={cache_key}, result={cached_coords}")

        if cached_coords:
            logger.info(f"从缓存获取坐标: {place_name} -> {cached_coords}")
            return cached_coords

        # 2. 优先查询本地数据库（智能地名匹配）
        try:
            match_result = self.place_matcher.match_place(place_name)
            if match_result:
                coords = (match_result['longitude'], match_result['latitude'])

                # 缓存结果（缓存1小时）
                self.cache.set(place_name, coords, ttl=3600, extra_params={"type": "coordinates"})

                logger.info(f"本地数据库匹配成功: {place_name} -> {match_result['name']} "
                           f"({coords[0]:.4f}, {coords[1]:.4f}) "
                           f"级别: {match_result['level_name']}")

                return coords
        except Exception as e:
            logger.error(f"本地数据库查询失败: {place_name}, error={e}")

        # 3. 本地数据库无匹配，查询高德API
        logger.info(f"本地数据库无匹配: {place_name}，尝试高德API查询")
        try:
            amap_result = self.amap_service.get_coordinate(place_name)
            if amap_result:
                coords = (amap_result.longitude, amap_result.latitude)

                # 缓存结果（缓存1小时）
                cache_key = self.cache._generate_key(place_name, {"type": "coordinates"})
                self.cache.set(place_name, coords, ttl=3600, extra_params={"type": "coordinates"})

                logger.info(f"高德API查询成功: {place_name} -> "
                           f"({coords[0]:.4f}, {coords[1]:.4f}) "
                           f"级别: {amap_result.level}")
                logger.info(f"坐标已缓存: key={cache_key}, place={place_name}")

                return coords
            else:
                logger.warning(f"高德API查询失败: {place_name}")
        except Exception as e:
            logger.error(f"高德API查询异常: {place_name}, error={e}")

        # 4. 高德API也失败，降级到原有逻辑
        logger.warning(f"高德API查询失败: {place_name}，降级到原有坐标查询")
        original_coords = super().get_coordinates(place_name)

        if original_coords:
            # 缓存原有坐标
            self.cache.set(place_name, original_coords, ttl=3600, extra_params={"type": "coordinates"})
            logger.info(f"原有逻辑查询成功: {place_name} -> ({original_coords[0]:.4f}, {original_coords[1]:.4f})")
        else:
            logger.warning(f"所有查询方式都失败: {place_name}")

        return original_coords

    def _fallback_to_amap(self, place_name: str) -> Optional[Tuple[float, float]]:
        """直接回退到高德API查询（数据库失败时使用）"""
        try:
            amap_result = self.amap_service.get_coordinate(place_name)
            if amap_result:
                coords = (amap_result.longitude, amap_result.latitude)

                # 缓存结果（缓存1小时）
                self.cache.set(place_name, coords, ttl=3600, extra_params={"type": "coordinates"})

                logger.info(f"高德API回退查询成功: {place_name} -> "
                           f"({coords[0]:.4f}, {coords[1]:.4f}) "
                           f"级别: {amap_result.level}")
                return coords
            else:
                logger.warning(f"高德API回退查询失败: {place_name}")
        except Exception as e:
            logger.error(f"高德API回退查询异常: {place_name}, error={e}")

        # 最后回退到原有逻辑
        return super().get_coordinates(place_name)

    def get_weather(self, place_name: str) -> Tuple[WeatherData, str]:
        """
        获取指定地区的天气信息（增强版本）

        Args:
            place_name: 地区名称（支持各级行政区划）

        Returns:
            (WeatherData, status_message) 元组
            status_message 描述了数据来源和匹配信息
        """
        if not place_name or not place_name.strip():
            error_msg = "地区名称不能为空"
            logger.error(error_msg)
            return self._create_error_weather_data(error_msg), f"错误: {error_msg}"

        # 1. 检查天气缓存
        cached_weather = self.cache.get(place_name, extra_params={"type": "weather"})
        if cached_weather:
            weather_data = WeatherData(**cached_weather["data"])
            logger.info(f"从缓存获取天气: {place_name}")
            return weather_data, f"缓存数据（{cached_weather.get('source', '未知来源')}）"

        # 2. 获取坐标
        coordinates = self.get_coordinates(place_name)
        if not coordinates:
            error_msg = f"未找到地区 '{place_name}' 的坐标信息"
            logger.warning(error_msg)
            fallback_data = self.get_fallback_weather(place_name)
            return fallback_data, f"模拟数据（坐标未找到）"

        longitude, latitude = coordinates

        # 3. 尝试调用天气 API
        weather_data = None
        source_message = ""

        if self.api_key:
            try:
                api_data = self.call_weather_api(longitude, latitude)
                if api_data:
                    weather_data = self.parse_weather_data(api_data)
                    if weather_data:
                        source_message = "实时数据（彩云天气 API）"
                        logger.info(f"API 调用成功: {place_name}")
                    else:
                        logger.warning(f"API 数据解析失败: {place_name}")
                        source_message = "API 数据解析失败"
                else:
                    logger.warning(f"API 调用失败: {place_name}")
                    source_message = "API 调用失败"
            except Exception as e:
                logger.error(f"API 调用异常: {place_name}, 错误: {e}")
                source_message = f"API 调用异常: {str(e)}"
        else:
            logger.info("未配置 API 密钥，使用模拟数据")
            source_message = "未配置 API 密钥"

        # 4. 如果 API 失败，使用模拟数据
        if weather_data is None:
            weather_data = self.get_fallback_weather(place_name)
            if not source_message:
                source_message = "模拟数据（API 不可用）"
            else:
                source_message = f"模拟数据（{source_message}）"

        # 5. 缓存结果（缓存30分钟）
        cache_data = {
            "data": asdict(weather_data),
            "source": source_message,
            "coordinates": coordinates,
            "timestamp": __import__('time').time()
        }
        self.cache.set(place_name, cache_data, ttl=1800, extra_params={"type": "weather"})

        # 6. 增强返回信息
        if coordinates:
            enhanced_source = f"{source_message} | 坐标: ({longitude:.4f}, {latitude:.4f})"
        else:
            enhanced_source = source_message

        return weather_data, enhanced_source

    def _create_error_weather_data(self, error_message: str) -> WeatherData:
        """创建错误状态的天气数据"""
        return WeatherData(
            temperature=0.0,
            apparent_temperature=0.0,
            humidity=0.0,
            pressure=0.0,
            wind_speed=0.0,
            wind_direction=0.0,
            condition="错误",
            description=error_message
        )

    def get_fallback_weather(self, place_name: str) -> WeatherData:
        """
        重写父类的fallback方法，返回错误信息而非模拟数据
        为避免误导用户，不再生成任何模拟天气数据

        Args:
            place_name: 地区名称

        Returns:
            错误状态的天气数据
        """
        logger.warning(f"增强版天气服务查询失败，不再生成模拟数据: {place_name}")

        # 返回明确的错误信息，不生成任何模拟天气数据
        return WeatherData(
            temperature=0.0,
            apparent_temperature=0.0,
            humidity=0.0,
            pressure=0.0,
            wind_speed=0.0,
            wind_direction=0.0,
            condition="天气服务查询失败",
            description="天气服务查询失败，请稍后再试"
        )

    def batch_get_weather(self, place_names: list) -> list:
        """
        批量获取多个地区的天气信息

        Args:
            place_names: 地区名称列表

        Returns:
            天气信息列表
        """
        results = []
        for place_name in place_names:
            try:
                weather_data, source = self.get_weather(place_name)
                results.append({
                    "place": place_name,
                    "weather": weather_data,
                    "source": source,
                    "success": True
                })
            except Exception as e:
                logger.error(f"批量查询失败: {place_name}, 错误: {e}")
                results.append({
                    "place": place_name,
                    "weather": None,
                    "source": f"查询失败: {str(e)}",
                    "success": False
                })

        return results

    def search_places(self, query: str, limit: int = 10) -> list:
        """
        搜索匹配的地区

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            匹配的地区列表
        """
        # 简化的搜索：使用单个查询并获取结果
        result = self.place_matcher.match_place(query)
        places = []
        if result:
            places.append({
                "name": result['name'],
                "level": result['level'],
                "coordinates": (result['longitude'], result['latitude']),
                "level_name": result['level_name'],
                "full_address": result.get('full_address', '')
            })

        return places[:limit]

    def get_supported_places_summary(self) -> dict:
        """获取支持的地区摘要信息"""
        db_stats = self.coordinate_db.get_statistics()
        matcher_stats = self.place_matcher.get_statistics()
        cache_stats = self.cache.get_statistics()

        return {
            "database_stats": db_stats,
            "matcher_stats": matcher_stats,
            "cache_stats": cache_stats,
            "api_configured": bool(self.api_key),
            "service_version": "enhanced-v1.0"
        }

    def clear_cache(self) -> dict:
        """清理所有缓存"""
        # 清理各组件缓存
        self.coordinate_db.clear_cache()
        # place_matcher 没有clear_cache方法，跳过
        self.cache.clear()

        return {
            "coordinate_db_cleared": True,
            "place_matcher_cleared": False,  # 没有此方法
            "weather_cache_cleared": True,
            "message": "缓存已清理（place_matcher不支持clear_cache）"
        }

    def __del__(self):
        """析构函数"""
        try:
            if hasattr(self, 'coordinate_db'):
                self.coordinate_db.close()
            if hasattr(self, 'place_matcher'):
                self.place_matcher.close()
            # 保存缓存到文件
            if hasattr(self, 'cache') and hasattr(self.cache, '_save_file_cache'):
                self.cache._save_file_cache()
        except:
            pass


# 全局增强版天气服务实例
_enhanced_weather_service = None

def get_enhanced_weather_service() -> EnhancedCaiyunWeatherService:
    """获取全局增强版天气服务实例"""
    global _enhanced_weather_service
    if _enhanced_weather_service is None:
        _enhanced_weather_service = EnhancedCaiyunWeatherService()
    return _enhanced_weather_service


def get_enhanced_weather_info(place_name: str) -> str:
    """
    获取增强版天气信息的便捷函数

    Args:
        place_name: 地区名称

    Returns:
        格式化的天气信息字符串
    """
    service = get_enhanced_weather_service()
    weather_data, source = service.get_weather(place_name)

    weather_info = (
        f"{place_name}天气: {weather_data.condition}，"
        f"温度 {weather_data.temperature:.1f}°C "
        f"(体感 {weather_data.apparent_temperature:.1f}°C)，"
        f"湿度 {weather_data.humidity:.0f}%，"
        f"风速 {weather_data.wind_speed:.1f}km/h\n"
        f"数据来源: {source}"
    )

    return weather_info


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试 EnhancedCaiyunWeatherService")
    print("=" * 60)

    service = EnhancedCaiyunWeatherService()

    # 测试服务摘要
    print("📊 服务摘要:")
    summary = service.get_supported_places_summary()
    for category, stats in summary.items():
        print(f"   {category}: {stats}")

    print("\n🌤️ 测试天气查询:")
    test_places = [
        "北京",  # 省级
        "上海",  # 省级
        "天河区",  # 县级
        "西湖区",  # 县级
        "广东省",  # 省级
        "广州市",  # 地级
        "朝阳区",  # 不存在的区
        "beijing",  # 拼音
        "湖",  # 模糊匹配
    ]

    for place in test_places:
        try:
            weather_data, source = service.get_weather(place)
            print(f"   ✅ {place}: {weather_data.condition} {weather_data.temperature:.1f}°C")
            print(f"      来源: {source}")
        except Exception as e:
            print(f"   ❌ {place}: 错误 - {e}")
        print()

    print("🔍 测试地区搜索:")
    search_results = service.search_places("湖", limit=5)
    for result in search_results:
        print(f"   📍 {result['name']} (级别: {result['level']}, "
              f"分数: {result['match_score']:.3f}, 类型: {result['match_type']})")

    print("\n📦 测试批量查询:")
    batch_places = ["北京", "上海", "广州", "深圳"]
    batch_results = service.batch_get_weather(batch_places)
    for result in batch_results:
        if result["success"]:
            print(f"   ✅ {result['place']}: {result['weather'].condition} "
                  f"{result['weather'].temperature:.1f}°C")
        else:
            print(f"   ❌ {result['place']}: {result['source']}")

    # 清理资源
    service.coordinate_db.close()
    print("\n✅ 增强版天气服务测试完成！")