# 智能钓鱼助手 - 测试文档 v5.0.2

本文档描述智能钓鱼助手v5.0.2的测试体系，包括数据分析报表、系统配置管理、爬虫监控模块、JWT认证系统、动态Prompt中间件、7因子科学评分系统、时间段意图理解、LLM优化功能、React管理前端、OCR多提供商系统、智能图片合并和集成测试。

**当前版本**: v5.0.2
**当前分支**: feature/equipment-ui (功能已完成)
**核心功能**: Phase 6 OCR多提供商支持 + Phase 5 数据分析配置 + Phase 4 爬虫监控 + JWT认证系统 + React管理前端 + 动态Prompt中间件 + 7因子科学评分 + LLM优化 + 装备管理UI优化

## 🧪 测试概览

### 测试覆盖率统计

| 测试模块 | 测试用例数 | 覆盖功能 | 状态 |
|----------|------------|----------|------|
| 数据分析报表系统 | 多个 | 装备统计/趋势分析/品牌排行 | ✅ 通过 |
| 系统配置管理 | 多个 | API密钥/配置加密/权限控制 | ✅ 通过 |
| 爬虫任务管理 | 多个 | 任务调度/进度监控/日志管理 | ✅ 通过 |
| 系统监控面板 | 多个 | API统计/LLM统计/数据库性能 | ✅ 通过 |
| JWT认证系统 | 4个文件 | 登录/权限/Token验证 | ✅ 全部通过 |
| 7因子科学评分系统 | 27个 | 季节/月相/趋势分析 | ✅ 全部通过 |
| 时间段意图识别 | 19个 | 时间段标准化/过滤 | ✅ 全部通过 |
| LLM优化功能 | 1个核心验证 | 工具选择效率/推理质量 | ✅ 通过 |
| 向量存储系统 | 多个 | 语义搜索/CLI管理 | ✅ 通过 |
| 全国覆盖测试 | 多个 | 3,142+地区支持 | ✅ 通过 |
| 集成测试 | 多个 | API集成/数据流 | ✅ 通过 |
| 边界测试 | 多个 | 异常处理/容错 | ✅ 通过 |

**总计**: 70+个测试用例，覆盖所有核心功能

## 📈 数据分析报表系统测试 (v5.0.0新增)

### 测试位置
- **目录**: `tests/api/test_analytics.py`
- **执行命令**: `uv run pytest tests/api/test_analytics.py -v`

### 核心测试功能

#### 装备数据统计测试
```python
def test_equipment_stats():
    """测试装备数据统计接口"""
    response = client.get("/api/v1/admin/analytics/equipment/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "category_stats" in data
    assert "price_distribution" in data

def test_equipment_trends():
    """测试装备趋势分析"""
    response = client.get("/api/v1/admin/analytics/equipment/trends?months=12")
    assert response.status_code == 200
    data = response.json()
    assert "monthly_trends" in data
    assert len(data["monthly_trends"]) <= 12
```

#### 品牌排行分析测试
```python
def test_brand_stats():
    """测试品牌统计排行"""
    response = client.get("/api/v1/admin/analytics/equipment/brand-stats?top_n=10")
    assert response.status_code == 200
    data = response.json()
    assert "brand_ranking" in data
    assert len(data["brand_ranking"]) <= 10
```

#### 报表生成测试
```python
def test_generate_report():
    """测试业务报表生成"""
    response = client.post("/api/v1/admin/analytics/reports/generate", json={
        "report_type": "equipment",
        "filters": {"category": "鱼竿"},
        "format": "pdf"
    })
    assert response.status_code == 200
    data = response.json()
    assert "report_id" in data
    assert "download_url" in data
```

## ⚙️ 系统配置管理测试 (v5.0.0新增)

### 测试位置
- **目录**: `tests/api/test_config.py`
- **执行命令**: `uv run pytest tests/api/test_config.py -v`

### 核心测试功能

#### 配置CRUD操作测试
```python
def test_create_config():
    """测试创建配置"""
    response = client.post("/api/v1/admin/config/configs", json={
        "config_key": "test.api_key",
        "config_value": "sk-test123",
        "config_type": "api",
        "description": "测试API密钥"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["config_key"] == "test.api_key"

def test_get_config():
    """测试获取配置"""
    response = client.get("/api/v1/admin/config/configs/test.api_key")
    assert response.status_code == 200
    data = response.json()
    assert "config_value" in data
    assert data["is_encrypted"] is True  # API密钥应加密存储
```

#### API密钥测试功能
```python
def test_api_key_validation():
    """测试API密钥有效性验证"""
    response = client.post("/api/v1/admin/config/configs/test-api-key", json={
        "config_type": "api",
        "test_endpoint": "https://api.caiyunapp.com/v2/weather"
    })
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "response_time" in data
```

## 🕷️ 爬虫任务管理测试 (v4.0.0新增)

### 测试位置
- **目录**: `tests/api/test_crawler_monitor.py`
- **执行命令**: `uv run pytest tests/api/test_crawler_monitor.py -v`

### 核心测试功能

#### 爬虫任务调度测试
```python
def test_trigger_crawler_task():
    """测试触发爬虫任务"""
    response = client.post("/api/v1/admin/crawler/tasks/trigger", json={
        "task_type": "taobao",
        "keywords": ["路亚竿"],
        "max_pages": 5
    })
    assert response.status_code == 201
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"

def test_get_crawler_tasks():
    """测试获取爬虫任务列表"""
    response = client.get("/api/v1/admin/crawler/tasks?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
```

#### WebSocket实时推送测试
```python
def test_crawler_websocket():
    """测试爬虫进度WebSocket推送"""
    with client.websocket_connect("/api/v1/admin/crawler/ws/crawler/1") as websocket:
        data = websocket.receive_json()
        assert "task_id" in data
        assert "progress" in data
```

## 📊 系统监控面板测试 (v4.0.0新增)

### 测试位置
- **目录**: `tests/api/test_monitor.py`
- **执行命令**: `uv run pytest tests/api/test_monitor.py -v`

### 核心测试功能

#### API统计监控测试
```python
def test_api_stats():
    """测试API调用统计"""
    response = client.get("/api/v1/admin/monitor/api-stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "avg_response_time" in data
    assert "top_endpoints" in data
```

#### LLM使用统计测试
```python
def test_llm_stats():
    """测试LLM使用统计"""
    response = client.get("/api/v1/admin/monitor/llm-stats")
    assert response.status_code == 200
    data = response.json()
    assert "token_usage" in data
    assert "cost_estimates" in data
    assert "success_rate" in data
```

## 🔐 JWT认证系统测试 (v3.1.1新增)

### 测试位置
- **目录**: `tests/test_auth/`
- **执行命令**: `uv run pytest tests/test_auth/ -v`

### 测试文件结构

#### 1. test_jwt.py - JWT核心功能测试
```python
def test_create_access_token():
    """测试JWT Token生成"""
    data = {"user_id": 1, "username": "admin", "role": "admin"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_token():
    """测试JWT Token验证"""
    # 先创建token
    token = create_access_token({"user_id": 1})
    # 验证token
    payload = verify_token(token)
    assert payload["user_id"] == 1
    assert "exp" in payload

def test_token_expiration():
    """测试Token过期处理"""
    # 创建已过期的token
    expired_token = create_access_token({}, expires_delta=timedelta(seconds=-1))
    # 验证应该抛出异常
    with pytest.raises(ValueError):
        verify_token(expired_token)
```

#### 2. test_login_routes.py - 登录接口测试
```python
def test_login_success():
    """测试登录成功"""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"

def test_login_wrong_password():
    """测试密码错误"""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "wrong"
    })
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]
```

#### 3. test_permissions.py - 权限管理测试
```python
def test_admin_permissions():
    """测试管理员权限"""
    permissions = get_role_permissions(RoleEnum.ADMIN)
    assert "equipment:create" in permissions
    assert "equipment:read" in permissions
    assert "equipment:update" in permissions
    assert "equipment:delete" in permissions

def test_user_permissions():
    """测试普通用户权限"""
    permissions = get_role_permissions(RoleEnum.USER)
    assert "equipment:read" in permissions
    assert "equipment:create" not in permissions
    assert "equipment:delete" not in permissions
```

#### 4. test_integration.py - 认证集成测试
```python
def test_protected_endpoint_without_token():
    """测试未认证访问保护端点"""
    response = client.get("/api/v1/auth/profile")
    assert response.status_code == 401

def test_protected_endpoint_with_token():
    """测试使用Token访问保护端点"""
    # 先登录获取token
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]

    # 使用token访问保护端点
    response = client.get("/api/v1/auth/profile", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "admin"
```

### 测试覆盖范围

1. **JWT工具函数**:
   - ✅ Token生成和验证
   - ✅ Token过期处理
   - ✅ 无效Token处理
   - ✅ 密码哈希和验证

2. **认证接口**:
   - ✅ 成功登录流程
   - ✅ 用户名密码错误处理
   - ✅ 禁用用户处理
   - ✅ 用户信息获取

3. **权限系统**:
   - ✅ 角色权限映射
   - ✅ 权限检查逻辑
   - ✅ 不同角色对比

4. **集成测试**:
   - ✅ 保护端点访问控制
   - ✅ Token传递机制
   - ✅ 认证中间件集成

## 🔬 7因子科学评分系统测试 (v3.0.0新增)

### 测试位置
- **文件**: `tests/agent_fishing/test_enhanced_fishing_scorer.py`
- **执行命令**: `uv run pytest tests/agent_fishing/test_enhanced_fishing_scorer.py -v`

### 测试类和用例

#### TestSeasonalScore (7个测试用例)
测试基于鱼类生物学规律的季节性评分算法：

```python
def test_spring_morning(self):
    """春季早晨评分测试 - 应为100分"""
    spring_morning = datetime(2024, 4, 15, 7, 0)
    score = calculate_seasonal_score(spring_morning, 7)
    assert score == 100.0

def test_spring_afternoon(self):
    """春季下午评分测试 - 应为85分"""
    spring_afternoon = datetime(2024, 4, 15, 14, 0)
    score = calculate_seasonal_score(spring_afternoon, 14)
    assert score == 85.0
```

**评分规则验证**:
- ✅ 春季：早晚最佳（100分），白天一般（85分），夜间差（70分）
- ✅ 夏季：清晨傍晚最佳（100分），中午最差（60分），其他中等（80分）
- ✅ 秋季：早晚最佳（100分），其他时段良好（85分）
- ✅ 冬季：中午最佳（90分），白天一般（75分），早晚很差（50分）

## ⏰ 时间段意图识别测试 (v2.3.0新增)

### 测试位置
- **文件**: `tests/agent_fishing/test_time_period_intent.py`
- **执行命令**: `uv run pytest tests/agent_fishing/test_time_period_intent.py -v`

### 测试类和用例 (19个测试用例)

#### TestTimePeriodNormalization (3个测试用例)
测试时间段标准化功能：

```python
def test_normalize_standard_names(self):
    """标准时间段名称测试"""
    assert normalize_time_period("白天") == "白天"
    assert normalize_time_period("晚上") == "晚上"
    assert normalize_time_period("上午") == "上午"

def test_normalize_aliases(self):
    """时间段别名标准化测试"""
    assert normalize_time_period("daytime") == "白天"
    assert normalize_time_period("night") == "晚上"
    assert normalize_time_period("morning") == "上午"
```

## 🖥️ React管理前端测试 (v5.0.0新增)

### 测试位置
- **目录**: `apps/web-admin/`
- **技术栈**: React 19.2.0 + TypeScript + Ant Design 5.22.0

### 前端测试策略

由于当前React前端使用的是基础Vite模板，没有集成测试框架，建议的测试方法：

#### 手动测试清单
```bash
# 1. 启动前端开发服务器
cd apps/web-admin
npm run dev

# 2. 手动测试项
- [ ] 页面加载正常
- [ ] 路由导航工作
- [ ] API接口调用
- [ ] 数据展示正确
- [ ] 表单提交功能
- [ ] 响应式布局
```

#### 建议的测试工具集成
```json
// package.json 可添加的测试依赖
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0"
  },
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

## 🚀 运行测试

### 快速测试命令

```bash
# 运行所有测试
uv run pytest tests/

# 运行数据分析API测试
uv run pytest tests/api/test_analytics.py -v

# 运行配置管理API测试
uv run pytest tests/api/test_config.py -v

# 运行爬虫监控测试
uv run pytest tests/api/test_crawler_monitor.py -v

# 运行系统监控测试
uv run pytest tests/api/test_monitor.py -v

# 运行JWT认证测试
uv run pytest tests/test_auth/ -v

# 运行7因子评分系统测试（27个用例）
uv run pytest tests/agent_fishing/test_enhanced_fishing_scorer.py -v

# 运行时间段意图测试（19个用例）
uv run pytest tests/agent_fishing/test_time_period_intent.py -v

# 运行LLM优化验证测试
uv run python test_quick_validation.py

# 运行全国覆盖测试
uv run pytest tests/agent_fishing/test_national_coverage.py

# 运行集成测试
uv run pytest tests/agent_fishing/integration/verify_national_integration.py

# 测试向量存储系统
uv run python -m packages.agent_fishing.tools.lure.cli status
uv run python -m packages.agent_fishing.tools.lure.cli search "鲈鱼习性" --type fish --top-k 3

# 生成测试覆盖率报告
uv run pytest tests/ --cov=packages --cov-report=html
```

### 前端测试命令

```bash
# 启动前端开发服务器
cd apps/web-admin
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 代码检查
npm run lint
```

### 分类测试执行

```bash
# 单元测试（不需要API密钥）
uv run pytest tests/ -k "not integration" -v

# 集成测试（需要API密钥）
uv run pytest tests/ -k "integration" -v

# API端点测试
uv run pytest tests/api/ -v

# 边界测试
uv run pytest tests/ -k "edge or boundary" -v

# 性能测试
uv run pytest tests/ -k "performance" -v

# LLM优化专项测试
uv run python test_quick_validation.py
```

## 📊 测试结果分析

### 预期测试结果

| 测试类型 | 预期通过率 | 备注 |
|----------|------------|------|
| 数据分析报表系统 | 95%+ | 依赖数据库数据 |
| 系统配置管理 | 100% | 完整CRUD操作 |
| 爬虫任务管理 | 90%+ | 依赖外部网站 |
| 系统监控面板 | 95%+ | 依赖运行时数据 |
| JWT认证系统 | 100% (4个文件) | 核心安全功能 |
| 7因子评分系统 | 100% (27/27) | 核心算法测试 |
| 时间段意图识别 | 100% (19/19) | 功能完整性测试 |
| LLM优化功能 | 100% (1/1) | 工具选择效率验证 |
| 向量存储系统 | 95%+ | 依赖DashScope API |
| 全国覆盖测试 | 95%+ | 依赖网络和API |
| 集成测试 | 90%+ | 依赖外部服务 |
| 边界测试 | 100% | 异常处理测试 |

### LLM优化功能验证标准

#### 工具选择优化
- **优化前**: 复合查询可能调用2-3个工具（天气+钓鱼+重复调用）
- **优化后**: 复合查询仅调用1个核心工具（钓鱼推荐工具包含天气分析）
- **验证方法**: `test_quick_validation.py` 验证工具调用次数

#### 推理质量改进
- **意图识别准确率**: 95%+ → 98%+
- **响应自然度**: 更流畅的中文表达
- **工具选择准确性**: 更精准的工具选择逻辑

### 故障排除

#### 常见失败原因

1. **API密钥未配置**
   ```bash
   # 检查环境变量
   echo $ANTHROPIC_AUTH_TOKEN
   echo $CAIYUN_API_KEY
   echo $AMAP_API_KEY
   echo $DASHSCOPE_API_KEY
   ```

2. **分支状态错误**
   ```bash
   # 确保在正确分支
   git checkout feature/equipment-ui
   git pull origin feature/equipment-ui
   ```

3. **网络连接问题**
   ```bash
   # 测试网络连接
   curl -I https://api.caiyunapp.com
   curl -I https://restapi.amap.com
   curl -I https://dashscope.aliyuncs.com
   ```

4. **前端依赖问题**
   ```bash
   # 重新安装前端依赖
   cd apps/web-admin
   rm -rf node_modules package-lock.json
   npm install
   ```

5. **数据库连接问题**
   ```bash
   # 检查数据库文件
   ls -la packages/agent_fishing/tools/lure/data/equipment.db
   ```

## 🎯 测试最佳实践

### API测试最佳实践

1. **使用测试数据库**
   ```python
   @pytest.fixture
   def test_db():
       # 创建临时测试数据库
       db_path = ":memory:"
       engine = create_engine(f"sqlite:///{db_path}")
       yield engine
       # 清理
   ```

2. **Mock外部依赖**
   ```python
   from unittest.mock import patch, MagicMock

   @patch('requests.get')
   def test_api_call(mock_get):
       mock_get.return_value.json.return_value = {"data": "test"}
       result = function_under_test()
       assert result is not None
   ```

3. **认证测试**
   ```python
   def test_protected_endpoint():
       # 测试未认证访问
       response = client.get("/api/v1/admin/analytics/equipment/stats")
       assert response.status_code == 401
       
       # 测试认证访问
       token = create_test_token()
       response = client.get("/api/v1/admin/analytics/equipment/stats", 
                            headers={"Authorization": f"Bearer {token}"})
       assert response.status_code == 200
   ```

### 前端测试建议

1. **组件单元测试**
   ```typescript
   import { render, screen } from '@testing-library/react'
   import { EquipmentList } from './EquipmentList'

   test('renders equipment list', () => {
     render(<EquipmentList equipments={mockData} />)
     expect(screen.getByText('Equipment Name')).toBeInTheDocument()
   })
   ```

2. **API集成测试**
   ```typescript
   import { renderHook } from '@testing-library/react'
   import { useEquipmentData } from './hooks'

   test('fetches equipment data', async () => {
   const { result } = renderHook(() => useEquipmentData())
   await waitFor(() => {
     expect(result.current.data).toBeDefined()
   })
   })
   ```

### 持续集成

测试系统设计为与CI/CD流水线兼容：

```yaml
# GitHub Actions 示例
- name: Run Backend Tests
  run: |
    uv run pytest tests/ --cov=packages --cov-report=xml

- name: Run Frontend Tests
  run: |
    cd apps/web-admin
    npm install
    npm run test

- name: Build Frontend
  run: |
    cd apps/web-admin
    npm run build

- name: E2E Tests
  run: |
    # 启动API服务
    uv run uvicorn apps.api.main:app &
    # 启动前端服务
    cd apps/web-admin && npm run dev &
    # 运行E2E测试
    npm run test:e2e
```

---

**文档版本**: v5.0.0
**最后更新**: 2025-12-11
**测试框架**: pytest 9.0.1
**前端框架**: React 19.2.0 + TypeScript + Ant Design 5.22.0
**覆盖率目标**: >85%
**维护者**: 智能钓鱼助手项目
**当前分支**: feature/equipment-ui

**测试哲学**: "快速失败，快速修复" - 通过全面的测试覆盖确保系统的可靠性和稳定性，重点验证Phase 5数据分析配置、Phase 4爬虫监控、JWT认证系统和React管理前端的集成稳定性。