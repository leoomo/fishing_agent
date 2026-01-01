"""
Article Vector Store Service

Uses ChromaDB for semantic search and RAG retrieval.
Integrates with DashScope Embedding API.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_PERSIST_DIR = "shared/data/chroma"


class DashScopeEmbeddingFunction:
    """
    Custom embedding function using DashScope Embedding API

    Uses text-embedding-v2 model from Alibaba Cloud.
    """

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY not set, vector search will be disabled")

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for input texts"""
        if not self.api_key:
            # Return zero vectors if API key not set
            return [[0.0] * 1536 for _ in input]

        try:
            import dashscope
            from dashscope import TextEmbedding

            dashscope.api_key = self.api_key

            embeddings = []
            # Process in batches of 25 (DashScope limit)
            batch_size = 25
            for i in range(0, len(input), batch_size):
                batch = input[i:i + batch_size]
                response = TextEmbedding.call(
                    model=TextEmbedding.Models.text_embedding_v2,
                    input=batch
                )

                if response.status_code == 200:
                    for item in response.output['embeddings']:
                        embeddings.append(item['embedding'])
                else:
                    logger.error(f"DashScope embedding failed: {response.message}")
                    # Return zero vectors on error
                    embeddings.extend([[0.0] * 1536 for _ in batch])

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [[0.0] * 1536 for _ in input]


class ArticleVectorStore:
    """
    Vector store for article content

    Features:
    - Upsert: Add or update article embeddings
    - Delete: Remove article from store
    - Search: Semantic search with metadata filtering
    - Similar: Find similar articles
    """

    def __init__(self, persist_dir: str = None):
        """
        Initialize vector store

        Args:
            persist_dir: Directory to persist ChromaDB data
        """
        if persist_dir is None:
            persist_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                DEFAULT_PERSIST_DIR
            )

        # Ensure directory exists
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self.persist_dir = persist_dir
        self.embedding_fn = DashScopeEmbeddingFunction()

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="articles",
            embedding_function=self.embedding_fn,
            metadata={"description": "Fishing articles for semantic search"}
        )

        logger.info(f"ArticleVectorStore initialized: persist_dir={persist_dir}")

    def upsert(
        self,
        article_id: int,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add or update article embedding

        Args:
            article_id: Article ID
            content: Article content (title + summary + content)
            metadata: Article metadata for filtering
                - article_type: strategy/tips/review/spot
                - status: draft/published/archived
                - tags: comma-separated tags
                - title: article title

        Returns:
            bool: Success status
        """
        try:
            doc_id = str(article_id)

            # Prepare metadata (ChromaDB only supports simple types)
            meta = {
                "article_id": article_id,
            }
            if metadata:
                if "article_type" in metadata:
                    meta["article_type"] = str(metadata["article_type"])
                if "status" in metadata:
                    meta["status"] = str(metadata["status"])
                if "title" in metadata:
                    meta["title"] = str(metadata["title"])[:100]
                if "tags" in metadata:
                    meta["tags"] = str(metadata["tags"])[:200]

            self.collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[meta]
            )

            logger.debug(f"Article upserted to vector store: id={article_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert article: {e}")
            return False

    def delete(self, article_id: int) -> bool:
        """
        Delete article from vector store

        Args:
            article_id: Article ID

        Returns:
            bool: Success status
        """
        try:
            doc_id = str(article_id)
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Article deleted from vector store: id={article_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete article: {e}")
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        article_type: Optional[str] = None,
        status: str = "published"
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for articles

        Args:
            query: Search query
            n_results: Number of results to return
            article_type: Filter by article type
            status: Filter by status (default: published)

        Returns:
            List of search results with id, score, and metadata
        """
        try:
            # Build where filter
            where = {}
            if status:
                where["status"] = status
            if article_type:
                where["article_type"] = article_type

            # Query collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where if where else None,
                include=["metadatas", "documents", "distances"]
            )

            # Format results
            formatted = []
            if results and results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted.append({
                        "id": int(doc_id),
                        "score": 1.0 - (results['distances'][0][i] if results['distances'] else 0),
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "content": results['documents'][0][i] if results['documents'] else ""
                    })

            return formatted

        except Exception as e:
            logger.error(f"Failed to search articles: {e}")
            return []

    def get_similar(
        self,
        article_id: int,
        n_results: int = 5,
        status: str = "published"
    ) -> List[Dict[str, Any]]:
        """
        Find similar articles

        Args:
            article_id: Source article ID
            n_results: Number of results
            status: Filter by status

        Returns:
            List of similar articles
        """
        try:
            doc_id = str(article_id)

            # Get the source document
            result = self.collection.get(
                ids=[doc_id],
                include=["documents"]
            )

            if not result['documents']:
                return []

            source_content = result['documents'][0]

            # Search for similar
            similar = self.search(
                query=source_content,
                n_results=n_results + 1,  # +1 to exclude self
                status=status
            )

            # Filter out the source article
            return [r for r in similar if r['id'] != article_id][:n_results]

        except Exception as e:
            logger.error(f"Failed to get similar articles: {e}")
            return []

    def count(self) -> int:
        """Get total number of articles in store"""
        return self.collection.count()


# Singleton instance
_vector_store: Optional[ArticleVectorStore] = None


def get_vector_store() -> ArticleVectorStore:
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = ArticleVectorStore()
    return _vector_store
