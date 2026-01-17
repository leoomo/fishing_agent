# 管理接口API - 系统管理功能

提供系统管理、用户管理、配置管理和监控功能的管理员专用API。

## 📋 接口概览

### 基础信息
- **路径前缀**: `/api/v1/admin`
- **认证要求**: 必需JWT认证 + 管理员权限
- **支持格式**: JSON
- **权限要求**: admin或super_admin角色

## 🔐 权限控制

### 角色权限矩阵

| 角色 | 用户管理 | 配置管理 | 数据采集 | 监控查看 | 系统配置 |
|------|----------|----------|----------|----------|----------|
| readonly | ❌ | ❌ | ✅ | ✅ | ❌ |
| editor | ❌ | ✅ | ✅ | ✅ | ❌ |
| admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| super_admin | ✅ | ✅ | ✅ | ✅ | ✅ |

## 👥 用户管理接口

### 1. 获取用户列表

获取系统用户列表，支持分页和筛选。

```http
GET /api/v1/admin/users?page=1&size=20&role=admin&status=active&search=张三
```

**查询参数**
- `page`: 页码（默认1）
- `size`: 每页数量（默认20，最大100）
- `role`: 角色筛选（readonly/editor/admin/super_admin）
- `status`: 状态筛选（active/inactive/banned）
- `search`: 搜索关键词（用户名、邮箱）

**响应示例**
```json
{
  "status": "success",
  "data": {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "super_admin",
        "status": "active",
        "last_login": "2024-12-20T10:30:00Z",
        "created_at": "2024-11-01T00:00:00Z",
        "wechat_user": {
          "openid": "wx123456",
          "nickname": "钓鱼达人",
          "avatar": "https://..."
        }
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

### 2. 创建用户

创建新的系统用户。

```http
POST /api/v1/admin/users
```

**请求参数**
```json
{
  "username": "newuser",
  "password": "securePassword123",
  "email": "newuser@example.com",
  "role": "editor",
  "status": "active"
}
```

### 3. 更新用户

更新用户信息和权限。

```http
PUT /api/v1/admin/users/{user_id}
```

**请求参数**
```json
{
  "email": "updated@example.com",
  "role": "admin",
  "status": "active"
}
```

### 4. 删除用户

删除系统用户（软删除）。

```http
DELETE /api/v1/admin/users/{user_id}
```

## 📊 数据分析接口

### 1. 装备统计分析

获取装备数据统计信息。

```http
GET /api/v1/admin/analytics/equipment/stats?start_date=2024-12-01&end_date=2024-12-31
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "total_equipments": 1250,
    "new_equipments": 85,
    "pending_reviews": 12,
    "approved_today": 8,
    "top_brands": [
      {"brand": "光威", "count": 320},
      {"brand": "达亿瓦", "count": 280},
      {"brand": "禧玛诺", "count": 200}
    ],
    "category_distribution": {
      "路亚竿": 450,
      "渔轮": 380,
      "鱼线": 280,
      "拟饵": 140
    }
  }
}
```

### 2. 趋势分析

获取装备数据趋势分析。

```http
GET /api/v1/admin/analytics/equipment/trends?period=30d&metric=daily_additions
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "period": "30d",
    "trends": [
      {"date": "2024-12-01", "value": 12},
      {"date": "2024-12-02", "value": 15},
      {"date": "2024-12-03", "value": 8}
    ],
    "summary": {
      "average": 11.7,
      "peak": 25,
      "growth_rate": "15.3%"
    }
  }
}
```

### 3. 生成报表

生成数据分析报表。

```http
POST /api/v1/admin/analytics/reports/generate
```

**请求参数**
```json
{
  "report_type": "equipment_summary",
  "format": "pdf",
  "period": {
    "start_date": "2024-12-01",
    "end_date": "2024-12-31"
  },
  "filters": {
    "categories": ["路亚竿", "渔轮"],
    "brands": ["光威", "达亿瓦"]
  }
}
```

## ⚙️ 配置管理接口

### 1. 获取配置列表

获取系统配置列表。

```http
GET /api/v1/admin/config/configs?category=api&status=active
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "configs": [
      {
        "id": 1,
        "key": "CAIYUN_API_KEY",
        "value": "************",  // 敏感信息已脱敏
        "description": "彩云天气API密钥",
        "category": "weather",
        "status": "active",
        "updated_at": "2024-12-20T10:30:00Z"
      }
    ]
  }
}
```

### 2. 创建配置

创建新的系统配置。

```http
POST /api/v1/admin/config/configs
```

**请求参数**
```json
{
  "key": "NEW_CONFIG_KEY",
  "value": "config_value",
  "description": "配置描述",
  "category": "system",
  "is_encrypted": true
}
```

### 3. 更新配置

更新系统配置值。

```http
PUT /api/v1/admin/config/configs/{config_id}
```

**请求参数**
```json
{
  "value": "updated_value",
  "description": "更新后的描述"
}
```

### 4. 测试API密钥

测试外部API密钥的有效性。

```http
POST /api/v1/admin/config/configs/test-api-key
```

**请求参数**
```json
{
  "config_key": "CAIYUN_API_KEY",
  "api_value": "test_api_key_value"
}
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "provider": "彩云天气",
    "response_time": 150,
    "test_result": "API密钥有效，服务正常"
  }
}
```

## 🕷️ 数据采集管理接口

### 1. 获取采集任务列表

获取数据采集任务列表。

```http
GET /api/v1/admin/crawler/tasks?page=1&size=20&status=running
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "id": 1,
        "name": "淘宝路亚装备采集",
        "platform": "taobao",
        "status": "running",
        "progress": 65,
        "total_items": 1000,
        "processed_items": 650,
        "created_at": "2024-12-20T08:00:00Z",
        "started_at": "2024-12-20T08:30:00Z",
        "estimated_completion": "2024-12-20T12:00:00Z"
      }
    ]
  }
}
```

### 2. 创建采集任务

创建新的数据采集任务。

```http
POST /api/v1/admin/crawler/tasks
```

**请求参数**
```json
{
  "name": "京东渔轮采集",
  "platform": "jd",
  "keywords": ["渔轮", "纺车轮"],
  "max_pages": 10,
  "schedule": {
    "type": "cron",
    "expression": "0 2 * * *"
  }
}
```

### 3. 触发任务执行

手动触发任务执行。

```http
POST /api/v1/admin/crawler/tasks/{task_id}/trigger
```

### 4. 获取任务日志

获取任务执行日志。

```http
GET /api/v1/admin/crawler/tasks/{task_id}/logs?level=error&page=1
```

## 📈 系统监控接口

### 1. API统计

获取API调用统计信息。

```http
GET /api/v1/admin/monitor/api-stats?period=24h
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "total_requests": 15420,
    "success_rate": 99.2,
    "average_response_time": 185,
    "top_endpoints": [
      {
        "endpoint": "/api/v1/fishing/chat",
        "requests": 8500,
        "avg_response_time": 220
      }
    ],
    "error_distribution": {
      "400": 50,
      "401": 30,
      "500": 10
    }
  }
}
```

### 2. LLM统计

获取大语言模型使用统计。

```http
GET /api/v1/admin/monitor/llm-stats?period=7d
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "total_tokens": 1250000,
    "total_calls": 3200,
    "model_distribution": {
      "zhipu": 1800,
      "dashscope": 900,
      "openai": 500
    },
    "cost_analysis": {
      "total_cost": 125.50,
      "average_cost_per_call": 0.039
    }
  }
}
```

## ✅ 待审核装备管理

### 1. 获取待审核装备列表

获取待审核的装备列表。

```http
GET /api/v1/admin/equipment/pending?page=1&size=20&status=pending
```

### 2. 审核装备

审核单个装备。

```http
PUT /api/v1/admin/equipment/pending/{pending_id}/review
```

**请求参数**
```json
{
  "action": "approve",  // approve/reject/modify
  "review_note": "装备信息完整，审核通过",
  "modifications": {   // 仅当action=modify时需要
    "price": 299.00,
    "description": "更新后的描述"
  }
}
```

### 3. 批量审核

批量审核多个装备。

```http
POST /api/v1/admin/equipment/pending/batch-review
```

**请求参数**
```json
{
  "pending_ids": [1, 2, 3, 4, 5],
  "action": "approve",
  "review_note": "批量审核通过"
}
```

## ⚠️ 错误处理

### 管理员权限错误

```json
{
  "status": "error",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "message": "需要管理员权限才能访问此接口",
  "required_role": "admin"
}
```

### 资源不存在错误

```json
{
  "status": "error",
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "用户ID 123 不存在",
  "resource_type": "user",
  "resource_id": 123
}
```

## 🔗 相关资源

- [认证授权](../authentication.md) - JWT认证和权限管理
- [数据结构](../data-schemas.md) - 请求响应格式
- [用户管理](./user-management.md) - 用户相关接口
- [装备API](./equipment-api.md) - 装备管理接口
- [数据分析](./analytics-api.md) - 统计分析接口

---

**API版本**: v1.0
**文档版本**: v5.1.0
**最后更新**: 2025-01-16
**权限要求**: 管理员角色