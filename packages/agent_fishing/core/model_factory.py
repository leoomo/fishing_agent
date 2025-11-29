#!/usr/bin/env python3
"""
Model Factory - Centralized LLM initialization
"""

import os
import logging
from typing import Dict, Any
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatTongyi

logger = logging.getLogger(__name__)


class ModelFactory:
    """Factory for creating LLM instances with unified configuration"""

    # Provider configurations
    PROVIDERS: Dict[str, Dict[str, Any]] = {
        "zhipu": {
            "class": ChatOpenAI,
            "base_url": "https://open.bigmodel.cn/api/paas/v4/",
            "model": "glm-4-flash",
            "env_key": "ANTHROPIC_AUTH_TOKEN",
            "display_name": "智谱AI GLM"
        },
        "qwen": {
            "class": ChatTongyi,
            "model": "qwen-plus",
            "env_key": "DASHSCOPE_API_KEY",
            "display_name": "通义千问"
        },
        "doubao": {
            "class": ChatOpenAI,
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-pro",
            "env_key": "ARK_API_KEY",
            "display_name": "豆包"
        },
        "openai": {
            "class": ChatOpenAI,
            "model": "gpt-3.5-turbo",
            "env_key": "OPENAI_API_KEY",
            "display_name": "OpenAI GPT"
        }
    }

    @classmethod
    def create(cls, provider: str = "zhipu", timeout: int = 60, **kwargs) -> BaseChatModel:
        """
        Create a language model instance

        Args:
            provider: Model provider name ("zhipu", "qwen", "doubao", "openai")
            timeout: Request timeout in seconds
            **kwargs: Additional model-specific parameters

        Returns:
            Initialized language model instance

        Raises:
            ValueError: If provider is unsupported or API key is missing
        """
        if provider not in cls.PROVIDERS:
            available = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(
                f"Unsupported model provider: {provider}. "
                f"Available providers: {available}"
            )

        config = cls.PROVIDERS[provider]
        api_key = os.getenv(config["env_key"])

        if not api_key:
            raise ValueError(
                f"API key not configured for {provider}. "
                f"Please set {config['env_key']} in your environment."
            )

        # Build model kwargs
        model_kwargs = {
            "api_key": api_key,
            "timeout": timeout,
        }

        # Add model name if specified
        if "model" in config:
            model_kwargs["model"] = config["model"]

        # Add base_url for OpenAI-compatible providers
        if "base_url" in config:
            model_kwargs["base_url"] = config["base_url"]

        # Merge any additional kwargs
        model_kwargs.update(kwargs)

        # Instantiate model
        model_class = config["class"]
        model = model_class(**model_kwargs)

        logger.info(
            f"✅ Model initialized: {config['display_name']} "
            f"(provider={provider}, model={config.get('model', 'default')})"
        )

        return model

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """
        List all available model providers

        Returns:
            Dict mapping provider name to display name
        """
        return {
            name: config["display_name"]
            for name, config in cls.PROVIDERS.items()
        }

    @classmethod
    def check_availability(cls) -> Dict[str, bool]:
        """
        Check which providers have configured API keys

        Returns:
            Dict mapping provider name to availability status
        """
        return {
            name: bool(os.getenv(config["env_key"]))
            for name, config in cls.PROVIDERS.items()
        }
