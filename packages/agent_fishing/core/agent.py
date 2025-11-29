#!/usr/bin/env python3
"""
Core Agent - Simplified fishing assistant implementation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable

from ..tools import get_all_tools
from .model_factory import ModelFactory
from .prompts import get_system_prompt
from .callbacks import FishingAgentCallback, OutputFormatValidator

logger = logging.getLogger(__name__)


class FishingAgent:
    """
    Simplified intelligent fishing assistant

    Built with LangChain 1.0+ best practices:
    - Direct tool integration (no middleware layers)
    - Callback-based stats tracking
    - Clean separation of concerns
    - Proper message protocol usage
    """

    def __init__(
        self,
        model_provider: str = "zhipu",
        timeout: int = 60,
        enable_logging: bool = True,
        verbose_callbacks: bool = False
    ):
        """
        Initialize fishing agent

        Args:
            model_provider: LLM provider ("zhipu", "qwen", "doubao", "openai")
            timeout: Request timeout in seconds
            enable_logging: Enable logging output
            verbose_callbacks: Enable verbose callback logging
        """
        self.model_provider = model_provider
        self.timeout = timeout
        self.enable_logging = enable_logging

        # Initialize callback handler
        self.callback = FishingAgentCallback(verbose=verbose_callbacks)

        # Initialize output format validator
        self._format_validator = OutputFormatValidator()

        # Initialize components
        self.model = self._initialize_model()
        self.tools = self._setup_tools()
        self.agent = self._create_agent()

        if enable_logging:
            logger.info(f"✅ 智能钓鱼助手初始化完成")
            logger.info(f"   模型: {model_provider}")
            logger.info(f"   工具数: {len(self.tools)}")
            logger.info(f"   架构: LangChain 1.0+ 简化版")

    def _initialize_model(self) -> Any:
        """Initialize language model using factory"""
        try:
            return ModelFactory.create(
                provider=self.model_provider,
                timeout=self.timeout
            )
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            raise

    def _setup_tools(self) -> List:
        """Setup tool set - simplified single import"""
        tools = get_all_tools()

        if self.enable_logging:
            logger.info(f"🛠️ 工具集配置完成: {len(tools)} 个工具")
            for tool in tools:
                logger.debug(f"   - {tool.name}")

        return tools

    def _create_agent(self) -> Runnable:
        """Create LangChain agent with standard pattern"""
        system_prompt = get_system_prompt()

        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=system_prompt
        )

        if self.enable_logging:
            logger.info("🤖 智能体创建完成")

        return agent

    def run(self, user_input: str) -> str:
        """
        Execute agent query

        Args:
            user_input: User query string

        Returns:
            Agent response string
        """
        try:
            if self.enable_logging:
                logger.info(f"📝 用户输入: {user_input}")

            # Invoke agent with callback tracking
            # 构建回调列表，包含主回调和 usage 跟踪回调
            callbacks = [self.callback]
            if self.callback._usage_handler:
                callbacks.append(self.callback._usage_handler)

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config={"callbacks": callbacks}
            )

            # Extract response using message protocol
            response = self._extract_response(result)

            if self.enable_logging:
                logger.info(f"🤖 智能体回复: {len(response)} 字符")

            return response

        except Exception as e:
            logger.error(f"💥 智能体执行出错: {e}")

            # Graceful degradation for weather/fishing queries
            if self._is_weather_fishing_query(user_input):
                return self._fallback_response(user_input)
            else:
                return f"抱歉，我遇到了一些技术问题：{str(e)}。请稍后重试。"

    def _extract_response(self, result: Any) -> str:
        """
        Extract response text from agent result

        Args:
            result: Agent invocation result

        Returns:
            Response text string
        """
        response = ""

        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            if messages and len(messages) > 0:
                last_message = messages[-1]

                # Try to get content attribute
                if hasattr(last_message, 'content'):
                    response = last_message.content
                # Try dict access
                elif isinstance(last_message, dict) and "content" in last_message:
                    response = last_message["content"]
                else:
                    response = str(result)
        else:
            response = str(result)

        # 验证输出格式（仅在调用了钓鱼推荐工具时）
        self._validate_output_format(response)

        return response

    def _validate_output_format(self, response: str) -> None:
        """
        验证 LLM 输出是否保留了工具的预设格式

        Args:
            response: LLM 返回的响应内容
        """
        # 获取最后调用的工具
        tool_calls = self.callback.stats.get("tool_calls", {})
        last_tool = None

        # 检查是否调用了钓鱼推荐工具
        if "query_fishing_recommendation" in tool_calls:
            last_tool = "query_fishing_recommendation"

        if last_tool:
            validation = self._format_validator.validate_fishing_report(
                response, last_tool
            )
            self._format_validator.log_validation_result(validation)

    def _is_weather_fishing_query(self, query: str) -> bool:
        """Check if query is weather/fishing related"""
        weather_keywords = ["天气", "温度", "下雨", "晴", "阴", "多云"]
        fishing_keywords = ["钓鱼", "路亚", "钓", "渔"]

        query_lower = query.lower()
        return (
            any(keyword in query_lower for keyword in weather_keywords) or
            any(keyword in query_lower for keyword in fishing_keywords)
        )

    def _fallback_response(self, query: str) -> str:
        """Generate fallback response for weather/fishing queries"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""## 🎯 智能钓鱼助手 - 降级模式

⚠️ 系统暂时遇到技术问题，为您提供基础建议：

**当前时间**: {current_time}
**查询内容**: {query}

### 🎣 基础钓鱼建议
- **最佳时段**: 早上5-9点、傍晚18-21点
- **理想温度**: 15-25°C
- **推荐天气**: 多云、阴天天气
- **避免条件**: 强风、暴雨、极端温度

### 🌤️ 通用建议
- 清晨和傍晚是鱼类活动高峰期
- 多云天气下鱼类更加活跃
- 选择适合当前季节的装备和饵料

建议稍后重试以获取详细的天气数据和专业分析。

---
*由智能钓鱼助手提供（降级模式）*"""

    def get_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics

        Returns:
            Dictionary with agent statistics
        """
        callback_summary = self.callback.get_summary()

        return {
            "model_provider": self.model_provider,
            "tools_count": len(self.tools),
            "timeout": self.timeout,
            "architecture": "LangChain 1.0+ 简化架构",
            "middleware_count": 0,
            **callback_summary
        }

    def get_llm_stats(self) -> Dict[str, Any]:
        """
        Get detailed LLM statistics

        Returns:
            Dictionary with LLM execution stats
        """
        summary = self.callback.get_summary()

        return {
            "enabled": True,
            "model_provider": self.model_provider,
            "architecture": "LangChain 1.0+ 直接工具调用",
            "total_model_calls": summary["llm_calls"],
            "total_errors": summary["total_errors"],
            "success_rate": summary["success_rate"],
            "total_tokens": summary["total_tokens"],
            "middleware_enabled": False,
            "performance": "简化架构，无过度抽象"
        }

    def reset_stats(self) -> None:
        """Reset execution statistics"""
        self.callback.reset()
        if self.enable_logging:
            logger.info("📊 统计信息已重置")

    def print_stats(self) -> None:
        """Print formatted statistics to console"""
        self.callback.print_summary()
