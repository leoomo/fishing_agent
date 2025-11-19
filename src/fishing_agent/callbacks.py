#!/usr/bin/env python3
"""
Callback Handlers - Stats tracking and monitoring
"""

import logging
import time
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class FishingAgentCallback(BaseCallbackHandler):
    """
    Callback handler for fishing agent execution tracking

    Tracks:
    - LLM call counts and tokens
    - Tool invocations
    - Errors and exceptions
    - Execution latency
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize callback handler

        Args:
            verbose: Enable verbose logging
        """
        super().__init__()
        self.verbose = verbose
        self.stats = {
            "total_calls": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "tool_calls": {},
            "llm_calls": 0,
            "start_time": None,
            "end_time": None,
            "latency_ms": 0
        }

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts generating"""
        self.stats["llm_calls"] += 1
        self.stats["total_calls"] += 1

        if self.stats["start_time"] is None:
            self.stats["start_time"] = time.time()

        if self.verbose:
            logger.debug(f"🤖 LLM started (call #{self.stats['llm_calls']})")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM finishes generating"""
        # Extract token usage if available
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            total_tokens = token_usage.get('total_tokens', 0)
            self.stats["total_tokens"] += total_tokens

            if self.verbose and total_tokens > 0:
                logger.debug(f"📊 Tokens used: {total_tokens}")

    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Called when LLM encounters an error"""
        self.stats["total_errors"] += 1
        logger.error(f"💥 LLM error: {error}")

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Called when a tool starts execution"""
        tool_name = serialized.get("name", "unknown")

        # Increment tool call counter
        if tool_name not in self.stats["tool_calls"]:
            self.stats["tool_calls"][tool_name] = 0
        self.stats["tool_calls"][tool_name] += 1

        if self.verbose:
            logger.debug(f"🛠️ Tool started: {tool_name}")

    def on_tool_end(
        self,
        output: str,
        **kwargs: Any
    ) -> None:
        """Called when a tool finishes execution"""
        if self.verbose:
            logger.debug(f"✅ Tool completed")

    def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Called when a tool encounters an error"""
        self.stats["total_errors"] += 1
        logger.error(f"💥 Tool error: {error}")

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when a chain starts execution"""
        if self.stats["start_time"] is None:
            self.stats["start_time"] = time.time()

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when a chain finishes execution"""
        if self.stats["start_time"] is not None:
            self.stats["end_time"] = time.time()
            self.stats["latency_ms"] = int(
                (self.stats["end_time"] - self.stats["start_time"]) * 1000
            )

    def on_chain_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Called when a chain encounters an error"""
        self.stats["total_errors"] += 1
        logger.error(f"💥 Chain error: {error}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get execution summary

        Returns:
            Dictionary with execution statistics
        """
        success_rate = 0.0
        if self.stats["total_calls"] > 0:
            success_count = self.stats["total_calls"] - self.stats["total_errors"]
            success_rate = (success_count / self.stats["total_calls"]) * 100

        return {
            "total_calls": self.stats["total_calls"],
            "llm_calls": self.stats["llm_calls"],
            "total_errors": self.stats["total_errors"],
            "success_rate": round(success_rate, 2),
            "total_tokens": self.stats["total_tokens"],
            "tool_calls": self.stats["tool_calls"],
            "latency_ms": self.stats["latency_ms"]
        }

    def reset(self) -> None:
        """Reset all statistics"""
        self.stats = {
            "total_calls": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "tool_calls": {},
            "llm_calls": 0,
            "start_time": None,
            "end_time": None,
            "latency_ms": 0
        }

    def print_summary(self) -> None:
        """Print formatted summary to console"""
        summary = self.get_summary()

        print("\n" + "=" * 50)
        print("🤖 智能体执行汇总")
        print("=" * 50)
        print(f"总调用次数: {summary['total_calls']}")
        print(f"LLM调用: {summary['llm_calls']}")
        print(f"错误数: {summary['total_errors']}")
        print(f"成功率: {summary['success_rate']}%")
        print(f"Token使用: {summary['total_tokens']}")
        print(f"执行时长: {summary['latency_ms']}ms")

        if summary['tool_calls']:
            print(f"\n工具调用统计:")
            for tool_name, count in summary['tool_calls'].items():
                print(f"  - {tool_name}: {count}次")

        print("=" * 50 + "\n")
