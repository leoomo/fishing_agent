#!/usr/bin/env python3
"""
Unified Monitoring Callback - Collects and persists Agent metrics to database

This callback handler provides:
- Token usage tracking across multiple LLM providers
- Tool call metrics with timing
- Automatic async persistence to database
- Cost estimation based on model pricing
"""

import logging
import time
import json
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


# Model pricing per 1K tokens (in CNY)
MODEL_PRICING = {
    "qwen": {"input": 0.0008, "output": 0.002},
    "zhipu": {"input": 0.001, "output": 0.001},
    "doubao": {"input": 0.0008, "output": 0.002},
    "openai": {"input": 0.015, "output": 0.06},  # GPT-4 pricing
    "deepseek": {"input": 0.001, "output": 0.002},
}


class MonitoringCallback(BaseCallbackHandler):
    """
    Unified callback handler for all Agent monitoring.

    Features:
    - Tracks LLM calls, tokens, and costs
    - Records tool invocations with timing
    - Automatically persists to database asynchronously (non-blocking)
    - Supports all agent types with unified interface

    Usage:
        callback = MonitoringCallback(
            agent_type="fishing",
            model_provider="zhipu",
            user_id=123,
            session_id=456
        )
        agent.invoke({"messages": [...]}, config={"callbacks": [callback]})
    """

    def __init__(
        self,
        agent_type: str,
        model_provider: str = "unknown",
        model_name: str = "unknown",
        user_id: Optional[int] = None,
        session_id: Optional[int] = None,
        persist: bool = True,
        verbose: bool = False
    ):
        """
        Initialize monitoring callback.

        Args:
            agent_type: Agent identifier (e.g., "fishing", "equipment_import")
            model_provider: LLM provider name (e.g., "zhipu", "qwen")
            model_name: Model name (e.g., "glm-4-flash")
            user_id: User ID for the request
            session_id: Chat session ID if applicable
            persist: Whether to persist to database (default True)
            verbose: Enable verbose logging
        """
        super().__init__()
        self.agent_type = agent_type
        self.model_provider = model_provider
        self.model_name = model_name
        self.user_id = user_id
        self.session_id = session_id
        self.persist = persist
        self.verbose = verbose

        # Execution tracking
        self.execution_id: Optional[int] = None
        self.input_text: str = ""
        self.output_text: str = ""

        # Reset stats
        self._reset_stats()

    def _reset_stats(self):
        """Reset all statistics for new execution"""
        self.stats = {
            "llm_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
            "latency_ms": 0,
            "tool_calls": [],  # List of tool call records
            "llm_logs": [],    # List of LLM call records
        }
        self._current_tool_start: Optional[float] = None
        self._current_tool_name: str = "unknown"
        self._current_tool_input: str = ""

    def set_input(self, text: str):
        """Set the user input text for this execution"""
        self.input_text = text[:1000] if text else ""

    def reset(self):
        """Reset for new execution"""
        self._reset_stats()
        self.execution_id = None
        self.input_text = ""
        self.output_text = ""

    # ========== LLM Callbacks ==========

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts generating"""
        self.stats["llm_calls"] += 1

        if self.stats["start_time"] is None:
            self.stats["start_time"] = time.time()

        if self.verbose:
            logger.debug(f"[{self.agent_type}] LLM started (call #{self.stats['llm_calls']})")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM finishes generating"""
        # Extract token usage
        input_tokens, output_tokens, total_tokens = self._extract_tokens(response)

        self.stats["input_tokens"] += input_tokens
        self.stats["output_tokens"] += output_tokens
        self.stats["total_tokens"] += total_tokens

        # Record LLM call
        llm_record = {
            "timestamp": datetime.utcnow(),
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "success": True,
            "error_message": None,
        }
        self.stats["llm_logs"].append(llm_record)

        if self.verbose:
            logger.debug(f"[{self.agent_type}] LLM tokens: in={input_tokens}, out={output_tokens}, total={total_tokens}")

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called on LLM error"""
        self.stats["errors"] += 1

        llm_record = {
            "timestamp": datetime.utcnow(),
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "success": False,
            "error_message": str(error)[:500],
        }
        self.stats["llm_logs"].append(llm_record)

        logger.error(f"[{self.agent_type}] LLM error: {error}")

    # ========== Tool Callbacks ==========

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Called when tool starts execution"""
        self._current_tool_name = serialized.get("name", "unknown")
        self._current_tool_start = time.time()
        self._current_tool_input = str(input_str)[:500] if input_str else ""

        if self.verbose:
            logger.debug(f"[{self.agent_type}] Tool started: {self._current_tool_name}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool finishes execution"""
        latency_ms = int((time.time() - self._current_tool_start) * 1000) if self._current_tool_start else 0

        tool_record = {
            "timestamp": datetime.utcnow(),
            "tool_name": self._current_tool_name,
            "tool_category": self._categorize_tool(self._current_tool_name),
            "input_args": self._current_tool_input,
            "output_result": str(output)[:1000] if output else "",
            "latency_ms": latency_ms,
            "success": True,
            "error_message": None,
        }
        self.stats["tool_calls"].append(tool_record)

        if self.verbose:
            logger.debug(f"[{self.agent_type}] Tool completed: {self._current_tool_name} ({latency_ms}ms)")

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called on tool error"""
        self.stats["errors"] += 1
        latency_ms = int((time.time() - self._current_tool_start) * 1000) if self._current_tool_start else 0

        tool_record = {
            "timestamp": datetime.utcnow(),
            "tool_name": self._current_tool_name,
            "tool_category": self._categorize_tool(self._current_tool_name),
            "input_args": self._current_tool_input,
            "output_result": None,
            "latency_ms": latency_ms,
            "success": False,
            "error_message": str(error)[:500],
        }
        self.stats["tool_calls"].append(tool_record)

        logger.error(f"[{self.agent_type}] Tool error in {self._current_tool_name}: {error}")

    # ========== Chain Callbacks ==========

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when chain starts execution"""
        if self.stats["start_time"] is None:
            self.stats["start_time"] = time.time()

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when chain finishes - persist data asynchronously"""
        if self.stats["start_time"]:
            self.stats["end_time"] = time.time()
            self.stats["latency_ms"] = int(
                (self.stats["end_time"] - self.stats["start_time"]) * 1000
            )

        # Extract output text
        if isinstance(outputs, dict) and "messages" in outputs:
            messages = outputs["messages"]
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    self.output_text = str(last_msg.content)[:2000]

        # Persist to database asynchronously (non-blocking)
        if self.persist:
            threading.Thread(
                target=self._persist_execution,
                daemon=True,
                name=f"monitor-persist-{self.agent_type}"
            ).start()

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Called on chain error"""
        self.stats["errors"] += 1

        if self.stats["start_time"]:
            self.stats["end_time"] = time.time()
            self.stats["latency_ms"] = int(
                (self.stats["end_time"] - self.stats["start_time"]) * 1000
            )

        logger.error(f"[{self.agent_type}] Chain error: {error}")

        # Still persist on error
        if self.persist:
            threading.Thread(
                target=self._persist_execution,
                daemon=True,
                name=f"monitor-persist-{self.agent_type}"
            ).start()

    # ========== Persistence ==========

    def _persist_execution(self):
        """Persist execution data to database (runs in background thread)"""
        try:
            from packages.agent_fishing.tools.lure.orm.session import get_db_session
            from packages.agent_fishing.tools.lure.models.system import (
                AgentExecutionLog, ToolCallLog, LLMLog
            )

            with get_db_session() as session:
                # Create execution log
                execution = AgentExecutionLog(
                    agent_type=self.agent_type,
                    session_id=self.session_id,
                    user_id=self.user_id,
                    input_text=self.input_text,
                    output_text=self.output_text,
                    model_provider=self.model_provider,
                    model_name=self.model_name,
                    llm_calls=self.stats["llm_calls"],
                    input_tokens=self.stats["input_tokens"],
                    output_tokens=self.stats["output_tokens"],
                    total_tokens=self.stats["total_tokens"],
                    latency_ms=self.stats["latency_ms"],
                    success=self.stats["errors"] == 0,
                    error_message=None,  # Could collect error messages
                    estimated_cost=self._calculate_cost(),
                    tool_calls_summary=json.dumps(
                        self._build_tool_summary(),
                        ensure_ascii=False
                    ),
                )
                session.add(execution)
                session.flush()  # Get the execution ID

                self.execution_id = execution.id

                # Create tool call logs
                for tool in self.stats["tool_calls"]:
                    tool_log = ToolCallLog(
                        execution_id=execution.id,
                        timestamp=tool["timestamp"],
                        tool_name=tool["tool_name"],
                        tool_category=tool.get("tool_category"),
                        input_args=tool.get("input_args"),
                        output_result=tool.get("output_result"),
                        latency_ms=tool.get("latency_ms"),
                        success=tool.get("success", True),
                        error_message=tool.get("error_message"),
                    )
                    session.add(tool_log)

                # Create LLM logs
                for llm in self.stats["llm_logs"]:
                    llm_log = LLMLog(
                        timestamp=llm["timestamp"],
                        model_provider=llm["model_provider"],
                        model_name=llm.get("model_name"),
                        prompt_tokens=llm.get("input_tokens", 0),
                        completion_tokens=llm.get("output_tokens", 0),
                        total_tokens=llm.get("total_tokens", 0),
                        success=llm.get("success", True),
                        error_message=llm.get("error_message"),
                        cost=self._calculate_single_cost(
                            llm.get("input_tokens", 0),
                            llm.get("output_tokens", 0)
                        ),
                        agent_type=self.agent_type,
                        session_id=self.session_id,
                        user_id=self.user_id,
                        execution_id=execution.id,
                    )
                    session.add(llm_log)

                session.commit()

            if self.verbose:
                logger.info(f"[{self.agent_type}] Persisted execution #{self.execution_id} "
                           f"(tokens={self.stats['total_tokens']}, cost={self._calculate_cost():.4f})")

        except Exception as e:
            logger.error(f"[{self.agent_type}] Failed to persist execution: {e}")

    # ========== Token Extraction ==========

    def _extract_tokens(self, response: Any) -> tuple:
        """
        Extract token counts from LLM response.
        Supports multiple model response formats.
        """
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        # Method 1: From generations (LangChain 1.0+)
        if hasattr(response, 'generations') and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, 'message'):
                        msg = gen.message
                        # From usage_metadata
                        if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                            usage = msg.usage_metadata
                            input_tokens += usage.get('input_tokens', 0)
                            output_tokens += usage.get('output_tokens', 0)
                            total_tokens += usage.get('total_tokens', 0)
                        # From response_metadata (ChatTongyi, etc.)
                        elif hasattr(msg, 'response_metadata') and msg.response_metadata:
                            meta = msg.response_metadata
                            if 'token_usage' in meta:
                                usage = meta['token_usage']
                                input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                                output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                                total_tokens += usage.get('total_tokens', 0)
                            elif 'usage' in meta:
                                usage = meta['usage']
                                input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                                output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                                total_tokens += usage.get('total_tokens', 0)

                    # From generation_info
                    if total_tokens == 0 and hasattr(gen, 'generation_info') and gen.generation_info:
                        gen_info = gen.generation_info
                        usage = gen_info.get('token_usage', gen_info.get('usage', {}))
                        if usage:
                            input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                            output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                            total_tokens += usage.get('total_tokens', 0)

        # Method 2: From llm_output (OpenAI compatible)
        if total_tokens == 0 and hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            if token_usage:
                input_tokens = token_usage.get('prompt_tokens', token_usage.get('input_tokens', 0))
                output_tokens = token_usage.get('completion_tokens', token_usage.get('output_tokens', 0))
                total_tokens = token_usage.get('total_tokens', 0)

        # Method 3: From llm_output usage field
        if total_tokens == 0 and hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('usage', {})
            if usage:
                input_tokens = usage.get('prompt_tokens', usage.get('input_tokens', 0))
                output_tokens = usage.get('completion_tokens', usage.get('output_tokens', 0))
                total_tokens = usage.get('total_tokens', 0)

        # Calculate total if not provided
        if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
            total_tokens = input_tokens + output_tokens

        return input_tokens, output_tokens, total_tokens

    # ========== Cost Calculation ==========

    def _calculate_cost(self) -> float:
        """Calculate estimated cost for this execution"""
        return self._calculate_single_cost(
            self.stats["input_tokens"],
            self.stats["output_tokens"]
        )

    def _calculate_single_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given token counts"""
        pricing = MODEL_PRICING.get(self.model_provider, {"input": 0.001, "output": 0.001})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    # ========== Helpers ==========

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by name"""
        if not tool_name:
            return "other"

        categories = {
            "weather": ["weather", "temperature", "forecast", "caiyun"],
            "fishing": ["fishing", "recommendation", "score"],
            "lure": ["lure", "equipment", "rod", "reel", "line"],
            "location": ["location", "coordinate", "map", "amap"],
            "knowledge": ["knowledge", "query", "search"],
            "time": ["time", "date", "current_time"],
        }

        tool_lower = tool_name.lower()
        for category, keywords in categories.items():
            if any(kw in tool_lower for kw in keywords):
                return category

        return "other"

    def _build_tool_summary(self) -> Dict[str, int]:
        """Build tool call count summary"""
        summary = {}
        for tool in self.stats["tool_calls"]:
            name = tool.get("tool_name", "unknown")
            summary[name] = summary.get(name, 0) + 1
        return summary

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary (compatible with existing callback interface)"""
        success_rate = 0.0
        total_calls = self.stats["llm_calls"] + len(self.stats["tool_calls"])
        if total_calls > 0:
            success_count = total_calls - self.stats["errors"]
            success_rate = (success_count / total_calls) * 100

        return {
            "agent_type": self.agent_type,
            "llm_calls": self.stats["llm_calls"],
            "total_tokens": self.stats["total_tokens"],
            "input_tokens": self.stats["input_tokens"],
            "output_tokens": self.stats["output_tokens"],
            "tool_calls": self._build_tool_summary(),
            "tool_calls_count": len(self.stats["tool_calls"]),
            "total_errors": self.stats["errors"],
            "success_rate": round(success_rate, 2),
            "latency_ms": self.stats["latency_ms"],
            "estimated_cost": self._calculate_cost(),
            "execution_id": self.execution_id,
        }

    def print_summary(self) -> None:
        """Print formatted summary to console"""
        summary = self.get_summary()

        print("\n" + "=" * 50)
        print(f"Agent Execution Summary [{summary['agent_type']}]")
        print("=" * 50)
        print(f"LLM Calls: {summary['llm_calls']}")
        print(f"Tokens: {summary['total_tokens']} (in={summary['input_tokens']}, out={summary['output_tokens']})")
        print(f"Tool Calls: {summary['tool_calls_count']}")
        print(f"Errors: {summary['total_errors']}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Latency: {summary['latency_ms']}ms")
        print(f"Estimated Cost: {summary['estimated_cost']:.4f} CNY")

        if summary['tool_calls']:
            print(f"\nTool Usage:")
            for tool_name, count in summary['tool_calls'].items():
                print(f"  - {tool_name}: {count}x")

        print("=" * 50 + "\n")
