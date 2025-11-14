"""
LangChain 智能体日志中间件

提供完整的智能体执行日志记录功能，包括：
- 用户输入和AI回复记录
- 工具调用监控和性能统计
- 错误追踪和调试信息
- 可配置的日志级别和输出方式
"""

import json
import time
import uuid
import os
import logging
import asyncio
from typing import Any, Dict, Optional, List, Callable, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass, asdict

# LangChain imports
if TYPE_CHECKING:
    from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
    from langgraph.runtime import Runtime
    from langchain.agents import AgentState
else:
    # 如果没有安装完整的LangChain，提供基础类型
    AgentMiddleware = object
    ModelRequest = object
    ModelResponse = object
    BaseMessage = object
    AgentState = Dict[str, Any]  # Runtime fallback
    Runtime = Any  # Runtime fallback

from .config import MiddlewareConfig, default_config


@dataclass
class PerformanceMetrics:
    """性能指标 - 支持动态扩展"""
    # 核心性能指标
    request_duration_ms: float = 0.0      # 请求处理时间
    inference_duration_ms: float = 0.0     # 模型推理时间
    response_duration_ms: float = 0.0     # 响应生成时间
    network_duration_ms: float = 0.0      # 网络传输时间

    # 扩展性能指标
    custom_metrics: Optional[Dict[str, Any]] = None  # 自定义指标

    def __post_init__(self):
        if self.custom_metrics is None:
            self.custom_metrics = {}

    def add_metric(self, name: str, value: Any, metric_type: str = "custom", unit: str = ""):
        """动态添加性能指标"""
        self.custom_metrics[name] = {
            "value": value,
            "type": metric_type,
            "unit": unit,
            "timestamp": time.time()
        }

    def get_total_duration(self) -> float:
        """获取总耗时"""
        return max(self.request_duration_ms,
                  self.inference_duration_ms + self.response_duration_ms)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "request_duration_ms": self.request_duration_ms,
            "inference_duration_ms": self.inference_duration_ms,
            "response_duration_ms": self.response_duration_ms,
            "network_duration_ms": self.network_duration_ms,
            "total_duration_ms": self.get_total_duration(),
            "custom_metrics": self.custom_metrics
        }


@dataclass
class ModelCallRecord:
    """模型调用记录 - 增强版（支持性能扩展）"""
    call_id: int
    timestamp: str
    model_name: str
    duration_ms: float
    token_usage: Dict[str, int]
    success: bool
    call_purpose: str = "unknown"  # 调用目的
    intent_category: str = ""  # 意图分类
    call_context_summary: str = ""  # 调用上下文摘要
    key_points: Optional[List[str]] = None  # 关键信息点
    inference_method: str = "position_and_content_analysis"  # 推断方法
    error_message: Optional[str] = None

    # 性能指标扩展字段
    performance_metrics: Optional[PerformanceMetrics] = None
    resource_usage: Optional[Dict[str, Any]] = None  # 资源使用情况

    def __post_init__(self):
        if self.key_points is None:
            self.key_points = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.token_usage:
            self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if self.performance_metrics is None:
            self.performance_metrics = PerformanceMetrics()
        if self.resource_usage is None:
            self.resource_usage = {}

    def get_detailed_performance(self) -> Dict[str, Any]:
        """获取详细的性能信息"""
        return {
            "call_id": self.call_id,
            "model_name": self.model_name,
            "success": self.success,
            "basic_duration_ms": self.duration_ms,
            "performance_metrics": self.performance_metrics.to_dict(),
            "token_efficiency": {
                "tokens_per_second": self._calculate_tokens_per_second(),
                "ms_per_token": self._calculate_ms_per_token()
            },
            "resource_usage": self.resource_usage
        }

    def _calculate_tokens_per_second(self) -> float:
        """计算每秒生成的token数"""
        total_tokens = self.token_usage.get("total_tokens", 0)
        if total_tokens > 0 and self.duration_ms > 0:
            return (total_tokens / self.duration_ms) * 1000
        return 0.0

    def _calculate_ms_per_token(self) -> float:
        """计算每个token的耗时"""
        total_tokens = self.token_usage.get("total_tokens", 0)
        if total_tokens > 0:
            return self.duration_ms / total_tokens
        return 0.0


@dataclass
class ToolCallRecord:
    """工具调用记录 - 增强版（支持性能扩展）"""
    tool_name: str
    tool_args: Dict[str, Any]
    result: Any
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: str = ""

    # 性能指标扩展字段
    performance_metrics: Optional[PerformanceMetrics] = None
    operation_phases: Optional[Dict[str, float]] = None  # 各操作阶段耗时
    cache_hit: bool = False  # 缓存命中状态
    retry_count: int = 0  # 重试次数
    resource_usage: Optional[Dict[str, Any]] = None  # 资源使用情况

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.performance_metrics is None:
            self.performance_metrics = PerformanceMetrics()
        if self.operation_phases is None:
            self.operation_phases = {}
        if self.resource_usage is None:
            self.resource_usage = {}

    def add_phase_duration(self, phase_name: str, duration_ms: float):
        """添加操作阶段耗时"""
        self.operation_phases[phase_name] = duration_ms

    def get_detailed_performance(self) -> Dict[str, Any]:
        """获取详细的性能信息"""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "basic_duration_ms": self.duration_ms,
            "performance_metrics": self.performance_metrics.to_dict(),
            "operation_phases": self.operation_phases,
            "cache_hit": self.cache_hit,
            "retry_count": self.retry_count,
            "resource_usage": self.resource_usage
        }


@dataclass
class AgentExecutionMetrics:
    """智能体执行指标"""
    session_id: str
    timestamp: str
    execution_id: str
    total_duration_ms: float = 0.0
    model_calls_count: int = 0
    tool_calls_count: int = 0
    token_usage: Optional[Dict[str, int]] = None
    errors_count: int = 0
    success: bool = True
    model_name: str = ""
    model_calls: Optional[List[ModelCallRecord]] = None  # 增强的模型调用记录
    tool_calls: Optional[List[ToolCallRecord]] = None    # 工具调用记录

    def __post_init__(self):
        if self.token_usage is None:
            self.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if self.model_calls is None:
            self.model_calls = []
        if self.tool_calls is None:
            self.tool_calls = []

    def add_model_call(self, call_record: ModelCallRecord):
        """添加模型调用记录"""
        self.model_calls.append(call_record)
        self.model_calls_count += 1

    def get_model_calls_summary(self) -> Dict[str, Any]:
        """获取模型调用摘要"""
        if not self.model_calls:
            return {}

        purposes = {}
        intents = {}
        total_duration = 0

        for call in self.model_calls:
            # 统计调用目的
            purpose = call.call_purpose
            purposes[purpose] = purposes.get(purpose, 0) + 1

            # 统计意图分类
            intent = call.intent_category
            intents[intent] = intents.get(intent, 0) + 1

            total_duration += call.duration_ms

        return {
            "total_calls": len(self.model_calls),
            "purposes_distribution": purposes,
            "intents_distribution": intents,
            "average_duration_ms": total_duration / len(self.model_calls) if self.model_calls else 0,
            "total_model_duration_ms": total_duration
        }


class PerformanceTracker:
    """性能追踪器 - 用于跟踪各种操作的耗时和指标"""

    def __init__(self):
        self.active_timings: Dict[str, Dict[str, Any]] = {}
        self.completed_operations: List[Dict[str, Any]] = []
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, Any] = {}

    def start_timing(self, operation_id: str, operation_type: str, metadata: Dict[str, Any] = None):
        """开始计时"""
        self.active_timings[operation_id] = {
            "start_time": time.time(),
            "type": operation_type,
            "metadata": metadata or {}
        }

    def end_timing(self, operation_id: str) -> Optional[float]:
        """结束计时并返回耗时"""
        if operation_id in self.active_timings:
            timing_info = self.active_timings.pop(operation_id)
            duration = (time.time() - timing_info["start_time"]) * 1000

            # 记录完成的操作
            self.completed_operations.append({
                "operation_id": operation_id,
                "type": timing_info["type"],
                "duration_ms": duration,
                "metadata": timing_info["metadata"],
                "timestamp": time.time()
            })

            return duration
        return None

    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: Any):
        """设置仪表值"""
        self.gauges[name] = value

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        # 按类型统计操作耗时
        type_stats = {}
        for op in self.completed_operations[-100:]:  # 最近100个操作
            op_type = op["type"]
            if op_type not in type_stats:
                type_stats[op_type] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "min_duration": float('inf'),
                    "max_duration": 0.0
                }

            stats = type_stats[op_type]
            stats["count"] += 1
            stats["total_duration"] += op["duration_ms"]
            stats["min_duration"] = min(stats["min_duration"], op["duration_ms"])
            stats["max_duration"] = max(stats["max_duration"], op["duration_ms"])

        # 计算平均值
        for stats in type_stats.values():
            if stats["count"] > 0:
                stats["avg_duration"] = stats["total_duration"] / stats["count"]

        return {
            "counters": self.counters,
            "gauges": self.gauges,
            "operation_stats": type_stats,
            "active_operations": len(self.active_timings),
            "completed_operations": len(self.completed_operations)
        }


class MetricRegistry:
    """指标注册表 - 管理所有性能指标的规范"""

    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def register_metric(self, name: str, metric_type: str, description: str = "", unit: str = ""):
        """注册指标"""
        self.metrics[name] = {
            "type": metric_type,  # timing, count, gauge, rate
            "description": description,
            "unit": unit,
            "registered_at": time.time()
        }

    def get_metric_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指标信息"""
        return self.metrics.get(name)

    def list_metrics(self) -> List[str]:
        """列出所有已注册的指标"""
        return list(self.metrics.keys())


# 全局指标注册表
metric_registry = MetricRegistry()

# 注册核心指标
metric_registry.register_metric("model_call_duration", "timing", "模型调用总耗时", "ms")
metric_registry.register_metric("model_inference_duration", "timing", "模型推理耗时", "ms")
metric_registry.register_metric("model_token_usage", "count", "Token使用量", "tokens")
metric_registry.register_metric("tool_call_duration", "timing", "工具调用耗时", "ms")
metric_registry.register_metric("tool_cache_hit_rate", "rate", "工具缓存命中率", "%")


class CallPurposeAnalyzer:
    """调用目的分析器 - 智能推断模型调用的目的和意图"""

    # 调用目的类型定义
    CALL_PURPOSES = {
        "tool_selection": "工具选择",
        "result_generation": "结果生成",
        "intent_understanding": "意图理解",
        "context_analysis": "上下文分析",
        "tool_execution": "工具执行处理",
        "final_response": "最终回复生成",
        "error_handling": "错误处理",
        "unknown": "未知目的"
    }

    # 意图分类定义
    INTENT_CATEGORIES = {
        "weather_query": "天气查询",
        "weather_fishing_query": "钓鱼天气查询",
        "fishing_advice_generation": "钓鱼建议生成",
        "fishing_data_processing": "钓鱼数据处理",
        "advice_generation": "建议生成",
        "data_processing": "数据处理",
        "location_query": "地点查询",
        "time_query": "时间查询",
        "calculation": "计算请求",
        "information_search": "信息搜索",
        "general_conversation": "一般对话",
        "error_recovery": "错误恢复",
        "unknown": "未知意图"
    }

    # 关键词映射
    INTENT_KEYWORDS = {
        "weather_query": ["天气", "气温", "下雨", "晴天", "阴天", "多云", "温度"],
        "weather_fishing_query": ["钓鱼", "钓鱼天气", "适合钓鱼", "钓鱼时间", "钓鱼推荐"],
        "location_query": ["在哪", "位置", "坐标", "地址", "怎么去"],
        "time_query": ["时间", "几点", "什么时候", "明天", "后天", "今天"],
        "calculation": ["计算", "加法", "乘法", "除法", "等于"],
        "information_search": ["搜索", "查找", "信息", "资料", "什么是"]
    }

    @classmethod
    def analyze_call_purpose(cls, messages: List[Any], call_position: int,
                            has_tool_calls: bool, response: Any = None,
                            compiled_patterns: Optional[Dict] = None,
                            execution_context: str = "unknown") -> Dict[str, str]:
        """
        分析模型调用的目的 - 增强版，支持预编译模式和执行阶段感知

        Args:
            messages: 消息列表
            call_position: 调用在对话中的位置（从1开始）
            has_tool_calls: 是否包含工具调用
            response: 模型响应（可选）
            compiled_patterns: 预编译的正则表达式模式（可选）
            execution_context: 执行上下文（tool_selection, result_generation, tool_execution）

        Returns:
            包含调用目的分析的字典
        """
        # 基于调用位置的基础推断
        purpose = cls._infer_purpose_by_position(call_position, has_tool_calls)

        # 如果没有明确提供执行上下文，基于purpose推断
        if execution_context == "unknown":
            execution_context = purpose

        # 基于消息内容和执行上下文的意图分析
        intent_category = cls._analyze_intent_from_messages(messages, call_position, has_tool_calls, execution_context)

        # 提取关键信息点（使用预编译模式）
        key_points = cls._extract_key_points(messages, response, compiled_patterns)

        # 生成上下文摘要
        context_summary = cls._generate_context_summary(messages, purpose, key_points)

        return {
            "call_purpose": purpose,
            "intent_category": intent_category,
            "key_points": key_points,
            "context_summary": context_summary,
            "execution_context": execution_context,
            "inference_method": "enhanced_position_content_analysis"
        }

    @classmethod
    def _infer_purpose_by_position(cls, position: int, has_tool_calls: bool) -> str:
        """基于调用位置推断目的"""
        if position == 1:
            # 首次调用通常是工具选择
            return "tool_selection"
        elif has_tool_calls:
            # 包含工具调用的可能是工具执行处理
            return "tool_execution"
        else:
            # 后续调用通常是结果生成
            return "result_generation"

    @classmethod
    def _analyze_intent_from_messages(cls, messages: List[Any], call_position: int = 1,
                                    has_tool_calls: bool = False, execution_context: str = "unknown") -> str:
        """从消息中分析用户意图 - 增强版，支持执行阶段感知"""
        if not messages:
            return "unknown"

        # 获取最新的用户消息
        user_message = None
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'human':
                user_message = msg
                break
            elif hasattr(msg, '__class__') and 'HumanMessage' in str(msg.__class__):
                user_message = msg
                break

        if not user_message or not hasattr(user_message, 'content'):
            return "unknown"

        content = str(user_message.content).lower()

        # 基于执行阶段和上下文的精细化意图分析
        if execution_context == "tool_selection":
            # 工具选择阶段：更注重查询类意图
            if "钓鱼" in content and any(keyword in content for keyword in ["天气", "时间", "什么时候", "明天", "后天"]):
                return "weather_fishing_query"
            elif any(keyword in content for keyword in ["天气", "气温", "下雨", "晴天"]):
                return "weather_query"
        elif execution_context == "result_generation":
            # 结果生成阶段：更注重分析和建议类意图
            if "钓鱼" in content:
                return "fishing_advice_generation"
            elif any(keyword in content for keyword in ["建议", "推荐", "分析"]):
                return "advice_generation"
        elif execution_context == "tool_execution":
            # 工具执行阶段：数据处理类意图
            if "钓鱼" in content:
                return "fishing_data_processing"
            else:
                return "data_processing"

        # 基于关键词匹配意图（保持向后兼容）
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            if any(keyword in content for keyword in keywords):
                return intent

        # 特殊检查：钓鱼相关查询（只在其他检查都未匹配时使用）
        if "钓鱼" in content:
            # 默认根据执行上下文决定钓鱼意图
            if execution_context == "result_generation":
                return "fishing_advice_generation"
            else:
                return "weather_fishing_query"

        return "general_conversation"

    @classmethod
    def _extract_key_points(cls, messages: List[Any], response: Any = None, compiled_patterns: Optional[Dict] = None) -> List[str]:
        """提取关键信息点 - 优化版本，支持预编译模式"""
        key_points = []

        # 从用户消息中提取关键词
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                content = str(msg.content)

                # 使用预编译模式（如果提供）
                if compiled_patterns:
                    # 时间相关关键词
                    for word in compiled_patterns.get('time_words', []):
                        if word in content:
                            key_points.append(word)

                    # 地点相关关键词（使用预编译正则）
                    location_regex = compiled_patterns.get('location')
                    if location_regex:
                        locations = location_regex.findall(content)
                        key_points.extend(locations)

                    # 活动相关关键词
                    for word in compiled_patterns.get('activity_words', []):
                        if word in content:
                            key_points.append(word)
                else:
                    # 回退到原始模式
                    # 时间相关关键词
                    time_words = ["明天", "后天", "今天", "早上", "上午", "下午", "晚上", "夜间"]
                    for word in time_words:
                        if word in content:
                            key_points.append(word)

                    # 地点相关关键词 - 修复地名截断问题
                    import re
                    # 添加完整的中国行政区县名称，避免截断
                    location_pattern = r'(北京|上海|广州|深圳|杭州|南京|苏州|成都|武汉|西安|郑州|青岛|大连|厦门|无锡|福州|济南|哈尔滨|沈阳|长春|石家庄|太原|呼和浩特|银川|西宁|乌鲁木齐|兰州|西安|成都|贵阳|昆明|南宁|拉萨|杭州|合肥|南昌|长沙|武汉|郑州|济南|青岛|南京|苏州|上海|福州|厦门|台北|香港|澳门|天津|重庆|朝阳区|海淀区|西城区|东城区|丰台区|石景山区|通州区|顺义区|昌平区|大兴区|房山区|门头沟区|怀柔区|平谷区|密云区|延庆区|余杭区|西湖区|拱墅区|滨江区|萧山区|临平区|钱塘区|富阳区|临安区|建德市|桐庐县|淳安县|浦东新区|黄浦区|徐汇区|长宁区|静安区|普陀区|虹口区|杨浦区|闵行区|宝山区|嘉定区|青浦区|松江区|金山区|奉贤区|崇明区)'
                    locations = re.findall(location_pattern, content)
                    key_points.extend(locations)

                    # 活动相关关键词
                    activity_words = ["钓鱼", "天气", "查询", "计算", "搜索"]
                    for word in activity_words:
                        if word in content:
                            key_points.append(word)

        # 去重并按长度排序，优先保留更长的关键点（避免地名截断）
        key_points = list(set(key_points))

        # 按长度降序排序，优先选择更长的关键点（完整地名）
        key_points.sort(key=len, reverse=True)

        # 限制数量，但确保重要信息不被丢弃
        key_points = key_points[:8]  # 增加到8个以保留更多关键信息
        return key_points

    @classmethod
    def _generate_context_summary(cls, messages: List[Any], purpose: str, key_points: List[str]) -> str:
        """生成调用上下文摘要"""
        if not messages:
            return "空消息上下文"

        # 获取用户消息内容
        user_content = ""
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                user_content = str(msg.content)[:100]  # 限制长度
                break

        # 生成摘要
        purpose_desc = cls.CALL_PURPOSES.get(purpose, purpose)

        if key_points:
            key_points_str = "、".join(key_points[:3])  # 最多显示3个关键点
            summary = f"{purpose_desc}，关键信息：{key_points_str}"
        else:
            summary = f"{purpose_desc}，用户输入：{user_content}"

        return summary[:200]  # 限制摘要长度


class SensitiveDataFilter:
    """敏感数据过滤器"""

    SENSITIVE_PATTERNS = [
        ('api_key', r'(?i)api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\\s]{10,})'),
        ('password', r'(?i)password["\']?\s*[:=]\s*["\']?([^"\'\\s]{6,})'),
        ('token', r'(?i)token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{10,})'),
        ('secret', r'(?i)secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{10,})'),
    ]

    @classmethod
    def filter_text(cls, text: str) -> str:
        """过滤文本中的敏感信息"""
        import re
        filtered_text = text
        for pattern_name, pattern in cls.SENSITIVE_PATTERNS:
            filtered_text = re.sub(pattern, f'{pattern_name}=***FILTERED***', filtered_text)
        return filtered_text

    @classmethod
    def filter_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """递归过滤字典中的敏感信息"""
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in ['api_key', 'password', 'token', 'secret', 'key']):
                filtered[key] = "***FILTERED***"
            elif isinstance(value, dict):
                filtered[key] = cls.filter_dict(value)
            elif isinstance(value, str):
                filtered[key] = cls.filter_text(value)
            else:
                filtered[key] = value
        return filtered


class AgentLoggingMiddleware(AgentMiddleware):
    """
    LangChain 智能体日志中间件

    提供完整的智能体执行日志记录和性能监控功能。
    """

    def __init__(self, config: Optional[MiddlewareConfig] = None, logger: Optional[logging.Logger] = None):
        """
        初始化日志中间件

        Args:
            config: 中间件配置，如果为None则使用默认配置
            logger: 自定义logger，如果为None则创建默认logger
        """
        self.config = config or default_config
        self.config.validate()

        # 设置logger
        self.logger = logger or self._setup_logger()

        # 中间件名称
        self.name = "AgentLoggingMiddleware"

        # 状态架构（LangChain中间件接口要求）
        self.state_schema = dict  # 使用内置的dict类作为状态架构

        # 会话管理
        self.session_id = self._generate_session_id()
        self.execution_start_time = None

        # 模型调用追踪
        self.current_request_model_calls = 0  # 当前请求的模型调用次数
        self.total_model_calls = 0  # 会话总模型调用次数
        self.request_start_time = None  # 当前请求开始时间

        # 执行统计
        self.metrics = AgentExecutionMetrics(
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            execution_id=str(uuid.uuid4())
        )

        # 工具调用记录
        self.tool_calls: List[ToolCallRecord] = []

        # 敏感数据过滤器
        self.sensitive_filter = SensitiveDataFilter() if self.config.enable_sensitive_filter else None

        # 性能优化：缓存机制
        self._purpose_analysis_cache = {}
        self._max_cache_size = 100

        # 性能优化：预编译正则表达式
        self._compiled_patterns = {}
        if self.config.enable_call_purpose_analysis:
            self._compile_intent_patterns()

        # 性能追踪器
        self.performance_tracker = PerformanceTracker()

        self.logger.info(f"🔧 AgentLoggingMiddleware 初始化完成 (性能增强版)", extra={
            'session_id': self.session_id,
            'config': self.config.to_dict(),
            'enhanced_features': {
                'call_purpose_analysis': self.config.enable_call_purpose_analysis,
                'enhanced_console_output': self.config.show_enhanced_console_output,
                'model_call_detail_level': self.config.model_call_detail_level,
                'performance_tracking': True,
                'extended_metrics': True
            }
        })

    def _compile_intent_patterns(self):
        """预编译意图识别的正则表达式以提高性能"""
        import re

        # 预编译地点识别正则 - 修复地名截断问题
        location_pattern = r'(北京|上海|广州|深圳|杭州|南京|苏州|成都|武汉|西安|郑州|青岛|大连|厦门|无锡|福州|济南|哈尔滨|沈阳|长春|石家庄|太原|呼和浩特|银川|西宁|乌鲁木齐|兰州|西安|成都|贵阳|昆明|南宁|拉萨|杭州|合肥|南昌|长沙|武汉|郑州|济南|青岛|南京|苏州|上海|福州|厦门|台北|香港|澳门|天津|重庆|朝阳区|海淀区|西城区|东城区|丰台区|石景山区|通州区|顺义区|昌平区|大兴区|房山区|门头沟区|怀柔区|平谷区|密云区|延庆区|余杭区|西湖区|拱墅区|滨江区|萧山区|临平区|钱塘区|富阳区|临安区|建德市|桐庐县|淳安县|浦东新区|黄浦区|徐汇区|长宁区|静安区|普陀区|虹口区|杨浦区|闵行区|宝山区|嘉定区|青浦区|松江区|金山区|奉贤区|崇明区)'
        self._compiled_patterns['location'] = re.compile(location_pattern)

        # 预编译时间词识别列表
        time_words = ["明天", "后天", "今天", "早上", "上午", "下午", "晚上", "夜间"]
        self._compiled_patterns['time_words'] = time_words

        # 预编译活动词识别列表
        activity_words = ["钓鱼", "天气", "查询", "计算", "搜索"]
        self._compiled_patterns['activity_words'] = activity_words

    def start_request_tracking(self, user_input: str = ""):
        """开始新的请求追踪"""
        import time

        self.request_start_time = time.time()
        self.current_request_model_calls = 0

        if self.config.show_enhanced_console_output and self.config.log_to_console:
            # 显示请求开始信息
            preview = user_input[:50] + "..." if len(user_input) > 50 else user_input
            print(f"\n🚀 新请求开始 [#{self.total_model_calls + 1}]")
            print(f"📝 用户输入: {preview}")
            print(f"⏱️  开始时间: {time.strftime('%H:%M:%S')}")
            print(f"🎯 历史总调用: {self.total_model_calls} 次")
            print("─" * 80)

    def end_request_tracking(self):
        """结束请求追踪并显示统计"""
        import time

        if self.request_start_time and self.config.show_enhanced_console_output and self.config.log_to_console:
            request_duration = (time.time() - self.request_start_time) * 1000

            print("─" * 80)
            print(f"✅ 请求完成 | 本次调用: {self.current_request_model_calls} 次 | 累计: {self.total_model_calls} 次")

            if self.current_request_model_calls > 0:
                avg_duration = request_duration / self.current_request_model_calls
                print(f"⏱️  总耗时: {request_duration:.1f}ms | 平均: {avg_duration:.1f}ms/次")

                # 显示调用效率评级
                if self.current_request_model_calls == 1:
                    efficiency = "🟢 优秀 (单次调用)"
                elif self.current_request_model_calls <= 2:
                    efficiency = "🟡 良好 (多次调用)"
                else:
                    efficiency = "🔴 需优化 (多次调用)"
                print(f"📊 效率评级: {efficiency}")

            print(f"🕐 完成时间: {time.strftime('%H:%M:%S')}\n")

        self.request_start_time = None
        self.current_request_model_calls = 0

    def _get_purpose_analysis_cache_key(self, messages_str: str, call_position: int,
                                   has_tool_calls: bool, execution_context: str = "unknown") -> str:
        """生成目的分析缓存键 - 增强版，包含执行上下文和消息类型"""
        import hashlib

        # 获取更详细的上下文信息用于缓存键
        try:
            # 提取消息类型分布
            message_types = []
            msg_count = 0

            # 简单的消息解析来获取类型信息
            if messages_str:
                # 检查是否包含AI回复、工具调用等标识
                if 'AIMessage' in messages_str or 'ai' in messages_str.lower():
                    message_types.append('ai')
                if 'HumanMessage' in messages_str or 'human' in messages_str.lower():
                    message_types.append('human')
                if 'ToolMessage' in messages_str or 'tool' in messages_str.lower():
                    message_types.append('tool')

                # 计算消息数量（简化版）
                msg_count = messages_str.count('content') or 1

            # 构建更精确的缓存键
            context_info = {
                'content_hash': hashlib.md5(messages_str.encode()).hexdigest()[:8],
                'position': call_position,
                'has_tools': has_tool_calls,
                'context': execution_context,
                'msg_types': sorted(message_types),
                'msg_count': msg_count
            }

            # 生成缓存键
            cache_content = f"{context_info['content_hash']}_{context_info['position']}_{context_info['has_tools']}_{context_info['context']}_{context_info['msg_count']}_{'_'.join(context_info['msg_types'])}"

            return hashlib.md5(cache_content.encode()).hexdigest()[:16]

        except Exception as e:
            # 如果出错，回退到简单版本
            content = f"{messages_str}_{call_position}_{has_tool_calls}_{execution_context}"
            return hashlib.md5(content.encode()).hexdigest()[:16]

    def _cache_purpose_analysis(self, cache_key: str, analysis: Dict[str, Any]):
        """缓存目的分析结果"""
        if len(self._purpose_analysis_cache) >= self._max_cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self._purpose_analysis_cache))
            del self._purpose_analysis_cache[oldest_key]

        self._purpose_analysis_cache[cache_key] = analysis

    def _get_cached_purpose_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的目的分析结果"""
        return self._purpose_analysis_cache.get(cache_key)

    def _setup_logger(self) -> logging.Logger:
        """设置专用的agent日志logger"""
        logger = logging.getLogger('agent.middleware')
        logger.setLevel(getattr(logging, self.config.log_level))

        # 避免重复添加handler
        if not logger.handlers:
            # 创建formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 控制台输出
            if self.config.log_to_console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

            # 文件输出
            if self.config.log_to_file:
                # 确保日志目录存在
                os.makedirs(os.path.dirname(self.config.log_file_path), exist_ok=True)
                file_handler = logging.FileHandler(self.config.log_file_path)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        return logger

    def _generate_session_id(self) -> str:
        """生成会话ID"""
        if self.config.session_id_generator == "uuid":
            return str(uuid.uuid4())
        elif self.config.session_id_generator == "timestamp":
            return str(int(time.time()))
        else:
            return f"session_{int(time.time())}"

    def _log_with_context(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """带上下文的日志记录"""
        log_extra = {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id,
            'component': 'AgentMiddleware'
        }

        if extra:
            log_extra.update(extra)

        # 过滤敏感信息
        if self.sensitive_filter and extra:
            log_extra = self.sensitive_filter.filter_dict(log_extra)

        # 截断过长的日志
        if len(message) > self.config.max_log_length:
            message = message[:self.config.max_log_length] + "...[TRUNCATED]"

        getattr(self.logger, level.lower())(message, extra=log_extra)

    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """格式化消息列表"""
        if not messages:
            return "[]"

        formatted = []
        for msg in messages:
            msg_dict = {
                'type': msg.__class__.__name__,
                'content': str(msg.content)[:200] + ("..." if len(str(msg.content)) > 200 else "")
            }

            # 添加工具调用信息
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                msg_dict['tool_calls'] = [
                    {
                        'name': tc.get('name', 'unknown'),
                        'args': tc.get('args', {})
                    }
                    for tc in msg.tool_calls
                ]

            formatted.append(msg_dict)

        return json.dumps(formatted, ensure_ascii=False, indent=2)

    def _extract_model_name(self, request: ModelRequest) -> str:
        """提取模型名称"""
        if hasattr(request, 'model') and request.model:
            if hasattr(request.model, 'model_name'):
                return request.model.model_name
            elif hasattr(request.model, 'name'):
                return request.model.name
            elif isinstance(request.model, str):
                return request.model
        return "unknown"

    def before_agent(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """智能体执行前的处理"""
        if not self.execution_start_time:
            self.execution_start_time = time.time()

        # 记录智能体开始执行
        self._log_with_context('INFO', "🚀 智能体开始执行", {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id
        })

        return None

    def after_agent(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """智能体执行后的处理"""
        if self.execution_start_time:
            total_duration = (time.time() - self.execution_start_time) * 1000
            self.metrics.total_duration_ms = total_duration
            self.metrics.success = True

        # 记录智能体执行完成
        self._log_with_context('INFO', "✅ 智能体执行完成", {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id,
            'total_duration_ms': self.metrics.total_duration_ms,
            'model_calls': self.metrics.model_calls_count,
            'tool_calls': self.metrics.tool_calls_count
        })

        return None

    async def abefore_agent(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """异步智能体执行前的处理"""
        if not self.execution_start_time:
            self.execution_start_time = time.time()

        # 记录智能体开始执行
        self._log_with_context('INFO', "🚀 智能体开始执行 (异步)", {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id
        })

        return None

    async def aafter_agent(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """异步智能体执行后的处理"""
        if self.execution_start_time:
            total_duration = (time.time() - self.execution_start_time) * 1000
            self.metrics.total_duration_ms = total_duration
            self.metrics.success = True

        # 记录智能体执行完成
        self._log_with_context('INFO', "✅ 智能体执行完成 (异步)", {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id,
            'total_duration_ms': self.metrics.total_duration_ms,
            'model_calls': self.metrics.model_calls_count,
            'tool_calls': self.metrics.tool_calls_count
        })

        return None

    def before_model(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """模型调用前的处理"""
        if not self.execution_start_time:
            self.execution_start_time = time.time()

        self.metrics.model_calls_count += 1

        # 记录输入信息
        messages = state.get('messages', [])

        self._log_with_context('INFO', "🚀 开始模型调用", {
            'messages_count': len(messages),
            'messages_preview': self._format_messages(messages),
            'runtime_context': str(runtime.context) if hasattr(runtime, 'context') else None
        })

        return None

    def wrap_model_call(self, request: ModelRequest, handler: Callable) -> ModelResponse:
        """包装模型调用，记录详细信息和调用目的分析（性能增强版）"""
        # 生成操作ID用于性能追踪
        operation_id = f"model_call_{self.metrics.model_calls_count + 1}_{int(time.time() * 1000)}"

        # 开始性能追踪
        request_start_time = time.time()
        self.performance_tracker.start_timing(operation_id, "model_call", {
            "model_name": self._extract_model_name(request),
            "call_position": self.metrics.model_calls_count + 1
        })

        self.metrics.model_name = self._extract_model_name(request)

        # 获取调用信息用于目的分析
        messages = getattr(request, 'messages', [])
        call_position = self.metrics.model_calls_count + 1  # 调用位置（从1开始）

        try:
            # 开始推理阶段计时
            inference_start_time = time.time()

            # 执行模型调用
            response = handler(request)

            # 结束推理阶段计时
            inference_duration_ms = (time.time() - inference_start_time) * 1000

            # 计算总耗时
            total_duration_ms = (time.time() - request_start_time) * 1000
            self.metrics.total_duration_ms += total_duration_ms

            # 提取token使用信息 (增强兼容性)
            token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            # 尝试多种方式获取Token使用量
            token_extracted = False

            # 方法1: usage_metadata (标准LangChain)
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_usage.update(response.usage_metadata)
                token_extracted = True
                self.metrics.token_usage.update(response.usage_metadata)

            # 方法2: response.usage (某些模型提供商)
            elif hasattr(response, 'usage') and response.usage:
                if hasattr(response.usage, 'prompt_tokens'):
                    token_usage["prompt_tokens"] = response.usage.prompt_tokens
                if hasattr(response.usage, 'completion_tokens'):
                    token_usage["completion_tokens"] = response.usage.completion_tokens
                if hasattr(response.usage, 'total_tokens'):
                    token_usage["total_tokens"] = response.usage.total_tokens
                token_extracted = True
                self.metrics.token_usage.update(token_usage)

            # 方法3: 从response对象中直接查找 (兼容更多提供商)
            else:
                # 尝试从response.response_metadata中查找
                if hasattr(response, 'response_metadata') and response.response_metadata:
                    if 'token_usage' in response.response_metadata:
                        token_usage.update(response.response_metadata['token_usage'])
                        token_extracted = True
                        self.metrics.token_usage.update(token_usage)
                    elif 'usage' in response.response_metadata:
                        token_usage.update(response.response_metadata['usage'])
                        token_extracted = True
                        self.metrics.token_usage.update(token_usage)

            # 方法4: 估算Token数量 (基于文本长度)
            if not token_extracted:
                # 如果无法获取Token，进行简单估算
                messages = getattr(request, 'messages', [])
                if messages:
                    # 估算输入Token (中文约1.5字符=1Token, 英文约4字符=1Token)
                    input_text = ""
                    for msg in messages:
                        if hasattr(msg, 'content'):
                            input_text += str(msg.content) + " "

                    # 简单估算：中文字符 / 1.5 + 英文单词 / 1
                    chinese_chars = len([c for c in input_text if '\u4e00' <= c <= '\u9fff'])
                    other_chars = len(input_text) - chinese_chars

                    estimated_input_tokens = int(chinese_chars / 1.5 + other_chars / 4)

                    # 估算输出Token (假设输出长度与输入相似)
                    estimated_output_tokens = estimated_input_tokens // 3

                    token_usage = {
                        "prompt_tokens": estimated_input_tokens,
                        "completion_tokens": estimated_output_tokens,
                        "total_tokens": estimated_input_tokens + estimated_output_tokens,
                        "estimated": True  # 标记这是估算值
                    }
                    self.metrics.token_usage.update(token_usage)

            # 检查是否包含工具调用
            has_tool_calls = False
            if hasattr(response, 'tool_calls') and response.tool_calls:
                has_tool_calls = True

            # 分析调用目的（如果启用）
            purpose_analysis = {}
            if self.config.enable_call_purpose_analysis:
                # 首先检查是否已经有意图分析结果（来自意图中间件）
                existing_intent_analysis = None
                if hasattr(request, 'metadata') and request.metadata:
                    existing_intent_analysis = request.metadata.get('intent_analysis')

                if existing_intent_analysis:
                    # 使用已有的意图分析结果，避免重复分析
                    purpose_analysis = existing_intent_analysis
                else:
                    # 推断执行上下文
                    execution_context = CallPurposeAnalyzer._infer_purpose_by_position(call_position, has_tool_calls)

                    # 尝试从缓存获取分析结果
                    messages_str = str([str(getattr(msg, 'content', '')) for msg in messages[-3:]])  # 只使用最近3条消息生成缓存键
                    cache_key = self._get_purpose_analysis_cache_key(messages_str, call_position, has_tool_calls, execution_context)

                    cached_analysis = self._get_cached_purpose_analysis(cache_key)
                    if cached_analysis:
                        purpose_analysis = cached_analysis
                    else:
                        # 执行分析并缓存结果
                        purpose_analysis = CallPurposeAnalyzer.analyze_call_purpose(
                            messages=messages,
                            call_position=call_position,
                            has_tool_calls=has_tool_calls,
                            response=response,
                            compiled_patterns=self._compiled_patterns,
                            execution_context=execution_context
                        )
                        self._cache_purpose_analysis(cache_key, purpose_analysis)

            # 创建增强的性能指标
            performance_metrics = PerformanceMetrics(
                request_duration_ms=total_duration_ms,
                inference_duration_ms=inference_duration_ms,
                response_duration_ms=total_duration_ms - inference_duration_ms
            )

            # 添加详细性能指标
            performance_metrics.add_metric("messages_count", len(messages), "count")
            performance_metrics.add_metric("tokens_per_second",
                                          (total_duration_ms > 0) and (token_usage.get("total_tokens", 0) / total_duration_ms * 1000) or 0,
                                          "rate", "tokens/sec")
            performance_metrics.add_metric("response_size", len(str(response)), "count", "chars")

            # 记录资源使用情况
            resource_usage = {
                "memory_usage_mb": 0,  # 可以集成实际的内存监控
                "cpu_usage_percent": 0,  # 可以集成实际的CPU监控
                "network_io_bytes": len(str(request)) + len(str(response))  # 简单的网络IO估算
            }

            # 创建增强的模型调用记录
            call_record = ModelCallRecord(
                call_id=call_position,
                timestamp=datetime.now().isoformat(),
                model_name=self.metrics.model_name,
                duration_ms=total_duration_ms,  # 保持向后兼容
                token_usage=token_usage.copy(),
                success=True,
                call_purpose=purpose_analysis.get("call_purpose", "unknown"),
                intent_category=purpose_analysis.get("intent_category", ""),
                call_context_summary=purpose_analysis.get("context_summary", ""),
                key_points=purpose_analysis.get("key_points", []),
                inference_method=purpose_analysis.get("inference_method", "position_and_content_analysis"),
                performance_metrics=performance_metrics,
                resource_usage=resource_usage
            )

            # 结束性能追踪
            self.performance_tracker.end_timing(operation_id)
            self.performance_tracker.increment_counter("model_calls_success")

            # 添加到指标中
            self.metrics.add_model_call(call_record)

            # 记录增强的请求信息
            self._log_enhanced_model_request(request, purpose_analysis)

            # 记录增强的响应信息
            self._log_enhanced_model_response(response, call_record, purpose_analysis)

            return response

        except Exception as e:
            self.metrics.errors_count += 1
            self.metrics.success = False
            error_duration_ms = (time.time() - request_start_time) * 1000

            # 结束性能追踪
            self.performance_tracker.end_timing(operation_id)

            # 即使失败也创建调用记录
            purpose_analysis = {}
            if self.config.enable_call_purpose_analysis:
                purpose_analysis = CallPurposeAnalyzer.analyze_call_purpose(
                    messages=messages,
                    call_position=call_position,
                    has_tool_calls=False,
                    response=None,
                    compiled_patterns=self._compiled_patterns
                )

            # 创建失败记录的性能指标
            error_performance_metrics = PerformanceMetrics(
                request_duration_ms=error_duration_ms,
                inference_duration_ms=error_duration_ms  # 整个过程都算推理时间
            )
            error_performance_metrics.add_metric("error_type", type(e).__name__, "custom")
            error_performance_metrics.add_metric("error_recovery", False, "boolean")

            error_call_record = ModelCallRecord(
                call_id=call_position,
                timestamp=datetime.now().isoformat(),
                model_name=self.metrics.model_name,
                duration_ms=error_duration_ms,
                token_usage=self.metrics.token_usage.copy(),
                success=False,
                call_purpose=purpose_analysis.get("call_purpose", "error_handling"),
                intent_category=purpose_analysis.get("intent_category", "error_recovery"),
                call_context_summary=purpose_analysis.get("context_summary", "模型调用失败"),
                key_points=purpose_analysis.get("key_points", []),
                inference_method=purpose_analysis.get("inference_method", "position_and_content_analysis"),
                error_message=str(e),
                performance_metrics=error_performance_metrics
            )

            self.metrics.add_model_call(error_call_record)

            # 记录错误信息
            self._log_with_context('ERROR', f"❌ 模型调用失败: {str(e)}", {
                'duration_ms': round(error_duration_ms, 2),
                'error_type': type(e).__name__,
                'error_details': str(e),
                'call_purpose': error_call_record.call_purpose,
                'call_id': call_position
            })

            raise

    def _log_enhanced_model_request(self, request: ModelRequest, purpose_analysis: Dict[str, str]):
        """记录增强的模型请求信息"""
        messages = getattr(request, 'messages', [])

        # 构建易读的控制台输出（如果启用增强输出）
        if self.config.show_enhanced_console_output and purpose_analysis:
            purpose_desc = CallPurposeAnalyzer.CALL_PURPOSES.get(
                purpose_analysis.get("call_purpose", "unknown"),
                "未知目的"
            )

            key_points = purpose_analysis.get("key_points", [])
            key_points_str = "、".join(key_points[:3]) if key_points else "无"

            console_msg = f"🤖 模型调用 #{self.metrics.model_calls_count + 1} [{purpose_desc}]"

            if self.config.log_to_console:
                print(f"\n{console_msg}")
                print(f"├── 目的: {purpose_desc}")
                print(f"├── 意图: {CallPurposeAnalyzer.INTENT_CATEGORIES.get(purpose_analysis.get('intent_category', ''), purpose_analysis.get('intent_category', ''))}")
                if key_points:
                    print(f"├── 关键点: [{key_points_str}]")
                print(f"└── 模型: {self.metrics.model_name}")

        # 记录调试信息
        self._log_with_context('DEBUG', "📤 模型请求详情", {
            'call_id': self.metrics.model_calls_count + 1,
            'model': self.metrics.model_name,
            'tools_count': len(getattr(request, 'tools', [])),
            'messages_count': len(messages),
            'call_purpose': purpose_analysis.get("call_purpose"),
            'intent_category': purpose_analysis.get("intent_category"),
            'key_points': key_points,
            'context_summary': purpose_analysis.get("context_summary", "")[:100]
        })

    def _log_enhanced_model_response(self, response: ModelResponse, call_record: ModelCallRecord, purpose_analysis: Dict[str, str]):
        """记录增强的模型响应信息"""

        # 构建易读的控制台输出（如果启用增强输出）
        if self.config.show_enhanced_console_output:
            purpose_desc = CallPurposeAnalyzer.CALL_PURPOSES.get(call_record.call_purpose, call_record.call_purpose)

            # 获取详细性能信息
            perf_metrics = call_record.performance_metrics
            total_duration = perf_metrics.get_total_duration()
            inference_duration = perf_metrics.inference_duration_ms
            tokens_per_sec = call_record._calculate_tokens_per_second()

            if self.config.log_to_console:
                # 更新调用计数
                self.current_request_model_calls += 1
                self.total_model_calls += 1

                # 选择合适的emoji
                if call_record.call_purpose == "tool_selection":
                    emoji = "🎯"
                elif call_record.call_purpose == "result_generation":
                    emoji = "✨"
                elif call_record.call_purpose == "tool_execution":
                    emoji = "⚙️"
                else:
                    emoji = "⚡"

                # 显示调用次数和性能信息
                call_info = f"第{self.total_model_calls}次"
                if self.current_request_model_calls > 1:
                    call_info += f" (本次第{self.current_request_model_calls}次)"

                # 检查Token是否为估算值
                total_tokens = call_record.token_usage.get('total_tokens', 0)
                is_estimated = call_record.token_usage.get('estimated', False)
                token_display = f"{total_tokens}{' (估算)' if is_estimated else ''}"

                print(f"{emoji} 模型调用[{call_info}]: {total_duration:.1f}ms | Tokens: {token_display} | 速率: {tokens_per_sec:.1f} t/s")

                # 显示详细性能分解
                if total_duration > 100:  # 只为较慢的调用显示详细信息
                    print(f"├── 推理: {inference_duration:.1f}ms | 响应: {perf_metrics.response_duration_ms:.1f}ms")
                    if perf_metrics.custom_metrics.get("tokens_per_second"):
                        print(f"├── 效率: {tokens_per_sec:.1f} tokens/sec | {call_record._calculate_ms_per_token():.2f} ms/token")

                    if call_record.resource_usage.get("network_io_bytes", 0) > 0:
                        network_kb = call_record.resource_usage["network_io_bytes"] / 1024
                        print(f"├── 网络: {network_kb:.1f}KB")

                if call_record.key_points:
                    print(f"└── 摘要: {call_record.call_context_summary[:80]}...")

        # 记录完整的响应信息（包含详细性能指标）
        self._log_with_context('INFO', "📥 模型响应详情", {
            'call_id': call_record.call_id,
            'call_purpose': call_record.call_purpose,
            'purpose_desc': purpose_desc,
            'basic_duration_ms': round(call_record.duration_ms, 2),
            'detailed_performance': call_record.performance_metrics.to_dict(),
            'token_usage': call_record.token_usage,
            'token_efficiency': {
                'tokens_per_second': call_record._calculate_tokens_per_second(),
                'ms_per_token': call_record._calculate_ms_per_token()
            },
            'intent_category': call_record.intent_category,
            'key_points': call_record.key_points,
            'context_summary': call_record.call_context_summary,
            'resource_usage': call_record.resource_usage,
            'success': call_record.success,
            'response_preview': str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
        })

    def wrap_tool_call(self, request, handler) -> Any:
        """包装工具调用，记录工具执行详情（性能增强版）"""
        if not self.config.enable_tool_tracking:
            return handler(request)

        # 提取工具信息
        tool_name = "unknown"
        tool_args = {}

        if hasattr(request, 'tool_call'):
            tool_call = request.tool_call
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
        elif hasattr(request, 'name'):
            tool_name = request.name
            tool_args = getattr(request, 'args', {})

        # 生成操作ID用于性能追踪
        tool_operation_id = f"tool_{tool_name}_{int(time.time() * 1000)}"

        # 开始性能追踪
        self.performance_tracker.start_timing(tool_operation_id, "tool_call", {
            "tool_name": tool_name,
            "args_count": len(tool_args) if isinstance(tool_args, dict) else 0
        })

        # 开始各阶段计时
        tool_start_time = time.time()

        self.metrics.tool_calls_count += 1

        try:
            # 记录工具调用开始
            self._log_with_context('INFO', f"🔧 开始工具调用: {tool_name}", {
                'tool_name': tool_name,
                'tool_args': tool_args,
                'args_count': len(tool_args) if isinstance(tool_args, dict) else 0
            })

            # 执行工具调用
            result = handler(request)

            # 计算总耗时
            total_duration_ms = (time.time() - tool_start_time) * 1000

            # 创建工具性能指标
            tool_performance_metrics = PerformanceMetrics(
                request_duration_ms=total_duration_ms,
                inference_duration_ms=total_duration_ms,  # 工具执行时间作为主要耗时
                response_duration_ms=0  # 工具通常没有独立的响应生成阶段
            )

            # 添加工具特定的性能指标
            tool_performance_metrics.add_metric("execution_duration_ms", total_duration_ms, "timing", "ms")
            tool_performance_metrics.add_metric("args_count", len(tool_args) if isinstance(tool_args, dict) else 0, "count")
            tool_performance_metrics.add_metric("result_size", len(str(result)), "count", "chars")

            # 记录缓存命中状态（如果可以检测）
            cache_hit = self._detect_cache_hit(tool_name, tool_args, result)
            if cache_hit is not None:
                tool_performance_metrics.add_metric("cache_hit", cache_hit, "boolean")

            # 记录资源使用情况
            resource_usage = {
                "input_size_bytes": len(str(tool_args)),
                "output_size_bytes": len(str(result)),
                "total_io_bytes": len(str(tool_args)) + len(str(result))
            }

            # 记录工具调用成功
            tool_record = ToolCallRecord(
                tool_name=tool_name,
                tool_args=tool_args,
                result=result,
                duration_ms=total_duration_ms,
                success=True,
                performance_metrics=tool_performance_metrics,
                operation_phases={
                    "execution": total_duration_ms,
                    "total": total_duration_ms
                },
                cache_hit=cache_hit or False,
                resource_usage=resource_usage
            )
            self.tool_calls.append(tool_record)

            # 结束性能追踪
            self.performance_tracker.end_timing(tool_operation_id)
            self.performance_tracker.increment_counter("tool_calls_success")
            if cache_hit:
                self.performance_tracker.increment_counter("tool_cache_hits")

            # 记录详细性能信息
            self._log_with_context('INFO', f"✅ 工具调用完成: {tool_name}", {
                'tool_name': tool_name,
                'duration_ms': round(total_duration_ms, 2),
                'performance_breakdown': tool_record.get_detailed_performance(),
                'cache_hit': cache_hit,
                'result_preview': str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            })

            return result

        except Exception as e:
            self.metrics.errors_count += 1
            duration_ms = (time.time() - tool_start_time) * 1000

            # 记录工具调用失败
            tool_record = ToolCallRecord(
                tool_name=tool_name,
                tool_args=tool_args,
                result=None,
                duration_ms=duration_ms,
                success=False,
                error_message=str(e)
            )
            self.tool_calls.append(tool_record)

            self._log_with_context('ERROR', f"❌ 工具调用失败: {tool_name}", {
                'tool_name': tool_name,
                'duration_ms': round(duration_ms, 2),
                'error_type': type(e).__name__,
                'error_message': str(e)
            })

            raise

    async def awrap_tool_call(self, request, handler) -> Any:
        """异步包装工具调用，记录工具执行详情（性能增强版）"""
        if not self.config.enable_tool_tracking:
            return await handler(request)

        # 提取工具信息
        tool_name = "unknown"
        tool_args = {}

        if hasattr(request, 'tool_call'):
            tool_call = request.tool_call
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
        elif hasattr(request, 'name'):
            tool_name = request.name
            tool_args = getattr(request, 'args', {})

        # 生成操作ID用于性能追踪
        tool_operation_id = f"tool_{tool_name}_{int(time.time() * 1000)}"

        # 开始性能追踪
        self.performance_tracker.start_timing(tool_operation_id, "tool_call", {
            "tool_name": tool_name,
            "args_count": len(tool_args) if isinstance(tool_args, dict) else 0
        })

        # 开始各阶段计时
        tool_start_time = time.time()

        self.metrics.tool_calls_count += 1

        try:
            # 检查缓存（如果可用）
            cache_hit = False
            if hasattr(self, '_tool_cache'):
                cache_key = f"{tool_name}:{hash(str(sorted(tool_args.items())))}"
                cached_result = self._tool_cache.get(cache_key)
                if cached_result is not None:
                    cache_hit = True
                    result = cached_result
                    total_duration_ms = (time.time() - tool_start_time) * 1000

                    # 记录缓存命中的工具调用
                    tool_record = ToolCallRecord(
                        tool_name=tool_name,
                        tool_args=tool_args,
                        result=result,
                        success=True,
                        total_duration_ms=total_duration_ms,
                        cache_hit=cache_hit,
                        timestamp=datetime.now().isoformat()
                    )
                    self.tool_calls.append(tool_record)

                    # 结束性能追踪
                    self.performance_tracker.end_timing(tool_operation_id)
                    self.performance_tracker.increment_counter("tool_cache_hits")

                    return result

            # 实际调用处理程序（异步）
            if asyncio.iscoroutinefunction(handler):
                result = await handler(request)
            else:
                result = handler(request)

            # 计算总耗时
            total_duration_ms = (time.time() - tool_start_time) * 1000

            # 检测缓存命中（启发式）
            if not cache_hit:
                cache_hit = self._detect_cache_hit(tool_name, tool_args, result) or False

            # 创建增强的工具调用记录
            tool_record = ToolCallRecord(
                tool_name=tool_name,
                tool_args=tool_args,
                result=result,
                success=True,
                total_duration_ms=total_duration_ms,
                cache_hit=cache_hit,
                timestamp=datetime.now().isoformat()
            )
            self.tool_calls.append(tool_record)

            # 结束性能追踪
            self.performance_tracker.end_timing(tool_operation_id)
            self.performance_tracker.increment_counter("tool_calls_success")
            if cache_hit:
                self.performance_tracker.increment_counter("tool_cache_hits")

            # 记录详细性能信息
            self._log_with_context('INFO', f"✅ 工具调用完成: {tool_name}", {
                'tool_name': tool_name,
                'duration_ms': round(total_duration_ms, 2),
                'performance_breakdown': tool_record.get_detailed_performance(),
                'cache_hit': cache_hit,
                'result_preview': str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            })

            return result

        except Exception as e:
            self.metrics.errors_count += 1
            duration_ms = (time.time() - tool_start_time) * 1000

            # 记录工具调用失败
            tool_record = ToolCallRecord(
                tool_name=tool_name,
                tool_args=tool_args,
                result=None,
                success=False,
                total_duration_ms=duration_ms,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )
            self.tool_calls.append(tool_record)

            # 结束性能追踪
            self.performance_tracker.end_timing(tool_operation_id)
            self.performance_tracker.increment_counter("tool_calls_error")

            # 记录错误信息
            self._log_with_context('ERROR', f"❌ 工具调用失败: {tool_name}", {
                'tool_name': tool_name,
                'duration_ms': round(duration_ms, 2),
                'error_type': type(e).__name__,
                'error_message': str(e)
            })

            raise

    async def awrap_model_call(self, request, handler) -> Any:
        """异步包装模型调用，记录模型调用详情（性能增强版）"""
        if not self.config.enable_model_logging:
            return await handler(request)

        # 开始请求追踪
        self.start_request_tracking()

        # 生成操作ID用于性能追踪
        operation_id = f"model_call_{self.metrics.model_calls_count + 1}_{int(time.time() * 1000)}"

        # 开始性能追踪
        request_start_time = time.time()
        self.performance_tracker.start_timing(operation_id, "model_call", {
            "model_name": self._extract_model_name(request),
            "call_position": self.metrics.model_calls_count + 1
        })

        try:
            # 实际调用处理程序（异步）
            if asyncio.iscoroutinefunction(handler):
                response = await handler(request)
            else:
                response = handler(request)

            # 计算总耗时
            request_duration = (time.time() - request_start_time) * 1000

            # 记录模型调用成功
            model_call_record = ModelCallRecord(
                model_name=self._extract_model_name(request),
                request=request,
                response=response,
                success=True,
                total_duration_ms=request_duration,
                timestamp=datetime.now().isoformat()
            )
            self.model_calls.append(model_call_record)

            # 结束性能追踪
            self.performance_tracker.end_timing(operation_id)
            self.performance_tracker.increment_counter("model_calls_success")

            # 记录详细信息
            self._log_with_context('INFO', f"✅ 模型调用完成: {model_call_record.model_name}", {
                'model_name': model_call_record.model_name,
                'duration_ms': round(request_duration, 2),
                'call_position': self.metrics.model_calls_count
            })

            return response

        except Exception as e:
            request_duration = (time.time() - request_start_time) * 1000

            # 记录模型调用失败
            model_call_record = ModelCallRecord(
                model_name=self._extract_model_name(request),
                request=request,
                response=None,
                success=False,
                total_duration_ms=request_duration,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )
            self.model_calls.append(model_call_record)

            # 结束性能追踪
            self.performance_tracker.end_timing(operation_id)
            self.performance_tracker.increment_counter("model_calls_error")

            # 记录错误信息
            self._log_with_context('ERROR', f"❌ 模型调用失败: {model_call_record.model_name}", {
                'model_name': model_call_record.model_name,
                'duration_ms': round(request_duration, 2),
                'error_type': type(e).__name__,
                'error_message': str(e)
            })

            raise

    def _detect_cache_hit(self, tool_name: str, tool_args: Dict[str, Any], result: Any) -> Optional[bool]:
        """
        检测工具调用是否命中缓存

        这是一个简单的启发式实现，可以根据实际需求进行扩展
        """
        try:
            # 对于天气查询工具，检查结果是否包含缓存标识
            if tool_name in ['query_current_weather', 'query_weather_by_date', 'query_fishing_recommendation']:
                result_str = str(result).lower()
                # 简单的缓存检测逻辑
                cache_indicators = ['cache', 'cached', 'from cache', '缓存']
                return any(indicator in result_str for indicator in cache_indicators)

            # 对于坐标查询工具，检查是否快速返回（通常表示缓存命中）
            elif tool_name in ['get_coordinate']:
                total_duration_ms = (time.time() - time.time())  # 这会在后面重置
                # 如果耗时非常短，可能是缓存命中
                return False  # 需要实际的缓存机制来支持

            return None
        except Exception:
            return None

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能统计摘要

        Returns:
            包含详细性能统计的字典
        """
        # 基础统计
        basic_summary = {
            "session_id": self.session_id,
            "total_model_calls": self.metrics.model_calls_count,
            "total_tool_calls": self.metrics.tool_calls_count,
            "total_duration_ms": self.metrics.total_duration_ms,
            "total_errors": self.metrics.errors_count,
            "success_rate": (self.metrics.model_calls_count - self.metrics.errors_count) / max(self.metrics.model_calls_count, 1)
        }

        # 模型调用性能统计
        model_calls_summary = self.metrics.get_model_calls_summary()

        # 性能追踪器统计
        tracker_summary = self.performance_tracker.get_metrics_summary()

        # 工具调用性能统计
        tool_performance = {}
        total_tool_duration = 0
        cache_hits = 0
        if self.tool_calls:
            for tool_call in self.tool_calls:
                tool_name = tool_call.tool_name
                if tool_name not in tool_performance:
                    tool_performance[tool_name] = {
                        "count": 0,
                        "total_duration_ms": 0,
                        "avg_duration_ms": 0,
                        "cache_hits": 0,
                        "success_rate": 0
                    }

                stats = tool_performance[tool_name]
                stats["count"] += 1
                stats["total_duration_ms"] += tool_call.duration_ms
                if tool_call.cache_hit:
                    stats["cache_hits"] += 1
                if tool_call.success:
                    stats["success_rate"] += 1

        # 计算总和
        total_tool_duration = sum(tc.duration_ms for tc in self.tool_calls)
        cache_hits = sum(1 for tc in self.tool_calls if tc.cache_hit)

        # 计算平均值和成功率
        for stats in tool_performance.values():
            if stats["count"] > 0:
                stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
                stats["success_rate"] = (stats["success_rate"] / stats["count"]) * 100

        # 整合摘要
        return {
            **basic_summary,
            "model_performance": model_calls_summary,
            "tool_performance": tool_performance,
            "tracker_performance": tracker_summary,
            "performance_metrics": {
                "avg_model_call_duration": model_calls_summary.get("average_duration_ms", 0),
                "total_tool_duration_ms": total_tool_duration,
                "cache_hit_rate": (cache_hits / max(len(self.tool_calls), 1)) * 100 if self.tool_calls else 0,
                "error_rate": (self.metrics.errors_count / max(self.metrics.model_calls_count + self.metrics.tool_calls_count, 1)) * 100
            }
        }

    async def abefore_model(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """异步模型调用前的处理"""
        if not self.execution_start_time:
            self.execution_start_time = time.time()

        self.metrics.model_calls_count += 1

        # 记录输入信息
        messages = state.get('messages', [])

        # 使用意图分析器分析模型调用目的
        purpose_analysis = CallPurposeAnalyzer.analyze_call_purpose(
            messages=messages,
            call_position=self.metrics.model_calls_count,
            has_tool_calls=False,  # 此时还没有工具调用
            execution_context="pre_model"
        )

        # 记录模型调用开始
        model_name = "unknown"
        if hasattr(runtime, 'model'):
            model_name = runtime.model
        elif hasattr(state, 'model'):
            model_name = state.model

        self._log_with_context('INFO', f"🧠 模型调用开始: {model_name}", {
            'model_name': model_name,
            'call_position': self.metrics.model_calls_count,
            'purpose_analysis': purpose_analysis
        })

        return None

    async def aafter_model(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """异步模型调用后的处理"""
        # 更新最终指标
        if self.execution_start_time:
            self.metrics.total_duration_ms = (time.time() - self.execution_start_time) * 1000

        # 记录执行完成
        self._log_with_context('INFO', "🏁 模型调用完成 (异步)", {
            'final_metrics': asdict(self.metrics),
            'total_model_calls': self.metrics.model_calls_count
        })

        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> Optional[Dict[str, Any]]:
        """模型调用后的处理"""
        # 更新最终指标
        if self.execution_start_time:
            self.metrics.total_duration_ms = (time.time() - self.execution_start_time) * 1000

        # 记录执行完成
        self._log_with_context('INFO', "🏁 模型调用完成", {
            'final_metrics': asdict(self.metrics),
            'tool_calls_summary': [
                {
                    'tool_name': tc.tool_name,
                    'duration_ms': round(tc.duration_ms, 2),
                    'success': tc.success
                }
                for tc in self.tool_calls[-5:]  # 只显示最近5个工具调用
            ]
        })

        return None

    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            'session_id': self.session_id,
            'execution_id': self.metrics.execution_id,
            'metrics': asdict(self.metrics),
            'tool_calls': [asdict(tc) for tc in self.tool_calls],
            'timestamp': datetime.now().isoformat()
        }

    def reset_metrics(self):
        """重置执行指标"""
        self.metrics = AgentExecutionMetrics(
            session_id=self.session_id,
            timestamp=datetime.now().isoformat(),
            execution_id=str(uuid.uuid4())
        )
        self.tool_calls = []
        self.execution_start_time = None