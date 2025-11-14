# 服务模块

提供统一的服务管理、坐标服务、天气服务和日志功能。

## 🏗️ 新架构特性

### 中央服务管理器
- **单例模式**：确保每个服务只有一个实例
- **懒加载**：服务按需初始化，避免资源浪费
- **线程安全**：支持多线程环境下的安全访问
- **健康检查**：内置服务状态监控和健康检查
- **依赖注入**：松耦合的服务依赖管理

### 服务接口抽象
- **ICoordinateService**：坐标服务统一接口
- **IWeatherService**：天气服务统一接口
- **可扩展设计**：便于添加新的服务实现

### 配置管理系统
- **环境变量支持**：支持通过环境变量配置
- **类型安全**：完整的类型注解和验证
- **集中管理**：统一的配置访问接口

## 📦 模块结构

```
services/
├── __init__.py                 # 服务导出接口
├── service_manager.py         # 中央服务管理器
├── coordinate/                 # 坐标服务
│   ├── __init__.py
│   ├── amap_coordinate_service.py      # 原版坐标服务（兼容）
│   └── enhanced_amap_coordinate_service.py # 增强版坐标服务
├── weather/                    # 天气服务
│   ├── __init__.py
│   ├── weather_service.py               # 原版天气服务
│   ├── enhanced_weather_service.py     # 原增强版天气服务
│   └── enhanced_caiyun_weather_service.py # 新增强版天气服务
└── logging/                    # 日志服务
    ├── __init__.py
    ├── business_logger.py              # 兼容版日志器
    └── enhanced_business_logger.py     # 增强版日志器
```

## 🚀 使用方法

### 基本用法

```python
from services.service_manager import get_coordinate_service, get_weather_service

# 获取坐标服务（单例，懒加载）
coordinate_service = get_coordinate_service()
coordinate = coordinate_service.get_coordinate("北京")

# 获取天气服务（单例，懒加载）
weather_service = get_weather_service()
weather = weather_service.get_current_weather("北京")
```

### 服务管理器

```python
from services.service_manager import get_service_manager

# 获取服务管理器
manager = get_service_manager()

# 获取服务状态
status = manager.get_service_status()
print(f"注册的服务: {status['registered_services']}")

# 健康检查
health_status = manager.health_check_all()
print(f"服务健康状态: {health_status}")
```

### 配置管理

```python
from config.service_config import get_service_config, get_config_value

# 获取完整配置
config = get_service_config()

# 获取特定配置值
debug_enabled = get_config_value('logging.debug_logging', False)
timeout = get_config_value('coordinate_service.timeout', 10)
```

### 日志服务

```python
from services.logging.enhanced_business_logger import EnhancedBusinessLogger

# 创建日志器
logger = EnhancedBusinessLogger(__name__)

# 记录服务操作
logger.log_service_initialized("我的服务")
logger.log_operation_success("数据查询", "查询成功")
logger.log_api_request_start("外部API", "获取数据", {"param": "value"})
```

## 🔧 服务接口

### 坐标服务接口 (ICoordinateService)

```python
class ICoordinateService:
    def get_coordinate(self, location_name: str) -> Optional[Coordinate]:
        """获取坐标"""

    def get_location_info(self, location_name: str) -> Optional[LocationInfo]:
        """获取位置信息"""

    def is_initialized(self) -> bool:
        """检查是否已初始化"""

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""

    def health_check(self) -> bool:
        """健康检查"""
```

### 天气服务接口 (IWeatherService)

```python
class IWeatherService:
    def get_current_weather(self, location: str) -> Optional[WeatherCondition]:
        """获取当前天气"""

    def get_weather_forecast(self, location: str, days: int = 3) -> Optional[List[WeatherForecast]]:
        """获取天气预报"""

    def get_weather_by_coordinate(self, coordinate: ICoordinateService) -> Optional[WeatherCondition]:
        """根据坐标获取天气"""

    def is_available(self) -> bool:
        """检查服务是否可用"""

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""

    def health_check(self) -> bool:
        """健康检查"""
```

## ⚙️ 配置选项

### 环境变量

```bash
# 坐标服务配置
COORDINATE_SERVICE_ENABLED=true
COORDINATE_DB_PATH=data/admin_divisions.db
COORDINATE_CACHE_TTL=3600

# 天气服务配置
WEATHER_SERVICE_ENABLED=true
CAIYUN_API_KEY=your_api_key
WEATHER_CACHE_TTL=600

# 日志配置
DEBUG_LOGGING=false
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
```

### 配置类

```python
@dataclass
class ServiceConfig:
    coordinate_service: CoordinateServiceConfig
    weather_service: WeatherServiceConfig
    logging: LoggingConfig
```

## 🧪 测试

运行服务测试：
```bash
# 测试新架构
uv run python test_new_architecture.py

# 测试特定服务
uv run python -c "
from services.service_manager import get_coordinate_service
service = get_coordinate_service()
print(f'坐标服务状态: {service.get_service_status()}')
"
```

## 🔄 向后兼容性

### 保持兼容的功能
- 原有的 `AmapCoordinateService` 仍然可用
- 原有的 `BusinessLogger` 接口保持不变
- 现有工具的使用方式基本不变

### 推荐迁移方式
- 新代码使用 `get_coordinate_service()` 获取服务
- 新代码使用 `EnhancedBusinessLogger` 日志器
- 配置优先使用环境变量和配置管理系统

## 🛠️ 开发指南

### 添加新服务

1. 在 `interfaces/` 中定义服务接口
2. 实现服务类并继承对应接口
3. 在 `services/` 模块中创建工厂函数
4. 在服务管理器中注册服务

```python
# 1. 定义接口
class INewService(ABC):
    @abstractmethod
    def do_something(self) -> str: ...

# 2. 实现服务
class NewService(INewService):
    def do_something(self) -> str:
        return "Hello World"

# 3. 创建工厂函数
def create_new_service() -> INewService:
    return NewService()

# 4. 注册到管理器
manager.register_service('new_service', create_new_service)
```

### 调试技巧

- 设置 `DEBUG_LOGGING=true` 启用详细日志
- 使用 `manager.get_service_status()` 查看服务状态
- 运行测试脚本验证架构完整性

## 📈 性能优化

### 内存优化
- **单例模式**：每个服务只创建一个实例
- **懒加载**：服务只在首次使用时初始化
- **资源清理**：支持服务生命周期管理

### 初始化优化
- **消除重复**：坐标数据库只初始化一次
- **线程安全**：使用锁机制防止并发初始化问题
- **错误处理**：优雅的初始化失败处理

### 🔧 最近修复 (2025-11-04)
- **WeatherTool服务集成修复**: 解决了坐标查询服务调用错误
- **架构验证**: 7/7项测试全部通过
- **工具兼容性**: 确保所有工具正确使用新服务架构

---

**版本**: 2.0.0-refactored-fixed (架构重构修复版)
**更新时间**: 2025年11月
**向后兼容**: 完全兼容
**状态**: 架构稳定，工具集成完善