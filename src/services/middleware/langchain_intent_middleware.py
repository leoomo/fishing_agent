"""
LangChain 1.0+ 意图识别增强中间件

将现有的CallPurposeAnalyzer逻辑包装为LangChain兼容的中间件，
利用框架能力增强意图识别和工具选择。
"""

from typing import Any, Dict, List, Optional
import time
import logging

# LangChain imports
try:
    from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
    from langchain_core.messages import BaseMessage
    from langchain_core.tools import BaseTool
except ImportError:
    # 如果没有安装完整LangChain，提供基础类型
    AgentMiddleware = object
    ModelRequest = object
    ModelResponse = object
    BaseMessage = object
    BaseTool = object

from .logging_middleware import CallPurposeAnalyzer, AgentLoggingMiddleware


class LangChainIntentMiddleware(AgentMiddleware):
    """
    LangChain 1.0+ 意图识别增强中间件

    功能：
    1. 包装现有的CallPurposeAnalyzer逻辑为LangChain中间件
    2. 基于意图动态优化工具选择
    3. 记录详细的意图分析日志
    4. 保持现有缓存和性能优化机制
    """

    def __init__(self, logger_middleware: Optional[AgentLoggingMiddleware] = None):
        """
        初始化意图中间件

        Args:
            logger_middleware: 现有的日志中间件实例，用于记录意图分析结果
        """
        self.logger_middleware = logger_middleware
        self.intent_stats = {
            'total_calls': 0,
            'intent_distribution': {},
            'tool_selection_enhancements': 0
        }

        # 工具优先级映射
        self.tool_priorities = {
            'weather_fishing_query': ['query_fishing_recommendation', 'query_current_weather', 'query_weather_by_date'],
            'weather_query': ['query_current_weather', 'query_weather_by_date', 'query_hourly_forecast'],
            'fishing_advice_generation': ['query_fishing_recommendation'],
            'time_query': ['get_current_time'],
            'calculation': ['calculate'],
            'information_search': ['search_information']
        }

        self.logger = logging.getLogger('langchain.intent_middleware')

    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """
        包装模型调用，进行意图分析和增强

        Args:
            request: LangChain模型请求
            handler: 原始处理器

        Returns:
            增强后的模型响应
        """
        start_time = time.time()

        try:
            # 分析用户意图
            intent_analysis = self._analyze_intent(request)
            self.intent_stats['total_calls'] += 1

            # 记录意图分布
            intent_category = intent_analysis['intent_category']
            self.intent_stats['intent_distribution'][intent_category] = \
                self.intent_stats['intent_distribution'].get(intent_category, 0) + 1

            # 基于意图增强工具选择
            enhanced_request = self._enhance_tool_selection(request, intent_analysis)

            # 动态调整系统提示（如果需要）
            if intent_analysis['intent_category'] in ['weather_fishing_query', 'fishing_advice_generation']:
                enhanced_request = self._enhance_fishing_prompt(enhanced_request, intent_analysis)

            # 调用原始处理器
            response = handler(enhanced_request)

            # 记录意图分析结果
            self._log_intent_analysis(intent_analysis, request, response, time.time() - start_time)

            # 将意图分析结果添加到请求中，供其他中间件使用
            if hasattr(request, 'metadata'):
                request.metadata['intent_analysis'] = intent_analysis
            else:
                # 创建metadata属性
                request.metadata = {'intent_analysis': intent_analysis}

            return response

        except Exception as e:
            self.logger.error(f"意图中间件处理失败: {e}")
            # 出错时直接调用原始处理器
            return handler(request)

    def _analyze_intent(self, request: ModelRequest) -> Dict[str, Any]:
        """
        分析用户意图

        Args:
            request: LangChain模型请求

        Returns:
            意图分析结果
        """
        try:
            # 提取消息列表
            messages = request.messages if hasattr(request, 'messages') else []

            # 推断调用位置
            call_position = self._get_call_position(request)
            has_tool_calls = self._has_tool_calls(request)

            # 推断执行上下文 - 使用增强的智能逻辑
            messages = request.messages if hasattr(request, 'messages') else []

            # 基于消息历史和工具调用状态推断执行上下文
            if call_position == 1:
                # 首次调用 - 总是工具选择阶段
                execution_context = "tool_selection"
            elif call_position > 1:
                # 后续调用 - 需要更细致的判断
                if has_tool_calls:
                    # 包含工具调用的后续调用
                    # 检查是否是工具调用后的第一次回复
                    has_ai_responses = any(
                        hasattr(msg, 'type') and msg.type == 'ai'
                        for msg in messages[:-1]  # 排除当前消息
                    )

                    if has_ai_responses:
                        # 已经有AI回复，说明是工具执行阶段
                        execution_context = "tool_execution"
                    else:
                        # 还没有AI回复，可能是工具选择阶段的延续
                        execution_context = "tool_selection"
                else:
                    # 不包含工具调用的后续调用
                    # 检查是否有工具执行结果
                    has_tool_results = any(
                        hasattr(msg, 'type') and msg.type == 'tool'
                        for msg in messages
                    )

                    if has_tool_results:
                        # 有工具执行结果，这是结果生成阶段
                        execution_context = "result_generation"
                    else:
                        # 没有工具执行结果，可能是连续的推理
                        execution_context = "tool_selection"
            else:
                # 默认使用基础推断逻辑
                execution_context = CallPurposeAnalyzer._infer_purpose_by_position(call_position, has_tool_calls)

            # 使用现有的意图分析逻辑
            intent_analysis = CallPurposeAnalyzer.analyze_call_purpose(
                messages=messages,
                call_position=call_position,
                has_tool_calls=has_tool_calls,
                execution_context=execution_context
            )

            # 添加增强信息
            intent_analysis['call_position'] = call_position
            intent_analysis['has_tool_calls'] = has_tool_calls
            intent_analysis['enhancement_suggestions'] = self._get_enhancement_suggestions(intent_analysis)

            return intent_analysis

        except Exception as e:
            self.logger.error(f"意图分析失败: {e}")
            return {
                'intent_category': 'unknown',
                'call_purpose': 'unknown',
                'execution_context': 'unknown',
                'key_points': [],
                'error': str(e)
            }

    def _enhance_tool_selection(self, request: ModelRequest, intent_analysis: Dict[str, Any]) -> ModelRequest:
        """
        基于意图分析结果增强工具选择

        Args:
            request: 原始请求
            intent_analysis: 意图分析结果

        Returns:
            工具选择增强后的请求
        """
        intent_category = intent_analysis.get('intent_category', 'unknown')

        if intent_category in self.tool_priorities:
            # 获取意图相关的工具优先级列表
            priority_tools = self.tool_priorities[intent_category]

            # 获取当前可用工具
            available_tools = getattr(request, 'tools', [])

            if available_tools and priority_tools:
                # 根据优先级重新排序工具
                enhanced_tools = self._reorder_tools_by_priority(available_tools, priority_tools)

                # 创建增强后的请求（保持原有结构）
                enhanced_request = self._create_enhanced_request(request, tools=enhanced_tools)
                self.intent_stats['tool_selection_enhancements'] += 1

                return enhanced_request

        return request

    def _enhance_fishing_prompt(self, request: ModelRequest, intent_analysis: Dict[str, Any]) -> ModelRequest:
        """
        为钓鱼相关查询增强系统提示

        Args:
            request: 原始请求
            intent_analysis: 意图分析结果

        Returns:
            提示增强后的请求
        """
        # 提取关键信息点
        key_points = intent_analysis.get('key_points', [])

        # 构建钓鱼相关的增强提示
        fishing_enhancement = f"""
钓鱼专家模式已启用：
- 当前用户查询涉及钓鱼时间建议
- 重点关注：天气条件、时段选择、最佳时机
- 推荐工具：钓鱼推荐分析器
- 输出格式：详细的时间段建议和原因分析
"""

        if key_points:
            fishing_enhancement += f"\n关键信息点：{', '.join(key_points)}"

        # 合并到现有系统提示
        current_prompt = getattr(request, 'system_prompt', '')
        enhanced_prompt = current_prompt + "\n" + fishing_enhancement

        return self._create_enhanced_request(request, system_prompt=enhanced_prompt)

    def _get_call_position(self, request: ModelRequest) -> int:
        """推断调用位置"""
        # 尝试从请求中提取调用位置信息
        if hasattr(request, 'call_position'):
            return request.call_position

        # 尝试从消息历史推断调用位置
        messages = getattr(request, 'messages', [])
        if len(messages) > 1:
            # 如果有多条消息，说明不是首次调用
            return 2
        elif len(messages) == 1:
            # 只有一条消息，是首次调用
            return 1
        else:
            # 默认为首次调用
            return 1

    def _has_tool_calls(self, request: ModelRequest) -> bool:
        """检查是否包含工具调用"""
        # 首先检查直接的属性
        if hasattr(request, 'has_tool_calls'):
            return request.has_tool_calls

        # 尝试从消息中检查工具调用
        messages = getattr(request, 'messages', [])
        for message in messages:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                return True
            if hasattr(message, 'additional_kwargs') and 'tool_calls' in message.additional_kwargs:
                return True
            # 检查消息内容中是否包含工具调用的标识
            if hasattr(message, 'content') and isinstance(message.content, str):
                if 'tool_calls' in str(message.content).lower():
                    return True

        return False

    def _reorder_tools_by_priority(self, available_tools: List[BaseTool], priority_tools: List[str]) -> List[BaseTool]:
        """根据优先级重新排序工具"""
        tool_map = {tool.name: tool for tool in available_tools if hasattr(tool, 'name')}

        # 按优先级顺序重新排列
        ordered_tools = []
        added_names = set()

        # 添加高优先级工具
        for priority_name in priority_tools:
            if priority_name in tool_map and priority_name not in added_names:
                ordered_tools.append(tool_map[priority_name])
                added_names.add(priority_name)

        # 添加剩余工具
        for tool in available_tools:
            if hasattr(tool, 'name') and tool.name not in added_names:
                ordered_tools.append(tool)
                added_names.add(tool.name)

        return ordered_tools

    def _create_enhanced_request(self, request: ModelRequest, **kwargs) -> ModelRequest:
        """创建增强后的请求"""
        # 这里需要根据实际的LangChain ModelRequest结构调整
        # 由于不同版本可能有差异，这里提供通用的包装逻辑

        enhanced_request = request

        # 更新工具列表
        if 'tools' in kwargs:
            if hasattr(enhanced_request, 'tools'):
                enhanced_request.tools = kwargs['tools']

        # 更新系统提示
        if 'system_prompt' in kwargs:
            if hasattr(enhanced_request, 'system_prompt'):
                enhanced_request.system_prompt = kwargs['system_prompt']

        return enhanced_request

    def _get_enhancement_suggestions(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """获取增强建议"""
        suggestions = []

        intent_category = intent_analysis.get('intent_category', '')
        key_points = intent_analysis.get('key_points', [])

        if intent_category == 'weather_fishing_query':
            suggestions.append("优先使用钓鱼推荐工具")
            if key_points:
                suggestions.append(f"关注关键信息：{', '.join(key_points)}")

        elif intent_category == 'fishing_advice_generation':
            suggestions.append("生成详细的钓鱼建议")
            suggestions.append("包含时间段和原因分析")

        return suggestions

    def _log_intent_analysis(self, intent_analysis: Dict[str, Any], request: ModelRequest,
                           response: ModelResponse, duration: float):
        """记录意图分析结果"""
        if self.logger_middleware:
            try:
                # 创建模型调用记录
                call_record = type('ModelCallRecord', (), {
                    'intent_category': intent_analysis.get('intent_category', 'unknown'),
                    'call_purpose': intent_analysis.get('call_purpose', 'unknown'),
                    'execution_context': intent_analysis.get('execution_context', 'unknown'),
                    'key_points': intent_analysis.get('key_points', []),
                    'duration_ms': duration * 1000,
                    'enhancement_suggestions': intent_analysis.get('enhancement_suggestions', [])
                })()

                # 记录到日志中间件
                if hasattr(self.logger_middleware, 'add_model_call'):
                    self.logger_middleware.add_model_call(call_record)

            except Exception as e:
                self.logger.error(f"记录意图分析失败: {e}")

    def get_intent_stats(self) -> Dict[str, Any]:
        """获取意图统计信息"""
        return {
            'total_calls': self.intent_stats['total_calls'],
            'intent_distribution': self.intent_stats['intent_distribution'].copy(),
            'tool_selection_enhancements': self.intent_stats['tool_selection_enhancements'],
            'most_common_intent': max(self.intent_stats['intent_distribution'].items(),
                                    key=lambda x: x[1])[0] if self.intent_stats['intent_distribution'] else None
        }

    def reset_stats(self):
        """重置统计信息"""
        self.intent_stats = {
            'total_calls': 0,
            'intent_distribution': {},
            'tool_selection_enhancements': 0
        }