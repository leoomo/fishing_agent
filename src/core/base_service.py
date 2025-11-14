"""
LangChain Learning - Base Service

提供服务的基础实现，包含通用的服务功能和资源管理。
"""

from typing import Dict, Any, Optional, List
import logging
import asyncio
from .interfaces import IService, ServiceConfig


class BaseService(IService):
    """服务基类，提供通用的服务功能"""

    def __init__(self, config: ServiceConfig, logger: Optional[logging.Logger] = None):
        self._config = config
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._initialized = False
        self._health_status = True
        self._startup_time: Optional[float] = None
        self._last_health_check: Optional[float] = None

    @property
    def config(self) -> ServiceConfig:
        """获取服务配置"""
        return self._config

    @property
    def logger(self) -> logging.Logger:
        """获取日志器"""
        return self._logger

    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self._initialized

    def is_healthy(self) -> bool:
        """检查服务是否健康"""
        return self._health_status and self._initialized

    async def initialize(self) -> None:
        """初始化服务"""
        if not self._initialized:
            self._logger.info(f"Initializing service: {self._config.name}")
            import time
            self._startup_time = time.time()

            try:
                await self._on_initialize()
                self._initialized = True
                self._logger.info(f"Service initialized successfully: {self._config.name}")
            except Exception as e:
                self._logger.error(f"Service initialization failed: {self._config.name} - {str(e)}")
                raise e

    async def _on_initialize(self) -> None:
        """初始化钩子方法（子类可重写）"""
        pass

    async def cleanup(self) -> None:
        """清理服务资源"""
        if self._initialized:
            self._logger.info(f"Cleaning up service: {self._config.name}")
            
            try:
                await self._on_cleanup()
                self._initialized = False
                self._logger.info(f"Service cleaned up successfully: {self._config.name}")
            except Exception as e:
                self._logger.error(f"Service cleanup failed: {self._config.name} - {str(e)}")
                raise e

    async def _on_cleanup(self) -> None:
        """清理钩子方法（子类可重写）"""
        pass

    def health_check(self) -> bool:
        """健康检查"""
        import time
        self._last_health_check = time.time()

        try:
            # 执行基础健康检查
            basic_health = self._basic_health_check()
            
            # 执行自定义健康检查
            custom_health = self._custom_health_check()
            
            self._health_status = basic_health and custom_health
            
            if self._health_status:
                self._logger.debug(f"Health check passed: {self._config.name}")
            else:
                self._logger.warning(f"Health check failed: {self._config.name}")

            return self._health_status

        except Exception as e:
            self._logger.error(f"Health check error: {self._config.name} - {str(e)}")
            self._health_status = False
            return False

    def _basic_health_check(self) -> bool:
        """基础健康检查"""
        return self._initialized

    def _custom_health_check(self) -> bool:
        """自定义健康检查（子类可重写）"""
        return True

    async def health_check_async(self) -> bool:
        """异步健康检查"""
        return self.health_check()

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        import time
        uptime = None
        if self._startup_time:
            uptime = time.time() - self._startup_time

        return {
            "name": self._config.name,
            "version": self._config.version,
            "enabled": self._config.enabled,
            "initialized": self._initialized,
            "healthy": self.is_healthy(),
            "uptime": uptime,
            "startup_time": self._startup_time,
            "last_health_check": self._last_health_check,
            "config": self._config.config
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新服务配置"""
        self._config.config.update(new_config)
        self._logger.info(f"Service config updated: {self._config.name}")

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.config.get(key, default)

    def set_config_value(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config.config[key] = value

    async def restart(self) -> None:
        """重启服务"""
        self._logger.info(f"Restarting service: {self._config.name}")
        await self.cleanup()
        await asyncio.sleep(1)  # 短暂等待
        await self.initialize()
        self._logger.info(f"Service restarted successfully: {self._config.name}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


class ManagedService(BaseService):
    """可管理的服务基类"""

    def __init__(self, config: ServiceConfig, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "avg_response_time": 0.0,
            "last_request_time": None
        }

    def get_metrics(self) -> Dict[str, Any]:
        """获取服务指标"""
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """重置服务指标"""
        self._metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "avg_response_time": 0.0,
            "last_request_time": None
        }

    def _record_request_start(self) -> float:
        """记录请求开始"""
        import time
        start_time = time.time()
        self._metrics["requests_total"] += 1
        self._metrics["last_request_time"] = start_time
        return start_time

    def _record_request_end(self, start_time: float, success: bool = True) -> None:
        """记录请求结束"""
        import time
        end_time = time.time()
        response_time = end_time - start_time

        if success:
            self._metrics["requests_successful"] += 1
        else:
            self._metrics["requests_failed"] += 1

        # 更新平均响应时间
        total_requests = self._metrics["requests_total"]
        if total_requests > 0:
            current_avg = self._metrics["avg_response_time"]
            self._metrics["avg_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )


class DependentService(BaseService):
    """有依赖的服务基类"""

    def __init__(self, config: ServiceConfig, dependencies: Optional[List[str]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._dependencies = dependencies or []
        self._dependency_status: Dict[str, bool] = {}

    def add_dependency(self, service_name: str) -> None:
        """添加依赖"""
        if service_name not in self._dependencies:
            self._dependencies.append(service_name)
            self._logger.info(f"Dependency added: {service_name}")

    def remove_dependency(self, service_name: str) -> None:
        """移除依赖"""
        if service_name in self._dependencies:
            self._dependencies.remove(service_name)
            self._dependency_status.pop(service_name, None)
            self._logger.info(f"Dependency removed: {service_name}")

    def update_dependency_status(self, service_name: str, status: bool) -> None:
        """更新依赖状态"""
        if service_name in self._dependencies:
            self._dependency_status[service_name] = status
            self._logger.debug(f"Dependency status updated: {service_name} -> {status}")

    def get_dependency_status(self) -> Dict[str, bool]:
        """获取依赖状态"""
        return self._dependency_status.copy()

    def all_dependencies_healthy(self) -> bool:
        """检查所有依赖是否健康"""
        if not self._dependencies:
            return True

        return all(
            self._dependency_status.get(dep, False) 
            for dep in self._dependencies
        )

    def _custom_health_check(self) -> bool:
        """自定义健康检查（包含依赖检查）"""
        return self.all_dependencies_healthy()