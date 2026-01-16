"""
文章搜索工具 - 从内容管理系统搜索钓鱼相关文章

使用 ChromaDB 向量数据库进行语义搜索，返回与查询最相关的文章内容。
"""

import logging
from typing import Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 懒加载服务实例
_vector_store = None


def _get_vector_store():
    """获取向量存储服务实例（懒加载）"""
    global _vector_store
    if _vector_store is None:
        from apps.api.services.vector_store import get_vector_store
        _vector_store = get_vector_store()
    return _vector_store


@tool
def search_fishing_articles(
    query: str,
    article_type: Optional[str] = None,
    max_results: int = 3
) -> str:
    """搜索钓鱼相关文章内容。

    当用户询问钓鱼技巧、策略、装备评测、钓点推荐等知识性问题时使用此工具。
    返回与查询最相关的文章摘要和关键信息。

    Args:
        query: 搜索关键词，如"路亚鲈鱼技巧"、"冬季钓鱼策略"、"德州钓组"
        article_type: 文章类型过滤，可选值：strategy(策略)、tips(技巧)、review(评测)、spot(钓点)
        max_results: 返回结果数量，默认3篇，最多5篇

    Returns:
        Markdown格式的文章搜索结果，包含标题、摘要、关键要点
    """
    try:
        # 限制最大结果数
        max_results = min(max_results, 5)

        vector_store = _get_vector_store()

        # 执行语义搜索
        results = vector_store.search(
            query=query,
            n_results=max_results,
            article_type=article_type,
            status="published"  # 只搜索已发布文章
        )

        if not results:
            return f"未找到与「{query}」相关的文章内容。建议尝试更换关键词或使用其他工具查询。"

        # 格式化输出
        output_parts = [f"## 找到 {len(results)} 篇相关文章\n"]

        type_labels = {
            "strategy": "策略",
            "tips": "技巧",
            "review": "评测",
            "spot": "钓点"
        }

        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            content = result.get("content", "")
            score = result.get("score", 0)

            title = metadata.get("title", "无标题")
            article_type_value = metadata.get("article_type", "")
            type_label = type_labels.get(article_type_value, "文章")
            tags = metadata.get("tags", "")

            output_parts.append(f"### {i}. {title} [{type_label}]")
            output_parts.append(f"**相关度**: {score:.0%}")

            if tags:
                output_parts.append(f"**标签**: {tags}")

            # 提取关键内容片段
            if content:
                # 内容通常是 "标题\n摘要\n正文"，取正文部分
                content_lines = content.split('\n', 2)
                if len(content_lines) > 2:
                    main_content = content_lines[2]
                else:
                    main_content = content

                content_preview = main_content[:500]
                if len(main_content) > 500:
                    content_preview += "..."
                output_parts.append(f"\n**内容摘要**:\n{content_preview}")

            output_parts.append("")  # 空行分隔

        return "\n".join(output_parts)

    except Exception as e:
        logger.error(f"文章搜索失败: {e}")
        return f"文章搜索暂时不可用，请稍后重试。错误信息: {str(e)}"
