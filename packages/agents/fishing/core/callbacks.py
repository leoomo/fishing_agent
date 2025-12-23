#!/usr/bin/env python3
"""
Callback Utilities - Output validation

Note: FishingAgentCallback 已移除，统一使用 agent_component.monitoring.MonitoringCallback
"""

import logging

logger = logging.getLogger(__name__)


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
            warnings = [f"LLM 返回缺少关键格式: {m}" for m in missing]

        return {
            "valid": len(missing) == 0,
            "missing_markers": missing,
            "warnings": warnings
        }

    def log_validation_result(self, result: dict) -> None:
        """
        记录验证结果到日志（仅 DEBUG 级别）

        Args:
            result: validate_fishing_report 的返回值
        """
        if not result["valid"]:
            for warning in result["warnings"]:
                logger.debug(warning)
            logger.debug(
                "提示: LLM 可能没有遵循'输出格式规则'，"
                "请检查系统提示词是否正确加载"
            )
