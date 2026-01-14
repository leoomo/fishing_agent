"""
通用 LLM 调用服务

提供统一的 LLM 调用接口，自动记录统计信息到 LLMLog 表。
支持多个提供商：qwen（通义千问）、zhipu（智谱）、deepseek。

使用示例：
    from apps.api.services.llm_service import LLMService

    llm = LLMService(provider="qwen", caller="fish_fetcher")
    response = llm.chat([
        {"role": "user", "content": "你好"}
    ])
    print(response.content)
"""

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from apps.api.models.system import LLMLog
from apps.api.orm.session import get_db_session

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM 响应结果"""

    content: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class LLMService:
    """
    通用 LLM 调用服务

    自动记录所有调用到 LLMLog 表，支持多提供商。

    Args:
        provider: LLM 提供商 (qwen/zhipu/deepseek)
        model: 模型名称，不指定则使用提供商默认模型
        caller: 调用方标识，用于统计区分（如 "fish_fetcher"）
        user_id: 用户 ID（可选）
    """

    # 支持的提供商配置
    PROVIDERS = {
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "env_key": "DASHSCOPE_API_KEY",
            "default_model": "qwen-plus",
            "pricing": {"input": 0.0008, "output": 0.002},  # 每 1K tokens (CNY)
        },
        "zhipu": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "env_key": "ZHIPU_API_KEY",
            "default_model": "glm-4-flash",
            "pricing": {"input": 0.001, "output": 0.001},
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "env_key": "DEEPSEEK_API_KEY",
            "default_model": "deepseek-chat",
            "pricing": {"input": 0.001, "output": 0.002},
        },
    }

    def __init__(
        self,
        provider: str = "qwen",
        model: Optional[str] = None,
        caller: str = "unknown",
        user_id: Optional[int] = None,
    ):
        if provider not in self.PROVIDERS:
            raise ValueError(f"不支持的提供商: {provider}，可选: {list(self.PROVIDERS.keys())}")

        self.provider = provider
        self.config = self.PROVIDERS[provider]
        self.model = model or self.config["default_model"]
        self.caller = caller
        self.user_id = user_id

        # 获取 API Key
        self.api_key = os.getenv(self.config["env_key"])
        if not self.api_key:
            logger.warning(f"未配置 {self.config['env_key']}，LLM 调用将失败")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
    ) -> LLMResponse:
        """
        发送聊天请求，自动记录统计

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数 (0-1)
            max_tokens: 最大输出 token 数
            timeout: 请求超时时间（秒）

        Returns:
            LLMResponse: 包含 content、usage、success、error
        """
        if not self.api_key:
            error_msg = f"未配置 {self.config['env_key']}"
            result = LLMResponse(success=False, error=error_msg)
            self._log_call(result, 0)
            return result

        start_time = time.time()

        try:
            response = self._call_api(messages, temperature, max_tokens, timeout)
            result = self._parse_response(response)
            self._log_call(result, time.time() - start_time)
            return result

        except requests.Timeout:
            error_msg = f"请求超时 ({timeout}s)"
            result = LLMResponse(success=False, error=error_msg)
            self._log_call(result, time.time() - start_time)
            return result

        except requests.RequestException as e:
            error_msg = f"请求失败: {str(e)}"
            result = LLMResponse(success=False, error=error_msg)
            self._log_call(result, time.time() - start_time)
            return result

        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.exception(f"LLM 调用异常: {e}")
            result = LLMResponse(success=False, error=error_msg)
            self._log_call(result, time.time() - start_time)
            return result

    def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        timeout: int,
    ) -> Dict[str, Any]:
        """调用 LLM API"""
        url = f"{self.config['base_url']}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()

        return response.json()

    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
        """解析 API 响应"""
        try:
            content = response["choices"][0]["message"]["content"]
            usage = response.get("usage", {})

            return LLMResponse(
                content=content,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                success=True,
            )

        except (KeyError, IndexError) as e:
            return LLMResponse(
                success=False,
                error=f"响应解析失败: {str(e)}",
            )

    def _calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算调用成本（CNY）"""
        pricing = self.config["pricing"]
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        # 价格是每 1K tokens
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    def _log_call(self, result: LLMResponse, response_time: float):
        """记录调用到 LLMLog 表"""
        try:
            with get_db_session() as session:
                cost = self._calculate_cost(result.usage) if result.success else 0

                log = LLMLog(
                    model_provider=self.provider,
                    model_name=self.model,
                    prompt_tokens=result.usage.get("prompt_tokens", 0),
                    completion_tokens=result.usage.get("completion_tokens", 0),
                    total_tokens=result.usage.get("total_tokens", 0),
                    response_time=round(response_time, 3),
                    success=result.success,
                    error_message=result.error,
                    cost=cost,
                    agent_type=self.caller,
                    user_id=self.user_id,
                )
                session.add(log)
                # commit 由 context manager 自动处理

        except Exception as e:
            # 日志记录失败不应影响主流程
            logger.warning(f"记录 LLM 调用日志失败: {e}")
