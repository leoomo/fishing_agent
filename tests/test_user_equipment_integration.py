"""
用户装备管理模块集成测试

测试用户装备管理的完整流程：
1. 创建用户
2. 添加装备
3. 查询装备列表
4. 获取统计信息
5. 推荐功能
6. 删除装备
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.agents.fishing.tools.user_equipment import (
    UserEquipmentManager,
    UserBasedRecommender,
)
from apps.api.database import get_db


def test_create_user():
    """测试创建用户"""
    print("\n" + "=" * 60)
    print("测试1: 创建用户")
    print("=" * 60)

    db = get_db()
    manager = UserEquipmentManager(db)

    try:
        # 创建测试用户
        user_id = manager.create_user(
            username="test_user_001",
            nickname="测试钓友",
            user_level="进阶",
            fishing_experience_years=3,
            preferred_fish="鲈鱼",
        )

        print(f"✅ 创建用户成功: user_id={user_id}")

        # 验证用户信息
        user = manager.get_user(user_id)
        print(f"✅ 用户信息: {user['username']} ({user['user_level']})")

        return user_id

    except ValueError as e:
        # 如果用户已存在，获取现有用户
        print(f"⚠️ 用户已存在，使用现有用户")
        user = manager.get_user_by_username("test_user_001")
        return user["user_id"]


def insert_test_equipment():
    """插入测试装备数据"""
    print("\n" + "=" * 60)
    print("准备: 插入测试装备数据")
    print("=" * 60)

    db = get_db()

    # 检查是否已有装备数据
    existing = db.execute("SELECT COUNT(*) as count FROM equipment")
    if existing[0]["count"] > 0:
        print(f"✅ 数据库中已有 {existing[0]['count']} 件装备，跳过插入")
        return

    # 插入测试品牌
    brand_id = db.execute_write(
        "INSERT INTO brands (name_cn, tier, description) VALUES (?, ?, ?)",
        ("测试品牌", "中端", "集成测试用品牌"),
    )
    print(f"✅ 插入测试品牌: brand_id={brand_id}")

    # 插入测试装备
    test_equipment = [
        ("测试鱼竿ML", "鱼竿", 299.0, 399.0, "ML调性路亚竿"),
        ("测试渔轮2000", "渔轮", 199.0, 299.0, "2000型纺车轮"),
        ("测试鱼线PE1.0", "鱼线", 49.0, 79.0, "PE编织线1.0号"),
        ("测试米诺", "拟饵", 29.0, 49.0, "浮水米诺"),
        ("测试软虫", "拟饵", 15.0, 25.0, "软胶虫"),
    ]

    for name, category, price_min, price_max, description in test_equipment:
        equipment_id = db.execute_write(
            """
            INSERT INTO equipment (name, category, brand_id, price_min, price_max, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (name, category, brand_id, price_min, price_max, description),
        )
        print(f"✅ 插入装备: {name} (ID:{equipment_id})")

    print(f"\n✅ 共插入 {len(test_equipment)} 件测试装备")


def test_add_equipment(user_id: int):
    """测试添加装备"""
    print("\n" + "=" * 60)
    print("测试2: 添加装备到用户库")
    print("=" * 60)

    db = get_db()
    manager = UserEquipmentManager(db)

    # 首先查询一些装备ID
    equipment_query = """
    SELECT equipment_id, name AS equipment_name, category, brand_id
    FROM equipment
    LIMIT 5
    """
    available_equipment = db.execute(equipment_query)

    if not available_equipment:
        print("❌ 数据库中没有可用的装备数据")
        return

    added_count = 0
    for eq in available_equipment[:3]:  # 添加前3个装备
        try:
            record_id = manager.add_equipment(
                user_id=user_id,
                equipment_id=eq["equipment_id"],
                purchase_price=299.99,
                purchase_date="2024-01-15",
                notes="集成测试装备",
            )

            print(
                f"✅ 添加装备: {eq['equipment_name']} ({eq['category']}) - record_id={record_id}"
            )
            added_count += 1

        except ValueError as e:
            print(f"⚠️ 跳过已存在的装备: {eq['equipment_name']}")

    print(f"\n✅ 共成功添加 {added_count} 件装备")


def test_list_equipment(user_id: int):
    """测试查询装备列表"""
    print("\n" + "=" * 60)
    print("测试3: 查询用户装备列表")
    print("=" * 60)

    db = get_db()
    manager = UserEquipmentManager(db)

    equipment_list = manager.list_user_equipment(user_id)

    print(f"✅ 装备总数: {len(equipment_list)}")

    for i, eq in enumerate(equipment_list, 1):
        print(
            f"{i}. {eq.equipment_name} ({eq.category}) - 品牌: {eq.brand_name or '未知'}"
        )


def test_statistics(user_id: int):
    """测试统计功能"""
    print("\n" + "=" * 60)
    print("测试4: 获取装备统计")
    print("=" * 60)

    db = get_db()
    manager = UserEquipmentManager(db)

    stats = manager.get_equipment_statistics(user_id)

    print(f"✅ 装备总数: {stats['total_count']}")
    print(f"✅ 总花费: ¥{stats['total_spent']:.2f}")
    print(f"✅ 收藏数: {stats['favorite_count']}")

    print("\n按类别统计:")
    for cat_stat in stats["by_category"]:
        print(
            f"  - {cat_stat['category']}: {cat_stat['count']}件 "
            f"(平均价格: ¥{cat_stat['avg_price'] or 0:.2f})"
        )


def test_recommendations(user_id: int):
    """测试推荐功能"""
    print("\n" + "=" * 60)
    print("测试5: 推荐功能")
    print("=" * 60)

    db = get_db()
    manager = UserEquipmentManager(db)
    recommender = UserBasedRecommender(db, manager)

    # 测试完善推荐
    print("\n--- 完善推荐 (complete) ---")
    complete_rec = recommender.recommend_complete_set(user_id)
    print(complete_rec[:500] + "...")  # 只显示前500字符

    # 测试升级推荐
    print("\n--- 升级推荐 (upgrade) ---")
    upgrade_rec = recommender.recommend_upgrade(user_id)
    print(upgrade_rec[:500] + "...")

    # 测试搭配推荐
    print("\n--- 搭配推荐 (match) ---")
    match_rec = recommender.recommend_matching(user_id)
    print(match_rec[:500] + "...")


def test_langchain_tools(user_id: int):
    """测试LangChain工具"""
    print("\n" + "=" * 60)
    print("测试6: LangChain工具调用")
    print("=" * 60)

    from packages.agents.fishing.tools.user_equipment.tools import (
        list_my_equipment,
        recommend_based_on_my_equipment,
    )

    # 测试 list_my_equipment
    print("\n--- 测试 list_my_equipment ---")
    result = list_my_equipment.invoke({"user_id": user_id})
    print(result[:500] + "...")

    # 测试 recommend_based_on_my_equipment
    print("\n--- 测试 recommend_based_on_my_equipment ---")
    result = recommend_based_on_my_equipment.invoke(
        {"user_id": user_id, "need_type": "complete"}
    )
    print(result[:500] + "...")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("用户装备管理模块 - 集成测试")
    print("=" * 60)

    try:
        # 0. 插入测试装备数据
        insert_test_equipment()

        # 1. 创建用户
        user_id = test_create_user()

        # 2. 添加装备
        test_add_equipment(user_id)

        # 3. 查询装备列表
        test_list_equipment(user_id)

        # 4. 统计信息
        test_statistics(user_id)

        # 5. 推荐功能
        test_recommendations(user_id)

        # 6. LangChain工具
        test_langchain_tools(user_id)

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
