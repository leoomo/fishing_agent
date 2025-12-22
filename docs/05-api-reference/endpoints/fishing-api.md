# 钓鱼API - 智能推荐接口

提供智能钓鱼推荐、天气分析和时段建议的核心功能API。

## 📋 接口概览

### 基础信息
- **路径前缀**: `/api/v1/fishing`
- **认证要求**: 部分接口需要JWT认证
- **支持格式**: JSON
- **请求方法**: POST

## 🎯 核心接口

### 1. 智能钓鱼推荐

聊天式智能钓鱼推荐接口，支持自然语言查询。

```http
POST /api/v1/fishing/chat
```

**请求头**
```http
Content-Type: application/json
Authorization: Bearer <access_token>  # 可选
```

**请求参数**
```json
{
  "query": "明天北京钓鱼怎么样？",     // 必需，用户查询
  "model_provider": "zhipu",          // 可选，模型提供商
  "user_id": 123,                     // 可选，用户ID
  "location": "北京",                  // 可选，指定地点
  "date": "2024-12-21",               // 可选，指定日期
  "time_range": "全天"                 // 可选，时间段
}
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "response": "根据天气预报，明天北京晴朗，温度15-25℃，风力2-3级，气压稳定，非常适合钓鱼！推荐早6-9点或晚5-7点作钓。",
    "recommendation": {
      "overall_score": 85,
      "time_slots": [
        {
          "time": "06:00-09:00",
          "score": 90,
          "reason": "温度适宜，鱼类活跃度高"
        },
        {
          "time": "17:00-19:00",
          "score": 88,
          "reason": "光线柔和，溶氧量充足"
        }
      ],
      "weather": {
        "temperature": "15-25℃",
        "condition": "晴朗",
        "wind": "2-3级",
        "humidity": "45%",
        "pressure": "1013hPa"
      }
    },
    "suggestions": [
      "建议使用路亚装备作钓",
      "推荐选择水库或湖泊",
      "注意防晒和补水"
    ]
  },
  "request_id": "req_1234567890",
  "timestamp": "2024-12-20T10:30:00Z"
}
```

### 2. 获取可用工具

获取系统支持的所有工具列表。

```http
GET /api/v1/fishing/tools
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "tools": [
      {
        "name": "get_weather",
        "description": "获取实时天气信息",
        "parameters": ["location", "date"]
      },
      {
        "name": "query_fishing_recommendation",
        "description": "查询钓鱼推荐",
        "parameters": ["location", "time", "weather"]
      },
      {
        "name": "get_coordinates",
        "description": "获取地理坐标",
        "parameters": ["location"]
      }
    ]
  }
}
```

### 3. 健康检查

检查钓鱼API服务状态。

```http
GET /health
```

**响应示例**
```json
{
  "status": "healthy",
  "service": "fishing-agent",
  "version": "5.0.2",
  "uptime": 86400,
  "timestamp": "2024-12-20T10:30:00Z"
}
```

## 🔧 高级功能

### 4. 批量推荐

批量获取多个地点的钓鱼推荐。

```http
POST /api/v1/fishing/batch-recommendation
```

**请求参数**
```json
{
  "locations": [
    {"name": "北京", "date": "2024-12-21"},
    {"name": "上海", "date": "2024-12-21"},
    {"name": "广州", "date": "2024-12-21"}
  ],
  "time_range": "全天",
  "model_provider": "zhipu"
}
```

### 5. 历史查询

获取用户历史钓鱼推荐记录。

```http
GET /api/v1/fishing/history?user_id=123&page=1&size=20
```

**响应示例**
```json
{
  "status": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "query": "明天北京钓鱼怎么样？",
        "response": "根据天气预报...",
        "location": "北京",
        "score": 85,
        "created_at": "2024-12-20T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 50,
      "pages": 3
    }
  }
}
```

## 📊 评分系统

### 7因子评分体系

系统基于以下7个因子进行科学评分：

| 因子 | 权重 | 说明 |
|------|------|------|
| 温度 | 25% | 体感温度和水温对鱼情的影响 |
| 天气 | 20% | 晴雨、云量对鱼类活动的影响 |
| 风力 | 15% | 风力等级对水层和溶氧量的影响 |
| 气压 | 15% | 气压变化对鱼类觅食的影响 |
| 湿度 | 10% | 空气湿度对舒适度的影响 |
| 季节 | 5% | 不同季节鱼类习性变化 |
| 月相 | 5% | 月相对潮汐和鱼类活动的影响 |

### 评分等级

- **90-100分**: 极佳，强烈推荐
- **80-89分**: 良好，推荐作钓
- **70-79分**: 一般，可以尝试
- **60-69分**: 较差，谨慎选择
- **60分以下**: 不推荐，建议另择时间

## ⚠️ 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查参数格式和必需字段 |
| 401 | 认证失败 | 检查Token是否有效 |
| 429 | 请求频率过高 | 降低请求频率 |
| 500 | 服务内部错误 | 稍后重试或联系技术支持 |

### 错误响应格式

```json
{
  "status": "error",
  "error_code": "INVALID_PARAMETER",
  "message": "地点参数不能为空",
  "details": {
    "field": "location",
    "reason": "required"
  },
  "request_id": "req_1234567890",
  "timestamp": "2024-12-20T10:30:00Z"
}
```

## 🚦 使用限制

### 频率限制
- **匿名用户**: 10请求/小时
- **注册用户**: 100请求/小时
- **VIP用户**: 500请求/小时

### 并发限制
- **单用户**: 5并发请求
- **总并发**: 100并发请求

## 🔗 相关资源

- [认证授权](../authentication.md) - JWT认证说明
- [数据结构](../data-schemas.md) - 请求响应格式
- [错误处理](../error-handling.md) - 详细错误码说明
- [装备API](./equipment-api.md) - 装备管理接口
- [用户管理](./user-management.md) - 用户相关接口

---

**API版本**: v1.0
**文档版本**: v5.0.2
**最后更新**: 2024-12-20