# 开发指南

本指南面向开发者，介绍如何参与智能钓鱼助手项目的开发和贡献。

## 目录

- [项目结构](#项目结构)
- [开发环境搭建](#开发环境搭建)
- [架构设计](#架构设计)
- [添加新功能](#添加新功能)
- [API 开发规范](#api-开发规范)
- [测试指南](#测试指南)
- [部署指南](#部署指南)
- [贡献流程](#贡献流程)

## 项目结构

```
fishing_agent/
├── packages/                    # 核心功能包
│   └── agent_fishing/          # 智能钓鱼Agent包
│       ├── __init__.py         # 包入口
│       ├── core/               # 核心模块
│       │   ├── agent.py        # Agent实现
│       │   ├── model_factory.py # 模型工厂
│       │   ├── prompts.py      # Prompt模板
│       │   ├── callbacks.py    # 回调处理
│       │   └── middleware/     # 中间件
│       │       └── dynamic_prompt.py # 动态Prompt
│       ├── tools/              # 工具模块
│       │   ├── basic/          # 基础工具
│       │   ├── weather/        # 天气工具
│       │   ├── fishing/        # 钓鱼工具
│       │   ├── lure_tools.py   # 装备工具
│       │   ├── lure/           # 装备数据
│       │   └── scoring/        # 评分系统
│       └── utils/              # 工具函数
├── apps/                       # 应用层
│   ├── cli/                    # CLI应用
│   │   └── main.py            # CLI入口
│   ├── api/                    # FastAPI应用
│   │   ├── main.py            # API服务器
│   │   ├── auth/              # 认证模块
│   │   ├── middleware/        # 中间件
│   │   ├── routes/            # API路由
│   │   ├── schemas/           # 数据模型
│   │   └── services/          # 业务服务
│   └── web-admin/             # React管理前端
│       ├── src/               # 源代码
│       ├── public/            # 静态资源
│       └── package.json       # 前端配置
├── shared/                     # 共享资源
│   ├── config/                 # 全局配置
│   └── data/                   # 共享数据
├── tests/                      # 测试文件
├── docs/                       # 文档
├── scripts/                    # 脚本工具
├── pyproject.toml             # 项目配置
└── README.md                  # 项目说明
```

## 开发环境搭建

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/fishing-agent.git
cd fishing-agent
```

### 2. 创建开发环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装uv（如果没有）
pip install uv

# 安装开发依赖
uv sync --dev
```

### 3. 配置开发环境

```bash
# 复制开发配置
cp .env.example .env
cp .env.example .env.dev

# 编辑开发配置
# 设置测试用的API密钥
# 启用调试模式
```

### 4. 安装pre-commit钩子

```bash
# 安装pre-commit
pip install pre-commit

# 安装钩子
pre-commit install
```

### 5. 验证环境

```bash
# 运行测试
uv run pytest tests/

# 运行代码检查
uv run flake8 packages/
uv run mypy packages/

# 测试导入
uv run python -c "from packages.agent_fishing import create_agent; print('✅ 环境配置成功')"
```

## 架构设计

### 分层架构

```
┌─────────────────────────────────────┐
│          Presentation Layer         │  ← CLI, API, Web UI
├─────────────────────────────────────┤
│         Application Layer           │  ← Routes, Middleware
├─────────────────────────────────────┤
│          Domain Layer              │  ← Agent, Tools, Services
├─────────────────────────────────────┤
│        Infrastructure Layer        │  ← Database, External APIs
└─────────────────────────────────────┘
```

### 核心组件

#### 1. Agent Core

```python
# packages/agent_fishing/core/agent.py
class FishingAgent:
    """智能钓鱼Agent核心类"""

    def __init__(self, model_provider: str = "zhipu"):
        self.model_provider = model_provider
        self.model = ModelFactory.create(model_provider)
        self.tools = get_all_tools()
        self.chain = self._create_chain()

    def run(self, query: str) -> str:
        """运行Agent查询"""
        # 动态Prompt选择
        prompt = DynamicPromptMiddleware.select(query)

        # 执行Chain
        response = self.chain.invoke({
            "input": query,
            "tools": self.tools,
            "prompt": prompt
        })

        return response["output"]
```

#### 2. Tool System

```python
# packages/agent_fishing/tools/base.py
from langchain.tools import tool

@tool
def get_weather(location: str, time: str) -> dict:
    """
    获取天气信息

    Args:
        location: 地点名称
        time: 时间描述

    Returns:
        dict: 天气数据
    """
    # 实现逻辑
```

#### 3. Scoring System

```python
# packages/agent_fishing/tools/scoring/scorer.py
class FishingScorer:
    """7因子评分系统"""

    def __init__(self):
        self.weights = {
            'temperature': 0.25,
            'weather': 0.20,
            'wind': 0.15,
            'pressure': 0.15,
            'humidity': 0.10,
            'season': 0.05,
            'moon_phase': 0.05
        }

    def calculate_score(self, weather_data: dict, time_info: dict) -> float:
        """计算综合评分"""
        scores = {}

        # 各因子评分
        scores['temperature'] = self._score_temperature(weather_data['temp'])
        scores['weather'] = self._score_weather(weather_data['condition'])
        scores['wind'] = self._score_wind(weather_data['wind_speed'])
        scores['pressure'] = self._score_pressure(weather_data['pressure'])
        scores['humidity'] = self._score_humidity(weather_data['humidity'])
        scores['season'] = self._score_season(time_info['month'])
        scores['moon_phase'] = self._score_moon_phase(time_info['moon_phase'])

        # 加权计算
        total_score = sum(scores[factor] * weight
                          for factor, weight in self.weights.items())

        # 特殊加成
        if self._is_pressure_dropping_fast(weather_data):
            total_score = min(100, total_score + 20)

        return total_score
```

## 添加新功能

### 1. 添加新的工具

#### Step 1: 创建工具文件

```python
# packages/agent_fishing/tools/new_feature.py
from langchain.tools import tool
from typing import Dict, Any

@tool
def new_tool_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    新工具的描述

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        Dict: 返回值说明
    """
    # 实现逻辑
    result = {
        "status": "success",
        "data": f"处理 {param1} 和 {param2}"
    }
    return result
```

#### Step 2: 注册工具

```python
# packages/agent_fishing/tools/__init__.py
from .new_feature import new_tool_function

def get_all_tools():
    tools = [
        # 现有工具...
        new_tool_function,  # 添加新工具
    ]
    return tools
```

#### Step 3: 添加测试

```python
# tests/tools/test_new_feature.py
import pytest
from packages.agent_fishing.tools.new_feature import new_tool_function

def test_new_tool_function():
    """测试新工具"""
    result = new_tool_function("test", 123)

    assert result["status"] == "success"
    assert "test" in result["data"]
```

### 2. 添加新的API端点

#### Step 1: 定义数据模型

```python
# apps/api/schemas/new_feature.py
from pydantic import BaseModel
from typing import Optional

class NewFeatureRequest(BaseModel):
    """新功能请求模型"""
    name: str
    description: Optional[str] = None

class NewFeatureResponse(BaseModel):
    """新功能响应模型"""
    id: int
    name: str
    created_at: datetime
```

#### Step 2: 创建路由

```python
# apps/api/routes/new_feature.py
from fastapi import APIRouter, Depends, HTTPException
from apps.api.schemas.new_feature import NewFeatureRequest, NewFeatureResponse
from apps.api.auth import get_current_user
from apps.api.services.new_feature_service import NewFeatureService

router = APIRouter(prefix="/api/v1/new-feature", tags=["new-feature"])

@router.post("/", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    current_user = Depends(get_current_user)
):
    """创建新功能"""
    service = NewFeatureService()
    return await service.create(request, current_user.id)

@router.get("/{feature_id}", response_model=NewFeatureResponse)
async def get_new_feature(
    feature_id: int,
    current_user = Depends(get_current_user)
):
    """获取新功能"""
    service = NewFeatureService()
    feature = await service.get_by_id(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="功能不存在")
    return feature
```

#### Step 3: 注册路由

```python
# apps/api/main.py
from apps.api.routes.new_feature import router as new_feature_router

app.include_router(new_feature_router)
```

### 3. 添加新的前端页面

#### Step 1: 创建页面组件

```typescript
// apps/web-admin/src/pages/NewFeature/index.tsx
import React from 'react';
import { Card, Table, Button, Space } from 'antd';
import { useFetchData } from '@/hooks/useFetchData';

const NewFeature: React.FC = () => {
  const { data, loading, refresh } = useFetchData('/api/v1/new-feature');

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link">编辑</Button>
          <Button type="link" danger>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <Card title="新功能管理">
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
      />
    </Card>
  );
};

export default NewFeature;
```

#### Step 2: 添加路由

```typescript
// apps/web-admin/src/routes/index.tsx
import NewFeature from '../pages/NewFeature';

export const routes = [
  // ... 现有路由
  {
    path: '/new-feature',
    component: NewFeature,
    title: '新功能',
  },
];
```

## API 开发规范

### 1. RESTful API 设计

```python
# 资源命名使用复数
GET    /api/v1/users          # 获取用户列表
POST   /api/v1/users          # 创建用户
GET    /api/v1/users/{id}     # 获取特定用户
PUT    /api/v1/users/{id}     # 更新用户
DELETE /api/v1/users/{id}     # 删除用户

# 嵌套资源
GET    /api/v1/users/{id}/equipment    # 获取用户的装备
POST   /api/v1/users/{id}/equipment    # 为用户添加装备
```

### 2. 状态码使用

```python
# 成功响应
200 OK          # 请求成功
201 Created     # 创建成功
204 No Content  # 删除成功

# 客户端错误
400 Bad Request     # 请求参数错误
401 Unauthorized    # 未认证
403 Forbidden       # 权限不足
404 Not Found       # 资源不存在
422 Unprocessable Entity  # 数据验证失败

# 服务器错误
500 Internal Server Error  # 服务器内部错误
503 Service Unavailable    # 服务不可用
```

### 3. 响应格式

```python
# 成功响应
{
  "data": {
    "id": 1,
    "name": "test"
  },
  "meta": {
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}

# 错误响应
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "数据验证失败",
    "details": {
      "field": "email",
      "reason": "格式不正确"
    }
  }
}
```

### 4. 认证和授权

```python
# 使用JWT认证
from apps.api.auth import get_current_user, require_permissions

@router.get("/protected")
async def protected_route(
    current_user = Depends(get_current_user)
):
    """需要登录的路由"""
    return {"message": "已认证"}

@router.post("/admin")
async def admin_route(
    current_user = Depends(require_permissions(["admin"]))
):
    """需要管理员权限的路由"""
    return {"message": "管理员访问"}
```

## 测试指南

### 1. 单元测试

```python
# tests/test_agent.py
import pytest
from packages.agent_fishing import create_agent

class TestFishingAgent:
    def setup_method(self):
        """每个测试方法前执行"""
        self.agent = create_agent(model_provider="test")

    def test_basic_query(self):
        """测试基础查询"""
        response = self.agent.run("今天天气怎么样？")
        assert "天气" in response
        assert len(response) > 0

    def test_fishing_recommendation(self):
        """测试钓鱼推荐"""
        response = self.agent.run("明天北京钓鱼怎么样？")
        assert "北京" in response
        assert "钓鱼" in response
```

### 2. API 测试

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

class TestAPI:
    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_login(self):
        """测试登录"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_protected_route(self):
        """测试受保护的路由"""
        # 先登录获取token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json()["access_token"]

        # 使用token访问
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
```

### 3. 集成测试

```python
# tests/test_integration.py
import pytest
from packages.agent_fishing import create_agent
from packages.agent_fishing.tools import get_weather

class TestIntegration:
    def test_weather_integration(self):
        """测试天气集成"""
        # 测试天气工具
        weather = get_weather("北京", "今天")
        assert weather is not None
        assert hasattr(weather, 'temperature')

        # 测试Agent使用天气
        agent = create_agent()
        response = agent.run("北京今天钓鱼怎么样？")
        assert "北京" in response
        assert "温度" in response or "天气" in response
```

### 4. 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_agent.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=packages --cov-report=html

# 运行性能测试
uv run pytest tests/performance/
```

## 部署指南

### 1. Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync --frozen

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CAIYUN_API_KEY=${CAIYUN_API_KEY}
      - AMAP_API_KEY=${AMAP_API_KEY}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    volumes:
      - ./data:/app/data

  web:
    image: node:18-alpine
    working_dir: /app
    ports:
      - "5173:5173"
    volumes:
      - ./apps/web-admin:/app
    command: npm run dev
```

### 2. 生产环境配置

```python
# apps/api/config.py
import os
from typing import Optional

class Settings:
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "智能钓鱼助手"

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # JWT配置
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS配置
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:5173",
        "https://admin.fishing.com"
    ]

    # 环境配置
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
```

### 3. 性能优化

```python
# apps/api/middleware/performance.py
from fastapi import Request, Response
import time
import logging

logger = logging.getLogger(__name__)

async def add_performance_headers(request: Request, call_next):
    """添加性能相关头部"""
    start_time = time.time()

    response = await call_next(request)

    # 计算处理时间
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # 记录慢查询
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} "
            f"took {process_time:.2f}s"
        )

    return response
```

## 贡献流程

### 1. Fork 项目

1. 在 GitHub 上 Fork 项目
2. Clone 你的 Fork
   ```bash
   git clone https://github.com/yourusername/fishing-agent.git
   ```

### 2. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

### 3. 开发和测试

1. 编写代码
2. 添加测试
3. 运行所有测试确保通过
   ```bash
   uv run pytest
   ```
4. 运行代码检查
   ```bash
   uv run flake8 packages/
   uv run mypy packages/
   ```

### 4. 提交代码

```bash
# 添加文件
git add .

# 提交（使用有意义的提交信息）
git commit -m "feat: 添加新的天气预警功能

- 实现恶劣天气预警
- 添加推送通知功能
- 更新相关测试"
```

### 5. 推送和 PR

```bash
# 推送到你的 Fork
git push origin feature/your-feature-name

# 在 GitHub 上创建 Pull Request
```

### 6. 代码审查

1. 等待代码审查
2. 根据反馈修改代码
3. 通过审查后合并

### 7. 版本发布

```bash
# 更新版本号
# pyproject.toml
version = "x.y.z"

# 创建标签
git tag -a v5.1.0 -m "Release version 5.1.0"

# 推送标签
git push origin v5.1.0
```

## 编码规范

### Python 规范

- 使用 Black 格式化代码
- 使用 flake8 进行代码检查
- 使用 type hints
- 文档字符串使用 Google 风格

```python
def calculate_score(
    temperature: float,
    humidity: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """计算综合评分。

    Args:
        temperature: 温度值（摄氏度）
        humidity: 湿度值（百分比）
        weights: 可选的权重字典

    Returns:
        0-100之间的评分

    Example:
        >>> calculate_score(25.0, 60.0)
        85.5
    """
    pass
```

### TypeScript 规范

- 使用 Prettier 格式化代码
- 使用 ESLint 进行代码检查
- 严格的类型定义

```typescript
interface WeatherData {
  temperature: number;
  humidity: number;
  condition: string;
}

const processWeather = (data: WeatherData): string => {
  return `当前温度${data.temperature}°C`;
};
```

## 更多资源

- [LangChain 文档](https://python.langchain.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Ant Design 文档](https://ant.design/)

---

欢迎贡献代码！🚀