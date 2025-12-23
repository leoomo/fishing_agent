"""
向量存储模块

提供基于Chroma的向量存储功能：
- 文本向量化和搜索（DashScope Embedding API）
- 图片向量化：当前已禁用（未来可扩展多模态API）
- 跨模态搜索：当前已禁用
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    score: float
    metadata: Dict[str, Any]
    document: Optional[str] = None


class VectorStoreAdapter(ABC):
    """向量存储适配器抽象基类"""

    @abstractmethod
    def add_texts(
        self,
        collection: str,
        texts: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """添加文本向量"""
        pass

    @abstractmethod
    def add_images(
        self,
        collection: str,
        image_paths: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """添加图片向量"""
        pass

    @abstractmethod
    def search_by_text(
        self,
        collection: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """文本查询"""
        pass

    @abstractmethod
    def search_by_image(
        self,
        collection: str,
        image_path: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """图片查询"""
        pass

    @abstractmethod
    def search_image_by_text(
        self,
        collection: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """跨模态搜索：文字搜图片"""
        pass

    @abstractmethod
    def delete(self, collection: str, ids: List[str]) -> None:
        """删除向量"""
        pass

    @abstractmethod
    def clear_collection(self, collection: str) -> None:
        """清空集合"""
        pass


class ChromaVectorStore(VectorStoreAdapter):
    """Chroma向量存储实现（使用DashScope Embedding API）"""

    # 默认存储路径
    DEFAULT_PERSIST_DIR = Path(__file__).parent / "data" / "vector_store"

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_provider=None
    ):
        """
        初始化Chroma向量存储

        Args:
            persist_directory: 持久化存储路径（默认为模块data目录）
            embedding_provider: Embedding提供商实例（默认使用DashScope）
        """
        self.persist_directory = persist_directory or str(self.DEFAULT_PERSIST_DIR)

        # 确保目录存在
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Chroma客户端（懒加载）
        self._client = None

        # Embedding提供商（懒加载）
        self._embedding_provider = embedding_provider

        # 图片功能禁用标记
        self._image_enabled = False

        # 集合缓存
        self._collections: Dict[str, Any] = {}

    @property
    def client(self):
        """懒加载Chroma客户端"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            except ImportError:
                raise ImportError(
                    "chromadb未安装，请运行: pip install chromadb"
                )
        return self._client

    @property
    def embedding_provider(self):
        """懒加载Embedding提供商"""
        if self._embedding_provider is None:
            try:
                from .embeddings import get_embedding_provider
                self._embedding_provider = get_embedding_provider()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize embedding provider: {e}")
        return self._embedding_provider

    def _get_collection(self, name: str):
        """获取或创建集合"""
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={
                    "hnsw:space": "cosine",  # 使用余弦相似度
                    "dimension": self.embedding_provider.dimension
                }
            )
        return self._collections[name]

    # ========== 文本操作 ==========

    def add_texts(
        self,
        collection: str,
        texts: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        添加文本向量

        Args:
            collection: 集合名称
            texts: 文本列表
            ids: ID列表
            metadatas: 元数据列表
        """
        if not texts:
            return

        # 使用DashScope Embedding API
        embeddings = self.embedding_provider.embed_texts(texts)

        col = self._get_collection(collection)
        col.add(
            embeddings=embeddings,
            documents=texts,
            ids=ids,
            metadatas=metadatas
        )

    def search_by_text(
        self,
        collection: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        文本语义搜索

        Args:
            collection: 集合名称
            query_text: 查询文本
            top_k: 返回数量
            filters: 元数据过滤器

        Returns:
            搜索结果列表
        """
        try:
            col = self.client.get_collection(name=collection)
        except Exception:
            return []  # 集合不存在，返回空结果

        # 使用DashScope Embedding API
        query_embedding = self.embedding_provider.embed_query(query_text)

        # 构建where过滤器
        where_filter = self._build_where_filter(filters) if filters else None

        results = col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        return self._parse_results(results)

    def update_texts(
        self,
        collection: str,
        texts: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        更新文本向量

        Args:
            collection: 集合名称
            texts: 文本列表
            ids: ID列表
            metadatas: 元数据列表
        """
        if not texts:
            return

        # 使用DashScope Embedding API
        embeddings = self.embedding_provider.embed_texts(texts)

        col = self._get_collection(collection)
        col.update(
            embeddings=embeddings,
            documents=texts,
            ids=ids,
            metadatas=metadatas
        )

    # ========== 图片操作（当前已禁用） ==========

    def add_images(
        self,
        collection: str,
        image_paths: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """添加图片向量 - 当前已禁用"""
        if not self._image_enabled:
            raise NotImplementedError(
                "图片embedding功能当前已禁用。"
                "如需启用，请配置本地模型或多模态API。"
            )

    def search_by_image(
        self,
        collection: str,
        image_path: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """以图搜图 - 当前已禁用"""
        raise NotImplementedError("图片embedding功能当前已禁用")

    def search_image_by_text(
        self,
        collection: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """跨模态搜索：用文字描述搜索图片 - 当前已禁用"""
        raise NotImplementedError("图片embedding功能当前已禁用")

    # ========== 删除操作 ==========

    def delete(self, collection: str, ids: List[str]) -> None:
        """删除指定向量"""
        if not ids:
            return
        col = self._get_collection(collection)
        col.delete(ids=ids)

    def clear_collection(self, collection: str) -> None:
        """清空集合"""
        try:
            self.client.delete_collection(collection)
            if collection in self._collections:
                del self._collections[collection]
        except Exception:
            pass  # 集合不存在时忽略

    def delete_collection(self, collection: str) -> None:
        """删除集合（clear_collection的别名）"""
        self.clear_collection(collection)

    # ========== 统计信息 ==========

    def get_collection_count(self, collection: str) -> int:
        """获取集合中的向量数量"""
        try:
            col = self._get_collection(collection)
            return col.count()
        except Exception:
            return 0

    def list_collections(self) -> List[str]:
        """列出所有集合"""
        return [c.name for c in self.client.list_collections()]

    # ========== 私有方法 ==========

    def _build_where_filter(self, filters: Dict) -> Dict:
        """
        构建Chroma where过滤器

        Args:
            filters: 简化的过滤器字典，如 {"knowledge_type": "behavior"}

        Returns:
            Chroma格式的where过滤器
        """
        if not filters:
            return None

        # 处理简单的相等过滤
        where = {}
        for key, value in filters.items():
            if isinstance(value, dict):
                # 已经是Chroma格式（如 {"$in": [...]}）
                where[key] = value
            else:
                # 简单相等
                where[key] = value

        return where if where else None

    def _parse_results(self, results: Dict) -> List[SearchResult]:
        """解析Chroma返回结果"""
        search_results = []

        if results['ids'] and results['ids'][0]:
            for i, id in enumerate(results['ids'][0]):
                # Chroma返回的是距离，需要转换为相似度分数
                # 对于余弦距离：similarity = 1 - distance
                distance = results['distances'][0][i] if results.get('distances') else 0
                score = 1 - distance

                search_results.append(SearchResult(
                    id=id,
                    score=score,
                    metadata=results['metadatas'][0][i] if results.get('metadatas') else {},
                    document=results['documents'][0][i] if results.get('documents') else None
                ))

        return search_results


# ========== 简化版向量存储（不依赖大型模型） ==========

class SimpleVectorStore(VectorStoreAdapter):
    """
    简化版向量存储

    不依赖大型Embedding模型，使用TF-IDF或简单的词向量。
    适用于测试或资源受限的环境。
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory
        self._collections: Dict[str, Dict] = {}

        # 如果有持久化目录，尝试加载
        if persist_directory:
            self._load()

    def add_texts(
        self,
        collection: str,
        texts: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """使用简单的关键词匹配代替向量搜索"""
        if collection not in self._collections:
            self._collections[collection] = {"items": {}}

        for i, id in enumerate(ids):
            self._collections[collection]["items"][id] = {
                "text": texts[i],
                "metadata": metadatas[i],
                "keywords": self._extract_keywords(texts[i])
            }

        self._save()

    def add_images(
        self,
        collection: str,
        image_paths: List[str],
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """简化版：只存储元数据，不支持真正的图片搜索"""
        if collection not in self._collections:
            self._collections[collection] = {"items": {}}

        for i, id in enumerate(ids):
            self._collections[collection]["items"][id] = {
                "image_path": image_paths[i],
                "metadata": metadatas[i]
            }

        self._save()

    def search_by_text(
        self,
        collection: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """使用关键词匹配进行搜索"""
        if collection not in self._collections:
            return []

        query_keywords = self._extract_keywords(query_text)
        results = []

        for id, item in self._collections[collection]["items"].items():
            if "keywords" not in item:
                continue

            # 检查过滤器
            if filters and not self._match_filters(item.get("metadata", {}), filters):
                continue

            # 计算关键词重叠度作为分数
            overlap = len(query_keywords & item["keywords"])
            if overlap > 0:
                score = overlap / max(len(query_keywords), len(item["keywords"]))
                results.append(SearchResult(
                    id=id,
                    score=score,
                    metadata=item.get("metadata", {}),
                    document=item.get("text")
                ))

        # 按分数排序并返回top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def search_by_image(
        self,
        collection: str,
        image_path: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """简化版：不支持真正的图片搜索，返回空结果"""
        return []

    def search_image_by_text(
        self,
        collection: str,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """简化版：基于元数据描述的关键词匹配"""
        if collection not in self._collections:
            return []

        query_keywords = self._extract_keywords(query_text)
        results = []

        for id, item in self._collections[collection]["items"].items():
            if filters and not self._match_filters(item.get("metadata", {}), filters):
                continue

            # 从元数据的描述字段提取关键词
            description = item.get("metadata", {}).get("description", "")
            if description:
                item_keywords = self._extract_keywords(description)
                overlap = len(query_keywords & item_keywords)
                if overlap > 0:
                    score = overlap / max(len(query_keywords), len(item_keywords))
                    results.append(SearchResult(
                        id=id,
                        score=score,
                        metadata=item.get("metadata", {})
                    ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete(self, collection: str, ids: List[str]) -> None:
        if collection in self._collections:
            for id in ids:
                self._collections[collection]["items"].pop(id, None)
            self._save()

    def clear_collection(self, collection: str) -> None:
        if collection in self._collections:
            del self._collections[collection]
            self._save()

    def get_collection_count(self, collection: str) -> int:
        if collection not in self._collections:
            return 0
        return len(self._collections[collection].get("items", {}))

    def list_collections(self) -> List[str]:
        return list(self._collections.keys())

    def _extract_keywords(self, text: str) -> set:
        """简单的关键词提取（支持中文）"""
        import re
        keywords = set()

        # 提取中文词组（连续汉字）
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
        for word in chinese_words:
            # 添加完整词组
            if len(word) >= 2:
                keywords.add(word)
            # 同时添加单个汉字（用于模糊匹配）
            for char in word:
                keywords.add(char)

        # 提取英文词
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        for word in english_words:
            if len(word) >= 2:
                keywords.add(word)

        return keywords

    def _match_filters(self, metadata: Dict, filters: Dict) -> bool:
        """检查元数据是否匹配过滤器"""
        for key, value in filters.items():
            if key.startswith("$"):
                # Chroma风格的操作符
                continue
            if metadata.get(key) != value:
                return False
        return True

    def _save(self):
        """保存到文件"""
        if self.persist_directory:
            import json
            path = Path(self.persist_directory) / "simple_store.json"
            path.parent.mkdir(parents=True, exist_ok=True)

            # 转换set为list以便JSON序列化
            serializable = {}
            for col_name, col_data in self._collections.items():
                serializable[col_name] = {"items": {}}
                for item_id, item in col_data.get("items", {}).items():
                    serializable[col_name]["items"][item_id] = {
                        k: list(v) if isinstance(v, set) else v
                        for k, v in item.items()
                    }

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)

    def _load(self):
        """从文件加载"""
        import json
        path = Path(self.persist_directory) / "simple_store.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)

            # 转换list回set
            self._collections = {}
            for col_name, col_data in loaded.items():
                self._collections[col_name] = {"items": {}}
                for item_id, item in col_data.get("items", {}).items():
                    self._collections[col_name]["items"][item_id] = {
                        k: set(v) if k == "keywords" and isinstance(v, list) else v
                        for k, v in item.items()
                    }


# ========== 工厂函数 ==========

_vector_store_instance: Optional[VectorStoreAdapter] = None


def get_vector_store(
    persist_directory: Optional[str] = None,
    use_simple: bool = False
) -> VectorStoreAdapter:
    """
    获取向量存储实例（单例模式）

    Args:
        persist_directory: 持久化目录
        use_simple: 是否使用简化版（不依赖大型模型）

    Returns:
        向量存储实例
    """
    global _vector_store_instance

    if _vector_store_instance is None:
        # 默认持久化目录
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent / "data" / "vector_store")

        if use_simple:
            _vector_store_instance = SimpleVectorStore(persist_directory)
        else:
            try:
                _vector_store_instance = ChromaVectorStore(persist_directory)
            except ImportError:
                print("警告: chromadb未安装，使用简化版向量存储")
                _vector_store_instance = SimpleVectorStore(persist_directory)

    return _vector_store_instance


def reset_vector_store():
    """重置向量存储实例"""
    global _vector_store_instance
    _vector_store_instance = None
