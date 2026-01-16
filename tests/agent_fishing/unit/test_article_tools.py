#!/usr/bin/env python3
"""
文章搜索工具单元测试

测试 search_fishing_articles 工具的功能
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSearchFishingArticles:
    """search_fishing_articles 工具测试"""

    @patch('packages.agents.fishing.tools.article_tools._get_vector_store')
    def test_search_returns_results(self, mock_get_store):
        """测试正常搜索返回结果"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        mock_store = MagicMock()
        mock_store.search.return_value = [
            {
                "id": 1,
                "score": 0.95,
                "metadata": {
                    "title": "路亚鲈鱼技巧",
                    "article_type": "tips",
                    "tags": "路亚,鲈鱼"
                },
                "content": "标题\n摘要\n路亚钓鲈鱼需要注意选择合适的拟饵..."
            }
        ]
        mock_get_store.return_value = mock_store

        result = search_fishing_articles.invoke({"query": "路亚鲈鱼"})

        assert "找到 1 篇相关文章" in result
        assert "路亚鲈鱼技巧" in result
        assert "技巧" in result
        assert "95%" in result  # 相关度

    @patch('packages.agents.fishing.tools.article_tools._get_vector_store')
    def test_search_no_results(self, mock_get_store):
        """测试无结果情况"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        mock_store = MagicMock()
        mock_store.search.return_value = []
        mock_get_store.return_value = mock_store

        result = search_fishing_articles.invoke({"query": "不存在的内容xyz"})

        assert "未找到" in result
        assert "不存在的内容xyz" in result

    @patch('packages.agents.fishing.tools.article_tools._get_vector_store')
    def test_search_with_type_filter(self, mock_get_store):
        """测试类型过滤"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        mock_store = MagicMock()
        mock_store.search.return_value = []
        mock_get_store.return_value = mock_store

        search_fishing_articles.invoke({
            "query": "装备推荐",
            "article_type": "review"
        })

        mock_store.search.assert_called_once_with(
            query="装备推荐",
            n_results=3,
            article_type="review",
            status="published"
        )

    @patch('packages.agents.fishing.tools.article_tools._get_vector_store')
    def test_search_with_custom_max_results(self, mock_get_store):
        """测试自定义返回数量"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        mock_store = MagicMock()
        mock_store.search.return_value = []
        mock_get_store.return_value = mock_store

        search_fishing_articles.invoke({
            "query": "钓鱼技巧",
            "max_results": 5
        })

        mock_store.search.assert_called_once_with(
            query="钓鱼技巧",
            n_results=5,
            article_type=None,
            status="published"
        )

    @patch('packages.agents.fishing.tools.article_tools._get_vector_store')
    def test_search_max_results_limit(self, mock_get_store):
        """测试最大结果数量限制（不超过5）"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        mock_store = MagicMock()
        mock_store.search.return_value = []
        mock_get_store.return_value = mock_store

        search_fishing_articles.invoke({
            "query": "钓鱼技巧",
            "max_results": 10  # 请求10个，但应该限制为5
        })

        mock_store.search.assert_called_once_with(
            query="钓鱼技巧",
            n_results=5,  # 限制为5
            article_type=None,
            status="published"
        )

    @patch('packages.agents.fishing.tools.article_tools._get_vector_store')
    def test_search_multiple_results(self, mock_get_store):
        """测试多个搜索结果"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        mock_store = MagicMock()
        mock_store.search.return_value = [
            {
                "id": 1,
                "score": 0.95,
                "metadata": {"title": "德州钓组详解", "article_type": "strategy", "tags": "德州钓组,路亚"},
                "content": "标题\n摘要\n德州钓组是最常用的软饵钓组之一..."
            },
            {
                "id": 2,
                "score": 0.85,
                "metadata": {"title": "卡罗莱纳钓组", "article_type": "strategy", "tags": "卡罗莱纳,钓组"},
                "content": "标题\n摘要\n卡罗莱纳钓组适合远投..."
            },
            {
                "id": 3,
                "score": 0.75,
                "metadata": {"title": "倒吊钓组入门", "article_type": "tips", "tags": "倒吊,新手"},
                "content": "标题\n摘要\n倒吊钓组是日系钓法..."
            }
        ]
        mock_get_store.return_value = mock_store

        result = search_fishing_articles.invoke({"query": "钓组"})

        assert "找到 3 篇相关文章" in result
        assert "德州钓组详解" in result
        assert "卡罗莱纳钓组" in result
        assert "倒吊钓组入门" in result
        assert "策略" in result  # article_type=strategy 显示为 策略
        assert "技巧" in result  # article_type=tips 显示为 技巧

    @patch('packages.agents.fishing.tools.article_tools._get_vector_store')
    def test_search_error_handling(self, mock_get_store):
        """测试错误处理"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        mock_store = MagicMock()
        mock_store.search.side_effect = Exception("数据库连接失败")
        mock_get_store.return_value = mock_store

        result = search_fishing_articles.invoke({"query": "测试"})

        assert "文章搜索暂时不可用" in result
        assert "数据库连接失败" in result


class TestToolRegistration:
    """工具注册测试"""

    def test_tool_is_registered(self):
        """测试工具已注册到 get_all_tools"""
        from packages.agents.fishing.tools import get_all_tools

        tools = get_all_tools()
        tool_names = [t.name for t in tools]

        assert "search_fishing_articles" in tool_names

    def test_tool_has_correct_description(self):
        """测试工具描述正确"""
        from packages.agents.fishing.tools.article_tools import search_fishing_articles

        assert "钓鱼" in search_fishing_articles.description
        assert "文章" in search_fishing_articles.description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
