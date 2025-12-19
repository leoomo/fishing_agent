# Phase 1: 数据库 ORM 层开发详细方案

**目标**: 实现 SQLAlchemy 模型和 ORM 仓库
**周期**: 第 1-2 周（10 个工作日）
**优先级**: P0（核心基础）

---

## 目标概述

将现有的 sqlite3 直接查询方式迁移到 SQLAlchemy ORM，支持多数据库（SQLite/PostgreSQL/MySQL），并保持与现有代码的完全兼容。

---

## 开发步骤

### Step 1: 创建数据模型（Day 1-3）

#### 1.1 创建基础模型类

**文件**: `packages/agent_fishing/tools/lure/models/base.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()

class TimestampMixin:
    """时间戳 Mixin"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class TableNameMixin:
    """自动表名 Mixin"""
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
```

**步骤**:
1. 创建 `models/` 目录
2. 创建 `base.py`，定义 `Base` 和 `Mixins`
3. 确保导入路径正确

#### 1.2 创建装备相关模型

**文件**: `packages/agent_fishing/tools/lure/models/equipment.py`

**步骤**:
1. 定义 `Equipment` 模型（对应 equipment 表）
2. 定义 `RodSpec`, `ReelSpec`, `LineSpec`, `LureSpec` 模型
3. 设置外键关系和索引
4. 添加 `relationship` 声明

**关键点**:
- 所有字段名必须与现有表完全一致
- 外键使用 `ondelete='CASCADE'`
- 需要的索引：`category`, `brand_id`, `price_min`, `is_active`, `source`

#### 1.3 创建其他核心模型

依次创建以下模型文件：

1. **brand.py**: `Brand` 模型
2. **user.py**: `User`, `UserEquipment`, `FishingLog`（新增）
3. **fish.py**: `FishSpecies`, `FishKnowledge`, `FishSeasonActivity`
4. **rig.py**: `RigTypes`, `RigSpecs`, `RigComponents`
5. **admin_user.py**: `AdminUser`
6. **system.py**: `CrawlerTask`, `CrawlerLog`, `APILog`, `LLMLog`, `SystemConfig`, `AnalyticsReport`

#### 1.4 创建模型总导出

**文件**: `packages/agent_fishing/tools/lure/models/__init__.py`

```python
from .base import Base
from .equipment import Equipment, RodSpec, ReelSpec, LineSpec, LureSpec
from .brand import Brand
from .user import User, UserEquipment, FishingLog
from .fish import FishSpecies, FishKnowledge, FishSeasonActivity
from .rig import RigTypes, RigSpecs, RigComponents
from .admin_user import AdminUser
from .system import CrawlerTask, CrawlerLog, APILog, LLMLog, SystemConfig, AnalyticsReport

__all__ = [
    'Base',
    'Equipment', 'RodSpec', 'ReelSpec', 'LineSpec', 'LureSpec',
    'Brand',
    'User', 'UserEquipment', 'FishingLog',
    # ... 其他模型
]
```

---

### Step 2: 实现 ORM 会话管理（Day 4）

#### 2.1 创建数据库配置

**文件**: `packages/agent_fishing/tools/lure/orm/session.py`

**步骤**:
1. 创建 `DatabaseConfig` 类，从环境变量读取配置
2. 支持 `DB_TYPE` 环境变量切换数据库类型
3. 实现 `get_engine()` 方法
4. 实现 `get_session_factory()` 方法（使用 `scoped_session`）
5. 实现 `get_db_session()` 上下文管理器
6. 实现 `init_db()` 方法（创建所有表）

**关键配置**:
- SQLite: `check_same_thread=False`
- PostgreSQL/MySQL: `pool_size=10, max_overflow=20, pool_pre_ping=True`

#### 2.2 测试数据库连接

**测试文件**: `tests/test_orm_session.py`

```python
def test_get_engine():
    engine = get_engine()
    assert engine is not None

def test_session_context():
    with get_db_session() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

---

### Step 3: 实现 Repository 模式（Day 5-6）

#### 3.1 创建 BaseRepository

**文件**: `packages/agent_fishing/tools/lure/orm/repository.py`

**步骤**:
1. 定义泛型 `BaseRepository[T]` 类
2. 实现通用方法：
   - `get(id)`: 根据主键查询
   - `get_all(filters, limit, offset)`: 列表查询
   - `create(obj)`: 创建记录
   - `update(id, data)`: 更新记录
   - `delete(id)`: 删除记录
   - `count(filters)`: 统计数量

#### 3.2 创建具体 Repository

**文件**: `packages/agent_fishing/tools/lure/orm/repositories/equipment_repo.py`

**步骤**:
1. 继承 `BaseRepository[Equipment]`
2. 实现扩展方法：
   - `get_with_details(equipment_id)`: 预加载关联数据
   - `search(category, brand_id, price_min, price_max, ...)`: 高级搜索
   - `create_with_specs(equipment_data, spec_data)`: 创建装备+规格

**文件**: `packages/agent_fishing/tools/lure/orm/repositories/brand_repo.py`

**步骤**:
1. 继承 `BaseRepository[Brand]`
2. 实现 `get_by_name(name_cn)`: 根据品牌名查询
3. 实现 `create_brand(brand_data)`: 创建品牌

依次创建：`user_repo.py`, `fish_repo.py`, `crawler_repo.py`

---

### Step 4: 配置 Alembic 迁移（Day 7）

#### 4.1 初始化 Alembic

```bash
cd packages/agent_fishing/tools/lure
alembic init alembic
```

#### 4.2 配置 Alembic

**文件**: `packages/agent_fishing/tools/lure/alembic.ini`

修改：
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
# → 改为从环境变量读取
```

**文件**: `packages/agent_fishing/tools/lure/alembic/env.py`

修改：
```python
from models.base import Base
from models import *  # 导入所有模型

target_metadata = Base.metadata

# 从环境变量读取数据库 URL
config.set_main_option('sqlalchemy.url', DatabaseConfig.get_database_url())
```

#### 4.3 生成初始迁移

```bash
alembic revision --autogenerate -m "initial migration"
alembic upgrade head
```

#### 4.4 创建新表迁移

**文件**: `alembic/versions/002_system_tables.py`

手动创建迁移：
- `fishing_logs` 表
- `crawler_tasks` 表
- `crawler_logs` 表
- `api_logs` 表
- `llm_logs` 表
- `system_config` 表
- `analytics_reports` 表

---

### Step 5: 编写单元测试（Day 8-9）

#### 5.1 测试模型定义

**文件**: `tests/test_models.py`

```python
def test_equipment_model():
    eq = Equipment(name="Test Rod", category="鱼竿", brand_id=1)
    assert eq.name == "Test Rod"

def test_relationships():
    # 测试外键关系
    eq = session.query(Equipment).first()
    assert eq.brand is not None
    assert eq.rod_spec is not None
```

#### 5.2 测试 Repository

**文件**: `tests/test_equipment_repo.py`

```python
def test_create_equipment():
    repo = EquipmentRepository(session)
    eq = repo.create(Equipment(name="Test", category="鱼竿"))
    assert eq.equipment_id is not None

def test_get_with_details():
    repo = EquipmentRepository(session)
    eq = repo.get_with_details(1)
    assert eq.brand is not None  # 预加载成功

def test_search():
    repo = EquipmentRepository(session)
    results = repo.search(category="鱼竿", price_max=500)
    assert len(results) > 0
```

#### 5.3 测试迁移

```bash
# 测试迁移
alembic downgrade base
alembic upgrade head

# 验证所有表都已创建
sqlite3 equipment.db ".tables"
```

---

### Step 6: 验证向后兼容性（Day 10）

#### 6.1 测试现有工具

运行现有 LangChain 工具，确保不受影响：

```bash
python debug_agent.py qwen direct "推荐适用饵范围介于2-10克的鱼竿"
```

**预期结果**: 工具正常运行，返回推荐结果

#### 6.2 测试新 ORM 访问

创建测试脚本 `test_orm_access.py`:

```python
from packages.agent_fishing.tools.lure.orm.session import get_db_session
from packages.agent_fishing.tools.lure.orm.repositories.equipment_repo import EquipmentRepository

with get_db_session() as session:
    repo = EquipmentRepository(session)
    equipment = repo.search(category='鱼竿', limit=5)
    print(f"Found {len(equipment)} equipment items")
    for eq in equipment:
        print(f"  - {eq.name} ({eq.brand.name_cn if eq.brand else 'Unknown'})")
```

**预期结果**: 成功查询并打印装备信息

---

## 测试用例

### 单元测试

```bash
# 运行所有模型测试
pytest tests/test_models.py -v

# 运行 Repository 测试
pytest tests/test_equipment_repo.py -v
pytest tests/test_brand_repo.py -v

# 运行会话管理测试
pytest tests/test_orm_session.py -v
```

### 集成测试

```bash
# 测试完整流程
pytest tests/test_integration_orm.py -v
```

**测试覆盖目标**: > 80%

---

## 注意事项

### 1. 数据库兼容性

⚠️ **重要**: 字段名和类型必须与现有表完全一致

- 检查现有表结构：
  ```bash
  sqlite3 equipment.db ".schema equipment"
  ```
- 对比模型定义，确保一致

### 2. 外键和索引

✅ **必须添加的索引**:
- `equipment.category`
- `equipment.brand_id`
- `equipment.is_active`
- `equipment.source`
- `user_equipment.user_id`
- `user_equipment.equipment_id`
- `api_logs.timestamp`
- `api_logs.endpoint`
- `llm_logs.timestamp`
- `llm_logs.model_provider`

### 3. 性能优化

🚀 **懒加载 vs 预加载**:
- 默认使用懒加载（`lazy='select'`）
- 列表查询使用 `joinedload` 预加载关联数据
- 避免 N+1 查询问题

示例：
```python
# ❌ N+1 查询
equipment = session.query(Equipment).all()
for eq in equipment:
    print(eq.brand.name_cn)  # 每次都查询数据库

# ✅ 预加载
equipment = session.query(Equipment)\
    .options(joinedload(Equipment.brand))\
    .all()
for eq in equipment:
    print(eq.brand.name_cn)  # 已加载，不再查询
```

### 4. 事务管理

⚠️ **重要**: 使用上下文管理器确保事务正确提交或回滚

```python
# ✅ 正确方式
with get_db_session() as session:
    repo = EquipmentRepository(session)
    repo.create(equipment)
    # 自动 commit 或 rollback

# ❌ 错误方式
session = get_session_factory()()
repo.create(equipment)
# 忘记 commit！
```

### 5. 常见陷阱

🐛 **常见错误**:

1. **循环导入**: 模型之间相互导入
   - 解决：使用字符串引用外键（`ForeignKey('table.id')`）

2. **Session 泄漏**: Session 未正确关闭
   - 解决：使用 `get_db_session()` 上下文管理器

3. **Detached Instance**: 在 session 关闭后访问对象
   - 解决：在 session 中完成所有数据访问

4. **列名冲突**: Python 保留字作为列名
   - 解决：使用 `name_` 或其他变体

### 6. 数据迁移检查清单

- [ ] 备份现有数据库
  ```bash
  cp equipment.db equipment.db.backup
  ```
- [ ] 生成迁移文件
  ```bash
  alembic revision --autogenerate -m "描述"
  ```
- [ ] 检查生成的迁移文件
  - 确认所有表和列都正确
  - 检查索引和外键
- [ ] 在开发环境测试迁移
  ```bash
  alembic upgrade head
  ```
- [ ] 验证数据完整性
  ```bash
  sqlite3 equipment.db "SELECT COUNT(*) FROM equipment"
  ```
- [ ] 测试降级
  ```bash
  alembic downgrade -1
  alembic upgrade head
  ```

### 7. 多数据库配置

**环境变量配置**:

```bash
# SQLite (开发)
export DB_TYPE=sqlite
export DB_PATH=packages/agent_fishing/tools/lure/data/equipment.db

# PostgreSQL (生产)
export DB_TYPE=postgresql
export DB_USER=fishing_admin
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=fishing_agent

# MySQL
export DB_TYPE=mysql
export DB_USER=root
export DB_PASSWORD=your_password
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=fishing_agent
```

**测试不同数据库**:

```bash
# 测试 SQLite
DB_TYPE=sqlite pytest tests/test_equipment_repo.py

# 测试 PostgreSQL
DB_TYPE=postgresql pytest tests/test_equipment_repo.py
```

---

## 验收标准

### 必须完成

- ✅ 所有模型定义完成（23 张表）
- ✅ 所有 Repository 实现完成（5 个核心 Repo）
- ✅ Alembic 迁移配置完成
- ✅ 单元测试通过，覆盖率 > 80%
- ✅ `alembic upgrade head` 成功创建所有表
- ✅ 现有 LangChain 工具继续正常工作
- ✅ 新 ORM 访问方式测试通过

### 可选优化

- 🔧 添加数据库查询日志（开发模式）
- 🔧 实现连接池监控
- 🔧 添加慢查询记录
- 🔧 实现数据库健康检查

---

## 下一步

完成 Phase 1 后，进入 **Phase 2: 认证授权 + 中间件**
