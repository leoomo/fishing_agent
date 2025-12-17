"""
路亚装备工具模块

提供路亚装备推荐、对比、知识查询和图片识别功能。

模块结构：
- database.py: 数据库访问层
- image_manager.py: 图片存储和管理
- fish_knowledge.py: 鱼类知识服务
- comparator.py: 装备对比服务
- formatters.py: 输出格式化
- embeddings.py: Embedding提供商（DashScope等）
- vector_store.py: 向量存储（Chroma）
- knowledge_indexer.py: 知识索引管理
- knowledge_search.py: 知识搜索服务
- cli.py: CLI管理工具
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
from .embeddings import (
    EmbeddingProvider,
    DashScopeEmbedding,
    get_embedding_provider
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

# Image Processing
from .image_merger import ImageMerger, create_image_merger
from .batch_merge_processor import (
    BatchMergeProcessor,
    MergeGroup,
    create_batch_processor
)
from .merge_split_processor import (
    MergeAndSplitProcessor,
    BlankRowDetector,
    ImageSplitter,
    BlankRegion,
    ContentRegion,
    create_merge_split_processor
)
from .text_region_detector import (
    TextRegionDetector,
    TextRegionCropper,
    TextBox,
    CropRegion,
    crop_text_area,
    detect_text_boxes
)
from .ocr_merge_processor import (
    OCRMergeProcessor,
    ProcessedImage,
    ProcessingResult,
    create_ocr_merge_processor
)


def create_processor(
    source_dir: str,
    strategy: str = "smart_group",
    **kwargs
):
    """
    创建图片处理器

    Args:
        source_dir: 源图片目录
        strategy: 处理策略
            - "smart_group": 原有策略（底部+头部文字检测，智能分组合并）
            - "merge_split": 先合并所有图片，再按空白切割
            - "ocr_crop": 使用 PaddleOCR 精准裁剪文字区域后合并（推荐）

    Returns:
        处理器实例
    """
    if strategy == "ocr_crop":
        return OCRMergeProcessor(source_dir, **kwargs)
    elif strategy == "merge_split":
        return MergeAndSplitProcessor(source_dir, **kwargs)
    else:
        return BatchMergeProcessor(source_dir, **kwargs)


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
    # Embeddings
    'EmbeddingProvider',
    'DashScopeEmbedding',
    'get_embedding_provider',
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
    # Image Processing
    'ImageMerger',
    'create_image_merger',
    'BatchMergeProcessor',
    'MergeGroup',
    'create_batch_processor',
    'MergeAndSplitProcessor',
    'BlankRowDetector',
    'ImageSplitter',
    'BlankRegion',
    'ContentRegion',
    'create_merge_split_processor',
    'create_processor',
    # Text Region Detection (PaddleOCR)
    'TextRegionDetector',
    'TextRegionCropper',
    'TextBox',
    'CropRegion',
    'crop_text_area',
    'detect_text_boxes',
    # OCR Merge Processor
    'OCRMergeProcessor',
    'ProcessedImage',
    'ProcessingResult',
    'create_ocr_merge_processor',
]
