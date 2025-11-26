"""
向量存储管理CLI工具

提供命令行接口管理向量索引：
- status: 查看索引状态
- rebuild: 重建向量索引
- search: 测试搜索功能
"""

import click
import sys


@click.group()
def cli():
    """路亚装备向量存储管理工具"""
    pass


@cli.command()
def status():
    """查看索引状态"""
    try:
        from .database import get_db
        from .vector_store import get_vector_store
        from .knowledge_indexer import KnowledgeIndexer

        db = get_db()
        vector_store = get_vector_store()
        indexer = KnowledgeIndexer(db, vector_store)

        stats = indexer.get_index_stats()

        click.echo("📊 向量存储状态\n")

        # Embedding信息
        try:
            click.echo(f"Embedding提供商: DashScope")
            click.echo(f"向量维度: {vector_store.embedding_provider.dimension}维\n")
        except Exception as e:
            click.echo(f"⚠️  Embedding提供商未初始化: {e}\n")

        # 向量集合统计
        click.echo("向量集合:")
        for coll, count in stats['collections'].items():
            click.echo(f"  • {coll}: {count} 条")

        # 数据库统计
        click.echo("\n数据库统计:")
        for table, info in stats['database'].items():
            if isinstance(info, dict):
                total = info.get('total', 0)
                indexed = info.get('indexed', 0)
                pending = info.get('pending', 0)

                status_icon = "✅" if pending == 0 else "⚠️ "
                click.echo(f"  {status_icon} {table}:")
                click.echo(f"      总计: {total} | 已索引: {indexed} | 待索引: {pending}")

    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--force', is_flag=True, help='强制重建所有索引')
def rebuild(force):
    """重建向量索引"""
    try:
        from .database import get_db
        from .vector_store import get_vector_store
        from .knowledge_indexer import KnowledgeIndexer

        db = get_db()
        vector_store = get_vector_store()
        indexer = KnowledgeIndexer(db, vector_store)

        if not force:
            if not click.confirm('⚠️  此操作将清空并重建所有向量索引，是否继续？'):
                click.echo("已取消")
                return

        click.echo("🔄 开始重建索引...\n")

        # 重建所有索引
        results = indexer.reindex_all()

        click.echo("\n✅ 重建完成:")
        for key, value in results.items():
            click.echo(f"  • {key}: {value}")

    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--type', 'search_type', type=click.Choice(['fish', 'rig', 'equipment']), default='fish', help='搜索类型')
@click.option('--top-k', default=3, help='返回结果数量')
def search(query, search_type, top_k):
    """测试搜索功能"""
    try:
        from .database import get_db
        from .vector_store import get_vector_store
        from .knowledge_search import KnowledgeSearchService

        db = get_db()
        vector_store = get_vector_store()
        service = KnowledgeSearchService(db, vector_store)

        click.echo(f"🔍 搜索: {query} (类型: {search_type}, Top-{top_k})\n")

        if search_type == 'fish':
            results = service.search_fish_knowledge(query, top_k=top_k)
            for i, r in enumerate(results, 1):
                click.echo(f"{i}. [{r.score:.3f}] {r.title}")
                content_preview = r.content[:80] + "..." if len(r.content) > 80 else r.content
                click.echo(f"   {content_preview}\n")

        elif search_type == 'rig':
            results = service.search_rig_knowledge(query, top_k=top_k)
            for i, r in enumerate(results, 1):
                click.echo(f"{i}. [{r.score:.3f}] {r.name}")
                desc_preview = r.description[:80] + "..." if len(r.description) > 80 else r.description
                click.echo(f"   {desc_preview}\n")

        elif search_type == 'equipment':
            results = service.search_equipment_by_description(query, top_k=top_k)
            for i, r in enumerate(results, 1):
                click.echo(f"{i}. [{r.get('score', 0):.3f}] {r.get('name', 'N/A')}")
                click.echo(f"   类别: {r.get('category', 'N/A')} | 品牌: {r.get('brand', 'N/A')}\n")

        if not results:
            click.echo("未找到相关结果")

    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def config():
    """查看当前配置"""
    import os

    click.echo("⚙️  当前配置\n")

    # API密钥
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    click.echo(f"DASHSCOPE_API_KEY: {'✅ 已配置' if dashscope_key else '❌ 未配置'}")

    # 向量配置
    embedding_model = os.getenv("VECTOR_EMBEDDING_MODEL", "text-embedding-v3")
    click.echo(f"VECTOR_EMBEDDING_MODEL: {embedding_model}")

    auto_index = os.getenv("VECTOR_AUTO_INDEX", "true")
    click.echo(f"VECTOR_AUTO_INDEX: {auto_index}")

    # 验证配置
    if not dashscope_key:
        click.echo("\n⚠️  警告: DASHSCOPE_API_KEY 未配置")
        click.echo("请在 .env 文件中配置您的 DashScope API 密钥")


if __name__ == '__main__':
    cli()
