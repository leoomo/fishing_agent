"""
用户装备管理 LangChain 工具

提供4个@tool装饰器工具供Agent调用：
1. list_my_equipment - 查看我的装备库
2. add_equipment_to_profile - 添加装备到装备库
3. remove_equipment_from_profile - 从装备库删除装备
4. recommend_based_on_my_equipment - 基于用户装备推荐
"""

import logging
from typing import Optional

from langchain.tools import tool

from .manager import UserEquipmentManager
from .recommender import UserBasedRecommender
from ..lure.database import LureDatabase, get_db

logger = logging.getLogger(__name__)


# ========== 服务实例（懒加载） ==========

_manager_instance: Optional[UserEquipmentManager] = None
_recommender_instance: Optional[UserBasedRecommender] = None


def _get_manager() -> UserEquipmentManager:
    """获取UserEquipmentManager实例（单例）"""
    global _manager_instance
    if _manager_instance is None:
        db = get_db()
        _manager_instance = UserEquipmentManager(db)
    return _manager_instance


def _get_recommender() -> UserBasedRecommender:
    """获取UserBasedRecommender实例（单例）"""
    global _recommender_instance
    if _recommender_instance is None:
        db = get_db()
        manager = _get_manager()
        _recommender_instance = UserBasedRecommender(db, manager)
    return _recommender_instance


# ========== LangChain 工具 ==========


@tool
def list_my_equipment(
    user_id: int,
    category: Optional[str] = None,
    only_favorites: bool = False,
) -> str:
    """
    查看我的装备库

    触发关键词：我的装备、我有哪些、查看装备库、装备清单、查看装备

    Args:
        user_id: 用户ID
        category: 装备类别过滤（鱼竿/渔轮/鱼线/拟饵），不提供则显示全部
        only_favorites: 是否只显示收藏装备，默认False

    Returns:
        Markdown格式的装备列表
    """
    try:
        manager = _get_manager()

        # 获取装备列表
        equipment_list = manager.list_user_equipment(user_id, category, only_favorites)

        if not equipment_list:
            if category:
                return f"# 我的装备库\n\n您的装备库中暂无{category}装备。"
            else:
                return "# 我的装备库\n\n您的装备库为空，快去添加您的第一件装备吧！"

        # 格式化输出Markdown
        output = "# 我的装备库\n\n"

        if only_favorites:
            output += "**（仅显示收藏装备）**\n\n"

        # 按类别分组
        from collections import defaultdict

        by_category = defaultdict(list)
        for eq in equipment_list:
            by_category[eq.category].append(eq)

        # 输出每个类别
        for cat, items in sorted(by_category.items()):
            output += f"## {cat} ({len(items)}件)\n\n"

            for eq in items:
                # 基本信息
                favorite_icon = "⭐" if eq.is_favorite else ""
                brand_model = f"{eq.brand_name} {eq.model}" if eq.model else eq.brand_name or "未知品牌"

                output += f"### {favorite_icon} {eq.equipment_name}\n\n"
                output += f"- **品牌型号**: {brand_model}\n"

                # 购买信息
                if eq.purchase_price:
                    output += f"- **购买价格**: ¥{eq.purchase_price:.2f}\n"
                if eq.purchase_date:
                    output += f"- **购买日期**: {eq.purchase_date}\n"
                if eq.purchase_source:
                    output += f"- **购买渠道**: {eq.purchase_source}\n"

                # 使用信息
                output += f"- **状态**: {eq.condition}\n"
                if eq.usage_frequency:
                    output += f"- **使用频率**: {eq.usage_frequency}\n"

                # 备注和标签
                if eq.notes:
                    output += f"- **备注**: {eq.notes}\n"
                if eq.tags:
                    output += f"- **标签**: {eq.tags}\n"

                output += "\n"

        # 统计信息
        stats = manager.get_equipment_statistics(user_id)
        output += "---\n\n"
        output += f"**装备总数**: {stats['total_count']}件  \n"
        output += f"**收藏数**: {stats['favorite_count']}件  \n"
        if stats['total_spent'] > 0:
            output += f"**总花费**: ¥{stats['total_spent']:.2f}  \n"

        return output

    except Exception as e:
        logger.error(f"查询装备库失败: {e}", exc_info=True)
        return f"❌ 查询装备库失败: {str(e)}"


@tool
def add_equipment_to_profile(
    user_id: int,
    equipment_id: int,
    purchase_price: Optional[float] = None,
    purchase_date: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    添加装备到我的装备库

    触发关键词：添加装备、我买了、记录一下、加入装备库

    Args:
        user_id: 用户ID
        equipment_id: 装备ID（从装备推荐结果中获取）
        purchase_price: 购买价格（可选）
        purchase_date: 购买日期（可选，格式：YYYY-MM-DD）
        notes: 备注（可选）

    Returns:
        操作结果消息
    """
    try:
        manager = _get_manager()

        # 添加装备
        record_id = manager.add_equipment(
            user_id=user_id,
            equipment_id=equipment_id,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            notes=notes,
        )

        # 获取装备名称
        db = get_db()
        equipment = db.execute(
            "SELECT name AS equipment_name FROM equipment WHERE equipment_id = ?",
            (equipment_id,),
        )
        equipment_name = equipment[0]["equipment_name"] if equipment else "未知装备"

        # 成功消息
        output = f"✅ 成功添加装备到装备库\n\n"
        output += f"**装备**: {equipment_name}\n"
        if purchase_price:
            output += f"**价格**: ¥{purchase_price:.2f}\n"
        if purchase_date:
            output += f"**购买日期**: {purchase_date}\n"
        if notes:
            output += f"**备注**: {notes}\n"

        output += "\n您可以使用 `list_my_equipment` 查看完整装备库。"

        return output

    except ValueError as e:
        logger.warning(f"添加装备失败: {e}")
        return f"❌ 添加失败: {str(e)}"
    except Exception as e:
        logger.error(f"添加装备失败: {e}", exc_info=True)
        return f"❌ 添加装备失败: {str(e)}"


@tool
def remove_equipment_from_profile(user_id: int, equipment_id: int) -> str:
    """
    从装备库删除装备

    触发关键词：删除装备、移除装备、卖了、不要了

    Args:
        user_id: 用户ID
        equipment_id: 装备ID

    Returns:
        操作结果消息
    """
    try:
        manager = _get_manager()

        # 获取装备名称（删除前）
        db = get_db()
        user_eq = db.execute(
            """
            SELECT e.name AS equipment_name
            FROM user_equipment ue
            JOIN equipment e ON ue.equipment_id = e.equipment_id
            WHERE ue.user_id = ? AND ue.equipment_id = ?
            """,
            (user_id, equipment_id),
        )
        equipment_name = user_eq[0]["equipment_name"] if user_eq else "未知装备"

        # 删除装备
        success = manager.remove_equipment(user_id, equipment_id)

        if success:
            return f"✅ 已从装备库移除: {equipment_name}"
        else:
            return f"❌ 该装备不在您的装备库中"

    except Exception as e:
        logger.error(f"删除装备失败: {e}", exc_info=True)
        return f"❌ 删除装备失败: {str(e)}"


@tool
def recommend_based_on_my_equipment(user_id: int, need_type: str) -> str:
    """
    基于我的装备推荐新装备

    触发关键词：升级、搭配、配什么、买什么好、装备推荐

    Args:
        user_id: 用户ID
        need_type: 需求类型，可选值：
            - "upgrade": 升级现有装备（推荐更高级的同类装备）
            - "complete": 完善装备配置（推荐缺失的装备）
            - "match": 装备搭配建议（检查装备是否匹配）

    Returns:
        Markdown格式的推荐报告
    """
    try:
        recommender = _get_recommender()

        if need_type == "upgrade":
            return recommender.recommend_upgrade(user_id)
        elif need_type == "complete":
            return recommender.recommend_complete_set(user_id)
        elif need_type == "match":
            return recommender.recommend_matching(user_id)
        else:
            return f"❌ 不支持的推荐类型: {need_type}\n\n支持的类型: upgrade（升级）、complete（完善）、match（搭配）"

    except Exception as e:
        logger.error(f"基于用户装备推荐失败: {e}", exc_info=True)
        return f"❌ 推荐失败: {str(e)}"


# ========== 导出工具列表 ==========

USER_EQUIPMENT_TOOLS = [
    list_my_equipment,
    add_equipment_to_profile,
    remove_equipment_from_profile,
    recommend_based_on_my_equipment,
]
