# Phase 4 爬虫和监控模块快速启动指南

## 🚀 快速启动

### 1. 启动 API 服务器

```bash
# 确保环境变量已配置
cp .env.example .env
# 编辑 .env 文件，设置必需的 API 密钥

# 启动服务器
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问 API 文档

```bash
# Swagger UI（推荐）
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc
```

## 🔐 获取访问 Token

使用管理员账户登录获取 token：

```bash
# 如果还没有创建管理员账户
uv run python scripts/create_admin.py --username admin --password admin123

# 登录获取 token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# 设置 token 环境变量
export TOKEN="your_access_token_here"
```

## 🕷️ 爬虫管理 API

### 查询爬虫任务列表

```bash
curl "http://localhost:8000/api/v1/admin/crawler/tasks?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# 按类型过滤
curl "http://localhost:8000/api/v1/admin/crawler/tasks?task_type=taobao" \
  -H "Authorization: Bearer $TOKEN"

# 按状态过滤
curl "http://localhost:8000/api/v1/admin/crawler/tasks?status=success" \
  -H "Authorization: Bearer $TOKEN"
```

### 手动触发爬虫任务

```bash
# 淘宝爬虫
curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/trigger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "taobao",
    "keywords": ["路亚竿", "渔轮"],
    "max_pages": 5,
    "proxy": null
  }'

# 京东爬虫
curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/trigger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "jd",
    "keywords": ["钓鱼竿"],
    "max_pages": 3
  }'

# 论坛爬虫
curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/trigger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "forum",
    "keywords": ["路亚技巧"],
    "max_pages": 10
  }'
```

### 获取任务详情

```bash
# 获取任务详情
curl "http://localhost:8000/api/v1/admin/crawler/tasks/1" \
  -H "Authorization: Bearer $TOKEN"

# 获取任务日志
curl "http://localhost:8000/api/v1/admin/crawler/tasks/1/logs" \
  -H "Authorization: Bearer $TOKEN"

# 按日志级别过滤
curl "http://localhost:8000/api/v1/admin/crawler/tasks/1/logs?level=error" \
  -H "Authorization: Bearer $TOKEN"
```

### 重试失败任务

```bash
# 重试任务（仅失败状态的任务可以重试）
curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/1/retry" \
  -H "Authorization: Bearer $TOKEN"
```

### 删除任务记录

```bash
# 删除任务（无法删除正在运行的任务）
curl -X DELETE "http://localhost:8000/api/v1/admin/crawler/tasks/1" \
  -H "Authorization: Bearer $TOKEN"
```

### 获取数据同步状态

```bash
curl "http://localhost:8000/api/v1/admin/crawler/sync-status" \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 监控管理 API

### API 调用统计

```bash
# 获取最近7天的API统计
curl "http://localhost:8000/api/v1/admin/monitor/api-stats" \
  -H "Authorization: Bearer $TOKEN"

# 指定日期范围
curl "http://localhost:8000/api/v1/admin/monitor/api-stats?start_date=2025-12-01&end_date=2025-12-10" \
  -H "Authorization: Bearer $TOKEN"
```

**响应示例**:
```json
{
  "total_calls": 1250,
  "avg_response_time": 45.3,
  "error_rate": 2.4,
  "top_endpoints": [
    {
      "endpoint": "/api/v1/fishing/chat",
      "count": 350,
      "avg_time": 120.5
    },
    {
      "endpoint": "/api/v1/admin/equipment",
      "count": 200,
      "avg_time": 25.3
    }
  ]
}
```

### LLM 使用统计

```bash
# 获取最近7天的LLM统计
curl "http://localhost:8000/api/v1/admin/monitor/llm-stats" \
  -H "Authorization: Bearer $TOKEN"

# 指定日期范围
curl "http://localhost:8000/api/v1/admin/monitor/llm-stats?start_date=2025-12-01&end_date=2025-12-10" \
  -H "Authorization: Bearer $TOKEN"
```

**响应示例**:
```json
{
  "total_calls": 450,
  "total_tokens": 125000,
  "total_cost": 15.75,
  "avg_response_time": 1.2,
  "success_rate": 98.5,
  "by_provider": {
    "qwen": {
      "calls": 300,
      "tokens": 80000,
      "cost": 10.0
    },
    "zhipu": {
      "calls": 150,
      "tokens": 45000,
      "cost": 5.75
    }
  }
}
```

### 数据库性能监控

```bash
curl "http://localhost:8000/api/v1/admin/monitor/db-performance" \
  -H "Authorization: Bearer $TOKEN"
```

**响应示例**:
```json
{
  "avg_query_time": 25.5,
  "slow_queries_count": 3,
  "connection_pool_size": 10,
  "active_connections": 2,
  "table_sizes": {
    "equipment": 150,
    "users": 80,
    "fishing_logs": 120,
    "crawler_tasks": 45,
    "api_logs": 200
  }
}
```

### 系统健康检查

```bash
# 健康检查（无需认证）
curl "http://localhost:8000/api/v1/admin/monitor/health-check"
```

**响应示例**:
```json
{
  "status": "healthy",
  "api_status": "healthy",
  "db_status": "healthy",
  "llm_status": "healthy",
  "uptime_seconds": 3600.5
}
```

## 🔌 WebSocket 实时监控

### 爬虫任务进度监控

使用 WebSocket 客户端连接爬虫任务进度：

**JavaScript 示例**:
```javascript
// 连接到爬虫任务进度 WebSocket
const taskId = 1;
const ws = new WebSocket(`ws://localhost:8000/api/v1/admin/crawler/ws/crawler/${taskId}`);

ws.onopen = () => {
  console.log('WebSocket 连接已建立');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('任务进度:', data);
  /*
  {
    "task_id": 1,
    "status": "running",
    "progress": "50/100",
    "success_items": 50,
    "failed_items": 2,
    "timestamp": "2025-12-10T10:30:45.123456"
  }
  */
};

ws.onerror = (error) => {
  console.error('WebSocket 错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket 连接已关闭');
};
```

**使用 websocat 命令行工具**:
```bash
# 安装 websocat
# macOS: brew install websocat
# Linux: cargo install websocat

# 连接到爬虫进度 WebSocket
websocat ws://localhost:8000/api/v1/admin/crawler/ws/crawler/1
```

### 系统实时监控

**JavaScript 示例**:
```javascript
// 连接到系统实时监控 WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/admin/monitor/ws/realtime-stats');

ws.onmessage = (event) => {
  const stats = JSON.parse(event.data);
  console.log('实时统计:', stats);
  /*
  {
    "timestamp": "2025-12-10T10:30:45.123456",
    "api_calls_per_minute": 25,
    "api_errors_per_minute": 1,
    "llm_calls_per_minute": 5,
    "llm_tokens_per_minute": 1200
  }
  */

  // 更新 UI 仪表盘
  updateDashboard(stats);
};
```

**使用 websocat**:
```bash
websocat ws://localhost:8000/api/v1/admin/monitor/ws/realtime-stats
```

## 🧪 运行测试

```bash
# 运行 Phase 4 集成测试（需要先创建 admin 用户）
uv run pytest tests/api/test_crawler_monitor.py -v

# 运行特定测试
uv run pytest tests/api/test_crawler_monitor.py::test_trigger_crawler_task -v

# 运行所有 API 测试
uv run pytest tests/api/ -v
```

## 🔍 常见问题

### 1. 401 Unauthorized
**问题**: 请求返回 401 错误
**解决**: 检查 token 是否正确，是否已过期（默认60分钟）

### 2. 403 Forbidden
**问题**: 请求返回 403 错误
**解决**: 检查当前用户是否有对应的权限（admin 用户有所有权限）

### 3. 爬虫任务没有进度
**问题**: 触发爬虫后任务一直是 pending 状态
**解决**: 当前为演示模式，未实际启动爬虫进程。生产环境需实现真实的爬虫逻辑。

### 4. WebSocket 连接失败
**问题**: WebSocket 无法连接
**解决**:
- 确保 API 服务器正在运行
- 检查防火墙设置
- 使用 `ws://` 而不是 `wss://`（开发环境）

### 5. 监控数据为0
**问题**: API/LLM 统计数据都是0
**解决**: 需要先产生一些 API 调用和 LLM 调用，监控数据才会有记录。可以尝试调用几次钓鱼助手 API。

## 📚 更多资源

- **API 文档**: http://localhost:8000/docs
- **开发计划**: docs/dev-plans/phase4-crawler-monitor.md
- **完成总结**: PHASE4_SUMMARY.md
- **Phase 3 文档**: QUICKSTART_PHASE3.md

## 💡 使用技巧

### 1. 批量触发爬虫任务

```bash
# 创建批量触发脚本
for type in taobao jd forum; do
  curl -X POST "http://localhost:8000/api/v1/admin/crawler/tasks/trigger" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"task_type\": \"$type\",
      \"keywords\": [\"路亚竿\"],
      \"max_pages\": 5
    }"
  sleep 1
done
```

### 2. 监控仪表盘

结合 WebSocket 创建实时监控仪表盘：

```html
<!DOCTYPE html>
<html>
<head>
  <title>系统监控仪表盘</title>
</head>
<body>
  <h1>实时系统监控</h1>
  <div id="stats"></div>

  <script>
    const ws = new WebSocket('ws://localhost:8000/api/v1/admin/monitor/ws/realtime-stats');

    ws.onmessage = (event) => {
      const stats = JSON.parse(event.data);
      document.getElementById('stats').innerHTML = `
        <p>API 调用/分钟: ${stats.api_calls_per_minute}</p>
        <p>API 错误/分钟: ${stats.api_errors_per_minute}</p>
        <p>LLM 调用/分钟: ${stats.llm_calls_per_minute}</p>
        <p>Token 消耗/分钟: ${stats.llm_tokens_per_minute}</p>
        <p>更新时间: ${stats.timestamp}</p>
      `;
    };
  </script>
</body>
</html>
```

### 3. 定期生成监控报告

```bash
# 创建监控报告脚本
#!/bin/bash
DATE=$(date +%Y-%m-%d)

# API 统计
curl "http://localhost:8000/api/v1/admin/monitor/api-stats" \
  -H "Authorization: Bearer $TOKEN" \
  > "reports/api_stats_${DATE}.json"

# LLM 统计
curl "http://localhost:8000/api/v1/admin/monitor/llm-stats" \
  -H "Authorization: Bearer $TOKEN" \
  > "reports/llm_stats_${DATE}.json"

echo "监控报告已生成: reports/*_${DATE}.json"
```

---

**开发完成日期**: 2025-12-10
**当前版本**: v4.0.0
