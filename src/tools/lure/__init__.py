"""
路亚装备工具模块

提供路亚装备推荐、对比、知识查询和图片识别功能。

模块结构：
- database.py: 数据库访问层
- image_manager.py: 图片存储和管理
- fish_knowledge.py: 鱼类知识服务
- comparator.py: 装备对比服务
- formatters.py: 输出格式化
- vector_store.py: 向量存储（Chroma）
- knowledge_indexer.py: 知识索引管理
- knowledge_search.py: 知识搜索服务
"""

from .database import LureDatabase, get_db, reset_db
from .image_manager import (
    ImageManager,
    LocalImageStorage,
    ImageStorageAdapter,
    ImageInfo,
    ImageMetadata
)
from .fish_knowledge import (
    FishKnowledgeService,
    FishInfo,
    KnowledgeItem
)
from .comparator import (
    EquipmentComparator,
    ComparisonResult,
    ComparisonItem
)
from .formatters import (
    format_recommendation,
    format_comparison,
    format_fish_knowledge,
    format_rig_guide,
    format_identification,
    format_package_recommendation
)
from .vector_store import (
    VectorStoreAdapter,
    ChromaVectorStore,
    SimpleVectorStore,
    SearchResult,
    get_vector_store,
    reset_vector_store
)
from .knowledge_indexer import (
    KnowledgeIndexer,
    create_indexer
)
from .knowledge_search import (
    KnowledgeSearchService,
    KnowledgeSearchResult,
    RigSearchResult,
    ImageSearchResult,
    create_search_service
)

__all__ = [
    # Database
    'LureDatabase',
    'get_db',
    'reset_db',
    # Image
    'ImageManager',
    'LocalImageStorage',
    'ImageStorageAdapter',
    'ImageInfo',
    'ImageMetadata',
    # Fish Knowledge
    'FishKnowledgeService',
    'FishInfo',
    'KnowledgeItem',
    # Comparator
    'EquipmentComparator',
    'ComparisonResult',
    'ComparisonItem',
    # Formatters
    'format_recommendation',
    'format_comparison',
    'format_fish_knowledge',
    'format_rig_guide',
    'format_identification',
    'format_package_recommendation',
    # Vector Store
    'VectorStoreAdapter',
    'ChromaVectorStore',
    'SimpleVectorStore',
    'SearchResult',
    'get_vector_store',
    'reset_vector_store',
    # Knowledge Indexer
    'KnowledgeIndexer',
    'create_indexer',
    # Knowledge Search
    'KnowledgeSearchService',
    'KnowledgeSearchResult',
    'RigSearchResult',
    'ImageSearchResult',
    'create_search_service',
]
