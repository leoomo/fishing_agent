#!/usr/bin/env python3
"""
装备爬虫CLI工具

提供命令行接口用于爬取电商装备数据、增量同步和管理爬虫任务。

使用示例:
    # 爬取淘宝装备
    python -m packages.agent_fishing.tools.crawler.cli crawl --source taobao --keyword "禧玛诺鱼竿" --category 鱼竿 --max-results 50

    # 爬取京东装备
    python -m packages.agent_fishing.tools.crawler.cli crawl --source jd --keyword "达亿瓦渔轮" --category 渔轮

    # 增量同步（更新最近30天的装备）
    python -m packages.agent_fishing.tools.crawler.cli sync --days 30

    # 查看统计信息
    python -m packages.agent_fishing.tools.crawler.cli stats
"""

import click
import sys
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from packages.agent_fishing.tools.crawler import (
    JDSpider,
    TaobaoSpider,
    ForumSpider,
    DataPersister,
    EquipmentData,
)
from packages.agent_fishing.tools.lure.database import get_db


@click.group()
@click.version_option(version="3.2.0", prog_name="装备爬虫CLI")
def cli():
    """装备爬虫命令行工具

    支持从淘宝、京东、路亚论坛爬取装备数据并自动入库。
    """
    pass


@cli.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(["taobao", "jd", "forum"], case_sensitive=False),
    required=True,
    help="爬虫来源: taobao(淘宝), jd(京东), forum(论坛)",
)
@click.option(
    "--keyword",
    "-k",
    required=True,
    help="搜索关键词，例如: 禧玛诺鱼竿",
)
@click.option(
    "--category",
    "-c",
    type=click.Choice(["鱼竿", "渔轮", "鱼线", "拟饵", ""], case_sensitive=False),
    default="",
    help="装备类别（可选）",
)
@click.option(
    "--max-results",
    "-m",
    type=int,
    default=20,
    help="最大爬取数量，默认20",
)
@click.option(
    "--save/--no-save",
    default=True,
    help="是否保存到数据库，默认保存",
)
@click.option(
    "--update/--no-update",
    default=True,
    help="如果装备已存在是否更新，默认更新",
)
def crawl(
    source: str,
    keyword: str,
    category: str,
    max_results: int,
    save: bool,
    update: bool,
):
    """爬取装备数据

    从指定来源爬取装备信息并可选保存到数据库。

    示例:
        \b
        # 爬取淘宝数据
        python -m packages.agent_fishing.tools.crawler.cli crawl -s taobao -k "禧玛诺" -c 鱼竿 -m 50

        \b
        # 爬取京东数据（仅查看，不保存）
        python -m packages.agent_fishing.tools.crawler.cli crawl -s jd -k "达亿瓦" --no-save
    """
    click.echo("=" * 60)
    click.echo(f"装备爬虫 - {source.upper()}")
    click.echo("=" * 60)
    click.echo(f"关键词: {keyword}")
    click.echo(f"类别: {category or '全部'}")
    click.echo(f"最大数量: {max_results}")
    click.echo(f"保存到数据库: {'是' if save else '否'}")
    click.echo(f"更新已有装备: {'是' if update else '否'}")
    click.echo("")

    # 初始化爬虫
    spider_map = {"taobao": TaobaoSpider, "jd": JDSpider, "forum": ForumSpider}

    spider_class = spider_map.get(source.lower())
    if not spider_class:
        click.echo(f"❌ 不支持的爬虫来源: {source}", err=True)
        sys.exit(1)

    try:
        spider = spider_class()
        click.echo(f"✅ 初始化{source.upper()}爬虫成功")
    except Exception as e:
        click.echo(f"❌ 初始化爬虫失败: {e}", err=True)
        sys.exit(1)

    # 开始爬取
    click.echo(f"\n🕷️ 开始爬取装备数据...")
    try:
        equipment_list = spider.search_equipment(
            keyword=keyword, category=category if category else None, max_results=max_results
        )
        click.echo(f"✅ 爬取完成，获取到 {len(equipment_list)} 件装备")
    except Exception as e:
        click.echo(f"❌ 爬取失败: {e}", err=True)
        sys.exit(1)

    if not equipment_list:
        click.echo("⚠️  未找到任何装备数据")
        return

    # 显示爬取结果
    click.echo(f"\n📦 爬取结果预览（前5条）:")
    for i, eq in enumerate(equipment_list[:5], 1):
        click.echo(
            f"  {i}. {eq.name} - {eq.brand_name} - ¥{eq.price_min:.2f}"
        )
    if len(equipment_list) > 5:
        click.echo(f"  ... 还有 {len(equipment_list) - 5} 件装备")

    # 保存到数据库
    if save:
        click.echo(f"\n💾 保存到数据库...")
        db = get_db()

        # 初始化图片管理器
        from packages.agent_fishing.tools.lure.image_manager import ImageManager, LocalImageStorage
        import tempfile
        temp_dir = tempfile.mkdtemp()
        storage = LocalImageStorage(base_path=temp_dir)
        image_manager = ImageManager(db, storage)

        persister = DataPersister(db, image_manager)

        success_count = 0
        fail_count = 0
        skip_count = 0

        with click.progressbar(
            equipment_list, label="保存进度", show_pos=True
        ) as bar:
            for eq in bar:
                try:
                    equipment_id = persister.save_equipment(eq, update_if_exists=update)
                    if equipment_id:
                        success_count += 1
                    else:
                        skip_count += 1
                except Exception as e:
                    fail_count += 1
                    if fail_count <= 3:  # 只显示前3个错误
                        click.echo(f"\n⚠️  保存失败: {eq.name} - {e}", err=True)

        click.echo(f"\n✅ 保存完成:")
        click.echo(f"  - 成功: {success_count} 件")
        click.echo(f"  - 跳过: {skip_count} 件（已存在且未更新）")
        if fail_count > 0:
            click.echo(f"  - 失败: {fail_count} 件")
    else:
        click.echo(f"\n⏭️  跳过数据库保存")

    click.echo(f"\n" + "=" * 60)
    click.echo("✅ 任务完成！")
    click.echo("=" * 60)


@cli.command()
@click.option(
    "--days",
    "-d",
    type=int,
    default=30,
    help="同步最近N天的装备数据，默认30天",
)
@click.option(
    "--source",
    "-s",
    type=click.Choice(["all", "taobao", "jd", "forum"], case_sensitive=False),
    default="all",
    help="同步来源，默认all（全部）",
)
def sync(days: int, source: str):
    """增量同步装备数据

    更新数据库中爬虫来源的装备数据（价格、图片等），基于最后同步时间。

    示例:
        \b
        # 同步所有来源最近30天的装备
        python -m packages.agent_fishing.tools.crawler.cli sync --days 30

        \b
        # 仅同步淘宝来源最近7天的装备
        python -m packages.agent_fishing.tools.crawler.cli sync --days 7 --source taobao
    """
    click.echo("=" * 60)
    click.echo("装备数据增量同步")
    click.echo("=" * 60)
    click.echo(f"同步范围: 最近 {days} 天")
    click.echo(f"数据来源: {source.upper()}")
    click.echo("")

    # 获取数据库中需要同步的装备
    db = get_db()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    # 构建查询条件
    source_filter = "" if source == "all" else f"AND source = '{source}'"
    query = f"""
        SELECT equipment_id, name, category, brand_id, source, source_url, crawled_at
        FROM equipment
        WHERE source IN ('taobao', 'jd', 'forum')
        {source_filter}
        AND (last_synced_at IS NULL OR last_synced_at < ?)
        ORDER BY crawled_at DESC
    """

    equipment_to_sync = db.execute(query, (cutoff_date,))

    if not equipment_to_sync:
        click.echo("✅ 没有需要同步的装备数据")
        return

    click.echo(f"📦 找到 {len(equipment_to_sync)} 件装备需要同步")

    # TODO: 实现同步逻辑
    # 这里需要根据source_url重新爬取装备详情，更新价格和图片
    click.echo(
        "\n⚠️  增量同步功能正在开发中，当前版本暂不支持自动同步"
    )
    click.echo("建议使用 crawl 命令重新爬取装备数据并启用 --update 选项")


@cli.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(["all", "taobao", "jd", "forum", "manual"], case_sensitive=False),
    default="all",
    help="统计来源，默认all（全部）",
)
def stats(source: str):
    """显示装备数据库统计信息

    查看数据库中装备数据的统计概况。

    示例:
        \b
        # 查看所有装备统计
        python -m packages.agent_fishing.tools.crawler.cli stats

        \b
        # 仅查看爬虫来源的装备统计
        python -m packages.agent_fishing.tools.crawler.cli stats --source taobao
    """
    click.echo("=" * 60)
    click.echo("装备数据库统计信息")
    click.echo("=" * 60)

    db = get_db()

    # 总装备数量
    source_filter = "" if source == "all" else f"WHERE source = '{source}'"
    total_query = f"SELECT COUNT(*) as count FROM equipment {source_filter}"
    total_result = db.execute(total_query)
    total_count = total_result[0]["count"] if total_result else 0

    click.echo(f"\n📦 装备总数: {total_count} 件")

    # 按来源统计
    click.echo(f"\n📊 按来源统计:")
    source_query = """
        SELECT source, COUNT(*) as count
        FROM equipment
        GROUP BY source
        ORDER BY count DESC
    """
    source_stats = db.execute(source_query)
    for stat in source_stats:
        src = stat["source"] or "未知"
        count = stat["count"]
        percentage = (count / total_count * 100) if total_count > 0 else 0
        click.echo(f"  - {src.ljust(10)}: {count:>6} 件 ({percentage:>5.1f}%)")

    # 按类别统计
    category_filter = "" if source == "all" else f"WHERE source = '{source}'"
    click.echo(f"\n🎣 按类别统计:")
    category_query = f"""
        SELECT category, COUNT(*) as count
        FROM equipment
        {category_filter}
        GROUP BY category
        ORDER BY count DESC
    """
    category_stats = db.execute(category_query)
    for stat in category_stats:
        cat = stat["category"] or "未分类"
        count = stat["count"]
        click.echo(f"  - {cat.ljust(10)}: {count:>6} 件")

    # 最近爬取时间
    if source in ["all", "taobao", "jd", "forum"]:
        click.echo(f"\n⏰ 爬虫数据时间:")
        recent_query = """
            SELECT source, MAX(crawled_at) as last_crawled
            FROM equipment
            WHERE source IN ('taobao', 'jd', 'forum')
            GROUP BY source
            ORDER BY last_crawled DESC
        """
        recent_stats = db.execute(recent_query)
        for stat in recent_stats:
            src = stat["source"]
            last = stat["last_crawled"] or "从未爬取"
            click.echo(f"  - {src.ljust(10)}: {last}")

    click.echo("\n" + "=" * 60)


@cli.command()
def test():
    """测试爬虫连接

    测试爬虫模块和数据库连接是否正常。
    """
    click.echo("=" * 60)
    click.echo("爬虫连接测试")
    click.echo("=" * 60)

    # 测试数据库连接
    click.echo("\n1. 测试数据库连接...")
    try:
        db = get_db()
        result = db.execute("SELECT COUNT(*) as count FROM equipment")
        count = result[0]["count"] if result else 0
        click.echo(f"   ✅ 数据库连接正常，当前有 {count} 件装备")
    except Exception as e:
        click.echo(f"   ❌ 数据库连接失败: {e}")
        return

    # 测试各个爬虫初始化
    spiders = [
        ("淘宝爬虫", TaobaoSpider),
        ("京东爬虫", JDSpider),
        ("论坛爬虫", ForumSpider),
    ]

    for name, spider_class in spiders:
        click.echo(f"\n2. 测试{name}...")
        try:
            spider = spider_class()
            click.echo(f"   ✅ {name}初始化成功")
        except Exception as e:
            click.echo(f"   ❌ {name}初始化失败: {e}")

    # 测试DataPersister
    click.echo(f"\n3. 测试数据持久化器...")
    try:
        from packages.agent_fishing.tools.lure.image_manager import ImageManager, LocalImageStorage
        import tempfile
        temp_dir = tempfile.mkdtemp()
        storage = LocalImageStorage(base_path=temp_dir)
        image_manager = ImageManager(db, storage)
        persister = DataPersister(db, image_manager)
        click.echo(f"   ✅ 数据持久化器初始化成功")
    except Exception as e:
        click.echo(f"   ❌ 数据持久化器初始化失败: {e}")

    click.echo("\n" + "=" * 60)
    click.echo("✅ 测试完成！")
    click.echo("=" * 60)


if __name__ == "__main__":
    cli()
