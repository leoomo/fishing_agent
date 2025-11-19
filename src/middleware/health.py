#!/usr/bin/env python3
"""
Health Check - System health monitoring
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HealthCheck:
    """
    System health check utilities

    Monitors:
    - Model availability
    - Tool loading
    - API key configuration
    """

    def __init__(self, agent: Any):
        """
        Initialize health checker

        Args:
            agent: FishingAgent instance to monitor
        """
        self.agent = agent

    def check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check

        Returns:
            Health status dictionary
        """
        health_status = {
            "status": "healthy",
            "architecture": "LangChain 1.0+ 简化架构",
            "checks": {}
        }

        # Check model
        try:
            _ = self.agent.model
            health_status["checks"]["model"] = "✅ 正常"
        except Exception as e:
            health_status["checks"]["model"] = f"❌ 异常: {e}"
            health_status["status"] = "degraded"

        # Check tools
        try:
            tools_count = len(self.agent.tools)
            if tools_count > 0:
                health_status["checks"]["tools"] = f"✅ 正常 ({tools_count}个工具)"
            else:
                health_status["checks"]["tools"] = "⚠️ 警告: 无可用工具"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["tools"] = f"❌ 异常: {e}"
            health_status["status"] = "degraded"

        # Check middleware (simplified - no middleware in v2.2.0)
        health_status["checks"]["middleware"] = "✅ 简化架构 (无中间件层)"

        # Check API keys
        api_keys_status = self._check_api_keys()
        health_status["checks"]["api_keys"] = api_keys_status

        return health_status

    def _check_api_keys(self) -> str:
        """
        Check API key configuration

        Returns:
            API keys status string
        """
        api_keys = {
            "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
            "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY"),
            "ARK_API_KEY": os.getenv("ARK_API_KEY"),
            "CAIYUN_API_KEY": os.getenv("CAIYUN_API_KEY"),
            "AMAP_API_KEY": os.getenv("AMAP_API_KEY"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
        }

        configured_count = sum(1 for key in api_keys.values() if key)
        total_count = len(api_keys)

        if configured_count == 0:
            return f"❌ 无API密钥配置"
        elif configured_count < 3:
            return f"⚠️ {configured_count}/{total_count} 个API密钥已配置 (建议配置更多)"
        else:
            return f"✅ {configured_count}/{total_count} 个API密钥已配置"

    def print_health(self) -> None:
        """Print health status to console"""
        health = self.check()

        print("\n" + "=" * 50)
        print(f"🏥 系统健康检查")
        print("=" * 50)
        print(f"状态: {health['status']}")
        print(f"架构: {health['architecture']}")
        print("\n检查结果:")

        for check_name, status in health['checks'].items():
            print(f"  {check_name}: {status}")

        print("=" * 50 + "\n")

    @staticmethod
    def check_environment() -> Dict[str, Any]:
        """
        Check environment configuration (static method)

        Returns:
            Environment status dictionary
        """
        from src.fishing_agent.model_factory import ModelFactory

        env_status = {
            "python_version": os.sys.version,
            "available_providers": ModelFactory.check_availability(),
            "required_apis": {
                "CAIYUN_API_KEY": bool(os.getenv("CAIYUN_API_KEY")),
                "AMAP_API_KEY": bool(os.getenv("AMAP_API_KEY"))
            }
        }

        return env_status
