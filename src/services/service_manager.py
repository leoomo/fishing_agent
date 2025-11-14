"""
中央服务管理器

提供统一的服务实例管理，实现单例模式和依赖注入。
确保核心服务只初始化一次，避免资源浪费。
"""

import threading
from typing import Dict, Any, Optional, TypeVar, Type, Callable
from functools import wraps
import time

try:
    from ..interfaces.coordinate_service import ICoordinateService
    from ..interfaces.weather_service import IWeatherService
    from ..config.service_config import get_service_config
except ImportError:
    # 处理相对导入失败的情况
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from interfaces.coordinate_service import ICoordinateService
    from interfaces.weather_service import IWeatherService
    from config.service_config import get_service_config


T = TypeVar('T')


class ServiceManager:
    """中央服务管理器 - 单例模式"""

    _instance: Optional['ServiceManager'] = None
    _lock = threading.Lock()
    _services: Dict[str, Any] = {}
    _service_factories: Dict[str, Callable] = {}
    _initialization_locks: Dict[str, threading.Lock] = {}

    def __new__(cls) -> 'ServiceManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config = get_service_config()
            self._initialized = True

    def register_service(self, service_name: str, factory: Callable[[], T]) -> None:
        """
        注册服务工厂函数

        Args:
            service_name: 服务名称
            factory: 服务工厂函数
        """
        self._service_factories[service_name] = factory
        if service_name not in self._initialization_locks:
            self._initialization_locks[service_name] = threading.Lock()

    def get_service(self, service_name: str) -> Optional[T]:
        """
        获取服务实例（懒加载）

        Args:
            service_name: 服务名称

        Returns:
            服务实例，如果未注册返回 None
        """
        if service_name in self._services:
            return self._services[service_name]

        if service_name not in self._service_factories:
            raise ValueError(f"Service '{service_name}' not registered")

        # 使用双重检查锁定模式确保线程安全
        if service_name not in self._services:
            with self._initialization_locks[service_name]:
                if service_name not in self._services:
                    try:
                        start_time = time.time()
                        service = self._service_factories[service_name]()
                        self._services[service_name] = service
                        init_time = time.time() - start_time
                        print(f"Service '{service_name}' initialized successfully in {init_time:.3f}s")
                    except Exception as e:
                        print(f"Failed to initialize service '{service_name}': {e}")
                        raise

        return self._services[service_name]

    def is_service_registered(self, service_name: str) -> bool:
        """
        检查服务是否已注册

        Args:
            service_name: 服务名称

        Returns:
            True 如果已注册，False 否则
        """
        return service_name in self._service_factories

    def is_service_initialized(self, service_name: str) -> bool:
        """
        检查服务是否已初始化

        Args:
            service_name: 服务名称

        Returns:
            True 如果已初始化，False 否则
        """
        return service_name in self._services

    def get_coordinate_service(self) -> ICoordinateService:
        """获取坐标服务实例"""
        return self.get_service('coordinate')

    def get_weather_service(self) -> IWeatherService:
        """获取天气服务实例"""
        return self.get_service('weather')

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取所有服务的状态

        Returns:
            服务状态字典
        """
        status = {
            'registered_services': list(self._service_factories.keys()),
            'initialized_services': list(self._services.keys()),
            'config': self.config.to_dict(),
        }

        # 添加各个服务的健康状态
        for service_name, service in self._services.items():
            try:
                if hasattr(service, 'get_service_status'):
                    status[f'{service_name}_status'] = service.get_service_status()
                if hasattr(service, 'health_check'):
                    status[f'{service_name}_healthy'] = service.health_check()
            except Exception as e:
                status[f'{service_name}_error'] = str(e)

        return status

    def health_check_all(self) -> Dict[str, bool]:
        """
        检查所有服务的健康状态

        Returns:
            服务健康状态字典
        """
        health_status = {}
        for service_name, service in self._services.items():
            try:
                if hasattr(service, 'health_check'):
                    health_status[service_name] = service.health_check()
                else:
                    health_status[service_name] = True  # 没有健康检查方法认为健康
            except Exception:
                health_status[service_name] = False

        return health_status

    def reload_service(self, service_name: str) -> bool:
        """
        重新加载指定服务

        Args:
            service_name: 服务名称

        Returns:
            True 如果重载成功，False 否则
        """
        try:
            if service_name in self._services:
                # 清理现有服务
                old_service = self._services.pop(service_name)
                if hasattr(old_service, 'cleanup'):
                    old_service.cleanup()

            # 重新初始化
            self.get_service(service_name)
            return True
        except Exception:
            return False

    def shutdown(self) -> None:
        """关闭服务管理器并清理所有服务"""
        for service_name, service in self._services.items():
            try:
                if hasattr(service, 'cleanup'):
                    service.cleanup()
                if hasattr(service, 'close'):
                    service.close()
            except Exception as e:
                print(f"Error cleaning up service '{service_name}': {e}")

        self._services.clear()
        self._service_factories.clear()
        self._initialization_locks.clear()


def service_cache(func: Callable[[str], T]) -> Callable[[str], T]:
    """
    服务缓存装饰器

    Args:
        func: 获取服务的函数

    Returns:
        装饰后的函数
    """
    cache = {}
    lock = threading.Lock()

    @wraps(func)
    def wrapper(service_name: str) -> T:
        if service_name in cache:
            return cache[service_name]

        with lock:
            if service_name not in cache:
                cache[service_name] = func(service_name)
            return cache[service_name]

    return wrapper


# 全局服务管理器实例
_global_service_manager: Optional[ServiceManager] = None
_manager_lock = threading.Lock()


def get_service_manager() -> ServiceManager:
    """
    获取全局服务管理器实例

    Returns:
        ServiceManager: 服务管理器实例
    """
    global _global_service_manager
    if _global_service_manager is None:
        with _manager_lock:
            if _global_service_manager is None:
                _global_service_manager = ServiceManager()
                _register_default_services(_global_service_manager)
    return _global_service_manager


def _register_default_services(manager: ServiceManager) -> None:
    """
    注册默认服务到管理器

    Args:
        manager: 服务管理器实例
    """
    try:
        # 注册坐标服务
        from .coordinate import create_coordinate_service
        manager.register_service('coordinate', create_coordinate_service)

        # 注册天气服务
        from .weather import create_weather_service
        manager.register_service('weather', create_weather_service)

    except ImportError as e:
        print(f"Warning: Failed to register default services: {e}")


def get_coordinate_service() -> ICoordinateService:
    """
    便捷函数：获取坐标服务

    Returns:
        ICoordinateService: 坐标服务实例
    """
    return get_service_manager().get_coordinate_service()


def get_weather_service() -> IWeatherService:
    """
    便捷函数：获取天气服务

    Returns:
        IWeatherService: 天气服务实例
    """
    return get_service_manager().get_weather_service()