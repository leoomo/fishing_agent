# Fishing Agent API Documentation

智能钓鱼助手 REST API 文档

**版本**: v3.1.1
**架构**: FastAPI 后端 + 模块化 Agent 包 + 动态Prompt中间件
**Base URL**: `http://localhost:8000`

## 概述

Fishing Agent API 提供智能钓鱼助手的 RESTful 接口，支持钓鱼推荐、天气查询、装备推荐等功能。基于 FastAPI 框架构建，使用模块化 Agent 架构和动态Prompt中间件系统。

## 核心特性

- 🚀 **FastAPI 后端**: 高性能异步 API 服务
- 🔐 **JWT 认证**: 安全的用户认证和权限管理
- 📦 **模块化 Agent**: 完全自包含的 Agent 包架构
- 🧠 **动态Prompt中间件**: 智能选择提示词，优化Token使用效率50%+
- 🎣 **智能推荐**: 7因子科学评分系统
- 🌤️ **天气查询**: 实时天气数据和72小时预报
- 🎯 **时段识别**: 精准的时间段意图理解（98%+准确率）
- 🧠 **LLM 优化**: 高质量的自然语言处理
- 🛠️ **调试工具**: 完整的开发调试支持

## API 端点

### 1. API 信息

#### GET `/`
获取 API 基本信息。

**响应示例**:
```json
{
  "name": "智能钓鱼助手 API",
  "version": "3.1.1",
  "description": "基于LangChain 1.0+和动态Prompt中间件的智能钓鱼助手",
  "features": [
    "动态Prompt中间件",
    "7因子科学评分",
    "时间段意图识别",
    "LLM优化"
  ],
  "docs": "/docs"
}
```

### 2. 健康检查

#### GET `/health`
检查 API 服务状态。

**响应示例**:
```json
{
  "status": "ok"
}
```

### 3. 认证管理

#### POST `/api/v1/auth/login`
管理员用户登录，获取 JWT 访问令牌。

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**参数说明**:
- `username` (string, required): 用户名（3-50字符）
- `password` (string, required): 密码（6-100字符）

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "full_name": "Administrator",
    "is_active": true
  },
  "permissions": ["equipment:create", "equipment:read", "equipment:update", "equipment:delete"]
}
```

#### GET `/api/v1/auth/profile`
获取当前用户信息（需要认证）。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "full_name": "Administrator",
    "is_active": true
  },
  "permissions": ["equipment:create", "equipment:read", "equipment:update", "equipment:delete"]
}
```

#### POST `/api/v1/auth/logout`
用户登出（需要认证）。

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "message": "登出成功"
}
```

**注意**: JWT 是无状态的，实际登出需要在客户端删除 token。

### 4. 钓鱼助手对话

#### POST `/api/v1/fishing/chat`
与钓鱼助手进行对话交互。

**请求体**:
```json
{
  "query": "明天杭州钓鱼怎么样？",
  "model_provider": "zhipu"
}
```

**参数说明**:
- `query` (string, required): 用户查询内容
- `model_provider` (string, optional): LLM 提供商，默认 "zhipu"
  - 可选值: "zhipu", "qwen", "doubao", "openai"

**响应示例**:
```json
{
  "response": "根据天气预报分析，明天杭州白天钓鱼条件较好...\n\n📊 **详细评分**:\n🥇 **最佳时段**: 09:00-11:00 (92分)\n🥈 **次优时段**: 14:00-16:00 (88分)\n\n🌤️ **天气详情**: ...\n🎯 **钓点建议**: ...",
  "status": "success",
  "error": null
}
```

**状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器内部错误

### 5. 工具列表

#### GET `/api/v1/fishing/tools`
获取所有可用的 Agent 工具列表。

**响应示例**:
```json
{
  "tools": [
    {
      "name": "get_current_time",
      "description": "获取当前时间，支持多种格式输出"
    },
    {
      "name": "get_weather",
      "description": "获取指定地点的天气信息"
    },
    {
      "name": "query_fishing_recommendation",
      "description": "查询钓鱼推荐，基于7因子科学评分系统"
    },
    {
      "name": "recommend_equipment",
      "description": "智能推荐路亚装备"
    },
    {
      "name": "compare_equipment",
      "description": "对比多款路亚装备"
    },
    {
      "name": "lookup_fishing_knowledge",
      "description": "查询钓鱼知识"
    },
    {
      "name": "identify_from_image",
      "description": "识别钓鱼相关图片"
    }
  ]
}
```

## 使用指南

### 基础对话

```bash
curl -X POST "http://localhost:8000/api/v1/fishing/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "明天白天杭州哪里适合钓鱼？",
    "model_provider": "zhipu"
  }'
```

### 天气查询

```bash
curl -X POST "http://localhost:8000/api/v1/fishing/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "北京今天天气怎么样？"
  }'
```

### 钓鱼推荐

```bash
curl -X POST "http://localhost:8000/api/v1/fishing/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "这个周末上海钓鱼有什么建议吗？"
  }'
```

### 装备推荐

```bash
curl -X POST "http://localhost:8000/api/v1/fishing/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "新手想买一套500元的路亚装备，主要钓鲈鱼，有什么推荐？"
  }'
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

- `400 Bad Request`: 请求参数格式错误或缺失必要参数
- `500 Internal Server Error`: 服务器内部错误，通常是 LLM API 调用失败

### 示例错误响应

```json
{
  "detail": "query field is required"
}
```

## 性能特性

### 响应时间

- **平均响应时间**: 2-5 秒（包含 LLM 推理时间）
- **健康检查**: < 50ms
- **工具列表**: < 100ms

### 并发处理

- **最大并发**: 100 个请求
- **队列处理**: 超出并发限制的请求会排队等待
- **超时设置**: 60 秒请求超时

## 限制和配额

### 请求限制

- **频率限制**: 每分钟最多 60 次请求
- **内容长度**: 查询内容最大 1000 字符
- **响应长度**: 响应内容最大 10000 字符

### 使用建议

1. **批量查询**: 避免频繁的单次请求，可以合并多个问题
2. **缓存结果**: 对于相同查询，可以缓存响应结果
3. **错误重试**: 实现指数退避的重试机制
4. **超时设置**: 客户端设置合理的超时时间

## 集成示例

### Python 客户端

```python
import requests
import json

class FishingAgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def chat(self, query, model_provider="zhipu"):
        """与钓鱼助手对话"""
        url = f"{self.base_url}/api/v1/fishing/chat"
        data = {
            "query": query,
            "model_provider": model_provider
        }

        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_tools(self):
        """获取工具列表"""
        url = f"{self.base_url}/api/v1/fishing/tools"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def health_check(self):
        """健康检查"""
        url = f"{self.base_url}/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

# 使用示例
client = FishingAgentClient()

# 健康检查
health = client.health_check()
print(f"服务状态: {health['status']}")

# 获取工具列表
tools = client.get_tools()
print(f"可用工具: {len(tools['tools'])} 个")

# 钓鱼查询
result = client.chat("明天杭州钓鱼怎么样？")
print(f"AI回复: {result['response']}")
```

### JavaScript 客户端

```javascript
class FishingAgentClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async chat(query, modelProvider = 'zhipu') {
        const response = await fetch(`${this.baseUrl}/api/v1/fishing/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                model_provider: modelProvider
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async getTools() {
        const response = await fetch(`${this.baseUrl}/api/v1/fishing/tools`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
}

// 使用示例
const client = new FishingAgentClient();

// 钓鱼查询
client.chat('明天杭州钓鱼怎么样？')
    .then(result => {
        console.log('AI回复:', result.response);
    })
    .catch(error => {
        console.error('请求失败:', error);
    });
```

## 部署指南

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量配置

```bash
# 必需的环境变量
export CAIYUN_API_KEY="your-caiyun-api-key"
export AMAP_API_KEY="your-amap-api-key"
export ANTHROPIC_AUTH_TOKEN="your-zhipu-token"
export DASHSCOPE_API_KEY="your-dashscope-api-key"

# 可选配置
export LOG_LEVEL="INFO"
export MAX_CONCURRENT_REQUESTS="100"
```

## 更新日志

### v3.1.1
- 🔐 新增 JWT 认证系统，支持管理员登录
- 👥 实现用户权限管理（RBAC）
- 🛡️ 添加认证中间件和安全保护
- 🔧 完善的测试覆盖和错误处理

### v3.1.0
- 🚀 新增 FastAPI REST API 后端
- 📦 集成模块化 Agent 架构
- 🎯 支持多种 LLM 提供商
- 📝 完整的 API 文档和示例

### v3.0.2
- 🎣 新增路亚装备推荐功能
- 🔍 支持向量搜索和装备对比
- 📱 完善的图片识别功能

## 支持与反馈

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: [项目邮箱]
- 🐛 问题反馈: [GitHub Issues]
- 📖 文档: [项目文档地址]

---

> 🎣 智能钓鱼，从此开始！