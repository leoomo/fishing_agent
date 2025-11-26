"""
向量存储使用示例

演示如何使用 DashScope Embedding API 和 ChromaDB 进行语义搜索。
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def example_1_basic_embedding():
    """示例1: 基础 Embedding 使用"""
    print("=" * 60)
    print("示例1: 基础 Embedding 使用")
    print("=" * 60)

    from src.tools.lure.embeddings import DashScopeEmbedding

    # 初始化 Embedding 提供商
    embedding = DashScopeEmbedding(model="text-embedding-v3")
    print(f"✅ Embedding 提供商: DashScope")
    print(f"📏 向量维度: {embedding.dimension}")

    # 单个文本向量化
    text = "鲈鱼是一种常见的淡水鱼"
    vector = embedding.embed_query(text)
    print(f"\n🔤 文本: {text}")
    print(f"📊 向量维度: {len(vector)}")
    print(f"📈 向量前5个值: {vector[:5]}")

    # 批量文本向量化
    texts = ["鲈鱼习性", "翘嘴钓法", "鳜鱼分布"]
    vectors = embedding.embed_texts(texts)
    print(f"\n📚 批量向量化: {len(texts)} 条文本")
    print(f"✅ 生成向量: {len(vectors)} 个")


def example_2_vector_store():
    """示例2: 向量存储基础操作"""
    print("\n" + "=" * 60)
    print("示例2: 向量存储基础操作")
    print("=" * 60)

    from src.tools.lure.vector_store import ChromaVectorStore

    # 初始化向量存储
    store = ChromaVectorStore()
    print(f"✅ 向量存储初始化成功")
    print(f"📁 持久化目录: {store.persist_directory}")

    # 添加文本到集合
    collection = "example_knowledge"
    texts = [
        "鲈鱼喜欢在清晨和傍晚活动",
        "翘嘴通常栖息在水域的中上层",
        "鳜鱼偏好隐蔽的水草区域"
    ]
    ids = ["fish_1", "fish_2", "fish_3"]
    metadatas = [
        {"fish": "鲈鱼", "type": "behavior"},
        {"fish": "翘嘴", "type": "habitat"},
        {"fish": "鳜鱼", "type": "habitat"}
    ]

    print(f"\n📝 添加 {len(texts)} 条知识到集合...")
    store.add_texts(collection, texts, ids, metadatas)
    print(f"✅ 添加成功")

    # 语义搜索
    query = "哪些鱼喜欢在水草附近"
    print(f"\n🔍 搜索查询: {query}")
    results = store.search_by_text(collection, query, top_k=2)

    print(f"📊 搜索结果 ({len(results)} 条):")
    for i, result in enumerate(results, 1):
        print(f"\n  {i}. [相似度: {result.score:.3f}]")
        print(f"     文档: {result.document}")
        print(f"     元数据: {result.metadata}")

    # 清理
    store.clear_collection(collection)
    print(f"\n🗑️  清理测试集合")


def example_3_knowledge_search():
    """示例3: 知识搜索服务（懒加载）"""
    print("\n" + "=" * 60)
    print("示例3: 知识搜索服务（懒加载索引）")
    print("=" * 60)

    from src.tools.lure.database import get_db
    from src.tools.lure.vector_store import get_vector_store
    from src.tools.lure.knowledge_search import KnowledgeSearchService

    # 初始化服务
    db = get_db()
    vector_store = get_vector_store()
    service = KnowledgeSearchService(db, vector_store, auto_index=True)

    print(f"✅ 知识搜索服务初始化成功")
    print(f"🔄 懒加载索引: 启用")

    # 搜索鱼类知识
    query = "鲈鱼的生活习性"
    print(f"\n🔍 搜索查询: {query}")
    print(f"💡 提示: 如果是首次搜索，会自动触发索引...")

    try:
        results = service.search_fish_knowledge(query, top_k=3)

        if results:
            print(f"\n📊 搜索结果 ({len(results)} 条):")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. [相似度: {result.score:.3f}] {result.title}")
                print(f"     内容: {result.content[:100]}...")
                if result.fish_name:
                    print(f"     鱼种: {result.fish_name}")
        else:
            print(f"\n⚠️  未找到相关结果（可能数据库中还没有鱼类知识）")
            print(f"💡 提示: 运行 src/tools/lure/init_data.py 初始化示例数据")

    except Exception as e:
        print(f"\n⚠️  搜索失败: {e}")
        print(f"💡 这可能是因为数据库中没有数据，属于正常情况")


def example_4_cli_usage():
    """示例4: CLI 工具使用"""
    print("\n" + "=" * 60)
    print("示例4: CLI 工具使用示例")
    print("=" * 60)

    print("""
CLI 工具提供了便捷的向量存储管理功能：

1. 查看索引状态:
   uv run python -m src.tools.lure.cli status

2. 重建向量索引:
   uv run python -m src.tools.lure.cli rebuild --force

3. 测试搜索功能:
   uv run python -m src.tools.lure.cli search "鲈鱼习性" --type fish --top-k 3

4. 查看配置:
   uv run python -m src.tools.lure.cli config

💡 提示: 首次使用前，确保已配置 DASHSCOPE_API_KEY
    """)


def main():
    """运行所有示例"""
    print("\n" + "🎯" * 30)
    print("向量存储使用示例")
    print("🎯" * 30)

    # 检查 API 密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("\n❌ 错误: DASHSCOPE_API_KEY 未配置")
        print("请在 .env 文件中配置您的 DashScope API 密钥")
        return

    print(f"\n✅ API 密钥已配置")

    try:
        # 运行示例
        example_1_basic_embedding()
        example_2_vector_store()
        example_3_knowledge_search()
        example_4_cli_usage()

        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
