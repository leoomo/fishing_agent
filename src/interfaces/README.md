# 服务接口抽象层

提供统一的服务接口定义，实现松耦合架构设计。

## 📋 接口列表

### 坐标服务接口 (ICoordinateService)
- **文件**: `coordinate_service.py`
- **功能**: 定义坐标服务的标准接口
- **实现**: `EnhancedAmapCoordinateService`

### 天气服务接口 (IWeatherService)
- **文件**: `weather_service.py`
- **功能**: 定义天气服务的标准接口
- **实现**: `EnhancedCaiyunWeatherService`

## 🏗️ 设计原则

### 接口隔离原则
- 每个接口专注于单一职责
- 避免臃肿的接口设计
- 支持接口的独立演进

### 依赖倒置原则
- 高层模块不依赖低层模块，都依赖于抽象
- 具体实现依赖于接口定义
- 便于单元测试和模拟

### 单一职责原则
- 每个接口只负责一类功能
- 接口方法职责明确
- 便于理解和维护

## 📦 接口结构

### 数据模型

```python
@dataclass
class Coordinate:
    """坐标数据模型"""
    longitude: float      # 经度
    latitude: float       # 纬度
    confidence: float     # 置信度 (0-1)
    source: str          # 数据源

@dataclass
class LocationInfo:
    """位置信息数据模型"""
    name: str            # 位置名称
    adcode: str          # 行政区划代码
    province: str        # 省份
    city: str           # 城市
    district: str       # 区县
    coordinate: Coordinate  # 坐标信息
    level: str          # 行政级别

@dataclass
class WeatherCondition:
    """天气条件数据模型"""
    temperature: float     # 温度（摄氏度）
    humidity: float       # 湿度（百分比）
    pressure: float       # 气压（hPa）
    wind_speed: float     # 风速（m/s）
    wind_direction: float # 风向（度）
    weather: str         # 天气描述
    visibility: float    # 能见度（km）
    timestamp: datetime  # 时间戳

@dataclass
class WeatherForecast:
    """天气预报数据模型"""
    date: date
    conditions: List[WeatherCondition]
    daily_high: float
    daily_low: float
    weather_summary: str
```

## 🔧 使用方法

### 依赖注入示例

```python
class MyService:
    def __init__(self, coordinate_service: ICoordinateService):
        self.coordinate_service = coordinate_service

    def get_location_distance(self, place1: str, place2: str) -> float:
        coord1 = self.coordinate_service.get_coordinate(place1)
        coord2 = self.coordinate_service.get_coordinate(place2)

        if coord1 and coord2:
            # 计算距离
            return self._calculate_distance(coord1, coord2)
        return 0.0
```

### 工厂模式

```python
def create_service(service_type: str) -> Union[ICoordinateService, IWeatherService]:
    if service_type == "coordinate":
        from services.service_manager import get_coordinate_service
        return get_coordinate_service()
    elif service_type == "weather":
        from services.service_manager import get_weather_service
        return get_weather_service()
    else:
        raise ValueError(f"Unknown service type: {service_type}")
```

### 测试模拟

```python
class MockCoordinateService(ICoordinateService):
    def get_coordinate(self, location_name: str) -> Optional[Coordinate]:
        # 模拟数据
        if location_name == "北京":
            return Coordinate(116.407387, 39.904179, 1.0, "mock")
        return None

    def is_initialized(self) -> bool:
        return True

    def get_service_status(self) -> Dict[str, Any]:
        return {"service": "mock", "status": "running"}

    def health_check(self) -> bool:
        return True

# 使用模拟服务进行测试
def test_location_service():
    mock_service = MockCoordinateService()
    my_service = MyService(mock_service)

    distance = my_service.get_location_distance("北京", "上海")
    assert distance >= 0
```

## 🎯 接口演进

### 版本兼容性
- 接口方法保持向后兼容
- 新增方法通过可选参数提供默认值
- 废弃方法保留至少一个大版本

### 扩展机制
- 支持接口方法的重载（通过可选参数）
- 支持返回类型的扩展（通过继承）
- 支持配置参数的扩展

## 🧪 接口测试

### 抽象测试基类

```python
import unittest
from abc import ABC, abstractmethod

class CoordinateServiceTest(ABC):
    """坐标服务测试基类"""

    @abstractmethod
    def get_service(self) -> ICoordinateService:
        """获取待测试的服务实例"""
        pass

    def test_get_coordinate(self):
        service = self.get_service()
        coordinate = service.get_coordinate("北京")

        if coordinate:
            self.assertIsInstance(coordinate.longitude, float)
            self.assertIsInstance(coordinate.latitude, float)
            self.assertGreaterEqual(coordinate.confidence, 0)
            self.assertLessEqual(coordinate.confidence, 1)

    def test_is_initialized(self):
        service = self.get_service()
        self.assertIsInstance(service.is_initialized(), bool)

    def test_health_check(self):
        service = self.get_service()
        self.assertIsInstance(service.health_check(), bool)

# 具体实现测试
class EnhancedCoordinateServiceTest(CoordinateServiceTest, unittest.TestCase):
    def get_service(self) -> ICoordinateService:
        from services.service_manager import get_coordinate_service
        return get_coordinate_service()
```

## 📚 最佳实践

### 接口设计
- **命名清晰**: 接口和方法名称要清晰表达意图
- **参数类型**: 使用类型注解提高代码可读性
- **文档完整**: 为每个接口和方法提供详细文档
- **错误处理**: 定义清晰的错误处理策略

### 实现指南
- **完全实现**: 实现接口的所有抽象方法
- **异常处理**: 合理处理异常情况
- **性能考虑**: 注意接口方法的性能影响
- **测试覆盖**: 为接口实现提供完整的测试

### 使用建议
- **依赖接口**: 编码时依赖接口而非具体实现
- **工厂模式**: 使用工厂模式获取接口实例
- **配置驱动**: 通过配置控制接口实现的选择
- **日志记录**: 为接口调用添加适当的日志

---

**版本**: 1.0.0
**更新时间**: 2025年1月
**设计模式**: 接口隔离、依赖倒置、工厂模式