"""
知识索引管理模块

提供知识向量化索引功能：
- 鱼类知识批量索引
- 钓组知识批量索引
- 图片向量化索引
- 增量/全量重建索引
"""

from typing import Dict, List, Optional, Any
from pathlib import Path


class KnowledgeIndexer:
    """知识索引管理器"""

    # 集合名称常量
    COLLECTION_FISH_KNOWLEDGE = "fish_knowledge"
    COLLECTION_RIG_KNOWLEDGE = "rig_knowledge"
    COLLECTION_EQUIPMENT_DESC = "equipment_descriptions"
    COLLECTION_IMAGE_EMBEDDINGS = "image_embeddings"

    def __init__(self, db, vector_store, image_manager=None):
        """
        初始化知识索引器

        Args:
            db: 数据库实例
            vector_store: 向量存储实例
            image_manager: 图片管理器（可选，用于图片索引）
        """
        self.db = db
        self.vector_store = vector_store
        self.image_manager = image_manager

    # ========== 鱼类知识索引 ==========

    def index_fish_knowledge(self, batch_size: int = 100) -> int:
        """
        索引鱼类知识（增量）

        Args:
            batch_size: 每批处理数量

        Returns:
            本次索引的数量
        """
        # 获取未索引的知识
        query = """
            SELECT fk.id, fk.fish_species_id, fk.knowledge_type,
                   fk.title, fk.content, fk.tags, fk.keywords,
                   fs.name_cn as fish_name
            FROM fish_knowledge fk
            LEFT JOIN fish_species fs ON fk.fish_species_id = fs.id
            WHERE fk.is_vectorized = 0 OR fk.is_vectorized IS NULL
            LIMIT ?
        """
        rows = self.db.execute(query, (batch_size,))

        if not rows:
            return 0

        # 准备数据
        texts = []
        ids = []
        metadatas = []

        for row in rows:
            # 组合文本：标题 + 鱼名 + 内容摘要 + 关键词
            parts = [row['title']]
            if row.get('fish_name'):
                parts.append(f"鱼种：{row['fish_name']}")
            if row.get('content'):
                # 内容截取前500字符
                parts.append(row['content'][:500])
            if row.get('keywords'):
                parts.append(f"关键词：{row['keywords']}")

            text = "\n".join(parts)
            texts.append(text)

            ids.append(f"fk_{row['id']}")

            metadatas.append({
                "knowledge_id": row['id'],
                "fish_id": row.get('fish_species_id'),
                "type": row['knowledge_type'],
                "fish_name": row.get('fish_name') or "",
                "tags": row.get('tags') or ""
            })

        # 添加到向量库
        self.vector_store.add_texts(
            collection=self.COLLECTION_FISH_KNOWLEDGE,
            texts=texts,
            ids=ids,
            metadatas=metadatas
        )

        # 更新索引状态
        knowledge_ids = [row['id'] for row in rows]
        self._mark_indexed("fish_knowledge", knowledge_ids)

        return len(rows)

    # ========== 钓组知识索引 ==========

    def index_rig_knowledge(self, batch_size: int = 100) -> int:
        """
        索引钓组知识（增量）

        Args:
            batch_size: 每批处理数量

        Returns:
            本次索引的数量
        """
        # 获取钓组类型和详细规格
        query = """
            SELECT rt.id, rt.name_cn, rt.name_en, rt.description,
                   rt.usage_scenario, rt.difficulty, rt.target_fish
            FROM rig_types rt
            WHERE rt.is_vectorized = 0 OR rt.is_vectorized IS NULL
            LIMIT ?
        """
        rows = self.db.execute(query, (batch_size,))

        if not rows:
            return 0

        texts = []
        ids = []
        metadatas = []

        for row in rows:
            # 组合文本
            parts = [row['name_cn']]
            if row.get('name_en'):
                parts.append(f"({row['name_en']})")
            if row.get('description'):
                parts.append(row['description'])
            if row.get('usage_scenario'):
                parts.append(f"适用场景：{row['usage_scenario']}")
            if row.get('target_fish'):
                parts.append(f"目标鱼种：{row['target_fish']}")

            text = "\n".join(parts)
            texts.append(text)

            ids.append(f"rt_{row['id']}")

            metadatas.append({
                "rig_type_id": row['id'],
                "name": row['name_cn'],
                "difficulty": row.get('difficulty') or "",
                "scenario": row.get('usage_scenario') or ""
            })

        self.vector_store.add_texts(
            collection=self.COLLECTION_RIG_KNOWLEDGE,
            texts=texts,
            ids=ids,
            metadatas=metadatas
        )

        # 更新索引状态
        rig_ids = [row['id'] for row in rows]
        self._mark_indexed("rig_types", rig_ids)

        return len(rows)

    # ========== 装备描述索引 ==========

    def index_equipment_descriptions(self, batch_size: int = 100) -> int:
        """
        索引装备描述（增量）

        Args:
            batch_size: 每批处理数量

        Returns:
            本次索引的数量
        """
        query = """
            SELECT e.equipment_id, e.name, e.category, e.description,
                   e.features, b.name_cn as brand_name
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.is_vectorized = 0 OR e.is_vectorized IS NULL
            LIMIT ?
        """
        rows = self.db.execute(query, (batch_size,))

        if not rows:
            return 0

        texts = []
        ids = []
        metadatas = []

        for row in rows:
            parts = [row['name']]
            if row.get('brand_name'):
                parts.append(f"品牌：{row['brand_name']}")
            if row.get('category'):
                parts.append(f"类别：{row['category']}")
            if row.get('description'):
                parts.append(row['description'][:300])
            if row.get('features'):
                parts.append(f"特点：{row['features']}")

            text = "\n".join(parts)
            texts.append(text)

            ids.append(f"eq_{row['equipment_id']}")

            metadatas.append({
                "equipment_id": row['equipment_id'],
                "name": row['name'],
                "category": row.get('category') or "",
                "brand": row.get('brand_name') or ""
            })

        self.vector_store.add_texts(
            collection=self.COLLECTION_EQUIPMENT_DESC,
            texts=texts,
            ids=ids,
            metadatas=metadatas
        )

        equipment_ids = [row['equipment_id'] for row in rows]
        self._mark_indexed("equipment", equipment_ids, id_column="equipment_id")

        return len(rows)

    # ========== 图片索引 ==========

    def index_images(self, batch_size: int = 50) -> int:
        """
        索引图片（增量）

        Args:
            batch_size: 每批处理数量

        Returns:
            本次索引的数量
        """
        query = """
            SELECT image_id, image_url, description, image_type,
                   equipment_id, rig_type_id, fish_species_id
            FROM product_images
            WHERE is_vectorized = 0 OR is_vectorized IS NULL
            LIMIT ?
        """
        rows = self.db.execute(query, (batch_size,))

        if not rows:
            return 0

        image_paths = []
        ids = []
        metadatas = []
        valid_indices = []

        for i, row in enumerate(rows):
            # 确定实体类型
            if row.get('equipment_id'):
                entity_type = "equipment"
                entity_id = row['equipment_id']
            elif row.get('rig_type_id'):
                entity_type = "rig"
                entity_id = row['rig_type_id']
            elif row.get('fish_species_id'):
                entity_type = "fish"
                entity_id = row['fish_species_id']
            else:
                continue

            # 获取图片路径
            image_path = self._url_to_path(row['image_url'])
            if not Path(image_path).exists():
                print(f"警告: 图片不存在 {image_path}")
                continue

            image_paths.append(image_path)
            ids.append(f"img_{row['image_id']}")
            metadatas.append({
                "image_id": row['image_id'],
                "entity_type": entity_type,
                "entity_id": entity_id,
                "image_type": row.get('image_type') or "",
                "description": row.get('description') or ""
            })
            valid_indices.append(i)

        if image_paths:
            self.vector_store.add_images(
                collection=self.COLLECTION_IMAGE_EMBEDDINGS,
                image_paths=image_paths,
                ids=ids,
                metadatas=metadatas
            )

            # 更新索引状态
            image_ids = [rows[i]['image_id'] for i in valid_indices]
            self._mark_images_indexed(image_ids)

        return len(image_paths)

    # ========== 批量操作 ==========

    def index_all(self) -> Dict[str, int]:
        """
        索引所有未索引的内容（增量）

        Returns:
            各类型索引数量的字典
        """
        results = {
            "fish_knowledge": 0,
            "rig_knowledge": 0,
            "equipment_descriptions": 0,
            "images": 0
        }

        # 索引鱼类知识
        while True:
            count = self.index_fish_knowledge()
            results["fish_knowledge"] += count
            if count == 0:
                break

        # 索引钓组知识
        while True:
            count = self.index_rig_knowledge()
            results["rig_knowledge"] += count
            if count == 0:
                break

        # 索引装备描述
        while True:
            count = self.index_equipment_descriptions()
            results["equipment_descriptions"] += count
            if count == 0:
                break

        # 索引图片
        while True:
            count = self.index_images()
            results["images"] += count
            if count == 0:
                break

        return results

    def reindex_all(self) -> Dict[str, int]:
        """
        重建所有索引（全量）

        Returns:
            各类型索引数量的字典
        """
        # 清空现有索引
        for collection in [
            self.COLLECTION_FISH_KNOWLEDGE,
            self.COLLECTION_RIG_KNOWLEDGE,
            self.COLLECTION_EQUIPMENT_DESC,
            self.COLLECTION_IMAGE_EMBEDDINGS
        ]:
            try:
                self.vector_store.clear_collection(collection)
            except Exception:
                pass

        # 重置索引状态
        self._reset_all_index_status()

        # 重新索引
        return self.index_all()

    def get_index_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "collections": {},
            "database": {}
        }

        # 向量库统计
        for collection in [
            self.COLLECTION_FISH_KNOWLEDGE,
            self.COLLECTION_RIG_KNOWLEDGE,
            self.COLLECTION_EQUIPMENT_DESC,
            self.COLLECTION_IMAGE_EMBEDDINGS
        ]:
            stats["collections"][collection] = \
                self.vector_store.get_collection_count(collection)

        # 数据库统计
        tables = [
            ("fish_knowledge", "id"),
            ("rig_types", "id"),
            ("equipment", "equipment_id"),
            ("product_images", "image_id")
        ]

        for table, id_col in tables:
            try:
                total = self.db.execute(f"SELECT COUNT(*) as cnt FROM {table}")[0]['cnt']
                indexed = self.db.execute(
                    f"SELECT COUNT(*) as cnt FROM {table} WHERE is_vectorized = 1"
                )[0]['cnt']
                stats["database"][table] = {
                    "total": total,
                    "indexed": indexed,
                    "pending": total - indexed
                }
            except Exception:
                stats["database"][table] = {"error": "表不存在或查询失败"}

        return stats

    # ========== 私有方法 ==========

    def _mark_indexed(
        self,
        table: str,
        ids: List[int],
        column: str = "is_vectorized",
        id_column: str = "id"
    ) -> None:
        """标记记录已索引"""
        if not ids:
            return

        placeholders = ",".join(["?"] * len(ids))
        query = f"UPDATE {table} SET {column} = 1 WHERE {id_column} IN ({placeholders})"
        self.db.execute_write(query, tuple(ids))

    def _mark_images_indexed(self, image_ids: List[int]) -> None:
        """标记图片已索引"""
        if not image_ids:
            return

        placeholders = ",".join(["?"] * len(image_ids))
        query = f"""
            UPDATE product_images
            SET is_vectorized = 1, embedding_id = 'img_' || image_id
            WHERE image_id IN ({placeholders})
        """
        self.db.execute_write(query, tuple(image_ids))

    def _reset_all_index_status(self) -> None:
        """重置所有索引状态"""
        tables = [
            "fish_knowledge",
            "rig_types",
            "equipment",
            "product_images"
        ]

        for table in tables:
            try:
                self.db.execute_write(
                    f"UPDATE {table} SET is_vectorized = 0"
                )
            except Exception:
                pass  # 表可能不存在或没有该列

        # 清除图片的embedding_id
        try:
            self.db.execute_write(
                "UPDATE product_images SET embedding_id = NULL"
            )
        except Exception:
            pass

    def _url_to_path(self, url: str) -> str:
        """将URL转换为本地路径"""
        if url.startswith("file://"):
            return url[7:]
        if url.startswith("/"):
            return url
        # 相对路径，基于图片管理器的根目录
        if self.image_manager:
            return str(Path(self.image_manager.storage.base_path) / url)
        return url


# ========== 便捷函数 ==========

def create_indexer(db=None, vector_store=None, image_manager=None) -> KnowledgeIndexer:
    """
    创建知识索引器的便捷函数

    Args:
        db: 数据库实例（可选，默认使用全局实例）
        vector_store: 向量存储实例（可选，默认使用全局实例）
        image_manager: 图片管理器（可选）

    Returns:
        KnowledgeIndexer实例
    """
    if db is None:
        from .database import get_db
        db = get_db()

    if vector_store is None:
        from .vector_store import get_vector_store
        vector_store = get_vector_store()

    return KnowledgeIndexer(db, vector_store, image_manager)
