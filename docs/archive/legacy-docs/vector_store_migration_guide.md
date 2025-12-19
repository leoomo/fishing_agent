# 向量存储迁移指南

**版本**: v3.1.1
**更新日期**: 2025-11-30
**适用架构**: packages/agent_fishing + DashScope Embedding + ChromaDB

本指南帮助您从旧版本（使用本地 BGE-M3 模型）迁移到新版本（使用 DashScope Embedding API）。

## 📋 版本对比

| 项目 | 旧版本 | 新版本 |
|------|--------|--------|
| **Embedding 方式** | 本地 BGE-M3 模型 | DashScope API |
| **文本向量维度** | 1024维 | 1024维（v3）或 1536维（v2） |
| **图片向量支持** | 支持（AltCLIP） | 暂时禁用 |
| **必需依赖** | sentence-transformers, transformers, torch | 仅 chromadb, dashscope |
| **安装大小** | ~4GB | ~100MB |
| **内存占用** | ~4GB | < 100MB |
| **首次启动** | 需加载模型（慢） | 即时启动 |
| **索引方式** | 手动触发 | 懒加载（自动） |

## 🚀 快速迁移步骤

### 步骤 1: 更新依赖

```bash
# 拉取最新代码
git pull

# 同步依赖（会自动安装 chromadb 和 click）
uv sync

# 验证安装
uv run python -c "import chromadb; print('✅ ChromaDB 已安装')"
```

### 步骤 2: 配置 API 密钥

在 `.env` 文件中添加或确认 `DASHSCOPE_API_KEY`：

```bash
# DashScope API 密钥（用于 LLM 和 Embedding）
DASHSCOPE_API_KEY=your-dashscope-api-key

# 可选：指定 Embedding 模型
VECTOR_EMBEDDING_MODEL=text-embedding-v3  # 1024维，推荐
# VECTOR_EMBEDDING_MODEL=text-embedding-v2  # 1536维

# 可选：控制懒加载索引
VECTOR_AUTO_INDEX=true  # 默认启用
```

**获取 API 密钥**: https://dashscope.console.aliyun.com/

### 步骤 3: 重建向量索引

⚠️ **重要**: 由于 Embedding 方式变更，需要重建所有向量索引。

**方式 A: 使用 CLI 工具（推荐）**

```bash
# 查看当前索引状态
uv run python -m packages.agent_fishing.tools.lure.cli status

# 重建所有索引
uv run python -m packages.agent_fishing.tools.lure.cli rebuild --force

# 验证重建结果
uv run python -m packages.agent_fishing.tools.lure.cli status
```

**方式 B: 删除旧索引目录**

```bash
# 删除旧的向量存储
rm -rf packages/agent_fishing/tools/lure/data/vector_store

# 下次搜索时会自动重建（懒加载）
```

**方式 C: 通过代码重建**

```python
from packages.agent_fishing.tools.lure.database import get_db
from packages.agent_fishing.tools.lure.vector_store import get_vector_store
from packages.agent_fishing.tools.lure.knowledge_indexer import KnowledgeIndexer

db = get_db()
vector_store = get_vector_store()
indexer = KnowledgeIndexer(db, vector_store)

# 重建所有索引
results = indexer.reindex_all()
print(f"索引完成: {results}")
```

### 步骤 4: 验证功能

```bash
# 测试搜索功能
uv run python -m packages.agent_fishing.tools.lure.cli search "鲈鱼习性" --type fish --top-k 3

# 运行示例脚本
uv run python examples/vector_store_example.py
```

## 🔧 常见问题

### Q1: 为什么需要重建索引？

**A**: 新版本使用 DashScope API 生成的向量与旧版本 BGE-M3 模型不兼容。虽然两者都是 1024维，但向量空间完全不同，必须重建。

### Q2: 重建索引需要多长时间？

**A**: 取决于数据量和网络速度：
- 100 条知识：约 10-30 秒
- 1000 条知识：约 1-3 分钟
- DashScope API 限制：25 条/批次

### Q3: 图片搜索功能怎么办？

**A**: 当前版本暂时禁用了图片 embedding 功能。如果调用相关方法会抛出 `NotImplementedError`。未来版本可能集成多模态 API（如 GLM-4V）。

### Q4: 如何切换到不同的 Embedding 模型？

**A**: 修改 `.env` 文件：

```bash
# 使用 v3（1024维，推荐）
VECTOR_EMBEDDING_MODEL=text-embedding-v3

# 或使用 v2（1536维）
VECTOR_EMBEDDING_MODEL=text-embedding-v2
```

然后重建索引：
```bash
uv run python -m packages.agent_fishing.tools.lure.cli rebuild --force
```

### Q5: 懒加载索引是如何工作的？

**A**:
1. 首次搜索时，系统检测到向量集合为空
2. 自动触发增量索引（只索引未向量化的数据）
3. 索引完成后执行搜索
4. 后续搜索直接使用已有索引

可以通过 `VECTOR_AUTO_INDEX=false` 禁用懒加载。

### Q6: API 调用会产生费用吗？

**A**: 是的，DashScope Embedding API 按调用次数计费。建议：
- 开发测试时使用少量数据
- 生产环境评估成本后使用
- 查看定价: https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-metering-and-billing

### Q7: 如何回退到旧版本？

**A**:
```bash
# 检出旧版本代码
git checkout <old-commit-hash>

# 重新安装旧依赖
uv sync --extra vector-local  # 安装本地模型依赖
```

注意：旧版本的向量索引与新版本不兼容。

## 📊 性能对比

### 索引性能

测试数据：100 条鱼类知识

| 指标 | 旧版本（BGE-M3） | 新版本（DashScope API） |
|------|-----------------|----------------------|
| 首次加载时间 | 10-20秒（加载模型） | 0秒（无需加载） |
| 索引时间 | 5-10秒 | 8-15秒（网络延迟） |
| 内存占用 | ~4GB | < 100MB |
| GPU 要求 | 推荐 | 不需要 |

### 搜索性能

| 指标 | 旧版本 | 新版本 |
|------|--------|--------|
| 查询向量化 | < 100ms（本地） | 100-300ms（API） |
| 向量搜索 | < 50ms | < 50ms |
| 总延迟 | ~150ms | ~200-350ms |

## 🎯 最佳实践

### 1. 开发环境

```bash
# 启用懒加载，减少启动时间
VECTOR_AUTO_INDEX=true

# 使用 v3 模型（1024维，速度快）
VECTOR_EMBEDDING_MODEL=text-embedding-v3
```

### 2. 生产环境

```bash
# 预先建立索引，避免首次搜索慢
uv run python -m packages.agent_fishing.tools.lure.cli rebuild --force

# 禁用自动索引，手动控制
VECTOR_AUTO_INDEX=false

# 根据质量需求选择模型
VECTOR_EMBEDDING_MODEL=text-embedding-v3  # 平衡
# VECTOR_EMBEDDING_MODEL=text-embedding-v2  # 高质量
```

### 3. 定期维护

```bash
# 每周检查索引状态
uv run python -m packages.agent_fishing.tools.lure.cli status

# 有新数据时增量索引（如果禁用了懒加载）
# 懒加载会自动处理，无需手动
```

## 🆘 故障排除

### 问题 1: ImportError: No module named 'chromadb'

**解决**:
```bash
uv sync
# 或
uv add chromadb
```

### 问题 2: DASHSCOPE_API_KEY not found

**解决**:
```bash
# 确保 .env 文件存在并包含 API 密钥
cp .env.example .env
# 编辑 .env 添加您的密钥
```

### 问题 3: DashScope API error: Unauthorized

**解决**:
- 检查 API 密钥是否正确
- 确认账户余额是否充足
- 查看 API 密钥是否有效

### 问题 4: 搜索结果为空

**可能原因**:
1. 数据库中没有数据
2. 索引未建立

**解决**:
```bash
# 检查数据库
uv run python -c "from packages.agent_fishing.tools.lure.database import get_db; db = get_db(); print(db.execute('SELECT COUNT(*) as c FROM fish_knowledge')[0])"

# 重建索引
uv run python -m packages.agent_fishing.tools.lure.cli rebuild --force
```

### 问题 5: 维度不匹配错误

**解决**:
```bash
# 清空旧索引
rm -rf packages/agent_fishing/tools/lure/data/vector_store

# 重建索引
uv run python -m packages.agent_fishing.tools.lure.cli rebuild --force
```

## 📞 获取帮助

- **文档**: 查看 `CLAUDE.md` 了解完整配置
- **示例**: 运行 `examples/vector_store_example.py`
- **CLI 帮助**: `uv run python -m packages.agent_fishing.tools.lure.cli --help`

## 📅 迁移检查清单

- [ ] 更新代码到最新版本
- [ ] 安装依赖（uv sync）
- [ ] 配置 DASHSCOPE_API_KEY
- [ ] 删除旧向量存储或运行 rebuild
- [ ] 测试搜索功能
- [ ] 更新生产环境配置
- [ ] 监控 API 调用费用

---

**迁移完成日期**: ___________
**迁移负责人**: ___________
**备注**: ___________
