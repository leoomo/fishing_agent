# API 参考文档

本文档提供了智能钓鱼助手所有 REST API 的详细说明和示例。

## 目录

- [认证方式](#认证方式)
- [基础信息](#基础信息)
- [核心 API](#核心-api)
- [认证 API](#认证-api)
- [用户装备管理 API](#用户装备管理-api)
- [爬虫管理 API](#爬虫管理-api)
- [工作流管理 API](#工作流管理-api)
- [监控管理 API](#监控管理-api)
- [数据分析管理 API](#数据分析管理-api)
- [配置管理 API](#配置管理-api)

## 认证方式

### JWT Token 认证

大部分 API 需要使用 JWT Token 进行认证：

```bash
# 获取 Token
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123"
}

# 在请求头中使用 Token
Authorization: Bearer <your_jwt_token>
```

### 权限说明

- **管理员权限**：可访问所有管理 API
- **普通用户权限**：可访问用户装备相关 API

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: `v1`
- **数据格式**: `JSON`

## 核心 API

### 1. 健康检查

检查 API 服务状态。

```http
GET /health
```

**响应示例**:
```json
{
  "status": "ok"
}
```

### 2. 智能对话

核心的钓鱼推荐对话接口。

```http
POST /api/v1/fishing/chat
```

**请求体**:
```json
{
  "query": "明天杭州钓鱼怎么样？",
  "model_provider": "zhipu",
  "user_id": 1
}
```

**响应示例**:
```json
{
  "response": "根据天气分析，明天杭州白天钓鱼条件较好...",
  "model_used": "zhipu",
  "timestamp": "2024-12-11T12:00:00Z"
}
```

### 3. 工具列表

获取所有可用的工具。

```http
GET /api/v1/fishing/tools
```

**响应示例**:
```json
{
  "tools": [
    {
      "name": "get_current_time",
      "description": "获取当前时间",
      "type": "basic"
    },
    {
      "name": "get_weather",
      "description": "获取天气信息",
      "type": "weather"
    },
    {
      "name": "query_fishing_recommendation",
      "description": "查询钓鱼推荐",
      "type": "fishing"
    }
  ],
  "total": 3
}
```

## 认证 API

### 1. 用户登录

获取访问 Token。

```http
POST /api/v1/auth/login
```

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 12,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  }
}
```

### 2. 获取用户信息

获取当前登录用户的信息。

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### 3. 用户登出

使 Token 失效。

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

## 用户装备管理 API

### 1. 创建用户

创建新用户档案。

```http
POST /api/v1/user-equipment/users
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "username": "test_user",
  "nickname": "测试用户",
  "user_level": "新手",
  "fishing_experience_years": 2,
  "preferred_fish": "鲈鱼,翘嘴"
}
```

### 2. 添加装备到用户库

为用户添加装备记录。

```http
POST /api/v1/user-equipment/users/{user_id}/equipment
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "equipment_id": 123,
  "purchase_price": 599.99,
  "purchase_date": "2024-01-15",
  "notes": "我的第一支鱼竿",
  "tags": ["入门", "鲈鱼专用"]
}
```

### 3. 查询用户装备列表

获取用户的装备清单。

```http
GET /api/v1/user-equipment/users/{user_id}/equipment?page=1&page_size=20&category=鱼竿
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 20）
- `category`: 装备类别（可选）
- `brand`: 品牌（可选）
- `is_favorite`: 是否收藏（可选）

### 4. 获取装备推荐

为用户生成装备推荐。

```http
POST /api/v1/user-equipment/users/{user_id}/recommend
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "recommendation_type": "upgrade",
  "budget": 1000,
  "target_fish": "鲈鱼"
}
```

### 5. 获取装备统计

获取用户的装备统计信息。

```http
GET /api/v1/user-equipment/users/{user_id}/statistics
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "total_count": 15,
  "total_spent": 5280.50,
  "category_counts": {
    "鱼竿": 5,
    "渔轮": 3,
    "拟饵": 7
  },
  "favorite_count": 8
}
```

## 爬虫管理 API

### 1. 查询爬虫任务列表

获取所有爬虫任务。

```http
GET /api/v1/admin/crawler/tasks?page=1&page_size=10
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "tasks": [
    {
      "id": 1,
      "task_type": "taobao",
      "status": "running",
      "created_at": "2024-12-11T10:00:00Z",
      "progress": 45
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 10
}
```

### 2. 手动触发爬虫任务

创建并执行新的爬虫任务。

```http
POST /api/v1/admin/crawler/tasks/trigger
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "task_type": "taobao",
  "keywords": ["路亚竿", "渔轮"],
  "max_pages": 5,
  "category": "鱼竿"
}
```

### 3. 获取任务详情

查看特定任务的详细信息。

```http
GET /api/v1/admin/crawler/tasks/{task_id}
Authorization: Bearer <token>
```

### 4. 重试失败任务

重新执行失败的任务。

```http
POST /api/v1/admin/crawler/tasks/{task_id}/retry
Authorization: Bearer <token>
```

### 5. 获取数据同步状态

查看爬虫数据同步统计。

```http
GET /api/v1/admin/crawler/sync-status
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "total_equipment": 1500,
  "last_sync": "2024-12-11T08:00:00Z",
  "sync_status": "success",
  "source_stats": {
    "taobao": 800,
    "jd": 500,
    "forum": 200
  }
}
```

## 工作流管理 API

### 1. 创建工作流模板

创建新的工作流模板。

```http
POST /api/v1/admin/crawler/workflows/templates
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "name": "商品数据爬取工作流",
  "description": "定期爬取电商平台商品数据",
  "steps": [
    {
      "name": "爬取淘宝商品",
      "task_type": "taobao",
      "config": {
        "keywords": ["路亚竿", "渔轮"],
        "max_pages": 5
      },
      "depends_on": []
    },
    {
      "name": "爬取京东商品",
      "task_type": "jd",
      "config": {
        "keywords": ["路亚竿", "渔轮"],
        "max_pages": 3
      },
      "depends_on": []
    },
    {
      "name": "数据整合",
      "task_type": "data_merge",
      "config": {},
      "depends_on": ["爬取淘宝商品", "爬取京东商品"]
    }
  ]
}
```

**响应示例**:
```json
{
  "id": 1,
  "name": "商品数据爬取工作流",
  "description": "定期爬取电商平台商品数据",
  "steps": [...],
  "is_active": true,
  "created_at": "2024-12-14T10:00:00Z",
  "updated_at": "2024-12-14T10:00:00Z"
}
```

### 2. 获取工作流模板列表

查询所有工作流模板。

```http
GET /api/v1/admin/crawler/workflows/templates?page=1&page_size=10
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码（默认 1）
- `page_size`: 每页数量（默认 10）
- `is_active`: 是否激活（可选）

### 3. 更新工作流模板

更新现有的工作流模板。

```http
PUT /api/v1/admin/crawler/workflows/templates/{template_id}
Authorization: Bearer <token>
```

**请求体**: 与创建模板相同的结构

### 4. 删除工作流模板

删除指定的工作流模板。

```http
DELETE /api/v1/admin/crawler/workflows/templates/{template_id}
Authorization: Bearer <token>
```

### 5. 执行工作流

手动触发工作流执行。

```http
POST /api/v1/admin/crawler/workflows/execute
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "template_id": 1,
  "params": {
    "override_config": {
      "max_pages": 10
    }
  }
}
```

**响应示例**:
```json
{
  "execution_id": "exec_20241214_001",
  "template_id": 1,
  "status": "running",
  "started_at": "2024-12-14T11:00:00Z"
}
```

### 6. 查询工作流执行状态

获取工作流的执行状态和进度。

```http
GET /api/v1/admin/crawler/workflows/status/{execution_id}
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "execution_id": "exec_20241214_001",
  "template_id": 1,
  "status": "running",
  "progress": {
    "total_steps": 3,
    "completed_steps": 2,
    "current_step": "数据整合"
  },
  "step_statuses": [
    {
      "step_name": "爬取淘宝商品",
      "status": "completed",
      "started_at": "2024-12-14T11:00:00Z",
      "completed_at": "2024-12-14T11:05:00Z"
    },
    {
      "step_name": "爬取京东商品",
      "status": "completed",
      "started_at": "2024-12-14T11:00:00Z",
      "completed_at": "2024-12-14T11:04:00Z"
    },
    {
      "step_name": "数据整合",
      "status": "running",
      "started_at": "2024-12-14T11:05:00Z"
    }
  ],
  "logs": [
    {
      "timestamp": "2024-12-14T11:05:00Z",
      "level": "INFO",
      "message": "开始执行数据整合步骤"
    }
  ]
}
```

### 7. 停止工作流执行

停止正在执行的工作流。

```http
POST /api/v1/admin/crawler/workflows/stop/{execution_id}
Authorization: Bearer <token>
```

### 8. 创建调度任务

为工作流创建定时调度。

```http
POST /api/v1/admin/crawler/schedules
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "name": "每日商品数据同步",
  "template_id": 1,
  "cron_expression": "0 2 * * *",
  "timezone": "Asia/Shanghai",
  "is_active": true,
  "params": {
    "notification_email": "admin@example.com"
  }
}
```

**Cron表达式说明**:
- 格式: `分 时 日 月 周`
- 示例: `0 2 * * *` (每天凌晨2点执行)

### 9. 获取调度列表

查询所有调度任务。

```http
GET /api/v1/admin/crawler/schedules?page=1&page_size=10
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "schedules": [
    {
      "id": 1,
      "name": "每日商品数据同步",
      "template_id": 1,
      "template_name": "商品数据爬取工作流",
      "cron_expression": "0 2 * * *",
      "timezone": "Asia/Shanghai",
      "is_active": true,
      "last_run": "2024-12-14T02:00:00Z",
      "next_run": "2024-12-15T02:00:00Z",
      "created_at": "2024-12-10T10:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10
}
```

### 10. 更新调度任务

修改调度任务配置。

```http
PUT /api/v1/admin/crawler/schedules/{schedule_id}
Authorization: Bearer <token>
```

### 11. 删除调度任务

删除指定的调度任务。

```http
DELETE /api/v1/admin/crawler/schedules/{schedule_id}
Authorization: Bearer <token>
```

### 12. 预览调度时间

预览Cron表达式的未来执行时间。

```http
POST /api/v1/admin/crawler/schedules/preview
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "cron_expression": "0 2 * * *",
  "timezone": "Asia/Shanghai",
  "count": 5
}
```

**响应示例**:
```json
{
  "next_runs": [
    "2024-12-15T02:00:00+08:00",
    "2024-12-16T02:00:00+08:00",
    "2024-12-17T02:00:00+08:00",
    "2024-12-18T02:00:00+08:00",
    "2024-12-19T02:00:00+08:00"
  ]
}
```

## 监控管理 API

### 1. API 调用统计

获取 API 使用统计。

```http
GET /api/v1/admin/monitor/api-stats
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "total_requests": 10000,
  "average_response_time": 245,
  "error_rate": 0.02,
  "top_endpoints": [
    {
      "path": "/api/v1/fishing/chat",
      "count": 5000,
      "avg_response_time": 320
    }
  ]
}
```

### 2. LLM 使用统计

获取 LLM 调用统计。

```http
GET /api/v1/admin/monitor/llm-stats
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "total_tokens": 1500000,
  "total_cost": 25.50,
  "success_rate": 0.98,
  "provider_stats": {
    "zhipu": {
      "tokens": 900000,
      "cost": 15.30,
      "requests": 4500
    },
    "qwen": {
      "tokens": 600000,
      "cost": 10.20,
      "requests": 3000
    }
  }
}
```

### 3. 数据库性能监控

获取数据库性能指标。

```http
GET /api/v1/admin/monitor/db-performance
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "connection_pool": {
    "active": 5,
    "idle": 15,
    "total": 20
  },
  "slow_queries": [
    {
      "query": "SELECT * FROM equipment WHERE...",
      "duration": 1250,
      "count": 3
    }
  ],
  "table_sizes": {
    "equipment": "2.5MB",
    "users": "0.5MB"
  }
}
```

### 4. 系统健康检查

检查各服务状态。

```http
GET /api/v1/admin/monitor/health-check
```

**响应示例**:
```json
{
  "api": "healthy",
  "database": "healthy",
  "llm_services": {
    "zhipu": "healthy",
    "qwen": "degraded"
  },
  "external_apis": {
    "caiyun": "healthy",
    "amap": "healthy"
  }
}
```

## 数据分析管理 API

### 1. 装备数据统计总览

获取装备数据的统计概览。

```http
GET /api/v1/admin/analytics/equipment/stats
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "total_equipment": 1500,
  "category_distribution": {
    "鱼竿": 600,
    "渔轮": 400,
    "拟饵": 350,
    "配件": 150
  },
  "price_ranges": {
    "0-200": 400,
    "200-500": 600,
    "500-1000": 350,
    "1000+": 150
  },
  "user_levels": {
    "新手": 800,
    "进阶": 500,
    "高手": 200
  }
}
```

### 2. 装备趋势分析

按月统计装备增长趋势。

```http
GET /api/v1/admin/analytics/equipment/trends?months=12
Authorization: Bearer <token>
```

**查询参数**:
- `months`: 统计月数（默认 12）

**响应示例**:
```json
{
  "monthly_data": [
    {
      "month": "2024-01",
      "equipment_count": 1200,
      "new_additions": 50
    },
    {
      "month": "2024-02",
      "equipment_count": 1250,
      "new_additions": 50
    }
  ],
  "growth_rate": 0.042
}
```

### 3. 价格分布统计

获取装备价格分布情况。

```http
GET /api/v1/admin/analytics/equipment/price-distribution
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "ranges": [
    {
      "range": "0-200",
      "count": 400,
      "percentage": 26.7
    },
    {
      "range": "200-500",
      "count": 600,
      "percentage": 40.0
    }
  ],
  "average_price": 485.50,
  "median_price": 380.00
}
```

### 4. 品牌统计排行

获取品牌使用统计。

```http
GET /api/v1/admin/analytics/equipment/brand-stats?top_n=10
Authorization: Bearer <token>
```

**查询参数**:
- `top_n`: 返回前 N 个品牌（默认 10）

**响应示例**:
```json
{
  "brands": [
    {
      "brand": "禧玛诺",
      "count": 300,
      "percentage": 20.0
    },
    {
      "brand": "达亿瓦",
      "count": 250,
      "percentage": 16.7
    }
  ]
}
```

### 5. 用户活跃度统计

获取用户活跃度分析。

```http
GET /api/v1/admin/analytics/users/activity?days=30
Authorization: Bearer <token>
```

**查询参数**:
- `days`: 统计天数（默认 30）

**响应示例**:
```json
{
  "active_users": 850,
  "new_users": 45,
  "daily_active": [
    {
      "date": "2024-12-10",
      "active_count": 120
    }
  ],
  "retention_rate": 0.78
}
```

### 6. 生成业务报表

生成各类业务报表。

```http
POST /api/v1/admin/analytics/reports/generate
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "report_type": "equipment",
  "format": "pdf",
  "filters": {
    "category": "鱼竿",
    "date_range": "2024-01-01,2024-12-31",
    "price_min": 200,
    "price_max": 1000
  },
  "include_charts": true
}
```

**响应示例**:
```json
{
  "report_id": "report_20241211_001",
  "status": "generating",
  "download_url": null,
  "estimated_completion": "2024-12-11T12:05:00Z"
}
```

### 7. 查询报表列表

获取已生成的报表列表。

```http
GET /api/v1/admin/analytics/reports/list?page=1&page_size=20
Authorization: Bearer <token>
```

## 配置管理 API

### 1. 查询配置列表

获取系统配置项列表。

```http
GET /api/v1/admin/config/configs?type=api&page=1&page_size=20
Authorization: Bearer <token>
```

**查询参数**:
- `type`: 配置类型（api, system, algorithm, agent）
- `page`: 页码
- `page_size`: 每页数量

**响应示例**:
```json
{
  "configs": [
    {
      "config_key": "CAIYUN_API_KEY",
      "config_type": "api",
      "description": "彩云天气API密钥",
      "is_encrypted": true,
      "updated_at": "2024-12-11T10:00:00Z"
    }
  ],
  "total": 25
}
```

### 2. 获取特定配置

获取单个配置项的值。

```http
GET /api/v1/admin/config/configs/CAIYUN_API_KEY
Authorization: Bearer <token>
```

**响应示例**:
```json
{
  "config_key": "CAIYUN_API_KEY",
  "config_value": "***",
  "config_type": "api",
  "description": "彩云天气API密钥",
  "is_encrypted": true
}
```

### 3. 创建配置

创建新的配置项。

```http
POST /api/v1/admin/config/configs
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "config_key": "NEW_API_KEY",
  "config_value": "your_api_key_value",
  "config_type": "api",
  "description": "新API密钥配置",
  "is_encrypted": true
}
```

### 4. 更新配置

更新现有配置项。

```http
PUT /api/v1/admin/config/configs/CAIYUN_API_KEY
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "config_value": "new_api_key_value",
  "description": "更新后的彩云天气API密钥"
}
```

### 5. 删除配置

删除配置项。

```http
DELETE /api/v1/admin/config/configs/OLD_CONFIG
Authorization: Bearer <token>
```

### 6. 测试 API 密钥

验证 API 密钥的有效性。

```http
POST /api/v1/admin/config/configs/test-api-key
Authorization: Bearer <token>
```

**请求体**:
```json
{
  "api_type": "caiyun",
  "api_key": "test_api_key_value"
}
```

**响应示例**:
```json
{
  "valid": true,
  "message": "API密钥有效",
  "response_time": 245
}
```

## 错误处理

### 标准错误响应

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "请求参数无效",
    "details": {
      "field": "location",
      "reason": "不能为空"
    }
  }
}
```

### 常见错误码

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | INVALID_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未认证或 Token 无效 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMITED | 请求频率超限 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

## 速率限制

- 未认证用户：100 请求/小时
- 普通用户：1000 请求/小时
- 管理员：无限制

## SDK 示例

### Python

```python
import requests

# 登录获取 token
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['access_token']

# 使用 token 调用 API
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/admin/analytics/equipment/stats',
    headers=headers
)
```

### JavaScript

```javascript
// 登录获取 token
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});
const {access_token} = await loginResponse.json();

// 使用 token 调用 API
const response = await fetch('http://localhost:8000/api/v1/admin/analytics/equipment/stats', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
```

---

更多信息请参考：
- [快速入门](./GETTING_STARTED.md)
- [用户指南](./USER_GUIDE.md)
- [架构文档](./ARCHITECTURE.md)