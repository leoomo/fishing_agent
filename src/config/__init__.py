"""
配置管理模块

提供统一的配置管理和服务行为控制。
"""

from .service_config import ServiceConfig, get_service_config

__all__ = [
    "ServiceConfig",
    "get_service_config",
]