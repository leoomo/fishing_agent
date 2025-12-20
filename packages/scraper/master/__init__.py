"""
Master Service - 分布式爬虫Master服务

提供节点管理、任务调度、图片处理等功能
"""

from .app import create_app

__all__ = ["create_app"]
