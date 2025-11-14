# 模块依赖关系图

## 架构概览

本项目采用分层架构设计，各模块之间依赖关系清晰，便于维护和扩展。

## 模块层次结构

```
┌─────────────────────────────────────────────────────────────────┐
│                        应用层                                    │
├─────────────────────────────────────────────────────────────────┤
│                        agents/                                   │
│                     (智能体层)                                  │
│  • ModernAgent           • AgentFactory                        │
│  • AgentManager         • AgentConfig                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 依赖
┌─────────────────────────────────────────────────────────────────┐
│                        tools/                                    │
│                      (工具层)                                     │
│  • TimeTool             • MathTool                            │
│  • WeatherTool          • SearchTool                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 依赖
┌─────────────────────────────────────────────────────────────────┐
│                      services/                                  │
│                    (服务层)                                       │
│  • WeatherService       • LocationService                    │
│  • CacheService         • DatabaseService                     │
│  • ServiceManager       • ServiceRegistry                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 依赖
┌─────────────────────────────────────────────────────────────────┐
│                       core/                                       │
│                  (核心基础设施层)                                    │
│  • ITool/IAgent/IService • BaseTool/BaseAgent/BaseService       │
│  • ToolRegistry         • ServiceRegistry                     │
│  • 接口定义              • 基础实现类                         │
└─────────────────────────────────────────────────────────────────┘
```

## 详细依赖关系

### 1. 核心模块 (core/)

**职责**: 提供系统的基础设施和接口定义

**包含组件**:
- `interfaces.py` - 接口定义 (ITool, IAgent, IService)
- `registry.py` - 注册器实现 (ToolRegistry, ServiceRegistry)
- `base_tool.py` - 工具基类 (BaseTool, ConfigurableTool, AsyncTool)
- `base_agent.py` - 智能体基类 (BaseAgent, ConfigurableAgent)
- `base_service.py` - 服务基类 (BaseService, ManagedService, DependentService)

**外部依赖**:
- `pydantic` - 数据模型和验证
- `abc` - 抽象基类
- `typing` - 类型注解
- `logging` - 日志记录
- `asyncio` - 异步编程

**依赖关系**: 无内部依赖，是整个系统的基础

---

### 2. 工具模块 (tools/)

**职责**: 提供各种功能工具的独立实现

**包含组件**:
- `time_tool.py` - 时间查询和计算工具
- `math_tool.py` - 数学计算工具
- `weather_tool.py` - 天气查询工具
- `search_tool.py` - 信息搜索工具

**依赖关系**:
```
tools/ ──> core/
         ├── ITool (接口继承)
         ├── BaseTool (基类继承)
         ├── ToolRegistry (注册到)
         └── ToolMetadata (元数据模型)

tools/ ──> services/
         ├── WeatherService (天气服务)
         ├── LocationService (地名匹配服务)
         └── CacheService (缓存服务)
```

---

### 3. 服务模块 (services/)

**职责**: 提供后端服务支持

**包含组件**:
- `weather/weather_service.py` - 天气数据服务
- `matching/location_service.py` - 地名匹配服务
- `cache/cache_service.py` - 缓存管理服务
- `database/database_service.py` - 数据库访问服务
- `service_manager.py` - 服务管理器

**依赖关系**:
```
services/ ──> core/
           ├── IService (接口继承)
           ├── BaseService (基类继承)
           ├── ServiceRegistry (注册到)
           └── ServiceConfig (配置模型)

services/ (可选) ──> 外部依赖
                   ├── aiohttp (HTTP客户端)
                   ├── sqlalchemy (ORM)
                   ├── redis (缓存)
                   └── 第三方API客户端
```

---

### 4. 智能体模块 (agents/)

**职责**: 提供智能体实现和管理

**包含组件**:
- `modern_agent.py` - 现代LangChain智能体
- `agent_factory.py` - 智能体工厂
- `agent_manager.py` - 智能体管理器
- `agent_config.py` - 智能体配置

**依赖关系**:
```
agents/ ──> core/
          ├── IAgent (接口继承)
          ├── BaseAgent (基类继承)
          ├── AgentConfig (配置模型)
          └── ITool (工具接口)

agents/ ──> tools/
          ├── TimeTool (时间工具)
          ├── MathTool (数学工具)
          ├── WeatherTool (天气工具)
          └── SearchTool (搜索工具)

agents/ ──> services/
          ├── WeatherService (天气服务)
          ├── LocationService (地名匹配)
          └── CacheService (缓存服务)

agents/ (可选) ──> 外部依赖
                 ├── langchain (LLM框架)
                 ├── langchain-openai (OpenAI集成)
                 ├── langchain-anthropic (Anthropic集成)
                 └── zai-sdk (智谱AI集成)
```

## 数据流图

```
用户查询
    ↓
agents/ (智能体层)
    ↓ 调用工具
tools/ (工具层)
    ↓ 调用服务
services/ (服务层)
    ↓ 基础设施
core/ (核心层)
```

## 接口契约

### 1. 工具接口 (ITool)

```python
class ITool(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata: ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult: ...

    @abstractmethod
    def validate_input(self, **kwargs) -> bool: ...
```

### 2. 智能体接口 (IAgent)

```python
class IAgent(ABC):
    @property
    @abstractmethod
    def config(self) -> AgentConfig: ...

    @abstractmethod
    async def run(self, query: str) -> str: ...

    @abstractmethod
    def add_tool(self, tool: ITool) -> None: ...

    @abstractmethod
    def remove_tool(self, tool_name: str) -> None: ...
```

### 3. 服务接口 (IService)

```python
class IService(ABC):
    @property
    @abstractmethod
    def config(self) -> ServiceConfig: ...

    @abstractmethod
    async def initialize(self) -> None: ...

    @abstractmethod
    async def cleanup(self) -> None: ...

    @abstractmethod
    def health_check(self) -> bool: ...
```

## 循环依赖避免

### 依赖注入模式

系统采用依赖注入模式来避免循环依赖：

1. **核心模块** (core/) 不依赖任何其他业务模块
2. **工具模块** (tools/) 只依赖核心模块和服务模块
3. **服务模块** (services/) 只依赖核心模块
4. **智能体模块** (agents/) 依赖核心模块、工具模块和服务模块

### 注册器模式

使用注册器模式来管理组件间的松耦合：

```python
# 核心注册器
class ToolRegistry:
    def register(self, name: str, tool: ITool) -> None: ...

class ServiceRegistry:
    def register(self, name: str, service: Any) -> None: ...

# 在智能体中使用
class AgentManager:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.service_manager = ServiceManager()
```

## 扩展性设计

### 1. 新增工具

```python
# 1. 创建新工具类
class NewTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(name="new_tool", ...)

    async def _execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        pass

# 2. 注册到工具注册器
registry = ToolRegistry()
registry.register_class(NewTool)
```

### 2. 新增服务

```python
# 1. 创建新服务类
class NewService(BaseService):
    async def _on_initialize(self) -> None:
        # 初始化逻辑
        pass

# 2. 注册到服务管理器
service_manager = ServiceManager()
service_manager.register("new_service", NewService())
```

### 3. 新增智能体

```python
# 1. 创建新智能体类
class NewAgent(BaseAgent):
    async def _run(self, query: str) -> str:
        # 智能体逻辑
        pass

# 2. 注册到智能体工厂
agent_factory = AgentFactory(tool_registry)
agent = agent_factory.create_agent("new_agent", config)
```

## 最佳实践

### 1. 依赖管理

- **单向依赖**: 高层模块依赖低层模块，避免循环依赖
- **接口隔离**: 依赖抽象接口而非具体实现
- **依赖注入**: 通过构造函数或方法参数注入依赖

### 2. 模块设计

- **单一职责**: 每个模块只负责一个明确的功能域
- **开闭原则**: 对扩展开放，对修改封闭
- **接口隔离**: 提供最小化的接口

### 3. 错误处理

- **异常传播**: 在适当的层次处理异常
- **错误恢复**: 提供优雅的降级和恢复机制
- **日志记录**: 记录关键操作和错误信息

## 性能考虑

### 1. 异步操作

- 所有I/O操作都应该是异步的
- 使用 `async/await` 语法
- 合理使用并发控制

### 2. 资源管理

- 使用上下文管理器管理资源
- 及时释放不再使用的资源
- 实现连接池和缓存机制

### 3. 懒加载

- 按需加载模块和组件
- 使用注册器模式支持动态发现
- 避免不必要的初始化开销