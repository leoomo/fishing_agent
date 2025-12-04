#!/usr/bin/env python3
"""
智能钓鱼助手 - 淘宝装备爬虫脚本（RPA模式）
使用方法:
  1. 安装依赖: uv sync --extra rpa && uv run playwright install chromium
  2. 配置环境: 编辑 .env 文件设置 PLAYWRIGHT_HEADLESS=false（首次扫码建议）
  3. 运行脚本: uv run python run_crawler.py
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from packages.agent_fishing.tools.crawler.rpa import TaobaoRPA
from packages.agent_fishing.tools.crawler import DataPersister
from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.lure.image_manager import ImageManager, LocalImageStorage


# ==================== 配置区域 ====================
# 在这里修改你要爬取的关键词和参数

KEYWORDS = [
    # 示例：{"keyword": "禧玛诺鱼竿", "category": "鱼竿", "max_results": 5},
    {"keyword": "禧玛诺鱼竿", "category": "鱼竿", "max_results": 5},
    {"keyword": "达亿瓦渔轮", "category": "渔轮", "max_results": 5},
]

# 是否保存到数据库（False则只显示结果不保存）
SAVE_TO_DB = True

# 是否更新已存在的装备
UPDATE_EXISTING = True

# ==================================================


def main():
    """主函数"""
    print("=" * 60)
    print("🎣 智能钓鱼助手 - 淘宝RPA爬虫 v3.2.1")
    print("=" * 60)
    print()

    # 初始化 RPA 爬虫
    print("📦 初始化淘宝RPA爬虫（Playwright浏览器自动化）...")
    try:
        spider = TaobaoRPA()
        print("✅ RPA爬虫初始化成功")
        print("ℹ️  首次运行需要扫码登录，Cookie会自动保存")
    except ImportError as e:
        print(f"❌ RPA模块未安装，请先运行:")
        print("   uv sync --extra rpa")
        print("   uv run playwright install chromium")
        sys.exit(1)
    except Exception as e:
        print(f"❌ RPA爬虫初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 初始化数据库和持久化器
    persister = None
    if SAVE_TO_DB:
        print("💾 初始化数据库...")
        try:
            db = get_db()
            temp_dir = tempfile.mkdtemp()
            storage = LocalImageStorage(base_path=temp_dir)
            image_manager = ImageManager(db, storage)
            persister = DataPersister(db, image_manager)
            print("✅ 数据库初始化成功")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            sys.exit(1)

    print()
    print("-" * 60)

    # 遍历关键词列表进行爬取
    total_success = 0
    total_fail = 0

    for idx, config in enumerate(KEYWORDS, 1):
        keyword = config["keyword"]
        category = config.get("category")
        max_results = config.get("max_results", 50)

        print()
        print(f"🕷️  [{idx}/{len(KEYWORDS)}] 开始爬取: {keyword}")
        print(f"   类别: {category or '全部'}")
        print(f"   数量: {max_results}")
        print()

        # 开始爬取
        try:
            equipment_list = spider.search_equipment(
                keyword=keyword,
                category=category,
                max_results=max_results
            )
            print(f"✅ 爬取完成，获取到 {len(equipment_list)} 件装备")
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            total_fail += 1
            continue

        if not equipment_list:
            print("⚠️  未找到任何装备数据")
            continue

        # 显示结果预览
        print(f"\n📦 装备预览（前5条）:")
        for i, eq in enumerate(equipment_list[:5], 1):
            # 兼容两种数据格式（RPA和传统爬虫）
            brand = getattr(eq, 'brand', None) or getattr(eq, 'brand_name', 'N/A')
            price = getattr(eq, 'price', None) or getattr(eq, 'price_min', None)
            price_str = f"¥{price}" if price else "N/A"
            print(f"  {i}. {eq.name} - {brand} - {price_str}")
        if len(equipment_list) > 5:
            print(f"  ... 还有 {len(equipment_list) - 5} 件装备")

        # 保存到数据库
        if SAVE_TO_DB and persister:
            print(f"\n💾 保存到数据库...")
            success_count = 0
            fail_count = 0
            skip_count = 0

            for eq in equipment_list:
                try:
                    equipment_id = persister.save_equipment(eq, update_if_exists=UPDATE_EXISTING)
                    if equipment_id:
                        success_count += 1
                    else:
                        skip_count += 1
                except Exception as e:
                    fail_count += 1
                    if fail_count <= 3:
                        print(f"  ⚠️  保存失败: {eq.name} - {e}")

            print(f"✅ 保存完成: 成功 {success_count} 件，跳过 {skip_count} 件，失败 {fail_count} 件")
            total_success += success_count
        else:
            print(f"\n⏭️  跳过数据库保存")

        print("-" * 60)

    # 显示总结
    print()
    print("=" * 60)
    print("📊 爬取任务完成！")
    print(f"   总关键词: {len(KEYWORDS)}")
    if SAVE_TO_DB:
        print(f"   成功保存: {total_success} 件装备")
        print(f"   失败任务: {total_fail} 个")
    print("=" * 60)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
