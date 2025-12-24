# Change: 添加分布式 OCR Worker 服务

## Why

当前系统中，爬虫从电商平台抓取的装备数据（PendingEquipment）包含产品图片，但缺乏自动化的 OCR 文本提取能力。人工查看图片并手动录入规格参数效率低下，无法支撑大规模数据处理需求。

需要一个分布式 OCR Worker 系统，能够：
- 自动从待审装备图片中提取文本
- 支持多 Worker 节点远程部署，提高处理吞吐量
- 提供前端管理界面监控 OCR 任务状态

## What Changes

### 后端变更
- 扩展 `PendingEquipment` 模型，添加 OCR 状态跟踪字段（ocr_status, ocr_worker_id, ocr_started_at 等）
- 新增 `/api/v1/ocr-worker/*` API 端点（注册、领取任务、汇报结果、心跳、图片下载）
- 新增 OCR 任务统计和列表查询接口（供前端使用）

### Worker 变更
- 创建 `OCRWorker` 类，复用现有 OCR 提供商（Ollama/SiliconFlow）
- 支持分布式部署：注册认证、任务轮询、结果汇报、心跳保活
- 提供 CLI 入口，便于远程启动

### 前端变更
- 新增 OCR Worker 管理页面（统计卡片 + 任务列表）
- 新增 Redux slice 和 API 服务

## Impact

- Affected specs: 新增 `ocr-worker` 能力规格
- Affected code:
  - `packages/agents/equipment_import/models/pending.py` - 模型扩展
  - `apps/api/routes/` - 新增路由文件
  - `packages/scraper/worker/` - 新增 Worker 实现
  - `apps/web-admin/src/` - 新增前端页面和状态管理
