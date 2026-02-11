# 开发工作流指南 v5.1.0

指导日常开发工作，确保代码质量和团队协作效率。

## 📋 目录

- [快速开始](#快速开始)
- [项目结构导航](#项目结构导航)
- [功能开发流程](#功能开发流程)
- [Bug修复流程](#bug修复流程)
- [包发布流程](#包发布流程)
- [测试策略](#测试策略)
- [代码质量](#代码质量)
- [CI/CD流程](#cicd流程)
- [调试技巧](#调试技巧)

## 🚀 快速开始

### 环境准备
```bash
# 1. 克隆项目
git clone <repository-url>
cd fishing-agent

# 2. 安装依赖
uv sync                    # Python依赖
cd apps/web-admin && npm install  # 前端依赖

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 添加必要的API密钥

# 4. 验证安装
uv run python -c "from packages.agents.fishing import get_all_tools; print('✅ Agent包正常')"
```

### 多端开发启动
```bash
# CLI开发
uv run fishing --help

# API服务开发
uv run fishing-api
# 或
uv run uvicorn apps.api.main:app --reload

# React前端开发
cd apps/web-admin && npm run dev

# 微信小程序开发
# 使用微信开发者工具打开 fishing_agent_app/ 目录
```

## 📁 项目结构导航

### 核心开发目录
```
fishing-agent/
├── packages/                   # 模块化包开发
│   ├── agents/                 # Agent统一目录 (v5.1.0 重构)
│   │   ├── agent_component/    # 共享组件
│   │   │   └── monitoring/     # 统一监控回调
│   │   ├── fishing/            # 钓鱼Agent包 ⭐ 核心业务
│   │   │   └── tools/
│   │   │       └── user_equipment/  # 用户装备工具
│   │   └── equipment_import/   # 装备导入Agent包 ⭐ v5.0.2新增
│   ├── data_processing/        # 数据处理包 ⭐ 图片/OCR
│   └── scraper/                # 爬虫框架包 ⭐ 数据采集
├── apps/                       # 应用层开发
│   ├── cli/                    # CLI应用
│   ├── api/                    # FastAPI后端 ⭐ REST接口
│   └── web-admin/              # React前端 ⭐ 管理界面
├── fishing_agent_app/          # 微信小程序 ⭐ v5.0.2新增
└── shared/                     # 共享资源
```

### 关键开发文件
```python
# 核心包入口 (v5.1.0 新路径)
packages/agents/fishing/__init__.py           # 钓鱼Agent包入口
packages/agents/agent_component/__init__.py # 共享组件入口
packages/agents/equipment_import/__init__.py # 装备导入Agent包入口
packages/data_processing/__init__.py         # 数据处理包入口
packages/scraper/__init__.py                 # 爬虫包入口

# 应用层入口
apps/cli/main.py                             # CLI应用入口
apps/api/main.py                             # FastAPI后端
apps/web-admin/src/App.tsx                   # React前端
fishing_agent_app/app.js                    # 微信小程序 ⭐ v5.0.2

# 项目配置
pyproject.toml                              # 项目配置
langgraph.json                              # LangGraph配置
```

## 🛠️ 功能开发流程

### Step 1: 创建功能分支
```bash
git checkout -b feature/your-feature-name
```

### Step 2: 选择开发目标

#### A. Agent包开发
```python
# 在 packages/agents/fishing/tools/ 下创建新工具
# your_new_tool.py
from langchain_core.tools import tool

@tool
def your_new_tool(param1: str, param2: int = None) -> str:
    """新工具描述，LLM会根据此描述选择使用"""
    return "工具执行结果"

# 在 tools/__init__.py 中注册
from .your_new_tool import your_new_tool

def get_all_tools():
    return [
        # 现有工具...
        your_new_tool,  # 添加新工具
    ]
```

#### B. API接口开发
```python
# 在 apps/api/routes/ 下创建路由
# your_feature.py
from fastapi import APIRouter, Depends
from packages.agents.fishing import create_agent

router = APIRouter(prefix="/api/v1/your-feature", tags=["your-feature"])

@router.post("/action")
async def your_action(
    request: YourRequest,
    current_user = Depends(get_current_user)
):
    agent = create_agent(model_provider="zhipu")
    result = agent.process_your_feature(request.data)
    return {"result": result}

# 在 apps/api/main.py 中注册路由
from .routes import your_feature_router
app.include_router(your_feature_router)
```

#### C. 前端组件开发
```typescript
// 在 apps/web-admin/src/pages/ 下创建页面
// YourFeature/index.tsx
import React from 'react';
import { Card, Button } from 'antd';

const YourFeature: React.FC = () => {
  return (
    <Card title="新功能">
      <Button>操作按钮</Button>
    </Card>
  );
};

export default YourFeature;

// 在路由中注册
// src/App.tsx 或路由配置文件
```

#### D. 微信小程序开发
```javascript
// 在 fishing_agent_app/pages/ 下创建页面
// your-feature/index.js
Page({
  data: {
    title: '新功能页面'
  },

  onLoad(options) {
    // 页面加载逻辑
  },

  onButtonClick() {
    // 按钮点击处理
  }
});

// 在 fishing_agent_app/app.json 中注册页面
{
  "pages": [
    "pages/your-feature/index"
  ]
}
```

### Step 3: 测试开发
```bash
# Python测试
uv run pytest tests/agents/fishing/test_your_tool.py

# 前端测试
cd apps/web-admin && npm test

# API测试
uv run pytest tests/api/test_your_endpoint.py
```

### Step 4: 提交代码
```bash
git add .
git commit -m "feat: 添加新功能 XXX"
git push origin feature/your-feature-name
```

## 🐛 Bug修复流程

### 定位问题
```bash
# 查看日志
tail -f logs/app.log

# 调试模式运行
uv run python debug_agent.py

# API调试
uv run uvicorn apps.api.main:app --reload --log-level debug
```

### 编写测试
```python
# tests/test_fix.py
import pytest
from packages.agents.fishing.tools.your_tool import your_new_tool

def test_your_tool_fix():
    """测试bug修复"""
    result = your_new_tool("test_input")
    assert result == "expected_output"
```

### 修复验证
```bash
# 运行相关测试
uv run pytest tests/test_fix.py -v

# 运行全量测试确保无回归
uv run pytest
```

## 📦 包发布流程

### 准备发布
```bash
# 1. 更新版本号
# packages/agents/fishing/pyproject.toml
version = "1.2.3"

# 2. 更新CHANGELOG
# packages/agents/fishing/CHANGELOG.md

# 3. 运行完整测试
uv run pytest packages/agents/fishing/tests/
```

### 发布到PyPI
```bash
cd packages/agents/fishing
uv build
uv publish --username __token__ --password your-pypi-token
```

## 🧪 测试策略

### 测试层级
```
测试金字塔:
├── 单元测试 (70%)
│   ├── 包级别测试
│   ├── 工具函数测试
│   └── 组件测试
├── 集成测试 (20%)
│   ├── API接口测试
│   ├── 数据库集成测试
│   └── 包间协作测试
└── 端到端测试 (10%)
    ├── 用户流程测试
    ├── 多端协作测试
    └── 性能测试
```

### 测试示例

#### 单元测试
```python
# tests/agents/fishing/tools/test_weather.py
import pytest
from packages.agents.fishing.tools.weather import get_weather_by_date

def test_get_weather_by_date():
    """测试天气工具"""
    result = get_weather_by_date("北京", "2024-12-20")

    assert "temperature" in result
    assert "weather" in result
    assert result["location"] == "北京"
```

#### 集成测试
```python
# tests/api/test_fishing.py
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_fishing_chat():
    """测试钓鱼对话接口"""
    response = client.post(
        "/api/v1/fishing/chat",
        json={"query": "今天适合钓鱼吗？", "model_provider": "zhipu"}
    )

    assert response.status_code == 200
    assert "response" in response.json()
    assert "status" in response.json()
```

#### 前端测试
```typescript
// apps/web-admin/src/components/__tests__/YourComponent.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import YourComponent from '../YourComponent';

test('renders component correctly', () => {
  render(<YourComponent />);
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
});
```

### 测试命令
```bash
# 运行所有测试
uv run pytest

# 运行特定包测试
uv run pytest packages/agents/fishing/tests/

# 运行覆盖率测试
uv run pytest --cov=packages.agents.fishing

# 前端测试
cd apps/web-admin && npm run test
```

## 📊 代码质量

### 代码规范

#### Python代码规范
```python
# 使用 Black 格式化
uv run black packages/ apps/

# 使用 isort 排序导入
uv run isort packages/ apps/

# 使用 flake8 检查代码质量
uv run flake8 packages/ apps/

# 使用 mypy 类型检查
uv run mypy packages/agents/fishing/
```

#### TypeScript代码规范
```bash
# 前端代码格式化
cd apps/web-admin
npm run lint          # ESLint检查
npm run format        # Prettier格式化
npm run type-check    # TypeScript类型检查
```

### 提交规范
```bash
# 提交消息格式
<type>(<scope>): <description>

# 类型说明
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式化
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动

# 示例
feat(api): 添加装备导入接口
fix(agent): 修复天气工具解析错误
docs(readme): 更新安装说明
```

## 🔄 CI/CD流程

### GitHub Actions配置
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install uv
        uv sync

    - name: Run tests
      run: uv run pytest --cov

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  frontend-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd apps/web-admin
        npm install

    - name: Run tests
      run: |
        cd apps/web-admin
        npm run test
        npm run build
```

## 🔧 调试技巧

### 后端调试
```python
# 使用pdb调试
import pdb; pdb.set_trace()

# 使用日志调试
import logging
logger = logging.getLogger(__name__)
logger.info("Debug information: %s", data)

# 使用uvicorn调试模式
uv run uvicorn apps.api.main:app --reload --log-level debug
```

### 前端调试
```typescript
// 使用console调试
console.log('Debug data:', data);

// 使用React DevTools
// 安装浏览器扩展进行组件调试

// 使用网络面板调试API请求
```

### 微信小程序调试
```javascript
// 使用console.log
console.log('Debug:', data);

// 使用微信开发者工具调试面板
// - Console: 查看日志
// - Network: 查看网络请求
// - Sources: 断点调试
```

## 📚 学习资源

### 内部文档
- [系统架构设计](../03-architecture/system-design.md)
- [API参考](../05-api-reference/)
- [部署运维指南](../04-operations/deployment-guide.md)

### 外部资源
- [LangChain官方文档](https://python.langchain.com/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [React官方文档](https://react.dev/)
- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)

---

**指南版本**: v5.1.0
**适用系统版本**: v5.1.0+
**更新时间**: 2026-01-17
