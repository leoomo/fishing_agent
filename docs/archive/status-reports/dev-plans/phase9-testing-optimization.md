# Phase 9: 测试与优化详细方案

**目标**: 完善测试和性能优化
**周期**: 第 11 周（5 个工作日）
**优先级**: P1（质量保障）

---

## 目标概述

确保系统质量和性能，通过全面测试和优化提升用户体验。

**核心任务**:
- 后端单元测试和集成测试
- 前端组件测试和 E2E 测试
- 性能优化（数据库、API、前端）
- 安全审计
- 负载测试

---

## Day 1-2: 后端测试

### Step 1: 单元测试（Day 1）

#### 1.1 测试环境配置

**文件**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=packages --cov-report=html --cov-report=term"

[project.optional-dependencies]
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",  # FastAPI 测试
]
```

**安装测试依赖**:
```bash
uv sync --extra test
```

#### 1.2 模型测试

**文件**: `tests/test_models.py`

```python
import pytest
from datetime import datetime
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.models.equipment import Equipment, RodSpec
from packages.agent_fishing.tools.lure.models.brand import Brand


@pytest.fixture
def test_db():
    """测试数据库 fixture"""
    # 使用测试数据库
    import os
    os.environ['DB_PATH'] = 'test_equipment.db'

    # 创建表
    from packages.agent_fishing.tools.lure.orm.session import init_db
    init_db()

    yield

    # 清理
    import os
    if os.path.exists('test_equipment.db'):
        os.remove('test_equipment.db')


def test_equipment_creation(test_db):
    """测试装备创建"""
    with get_db_session() as session:
        # 创建品牌
        brand = Brand(
            name_cn="测试品牌",
            name_en="Test Brand"
        )
        session.add(brand)
        session.commit()
        session.refresh(brand)

        # 创建装备
        equipment = Equipment(
            name="测试鱼竿",
            category="鱼竿",
            brand_id=brand.brand_id,
            model="TEST-001",
            price_min=199,
            price_max=299,
            user_level="新手",
            is_active=True,
            source="test"
        )
        session.add(equipment)
        session.commit()
        session.refresh(equipment)

        assert equipment.equipment_id is not None
        assert equipment.name == "测试鱼竿"
        assert equipment.brand_id == brand.brand_id


def test_equipment_with_specs(test_db):
    """测试装备规格关联"""
    with get_db_session() as session:
        # 创建品牌
        brand = Brand(name_cn="测试品牌")
        session.add(brand)
        session.commit()

        # 创建装备
        equipment = Equipment(
            name="测试鱼竿",
            category="鱼竿",
            brand_id=brand.brand_id,
            user_level="新手"
        )
        session.add(equipment)
        session.commit()
        session.refresh(equipment)

        # 创建规格
        rod_spec = RodSpec(
            equipment_id=equipment.equipment_id,
            length=2.1,
            power="ML",
            action="Fast",
            lure_weight_min=2,
            lure_weight_max=10
        )
        session.add(rod_spec)
        session.commit()

        # 验证关联
        equipment = session.query(Equipment).filter_by(
            equipment_id=equipment.equipment_id
        ).first()

        assert equipment.rod_spec is not None
        assert equipment.rod_spec.length == 2.1
        assert equipment.rod_spec.power == "ML"


def test_equipment_brand_relationship(test_db):
    """测试装备品牌关系"""
    with get_db_session() as session:
        brand = Brand(name_cn="迪卡侬")
        session.add(brand)
        session.commit()

        equipment = Equipment(
            name="CAPERLAN路亚竿",
            category="鱼竿",
            brand_id=brand.brand_id,
            user_level="新手"
        )
        session.add(equipment)
        session.commit()
        session.refresh(equipment)

        # 测试关系
        assert equipment.brand is not None
        assert equipment.brand.name_cn == "迪卡侬"
```

#### 1.3 Repository 测试

**文件**: `tests/test_repositories.py`

```python
import pytest
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository
from packages.agent_fishing.tools.lure.orm.repositories.brand_repo import BrandRepository
from packages.agent_fishing.tools.lure.models.equipment import Equipment
from packages.agent_fishing.tools.lure.models.brand import Brand


@pytest.fixture
def test_db():
    """测试数据库 fixture"""
    import os
    os.environ['DB_PATH'] = 'test_equipment.db'

    from packages.agent_fishing.tools.lure.orm.session import init_db
    init_db()

    yield

    if os.path.exists('test_equipment.db'):
        os.remove('test_equipment.db')


def test_equipment_repo_create(test_db):
    """测试装备仓库创建"""
    with get_db_session() as session:
        brand_repo = BrandRepository(session)
        equipment_repo = EquipmentRepository(session)

        # 创建品牌
        brand = brand_repo.create_brand({
            "name_cn": "测试品牌"
        })

        # 创建装备
        equipment_data = {
            "name": "测试装备",
            "category": "鱼竿",
            "brand_id": brand.brand_id,
            "user_level": "新手",
            "is_active": True,
            "source": "test"
        }

        equipment = equipment_repo.create(equipment_data)

        assert equipment.equipment_id is not None
        assert equipment.name == "测试装备"


def test_equipment_repo_search(test_db):
    """测试装备搜索"""
    with get_db_session() as session:
        brand_repo = BrandRepository(session)
        equipment_repo = EquipmentRepository(session)

        # 准备测试数据
        brand = brand_repo.create_brand({"name_cn": "测试品牌"})

        for i in range(5):
            equipment_repo.create({
                "name": f"测试鱼竿{i}",
                "category": "鱼竿",
                "brand_id": brand.brand_id,
                "price_min": 100 + i * 100,
                "price_max": 200 + i * 100,
                "user_level": "新手"
            })

        # 测试搜索
        results = equipment_repo.search(
            filters={"category": "鱼竿"},
            price_min=150,
            price_max=350,
            limit=10
        )

        assert len(results) > 0
        assert all(eq.category == "鱼竿" for eq in results)


def test_equipment_repo_create_with_specs(test_db):
    """测试带规格创建装备"""
    with get_db_session() as session:
        brand_repo = BrandRepository(session)
        equipment_repo = EquipmentRepository(session)

        brand = brand_repo.create_brand({"name_cn": "测试品牌"})

        equipment_data = {
            "name": "测试鱼竿",
            "category": "鱼竿",
            "brand_id": brand.brand_id,
            "user_level": "新手"
        }

        spec_data = {
            "length": 2.1,
            "power": "ML",
            "action": "Fast",
            "lure_weight_min": 2,
            "lure_weight_max": 10
        }

        equipment = equipment_repo.create_with_specs(
            equipment_data=equipment_data,
            spec_data=spec_data,
            category="鱼竿"
        )

        assert equipment.rod_spec is not None
        assert equipment.rod_spec.length == 2.1
```

#### 1.4 API 测试

**文件**: `tests/test_api_equipment.py`

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


@pytest.fixture
def admin_token():
    """获取管理员 token"""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_list_equipment(admin_token):
    """测试装备列表"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(
        "/api/v1/admin/equipment?page=1&page_size=10",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_create_equipment(admin_token):
    """测试创建装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    equipment_data = {
        "name": "测试鱼竿API",
        "category": "鱼竿",
        "brand_id": 1,
        "model": "TEST-API-001",
        "price_min": 199,
        "price_max": 299,
        "user_level": "新手",
        "specs": {
            "length": 2.1,
            "power": "ML",
            "action": "Fast",
            "lure_weight_min": 2,
            "lure_weight_max": 10
        }
    }

    response = client.post(
        "/api/v1/admin/equipment",
        headers=headers,
        json=equipment_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试鱼竿API"
    assert "equipment_id" in data


def test_update_equipment(admin_token):
    """测试更新装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    update_data = {
        "price_min": 249,
        "price_max": 349,
        "description": "更新后的描述"
    }

    response = client.put(
        "/api/v1/admin/equipment/1",
        headers=headers,
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["price_min"] == 249


def test_delete_equipment(admin_token):
    """测试删除装备"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.delete(
        "/api/v1/admin/equipment/999",  # 使用不存在的ID
        headers=headers
    )

    # 应该返回 404
    assert response.status_code == 404


def test_permission_denied():
    """测试权限拒绝"""
    # 不带 token 访问
    response = client.get("/api/v1/admin/equipment")
    assert response.status_code == 401
```

### Step 2: 运行测试（Day 1）

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_models.py -v

# 生成覆盖率报告
uv run pytest tests/ --cov=packages --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

**验收标准**:
- ✅ 测试覆盖率 > 70%
- ✅ 所有测试通过
- ✅ 无警告和错误

---

## Day 3: 前端测试

### Step 3: 组件测试

**安装测试库**:
```bash
cd apps/web-admin
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom
```

**配置 Vitest**:

**文件**: `apps/web-admin/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
```

**文件**: `apps/web-admin/src/test/setup.ts`

```typescript
import '@testing-library/jest-dom'
```

**测试示例**:

**文件**: `apps/web-admin/src/components/Equipment/__tests__/EquipmentList.test.tsx`

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { configureStore } from '@reduxjs/toolkit'
import EquipmentList from '../EquipmentList'
import equipmentReducer from '@/store/slices/equipmentSlice'

const renderWithProviders = (component: React.ReactElement) => {
  const store = configureStore({
    reducer: {
      equipment: equipmentReducer,
    },
  })

  return render(
    <Provider store={store}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </Provider>
  )
}

describe('EquipmentList', () => {
  it('renders equipment list', async () => {
    renderWithProviders(<EquipmentList />)

    // 等待加载完成
    await waitFor(() => {
      expect(screen.getByText('装备管理')).toBeInTheDocument()
    })
  })

  it('shows loading state', () => {
    renderWithProviders(<EquipmentList />)

    // 应该显示加载状态
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })
})
```

**运行测试**:
```bash
npm run test
```

---

## Day 4-5: 性能优化

### Step 4: 数据库优化（Day 4）

#### 4.1 添加索引

**文件**: `packages/agent_fishing/tools/lure/alembic/versions/003_add_indexes.py`

```python
"""添加性能索引

Revision ID: 003
"""
from alembic import op


def upgrade():
    # 装备表索引
    op.create_index('idx_equipment_category', 'equipment', ['category'])
    op.create_index('idx_equipment_brand_id', 'equipment', ['brand_id'])
    op.create_index('idx_equipment_is_active', 'equipment', ['is_active'])
    op.create_index('idx_equipment_created_at', 'equipment', ['created_at'])
    op.create_index('idx_equipment_price', 'equipment', ['price_min', 'price_max'])

    # API 日志索引
    op.create_index('idx_api_logs_timestamp', 'api_logs', ['timestamp'])
    op.create_index('idx_api_logs_endpoint', 'api_logs', ['endpoint'])
    op.create_index('idx_api_logs_status', 'api_logs', ['status_code'])

    # LLM 日志索引
    op.create_index('idx_llm_logs_timestamp', 'llm_logs', ['timestamp'])
    op.create_index('idx_llm_logs_provider', 'llm_logs', ['model_provider'])
    op.create_index('idx_llm_logs_success', 'llm_logs', ['success'])

    # 用户装备索引
    op.create_index('idx_user_equipment_user_id', 'user_equipment', ['user_id'])
    op.create_index('idx_user_equipment_equipment_id', 'user_equipment', ['equipment_id'])


def downgrade():
    # 删除索引
    op.drop_index('idx_equipment_category')
    op.drop_index('idx_equipment_brand_id')
    op.drop_index('idx_equipment_is_active')
    op.drop_index('idx_equipment_created_at')
    op.drop_index('idx_equipment_price')

    op.drop_index('idx_api_logs_timestamp')
    op.drop_index('idx_api_logs_endpoint')
    op.drop_index('idx_api_logs_status')

    op.drop_index('idx_llm_logs_timestamp')
    op.drop_index('idx_llm_logs_provider')
    op.drop_index('idx_llm_logs_success')

    op.drop_index('idx_user_equipment_user_id')
    op.drop_index('idx_user_equipment_equipment_id')
```

**应用迁移**:
```bash
cd packages/agent_fishing/tools/lure
alembic upgrade head
```

#### 4.2 查询优化

**使用预加载避免 N+1**:

```python
# ❌ N+1 查询
equipment_list = session.query(Equipment).all()
for eq in equipment_list:
    print(eq.brand.name_cn)  # 每次都查询数据库

# ✅ 预加载
from sqlalchemy.orm import joinedload

equipment_list = session.query(Equipment)\
    .options(joinedload(Equipment.brand))\
    .all()

for eq in equipment_list:
    print(eq.brand.name_cn)  # 已加载，不再查询
```

#### 4.3 分页优化

```python
# ✅ 使用 LIMIT + OFFSET
equipment_list = session.query(Equipment)\
    .filter(Equipment.is_active == True)\
    .limit(20)\
    .offset(0)\
    .all()

# ✅ 使用游标分页（更高效）
last_id = 0
equipment_list = session.query(Equipment)\
    .filter(Equipment.equipment_id > last_id)\
    .order_by(Equipment.equipment_id)\
    .limit(20)\
    .all()
```

### Step 5: API 性能优化（Day 4）

#### 5.1 添加缓存（可选：Redis）

**文件**: `apps/api/utils/cache.py`

```python
import json
from typing import Optional, Callable
from functools import wraps
import hashlib

# 简单的内存缓存（生产环境建议使用 Redis）
_cache = {}


def cache_response(ttl: int = 300):
    """
    缓存装饰器

    Args:
        ttl: 过期时间（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = hashlib.md5(
                f"{func.__name__}:{args}:{kwargs}".encode()
            ).hexdigest()

            # 检查缓存
            if cache_key in _cache:
                cached_value, timestamp = _cache[cache_key]
                if time.time() - timestamp < ttl:
                    return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            _cache[cache_key] = (result, time.time())

            return result

        return wrapper
    return decorator


# 使用示例
@router.get("/equipment")
@cache_response(ttl=60)  # 缓存 60 秒
async def list_equipment(...):
    ...
```

#### 5.2 批量操作

**批量创建**:

```python
@router.post("/equipment/batch")
async def batch_create_equipment(
    equipment_list: List[EquipmentCreate],
    current_user: CurrentUser = Depends(require_permission(PermissionEnum.EQUIPMENT_CREATE))
):
    """批量创建装备"""
    with get_db_session() as session:
        repo = EquipmentRepository(session)

        created_count = 0
        errors = []

        for eq_data in equipment_list:
            try:
                repo.create(eq_data.model_dump())
                created_count += 1
            except Exception as e:
                errors.append({
                    "name": eq_data.name,
                    "error": str(e)
                })

        session.commit()  # 一次性提交

        return {
            "success_count": created_count,
            "error_count": len(errors),
            "errors": errors
        }
```

### Step 6: 前端性能优化（Day 5）

#### 6.1 代码分割

**文件**: `apps/web-admin/src/App.tsx`

```typescript
import React, { lazy, Suspense } from 'react'
import { Spin } from 'antd'

// 懒加载页面
const EquipmentList = lazy(() => import('./pages/Equipment/List'))
const EquipmentForm = lazy(() => import('./pages/Equipment/Form'))
const UserList = lazy(() => import('./pages/Users/List'))

const App: React.FC = () => {
  return (
    <Suspense fallback={<Spin size="large" />}>
      <Routes>
        <Route path="/equipment" element={<EquipmentList />} />
        <Route path="/equipment/create" element={<EquipmentForm />} />
        <Route path="/users" element={<UserList />} />
      </Routes>
    </Suspense>
  )
}
```

#### 6.2 虚拟滚动

**安装**:
```bash
npm install react-window
```

**使用**:
```typescript
import { FixedSizeList } from 'react-window'

const VirtualList: React.FC<{ data: any[] }> = ({ data }) => {
  const Row = ({ index, style }: any) => (
    <div style={style}>
      {data[index].name}
    </div>
  )

  return (
    <FixedSizeList
      height={600}
      itemCount={data.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  )
}
```

#### 6.3 防抖搜索

```typescript
import { useCallback } from 'react'
import debounce from 'lodash/debounce'

const EquipmentList: React.FC = () => {
  const [keyword, setKeyword] = useState('')

  const handleSearch = useCallback(
    debounce((value: string) => {
      // 执行搜索
      fetchData({ keyword: value })
    }, 500),
    []
  )

  return (
    <Search
      placeholder="搜索装备"
      onChange={(e) => handleSearch(e.target.value)}
    />
  )
}
```

---

## Day 5: 安全审计

### Step 7: 安全检查

#### 7.1 SQL 注入防护

✅ **使用 ORM 参数化查询**（已实现）:
```python
# ✅ 安全
equipment = session.query(Equipment).filter(
    Equipment.name == user_input
).first()

# ❌ 不安全
equipment = session.execute(
    f"SELECT * FROM equipment WHERE name = '{user_input}'"
)
```

#### 7.2 XSS 防护

✅ **前端自动转义**（React 默认）:
```typescript
// ✅ React 自动转义
<div>{userInput}</div>

// ❌ 危险：使用 dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

#### 7.3 CSRF 防护

✅ **JWT token 认证**（已实现，无需 CSRF token）

#### 7.4 敏感数据加密

✅ **密码哈希**（已实现 bcrypt）
✅ **API 密钥加密**（已实现 Fernet）

#### 7.5 安全检查清单

```bash
# Python 依赖安全检查
uv run pip-audit

# 前端依赖安全检查
cd apps/web-admin
npm audit

# 修复漏洞
npm audit fix
```

---

## 验收标准

### 必须完成

- ✅ 后端测试覆盖率 > 70%
- ✅ 所有单元测试通过
- ✅ 所有 API 集成测试通过
- ✅ 前端组件测试通过
- ✅ 数据库索引已添加
- ✅ API 响应时间 < 200ms（平均）
- ✅ 前端首屏加载 < 2s
- ✅ 安全审计通过
- ✅ 无已知安全漏洞

### 性能指标

- API 平均响应时间: < 200ms
- API P95 响应时间: < 500ms
- 数据库查询时间: < 50ms
- 前端首屏加载: < 2s
- 前端交互响应: < 100ms

### 可选优化

- 🔧 负载测试（1000 并发）
- 🔧 压力测试（找到系统瓶颈）
- 🔧 Redis 缓存集成
- 🔧 CDN 静态资源加速
- 🔧 Gzip 压缩

---

## 下一步

完成 Phase 9 后，进入 **Phase 10: 文档与部署**
