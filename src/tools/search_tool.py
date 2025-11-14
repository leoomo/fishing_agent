"""
LangChain Learning - Search Tool

信息搜索工具模块提供网络搜索和知识检索功能。
"""

import re
import json
from typing import Optional, Any, Dict, Union, List
import logging
from urllib.parse import urlencode, quote_plus
from core.base_tool import BaseTool, ConfigurableTool
from core.interfaces import ToolMetadata, ToolResult


class SearchTool(ConfigurableTool):
    """信息搜索工具类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._max_results = self.get_config_value("max_results", 10)
        self._timeout = self.get_config_value("timeout", 10)
        self._cache = {}  # 简单缓存
        self._cache_ttl = self.get_config_value("cache_ttl", 3600)  # 1小时缓存

        # 知识库数据（模拟）
        self._knowledge_base = {
            "technology": {
                "python": {
                    "description": "Python是一种高级编程语言，以简洁易读的语法著称。",
                    "features": ["动态类型", "自动内存管理", "面向对象", "丰富的标准库"],
                    "applications": ["Web开发", "数据科学", "人工智能", "自动化脚本"],
                    "created_by": "Guido van Rossum",
                    "first_release": "1991年"
                },
                "javascript": {
                    "description": "JavaScript是一种主要用于Web开发的编程语言。",
                    "features": ["动态类型", "事件驱动", "函数式编程", "原型继承"],
                    "applications": ["前端开发", "后端开发", "移动应用", "桌面应用"],
                    "created_by": "Brendan Eich",
                    "first_release": "1995年"
                },
                "langchain": {
                    "description": "LangChain是一个用于构建LLM应用的框架。",
                    "features": ["链式调用", "智能体", "记忆管理", "工具集成"],
                    "applications": ["聊天机器人", "问答系统", "文档分析", "代码生成"],
                    "created_by": "LangChain团队",
                    "first_release": "2022年"
                }
            },
            "science": {
                "quantum_computing": {
                    "description": "量子计算利用量子力学原理进行信息处理。",
                    "concepts": ["量子比特", "叠加态", "纠缠", "量子门"],
                    "advantages": ["并行计算", "特定问题指数级加速", "密码学应用"],
                    "challenges": ["量子退相干", "错误率", "扩展性问题"]
                },
                "artificial_intelligence": {
                    "description": "人工智能是使计算机模拟人类智能的技术。",
                    "types": ["机器学习", "深度学习", "自然语言处理", "计算机视觉"],
                    "applications": ["自动驾驶", "医疗诊断", "金融分析", "语音识别"],
                    "ethics": ["隐私保护", "算法公平", "就业影响", "安全风险"]
                }
            },
            "general": {
                "climate_change": {
                    "description": "气候变化是地球气候系统的长期变化。",
                    "causes": ["温室气体排放", "森林砍伐", "工业活动", "交通运输"],
                    "effects": ["全球变暖", "海平面上升", "极端天气", "生态系统破坏"],
                    "solutions": ["可再生能源", "碳捕获", "能源效率", "政策行动"]
                }
            }
        }

        # 常见搜索结果的模拟数据
        self._mock_search_results = {
            "python编程": [
                {
                    "title": "Python 官方文档",
                    "url": "https://docs.python.org/",
                    "snippet": "Python官方文档提供了完整的语言参考和标准库文档。",
                    "relevance": 0.95
                },
                {
                    "title": "Python 教程 - 菜鸟教程",
                    "url": "https://www.runoob.com/python",
                    "snippet": "Python是一种简单易学的编程语言，适合初学者入门。",
                    "relevance": 0.88
                }
            ],
            "人工智能": [
                {
                    "title": "人工智能 - 维基百科",
                    "url": "https://zh.wikipedia.org/wiki/人工智能",
                    "snippet": "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                    "relevance": 0.92
                },
                {
                    "title": "机器学习入门",
                    "url": "https://example.com/ml-intro",
                    "snippet": "机器学习是人工智能的一个子集，使计算机能够从数据中学习而无需明确编程。",
                    "relevance": 0.85
                }
            ]
        }

    @property
    def metadata(self) -> ToolMetadata:
        """工具元数据"""
        return ToolMetadata(
            name="search_tool",
            description="提供网络搜索和知识检索功能",
            version="1.0.0",
            author="langchain-learning",
            tags=["search", "information", "knowledge", "web"],
            dependencies=[]
        )

    def validate_input(self, **kwargs) -> bool:
        """验证输入参数"""
        operation = kwargs.get("operation")
        return operation in [
            "web_search", "knowledge_search", "search_by_category",
            "get_definition", "get_features", "get_applications",
            "search_similar", "advanced_search"
        ]

    async def _execute(self, **kwargs) -> ToolResult:
        """执行搜索操作"""
        operation = kwargs.get("operation")

        try:
            if operation == "web_search":
                return await self._web_search(**kwargs)
            elif operation == "knowledge_search":
                return await self._knowledge_search(**kwargs)
            elif operation == "search_by_category":
                return await self._search_by_category(**kwargs)
            elif operation == "get_definition":
                return await self._get_definition(**kwargs)
            elif operation == "get_features":
                return await self._get_features(**kwargs)
            elif operation == "get_applications":
                return await self._get_applications(**kwargs)
            elif operation == "search_similar":
                return await self._search_similar(**kwargs)
            elif operation == "advanced_search":
                return await self._advanced_search(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {operation}"
                )

        except Exception as e:
            self._logger.error(f"搜索工具执行失败: {str(e)}")
            return ToolResult(
                success=False,
                error=f"搜索工具执行失败: {str(e)}"
            )

    async def _web_search(self, query: str, max_results: Optional[int] = None, **kwargs) -> ToolResult:
        """网络搜索（模拟）"""
        try:
            max_results = max_results or self._max_results

            # 检查缓存
            cache_key = f"web_search:{query}:{max_results}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return ToolResult(
                    success=True,
                    data=cached_data,
                    metadata={"operation": "web_search", "source": "cache"}
                )

            # 模拟搜索结果
            results = self._mock_web_search(query, max_results)

            search_data = {
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_time": 0.3,
                "source": "模拟搜索引擎"
            }

            # 缓存结果
            self._set_cache(cache_key, search_data)

            return ToolResult(
                success=True,
                data=search_data,
                metadata={"operation": "web_search", "source": "mock_search"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"网络搜索失败: {str(e)}"
            )

    async def _knowledge_search(self, query: str, category: Optional[str] = None, **kwargs) -> ToolResult:
        """知识库搜索"""
        try:
            # 检查缓存
            cache_key = f"knowledge_search:{query}:{category or 'all'}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return ToolResult(
                    success=True,
                    data=cached_data,
                    metadata={"operation": "knowledge_search", "source": "cache"}
                )

            results = []

            # 如果指定了类别，只在特定类别中搜索
            if category and category in self._knowledge_base:
                results = self._search_in_category(self._knowledge_base[category], query, category)
            else:
                # 在所有类别中搜索
                for cat_name, cat_data in self._knowledge_base.items():
                    cat_results = self._search_in_category(cat_data, query, cat_name)
                    results.extend(cat_results)

            search_data = {
                "query": query,
                "category": category,
                "results": results,
                "total_results": len(results),
                "source": "本地知识库"
            }

            # 缓存结果
            self._set_cache(cache_key, search_data)

            return ToolResult(
                success=True,
                data=search_data,
                metadata={"operation": "knowledge_search", "source": "knowledge_base"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"知识库搜索失败: {str(e)}"
            )

    async def _search_by_category(self, category: str, **kwargs) -> ToolResult:
        """按类别搜索"""
        try:
            if category not in self._knowledge_base:
                return ToolResult(
                    success=False,
                    error=f"未知类别: {category}"
                )

            category_data = self._knowledge_base[category]

            # 格式化结果
            results = []
            for topic, data in category_data.items():
                result = {
                    "topic": topic,
                    "category": category,
                    "description": data.get("description", ""),
                    "summary": {k: v for k, v in data.items() if k != "description"}
                }
                results.append(result)

            return ToolResult(
                success=True,
                data={
                    "category": category,
                    "results": results,
                    "total_topics": len(results),
                    "source": "本地知识库"
                },
                metadata={"operation": "search_by_category"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"类别搜索失败: {str(e)}"
            )

    async def _get_definition(self, topic: str, category: Optional[str] = None, **kwargs) -> ToolResult:
        """获取定义"""
        try:
            definition = None
            source_category = None

            if category and category in self._knowledge_base:
                if topic in self._knowledge_base[category]:
                    definition = self._knowledge_base[category][topic].get("description")
                    source_category = category
            else:
                # 在所有类别中搜索
                for cat_name, cat_data in self._knowledge_base.items():
                    if topic in cat_data:
                        definition = cat_data[topic].get("description")
                        source_category = cat_name
                        break

            if definition:
                return ToolResult(
                    success=True,
                    data={
                        "topic": topic,
                        "definition": definition,
                        "category": source_category,
                        "source": "本地知识库"
                    },
                    metadata={"operation": "get_definition"}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"未找到主题 '{topic}' 的定义"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取定义失败: {str(e)}"
            )

    async def _get_features(self, topic: str, category: Optional[str] = None, **kwargs) -> ToolResult:
        """获取特性"""
        try:
            features = None
            source_category = None

            if category and category in self._knowledge_base:
                if topic in self._knowledge_base[category]:
                    features = self._knowledge_base[category][topic].get("features")
                    source_category = category
            else:
                # 在所有类别中搜索
                for cat_name, cat_data in self._knowledge_base.items():
                    if topic in cat_data:
                        features = cat_data[topic].get("features")
                        source_category = cat_name
                        break

            if features:
                return ToolResult(
                    success=True,
                    data={
                        "topic": topic,
                        "features": features,
                        "category": source_category,
                        "total_features": len(features),
                        "source": "本地知识库"
                    },
                    metadata={"operation": "get_features"}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"未找到主题 '{topic}' 的特性信息"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取特性失败: {str(e)}"
            )

    async def _get_applications(self, topic: str, category: Optional[str] = None, **kwargs) -> ToolResult:
        """获取应用"""
        try:
            applications = None
            source_category = None

            if category and category in self._knowledge_base:
                if topic in self._knowledge_base[category]:
                    applications = self._knowledge_base[category][topic].get("applications")
                    source_category = category
            else:
                # 在所有类别中搜索
                for cat_name, cat_data in self._knowledge_base.items():
                    if topic in cat_data:
                        applications = cat_data[topic].get("applications")
                        source_category = cat_name
                        break

            if applications:
                return ToolResult(
                    success=True,
                    data={
                        "topic": topic,
                        "applications": applications,
                        "category": source_category,
                        "total_applications": len(applications),
                        "source": "本地知识库"
                    },
                    metadata={"operation": "get_applications"}
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"未找到主题 '{topic}' 的应用信息"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"获取应用失败: {str(e)}"
            )

    async def _search_similar(self, query: str, threshold: float = 0.3, **kwargs) -> ToolResult:
        """相似搜索"""
        try:
            similar_results = []

            # 在所有类别中搜索相似内容
            for cat_name, cat_data in self._knowledge_base.items():
                for topic, data in cat_data.items():
                    similarity = self._calculate_similarity(query, topic)
                    if similarity >= threshold:
                        similar_results.append({
                            "topic": topic,
                            "category": cat_name,
                            "similarity": similarity,
                            "description": data.get("description", ""),
                            "match_type": self._get_match_type(similarity)
                        })

            # 按相似度排序
            similar_results.sort(key=lambda x: x["similarity"], reverse=True)

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "threshold": threshold,
                    "results": similar_results,
                    "total_results": len(similar_results),
                    "source": "本地知识库"
                },
                metadata={"operation": "search_similar"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"相似搜索失败: {str(e)}"
            )

    async def _advanced_search(self, query: str, filters: Optional[Dict] = None, **kwargs) -> ToolResult:
        """高级搜索"""
        try:
            filters = filters or {}
            max_results = filters.get("max_results", self._max_results)
            categories = filters.get("categories", [])
            include_web = filters.get("include_web", True)
            include_knowledge = filters.get("include_knowledge", True)

            all_results = []

            # 网络搜索
            if include_web:
                web_result = await self._web_search(query, max_results // 2)
                if web_result.success:
                    for item in web_result.data["results"]:
                        item["source_type"] = "web"
                        all_results.append(item)

            # 知识库搜索
            if include_knowledge:
                if categories:
                    for category in categories:
                        knowledge_result = await self._knowledge_search(query, category)
                        if knowledge_result.success:
                            for item in knowledge_result.data["results"]:
                                item["source_type"] = "knowledge"
                                all_results.append(item)
                else:
                    knowledge_result = await self._knowledge_search(query)
                    if knowledge_result.success:
                        for item in knowledge_result.data["results"]:
                            item["source_type"] = "knowledge"
                            all_results.append(item)

            # 去重和排序
            unique_results = self._deduplicate_results(all_results)
            final_results = unique_results[:max_results]

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "filters": filters,
                    "results": final_results,
                    "total_results": len(final_results),
                    "source": "混合搜索"
                },
                metadata={"operation": "advanced_search"}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"高级搜索失败: {str(e)}"
            )

    def _mock_web_search(self, query: str, max_results: int) -> List[Dict]:
        """模拟网络搜索结果"""
        # 检查预定义的搜索结果
        for key, results in self._mock_search_results.items():
            if key.lower() in query.lower():
                return results[:max_results]

        # 生成通用搜索结果
        return [
            {
                "title": f"关于 {query} 的搜索结果",
                "url": f"https://example.com/search?q={quote_plus(query)}",
                "snippet": f"这是关于{query}的模拟搜索结果摘要。",
                "relevance": 0.8
            },
            {
                "title": f"{query} - 维基百科",
                "url": "https://zh.wikipedia.org/wiki/" + quote_plus(query),
                "snippet": f"{query}的相关信息和详细介绍。",
                "relevance": 0.75
            }
        ][:max_results]

    def _search_in_category(self, category_data: Dict, query: str, category_name: str) -> List[Dict]:
        """在特定类别中搜索"""
        results = []
        query_lower = query.lower()

        for topic, data in category_data.items():
            # 检查主题名匹配
            topic_match = query_lower in topic.lower()

            # 检查描述匹配
            description = data.get("description", "")
            desc_match = query_lower in description.lower()

            # 检查其他字段匹配
            other_match = False
            for key, value in data.items():
                if key != "description" and isinstance(value, list):
                    if any(query_lower in str(item).lower() for item in value):
                        other_match = True
                        break

            if topic_match or desc_match or other_match:
                relevance = 0.0
                if topic_match:
                    relevance += 0.5
                if desc_match:
                    relevance += 0.3
                if other_match:
                    relevance += 0.2

                results.append({
                    "topic": topic,
                    "category": category_name,
                    "description": description,
                    "relevance": min(relevance, 1.0),
                    "match_details": {
                        "topic_match": topic_match,
                        "description_match": desc_match,
                        "other_match": other_match
                    }
                })

        # 按相关性排序
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results

    def _calculate_similarity(self, query: str, topic: str) -> float:
        """计算查询和主题的相似度"""
        query_lower = query.lower()
        topic_lower = topic.lower()

        # 简单的相似度计算
        if query_lower == topic_lower:
            return 1.0

        # 检查包含关系
        if query_lower in topic_lower or topic_lower in query_lower:
            return 0.8

        # 检查词汇重叠
        query_words = set(query_lower.split())
        topic_words = set(topic_lower.split())

        if not query_words or not topic_words:
            return 0.0

        intersection = query_words & topic_words
        union = query_words | topic_words

        return len(intersection) / len(union) if union else 0.0

    def _get_match_type(self, similarity: float) -> str:
        """获取匹配类型"""
        if similarity >= 0.8:
            return "精确匹配"
        elif similarity >= 0.6:
            return "高度匹配"
        elif similarity >= 0.4:
            return "中度匹配"
        else:
            return "低度匹配"

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重搜索结果"""
        seen_titles = set()
        unique_results = []

        for result in results:
            title = result.get("title", "") or result.get("topic", "")
            if title not in seen_titles:
                seen_titles.add(title)
                unique_results.append(result)

        return unique_results

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if __import__('time').time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Dict) -> None:
        """设置缓存数据"""
        self._cache[key] = (data, __import__('time').time())

    def clear_cache(self) -> None:
        """清理缓存"""
        self._cache.clear()

    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        return {
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl,
            "knowledge_base_size": sum(len(cat) for cat in self._knowledge_base.values()),
            "categories": list(self._knowledge_base.keys())
        }

    def _validate_required_params(self, required_params: list, **kwargs) -> bool:
        """验证必需参数"""
        for param in required_params:
            if param not in kwargs or kwargs[param] is None:
                self._logger.error(f"缺少必需参数: {param}")
                return False
        return True