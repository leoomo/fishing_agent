#!/usr/bin/env python3
"""
天气服务模块的单元测试
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import requests
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.weather.weather_service import CaiyunWeatherService, WeatherData, get_weather_info

class TestWeatherService(unittest.TestCase):
    """天气服务测试类"""

    def setUp(self):
        """测试前的设置"""
        self.service = CaiyunWeatherService()
        self.test_api_key = "test_api_key"

    def test_get_coordinates_success(self):
        """测试成功获取城市坐标"""
        # 测试北京
        coords = self.service.get_coordinates("北京")
        self.assertIsNotNone(coords)
        self.assertEqual(len(coords), 2)
        self.assertIsInstance(coords[0], float)  # 经度
        self.assertIsInstance(coords[1], float)  # 纬度

        # 测试上海
        coords = self.service.get_coordinates("上海")
        self.assertIsNotNone(coords)
        self.assertAlmostEqual(coords[0], 121.4737, places=4)
        self.assertAlmostEqual(coords[1], 31.2304, places=4)

    def test_get_coordinates_failure(self):
        """测试获取不存在城市的坐标"""
        coords = self.service.get_coordinates("不存在的城市")
        self.assertIsNone(coords)

    def test_get_coordinates_case_insensitive(self):
        """测试城市名称大小写和空格处理"""
        coords1 = self.service.get_coordinates("北京")
        coords2 = self.service.get_coordinates(" 北京 ")
        coords3 = self.service.get_coordinates("beijing")

        self.assertEqual(coords1, coords2)
        # beijing 不在中文城市列表中，应该返回 None

    @patch('weather_service.requests.get')
    def test_call_weather_api_success(self, mock_get):
        """测试成功调用天气 API"""
        # 模拟 API 响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "result": {
                "realtime": {
                    "temperature": 25.5,
                    "apparent_temperature": 27.0,
                    "humidity": 65,
                    "pressure": 1013.25,
                    "wind": {
                        "speed": 10.5,
                        "direction": 180
                    },
                    "skycon": "CLEAR_DAY"
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        service = CaiyunWeatherService(api_key=self.test_api_key)
        result = service.call_weather_api(116.4074, 39.9042)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "ok")
        mock_get.assert_called_once()

    @patch('weather_service.requests.get')
    def test_call_weather_api_failure(self, mock_get):
        """测试 API 调用失败"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        service = CaiyunWeatherService(api_key=self.test_api_key)
        result = service.call_weather_api(116.4074, 39.9042)

        self.assertIsNone(result)

    @patch('weather_service.requests.get')
    def test_call_weather_api_invalid_response(self, mock_get):
        """测试 API 返回无效响应"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "error",
            "error": "Invalid API key"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        service = CaiyunWeatherService(api_key=self.test_api_key)
        result = service.call_weather_api(116.4074, 39.9042)

        self.assertIsNone(result)

    def test_parse_weather_data_success(self):
        """测试成功解析天气数据"""
        api_data = {
            "result": {
                "realtime": {
                    "temperature": 25.5,
                    "apparent_temperature": 27.0,
                    "humidity": 65,
                    "pressure": 1013.25,
                    "wind": {
                        "speed": 10.5,
                        "direction": 180
                    },
                    "skycon": "CLEAR_DAY"
                }
            }
        }

        weather_data = self.service.parse_weather_data(api_data)

        self.assertIsNotNone(weather_data)
        self.assertIsInstance(weather_data, WeatherData)
        self.assertEqual(weather_data.temperature, 25.5)
        self.assertEqual(weather_data.apparent_temperature, 27.0)
        self.assertEqual(weather_data.humidity, 65)
        self.assertEqual(weather_data.pressure, 1013.25)
        self.assertEqual(weather_data.wind_speed, 10.5)
        self.assertEqual(weather_data.wind_direction, 180)
        self.assertEqual(weather_data.condition, "晴天")

    def test_parse_weather_data_invalid(self):
        """测试解析无效天气数据"""
        invalid_data = {"invalid": "data"}
        weather_data = self.service.parse_weather_data(invalid_data)
        self.assertIsNone(weather_data)

    def test_get_fallback_weather(self):
        """测试获取模拟天气数据"""
        weather_data = self.service.get_fallback_weather("北京")

        self.assertIsNotNone(weather_data)
        self.assertIsInstance(weather_data, WeatherData)
        self.assertIsInstance(weather_data.temperature, (int, float))
        self.assertIsInstance(weather_data.condition, str)
        self.assertIsInstance(weather_data.humidity, (int, float))

    @patch.object(CaiyunWeatherService, 'call_weather_api')
    def test_get_weather_with_api_success(self, mock_call_api):
        """测试通过 API 获取天气数据成功"""
        # 模拟 API 返回数据
        mock_call_api.return_value = {
            "status": "ok",
            "result": {
                "realtime": {
                    "temperature": 22.0,
                    "apparent_temperature": 24.0,
                    "humidity": 55,
                    "pressure": 1015.0,
                    "wind": {
                        "speed": 5.0,
                        "direction": 90
                    },
                    "skycon": "PARTLY_CLOUDY_DAY"
                }
            }
        }

        service = CaiyunWeatherService(api_key=self.test_api_key)
        weather_data, source = service.get_weather("北京")

        self.assertIsNotNone(weather_data)
        self.assertEqual(weather_data.temperature, 22.0)
        self.assertEqual(weather_data.condition, "多云")
        self.assertIn("API", source)

    @patch.object(CaiyunWeatherService, 'call_weather_api')
    def test_get_weather_api_failure_fallback(self, mock_call_api):
        """测试 API 失败时回退到模拟数据"""
        mock_call_api.return_value = None

        service = CaiyunWeatherService(api_key=self.test_api_key)
        weather_data, source = service.get_weather("北京")

        self.assertIsNotNone(weather_data)
        self.assertIn("模拟数据", source)

    def test_get_weather_no_api_key(self):
        """测试没有 API 密钥时使用模拟数据"""
        service = CaiyunWeatherService(api_key=None)
        weather_data, source = service.get_weather("北京")

        self.assertIsNotNone(weather_data)
        self.assertIn("模拟数据", source)

    def test_get_weather_unknown_city(self):
        """测试获取未知城市天气"""
        service = CaiyunWeatherService(api_key=self.test_api_key)
        weather_data, source = service.get_weather("不存在的城市")

        self.assertIsNotNone(weather_data)
        # 应该使用模拟数据
        self.assertIn("模拟数据", source)

class TestWeatherIntegration(unittest.TestCase):
    """集成测试"""

    def test_get_weather_info_function(self):
        """测试便捷函数 get_weather_info"""
        result = get_weather_info("北京")

        self.assertIsInstance(result, str)
        self.assertIn("北京天气:", result)
        self.assertIn("温度", result)
        self.assertIn("数据来源:", result)

    @patch.dict(os.environ, {'CAIYUN_API_KEY': 'test_key'})
    def test_environment_variable_api_key(self):
        """测试从环境变量读取 API 密钥"""
        service = CaiyunWeatherService()
        self.assertEqual(service.api_key, 'test_key')

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)