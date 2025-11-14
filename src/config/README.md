# 配置管理模块

提供统一的服务配置管理，支持环境变量配置和类型安全的配置访问。

## 📋 配置模块

### 核心配置类
- **文件**: `service_config.py`
- **功能**: 集中管理所有服务的配置参数
- **特性**: 环境变量支持、类型注解、默认值、验证机制

## 🏗️ 配置架构

### 配置层次结构

```
ServiceConfig
├── coordinate_service (CoordinateServiceConfig)
│   ├── enabled: bool
│   ├── auto_init: bool
│   ├── health_check_interval: int
│   ├── max_retries: int
│   ├── timeout: int
│   └── database (DatabaseConfig)
│       ├── path: str
│       ├── cache_enabled: bool
│       └── cache_ttl: int
├── weather_service (WeatherServiceConfig)
│   ├── enabled: bool
│   ├── api_key: Optional[str]
│   ├── timeout: int
│   ├── max_retries: int
│   ├── cache_enabled: bool
│   └── cache_ttl: int
└── logging (LoggingConfig)
    ├── level: str
    ├── debug_logging: bool
    ├── log_to_file: bool
    ├── log_file_path: str
    ├── max_log_size: int
    └── backup_count: int
```

## 🔧 环境变量配置

### 坐标服务配置

```bash
# 启用坐标服务
COORDINATE_SERVICE_ENABLED=true

# 自动初始化
COORDINATE_SERVICE_AUTO_INIT=true

# 健康检查间隔（秒）
COORDINATE_HEALTH_CHECK_INTERVAL=300

# 最大重试次数
COORDINATE_MAX_RETRIES=3

# 超时时间（秒）
COORDINATE_TIMEOUT=10

# 数据库路径
COORDINATE_DB_PATH=data/admin_divisions.db

# 缓存开关
COORDINATE_CACHE_ENABLED=true

# 缓存过期时间（秒）
COORDINATE_CACHE_TTL=3600
```

### 天气服务配置

```bash
# 启用天气服务
WEATHER_SERVICE_ENABLED=true

# API密钥
CAIYUN_API_KEY=your_api_key_here

# 超时时间（秒）
WEATHER_TIMEOUT=30

# 最大重试次数
WEATHER_MAX_RETRIES=3

# 缓存开关
WEATHER_CACHE_ENABLED=true

# 缓存过期时间（秒）
WEATHER_CACHE_TTL=600
```

### 日志配置

```bash
# 调试日志开关
DEBUG_LOGGING=false

# 日志级别
LOG_LEVEL=INFO

# 文件日志开关
LOG_TO_FILE=true

# 日志文件路径
LOG_FILE_PATH=logs/app.log

# 最大日志文件大小（字节）
LOG_MAX_SIZE=10485760

# 日志文件备份数量
LOG_BACKUP_COUNT=5
```

## 🚀 使用方法

### 基本用法

```python
from config.service_config import get_service_config, get_config_value

# 获取完整配置对象
config = get_service_config()

# 访问配置值
coordinate_enabled = config.coordinate_service.enabled
weather_timeout = config.weather_service.timeout
log_level = config.logging.level

print(f"坐标服务启用: {coordinate_enabled}")
print(f"天气服务超时: {weather_timeout}s")
print(f"日志级别: {log_level}")
```

### 配置值访问

```python
# 使用便捷函数获取配置值
debug_enabled = get_config_value('logging.debug_logging', False)
db_path = get_config_value('coordinate_service.database.path', 'data/default.db')
api_timeout = get_config_value('weather_service.timeout', 30)

# 点分隔的配置路径
value = get_config_value('coordinate_service.max_retries', 3)
```

### 配置转换

```python
# 转换为字典
config_dict = config.to_dict()
print(f"配置字典: {config_dict}")

# JSON序列化
import json
config_json = json.dumps(config_dict, indent=2, ensure_ascii=False)
print(config_json)
```

### 目录管理

```python
# 确保配置的目录存在
config = get_service_config()
config.ensure_directories()

# 这会自动创建：
# - 数据库目录（如果不存在）
# - 日志目录（如果启用文件日志）
```

## 🏭 配置工厂

### 配置创建

```python
from config.service_config import ServiceConfig

# 从环境变量创建（推荐）
config = ServiceConfig.from_env()

# 手动创建
config = ServiceConfig(
    coordinate_service=CoordinateServiceConfig(
        enabled=True,
        database=DatabaseConfig(path="data/my_db.db")
    )
)
```

### 配置验证

```python
def validate_config(config: ServiceConfig) -> bool:
    """验证配置的有效性"""
    errors = []

    # 检查必需的API密钥
    if config.weather_service.enabled and not config.weather_service.api_key:
        errors.append("天气服务启用但缺少API密钥")

    # 检查路径有效性
    db_path = Path(config.coordinate_service.database.path)
    if not db_path.parent.exists():
        errors.append(f"数据库目录不存在: {db_path.parent}")

    # 检查日志级别
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.logging.level not in valid_levels:
        errors.append(f"无效的日志级别: {config.logging.level}")

    if errors:
        for error in errors:
            print(f"配置错误: {error}")
        return False

    return True

# 使用验证
config = get_service_config()
if validate_config(config):
    print("配置验证通过")
else:
    print("配置验证失败")
```

## 🔍 配置调试

### 配置检查工具

```python
def print_config_status():
    """打印配置状态"""
    config = get_service_config()

    print("=== 服务配置状态 ===")
    print(f"坐标服务: {'启用' if config.coordinate_service.enabled else '禁用'}")
    print(f"天气服务: {'启用' if config.weather_service.enabled else '禁用'}")
    print(f"调试日志: {'启用' if config.logging.debug_logging else '禁用'}")

    print("\n=== 详细配置 ===")
    print(f"数据库路径: {config.coordinate_service.database.path}")
    print(f"缓存TTL: 坐标={config.coordinate_service.database.cache_ttl}s, 天气={config.weather_service.cache_ttl}s")
    print(f"超时设置: 坐标={config.coordinate_service.timeout}s, 天气={config.weather_service.timeout}s")

    if config.weather_service.api_key:
        print("API密钥: 已配置")
    else:
        print("API密钥: 未配置")

# 运行配置检查
print_config_status()
```

### 环境变量检查

```python
import os

def check_env_variables():
    """检查环境变量配置"""
    env_vars = {
        'DEBUG_LOGGING': os.getenv('DEBUG_LOGGING'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL'),
        'COORDINATE_SERVICE_ENABLED': os.getenv('COORDINATE_SERVICE_ENABLED'),
        'WEATHER_SERVICE_ENABLED': os.getenv('WEATHER_SERVICE_ENABLED'),
        'CAIYUN_API_KEY': os.getenv('CAIYUN_API_KEY'),
        'COORDINATE_DB_PATH': os.getenv('COORDINATE_DB_PATH'),
    }

    print("=== 环境变量配置 ===")
    for key, value in env_vars.items():
        if value:
            if 'API_KEY' in key:
                print(f"{key}: ***已配置***")
            else:
                print(f"{key}: {value}")
        else:
            print(f"{key}: (未设置)")

check_env_variables()
```

## 📝 配置模板

### .env.example 文件

```bash
# 应用配置
DEBUG_LOGGING=false
LOG_LEVEL=INFO

# 坐标服务配置
COORDINATE_SERVICE_ENABLED=true
COORDINATE_SERVICE_AUTO_INIT=true
COORDINATE_HEALTH_CHECK_INTERVAL=300
COORDINATE_MAX_RETRIES=3
COORDINATE_TIMEOUT=10
COORDINATE_DB_PATH=data/admin_divisions.db
COORDINATE_CACHE_ENABLED=true
COORDINATE_CACHE_TTL=3600

# 天气服务配置
WEATHER_SERVICE_ENABLED=true
CAIYUN_API_KEY=your_caiyun_api_key_here
WEATHER_TIMEOUT=30
WEATHER_MAX_RETRIES=3
WEATHER_CACHE_ENABLED=true
WEATHER_CACHE_TTL=600

# 日志配置
LOG_TO_FILE=true
LOG_FILE_PATH=logs/app.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# API配置（可选）
AMAP_API_KEY=your_amap_api_key_here
```

## 🔒 安全考虑

### 敏感信息处理

```python
# API密钥安全存储
def get_secure_config():
    """获取安全的配置（隐藏敏感信息）"""
    config = get_service_config()

    # 创建安全的配置副本
    safe_config = {
        'coordinate_service': {
            'enabled': config.coordinate_service.enabled,
            'timeout': config.coordinate_service.timeout,
            'database': {
                'path': config.coordinate_service.database.path,
                'cache_enabled': config.coordinate_service.database.cache_enabled,
            }
        },
        'weather_service': {
            'enabled': config.weather_service.enabled,
            'timeout': config.weather_service.timeout,
            'api_key_configured': bool(config.weather_service.api_key),
            # 不直接输出API密钥
        },
        'logging': config.logging.to_dict()
    }

    return safe_config

# 使用安全配置
safe_config = get_secure_config()
print(json.dumps(safe_config, indent=2, ensure_ascii=False))
```

## 🧪 配置测试

### 配置验证测试

```python
import unittest
from config.service_config import ServiceConfig, get_service_config

class TestServiceConfig(unittest.TestCase):

    def test_default_config(self):
        """测试默认配置"""
        config = ServiceConfig()

        self.assertTrue(config.coordinate_service.enabled)
        self.assertTrue(config.weather_service.enabled)
        self.assertEqual(config.logging.level, "INFO")
        self.assertFalse(config.logging.debug_logging)

    def test_config_from_env(self):
        """测试从环境变量创建配置"""
        import os
        os.environ['DEBUG_LOGGING'] = 'true'
        os.environ['LOG_LEVEL'] = 'DEBUG'

        try:
            config = ServiceConfig.from_env()
            self.assertTrue(config.logging.debug_logging)
            self.assertEqual(config.logging.level, "DEBUG")
        finally:
            # 清理环境变量
            os.environ.pop('DEBUG_LOGGING', None)
            os.environ.pop('LOG_LEVEL', None)

    def test_config_dict_conversion(self):
        """测试配置字典转换"""
        config = get_service_config()
        config_dict = config.to_dict()

        self.assertIn('coordinate_service', config_dict)
        self.assertIn('weather_service', config_dict)
        self.assertIn('logging', config_dict)

        # 检查嵌套结构
        coord_config = config_dict['coordinate_service']
        self.assertIn('database', coord_config)

if __name__ == '__main__':
    unittest.main()
```

---

**版本**: 1.0.0
**更新时间**: 2025年1月
**支持**: 环境变量、类型注解、配置验证