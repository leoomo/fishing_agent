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

from packages.agent_fishing.tools.crawler.rpa import TaobaoRPA, TaobaoShopCategoryRPA, TaobaoShopRPA
from packages.agent_fishing.tools.crawler import DataPersister
from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.lure.image_manager import ImageManager, LocalImageStorage


# ==================== 配置区域 ====================
# 在这里修改你要爬取的模式和参数

# 爬虫模式选择：
# "keyword_search" - 关键词搜索模式（传统搜索）
# "shop_category" - 店铺分类模式（访问指定店铺，点击特定分类）
# "shop_crawl" - 店铺爬取模式（爬取整个店铺或多个店铺）
CRAWLER_MODE = "shop_category"  # 修改这里来切换模式

# ==================== 关键词搜索模式配置 ====================
KEYWORDS = [
    # 示例：{"keyword": "禧玛诺鱼竿", "category": "鱼竿", "max_results": 5},
    {"keyword": "禧玛诺鱼竿", "category": "鱼竿", "max_results": 5},
    {"keyword": "达亿瓦渔轮", "category": "渔轮", "max_results": 5},
]

# ==================== 店铺分类模式配置 ====================
# 当 CRAWLER_MODE = "shop_category" 时使用
SHOP_CATEGORY_CONFIG = {
    "shop_url": "https://shop437350870.taobao.com",  # 店铺地址
    "category_name": "路亚竿",                       # 目标分类
    "max_results": 5,                              # 最大结果数（只处理前几个商品）
    "download_images": True,                       # 是否下载图片
}

# ==================== 店铺爬取模式配置 ====================
# 当 CRAWLER_MODE = "shop_crawl" 时使用
SHOP_CRAWL_CONFIG = {
    "shop_urls": [
        # 可以指定多个店铺URL
        "https://shop437350870.taobao.com",
        # "https://shop123456789.taobao.com",
    ],
    "categories": ["路亚竿"],  # 指定分类，None表示爬取所有分类
    "max_items_per_category": 10,  # 每个分类最大商品数
    "crawl_default_shops": True,   # 是否也爬取默认配置的店铺
}

# ==================== 通用配置 ====================
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

    # 显示当前模式
    mode_descriptions = {
        "keyword_search": "关键词搜索模式",
        "shop_category": "店铺分类模式",
        "shop_crawl": "店铺爬取模式",
    }
    print(f"🔧 当前模式: {mode_descriptions.get(CRAWLER_MODE, CRAWLER_MODE)}")
    print()

    # 初始化爬虫
    spider = None
    try:
        if CRAWLER_MODE == "keyword_search":
            print("📦 初始化关键词搜索RPA爬虫...")
            spider = TaobaoRPA()
        elif CRAWLER_MODE == "shop_category":
            print("📦 初始化店铺分类RPA爬虫...")
            spider = TaobaoShopCategoryRPA()
        elif CRAWLER_MODE == "shop_crawl":
            print("📦 初始化店铺爬取RPA爬虫...")
            spider = TaobaoShopRPA()
        else:
            print(f"❌ 不支持的爬虫模式: {CRAWLER_MODE}")
            sys.exit(1)

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

    total_success = 0
    total_fail = 0
    all_equipment_list = []
 
    # 根据模式执行不同的爬取逻辑
    if CRAWLER_MODE == "keyword_search":
        # 关键词搜索模式
        all_equipment_list, total_success, total_fail = _run_keyword_search_mode(spider, persister)

    elif CRAWLER_MODE == "shop_category":
        # 店铺分类模式
        all_equipment_list, total_success, total_fail = _run_shop_category_mode(spider, persister)

    elif CRAWLER_MODE == "shop_crawl":
        # 店铺爬取模式
        all_equipment_list, total_success, total_fail = _run_shop_crawl_mode(spider, persister)

    # 显示总结
    print()
    print("=" * 60)
    print("📊 爬取任务完成！")
    print(f"   爬取模式: {mode_descriptions.get(CRAWLER_MODE, CRAWLER_MODE)}")
    if SAVE_TO_DB:
        print(f"   成功保存: {total_success} 件装备")
        print(f"   失败任务: {total_fail} 个")
    print(f"   总获取: {len(all_equipment_list)} 件装备")
    print("=" * 60)
    print()


def _run_keyword_search_mode(spider, persister):
    """运行关键词搜索模式"""
    total_success = 0
    total_fail = 0
    all_equipment_list = []

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
            all_equipment_list.extend(equipment_list)
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            total_fail += 1
            continue

        # 保存到数据库
        if SAVE_TO_DB and persister and equipment_list:
            success_count = _save_to_database(equipment_list, persister)
            total_success += success_count

        print("-" * 60)

    return all_equipment_list, total_success, total_fail


def _run_shop_category_mode(spider, persister):
    """运行店铺分类模式"""
    total_success = 0
    total_fail = 0

    shop_url = SHOP_CATEGORY_CONFIG["shop_url"]
    category_name = SHOP_CATEGORY_CONFIG["category_name"]
    max_results = SHOP_CATEGORY_CONFIG["max_results"]
    download_images = SHOP_CATEGORY_CONFIG["download_images"]

    print()
    print(f"🏪 店铺分类爬取:")
    print(f"   店铺地址: {shop_url}")
    print(f"   目标分类: {category_name}")
    print(f"   最大结果: {max_results}")
    print(f"   下载图片: {'是' if download_images else '否'}")
    print()

    # 开始爬取
    try:
        equipment_list = spider.crawl_shop_category()
        print(f"✅ 店铺分类爬取完成，获取到 {len(equipment_list)} 件装备")

        # 限制结果数量
        if equipment_list and len(equipment_list) > max_results:
            equipment_list = equipment_list[:max_results]
            print(f"📊 限制结果为前 {max_results} 件装备")

        # 显示结果预览
        if equipment_list:
            _display_equipment_preview(equipment_list)

        # 保存到数据库
        if SAVE_TO_DB and persister and equipment_list:
            success_count = _save_to_database(equipment_list, persister)
            total_success = success_count

    except Exception as e:
        print(f"❌ 店铺分类爬取失败: {e}")
        total_fail += 1
        import traceback
        traceback.print_exc()

    print("-" * 60)
    return equipment_list or [], total_success, total_fail


def _run_shop_crawl_mode(spider, persister):
    """运行店铺爬取模式"""
    total_success = 0
    total_fail = 0
    all_equipment_list = []

    shop_urls = SHOP_CRAWL_CONFIG["shop_urls"]
    categories = SHOP_CRAWL_CONFIG["categories"]
    max_items_per_category = SHOP_CRAWL_CONFIG["max_items_per_category"]
    crawl_default_shops = SHOP_CRAWL_CONFIG["crawl_default_shops"]

    print()
    print(f"🏪 店铺爬取:")
    print(f"   指定店铺: {len(shop_urls)} 个")
    print(f"   目标分类: {categories or '全部'}")
    print(f"   每类最大: {max_items_per_category} 件")
    print(f"   包含默认店: {'是' if crawl_default_shops else '否'}")
    print()

    # 爬取指定店铺
    for idx, shop_url in enumerate(shop_urls, 1):
        print()
        print(f"🏪 [{idx}/{len(shop_urls)}] 爬取店铺: {shop_url}")

        try:
            equipment_list = spider.crawl_shop(
                shop_url=shop_url,
                categories=categories,
                max_items_per_category=max_items_per_category
            )
            print(f"✅ 店铺爬取完成，获取到 {len(equipment_list)} 件装备")
            all_equipment_list.extend(equipment_list)

            # 保存到数据库
            if SAVE_TO_DB and persister and equipment_list:
                success_count = _save_to_database(equipment_list, persister)
                total_success += success_count

        except Exception as e:
            print(f"❌ 店铺爬取失败: {e}")
            total_fail += 1

        print("-" * 40)

    # 爬取默认店铺
    if crawl_default_shops:
        print()
        print(f"🏪 爬取默认店铺...")

        try:
            default_equipment_list = spider.crawl_default_shops()
            print(f"✅ 默认店铺爬取完成，获取到 {len(default_equipment_list)} 件装备")
            all_equipment_list.extend(default_equipment_list)

            # 保存到数据库
            if SAVE_TO_DB and persister and default_equipment_list:
                success_count = _save_to_database(default_equipment_list, persister)
                total_success += success_count

        except Exception as e:
            print(f"❌ 默认店铺爬取失败: {e}")
            total_fail += 1

    return all_equipment_list, total_success, total_fail


def _display_equipment_preview(equipment_list):
    """显示装备预览"""
    print(f"\n📦 装备预览（前5条）:")
    for i, eq in enumerate(equipment_list[:5], 1):
        # 兼容两种数据格式（RPA和传统爬虫）
        brand = getattr(eq, 'brand', None) or getattr(eq, 'brand_name', 'N/A')
        price = getattr(eq, 'price', None) or getattr(eq, 'price_min', None)
        price_str = f"¥{price}" if price else "N/A"

        # 显示商品ID（如果有）
        product_id = getattr(eq, 'id', None)
        id_str = f" (ID: {product_id})" if product_id else ""

        print(f"  {i}. {eq.name}{id_str} - {brand} - {price_str}")

    if len(equipment_list) > 5:
        print(f"  ... 还有 {len(equipment_list) - 5} 件装备")


def _save_to_database(equipment_list, persister):
    """保存装备到数据库"""
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
    return success_count


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
