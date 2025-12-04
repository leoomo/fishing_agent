"""
基于用户装备的推荐增强器

提供三种推荐策略：
1. 升级推荐 - 根据用户现有装备推荐更高级的同类装备
2. 完善推荐 - 推荐缺失的装备类型
3. 搭配推荐 - 检查装备是否匹配并给出建议
"""

import logging
from typing import List, Dict, Any, Optional

from .manager import UserEquipmentManager
from ..lure.database import LureDatabase
from ..lure.recommender import LureRecommender

logger = logging.getLogger(__name__)


class UserBasedRecommender:
    """基于用户装备的推荐增强器"""

    # 装备等级映射
    TIER_LEVELS = {
        "入门": 1,
        "中端": 2,
        "高端": 3,
        "旗舰": 4,
        "未知": 0,
    }

    # 基础装备要求
    ESSENTIAL_CATEGORIES = ["鱼竿", "渔轮", "鱼线"]

    def __init__(self, db: LureDatabase, manager: UserEquipmentManager):
        """
        初始化推荐器

        Args:
            db: 数据库实例
            manager: 用户装备管理器
        """
        self.db = db
        self.manager = manager
        self.lure_recommender = LureRecommender(db)
        logger.info("初始化基于用户装备的推荐器")

    # ========== 升级推荐 ==========

    def recommend_upgrade(self, user_id: int) -> str:
        """
        升级推荐策略

        分析用户装备水平，找出薄弱环节，推荐同类更高一级装备

        Args:
            user_id: 用户ID

        Returns:
            Markdown格式的升级推荐报告
        """
        try:
            # 获取用户装备列表
            equipment_list = self.manager.list_user_equipment(user_id)

            if not equipment_list:
                return "# 装备升级推荐\n\n您的装备库为空，无法提供升级建议。请先添加您现有的装备。"

            output = "# 装备升级推荐\n\n"

            # 按类别分组分析
            by_category = self._group_by_category(equipment_list)

            upgradeable_items = []

            for category, items in by_category.items():
                # 分析该类别的平均水平
                avg_level = self._analyze_category_level(items)

                # 找出低于平均水平的装备
                for item in items:
                    item_level = self._get_equipment_tier_level(item.equipment_id)

                    if item_level < avg_level or item_level <= 2:  # 中端及以下建议升级
                        upgradeable_items.append(
                            {
                                "current": item,
                                "current_level": item_level,
                                "category": category,
                            }
                        )

            if not upgradeable_items:
                output += "✅ 您的装备已经很不错了！暂无明显需要升级的装备。\n\n"
                output += "如果预算充足，可以考虑尝试旗舰级装备以获得更好的使用体验。"
                return output

            output += f"分析您的 {len(equipment_list)} 件装备后，发现以下升级建议：\n\n"

            # 对每个可升级装备给出建议
            for i, item_info in enumerate(upgradeable_items, 1):
                current = item_info["current"]
                category = item_info["category"]

                output += f"## {i}. {category} - {current.equipment_name}\n\n"

                # 当前装备信息
                brand_model = (
                    f"{current.brand_name} {current.model}"
                    if current.model
                    else current.brand_name or "未知品牌"
                )
                output += f"**当前装备**: {brand_model}\n"

                if current.purchase_price:
                    output += f"**购买价格**: ¥{current.purchase_price:.2f}\n"

                # 查询升级推荐
                upgrade_suggestions = self._find_upgrade_equipment(
                    current.equipment_id, category
                )

                if upgrade_suggestions:
                    output += f"\n**升级建议** (共{len(upgrade_suggestions)}个选项):\n\n"

                    for j, eq in enumerate(upgrade_suggestions[:3], 1):  # 最多显示3个
                        output += f"{j}. **{eq['equipment_name']}**\n"
                        output += f"   - 品牌: {eq['brand_name']}\n"

                        if eq.get("price_min"):
                            output += f"   - 价格区间: ¥{eq['price_min']:.2f}"
                            if eq.get("price_max"):
                                output += f" - ¥{eq['price_max']:.2f}"
                            output += "\n"

                        if eq.get("description"):
                            output += f"   - 特点: {eq['description'][:100]}...\n"

                        output += "\n"
                else:
                    output += "\n暂无更高级的同类装备推荐。\n\n"

            return output

        except Exception as e:
            logger.error(f"升级推荐失败: {e}", exc_info=True)
            return f"❌ 升级推荐失败: {str(e)}"

    def _find_upgrade_equipment(
        self, current_equipment_id: int, category: str
    ) -> List[Dict[str, Any]]:
        """
        查找升级装备

        Args:
            current_equipment_id: 当前装备ID
            category: 装备类别

        Returns:
            升级装备列表
        """
        # 获取当前装备信息
        current_eq = self.db.execute(
            """
            SELECT e.*, b.tier
            FROM equipment e
            LEFT JOIN brands b ON e.brand_id = b.id
            WHERE e.equipment_id = ?
            """,
            (current_equipment_id,),
        )

        if not current_eq:
            return []

        current = current_eq[0]
        current_tier_level = self.TIER_LEVELS.get(current.get("tier", "未知"), 0)

        # 查询更高级的同类装备
        query = """
        SELECT
            e.equipment_id,
            e.name AS equipment_name,
            e.category,
            b.name_cn AS brand_name,
            b.tier,
            e.model,
            e.price_min,
            e.price_max,
            e.description,
            e.user_level
        FROM equipment e
        LEFT JOIN brands b ON e.brand_id = b.id
        WHERE e.category = ?
            AND e.is_active = 1
            AND e.equipment_id != ?
        ORDER BY
            CASE b.tier
                WHEN '旗舰' THEN 4
                WHEN '高端' THEN 3
                WHEN '中端' THEN 2
                WHEN '入门' THEN 1
                ELSE 0
            END DESC,
            e.price_min DESC
        LIMIT 10
        """

        rows = self.db.execute(query, (category, current_equipment_id))

        # 过滤出真正升级的装备
        upgrades = []
        for row in rows:
            tier_level = self.TIER_LEVELS.get(row.get("tier", "未知"), 0)

            # 如果等级更高，或者价格更高，则认为是升级
            if tier_level > current_tier_level or (
                row.get("price_min") and current.get("price_min")
                and row["price_min"] > current["price_min"] * 1.2  # 价格至少高20%
            ):
                upgrades.append(dict(row))

        return upgrades

    # ========== 完善推荐 ==========

    def recommend_complete_set(self, user_id: int) -> str:
        """
        配置完善策略

        检查基础装备是否齐全，推荐缺失装备和拟饵组合

        Args:
            user_id: 用户ID

        Returns:
            Markdown格式的完善推荐报告
        """
        try:
            # 获取用户信息
            user = self.manager.get_user(user_id)
            user_level = user.get("user_level", "新手") if user else "新手"

            # 获取用户装备列表
            equipment_list = self.manager.list_user_equipment(user_id)

            # 获取缺失的装备类型
            missing_categories = self.manager.get_missing_equipment_types(user_id)

            output = "# 装备配置完善建议\n\n"

            # 1. 检查基础装备
            if missing_categories:
                output += "## ⚠️ 基础装备缺失\n\n"
                output += "路亚钓鱼的基础三件套（鱼竿、渔轮、鱼线）缺少以下装备：\n\n"

                for category in missing_categories:
                    output += f"### {category}\n\n"

                    # 根据用户水平推荐该类别装备
                    recommendations = self._recommend_by_category(category, user_level)

                    if recommendations:
                        output += f"**推荐装备** (根据您的水平：{user_level}):\n\n"

                        for i, eq in enumerate(recommendations[:3], 1):
                            output += f"{i}. **{eq['equipment_name']}**\n"
                            output += f"   - 品牌: {eq['brand_name']}\n"

                            if eq.get("price_min"):
                                output += f"   - 价格: ¥{eq['price_min']:.2f}"
                                if eq.get("price_max"):
                                    output += f" - ¥{eq['price_max']:.2f}"
                                output += "\n"

                            if eq.get("description"):
                                output += f"   - 说明: {eq['description'][:100]}...\n"

                            output += "\n"
                    else:
                        output += "暂无该类装备推荐。\n\n"

            else:
                output += "✅ 您的基础装备已齐全（鱼竿、渔轮、鱼线）！\n\n"

            # 2. 推荐拟饵
            output += "## 🎣 拟饵推荐\n\n"

            # 检查是否有拟饵
            has_lures = any(eq.category == "拟饵" for eq in equipment_list)

            if not has_lures:
                output += "您的装备库中暂无拟饵，建议添加以下常用拟饵：\n\n"

                # 推荐基础拟饵组合
                lure_recommendations = self._recommend_basic_lures(user_level)

                for i, lure in enumerate(lure_recommendations[:5], 1):
                    output += f"{i}. **{lure['equipment_name']}**\n"
                    output += f"   - 品牌: {lure['brand_name']}\n"
                    output += f"   - 适用: {lure.get('target_fish', '通用')}\n"

                    if lure.get("price_min"):
                        output += f"   - 价格: ¥{lure['price_min']:.2f}\n"

                    output += "\n"
            else:
                lure_count = sum(1 for eq in equipment_list if eq.category == "拟饵")
                output += f"您已有 {lure_count} 种拟饵，可以尝试更多饵型以应对不同场景。\n"

            # 3. 其他建议
            output += "\n## 💡 其他建议\n\n"

            if len(equipment_list) < 5:
                output += "- 建议逐步丰富装备库，可以根据实际钓场环境和目标鱼种选择合适装备\n"
            else:
                output += "- 您的装备库已较为丰富，可以专注于提升装备品质或探索新的钓法\n"

            output += "- 使用 `recommend_based_on_my_equipment` 工具获取装备搭配建议\n"

            return output

        except Exception as e:
            logger.error(f"完善推荐失败: {e}", exc_info=True)
            return f"❌ 完善推荐失败: {str(e)}"

    def _recommend_by_category(
        self, category: str, user_level: str
    ) -> List[Dict[str, Any]]:
        """
        根据类别和用户水平推荐装备

        Args:
            category: 装备类别
            user_level: 用户水平

        Returns:
            推荐装备列表
        """
        query = """
        SELECT
            e.equipment_id,
            e.name AS equipment_name,
            e.category,
            b.name_cn AS brand_name,
            e.model,
            e.price_min,
            e.price_max,
            e.description,
            e.user_level
        FROM equipment e
        LEFT JOIN brands b ON e.brand_id = b.id
        WHERE e.category = ?
            AND e.is_active = 1
            AND (e.user_level = ? OR e.user_level IS NULL)
        ORDER BY e.price_min ASC
        LIMIT 5
        """

        rows = self.db.execute(query, (category, user_level))
        return [dict(row) for row in rows]

    def _recommend_basic_lures(self, user_level: str) -> List[Dict[str, Any]]:
        """
        推荐基础拟饵组合

        Args:
            user_level: 用户水平

        Returns:
            拟饵推荐列表
        """
        query = """
        SELECT
            e.equipment_id,
            e.name AS equipment_name,
            b.name_cn AS brand_name,
            e.price_min,
            e.target_fish
        FROM equipment e
        LEFT JOIN brands b ON e.brand_id = b.id
        WHERE e.category = '拟饵'
            AND e.is_active = 1
            AND (e.user_level = ? OR e.user_level IS NULL)
        ORDER BY e.price_min ASC
        LIMIT 10
        """

        rows = self.db.execute(query, (user_level,))
        return [dict(row) for row in rows]

    # ========== 搭配推荐 ==========

    def recommend_matching(self, user_id: int) -> str:
        """
        装备搭配分析策略

        检查鱼竿和渔轮是否匹配，鱼线是否适配，给出搭配建议

        Args:
            user_id: 用户ID

        Returns:
            Markdown格式的搭配分析报告
        """
        try:
            # 获取用户装备列表
            equipment_list = self.manager.list_user_equipment(user_id)

            if not equipment_list:
                return "# 装备搭配分析\n\n您的装备库为空，无法进行搭配分析。"

            output = "# 装备搭配分析\n\n"

            # 按类别分组
            by_category = self._group_by_category(equipment_list)

            # 获取关键装备
            rods = by_category.get("鱼竿", [])
            reels = by_category.get("渔轮", [])
            lines = by_category.get("鱼线", [])

            # 1. 检查基础装备完整性
            output += "## 装备完整性检查\n\n"

            completeness = []
            if rods:
                completeness.append(f"✅ 鱼竿: {len(rods)}件")
            else:
                completeness.append("❌ 鱼竿: 缺失")

            if reels:
                completeness.append(f"✅ 渔轮: {len(reels)}件")
            else:
                completeness.append("❌ 渔轮: 缺失")

            if lines:
                completeness.append(f"✅ 鱼线: {len(lines)}件")
            else:
                completeness.append("❌ 鱼线: 缺失")

            output += " | ".join(completeness) + "\n\n"

            # 2. 鱼竿 - 渔轮匹配分析
            if rods and reels:
                output += "## 鱼竿 - 渔轮 搭配分析\n\n"

                for rod in rods:
                    rod_specs = self._get_rod_specs(rod.equipment_id)

                    if rod_specs:
                        output += f"### {rod.equipment_name}\n\n"
                        output += f"**规格**: 长度 {rod_specs.get('length', '未知')}"

                        if rod_specs.get("power"):
                            output += f" | 硬度 {rod_specs['power']}"
                        output += "\n\n"

                        # 推荐匹配的渔轮
                        matching_reels = self._find_matching_reels(rod_specs, reels)

                        if matching_reels:
                            output += "**匹配的渔轮**:\n"
                            for reel in matching_reels:
                                output += f"- ✅ {reel.equipment_name}\n"
                        else:
                            output += "⚠️ 您的渔轮可能与此鱼竿不太匹配，建议检查轮型和尺寸。\n"

                        output += "\n"
            else:
                if not rods:
                    output += "⚠️ 缺少鱼竿，无法进行搭配分析\n\n"
                if not reels:
                    output += "⚠️ 缺少渔轮，无法进行搭配分析\n\n"

            # 3. 鱼线匹配分析
            if lines:
                output += "## 鱼线配置分析\n\n"

                for line in lines:
                    line_specs = self._get_line_specs(line.equipment_id)

                    if line_specs:
                        output += f"- **{line.equipment_name}**"

                        if line_specs.get("line_type"):
                            output += f" (线型: {line_specs['line_type']})"

                        if line_specs.get("strength_lb"):
                            output += f" | 拉力: {line_specs['strength_lb']}lb"

                        output += "\n"

                output += "\n💡 建议根据鱼竿的硬度和目标鱼种选择合适拉力的鱼线。\n\n"
            else:
                output += "## 鱼线配置\n\n⚠️ 您的装备库中暂无鱼线，建议添加。\n\n"

            # 4. 总体建议
            output += "## 💡 总体建议\n\n"

            issues = []
            if not rods:
                issues.append("缺少鱼竿")
            if not reels:
                issues.append("缺少渔轮")
            if not lines:
                issues.append("缺少鱼线")

            if issues:
                output += f"- 您的装备配置存在以下问题: {', '.join(issues)}\n"
                output += "- 建议使用 `recommend_based_on_my_equipment` 工具获取完善建议\n"
            else:
                output += "- ✅ 您的基础装备已齐全\n"
                output += "- 建议根据实际钓场和目标鱼种调整装备搭配\n"
                output += "- 可以尝试不同的拟饵以提升钓获率\n"

            return output

        except Exception as e:
            logger.error(f"搭配分析失败: {e}", exc_info=True)
            return f"❌ 搭配分析失败: {str(e)}"

    def _find_matching_reels(
        self, rod_specs: Dict[str, Any], reels: List[Any]
    ) -> List[Any]:
        """
        查找匹配的渔轮

        根据鱼竿规格匹配渔轮（简化版，实际需要更复杂的匹配逻辑）

        Args:
            rod_specs: 鱼竿规格
            reels: 用户的渔轮列表

        Returns:
            匹配的渔轮列表
        """
        # 简化匹配逻辑：所有渔轮都认为可能匹配
        # 实际应该根据鱼竿长度、硬度匹配渔轮型号和尺寸
        return reels

    # ========== 辅助方法 ==========

    def _group_by_category(self, equipment_list: List[Any]) -> Dict[str, List[Any]]:
        """按类别分组"""
        from collections import defaultdict

        by_category = defaultdict(list)
        for eq in equipment_list:
            by_category[eq.category].append(eq)
        return dict(by_category)

    def _analyze_category_level(self, items: List[Any]) -> int:
        """
        分析某类别装备的平均水平

        Args:
            items: 装备列表

        Returns:
            平均水平（1-4）
        """
        if not items:
            return 0

        levels = []
        for item in items:
            level = self._get_equipment_tier_level(item.equipment_id)
            levels.append(level)

        return int(sum(levels) / len(levels)) if levels else 0

    def _get_equipment_tier_level(self, equipment_id: int) -> int:
        """
        获取装备的等级水平

        Args:
            equipment_id: 装备ID

        Returns:
            等级水平（0-4）
        """
        query = """
        SELECT b.tier
        FROM equipment e
        LEFT JOIN brands b ON e.brand_id = b.id
        WHERE e.equipment_id = ?
        """

        rows = self.db.execute(query, (equipment_id,))

        if rows and rows[0].get("tier"):
            return self.TIER_LEVELS.get(rows[0]["tier"], 0)

        return 0

    def _get_rod_specs(self, equipment_id: int) -> Optional[Dict[str, Any]]:
        """获取鱼竿规格"""
        query = "SELECT * FROM rod_specs WHERE equipment_id = ?"
        rows = self.db.execute(query, (equipment_id,))
        return dict(rows[0]) if rows else None

    def _get_line_specs(self, equipment_id: int) -> Optional[Dict[str, Any]]:
        """获取鱼线规格"""
        query = "SELECT * FROM line_specs WHERE equipment_id = ?"
        rows = self.db.execute(query, (equipment_id,))
        return dict(rows[0]) if rows else None
