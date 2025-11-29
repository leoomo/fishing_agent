#!/usr/bin/env python3
"""
Dynamic Prompt Middleware - 根据查询类型动态选择系统 prompt

支持的查询类型：
1. 钓鱼查询：包含"钓鱼"关键词 → BASE + FISHING_OUTPUT_RULES (~1200 tokens)
2. 天气查询：包含"天气"/"温度"/"下雨"等关键词 → BASE + WEATHER_QUERY_RULES (~800 tokens)
3. 其他查询：使用基础 prompt → BASE (~600 tokens)
"""

import logging
from langchain.agents.middleware import dynamic_prompt, ModelRequest

from ..prompts import BASE_SYSTEM_PROMPT, FISHING_OUTPUT_RULES, WEATHER_QUERY_RULES

logger = logging.getLogger(__name__)


@dynamic_prompt
def select_prompt_by_query_type(request: ModelRequest) -> str:
    """
    根据用户查询动态选择系统 prompt

    查询类型检测优先级：
    1. 钓鱼查询：包含"钓鱼"关键词 → BASE + FISHING_OUTPUT_RULES
    2. 天气查询：包含"天气"/"温度"/"下雨"等关键词 → BASE + WEATHER_QUERY_RULES
    3. 其他查询：使用基础 prompt → BASE

    Args:
        request: ModelRequest 包含 state 和其他信息

    Returns:
        Combined system prompt
    """
    # 获取最新用户消息
    messages = request.state.get("messages", [])
    if not messages:
        logger.debug("No messages in state, using base prompt")
        return BASE_SYSTEM_PROMPT

    # 获取最后一条用户消息
    last_message = messages[-1]
    user_input = ""

    if hasattr(last_message, 'content'):
        user_input = last_message.content
    elif isinstance(last_message, dict):
        user_input = last_message.get('content', '')

    # 转为字符串并清理
    user_input = str(user_input).strip()

    # 检测查询类型
    if "钓鱼" in user_input:
        # 钓鱼查询：加载完整规则
        logger.debug(f"Detected fishing query, loading fishing rules (~1200 tokens)")
        return BASE_SYSTEM_PROMPT + "\n\n" + FISHING_OUTPUT_RULES
    elif any(kw in user_input for kw in ["天气", "温度", "下雨", "气温", "降水"]):
        # 天气查询：加载简化规则
        logger.debug(f"Detected weather query, loading weather rules (~800 tokens)")
        return BASE_SYSTEM_PROMPT + "\n\n" + WEATHER_QUERY_RULES
    else:
        # 其他查询：仅基础 prompt
        logger.debug(f"Detected general query, loading base prompt (~600 tokens)")
        return BASE_SYSTEM_PROMPT
