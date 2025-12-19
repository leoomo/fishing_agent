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
from ..schemas.extracted import ExtractedEquipment, ImportResult
from ..models.pending import save_pending_equipment
from ..middleware import TextCompressorMiddleware, TextCompressor

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
        model_provider: str = "zhipu",
        timeout: int = 60,
        enable_logging: bool = True,
        enable_compression: bool = True,
        compression_min_length: int = 2000
    ):
        """
        初始化装备导入 Agent

        Args:
            model_provider: LLM 提供商 ("zhipu", "qwen", "doubao", "openai")
            timeout: 请求超时时间（秒）
            enable_logging: 是否启用日志
            enable_compression: 是否启用文本压缩中间件
            compression_min_length: 触发压缩的最小文本长度
        """
        self.model_provider = model_provider
        self.timeout = timeout
        self.enable_logging = enable_logging
        self.enable_compression = enable_compression

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
            from packages.agent_fishing.core import ModelFactory
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

    def run(self, user_input: str) -> str:
        """
        对话式交互

        Agent 会理解用户意图并自动调用工具完成任务。

        Args:
            user_input: 用户输入的自然语言

        Returns:
            str: Agent 的回复
        """
        try:
            if self.enable_logging:
                logger.info(f"用户输入: {user_input}")

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=user_input)]}
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
        source_url: Optional[str] = None
    ) -> ImportResult:
        """
        直接 API 调用：提取装备信息并存入待审核表

        Args:
            text: 包含装备信息的文本内容
            source_type: 来源类型 (ecommerce/official/forum/unknown)
            source_url: 来源 URL

        Returns:
            ImportResult: 导入结果
        """
        try:
            if not text or not text.strip():
                return ImportResult(
                    success=False,
                    message="文本内容为空"
                )

            # 使用 LLM 提取装备信息
            extracted = self.extractor.extract(text, source_type)

            # 检查提取结果
            if not extracted.equipment_type:
                return ImportResult(
                    success=False,
                    message="无法识别装备类型",
                    extracted=extracted
                )

            # 存入待审核表
            pending_id = save_pending_equipment(
                extracted=extracted,
                ocr_text=text,  # 数据库字段名保持不变
                source_type=source_type,
                source_url=source_url
            )

            return ImportResult(
                success=True,
                pending_id=pending_id,
                message=f"成功提取 {extracted.equipment_type} 信息，已存入待审核表",
                extracted=extracted
            )

        except Exception as e:
            logger.error(f"提取并保存失败: {e}")
            return ImportResult(
                success=False,
                message=f"处理失败: {str(e)}"
            )

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
        try:
            if not text or not text.strip():
                return [ImportResult(
                    success=False,
                    message="文本内容为空"
                )]

            # 如果启用压缩，先压缩文本
            processed_text = text
            if self.compressor and len(text) > 2000:
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
                        ocr_text=text[:1000],  # 只保存原文前 1000 字符
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

            return results

        except Exception as e:
            logger.error(f"批量提取并保存失败: {e}")
            return [ImportResult(
                success=False,
                message=f"批量处理失败: {str(e)}"
            )]

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
        if self.compressor and len(text) > 2000:
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
