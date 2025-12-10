# API 完整参考

**版本**: v4.0.0
**基础URL**: `http://localhost:8000`
**最后更新**: 2025-12-10

## 目录

- [概述](#概述)
- [认证](#认证)
- [错误处理](#错误处理)
- [认证 API](#认证-api)
- [钓鱼助手 API](#钓鱼助手-api)
- [用户装备管理 API](#用户装备管理-api)
- [爬虫管理 API](#爬虫管理-api) ⭐ v4.0.0新增
- [监控管理 API](#监控管理-api) ⭐ v4.0.0新增
- [WebSocket API](#websocket-api) ⭐ v4.0.0新增
- [数据模型](#数据模型)

---

## 概述

智能钓鱼助手 API 提供五类接口：

1. **钓鱼助手 API** (`/api/v1/fishing/`)
   - Agent 对话接口
   - 工具列表查询

2. **用户装备管理 API** (`/api/v1/user-equipment/`)
   - 用户管理
   - 装备库管理
   - 推荐功能
   - 统计分析

3. **爬虫管理 API** (`/api/v1/admin/crawler/`) ⭐ v4.0.0新增
   - 爬虫任务管理
   - 任务调度和监控
   - 任务日志查询

4. **监控管理 API** (`/api/v1/admin/monitor/`) ⭐ v4.0.0新增
   - API调用统计
   - LLM使用统计
   - 数据库性能监控
   - 系统健康检查

5. **WebSocket API** (`/ws/`) ⭐ v4.0.0新增
   - 爬虫任务实时进度推送
   - 系统监控实时数据推送

### 技术栈

- **框架**: FastAPI
- **文档**: OpenAPI 3.0 (Swagger UI)
- **格式**: JSON
- **编码**: UTF-8

### 交互式文档

启动服务后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 认证

本版本已实现 **JWT Token 认证机制**，用于管理员用户认证。

### 创建管理员账户

首次使用前需要创建管理员账户：

```bash
# 使用脚本创建管理员用户
uv run python scripts/create_admin.py --username admin --password admin123

# 或者手动注册（通过 API）
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "email": "admin@example.com"
  }'
```

### 获取访问令牌

```bash
# 登录获取 JWT Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# 响应示例
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 使用 Token 访问 API

```bash
# 在请求头中添加 Token
curl "http://localhost:8000/api/v1/admin/crawler/tasks" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 令牌使用说明
在需要认证的请求头中添加：`Authorization: Bearer <token>`

### Token 有效期

- **默认有效期**: 30分钟
- **算法**: HS256
- **编码**: Base64URL

### 认证端点

详细接口文档请参考 [认证 API](#认证-api) 部分。

### 保护的端点

以下端点需要认证：
- `GET /api/v1/auth/profile` - 获取用户信息
- `POST /api/v1/auth/logout` - 用户登出

**未来版本**将支持：
- API Key 认证
- OAuth 2.0
- 刷新令牌机制

---

## 错误处理

### 标准错误响应

```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证/认证失败 |
| 403 | 禁止访问（权限不足） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 常见错误示例

#### 400 Bad Request

```json
{
  "detail": "用户名已存在: fishing_lover_001"
}
```

#### 404 Not Found

```json
{
  "detail": "用户不存在: 999"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "数据库连接失败"
}
```

---

## 认证 API

### POST /api/v1/auth/login

管理员用户登录

#### 请求

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（3-50字符） |
| password | string | 是 | 密码（6-100字符） |

#### 响应

**200 OK**:
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
    "is_active": true,
    "last_login": "2024-12-10T10:30:00",
    "created_at": "2024-12-01T00:00:00"
  },
  "permissions": ["equipment:create", "equipment:read", "equipment:update", "equipment:delete"]
}
```

**401 Unauthorized**:
```json
{
  "detail": "用户名或密码错误"
}
```

**403 Forbidden**:
```json
{
  "detail": "账户已被禁用，请联系管理员"
}
```

#### cURL 示例

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

---

### GET /api/v1/auth/profile

获取当前用户信息

#### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 响应

**200 OK**:
```json
{
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "full_name": "Administrator",
    "is_active": true,
    "last_login": "2024-12-10T10:30:00",
    "created_at": "2024-12-01T00:00:00"
  },
  "permissions": ["equipment:create", "equipment:read", "equipment:update", "equipment:delete"]
}
```

**401 Unauthorized**:
```json
{
  "detail": "Token 验证失败"
}
```

#### cURL 示例

```bash
curl -X GET "http://localhost:8000/api/v1/auth/profile" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### POST /api/v1/auth/logout

用户登出

#### 请求

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### 响应

**200 OK**:
```json
{
  "message": "登出成功"
}
```

**注意**: JWT 是无状态的，实际登出需要在客户端删除 token。

#### cURL 示例

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 钓鱼助手 API

### POST /api/v1/fishing/chat

与钓鱼助手对话

#### 请求

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "query": "明天杭州西湖适合钓鱼吗？",
  "model_provider": "zhipu",
  "user_id": 1
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 用户查询内容 |
| model_provider | string | 否 | LLM提供商（默认: "zhipu"） |
| user_id | integer | 否 | 用户ID（用于用户装备管理） |

**model_provider 可选值**:
- `zhipu`: 智谱AI (推荐)
- `dashscope`: 通义千问
- `openai`: OpenAI

#### 响应

**200 OK**:
```json
{
  "response": "根据明天的天气预报...\n\n钓鱼评分: 7.5分\n推荐时间: 06:00-09:00, 16:00-18:00",
  "status": "success",
  "error": null
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Agent 执行失败: ..."
}
```

#### cURL 示例

```bash
curl -X POST "http://localhost:8000/api/v1/fishing/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "明天杭州西湖适合钓鱼吗？",
    "model_provider": "zhipu",
    "user_id": 1
  }'
```

#### Python 示例

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/fishing/chat",
    json={
        "query": "推荐一款入门级路亚竿",
        "model_provider": "zhipu",
        "user_id": 1
    }
)

result = response.json()
print(result["response"])
```

---

### GET /api/v1/fishing/tools

获取所有可用工具列表

#### 请求

无需参数

#### 响应

**200 OK**:
```json
{
  "tools": [
    {
      "name": "get_current_time",
      "description": "获取当前时间和日期信息\n\nReturns:\n    当前的详细时间信息..."
    },
    {
      "name": "get_weather",
      "description": "获取指定位置的天气信息（纯天气查询专用工具）..."
    },
    {
      "name": "list_my_equipment",
      "description": "查看我的装备库\n\n触发关键词：我的装备、我有哪些..."
    }
  ]
}
```

#### cURL 示例

```bash
curl "http://localhost:8000/api/v1/fishing/tools"
```

---

## 用户装备管理 API

### 用户管理

#### POST /api/v1/user-equipment/users

创建新用户

**请求**:
```json
{
  "username": "fishing_lover_001",
  "nickname": "路亚小白",
  "email": "user@example.com",
  "user_level": "新手",
  "fishing_experience_years": 1,
  "preferred_fish": "鲈鱼"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| username | string | 是 | 3-50字符，唯一 | 用户名 |
| nickname | string | 否 | 最多100字符 | 昵称 |
| email | string | 否 | 邮箱格式 | 邮箱地址 |
| user_level | string | 否 | 新手/进阶/高手 | 用户水平（默认：新手） |
| fishing_experience_years | integer | 否 | 0-100 | 钓龄（年） |
| preferred_fish | string | 否 | 最多200字符 | 偏好鱼种 |

**响应 201 Created**:
```json
{
  "success": true,
  "message": "用户创建成功",
  "data": {
    "user_id": 1,
    "username": "fishing_lover_001"
  }
}
```

**错误 400 Bad Request**:
```json
{
  "detail": "用户名已存在: fishing_lover_001"
}
```

---

#### GET /api/v1/user-equipment/users/{user_id}

获取用户信息

**路径参数**:
- `user_id` (integer, 必填): 用户ID

**响应 200 OK**:
```json
{
  "user_id": 1,
  "username": "fishing_lover_001",
  "nickname": "路亚小白",
  "email": "user@example.com",
  "user_level": "新手",
  "fishing_experience_years": 1,
  "preferred_fish": "鲈鱼",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**错误 404 Not Found**:
```json
{
  "detail": "用户不存在: 999"
}
```

---

### 装备库管理

#### POST /api/v1/user-equipment/users/{user_id}/equipment

添加装备到用户库

**路径参数**:
- `user_id` (integer, 必填): 用户ID

**请求**:
```json
{
  "equipment_id": 1,
  "purchase_price": 680.0,
  "purchase_date": "2024-01-15",
  "purchase_source": "淘宝旗舰店",
  "notes": "第一把路亚竿",
  "tags": ["入门", "ML调", "岸钓"]
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| equipment_id | integer | 是 | >0 | 装备ID |
| purchase_price | number | 否 | ≥0 | 购买价格（元） |
| purchase_date | string | 否 | YYYY-MM-DD | 购买日期 |
| purchase_source | string | 否 | 最多200字符 | 购买渠道 |
| notes | string | 否 | 最多500字符 | 备注 |
| tags | array[string] | 否 | 最多10个 | 标签列表 |

**响应 201 Created**:
```json
{
  "success": true,
  "message": "装备添加成功",
  "data": {
    "record_id": 1,
    "equipment_id": 1
  }
}
```

**错误响应**:

- **400 Bad Request** - 装备不存在或已添加:
```json
{
  "detail": "装备已在装备库中: equipment_id=1"
}
```

- **404 Not Found** - 用户不存在:
```json
{
  "detail": "用户不存在: 999"
}
```

---

#### GET /api/v1/user-equipment/users/{user_id}/equipment

查询用户装备列表

**路径参数**:
- `user_id` (integer, 必填): 用户ID

**查询参数**:
- `category` (string, 可选): 装备类别过滤（鱼竿/渔轮/鱼线/拟饵）
- `only_favorites` (boolean, 可选): 仅显示收藏装备（默认: false）

**响应 200 OK**:
```json
{
  "total": 3,
  "equipment_list": [
    {
      "id": 1,
      "user_id": 1,
      "equipment_id": 1,
      "equipment_name": "禧玛诺ZODIAS 264ML",
      "category": "鱼竿",
      "brand_name": "禧玛诺",
      "model": "264ML",
      "purchase_date": "2024-01-15",
      "purchase_price": 680.0,
      "purchase_source": "淘宝旗舰店",
      "condition": "正常",
      "usage_frequency": null,
      "notes": "第一把路亚竿",
      "is_favorite": true,
      "tags": "[\"入门\", \"ML调\"]",
      "created_at": "2024-01-15T10:35:00"
    },
    {
      "id": 2,
      "equipment_id": 2,
      "equipment_name": "达亿瓦BASS X 662ML",
      "category": "鱼竿",
      "brand_name": "达亿瓦",
      "purchase_price": 450.0,
      "is_favorite": false,
      "created_at": "2024-01-16T15:20:00"
    }
  ]
}
```

**示例**:

```bash
# 查询所有装备
curl "http://localhost:8000/api/v1/user-equipment/users/1/equipment"

# 查询鱼竿类装备
curl "http://localhost:8000/api/v1/user-equipment/users/1/equipment?category=鱼竿"

# 查询收藏装备
curl "http://localhost:8000/api/v1/user-equipment/users/1/equipment?only_favorites=true"
```

---

#### DELETE /api/v1/user-equipment/users/{user_id}/equipment/{equipment_id}

删除装备

**路径参数**:
- `user_id` (integer, 必填): 用户ID
- `equipment_id` (integer, 必填): 装备ID

**响应 200 OK**:
```json
{
  "success": true,
  "message": "装备删除成功",
  "data": {
    "equipment_id": 1
  }
}
```

**错误 404 Not Found**:
```json
{
  "detail": "装备不在用户库中: equipment_id=1"
}
```

**示例**:

```bash
curl -X DELETE "http://localhost:8000/api/v1/user-equipment/users/1/equipment/1"
```

---

### 推荐功能

#### POST /api/v1/user-equipment/users/{user_id}/recommend

基于用户装备推荐

**路径参数**:
- `user_id` (integer, 必填): 用户ID

**请求**:
```json
{
  "need_type": "upgrade"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 可选值 | 说明 |
|------|------|------|--------|------|
| need_type | string | 是 | upgrade/complete/match | 推荐类型 |

**need_type 说明**:
- `upgrade`: 升级推荐 - 推荐更高级的同类装备
- `complete`: 完善推荐 - 推荐缺失的装备类型
- `match`: 搭配推荐 - 分析装备是否匹配

**响应 200 OK**:
```json
{
  "recommendation": "# 装备升级推荐\n\n分析您的 3 件装备后...",
  "need_type": "upgrade"
}
```

**示例**:

```bash
# 升级推荐
curl -X POST "http://localhost:8000/api/v1/user-equipment/users/1/recommend" \
  -H "Content-Type: application/json" \
  -d '{"need_type": "upgrade"}'

# 完善推荐
curl -X POST "http://localhost:8000/api/v1/user-equipment/users/1/recommend" \
  -H "Content-Type: application/json" \
  -d '{"need_type": "complete"}'

# 搭配推荐
curl -X POST "http://localhost:8000/api/v1/user-equipment/users/1/recommend" \
  -H "Content-Type: application/json" \
  -d '{"need_type": "match"}'
```

---

### 统计功能

#### GET /api/v1/user-equipment/users/{user_id}/statistics

获取用户装备统计

**路径参数**:
- `user_id` (integer, 必填): 用户ID

**响应 200 OK**:
```json
{
  "user_id": 1,
  "total_count": 5,
  "total_spent": 2150.0,
  "favorite_count": 2,
  "by_category": [
    {
      "category": "鱼竿",
      "count": 2,
      "avg_price": 565.0,
      "total_price": 1130.0
    },
    {
      "category": "渔轮",
      "count": 2,
      "avg_price": 350.0,
      "total_price": 700.0
    },
    {
      "category": "拟饵",
      "count": 1,
      "avg_price": 120.0,
      "total_price": 120.0
    }
  ]
}
```

**示例**:

```bash
curl "http://localhost:8000/api/v1/user-equipment/users/1/statistics"
```

---

## 数据模型

### UserCreate

创建用户请求模型

```typescript
{
  username: string;          // 3-50字符，唯一
  nickname?: string;         // 最多100字符
  email?: string;           // 邮箱格式
  user_level?: "新手" | "进阶" | "高手";  // 默认：新手
  fishing_experience_years?: number;  // 0-100
  preferred_fish?: string;  // 最多200字符
}
```

### UserResponse

用户信息响应模型

```typescript
{
  user_id: number;
  username: string;
  nickname: string | null;
  email: string | null;
  user_level: string;
  fishing_experience_years: number | null;
  preferred_fish: string | null;
  created_at: string;      // ISO 8601 格式
  updated_at: string;      // ISO 8601 格式
}
```

### AddEquipmentRequest

添加装备请求模型

```typescript
{
  equipment_id: number;           // >0
  purchase_price?: number;        // ≥0
  purchase_date?: string;         // YYYY-MM-DD
  purchase_source?: string;       // 最多200字符
  notes?: string;                 // 最多500字符
  tags?: string[];                // 最多10个
}
```

### UserEquipmentResponse

用户装备响应模型

```typescript
{
  id: number;
  user_id: number;
  equipment_id: number;
  equipment_name: string;
  category: string;
  brand_name: string | null;
  model: string | null;
  purchase_date: string | null;
  purchase_price: number | null;
  purchase_source: string | null;
  condition: string;
  usage_frequency: string | null;
  notes: string | null;
  is_favorite: boolean;
  tags: string | null;            // JSON字符串
  created_at: string;             // ISO 8601 格式
}
```

### UserEquipmentListResponse

用户装备列表响应模型

```typescript
{
  total: number;
  equipment_list: UserEquipmentResponse[];
}
```

### RecommendRequest

推荐请求模型

```typescript
{
  need_type: "upgrade" | "complete" | "match";
}
```

### RecommendResponse

推荐响应模型

```typescript
{
  recommendation: string;  // Markdown格式的推荐报告
  need_type: string;
}
```

### CategoryStatistics

类别统计模型

```typescript
{
  category: string;
  count: number;
  avg_price: number | null;
  total_price: number | null;
}
```

### UserStatisticsResponse

用户装备统计响应模型

```typescript
{
  user_id: number;
  total_count: number;
  total_spent: number;
  favorite_count: number;
  by_category: CategoryStatistics[];
}
```

### ChatRequest

对话请求模型

```typescript
{
  query: string;
  model_provider?: string;  // 默认："zhipu"
  user_id?: number;
}
```

### ChatResponse

对话响应模型

```typescript
{
  response: string;
  status: string;           // "success" | "error"
  error: string | null;
}
```

---

## 完整示例

### Python 客户端示例

```python
import requests

class FishingAgentClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def chat(self, query, model_provider="zhipu", user_id=None):
        """与 Agent 对话"""
        response = self.session.post(
            f"{self.base_url}/api/v1/fishing/chat",
            json={
                "query": query,
                "model_provider": model_provider,
                "user_id": user_id
            }
        )
        response.raise_for_status()
        return response.json()

    def create_user(self, username, **kwargs):
        """创建用户"""
        response = self.session.post(
            f"{self.base_url}/api/v1/user-equipment/users",
            json={"username": username, **kwargs}
        )
        response.raise_for_status()
        return response.json()

    def add_equipment(self, user_id, equipment_id, **kwargs):
        """添加装备"""
        response = self.session.post(
            f"{self.base_url}/api/v1/user-equipment/users/{user_id}/equipment",
            json={"equipment_id": equipment_id, **kwargs}
        )
        response.raise_for_status()
        return response.json()

    def list_equipment(self, user_id, category=None, only_favorites=False):
        """查询装备列表"""
        params = {}
        if category:
            params["category"] = category
        if only_favorites:
            params["only_favorites"] = only_favorites

        response = self.session.get(
            f"{self.base_url}/api/v1/user-equipment/users/{user_id}/equipment",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_recommendation(self, user_id, need_type):
        """获取推荐"""
        response = self.session.post(
            f"{self.base_url}/api/v1/user-equipment/users/{user_id}/recommend",
            json={"need_type": need_type}
        )
        response.raise_for_status()
        return response.json()

    def get_statistics(self, user_id):
        """获取统计"""
        response = self.session.get(
            f"{self.base_url}/api/v1/user-equipment/users/{user_id}/statistics"
        )
        response.raise_for_status()
        return response.json()


# 使用示例
if __name__ == "__main__":
    client = FishingAgentClient()

    # 创建用户
    user = client.create_user(
        username="test_user",
        nickname="测试用户",
        user_level="新手"
    )
    user_id = user["data"]["user_id"]
    print(f"创建用户: {user_id}")

    # 添加装备
    client.add_equipment(
        user_id=user_id,
        equipment_id=1,
        purchase_price=680.0,
        notes="第一把路亚竿"
    )
    print("添加装备成功")

    # 查询装备列表
    equipment_list = client.list_equipment(user_id)
    print(f"装备总数: {equipment_list['total']}")

    # 获取推荐
    recommendation = client.get_recommendation(user_id, "complete")
    print(recommendation["recommendation"][:200])

    # 获取统计
    stats = client.get_statistics(user_id)
    print(f"总花费: ¥{stats['total_spent']:.2f}")
```

---

## 爬虫管理 API ⭐ v4.0.0新增

**基础路径**: `/api/v1/admin/crawler`

### 权限要求
- 需要 JWT Token 认证
- 需要 `CRAWLER_READ`、`CRAWLER_EXECUTE`、`CRAWLER_DELETE` 权限

### 1. 查询爬虫任务列表

```http
GET /api/v1/admin/crawler/tasks
```

**查询参数**:
- `page` (int, optional): 页码，默认 1
- `page_size` (int, optional): 每页数量，默认 20
- `task_type` (str, optional): 任务类型过滤 (taobao/jd/forum)
- `status` (str, optional): 状态过滤 (pending/running/success/failed)

**响应示例**:
```json
{
  "items": [
    {
      "id": 1,
      "task_type": "taobao",
      "keywords": ["路亚竿"],
      "status": "success",
      "total_items": 100,
      "success_items": 95,
      "failed_items": 5,
      "start_time": "2025-12-10T10:00:00",
      "end_time": "2025-12-10T10:05:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### 2. 手动触发爬虫任务

```http
POST /api/v1/admin/crawler/tasks/trigger
```

**请求体**:
```json
{
  "task_type": "taobao",
  "keywords": ["路亚竿", "渔轮"],
  "max_pages": 5,
  "proxy": null
}
```

**响应示例**:
```json
{
  "task_id": 123,
  "message": "爬虫任务已启动",
  "status": "pending"
}
```

### 3. 获取任务详情

```http
GET /api/v1/admin/crawler/tasks/{task_id}
```

### 4. 重试失败任务

```http
POST /api/v1/admin/crawler/tasks/{task_id}/retry
```

### 5. 获取任务日志

```http
GET /api/v1/admin/crawler/tasks/{task_id}/logs
```

### 6. 删除任务记录

```http
DELETE /api/v1/admin/crawler/tasks/{task_id}
```

### 7. 获取数据同步状态

```http
GET /api/v1/admin/crawler/sync-status
```

---

## 监控管理 API ⭐ v4.0.0新增

**基础路径**: `/api/v1/admin/monitor`

### 权限要求
- 需要 JWT Token 认证
- 需要 `MONITOR_READ` 权限

### 1. API调用统计

```http
GET /api/v1/admin/monitor/api-stats
```

**查询参数**:
- `start_date` (date, optional): 开始日期
- `end_date` (date, optional): 结束日期

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
    }
  ]
}
```

### 2. LLM使用统计

```http
GET /api/v1/admin/monitor/llm-stats
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
    }
  }
}
```

### 3. 数据库性能监控

```http
GET /api/v1/admin/monitor/db-performance
```

### 4. 系统健康检查

```http
GET /api/v1/admin/monitor/health-check
```

**注意**: 此端点无需认证

---

## WebSocket API ⭐ v4.0.0新增

### 1. 爬虫任务进度推送

```
WS /api/v1/admin/crawler/ws/crawler/{task_id}
```

**推送数据格式**:
```json
{
  "task_id": 1,
  "status": "running",
  "progress": "50/100",
  "success_items": 50,
  "failed_items": 2,
  "timestamp": "2025-12-10T10:30:45.123456"
}
```

### 2. 系统监控实时推送

```
WS /api/v1/admin/monitor/ws/realtime-stats
```

**推送数据格式**:
```json
{
  "timestamp": "2025-12-10T10:30:45.123456",
  "api_calls_per_minute": 25,
  "api_errors_per_minute": 1,
  "llm_calls_per_minute": 5,
  "llm_tokens_per_minute": 1200
}
```

---

## 更新日志

### v4.0.0 (2025-12-10)

**新增功能**:
- 爬虫管理 API（7个端点 + 1个WebSocket）
- 监控管理 API（4个端点 + 1个WebSocket）
- WebSocket 实时通信支持
- 完整的 RBAC 权限控制

**技术升级**:
- API 版本升级至 v4.0.0
- 实时数据推送
- 完善的权限管理

### v3.2.0 (2024-12-03)

**新增功能**:
- 用户装备管理 API（6个端点）
- 用户管理（创建用户、获取用户信息）
- 装备库管理（添加、查询、删除）
- 推荐功能（升级/完善/搭配）
- 统计功能（装备数量、花费、类别分布）

**改进**:
- 对话接口支持 `user_id` 参数
- 完善错误处理和响应格式

### v3.1.1 (2024-11-28)

- 初始版本
- 钓鱼助手对话接口
- 工具列表查询接口

---

## 联系支持

- **项目地址**: https://github.com/anthropics/claude-code
- **问题反馈**: https://github.com/anthropics/claude-code/issues
- **文档**: [README](../README.md)
