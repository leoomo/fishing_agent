"""
鱼类知识服务模块

提供鱼类知识查询功能：
- 鱼类基础信息查询
- 知识内容检索
- 季节活动查询
- 语义搜索（需要向量库支持）
"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class FishInfo:
    """鱼类基础信息"""
    id: int
    name_cn: str
    name_en: Optional[str] = None
    category: str = ""
    habitat: str = ""
    lure_difficulty: str = ""
    recommended_lures: List[str] = field(default_factory=list)
    recommended_rigs: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)

    # 扩展信息
    active_temp_min: Optional[float] = None
    active_temp_max: Optional[float] = None
    feeding_habits: Optional[str] = None
    fight_intensity: Optional[str] = None


@dataclass
class KnowledgeItem:
    """知识条目"""
    id: int
    knowledge_type: str
    title: str
    content: str
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    species_id: Optional[int] = None
    fish_name: Optional[str] = None


class FishKnowledgeService:
    """鱼类知识服务"""

    def __init__(self, db, image_manager=None, vector_store=None):
        """
        初始化鱼类知识服务

        Args:
            db: 数据库实例
            image_manager: 图片管理器（可选）
            vector_store: 向量存储（可选，用于语义搜索）
        """
        self.db = db
        self.image_manager = image_manager
        self.vector_store = vector_store

    # ========== 鱼类查询 ==========

    def get_fish_by_id(self, fish_id: int) -> Optional[FishInfo]:
        """根据ID查询鱼类"""
        query = "SELECT * FROM fish_species WHERE species_id = ?"
        rows = self.db.execute(query, (fish_id,))

        if rows:
            return self._row_to_fish_info(rows[0])
        return None

    def get_fish_by_name(self, name: str) -> Optional[FishInfo]:
        """
        根据名称查询鱼类（支持别名）

        Args:
            name: 鱼类名称（中文名、英文名或别名）

        Returns:
            FishInfo对象或None
        """
        query = """
            SELECT * FROM fish_species
            WHERE name_cn = ?
               OR name_en = ?
               OR aliases LIKE ?
        """
        rows = self.db.execute(query, (name, name, f'%"{name}"%'))

        if rows:
            return self._row_to_fish_info(rows[0])
        return None

    def search_fish(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        habitat: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[FishInfo]:
        """
        搜索鱼类

        Args:
            category: 分类（淡水/海水/广盐）
            difficulty: 路亚难度（新手/进阶/高手）
            habitat: 栖息水层
            keyword: 关键词（搜索名称和别名）

        Returns:
            匹配的鱼类列表
        """
        query = "SELECT * FROM fish_species WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if difficulty:
            query += " AND lure_difficulty = ?"
            params.append(difficulty)
        if habitat:
            query += " AND habitat LIKE ?"
            params.append(f"%{habitat}%")
        if keyword:
            query += " AND (name_cn LIKE ? OR name_en LIKE ? OR aliases LIKE ?)"
            params.extend([f"%{keyword}%"] * 3)

        query += " ORDER BY name_cn"

        rows = self.db.execute(query, tuple(params))
        return [self._row_to_fish_info(row) for row in rows]

    def get_all_fish(self) -> List[FishInfo]:
        """获取所有鱼类"""
        query = "SELECT * FROM fish_species ORDER BY category, name_cn"
        rows = self.db.execute(query)
        return [self._row_to_fish_info(row) for row in rows]

    def get_fish_with_images(self, fish_id: int) -> Optional[Dict[str, Any]]:
        """
        获取鱼类完整信息（含图片）

        Args:
            fish_id: 鱼类ID

        Returns:
            包含鱼类信息和图片的字典
        """
        fish = self.get_fish_by_id(fish_id)
        if not fish:
            return None

        images = []
        main_image = None
        if self.image_manager:
            images = self.image_manager.get_fish_images(fish_id)
            main_image = next(
                (img for img in images if img.image_type == 'main'),
                images[0] if images else None
            )

        return {
            "fish": fish,
            "images": images,
            "main_image": main_image
        }

    # ========== 知识查询 ==========

    def get_knowledge_by_fish(
        self,
        fish_id: int,
        knowledge_type: Optional[str] = None
    ) -> List[KnowledgeItem]:
        """
        获取特定鱼类的知识

        Args:
            fish_id: 鱼类ID
            knowledge_type: 知识类型（可选）
                - behavior: 习性行为
                - habitat: 栖息环境
                - season: 季节特性
                - technique: 钓法技巧
                - lure_match: 拟饵匹配
                - rig_match: 钓组匹配

        Returns:
            知识条目列表
        """
        query = """
            SELECT fk.*, fs.name_cn as fish_name
            FROM fish_knowledge fk
            LEFT JOIN fish_species fs ON fk.species_id = fs.species_id
            WHERE fk.species_id = ?
        """
        params = [fish_id]

        if knowledge_type:
            query += " AND fk.knowledge_type = ?"
            params.append(knowledge_type)

        query += " ORDER BY fk.knowledge_type, fk.id"

        rows = self.db.execute(query, tuple(params))
        return [self._row_to_knowledge(row) for row in rows]

    def get_general_knowledge(
        self,
        knowledge_type: Optional[str] = None
    ) -> List[KnowledgeItem]:
        """获取通用知识（不关联特定鱼类）"""
        query = """
            SELECT * FROM fish_knowledge
            WHERE species_id IS NULL
        """
        params = []

        if knowledge_type:
            query += " AND knowledge_type = ?"
            params.append(knowledge_type)

        query += " ORDER BY knowledge_type, id"

        rows = self.db.execute(query, tuple(params))
        return [self._row_to_knowledge(row) for row in rows]

    def get_knowledge_by_id(self, knowledge_id: int) -> Optional[KnowledgeItem]:
        """根据ID获取知识条目"""
        query = """
            SELECT fk.*, fs.name_cn as fish_name
            FROM fish_knowledge fk
            LEFT JOIN fish_species fs ON fk.species_id = fs.species_id
            WHERE fk.id = ?
        """
        rows = self.db.execute(query, (knowledge_id,))
        return self._row_to_knowledge(rows[0]) if rows else None

    def search_knowledge(self, keyword: str) -> List[KnowledgeItem]:
        """
        关键词搜索知识

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的知识条目列表
        """
        query = """
            SELECT fk.*, fs.name_cn as fish_name
            FROM fish_knowledge fk
            LEFT JOIN fish_species fs ON fk.species_id = fs.species_id
            WHERE fk.title LIKE ?
               OR fk.content LIKE ?
               OR fk.keywords LIKE ?
               OR fk.tags LIKE ?
        """
        pattern = f"%{keyword}%"
        rows = self.db.execute(query, (pattern, pattern, pattern, pattern))
        return [self._row_to_knowledge(row) for row in rows]

    def semantic_search(
        self,
        query_text: str,
        top_k: int = 5,
        knowledge_type: Optional[str] = None
    ) -> List[KnowledgeItem]:
        """
        语义搜索知识（需要向量库支持）

        Args:
            query_text: 查询文本
            top_k: 返回数量
            knowledge_type: 限定知识类型

        Returns:
            匹配的知识条目列表
        """
        if not self.vector_store:
            # 降级为关键词搜索
            return self.search_knowledge(query_text)[:top_k]

        # 构建过滤器
        filters = {}
        if knowledge_type:
            filters["type"] = knowledge_type

        # 向量搜索
        results = self.vector_store.search_by_text(
            collection="fish_knowledge",
            query_text=query_text,
            top_k=top_k,
            filters=filters if filters else None
        )

        # 根据ID查询完整内容
        knowledge_ids = [int(r.metadata.get("knowledge_id", 0)) for r in results]
        return self.get_knowledge_by_ids(knowledge_ids)

    def get_knowledge_by_ids(self, knowledge_ids: List[int]) -> List[KnowledgeItem]:
        """批量获取知识条目"""
        if not knowledge_ids:
            return []

        placeholders = ",".join(["?"] * len(knowledge_ids))
        query = f"""
            SELECT fk.*, fs.name_cn as fish_name
            FROM fish_knowledge fk
            LEFT JOIN fish_species fs ON fk.species_id = fs.species_id
            WHERE fk.id IN ({placeholders})
        """
        rows = self.db.execute(query, tuple(knowledge_ids))

        # 按输入顺序排序
        id_to_row = {row['id']: row for row in rows}
        return [
            self._row_to_knowledge(id_to_row[kid])
            for kid in knowledge_ids
            if kid in id_to_row
        ]

    # ========== 推荐查询 ==========

    def get_lure_recommendations(self, fish_id: int) -> Optional[Dict[str, Any]]:
        """
        获取针对特定鱼种的拟饵推荐

        Args:
            fish_id: 鱼类ID

        Returns:
            推荐信息字典
        """
        fish = self.get_fish_by_id(fish_id)
        if not fish:
            return None

        return {
            "fish": fish.name_cn,
            "difficulty": fish.lure_difficulty,
            "recommended_lures": fish.recommended_lures,
            "recommended_rigs": fish.recommended_rigs,
            "feeding_habits": fish.feeding_habits,
            "active_temp_range": (fish.active_temp_min, fish.active_temp_max)
        }

    def get_fish_for_lure(self, lure_type: str) -> List[FishInfo]:
        """
        查询适合某种拟饵的鱼类

        Args:
            lure_type: 拟饵类型（如：米诺、VIB、软虫）

        Returns:
            适合的鱼类列表
        """
        query = """
            SELECT * FROM fish_species
            WHERE recommended_lures LIKE ?
        """
        rows = self.db.execute(query, (f'%"{lure_type}"%',))
        return [self._row_to_fish_info(row) for row in rows]

    def get_fish_for_rig(self, rig_name: str) -> List[FishInfo]:
        """
        查询适合某种钓组的鱼类

        Args:
            rig_name: 钓组名称（如：德州钓组）

        Returns:
            适合的鱼类列表
        """
        query = """
            SELECT * FROM fish_species
            WHERE recommended_rigs LIKE ?
        """
        rows = self.db.execute(query, (f'%"{rig_name}"%',))
        return [self._row_to_fish_info(row) for row in rows]

    # ========== 数据写入 ==========

    def add_fish(self, fish_data: Dict[str, Any]) -> int:
        """添加鱼类"""
        # 处理JSON字段
        for json_field in ['aliases', 'active_seasons', 'prey_types',
                           'recommended_lures', 'recommended_rigs',
                           'recommended_rod_power']:
            if json_field in fish_data and isinstance(fish_data[json_field], list):
                fish_data[json_field] = json.dumps(fish_data[json_field], ensure_ascii=False)

        columns = ', '.join(fish_data.keys())
        placeholders = ', '.join(['?'] * len(fish_data))
        query = f"INSERT INTO fish_species ({columns}) VALUES ({placeholders})"

        return self.db.execute_write(query, tuple(fish_data.values()))

    def add_knowledge(
        self,
        title: str,
        content: str,
        knowledge_type: str,
        species_id: Optional[int] = None,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        source: Optional[str] = None
    ) -> int:
        """添加知识条目"""
        query = """
            INSERT INTO fish_knowledge (
                species_id, knowledge_type, title, content,
                summary, tags, keywords, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            species_id, knowledge_type, title, content,
            summary,
            json.dumps(tags, ensure_ascii=False) if tags else None,
            keywords, source
        )
        return self.db.execute_write(query, params)

    # ========== 私有方法 ==========

    def _row_to_fish_info(self, row: Dict) -> FishInfo:
        """将数据库行转换为FishInfo对象"""
        return FishInfo(
            id=row.get('species_id') or row.get('id'),
            name_cn=row['name_cn'],
            name_en=row.get('name_en'),
            category=row.get('category', ''),
            habitat=row.get('habitat', ''),
            lure_difficulty=row.get('lure_difficulty', ''),
            recommended_lures=self._parse_json_list(row.get('recommended_lures')),
            recommended_rigs=self._parse_json_list(row.get('recommended_rigs')),
            aliases=self._parse_json_list(row.get('aliases')),
            active_temp_min=row.get('active_temp_min'),
            active_temp_max=row.get('active_temp_max'),
            feeding_habits=row.get('feeding_habits'),
            fight_intensity=row.get('fight_intensity')
        )

    def _row_to_knowledge(self, row: Dict) -> KnowledgeItem:
        """将数据库行转换为KnowledgeItem对象"""
        return KnowledgeItem(
            id=row['id'],
            knowledge_type=row['knowledge_type'],
            title=row['title'],
            content=row['content'],
            summary=row.get('summary'),
            tags=self._parse_json_list(row.get('tags')),
            species_id=row.get('species_id'),
            fish_name=row.get('fish_name')
        )

    def _parse_json_list(self, value: Optional[str]) -> List[str]:
        """解析JSON列表字段"""
        if not value:
            return []
        try:
            result = json.loads(value)
            return result if isinstance(result, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
