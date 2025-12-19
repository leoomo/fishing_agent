# 开发指南 v5.0.2

面向开发者的智能钓鱼助手项目开发与贡献指南。

## 📋 目录

1. [项目概览](#1-项目概览)
2. [快速开始](#2-快速开始)
3. [架构设计](#3-架构设计)
4. [开发模式](#4-开发模式)
5. [API开发](#5-api开发)
6. [测试指南](#6-测试指南)
7. [部署配置](#7-部署配置)
8. [专项开发](#8-专项开发)

## 1. 项目概览

### 核心架构
```
智能钓鱼助手 v5.0.2
├── 模块化包架构 (4个独立包)
├── 多端应用支持 (CLI/API/Web/小程序)
├── 智能处理系统 (OCR/图片合并/装备导入)
└── 现代技术栈 (LangChain 1.0+ / FastAPI / React 19)
```

### 技术栈
- **后端**: Python 3.9+, LangChain 1.0+, FastAPI, SQLAlchemy
- **前端**: React 19.2.0, TypeScript, Ant Design 5.22.0
- **AI**: 通义千问, 智谱AI, Ollama本地OCR, SiliconFlow云端OCR
- **工具**: uv包管理, pytest测试, Docker容器化

### 包结构
```
packages/                           # 模块化包
├── agent_fishing/                  # 钓鱼Agent包
├── agent_equipment_import/         # 装备导入Agent包 ⭐v5.0.2
├── data_processing/                # 数据处理包 (图片/OCR) ⭐v5.0.2
└── scraper/                        # 爬虫框架包 ⭐v5.0.2

apps/                              # 应用层
├── cli/                           # CLI应用
├── api/                           # FastAPI后端
└── web-admin/                     # React管理前端
```

## 2. 快速开始

### 环境搭建
```bash
# 1. 克隆项目
git clone <repository-url>
cd fishing-agent

# 2. 安装依赖
uv sync                    # Python依赖
cd apps/web-admin && npm install  # 前端依赖

# 3. 配置环境
cp .env.example .env
# 编辑 .env 添加API密钥 (必需: DASHSCOPE_API_KEY, CAIYUN_API_KEY, AMAP_API_KEY, JWT_SECRET_KEY)

# 4. 验证安装
uv run python -c "from packages.agent_fishing import create_agent; print('✅ OK')"
```

### 开发命令
```bash
# CLI开发
uv run fishing --help

# API服务
uv run fishing-api  # 或 uv run uvicorn apps.api.main:app --reload

# React前端
cd apps/web-admin && npm run dev

# 运行测试
uv run pytest
```

## 3. 架构设计

### 分层架构
```
Presentation Layer    ← CLI, API, Web UI, Miniprogram
Application Layer     ← Routes, Middleware, Services
Domain Layer          ← Agents, Tools, Business Logic
Infrastructure Layer ← Database, External APIs, OCR
```

### 核心组件

#### Agent Core
```python
# packages/agent_fishing/core/agent.py
class FishingAgent:
    def __init__(self, model_provider: str = "zhipu"):
        self.model = ModelFactory.create(model_provider)
        self.tools = get_all_tools()
        self.chain = self._create_chain()

    def run(self, query: str) -> str:
        # 动态Prompt选择
        prompt = DynamicPromptMiddleware.select(query)
        response = self.chain.invoke({"input": query, "tools": self.tools})
        return response["output"]
```

#### 装备导入Agent ⭐ v5.0.2
```python
# packages/agent_equipment_import/core/agent.py
class EquipmentImportAgent:
    def extract_and_save(self, text: str, source_type: str = "forum"):
        # 文本压缩 → 信息提取 → 保存待审核
        if len(text) > 2000:
            text = TextCompressor.compress(text)
        equipment_list = self._extract_equipment(text)
        return [self._save_to_pending(eq, source_type) for eq in equipment_list]
```

#### 图片处理系统 ⭐ v5.0.2
```python
# packages/data_processing/image/batch_processor.py
class BatchMergeProcessor:
    def process(self):
        # OCR文字检测 → 智能分组 → 批量合并
        images = self._get_image_list()
        merge_groups = self._detect_merge_groups(images)
        return [self._merge_group(group) for group in merge_groups]
```

## 4. 开发模式

### 添加新功能

#### 1. 新Agent包
```bash
mkdir -p packages/agent_xxx/{core,tools,utils}
# 创建 __init__.py 和核心文件
# 在 langgraph.json 中注册
```

#### 2. 新OCR提供商
```python
# packages/data_processing/ocr/providers/new_provider.py
class NewOCRProvider(BaseOCRProvider):
    async def recognize(self, image: bytes) -> OCRResult:
        # 实现OCR逻辑
        pass

# 注册到 OCR_PROVIDERS 字典
```

#### 3. 新爬虫
```python
# packages/scraper/spiders/new_spider.py
class NewSpider(BaseSpider):
    async def crawl(self, keywords: List[str]) -> List[CrawlItem]:
        # 实现爬取逻辑
        pass

# 注册到 SPIDER_REGISTRY
```

## 5. API开发

### RESTful API规范
```python
# 资源命名
GET    /api/v1/users           # 获取列表
POST   /api/v1/users           # 创建
GET    /api/v1/users/{id}      # 获取单个
PUT    /api/v1/users/{id}      # 更新
DELETE /api/v1/users/{id}      # 删除

# 嵌套资源
GET    /api/v1/users/{id}/equipment  # 用户装备
POST   /api/v1/equipment/import/csv   # 特殊操作
```

### 认证授权
```python
# 认证依赖
from apps.api.auth.dependencies import get_current_user, require_permission

@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"message": "已认证"}

@router.post("/admin")
async def admin_route(current_user = Depends(require_permission(PermissionEnum.USER_MANAGE))):
    return {"message": "管理员访问"}

# 微信登录
@router.post("/wechat/login")
async def wechat_login(request: WechatLoginRequest):
    # 验证code → 创建/获取用户 → 返回JWT
    pass
```

### 请求响应格式
```python
# Pydantic模型
class EquipmentExtractRequest(BaseModel):
    text: str = Field(..., description="要提取的文本")
    source_type: str = Field(..., description="来源类型")
    enable_compression: bool = Field(True, description="启用文本压缩")

class EquipmentExtractResponse(BaseModel):
    success: bool
    extracted_count: int
    results: List[EquipmentInfo]
    compression_stats: Optional[CompressionStats] = None
```

## 6. 测试指南

### 单元测试
```python
# tests/test_equipment_import.py
class TestEquipmentImportAgent:
    def test_extract_single_equipment(self):
        agent = EquipmentImportAgent(model_provider="test")
        text = "光威赤刃 GT602L-M 路亚竿，碳纤维材质，价格299元"
        result = agent.extract_and_save(text=text, source_type="forum")

        assert len(result) == 1
        assert result[0].data["brand"] == "光威"
        assert result[0].data["model"] == "赤刃 GT602L-M"
```

### API测试
```python
# tests/test_ocr_api.py
client = TestClient(app)

def test_recognize_table_success(self):
    token = self._get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    with open("tests/fixtures/table.jpg", "rb") as f:
        response = client.post(
            "/api/v1/ocr/recognize-table",
            headers=headers,
            files={"files": ("table.jpg", f, "image/jpeg")}
        )

    assert response.status_code == 200
    assert "|" in response.json()["markdown"]  # Markdown格式
```

### 运行测试
```bash
# 所有测试
uv run pytest

# 特定包测试
uv run pytest packages/agent_fishing/tests/

# 覆盖率报告
uv run pytest --cov=packages.agent_fishing

# 性能测试
uv run pytest tests/performance/ -v
```

## 7. 部署配置

### Docker部署
```dockerfile
# Dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/ apps/ shared/ ./
RUN uv sync --frozen

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - CAIYUN_API_KEY=${CAIYUN_API_KEY}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - OCR_PROVIDER=ollama
    depends_on: [redis, ollama]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  ollama:
    image: ollama/ollama
    ports: ["11434:11434"]
    environment:
      - OLLAMA_KEEP_ALIVE=24h

  web:
    image: node:18-alpine
    working_dir: /app
    ports: ["5173:5173"]
    volumes: ["./apps/web-admin:/app"]
    command: npm run dev
```

### 生产优化
```python
# 性能配置
class Settings:
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    MAX_CONNECTIONS: int = int(os.getenv("MAX_CONNECTIONS", "100"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    OCR_TIMEOUT: int = int(os.getenv("OCR_TIMEOUT", "30"))
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
```

## 8. 专项开发

### 微信小程序开发 ⭐ v5.0.2

#### API封装
```javascript
// miniprogram/utils/api.js
class API {
  request(options) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${app.globalData.baseURL}${options.url}`,
        method: options.method || 'GET',
        header: {
          'Authorization': app.globalData.token
            ? `Bearer ${app.globalData.token}`
            : undefined
        },
        success: resolve,
        fail: reject
      });
    });
  }

  // 钓鱼推荐
  getFishingRecommendation(query) {
    return this.request({
      url: '/api/v1/fishing/chat',
      method: 'POST',
      data: { query, model_provider: 'zhipu' }
    });
  }

  // OCR识别
  recognizeTable(filePath) {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${app.globalData.baseURL}/api/v1/ocr/recognize-table`,
        filePath,
        name: 'files',
        header: { 'Authorization': `Bearer ${app.globalData.token}` },
        success: (res) => resolve(JSON.parse(res.data)),
        fail: reject
      });
    });
  }
}
```

### OCR功能开发 ⭐ v5.0.2

#### 多提供商支持
```python
# packages/data_processing/ocr/ocr_processor.py
class OCRMergeProcessor:
    def __init__(self, provider: str = "ollama"):
        self.provider = provider
        self.client = self._create_client()

    def _create_client(self):
        if self.provider == "ollama":
            return OllamaOCRClient()
        elif self.provider == "siliconflow":
            return SiliconFlowOCRClient()
        # 可扩展其他提供商

    async def recognize_table(self, images: List[str]) -> str:
        # 预处理 → 文字检测 → OCR识别 → Markdown转换
        processed_images = await self._preprocess_images(images)
        table_data = await self._extract_table_data(processed_images)
        return self._convert_to_markdown(table_data)
```

#### 结果后处理
```python
class OCRPostProcessor:
    def enhance_accuracy(self, text: str) -> str:
        # 修正常见OCR错误
        corrections = {"O": "0", "l": "1", "I": "1"}
        for wrong, correct in corrections.items():
            text = re.sub(rf'(?<=\d){wrong}(?=\d)', correct, text)
        return text

    def process_table_result(self, raw_result: Dict) -> str:
        # 转换表格结果为Markdown格式
        table = raw_result.get("tables_result", [{}])[0]
        return self._convert_to_markdown(table)
```

### 装备导入开发 ⭐ v5.0.2

#### 自定义提取器
```python
# packages/agent_equipment_import/core/extractors/custom_extractor.py
class CustomExtractor:
    def __init__(self):
        self.brands = {"光威", "达亿瓦", "禧玛诺", "阿布", "Shimano", "Daiwa"}
        self.categories = {
            "路亚竿": ["竿", "路亚竿"],
            "纺车轮": ["轮", "纺车轮"],
            "拟饵": ["饵", "拟饵", "crank", "minnow"]
        }

    def extract(self, text: str) -> List[Dict]:
        # 分段处理 → 品牌识别 → 型号提取 → 价格解析 → 规格提取
        segments = self._split_segments(text)
        equipment_list = []

        for segment in segments:
            equipment = {
                "brand": self._extract_brand(segment),
                "model": self._extract_model(segment),
                "category": self._detect_category(segment),
                "price": self._extract_price(segment),
                "specs": self._extract_specs(segment)
            }
            if equipment["brand"] or equipment["model"]:
                equipment_list.append(equipment)

        return equipment_list

    def _extract_price(self, text: str) -> float:
        patterns = [r'￥(\d+\.?\d*)', r'(\d+)元', r'\$(\d+\.?\d*)']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return 0.0
```

## 🚀 下一步

1. **阅读架构文档**: [ARCHITECTURE.md](./ARCHITECTURE.md) - 深入理解系统设计
2. **查看API参考**: [API_REFERENCE.md](./API_REFERENCE.md) - 了解所有接口
3. **运行测试**: `uv run pytest` - 开始测试开发环境
4. **创建贡献**: 提交Issue或Pull Request开始贡献代码

## 📚 相关资源

- [LangChain文档](https://python.langchain.com/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [React文档](https://react.dev/)
- [微信小程序开发](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [uv包管理器](https://docs.astral.sh/uv/)
- [Ollama文档](https://ollama.com/documentation)

---

**版本**: v5.0.2
**更新**: 2024-12-20
**维护**: 智能钓鱼助手开发团队