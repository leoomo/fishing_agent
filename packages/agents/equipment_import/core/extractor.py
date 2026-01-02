"""
EquipmentExtractor - LLM 装备信息提取器

使用 LLM 从文本中提取结构化的装备信息。
"""

import json
import logging
import re
from typing import Optional, Any

from ..schemas.extracted import ExtractedEquipment
from .prompts import get_extraction_prompt, get_batch_extraction_prompt

logger = logging.getLogger(__name__)


class EquipmentExtractor:
    """
    使用 LLM 从文本提取结构化装备信息

    支持从电商详情、官方规格表、论坛帖子等不同来源提取信息。
    """

    def __init__(self, model: Optional[Any] = None, model_provider: str = "zhipu"):
        """
        初始化提取器

        Args:
            model: LLM 模型实例 (可选，如果不提供则自动创建)
            model_provider: LLM 提供商 (当 model 为 None 时使用)
        """
        if model is not None:
            self.model = model
        else:
            # 延迟导入，避免循环依赖
            from packages.agents.fishing.core import ModelFactory
            self.model = ModelFactory.create(provider=model_provider)

    def extract(
        self,
        text: str,
        source_type: str = "unknown"
    ) -> ExtractedEquipment:
        """
        从文本中提取装备信息

        Args:
            text: 包含装备信息的文本内容
            source_type: 来源类型 (ecommerce/official/forum/unknown)

        Returns:
            ExtractedEquipment: 提取的装备信息
        """
        if not text or not text.strip():
            return ExtractedEquipment(
                confidence=0.0,
                extraction_notes="输入文本为空"
            )

        try:
            # 获取提取提示词
            prompt = get_extraction_prompt(source_type)

            # 构建消息
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"请从以下文本中提取装备信息：\n\n{text}"}
            ]

            # 调用 LLM
            response = self.model.invoke(messages)

            # 提取响应内容
            content = self._extract_content(response)

            # 解析 JSON
            extracted_data = self._parse_json_response(content)

            # 创建 ExtractedEquipment 实例
            return ExtractedEquipment.from_dict(extracted_data)

        except Exception as e:
            logger.error(f"提取装备信息失败: {e}")
            return ExtractedEquipment(
                confidence=0.0,
                extraction_notes=f"提取失败: {str(e)}"
            )

    def _extract_content(self, response: Any) -> str:
        """
        从 LLM 响应中提取文本内容

        Args:
            response: LLM 响应对象

        Returns:
            str: 响应文本内容
        """
        # 处理不同类型的响应
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, dict) and 'content' in response:
            return response['content']
        elif isinstance(response, str):
            return response
        else:
            return str(response)

    def _parse_json_response(self, content: str) -> dict:
        """
        解析 LLM 返回的 JSON 内容

        Args:
            content: LLM 返回的文本内容

        Returns:
            dict: 解析后的字典
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { } 之间的内容
        brace_match = re.search(r'\{[\s\S]*\}', content)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        # 解析失败，返回空结果
        logger.warning(f"无法解析 LLM 返回的 JSON: {content[:200]}...")
        return {
            "equipment_type": "",
            "confidence": 0.1,
            "extraction_notes": f"JSON 解析失败，原始响应: {content[:500]}"
        }

    def extract_multiple(
        self,
        text: str,
        source_type: str = "unknown"
    ) -> list[ExtractedEquipment]:
        """
        从单个长文本中提取多个装备型号

        使用批量提取提示词，让 LLM 返回 JSON 数组格式，
        一次调用提取所有型号的信息。

        Args:
            text: 包含多个装备型号的长文本
            source_type: 来源类型 (ecommerce/official/forum/unknown)

        Returns:
            list[ExtractedEquipment]: 提取的装备信息列表
        """
        if not text or not text.strip():
            return []

        try:
            # 获取批量提取提示词
            prompt = get_batch_extraction_prompt(source_type)

            # 构建消息
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"请从以下文本中提取所有装备型号的信息：\n\n{text}"}
            ]

            # 调用 LLM
            logger.info(f"开始批量提取，文本长度: {len(text)} 字符")
            response = self.model.invoke(messages)

            # 提取响应内容
            content = self._extract_content(response)

            # 解析 JSON 数组
            extracted_list = self._parse_json_array_response(content)

            # 转换为 ExtractedEquipment 列表
            results = []
            for data in extracted_list:
                try:
                    equipment = ExtractedEquipment.from_dict(data)
                    results.append(equipment)
                except Exception as e:
                    logger.warning(f"转换装备数据失败: {e}, data={data}")

            logger.info(f"批量提取完成，共提取 {len(results)} 个型号")
            return results

        except Exception as e:
            logger.error(f"批量提取装备信息失败: {e}")
            return []

    def _parse_json_array_response(self, content: str) -> list[dict]:
        """
        解析 LLM 返回的 JSON 数组内容

        Args:
            content: LLM 返回的文本内容

        Returns:
            list[dict]: 解析后的字典列表
        """
        # 尝试直接解析
        try:
            result = json.loads(content)
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                # 如果返回的是单个对象，包装成列表
                return [result]
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    return [result]
            except json.JSONDecodeError:
                pass

        # 尝试提取 [ ] 之间的内容
        bracket_match = re.search(r'\[[\s\S]*\]', content)
        if bracket_match:
            try:
                result = json.loads(bracket_match.group(0))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        # 尝试提取 { } 之间的内容 (可能是单个对象)
        brace_match = re.search(r'\{[\s\S]*\}', content)
        if brace_match:
            try:
                result = json.loads(brace_match.group(0))
                if isinstance(result, dict):
                    return [result]
            except json.JSONDecodeError:
                pass

        # 解析失败，返回空列表
        logger.warning(f"无法解析 LLM 返回的 JSON 数组: {content[:200]}...")
        return []

    def extract_batch(
        self,
        texts: list[str],
        source_type: str = "unknown"
    ) -> list[ExtractedEquipment]:
        """
        批量提取装备信息（多个文本分别提取）

        Args:
            texts: 文本列表
            source_type: 来源类型

        Returns:
            list[ExtractedEquipment]: 提取结果列表
        """
        results = []
        for text in texts:
            result = self.extract(text, source_type)
            results.append(result)
        return results
