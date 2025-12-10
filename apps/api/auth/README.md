# 认证系统使用指南

Phase 2 后端认证与中间件系统完整实现。

## 快速开始

### 1. 运行数据库迁移

```bash
uv run python -c "from packages.agent_fishing.tools.lure.migrations import run_migrations; run_migrations()"
```

### 2. 创建管理员用户

**交互模式（推荐）：**
```bash
uv run python scripts/create_admin.py --interactive
```

**命令行模式：**
```bash
uv run python scripts/create_admin.py \
  --username admin \
  --email admin@example.com \
  --role admin \
  --full-name "System Administrator"
```

### 3. 启动API服务器

```bash
uv run uvicorn apps.api.main:app --reload
```

## API端点

### 登录
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}

# 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "full_name": "System Administrator",
    "is_active": true
  },
  "permissions": ["equipment:create", "equipment:read", ...]
}
```

### 获取个人资料
```bash
GET /api/v1/auth/profile
Authorization: Bearer <your_token>

# 响应
{
  "user": { ... },
  "permissions": [...]
}
```

### 登出
```bash
POST /api/v1/auth/logout
Authorization: Bearer <your_token>
```

## 在代码中使用认证

### 保护路由 - 需要登录

```python
from fastapi import APIRouter, Depends
from apps.api.auth.dependencies import get_current_user, CurrentUser

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: CurrentUser = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}"}
```

### 保护路由 - 需要特定权限

```python
from apps.api.auth.dependencies import require_permission
from apps.api.auth.permissions import PermissionEnum

@router.post(
    "/equipment",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def create_equipment(...):
    # 只有具有 EQUIPMENT_CREATE 权限的用户可以访问
    pass
```

### 保护路由 - 仅管理员

```python
from apps.api.auth.dependencies import require_admin

@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_admin())]
)
async def delete_user(user_id: int):
    # 只有管理员可以访问
    pass
```

### 可选认证

```python
from apps.api.auth.dependencies import get_current_user_optional

@router.get("/public")
async def public_endpoint(
    current_user: Optional[CurrentUser] = Depends(get_current_user_optional)
):
    if current_user:
        return {"message": f"Hello {current_user.username}"}
    return {"message": "Hello guest"}
```

## 角色和权限

### 角色

1. **admin** - 完全访问权限
   - 所有27个权限
   - 可以管理用户、配置、执行所有操作

2. **editor** - 内容编辑权限
   - 可以创建、读取、更新内容
   - 不能删除或管理用户
   - 不能修改系统配置

3. **readonly** - 只读权限
   - 仅可读取所有模块
   - 不能进行任何修改操作

### 权限列表

```python
# 装备管理
EQUIPMENT_CREATE = "equipment:create"
EQUIPMENT_READ = "equipment:read"
EQUIPMENT_UPDATE = "equipment:update"
EQUIPMENT_DELETE = "equipment:delete"

# 品牌管理
BRAND_CREATE = "brand:create"
BRAND_READ = "brand:read"
BRAND_UPDATE = "brand:update"
BRAND_DELETE = "brand:delete"

# 用户管理
USER_READ = "user:read"
USER_UPDATE = "user:update"
USER_MANAGE = "user:manage"

# 内容管理
CONTENT_CREATE = "content:create"
CONTENT_READ = "content:read"
CONTENT_UPDATE = "content:update"
CONTENT_DELETE = "content:delete"

# 爬虫管理
CRAWLER_READ = "crawler:read"
CRAWLER_EXECUTE = "crawler:execute"
CRAWLER_DELETE = "crawler:delete"

# 系统监控
MONITOR_READ = "monitor:read"

# 数据分析
ANALYTICS_READ = "analytics:read"

# 配置管理
CONFIG_READ = "config:read"
CONFIG_UPDATE = "config:update"
CONFIG_CREATE = "config:create"
CONFIG_DELETE = "config:delete"
CONFIG_TEST = "config:test"

# 导入导出
DATA_IMPORT = "data:import"
DATA_EXPORT = "data:export"
```

## 安全特性

- ✅ Bcrypt密码哈希（带盐值）
- ✅ JWT令牌认证（30分钟过期）
- ✅ 基于角色的访问控制（RBAC）
- ✅ 密码强度验证（最少6个字符）
- ✅ 用户名/邮箱唯一性校验
- ✅ 禁用用户阻止登录
- ✅ API请求日志记录
- ✅ 自动登录时间跟踪

## 测试

运行所有认证测试：

```bash
uv run pytest tests/test_auth/ -v
```

测试覆盖：
- ✅ 6个JWT测试（令牌创建、过期、密码哈希）
- ✅ 9个登录路由测试（成功、错误、验证）
- ✅ 11个权限测试（角色、权限、依赖）
- ✅ 9个集成测试（完整流程、数据库迁移）

**总计：35个测试全部通过** ✅

## 环境变量

在 `.env` 文件中配置：

```bash
# JWT密钥（生产环境必须修改！）
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# JWT过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 故障排除

### 令牌验证失败

- 检查JWT_SECRET_KEY是否正确
- 检查令牌是否过期
- 确保Bearer令牌格式正确：`Authorization: Bearer <token>`

### 权限被拒绝

- 验证用户角色是否有所需权限
- 使用 `/api/v1/auth/profile` 查看当前用户权限

### 数据库错误

- 运行数据库迁移：`uv run python -c "from packages.agent_fishing.tools.lure.migrations import run_migrations; run_migrations()"`
- 检查数据库文件权限

## 文件结构

```
apps/api/auth/
├── jwt.py              # JWT令牌生成和验证
├── permissions.py      # 角色和权限定义
├── dependencies.py     # FastAPI认证依赖
└── README.md          # 本文档

apps/api/routes/
└── auth.py            # 认证路由（登录、登出、个人资料）

apps/api/middleware/
├── __init__.py
└── api_logger.py      # API日志中间件

packages/agent_fishing/tools/lure/orm/repositories/
└── admin_user_repo.py # 管理员用户仓库

packages/agent_fishing/tools/lure/models/
├── admin_user.py      # 管理员用户模型
└── system.py          # 系统模型（配置、日志、报告）

scripts/
└── create_admin.py    # 创建管理员用户脚本

tests/test_auth/
├── test_jwt.py        # JWT测试
├── test_permissions.py # 权限测试
├── test_login_routes.py # 登录路由测试
└── test_integration.py  # 集成测试
```
