# OCR Worker 能力规格

## ADDED Requirements

### Requirement: OCR 任务管理

系统 SHALL 支持 OCR 任务的生命周期管理，包括任务创建、分配、执行和完成。

#### Scenario: 任务自动创建
- **WHEN** 新的 PendingEquipment 记录被创建且包含图片
- **THEN** 该记录的 ocr_status 默认为 "pending"
- **AND** 可被 OCR Worker 领取处理

#### Scenario: 任务状态流转
- **WHEN** OCR 任务被处理
- **THEN** 状态按 pending → processing → completed/failed 流转
- **AND** 失败任务在重试次数未超限时可重置为 pending

---

### Requirement: OCR Worker 注册认证

系统 SHALL 支持远程 OCR Worker 的注册和认证。

#### Scenario: Worker 注册成功
- **GIVEN** 一个新的 OCR Worker
- **WHEN** Worker 发送注册请求（包含 worker_id、名称、支持的类型）
- **THEN** 系统返回认证 Token
- **AND** Worker 使用该 Token 进行后续请求

#### Scenario: Token 验证
- **WHEN** Worker 发送带有 X-Worker-Token 头的请求
- **THEN** 系统验证 Token 格式和有效性
- **AND** 无效 Token 返回 401 错误

---

### Requirement: OCR 任务领取

系统 SHALL 支持 OCR Worker 主动领取待处理任务。

#### Scenario: 领取可用任务
- **GIVEN** 存在 ocr_status 为 "pending" 的 PendingEquipment
- **WHEN** Worker 调用领取接口
- **THEN** 系统返回待处理任务列表（包含 pending_id、图片路径）
- **AND** 任务 ocr_status 更新为 "processing"
- **AND** 记录 ocr_worker_id 和 ocr_started_at

#### Scenario: 无可用任务
- **WHEN** Worker 调用领取接口但无待处理任务
- **THEN** 系统返回空任务列表
- **AND** Worker 继续轮询等待

---

### Requirement: OCR 结果汇报

系统 SHALL 支持 Worker 汇报 OCR 处理结果。

#### Scenario: OCR 成功
- **WHEN** Worker 完成 OCR 识别并汇报成功结果
- **THEN** PendingEquipment.ocr_text 更新为识别的文本
- **AND** ocr_status 更新为 "completed"
- **AND** 记录 ocr_completed_at 和 ocr_processing_time_ms

#### Scenario: OCR 失败
- **WHEN** Worker 汇报 OCR 失败
- **THEN** ocr_retry_count 增加 1
- **AND** 如果重试次数 < 3，ocr_status 重置为 "pending"
- **AND** 如果重试次数 >= 3，ocr_status 更新为 "failed"
- **AND** 记录 ocr_error_message

---

### Requirement: Worker 心跳保活

系统 SHALL 支持 Worker 心跳机制以监控存活状态。

#### Scenario: 正常心跳
- **WHEN** Worker 定期发送心跳请求
- **THEN** 系统记录心跳时间
- **AND** 返回服务器时间和下发命令（如取消任务）

#### Scenario: 任务超时检测
- **WHEN** 任务 ocr_status 为 "processing" 且 ocr_started_at 超过 30 分钟
- **THEN** 系统可将任务状态重置为 "pending"
- **AND** 允许其他 Worker 重新领取

---

### Requirement: 图片下载接口

系统 SHALL 提供图片下载接口供 Worker 获取待处理图片。

#### Scenario: 下载成功
- **GIVEN** PendingEquipment 记录存在且有关联图片
- **WHEN** Worker 请求下载图片
- **THEN** 系统返回图片文件或图片列表
- **AND** 图片可被 Worker 本地处理

#### Scenario: 图片不存在
- **WHEN** Worker 请求下载不存在的图片
- **THEN** 系统返回 404 错误

---

### Requirement: OCR 任务统计

系统 SHALL 提供 OCR 任务统计接口供管理界面展示。

#### Scenario: 获取统计数据
- **WHEN** 前端请求 OCR 统计接口
- **THEN** 系统返回各状态的任务数量
- **AND** 包含 pending、processing、completed、failed 的计数

---

### Requirement: OCR 任务列表查询

系统 SHALL 提供 OCR 任务列表查询接口。

#### Scenario: 分页查询
- **WHEN** 前端请求任务列表（带分页参数）
- **THEN** 系统返回分页的任务数据
- **AND** 包含 pending_id、品牌、状态、Worker、耗时等信息

#### Scenario: 状态筛选
- **WHEN** 前端按 ocr_status 筛选任务
- **THEN** 系统返回符合条件的任务列表
