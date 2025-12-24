# 实施任务清单

## 1. 数据模型扩展

- [x] 1.1 在 `PendingEquipment` 模型中添加 OCR 相关字段
  - `ocr_status`: OCR 状态（pending/processing/completed/failed/skipped）
  - `ocr_started_at`: OCR 开始时间
  - `ocr_completed_at`: OCR 完成时间
  - `ocr_worker_id`: 处理该任务的 Worker ID
  - `ocr_error_message`: OCR 错误信息
  - `ocr_retry_count`: 重试次数
  - `ocr_provider`: 使用的 OCR 提供商
  - `ocr_processing_time_ms`: 处理耗时

## 2. 后端 API 开发

- [x] 2.1 创建 `apps/api/schemas/ocr_worker.py` - 请求/响应模型
- [x] 2.2 创建 `apps/api/routes/ocr_worker.py` - API 路由
  - POST `/register` - Worker 注册
  - POST `/claim` - 领取 OCR 任务
  - POST `/report` - 汇报 OCR 结果
  - POST `/heartbeat` - Worker 心跳
  - GET `/images/{pending_id}` - 下载图片
  - GET `/stats` - OCR 任务统计
  - GET `/tasks` - OCR 任务列表
- [x] 2.3 在 `apps/api/main.py` 中注册路由

## 3. OCR Worker 开发

- [x] 3.1 创建 `packages/scraper/worker/ocr_worker.py` - OCR Worker 主类
  - 继承/复用 ApiWorker 模式
  - 集成 OCR 提供商（Ollama/SiliconFlow）
  - 实现任务执行流程：下载图片 → OCR 识别 → 汇报结果
- [x] 3.2 创建 `packages/scraper/worker/ocr_cli.py` - CLI 入口
- [x] 3.3 更新 `packages/scraper/worker/__init__.py` - 导出 OCRWorker

## 4. 前端开发

- [x] 4.1 创建 `apps/web-admin/src/types/ocrWorker.ts` - 类型定义
- [x] 4.2 创建 `apps/web-admin/src/api/services/ocrWorker.ts` - API 服务
- [x] 4.3 创建 `apps/web-admin/src/store/slices/ocrWorkerSlice.ts` - Redux slice
- [x] 4.4 创建 `apps/web-admin/src/pages/OCRWorker/index.tsx` - 管理页面
- [x] 4.5 更新 `apps/web-admin/src/App.tsx` - 添加路由
- [x] 4.6 更新 `apps/web-admin/src/store/store.ts` - 注册 reducer
- [x] 4.7 更新 `apps/web-admin/src/components/Layout/MainLayout.tsx` - 添加侧边栏菜单

## 5. 测试与验证

- [x] 5.1 验证 API 路由加载（7 个端点确认）
- [x] 5.2 验证 OCRWorker 和 OCRWorkerClient 模块导入
- [x] 5.3 验证前端 TypeScript 编译（OCR Worker 相关代码无错误）
- [x] 5.4 端到端测试：Worker 与服务端通信
- [x] 5.5 端到端测试：完整 OCR 流程（图片下载 → 识别 → 结果保存）
- [x] 5.6 端到端测试：前端页面功能

## 实施完成文件清单

### 新建文件 (9 个)
| 文件 | 状态 |
|------|------|
| `apps/api/schemas/ocr_worker.py` | ✅ 完成 |
| `apps/api/routes/ocr_worker.py` | ✅ 完成 |
| `packages/scraper/worker/ocr_worker.py` | ✅ 完成 |
| `packages/scraper/worker/ocr_cli.py` | ✅ 完成 |
| `apps/web-admin/src/types/ocrWorker.ts` | ✅ 完成 |
| `apps/web-admin/src/api/services/ocrWorker.ts` | ✅ 完成 |
| `apps/web-admin/src/store/slices/ocrWorkerSlice.ts` | ✅ 完成 |
| `apps/web-admin/src/pages/OCRWorker/index.tsx` | ✅ 完成 |

### 修改文件 (5 个)
| 文件 | 修改内容 | 状态 |
|------|----------|------|
| `packages/agents/equipment_import/models/pending.py` | 添加 OCR 字段 | ✅ 完成 |
| `apps/api/main.py` | 注册 ocr_worker 路由 | ✅ 完成 |
| `packages/scraper/worker/__init__.py` | 导出 OCRWorker | ✅ 完成 |
| `apps/web-admin/src/App.tsx` | 添加 OCRWorker 路由 | ✅ 完成 |
| `apps/web-admin/src/store/store.ts` | 添加 ocrWorker reducer | ✅ 完成 |
| `apps/web-admin/src/components/Layout/MainLayout.tsx` | 添加侧边栏菜单 | ✅ 完成 |
