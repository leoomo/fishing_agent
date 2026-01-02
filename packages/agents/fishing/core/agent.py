#!/usr/bin/env python3
"""
Core Agent - Simplified fishing assistant implementation
"""

import logging
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable

from ..tools import get_all_tools
from .model_factory import ModelFactory
from .prompts import BASE_SYSTEM_PROMPT, FISHING_OUTPUT_RULES, WEATHER_QUERY_RULES
from .callbacks import OutputFormatValidator
from packages.agents.agent_component.monitoring import MonitoringCallback
from ..middleware import select_prompt_by_query_type

logger = logging.getLogger(__name__)


class FishingAgent:
    """
    Simplified intelligent fishing assistant

    Built with LangChain 1.0+ best practices:
    - Direct tool integration (no middleware layers)
    - Unified monitoring callback
    - Clean separation of concerns
    - Proper message protocol usage
    """

    def __init__(
        self,
        model_provider: str = "zhipu",
        timeout: int = 60,
        enable_logging: bool = True,
        verbose_callbacks: bool = False,
        enable_monitoring: bool = True,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ):
        """
        Initialize fishing agent

        Args:
            model_provider: LLM provider ("zhipu", "qwen", "doubao", "openai")
            timeout: Request timeout in seconds
            enable_logging: Enable logging output
            verbose_callbacks: Enable verbose callback logging
            enable_monitoring: Enable database monitoring (default True)
            user_id: User ID for monitoring context
            session_id: Chat session ID for monitoring context
        """
        self.model_provider = model_provider
        self.timeout = timeout
        self.enable_logging = enable_logging
        self.enable_monitoring = enable_monitoring
        self.user_id = user_id
        self.session_id = session_id

        # 统一监控回调（替代旧的双回调架构）
        self.callback = MonitoringCallback(
            agent_type="fishing",
            model_provider=model_provider,
            user_id=user_id,
            session_id=session_id,
            persist=enable_monitoring,
            verbose=verbose_callbacks
        )

        # Initialize output format validator
        self._format_validator = OutputFormatValidator()

        # Initialize components
        self.model = self._initialize_model()
        self.tools = self._setup_tools()
        self.agent = self._create_agent()

        if enable_logging:
            logger.info(f"智能钓鱼助手初始化完成")
            logger.info(f"   模型: {model_provider}")
            logger.info(f"   工具数: {len(self.tools)}")
            logger.info(f"   架构: LangChain 1.0+ 统一监控")

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
            logger.info(f"工具集配置完成: {len(tools)} 个工具")
            for tool in tools:
                logger.debug(f"   - {tool.name}")

        return tools

    def _create_agent(self) -> Runnable:
        """
        Create LangChain agent with dynamic prompt middleware

        使用 @dynamic_prompt 中间件实现运行时 prompt 选择：
        - 钓鱼查询：~1,200 tokens (BASE + FISHING_OUTPUT_RULES)
        - 天气查询：~800 tokens (BASE + WEATHER_QUERY_RULES)
        - 其他查询：~600 tokens (BASE only)
        """
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            middleware=[select_prompt_by_query_type]
        )

        if self.enable_logging:
            logger.info("智能体创建完成（使用动态 prompt 中间件）")

        return agent

    def run(
        self,
        user_input: str,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> str:
        """
        Execute agent query

        Args:
            user_input: User query string
            user_id: Override user ID for this execution
            session_id: Override session ID for this execution

        Returns:
            Agent response string
        """
        try:
            if self.enable_logging:
                logger.info(f"用户输入: {user_input}")

            # Update monitoring context if provided
            if user_id is not None:
                self.callback.user_id = user_id
            if session_id is not None:
                self.callback.session_id = session_id

            # Set input text for monitoring
            self.callback.set_input(user_input)

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config={"callbacks": [self.callback]}
            )

            # Extract response using message protocol
            response = self._extract_response(result)

            if self.enable_logging:
                logger.info(f"智能体回复: {len(response)} 字符")

            return response

        except Exception as e:
            logger.error(f"智能体执行出错: {e}")

            # Graceful degradation for weather/fishing queries
            if self._is_weather_fishing_query(user_input):
                return self._fallback_response(user_input)
            else:
                return f"抱歉，我遇到了一些技术问题：{str(e)}。请稍后重试。"

    def stream(
        self,
        user_input: str,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Execute agent query with streaming output

        Uses LangChain 1.0+ native .stream() method to yield
        incremental content chunks for SSE responses.

        Args:
            user_input: User query string
            user_id: Override user ID for this execution
            session_id: Override session ID for this execution

        Yields:
            Content chunks as they are generated
        """
        try:
            if self.enable_logging:
                logger.info(f"[流式] 用户输入: {user_input}")

            # Update monitoring context if provided
            if user_id is not None:
                self.callback.user_id = user_id
            if session_id is not None:
                self.callback.session_id = session_id

            # Set input text for monitoring
            self.callback.set_input(user_input)

            # 使用 stream_mode="messages" 获取逐 token 流式输出
            total_content = ""
            seen_chunks = set()

            for chunk in self.agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config={"callbacks": [self.callback]},
                stream_mode="messages"
            ):
                # stream_mode="messages" 返回 (message, metadata) 元组
                if isinstance(chunk, tuple) and len(chunk) >= 2:
                    msg, metadata = chunk[0], chunk[1]
                    msg_type = type(msg).__name__

                    # 只处理 AIMessageChunk
                    if msg_type != "AIMessageChunk":
                        continue

                    if hasattr(msg, 'content') and msg.content:
                        content = msg.content
                        if content and isinstance(content, str):
                            chunk_hash = hash(content)
                            if chunk_hash in seen_chunks:
                                continue
                            seen_chunks.add(chunk_hash)

                            total_content += content
                            yield content

            if self.enable_logging:
                logger.info(f"[流式] 回复完成: {len(total_content)} 字符")

        except Exception as e:
            logger.error(f"[流式] 智能体执行出错: {e}")

            if self._is_weather_fishing_query(user_input):
                fallback = self._fallback_response(user_input)
                yield fallback
            else:
                yield f"抱歉，我遇到了一些技术问题：{str(e)}。请稍后重试。"

    def _extract_response(self, result: Any) -> str:
        """Extract response text from agent result"""
        response = ""

        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            if messages and len(messages) > 0:
                last_message = messages[-1]

                if hasattr(last_message, 'content'):
                    response = last_message.content
                elif isinstance(last_message, dict) and "content" in last_message:
                    response = last_message["content"]
                else:
                    response = str(result)
        else:
            response = str(result)

        # 验证输出格式
        self._validate_output_format(response)

        return response

    def _validate_output_format(self, response: str) -> None:
        """验证 LLM 输出是否保留了工具的预设格式"""
        tool_calls = self.callback._build_tool_summary()

        if "query_fishing_recommendation" in tool_calls:
            validation = self._format_validator.validate_fishing_report(
                response, "query_fishing_recommendation"
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

        return f"""## 智能钓鱼助手 - 降级模式

系统暂时遇到技术问题，为您提供基础建议：

**当前时间**: {current_time}
**查询内容**: {query}

### 基础钓鱼建议
- **最佳时段**: 早上5-9点、傍晚18-21点
- **理想温度**: 15-25°C
- **推荐天气**: 多云、阴天天气
- **避免条件**: 强风、暴雨、极端温度

### 通用建议
- 清晨和傍晚是鱼类活动高峰期
- 多云天气下鱼类更加活跃
- 选择适合当前季节的装备和饵料

建议稍后重试以获取详细的天气数据和专业分析。

---
*由智能钓鱼助手提供（降级模式）*"""

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        summary = self.callback.get_summary()

        return {
            "model_provider": self.model_provider,
            "tools_count": len(self.tools),
            "timeout": self.timeout,
            "architecture": "LangChain 1.0+ 统一监控",
            **summary
        }

    def get_llm_stats(self) -> Dict[str, Any]:
        """Get detailed LLM statistics"""
        summary = self.callback.get_summary()

        return {
            "enabled": True,
            "model_provider": self.model_provider,
            "architecture": "LangChain 1.0+ 统一监控",
            "total_model_calls": summary["llm_calls"],
            "total_errors": summary["total_errors"],
            "success_rate": summary["success_rate"],
            "total_tokens": summary["total_tokens"],
            "estimated_cost": summary["estimated_cost"],
        }

    def reset_stats(self) -> None:
        """Reset execution statistics"""
        self.callback.reset()
        if self.enable_logging:
            logger.info("统计信息已重置")

    def print_stats(self) -> None:
        """Print formatted statistics to console"""
        self.callback.print_summary()

    # 兼容旧属性名
    @property
    def monitoring_callback(self):
        return self.callback
