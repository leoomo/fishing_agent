#!/usr/bin/env python3
"""
Callback Handlers - Stats tracking and monitoring
"""

import logging
import time
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler

# 尝试导入 UsageMetadataCallbackHandler（LangChain 1.0+）
try:
    from langchain_core.callbacks import UsageMetadataCallbackHandler
    HAS_USAGE_HANDLER = True
except ImportError:
    HAS_USAGE_HANDLER = False

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
            "input_tokens": 0,
            "output_tokens": 0,
            "tool_calls": {},
            "llm_calls": 0,
            "start_time": None,
            "end_time": None,
            "latency_ms": 0
        }

        # 使用 LangChain 内置的 UsageMetadataCallbackHandler 来跟踪 token
        self._usage_handler = None
        if HAS_USAGE_HANDLER:
            self._usage_handler = UsageMetadataCallbackHandler()

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
        # 尝试多种方式提取 token 使用信息
        total_tokens = 0
        input_tokens = 0
        output_tokens = 0

        # 方式1: LangChain 1.0+ 从 generations 中获取 usage_metadata 或 response_metadata
        if hasattr(response, 'generations') and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    # 从 message 的 usage_metadata 获取
                    if hasattr(gen, 'message'):
                        msg = gen.message
                        # 优先从 usage_metadata 获取
                        if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                            usage = msg.usage_metadata
                            input_tokens += usage.get('input_tokens', 0)
                            output_tokens += usage.get('output_tokens', 0)
                            total_tokens += usage.get('total_tokens', 0)
                        # 从 response_metadata 获取（ChatTongyi 等模型）
                        elif hasattr(msg, 'response_metadata') and msg.response_metadata:
                            meta = msg.response_metadata
                            # 优先检查 token_usage 格式（ChatTongyi/通义千问）
                            if 'token_usage' in meta:
                                usage = meta['token_usage']
                                input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                                output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                                total_tokens += usage.get('total_tokens', 0)
                            # 其他模型的 usage 格式
                            elif 'usage' in meta:
                                usage = meta['usage']
                                input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                                output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                                total_tokens += usage.get('total_tokens', 0)

                    # 从 generation_info 获取
                    if total_tokens == 0 and hasattr(gen, 'generation_info') and gen.generation_info:
                        gen_info = gen.generation_info
                        # 优先检查 token_usage（ChatTongyi 格式）
                        usage = gen_info.get('token_usage', gen_info.get('usage', {}))
                        if usage:
                            input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                            output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                            total_tokens += usage.get('total_tokens', 0)

        # 方式2: 从 llm_output 的 token_usage 获取（OpenAI 兼容）
        if total_tokens == 0 and hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            if token_usage:
                input_tokens = token_usage.get('prompt_tokens', token_usage.get('input_tokens', 0))
                output_tokens = token_usage.get('completion_tokens', token_usage.get('output_tokens', 0))
                total_tokens = token_usage.get('total_tokens', 0)

        # 方式3: 从 llm_output 的 usage 字段获取
        if total_tokens == 0 and hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('usage', {})
            if usage:
                input_tokens = usage.get('prompt_tokens', usage.get('input_tokens', 0))
                output_tokens = usage.get('completion_tokens', usage.get('output_tokens', 0))
                total_tokens = usage.get('total_tokens', 0)

        # 如果有分项但没有总数，计算总数
        if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
            total_tokens = input_tokens + output_tokens

        if total_tokens > 0:
            self.stats["total_tokens"] += total_tokens
            self.stats["input_tokens"] = self.stats.get("input_tokens", 0) + input_tokens
            self.stats["output_tokens"] = self.stats.get("output_tokens", 0) + output_tokens

            if self.verbose:
                logger.debug(f"📊 Tokens: input={input_tokens}, output={output_tokens}, total={total_tokens}")

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

        # 获取 token 统计
        total_tokens = self.stats["total_tokens"]
        input_tokens = self.stats.get("input_tokens", 0)
        output_tokens = self.stats.get("output_tokens", 0)

        # 如果内置回调有数据，合并使用
        if self._usage_handler and hasattr(self._usage_handler, 'usage_metadata'):
            for model_name, usage in self._usage_handler.usage_metadata.items():
                total_tokens += usage.get('total_tokens', 0)
                input_tokens += usage.get('input_tokens', 0)
                output_tokens += usage.get('output_tokens', 0)

        return {
            "total_calls": self.stats["total_calls"],
            "llm_calls": self.stats["llm_calls"],
            "total_errors": self.stats["total_errors"],
            "success_rate": round(success_rate, 2),
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "tool_calls": self.stats["tool_calls"],
            "latency_ms": self.stats["latency_ms"]
        }

    def reset(self) -> None:
        """Reset all statistics"""
        self.stats = {
            "total_calls": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
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

        # Token 统计（显示分项）
        total_tokens = summary['total_tokens']
        input_tokens = summary.get('input_tokens', 0)
        output_tokens = summary.get('output_tokens', 0)
        if total_tokens > 0:
            print(f"Token使用: {total_tokens} (输入: {input_tokens}, 输出: {output_tokens})")
        else:
            print(f"Token使用: 未统计 (模型可能不返回token信息)")

        print(f"执行时长: {summary['latency_ms']}ms")

        if summary['tool_calls']:
            print(f"\n工具调用统计:")
            for tool_name, count in summary['tool_calls'].items():
                print(f"  - {tool_name}: {count}次")

        print("=" * 50 + "\n")


class OutputFormatValidator:
    """
    验证 LLM 输出是否保留了工具的预设格式

    用于检测 LLM 是否遵循系统提示词中的"输出格式规则"，
    确保工具返回的格式化报告被原样展示给用户。
    """

    # 钓鱼报告必须包含的关键标记
    REQUIRED_MARKERS = {
        "🎣": "报告标题",
        "🏆": "综合评分",
        "⏰": "时段推荐",
        "🌤️": "天气条件",
    }

    # 时段推荐至少包含一个排名标记
    RANKING_MARKERS = ["🥇", "🥈", "🥉"]

    def validate_fishing_report(self, content: str, tool_called: str) -> dict:
        """
        验证钓鱼报告格式是否完整

        Args:
            content: LLM 返回的响应内容
            tool_called: 调用的工具名称

        Returns:
            {
                "valid": bool,          # 格式是否有效
                "missing_markers": list, # 缺失的标记列表
                "warnings": list         # 警告信息列表
            }
        """
        # 非钓鱼推荐工具，跳过验证
        if tool_called != "query_fishing_recommendation":
            return {"valid": True, "missing_markers": [], "warnings": []}

        missing = []
        warnings = []

        # 检查必需的标记
        for marker, desc in self.REQUIRED_MARKERS.items():
            if marker not in content:
                missing.append(f"{marker} ({desc})")

        # 检查是否有排名标记（至少有一个）
        has_ranking = any(m in content for m in self.RANKING_MARKERS)
        if not has_ranking:
            missing.append("🥇/🥈/🥉 (时段排名)")

        # 生成警告信息
        if missing:
            warnings = [f"⚠️ LLM 返回缺少关键格式: {m}" for m in missing]

        return {
            "valid": len(missing) == 0,
            "missing_markers": missing,
            "warnings": warnings
        }

    def log_validation_result(self, result: dict) -> None:
        """
        记录验证结果到日志（仅 DEBUG 级别，不向用户显示）

        Args:
            result: validate_fishing_report 的返回值
        """
        if not result["valid"]:
            # 使用 DEBUG 级别，避免在生产环境向用户显示内部验证警告
            for warning in result["warnings"]:
                logger.debug(warning)
            logger.debug(
                "💡 提示: LLM 可能没有遵循'输出格式规则'，"
                "请检查系统提示词是否正确加载"
            )
