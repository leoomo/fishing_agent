# 架构设计文档

欢迎来到智能钓鱼助手架构设计文档！本部分面向系统架构师、技术负责人和高级开发者，深入阐述系统的设计理念、技术架构和关键决策。

## 📋 文档内容

### 🏗️ [系统设计](./system-design.md)
- 整体架构概览
- 核心设计原则
- 技术选型决策
- 架构演进历程

### 🔧 [模块架构](./module-architecture.md)
- 模块化设计详解
- 包间依赖关系
- 接口设计规范
- 扩展性设计

### 🗄️ [数据库设计](./database-schema.md)
- 数据模型设计
- 关系结构说明
- 性能优化策略
- 数据迁移方案

### 🔐 [安全架构](./security-design.md)
- JWT认证系统
- 权限控制设计
- 数据安全措施
- 安全最佳实践

### 📈 [可扩展性](./scalability.md)
- 水平扩展策略
- 性能瓶颈分析
- 负载均衡设计
- 监控和调优

### 📝 [设计决策](./design-decisions.md)
- 重要架构决策记录
- 技术选型分析
- 设计权衡说明
- 未来规划方向

## 🎯 架构概览

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层                              │
├───────────┬───────────┬───────────┬─────────────────────┤
│    CLI    │   Web UI  │   小程序   │      API客户端        │
└───────────┴───────────┴───────────┴─────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    应用服务层                              │
├───────────┬───────────┬───────────┬─────────────────────┤
│ FastAPI   │   中间件   │   路由     │      业务服务         │
│  服务     │  (认证/    │  管理     │     (Service)        │
│           │  CORS)     │           │                      │
└───────────┴───────────┴───────────┴─────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    领域层                                 │
├───────────┬───────────┬───────────┬─────────────────────┤
│ 钓鱼Agent  │ 装备导入   │ 数据处理   │     爬虫框架         │
│(fishing/) │(equipment_│   系统    │  (Master-Worker)     │
│           │  import/) │           │                      │
└───────────┴───────────┴───────────┴─────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                  OCR工作流系统                            │
├───────────┬───────────┬───────────┬─────────────────────┤
│ 图片合并   │ 文字检测   │ OCR识别    │      结果处理        │
│ ImageMerger│TextRegion │ Provider  │    PostProcess      │
└───────────┴───────────┴───────────┴─────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                  基础设施层                               │
├───────────┬───────────┬───────────┬─────────────────────┤
│   数据库   │   缓存     │  外部API  │     OCR服务          │
│ (SQLite/  │  (Redis)   │ (天气/地图)│   (Ollama/云)       │
│PostgreSQL)│           │           │                      │
└───────────┴───────────┴───────────┴─────────────────────┘
```

### 核心架构原则

1. **模块化包架构**
   - 每个包独立可发布
   - 清晰的依赖边界
   - 最小化包间耦合

2. **Agent驱动设计**
   - 基于LangChain的智能体
   - 工具化功能封装
   - 动态Prompt选择

3. **API优先策略**
   - RESTful API设计
   - 多端统一接口
   - 版本化API管理

4. **数据驱动决策**
   - 7因子科学评分
   - 实时数据分析
   - 机器学习优化

## 🏛️ 技术架构栈

### 后端技术栈
- **Python 3.11+**: 主要开发语言
- **LangChain 1.0+**: AI Agent框架
- **FastAPI**: 高性能Web框架
- **SQLAlchemy**: ORM数据访问
- **Pydantic**: 数据验证和序列化
- **uv**: 现代包管理工具

### 前端技术栈
- **React 19.2.0**: 用户界面框架
- **TypeScript**: 类型安全的JavaScript
- **Ant Design 5.22.0**: 企业级UI组件库
- **Vite**: 快速构建工具
- **React Router**: 路由管理
- **Zustand**: 轻量状态管理

### 基础设施
- **SQLite**: 开发和测试数据库
- **PostgreSQL**: 生产数据库
- **Redis**: 缓存和会话存储
- **Docker**: 容器化部署
- **Nginx**: 反向代理和负载均衡

### AI和数据处理
- **通义千问**: 大语言模型服务
- **智谱AI**: GLM-4.6模型
- **Ollama**: 本地OCR模型
- **SiliconFlow**: 云端OCR服务
- **彩云天气**: 气象数据API
- **高德地图**: 地理位置服务

## 🔧 关键设计模式

### 1. Agent模式
```python
# 智能体为核心的设计
class FishingAgent:
    def __init__(self, model_provider: str):
        self.model = ModelFactory.create(model_provider)
        self.tools = get_all_tools()
        self.chain = self._create_chain()
    
    def run(self, query: str) -> str:
        # 动态选择工具和策略
        return self.chain.invoke({"input": query})
```

### 2. 工厂模式
```python
# 模型和OCR提供商工厂
class ModelFactory:
    @staticmethod
    def create(provider: str) -> BaseLLM:
        return MODEL_REGISTRY[provider]()

class OCRFactory:
    @staticmethod
    def create(provider: str) -> BaseOCRProvider:
        return OCR_PROVIDERS[provider]()
```

### 3. 策略模式
```python
# 动态选择处理策略
class PromptSelector:
    @staticmethod
    def select(query: str) -> str:
        if "钓鱼" in query:
            return FISHING_PROMPT
        elif "天气" in query:
            return WEATHER_PROMPT
        return BASE_PROMPT
```

### 4. Master-Worker模式 (分布式爬虫)
```python
# 分布式爬虫架构
class MasterNode:
    def __init__(self):
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.workers = []

    def distribute_tasks(self, tasks: List[CrawlItem]):
        for task in tasks:
            self.task_queue.put(task)

    def collect_results(self) -> List[CrawlResult]:
        results = []
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        return results

class WorkerNode:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.spider = self._init_spider()

    def process_task(self, task: CrawlItem) -> CrawlResult:
        return self.spider.crawl(task)

    def run(self, task_queue: Queue, result_queue: Queue):
        while True:
            task = task_queue.get()
            result = self.process_task(task)
            result_queue.put(result)
```

### 5. 工作流模式 (OCR系统)
```python
# OCR工作流管道
class OCRWorkflow:
    def __init__(self):
        self.merger = ImageMerger()
        self.detector = TextRegionDetector()
        self.ocr = OCRFactory.create()
        self.post_processor = PostProcessor()

    def execute(self, images: List[Image]) -> OCRResult:
        # 1. 图片合并
        merged = self.merger.merge(images)

        # 2. 文字区域检测
        regions = self.detector.detect(merged)

        # 3. OCR识别
        texts = self.ocr.recognize(regions)

        # 4. 后处理
        result = self.post_processor.process(texts)
        return result
```

## 📊 数据流架构

### 请求处理流程
```
用户请求 → API网关 → 认证中间件 → 路由分发 → 业务服务
    ↓
智能Agent → 工具选择 → 外部API调用 → 数据处理 → 结果聚合
    ↓
响应格式化 → 缓存存储 → 返回用户
```

### 数据流向
```
用户输入 → 预处理 → Agent处理 → 工具执行 → 结果整合 → 输出格式化
    ↑           ↑           ↑           ↑           ↑           ↑
  历史记录   参数验证   Prompt选择   API调用   数据聚合   缓存更新
```

## 🕷️ 分布式爬虫架构

### Master-Worker模式设计

```
┌─────────────────────────────────────────────────────────┐
│                    Master节点                            │
├───────────┬───────────┬───────────┬─────────────────────┤
│  任务调度   │  结果聚合   │  状态监控   │     故障恢复         │
│ Scheduler │  Aggregator│  Monitor   │    Recovery         │
└───────────┴───────────┴───────────┴─────────────────────┘
         │                   │                   │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │ 任务队列  │         │ 结果队列  │         │ 状态队列  │
    └─────────┘         └─────────┘         └─────────┘
         │                   │                   │
┌────────┼────────┬────────┼────────┬────────┼────────┐
│        │        │        │        │        │        │
▼        ▼        ▼        ▼        ▼        ▼        ▼
Worker1  Worker2  Worker3  Worker4  Worker5  WorkerN  ...
└────────┴────────┴────────┴────────┴────────┴────────┘
```

### 核心组件

1. **Master节点职责**
   - 任务分发和调度
   - Worker状态监控
   - 结果聚合和去重
   - 故障检测和恢复

2. **Worker节点职责**
   - 从任务队列获取任务
   - 执行具体爬虫逻辑
   - 上报执行结果
   - 心跳保活机制

3. **队列系统**
   - 任务队列 (Task Queue)
   - 结果队列 (Result Queue)
   - 延迟队列 (Delayed Queue)
   - 死信队列 (Dead Letter Queue)

### 分布式爬虫包结构
```
packages/scraper/
├── spider/              # 爬虫核心
│   ├── base.py         # BaseSpider基类
│   └── item.py         # CrawlItem数据模型
├── spiders/            # 具体爬虫实现
│   ├── taobao.py       # 淘宝爬虫
│   ├── jd.py           # 京东爬虫
│   └── forum.py        # 论坛爬虫
├── rpa/                # RPA自动化框架
│   └── taobao_rpa.py   # 淘宝RPA
├── platform/           # 平台抽象层
│   └── base_platform.py
├── workflow/           # 工作流引擎
│   └── workflow_manager.py
├── executor/           # 任务执行器
│   └── task_executor.py
├── monitoring/         # 监控告警
│   └── crawler_monitor.py
├── scheduler/          # 定时调度
│   └── task_scheduler.py
├── persister/          # 数据持久化
│   └── result_persister.py
└── models/             # 独立的爬虫模型
    └── crawl_models.py
```

## 🖼️ OCR工作流系统

### 工作流管道架构

```
输入图片
    │
    ▼
┌─────────────────┐
│   图片预处理     │  → 尺寸调整、格式转换、质量优化
│  ImageMerger    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   文字区域检测   │  → 检测文字区域、过滤无关区域
│ TextRegion      │
│  Detector       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   OCR识别        │  → 支持多提供商 (Ollama/SiliconFlow)
│  OCRProvider    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   结果后处理     │  → 文字校正、格式化、结构化
│ PostProcessor   │
└────────┬────────┘
         │
         ▼
    输出结果
```

### OCR系统包结构
```
packages/data_processing/
├── image/              # 图片处理模块
│   ├── merger.py       # ImageMerger图片合并
│   └── batch_merger.py # BatchMergeProcessor批量处理
├── ocr/                # OCR识别模块
│   ├── detector.py     # TextRegionDetector文字检测
│   ├── processor.py    # OCRMergeProcessor处理器
│   └── providers/      # OCR提供商
│       ├── base.py     # BaseOCRProvider基类
│       ├── ollama.py   # Ollama本地OCR
│       └── silicon.py  # SiliconFlow云端OCR
└── dedup/              # 去重工具
    └── deduplicator.py # Deduplicator去重器
```

### 工作流特性

1. **模块化设计**
   - 每个处理步骤独立可配置
   - 支持自定义处理器
   - 易于扩展和测试

2. **多提供商支持**
   - 本地OCR (Ollama)
   - 云端OCR (SiliconFlow)
   - 自动降级策略
   - 负载均衡

3. **批量处理**
   - 支持多图片合并
   - 并行处理优化
   - 错误恢复机制

## 🔒 安全架构

### 认证和授权
- **JWT Token**: 无状态认证
- **RBAC权限**: 基于角色的访问控制
- **API密钥**: 服务间认证
- **OAuth 2.0**: 第三方集成

### 数据安全
- **传输加密**: HTTPS/TLS
- **存储加密**: 敏感数据加密
- **访问控制**: 细粒度权限管理
- **审计日志**: 操作记录追踪

## 📈 性能优化

### 缓存策略
```
缓存层次:
├── L1: 内存缓存 (应用内, TTL: 5分钟)
├── L2: Redis缓存 (分布式, TTL: 1小时)
└── L3: 数据库缓存 (持久化, TTL: 24小时)
```

### 异步处理
- **FastAPI异步**: 支持高并发请求
- **后台任务**: 处理耗时操作
- **消息队列**: 任务解耦和削峰
- **批量处理**: 提高数据处理效率

## 🔮 扩展性设计

### 水平扩展
- **无状态设计**: 服务可任意扩展
- **负载均衡**: 多实例部署
- **数据库分片**: 支持大规模数据
- **微服务拆分**: 按业务域分离

### 垂直扩展
- **资源优化**: CPU/内存/IO调优
- **算法优化**: 提升处理效率
- **缓存策略**: 减少重复计算
- **数据压缩**: 降低存储和传输成本

## 📚 架构演进

### 当前架构 (v5.0.2)
- ✅ 模块化包架构
- ✅ JWT认证系统
- ✅ 多端支持
- ✅ OCR多提供商
- ✅ 微信小程序集成

### 规划演进 (v6.0.0)
- 🔄 微服务架构重构
- 🔄 事件驱动架构
- 🔄 机器学习平台
- 🔄 多租户支持
- 🔄 国际化支持

## 🔗 相关资源

### 内部文档
- [代码结构](../02-developer-guide/codebase-structure.md) - 详细代码组织
- [开发工作流](../02-developer-guide/development-workflows.md) - 开发流程指南
- [API参考](../05-api-reference/) - 完整API文档
- [部署指南](../04-operations/deployment-guide.md) - 生产部署方案

### 外部资源
- [LangChain架构指南](https://python.langchain.com/docs/modules/)
- [FastAPI最佳实践](https://fastapi.tiangolo.com/tutorial/advanced/)
- [React架构模式](https://react.dev/learn/thinking-in-react)
- [微服务设计模式](https://microservices.io/patterns/)

---

## 🎯 适用人群

### 主要受众
- **系统架构师**: 负责整体架构设计和技术选型
- **技术负责人**: 把握技术方向和团队技术决策
- **高级开发者**: 深入理解系统设计和实现细节
- **DevOps工程师**: 了解系统部署和运维架构

### 阅读建议
1. **新手入门**: 从系统设计开始，了解整体架构
2. **深入理解**: 阅读模块架构和数据库设计
3. **安全考虑**: 重点阅读安全架构部分
4. **性能优化**: 关注可扩展性和性能调优
5. **决策参考**: 查看设计决策了解技术选择

---

**文档版本**: v5.0.2  
**适用系统版本**: v5.0.2+  
**更新时间**: 2024-12-20  
**维护团队**: 智能钓鱼助手架构团队