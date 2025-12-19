# API 参考文档 v5.0.2

智能钓鱼助手 REST API 完整参考指南

## 📋 目录

1. [基础信息](#1-基础信息)
2. [认证方式](#2-认证方式)
3. [核心API](#3-核心api)
4. [认证API](#4-认证api)
5. [微信小程序API](#5-微信小程序api)
6. [装备管理API](#6-装备管理api)
7. [图片处理API](#7-图片处理api)
8. [导入导出API](#8-导入导出api)
9. [管理后台API](#9-管理后台api)
10. [错误处理](#10-错误处理)

## 1. 基础信息

- **Base URL**: `http://localhost:8000`
- **API版本**: `v1`
- **数据格式**: `JSON`
- **认证方式**: JWT Token + 微信小程序登录
- **当前版本**: v5.0.2

## 2. 认证方式

### JWT Token认证
```bash
# 获取Token
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123"
}

# 请求头使用
Authorization: Bearer <your_jwt_token>
```

### 微信小程序认证
```bash
# 微信code登录
POST /api/v1/auth/wechat/login
{
  "code": "wx_code_from_miniprogram"
}
```

### 权限级别
- **管理员**: 全部API访问权限
- **编辑**: 装备管理相关API
- **只读**: 查询类API
- **微信用户**: 默认只读权限

## 3. 核心API

### 3.1 健康检查
```http
GET /health
```

**响应**:
```json
{
  "status": "ok",
  "version": "5.0.2",
  "features": ["jwt_auth", "wechat_login", "equipment_import", "ocr_processing"]
}
```

### 3.2 智能对话
```http
POST /api/v1/fishing/chat
```

**请求**:
```json
{
  "query": "明天杭州钓鱼怎么样？",
  "model_provider": "zhipu",
  "user_id": 1,
  "location": "杭州",
  "date": "2024-12-12"
}
```

**响应**:
```json
{
  "response": "根据天气分析，明天杭州白天钓鱼条件较好...",
  "model_used": "zhipu",
  "timestamp": "2024-12-11T12:00:00Z",
  "recommendations": [
    {
      "time": "早上6-9点",
      "score": 8.5,
      "reason": "温度适宜，风力小"
    }
  ]
}
```

### 3.3 工具列表
```http
GET /api/v1/fishing/tools
```

**响应**:
```json
{
  "tools": [
    {"name": "get_current_time", "type": "basic"},
    {"name": "get_weather", "type": "weather"},
    {"name": "query_fishing_recommendation", "type": "fishing"},
    {"name": "extract_equipment_info", "type": "equipment"}
  ],
  "total": 4
}
```

## 4. 认证API

### 4.1 用户登录
```http
POST /api/v1/auth/login
```

### 4.2 获取用户信息
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### 4.3 用户登出
```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

### 4.4 刷新Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <token>
```

## 5. 微信小程序API

### 5.1 微信登录
```http
POST /api/v1/auth/wechat/login
```

**请求**:
```json
{
  "code": "wx_code_from_miniprogram"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": 12,
    "openid": "ox1234567890abcdef",
    "nickname": "钓鱼爱好者",
    "role": "readonly"
  },
  "is_new_user": false
}
```

### 5.2 绑定微信账号
```http
POST /api/v1/auth/wechat/bind
Authorization: Bearer <token>
```

### 5.3 解绑微信账号
```http
POST /api/v1/auth/wechat/unbind
Authorization: Bearer <token>
```

## 6. 装备管理API

### 6.1 装备导入提取
```http
POST /api/v1/equipment/import/extract
Authorization: Bearer <token>
```

**请求**:
```json
{
  "text": "光威赤刃 GT602L-M 路亚竿，碳纤维材质，价格¥299",
  "source_type": "forum",
  "source_url": "https://example.com/forum/post/123",
  "enable_compression": true
}
```

**响应**:
```json
{
  "success": true,
  "extracted_count": 1,
  "results": [
    {
      "brand": "光威",
      "model": "赤刃 GT602L-M",
      "category": "路亚竿",
      "price": 299,
      "specs": {
        "material": "碳纤维",
        "length": "2.4m",
        "action": "L"
      }
    }
  ]
}
```

### 6.2 批量提取装备
```http
POST /api/v1/equipment/import/batch-extract
Authorization: Bearer <token>
```

### 6.3 待审核装备列表
```http
GET /api/v1/equipment/pending?page=1&page_size=20&source_type=forum
Authorization: Bearer <token>
```

**查询参数**:
- `source_type`: forum, ecommerce, official
- `status`: pending, approved, rejected
- `date_from`: 开始日期
- `date_to`: 结束日期

### 6.4 审核装备信息
```http
POST /api/v1/equipment/pending/{pending_id}/review
Authorization: Bearer <token>
```

**请求**:
```json
{
  "action": "approve",
  "review_notes": "信息准确，批准入库",
  "equipment_data": {
    "brand_id": 1,
    "category": "路亚竿",
    "model_name": "赤刃 GT602L-M",
    "price": 299
  }
}
```

## 7. 图片处理API

### 7.1 OCR表格识别 ⭐v5.0.2
```http
POST /api/v1/ocr/recognize-table
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**参数**:
- `files`: 图片文件列表（支持多张自动合并）
- `image_url`: 图片URL（与files二选一）

**支持格式**: PNG, JPG, JPEG, WebP
**最大文件大小**:
- Ollama: 20MB
- SiliconFlow: 10MB

**响应**:
```json
{
  "success": true,
  "markdown": "| 品牌 | 型号 | 价格 |\n|------|------|------|\n| 达亿瓦 | 1000 | ¥299 |",
  "metadata": {
    "provider": "ollama",
    "model": "deepseek-ocr",
    "processing_time_ms": 1500,
    "images_merged": 2
  }
}
```

### 7.2 OCR服务状态
```http
GET /api/v1/ocr/status
Authorization: Bearer <token>
```

**响应**:
```json
{
  "service": "ocr",
  "provider": "ollama",
  "model": "deepseek-ocr",
  "available": true,
  "supported_formats": ["png", "jpg", "jpeg", "webp"],
  "max_size_mb": 20
}
```

### 7.3 批量图片合并（CLI）
```bash
uv run python -m packages.data_processing.image.batch_merge_processor <source_directory> \
  --output-dir ./merged \
  --quality 98 \
  --parallel-detection
```

## 8. 导入导出API

### 8.1 CSV导入装备
```http
POST /api/v1/equipment/import/csv
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**CSV格式**:
```csv
品牌,型号,类别,价格,描述,规格
光威,赤刃 GT602L-M,路亚竿,299,高性能碳纤维路亚竿,"材质:碳纤维;长度:2.4m"
```

### 8.2 JSON导入装备
```http
POST /api/v1/equipment/import/json
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

### 8.3 CSV导出装备
```http
GET /api/v1/equipment/export/csv?category=路亚竿&brand=光威&limit=1000
Authorization: Bearer <token>
```

### 8.4 JSON导出装备
```http
GET /api/v1/equipment/export/json?include_specs=true&limit=1000
Authorization: Bearer <token>
```

## 9. 管理后台API

### 9.1 装备管理

#### 装备列表
```http
GET /api/v1/admin/equipment/list?page=1&page_size=20&category=路亚竿&brand=光威
Authorization: Bearer <token>
```

#### 创建装备
```http
POST /api/v1/admin/equipment
Authorization: Bearer <token>
```

**请求**:
```json
{
  "brand_id": 1,
  "category": "路亚竿",
  "model_name": "赤刃 GT602L-M",
  "price": 299.99,
  "specs": {
    "material": "碳纤维",
    "length": "2.4m",
    "weight": "120g"
  },
  "is_active": true
}
```

#### 批量操作
```http
POST /api/v1/admin/equipment/batch
Authorization: Bearer <token>
```

### 9.2 用户装备管理

#### 创建用户档案
```http
POST /api/v1/user-equipment/users
Authorization: Bearer <token>
```

#### 添加装备到用户库
```http
POST /api/v1/user-equipment/users/{user_id}/equipment
Authorization: Bearer <token>
```

#### 查询用户装备
```http
GET /api/v1/user-equipment/users/{user_id}/equipment?page=1&page_size=20
Authorization: Bearer <token>
```

#### 装备推荐
```http
POST /api/v1/user-equipment/users/{user_id}/recommend
Authorization: Bearer <token>
```

### 9.3 数据分析

#### 装备统计
```http
GET /api/v1/admin/analytics/equipment/stats
Authorization: Bearer <token>
```

**响应**:
```json
{
  "total_equipment": 1500,
  "category_distribution": {
    "鱼竿": 600,
    "渔轮": 400,
    "拟饵": 350
  },
  "price_ranges": {
    "0-200": 400,
    "200-500": 600,
    "500-1000": 350
  }
}
```

#### 趋势分析
```http
GET /api/v1/admin/analytics/equipment/trends?months=12
Authorization: Bearer <token>
```

### 9.4 配置管理

#### 查询配置
```http
GET /api/v1/admin/config/configs?type=api
Authorization: Bearer <token>
```

#### 创建配置
```http
POST /api/v1/admin/config/configs
Authorization: Bearer <token>
```

#### 测试API密钥
```http
POST /api/v1/admin/config/configs/test-api-key
Authorization: Bearer <token>
```

### 9.5 用户管理

#### 用户列表
```http
GET /api/v1/admin/users?page=1&page_size=20&role=admin
Authorization: Bearer <token>
```

#### 创建用户
```http
POST /api/v1/admin/users
Authorization: Bearer <token>
```

#### 权限管理
```http
PUT /api/v1/admin/users/{user_id}/permissions
Authorization: Bearer <token>
```

### 9.6 监控管理

#### API统计
```http
GET /api/v1/admin/monitor/api-stats
Authorization: Bearer <token>
```

#### LLM统计
```http
GET /api/v1/admin/monitor/llm-stats
Authorization: Bearer <token>
```

#### 系统健康检查
```http
GET /api/v1/admin/monitor/health-check
Authorization: Bearer <token>
```

### 9.7 爬虫管理

#### 任务列表
```http
GET /api/v1/admin/crawler/tasks?page=1&page_size=10
Authorization: Bearer <token>
```

#### 触发爬虫
```http
POST /api/v1/admin/crawler/tasks/trigger
Authorization: Bearer <token>
```

#### 同步状态
```http
GET /api/v1/admin/crawler/sync-status
Authorization: Bearer <token>
```

### 9.8 工作流管理

#### 创建工作流模板
```http
POST /api/v1/admin/crawler/workflows/templates
Authorization: Bearer <token>
```

#### 执行工作流
```http
POST /api/v1/admin/crawler/workflows/execute
Authorization: Bearer <token>
```

## 10. 错误处理

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
| 401 | UNAUTHORIZED | 未认证或Token无效 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMITED | 请求频率超限 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

### 速率限制
- **未认证**: 100请求/小时
- **只读用户**: 500请求/小时
- **编辑用户**: 1000请求/小时
- **管理员**: 无限制

## SDK示例

### Python
```python
import requests

# 登录
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'admin', 'password': 'admin123'
})
token = response.json()['access_token']

# 调用API
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/admin/analytics/equipment/stats',
    headers=headers
)
```

### JavaScript
```javascript
// 登录
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'admin', password: 'admin123'})
});
const {access_token} = await response.json();

// 调用API
const data = await fetch('http://localhost:8000/api/v1/admin/analytics/equipment/stats', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  }
});
```

### 微信小程序
```javascript
// 微信登录
wx.login({
  success: async (res) => {
    const response = await wx.request({
      url: 'http://localhost:8000/api/v1/auth/wechat/login',
      method: 'POST',
      data: { code: res.code }
    });

    wx.setStorageSync('access_token', response.data.access_token);
  }
});

// API调用
const token = wx.getStorageSync('access_token');
wx.request({
  url: 'http://localhost:8000/api/v1/equipment/pending',
  method: 'GET',
  header: {'Authorization': `Bearer ${token}`},
  success: (res) => console.log(res.data)
});
```

---

**版本**: v5.0.2
**更新**: 2024-12-20
**维护**: 智能钓鱼助手开发团队

**相关文档**:
- [快速入门](./GETTING_STARTED.md)
- [用户指南](./USER_GUIDE.md)
- [架构文档](./ARCHITECTURE.md)