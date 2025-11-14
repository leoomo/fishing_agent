# 基础设施开发指南

## 📋 概述

本文档详细描述智能钓鱼生态系统的共享基础设施层设计，为四大业务模块提供统一的技术支撑。基础设施层包括数据库管理、缓存系统、配置管理、服务管理和接口抽象等核心组件。

## 🏗️ 基础设施架构

### 目录结构
```
shared/
├── __init__.py
├── infrastructure/
│   ├── __init__.py
│   ├── database.py          # 统一数据库管理
│   ├── cache.py             # 智能缓存系统
│   ├── config.py            # 配置管理
│   └── service_manager.py   # 依赖注入容器
├── interfaces/
│   ├── __init__.py
│   ├── repositories.py      # 数据访问接口
│   ├── services.py          # 业务服务接口
│   └── tools.py             # LangChain工具接口
└── utils/
    ├── __init__.py
    ├── logging.py           # 统一日志系统
    └── validators.py        # 数据验证工具
```

## 🔧 核心组件设计

### 1. 统一数据库管理

#### 数据库配置
```python
# shared/infrastructure/database.py
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from typing import Dict, Any
import os

class DatabaseConfig:
    """数据库配置管理"""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./data/fishing_ecosystem.db')
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.echo = os.getenv('DB_ECHO', 'false').lower() == 'true'

class DatabaseManager:
    """统一数据库管理器"""

    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        self.Base = declarative_base()

    def initialize(self):
        """初始化数据库连接"""
        self.engine = create_engine(
            self.config.database_url,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            echo=self.config.echo
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # 创建所有表
        self.Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()

# 全局数据库实例
db_manager = DatabaseManager()
```

#### 数据库基类
```python
# shared/infrastructure/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from .database import db_manager

class BaseModel(db_manager.Base):
    """数据库模型基类"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
```

### 2. 智能缓存系统

#### 缓存配置和接口
```python
# shared/infrastructure/cache.py
import redis
import json
import pickle
from typing import Any, Optional, Union
from abc import ABC, abstractmethod
import os

class CacheConfig:
    """缓存配置"""

    def __init__(self):
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.default_ttl = int(os.getenv('CACHE_DEFAULT_TTL', 3600))
        self.key_prefix = os.getenv('CACHE_KEY_PREFIX', 'fishing:')

class CacheInterface(ABC):
    """缓存接口"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass

class RedisCache(CacheInterface):
    """Redis缓存实现"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.client = redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            decode_responses=False
        )

    def _make_key(self, key: str) -> str:
        """生成完整的缓存键"""
        return f"{self.config.key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            full_key = self._make_key(key)
            value = self.client.get(full_key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"缓存获取失败: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            full_key = self._make_key(key)
            serialized_value = pickle.dumps(value)
            ttl = ttl or self.config.default_ttl
            return self.client.setex(full_key, ttl, serialized_value)
        except Exception as e:
            print(f"缓存设置失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            full_key = self._make_key(key)
            return bool(self.client.delete(full_key))
        except Exception as e:
            print(f"缓存删除失败: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            full_key = self._make_key(key)
            return bool(self.client.exists(full_key))
        except Exception as e:
            print(f"缓存检查失败: {e}")
            return False

class MemoryCache(CacheInterface):
    """内存缓存实现（用于开发环境）"""

    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            if key in self._ttl:
                import time
                if time.time() > self._ttl[key]:
                    self.delete(key)
                    return None
            return self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        self._cache[key] = value
        if ttl:
            import time
            self._ttl[key] = time.time() + ttl
        return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self._cache

# 缓存工厂
class CacheFactory:
    """缓存工厂"""

    @staticmethod
    def create_cache(use_redis: bool = True) -> CacheInterface:
        """创建缓存实例"""
        if use_redis:
            return RedisCache()
        else:
            return MemoryCache()

# 全局缓存实例
cache = CacheFactory.create_cache(use_redis=True)
```

### 3. 配置管理系统

#### 配置加载和管理
```python
# shared/infrastructure/config.py
import os
import json
import yaml
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class AppConfig:
    """应用配置"""

    # 数据库配置
    database_url: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///./data/fishing_ecosystem.db'))

    # 缓存配置
    redis_host: str = field(default_factory=lambda: os.getenv('REDIS_HOST', 'localhost'))
    redis_port: int = field(default_factory=lambda: int(os.getenv('REDIS_PORT', 6379)))

    # API配置
    api_host: str = field(default_factory=lambda: os.getenv('API_HOST', '0.0.0.0'))
    api_port: int = field(default_factory=lambda: int(os.getenv('API_PORT', 8000)))

    # 日志配置
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_file: str = field(default_factory=lambda: os.getenv('LOG_FILE', './logs/app.log'))

    # 功能开关
    enable_caching: bool = field(default_factory=lambda: os.getenv('ENABLE_CACHING', 'true').lower() == 'true')
    enable_logging: bool = field(default_factory=lambda: os.getenv('ENABLE_LOGGING', 'true').lower() == 'true')
    enable_monitoring: bool = field(default_factory=lambda: os.getenv('ENABLE_MONITORING', 'false').lower() == 'true')

    # 业务配置
    default_cache_ttl: int = field(default_factory=lambda: int(os.getenv('DEFAULT_CACHE_TTL', 3600)))
    max_concurrent_requests: int = field(default_factory=lambda: int(os.getenv('MAX_CONCURRENT_REQUESTS', 100)))

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or './config/app_config.yaml'
        self._config = AppConfig()
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    self._update_config_from_dict(config_data)
            except Exception as e:
                print(f"配置文件加载失败: {e}，使用默认配置")

        # 从环境变量更新配置
        self._update_config_from_env()

    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """从字典更新配置"""
        for key, value in config_data.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def _update_config_from_env(self):
        """从环境变量更新配置"""
        # 这里可以根据需要添加更多的环境变量映射
        env_mappings = {
            'DATABASE_URL': 'database_url',
            'REDIS_HOST': 'redis_host',
            'LOG_LEVEL': 'log_level',
        }

        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                setattr(self._config, config_key, env_value)

    def get_config(self) -> AppConfig:
        """获取配置对象"""
        return self._config

    def reload(self):
        """重新加载配置"""
        self._load_config()

# 全局配置实例
config_manager = ConfigManager()
config = config_manager.get_config()
```

### 4. 服务管理和依赖注入

#### 服务容器
```python
# shared/infrastructure/service_manager.py
from typing import Dict, Type, Any, Optional, Callable
from abc import ABC, abstractmethod
import inspect

class ServiceContainer:
    """服务容器"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._instances: Dict[str, Any] = {}

    def register_service(self, name: str, service_class: Type, singleton: bool = False):
        """注册服务类"""
        self._services[name] = (service_class, singleton)

    def register_factory(self, name: str, factory: Callable):
        """注册工厂函数"""
        self._factories[name] = factory

    def register_instance(self, name: str, instance: Any):
        """注册服务实例"""
        self._instances[name] = instance

    def get(self, name: str) -> Any:
        """获取服务实例"""
        # 如果已有实例，直接返回
        if name in self._instances:
            return self._instances[name]

        # 检查工厂函数
        if name in self._factories:
            instance = self._factories[name]()
            self._instances[name] = instance
            return instance

        # 检查服务类
        if name in self._services:
            service_class, is_singleton = self._services[name]

            if is_singleton:
                if name not in self._singletons:
                    self._singletons[name] = self._create_instance(service_class)
                return self._singletons[name]
            else:
                return self._create_instance(service_class)

        raise ValueError(f"服务 '{name}' 未注册")

    def _create_instance(self, service_class: Type) -> Any:
        """创建服务实例（支持依赖注入）"""
        # 获取构造函数参数
        sig = inspect.signature(service_class.__init__)
        parameters = sig.parameters

        # 准备构造参数
        kwargs = {}
        for param_name, param in parameters.items():
            if param_name == 'self':
                continue

            # 尝试从容器获取依赖
            try:
                kwargs[param_name] = self.get(param_name)
            except ValueError:
                # 如果依赖不存在，使用默认值
                if param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default

        return service_class(**kwargs)

class ServiceManager:
    """服务管理器"""

    def __init__(self):
        self.container = ServiceContainer()
        self._register_core_services()

    def _register_core_services(self):
        """注册核心服务"""
        # 注册配置服务
        self.container.register_instance('config', config)

        # 注册数据库服务
        self.container.register_factory('db_manager', lambda: db_manager)

        # 注册缓存服务
        self.container.register_factory('cache', lambda: cache)

        # 注册日志服务
        self.container.register_factory('logger', lambda: self._create_logger())

    def _create_logger(self):
        """创建日志服务"""
        import logging
        from .utils.logging import setup_logger
        return setup_logger(config.log_level, config.log_file)

    def register_service(self, name: str, service_class: Type, singleton: bool = False):
        """注册服务"""
        self.container.register_service(name, service_class, singleton)

    def register_factory(self, name: str, factory: Callable):
        """注册工厂函数"""
        self.container.register_factory(name, factory)

    def register_instance(self, name: str, instance: Any):
        """注册服务实例"""
        self.container.register_instance(name, instance)

    def get(self, name: str) -> Any:
        """获取服务"""
        return self.container.get(name)

    def create_instance(self, service_class: Type) -> Any:
        """创建服务实例"""
        return self.container._create_instance(service_class)

# 全局服务管理器
service_manager = ServiceManager()
```

### 5. 接口抽象层

#### 数据访问接口
```python
# shared/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

class IRepository(ABC):
    """通用仓储接口"""

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        """根据ID获取实体"""
        pass

    @abstractmethod
    def get_all(self) -> List[Any]:
        """获取所有实体"""
        pass

    @abstractmethod
    def create(self, entity: Any) -> Any:
        """创建实体"""
        pass

    @abstractmethod
    def update(self, id: int, entity: Any) -> Optional[Any]:
        """更新实体"""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """删除实体"""
        pass

class IFishRepository(IRepository):
    """鱼类数据仓储接口"""

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Any]:
        """根据名称获取鱼种信息"""
        pass

    @abstractmethod
    def search_by_family(self, family: str) -> List[Any]:
        """根据科属搜索鱼种"""
        pass

    @abstractmethod
    def get_by_habitat(self, habitat_type: str) -> List[Any]:
        """根据栖息地类型获取鱼种"""
        pass

class IEquipmentRepository(IRepository):
    """装备数据仓储接口"""

    @abstractmethod
    def get_by_category(self, category: str) -> List[Any]:
        """根据类别获取装备"""
        pass

    @abstractmethod
    def search_by_price_range(self, min_price: float, max_price: float) -> List[Any]:
        """根据价格范围搜索装备"""
        pass

    @abstractmethod
    def get_recommendations(self, fish_species: str, budget: float) -> List[Any]:
        """获取推荐装备"""
        pass

class IUserRepository(IRepository):
    """用户数据仓储接口"""

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[Any]:
        """根据用户名获取用户信息"""
        pass

    @abstractmethod
    def update_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """更新用户偏好"""
        pass
```

#### 业务服务接口
```python
# shared/interfaces/services.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IService(ABC):
    """通用服务接口"""

    @abstractmethod
    def initialize(self) -> bool:
        """初始化服务"""
        pass

class IFishKnowledgeService(IService):
    """鱼类知识服务接口"""

    @abstractmethod
    def get_fish_species_info(self, fish_name: str) -> Optional[Dict[str, Any]]:
        """获取鱼种详细信息"""
        pass

    @abstractmethod
    def get_seasonal_strategy(self, season: str, location: str) -> Optional[Dict[str, Any]]:
        """获取季节性策略"""
        pass

    @abstractmethod
    def analyze_weather_impact(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析天气影响"""
        pass

class IEquipmentRecommendationService(IService):
    """装备推荐服务接口"""

    @abstractmethod
    def recommend_equipment_set(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """推荐装备套装"""
        pass

    @abstractmethod
    def analyze_equipment_combo(self, equipment_list: List[str]) -> Dict[str, Any]:
        """分析装备搭配"""
        pass

    @abstractmethod
    def optimize_budget_allocation(self, budget: float, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """优化预算分配"""
        pass

class IEquipmentComparisonService(IService):
    """装备对比服务接口"""

    @abstractmethod
    def compare_equipment(self, equipment1: str, equipment2: str) -> Dict[str, Any]:
        """对比两款装备"""
        pass

    @abstractmethod
    def get_performance_scores(self, equipment_list: List[str]) -> Dict[str, Any]:
        """获取性能评分"""
        pass

    @abstractmethod
    def analyze_upgrade_value(self, current_equipment: str, target_equipment: str) -> Dict[str, Any]:
        """分析升级价值"""
        pass
```

#### LangChain工具接口
```python
# shared/interfaces/tools.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain.tools import BaseTool

class IFishingTool(ABC):
    """钓鱼工具接口"""

    @abstractmethod
    def get_description(self) -> str:
        """获取工具描述"""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取工具参数"""
        pass

class IFishSpeciesTool(IFishingTool):
    """鱼种工具接口"""

    @abstractmethod
    def analyze_fish_species(self, fish_name: str) -> str:
        """分析鱼种信息"""
        pass

class IEquipmentTool(IFishingTool):
    """装备工具接口"""

    @abstractmethod
    def recommend_equipment(self, requirements: Dict[str, Any]) -> str:
        """推荐装备"""
        pass

class IComparisonTool(IFishingTool):
    """对比工具接口"""

    @abstractmethod
    def compare_items(self, items: List[str]) -> str:
        """对比项目"""
        pass

# 工具基类
class BaseFishingTool(BaseTool, IFishingTool):
    """钓鱼工具基类"""

    def __init__(self):
        super().__init__()

    def get_description(self) -> str:
        return self.description

    def get_parameters(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'args_schema': self.args_schema
        }
```

## 🛠️ 工具函数

### 数据验证工具
```python
# shared/utils/validators.py
from typing import Any, List, Dict
from pydantic import BaseModel, ValidationError
import re

class ValidationException(Exception):
    """验证异常"""
    pass

class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_fish_name(fish_name: str) -> bool:
        """验证鱼种名称"""
        if not fish_name or len(fish_name.strip()) == 0:
            return False

        # 检查是否包含中文字符
        if not re.search(r'[\u4e00-\u9fff]', fish_name):
            return False

        # 检查长度限制
        if len(fish_name) > 20:
            return False

        return True

    @staticmethod
    def validate_price(price: Any) -> bool:
        """验证价格"""
        try:
            price_value = float(price)
            return price_value > 0 and price_value <= 1000000  # 合理的价格范围
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_coordinates(lat: Any, lng: Any) -> bool:
        """验证坐标"""
        try:
            lat_value = float(lat)
            lng_value = float(lng)
            return (-90 <= lat_value <= 90) and (-180 <= lng_value <= 180)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_season(season: str) -> bool:
        """验证季节"""
        valid_seasons = ['春', '夏', '秋', '冬', '春季', '夏季', '秋季', '冬季']
        return season in valid_seasons

class ModelValidator:
    """模型验证器"""

    @staticmethod
    def validate_model(model: BaseModel, data: Dict[str, Any]) -> BaseModel:
        """验证Pydantic模型"""
        try:
            return model(**data)
        except ValidationError as e:
            raise ValidationException(f"数据验证失败: {e}")

    @staticmethod
    def validate_list_of_models(model: BaseModel, data_list: List[Dict[str, Any]]) -> List[BaseModel]:
        """验证模型列表"""
        validated_models = []
        for data in data_list:
            try:
                validated_models.append(model(**data))
            except ValidationError as e:
                raise ValidationException(f"数据验证失败: {e}")
        return validated_models
```

### 日志系统
```python
# shared/utils/logging.py
import logging
import os
from datetime import datetime
from typing import Optional
from .validators import ValidationException

class FishingLogger:
    """钓鱼系统专用日志器"""

    def __init__(self, name: str = 'fishing_ecosystem'):
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        if not self.logger.handlers:
            # 创建格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # 文件处理器
            if os.path.exists('./logs'):
                file_handler = logging.FileHandler('./logs/app.log')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

    def info(self, message: str, extra: Optional[Dict] = None):
        """记录信息日志"""
        self.logger.info(message, extra=extra or {})

    def warning(self, message: str, extra: Optional[Dict] = None):
        """记录警告日志"""
        self.logger.warning(message, extra=extra or {})

    def error(self, message: str, extra: Optional[Dict] = None):
        """记录错误日志"""
        self.logger.error(message, extra=extra or {})

    def debug(self, message: str, extra: Optional[Dict] = None):
        """记录调试日志"""
        self.logger.debug(message, extra=extra or {})

def setup_logger(level: str = 'INFO', log_file: str = './logs/app.log') -> FishingLogger:
    """设置日志系统"""
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 设置日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logger = FishingLogger()
    logger.logger.setLevel(numeric_level)

    return logger

# 全局日志器
logger = setup_logger()
```

## 🚀 使用指南

### 初始化基础设施
```python
# 在应用启动时初始化基础设施
from shared.infrastructure.database import db_manager
from shared.infrastructure.config import config_manager
from shared.infrastructure.service_manager import service_manager

def initialize_infrastructure():
    """初始化基础设施"""
    # 1. 加载配置
    config_manager.reload()

    # 2. 初始化数据库
    db_manager.initialize()

    # 3. 初始化服务管理器
    # 服务管理器在创建时已经自动初始化了核心服务

    print("基础设施初始化完成")

# 使用依赖注入创建服务
class FishKnowledgeService:
    def __init__(self, db_manager, cache, logger):
        self.db_manager = db_manager
        self.cache = cache
        self.logger = logger

    def get_fish_info(self, fish_name: str):
        # 使用依赖的服务
        self.logger.info(f"查询鱼种信息: {fish_name}")

        # 尝试从缓存获取
        cache_key = f"fish_info:{fish_name}"
        cached_info = self.cache.get(cache_key)
        if cached_info:
            return cached_info

        # 从数据库查询
        # ... 数据库查询逻辑

        # 缓存结果
        # self.cache.set(cache_key, result, ttl=3600)

        return result

# 注册服务
service_manager.register_service(
    'fish_knowledge_service',
    FishKnowledgeService,
    singleton=True
)
```

### 业务模块开发
```python
# 在业务模块中使用基础设施
from shared.interfaces.repositories import IFishRepository
from shared.interfaces.services import IFishKnowledgeService
from shared.infrastructure.service_manager import service_manager

class FishSpeciesAnalyzer:
    def __init__(self,
                 fish_repository: IFishRepository,
                 knowledge_service: IFishKnowledgeService):
        self.fish_repository = fish_repository
        self.knowledge_service = knowledge_service

    def analyze_species(self, fish_name: str):
        # 使用注入的依赖
        fish_data = self.fish_repository.get_by_name(fish_name)
        if not fish_data:
            return None

        return self.knowledge_service.analyze_fish_species(fish_name)

# 自动依赖注入
analyzer = service_manager.create_instance(FishSpeciesAnalyzer)
```

## 📋 开发清单

### 必须实现的项目
- [ ] **数据库层**: 实现具体的Repository类
- [ ] **缓存层**: 根据需求选择合适的缓存策略
- [ ] **配置层**: 完善配置文件和环境变量
- [ ] **服务层**: 实现具体的业务服务类
- [ ] **日志层**: 完善日志记录规范

### 可选的增强功能
- [ ] **监控集成**: 添加性能监控和健康检查
- [ ] **连接池**: 优化数据库连接池配置
- [ ] **缓存策略**: 实现多级缓存和缓存预热
- [ ] **配置热重载**: 支持运行时配置更新
- [ ] **数据迁移**: 实现数据库版本控制和迁移工具

---

*本文档为智能钓鱼生态系统提供了完整的基础设施设计，确保各业务模块能够高效、稳定地运行。*