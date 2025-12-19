# Phase 2: 认证授权 + 中间件开发详细方案

**目标**: 实现 JWT 认证和角色权限系统 + API/LLM 日志中间件
**周期**: 第 3 周（5 个工作日）
**优先级**: P0（核心基础）

---

## 目标概述

构建完整的认证授权体系和监控中间件，为管理后台提供安全保障和数据洞察。

**核心功能**:
- JWT token 生成和验证
- 基于角色的权限控制（Admin/Editor/ReadOnly）
- API 调用日志记录中间件
- LLM 调用监控集成
- 首个 admin 用户创建工具

---

## 开发步骤

### Step 1: 实现 JWT 认证（Day 1-2）

#### 1.1 创建 JWT 工具模块

**文件**: `apps/api/auth/jwt.py`

**步骤**:
1. 安装依赖（已在 pyproject.toml 中）:
   ```toml
   python-jose[cryptography] = "^3.3.0"
   passlib[bcrypt] = "^1.7.4"
   ```

2. 实现 JWT token 生成和验证:

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    生成 JWT access token

    Args:
        data: token payload（通常包含 user_id, username, role）
        expires_delta: 过期时间增量（默认30分钟）

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    验证并解码 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        dict: token payload

    Raises:
        JWTError: token 无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Token 验证失败: {str(e)}")


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)
```

3. 创建测试文件:

**文件**: `tests/test_jwt.py`

```python
import pytest
from datetime import timedelta
from apps.api.auth.jwt import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)


def test_create_and_verify_token():
    """测试 token 创建和验证"""
    payload = {"user_id": 1, "username": "admin", "role": "admin"}
    token = create_access_token(payload)

    # 验证 token
    decoded = verify_token(token)

    assert decoded["user_id"] == 1
    assert decoded["username"] == "admin"
    assert decoded["role"] == "admin"
    assert "exp" in decoded  # 包含过期时间


def test_token_expiration():
    """测试 token 过期"""
    payload = {"user_id": 1}

    # 创建1秒后过期的 token
    token = create_access_token(payload, expires_delta=timedelta(seconds=1))

    # 立即验证应该成功
    decoded = verify_token(token)
    assert decoded["user_id"] == 1

    # 等待2秒后验证应该失败
    import time
    time.sleep(2)

    with pytest.raises(ValueError, match="Token 验证失败"):
        verify_token(token)


def test_password_hashing():
    """测试密码哈希"""
    password = "test_password_123"

    # 生成哈希
    hashed = get_password_hash(password)

    # 哈希值应该不同于原密码
    assert hashed != password

    # 验证正确密码
    assert verify_password(password, hashed) is True

    # 验证错误密码
    assert verify_password("wrong_password", hashed) is False


def test_bcrypt_salt():
    """测试 bcrypt salt（每次哈希结果不同）"""
    password = "same_password"

    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # 两次哈希结果应该不同（因为 salt 不同）
    assert hash1 != hash2

    # 但都能验证成功
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
```

#### 1.2 实现登录端点

**文件**: `apps/api/routes/auth.py`

**步骤**:
1. 创建登录 Schema:

```python
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="JWT token")
    token_type: str = Field(default="bearer", description="Token 类型")
    user_info: dict = Field(..., description="用户信息")
```

2. 实现登录路由:

```python
from fastapi import APIRouter, HTTPException, status
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.admin_user_repo import AdminUserRepository
from apps.api.auth.jwt import create_access_token, verify_password
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    用户登录

    Args:
        credentials: 登录凭据（用户名 + 密码）

    Returns:
        LoginResponse: 包含 JWT token 和用户信息

    Raises:
        HTTPException: 用户名或密码错误
    """
    with get_db_session() as session:
        repo = AdminUserRepository(session)

        # 查询用户
        admin_user = repo.get_by_username(credentials.username)

        if not admin_user:
            logger.warning(f"登录失败: 用户不存在 - {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 验证密码
        if not verify_password(credentials.password, admin_user.password_hash):
            logger.warning(f"登录失败: 密码错误 - {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 检查用户状态
        if not admin_user.is_active:
            logger.warning(f"登录失败: 用户已禁用 - {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用"
            )

        # 生成 JWT token
        token_payload = {
            "user_id": admin_user.id,
            "username": admin_user.username,
            "role": admin_user.role
        }
        access_token = create_access_token(token_payload)

        # 更新最后登录时间
        repo.update_last_login(admin_user.id)

        logger.info(f"登录成功: {credentials.username} (role={admin_user.role})")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_info={
                "user_id": admin_user.id,
                "username": admin_user.username,
                "role": admin_user.role,
                "email": admin_user.email
            }
        )
```

3. 测试登录端点:

```bash
# 运行服务器
uv run uvicorn apps.api.main:app --reload

# 测试登录（使用 curl）
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 预期响应:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "user_info": {
#     "user_id": 1,
#     "username": "admin",
#     "role": "admin",
#     "email": "admin@example.com"
#   }
# }
```

---

### Step 2: 实现权限系统（Day 2-3）

#### 2.1 定义权限枚举

**文件**: `apps/api/auth/permissions.py`

**步骤**:
1. 定义角色和权限:

```python
from enum import Enum
from typing import List, Set


class RoleEnum(str, Enum):
    """用户角色"""
    ADMIN = "admin"          # 管理员：所有权限
    EDITOR = "editor"        # 编辑：创建、读取、更新
    READONLY = "readonly"    # 只读：仅读取


class PermissionEnum(str, Enum):
    """权限枚举"""
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
    USER_MANAGE = "user:manage"  # 禁用/启用用户

    # 内容管理（鱼类、钓组、拟饵）
    CONTENT_CREATE = "content:create"
    CONTENT_READ = "content:read"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"

    # 爬虫管理
    CRAWLER_READ = "crawler:read"
    CRAWLER_EXECUTE = "crawler:execute"  # 触发任务
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
    CONFIG_TEST = "config:test"  # 测试 API 密钥

    # 导入导出
    DATA_IMPORT = "data:import"
    DATA_EXPORT = "data:export"


# 角色权限映射
ROLE_PERMISSIONS: dict[RoleEnum, Set[PermissionEnum]] = {
    RoleEnum.ADMIN: {
        # Admin 拥有所有权限
        perm for perm in PermissionEnum
    },

    RoleEnum.EDITOR: {
        # 装备和品牌：创建、读取、更新
        PermissionEnum.EQUIPMENT_CREATE,
        PermissionEnum.EQUIPMENT_READ,
        PermissionEnum.EQUIPMENT_UPDATE,
        PermissionEnum.BRAND_CREATE,
        PermissionEnum.BRAND_READ,
        PermissionEnum.BRAND_UPDATE,

        # 用户：只读
        PermissionEnum.USER_READ,

        # 内容：创建、读取、更新
        PermissionEnum.CONTENT_CREATE,
        PermissionEnum.CONTENT_READ,
        PermissionEnum.CONTENT_UPDATE,

        # 爬虫：只读
        PermissionEnum.CRAWLER_READ,

        # 监控和分析：只读
        PermissionEnum.MONITOR_READ,
        PermissionEnum.ANALYTICS_READ,

        # 配置：只读
        PermissionEnum.CONFIG_READ,

        # 导出数据
        PermissionEnum.DATA_EXPORT,
    },

    RoleEnum.READONLY: {
        # 所有模块：只读
        PermissionEnum.EQUIPMENT_READ,
        PermissionEnum.BRAND_READ,
        PermissionEnum.USER_READ,
        PermissionEnum.CONTENT_READ,
        PermissionEnum.CRAWLER_READ,
        PermissionEnum.MONITOR_READ,
        PermissionEnum.ANALYTICS_READ,
        PermissionEnum.CONFIG_READ,
    }
}


def has_permission(role: RoleEnum, permission: PermissionEnum) -> bool:
    """
    检查角色是否拥有指定权限

    Args:
        role: 用户角色
        permission: 权限

    Returns:
        bool: 是否拥有权限
    """
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_role_permissions(role: RoleEnum) -> List[str]:
    """
    获取角色的所有权限列表

    Args:
        role: 用户角色

    Returns:
        List[str]: 权限列表
    """
    return [perm.value for perm in ROLE_PERMISSIONS.get(role, set())]
```

2. 测试权限系统:

**文件**: `tests/test_permissions.py`

```python
import pytest
from apps.api.auth.permissions import (
    RoleEnum,
    PermissionEnum,
    has_permission,
    get_role_permissions,
    ROLE_PERMISSIONS
)


def test_admin_has_all_permissions():
    """测试 Admin 拥有所有权限"""
    admin_permissions = ROLE_PERMISSIONS[RoleEnum.ADMIN]
    all_permissions = set(PermissionEnum)

    assert admin_permissions == all_permissions


def test_editor_permissions():
    """测试 Editor 权限"""
    # Editor 可以创建装备
    assert has_permission(RoleEnum.EDITOR, PermissionEnum.EQUIPMENT_CREATE) is True

    # Editor 不能删除装备
    assert has_permission(RoleEnum.EDITOR, PermissionEnum.EQUIPMENT_DELETE) is False

    # Editor 可以导出数据
    assert has_permission(RoleEnum.EDITOR, PermissionEnum.DATA_EXPORT) is True

    # Editor 不能导入数据
    assert has_permission(RoleEnum.EDITOR, PermissionEnum.DATA_IMPORT) is False


def test_readonly_permissions():
    """测试 ReadOnly 权限"""
    # ReadOnly 可以读取装备
    assert has_permission(RoleEnum.READONLY, PermissionEnum.EQUIPMENT_READ) is True

    # ReadOnly 不能创建装备
    assert has_permission(RoleEnum.READONLY, PermissionEnum.EQUIPMENT_CREATE) is False

    # ReadOnly 不能更新配置
    assert has_permission(RoleEnum.READONLY, PermissionEnum.CONFIG_UPDATE) is False


def test_get_role_permissions():
    """测试获取角色权限列表"""
    admin_perms = get_role_permissions(RoleEnum.ADMIN)

    # Admin 应该有所有权限
    assert len(admin_perms) == len(PermissionEnum)
    assert "equipment:create" in admin_perms

    readonly_perms = get_role_permissions(RoleEnum.READONLY)

    # ReadOnly 应该只有读取权限
    assert all(":read" in perm for perm in readonly_perms)
```

#### 2.2 实现 FastAPI 权限依赖

**文件**: `apps/api/auth/dependencies.py`

**步骤**:
1. 实现权限检查依赖:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from apps.api.auth.jwt import verify_token
from apps.api.auth.permissions import RoleEnum, PermissionEnum, has_permission
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


class CurrentUser:
    """当前用户信息"""
    def __init__(self, user_id: int, username: str, role: RoleEnum):
        self.user_id = user_id
        self.username = username
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    从 JWT token 提取当前用户信息

    Args:
        credentials: HTTP Authorization header

    Returns:
        CurrentUser: 当前用户

    Raises:
        HTTPException: token 无效或过期
    """
    token = credentials.credentials

    try:
        # 验证 token
        payload = verify_token(token)

        # 提取用户信息
        user_id = payload.get("user_id")
        username = payload.get("username")
        role_str = payload.get("role")

        if not all([user_id, username, role_str]):
            raise ValueError("Token payload 缺少必需字段")

        # 验证角色
        try:
            role = RoleEnum(role_str)
        except ValueError:
            raise ValueError(f"无效的角色: {role_str}")

        return CurrentUser(user_id=user_id, username=username, role=role)

    except ValueError as e:
        logger.warning(f"Token 验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"身份验证失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: PermissionEnum):
    """
    权限检查装饰器工厂

    Args:
        permission: 需要的权限

    Returns:
        Callable: FastAPI 依赖函数

    Usage:
        @router.post("/equipment", dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))])
        async def create_equipment(...):
            ...
    """
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ):
        if not has_permission(current_user.role, permission):
            logger.warning(
                f"权限拒绝: user={current_user.username}, "
                f"role={current_user.role}, "
                f"required_permission={permission.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足: 需要 {permission.value}"
            )

        return current_user

    return permission_checker


def require_admin():
    """要求 Admin 角色"""
    async def admin_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ):
        if current_user.role != RoleEnum.ADMIN:
            logger.warning(
                f"Admin 权限拒绝: user={current_user.username}, role={current_user.role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )

        return current_user

    return admin_checker
```

2. 在路由中使用权限依赖:

**示例**: `apps/api/routes/equipment_admin.py`

```python
from fastapi import APIRouter, Depends
from apps.api.auth.dependencies import require_permission, CurrentUser
from apps.api.auth.permissions import PermissionEnum

router = APIRouter()


@router.post(
    "/equipment",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))]
)
async def create_equipment(
    equipment_data: EquipmentCreate,
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))
):
    """
    创建装备（需要 equipment:create 权限）
    """
    # current_user 包含用户信息
    logger.info(f"用户 {current_user.username} 创建装备: {equipment_data.name}")

    # ... 业务逻辑


@router.get(
    "/equipment",
    dependencies=[Depends(require_permission(PermissionEnum.EQUIPMENT_READ))]
)
async def list_equipment():
    """
    查询装备列表（需要 equipment:read 权限）
    """
    # ...
```

---

### Step 3: 实现 API 日志中间件（Day 4）

#### 3.1 创建日志中间件

**文件**: `apps/api/middleware/logging.py`

**步骤**:
1. 实现 API 日志中间件:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import logging
from typing import Callable
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import APILog

logger = logging.getLogger(__name__)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    API 调用日志中间件

    功能:
    - 记录所有 API 调用
    - 记录响应时间
    - 记录错误信息
    - 提取用户信息（如果有）
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # 记录请求开始时间
        start_time = time.time()

        # 提取请求信息
        endpoint = request.url.path
        method = request.method
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # 提取用户信息（如果 token 存在）
        user_id = None
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from apps.api.auth.jwt import verify_token
                token = auth_header.split(" ")[1]
                payload = verify_token(token)
                user_id = payload.get("user_id")
        except Exception:
            pass  # token 解析失败，user_id 保持 None

        # 执行请求
        error_message = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(f"请求处理异常: {endpoint} - {str(e)}", exc_info=True)
            status_code = 500
            error_message = str(e)
            # 重新抛出异常
            raise
        finally:
            # 计算响应时间（毫秒）
            response_time = (time.time() - start_time) * 1000

            # 异步写入数据库（避免阻塞响应）
            try:
                await self._log_to_database(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message=error_message
                )
            except Exception as e:
                logger.error(f"API 日志写入失败: {e}", exc_info=True)

        return response

    async def _log_to_database(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: int = None,
        ip_address: str = None,
        user_agent: str = None,
        error_message: str = None
    ):
        """异步写入日志到数据库"""
        try:
            with get_db_session() as session:
                api_log = APILog(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message=error_message
                )
                session.add(api_log)
                session.commit()
        except Exception as e:
            logger.error(f"数据库日志写入失败: {e}", exc_info=True)
```

#### 3.2 注册中间件

**文件**: `apps/api/main.py`

**步骤**:
1. 在 FastAPI 应用中注册中间件:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.middleware.logging import APILoggingMiddleware

app = FastAPI(
    title="智能钓鱼助手 API",
    version="3.1.1",
    description="基于 LangChain 的智能钓鱼助手 REST API"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 日志中间件（新增）
app.add_middleware(APILoggingMiddleware)

# 注册路由
from apps.api.routes import fishing_router
from apps.api.routes.user_equipment import router as user_equipment_router
from apps.api.routes.auth import router as auth_router

app.include_router(fishing_router, prefix="/api/v1/fishing", tags=["fishing"])
app.include_router(user_equipment_router, prefix="/api/v1/user-equipment", tags=["user-equipment"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
```

2. 测试中间件:

```bash
# 启动服务器
uv run uvicorn apps.api.main:app --reload

# 发送测试请求
curl -X GET "http://localhost:8000/api/v1/fishing/tools"

# 查询日志数据库
sqlite3 packages/agent_fishing/tools/lure/data/equipment.db \
  "SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT 5;"

# 预期输出:
# id|timestamp|endpoint|method|status_code|response_time|user_id|ip_address|user_agent|error_message
# 1|2025-01-10 10:30:00|/api/v1/fishing/tools|GET|200|15.5||127.0.0.1|curl/7.68.0|
```

---

### Step 4: 实现 LLM 调用监控（Day 5）

#### 4.1 在 FishingAgent 中添加监控

**文件**: `packages/agent_fishing/core/agent.py`

**步骤**:
1. 添加 `_log_llm_call` 方法:

```python
import time
from datetime import datetime
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.system import LLMLog


class FishingAgent:
    # ... 现有代码

    def run(self, query: str) -> str:
        """
        执行查询（添加 LLM 监控）
        """
        start_time = time.time()

        # 记录调用统计
        self.total_model_calls += 1

        try:
            # 执行原有逻辑
            response = self.agent_executor.invoke(
                {"messages": [HumanMessage(content=query)]},
                config={"callbacks": [self.llm_callback]}
            )

            # 提取 token 统计
            prompt_tokens = getattr(self.llm_callback, 'prompt_tokens', 0)
            completion_tokens = getattr(self.llm_callback, 'completion_tokens', 0)
            total_tokens = prompt_tokens + completion_tokens

            # 计算成本（示例：通义千问定价）
            cost = self._calculate_cost(
                self.model_provider,
                prompt_tokens,
                completion_tokens
            )

            # 记录成功调用
            self._log_llm_call(
                model_provider=self.model_provider,
                model_name=self.llm.model_name if hasattr(self.llm, 'model_name') else 'unknown',
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time=time.time() - start_time,
                success=True,
                cost=cost
            )

            return response["messages"][-1].content

        except Exception as e:
            # 记录失败
            self.total_errors += 1

            self._log_llm_call(
                model_provider=self.model_provider,
                model_name=self.llm.model_name if hasattr(self.llm, 'model_name') else 'unknown',
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )

            raise

    def _log_llm_call(
        self,
        model_provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        response_time: float,
        success: bool,
        cost: float = 0.0,
        error_message: str = None
    ):
        """记录 LLM 调用到数据库"""
        try:
            with get_db_session() as session:
                llm_log = LLMLog(
                    model_provider=model_provider,
                    model_name=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    response_time=response_time,
                    success=success,
                    cost=cost,
                    error_message=error_message
                )
                session.add(llm_log)
                session.commit()
        except Exception as e:
            # 日志失败不应影响主流程
            import logging
            logging.error(f"LLM 日志写入失败: {e}", exc_info=True)

    def _calculate_cost(
        self,
        model_provider: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        计算 LLM 调用成本（元）

        定价参考（示例）:
        - 通义千问 qwen-max: ¥0.02/1K tokens
        - 智谱 GLM-4: ¥0.10/1K tokens
        - OpenAI GPT-4: $0.03/1K tokens ≈ ¥0.22/1K tokens
        """
        pricing = {
            "qwen": {"prompt": 0.02, "completion": 0.02},
            "zhipu": {"prompt": 0.10, "completion": 0.10},
            "openai": {"prompt": 0.22, "completion": 0.22},
            "doubao": {"prompt": 0.05, "completion": 0.05}
        }

        provider_pricing = pricing.get(model_provider, {"prompt": 0.0, "completion": 0.0})

        cost = (
            (prompt_tokens / 1000) * provider_pricing["prompt"] +
            (completion_tokens / 1000) * provider_pricing["completion"]
        )

        return round(cost, 6)  # 保留6位小数
```

2. 测试 LLM 监控:

```bash
# 运行 Agent 查询
uv run python debug_agent.py qwen direct "推荐适用饵范围介于2-10克的鱼竿"

# 查询 LLM 日志
sqlite3 packages/agent_fishing/tools/lure/data/equipment.db \
  "SELECT model_provider, total_tokens, response_time, cost, success FROM llm_logs ORDER BY timestamp DESC LIMIT 5;"

# 预期输出:
# model_provider|total_tokens|response_time|cost|success
# qwen|1523|2.34|0.030460|1
```

---

### Step 5: 创建首个 Admin 用户（Day 5）

#### 5.1 实现 CLI 脚本

**文件**: `scripts/create_admin.py`

**步骤**:
1. 创建管理员用户脚本:

```python
#!/usr/bin/env python3
"""
创建首个管理员用户

Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --username admin --password admin123
"""
import sys
import argparse
from getpass import getpass
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.admin_user import AdminUser
from apps.api.auth.jwt import get_password_hash
from apps.api.auth.permissions import RoleEnum


def create_admin_user(username: str, password: str, email: str = None):
    """
    创建管理员用户

    Args:
        username: 用户名
        password: 密码
        email: 邮箱（可选）
    """
    with get_db_session() as session:
        # 检查用户名是否已存在
        existing = session.query(AdminUser).filter_by(username=username).first()

        if existing:
            print(f"❌ 用户名已存在: {username}")
            return False

        # 创建管理员用户
        admin_user = AdminUser(
            username=username,
            password_hash=get_password_hash(password),
            role=RoleEnum.ADMIN.value,
            email=email,
            is_active=True
        )

        session.add(admin_user)
        session.commit()

        print(f"✅ 管理员用户创建成功!")
        print(f"   用户名: {username}")
        print(f"   角色: admin")
        print(f"   邮箱: {email or '未设置'}")

        return True


def main():
    parser = argparse.ArgumentParser(description="创建管理员用户")
    parser.add_argument("--username", default="admin", help="用户名（默认: admin）")
    parser.add_argument("--password", help="密码（不提供则交互式输入）")
    parser.add_argument("--email", help="邮箱（可选）")

    args = parser.parse_args()

    # 获取密码
    if args.password:
        password = args.password
    else:
        print(f"为用户 '{args.username}' 设置密码:")
        password = getpass("密码: ")
        password_confirm = getpass("确认密码: ")

        if password != password_confirm:
            print("❌ 两次密码不一致")
            sys.exit(1)

    # 密码强度检查
    if len(password) < 6:
        print("❌ 密码长度至少为 6 位")
        sys.exit(1)

    # 创建用户
    success = create_admin_user(
        username=args.username,
        password=password,
        email=args.email
    )

    if success:
        print("\n🎉 现在可以使用该账户登录管理后台!")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

2. 使用脚本创建管理员:

```bash
# 交互式创建（推荐）
uv run python scripts/create_admin.py
# 输入用户名: admin
# 输入密码: ******
# 确认密码: ******

# 命令行参数创建（开发环境）
uv run python scripts/create_admin.py --username admin --password admin123 --email admin@example.com

# 预期输出:
# ✅ 管理员用户创建成功!
#    用户名: admin
#    角色: admin
#    邮箱: admin@example.com
#
# 🎉 现在可以使用该账户登录管理后台!
```

---

## 测试用例

### 单元测试

```bash
# 测试 JWT
uv run pytest tests/test_jwt.py -v

# 测试权限系统
uv run pytest tests/test_permissions.py -v

# 测试登录端点
uv run pytest tests/test_auth_routes.py -v
```

### 集成测试

**文件**: `tests/test_integration_auth.py`

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_full_auth_flow():
    """测试完整认证流程"""
    # 1. 未认证访问应该返回 401
    response = client.get("/api/v1/equipment")
    assert response.status_code == 401

    # 2. 登录获取 token
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. 使用 token 访问受保护端点
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/equipment", headers=headers)
    assert response.status_code == 200


def test_permission_denied():
    """测试权限拒绝"""
    # 1. 以 readonly 用户登录
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "readonly_user", "password": "password"}
    )
    token = login_response.json()["access_token"]

    # 2. 尝试创建装备（应该被拒绝）
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/equipment",
        headers=headers,
        json={"name": "Test Equipment", "category": "鱼竿"}
    )
    assert response.status_code == 403
    assert "权限不足" in response.json()["detail"]
```

---

## 注意事项

### 1. 安全最佳实践

⚠️ **JWT Secret Key**:
```bash
# 生产环境必须更换默认密钥
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

⚠️ **密码哈希强度**:
- bcrypt cost factor 默认 12（2^12 = 4096 轮）
- 验证时间约 100-200ms，安全性与性能平衡

⚠️ **Token 过期时间**:
- 开发环境: 30 分钟
- 生产环境: 建议 15 分钟 + Refresh Token 机制

### 2. 性能优化

🚀 **日志异步写入**:
- 中间件使用 `finally` 确保日志写入
- 日志失败不阻塞响应
- 考虑使用消息队列（Redis/RabbitMQ）批量写入

🚀 **Token 验证缓存**:
- 可选：使用 Redis 缓存已验证的 token（key=token, value=user_info, ttl=5min）
- 减少重复验证开销

### 3. 监控告警

📊 **关键指标**:
- API 错误率 > 5% → 告警
- 平均响应时间 > 500ms → 告警
- LLM 调用失败率 > 10% → 告警
- Token 成本超预算 → 告警

### 4. 常见陷阱

🐛 **中间件顺序**:
```python
# ✅ 正确顺序
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(APILoggingMiddleware)  # 日志中间件在 CORS 之后

# ❌ 错误顺序
app.add_middleware(APILoggingMiddleware)  # 会记录 CORS preflight 请求
app.add_middleware(CORSMiddleware, ...)
```

🐛 **密码验证顺序**:
```python
# ✅ 先查用户再验证密码（防止时序攻击）
user = get_user(username)
if not user:
    raise HTTPException(...)  # 用户不存在
if not verify_password(password, user.password_hash):
    raise HTTPException(...)  # 密码错误

# ❌ 直接在查询中验证（泄露用户存在性）
user = session.query(AdminUser).filter_by(
    username=username,
    password_hash=get_password_hash(password)
).first()
```

---

## 验收标准

### 必须完成

- ✅ JWT token 生成和验证测试通过
- ✅ 3 种角色（Admin/Editor/ReadOnly）权限正确
- ✅ 登录端点返回正确的 token 和用户信息
- ✅ 权限依赖在路由中生效（403 错误）
- ✅ API 日志中间件记录所有请求
- ✅ LLM 调用监控记录 token 和成本
- ✅ 首个 admin 用户创建成功

### 可选优化

- 🔧 实现 Refresh Token 机制
- 🔧 添加登录限流（5次/分钟）
- 🔧 密码强度检查（正则表达式）
- 🔧 Token 黑名单（Redis）
- 🔧 审计日志（管理员操作记录）

---

## 下一步

完成 Phase 2 后，进入 **Phase 3: 核心管理模块 API**（装备、用户、内容管理）
