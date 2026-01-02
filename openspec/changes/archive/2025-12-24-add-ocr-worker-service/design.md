# OCR Worker 系统技术设计

## Context

本项目已有成熟的爬虫 Worker 架构（`packages/scraper/worker/`），采用轮询拉取任务模式，支持分布式部署。同时已有完善的 OCR 服务层（`apps/api/services/ocr/`），支持 Ollama 本地和 SiliconFlow 云端两种提供商。

本设计复用这两套成熟架构，创建专门的 OCR Worker 服务。

## Goals / Non-Goals

**Goals:**
- 自动处理 PendingEquipment 中的图片进行 OCR 文本提取
- 支持多 Worker 节点分布式部署
- 提供简单的前端管理界面
- 复用现有 OCR 提供商（Ollama/SiliconFlow）

**Non-Goals:**
- 不实现复杂的任务调度策略（使用简单的 FIFO）
- 不实现 OCR 结果的智能解析（只提取原始文本）
- 不实现 Worker 负载均衡（由 Worker 自主领取）

## Decisions

### 1. 任务来源：复用 PendingEquipment 表

**决策**：在 `PendingEquipment` 模型中添加 OCR 状态字段，而非创建独立的 OCR 任务表。

**原因**：
- 避免数据冗余和同步问题
- OCR 任务与待审装备一一对应
- 简化实现，减少代码量

**字段设计**：
```python
ocr_status = Column(String(20), default="pending", index=True)
ocr_started_at = Column(DateTime, nullable=True)
ocr_completed_at = Column(DateTime, nullable=True)
ocr_worker_id = Column(String(100), nullable=True, index=True)
ocr_error_message = Column(Text, nullable=True)
ocr_retry_count = Column(Integer, default=0)
ocr_provider = Column(String(50), nullable=True)
ocr_processing_time_ms = Column(Integer, nullable=True)
```

### 2. Worker 架构：复用 ApiWorker 模式

**决策**：创建 `OCRWorker` 类，复用现有的轮询拉取模式。

**原因**：
- 现有架构经过验证，稳定可靠
- 减少重复开发
- 保持系统一致性

**关键流程**：
```
Worker 启动 → 注册 → 心跳线程 + 轮询线程
              ↓
领取任务 → 下载图片 → OCR 识别 → 汇报结果
```

### 3. OCR 执行：在 Worker 端调用提供商

**决策**：Worker 在本地调用 OCR 提供商，而非通过 API 转发。

**原因**：
- 减少网络延迟
- Worker 可选择就近的 OCR 服务
- 支持 Worker 使用本地 Ollama

**替代方案（未采用）**：
- Worker 上传图片到 API，由 API 统一调用 OCR
- 缺点：增加网络传输，不够灵活

### 4. 图片传输：按需下载

**决策**：Worker 从 API 下载图片到本地缓存，处理后清理。

**接口**：
```
GET /api/v1/ocr-worker/images/{pending_id}
```

**返回**：图片文件的 ZIP 包或单张图片

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| Worker 与 API 网络中断 | 心跳检测 + 任务超时重置 |
| OCR 提供商不可用 | 支持多提供商，失败自动重试 |
| 大量任务堆积 | 支持多 Worker 扩展 |
| 图片下载失败 | 重试机制 + 跳过无效任务 |

## Migration Plan

1. 数据库迁移：添加 OCR 字段（向后兼容，新字段默认值）
2. 部署 API 更新
3. 启动 OCR Worker
4. 前端更新（可选，不影响后端功能）

**回滚**：
- Worker 停止即可，不影响现有系统
- 数据库字段保留，不影响原有功能

## Open Questions

1. ~~OCR 结果是否需要结构化解析？~~ → 当前阶段只提取原始文本
2. ~~是否需要支持任务优先级？~~ → 暂不支持，使用 FIFO
