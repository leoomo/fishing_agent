# Phase 3 管理模块快速启动指南

## 🚀 快速启动

### 1. 启动 API 服务器

```bash
# 确保环境变量已配置
cp .env.example .env
# 编辑 .env 文件，设置必需的 API 密钥

# 启动服务器
uv run uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 创建管理员用户

```bash
# 创建管理员账户（仅需执行一次）
uv run python scripts/create_admin.py --username admin --password admin123
```

### 3. 访问 API 文档

```bash
# Swagger UI（推荐）
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc
```

## 🔐 获取访问 Token

### 方式一：使用 Swagger UI
1. 打开 http://localhost:8000/docs
2. 找到 `POST /api/v1/auth/login` 端点
3. 点击 "Try it out"
4. 输入用户名和密码
5. 执行请求，复制返回的 `access_token`
6. 点击页面右上角的 "Authorize" 按钮
7. 输入 `Bearer {your_token}`
8. 现在可以测试所有需要认证的端点了

### 方式二：使用 curl

```bash
# 登录获取 token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 响应示例
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_info": {
    "user_id": 1,
    "username": "admin",
    "role": "admin"
  }
}

# 使用 token 访问受保护端点
export TOKEN="your_access_token_here"

curl -X GET "http://localhost:8000/api/v1/admin/equipment" \
  -H "Authorization: Bearer $TOKEN"
```

## 📦 API 端点快速参考

### 装备管理

```bash
# 创建装备
curl -X POST "http://localhost:8000/api/v1/admin/equipment" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "达瓦月下美人76ML",
    "category": "鱼竿",
    "brand_id": 1,
    "model": "76ML",
    "price_min": 899,
    "price_max": 999,
    "user_level": "进阶",
    "specs": {
      "length": 2.28,
      "power": "ML",
      "action": "Fast",
      "lure_weight_min": 3,
      "lure_weight_max": 12
    }
  }'

# 查询装备列表
curl -X GET "http://localhost:8000/api/v1/admin/equipment?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# 查询特定类别
curl -X GET "http://localhost:8000/api/v1/admin/equipment?category=鱼竿" \
  -H "Authorization: Bearer $TOKEN"

# 关键词搜索
curl -X GET "http://localhost:8000/api/v1/admin/equipment?keyword=达瓦" \
  -H "Authorization: Bearer $TOKEN"

# 获取装备详情
curl -X GET "http://localhost:8000/api/v1/admin/equipment/1" \
  -H "Authorization: Bearer $TOKEN"

# 更新装备
curl -X PUT "http://localhost:8000/api/v1/admin/equipment/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_min": 799,
    "price_max": 899,
    "description": "限时促销"
  }'

# 删除装备（软删除）
curl -X DELETE "http://localhost:8000/api/v1/admin/equipment/1" \
  -H "Authorization: Bearer $TOKEN"
```

### 品牌管理

```bash
# 创建品牌
curl -X POST "http://localhost:8000/api/v1/admin/brands" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name_cn": "达瓦",
    "name_en": "DAIWA",
    "country": "日本",
    "description": "世界知名钓具品牌"
  }'

# 查询品牌列表
curl -X GET "http://localhost:8000/api/v1/admin/brands" \
  -H "Authorization: Bearer $TOKEN"

# 查询品牌（含装备数量）
curl -X GET "http://localhost:8000/api/v1/admin/brands?with_equipment_count=true" \
  -H "Authorization: Bearer $TOKEN"
```

### 用户管理

```bash
# 查询用户列表
curl -X GET "http://localhost:8000/api/v1/admin/users?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# 获取用户详情
curl -X GET "http://localhost:8000/api/v1/admin/users/1" \
  -H "Authorization: Bearer $TOKEN"

# 获取用户装备库
curl -X GET "http://localhost:8000/api/v1/admin/users/1/equipment" \
  -H "Authorization: Bearer $TOKEN"

# 获取用户钓鱼记录
curl -X GET "http://localhost:8000/api/v1/admin/users/1/fishing-logs" \
  -H "Authorization: Bearer $TOKEN"
```

### 导入导出

```bash
# 导出装备为 CSV
curl -X GET "http://localhost:8000/api/v1/admin/import-export/export/csv?category=鱼竿" \
  -H "Authorization: Bearer $TOKEN" \
  -o equipment_export.csv

# 导出装备为 JSON（含完整规格）
curl -X GET "http://localhost:8000/api/v1/admin/import-export/export/json?category=鱼竿" \
  -H "Authorization: Bearer $TOKEN" \
  -o equipment_export.json

# 导入 CSV 文件
curl -X POST "http://localhost:8000/api/v1/admin/import-export/import/csv" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@equipment.csv"

# 导入 JSON 文件
curl -X POST "http://localhost:8000/api/v1/admin/import-export/import/json" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@equipment.json"
```

## 🧪 运行测试

```bash
# 运行集成测试（需要先创建 admin 用户）
uv run pytest tests/api/test_equipment_admin.py -v

# 运行特定测试
uv run pytest tests/api/test_equipment_admin.py::test_create_equipment -v
```

## 📊 查看所有端点

```bash
# 使用自带工具列出所有端点
uv run python list_endpoints.py
```

## 🛠️ 工具脚本

### 创建管理员用户
```bash
uv run python scripts/create_admin.py
```

### 列出所有 API 端点
```bash
uv run python list_endpoints.py
```

## 📝 CSV 导入格式示例

创建 `equipment.csv` 文件：

```csv
name,category,brand_name,model,price_min,price_max,description,user_level
达瓦月下美人76ML,鱼竿,达瓦,76ML,899,999,经典路亚竿,进阶
禧玛诺毒牙264ML,鱼竿,禧玛诺,264ML,699,799,性价比之选,新手
```

## 📝 JSON 导入格式示例

创建 `equipment.json` 文件：

```json
[
  {
    "name": "达瓦月下美人76ML",
    "category": "鱼竿",
    "brand_name": "达瓦",
    "model": "76ML",
    "price_min": 899,
    "price_max": 999,
    "description": "经典路亚竿",
    "user_level": "进阶",
    "specs": {
      "length": 2.28,
      "power": "ML",
      "action": "Fast",
      "lure_weight_min": 3,
      "lure_weight_max": 12
    }
  }
]
```

## 🔍 常见问题

### 1. 401 Unauthorized
**问题**: 请求返回 401 错误
**解决**: 检查 token 是否正确，是否已过期（默认60分钟）

### 2. 403 Forbidden
**问题**: 请求返回 403 错误
**解决**: 检查当前用户是否有对应的权限

### 3. 品牌不存在
**问题**: 创建装备时提示品牌不存在
**解决**: 先创建品牌，或使用已存在的 `brand_id`

### 4. 导入失败
**问题**: CSV/JSON 导入返回错误
**解决**: 检查文件格式和必需字段（name, category, brand_name）

## 📚 更多资源

- **API 文档**: http://localhost:8000/docs
- **开发计划**: docs/dev-plans/phase3-core-api.md
- **完成总结**: PHASE3_WEEK4_SUMMARY.md
- **认证文档**: apps/api/auth/README.md

---

**开发完成日期**: 2025-12-10
**当前版本**: v3.1.1
