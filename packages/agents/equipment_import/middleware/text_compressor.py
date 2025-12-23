"""
TextCompressorMiddleware - 文本压缩中间件

在 Agent 启动前自动压缩用户输入的长文本，删除冗余内容保留核心信息。
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional, Set

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain_core.messages import HumanMessage
from langgraph.runtime import Runtime

from .patterns import (
    REMOVE_BLOCK_COMPILED,
    BRAND_PATTERNS,
    SERIES_PATTERNS,
    MODEL_PATTERN,
    should_remove_line,
    should_keep_line,
)

logger = logging.getLogger(__name__)


@dataclass
class CompressedText:
    """压缩结果"""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    original_length: int = 0
    compressed_length: int = 0

    @property
    def compression_ratio(self) -> float:
        """压缩率 (0-1)，值越大压缩越多"""
        if self.original_length == 0:
            return 0.0
        return 1 - (self.compressed_length / self.original_length)

    def get_stats(self) -> str:
        """获取压缩统计信息"""
        return (
            f"压缩: {self.original_length} → {self.compressed_length} 字符 "
            f"(压缩率 {self.compression_ratio:.1%})"
        )


class TextCompressor:
    """
    OCR 文本压缩器

    删除冗余内容（英文营销语、售后说明、技术原理图等），
    保留核心信息（规格表、型号描述、技术特色、代言人等）。
    """

    def compress(self, text: str) -> CompressedText:
        """
        压缩文本

        Args:
            text: 原始文本

        Returns:
            CompressedText: 压缩结果
        """
        original_length = len(text)

        # 1. 提取元信息（品牌、系列、型号列表）
        metadata = self._extract_metadata(text)

        # 2. 删除大块冗余内容
        cleaned = self._remove_blocks(text)

        # 3. 逐行过滤
        cleaned = self._filter_lines(cleaned)

        # 4. 去除重复段落
        cleaned = self._deduplicate(cleaned)

        # 5. 清理多余空行
        cleaned = self._clean_whitespace(cleaned)

        compressed_length = len(cleaned)

        logger.info(
            f"文本压缩完成: {original_length} → {compressed_length} 字符 "
            f"(压缩率 {1 - compressed_length/original_length:.1%})"
        )

        return CompressedText(
            content=cleaned,
            metadata=metadata,
            original_length=original_length,
            compressed_length=compressed_length,
        )

    def _extract_metadata(self, text: str) -> dict[str, Any]:
        """提取元信息"""
        metadata: dict[str, Any] = {}

        # 提取品牌
        brands: Set[str] = set()
        for pattern in BRAND_PATTERNS:
            if re.search(pattern, text):
                brands.add(pattern.replace('\\', ''))
        if brands:
            metadata["brands"] = list(brands)

        # 提取系列
        series: Set[str] = set()
        for pattern in SERIES_PATTERNS:
            matches = re.findall(pattern, text)
            series.update(matches)
        if series:
            metadata["series"] = list(series)

        # 提取型号列表
        models = MODEL_PATTERN.findall(text)
        unique_models = list(dict.fromkeys(models))  # 去重保序
        if unique_models:
            metadata["models"] = unique_models
            metadata["model_count"] = len(unique_models)

        return metadata

    def _remove_blocks(self, text: str) -> str:
        """删除大块冗余内容"""
        result = text
        for pattern in REMOVE_BLOCK_COMPILED:
            result = pattern.sub('', result)
        return result

    def _filter_lines(self, text: str) -> str:
        """逐行过滤"""
        lines = text.split('\n')
        filtered: List[str] = []

        for line in lines:
            if not should_remove_line(line):
                filtered.append(line)

        return '\n'.join(filtered)

    def _deduplicate(self, text: str) -> str:
        """去除重复段落"""
        # 按空行分割成段落
        paragraphs = re.split(r'\n\s*\n', text)

        seen: Set[str] = set()
        unique: List[str] = []

        for para in paragraphs:
            # 标准化段落（去除首尾空白）
            normalized = para.strip()
            if not normalized:
                continue

            # 对于短段落（<100字符），精确去重
            if len(normalized) < 100:
                if normalized not in seen:
                    seen.add(normalized)
                    unique.append(para)
            else:
                # 对于长段落，检查是否有高度相似的
                # 简单实现：取前100字符作为指纹
                fingerprint = normalized[:100]
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    unique.append(para)

        return '\n\n'.join(unique)

    def _clean_whitespace(self, text: str) -> str:
        """清理多余空行"""
        # 将连续3个以上空行替换为2个
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 去除首尾空白
        return text.strip()


class TextCompressorMiddleware(AgentMiddleware):
    """
    文本压缩中间件

    在每次模型调用前（before_model）自动压缩用户输入的长文本。

    使用方式:
        from langchain.agents import create_agent
        from .middleware import TextCompressorMiddleware

        agent = create_agent(
            model=model,
            tools=tools,
            middleware=[TextCompressorMiddleware()],
        )
    """

    def __init__(self, min_length: int = 2000, enabled: bool = True):
        """
        初始化中间件

        Args:
            min_length: 触发压缩的最小文本长度
            enabled: 是否启用压缩
        """
        super().__init__()  # 必须调用父类初始化
        self.min_length = min_length
        self.enabled = enabled
        self.compressor = TextCompressor()
        self._last_compression: Optional[CompressedText] = None

    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        """
        在每次模型调用前压缩用户消息

        Args:
            state: Agent 状态，包含 messages
            runtime: LangGraph 运行时

        Returns:
            更新后的状态（如果有修改），否则返回 None
        """
        if not self.enabled:
            return None

        messages = state.get("messages", [])
        if not messages:
            return None

        # 检查最后一条消息
        last_msg = messages[-1]

        # 只处理用户消息
        if not hasattr(last_msg, 'type') or last_msg.type != "human":
            return None

        # 获取消息内容
        content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)

        # 检查长度
        if len(content) <= self.min_length:
            return None

        # 压缩文本
        logger.info(f"触发文本压缩: 原文长度 {len(content)} 字符")
        compressed = self.compressor.compress(content)
        self._last_compression = compressed

        logger.info(compressed.get_stats())
        if compressed.metadata.get("model_count"):
            logger.info(f"检测到 {compressed.metadata['model_count']} 个型号")

        # 返回更新后的 messages
        return {
            "messages": messages[:-1] + [HumanMessage(content=compressed.content)]
        }

    def get_last_compression(self) -> Optional[CompressedText]:
        """获取最近一次压缩结果"""
        return self._last_compression
