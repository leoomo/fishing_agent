"""
Unified Monitoring Callback - 统一监控回调

适用于所有 Agent 的通用监控组件，提供:
- Token 使用量追踪
- 工具调用计时和分类
- 异步数据库持久化
- 成本估算
"""

import logging
import time
import json
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


# 模型定价 (每 1K tokens，单位: CNY)
MODEL_PRICING = {
    "qwen": {"input": 0.0008, "output": 0.002},
    "zhipu": {"input": 0.001, "output": 0.001},
    "doubao": {"input": 0.0008, "output": 0.002},
    "openai": {"input": 0.015, "output": 0.06},
    "deepseek": {"input": 0.001, "output": 0.002},
}


class MonitoringCallback(BaseCallbackHandler):
    """
    统一监控回调 - 适用于所有 Agent

    特性:
    - 单一回调替代双回调架构
    - 异步非阻塞持久化
    - 多 LLM 提供商 token 提取
    - 工具调用分类和计时

    Usage:
        callback = MonitoringCallback(
            agent_type="fishing",
            model_provider="zhipu",
            user_id=123,
            session_id=456
        )
        agent.invoke({...}, config={"callbacks": [callback]})
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
        初始化监控回调

        Args:
            agent_type: Agent 类型标识 (如 "fishing", "equipment_import")
            model_provider: LLM 提供商 (如 "zhipu", "qwen")
            model_name: 模型名称
            user_id: 用户 ID
            session_id: 会话 ID
            persist: 是否持久化到数据库
            verbose: 是否输出详细日志
        """
        super().__init__()
        self.agent_type = agent_type
        self.model_provider = model_provider
        self.model_name = model_name
        self.user_id = user_id
        self.session_id = session_id
        self.persist = persist
        self.verbose = verbose

        # 执行追踪
        self.execution_id: Optional[int] = None
        self.input_text: str = ""
        self.output_text: str = ""

        self._reset_stats()

    def _reset_stats(self):
        """重置统计数据"""
        self.stats = {
            "llm_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
            "latency_ms": 0,
            "tool_calls": [],
            "llm_logs": [],
        }
        self._current_tool_start: Optional[float] = None
        self._current_tool_name: str = "unknown"
        self._current_tool_input: str = ""

    def set_input(self, text: str):
        """设置用户输入文本"""
        self.input_text = text[:1000] if text else ""

    def reset(self):
        """重置以进行新的执行"""
        self._reset_stats()
        self.execution_id = None
        self.input_text = ""
        self.output_text = ""

    # ========== LLM 回调 ==========

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM 开始生成"""
        self.stats["llm_calls"] += 1
        if self.stats["start_time"] is None:
            self.stats["start_time"] = time.time()

        if self.verbose:
            logger.debug(f"[{self.agent_type}] LLM started (call #{self.stats['llm_calls']})")

    def on_llm_end(self, response: Any, **kwargs) -> None:
        """LLM 完成生成"""
        input_tokens, output_tokens, total_tokens = self._extract_tokens(response)

        self.stats["input_tokens"] += input_tokens
        self.stats["output_tokens"] += output_tokens
        self.stats["total_tokens"] += total_tokens

        self.stats["llm_logs"].append({
            "timestamp": datetime.utcnow(),
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "success": True,
            "error_message": None,
        })

        if self.verbose:
            logger.debug(f"[{self.agent_type}] LLM tokens: in={input_tokens}, out={output_tokens}")

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """LLM 错误"""
        self.stats["errors"] += 1
        self.stats["llm_logs"].append({
            "timestamp": datetime.utcnow(),
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "success": False,
            "error_message": str(error)[:500],
        })
        logger.error(f"[{self.agent_type}] LLM error: {error}")

    # ========== 工具回调 ==========

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """工具开始执行"""
        self._current_tool_name = serialized.get("name", "unknown")
        self._current_tool_start = time.time()
        self._current_tool_input = str(input_str)[:500] if input_str else ""

        if self.verbose:
            logger.debug(f"[{self.agent_type}] Tool started: {self._current_tool_name}")

    def on_tool_end(self, output: str, **kwargs) -> None:
        """工具完成执行"""
        latency_ms = int((time.time() - self._current_tool_start) * 1000) if self._current_tool_start else 0

        self.stats["tool_calls"].append({
            "timestamp": datetime.utcnow(),
            "tool_name": self._current_tool_name,
            "tool_category": self._categorize_tool(self._current_tool_name),
            "input_args": self._current_tool_input,
            "output_result": str(output)[:1000] if output else "",
            "latency_ms": latency_ms,
            "success": True,
            "error_message": None,
        })

        if self.verbose:
            logger.debug(f"[{self.agent_type}] Tool completed: {self._current_tool_name} ({latency_ms}ms)")

    def on_tool_error(self, error: Exception, **kwargs) -> None:
        """工具错误"""
        self.stats["errors"] += 1
        latency_ms = int((time.time() - self._current_tool_start) * 1000) if self._current_tool_start else 0

        self.stats["tool_calls"].append({
            "timestamp": datetime.utcnow(),
            "tool_name": self._current_tool_name,
            "tool_category": self._categorize_tool(self._current_tool_name),
            "input_args": self._current_tool_input,
            "output_result": None,
            "latency_ms": latency_ms,
            "success": False,
            "error_message": str(error)[:500],
        })
        logger.error(f"[{self.agent_type}] Tool error in {self._current_tool_name}: {error}")

    # ========== Chain 回调 ==========

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        """Chain 开始执行"""
        if self.stats["start_time"] is None:
            self.stats["start_time"] = time.time()

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs) -> None:
        """Chain 完成 - 异步持久化"""
        if self.stats["start_time"]:
            self.stats["end_time"] = time.time()
            self.stats["latency_ms"] = int((self.stats["end_time"] - self.stats["start_time"]) * 1000)

        # 提取输出文本
        if isinstance(outputs, dict) and "messages" in outputs:
            messages = outputs["messages"]
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    self.output_text = str(last_msg.content)[:2000]

        # 异步持久化
        if self.persist:
            threading.Thread(
                target=self._persist_execution,
                daemon=True,
                name=f"monitor-persist-{self.agent_type}"
            ).start()

    def on_chain_error(self, error: Exception, **kwargs) -> None:
        """Chain 错误"""
        self.stats["errors"] += 1

        if self.stats["start_time"]:
            self.stats["end_time"] = time.time()
            self.stats["latency_ms"] = int((self.stats["end_time"] - self.stats["start_time"]) * 1000)

        logger.error(f"[{self.agent_type}] Chain error: {error}")

        if self.persist:
            threading.Thread(
                target=self._persist_execution,
                daemon=True,
                name=f"monitor-persist-{self.agent_type}"
            ).start()

    # ========== 持久化 ==========

    def _persist_execution(self):
        """持久化执行数据到数据库（后台线程）"""
        try:
            from apps.api.orm.session import get_db_session
            from apps.api.models.system import (
                AgentExecutionLog, ToolCallLog, LLMLog
            )

            with get_db_session() as session:
                # 创建执行日志
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
                    error_message=None,
                    estimated_cost=self._calculate_cost(),
                    tool_calls_summary=json.dumps(self._build_tool_summary(), ensure_ascii=False),
                )
                session.add(execution)
                session.flush()

                self.execution_id = execution.id

                # 创建工具调用日志
                for tool in self.stats["tool_calls"]:
                    session.add(ToolCallLog(
                        execution_id=execution.id,
                        timestamp=tool["timestamp"],
                        tool_name=tool["tool_name"],
                        tool_category=tool.get("tool_category"),
                        input_args=tool.get("input_args"),
                        output_result=tool.get("output_result"),
                        latency_ms=tool.get("latency_ms"),
                        success=tool.get("success", True),
                        error_message=tool.get("error_message"),
                    ))

                # 创建 LLM 日志
                for llm in self.stats["llm_logs"]:
                    session.add(LLMLog(
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
                    ))

                session.commit()

            if self.verbose:
                logger.info(f"[{self.agent_type}] Persisted execution #{self.execution_id}")

        except Exception as e:
            logger.error(f"[{self.agent_type}] Failed to persist execution: {e}")

    # ========== Token 提取 ==========

    def _extract_tokens(self, response: Any) -> tuple:
        """从 LLM 响应中提取 token 数量（支持多种格式）"""
        input_tokens = output_tokens = total_tokens = 0

        # 方法 1: generations.usage_metadata (LangChain 1.0+)
        if hasattr(response, 'generations') and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, 'message'):
                        msg = gen.message
                        if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                            usage = msg.usage_metadata
                            input_tokens += usage.get('input_tokens', 0)
                            output_tokens += usage.get('output_tokens', 0)
                            total_tokens += usage.get('total_tokens', 0)
                        elif hasattr(msg, 'response_metadata') and msg.response_metadata:
                            meta = msg.response_metadata
                            usage = meta.get('token_usage', meta.get('usage', {}))
                            if usage:
                                input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                                output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                                total_tokens += usage.get('total_tokens', 0)

                    if total_tokens == 0 and hasattr(gen, 'generation_info') and gen.generation_info:
                        usage = gen.generation_info.get('token_usage', gen.generation_info.get('usage', {}))
                        if usage:
                            input_tokens += usage.get('input_tokens', usage.get('prompt_tokens', 0))
                            output_tokens += usage.get('output_tokens', usage.get('completion_tokens', 0))
                            total_tokens += usage.get('total_tokens', 0)

        # 方法 2: llm_output.token_usage (OpenAI 兼容)
        if total_tokens == 0 and hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', response.llm_output.get('usage', {}))
            if usage:
                input_tokens = usage.get('prompt_tokens', usage.get('input_tokens', 0))
                output_tokens = usage.get('completion_tokens', usage.get('output_tokens', 0))
                total_tokens = usage.get('total_tokens', 0)

        # 计算总数
        if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
            total_tokens = input_tokens + output_tokens

        return input_tokens, output_tokens, total_tokens

    # ========== 成本计算 ==========

    def _calculate_cost(self) -> float:
        """计算本次执行的估算成本"""
        return self._calculate_single_cost(self.stats["input_tokens"], self.stats["output_tokens"])

    def _calculate_single_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算单次调用成本"""
        pricing = MODEL_PRICING.get(self.model_provider, {"input": 0.001, "output": 0.001})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    # ========== 辅助方法 ==========

    def _categorize_tool(self, tool_name: str) -> str:
        """根据工具名称分类"""
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
        """构建工具调用统计摘要"""
        summary = {}
        for tool in self.stats["tool_calls"]:
            name = tool.get("tool_name", "unknown")
            summary[name] = summary.get(name, 0) + 1
        return summary

    def get_summary(self) -> Dict[str, Any]:
        """获取执行统计摘要"""
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
        """打印格式化的统计摘要"""
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

    # ========== 手动生命周期方法 (用于非 Agent 调用) ==========

    def start_execution(self):
        """手动开始执行追踪"""
        if self.stats["start_time"] is None:
            self.stats["start_time"] = time.time()

    def end_execution(self):
        """手动结束执行追踪"""
        if self.stats["start_time"] and not self.stats["end_time"]:
            self.stats["end_time"] = time.time()
            self.stats["latency_ms"] = int((self.stats["end_time"] - self.stats["start_time"]) * 1000)

            if self.persist:
                threading.Thread(
                    target=self._persist_execution,
                    daemon=True,
                    name=f"monitor-persist-{self.agent_type}"
                ).start()

    def set_error(self, message: str):
        """设置错误信息"""
        self.stats["errors"] += 1
        logger.error(f"[{self.agent_type}] Error: {message}")

    def set_success(self, success: bool):
        """设置执行成功状态"""
        if not success:
            self.stats["errors"] += 1
