#!/usr/bin/env python3
"""
用户装备管理示例代码

演示如何使用用户装备管理功能：
1. 创建用户
2. 添加装备
3. 查询装备列表
4. 获取推荐
5. 统计分析
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.agent_fishing.tools.user_equipment import (
    UserEquipmentManager,
    UserBasedRecommender,
)
from packages.agent_fishing.tools.lure.database import get_db


def main():
    print("=" * 60)
    print("用户装备管理示例")
    print("=" * 60)

    # 初始化
    db = get_db()
    manager = UserEquipmentManager(db)
    recommender = UserBasedRecommender(db, manager)

    # ========== 1. 创建用户 ==========
    print("\n1. 创建用户...")
    try:
        user_id = manager.create_user(
            username="example_user",
            nickname="示例用户",
            user_level="进阶",
            fishing_experience_years=3,
            preferred_fish="鲈鱼,翘嘴",
        )
        print(f"✅ 创建用户成功: user_id={user_id}")
    except ValueError as e:
        print(f"⚠️ 用户已存在，使用现有用户")
        user = manager.get_user_by_username("example_user")
        user_id = user["user_id"]
        print(f"✅ 用户ID: {user_id}")

    # ========== 2. 添加装备 ==========
    print("\n2. 添加装备到装备库...")

    # 查询可用装备
    available_equipment = db.execute(
        "SELECT equipment_id, name, category, price_min FROM equipment LIMIT 5"
    )

    if not available_equipment:
        print("❌ 数据库中暂无装备数据，请先运行爬虫或手动添加")
        return

    # 添加前3件装备
    added_count = 0
    for eq in available_equipment[:3]:
        try:
            record_id = manager.add_equipment(
                user_id=user_id,
                equipment_id=eq["equipment_id"],
                purchase_price=eq["price_min"] if eq["price_min"] else 299.99,
                purchase_date="2024-01-15",
                notes="示例装备",
                tags=["测试", "示例"],
            )
            print(
                f"✅ 添加装备: {eq['name']} ({eq['category']}) - record_id={record_id}"
            )
            added_count += 1
        except ValueError as e:
            print(f"⚠️ 跳过已添加的装备: {eq['name']}")

    print(f"\n✅ 共添加 {added_count} 件装备")

    # ========== 3. 查询装备列表 ==========
    print("\n3. 查询装备列表...")

    equipment_list = manager.list_user_equipment(user_id)
    print(f"✅ 装备总数: {len(equipment_list)}")

    for i, eq in enumerate(equipment_list, 1):
        favorite_icon = "⭐" if eq.is_favorite else "  "
        print(
            f"{favorite_icon} {i}. {eq.equipment_name} ({eq.category}) - "
            f"品牌: {eq.brand_name or '未知'} - "
            f"价格: ¥{eq.purchase_price or 0:.2f}"
        )

    # 查询特定类别
    print("\n查询鱼竿类装备...")
    rod_list = manager.list_user_equipment(user_id, category="鱼竿")
    print(f"✅ 鱼竿数量: {len(rod_list)}")

    # ========== 4. 获取推荐 ==========
    print("\n4. 获取装备推荐...")

    # 完善推荐
    print("\n--- 完善推荐 (查看缺少哪些装备) ---")
    complete_rec = recommender.recommend_complete_set(user_id)
    print(complete_rec[:500] + "..." if len(complete_rec) > 500 else complete_rec)

    # 升级推荐
    print("\n--- 升级推荐 (推荐更高级装备) ---")
    upgrade_rec = recommender.recommend_upgrade(user_id)
    print(upgrade_rec[:500] + "..." if len(upgrade_rec) > 500 else upgrade_rec)

    # 搭配推荐
    print("\n--- 搭配推荐 (检查装备是否匹配) ---")
    match_rec = recommender.recommend_matching(user_id)
    print(match_rec[:500] + "..." if len(match_rec) > 500 else match_rec)

    # ========== 5. 统计分析 ==========
    print("\n5. 装备统计分析...")

    stats = manager.get_equipment_statistics(user_id)
    print(f"\n✅ 装备总数: {stats['total_count']}")
    print(f"✅ 总花费: ¥{stats['total_spent']:.2f}")
    print(f"✅ 收藏数: {stats['favorite_count']}")

    print("\n按类别统计:")
    for cat_stat in stats["by_category"]:
        avg_price = cat_stat["avg_price"] if cat_stat["avg_price"] else 0
        total_price = cat_stat["total_price"] if cat_stat["total_price"] else 0
        print(
            f"  - {cat_stat['category']}: {cat_stat['count']}件 "
            f"(平均: ¥{avg_price:.2f}, 总计: ¥{total_price:.2f})"
        )

    # 分析缺失装备
    missing = manager.get_missing_equipment_types(user_id)
    if missing:
        print(f"\n⚠️ 缺失的装备类型: {', '.join(missing)}")
    else:
        print("\n✅ 基础装备齐全（鱼竿、渔轮、鱼线）")

    # 品牌分布
    brands = manager.get_equipment_brands(user_id)
    if brands:
        print("\n品牌分布:")
        for brand in brands:
            print(f"  - {brand['brand_name']}: {brand['count']}件")

    # ========== 6. 装备操作示例 ==========
    print("\n6. 其他装备操作...")

    if equipment_list:
        # 切换收藏状态
        first_equipment = equipment_list[0]
        print(f"\n切换收藏状态: {first_equipment.equipment_name}")
        success = manager.toggle_favorite(user_id, first_equipment.equipment_id)
        if success:
            print("✅ 收藏状态已切换")

        # 更新备注
        print(f"\n更新装备备注: {first_equipment.equipment_name}")
        success = manager.update_equipment_notes(
            user_id, first_equipment.equipment_id, "更新后的备注信息"
        )
        if success:
            print("✅ 备注已更新")

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
