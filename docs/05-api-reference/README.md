# API参考文档

完整的智能钓鱼助手RESTful API接口文档，面向需要集成或调用API的开发者。

## 📋 API概览

### 🌐 基础信息
- **Base URL**: `https://api.fishing-agent.com`
- **API版本**: v1
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

### 🔗 [认证授权](./authentication.md)
- JWT认证机制
- 微信小程序登录
- API密钥管理
- 权限控制说明

### 🎣 [核心接口](./endpoints/)
- **[钓鱼API](./endpoints/fishing-api.md)** - 智能钓鱼推荐
- **[装备API](./endpoints/equipment-api.md)** - 装备管理功能
- **[用户管理](./endpoints/user-management.md)** - 用户和认证
- **[数据分析](./endpoints/analytics-api.md)** - 统计分析
- **[管理接口](./endpoints/admin-api.md)** - 管理员功能

### 📊 [数据结构](./data-schemas.md)
- 请求参数说明
- 响应数据格式
- 错误码定义
- 数据类型约束

### ⚠️ [错误处理](./error-handling.md)
- HTTP状态码说明
- 错误响应格式
- 常见错误示例
- 故障排除指南

### 🚦 [限流规则](./rate-limiting.md)
- API调用频率限制
- 配额说明
- 限流策略
- 提升限额申请

## 🎯 快速开始

### 1. 获取访问令牌
```bash
# 微信小程序登录
curl -X POST "https://api.fishing-agent.com/api/v1/auth/wechat/login" \
  -H "Content-Type: application/json" \
  -d '{"code": "your_wechat_code"}'

# 响应示例
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 123,
    "username": "fisher_user",
    "avatar": "https://..."
  }
}
```

### 2. 调用API接口
```bash
# 使用Token调用钓鱼推荐接口
curl -X POST "https://api.fishing-agent.com/api/v1/fishing/chat" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "明天北京钓鱼怎么样？",
    "model_provider": "zhipu",
    "user_id": 123
  }'

# 响应示例
{
  "response": "根据天气预报，明天北京晴朗，温度15-25℃，风力2-3级，非常适合钓鱼。建议早6-9点或晚5-7点作钓。",
  "status": "success",
  "request_id": "req_1234567890",
  "timestamp": "2024-12-20T10:30:00Z"
}
```

## 📡 API功能分类

### 核心功能API
- **智能推荐**: 基于天气和7因子的钓鱼建议
- **装备管理**: 钓鱼装备查询、添加、管理
- **用户服务**: 用户认证、个人信息管理
- **数据分析**: 个人数据和统计信息

### 高级功能API
- **OCR识别**: 图片文字识别和数据提取
- **装备导入**: 批量装备信息导入
- **爬虫管理**: 爬虫任务控制
- **系统配置**: 系统参数和配置管理

### 管理功能API
- **用户管理**: 用户列表和权限管理
- **系统监控**: 服务状态和性能监控
- **日志查询**: 操作日志和错误日志
- **数据导出**: 业务数据导出

## 🔧 开发工具

### Postman集合
提供完整的Postman集合文件，包含所有API接口的示例：
- [下载Postman集合](./postman/fishing-agent-api.json)
- [环境变量配置](./postman/environment.json)

### SDK支持
```python
# Python SDK示例
from fishing_agent_sdk import FishingClient

client = FishingClient(
    base_url="https://api.fishing-agent.com",
    api_key="your_api_key"
)

# 获取钓鱼推荐
response = client.fishing.get_recommendation(
    query="明天上海钓鱼怎么样？",
    location="上海",
    model="zhipu"
)
```

```javascript
// JavaScript SDK示例
import { FishingAgentAPI } from 'fishing-agent-sdk';

const api = new FishingAgentAPI({
  baseURL: 'https://api.fishing-agent.com',
  apiKey: 'your_api_key'
});

// 获取钓鱼推荐
const response = await api.fishing.getRecommendation({
  query: '明天上海钓鱼怎么样？',
  location: '上海',
  model: 'zhipu'
});
```

## 📋 接口规范

### HTTP方法
- `GET`: 获取资源
- `POST`: 创建资源或执行操作
- `PUT`: 更新整个资源
- `PATCH`: 部分更新资源
- `DELETE`: 删除资源

### 请求头
```http
Content-Type: application/json
Authorization: Bearer <access_token>
User-Agent: fishing-agent-sdk/1.0.0
X-Request-ID: <unique_request_id>
```

### 响应格式
```json
{
  "status": "success|error",
  "data": {
    // 业务数据
  },
  "message": "操作结果描述",
  "request_id": "唯一请求ID",
  "timestamp": "2024-12-20T10:30:00Z"
}
```

## 🔍 查询和过滤

### 分页参数
```bash
GET /api/v1/equipment?page=1&size=20&sort=created_at&order=desc

# 响应
{
  "data": [...],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 100,
    "pages": 5
  }
}
```

### 过滤参数
```bash
GET /api/v1/equipment?brand=光威&category=路亚竿&price_min=100&price_max=500
```

### 搜索参数
```bash
GET /api/v1/equipment?q=赤刃&search_fields=brand,model,description
```

## 🚦 速率限制

### 限制策略
- **默认限制**: 100请求/分钟/用户
- **API密钥**: 1000请求/分钟/密钥
- **管理员**: 5000请求/分钟/用户

### 限流响应
```json
{
  "status": "error",
  "message": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

### 请求头信息
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 🔄 版本管理

### API版本控制
- **URL版本**: `/api/v1/`, `/api/v2/`
- **Header版本**: `Accept: application/vnd.fishing-agent.v1+json`
- **查询参数**: `?version=1`

### 版本兼容性
- **向后兼容**: 旧版本API至少维护12个月
- **弃用通知**: 提前3个月通知API弃用
- **迁移指南**: 提供版本迁移文档

## 📊 监控和分析

### API监控
- **可用性**: 99.9% SLA保证
- **响应时间**: P95 < 500ms
- **错误率**: < 0.1%

### 使用分析
- **调用统计**: 实时API调用统计
- **用户分析**: API用户行为分析
- **性能监控**: API性能和健康检查

## 🔗 相关资源

### 开发资源
- [SDK下载](https://github.com/fishing-agent/sdk)
- [开发文档](../02-developer-guide/)
- [测试指南](../02-developer-guide/testing.md)
- [调试工具](./debug-tools/)

### 社区支持
- [开发者论坛](https://community.fishing-agent.com)
- [GitHub Issues](https://github.com/fishing-agent/api/issues)
- [技术支持](mailto:dev@fishing-agent.com)
- [API状态](https://status.fishing-agent.com)

### 更新日志
- [v1.0.0](./changelog/v1.0.0.md) - 初始版本
- [v1.1.0](./changelog/v1.1.0.md) - 添加装备管理API
- [v1.2.0](./changelog/v1.2.0.md) - 微信小程序集成

## 🎯 适用场景

### 应用集成
- **微信小程序**: 钓鱼助手小程序后端
- **移动应用**: iOS/Android应用集成
- **Web应用**: 第三方网站集成
- **企业系统**: 企业内部系统集成

### 开发场景
- **数据查询**: 钓鱼数据和天气信息
- **业务流程**: 装备管理和推荐系统
- **用户服务**: 用户认证和个人数据
- **分析统计**: 数据分析和报表生成

---

**API版本**: v1.0  
**文档版本**: v5.0.2  
**最后更新**: 2024-12-20  
**维护团队**: 智能钓鱼助手API团队