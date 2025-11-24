"""
知识搜索服务模块

提供统一的知识搜索接口：
- 语义搜索鱼类知识
- 语义搜索钓组知识
- 以图搜图识别
- 跨模态搜索（文字搜图片）
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class KnowledgeSearchResult:
    """知识搜索结果"""
    id: int
    score: float
    title: str
    content: str
    knowledge_type: str
    fish_name: Optional[str] = None
    tags: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class RigSearchResult:
    """钓组搜索结果"""
    id: int
    score: float
    name: str
    description: str
    difficulty: Optional[str] = None
    usage_scenario: Optional[str] = None
    target_fish: Optional[str] = None


@dataclass
class ImageSearchResult:
    """图片搜索结果"""
    score: float
    entity_type: str  # equipment, rig, fish
    entity_id: int
    entity: Dict[str, Any]
    image: Dict[str, Any]


class KnowledgeSearchService:
    """知识搜索服务"""

    # 集合名称常量（与KnowledgeIndexer保持一致）
    COLLECTION_FISH_KNOWLEDGE = "fish_knowledge"
    COLLECTION_RIG_KNOWLEDGE = "rig_knowledge"
    COLLECTION_EQUIPMENT_DESC = "equipment_descriptions"
    COLLECTION_IMAGE_EMBEDDINGS = "image_embeddings"

    def __init__(self, db, vector_store, image_manager=None):
        """
        初始化知识搜索服务

        Args:
            db: 数据库实例
            vector_store: 向量存储实例
            image_manager: 图片管理器（可选）
        """
        self.db = db
        self.vector_store = vector_store
        self.image_manager = image_manager

    # ========== 鱼类知识搜索 ==========

    def search_fish_knowledge(
        self,
        query: str,
        knowledge_types: Optional[List[str]] = None,
        fish_name: Optional[str] = None,
        fish_id: Optional[int] = None,
        top_k: int = 5,
        min_score: float = 0.01
    ) -> List[KnowledgeSearchResult]:
        """
        语义搜索鱼类知识

        Args:
            query: 查询文本
            knowledge_types: 知识类型过滤（behavior/habitat/season/technique/lure_match/rig_match）
            fish_name: 鱼名过滤
            fish_id: 鱼ID过滤
            top_k: 返回数量
            min_score: 最低相似度阈值

        Returns:
            KnowledgeSearchResult列表
        """
        # 构建过滤器
        filters = {}
        if knowledge_types:
            if len(knowledge_types) == 1:
                filters["type"] = knowledge_types[0]
            else:
                filters["type"] = {"$in": knowledge_types}
        if fish_id:
            filters["fish_id"] = fish_id
        if fish_name:
            filters["fish_name"] = fish_name

        # 向量搜索
        results = self.vector_store.search_by_text(
            collection=self.COLLECTION_FISH_KNOWLEDGE,
            query_text=query,
            top_k=top_k,
            filters=filters if filters else None
        )

        # 过滤低分结果
        results = [r for r in results if r.score >= min_score]

        if not results:
            return []

        # 获取完整内容
        knowledge_ids = [int(r.metadata.get("knowledge_id", 0)) for r in results]
        return self._get_knowledge_details(knowledge_ids, results)

    def search_knowledge(
        self,
        query: str,
        knowledge_types: Optional[List[str]] = None,
        fish_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索知识（兼容旧接口）

        Args:
            query: 查询文本
            knowledge_types: 知识类型过滤
            fish_id: 鱼ID过滤
            top_k: 返回数量

        Returns:
            知识字典列表
        """
        results = self.search_fish_knowledge(
            query=query,
            knowledge_types=knowledge_types,
            fish_id=fish_id,
            top_k=top_k
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "title": r.title,
                "content": r.content,
                "knowledge_type": r.knowledge_type,
                "fish_name": r.fish_name,
                "tags": r.tags
            }
            for r in results
        ]

    # ========== 钓组知识搜索 ==========

    def search_rig_knowledge(
        self,
        query: str,
        difficulty: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.01
    ) -> List[RigSearchResult]:
        """
        语义搜索钓组知识

        Args:
            query: 查询文本
            difficulty: 难度过滤（新手/进阶/高手）
            top_k: 返回数量
            min_score: 最低相似度阈值

        Returns:
            RigSearchResult列表
        """
        filters = {}
        if difficulty:
            filters["difficulty"] = difficulty

        results = self.vector_store.search_by_text(
            collection=self.COLLECTION_RIG_KNOWLEDGE,
            query_text=query,
            top_k=top_k,
            filters=filters if filters else None
        )

        results = [r for r in results if r.score >= min_score]

        if not results:
            return []

        rig_ids = [int(r.metadata.get("rig_type_id", 0)) for r in results]
        return self._get_rig_details(rig_ids, results)

    def search_rig(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索钓组知识（兼容旧接口）

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            钓组字典列表
        """
        results = self.search_rig_knowledge(query=query, top_k=top_k)

        return [
            {
                "id": r.id,
                "score": r.score,
                "name": r.name,
                "description": r.description,
                "difficulty": r.difficulty,
                "usage_scenario": r.usage_scenario,
                "target_fish": r.target_fish
            }
            for r in results
        ]

    # ========== 装备描述搜索 ==========

    def search_equipment_by_description(
        self,
        query: str,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        通过描述语义搜索装备

        Args:
            query: 查询描述
            category: 类别过滤（鱼竿/渔轮/鱼线/拟饵）
            brand: 品牌过滤
            top_k: 返回数量
            min_score: 最低相似度阈值

        Returns:
            装备字典列表
        """
        filters = {}
        if category:
            filters["category"] = category
        if brand:
            filters["brand"] = brand

        results = self.vector_store.search_by_text(
            collection=self.COLLECTION_EQUIPMENT_DESC,
            query_text=query,
            top_k=top_k,
            filters=filters if filters else None
        )

        results = [r for r in results if r.score >= min_score]

        if not results:
            return []

        equipment_ids = [int(r.metadata.get("equipment_id", 0)) for r in results]
        return self._get_equipment_details(equipment_ids, results)

    # ========== 图片搜索 ==========

    def identify_image(
        self,
        image_path: str,
        entity_type: Optional[str] = None,
        top_k: int = 3,
        min_score: float = 0.5
    ) -> List[ImageSearchResult]:
        """
        以图搜图识别

        Args:
            image_path: 查询图片路径
            entity_type: 实体类型过滤（equipment/rig/fish）
            top_k: 返回数量
            min_score: 最低相似度阈值

        Returns:
            ImageSearchResult列表
        """
        filters = {"entity_type": entity_type} if entity_type else None

        results = self.vector_store.search_by_image(
            collection=self.COLLECTION_IMAGE_EMBEDDINGS,
            image_path=image_path,
            top_k=top_k,
            filters=filters
        )

        results = [r for r in results if r.score >= min_score]

        return self._get_image_entity_details(results)

    def search_image_by_description(
        self,
        description: str,
        entity_type: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[ImageSearchResult]:
        """
        用文字描述搜索图片（跨模态）

        Args:
            description: 图片描述文本
            entity_type: 实体类型过滤（equipment/rig/fish）
            top_k: 返回数量
            min_score: 最低相似度阈值

        Returns:
            ImageSearchResult列表
        """
        filters = {"entity_type": entity_type} if entity_type else None

        results = self.vector_store.search_image_by_text(
            collection=self.COLLECTION_IMAGE_EMBEDDINGS,
            query_text=description,
            top_k=top_k,
            filters=filters
        )

        results = [r for r in results if r.score >= min_score]

        return self._get_image_entity_details(results)

    # ========== 综合搜索 ==========

    def unified_search(
        self,
        query: str,
        search_types: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        统一搜索接口

        Args:
            query: 查询文本
            search_types: 搜索类型列表（knowledge/rig/equipment）
            top_k: 每类返回数量

        Returns:
            各类型搜索结果的字典
        """
        if search_types is None:
            search_types = ["knowledge", "rig", "equipment"]

        results = {}

        if "knowledge" in search_types:
            results["knowledge"] = self.search_knowledge(query, top_k=top_k)

        if "rig" in search_types:
            results["rig"] = self.search_rig(query, top_k=top_k)

        if "equipment" in search_types:
            results["equipment"] = self.search_equipment_by_description(
                query, top_k=top_k
            )

        return results

    # ========== 私有方法 ==========

    def _get_knowledge_details(
        self,
        knowledge_ids: List[int],
        search_results
    ) -> List[KnowledgeSearchResult]:
        """获取知识详情"""
        if not knowledge_ids:
            return []

        placeholders = ",".join(["?"] * len(knowledge_ids))
        query = f"""
            SELECT fk.*, fs.name_cn as fish_name
            FROM fish_knowledge fk
            LEFT JOIN fish_species fs ON fk.fish_species_id = fs.id
            WHERE fk.id IN ({placeholders})
        """
        rows = self.db.execute(query, tuple(knowledge_ids))

        # 构建ID到行的映射
        row_map = {row['id']: row for row in rows}

        # 按搜索结果顺序返回
        results = []
        for sr in search_results:
            kid = int(sr.metadata.get("knowledge_id", 0))
            if kid in row_map:
                row = row_map[kid]
                results.append(KnowledgeSearchResult(
                    id=kid,
                    score=sr.score,
                    title=row['title'],
                    content=row['content'],
                    knowledge_type=row['knowledge_type'],
                    fish_name=row.get('fish_name'),
                    tags=row.get('tags'),
                    summary=row.get('summary')
                ))

        return results

    def _get_rig_details(
        self,
        rig_ids: List[int],
        search_results
    ) -> List[RigSearchResult]:
        """获取钓组详情"""
        if not rig_ids:
            return []

        placeholders = ",".join(["?"] * len(rig_ids))
        query = f"""
            SELECT * FROM rig_types
            WHERE id IN ({placeholders})
        """
        rows = self.db.execute(query, tuple(rig_ids))

        row_map = {row['id']: row for row in rows}

        results = []
        for sr in search_results:
            rid = int(sr.metadata.get("rig_type_id", 0))
            if rid in row_map:
                row = row_map[rid]
                results.append(RigSearchResult(
                    id=rid,
                    score=sr.score,
                    name=row['name_cn'],
                    description=row.get('description') or "",
                    difficulty=row.get('difficulty'),
                    usage_scenario=row.get('usage_scenario'),
                    target_fish=row.get('target_fish')
                ))

        return results

    def _get_equipment_details(
        self,
        equipment_ids: List[int],
        search_results
    ) -> List[Dict[str, Any]]:
        """获取装备详情"""
        if not equipment_ids:
            return []

        placeholders = ",".join(["?"] * len(equipment_ids))
        query = f"""
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.equipment_id IN ({placeholders})
        """
        rows = self.db.execute(query, tuple(equipment_ids))

        row_map = {row['equipment_id']: row for row in rows}

        results = []
        for sr in search_results:
            eid = int(sr.metadata.get("equipment_id", 0))
            if eid in row_map:
                row = row_map[eid]
                results.append({
                    "equipment_id": eid,
                    "score": sr.score,
                    "name": row['name'],
                    "category": row.get('category'),
                    "brand": row.get('brand_name'),
                    "description": row.get('description'),
                    "price_min": row.get('price_min'),
                    "price_max": row.get('price_max')
                })

        return results

    def _get_image_entity_details(
        self,
        search_results
    ) -> List[ImageSearchResult]:
        """获取图片关联实体详情"""
        results = []

        for sr in search_results:
            entity_type = sr.metadata.get("entity_type")
            entity_id = sr.metadata.get("entity_id")
            image_id = sr.metadata.get("image_id")

            if not entity_type or not entity_id:
                continue

            # 根据实体类型查询详情
            if entity_type == "equipment":
                entity = self._get_equipment(entity_id)
            elif entity_type == "rig":
                entity = self._get_rig(entity_id)
            elif entity_type == "fish":
                entity = self._get_fish(entity_id)
            else:
                entity = {}

            # 获取图片信息
            image = self._get_image(image_id) if image_id else {}

            results.append(ImageSearchResult(
                score=sr.score,
                entity_type=entity_type,
                entity_id=entity_id,
                entity=entity,
                image=image
            ))

        return results

    def _get_equipment(self, equipment_id: int) -> Dict[str, Any]:
        """获取装备信息"""
        query = """
            SELECT e.*, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.equipment_id = ?
        """
        rows = self.db.execute(query, (equipment_id,))
        return dict(rows[0]) if rows else {}

    def _get_rig(self, rig_id: int) -> Dict[str, Any]:
        """获取钓组信息"""
        query = "SELECT * FROM rig_types WHERE id = ?"
        rows = self.db.execute(query, (rig_id,))
        return dict(rows[0]) if rows else {}

    def _get_fish(self, fish_id: int) -> Dict[str, Any]:
        """获取鱼类信息"""
        query = "SELECT * FROM fish_species WHERE id = ?"
        rows = self.db.execute(query, (fish_id,))
        return dict(rows[0]) if rows else {}

    def _get_image(self, image_id: int) -> Dict[str, Any]:
        """获取图片信息"""
        query = "SELECT * FROM product_images WHERE image_id = ?"
        rows = self.db.execute(query, (image_id,))
        return dict(rows[0]) if rows else {}


# ========== 便捷函数 ==========

def create_search_service(
    db=None,
    vector_store=None,
    image_manager=None
) -> KnowledgeSearchService:
    """
    创建知识搜索服务的便捷函数

    Args:
        db: 数据库实例（可选，默认使用全局实例）
        vector_store: 向量存储实例（可选，默认使用全局实例）
        image_manager: 图片管理器（可选）

    Returns:
        KnowledgeSearchService实例
    """
    if db is None:
        from .database import get_db
        db = get_db()

    if vector_store is None:
        from .vector_store import get_vector_store
        vector_store = get_vector_store()

    return KnowledgeSearchService(db, vector_store, image_manager)
