"""
EquipmentImportAgent - 装备导入 Agent

支持对话式交互和直接 API 调用两种方式。
"""

import logging
from typing import List, Optional, Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable

from .extractor import EquipmentExtractor
from .prompts import EQUIPMENT_IMPORT_SYSTEM_PROMPT
from ..tools import get_import_tools
from ..tools.import_tool import (
    _check_duplicate_equipment,
    _check_duplicate_pending
)
from ..schemas.extracted import ExtractedEquipment, ImportResult
from ..models.pending import save_pending_equipment
from ..middleware import TextCompressorMiddleware, TextCompressor
from ..constants import (
    EQUIPMENT_TYPES,
    CONFIDENCE_THRESHOLD_LOW,
    DEFAULT_MODEL_PROVIDER,
    COMPRESSION_MIN_LENGTH,
    BATCH_OCR_TEXT_LIMIT
)
from packages.agents.agent_component.monitoring import MonitoringCallback

logger = logging.getLogger(__name__)


class EquipmentImportAgent:
    """
    装备导入 Agent

    支持两种使用方式：
    1. 对话式交互: agent.run("帮我识别这段文字里的装备信息...")
    2. 直接 API 调用: agent.extract_and_save(text, source_type)
    """

    def __init__(
        self,
        model_provider: str = DEFAULT_MODEL_PROVIDER,
        timeout: int = 60,
        enable_logging: bool = True,
        enable_compression: bool = True,
        compression_min_length: int = COMPRESSION_MIN_LENGTH,
        enable_monitoring: bool = True,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ):
        """
        初始化装备导入 Agent

        Args:
            model_provider: LLM 提供商 ("zhipu", "qwen", "doubao", "openai")
            timeout: 请求超时时间（秒）
            enable_logging: 是否启用日志
            enable_compression: 是否启用文本压缩中间件
            compression_min_length: 触发压缩的最小文本长度
            enable_monitoring: 是否启用数据库监控 (默认 True)
            user_id: 用户 ID（用于监控上下文）
            session_id: 会话 ID（用于监控上下文）
        """
        self.model_provider = model_provider
        self.timeout = timeout
        self.enable_logging = enable_logging
        self.enable_compression = enable_compression
        self.enable_monitoring = enable_monitoring
        self.user_id = user_id
        self.session_id = session_id

        # 初始化监控回调
        self.monitoring_callback = MonitoringCallback(
            agent_type="equipment_import",
            model_provider=model_provider,
            user_id=user_id,
            session_id=session_id,
            persist=enable_monitoring,
            verbose=False
        )

        # 初始化组件
        self.model = self._initialize_model()
        self.extractor = EquipmentExtractor(model=self.model)
        self.tools = self._setup_tools()
        self.compressor = TextCompressor() if enable_compression else None
        self.middleware = self._setup_middleware(enable_compression, compression_min_length)
        self.agent = self._create_agent()

        if enable_logging:
            logger.info("装备导入 Agent 初始化完成")
            logger.info(f"   模型: {model_provider}")
            logger.info(f"   工具数: {len(self.tools)}")
            logger.info(f"   文本压缩: {'启用' if enable_compression else '禁用'}")

    def _initialize_model(self) -> Any:
        """初始化 LLM 模型"""
        try:
            from packages.agents.fishing.core import ModelFactory
            return ModelFactory.create(
                provider=self.model_provider,
                timeout=self.timeout
            )
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            raise

    def _setup_tools(self) -> List:
        """配置工具集"""
        tools = get_import_tools()

        if self.enable_logging:
            logger.info(f"工具集配置完成: {len(tools)} 个工具")
            for tool in tools:
                logger.debug(f"   - {tool.name}")

        return tools

    def _setup_middleware(self, enable_compression: bool, min_length: int) -> List:
        """配置中间件"""
        middleware = []

        if enable_compression:
            middleware.append(TextCompressorMiddleware(min_length=min_length))
            if self.enable_logging:
                logger.info(f"文本压缩中间件已配置 (最小长度: {min_length})")

        return middleware

    def _create_agent(self) -> Runnable:
        """创建 LangChain Agent"""
        agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=EQUIPMENT_IMPORT_SYSTEM_PROMPT
        )

        if self.enable_logging:
            logger.info("Agent 创建完成")

        return agent

    # ========== 对话式调用 ==========

    def run(
        self,
        user_input: str,
        user_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> str:
        """
        对话式交互

        Agent 会理解用户意图并自动调用工具完成任务。

        Args:
            user_input: 用户输入的自然语言
            user_id: 覆盖用户 ID（用于监控）
            session_id: 覆盖会话 ID（用于监控）

        Returns:
            str: Agent 的回复
        """
        try:
            if self.enable_logging:
                logger.info(f"用户输入: {user_input}")

            # 更新监控上下文
            if user_id is not None:
                self.monitoring_callback.user_id = user_id
            if session_id is not None:
                self.monitoring_callback.session_id = session_id

            # 设置输入文本用于监控
            self.monitoring_callback.set_input(user_input)

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config={"callbacks": [self.monitoring_callback]}
            )

            response = self._extract_response(result)

            if self.enable_logging:
                logger.info(f"Agent 回复: {len(response)} 字符")

            return response

        except Exception as e:
            logger.error(f"Agent 执行出错: {e}")
            return f"抱歉，处理过程中遇到问题：{str(e)}"

    def _extract_response(self, result: Any) -> str:
        """从 Agent 结果中提取响应文本"""
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            if messages and len(messages) > 0:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict) and "content" in last_message:
                    return last_message["content"]
        return str(result)

    # ========== 直接 API 调用 ==========

    def extract_and_save(
        self,
        text: str,
        source_type: str = "unknown",
        source_url: Optional[str] = None,
        check_duplicates: bool = True,
        brand_hint: str = "",
        dry_run: bool = False
    ) -> ImportResult:
        """
        直接 API 调用：提取装备信息并存入待审核表

        Args:
            text: 包含装备信息的文本内容
            source_type: 来源类型 (ecommerce/official/forum/unknown)
            source_url: 来源 URL
            check_duplicates: 是否检查重复装备
            brand_hint: 品牌提示
            dry_run: 仅提取不保存

        Returns:
            ImportResult: 导入结果
        """
        # 记录执行开始
        self.monitoring_callback.set_input(f"extract_and_save: {text[:100]}...")
        self.monitoring_callback.start_execution()

        try:
            if not text or not text.strip():
                self.monitoring_callback.set_error("文本内容为空")
                return ImportResult(
                    success=False,
                    message="文本内容为空"
                )

            # 如果有品牌提示，添加到文本开头
            processed_text = text
            if brand_hint:
                processed_text = f"[品牌提示: {brand_hint}]\n\n{text}"

            # 使用 LLM 提取装备信息
            extracted = self.extractor.extract(processed_text, source_type)

            # 检查提取结果
            if not extracted.equipment_type:
                self.monitoring_callback.set_error("无法识别装备类型")
                return ImportResult(
                    success=False,
                    message="无法识别装备类型",
                    extracted=extracted
                )

            # 验证装备类型
            if extracted.equipment_type not in EQUIPMENT_TYPES:
                self.monitoring_callback.set_error(f"不支持的装备类型: {extracted.equipment_type}")
                return ImportResult(
                    success=False,
                    message=f"不支持的装备类型: {extracted.equipment_type}",
                    extracted=extracted
                )

            # 检查置信度
            if extracted.confidence < CONFIDENCE_THRESHOLD_LOW:
                return ImportResult(
                    success=False,
                    message=f"提取置信度过低 ({extracted.confidence:.0%})",
                    extracted=extracted
                )

            # 检查重复
            duplicate_info = None
            if check_duplicates:
                dup_equipment = _check_duplicate_equipment(
                    extracted.brand_name,
                    extracted.model,
                    extracted.equipment_type
                )
                if dup_equipment:
                    duplicate_info = {
                        "type": "equipment",
                        "id": dup_equipment.get("id"),
                        "name": dup_equipment.get("name")
                    }

                if not duplicate_info:
                    dup_pending = _check_duplicate_pending(
                        extracted.brand_name,
                        extracted.model
                    )
                    if dup_pending:
                        duplicate_info = {
                            "type": "pending",
                            "id": dup_pending.get("id"),
                            "name": f"{dup_pending.get('brand_name')} {dup_pending.get('model_name')}"
                        }

            # dry_run 模式：只返回提取结果，不保存
            if dry_run:
                message = f"预览模式：成功提取 {extracted.equipment_type} 信息"
                if duplicate_info:
                    message += f"（注意：已存在相似记录）"

                self.monitoring_callback.set_success(True)
                self.monitoring_callback.end_execution()

                result = ImportResult(
                    success=True,
                    message=message,
                    extracted=extracted
                )
                return result

            # 存入待审核表
            pending_id = save_pending_equipment(
                extracted=extracted,
                ocr_text=text,
                source_type=source_type,
                source_url=source_url
            )

            # 记录成功执行
            self.monitoring_callback.set_success(True)
            self.monitoring_callback.end_execution()

            message = f"成功提取 {extracted.equipment_type} 信息，已存入待审核表"
            if duplicate_info:
                message += f"（注意：已存在相似记录 {duplicate_info['name']}）"

            return ImportResult(
                success=True,
                pending_id=pending_id,
                message=message,
                extracted=extracted
            )

        except Exception as e:
            logger.error(f"提取并保存失败: {e}")
            self.monitoring_callback.set_error(f"处理失败: {str(e)}")
            return ImportResult(
                success=False,
                message=f"处理失败: {str(e)}"
            )
        finally:
            # 确保执行总是结束
            self.monitoring_callback.end_execution()

    def extract_only(
        self,
        text: str,
        source_type: str = "unknown"
    ) -> ExtractedEquipment:
        """
        仅提取装备信息（不保存）

        Args:
            text: 包含装备信息的文本内容
            source_type: 来源类型

        Returns:
            ExtractedEquipment: 提取的装备信息
        """
        return self.extractor.extract(text, source_type)

    # ========== 批量提取 API ==========

    def batch_extract_and_save(
        self,
        text: str,
        source_type: str = "unknown",
        source_url: Optional[str] = None
    ) -> List[ImportResult]:
        """
        批量提取装备信息并存入待审核表

        从单个长文本中提取所有装备型号，并分别保存到待审核表。
        如果启用了文本压缩，会先压缩文本再提取。

        Args:
            text: 包含多个装备型号的长文本
            source_type: 来源类型 (ecommerce/official/forum/unknown)
            source_url: 来源 URL

        Returns:
            List[ImportResult]: 每个型号的导入结果
        """
        # 记录执行开始
        self.monitoring_callback.set_input(f"batch_extract_and_save: {text[:100]}...")
        self.monitoring_callback.start_execution()

        try:
            if not text or not text.strip():
                self.monitoring_callback.set_error("文本内容为空")
                return [ImportResult(
                    success=False,
                    message="文本内容为空"
                )]

            # 如果启用压缩，先压缩文本
            processed_text = text
            if self.compressor and len(text) > COMPRESSION_MIN_LENGTH:
                compressed = self.compressor.compress(text)
                processed_text = compressed.content
                if self.enable_logging:
                    logger.info(compressed.get_stats())
                    if compressed.metadata.get("model_count"):
                        logger.info(f"检测到 {compressed.metadata['model_count']} 个型号")

            # 批量提取所有型号
            extracted_list = self.extractor.extract_multiple(processed_text, source_type)

            if not extracted_list:
                return [ImportResult(
                    success=False,
                    message="无法识别任何装备型号"
                )]

            # 逐个保存到待审核表
            results = []
            for extracted in extracted_list:
                try:
                    # 检查必要字段
                    if not extracted.equipment_type:
                        results.append(ImportResult(
                            success=False,
                            message=f"型号 {extracted.model} 缺少装备类型",
                            extracted=extracted
                        ))
                        continue

                    # 存入待审核表
                    pending_id = save_pending_equipment(
                        extracted=extracted,
                        ocr_text=text[:BATCH_OCR_TEXT_LIMIT],  # 只保存原文前 N 字符
                        source_type=source_type,
                        source_url=source_url
                    )

                    results.append(ImportResult(
                        success=True,
                        pending_id=pending_id,
                        message=f"成功提取 {extracted.equipment_type} {extracted.model}",
                        extracted=extracted
                    ))

                except Exception as e:
                    logger.warning(f"保存型号 {extracted.model} 失败: {e}")
                    results.append(ImportResult(
                        success=False,
                        message=f"保存失败: {str(e)}",
                        extracted=extracted
                    ))

            if self.enable_logging:
                success_count = sum(1 for r in results if r.success)
                logger.info(f"批量提取完成: {success_count}/{len(results)} 个型号成功")

            # 记录成功执行
            self.monitoring_callback.set_success(True)
            self.monitoring_callback.end_execution()

            return results

        except Exception as e:
            logger.error(f"批量提取并保存失败: {e}")
            self.monitoring_callback.set_error(f"批量处理失败: {str(e)}")
            return [ImportResult(
                success=False,
                message=f"批量处理失败: {str(e)}"
            )]
        finally:
            # 确保执行总是结束
            self.monitoring_callback.end_execution()

    def batch_extract_only(
        self,
        text: str,
        source_type: str = "unknown"
    ) -> List[ExtractedEquipment]:
        """
        批量提取装备信息（不保存）

        从单个长文本中提取所有装备型号。
        如果启用了文本压缩，会先压缩文本再提取。

        Args:
            text: 包含多个装备型号的长文本
            source_type: 来源类型

        Returns:
            List[ExtractedEquipment]: 提取的装备信息列表
        """
        # 如果启用压缩，先压缩文本
        processed_text = text
        if self.compressor and len(text) > COMPRESSION_MIN_LENGTH:
            compressed = self.compressor.compress(text)
            processed_text = compressed.content
            if self.enable_logging:
                logger.info(compressed.get_stats())

        return self.extractor.extract_multiple(processed_text, source_type)

    # ========== 工具方法 ==========

    def get_tools(self) -> List:
        """获取工具列表"""
        return self.tools

    def get_tool_names(self) -> List[str]:
        """获取工具名称列表"""
        return [tool.name for tool in self.tools]
