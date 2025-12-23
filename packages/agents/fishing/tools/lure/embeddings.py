"""
Embedding提供商模块

提供统一的Embedding API接口，支持多种提供商：
- DashScope (通义千问)
- 未来可扩展：OpenAI, 智谱AI等
"""

from abc import ABC, abstractmethod
from typing import List
import os


class EmbeddingProvider(ABC):
    """Embedding提供商抽象基类"""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表，每个向量是float列表
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        单个查询向量化

        Args:
            text: 查询文本

        Returns:
            向量（float列表）
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass


class DashScopeEmbedding(EmbeddingProvider):
    """通义千问DashScope Embedding"""

    def __init__(self, model: str = "text-embedding-v3"):
        """
        初始化DashScope Embedding

        Args:
            model: 模型名称
                - text-embedding-v3: 1024维（推荐，最新版本）
                - text-embedding-v2: 1536维
        """
        self.model = model
        self.api_key = os.getenv("DASHSCOPE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY not found in environment. "
                "Please set it in .env file."
            )

        # 模型维度映射（注意：v3是1024维，v2是1536维）
        self._dimension = 1024 if model == "text-embedding-v3" else 1536

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not texts:
            return []

        try:
            from dashscope import TextEmbedding
            import dashscope

            dashscope.api_key = self.api_key

            # DashScope 支持批量，但限制25条/次
            batch_size = 25
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                resp = TextEmbedding.call(
                    model=self.model,
                    input=batch
                )

                if resp.status_code != 200:
                    raise RuntimeError(
                        f"DashScope API error: {resp.message} "
                        f"(status_code: {resp.status_code})"
                    )

                # 提取embeddings并按顺序排列
                embeddings = [
                    item['embedding']
                    for item in resp.output['embeddings']
                ]
                all_embeddings.extend(embeddings)

            return all_embeddings

        except ImportError:
            raise RuntimeError(
                "dashscope package not installed. "
                "Run: uv add dashscope"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to embed texts: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        """
        单个查询向量化

        Args:
            text: 查询文本

        Returns:
            向量
        """
        return self.embed_texts([text])[0]

    @property
    def dimension(self) -> int:
        """向量维度"""
        return self._dimension


def get_embedding_provider(
    provider: str = "dashscope",
    model: str = None
) -> EmbeddingProvider:
    """
    获取Embedding提供商实例（工厂函数）

    Args:
        provider: 提供商名称 (dashscope | openai | zhipu)
        model: 模型名称（可选，使用默认值）

    Returns:
        EmbeddingProvider实例
    """
    # 从环境变量读取配置
    if model is None:
        model = os.getenv("VECTOR_EMBEDDING_MODEL", "text-embedding-v3")

    if provider == "dashscope":
        return DashScopeEmbedding(model=model)
    # 未来可扩展其他提供商
    # elif provider == "openai":
    #     return OpenAIEmbedding(model=model)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
